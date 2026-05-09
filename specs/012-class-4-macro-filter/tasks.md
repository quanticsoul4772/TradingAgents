---

description: "Task list for Spec 012 (Class 4 Macro-Environment Filter) implementation"
---

# Tasks: Class 4 Macro-Environment Filter (Spec 012)

**Input**: Design documents from `/specs/012-class-4-macro-filter/`
**Prerequisites**: spec.md (✅ PR #194), plan.md (✅ PR #194)

**Tests**: REQUIRED. Spec mandates ≥10 unit tests + ≥3 PM integration tests + ≥2 state-log regression tests per SC-001 through SC-009 + SC-011. Tests land in same PR as implementation per existing project convention.

**Organization**: Tasks grouped by Branch A user story (Branch B = future amendment, no tasks here).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (A1 = operator-runs-shadow, A2 = researcher-reviews-fires)
- Include exact file paths in descriptions

## Path Conventions

Single-package extension to existing `tradingagents` Python package per plan.md:

- Filter helper module: `tradingagents/agents/utils/macro_environment_filter.py`
- PM-hook integration: `tradingagents/agents/managers/portfolio_manager.py`
- Config keys: `tradingagents/default_config.py`
- AgentState TypedDict: `tradingagents/agents/utils/agent_states.py`
- State log whitelist: `tradingagents/graph/trading_graph.py`
- Unit tests: `tests/test_macro_environment_filter.py`
- Integration tests: `tests/test_class_4_pm_integration.py`
- Shadow audit script: `scripts/class4_macro_shadow_audit.py`
- Per-spec retrospective: `claudedocs/spec-012-class-4-retrospective-<date>.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed. All infrastructure already in place per existing tradingagents package + pytest configuration.

- [ ] T001 Verify existing pytest collection works on the feature branch via `pytest --collect-only -q tests/` (no new fixtures or config needed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add 3 new TradingAgentsConfig keys + AgentState TypedDict declaration. Blocking prerequisites for both user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T002 Add 3 new TradingAgentsConfig keys to `tradingagents/default_config.py`: `class_4_macro_bear_mode` (Literal["off","shadow","active"], default "shadow"), `class_4_macro_bull_mode` (Literal["off","shadow","active"], default "off"), `class_4_macro_vix_threshold` (float, default 18.0). Add to BOTH the `TradingAgentsConfig` TypedDict AND the `DEFAULT_CONFIG` dict per the existing pattern.

- [ ] T003 Add `class_4_macro: Annotated[dict, ...]` to AgentState TypedDict in `tradingagents/agents/utils/agent_states.py` per the Spec 003 silent-drop precedent.

- [ ] T004 Add `"class_4_macro"` to the `_log_state` whitelist in `tradingagents/graph/trading_graph.py` so the dict appears in saved state logs (mirrors Spec X-1 PR #92 pattern).

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story A1 — Operator runs propagates with Class 4 in shadow (Priority: P1)

**Independent test criteria**: a propagate with `class_4_macro_bear_mode="shadow"` + a bear pre_rating produces `state["class_4_macro"]` dict with 7 fields including `would_fire_bear` (computed) AND `fired_bear=False` AND `pre_rating == post_rating`.

- [ ] T005 [P] [A1] Create `tradingagents/agents/utils/macro_environment_filter.py` with public function `maybe_suppress_bear_macro(final_trade_decision: str, ticker: str, trade_date: str, bear_mode: Literal["off","shadow","active"]="shadow", vix_threshold: float=18.0) -> tuple[str, dict | None]`. Returns `(post_rating_markdown, annotation_dict)`. annotation_dict has 7 fields per spec FR-008 OR `None` if `bear_mode == "off"`.

- [ ] T006 [P] [A1] Add internal helper `_vix_snapshot(trade_date: str) -> float | None` in same module. LRU-cached yfinance VIX history fetch. Per FR-006 (process-lifetime in-process cache, no persistence). Per FR-007 graceful failure (returns `None` on yfinance exception).

- [ ] T007 [P] [A1] Add internal helper `_macro_30d_changes(trade_date: str) -> dict` in same module. Returns dict with `vix_30d_pct`, `tnx_30d_pct`, `dxy_30d_pct` keys. Same yfinance + LRU + graceful-failure pattern as T006.

- [ ] T008 [P] [A1] Add internal helper `_classify_bear_macro(vix: float | None, threshold: float) -> bool` in same module. Pure threshold logic (returns True iff `vix is not None and vix < threshold`). No I/O.

- [ ] T009 [A1] Wire `maybe_suppress_bear_macro` into `tradingagents/agents/managers/portfolio_manager.py` PM hook chain. Insert BETWEEN A3 (`maybe_suppress_bear_rating`) and Spec X-1 (institutional rotation) per FR-004 smallest-sample-last ordering. When `class_4_macro_bear_mode != "off"` AND pre_rating in {Underweight, Sell}: invoke filter; record returned dict in state_log_extras. When `class_4_macro_bear_mode == "shadow"`: filter records would_fire but does NOT modify rating. When `"active"`: filter overwrites Rating header to "Hold" if would_fire.

- [ ] T010 [A1] Create `tests/test_macro_environment_filter.py` with ≥10 unit tests:
  - 2 tests: `_vix_snapshot` LRU caching (1 yfinance call across 2 same-date invocations) + graceful failure (mocked yfinance raise → returns None)
  - 2 tests: `_macro_30d_changes` returns 3-key dict + graceful failure
  - 4 tests: `_classify_bear_macro` boundary cases (VIX < 18 fires; VIX == 18 does NOT fire per FR-002 strict-less-than; VIX > 18 does not fire; vix=None does not fire)
  - 2 tests: `maybe_suppress_bear_macro` mode-specific (off mode returns None annotation; shadow + active mode return 7-field dict)

- [ ] T011 [A1] Create `tests/test_class_4_pm_integration.py` with ≥3 PM integration tests covering off / shadow / active modes. Pattern follows `tests/test_institutional_rotation_pm_integration.py` (Spec X-1 PR #92 precedent): mock LLM + config injection + autouse fixture disabling other LLM-calling filters. Verify SC-005 (shadow no-modify) + SC-006 (active suppresses to Hold) + SC-003 (PM-hook position correct) + SC-004 (state annotation completeness).

**Checkpoint**: A1 complete — operator can run propagates with Class 4 in shadow mode + state log captures would-fire decisions.

---

## Phase 4: User Story A2 — Researcher reviews shadow-mode fire log (Priority: P2)

**Independent test criteria**: `python scripts/class4_macro_shadow_audit.py` walks state logs + outputs would-fire enumeration + realized α + default-on-flip-readiness report when 30+ would-fire instances accumulate.

- [ ] T012 [A2] Create `scripts/class4_macro_shadow_audit.py` walking `~/.tradingagents/results/<state_log_dir>/*.json` for `state["class_4_macro"]` dicts where `would_fire_bear == True`. Computes per-fire realized α via `tradingagents.graph.trading_graph.fetch_returns`. Outputs:
  1. Per-fire enumeration table (ticker / date / vix_snapshot / vix_30d_pct / would_fire / realized α at 21d)
  2. Cumulative would-fire count
  3. Mean realized α on would-fire cohort
  4. Default-on-flip-readiness verdict per Spec 012 SC-010 (`n ≥ 30 fires AND mean realized α ≥ -1pp at 21d`)

- [ ] T013 [P] [A2] Add 1 unit test for `class4_macro_shadow_audit.py` verifying it parses a fixture state log + outputs expected enumeration row count. Tests in `tests/test_class4_macro_shadow_audit.py`.

**Checkpoint**: A2 complete — researcher can build the n≥30 evidence base for default-on flip per Constitution VIII v1.4.0.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T014 Add 2 state-log persistence regression tests to `tests/test_state_log_persistence.py` (NEW or extend existing) verifying `class_4_macro` field persists in saved state logs across off / shadow modes per FR-008.

- [ ] T015 [P] Update `docs/SIGNALS.md` with new "Class 4 macro-environment filter" sub-section per spec Phase 7. Cohort-validation table + 3-mode comparison.

- [ ] T016 [P] Update `RESEARCH_FINDINGS.md` "Filter portfolio status" table — flip Spec 012 row from CONDITIONAL DRAFT to active SHADOW mode entry. Per PR #196 row pre-scaffolded.

- [ ] T017 Create `claudedocs/spec-012-class-4-retrospective-<date>.md` documenting the chain: 2026-05-09 retrospective PASS (PR #193) → spec drafting PR #194 → tasks/MVP/tests/polish PRs (this bundle) → SHADOW mode launch. Per Constitution VIII v1.4.1 (spec ships its retrospective).

---

## Implementation Strategy

**MVP scope**: T001–T011 (Phases 1+2+3). Ships the operator-facing shadow-mode capability + tests for that capability. Branch A complete.

**Increment 1 (post-MVP)**: T012–T013 (Phase 4 = A2 audit script). Ships the researcher-facing audit tooling for default-on flip evidence.

**Increment 2 (polish)**: T014–T017 (Phase 5). Ships state-log regression tests + docs + retrospective.

**Recommended PR breakdown**:
- PR #X+3 (MVP): T001–T011 (11 tasks; Phases 1+2+3) — primary code + unit tests + PM integration tests
- PR #X+4 (tests + audit): T012–T014 (3 tasks; Phase 4 + state-log regression)
- PR #X+5 (polish): T015–T017 (3 tasks; docs + RESEARCH_FINDINGS + retrospective)

**Effort estimate** (per plan.md): ~5h total across PRs #X+3 + #X+4 + #X+5.

## Parallelization opportunities

Within Phase 3 (User Story A1):
- T005, T006, T007, T008 can all run in parallel (different functions in the same module; independent)
- T010 + T011 can run in parallel (different test files)
- T009 must run sequentially after T005-T008 (depends on the public function existing)

Within Phase 5:
- T015 + T016 + T017 can run in parallel (different files; no shared dependencies)

## Cost discipline (Constitution III)

All tasks: $0 LLM cost. Filter operates on yfinance + arithmetic; no LLM call per propagate. Same cost profile as A3 + Spec X-1.

## Dependencies summary

- T001 → T002 → T003 → T004 → (T005, T006, T007, T008 in parallel) → T009 → (T010, T011 in parallel)
- T012 depends on T011 (state log format established)
- T013 depends on T012
- T014 depends on T009 (state annotation written)
- T015, T016, T017 depend on T009 (filter behavior documented)

## Cross-references

- `specs/012-class-4-macro-filter/spec.md` (PR #194)
- `specs/012-class-4-macro-filter/plan.md` (PR #194)
- `specs/091-c4-institutional-rotation/tasks.md` (Spec X-1 — same task structure)
- `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193 — verdict)
- Memory: `reference_speckit_6pr_workflow_pattern.md` (the bundle pattern)
