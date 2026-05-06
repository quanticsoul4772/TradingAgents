# Feature Specification: Sector-Momentum Filter

**Feature Branch**: `004-sector-momentum-filter`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "Sector-momentum filter (Spec 004). Analogous to A3 momentum filter but operating at SECTOR level instead of per-ticker. Empirical motivation: claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md showed the SC-003 Financials losers (-7.07% mean α on 5 OW commits) came from sector-rotation. Mechanism: when a ticker's GICS sector maps to a sector ETF (Technology→XLK, Financials→XLF, ...) and that ETF is down more than a configurable threshold in the prior 30 trading days, suppress the ticker's Buy/Overweight commit to Hold."

## Why this exists

The framework has two existing mean-reversion-zone filters:

- **A3 momentum filter** (`tradingagents/agents/utils/momentum_filter.py`) — suppresses Underweight/Sell commits to Hold when a ticker is down >5% over the prior 30 trading days (per-ticker bear suppression).
- **Spec 003 contrarian gate** + **Spec 003.5 sector-baseline fallback** — suppress Buy/Overweight commits to Hold when the analyst's `bull_keyword_count` exceeds the 80th percentile of historical observations (within-ticker prose-density mean-reversion, with sector-pool fallback for cold-start tickers).

Today's spec 003.5 validation against the SC-003 Financials cohort (`claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md`) revealed a **third class of bullish-side miss neither existing filter catches**: sector-rotation losses where the ticker isn't anomalous within itself or its sector — the entire sector is down. The 5 SC-003 Financials Overweight commits (-7.07% mean α) had moderate `bull_keyword_count` values (46-65) and the Financials sector was down ~7% relative to SPY in the 21d window. Neither the per-ticker prose-density check nor the sector-prose-percentile check fires on moderate-density commits in a sector-rotation regime.

This feature adds a sector-momentum filter to fill that gap: when a ticker's sector ETF is in a mean-reversion-zone (or, more precisely, a still-falling regime) at the moment of a bullish commit, suppress the commit to Hold. This is the bullish-side analog of A3.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sector-rotation bullish miss prevented (Priority: P1)

The framework propagates on a Financials ticker (e.g. WFC) and the Portfolio Manager emits **Overweight**. Before persisting the rating, the sector-momentum filter checks: WFC's GICS sector is "Financial Services" → maps to XLF. XLF is down -8% over the prior 30 trading days (below the configured -5% threshold). The filter overrides the rating to **Hold**, annotating the decision markdown with the sector-rotation rationale. The persisted state log + downstream consumers see Hold, not Overweight.

**Why this priority**: The whole feature exists to catch this case. Without it, the SC-003-Financials class of failure remains uncaught.

**Independent Test**: Run a propagate against WFC for a date when XLF was down -8% in the prior 30 trading days. With the filter on, verify the rating is Hold (and the markdown contains a `[Sector-momentum filter]` note explaining XLF's drawdown). With the filter off (default), verify the rating is Overweight.

**Acceptance Scenarios**:

1. **Given** WFC PM rating = Overweight AND XLF prior-30d return = -8% AND filter threshold = -5%, **When** the filter evaluates the rating, **Then** the rating is downgraded to Hold and the decision markdown carries a sector-momentum note (sector ETF, drawdown %, threshold).
2. **Given** WFC PM rating = Overweight AND XLF prior-30d return = -2% (above threshold), **When** the filter evaluates, **Then** the rating remains Overweight (no override; no annotation).
3. **Given** WFC PM rating = Underweight AND XLF prior-30d return = -8%, **When** the filter evaluates, **Then** the rating remains Underweight (filter only acts on Buy/Overweight per the bullish-suppression scope).
4. **Given** WFC PM rating = Hold AND XLF prior-30d return = -8%, **When** the filter evaluates, **Then** the rating remains Hold (no-op; nothing to suppress).

---

### User Story 2 - Operator distinguishes sector-momentum firings in audit (Priority: P2)

The operator inspects the contrarian/momentum filter activity across a corpus and wants to know which Buy/OW → Hold downgrades came from this filter vs from the spec 003 contrarian gate vs from no filter at all. The filter emits a structured annotation (`sector_momentum: dict | None`) into the LangGraph state alongside the existing `contrarian_gate` annotation, with fields identifying which sector ETF, what its prior-30d return was, what threshold fired, and whether the rating was actually overridden (active mode) vs would-have-been (shadow mode for measurement).

**Why this priority**: Operational ergonomic — necessary so operators don't conflate filter sources when computing realized α attribution per filter. Not blocking the MVP firing logic.

**Independent Test**: Run a small corpus through the harness with the filter in shadow mode. Inspect each `state["sector_momentum"]` annotation; verify the fields are populated correctly (sector ETF, drawdown %, threshold, would_fire, fired).

**Acceptance Scenarios**:

1. **Given** a propagate where the filter fired (active mode, threshold crossed, bullish rating), **When** the operator reads `state["sector_momentum"]`, **Then** the dict contains `{"mode": "active", "sector": "Financial Services", "etf": "XLF", "etf_30d_return_pct": -8.x, "threshold_pct": -5.0, "would_fire": True, "fired": True, "pre_rating": "Overweight", "post_rating": "Hold"}`.
2. **Given** a propagate where filter is in shadow mode and threshold crossed, **When** the operator reads the annotation, **Then** `would_fire: True` AND `fired: False` AND `post_rating == pre_rating == "Overweight"`.
3. **Given** a propagate where the filter is off, **When** the operator reads `state["sector_momentum"]`, **Then** the field is `None` or absent.

---

### Edge Cases

- What happens when a ticker's sector is `"Unknown"` (yfinance lookup failed or returned empty)? The filter cannot determine which sector ETF to consult; emit `mode_skipped` annotation with reason `"unknown_sector"` and pass the rating through unchanged. Same defensive pattern as spec 003.5 for `"Unknown"` sector.
- What happens when a sector has no canonical ETF mapping in the table (e.g., a sector yfinance reports that wasn't on the spec's mapping list)? Emit `mode_skipped` with reason `"no_etf_mapping"` and pass the rating through unchanged.
- What happens when the sector ETF's price history is unavailable for the prior 30 trading days (yfinance failure, weekend boundary, etc.)? Emit `mode_skipped` with reason `"missing_etf_data"` and pass the rating through unchanged. Filter never breaks the propagate pipeline.
- What happens when the sector ETF's prior-30d return equals the threshold exactly (e.g., -5.0% with threshold -5.0%)? Treat as "below threshold" (use `<` not `<=`) — fires only when strictly more negative than the threshold. Matches A3's semantics.
- What happens when the same propagate hits multiple filters in sequence (A3 + spec 003 + spec 003.5 + this)? Filters run in defined order; this filter only sees the rating PRIOR filters left in place. If the rating is already Hold (because spec 003 / 003.5 fired earlier), this filter no-ops. If the rating is still Buy/OW after prior filters, this filter applies. Order matters and must be deterministic — see the Functional Requirements for the exact wiring order.
- What happens to a Buy rating (not just Overweight)? Same treatment: downgrade Buy to Hold. Both Buy and Overweight are "bullish" per the existing `_BULLISH_RATINGS = {"Buy", "Overweight"}` convention from spec 003.
- What happens when an operator sets the threshold to a positive number (e.g. +5%)? The filter would fire on UP-trending sectors, which inverts the intent. Constrain threshold to ≤ 0 in config validation; reject (with warning) and skip the filter if a positive threshold is configured.
- What happens when spec 003 is in "off" mode but this filter is "active"? Filters are independent — this filter still runs, regardless of spec 003 mode.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The filter MUST evaluate after the LLM's Portfolio Manager has emitted its rating but before the rating is persisted to state. Wired into `tradingagents/agents/managers/portfolio_manager.py` after the existing A3 + spec 003 contrarian gate hooks.
- **FR-002**: The filter MUST only act on `Buy` and `Overweight` ratings. `Hold`, `Underweight`, `Sell` are passed through unchanged.
- **FR-003**: The filter MUST resolve the ticker's sector via `tradingagents/paper/sectors.py::get_sector` (the same yfinance-cached source spec 003.5 uses). When the sector lookup returns `"Unknown"` or fails, the filter MUST skip with annotation reason `"unknown_sector"` and not modify the rating.
- **FR-004**: The filter MUST map sector to ETF using a canonical built-in table covering the 11 GICS sectors:
  - Technology → XLK
  - Financial Services / Financials → XLF
  - Healthcare → XLV
  - Energy → XLE
  - Consumer Cyclical / Consumer Discretionary → XLY
  - Consumer Defensive / Consumer Staples → XLP
  - Industrials → XLI
  - Communication Services → XLC
  - Utilities → XLU
  - Real Estate → XLRE
  - Basic Materials / Materials → XLB

  Sector names that don't appear in this table MUST cause the filter to skip with annotation reason `"no_etf_mapping"`. The mapping table is hardcoded; new sector ETFs require a code change (deliberate — sector ETF mappings are stable and adding entries should be reviewed).
- **FR-005**: The filter MUST compute the sector ETF's return over the prior N trading days (default 30, matching A3's lookback) using the same `tradingagents.dataflows.returns` primitive (`returns_from_frames` or equivalent close-to-close math) as the rest of the framework. No new forward-α math is permitted.
- **FR-006**: The filter MUST use a configurable threshold (default `None` = filter disabled; explicit numeric value enables). When the sector ETF's prior-N-day return is **strictly less than** the configured threshold (e.g., return = -8% < threshold = -5% → fire), the filter MUST act on bullish ratings. The threshold MUST be ≤ 0; positive thresholds are rejected at config-load time with a warning + filter disabled.
- **FR-007**: When the filter fires in active mode on a bullish rating, the rating MUST be downgraded to `"Hold"`. The decision markdown MUST be annotated with a `[Sector-momentum filter]` note containing: sector name, ETF symbol, prior-N-day return %, threshold %, and the original rating.
- **FR-008**: The filter MUST support three modes via config: `"off"` (filter disabled, no annotation emitted), `"shadow"` (compute the annotation, mark `would_fire`, but do NOT override the rating), `"active"` (compute + override). Default is `"off"` (consistent with how A3 was originally introduced; flipped to `"active"` only after corpus retrospective validation per Constitution II ablation discipline).
- **FR-009**: The filter MUST emit a structured annotation to LangGraph state at `state["sector_momentum"]` with the schema defined in Key Entities below. The annotation is `None` when mode is `"off"`. The state-log writer (`tradingagents/graph/trading_graph.py:_log_state`) MUST be extended to persist this field (parallel to the spec 003 `contrarian_gate` field added in commit `4c14d0f`).
- **FR-010**: The filter MUST never break the PM pipeline. All exception paths (yfinance failure, sector-lookup failure, ETF-mapping miss, etc.) MUST log a warning + emit a skipped annotation + return the rating unchanged. Same resilience pattern as the existing A3 + spec 003 hooks.
- **FR-011**: The filter MUST be deterministic — same ticker + same trade_date + same threshold + same lookback ⇒ same fire decision (modulo upstream yfinance data corrections, which apply to the entire framework).
- **FR-012**: When wired into the PM hook chain, the order MUST be: (1) A3 (bear suppression on UW/Sell), (2) Spec 003 + 003.5 contrarian gate (within-ticker / sector-baseline bull suppression), (3) Sector-momentum filter (this spec — sector-ETF bull suppression). The order matters because the contrarian gate's bull-suppression may have already turned the rating to Hold, in which case this filter no-ops. Documented in CLAUDE.md and the wiring code comments.
- **FR-013**: The filter MUST be feature-flagged via the threshold config key (default `None` → disabled). No separate boolean flag — passing `None` IS the off switch. This mirrors A3's `uw_momentum_filter_threshold` config pattern.

### Key Entities *(include if data involved)*

- **`SectorMomentumAnnotation`**: The dict emitted to `state["sector_momentum"]`. Fields:
  - `mode: Literal["off", "shadow", "active"]` — the filter's active mode at evaluation
  - `sector: str | None` — the GICS sector resolved for the ticker (or `None` if `"Unknown"`)
  - `etf: str | None` — the ETF symbol the sector maps to (e.g., `"XLF"`); `None` if no mapping or sector unknown
  - `etf_30d_return_pct: float | None` — the sector ETF's prior-30-trading-day return as a percentage; `None` if data unavailable
  - `threshold_pct: float | None` — the configured threshold (e.g., `-5.0`); `None` when filter disabled
  - `lookback_days: int` — the lookback period used (default 30)
  - `would_fire: bool` — `True` iff `etf_30d_return_pct < threshold_pct AND pre_rating in {Buy, Overweight}`
  - `fired: bool` — `True` iff `would_fire AND mode == "active"` (i.e., the rating was actually overridden)
  - `pre_rating: str` — the rating BEFORE this filter ran
  - `post_rating: str` — the rating AFTER this filter ran (may equal `pre_rating` if mode != "active")
  - `skipped: Literal["off", "unknown_sector", "no_etf_mapping", "missing_etf_data", "rating_not_bullish"] | None` — reason the filter didn't compute a fire decision (or `None` if it did)
- **`SECTOR_ETF_MAP` (constant)**: Hardcoded module-level dict at `tradingagents/agents/utils/sector_momentum_filter.py` (parallel placement to A3's `momentum_filter.py`). Maps GICS sector names (per yfinance's reported strings) to sector ETF symbols. The 11-entry table per FR-004.
- **Configuration extensions to `TradingAgentsConfig` (TypedDict)**: Three new keys added to `tradingagents/default_config.py`:
  - `sector_momentum_filter_mode: Literal["off", "shadow", "active"]` (default `"off"`)
  - `sector_momentum_filter_threshold_pct: float | None` (default `None`; rejected if > 0)
  - `sector_momentum_filter_lookback_days: int` (default `30`, mirroring A3)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Mechanism correctness)**: When evaluated against a synthetic test corpus where the sector ETF return is `-8%` and threshold is `-5%`, the filter MUST fire on `Overweight`/`Buy` ratings and NOT fire on `Hold`/`Underweight`/`Sell` ratings. Verified by 4 unit tests covering all 5 ratings × the threshold-crossed condition.
- **SC-002 (Threshold semantics)**: When evaluated with sector ETF return exactly equal to the threshold (e.g., -5.0% with threshold -5.0%), the filter MUST NOT fire (strict less-than). Verified by a boundary unit test.
- **SC-003 (Audit clarity)**: For every state log produced after this feature lands with mode != `"off"`, `state["sector_momentum"]` MUST be present and equal a populated dict matching the schema in Key Entities. An aggregator script MUST be able to filter the corpus by `state["sector_momentum"]["fired"]` and produce per-sector α statistics.
- **SC-004 (Reproducibility / determinism)**: Running the filter twice on the same `(ticker, trade_date, threshold, lookback)` tuple MUST produce identical annotations (modulo yfinance data corrections). Verified by an integration test.
- **SC-005 (No new LLM cost)**: This feature adds zero LLM API calls. Verified by running with all provider API keys unset and observing no failures attributable to missing keys.
- **SC-006 (Default-off honored)**: When `sector_momentum_filter_threshold_pct` is `None` (the default), the filter MUST emit `state["sector_momentum"] = None` or omit the key entirely; PM ratings MUST be byte-identical to the no-filter baseline. Verified by a regression-guard unit test.
- **SC-007 (Test coverage)**: New code in `tradingagents/agents/utils/sector_momentum_filter.py` AND the wiring in `portfolio_manager.py` MUST reach at least 90% line coverage. All 4 acceptance scenarios for User Story 1 are encoded as unit tests.
- **SC-008 (Validation against SC-003 Financials)**: After landing, an offline diagnostic script MUST be created (or `scripts/sc003_financials_gate_check.py` extended) to compute what the sector-momentum filter WOULD have done on the SC-003 Financials cohort with the default `-5%` threshold. Documented expected result: at least 3 of the 5 Financials Overweight commits would have been suppressed (XLF was empirically down >5% in 30d before 2026-04-03; verify at implementation time). This is the empirical-validation gate for the spec — closes the loop on the spec 003.5 validation findings.

## Assumptions

- **Sector source**: `tradingagents/paper/sectors.py::get_sector` (yfinance cache) is the canonical sector-membership lookup, same as spec 003.5. The cache lives at `<paper_state_dir>/sectors.json` per spec 002.
- **Sector ETF universe**: The 11-ETF SPDR sector family (XLK / XLF / XLV / XLE / XLY / XLP / XLI / XLC / XLU / XLRE / XLB) covers the 11 GICS sectors. Edge sectors that yfinance reports outside this taxonomy (e.g. some ADR / international tickers may report unusual sector strings) gracefully degrade to `no_etf_mapping` skip per FR-004.
- **Lookback period**: 30 trading days default, matching A3. A future variant could test 60d / 90d / 5d if empirical work motivates; out of scope for this spec.
- **Threshold semantics**: Strictly less than (return < threshold means "more negative than"). Configurable; threshold = `None` disables; threshold > 0 rejected at config-load time.
- **Default mode**: `"off"`. Operators must explicitly opt-in via `sector_momentum_filter_threshold_pct = -5.0`. This mirrors A3's introduction pattern (also default-off until corpus validation flipped it on per Constitution II).
- **Filter ordering**: A3 → Spec 003/003.5 → Spec 004. Order matters because earlier filters can pre-empt later ones. The contrarian gate runs before this filter so within-ticker prose-density spikes are caught with their own (higher-confidence) signal first; this filter is the safety net for sector-rotation losses the gate misses.
- **No interaction with paper-trading harness defaults**: The Spec 002 paper-trading harness consumes the framework's emitted ratings unchanged. If the filter is `"active"`, the harness sees Hold (and won't open a position). If `"off"` or `"shadow"`, the harness behaves identically to the no-filter baseline.
- **Corpus retrospective before default-on flip**: Per Constitution II, after this feature lands, an offline retrospective script (parallel to `scripts/uw_suppression_filter.py` for A3 and `scripts/contrarian_gate_retrospective.py` for spec 003) MUST be created and run to measure expected Δα contribution at various thresholds. Default-on flip happens in a SEPARATE commit after that retrospective justifies it. Out of scope for this spec; documented as a follow-up.
- **No state-log replay invariant impact**: Adding the new `state["sector_momentum"]` key is additive to the persisted state log; existing replay/analysis scripts continue to work. The `trading_graph.py:_log_state` whitelist must be extended to include the new key (precedent set by commit `4c14d0f` which added `contrarian_gate` to the same whitelist).
- **Sector ETF data via yfinance**: Same provider as the rest of the framework. yfinance failures are transparent — the filter degrades to `missing_etf_data` skip and the propagate completes with the pre-filter rating intact.
