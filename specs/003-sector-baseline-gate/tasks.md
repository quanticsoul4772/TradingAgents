---

description: "Task list for Sector-Baseline Fallback for Contrarian Gate"
---

# Tasks: Sector-Baseline Fallback for Contrarian Gate

**Input**: Design documents from `specs/003-sector-baseline-gate/`
**Prerequisites**: spec.md ✓, plan.md ✓, research.md ✓, data-model.md ✓, contracts/ (2) ✓, quickstart.md ✓

**Tests**: Included throughout. Spec requires ≥90% line coverage on new code (SC-007). Tests are written alongside implementation (not strict TDD-first); pre-commit's `pytest -m unit` gate enforces unit-test pass on every commit. Integration-marked test for SC-002 byte-identity regression-guard runs against real state-log fixtures.

**Organization**: Tasks grouped by user story (US1, US2 from spec.md). Within each story, [P] marks parallel-safe tasks (different files, no incomplete dependencies in the same phase).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Single-project Python library extension per `plan.md` Structure Decision:
- Source: `tradingagents/signals/` (extends existing `contrarian_gate.py` + adds `sector_baseline.py`)
- Config: `tradingagents/default_config.py` (extend `TradingAgentsConfig` TypedDict + DEFAULT_CONFIG)
- Tests: `tests/` (flat)
- Docs: `CLAUDE.md` (existing)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the new config keys + scaffold the new module so US1's tests have something to import.

- [X] T001 Add `contrarian_gate_sector_fallback_enabled: bool` and `contrarian_gate_sector_floor: int` keys to `TradingAgentsConfig` TypedDict in `tradingagents/default_config.py` (alphabetical placement next to existing contrarian_gate_* keys; defaults `True` and `20` respectively per R-5 + FR-003)
- [X] T002 Add the same two keys to `DEFAULT_CONFIG` in `tradingagents/default_config.py` with `True` and `20` values + a 4-line comment cross-referencing `specs/003-sector-baseline-gate/spec.md` and explaining the ablation flag
- [X] T003 [P] Create empty `tradingagents/signals/sector_baseline.py` with module docstring referencing the spec; placeholder so US2 tests can import without circular-import issues during test collection

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The sector-pool aggregator is required by both US1 (cold-start firing) and US2 (audit annotation). Build it once, here, before either story phase begins.

**⚠️ CRITICAL**: Both user stories depend on `aggregate_sector_pool()` existing.

- [X] T004 [P] Implement `SectorPool` frozen dataclass in `tradingagents/signals/sector_baseline.py` per `data-model.md` (`sector: str`, `before_date: date`, `values: list[float]`, `n: int`, `contributors: dict[str, int]`); cross-reference `contracts/sector_pool_function.md` for field semantics
- [X] T005 Implement `aggregate_sector_pool(sector, before_date, *, sectors_cache_path, state_logs_root, feature_callable, log_filename_pattern="full_states_log_*.json") -> SectorPool` in `tradingagents/signals/sector_baseline.py` per `contracts/sector_pool_function.md`; depends on T004; behavior: empty pool for `"Unknown"`/empty sector (R-4); strict-prior cutoff via filename-date parse (R-2); deterministic sorted iteration (R-1, R-9); skip corrupt JSON / featurizer failures with warning logs (resilience pattern from `scripts/contrarian_gate_retrospective.py`)
- [X] T006 [P] Create `tests/test_sector_baseline.py` with unit tests covering ALL 6 fixtures from `contracts/sector_pool_function.md` test-fixtures section: `test_empty_pool_for_unknown_sector`, `test_empty_pool_for_empty_string_sector`, `test_strict_prior_cutoff_excludes_same_day_observations`, `test_aggregates_across_multiple_same_sector_tickers`, `test_corrupt_state_log_skipped_with_warning`, `test_iteration_order_deterministic`, `test_feature_callable_failure_skips_observation`; uses tmp_path with synthetic state-log JSON files (no live filesystem dependency); covers T004 + T005

**Checkpoint**: Foundation ready. `SectorPool` and `aggregate_sector_pool` are available for the gate's fallback path. User story implementation can begin.

---

## Phase 3: User Story 1 - Cold-start ticker gets gate coverage via sector baseline (Priority: P1) 🎯 MVP

**Goal**: When a ticker has < 20 prior state logs, the contrarian gate consults the sector-pool baseline. Gate fires (active mode) or annotates as would-fire (shadow mode) when the current `bull_keyword_count` exceeds the 80th percentile of the pooled distribution.

**Independent Test**: Hand-craft state-log fixtures with 8 Tech tickers having varied `bull_keyword_count` history. Run the gate against a new Tech ticker (per-ticker N=0) with current `bull_keyword_count` = 75 in `active` mode. Verify the gate fires (downgrades Buy/OW → Hold) when the sector-pooled 80th percentile is ≤ 75; verify it doesn't fire when sector-pooled 80th percentile is > 75.

### Tests for User Story 1

- [X] T007 [P] [US1] Add `test_gate_baseline_per_ticker_when_history_thick` to `tests/test_contrarian_gate_fallback.py` (NEW file): per-ticker N=25 → uses per_ticker baseline regardless of sector pool size; sector path NOT consulted; `gate_baseline == "per_ticker"`
- [X] T008 [P] [US1] Add `test_gate_baseline_sector_when_per_ticker_thin` to `tests/test_contrarian_gate_fallback.py`: per-ticker N=0, sector pool N=80 with current value at 92nd percentile → `gate_baseline == "sector"`, `would_fire == True`, `percentile == 92`
- [X] T009 [P] [US1] Add `test_gate_baseline_none_when_both_thin` to `tests/test_contrarian_gate_fallback.py`: per-ticker N=5, sector pool N=10 (both below floor) → `gate_baseline == "none"`, `would_fire == False`, `skipped == "insufficient_history"`, `percentile is None`
- [X] T010 [P] [US1] Add `test_unknown_sector_collapses_to_none` to `tests/test_contrarian_gate_fallback.py`: ticker's cached sector is `"Unknown"` → sector pool not consulted → `gate_baseline == "none"` per FR-008/R-4
- [X] T011 [P] [US1] Add `test_active_mode_downgrades_when_sector_baseline_fires` to `tests/test_contrarian_gate_fallback.py`: per-ticker thin, sector pool fires, `mode=="active"`, original PM rating `Overweight` → `pm_rating_post_gate == "Hold"` (per `contrarian_gate_target` default), `gate_fired == True`
- [X] T012 [P] [US1] Add `test_shadow_mode_annotates_but_does_not_downgrade_when_sector_fires` to `tests/test_contrarian_gate_fallback.py`: same setup as T011 but `mode=="shadow"` → `pm_rating_post_gate == pm_rating_pre_gate == "Overweight"`, `would_fire == True`, `gate_fired == False`
- [X] T013 [P] [US1] Add `test_off_mode_emits_no_annotation` to `tests/test_contrarian_gate_fallback.py`: `mode=="off"` → no `state["contrarian_gate"]` key emitted; preserves Spec 003 off-mode semantics
- [X] T014 [P] [US1] Add `test_ablation_flag_disables_sector_fallback` to `tests/test_contrarian_gate_fallback.py`: `contrarian_gate_sector_fallback_enabled=False`, per-ticker thin, sector pool would-fire if enabled → `gate_baseline == "none"`, `would_fire == False`; matches Spec 003 byte-identity (SC-005)
- [X] T015 [P] [US1] Add `test_per_ticker_floor_strict_check` to `tests/test_contrarian_gate_fallback.py`: per-ticker N exactly equals `per_ticker_floor` → uses per_ticker baseline (boundary check, ≥ floor passes)

### Implementation for User Story 1

- [X] T016 [US1] Modify `ContrarianGate.compute_annotation()` in `tradingagents/signals/contrarian_gate.py` to implement the fallback ladder per `data-model.md` "State transitions" section: (a) if `mode == "off"`: existing early-return path unchanged; (b) compute `feature_value` as today; (c) compute `per_ticker_history`; (d) if `len(per_ticker_history) >= per_ticker_floor`: use per-ticker baseline (existing path), set `gate_baseline = "per_ticker"`; (e) elif `config.contrarian_gate_sector_fallback_enabled`: call `tradingagents.signals.sector_baseline.aggregate_sector_pool(sector, before_date, ...)`, if pool size >= sector_floor use sector baseline + set `gate_baseline = "sector"`; (f) else: emit `gate_baseline = "none"` + skipped="insufficient_history". Depends on T005.
- [X] T017 [US1] Extend `GateAnnotation` (the dict shape returned by `compute_annotation`) in `tradingagents/signals/contrarian_gate.py` with `gate_baseline` (Literal["per_ticker", "sector", "none"]), `n_history_per_ticker` (int), `n_history_sector` (int) per `contracts/gate_annotation_extended.md`; preserve existing fields unchanged; assert the 4 invariants from `data-model.md` Validation invariants section before returning the dict
- [X] T018 [US1] Wire the new config keys into `ContrarianGate.__init__` in `tradingagents/signals/contrarian_gate.py`: read `contrarian_gate_sector_fallback_enabled` (default True from FR-010 / R-5) and `contrarian_gate_sector_floor` (default 20 from FR-003), store on the gate instance; depends on T001 + T002
- [X] T019 [US1] Resolve sector for current ticker via `tradingagents/paper/sectors.py::get_sector(ticker, sectors_cache_path)` inside `ContrarianGate.compute_annotation` per R-10; the cache path comes from `paper_state_dir / "sectors.json"` per Spec 002 convention; if `paper_state_dir` config key missing, default to `~/.tradingagents/paper/sectors.json`; pass returned sector into `aggregate_sector_pool` call from T016

**Checkpoint**: At this point US1 is functional. Cold-start tickers can fire the gate via sector pool. **MVP delivered.** All US1 acceptance scenarios from spec.md pass.

---

## Phase 4: User Story 2 - Operator distinguishes per-ticker vs sector firings in audit (Priority: P2)

**Goal**: Operator inspecting `state["contrarian_gate"]` sees `gate_baseline` field with values `"per_ticker"` / `"sector"` / `"none"` so they can filter firings by confidence level when computing realized α attribution.

**Independent Test**: Inspect contrarian_gate annotations across a mixed corpus (some thick-history tickers, some cold-start) using the corpus-audit script from `quickstart.md` Walkthrough 3. Verify the per-baseline counts match the expected breakdown for the test fixture.

### Tests for User Story 2

- [X] T020 [P] [US2] Add `test_n_history_alias_matches_per_ticker_baseline` to `tests/test_contrarian_gate_fallback.py`: when `gate_baseline == "per_ticker"`, the legacy `n_history` field equals `n_history_per_ticker` (backward-compat alias per R-6)
- [X] T021 [P] [US2] Add `test_n_history_alias_matches_sector_baseline` to `tests/test_contrarian_gate_fallback.py`: when `gate_baseline == "sector"`, the legacy `n_history` field equals `n_history_sector`
- [X] T022 [P] [US2] Add `test_annotation_contains_both_n_history_fields_always` to `tests/test_contrarian_gate_fallback.py`: regardless of which baseline fired, both `n_history_per_ticker` and `n_history_sector` are present in the annotation (so operator audit can see both pool sizes)
- [X] T023 [P] [US2] Add `test_audit_corpus_filter_by_baseline` to `tests/test_contrarian_gate_fallback.py`: build a corpus of 6 synthetic state logs (2 per-ticker fires, 2 sector fires, 2 none) and verify a python filter expression like `[s for s in logs if s["contrarian_gate"]["gate_baseline"] == "sector"]` returns the correct subset (matches `quickstart.md` Walkthrough 3 audit pattern)

### Implementation for User Story 2

- [X] T024 [US2] Verify the `n_history` alias semantics in `tradingagents/signals/contrarian_gate.py` per R-6: when emitting the annotation dict in `compute_annotation`, set `n_history` to whichever pool drove the decision (`n_history_per_ticker` if `gate_baseline=="per_ticker"`, `n_history_sector` if `"sector"`, `0` if `"none"`). This may already be done in T017's invariant assertion; this task ensures the BACKWARD-COMPAT semantics specifically (existing consumers reading `n_history` continue to get a meaningful value)
- [X] T025 [US2] Confirm the persistence path: the new annotation fields must flow through `state["contrarian_gate"]` to the persisted JSON state log. Per commit `4c14d0f` (2026-05-06) the state-log writer in `tradingagents/graph/trading_graph.py:425-453` already includes `contrarian_gate` in the whitelist; the annotation dict's NEW fields ride that path automatically since the writer dumps the whole dict. **Verify** by inspecting `_log_state` and confirming no field-level filtering occurs that would drop the new keys; if any filtering exists, extend it.

**Checkpoint**: US1 + US2 both functional. Audit annotation fields are persisted, queryable, and distinguish per-ticker vs sector firings.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Regression-guard tests for SC-002 byte-identity, CLAUDE.md updates, and a one-line bump to existing scripts that consume the contrarian gate annotation.

- [X] T026 [P] Add `test_byte_identity_with_fallback_disabled` to `tests/test_contrarian_gate.py` (extend existing file, not the new fallback test file): integration-marked test (`@pytest.mark.integration`) that runs the gate over the existing real state-log corpus at `~/.tradingagents/logs/` with `contrarian_gate_sector_fallback_enabled=False`, then asserts the `gate_fired` decisions match what Spec 003's per-ticker-only behavior would have produced (per SC-002). Skip with clear message if `~/.tradingagents/logs/` is empty.
- [X] T027 [P] Update `CLAUDE.md` Architecture section's "Spec 003 contrarian gate" paragraph to note: (a) the sector-baseline fallback (Spec 003.5 / `specs/003-sector-baseline-gate/`); (b) the new `gate_baseline` annotation field with three possible values; (c) the `contrarian_gate_sector_fallback_enabled` ablation flag; (d) the empirical motivation (SC-003 Financials investigation revealed cold-start gap). Cross-link `claudedocs/sc003-financials-gate-check-2026-05-06.md`.
- [ ] T028 [P] Update `scripts/sc003_financials_gate_check.py` to support `--sector-fallback` / `--no-sector-fallback` CLI flags (typer Option) so the SC-003 Financials ablation comparison from `quickstart.md` Walkthrough 2 works as documented; the script already does its own offline gate-firing simulation, so it needs to call `aggregate_sector_pool` when the flag is on
- [ ] T029 [P] Update `scripts/contrarian_gate_retrospective.py` to surface the `gate_baseline` field in its output table so per-baseline α attribution is visible alongside the existing per-floor breakdown
- [ ] T030 Run full `pytest -q` suite (unit + integration markers) plus `ruff check .` plus `mypy tradingagents`; gate: 895+ baseline unit tests still pass plus the new ~17 added by this spec; ruff 0 errors; mypy ≤ 132 (current floor 129 + at most 3 from new code; flag if higher)
- [ ] T031 Run `quickstart.md` Walkthrough 3 (corpus-level audit by baseline source) end-to-end as a manual smoke test against your real `~/.tradingagents/logs/` corpus; record the per_ticker / sector / none counts in the closing commit message for verification

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T002 add config keys read by T018; T003 is the placeholder file T004-T005 fill in). **BLOCKS** both user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Independent of US2.
- **User Story 2 (Phase 4)**: Depends on Foundational completion AND US1 (US2's implementation tasks T024-T025 verify properties of the annotation that US1 produces). Cannot run in parallel with US1 because both extend `tradingagents/signals/contrarian_gate.py`.
- **Polish (Phase 5)**: Depends on US1 + US2 complete. Manual smoke (T031) last.

### User Story Dependencies

- **US1 (P1, MVP)**: Can start after Phase 2. **MVP-deliverable on its own** — operator gets cold-start gate coverage even if US2's audit-clarity tasks haven't landed.
- **US2 (P2)**: Strictly depends on US1 (the audit fields it verifies are emitted by US1's implementation tasks). Cannot run in parallel.

### Within Each User Story

- Tests can be batched in parallel within a phase (different functions in the same test file ARE safe to write in parallel since they don't conflict at the function level; if implementer prefers, write them one at a time).
- Implementation tasks within US1 are sequential because T016, T017, T018, T019 all extend the same file (`contrarian_gate.py`).

### Parallel Opportunities

**Within Phase 1**: T001 + T002 modify the same file (`default_config.py`) — keep sequential. T003 is independent.

**Within Phase 2**: T004 + T006 are [P] (different files). T005 sequential after T004 (same file). T006 can be batched with T004 in a single multi-tool-call message since the test file imports T004's `SectorPool` only.

**Within Phase 3 (US1)**: All 9 test tasks (T007-T015) are [P] — they're separate test functions in the same new file (`test_contrarian_gate_fallback.py`). Implementation tasks T016-T019 are sequential (same file).

**Within Phase 4 (US2)**: All 4 test tasks (T020-T023) are [P]. Implementation tasks T024-T025 are sequential (same file).

**Within Phase 5**: T026, T027, T028, T029 are [P] — all different files. T030 + T031 sequential at end.

---

## Parallel Example: Phase 2 Foundational

After Phase 1 setup completes, fire these in parallel (different files, no inter-dependencies):

```bash
# Two implementation tasks in parallel (T004 in sector_baseline.py, T006 test fixtures):
Task: "Implement SectorPool dataclass in tradingagents/signals/sector_baseline.py"   # T004
Task: "Create tests/test_sector_baseline.py with 6 unit-test fixtures"               # T006

# Then T005 sequentially after T004 (same file, function depends on dataclass):
Task: "Implement aggregate_sector_pool() in tradingagents/signals/sector_baseline.py" # T005
```

## Parallel Example: Phase 3 US1

After Phase 2 completes:

```bash
# All 9 test functions in parallel (separate functions in the same new file):
Task: "Add test_gate_baseline_per_ticker_when_history_thick to test_contrarian_gate_fallback.py"  # T007
Task: "Add test_gate_baseline_sector_when_per_ticker_thin to test_contrarian_gate_fallback.py"   # T008
Task: "Add test_gate_baseline_none_when_both_thin to test_contrarian_gate_fallback.py"           # T009
... (T010-T015 same pattern)

# Then implementation sequentially (all extend contrarian_gate.py):
Task: "Modify compute_annotation to implement fallback ladder"                                    # T016
Task: "Extend GateAnnotation dict with new fields + invariant assertions"                         # T017
Task: "Wire new config keys into ContrarianGate.__init__"                                         # T018
Task: "Resolve sector via paper/sectors.py::get_sector"                                           # T019
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001-T003) — ~15 min
2. Complete Phase 2: Foundational (T004-T006) — ~1.5h (aggregator + tests)
3. Complete Phase 3: User Story 1 (T007-T019) — ~2h (9 tests + 4 implementation tasks)
4. **STOP and VALIDATE**: Run T026 (SC-002 byte-identity regression-guard) plus the 9 US1 tests. If all green and SC-002 holds, MVP complete.
5. Operator demo: re-run `scripts/sc003_financials_gate_check.py` (after T028 lands the CLI flags) on the same SC-003 Financials corpus and observe whether sector fallback now fires on tickers that previously couldn't.

### Incremental Delivery

1. Setup + Foundational + US1 → MVP (cold-start gate coverage works) → demo
2. Add US2 → Audit annotation fields persisted + queryable → operator can attribute α per baseline
3. Polish (T026-T031) → CLAUDE.md updated + scripts surface gate_baseline + green test/ruff/mypy gate → ready to commit + push the branch

### Single-developer Strategy

Sequential in practice; [P] markers indicate which tasks can be batched in a single multi-tool-call message. Most useful at:
- Phase 2 test-writing batch (T006 alongside T004)
- Phase 3 US1 test-writing batch (T007-T015 in one batch, then implementation in another)

---

## Notes

- **[P] tasks** = different files, no dependencies — safe to batch in a single multi-tool-call message.
- **[Story] label** maps each task to its user story for traceability against `spec.md` acceptance scenarios.
- **Each user story is independently completable** within the constraint that US2's verification depends on US1's implementation. This matches the spec's intent — US1 is the MVP, US2 is operational ergonomic on top.
- **Pre-commit gate**: pytest unit tests must pass on every commit. T030 (full suite + ruff + mypy) is the polish-phase gate; intermediate commits within phases must keep the unit-test suite green.
- **Cost discipline (Principle III)**: this entire implementation has T1 cost (zero LLM API calls per FR-006/SC-006). The validation walkthrough in `quickstart.md` Walkthrough 4 (ablation experiment) IS T2-T3 cost depending on the experiment scope; HYPOTHESIS.md should justify per the constitution.
- **Avoid**: cross-story dependencies that break independence beyond the documented US2-needs-US1 ordering. Avoid: vague tasks ("improve fallback") — every task above names exact files + precise behavior.
- **After completion**: invoke `/speckit.analyze` for post-mortem if anything is worth recording structurally; otherwise the spec dir + commit history is the record.
