# Feature Specification: WC-10 Continuous Scalar Rating

**Feature Branch**: `108-wc-10-continuous-scalar-rating`
**Created**: 2026-05-08
**Status**: Draft
**Input**: User description (excerpted): "WC-10 Continuous Scalar Rating — Tier 2 experiment to test the categorical-bottleneck hypothesis. Replaces the framework's 5-tier categorical PortfolioRating enum with a continuous scalar in [-1, +1] (signed conviction magnitude). Default-OFF (operator opts in via PARAMS.json)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator runs WC-10 pilot to test categorical-bottleneck hypothesis (Priority: P1)

An operator wants to test whether the framework's well-documented mode collapse to Hold (Constitution VII Calibrated Abstention) is partially driven by the 5-tier categorical rating scale forcing discrete commitment. The operator opts WC-10 active via PARAMS.json (`wc_10_enabled=True`) on a 20-propagate grid (10 dates × 2 tickers — NVDA + AAPL); the framework outputs continuous scalar ratings in `[-1, +1]` instead of 5-tier categorical. Operator analyzes the rating distribution to determine which of 3 falsifiable predictions empirically holds.

**Why this priority**: This is the core feature. The empirical falsification test is what makes WC-10 a worthwhile experiment.

**Independent Test**: Run `propagate("NVDA", "2026-04-30")` with `wc_10_enabled=True`. Verify the final state contains a numeric rating in `[-1, +1]`. Compare output distribution to a baseline run with `wc_10_enabled=False` on the same date.

**Acceptance Scenarios**:

1. **Given** `wc_10_enabled=True` and `wc_10_filter_mode="bypass"`, **When** the operator runs propagate on a (ticker, date) pair, **Then** the framework's `final_trade_decision` contains a numeric rating in [-1, +1] AND no filter from the chain (A3, spec 003, 003.5, 004, 006, 007, 008, X-1) executes.
2. **Given** `wc_10_enabled=False` (default), **When** the operator runs propagate, **Then** the framework behaves identically to the current 5-tier baseline.
3. **Given** the 20-propagate v1 pilot grid completed with WC-10 enabled, **When** the operator analyzes the resulting CSV, **Then** at least one of the 3 falsifiable predictions (NULL / ALT-A / ALT-B) is empirically distinguishable from the others.

---

### User Story 2 - Operator opts out for zero-overhead default (Priority: P1)

An operator who wants no WC-10 behavior in their production daily_signals workflow leaves `wc_10_enabled=False` (the default). The framework's existing 5-tier categorical rating behavior is fully preserved.

**Why this priority**: Backward compatibility is non-negotiable.

**Independent Test**: Run `propagate("NVDA", "2026-04-30")` with default config. Verify state log shape is byte-identical to a pre-WC-10 baseline. Verify all 9 filters execute as before.

**Acceptance Scenarios**:

1. **Given** `wc_10_enabled=False`, **When** propagate runs, **Then** the rating field is a 5-tier categorical string.
2. **Given** `wc_10_enabled=False`, **When** state log is written, **Then** no new top-level `wc_10_*` keys appear.
3. **Given** `wc_10_enabled=False`, **When** propagate runs, **Then** all 9 production filters execute per the FR-012 chain ordering.

---

### User Story 3 - Operator bins continuous scalar to 5-tier ex-post for analysis (Priority: P2)

An operator running the WC-10 pilot wants to compare the continuous-scalar distribution to the existing 5-tier baseline corpus. The framework provides `bin_scalar_to_tier()` as a pure function.

**Why this priority**: SC-006 (5-tier baseline comparison) requires this binning.

**Independent Test**: Pure-function tests at boundary thresholds: `bin_scalar_to_tier(0.65)` → "Buy"; `bin_scalar_to_tier(-0.6)` → "Sell" (boundary).

**Acceptance Scenarios**:

1. **Given** default thresholds `(-0.6, -0.2, +0.2, +0.6)`, **When** `bin_scalar_to_tier(0.7)` is called, **Then** the result is "Buy".
2. **Given** the same thresholds, **When** `bin_scalar_to_tier(-0.6)` is called, **Then** the result is "Sell" (boundary semantics: `<=` lands in lower bin).
3. **Given** custom thresholds via `wc_10_bin_thresholds`, **When** the function is called, **Then** the bin assignment uses the custom thresholds.

---

### Edge Cases

- **Rating exactly at threshold boundary**: bin function uses `<=` semantics (lower bin claims the boundary).
- **Scalar rating outside [-1, +1]**: Pydantic validation rejects at LLM-output time.
- **Bin thresholds out of order or duplicated**: config-load-time error.
- **WC-10 enabled but `wc_10_filter_mode="passthrough"`**: NOT supported in v1; raises clear error or silently downgrades to bypass with warning.
- **Memory log entry with WC-10 enabled**: bin scalar to 5-tier when writing memory log entry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add 3 new TradingAgentsConfig keys: `wc_10_enabled` (bool, default False), `wc_10_filter_mode` (Literal["bypass", "passthrough"], default "bypass"), `wc_10_bin_thresholds` (tuple of 4 floats, default (-0.6, -0.2, +0.2, +0.6)).
- **FR-002**: System MUST modify `PortfolioDecision.rating` to accept a continuous scalar in [-1, +1] when `wc_10_enabled=True`; existing 5-tier `PortfolioRating` enum behavior is preserved when `wc_10_enabled=False`.
- **FR-003**: System MUST extract the scalar rating from the LLM output via SignalProcessor when `wc_10_enabled=True`; existing 5-tier regex extractor remains for the default-off path.
- **FR-004**: System MUST provide `bin_scalar_to_tier(rating: float, thresholds: tuple[float, float, float, float] | None = None) -> str` as a pure function with `<=` boundary semantics.
- **FR-005**: When `wc_10_filter_mode="bypass"` AND `wc_10_enabled=True`, system MUST skip the entire 9-filter PM chain.
- **FR-006**: System MUST preserve existing 5-tier behavior when `wc_10_enabled=False`.
- **FR-007**: System MUST persist WC-10 state in the state log when `wc_10_enabled=True`: scalar rating value, `wc_10_filter_mode`, `wc_10_bin_thresholds` snapshot at fire time.
- **FR-008**: System MUST gracefully refuse to run with invalid `wc_10_bin_thresholds` (out of order, duplicates, outside [-1, +1]).

### Key Entities *(include if feature involves data)*

- **Continuous scalar rating**: a `float` in [-1, +1]. -1 = max bearish; 0 = balanced/Hold-equivalent; +1 = max bullish. Values express partial confidence.
- **5-tier bin function output**: a `str` in {Buy, Overweight, Hold, Underweight, Sell} computed deterministically via configurable thresholds.
- **3 new TradingAgentsConfig keys**: `wc_10_enabled` (bool), `wc_10_filter_mode` (Literal[bypass/passthrough]), `wc_10_bin_thresholds` (tuple[float, float, float, float]).
- **State log WC-10 annotation**: `state["wc_10"]` sub-dict with `rating_scalar`, `filter_mode`, `bin_thresholds_snapshot` fields (only when enabled).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Schema correctness)**: When `wc_10_enabled=True`, `final_state["final_trade_decision"]` contains a numeric rating in `[-1, +1]`. Verified by ~3 unit tests covering boundary + interior values.
- **SC-002 (Bin function deterministic)**: `bin_scalar_to_tier()` is a pure function with deterministic bin assignment. Verified by parametrized test over the 4 boundary thresholds.
- **SC-003 (Default-off integrity)**: When `wc_10_enabled=False`, framework behavior is identical to current 5-tier baseline. Verified by integration test comparing state log shapes.
- **SC-004 (Filter-bypass mode integrity)**: When `wc_10_filter_mode="bypass"` AND `wc_10_enabled=True`, NO filter from the 9-chain executes. Verified by integration test asserting filter mocks NOT called.
- **SC-005 (Empirical pilot run)**: 10 dates × 2 tickers (NVDA + AAPL) v1 pilot completes; rating distribution captured; 3 headline metrics reported: (a) fraction of |rating| > 0.2 (= committed); (b) signed-rating × 21d-forward-α correlation; (c) bin-ex-post-to-5-tier and compare bucket means to existing 5-tier baseline corpus.
- **SC-006 (Comparison to 5-tier baseline)**: Same (date, ticker) pairs run with `wc_10_enabled=False` for direct comparison. ~$8 additional cost; total v1 ~$16.
- **SC-007 (Falsification check)**: At least ONE of the 3 hypothesis predictions (NULL / ALT-A / ALT-B) MUST be empirically distinguishable post-run. INCONCLUSIVE is permitted as a valid outcome under Principle IV.

## Assumptions

- **5-tier baseline corpus is comparable**: existing 65-run corpus uses the 5-tier `PortfolioRating` enum; `bin_scalar_to_tier()` with default thresholds maps continuous scalar back for direct comparison.
- **NVDA + AAPL are representative**: both have rich existing baseline corpora.
- **10-date grid is sufficient for falsification**: n=20 consistent with prior Tier 2-style experiments.
- **Filter-bypass mode preserves experiment information value**: cleanest way to test schema-only intervention.
- **PARAMS.json opt-in is the correct mechanism**: consistent with Spec 003/004/006/007/008/X-1 precedent.
- **AgentState TypedDict requires `wc_10` field declaration**: per spec 003 silent-drop bug history.

## Constitution adherence

This spec satisfies:

- **Principle II (One Experiment Per Change)**: SINGLE intervention — schema 5-tier → continuous scalar. Filter ablation is consequence, not separate intervention.
- **Principle III (Stay Cheap)**: T2 ≤$30; total v1 ~$16. Default-off prevents accidental cost.
- **Principle IV (No Production Claims)**: Negative result (NULL or INCONCLUSIVE) is a valid deliverable.
- **Principle VI (Spec Before Structural Change)**: this spec + subsequent spec-kit phases provide the discipline.
- **Principle VII (Calibrated Abstention)**: WC-10 directly tests whether the abstention is genuinely calibrated vs categorical-bottleneck-induced. Any result is valid evidence under VII.

## Dependencies

- `tradingagents.agents.schemas.PortfolioDecision` — schema change scope
- `tradingagents.graph.signal_processing.SignalProcessor` — scalar-aware extractor when enabled
- `tradingagents.agents.managers.portfolio_manager.portfolio_manager_node` — bypass-mode branch
- `tradingagents.default_config.TradingAgentsConfig` — 3 new keys
- `tradingagents.agents.utils.agent_states.AgentState` — new `wc_10` field

No new external dependencies.

## Out of scope (v1)

- 3-tier Trader rating (still Buy/Hold/Sell — natural ternary; WC-10 is PM-only)
- Memory log entry rating (still 5-tier; bin via `bin_scalar_to_tier()` when writing)
- Bin threshold tuning study (defer to v2 if v1 surfaces interesting results)
- Filter-passthrough mode (`wc_10_filter_mode="passthrough"` — defer; v1 is bypass-only)
- Multi-ticker test grid expansion (v1 is NVDA + AAPL only)
- CLI flag (operator opts in via PARAMS.json per existing precedent)

## Sibling docs

- `claudedocs/wc-10-continuous-scalar-rating-feature-description-2026-05-08.md` — PR #104 feature description draft
- `claudedocs/experiment-md-tier-2-3-status-2026-05-08.md` — PR #97 Tier 2/3 survey
- `docs/EXPERIMENT.md` — original WC-10 brainstorm
- `RESEARCH_FINDINGS.md` — Constitution VII thread + 5-tier mode collapse evidence
- `experiments/2026-05-03-003-single-call-baseline-nvda/` — architecturally adjacent precedent
- `specs/091-c4-institutional-rotation/` — Spec X-1 spec-kit 6-PR-bundle precedent
