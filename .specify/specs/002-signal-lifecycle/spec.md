# Feature Specification: Signal Lifecycle (discover, evaluate, promote, retire, learn)

**Feature Branch**: `002-signal-lifecycle`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User direction: "we should develop and maintain a signal lifecycle. we should continuously explore and evaluate the information we gather. we should discover new signals in the noise. we must endlessly learn from everything we find."

## Background

Derived from `docs/SIGNAL_LIFECYCLE.md` (committed `89f72fb`), which contains the full design rationale, component sketches, metric definitions, and risk analysis. This spec re-frames that design as an executable plan with measurable acceptance criteria.

Per Constitution Principle VI (Spec Before Structural Change): introducing a Signal Registry, Computation Cache, Evaluation Harness, and automated promotion / demotion machinery is a worker-structure change that requires this spec before code.

This spec is **complementary** to `001-bots-architecture` (the deterministic aggregator that consumes signals). The two specs interlock per the sequencing in SIGNAL_LIFECYCLE.md: BOTS Phase 1 (Shadow) → SIGNAL Phase 0-2 (registry / cache / evaluation / drift) → BOTS Phase 2-3 → SIGNAL Phase 3 (data-driven reweighting) → SIGNAL Phase 4-6.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Signal Registry + Computation Cache (Priority: P1)

As a researcher, I want every signal computation persisted with provenance — signal id, fetcher version, ticker, date, value — so that signal evaluation can be re-run on the entire historical corpus without re-paying compute, and so that signal definitions can evolve while old values remain accessible.

**Why this priority**: foundational. Every other story depends on having (a) a registry that knows which signals exist + their current state, and (b) a cache that lets the harness score signals against historical outcomes without re-fetching everything.

**Independent Test**: Run a single backtest; verify each tool call writes a row to `signal_values(signal_id, ticker, date, value, raw_json, fetcher_version)`. Compare cache contents to state-log signal data — they must agree.

**Acceptance Scenarios**:

1. **Given** a backtest completes, **When** I query the cache for `(signal_id="get_vix", ticker="NVDA", date="2026-02-06")`, **Then** a single row is returned with the value computed during that backtest.
2. **Given** all 18 currently-wired signals run on a propagate, **When** the registry is queried, **Then** all 18 appear with `state="production"` and a populated `last_evaluated` timestamp.
3. **Given** a signal's fetcher logic changes, **When** a new computation runs with `fetcher_version="v2"`, **Then** old `fetcher_version="v1"` rows are still queryable but flagged as historical.

---

### User Story 2 — Evaluation Harness (Priority: P1)

As a researcher, I want a script that scores every signal in the registry against realized alpha at the signal's target horizon, producing IC, hit rate, info ratio, and quintile gradient per (signal, horizon, ticker-set). The output is a markdown report that ranks all signals and emits state transitions for any that crossed promotion / demotion thresholds.

**Why this priority**: this is the first time we'll empirically know which of our 18 production signals actually predict 21d alpha. Until this lands, we're flying on hand-tuned weights without measurement.

**Independent Test**: Run `scripts/evaluate_signals.py` against the existing 13-experiment corpus + cache; verify the report contains IC for each signal and that ≥1 signal scores IC > +0.05.

**Acceptance Scenarios**:

1. **Given** the cache contains signal values for the 13-experiment corpus, **When** `evaluate_signals.py` is run, **Then** a report at `claudedocs/signal-evaluation-<date>.md` is written containing IC, hit rate, info ratio, and quintile gradient per signal at horizons 5/10/21 days.
2. **Given** a signal's IC drops below +0.02 for 3 consecutive measurement windows, **When** the harness runs, **Then** the signal is auto-demoted from `production` to `deprecated` and a state-transition event is appended to the registry.
3. **Given** a candidate signal's IC > +0.05 on n ≥ 30 commits and its independence (max pairwise correlation) < 0.85, **When** the harness runs, **Then** the candidate is auto-promoted to `experimental`.

---

### User Story 3 — Drift Detector + Counterfactual Tester (Priority: P2)

As a researcher, I want automated detection of signals whose predictive value is degrading (rolling-IC trend declining, distribution drift via KS-statistic) and a tool that lets me ask "what if I added / removed signal X" without running new propagations.

**Why this priority**: prevents accumulation of dead-weight signals (drift detector) and enables cheap exploration of the signal space (counterfactual tester) before expensive empirical experiments.

**Independent Test**: Run `scripts/detect_signal_drift.py` against the corpus; verify it produces a report flagging at least one signal with declining rolling IC. Run `scripts/counterfactual_signal.py --add vix_30d_change` and verify it produces a report comparing alternative-aggregator outputs to actual outcomes without making new LLM calls.

**Acceptance Scenarios**:

1. **Given** a signal whose rolling 30-day IC has declined ≥0.05 over the last 60 days, **When** the drift detector runs, **Then** an alert is written to `claudedocs/signal-drift-<date>.md` with the signal id, IC trend, and suggested action.
2. **Given** a signal whose 30-day rolling IC was > +0.05 in the prior window AND < 0 in the current window, **When** the drift detector runs, **Then** an urgent "sign flip" alert is emitted.
3. **Given** I propose adding a new signal (provide name + values for all historical (ticker, date) pairs), **When** the counterfactual tester runs, **Then** it produces a report showing the alternate aggregator decisions on each historical commit + delta in mean alpha vs actual.

---

### User Story 4 — Reweight Aggregator from Metrics (Priority: P3)

As a researcher, I want the aggregator's weight per signal to be a function of measured IC + cost (lower-IC signals get less weight; high-cost signals are penalized), replacing hand-tuned constants in `BOTS_DESIGN` with data-driven values.

**Why this priority**: blocked on User Story 2 (need IC measurements first) AND on bots-architecture P2 (opt-in bots mode landed). Once both are present, the aggregator becomes self-tuning rather than statically weighted.

**Independent Test**: Run a 10-date grid with hand-tuned WEIGHTS (current bots-architecture default) vs `reweight_from_metrics(registry)`. Compare 21d OW α and rating distribution.

**Acceptance Scenarios**:

1. **Given** the registry has IC + cost metrics for all production signals, **When** `reweight_from_metrics(registry)` is called, **Then** it returns a normalized weights dict whose entries sum to 1.0 and where higher-IC signals have higher weight.
2. **Given** matched 10-date grids in fixed-weights vs reweighted-from-metrics modes, **When** ratings are compared, **Then** they agree within ±1 tier in ≥80% of cases.
3. **Given** the same matched grid, **When** 21d OW α is compared, **Then** reweighted-mode is within ±1.0pp of fixed-mode (signal-equivalent at minimum) AND ideally improves on it.
4. **Given** a signal's IC drops to negative, **When** the aggregator reweights, **Then** that signal's weight is clipped to 0 (never weight an anti-signal positively).

---

### User Story 5 — Combinatorial Signal Discovery (Priority: P3)

As a researcher, I want a discovery script that auto-generates candidate signals as cross-products, lags, and deltas of existing signals, evaluates them, and auto-promotes those passing thresholds — without me writing them by hand.

**Why this priority**: scalability. Manually specifying every interesting feature is bottlenecked by my time. Combinatorial discovery scales the search space while the evaluation harness filters out noise.

**Independent Test**: Run `scripts/discover_signals.py --type combinatorial` against existing signal cache. Verify ≥10 new candidate signals appear in the registry; verify ≥1 reaches `experimental` state after evaluation.

**Acceptance Scenarios**:

1. **Given** N production signals with values cached for ≥30 (ticker, date) pairs, **When** combinatorial discovery runs, **Then** it generates O(N²) cross-product candidates + O(N) lag candidates + O(N) delta candidates and adds each to the registry as `candidate`.
2. **Given** a discovered candidate's evaluation IC > +0.05 with n ≥ 30 and max pairwise correlation with existing signals < 0.85, **When** the next evaluation harness run completes, **Then** the candidate is auto-promoted to `experimental`.
3. **Given** the registry size approaches 200 entries, **When** discovery runs, **Then** lowest-IC `candidate` and `archived` entries are evicted to keep the registry under cap.

---

### User Story 6 — LLM-Driven Hypothesis Generation (Priority: P4)

As a researcher, I want Claude to periodically read recent state logs + their realized outcomes and propose new features I haven't thought of. Initial implementation: human-in-the-loop (Claude proposes structured candidate; I review and approve before implementation). Later: auto-implement low-risk proposals.

**Why this priority**: depends on P1-P3 working. The LLM proposals are most valuable when there's a registry to add to + an evaluation harness to score them.

**Independent Test**: Run `scripts/discover_signals.py --type llm` with a fixed sample of 10 state logs + outcomes. Verify Claude returns ≥3 structured `{name, fetcher_logic_pseudocode, expected_IC, expected_cost}` proposals.

**Acceptance Scenarios**:

1. **Given** the most recent N state logs + their realized 21d outcomes, **When** the LLM-discovery script is invoked, **Then** Claude returns structured candidate proposals with `(name, fetcher_logic, rationale, expected_IC, expected_cost)` fields.
2. **Given** a Claude-proposed signal is approved by a human, **When** the framework attempts auto-implementation, **Then** it generates the fetcher Python code, registers it as `candidate`, and queues it for evaluation.
3. **Given** an LLM-proposed signal is implemented and evaluated, **When** its IC is computed, **Then** it goes through the same promotion / demotion gates as human-authored signals (no special treatment).
4. **Given** an LLM-proposed signal fails the causality check (signal value at t correlates with realized alpha at t, NOT t+horizon — i.e., the proposal accidentally peeks into the future), **When** evaluation runs, **Then** the signal is auto-rejected and an alert is logged.

---

### User Story 7 — Meta-learning: Regime-Conditional Weights (Priority: P5)

As a researcher, I want the aggregator's weights to depend on the current market regime (high-VIX vs low-VIX vs trending vs choppy), so that signal types known to work in some regimes get heavier weight in those regimes.

**Why this priority**: requires substantial corpus (n ≥ 100 commits stratified by regime). Likely the most valuable improvement long-term, but blocked on having enough data to stratify meaningfully.

**Independent Test**: Build a regime → weights lookup table from historical IC stratified by VIX level. Compare regime-conditional vs flat weighting on a holdout set of experiments.

**Acceptance Scenarios**:

1. **Given** the corpus contains ≥100 commits across both high-VIX and low-VIX regimes, **When** meta-learning runs, **Then** it produces a `regime_weights.json` mapping `(regime, signal_type) → weight` for at least 4 distinct regimes.
2. **Given** matched 10-date grid runs in flat-weight vs regime-conditional-weight modes, **When** 21d OW α is compared, **Then** regime-conditional mode shows ≥0.5pp lift over flat mode on the holdout subset.
3. **Given** a runtime call to the aggregator, **When** the current regime is determined (via VIX + trend), **Then** the weights from `regime_weights[regime]` are used; falls back to flat weights if regime is novel / unknown.

---

### Edge Cases

- **Cache miss for a (signal, ticker, date) combination**: evaluation harness skips that data point with a warning; never extrapolates a value.
- **Signal fetcher_version changes mid-corpus**: harness uses the latest version's values for all evaluations; old-version values remain queryable but ignored for production scoring.
- **All signals abstain on a propagate**: aggregator emits Hold with `confidence=0`; logged as a distinct outcome ("no signal data") rather than treated as neutral conviction.
- **Registry corruption / append failure**: registry is append-only JSONL; corruption only affects reads after the failure point — recoverable by truncating to last valid event.
- **Drift detector flags a signal that's actually still useful (false positive)**: human review window of 1 measurement cycle before the soft-alert escalates to demotion. Manual override always available.
- **LLM proposes a signal that requires a vendor we don't have access to** (e.g., a Bloomberg field): proposal gets flagged "needs_external_vendor" and remains in `candidate` state without auto-implementation.
- **Combinatorial discovery generates a signal that's mathematically degenerate** (e.g., `signal_X / signal_X` always returns 1): pre-filter via variance check; degenerate signals never reach evaluation.
- **Counterfactual tester run on a hypothetical "remove all signals" config**: aggregator returns the all-Hold default; tester reports this as the floor case.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist a `SignalDefinition` per signal in an append-only registry at `~/.tradingagents/signals/registry.jsonl`, with fields: `signal_id`, `name`, `fetcher` (dotted path), `inputs`, `output_type`, `horizon_days`, `introduced`, `state`, `state_history`, `metrics`, `weight`.
- **FR-002**: System MUST cache every signal computation in `~/.tradingagents/signals/cache.db` (SQLite) with schema: `signal_values(signal_id, ticker, date, value, raw_json, computed_at, fetcher_version)`.
- **FR-003**: Every analyst tool call invoked during a backtest MUST write its computed value to the cache, transparently (without changing the tool's return value or breaking existing analyst behavior).
- **FR-004**: System MUST provide `scripts/evaluate_signals.py` that reads cache + experiment outcomes, computes IC/hit-rate/info-ratio/quintile-gradient per signal at multiple horizons, and writes a markdown report.
- **FR-005**: Evaluation harness MUST emit state-transition events (Candidate → Experimental → Production → Deprecated → Archived) per the criteria in `docs/SIGNAL_LIFECYCLE.md` "Signal lifecycle states" table.
- **FR-006**: System MUST provide `scripts/detect_signal_drift.py` that detects rolling-IC degradation (≥0.05 decline over 60d) and KS-distribution drift (>0.2 vs historical), writing alerts.
- **FR-007**: System MUST provide `scripts/counterfactual_signal.py` that, given a hypothetical signal addition or removal, recomputes aggregator decisions over historical corpus and reports the alpha delta — without making new LLM calls.
- **FR-008**: System MUST provide `reweight_from_metrics(registry)` callable by the bots-architecture aggregator, producing normalized weights as `IC / (1 + cost_penalty)` clipped to ≥0.
- **FR-009**: System MUST provide `scripts/discover_signals.py` with `--type combinatorial` mode generating cross-products, lags, and deltas of existing production signals, registering each as `candidate`.
- **FR-010**: System MUST provide `scripts/discover_signals.py --type llm` mode that pulls recent state logs + outcomes, asks Claude for structured candidate proposals, and either queues them for human review or auto-implements low-risk proposals (configurable via `config["llm_discovery_auto_implement"] = bool`).
- **FR-011**: System MUST validate every new signal against a causality test: signal value at `t` must NOT correlate with realized alpha at `t` (only with `t+horizon`). Failures are auto-rejected and logged.
- **FR-012**: System MUST cap registry size at `MAX_REGISTRY_SIZE` (default 200); when exceeded, lowest-IC `candidate` and `archived` entries are evicted with the eviction logged.
- **FR-013**: System MUST support regime-conditional weighting via `~/.tradingagents/signals/regime_weights.json`. Aggregator looks up the current regime (computed from VIX + sector trend) and applies that regime's weights; falls back to flat weights if regime is novel.
- **FR-014**: All registry mutations (state transitions, weight updates, cache writes) MUST be transactional — either fully complete or fully rolled back. Concurrent backtests MUST not corrupt the registry.
- **FR-015**: Backwards compatibility — none of FR-001..FR-014 may break existing analyst tool behavior or the prose-mode pipeline. The registry + cache are pure additions until reweighting (FR-008) is opted into.

### Key Entities

- **SignalDefinition**: Registry entry per signal. Fields per FR-001.
- **SignalMetrics**: IC, hit rate, info ratio, quintile gradient, rolling IC trend, distribution drift KS, max pairwise correlation, marginal IC, cost per call, coverage. Updated each evaluation.
- **StateTransition**: Append-only event. Fields: `timestamp`, `signal_id`, `from_state`, `to_state`, `reason`, `metric_snapshot`.
- **CachedSignalValue**: Per (signal, ticker, date, fetcher_version) row. The atomic unit of historical signal data.
- **EvaluationReport**: Markdown output of `evaluate_signals.py`. Includes per-signal IC table, transitions emitted, drift warnings, recommended next-discovery directions.
- **CounterfactualReport**: Markdown output of `counterfactual_signal.py`. Includes per-(ticker, date) decision delta, aggregate alpha delta, signal-importance attribution.
- **RegimeWeights**: JSON mapping `(regime_id, signal_type) → weight`. Regime IDs: `low_vix_bull`, `low_vix_bear`, `high_vix_bull`, `high_vix_bear`, `transition`. (Five initial regimes; expandable.)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Phase 0 (P1 registry/cache) — All 18 currently-wired signals registered with `state=production`. After 5 backtest propagates, the cache contains values for ≥18×5=90 (signal, ticker, date) tuples. No production behavior change.
- **SC-002**: Phase 1 (P1 evaluation) — First evaluation report shows IC for every signal at horizons 5/10/21d. ≥3 signals score IC > +0.05 (otherwise current 18-signal set has no measurable predictive value, which itself is a publishable finding).
- **SC-003**: Phase 2 (P2 drift) — Drift detector successfully flags ≥1 signal whose IC has degraded over corpus history. Counterfactual tester runs in ≤30s for any single-signal add/remove proposal.
- **SC-004**: Phase 3 (P3 reweight) — Data-driven reweighting matches or beats hand-tuned weights on holdout (within ±1pp at 21d OW α). Anti-signals (negative IC) are correctly clipped to 0 weight.
- **SC-005**: Phase 4 (P3 combinatorial discovery) — At least 5 combinatorial signals reach `experimental` state after auto-evaluation; ≥1 reaches `production`. False-positive rate (signals that pass thresholds but degrade within 1 quarter) ≤30%.
- **SC-006**: Phase 5 (P4 LLM discovery) — Claude proposes ≥10 candidates; ≥2 reach `experimental`; ≥1 reaches `production`. Causality-check rejection rate is non-zero (proves the check is firing on at least some bad proposals).
- **SC-007**: Phase 6 (P5 regime-conditional) — Regime-conditional weights show ≥0.5pp lift over flat weights on holdout. Regime classifier returns a known regime in ≥90% of cases (≤10% novel-regime fallback rate).
- **SC-008**: Total dev-time cost across all phases ≤ 8 weeks of focused work; LLM-spend cost ≤ $250 (Phase 5 only — other phases are dev-only and operate on existing data).
- **SC-009**: No production regression — prose-mode (default, current behavior) MUST be identical to pre-spec behavior on a regression test of 5 fixed (ticker, date) pairs (same as `001-bots-architecture` SC-008).
- **SC-010**: Quarterly review (after Phase 7 ongoing loop is live) — measurable signal turnover: at least 1 promotion, 1 demotion, and 1 archival per quarter, demonstrating the system is actively learning rather than static.

## Assumptions

- The current 18 signals are a sufficient starting basis; the lifecycle should empirically validate or invalidate that, but it's not assumed wrong upfront.
- IC at the 21d horizon is the primary success metric (per RESEARCH_FINDINGS, 21d is where the framework shows real signal). 5d and 10d are tracked but secondary.
- Initial regime classification is coarse (5 regimes via VIX + trend); expanding to finer-grained regimes is a follow-on enhancement once Phase 6 lands.
- LLM-discovered signals will mostly be redundant or low-value in early iterations; the value emerges over time as Claude observes more outcomes. Initial value should be measured pessimistically.
- Storage costs are negligible — registry + cache for current corpus ~10MB, growing linearly with experiments. No cloud storage needed; local SQLite + JSONL is sufficient indefinitely.
- The causality check (signal at t correlates with alpha at t+horizon, not at t) catches most look-ahead bias but not all subtle leakage. Manual review still expected for novel proposals.
- Phases can be developed in parallel where dependencies permit (e.g., drift detector can be developed alongside evaluation harness once registry exists).

## Out of Scope

- **Replacing the analyst layer with pure ML models**: signals still come from analyst tool calls (which still call LLMs for prose reports). Lifecycle is about measuring + weighting those signals, not generating them via non-LLM means.
- **Cross-experiment caching beyond signal values**: state logs (full propagate transcripts) are NOT cached in the signal cache — that's the existing state log system at `~/.tradingagents/logs/`.
- **Distributed registry / multi-machine consistency**: registry is single-node SQLite + JSONL. Multi-machine sync is out of scope.
- **Real-time streaming evaluation**: harness runs on demand or via cron, not continuously. Streaming is out of scope.
- **Non-financial signal sources**: macro / sentiment / fundamental signals fit. Sports betting features, weather data, etc. are out of scope (fits a separate "substrate exploration" effort per ROADMAP Phase D).
- **Alternative aggregation methods beyond linear weighted sum**: nonlinear / hierarchical / conditional aggregation is interesting but out of scope for this spec. Phase 6 regime-conditional is the only nonlinearity included.
- **Adversarial robustness** (signals that work well in backtests but fail in production due to overfitting): partially addressed via causality check + holdout testing, but full robustness analysis is out of scope.

## Dependencies

- **Constitution v1.1.0** — Principles II (one experiment per change), III ($30 / $250 lifetime ceiling), VI (this spec exists), VII (calibrated abstention; lifecycle measures whether the abstention claim holds via per-signal IC).
- **`.specify/specs/001-bots-architecture/spec.md`** — must reach Phase 1 (Shadow Aggregator) before this spec's Phase 0 (Registry+Cache) is useful, because Signal flow depends on that schema. Must reach Phase 2 (opt-in bots mode) before this spec's Phase 3 (reweight aggregator) lands.
- **`tradingagents/dataflows/macro.py`** + **`tradingagents/dataflows/y_finance.py`** + 18 wired signals (committed `171ea2b`) — the initial production signal set.
- **`tradingagents/agents/utils/structured.py`** — existing structured-output bind + free-text fallback. LLM-discovery proposals reuse this pattern.
- **`scripts/horizon_sweep.py`** — pattern reused for the evaluation harness's per-bucket-α computation.
- **`scripts/identify_hold_extremes.py`** — pattern reused for surfacing degraded signals to humans.

## Related Artifacts

- `docs/SIGNAL_LIFECYCLE.md` — design doc with component sketches, metric definitions, phased rollout, risk table
- `docs/SIGNALS.md` — current signal inventory (would become auto-generated from registry once Phase 0 lands)
- `docs/BOTS_DESIGN.md` — downstream consumer of signals; this spec's reweighting plugs into bots-architecture aggregator
- `.specify/specs/001-bots-architecture/spec.md` — paired structural-change spec with explicit sequencing
- `RESEARCH_FINDINGS.md` — existing empirical context (Constitution VII, 21d signal claim) that this lifecycle will empirically validate or invalidate
- `ROADMAP.md` — Phase C (operationalize) hosts both this spec and bots-architecture

## Next Steps

Per spec-kit workflow:

1. `/speckit.clarify` — resolve open questions:
   - Final promotion thresholds (current proposal: IC ≥ +0.05, n ≥ 30, independence ≥ 0.3)
   - LLM discovery cadence (monthly? after each batch of N propagates?)
   - Initial regime taxonomy (5 regimes proposed; could refine before code)
2. `/speckit.plan` — generate implementation plan with file changes per phase
3. `/speckit.tasks` — actionable checklist
4. `/speckit.implement` — execute or do by hand against tasks.md
5. `/speckit.analyze` — post-mortem after each phase

Recommended sequencing per ROADMAP and per dependency on `001-bots-architecture`:

| Order | What | Estimated time |
|---|---|---|
| 1 | bots-architecture Phase 1 (Shadow Aggregator) | 1-2 days |
| 2 | this spec Phase 0 (Registry + Cache) | 3-4 days |
| 3 | this spec Phase 1 (Evaluation Harness) | 3-4 days |
| 4 | this spec Phase 2 (Drift + Counterfactual) | 3-4 days |
| 5 | bots-architecture Phase 2-3 (Opt-in mode + shortcuts) | 1-2 weeks |
| 6 | this spec Phase 3 (Reweight from Metrics) | 2-3 days |
| 7 | this spec Phase 4 (Combinatorial Discovery) | 1 week |
| 8 | this spec Phase 5 (LLM-Driven Discovery) | 1 week |
| 9 | this spec Phase 6 (Regime-Conditional Weights) | 1-2 weeks |
| 10 | this spec Phase 7 (Continuous Loop — ongoing) | continuous |

Total to Phase 9 (full system): ~7-9 weeks of focused work.
