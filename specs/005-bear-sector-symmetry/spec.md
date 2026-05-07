# Feature Specification: Bear-Sector-Symmetry Filter (Spec 006)

**Feature Branch**: `005-bear-sector-symmetry`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "Spec 006: Bearish-symmetry filter — sector-relative mean-reversion analog of A3 momentum filter, but operating on BEAR-side commits and using ticker-vs-sector relative strength instead of per-ticker absolute return. When a ticker has outperformed its sector ETF by more than a configurable threshold (default +5%) over the prior 30 trading days, suppress the ticker's Underweight/Sell commit to Hold."

> Naming note: this spec is referred to as **Spec 006** in CLAUDE.md, RESEARCH_FINDINGS.md, ROADMAP.md, and commit messages to match the user-facing filter-portfolio numbering. The spec-kit branch directory is auto-numbered `005-bear-sector-symmetry` because the spec-kit script ignores the user-facing offset that exists in the broader documentation. The two names refer to the same feature.

## Why this exists

The framework has four existing rating-suppression filters today:

- **A3 momentum filter** (`tradingagents/agents/utils/momentum_filter.py`) — bear-side, per-ticker absolute price. Suppresses Underweight/Sell commits to Hold when a ticker is down >5% over the prior 30 trading days (mean reversion zone).
- **Spec 003 contrarian gate** + **Spec 003.5 sector-baseline fallback** (`tradingagents/signals/contrarian_gate.py`) — bull-side, prose-density. Suppresses Buy/Overweight commits to Hold when the analyst's `bull_keyword_count` exceeds the 80th percentile of its history.
- **Spec 004 sector-momentum filter** (`tradingagents/agents/utils/sector_momentum_filter.py`) — bull-side, sector-ETF absolute price. Suppresses Buy/Overweight commits to Hold when the ticker's sector ETF is down >5% over the prior 30 trading days.

Today's sector-α attribution analysis (`claudedocs/sector-alpha-attribution-2026-05-06.md`) revealed a **massive bear-side anti-calibration that none of these four filters catches**: of 37 bearish commits in the 194-row corpus, 18 (48.6%) landed in the `ticker_strong` cell — ticker rallied vs both SPY AND its own sector despite the bear call. Mean realized α-vs-SPY for that cell: **+28.02%** (n=18). The mechanism is the inverse of A3's premise: A3 catches bearish commits when the ticker is already DOWN (mean-reversion zone for buyers); the cohort this spec targets is bearish commits when the ticker is already UP relative to its sector (the ticker is too strong for a bear call to be probable).

This feature adds a sector-relative bearish-symmetry filter to fill that gap: when a ticker has outperformed its sector ETF by more than a configurable threshold over the prior N trading days, suppress an Underweight/Sell commit to Hold. This is the bear-side relative-strength analog of A3.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Counter-trend bear miss prevented (Priority: P1)

The framework propagates on a Tech ticker (e.g. NVDA) and the Portfolio Manager emits **Underweight**. Before persisting the rating, the bear-sector-symmetry filter checks: NVDA's GICS sector is "Technology" → maps to XLK. NVDA's prior-30-trading-day return = +18%; XLK's prior-30-trading-day return = +6%; the relative-strength delta = +12%, which is above the configured +5% threshold. The filter overrides the rating to **Hold**, annotating the decision markdown with the relative-strength rationale. The persisted state log + downstream consumers see Hold, not Underweight.

**Why this priority**: The whole feature exists to catch this case. Without it, the +28%-mean-α `ticker_strong`-bear cohort identified by today's sector-α attribution remains entirely uncaught.

**Independent Test**: Run a propagate against NVDA for a date when NVDA prior-30d return − XLK prior-30d return > +5%. With the filter on, verify the rating is Hold (and the markdown contains a `[Bear-sector-symmetry filter]` note explaining the relative-strength). With the filter off (default), verify the rating is Underweight.

**Acceptance Scenarios**:

1. **Given** NVDA PM rating = Underweight AND NVDA prior-30d return = +18% AND XLK prior-30d return = +6% AND filter threshold = +5%, **When** the filter evaluates the rating, **Then** the rating is downgraded to Hold and the decision markdown carries a bear-sector-symmetry note (sector ETF, relative-strength delta, threshold).
2. **Given** NVDA PM rating = Sell AND NVDA prior-30d return = +18% AND XLK prior-30d return = +6%, **When** the filter evaluates, **Then** the rating is downgraded to Hold (filter acts on Sell as well as Underweight).
3. **Given** NVDA PM rating = Underweight AND NVDA prior-30d return = +18% AND XLK prior-30d return = +14% (delta = +4%, below +5% threshold), **When** the filter evaluates, **Then** the rating remains Underweight.
4. **Given** NVDA PM rating = Buy AND relative-strength delta = +12%, **When** the filter evaluates, **Then** the rating remains Buy (filter only acts on Underweight/Sell per the bearish-suppression scope).
5. **Given** NVDA PM rating = Hold, **When** the filter evaluates, **Then** the rating remains Hold (no-op; nothing to suppress).
6. **Given** NVDA PM rating = Underweight AND A3 already suppressed it to Hold (ticker also -5% in absolute terms — empirically rare since the two filter conditions are nearly disjoint), **When** this filter evaluates the rating, **Then** the rating remains Hold (no-op; pre-filter chain already neutralized).

---

### User Story 2 - Operator distinguishes bear-sector-symmetry firings in audit (Priority: P2)

The operator inspects bear-side filter activity across a corpus and wants to know which UW/Sell → Hold downgrades came from this filter vs from A3 vs from no filter at all. The filter emits a structured annotation (`bear_sector_symmetry: dict | None`) into the LangGraph state alongside the existing `contrarian_gate` and `sector_momentum` annotations, with fields identifying the sector ETF, the ticker's prior-30d return, the sector ETF's prior-30d return, the relative-strength delta, the threshold, and whether the rating was actually overridden (active mode) vs would-have-been (shadow mode for measurement).

**Why this priority**: Operational ergonomic — necessary so operators don't conflate filter sources when computing realized α attribution per filter. Mirrors the audit pattern established by spec 003's `contrarian_gate` annotation and spec 004's `sector_momentum` annotation. Not blocking the MVP firing logic.

**Independent Test**: Run a small corpus through the harness with the filter in shadow mode. Inspect each `state["bear_sector_symmetry"]` annotation; verify the fields are populated correctly (sector, ETF, ticker_30d_return_pct, etf_30d_return_pct, relative_strength_pct, threshold_pct, would_fire, fired, pre_rating, post_rating, skipped).

**Acceptance Scenarios**:

1. **Given** a propagate where the filter fired (active mode, threshold crossed, bearish rating), **When** the operator reads `state["bear_sector_symmetry"]`, **Then** the dict contains `{"mode": "active", "sector": "Technology", "etf": "XLK", "ticker_30d_return_pct": 18.x, "etf_30d_return_pct": 6.x, "relative_strength_pct": 12.x, "threshold_pct": 5.0, "would_fire": True, "fired": True, "pre_rating": "Underweight", "post_rating": "Hold", "skipped": None}`.
2. **Given** a propagate where filter is in shadow mode and threshold crossed, **When** the operator reads the annotation, **Then** `would_fire: True` AND `fired: False` AND `post_rating == pre_rating == "Underweight"`.
3. **Given** a propagate where the filter is off, **When** the operator reads `state["bear_sector_symmetry"]`, **Then** the field is `None` or absent.

---

### User Story 3 - Corpus retrospective gate before default-on flip (Priority: P3)

Per Constitution II ablation discipline (and the precedent set by spec 003 + spec 004 retrospectives), before the filter's default mode is flipped from `"off"` to `"active"`, an offline retrospective script must be created that walks the existing `experiments/*/results.csv` corpus, simulates the filter at multiple thresholds (e.g. +3% / +5% / +7.5% / +10%), and reports per-threshold + per-sector net Δα contribution. The default-on flip happens in a SEPARATE commit only if the retrospective shows positive net Δα at the chosen default threshold.

**Why this priority**: Process discipline. The implementation work (User Story 1+2) lands first; the retrospective + default-on flip are sequenced afterward. This story exists in the spec to make the gate explicit so the work isn't skipped.

**Independent Test**: Run `scripts/bear_sector_symmetry_retrospective.py` against the existing corpus. Inspect the output markdown; verify it reports baseline mean α (no filter) + per-threshold (kept α, fired α, net Δα) + per-sector breakdown at the default threshold + worst-fire / best-suppression-miss outliers.

**Acceptance Scenarios**:

1. **Given** the implementation has landed (User Stories 1+2 complete) AND the retrospective script exists, **When** the operator runs the script, **Then** the output reports per-threshold net Δα across the n=37 bearish commits (or whatever the corpus size is at run time).
2. **Given** the retrospective shows positive net Δα at the +5% default threshold, **When** the operator authors a follow-up commit setting `bear_sector_symmetry_filter_threshold_pct = 5.0` + `bear_sector_symmetry_filter_mode = "active"` in `default_config.py`, **Then** the test suite passes and the change is empirically justified per Constitution II.
3. **Given** the retrospective shows negative or zero net Δα at +5%, **When** the operator decides not to flip default-on, **Then** the filter remains default-off as an operator-opt-in tool (parallel outcome to spec 004's retrospective verdict).

---

### Edge Cases

- What happens when a ticker's sector is `"Unknown"` (yfinance lookup failed or returned empty)? The filter cannot determine which sector ETF to consult; emit `skipped="unknown_sector"` annotation and pass the rating through unchanged. Same defensive pattern as spec 003.5 and spec 004.
- What happens when a sector has no canonical ETF mapping (sector yfinance reports outside the SECTOR_ETF_MAP table)? Emit `skipped="no_etf_mapping"` and pass the rating through unchanged.
- What happens when the ticker's price history is unavailable for the prior 30 trading days (yfinance failure)? Emit `skipped="missing_ticker_data"` and pass the rating through unchanged.
- What happens when the sector ETF's price history is unavailable? Emit `skipped="missing_etf_data"` and pass the rating through unchanged.
- What happens when the ticker's prior-30d return MINUS sector ETF's prior-30d return equals the threshold exactly (e.g., delta = +5.0% with threshold +5.0%)? Treat as "below threshold" (use `>` not `>=`) — fires only when the relative-strength delta is strictly greater than the threshold. Mirrors spec 004's strict-less-than semantics inverted for the bear side.
- What happens when the same propagate hits A3 first and A3 already suppressed UW/Sell to Hold? This filter sees Hold and no-ops (rating not in the bear set). The two filters' fire conditions are nearly disjoint by construction (A3 fires when ticker is DOWN ≥5% absolute; spec 006 fires when ticker is UP ≥5% relative to sector, which usually means the ticker is also UP in absolute terms), but the no-op path is the safety net for the rare overlap case (e.g. ticker is -5% absolute AND sector is -10% — ticker outperforms sector despite both being down).
- What happens to a Sell rating (not just Underweight)? Same treatment: downgrade Sell to Hold. Both Underweight and Sell are "bearish" per the existing `_BEARISH_RATINGS` convention used by A3.
- What happens when an operator sets the threshold to a negative number (e.g. -5%)? The filter would fire when the ticker has UNDERPERFORMED its sector by more than 5% — which is the OPPOSITE of the spec's intent (ticker is weak vs sector → already a candidate for further selling, not a contrarian buy-the-dip). Constrain threshold to ≥ 0 in config validation; reject (with warning) and skip the filter if a negative threshold is configured. Symmetric inverse of spec 004's positive-threshold rejection.
- What happens when spec 003 / 003.5 / 004 are in any combination of modes? Filters are independent — this filter still runs on bearish ratings, regardless of bull-side filter modes. Bull-side filters (spec 003 / 003.5 / 004) only act on Buy/Overweight; they don't touch bearish ratings, so there's no interaction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The filter MUST evaluate after the LLM's Portfolio Manager has emitted its rating but before the rating is persisted to state. Wired into `tradingagents/agents/managers/portfolio_manager.py` after the existing A3 hook (and parallel to spec 003 / spec 004 hooks for code organization).
- **FR-002**: The filter MUST only act on `Underweight` and `Sell` ratings. `Buy`, `Overweight`, `Hold` are passed through unchanged.
- **FR-003**: The filter MUST resolve the ticker's sector via `tradingagents/paper/sectors.py::get_sector` (the same yfinance-cached source spec 003.5 + spec 004 use). When the sector lookup returns `"Unknown"` or fails, the filter MUST skip with annotation reason `"unknown_sector"` and not modify the rating.
- **FR-004**: The filter MUST map sector to ETF using the existing `SECTOR_ETF_MAP` constant from `tradingagents/agents/utils/sector_momentum_filter.py` (the 11-entry SPDR mapping established by spec 004). NO duplication of the mapping table — the new filter imports the existing one. Sector names that don't appear in the map MUST cause the filter to skip with annotation reason `"no_etf_mapping"`.
- **FR-005**: The filter MUST compute (a) the ticker's return over the prior N trading days and (b) the sector ETF's return over the same N trading days using the existing `_etf_history` LRU-cached fetcher pattern from spec 004 (and an analogous `_ticker_history` fetcher with the same caching semantics). The relative-strength delta is `ticker_return_pct − etf_return_pct`. Default lookback N = 30 trading days, matching A3 + spec 004.
- **FR-006**: The filter MUST use a configurable threshold (default `None` = filter disabled; explicit numeric value enables). When the relative-strength delta is **strictly greater than** the configured threshold (e.g., delta = +12% > threshold = +5% → fire), the filter MUST act on bearish ratings. The threshold MUST be ≥ 0; negative thresholds are rejected at config-load time with a warning + filter disabled. (Symmetric inverse of spec 004's `≤ 0` constraint.)
- **FR-007**: When the filter fires in active mode on a bearish rating, the rating MUST be downgraded to `"Hold"`. The filter MUST NEVER upgrade ratings to `Buy`/`Overweight` (suppression target is Hold, not flip-to-bullish; aligns with the existing filter family's downgrade-only semantics). The decision markdown MUST be annotated with a `[Bear-sector-symmetry filter]` note containing: sector name, ETF symbol, ticker prior-N-day return %, ETF prior-N-day return %, relative-strength delta %, threshold %, and the original rating.
- **FR-008**: The filter MUST support three modes via config: `"off"` (filter disabled, no annotation emitted), `"shadow"` (compute the annotation, mark `would_fire`, but do NOT override the rating), `"active"` (compute + override). Default is `"off"` (consistent with how A3 + spec 004 were originally introduced; flipped to `"active"` only after corpus retrospective validation per Constitution II ablation discipline).
- **FR-009**: The filter MUST emit a structured annotation to LangGraph state at `state["bear_sector_symmetry"]` with the schema defined in Key Entities below. The annotation is `None` when mode is `"off"`. The state-log writer (`tradingagents/graph/trading_graph.py:_log_state`) MUST be extended to persist this field (parallel to the spec 003 `contrarian_gate` field added in commit `4c14d0f` and the spec 004 `sector_momentum` field). The LangGraph `AgentState` TypedDict (`tradingagents/agents/utils/agent_states.py`) MUST be extended with the `bear_sector_symmetry` key (precedent set by spec 003 — undeclared keys are silently dropped from state merges).
- **FR-010**: The filter MUST never break the PM pipeline. All exception paths (yfinance failure, sector-lookup failure, ETF-mapping miss, etc.) MUST log a warning + emit a skipped annotation + return the rating unchanged. Same resilience pattern as the existing A3 + spec 003 + spec 004 hooks.
- **FR-011**: The filter MUST be deterministic — same ticker + same trade_date + same threshold + same lookback ⇒ same fire decision (modulo upstream yfinance data corrections, which apply to the entire framework).
- **FR-012**: When wired into the PM hook chain, the order MUST be: (1) A3 (per-ticker bear suppression on UW/Sell when ticker is DOWN), (2) Bear-sector-symmetry filter (this spec — sector-relative bear suppression on UW/Sell when ticker is UP relative to sector), (3) Spec 003 + 003.5 contrarian gate (within-ticker / sector-baseline bull suppression), (4) Spec 004 sector-momentum filter (sector-ETF bull suppression). The two bear filters (A3 + spec 006) operate on disjoint price-condition cohorts; the relative ordering between them is documented for determinism but doesn't affect outcomes in practice. Order matters for the bull/bear separation: bull-side filters never see bearish ratings (and vice versa), so the cross-side filters are commutative.
- **FR-013**: The filter MUST be feature-flagged via the threshold config key (default `None` → disabled). No separate boolean flag — passing `None` IS the off switch. This mirrors A3's + spec 004's config patterns.

### Key Entities *(include if data involved)*

- **`BearSectorSymmetryAnnotation`**: The dict emitted to `state["bear_sector_symmetry"]`. Fields:
  - `mode: Literal["off", "shadow", "active"]` — the filter's active mode at evaluation
  - `sector: str | None` — the GICS sector resolved for the ticker (or `None` if `"Unknown"`)
  - `etf: str | None` — the ETF symbol the sector maps to (e.g., `"XLK"`); `None` if no mapping or sector unknown
  - `ticker_30d_return_pct: float | None` — the ticker's prior-30-trading-day return as a percentage; `None` if data unavailable
  - `etf_30d_return_pct: float | None` — the sector ETF's prior-30-trading-day return as a percentage; `None` if data unavailable
  - `relative_strength_pct: float | None` — `ticker_30d_return_pct − etf_30d_return_pct`; `None` if either component is missing
  - `threshold_pct: float | None` — the configured threshold (e.g., `+5.0`); `None` when filter disabled
  - `lookback_days: int` — the lookback period used (default 30)
  - `would_fire: bool` — `True` iff `relative_strength_pct > threshold_pct AND pre_rating in {Underweight, Sell}`
  - `fired: bool` — `True` iff `would_fire AND mode == "active"` (i.e., the rating was actually overridden)
  - `pre_rating: str` — the rating BEFORE this filter ran
  - `post_rating: str` — the rating AFTER this filter ran (may equal `pre_rating` if mode != "active")
  - `skipped: Literal["off", "unknown_sector", "no_etf_mapping", "missing_ticker_data", "missing_etf_data", "rating_not_bearish", "invalid_threshold"] | None` — reason the filter didn't compute a fire decision (or `None` if it did)
- **`SECTOR_ETF_MAP` (reuse, not redefine)**: Imported from `tradingagents/agents/utils/sector_momentum_filter.py`. The 11-entry SPDR mapping defined by spec 004 is the single source of truth.
- **Configuration extensions to `TradingAgentsConfig` (TypedDict)**: Three new keys added to `tradingagents/default_config.py`:
  - `bear_sector_symmetry_filter_mode: Literal["off", "shadow", "active"]` (default `"off"`)
  - `bear_sector_symmetry_filter_threshold_pct: float | None` (default `None`; rejected if < 0)
  - `bear_sector_symmetry_filter_lookback_days: int` (default `30`, mirroring A3 + spec 004)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Mechanism correctness)**: When evaluated against a synthetic test corpus where the relative-strength delta is `+12%` and threshold is `+5%`, the filter MUST fire on `Underweight`/`Sell` ratings and NOT fire on `Hold`/`Buy`/`Overweight` ratings. Verified by 5 unit tests covering all 5 ratings × the threshold-crossed condition.
- **SC-002 (Threshold semantics)**: When evaluated with relative-strength delta exactly equal to the threshold (e.g., delta = +5.0% with threshold +5.0%), the filter MUST NOT fire (strict greater-than). Verified by a boundary unit test.
- **SC-003 (Audit clarity)**: For every state log produced after this feature lands with mode != `"off"`, `state["bear_sector_symmetry"]` MUST be present and equal a populated dict matching the schema in Key Entities. An aggregator script MUST be able to filter the corpus by `state["bear_sector_symmetry"]["fired"]` and produce per-sector α statistics.
- **SC-004 (Reproducibility / determinism)**: Running the filter twice on the same `(ticker, trade_date, threshold, lookback)` tuple MUST produce identical annotations (modulo yfinance data corrections). Verified by an integration test.
- **SC-005 (No new LLM cost)**: This feature adds zero LLM API calls. Verified by running with all provider API keys unset and observing no failures attributable to missing keys.
- **SC-006 (Default-off honored)**: When `bear_sector_symmetry_filter_threshold_pct` is `None` (the default), the filter MUST emit `state["bear_sector_symmetry"] = None` or omit the key entirely; PM ratings MUST be byte-identical to the no-filter baseline. Verified by a regression-guard unit test.
- **SC-007 (Test coverage)**: New code in `tradingagents/agents/utils/bear_sector_symmetry_filter.py` AND the wiring in `portfolio_manager.py` MUST reach at least 90% line coverage. All 6 acceptance scenarios for User Story 1 are encoded as unit tests.
- **SC-008 (Validation against today's bear cohort)**: After landing, a corpus retrospective script (`scripts/bear_sector_symmetry_retrospective.py`) MUST be created that simulates the filter at multiple thresholds against the existing 37-row bearish-commit corpus. Documented expected result: at the default `+5%` threshold, the filter fires on a meaningful subset of the 18 `ticker_strong`-bearish commits identified in `claudedocs/sector-alpha-attribution-2026-05-06.md`. Specific quantitative target: at least 8 of 18 `ticker_strong` bear commits would be suppressed at `+5%` threshold (verify exact count at retrospective time). Net Δα target: positive at the default threshold (sign criterion only — magnitude TBD by retrospective).
- **SC-009 (Disjoint-condition guard with A3)**: When A3 has already suppressed an UW/Sell to Hold (ticker is down ≥5% absolute), this filter MUST no-op (rating not in bear set). Verified by a unit test that runs both filters in sequence on a synthetic ticker that is both DOWN absolute AND DOWN relative to sector.

## Assumptions

- **Sector source**: `tradingagents/paper/sectors.py::get_sector` (yfinance cache) is the canonical sector-membership lookup, same as spec 003.5 and spec 004. The cache lives at `<paper_state_dir>/sectors.json` per spec 002.
- **Sector ETF universe**: The 11-entry SPDR mapping (`SECTOR_ETF_MAP`) defined by spec 004 is reused unchanged. This spec adds NO new sector mappings.
- **Lookback period**: 30 trading days default, matching A3 and spec 004. A future variant could test 60d / 90d / 5d if empirical work motivates; out of scope for this spec.
- **Threshold semantics**: Strictly greater than (relative-strength delta > threshold means "ticker outperformed sector by MORE than threshold"). Configurable; threshold = `None` disables; threshold < 0 rejected at config-load time. Symmetric inverse of spec 004's strictly-less-than + threshold-must-be-non-positive constraint.
- **Default mode**: `"off"`. Operators must explicitly opt-in via `bear_sector_symmetry_filter_threshold_pct = 5.0`. This mirrors A3's + spec 004's introduction patterns (also default-off until corpus validation justified flipping on).
- **Filter ordering**: A3 → Bear-sector-symmetry (this spec) → Spec 003/003.5 → Spec 004. The two bear filters fire on price conditions that are nearly disjoint by construction (A3 needs ticker DOWN absolute; spec 006 needs ticker UP relative to sector); the rare overlap case (e.g. ticker is -5% absolute AND sector is -10% — ticker outperforms a worse-down sector) is gracefully handled by spec 006's no-op-on-Hold path.
- **No interaction with paper-trading harness defaults**: The Spec 002 paper-trading harness consumes the framework's emitted ratings unchanged. If the filter is `"active"`, the harness sees Hold (and won't open a SHORT or close a long position). If `"off"` or `"shadow"`, the harness behaves identically to the no-filter baseline. Note: the harness as of 2026-05-06 does NOT short — its bearish-rating handling is "skip / don't add long" — so the filter's primary impact is preventing the harness from CLOSING existing long positions on counter-trend bear calls. This is a desirable behavior given the +28% mean α evidence.
- **Corpus retrospective before default-on flip**: Per Constitution II + the precedent set by spec 003 + spec 004 retrospectives, after this feature lands, an offline retrospective script (`scripts/bear_sector_symmetry_retrospective.py`) MUST be created and run to measure expected Δα contribution at various thresholds. Default-on flip happens in a SEPARATE commit after that retrospective justifies it. Captured as User Story 3 (P3) above.
- **No state-log replay invariant impact**: Adding the new `state["bear_sector_symmetry"]` key is additive to the persisted state log; existing replay/analysis scripts continue to work. The `trading_graph.py:_log_state` whitelist MUST be extended to include the new key (precedent set by commits adding `contrarian_gate` and `sector_momentum`).
- **Sector ETF data via yfinance**: Same provider as the rest of the framework. yfinance failures are transparent — the filter degrades to `missing_ticker_data` or `missing_etf_data` skip and the propagate completes with the pre-filter rating intact.
- **No new code primitive for return computation**: The filter reuses the existing `tradingagents.dataflows.returns` primitive (specifically the close-to-close math via `returns_from_frames`). No new forward-α math is introduced.
