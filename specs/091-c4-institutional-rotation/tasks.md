---

description: "Task list for Spec X-1 (C-4 Institutional Rotation Filter) implementation"
---

# Tasks: C-4 Institutional Rotation Filter (Spec X-1)

**Input**: Design documents from `/specs/091-c4-institutional-rotation/`
**Prerequisites**: spec.md (✅ PR #88), plan.md + research.md + data-model.md + contracts/ + quickstart.md (✅ PR #89)

**Tests**: REQUIRED. Spec mandates ~14 unit tests + 4 integration tests per SC-001 through SC-008. TDD-style not strictly required but tests must land in same PR as implementation per existing project convention.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single-package extension to existing `tradingagents` Python package per plan.md:

- Filter helper module: `tradingagents/agents/utils/institutional_rotation_filter.py`
- PM-hook integration: `tradingagents/agents/managers/portfolio_manager.py`
- Config keys: `tradingagents/default_config.py`
- Unit tests: `tests/test_institutional_rotation_filter.py`
- Integration tests: `tests/test_institutional_rotation_pm_integration.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed. All infrastructure already in place per existing tradingagents package + pytest configuration.

- [ ] T001 Verify existing pytest collection works on the feature branch via `pytest --collect-only -q tests/` (no new fixtures or config needed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the 4 new TradingAgentsConfig keys + verify Spec 007's `state["forward_catalyst"]` annotation dict is the integration target. These are blocking prerequisites for ALL user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Add 4 new TradingAgentsConfig keys to `tradingagents/default_config.py`: `institutional_rotation_bear_mode` (Literal["off","shadow","active"], default "shadow"), `institutional_rotation_bull_mode` (Literal["off","shadow","active"], default "off"), `institutional_rotation_outflow_threshold` (float, default 0.05), `institutional_rotation_inflow_threshold` (float, default 0.05). Add to BOTH the `TradingAgentsConfig` TypedDict AND the `DEFAULT_CONFIG` dict per the existing pattern.
- [ ] T003 Verify `state["forward_catalyst"]` is already declared in AgentState TypedDict (`tradingagents/agents/utils/agent_states.py`) and `_log_state` whitelist already includes `forward_catalyst` (`tradingagents/graph/trading_graph.py`). No changes required — just confirm the integration target exists. Document the verification in commit message.

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Bear-side commit suppression on institutional outflow signal (Priority: P1) 🎯 MVP

**Goal**: When institutional outflow + bearish pre-rating, filter suppresses to Hold. This is the core empirical finding (PR #75 + #77 evidence base).

**Independent Test**: Run `propagate("AMD", "2026-04-24")` (or any retrospective-cohort ticker with institutional outflow) with `institutional_rotation_bear_mode="active"`. Verify state log contains `state["forward_catalyst"]["institutional_rotation"]` with `fired_bear=True`, `pre_rating="Underweight"` (or Sell), `post_rating="Hold"`, and `net_rotation_pct < -threshold`. Verify rendered Portfolio Manager output shows Hold instead of original bearish rating.

### Tests for User Story 1 ⚠️

> Write these tests in the SAME PR as implementation per project convention (no separate test PR).

- [ ] T004 [P] [US1] Add test fixtures to `tests/test_institutional_rotation_filter.py` — autouse `mocker.patch` for `tradingagents.agents.utils.institutional_rotation_filter.yf.Ticker` to prevent network calls (per contracts/institutional_rotation_filter.md test-isolation requirement)
- [ ] T005 [P] [US1] Unit test in `tests/test_institutional_rotation_filter.py`: `test_fetch_happy_path` — mock yfinance returning a 10-row DataFrame with pctChange column; assert `_fetch_institutional_rotation("NVDA")` returns the correct sum (covers SC-001 prerequisite)
- [ ] T006 [P] [US1] Unit test: `test_fetch_handles_nan_pctchange` — yfinance DataFrame with mixed NaN + numeric pctChange values; assert NaN treated as 0 via `.fillna(0).sum()` (covers FR-002)
- [ ] T007 [P] [US1] Unit test: `test_should_suppress_bear_below_threshold` — `should_suppress_bear(-0.06, 0.05)` → True (covers SC-001)
- [ ] T008 [P] [US1] Unit test: `test_should_suppress_bear_above_threshold` — `should_suppress_bear(-0.04, 0.05)` → False (covers SC-001)
- [ ] T009 [P] [US1] Unit test: `test_should_suppress_bear_boundary_equals` — `should_suppress_bear(-0.05, 0.05)` → False (strict less-than per FR-005, SC-002)
- [ ] T010 [P] [US1] Unit test: `test_apply_filter_active_mode_fires` — given `bear_mode="active"`, `pre_rating="Underweight"`, `net_rotation=-0.08`, assert `state["forward_catalyst"]["institutional_rotation"]["fired_bear"]==True` AND `post_rating=="Hold"` AND state's `final_trade_decision` markdown is mutated to show Hold rating (covers SC-001, SC-007, SC-008)

### Implementation for User Story 1

- [ ] T011 [US1] Create `tradingagents/agents/utils/institutional_rotation_filter.py` with module docstring (mirror Spec 007's `forward_catalyst_filter.py` opening), imports (`functools.lru_cache`, `logging`, `re`, `yfinance as yf`, `tradingagents.agents.utils.agent_states.AgentState`, `tradingagents.default_config.TradingAgentsConfig`), and constants (`_BULLISH_RATINGS`, `_BEARISH_RATINGS`, `_VALID_MODES`)
- [ ] T012 [US1] Add `_fetch_institutional_rotation(ticker: str) -> float | None` function with `@lru_cache(maxsize=128)` decorator. Implementation: try yfinance fetch → handle None / empty / missing pctChange / exceptions → return None on any failure → return `df.head(10)["pctChange"].fillna(0).sum()` on success. Mirror exactly the same logic as `scripts/forward_catalyst_class4_retrospective.py:_fetch_institutional_rotation` (single source of truth)
- [ ] T013 [US1] Add `should_suppress_bear(net_rotation: float | None, threshold: float) -> bool` pure function. Implementation: return `net_rotation is not None and net_rotation < -threshold`. Strict less-than per FR-005
- [ ] T014 [US1] Add `apply_filter(state: AgentState, config: TradingAgentsConfig) -> AgentState` function. Implementation order:
   1. Read `bear_mode = config.get("institutional_rotation_bear_mode", "off")` and `bull_mode = config.get("institutional_rotation_bull_mode", "off")`
   2. If both modes are "off", return state unchanged (FR-011)
   3. Read `ticker = state.get("company_of_interest")` and call `net_rotation = _fetch_institutional_rotation(ticker)`
   4. Read `outflow_threshold = config.get("institutional_rotation_outflow_threshold", 0.05)`
   5. Extract `pre_rating` from `state["final_trade_decision"]` markdown via regex (mirror `signal_processing.py` pattern)
   6. Compute `would_fire_bear = should_suppress_bear(net_rotation, outflow_threshold) and pre_rating in _BEARISH_RATINGS`
   7. Compute `fired_bear = would_fire_bear and bear_mode == "active"`
   8. Compute `post_rating = "Hold" if fired_bear else pre_rating`
   9. Build 8-field annotation dict and assign to `state.setdefault("forward_catalyst", {})["institutional_rotation"]`
   10. If `fired_bear`, mutate `state["final_trade_decision"]` to replace the rating string with "Hold" (use the same regex-based replacement pattern Spec 007 uses)
   11. Return state
- [ ] T015 [US1] Integrate the filter into `tradingagents/agents/managers/portfolio_manager.py` PM-hook chain. Add `from tradingagents.agents.utils import institutional_rotation_filter` to imports. Add `state = institutional_rotation_filter.apply_filter(state, config)` as the LAST call in the filter chain (after `forward_catalyst_filter.apply_filter`). FR-012 ordering: A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → **spec X-1**

**Checkpoint**: At this point, User Story 1 (core bear-side suppression) should be fully functional and testable. The filter fires in active mode when institutional outflow + bearish pre-rating align.

---

## Phase 4: User Story 2 — Shadow-mode observation without suppression (Priority: P1)

**Goal**: Operators can observe filter behavior without committing to active suppression. Constitution VIII v1.4.0 shadow-mode-first pattern requires this for any new mechanism class at small sample size.

**Independent Test**: Set `institutional_rotation_bear_mode="shadow"` in PARAMS.json. Run propagate on a ticker with confirmed institutional outflow + bearish pre-rating. Verify state log shows `would_fire_bear=True` AND `fired_bear=False`, AND `post_rating == pre_rating` (no mutation).

### Tests for User Story 2 ⚠️

- [ ] T016 [P] [US2] Unit test in `tests/test_institutional_rotation_filter.py`: `test_apply_filter_shadow_mode_observes_only` — given `bear_mode="shadow"`, `pre_rating="Underweight"`, `net_rotation=-0.08`, assert `would_fire_bear==True` AND `fired_bear==False` AND `post_rating=="Underweight"` (unchanged) AND state's `final_trade_decision` markdown is unchanged (covers SC-006)
- [ ] T017 [P] [US2] Integration test in `tests/test_institutional_rotation_pm_integration.py`: `test_pm_hook_shadow_mode_no_mutation` — exercise the full PM-hook chain with `bear_mode="shadow"`, mocked yfinance returning outflow data, mocked propagate state with bearish pre-rating. Assert post-filter state matches the shadow-mode contract from contracts/institutional_rotation_filter.md (covers SC-006)

### Implementation for User Story 2

No new implementation needed beyond Phase 3. The `apply_filter` function from T014 already handles the shadow-mode branch correctly via the `fired_bear = would_fire_bear and bear_mode == "active"` short-circuit. Verify by running T016 + T017 tests against the existing implementation.

**Checkpoint**: Shadow mode is testably distinct from active mode. Operators can choose between observation and suppression.

---

## Phase 5: User Story 3 — Filter degrades cleanly on data unavailability (Priority: P1)

**Goal**: When yfinance is unavailable for a ticker (ETF, small cap, API outage, missing pctChange), filter does NOT fire and propagate completes successfully.

**Independent Test**: Run propagate on an ETF ticker (e.g., "SPY", "XLK"). Verify state log shows `net_rotation_pct=None`, `fired_bear=False`, `would_fire_bear=False`, and rating unchanged from pre-filter. Verify no exception raised.

### Tests for User Story 3 ⚠️

- [ ] T018 [P] [US3] Unit test in `tests/test_institutional_rotation_filter.py`: `test_fetch_returns_none_on_yfinance_none` — mock `yf.Ticker(t).institutional_holders` returning None; assert `_fetch_institutional_rotation` returns None (covers SC-003)
- [ ] T019 [P] [US3] Unit test: `test_fetch_returns_none_on_empty_dataframe` — mock yfinance returning empty DataFrame; assert returns None (covers SC-003)
- [ ] T020 [P] [US3] Unit test: `test_fetch_returns_none_on_missing_pctchange_column` — mock yfinance returning DataFrame missing the pctChange column; assert returns None (covers SC-003)
- [ ] T021 [P] [US3] Unit test: `test_fetch_returns_none_on_yfinance_exception` — mock `yf.Ticker(t).institutional_holders` to raise an arbitrary exception; assert returns None (no exception escapes) (covers SC-003)
- [ ] T022 [P] [US3] Unit test: `test_should_suppress_bear_none_input_returns_false` — `should_suppress_bear(None, 0.05)` → False (covers SC-003 boundary)
- [ ] T023 [P] [US3] Integration test in `tests/test_institutional_rotation_pm_integration.py`: `test_pm_hook_yfinance_failure_graceful` — exercise full PM-hook with `bear_mode="active"` and yfinance mocked to raise; assert no exception, `fired_bear=False`, `post_rating == pre_rating`, propagate completes (covers SC-003)

### Implementation for User Story 3

No new implementation needed beyond Phase 3. The `_fetch_institutional_rotation` from T012 already handles all 4 failure modes via try/except returning None. Verify by running T018-T023 tests against the existing implementation.

**Checkpoint**: Filter is operationally safe on any ticker. ETFs, small caps, and API outages don't break propagate.

---

## Phase 6: User Story 4 — Operator cost-control via mode=off escape hatch (Priority: P2)

**Goal**: When both modes are off, helper module is not invoked, no yfinance call, no state annotation. Backward compatibility with pre-Spec-X-1 state log shape.

**Independent Test**: Set both modes to "off" in PARAMS.json. Run propagate on a ticker that would otherwise trigger. Verify state log does NOT contain `state["forward_catalyst"]["institutional_rotation"]` field. Verify yfinance NOT called.

### Tests for User Story 4 ⚠️

- [ ] T024 [P] [US4] Unit test in `tests/test_institutional_rotation_filter.py`: `test_apply_filter_both_modes_off_no_annotation` — given `bear_mode="off"`, `bull_mode="off"`, assert `apply_filter` returns state unchanged AND `state["forward_catalyst"]` does NOT contain `"institutional_rotation"` key (covers SC-005, FR-011)
- [ ] T025 [P] [US4] Unit test: `test_apply_filter_both_modes_off_no_yfinance_call` — given both modes "off", patch `_fetch_institutional_rotation` and assert it is NOT called (covers SC-005)
- [ ] T026 [P] [US4] Integration test in `tests/test_institutional_rotation_pm_integration.py`: `test_pm_hook_both_modes_off_baseline_state_log` — exercise full PM-hook with both modes "off"; assert state log shape exactly matches pre-Spec-X-1 baseline (no `institutional_rotation` sub-dict in `forward_catalyst`) (covers SC-005)

### Implementation for User Story 4

No new implementation needed beyond Phase 3. The `apply_filter` function from T014 already handles the both-modes-off branch via the early return at step 2. Verify by running T024-T026 tests against the existing implementation.

**Checkpoint**: Operators have a fully functional opt-out. Filter has zero overhead when disabled.

---

## Phase 7: LRU cache verification (cross-cutting)

**Goal**: SC-004 LRU cache correctness — same ticker requested twice in a single process MUST hit cache (no second yfinance call).

This is cross-cutting because it affects performance characteristics of all 4 user stories.

- [ ] T027 [P] Unit test in `tests/test_institutional_rotation_filter.py`: `test_lru_cache_correctness` — patch `yf.Ticker` with a mock; call `_fetch_institutional_rotation("NVDA")` twice; assert mock was called only once (covers SC-004). NOTE: must clear the LRU cache before this test via `_fetch_institutional_rotation.cache_clear()` to ensure a known starting state.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Verify Constitution adherence, run full test suite, update documentation.

- [ ] T028 Run full pytest suite: `pytest -m unit -q` then `pytest -m integration -q`. Verify all 18 new tests (14 unit + 4 integration) pass AND no existing tests regress.
- [ ] T029 Run ruff: `ruff check tradingagents/agents/utils/institutional_rotation_filter.py tests/test_institutional_rotation_filter.py tests/test_institutional_rotation_pm_integration.py`. Verify zero violations (per project baseline).
- [ ] T030 Run mypy on the new module: `mypy tradingagents/agents/utils/institutional_rotation_filter.py`. Verify no new errors introduced (existing project mypy floor is acceptable; only NEW errors block).
- [ ] T031 Update `CLAUDE.md` to add Spec X-1 to the empirical-filters section (after Spec 008). Brief mention: module path, default-shadow rationale, config-key namespace, ablation toggle.
- [ ] T032 Update `tradingagents/agents/utils/__init__.py` if it exports filter modules (verify; if module-level exports are not used, no change needed).
- [ ] T033 Verify state log integrity by running `propagate("NVDA", "<recent-date>")` end-to-end OR a dry-run via the existing `daily_signals.py --shadow-gates` flag with mode-shadow active. Confirm state log contains the new annotation when expected. (Manual smoke test; document in PR description, not a unit test.)
- [ ] T034 Add CHANGELOG entry under `[Unreleased]` summarizing Spec X-1 deployment + linking to PR #88 (spec) + PR #89 (plan) + this PR.

**Checkpoint**: All quality gates green. Spec X-1 is ready for shadow-mode operator validation. SC-009 + SC-010 follow-up gates remain deferred (Q1 2026 13F refresh + n≥30 ablation respectively).

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 1 | (none) |
| Phase 2 | Phase 1 |
| Phase 3 (US1) | Phase 2 |
| Phase 4 (US2) | Phase 3 (shares `apply_filter` implementation) |
| Phase 5 (US3) | Phase 3 (shares `_fetch_institutional_rotation` implementation) |
| Phase 6 (US4) | Phase 3 (shares early-return branch) |
| Phase 7 | Phase 3 (LRU cache decorator) |
| Phase 8 | Phases 1-7 all complete |

**Independence note**: User Stories 2-4 share implementation with US1 because the filter's behavior across modes is encoded in a single `apply_filter` function. They are independently TESTABLE (each has dedicated tests) but not independently IMPLEMENTABLE — US1's core implementation covers all four story behaviors. This deviates slightly from spec-template's "fully independent stories" ideal but is the natural shape for a small filter module.

## Parallel execution opportunities

Within Phase 3 (US1):
- T004-T010 (test fixtures + 6 unit tests) can be drafted in parallel [P], but they must all land alongside or after T011-T015 (implementation). Suggested execution: write tests first as stubs (assertions wired to expected behavior), implement T011-T015, run tests, fix failing tests.

Within Phase 4-6 (US2, US3, US4):
- All test tasks (T016-T026) are [P] — different test functions in two test files; can be authored in parallel.

Phase 7 (T027) is [P] but should run AFTER T011-T012 (core implementation) is in place.

Phase 8 polish tasks are mostly sequential (full test suite → linting → docs).

## Implementation strategy

**MVP scope (T001-T015 = Phase 1 + 2 + US1)**: Delivers core bear-side suppression in active mode. ~12 tasks. ~80% of empirical value (the +5.41pp Δα + +8.06pp additive Δα come from active-mode bear suppression).

**Full v1 scope (T001-T034)**: Adds shadow mode + graceful degradation + opt-out + cross-cutting polish. ~34 tasks total. Estimated 3-4h end-to-end including testing.

**Recommended PR breakdown**:

- **PR-A**: T001-T015 (MVP — Phases 1+2+US1). Module + PM-hook + 7 tests covering core suppression. Ships the empirical mechanism.
- **PR-B**: T016-T027 (US2 + US3 + US4 + LRU verification). 11 tests covering shadow/degradation/opt-out/cache. Ships operational safety.
- **PR-C**: T028-T034 (polish). Full test runs + lint + mypy + CLAUDE.md + CHANGELOG. Ships quality gates.

OR a single bundled PR if the operator prefers (consistent with Spec 008 Hybrid C precedent).

## Format validation

All tasks above conform to the required format:
- ✅ Checkbox `- [ ]` start
- ✅ Sequential T### IDs (T001 through T034)
- ✅ [P] markers on parallelizable tasks (different files)
- ✅ [US1] / [US2] / [US3] / [US4] story labels on user-story phase tasks (T004-T026)
- ✅ NO story labels on Setup (T001), Foundational (T002-T003), Cross-cutting (T027), Polish (T028-T034) phase tasks
- ✅ Exact file paths in every description
- ✅ Total task count: 34
