---

description: "Task list for Forward-Catalyst-Aware Contrarian Gate (Spec 007) implementation"
---

# Tasks: Forward-Catalyst-Aware Contrarian Gate (Spec 007)

**Input**: Design documents from `specs/006-forward-catalyst-gate/`
**Prerequisites**: spec.md ✓, plan.md ✓, research.md ✓, data-model.md ✓, contracts/ (2) ✓, quickstart.md ✓

**Tests**: Included throughout. Spec requires ≥90% line coverage on new code (SC-007). Integration-marked test for SC-008 empirical-validation gate (cohort-loaded retrospective verifies bull fires ≥24/27 + bear shadow fires ≥10/18).

**Organization**: Tasks grouped by user story (US1, US2, US3, US4 from spec.md). Within each story, [P] marks parallel-safe tasks (different files, no incomplete dependencies in the same phase).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single-project Python library extension per `plan.md` Structure Decision:
- Source: `tradingagents/agents/utils/` (new module parallel to A3 + spec 004 + spec 006) + `tradingagents/agents/managers/portfolio_manager.py` wiring
- Config: `tradingagents/default_config.py` (extend `TradingAgentsConfig` TypedDict + `DEFAULT_CONFIG`)
- State persistence: `tradingagents/graph/trading_graph.py:_log_state` whitelist + `tradingagents/agents/utils/agent_states.py` AgentState TypedDict
- Tests: `tests/` (flat)
- Scripts: `scripts/forward_catalyst_retrospective.py` (new; extends `scripts/forward_catalyst_class3_retrospective.py`)
- Docs: `CLAUDE.md` (existing), `CHANGELOG.md` (existing), `.specify/memory/constitution.md` (Principle VIII v1.4.0 amendment per FR-015)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add 6 config keys + scaffold the new module + extend the state-log whitelist + AgentState TypedDict so US1's tests have something to import and the persistence path is in place.

- [X] T001 Add `forward_catalyst_bull_mode: Literal["off", "shadow", "active"]`, `forward_catalyst_bear_mode: Literal["off", "shadow", "active"]`, `forward_catalyst_bull_threshold: float`, `forward_catalyst_bear_threshold: float`, `forward_catalyst_model: str`, `forward_catalyst_max_rationale_chars: int` keys to `TradingAgentsConfig` TypedDict in `tradingagents/default_config.py` (placement next to existing filter config keys; defaults `"active"` / `"shadow"` / `0.60` / `0.50` / `"claude-opus-4-7"` / `2000` per FR-005 + FR-006 + R-7)
- [X] T002 Add the same six keys to `DEFAULT_CONFIG` in `tradingagents/default_config.py` with default values + a 8-line comment cross-referencing `specs/006-forward-catalyst-gate/spec.md` and explaining (a) bull-side default-on per Constitution VIII Class 3 Opus retrospective DECISIVE PASS, (b) bear-side default-shadow per VIII shadow-mode-first condition, (c) Opus default justified by retrospective evidence (~10× cost vs Haiku but required for the bull-side default-on flip), (d) per-propagate cost ~$0.025
- [X] T003 [P] Create `tradingagents/agents/utils/forward_catalyst_filter.py` with module docstring referencing the spec; include `CasePricedInScore` Pydantic BaseModel + placeholder `evaluate_forward_catalyst()` function stub returning unmodified decision + off annotation, so US1 tests can import without circular-import issues. Includes import of `tradingagents.llm_clients.factory.create_llm_client` per R-1.
- [X] T004 [P] Extend `_log_state` whitelist in `tradingagents/graph/trading_graph.py` to include `"forward_catalyst": final_state.get("forward_catalyst")` with a 3-line comment cross-referencing the precedent set by commit `4c14d0f` (which added `contrarian_gate`), spec 004 (which added `sector_momentum`), and spec 006 (which added `bear_sector_symmetry`); per R-5 + FR-008
- [X] T005 [P] Extend `AgentState` TypedDict in `tradingagents/agents/utils/agent_states.py` to declare `forward_catalyst: NotRequired[dict | None]` (matches existing `contrarian_gate` + `sector_momentum` + `bear_sector_symmetry` declarations); without this, LangGraph silently drops the field from state merges per the bug spec 003 originally hit and CLAUDE.md documents

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the filter function + supporting infrastructure (CasePricedInScore schema, LLM call + structured output, prompt builder, threshold validation, annotation builder). All four user stories depend on `evaluate_forward_catalyst` existing.

**⚠️ CRITICAL**: All user stories depend on the filter function being callable.

- [X] T006 [P] Implement the `CasePricedInScore` Pydantic BaseModel in `tradingagents/agents/utils/forward_catalyst_filter.py` per data-model.md §1: `bull_case_priced_in: float (ge=0, le=1)`, `bear_case_priced_in: float (ge=0, le=1)`, `rationale: str (max_length=2000)`. Mirror the `second_opinion.py::SecondOpinionResult` pattern.
- [X] T007 [P] Implement the `_build_prompt(state, ticker, trade_date)` helper in `tradingagents/agents/utils/forward_catalyst_filter.py` that constructs the LLM prompt from the state's analyst reports + bull/bear debate + investment plan. Reuse the truncation pattern from `scripts/forward_catalyst_class3_retrospective.py::_build_prompt` (truncate each section to ≤6000 chars; total prompt ~12K tokens).
- [X] T008 Implement `evaluate_forward_catalyst(decision_markdown, state, *, bull_mode, bear_mode, bull_threshold, bear_threshold, model, max_rationale_chars=2000, llm=None) -> tuple[str, dict]` in `tradingagents/agents/utils/forward_catalyst_filter.py` per `contracts/filter_function.md`; depends on T006 + T007. Flow per data-model.md "State transitions" section: both-modes-off early return → threshold validation → LLM client construction (via factory; `llm` injection point for tests) → structured-output call (with try/except per FR-010 / FR-004) → strict greater-than threshold checks → active-mode override (bull or bear; mutually exclusive) → annotation dict population. Mirror the `second_opinion.py::evaluate_pm_decision` pattern for LLM-call resilience.
- [X] T009 [P] Create `tests/test_forward_catalyst_filter.py` covering all 28 fixtures named in `contracts/filter_function.md` + `contracts/annotation_schema.md`: both-modes-off / threshold-validation / LLM-failure / Pydantic-validation-failure / bull-active-fires (Buy + OW separate) / bull-no-fire (below threshold + Hold + UW) / bull-shadow-records-only / bear-active-fires (UW + Sell separate) / bear-shadow-default-no-override / strict-greater-than-boundary (bull + bear) / decision-markdown-no-rating-defensive / state-missing-reports-empty-substitute / annotation-active-bull-fires-full-dict / annotation-active-bear-fires-full-dict / annotation-shadow-records-would-fire-only / annotation-off-returns-off-skipped / annotation-llm-failure-skipped-with-error / annotation-invalid-threshold-skipped / annotation-invariant-fired-bull-implies-active / annotation-invariant-fired-bear-implies-active / annotation-strict-gt-bull / annotation-strict-gt-bear / annotation-fired-mutually-exclusive / audit-corpus-filter-by-fired-bull / haiku-routing / opus-routing / invalid-mode-falls-back-to-off / per-call-cost-ceiling. Uses synthetic LLM mocks (the `llm` injection point) to avoid live LLM calls.

**Checkpoint**: Foundation ready. The filter function is fully testable in isolation. User story implementation can begin.

---

## Phase 3: User Story 1 - Bull-side suppression (Priority: P1) 🎯 MVP

**Goal**: When the PM emits Buy/Overweight on a propagate where the LLM-extracted `bull_case_priced_in` score exceeds the bull threshold (default 0.60), the filter downgrades the rating to Hold and emits an annotation describing the suppression.

**Independent Test**: Run a propagate against AAPL on a date where the analyst reports + bull/bear debate produce a `bull_case_priced_in` score above 0.60 (verifiable via the retrospective CSV). With `forward_catalyst_bull_mode="active"` + `bull_threshold=0.60`, verify the persisted state shows `final_trade_decision` as Hold (not Overweight) and `state["forward_catalyst"]["fired_bull"] == True`.

### Tests for User Story 1

- [X] T010 [P] [US1] Add `test_forward_catalyst_disabled_when_both_modes_off` to `tests/test_portfolio_manager_filter_integration.py`: with both modes set to `"off"`, running the PM hook chain on an Overweight rating produces unchanged rating + no LLM call (mock the LLM client and assert zero invocations); SC-006 byte-identity regression-guard
- [X] T011 [P] [US1] Add `test_forward_catalyst_active_downgrades_overweight_when_bull_priced_in_above_threshold` to `tests/test_portfolio_manager_filter_integration.py`: mocked LLM returns `bull_case_priced_in=0.78, bear_case_priced_in=0.45`, `bull_threshold=0.60`, `bull_mode="active"`; verify `final_trade_decision` rating downgraded to Hold + `state["forward_catalyst"]["fired_bull"] == True` + post_rating == "Hold"; covers US1 acceptance scenario 1
- [X] T012 [P] [US1] Add `test_forward_catalyst_active_downgrades_buy_above_threshold` to `tests/test_portfolio_manager_filter_integration.py`: same setup as T011 but PM rating is Buy; verify rating downgraded to Hold; covers US1 acceptance scenario 2
- [X] T013 [P] [US1] Add `test_forward_catalyst_active_keeps_overweight_when_bull_priced_in_below_threshold` to `tests/test_portfolio_manager_filter_integration.py`: mocked LLM returns `bull_case_priced_in=0.55` (below 0.60); verify rating remains Overweight + `would_fire_bull == False`; covers US1 acceptance scenario 3
- [X] T014 [P] [US1] Add `test_forward_catalyst_does_not_act_on_non_bullish_ratings` to `tests/test_portfolio_manager_filter_integration.py`: mocked LLM returns `bull_case_priced_in=0.78`, but PM rating is Hold / Underweight (parameterized); verify rating unchanged on bull side + annotation captures `would_fire_bull=False`; covers US1 acceptance scenarios 4 + 5
- [X] T015 [P] [US1] Add `test_forward_catalyst_runs_after_all_other_filters_in_chain` to `tests/test_portfolio_manager_filter_integration.py`: setup where spec 004 has already downgraded Overweight to Hold; verify the forward-catalyst filter still calls the LLM (annotation captured for audit) but bull-side branch no-ops because pre-rating is Hold; covers FR-012 ordering
- [X] T016 [P] [US1] Add `test_state_log_persists_forward_catalyst_field` to `tests/test_trading_graph.py`: regression-guard mirroring `test_state_log_persists_bear_sector_symmetry_field` (the spec 006 test); constructs final_state with `"forward_catalyst"` populated, calls `_log_state`, asserts the field appears in the persisted JSON
- [X] T017 [P] [US1] Add `test_state_log_forward_catalyst_is_none_when_field_absent` to `tests/test_trading_graph.py`: when both modes off OR `forward_catalyst` key is absent from final_state, persisted log has `"forward_catalyst": null`; mirrors the parallel test for `contrarian_gate` / `sector_momentum` / `bear_sector_symmetry`

### Implementation for User Story 1

- [X] T018 [US1] Wire `evaluate_forward_catalyst` into `tradingagents/agents/managers/portfolio_manager.py` LAST in the chain (after A3 + spec 006 + spec 003/003.5 + spec 004 hooks) per FR-012 ordering. Pass: `decision_markdown=final_trade_decision`, `state=state`, `bull_mode=config.get("forward_catalyst_bull_mode", "active")`, `bear_mode=config.get("forward_catalyst_bear_mode", "shadow")`, `bull_threshold=config.get("forward_catalyst_bull_threshold", 0.60)`, `bear_threshold=config.get("forward_catalyst_bear_threshold", 0.50)`, `model=config.get("forward_catalyst_model", "claude-opus-4-7")`, `max_rationale_chars=config.get("forward_catalyst_max_rationale_chars", 2000)`, `llm=None` (production passes None; tests inject). Wrap in try/except that mirrors the existing spec 003 + spec 004 + spec 006 wraps (per FR-010); merge the returned annotation into the result dict at `result["forward_catalyst"] = annotation`. Depends on T008.

**Checkpoint**: At this point US1 is functional. Operator can enable the filter via PARAMS.json and observe both shadow + active mode behavior. **MVP delivered.** All 6 US1 acceptance scenarios from spec.md pass.

---

## Phase 4: User Story 2 - Bear-side shadow-mode observation (Priority: P2)

**Goal**: When `bear_mode="shadow"` (the default), the filter records `would_fire_bear=True` annotations on bearish commits where `bear_case_priced_in > bear_threshold`, but does NOT modify the rating. After 20+ propagates of shadow observation, operator can review + flip to `bear_mode="active"`.

**Independent Test**: Run a propagate against NVDA where mocked `bear_case_priced_in=0.65` (above 0.50). With `bear_mode="shadow"` (default), verify rating remains Underweight + `state["forward_catalyst"]["would_fire_bear"] == True` + `fired_bear == False`. With `bear_mode="active"`, verify rating is Hold.

### Tests for User Story 2

- [X] T019 [P] [US2] Add `test_forward_catalyst_bear_shadow_records_would_fire_only` to `tests/test_portfolio_manager_filter_integration.py`: mocked LLM returns `bear_case_priced_in=0.65`, `bear_mode="shadow"` (default), pre-rating Underweight; verify `would_fire_bear=True`, `fired_bear=False`, rating remains Underweight; covers US2 acceptance scenario 1
- [X] T020 [P] [US2] Add `test_forward_catalyst_bear_active_downgrades_underweight` to `tests/test_portfolio_manager_filter_integration.py`: mocked LLM returns `bear_case_priced_in=0.65`, `bear_mode="active"`; verify rating downgraded to Hold + `fired_bear=True`; covers US2 acceptance scenario 2
- [X] T021 [P] [US2] Add `test_forward_catalyst_bear_active_downgrades_sell` to `tests/test_portfolio_manager_filter_integration.py`: same setup but PM rating is Sell; verify rating downgraded to Hold; covers US2 acceptance scenario 3
- [X] T022 [P] [US2] Add `test_forward_catalyst_bear_does_not_act_on_hold` to `tests/test_portfolio_manager_filter_integration.py`: mocked LLM returns `bear_case_priced_in=0.65`, `bear_mode="active"`, but pre-rating is Hold (e.g., A3 already fired); verify rating unchanged (no fire); covers US2 acceptance scenario 4
- [X] T023 [P] [US2] Add `test_forward_catalyst_default_bear_shadow_never_modifies_rating` to `tests/test_forward_catalyst_filter.py`: parameterize over 25 mocked-LLM propagates with `bear_mode="shadow"` (default) + various score combinations; assert zero rating modifications + non-zero `would_fire_bear` annotations; covers SC-011 (Shadow-mode integrity for bear side)

### Implementation for User Story 2

- [X] T024 [US2] Verify the `evaluate_forward_catalyst` implementation (T008) correctly handles the bear-side branch: mode dispatch, threshold check, would_fire_bear computation, fire only if `bear_mode="active"`, never modify rating in shadow mode. This is a verification-and-tightening pass on T008's existing implementation, not a separate function.

**Checkpoint**: US1 + US2 both functional. Bull-side fires; bear-side observes in shadow mode. Operators can opt to flip bear-side to active after the 20+-propagate observation period.

---

## Phase 5: User Story 3 - Operator audit clarity (Priority: P2)

**Goal**: Operator inspecting `state["forward_catalyst"]` sees a populated dict with all 16 fields documented in `contracts/annotation_schema.md` so they can filter the corpus by `fired_bull` / `fired_bear` / `bull_case_priced_in` / etc. for per-side α attribution distinct from A3 / spec 003 / spec 004 / spec 006.

**Independent Test**: Run a small corpus through the harness with bull-mode=shadow (so all annotations are captured without firing). Inspect each `state["forward_catalyst"]` annotation; verify the fields are populated correctly per the schema.

### Tests for User Story 3

- [X] T025 [P] [US3] Add `test_annotation_active_fires_populates_all_16_fields` to `tests/test_forward_catalyst_filter.py`: mode=active + bull_case_priced_in above threshold → all 16 fields populated per `contracts/annotation_schema.md` schema; covers US3 acceptance scenario 1
- [X] T026 [P] [US3] Add `test_annotation_llm_failure_skipped_with_error_field` to `tests/test_forward_catalyst_filter.py`: mocked LLM raises exception → `skipped="llm_failed"`, `error` populated, scores None, rating unchanged; covers US3 acceptance scenario 2
- [X] T027 [P] [US3] Add `test_annotation_off_returns_none_or_off_skipped` to `tests/test_forward_catalyst_filter.py`: both modes off → annotation dict OR None per implementer's choice (both forms documented as valid in contract); covers US3 acceptance scenario 3
- [X] T028 [P] [US3] Add `test_annotation_invariants_per_data_model` to `tests/test_forward_catalyst_filter.py`: invariants 1-8 from `data-model.md` "Validation invariants"; one assert per invariant; covers schema-level audit guarantees
- [X] T029 [P] [US3] Add `test_audit_corpus_filter_by_fired_bull_and_score` to `tests/test_forward_catalyst_filter.py`: build a list of 6 synthetic annotations (2 bull-fired, 2 bear-fired, 2 not-fired), verify Python filters `[a for a in annotations if a["fired_bull"]]` and `[a for a in annotations if a["bull_case_priced_in"] is not None and a["bull_case_priced_in"] > 0.7]` return correct subsets; matches the corpus-audit pattern in `quickstart.md` Walkthrough 1

### Implementation for User Story 3

- [X] T030 [US3] Verify the annotation builder in `evaluate_forward_catalyst` (T008) populates ALL 16 fields specified in `contracts/annotation_schema.md` regardless of which path is taken (off / skipped / not-fired / fired). Add explicit field-by-field initialization to a default dict at the function entry; mutate fields as the function progresses; assert all 16 fields are present in the returned dict before returning.

**Checkpoint**: US1 + US2 + US3 all functional. Audit annotation fields are persisted, queryable, and distinguish all four spec-007 outcomes (bull-fire / bear-fire / would-fire-only / no-fire).

---

## Phase 6: User Story 4 - Constitution v1.4.0 amendment (Priority: P3)

**Goal**: As part of this spec landing, Constitution Principle VIII is amended to v1.4.0 with a new sub-section "Forward-catalyst-class validation gate" containing the three criteria (discrim ≥ +5pp + cohort hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first). Constitution version bumps from 1.3.0 → 1.4.0 (MINOR per added/amended principle rule).

**Independent Test**: After landing, verify `.specify/memory/constitution.md` Principle VIII has the new sub-section + version bump + footer entry. Verify CLAUDE.md "eight principles" wording remains correct.

### Implementation for User Story 4

- [X] T031 [US4] Amend `.specify/memory/constitution.md` Principle VIII to add a new sub-section titled "Forward-catalyst-class validation gate" with text:
    > **Forward-catalyst-class filters require a corpus retrospective showing (1) discrimination ≥ +5pp in correct direction (PRIMARY), (2) cohort hit rate ≥ 60% (when target cohort named), (3) net Δα ≥ +0.5pp OR shadow-mode-first if (3) is unmeasurable on small retrospective corpus. Empirical basis: Class 3 Opus retrospective (2026-05-06) DECISIVELY PASSED bull-side at T=0.60 (discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp on n=33 fires). Bear-side passed criteria 1+2 with shadow-mode-first condition (criterion 3 net Δα +0.30pp just below the +0.5pp gate). Spec 007 ships as the first instance of this filter class.**
    Bump version 1.3.0 → 1.4.0 in header; update "Adopted" / "Last amended" lines + add prior-version footer entry referencing the v1.3.0 → v1.4.0 amendment.
- [X] T032 [US4] Update `CLAUDE.md` "eight principles" wording to add "(Principle VIII v1.4.0 amended 2026-05-06: forward-catalyst-class validation gate)" without changing the count (8 principles).
- [X] T033 [US4] Add `CHANGELOG.md` [Unreleased] entry referencing the v1.4.0 amendment + spec 007 as the trigger; ~6-line block under "Added (constitution v1.4.0 — Principle VIII forward-catalyst extension)".

**Checkpoint**: Constitution v1.4.0 amendment landed. Future forward-catalyst filters have an explicit precedent.

---

## Phase 7: SC-008 retrospective + Polish & Cross-Cutting Concerns

**Purpose**: SC-008 empirical-validation gate, retrospective script for the production-config validation, CLAUDE.md update, final test/ruff/mypy gate, manual smoke.

- [X] T034 [P] Create `scripts/forward_catalyst_retrospective.py` per R-6: extends `scripts/forward_catalyst_class3_retrospective.py` by loading config from `tradingagents.default_config.DEFAULT_CONFIG` (production thresholds + modes + model) and re-applying the production filter logic to the existing CSV. Reports per-side fire rates + cohort hit rates + verifies SC-008 acceptance criteria (bull ≥24/27, bear shadow ≥10/18). No new LLM cost — reuses cached scores from the Opus retrospective CSV.
- [X] T035 [P] Add `test_sc008_production_config_validation` to `tests/test_forward_catalyst_filter.py` per SC-008: load the production config + invoke the SC-008 logic from T034; assert bull-fires ≥24/27 + bear-shadow-fires ≥10/18. Marked `@pytest.mark.integration` so pre-commit's `pytest -m unit` skips it.
- [X] T036 [P] Update `CLAUDE.md` "Empirical filters" section to add a 6th bullet for spec 007: name the filter, mention the empirical motivation (Class 3 Opus retrospective DECISIVE PASS bull / shadow-mode-first bear), default-on bull / default-shadow bear status, threshold/mode/model config keys, the `state["forward_catalyst"]` annotation field, the SC-008 validation gate. Cross-link the spec dir, `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md`, the design doc, and the new retrospective script.
- [X] T037 Run full `pytest -q` suite (unit + integration markers) plus `ruff check .` plus `mypy tradingagents`; gate: existing 984 baseline tests still pass plus the ~30 added by this spec; ruff 0 errors; mypy ≤ 132 (current floor 126 + at most 6 from new code; flag if higher)
- [X] T038 Run `quickstart.md` Walkthrough 5 (SC-008 retrospective) end-to-end as a manual smoke test; record the bull/bear fire counts in the closing commit message. If gates fail, document the empirical finding in `claudedocs/spec-007-sc008-validation-<DATE>.md` and note that the spec's motivating premise needs revisiting.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. **BLOCKS** all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Independent of US2 / US3 / US4.
- **User Story 2 (Phase 4)**: Depends on Foundational completion + US1 (US2's verification depends on US1's wiring producing the annotation fields). Cannot run in parallel with US1 because both touch `portfolio_manager.py` / `forward_catalyst_filter.py`.
- **User Story 3 (Phase 5)**: Depends on Foundational completion + US1. Mostly verification + audit-pattern tests.
- **User Story 4 (Phase 6)**: Independent of US1 / US2 / US3. Constitution amendment + CLAUDE.md + CHANGELOG.md only.
- **Polish (Phase 7)**: Depends on US1 + US2 + US3 + US4 complete.

### User Story Dependencies

- **US1 (P1, MVP)**: Can start after Phase 2. **MVP-deliverable on its own** — operator gets bull-side default-on + bear-side default-shadow even if US3 + US4 haven't landed.
- **US2 (P2)**: Strictly depends on US1 (the bear-side branch shares the same function as the bull-side; US2's tests parameterize the same wiring).
- **US3 (P2)**: Depends on US1 (audit fields are emitted by US1's wiring). Mostly verification; can run in parallel with US2 if developer capacity allows.
- **US4 (P3)**: Independent — touches only docs (constitution + CLAUDE.md + CHANGELOG.md). Can run in parallel with any of US1-US3.

### Within Each User Story

- Tests can be batched in parallel within a phase (separate functions in the same test file).
- Implementation tasks within US1 are minimal because the heavy lifting is in Phase 2; T018 is sequential (touches portfolio_manager.py).

### Parallel Opportunities

**Within Phase 1**: T001 + T002 sequential (same file `default_config.py`); T003 + T004 + T005 [P] (3 different files).

**Within Phase 2**: T006 + T007 [P] (different functions, can be drafted in parallel); T008 sequential after T006 + T007 (same file). T009 [P] with T006-T008 as test-writing batch (separate file, no dependency on impl ordering).

**Within Phase 3 (US1)**: 8 test tasks T010-T017 all in parallel — separate functions in 2 test files (test_portfolio_manager_filter_integration.py + test_trading_graph.py). Implementation T018 sequential after tests (touches portfolio_manager.py).

**Within Phase 4 (US2)**: 5 test tasks T019-T023 in parallel; T024 verification pass on existing files.

**Within Phase 5 (US3)**: 5 test tasks T025-T029 in parallel; T030 verification pass.

**Within Phase 6 (US4)**: T031 sequential (single file constitution.md); T032 + T033 [P] (different files).

**Within Phase 7**: T034 + T035 + T036 [P] (different files); T037 + T038 sequential at end.

---

## Implementation Strategy

### MVP First (US1 + US4 in parallel)

1. Complete Phase 1: Setup (T001-T005) — ~30 min
2. Complete Phase 2: Foundational (T006-T009) — ~3h (filter logic + 28 unit tests + Pydantic schema + LLM call wiring)
3. Complete Phase 3: US1 (T010-T018) — ~2h (8 integration tests + 1 wiring task)
4. Run T037 (full test/lint/mypy gate) — ~5 min
5. **STOP and VALIDATE**: MVP complete. Operator can enable bull-side default-on + bear-side default-shadow + observe annotations.
6. **In parallel**: Phase 6 (US4 constitution amendment) — ~30 min, independent of US1.

### Incremental Delivery

1. Setup + Foundational + US1 → MVP (bull-side default-on works) → demo
2. Add US2 → bear-side shadow-mode observation works → ready for shadow-mode period
3. Add US3 → audit annotation fields persisted + queryable → operator can attribute α per filter
4. Add US4 → Constitution v1.4.0 amendment → methodology codified
5. Polish (T034-T038) → SC-008 retrospective + manual smoke + green test/ruff/mypy gate → ready to commit + push the branch

### Single-developer Strategy

Sequential in practice; [P] markers indicate which tasks can be batched in a single multi-tool-call message. Most useful at:
- Phase 1 setup files batch (T003 + T004 + T005 together)
- Phase 2 test-writing batch (T009 alongside T006-T008)
- Phase 3 US1 test-writing batch (T010-T017 in one batch, then implementation)
- Phase 4 US2 test-writing batch (T019-T023)
- Phase 5 US3 test-writing batch (T025-T029)
- Phase 6 US4 docs batch (T032 + T033 in parallel after T031)
- Phase 7 polish files in parallel (T034 + T035 + T036)

---

## Notes

- **[P] tasks** = different files, no dependencies — safe to batch in a single multi-tool-call message.
- **[Story] label** maps each task to its user story for traceability against `spec.md` acceptance scenarios.
- **Each user story is independently completable** within the constraint that US2 + US3 depend on US1's wiring producing the annotation fields. US4 is genuinely independent (different files entirely).
- **Pre-commit gate**: pytest unit tests must pass on every commit. T037 (full gate) is the polish-phase final gate; intermediate commits within phases must keep the unit-test suite green.
- **Cost discipline (Principle III)**: this implementation has T1 cost (no LLM API calls during testing because of mocking). Per-propagate cost addition (~$0.025 Opus) is the operational cost; documented in spec + quickstart.
- **LLM client reuse**: `tradingagents.llm_clients.factory.create_llm_client` is the canonical entry point per R-1. New code does NOT instantiate `anthropic.Anthropic()` directly.
- **Pydantic structured output reuse**: `llm.with_structured_output(CasePricedInScore)` per R-2 + the `second_opinion.py` precedent. Try/except around both `with_structured_output` AND `invoke()` per the resilience pattern.
- **AgentState declaration (T005)**: load-bearing per CLAUDE.md note + the spec 003 + spec 004 + spec 006 precedents. Without it, LangGraph silently drops the field from state merges.
- **Filter ordering (FR-012)**: spec 007 runs LAST in the chain (after A3 + spec 006 + spec 003/003.5 + spec 004). Documented in plan.md + portfolio_manager.py wiring comments.
- **Constitution VIII amendment (FR-015 + SC-009)**: included as part of this spec implementation, not separately. Codifies the methodology lesson AT THE TIME the first forward-catalyst filter ships.
- **After completion**: invoke `/speckit.analyze` for post-mortem if anything is worth recording structurally; otherwise the spec dir + commit history is the record.
