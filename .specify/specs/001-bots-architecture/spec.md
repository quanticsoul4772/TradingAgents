# Feature Specification: Bots Architecture (battlecode-style refactor)

**Feature Branch**: `001-bots-architecture`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "Apply 6 patterns from battlecode2026 ratbot6 to refactor TradingAgents agents into resource-budgeted, signal-emitting bots with deterministic aggregation."

## Background

This spec is derived from `docs/BOTS_DESIGN.md` (committed `aa96d54`), which contains the architectural rationale, diagrams, code sketches, and risk analysis. This spec re-frames that design as an executable plan with measurable acceptance criteria.

Per Constitution Principle VI (Spec Before Structural Change): refactoring the analyst → debate → synthesis → risk → PM pipeline counts as a worker-structure change and requires this spec before code.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Shadow Aggregator (Priority: P1)

As a researcher running the framework, I want each analyst to ALSO emit a structured `Signal` alongside its prose report, and I want a deterministic `aggregate(signals)` to compute a "shadow rating" logged next to the actual PM rating — without changing the production decision path.

**Why this priority**: validates the Signal schema works for all 4 analysts on real evidence, with zero risk to current behavior. Discovers ambiguities in the schema before any production change. Foundation for every subsequent story.

**Independent Test**: Run a single propagate; verify the state log contains `signals: [...]` with one entry per analyst, plus a `shadow_aggregate_decision: {rating, confidence}` field. Compare shadow rating to actual PM rating across 10 dates — they should agree on direction in ≥80% of cases.

**Acceptance Scenarios**:

1. **Given** a propagate completes successfully, **When** the state log is written, **Then** it contains a `signals` array with one Signal per selected analyst, and a `shadow_aggregate_decision` object.
2. **Given** 10 propagates over the same date grid, **When** the shadow ratings are compared to actual PM ratings, **Then** direction agreement (bull/bear/neutral) is ≥80%.
3. **Given** an analyst produces an empty or low-content report, **When** its Signal is emitted, **Then** `signal.abstain == True` and the aggregator weights it at zero.

---

### User Story 2 — Opt-in Bots Mode (Priority: P2)

As a researcher, I want a `config["framework_mode"] = "bots"` flag that routes propagate through the deterministic aggregator (skipping the LLM-based Research Manager + PM synthesis stages), so I can A/B test the bot path against the prose path on identical inputs.

**Why this priority**: only useful AFTER P1 validates the Signal schema. Enables real measurement of the bot path's calibration vs the prose path.

**Independent Test**: Run the same 10-date NVDA grid with `framework_mode=bots` and `framework_mode=prose` (current default). Compare bucket-level alpha at 21d and rating distribution.

**Acceptance Scenarios**:

1. **Given** `config["framework_mode"] = "bots"`, **When** a propagate completes, **Then** `final_trade_decision` was produced by the aggregator (no LLM call to PM/RM), and the state log records `framework_mode: bots`.
2. **Given** matched 10-date runs in bots vs prose mode, **When** ratings are compared, **Then** ≥80% agree within ±1 tier (e.g., OW vs Buy is acceptable; OW vs UW is not).
3. **Given** matched 10-date runs in bots vs prose mode, **When** 21d bucket alpha is computed for OW commits in each, **Then** the means are within ±1.0pp of each other (signal-equivalent).

---

### User Story 3 — Convergence Shortcut + Bot Budgets (Priority: P3)

As a researcher trying to reduce per-propagate cost, I want the framework to skip the bull/bear debate stage when analyst Signals already converge (3+ signals in same direction with magnitude > 0.7), and I want each bot to have a token-budget ceiling that triggers automatic abstention.

**Why this priority**: cost optimization layered on top of P2. Builds on the working aggregator + Signal schema. Quantifies the practical cost-savings claim from the design doc.

**Independent Test**: Run identical 10-date grid with shortcut+budget vs without. Compare per-propagate token spend.

**Acceptance Scenarios**:

1. **Given** 3+ analyst Signals converge bullish (each magnitude > 0.7), **When** the framework decides whether to invoke debate, **Then** the bull/bear debate is skipped and the state log records `skipped_debate: true`.
2. **Given** a bot exceeds its configured token budget mid-run, **When** the bot is invoked next, **Then** it returns `Signal(abstain=True)` and logs the reason.
3. **Given** matched 10-date runs with vs without shortcut+budget, **When** per-propagate token spend is computed, **Then** the shortcut+budget run uses ≥30% fewer tokens on propagates where shortcut fires, with overall reduction ≥15%.

---

### User Story 4 — Role Specialization (Priority: P4)

As a researcher tuning cost vs quality, I want different LLM models per bot role (e.g., MarketBot uses Haiku; FundBot uses Sonnet; NewsBot uses Opus), so I can match model strength to task complexity.

**Why this priority**: secondary optimization. Only useful once the Signal schema + aggregator path is established. Easy to revert if quality degrades.

**Independent Test**: Run identical 10-date grid with role-specialized config vs uniform config. Compare ratings + cost.

**Acceptance Scenarios**:

1. **Given** `config["bot_models"] = {"market": "claude-haiku-4-5", "fundamentals": "claude-sonnet-4-6"}`, **When** a propagate runs, **Then** each bot uses its configured model.
2. **Given** matched runs with role-specialized vs uniform config, **When** ratings are compared, **Then** rating consistency (within ±1 tier) is ≥85%.
3. **Given** the same matched runs, **When** cost is compared, **Then** the role-specialized config costs ≤80% of the uniform-Sonnet config.

---

### User Story 5 — Weight Tuning (Priority: P5)

As a researcher, I want to optimize the `WEIGHTS` in `aggregate()` against the existing experiment corpus, so the value function reflects empirical signal-quality per analyst rather than an a priori guess.

**Why this priority**: ongoing — runs after P1-P4 are stable. Requires meaningful corpus (n≥100 commits across mixed regimes) to avoid overfitting.

**Independent Test**: Run grid search over a held-out subset of historical experiments. Compare optimized weights' calibration vs the original guess.

**Acceptance Scenarios**:

1. **Given** the experiment corpus is split 70/30 train/test by date, **When** weights are optimized on train and evaluated on test, **Then** test-set OW 21d α is within ±0.3pp of train-set.
2. **Given** weight tuning produces new `WEIGHTS`, **When** they replace defaults, **Then** the change is documented in a separate experiment with HYPOTHESIS justifying the adjustment.

---

### Edge Cases

- **All analysts abstain**: aggregator returns `Hold` with `confidence=0`. Logged as a distinct outcome ("no signal") rather than treated as neutral conviction.
- **Mixed signals with low magnitudes**: aggregator's normalized direction score is < threshold, returns `Hold` with low confidence. Indistinguishable from "all abstain" in the rating but distinguishable in the audit log.
- **Pydantic structured-output fails on a bot's Signal**: same fallback as current decision agents — free-text retry, regex extraction. If still fails, `abstain=True`.
- **Convergence shortcut fires but realized α is wrong**: log this as a discriminating diagnostic. If shortcut produces wrong-direction commits at >40% rate over n≥30, raise the convergence threshold or remove the shortcut entirely.
- **Budget exhausted mid-bull-debate**: bull bot abstains; bear bot still runs. Aggregator still completes with the partial signal set.
- **Existing prose-mode users break on Signal schema introduction**: P1 is non-breaking — Signal is added alongside prose; no existing field is removed. Production behavior unchanged unless `framework_mode=bots` is set.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST emit a `Signal` object per selected analyst on every propagate, with fields `bot_id`, `direction`, `magnitude`, `horizon_days`, `key_facts`, `risks`, `abstain`, and optional `full_report`.
- **FR-002**: System MUST persist the `signals` list and `shadow_aggregate_decision` in the state log JSON alongside existing fields (P1).
- **FR-003**: When `config["framework_mode"] = "bots"`, the framework MUST route the final rating decision through `aggregate(signals)` instead of the LLM-based PM/RM stages (P2).
- **FR-004**: When `config["framework_mode"]` is unset or `"prose"`, the framework MUST behave identically to current production (P2 backwards-compat).
- **FR-005**: System MUST support a per-bot token-budget ceiling configured via `config["bot_budgets"]: dict[str, int]`. When exceeded, the bot MUST emit `Signal(abstain=True)` and log a `BudgetExceeded` warning (P3).
- **FR-006**: When `config["enable_convergence_shortcut"] = True`, the framework MUST skip the bull/bear debate stage when 3+ analyst Signals share a direction with magnitude > 0.7 (P3).
- **FR-007**: System MUST support per-bot LLM model configuration via `config["bot_models"]: dict[str, str]`. Bots without an entry use `quick_thinking_llm` (P4).
- **FR-008**: System MUST persist Signal-emitter bot identity, model used, and token spend per bot in the state log (P3, for cost analysis).
- **FR-009**: All Signals MUST validate against the Pydantic schema; failure MUST trigger free-text fallback (matching existing structured-output retry pattern in `tradingagents/agents/utils/structured.py`).
- **FR-010**: The aggregator MUST be deterministic — same Signal inputs yield same rating output (no LLM call inside `aggregate`).

### Key Entities

- **Signal**: Per-analyst structured output. Replaces (alongside) prose reports. Bridges "LLM analyst" and "deterministic aggregator." Schema in BOTS_DESIGN.md §"Signal type."
- **AggregatedDecision**: Output of `aggregate(signals)`. Contains `rating` (5-tier), `confidence` (0-1), `direction_score` (raw weighted sum), and `bots_used` (which Signals contributed non-zero weight).
- **BotBudget**: Per-bot token-spend tracker. Configured per-propagate, reservation-based usage tracking.
- **BudgetReservation**: Returned by `BotBudget.reserve(bot_id)`; bot calls `record(prompt_tokens, completion_tokens)` after each LLM call.
- **DebatePhase** (enum): Replaces implicit `current_response.startswith("Bull")` regex routing in `conditional_logic.py` with explicit state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Phase 1 (P1) — Shadow aggregator decision agrees with actual PM decision on direction in ≥80% of cases across 10-date NVDA grid. Disagreements are characterized in writeup.
- **SC-002**: Phase 2 (P2) — Bots-mode and prose-mode rating distributions match within ±1 tier in ≥80% of cases on matched 10-date grid.
- **SC-003**: Phase 2 — Bots-mode 21d OW α is within ±1.0pp of prose-mode on the same grid (signal-equivalent).
- **SC-004**: Phase 3 (P3) — Per-propagate token spend reduced by ≥15% on average across mixed runs; ≥30% reduction on propagates where convergence shortcut fires.
- **SC-005**: Phase 4 (P4) — Role-specialized config achieves ≤80% of uniform-Sonnet cost with rating consistency ≥85%.
- **SC-006**: Phase 5 (P5) — Tuned weights' test-set OW 21d α is within ±0.3pp of train-set (no overfitting).
- **SC-007**: Total dev cost across all 5 phases stays under $80 USD in LLM spend, with each individual experiment under the $30 Constitution Principle III ceiling.
- **SC-008**: No production regression — prose-mode (default) behavior MUST be identical to pre-spec behavior on a regression test of 5 fixed (ticker, date) pairs.

## Assumptions

- LLM-based analysts can produce structured output via `with_structured_output(Signal)` reliably enough that free-text fallback fires <10% of the time. (Validated on existing PortfolioDecision schema.)
- Initial `WEIGHTS` (market 0.25, news 0.20, fundamentals 0.30, sentiment 0.10, debate 0.075 each) are placeholders; Phase 5 will tune. Until tuned, decisions may differ from current PM ratings — that's expected and is what P1 measures.
- The 4 analysts each touch sufficiently different evidence that their Signals are not perfectly correlated (i.e., the weighted sum captures more information than any single Signal). If correlations turn out >0.9 across analysts, the weighted sum collapses to a single Signal and most architectural benefit is lost.
- The convergence shortcut's 3+ signals @ magnitude>0.7 threshold is a starting point; will be retuned after Phase 3 measurement.
- Per-bot token budgets are configurable; Phase 3 will discover reasonable defaults from observed spend distribution.
- Phase 1-4 implementation can be done without additional spec amendment. Phase 5 (weight tuning) may require its own per-experiment HYPOTHESIS justifying the adjustment.

## Out of Scope

- **Replacing LLMs with rule-based bots**: bots still call LLMs. Structured signaling is about output shape, not reasoning method.
- **Removing the existing prose pipeline**: prose-mode is kept indefinitely as fallback + audit trail. P2 adds bots-mode opt-in; never removes prose-mode.
- **Cross-bot communication during analysis**: each bot is independent (no chatter between analysts mid-analysis). The "debate" is the only inter-bot communication and is optional via convergence shortcut.
- **Online learning**: weights are static within a propagate; updated only between experiments via Phase 5.
- **Replacing the Risk Debate stage**: out of scope for this spec. Risk debate continues to run on bots-mode output. Future spec could extend bot architecture to risk debaters.

## Dependencies

- Constitution v1.1.0 — Principles II (one experiment per change), III ($30 ceiling per experiment), VI (this spec exists), VII (calibrated abstention; aligns with `Signal.abstain`).
- `tradingagents/agents/utils/structured.py` — existing structured-output bind + free-text fallback. Bots reuse this pattern.
- `tradingagents/agents/schemas.py` — existing `PortfolioRating` enum (5-tier) reused.
- `tradingagents/graph/setup.py` — needs modification in P2 to route via aggregator when `framework_mode=bots`.
- `tradingagents/graph/conditional_logic.py` — needs modification in P2 to use explicit `DebatePhase` enum instead of `current_response.startswith("Bull")` regex.

## Related Artifacts

- `docs/BOTS_DESIGN.md` — design doc with architecture diagrams, code sketches, risk table
- `battlecode2026/AGENTS.md` — source of patterns
- `ROADMAP.md` cross-pollination table — high-level pointers
- `RESEARCH_FINDINGS.md` — empirical evidence motivating the refactor (especially the Constitution VII reframe)

## Next Steps

Per spec-kit workflow:
1. `/speckit.clarify` — resolve open questions (e.g., final WEIGHTS, exact convergence threshold)
2. `/speckit.plan` — generate `plan.md` with implementation order + file changes per phase
3. `/speckit.tasks` — generate `tasks.md` as actionable checklist
4. `/speckit.implement` — execute (or do by hand against the task list)
5. `/speckit.analyze` — post-mortem after each phase

Recommended sequencing per ROADMAP: this spec sits in Phase E (architectural variants), best pursued AFTER current Phase B (007 30-pair Opus re-pilot) result lands and the 21d bull-side signal is validated at scale.
