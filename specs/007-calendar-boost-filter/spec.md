# Feature Specification: Hybrid C — Calendar-Boosted Forward-Catalyst Filter (Spec 008)

**Feature Branch**: `007-calendar-boost-filter`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "Hybrid C — Calendar-Boosted Forward-Catalyst Filter (Spec 008). FIRST hybrid filter combining the validated Spec 007 Class 3 LLM-extracted scores with Class 6 calendar features (days-to-next-earnings via yfinance.earnings_dates) — a calendar-aware enhancement of the bull-side branch of the spec 007 forward-catalyst-aware contrarian gate."

> **Numbering note**: This feature is *logical* Spec 008 (the project's 8th formal spec). The on-disk feature directory is `specs/007-calendar-boost-filter/` per spec-kit's auto-incrementing sequential numbering (which counts from `001-experiments-scaffolding`). Throughout this document, "Spec 008" refers to the logical feature; the directory prefix is mechanical.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator opts into calendar-boost layer for bull-only filtering (Priority: P1)

An operator running the Spec 007 forward-catalyst filter reads the Hybrid C retrospective findings (`claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`) which show that combining the Class 3 LLM scores with a 14-day earnings-proximity boost catches an additional ~+3.35pp of bull-side net Δα the underlying spec 007 filter alone misses. The operator sets `hybrid_c_calendar_boost_enabled = True` in their PARAMS.json (with default window=14d / magnitude=0.5), runs `python scripts/daily_signals.py --tickers tickers.txt`, and observes that on bull-side commits where the underlying `bull_case_priced_in` score is borderline-below-threshold (e.g., 0.45) AND the ticker has earnings within 14 days, the effective score crosses the threshold and the rating gets downgraded to Hold.

**Why this priority**: This is the entire feature. Without the operator-facing opt-in path, the empirical findings are unrealized.

**Independent Test**: Operator can be confident the feature works by (a) running daily_signals with the boost enabled, (b) verifying state logs show the four new annotation fields (`days_to_earnings`, `calendar_boost`, `effective_bull_score`, `effective_bear_score`), (c) confirming at least one historical date in the spec 007 retrospective cohort that previously kept its Buy/Overweight rating now downgrades to Hold under the boost.

**Acceptance Scenarios**:

1. **Given** Spec 007 active + Hybrid C enabled (window=14, magnitude=0.5) + a ticker with `bull_case_priced_in=0.50` + earnings in 7 days, **When** the PM stage processes a Buy rating, **Then** the effective score = `0.50 × (1 + 0.5 × (1 - 7/14)) = 0.50 × 1.25 = 0.625` which exceeds `bull_threshold=0.60`, so the filter fires and the rating downgrades to Hold.
2. **Given** the same setup but earnings are 14+ days away, **When** the PM stage processes the same Buy rating, **Then** boost = 0, effective = base = 0.50 ≤ 0.60, so the filter does NOT fire and the rating stays Buy.
3. **Given** Spec 007 active + Hybrid C enabled + a ticker for which `yfinance.Ticker(t).earnings_dates` raises an exception, **When** the PM stage processes a Buy rating, **Then** `days_to_earnings = None`, boost = 0, effective = base, the filter behaves identically to spec 007 baseline, and no error is raised.

---

### User Story 2 - Backward-compatibility for operators who haven't opted in (Priority: P1)

An operator who has not enabled the boost continues running their existing Spec 007 setup unchanged. Their state logs continue to be byte-equivalent to pre-Spec-008 logs (modulo unrelated changes), and their daily_signals output, paper_trade harness, and analyze_backtest results are unaffected.

**Why this priority**: Same priority as US1 because backward-compat is the gate for landing the feature without disrupting validated baseline measurements.

**Independent Test**: Compare a state log produced after Spec 008 lands (with default `hybrid_c_calendar_boost_enabled=False`) against the spec 007 baseline state log shape — the four new annotation keys MUST be absent, and all previously-present spec 007 keys MUST be byte-equivalent.

**Acceptance Scenarios**:

1. **Given** Spec 008 code is merged + operator has NOT modified their config, **When** they run `propagate(ticker, date)`, **Then** `state["forward_catalyst"]` contains exactly the spec 007 fields (no new keys added).
2. **Given** a pytest run after Spec 008 lands, **When** the existing spec 007 PM-integration tests execute, **Then** all spec 007 tests pass without modification.

---

### User Story 3 - Researcher attributes alpha specifically to the boost layer (Priority: P2)

A researcher analyzing the Spec 008 corpus needs to attribute alpha changes to the boost layer (versus the underlying Spec 007 filter). They run `analyze_backtest.py` over a results.csv produced with `hybrid_c_calendar_boost_enabled=True`, and the per-row `state["forward_catalyst"]` annotations let them filter to the subset where `calendar_boost > 0` (boost actually fired), separating "boost-attributable" downgrades from "spec 007 baseline" downgrades.

**Why this priority**: Attribution is required for the post-landing live-mode ablation (SC-009) but isn't blocking for first-merge.

**Independent Test**: Run a small replay (e.g., 5 propagates) with the boost enabled, then verify the resulting CSV contains ≥1 row where `state["forward_catalyst"]["calendar_boost"] > 0` AND `state["forward_catalyst"]["effective_bull_score"] > state["forward_catalyst"]["bull_case_priced_in"]`.

**Acceptance Scenarios**:

1. **Given** a results.csv from a `daily_signals.py` run with the boost enabled across earnings-proximate tickers, **When** the researcher filters rows by `calendar_boost > 0`, **Then** they can compute alpha statistics specifically over boost-driven downgrades.

---

### Edge Cases

- **What happens when the ticker has no earnings calendar (e.g., ETF, new IPO)?** `yfinance.Ticker(t).earnings_dates` returns empty or raises; the helper catches and returns `days_to_earnings = None`; boost = 0; effective = base; filter behaves identically to spec 007 baseline. No error raised, no warning logged at INFO level (debug-level acceptable).
- **What happens when the ticker has earnings on the trade date itself?** `days_to_earnings = 0`; boost = 1.0; effective = base × (1 + magnitude). At magnitude=0.5: effective = base × 1.5. Clamped to [0, 1.0] via min().
- **What happens when the trade_date is malformed/unparseable?** `_days_to_next_earnings` returns None; boost = 0; effective = base. Same as no-calendar-data path.
- **What happens when boost would push effective above 1.0?** Clamped: `effective = min(1.0, base × (1 + magnitude × boost))`. At base=0.95 + magnitude=0.5 + boost=1.0: raw = 1.425, clamped to 1.0.
- **What happens when Spec 007 itself is disabled (mode="off")?** Hybrid C does nothing. The boost layer is structurally INSIDE Spec 007's score computation; if Spec 007 doesn't run, neither does the boost. State annotation fields are not added.
- **What happens when the same ticker is queried twice in one process?** LRU cache returns cached `earnings_dates`; no second yfinance HTTP call. Verified by mock-call-count test.
- **What happens when Spec 007 is in shadow mode?** Boost still applies to the score computation; the spec 007 fire decision (which is observed-only in shadow) uses the boosted score. `would_fire_bull` annotations reflect the boosted-score decision.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Boost factor formula)**: System MUST compute calendar boost factor as `max(0, 1 - days_to_next_earnings / boost_window)` when `hybrid_c_calendar_boost_enabled=True`. Result is in `[0, 1]`. When `days_to_earnings >= boost_window` OR `days_to_earnings is None` OR `days_to_earnings < 0`, boost MUST equal 0.
- **FR-002 (Effective score formula)**: System MUST compute `effective_bull_score = min(1.0, bull_case_priced_in × (1 + hybrid_c_calendar_boost_magnitude × boost))`. The `min(1.0, ...)` clamp prevents the effective score from exceeding the conventional [0, 1] score range.
- **FR-003 (Decision substitution)**: System MUST use `effective_bull_score` (not `bull_case_priced_in`) in the Spec 007 bull-side fire decision when `hybrid_c_calendar_boost_enabled=True`. Comparison MUST use strict greater-than against `forward_catalyst_bull_threshold`, matching Spec 007 SC-002 boundary semantics.
- **FR-004 (Bull-only scope)**: System MUST NOT modify `bear_case_priced_in` or the bear-side fire decision. The Hybrid C retrospective showed bear-side neutral-to-negative; Spec 008 explicitly excludes bear-side enhancement.
- **FR-005 (Days-to-earnings source)**: System MUST source `days_to_next_earnings` from `yfinance.Ticker(t).earnings_dates`, returning the calendar days from `trade_date` to the next earnings date that is greater than or equal to `trade_date`. Result type: `int | None`.
- **FR-006 (LRU caching)**: System MUST cache `yfinance.Ticker(t).earnings_dates` results via an in-process LRU cache keyed by ticker, so two requests for the same ticker in a single process result in exactly one yfinance HTTP call. Cache scope is process lifetime (no persistence across runs).
- **FR-007 (Default-off launch)**: System MUST default `hybrid_c_calendar_boost_enabled` to `False`. The Hybrid C retrospective evidence is retrofit-cohort-only; live-mode ablation (SC-009) is required before any default-on flip.
- **FR-008 (Default boost window)**: When enabled, system MUST default `hybrid_c_calendar_boost_window_days` to `14` per the retrospective best-config finding (window=14d magnitude=0.5x produced +3.35pp net Δα, the maximum of the swept configs).
- **FR-009 (Default magnitude)**: When enabled, system MUST default `hybrid_c_calendar_boost_magnitude` to `0.5`. The retrospective showed magnitude is fungible within window=14d (any of {0.5, 1.0, 2.0} produced identical fire pattern); 0.5 is the most conservative choice.
- **FR-010 (yfinance failure resilience)**: System MUST gracefully degrade when `yfinance.Ticker(t).earnings_dates` raises an exception OR returns empty: `days_to_earnings = None`, `calendar_boost = 0`, `effective_bull_score = bull_case_priced_in`. The filter MUST NOT raise an exception or log at ERROR/WARNING level for this case (DEBUG level acceptable).
- **FR-011 (Backward-compat state-log shape)**: System MUST NOT add the four new annotation fields (`days_to_earnings`, `calendar_boost`, `effective_bull_score`, `effective_bear_score`) to `state["forward_catalyst"]` when `hybrid_c_calendar_boost_enabled=False`. Spec 007 baseline state logs MUST remain byte-equivalent.
- **FR-012 (State annotation completeness — enabled path)**: When `hybrid_c_calendar_boost_enabled=True`, system MUST add to `state["forward_catalyst"]` exactly four fields: `days_to_earnings: int | None`, `calendar_boost: float in [0, 1]`, `effective_bull_score: float in [0, 1.0]`, `effective_bear_score: float in [0, 1.0]` (the bear field MUST equal `bear_case_priced_in` since FR-004 prohibits bear modification).
- **FR-013 (State persistence)**: System MUST persist the four new annotation fields via the existing `_log_state` whitelist that already includes `forward_catalyst`. NO changes to `AgentState` TypedDict are required (the `forward_catalyst` key is already declared as `Annotated[dict, ...]` per spec 007).
- **FR-014 (Filter chain ordering — no change)**: System MUST NOT modify the PM hook chain ordering. Hybrid C is structurally INSIDE Spec 007's score computation, not parallel to it. The chain remains: A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 (with the boost applied to the spec 007 score input when enabled).
- **FR-015 (Zero LLM cost)**: System MUST NOT add any LLM call. Hybrid C is pure post-processing of Spec 007's already-paid LLM output plus a free yfinance HTTP fetch (LRU-cached). Per-propagate cost addition MUST be exactly $0 in LLM tokens.
- **FR-016 (No new mode dimension)**: System MUST NOT add an off/shadow/active mode setting. Hybrid C is governed purely by the boolean enable flag (FR-007); the underlying Spec 007 mode setting controls fire behavior. Adding a mode here would create N×M state-space confusion with Spec 007's own modes.

### Key Entities *(include if feature involves data)*

- **CalendarBoost**: Derived numeric value in `[0, 1]`. Function of `(days_to_next_earnings, boost_window)`. Equals `1.0` at the earnings day, decreases linearly to `0` at `boost_window+` days out. Equals `0` whenever calendar data is unavailable.
- **EffectiveScore**: Derived numeric value in `[0, 1.0]`. Function of `(base_score, calendar_boost, magnitude)`. Equals `min(1.0, base × (1 + magnitude × boost))`. Used as the spec 007 fire-decision input when the feature is enabled.
- **DaysToNextEarnings**: Calendar days (int) from `trade_date` to the next earnings date `>= trade_date`. `None` when calendar unavailable, ticker has no earnings calendar (ETFs, new IPOs), trade_date is unparseable, or yfinance fails.
- **EarningsCalendarCache**: LRU-cached map `{ticker: list[datetime]}` of sorted future earnings dates per ticker. Process-scoped (cleared on process exit). One yfinance HTTP call per unique ticker per process.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Calendar-boost firing logic)**: Synthetic-input test with `bull_case_priced_in=0.50`, `days_to_earnings=0`, `window=14`, `magnitude=0.5`, `bull_threshold=0.60` produces `effective = 0.50 × 1.5 = 0.75 > 0.60` and the filter MUST fire. Same inputs at `days_to_earnings=14` produce `boost=0`, `effective = 0.50` and the filter MUST NOT fire. Verified by ≥6 unit tests covering the boost formula corners (days=0, days=window/2, days=window, days=window+1, days=None, base=1.0+saturation).
- **SC-002 (Boost monotonicity)**: For fixed `(ticker, base_score, magnitude, window)`, `effective_score` MUST monotonically decrease (non-strictly) as `days_to_earnings` increases from `0` to `window+1`. Verified by parametrized unit test sweeping days_to_earnings ∈ {0, 1, 7, 13, 14, 15, 30}.
- **SC-003 (yfinance failure resilience)**: When `yfinance.Ticker(t).earnings_dates` raises an exception OR returns `None`/empty, `days_to_earnings` MUST be `None`, `calendar_boost` MUST be `0`, `effective_bull_score` MUST equal `bull_case_priced_in`, and the filter MUST behave identically to spec 007 baseline. Verified by mocked test with both exception and empty-result paths.
- **SC-004 (LRU cache correctness)**: Two requests for the same ticker in a single process MUST result in exactly one `yfinance.Ticker(t).earnings_dates` call. Verified by mock-call-count test asserting `mock.call_count == 1` after two same-ticker `days_to_next_earnings(t, ...)` invocations.
- **SC-005 (Default-off integrity)**: When `hybrid_c_calendar_boost_enabled=False` (the default), the helper module MUST NOT be invoked. Spec 007 state logs MUST NOT contain `days_to_earnings`, `calendar_boost`, `effective_bull_score`, or `effective_bear_score` keys in `state["forward_catalyst"]`. Verified by integration test that asserts dict-key equivalence between spec-007-baseline and spec-008-default state logs.
- **SC-006 (Boundary semantics — strict greater-than)**: When `effective_bull_score == bull_threshold` exactly (e.g., both `0.60`), the filter MUST NOT fire (matching Spec 007 SC-002). Verified by boundary unit test.
- **SC-007 (State annotation completeness)**: When the feature is enabled and applied, `state["forward_catalyst"]` MUST contain exactly the four new fields (`days_to_earnings`, `calendar_boost`, `effective_bull_score`, `effective_bear_score`) AND all the existing spec 007 fields. Verified by state-log persistence regression test.
- **SC-008 (Empirical retrospective re-validation)**: After landing, re-running `python scripts/forward_catalyst_hybrid_c_retrospective.py` with the production config MUST reproduce the +3.35pp bull-side net Δα improvement (within ±0.5pp tolerance for any minor implementation drift). The existing retrospective script becomes the post-merge regression check per the Constitution VIII v1.4.1 "spec ships its retrospective" pattern.
- **SC-009 (Live-mode ablation requirement before default-on flip)**: Before any future change flips `hybrid_c_calendar_boost_enabled` default to `True`, operators MUST run a live-mode A/B ablation (boost enabled vs disabled on the same propagates) for n ≥ 30 propagates AND verify the retrofit's +3.35pp bull-side net Δα improvement holds within ±1pp at the 21-day forward-alpha horizon. This SC is enforced procedurally — a future spec amendment must cite the ablation evidence to justify the flip.
- **SC-010 (Test count expectation)**: Spec 008 ships with ≥12 unit tests covering the helper module (boost formula edge cases + days-to-earnings + LRU cache) plus ≥4 integration tests (spec 007 with boost enabled / disabled / yfinance failure / state-log persistence). Total net-new test count: ≥16. PM-integration test count unchanged (no PM hook chain modification).
- **SC-011 (Cost discipline — Constitution III T0)**: Per-propagate LLM cost addition from Spec 008 MUST be exactly `$0` (the boost is post-processing of Spec 007's already-paid LLM call). Verified by manual smoke run with cost output captured before vs after enabling the boost — totals MUST be byte-equal.
- **SC-012 (Latency budget)**: Per-propagate latency addition from Spec 008 MUST be ≤ 250 ms p99 on cache-cold ticker (single yfinance HTTP fetch) and ≤ 5 ms on cache-warm ticker (in-memory LRU lookup). Measured by wall-clock timing the helper invocation in a smoke test.

## Assumptions

- **Spec 007 is active**: Hybrid C is an enhancement layer on Spec 007's bull-side score, not a standalone filter. If Spec 007 is in `mode="off"`, Hybrid C does nothing (FR-014 — boost is structurally inside Spec 007). The spec assumes operators considering the boost have already validated Spec 007 active mode for their use case.
- **yfinance.earnings_dates is available for the ticker universe**: For most large-cap US equities (the tested SC-003 retrospective cohort), `yfinance.Ticker(t).earnings_dates` returns a sorted list of historical + upcoming earnings. For ETFs, new IPOs, and certain international tickers, the call may return empty or raise — the FR-010 graceful-degradation path handles this transparently. No operator action required.
- **LRU cache scope is process lifetime**: Earnings calendars don't change frequently enough within a single process invocation (typically minutes to hours for batch backtests, seconds for single propagates) to warrant TTL-based eviction. The cache is cleared on process exit; subsequent runs re-fetch.
- **yfinance HTTP latency is bounded**: Single `yfinance.Ticker(t).earnings_dates` call typically completes in <500 ms over a residential broadband connection. The SC-012 250 ms p99 budget assumes typical network conditions; operators on degraded connections may exceed this without functional impact (the boost still computes correctly, just slower).
- **Days-to-earnings monotonicity reflects market-priced-in dynamic**: The retrospective hypothesis is that earnings-proximate commits are more likely to have the bull case "priced in" by the market (the LLM's `bull_case_priced_in` score is already measuring this directly, but the calendar feature adds an explicit time-decay multiplier the prose synthesis may not weight uniformly). This is the empirical motivation, not a load-bearing assumption — if the mechanism turns out to be different (e.g., earnings-proximate volatility expansion), the retrospective number still holds and the spec ships unchanged.
- **No bear-side enhancement in this spec**: Bear-side was neutral at 14d and harmful at 21d in the retrospective. A future Spec 008.5 or Spec 009 could revisit bear-side with a different boost direction (e.g., negative magnitude on bear cohort), but that requires its own retrospective + Constitution VIII gate. Out of scope for Spec 008.
- **Empirical-retrospective evidence is load-bearing**: The spec is justified by `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md` (production-config retrospective at commit `6cc7be9`). Future operators considering threshold/window/magnitude adjustments should re-run the retrospective with the new config to validate the change before flipping defaults. The retrospective script (`scripts/forward_catalyst_hybrid_c_retrospective.py`) is the gate per Constitution VIII v1.4.1.
- **Constitution VIII v1.4.0 forward-catalyst-class gate already cleared**: Discrim +11.30pp > +5pp, cohort hit 92.6% > 60%, net Δα +5.58pp > +0.5pp at the boosted threshold (all three exceed Class 3-alone baseline by meaningful margins). No new Constitution amendment is required for this spec.

## Out of Scope

- **Bear-side calendar boost** — empirically neutral at 14d and harmful at 21d; explicitly excluded per FR-004.
- **Boost windows other than 14 days as default** — sweep showed magnitude is fungible within window; window=7d showed no benefit (only 1 commit within 7d in the cohort), window=21d showed bear-side regression. Operators can override via PARAMS.json but the default is empirically grounded at 14d.
- **Magnitude tuning beyond 0.5 default** — fungible within window=14d; 0.5 is the most conservative choice, matching the retrospective best config.
- **Persisting the LRU cache across runs** — out of scope for v1; in-process cache is sufficient for the documented use cases (backtests + daily_signals). A future enhancement could add disk-cache via `~/.tradingagents/cache/earnings/` if measurement shows network is a bottleneck.
- **Default-on flip in this spec** — explicitly default-off per FR-007 + SC-009. A future spec amendment cites the live-mode ablation evidence to justify the flip.
- **TTL-based cache invalidation** — not needed for typical batch/daily-signals use; out of scope.
- **Earnings-calendar source other than yfinance** — Alpha Vantage / IEX / similar alternatives are not added in this spec. yfinance is sufficient for the documented use cases and matches the existing project data-vendor pattern.
- **State-log schema changes to AgentState TypedDict** — `state["forward_catalyst"]` is already declared as `Annotated[dict, ...]` (spec 007); the four new fields are dict additions that don't require schema changes.
- **Modifying the PM hook chain ordering** — Hybrid C is structurally inside spec 007 (FR-014); no chain step added.
