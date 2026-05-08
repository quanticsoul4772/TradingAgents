---

description: "Task list for WC-10 Continuous Scalar Rating implementation + empirical pilot"
---

# Tasks: WC-10 Continuous Scalar Rating

**Input**: Design documents from `/specs/108-wc-10-continuous-scalar-rating/`
**Prerequisites**: spec.md (✅ PR #107), plan.md + research.md + data-model.md + contracts/ + quickstart.md (✅ PR #108)

**Tests**: REQUIRED. ~6 unit + 2 integration per spec.md SC-001 through SC-004.

**Organization**: Tasks grouped by user story for independent implementation + testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 (user story phase tasks only)
- Include exact file paths in descriptions

## Path Conventions

Single-package extension to `tradingagents` per plan.md:
- New package: `tradingagents/wc_10/{__init__.py,bin.py}`
- Modified existing: `tradingagents/agents/schemas.py` + `tradingagents/agents/utils/agent_states.py` + `tradingagents/agents/managers/portfolio_manager.py` + `tradingagents/graph/signal_processing.py` + `tradingagents/graph/trading_graph.py` + `tradingagents/default_config.py`
- Tests: `tests/test_wc_10_bin.py` + `tests/test_wc_10_pm_integration.py`
- Pilot harness: `scripts/wc_10_pilot.py`
- Experiment dir: `experiments/2026-05-08-001-wc-10-pilot/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify pytest collection works on the feature branch.

- [ ] T001 Verify existing pytest collection: `uv run --no-sync pytest --collect-only -q tests/` returns 1134+ tests collected with no errors

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add 3 new TradingAgentsConfig keys + AgentState wc_10 field + extend `_log_state` whitelist. Blocking prerequisites for ALL user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Add 3 new TradingAgentsConfig keys to `tradingagents/default_config.py`: `wc_10_enabled` (bool, default False), `wc_10_filter_mode` (Literal["bypass", "passthrough"], default "bypass"), `wc_10_bin_thresholds` (tuple of 4 floats, default (-0.6, -0.2, 0.2, 0.6)). Add to BOTH the `TradingAgentsConfig` TypedDict AND the `DEFAULT_CONFIG` dict per the existing pattern. Add 14-line empirical-justification comment block.
- [ ] T003 Add `wc_10` field to AgentState TypedDict in `tradingagents/agents/utils/agent_states.py`. Use `NotRequired[dict[str, Any]]` per FR-006 backward-compat (per spec X-1 PR #88 precedent + reference_speckit_6pr_workflow_pattern.md memory).
- [ ] T004 Extend `_log_state` whitelist in `tradingagents/graph/trading_graph.py` to include `"wc_10"` key. Verify the existing whitelist (`forward_catalyst`, `contrarian_gate`, `sector_momentum`, `bear_sector_symmetry`) is preserved.

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 3 — Bin function for ex-post analysis (Priority: P2; foundational for US1)

**Goal**: `bin_scalar_to_tier()` pure function provides 5-tier categorical mapping for ex-post analysis + filter-passthrough mode (deferred to v2).

**Why ordered before US1**: US1 + US2 don't directly depend on the bin function (filter-bypass mode skips the chain), but US3 unit tests are the foundation for verifying SC-002 + SC-007 (analyzer needs bin for ex-post comparison).

**Independent Test**: Pure-function tests at boundary thresholds: `bin_scalar_to_tier(0.65)` → "Buy"; `bin_scalar_to_tier(-0.6)` → "Sell" (boundary). Custom thresholds: pass `(-0.7, -0.3, 0.3, 0.7)` and verify bin assignment uses custom values.

### Tests for User Story 3 ⚠️

- [ ] T005 [P] [US3] Create `tests/test_wc_10_bin.py` with 6 unit tests per `contracts/wc_10_module.md` test contract (test_bin_buy_interior + test_bin_overweight_boundary + test_bin_hold_interior + test_bin_sell_boundary + test_bin_sell_interior + test_bin_rejects_invalid_thresholds). Use `pytestmark = pytest.mark.unit`.

### Implementation for User Story 3

- [ ] T006 [US3] Create `tradingagents/wc_10/__init__.py` exporting `bin_scalar_to_tier` + `DEFAULT_BIN_THRESHOLDS`
- [ ] T007 [US3] Create `tradingagents/wc_10/bin.py` (~80 LOC) with `DEFAULT_BIN_THRESHOLDS` constant + `bin_scalar_to_tier(rating, thresholds=None) -> str` pure function. Implementation per `contracts/wc_10_module.md`:
   1. Validate thresholds (strictly monotonic + in [-1, +1]) → raise ValueError
   2. Validate rating in [-1, +1] → raise ValueError
   3. Apply ≤ boundary semantics: Sell / Underweight / Hold / Overweight / Buy

**Checkpoint**: bin function works + 6 unit tests PASS. US1 + US2 can build on this.

---

## Phase 4: User Story 1 — Operator runs WC-10 pilot (Priority: P1) 🎯 MVP

**Goal**: Schema mutation + SignalProcessor scalar branch + portfolio_manager_node bypass branch + state log persistence. Operator can opt in via PARAMS.json and run propagate(ticker, date) to get a scalar rating.

**Independent Test**: Run `propagate("NVDA", "2026-04-30")` with `wc_10_enabled=True`. Verify `final_state["final_trade_decision"]` contains a numeric rating in [-1, +1]. Verify `final_state["wc_10"]` annotation has 3 fields (rating_scalar, filter_mode, bin_thresholds_snapshot). Verify NO filter from the chain (A3, spec 003, etc.) executed (mock filter calls + assert_not_called).

### Tests for User Story 1 ⚠️

- [ ] T008 [P] [US1] Create `tests/test_wc_10_pm_integration.py` with 2 integration tests per `contracts/wc_10_module.md` test contract:
   - `test_default_off_5tier_unchanged`: `wc_10_enabled=False` (default) → state log shape identical to pre-WC-10 baseline; rating is 5-tier string; all 9 filters execute (SC-003)
   - `test_bypass_mode_skips_filters`: `wc_10_enabled=True` + `wc_10_filter_mode="bypass"` → rating is float; `state["wc_10"]` annotation present with 3 fields; ALL 9 filter mocks NOT called (SC-001 + SC-004)
   Use `pytestmark = pytest.mark.unit`. Mirror the test isolation pattern from `tests/test_institutional_rotation_pm_integration.py` (PR #92).

### Implementation for User Story 1

- [ ] T009 [US1] Modify `tradingagents/agents/schemas.py` `PortfolioDecision.rating` field: change from `PortfolioRating` enum to `Union[PortfolioRating, float]` per `contracts/wc_10_module.md`. Add a `@validator` ensuring float values are in [-1, +1]. Update field description to document both modes.
- [ ] T010 [US1] Modify `tradingagents/graph/signal_processing.py` `SignalProcessor.extract_rating()` method. Add a scalar-aware branch: when `config["wc_10_enabled"]` AND parsed rating is float, return the float directly. Existing 5-tier regex extraction remains for default-off path.
- [ ] T011 [US1] Modify `tradingagents/agents/managers/portfolio_manager.py.portfolio_manager_node` to add filter-bypass branch:
   1. After existing LLM call to produce `final_trade_decision`
   2. If `config.get("wc_10_enabled") and config.get("wc_10_filter_mode") == "bypass"`:
      - Set `state["wc_10"]` = {rating_scalar, filter_mode, bin_thresholds_snapshot}
      - Return state immediately (skip 9-filter chain)
   3. Else: existing chain (A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → spec X-1)

**Checkpoint**: User Story 1 fully functional. Operator can opt in + see scalar ratings in state logs + verify bypass mode skips filter chain.

---

## Phase 5: User Story 2 — Operator opts out for zero-overhead default (Priority: P1)

**Goal**: When `wc_10_enabled=False` (default), framework behavior is identical to current 5-tier baseline. NO regression.

**Independent Test**: Run `propagate("NVDA", "2026-04-30")` with default config (`wc_10_enabled=False`). Verify state log shape is byte-identical to pre-WC-10 baseline (modulo timestamps). Verify rating field is 5-tier string. Verify all 9 filters execute.

### Tests for User Story 2 ⚠️

US2 acceptance scenarios are covered by `test_default_off_5tier_unchanged` (T008). No additional integration tests required.

### Implementation for User Story 2

No new implementation needed beyond Phase 4. The `portfolio_manager_node` filter-bypass branch from T011 short-circuits ONLY when `wc_10_enabled=True`. When False, the existing 5-tier code path runs unchanged. Verify by running T008's `test_default_off_5tier_unchanged`.

**Checkpoint**: Backward compat verified. Existing daily_signals + paper-trading workflows continue to work.

---

## Phase 6: Empirical pilot harness

**Purpose**: Build the 40-propagate pilot harness + experiment scaffolding to actually run the WC-10 v1 experiment.

- [ ] T012 Create `experiments/2026-05-08-001-wc-10-pilot/` via `python scripts/new_experiment.py wc-10-pilot --source-idea WC-10`. Verify scaffolding produces HYPOTHESIS.md + PARAMS.json + run.sh + run.ps1 stubs.
- [ ] T013 Edit `experiments/2026-05-08-001-wc-10-pilot/HYPOTHESIS.md` to document the 3 falsifiable predictions (NULL / ALT-A / ALT-B) per spec.md SC-007. Document the test grid (10 dates × NVDA + AAPL × 2 modes = 40 propagates).
- [ ] T014 Edit `experiments/2026-05-08-001-wc-10-pilot/PARAMS.json` with the WC-10 + 5-tier-baseline config diff per `data-model.md`. Two PARAMS files OR one PARAMS with `mode` parameter — operator chooses pattern.
- [ ] T015 Create `scripts/wc_10_pilot.py` (~120 LOC) per `contracts/wc_10_module.md` pilot harness contract:
   1. CLI: `--tickers NVDA,AAPL --dates 10 --out experiments/<dir>/results.csv`
   2. Build (ticker, date) grid (10 dates × 2 tickers = 20 pairs)
   3. For each pair × each mode (wc_10 + 5tier_baseline) = 40 propagates
   4. Append-on-each-row CSV write (resume-on-crash pattern from `scripts/backtest.py`)
   5. Build TradingAgentsConfig with mode-specific overrides (`wc_10_enabled=True/False` + `wc_10_filter_mode="bypass"`)
   6. Memory-log isolation: `memory_log_path = <out_dir>/wc10_pilot_memory.md` (segregates from operator's real memory)

**Checkpoint**: Pilot harness ready to run. Estimated cost: ~$16 LLM (40 propagates × ~$0.40).

---

## Phase 7: Empirical pilot run (operator authorization required)

**Purpose**: Actually execute the pilot. ~$16 LLM cost; requires operator authorization gate.

- [ ] T016 Operator approves pilot run + cost (Constitution III T2 ≤$30 budget verified).
- [ ] T017 Run pilot: `uv run --no-sync python scripts/wc_10_pilot.py --tickers NVDA,AAPL --out experiments/2026-05-08-001-wc-10-pilot/results.csv`. Estimated 40 propagates × ~3-5min wall-clock = ~2-3.5h end-to-end. Resume-on-crash if interrupted.
- [ ] T018 Verify results.csv has 40 rows (or whatever subset completed). Spot-check 2-3 rows for schema correctness (rating type matches mode column).

---

## Phase 8: Empirical analysis + ANALYSIS.md

**Purpose**: Compute the 3 headline metrics + falsification verdict per SC-005 + SC-007.

- [ ] T019 Compute 3 SC-005 headline metrics:
   1. Fraction of `|rating| > 0.2` in WC-10 mode (= committed cases) vs fraction non-Hold in 5tier_baseline mode
   2. Signed-rating × 21d-forward-α correlation (Pearson + Spearman)
   3. Bin-ex-post-to-5-tier (using `bin_scalar_to_tier()`) and compare bucket means to 5tier_baseline bucket means
- [ ] T020 Apply SC-007 falsification framework: determine which of NULL / ALT-A / ALT-B is empirically distinguishable. Document the verdict (PASS one prediction, INCONCLUSIVE if all ambiguous).
- [ ] T021 Write `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` with the 3 metrics + falsification verdict. Per Constitution Principle IV, INCONCLUSIVE is a valid outcome.

**Checkpoint**: Empirical pilot SHIPPED with verdict per Constitution II (One Experiment Per Change ships its empirical results).

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T022 Run full pytest suite: `uv run --no-sync pytest -m unit -q` AND `pytest -m integration -q`. Verify all 8 new tests (6 unit + 2 integration) pass AND no existing tests regress.
- [ ] T023 Run ruff: `ruff check tradingagents/wc_10/ tests/test_wc_10_*.py scripts/wc_10_pilot.py tradingagents/default_config.py tradingagents/agents/schemas.py tradingagents/agents/utils/agent_states.py tradingagents/agents/managers/portfolio_manager.py tradingagents/graph/signal_processing.py tradingagents/graph/trading_graph.py`. Verify zero violations.
- [ ] T024 Run mypy on new module: `uv run --no-sync mypy tradingagents/wc_10/`. Verify 0 NEW errors (existing project mypy floor of 126 is acceptable; only NEW errors block).
- [ ] T025 Update `CLAUDE.md` to add WC-10 to the empirical-filters section (after Spec X-1). Brief mention: module path, default-off rationale, config-key namespace, pilot results pointer.
- [ ] T026 Add CHANGELOG entry under `[Unreleased]` summarizing WC-10 deployment + linking to PRs (#107 spec, #108 plan, this tasks PR, MVP PR, pilot run PR, ANALYSIS PR).

**Checkpoint**: All quality gates green. WC-10 v1 SHIPPED end-to-end.

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 1 | (none) |
| Phase 2 | Phase 1 |
| Phase 3 (US3 — bin function) | Phase 2 |
| Phase 4 (US1 — MVP) | Phase 2 + Phase 3 (uses bin in pilot analysis) |
| Phase 5 (US2 — opt-out) | Phase 4 (shares portfolio_manager_node implementation) |
| Phase 6 (pilot harness) | Phase 4 |
| Phase 7 (pilot RUN) | Phase 6 + operator authorization |
| Phase 8 (analysis) | Phase 7 |
| Phase 9 (polish) | Phases 1-8 all complete |

**Independence note**: US2 has no separate implementation; it shares the conditional branch from US1 (filter-bypass triggers only when wc_10_enabled=True; otherwise existing 5-tier code path runs unchanged). Independently TESTABLE via T008 but not independently IMPLEMENTABLE.

## Parallel execution opportunities

- T005 (US3 unit tests) + T006 + T007 (US3 implementation) can be authored in parallel [P] but T007 is implementation that T005 depends on for actual test runs.
- T008 (US1 integration tests) + T009 + T010 + T011 (US1 implementation) similarly.
- T013 + T014 (HYPOTHESIS + PARAMS edits) can run in parallel.
- T019 + T020 (SC-005 + SC-007 analysis) can run in parallel.

## Implementation strategy

**MVP scope (T001-T011 = Phases 1+2+3+4)**: ~12 tasks. Delivers schema mutation + SignalProcessor scalar extraction + portfolio_manager_node bypass branch + bin function + 8 tests covering core mechanism. Operator can opt in to WC-10 + see scalar ratings in state logs.

**Full v1 scope (T001-T026)**: ~26 tasks. Adds pilot harness + experiment scaffolding + actual pilot run + ANALYSIS.md verdict + cross-cutting polish.

**Recommended PR breakdown**:

- **PR-A (MVP)**: T001-T011 (Phases 1+2+3+4). ~12 tasks. Ships the implementation. $0 LLM cost (pure code).
- **PR-B (Pilot harness)**: T012-T015 (Phase 6). ~4 tasks. Ships the harness + experiment scaffold. $0 LLM cost.
- **PR-C (Pilot run)**: T016-T018 (Phase 7). ~3 tasks. Operator authorizes; runs ~$16 LLM. ~2-3.5h wall-clock.
- **PR-D (Analysis + polish)**: T019-T026 (Phases 8+9). ~8 tasks. Ships ANALYSIS.md verdict + CLAUDE.md + CHANGELOG + quality gate cleanups. $0 LLM cost.

OR a single bundled PR if the operator prefers (consistent with smaller spec patterns).

## Format validation

All tasks above conform to the required format:
- ✅ Checkbox `- [ ]` start
- ✅ Sequential T### IDs (T001 through T026)
- ✅ [P] markers on parallelizable tasks (different files)
- ✅ [US1] / [US2] / [US3] story labels on user-story phase tasks (T005-T011)
- ✅ NO story labels on Setup (T001), Foundational (T002-T004), Pilot (T012-T021), Polish (T022-T026) phases
- ✅ Exact file paths in every description
- ✅ Total task count: 26
