---
description: "Task list for Spec 008 — Hybrid C calendar-boosted forward-catalyst filter"
---

# Tasks: Hybrid C — Calendar-Boosted Forward-Catalyst Filter (Spec 008)

**Input**: Design documents from `/specs/007-calendar-boost-filter/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/calendar_boost_api.md ✓

**Tests**: Required per spec SC-010 (≥12 unit + ≥4 integration). Tests for User Story 1 are MANDATORY (the boost mechanism IS the feature; without tests, SC-001..SC-007 are unverifiable). Tests for User Story 2 are MANDATORY (backward-compat verification per SC-005).

**Organization**: Tasks grouped by user story per the spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are absolute or relative to repo root

## Path Conventions

Single-package Python project. New files go to existing directories:
- Helper module: `tradingagents/agents/utils/calendar_boost.py`
- Integration target: `tradingagents/agents/utils/forward_catalyst_filter.py`
- Config: `tradingagents/default_config.py`
- Tests: `tests/test_calendar_boost.py` + `tests/test_forward_catalyst_filter_calendar_boost.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: NONE required. Spec 008 reuses existing project scaffolding (yfinance dep already present, pre-commit hooks already configured, pytest already configured).

- [X] T001 Verify yfinance is in `pyproject.toml` `[project.dependencies]` (it is — used by spec 004 sector momentum + analyst tools). No setup changes required.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: NONE required. Spec 008 has no blocking prerequisites — Spec 007 is already merged + tagged at v0.7.0; `state["forward_catalyst"]` is already declared in `AgentState` TypedDict; `_log_state` already whitelists the key.

- [X] T002 Verify `state["forward_catalyst"]` is declared in `tradingagents/agents/utils/agent_states.py` AgentState TypedDict (it is, per spec 007). No foundational changes required.

**Checkpoint**: Foundation ready (vacuously). User stories can proceed.

---

## Phase 3: User Story 1 - Operator opts into calendar-boost layer for bull-only filtering (Priority: P1) 🎯 MVP

**Goal**: Implement the helper module + integrate with spec 007 + 3 new config keys. After this phase, an operator setting `hybrid_c_calendar_boost_enabled=True` in PARAMS.json sees the boost behavior end-to-end.

**Independent Test**: Run `daily_signals.py` with the boost enabled on a ticker with earnings within 14 days; verify state["forward_catalyst"] gains the four new annotation fields and that a borderline-below-threshold bull rating gets downgraded to Hold.

### Tests for User Story 1 (MANDATORY per SC-010)

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation (TDD).

- [ ] T010 [P] [US1] Create `tests/test_calendar_boost.py` with autouse `_fetch_earnings_dates.cache_clear()` fixture (per R-7).
- [ ] T011 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_calendar_boost_at_zero_days_equals_one()` — verifies I-1 boundary (days=0 → boost=1.0).
- [ ] T012 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_calendar_boost_at_window_equals_zero()` — verifies the `>=window` strict path (days=14, window=14 → boost=0).
- [ ] T013 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_calendar_boost_returns_zero_for_none_days()` — verifies graceful-degradation path (days=None → boost=0).
- [ ] T014 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_calendar_boost_returns_zero_for_negative_days()` — verifies defensive guard (days=-1 → boost=0).
- [ ] T015 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_calendar_boost_linear_decay()` — verifies linear decay at days=window/2 (days=7, window=14 → boost=0.5).
- [ ] T016 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_apply_calendar_boost_no_op_when_boost_zero()` — verifies I-3 no-boost identity (boost=0 → effective=base).
- [ ] T017 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_apply_calendar_boost_saturation_clamp()` — verifies I-4 clamp (base=0.95, magnitude=0.5, boost=1.0 → effective=1.0 not 1.425).
- [ ] T018 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_apply_calendar_boost_normal_case()` — verifies SC-001 happy path (base=0.50, boost=0.5, magnitude=0.5 → effective=0.625).
- [ ] T019 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_effective_score_monotonicity()` — parametrized sweep over days_to_earnings ∈ {0, 1, 7, 13, 14, 15, 30}; verifies SC-002 (effective non-strictly decreasing in days).
- [ ] T020 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_yfinance_failure_returns_none()` — mocks yfinance.Ticker to raise; verifies SC-003 (days_to_next_earnings returns None).
- [ ] T021 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_yfinance_empty_calendar_returns_none()` — mocks yfinance.Ticker to return empty DataFrame; verifies SC-003 (days_to_next_earnings returns None).
- [ ] T022 [P] [US1] Add unit test in `tests/test_calendar_boost.py`: `test_lru_cache_idempotency()` — mocks yfinance.Ticker, calls `_fetch_earnings_dates(t)` twice; asserts mock.call_count == 1; verifies SC-004 + I-5.

**Phase 3 test checkpoint**: All 13 unit tests written and failing (no implementation yet). Run `pytest tests/test_calendar_boost.py -v` and confirm all FAIL with `ImportError` or `AttributeError`.

### Implementation for User Story 1

- [ ] T023 [US1] Create `tradingagents/agents/utils/calendar_boost.py` with the four public functions per `contracts/calendar_boost_api.md`: `_fetch_earnings_dates(ticker) -> tuple[datetime, ...]` (LRU-cached via `@lru_cache(maxsize=None)`), `days_to_next_earnings(ticker, trade_date) -> int | None`, `calendar_boost(days_to_earnings, window) -> float`, `apply_calendar_boost(score, days_to_earnings, window, magnitude) -> float`. Implementation MUST satisfy invariants I-1..I-6 + contracts C-1..C-3. Reuse the yfinance fetch pattern verbatim from `scripts/forward_catalyst_hybrid_c_retrospective.py:_build_earnings_cache` per R-1.
- [ ] T024 [US1] Run `pytest tests/test_calendar_boost.py -v`; confirm all 13 tests now PASS.
- [ ] T025 [US1] Run `ruff check tradingagents/agents/utils/calendar_boost.py tests/test_calendar_boost.py`; confirm zero violations.
- [ ] T026 [US1] Add three new keys to `tradingagents/default_config.py`: `hybrid_c_calendar_boost_enabled: bool = False` (FR-007), `hybrid_c_calendar_boost_window_days: int = 14` (FR-008), `hybrid_c_calendar_boost_magnitude: float = 0.5` (FR-009). Add corresponding entries to the `TradingAgentsConfig` TypedDict per contracts III-1..III-3.
- [ ] T027 [US1] Modify `tradingagents/agents/utils/forward_catalyst_filter.py` to add the conditional boost branch per R-5 + contracts II-1..II-4: when `config.get("hybrid_c_calendar_boost_enabled", False)` is True, fetch days, compute boost + effective_bull_score + effective_bear_score, update `state["forward_catalyst"]` with the four new keys. Otherwise effective_bull_score = bull_case_priced_in. Use effective_bull_score as the input to the existing fire-decision comparison.

**Checkpoint US1**: At this point, manually setting `hybrid_c_calendar_boost_enabled=True` + running a single propagate produces state log with the four new annotation keys. The helper integration is complete.

---

## Phase 4: User Story 2 - Backward-compatibility for operators who haven't opted in (Priority: P1)

**Goal**: Verify that with default config (boost disabled), spec 007 baseline behavior is preserved byte-equivalent.

**Independent Test**: Run a single propagate with default config; verify state["forward_catalyst"] dict-key set equals spec 007 baseline (no Hybrid C keys).

### Tests for User Story 2 (MANDATORY per SC-005 + SC-007)

- [ ] T030 [P] [US2] Create `tests/test_forward_catalyst_filter_calendar_boost.py` with autouse fixture cleaning the calendar_boost LRU cache.
- [ ] T031 [P] [US2] Add integration test in `tests/test_forward_catalyst_filter_calendar_boost.py`: `test_default_off_state_log_equals_spec_007_baseline()` — runs `evaluate_forward_catalyst` with default config; asserts `state["forward_catalyst"]` dict-key set is exactly the spec 007 baseline keys (no `days_to_earnings`, `calendar_boost`, `effective_bull_score`, `effective_bear_score`). Verifies SC-005 + FR-011.
- [ ] T032 [P] [US2] Add integration test: `test_enabled_state_log_gains_four_keys()` — runs with `hybrid_c_calendar_boost_enabled=True` and a mocked earnings fetch; asserts all four new keys are present. Verifies SC-007 + FR-012.
- [ ] T033 [P] [US2] Add integration test: `test_enabled_yfinance_failure_falls_through_to_baseline()` — runs with boost enabled + mocked yfinance.Ticker raising; asserts `days_to_earnings=None`, `calendar_boost=0`, `effective_bull_score == bull_case_priced_in`, fire decision equals spec 007 baseline. Verifies SC-003 path-through.

### Implementation for User Story 2

- [ ] T034 [US2] Run `pytest tests/test_forward_catalyst_filter.py tests/test_forward_catalyst_filter_calendar_boost.py -v`; confirm all spec 007 baseline tests still PASS (no regression) AND all new spec 008 tests PASS.
- [ ] T035 [US2] Run `pytest tests/test_portfolio_manager_filter_integration.py -v`; confirm all PM-integration tests still PASS unchanged (no PM hook chain modification per FR-014).

**Checkpoint US2**: Backward-compat verified. Existing operators see no behavioral change with default config.

---

## Phase 5: User Story 3 - Researcher attributes alpha specifically to the boost layer (Priority: P2)

**Goal**: The state log annotations (already added in US1) enable downstream alpha attribution. This phase is SC-008 regression check + a quick smoke test of the analyzer integration.

**Independent Test**: Run `scripts/forward_catalyst_hybrid_c_retrospective.py` against the cached Class 3 Opus scores; verify the +3.35pp bull-side improvement reproduces (SC-008).

### Implementation for User Story 3

- [ ] T040 [US3] Run `python scripts/forward_catalyst_hybrid_c_retrospective.py`; verify output matches the committed `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md` (bull-side +3.35pp net Δα at window=14d magnitude=0.5x ±0.5pp). Verifies SC-008 — the existing retrospective is the post-merge regression check.
- [ ] T041 [US3] Smoke test: run `python scripts/daily_signals.py --tickers <2-3-ticker-watchlist> --shadow-gates` with `hybrid_c_calendar_boost_enabled=True` in the override; verify the resulting state-log JSON contains the four new annotation fields. (Cost: ~$1-2 LLM for spec 007's underlying call, $0 marginal for Hybrid C.)

**Checkpoint US3**: Attribution path validated. Researchers can filter results.csv rows by `state.forward_catalyst.calendar_boost > 0` to attribute alpha.

---

## Phase N: Polish & Cross-Cutting Concerns

- [X] T050 [P] Run full test suite: `pytest tests/ -q`. Confirm: total test count = previous + ≥17 (13 unit + 4 integration); zero new failures.
- [X] T051 [P] Run `ruff check tradingagents/ tests/` — confirm zero new violations vs the baseline (current 0 errors per CLAUDE.md).
- [X] T052 [P] Run `mypy tradingagents/agents/utils/calendar_boost.py tradingagents/agents/utils/forward_catalyst_filter.py tradingagents/default_config.py` — confirm no NEW mypy errors introduced (the project baseline is 126 errors, none in the modified files).
- [X] T053 [P] Update `CLAUDE.md` "Empirical filters" section to document the new Hybrid C boost layer (default-off, opt-in pattern, +3.35pp empirical evidence reference).
- [X] T054 [P] Update `CHANGELOG.md` with a new entry for Spec 008 (date 2026-05-06, version bump per current convention).
- [X] T055 Run `pytest tests/test_calendar_boost.py tests/test_forward_catalyst_filter_calendar_boost.py -v --tb=short` one final time to confirm green.

## Phase N+1: Spec 008.5 amendment (added 2026-05-06 late-evening)

Closes the 1 coverage gap from `/speckit.analyze` (SC-012 latency benchmark not previously tested).

- [X] T056 Add `tests/test_calendar_boost_latency.py` with 2 wall-clock assertions:
  - `test_cache_warm_latency_under_5ms_p99`: 100-iteration p99 < 5 ms with mocked yfinance + warm cache
  - `test_cache_warm_arithmetic_only_under_1ms`: 1000-iteration per-call cost < 100 µs for boost math
- [X] T057 Update `spec.md` SC-012 to mark VERIFIED with reference to the new test file. Document cache-cold path as operator-validated via `scripts/smoke_spec_008.py` (network-dependent, not CI-testable).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: vacuous (T001 + T002 are verifications, not work)
- **Foundational (Phase 2)**: vacuous
- **User Stories (Phase 3+)**: US1 → US2 → US3 sequentially (US2 verifies US1's backward-compat; US3 is the regression check on US1's implementation)
- **Polish (Phase N)**: depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Standalone. Implements the boost mechanism end-to-end.
- **US2 (P1)**: Depends on US1 implementation (T026 + T027). Verifies backward-compat.
- **US3 (P2)**: Depends on US1 implementation (the state annotations US1 adds). Runs the retrospective regression check.

### Within Each User Story

- **TDD ordering for US1**: T010-T022 (write tests, FAIL) → T023 (impl) → T024 (tests PASS) → T025 (lint clean) → T026 (config keys) → T027 (integration).
- **Models / impl ordering**: helper module (T023) before config keys (T026) before integration (T027). The integration imports from the helper module + reads config keys.

### Parallel Opportunities

- All 13 US1 test tasks (T010-T022) can be written in parallel (same file, but each is a distinct test function — write them in one editor session).
- All 4 US2 integration tests (T030-T033) can be written in parallel (same file).
- T053 + T054 in Polish phase are independent doc updates.
- T050, T051, T052 in Polish phase can run in parallel (independent commands).

---

## Parallel Example: User Story 1 unit tests

```bash
# Open tests/test_calendar_boost.py in editor
# Add all 13 test functions in one file in a single editing session:
#   - test_calendar_boost_at_zero_days_equals_one
#   - test_calendar_boost_at_window_equals_zero
#   - test_calendar_boost_returns_zero_for_none_days
#   - test_calendar_boost_returns_zero_for_negative_days
#   - test_calendar_boost_linear_decay
#   - test_apply_calendar_boost_no_op_when_boost_zero
#   - test_apply_calendar_boost_saturation_clamp
#   - test_apply_calendar_boost_normal_case
#   - test_effective_score_monotonicity (parametrized)
#   - test_yfinance_failure_returns_none (mocked)
#   - test_yfinance_empty_calendar_returns_none (mocked)
#   - test_lru_cache_idempotency (mock-call-count)
# All FAIL with ImportError until T023 lands the helper module.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Verify Setup + Foundational vacuous (T001 + T002)
2. Write all 13 US1 tests (T010-T022) — they FAIL
3. Implement helper module (T023) — tests PASS
4. Lint clean (T024 + T025)
5. Add config keys (T026) + integrate into spec 007 (T027)
6. **STOP and VALIDATE**: Manual smoke test of one propagate with boost enabled
7. Commit + push US1

### Incremental Delivery

1. Setup + Foundational verified → MVP foundation ready (vacuous)
2. US1 (boost mechanism + integration) → Manual smoke test → COMMIT (PR-able state)
3. US2 (backward-compat verification) → Auto-test confirms zero regression → COMMIT
4. US3 (SC-008 regression check) → Verify +3.35pp reproduction → COMMIT
5. Polish (test suite green + lint clean + docs) → COMMIT
6. Open PR; merge to main; tag v0.8.0-spec-008.

### Sequential Solo Strategy (current session pattern)

Single developer (this session). Sequence:
1. T010-T022: write all 13 US1 tests in one editing session
2. T023: write helper module
3. T024-T025: verify tests pass + lint clean
4. T026-T027: config + integration
5. Commit + push (US1 complete)
6. T030-T035: US2 integration tests + verification
7. Commit + push (US2 complete)
8. T040-T041: US3 SC-008 regression check
9. Commit + push (US3 complete)
10. T050-T055: polish — full test + lint + mypy + doc updates
11. Commit + push (Polish complete)
12. Open PR for merge to main.

---

## Notes

- [P] tasks = different files OR distinct test functions in the same file
- [Story] label maps each task to US1/US2/US3 for traceability
- TDD: write tests first, ensure they FAIL, then implement
- Verify SC-008 reproduction is THE gate for declaring Spec 008 complete (per Constitution VIII v1.4.1)
- Commit after each user story (US1 / US2 / US3 / Polish = 4 commits minimum)
- Backward-compat is non-negotiable (FR-011 + SC-005); US2 explicitly verifies this
- Stop at any checkpoint to manually validate independently
