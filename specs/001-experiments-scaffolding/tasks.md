---
description: "Task list for experiments-scaffolding implementation"
---

# Tasks: Experiments Scaffolding

**Input**: Design documents from `/specs/001-experiments-scaffolding/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓ (4 contracts), quickstart.md ✓

**Tests**: Included. Each contract specifies its own test list; we honor them as TDD-ish tasks (test file written alongside or just-before implementation, not strictly red-green-refactor).

**Organization**: Tasks grouped by user story so P1 can ship as MVP without P2 or P3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependency on incomplete tasks in this list)
- **[Story]**: `[US1]` / `[US2]` / `[US3]` for user-story-specific tasks; absent for Setup, Foundational, and Polish phases
- Each task names the exact file path

## Path Conventions

Single project (per plan.md):
- Python source: `tradingagents/experiments/`
- Operator scripts: `scripts/`
- Tests: `tests/`
- Spec artifacts: `specs/001-experiments-scaffolding/`
- Experiment artifact dir: `experiments/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization for the new module.

- [ ] T001 Create directory `tradingagents/experiments/` with empty `__init__.py`
- [ ] T002 Create directory `experiments/` and add `experiments/.gitkeep` so the directory exists in fresh clones (per R-006)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helper module that all three user stories depend on. **No user story work can begin until this phase is complete.**

The three files in `tradingagents/experiments/` can be developed in parallel — different files, no inter-file dependencies. Their tests can also be developed in parallel.

### Implementation

- [ ] T003 [P] Implement experiment ID generation + validation in `tradingagents/experiments/ids.py`. Functions: `next_experiment_id(experiments_dir, slug, date=None)`, `validate_id(id_str) -> bool`, `parse_id(id_str) -> tuple[date, int, str]`. Use the regex `^\d{4}-\d{2}-\d{2}-\d{3}-[a-z0-9][a-z0-9-]{0,38}[a-z0-9]$` per `data-model.md`. Sequence number scans `experiments/` for `<date>-NNN-*` dirs, takes max + 1, zero-pads to 3 digits.
- [ ] T004 [P] Implement config-override parsing + application in `tradingagents/experiments/overrides.py`. Functions: `parse_override(s: str) -> tuple[str, Any]`, `apply_overrides(config: dict, overrides: list[str], allow_unknown: bool = True) -> dict`. Coercion order per R-003: int → float → bool ("true"/"false" case-insensitive) → null ("none"/"null") → str. Quoted values (`KEY="42"`) skip coercion. Emits a warning via `logging` for unknown keys.
- [ ] T005 [P] Implement template loaders in `tradingagents/experiments/templates.py`. Functions: `render_hypothesis(id_str, source_idea=None, cost=None) -> str`, `render_run_sh(id_str) -> str`, `render_run_ps1(id_str) -> str`, `render_params_json() -> str`. Templates baked as module-level multi-line strings (no external template files; keeps it self-contained).

### Tests

- [ ] T006 [P] Write `tests/test_experiments_ids.py` covering: valid ID round-trips, invalid IDs rejected, sequence increments within day, sequence resets across days, slug regex enforced.
- [ ] T007 [P] Write `tests/test_experiments_overrides.py` covering all R-003 coercion paths: int / float / bool / null / str / quoted string / malformed input / unknown key warning.
- [ ] T008 [P] Write `tests/test_experiments_templates.py` covering: HYPOTHESIS template includes ID + source idea + cost when provided / omits sections when not provided; PARAMS.json is valid JSON; run.sh and run.ps1 stubs reference the experiment ID.

**Checkpoint**: Foundation ready. T009 onward can begin in parallel where indicated.

---

## Phase 3: User Story 1 — Set up a new experiment (Priority: P1) 🎯 MVP

**Goal**: A researcher can invoke a single command to scaffold a new `experiments/<id>/` directory with templated `HYPOTHESIS.md`, empty `PARAMS.json`, and `run.sh`/`run.ps1` stubs. (FR-001 through FR-004; SC-001, SC-003, SC-006.)

**Independent Test**: Per `contracts/new_experiment_cli.md` test list. After T009 + T010, `python scripts/new_experiment.py mr1-contradiction` produces a complete experiment directory; `pytest tests/test_new_experiment.py` passes.

### Implementation

- [ ] T009 [US1] Implement `scripts/new_experiment.py` per `contracts/new_experiment_cli.md`. Use typer for the CLI. Wire to `tradingagents.experiments.ids.next_experiment_id` and `tradingagents.experiments.templates.render_*`. Refuses to overwrite existing dirs (FR-003). Validates short-name against regex.

### Tests

- [ ] T010 [US1] Write `tests/test_new_experiment.py` covering the 5 tests listed in `contracts/new_experiment_cli.md`: creates dir + files (happy path), refuses duplicate, rejects invalid short-name, increments sequence within day, --source-idea pre-fills hypothesis.

**Checkpoint**: US1 (MVP) shippable. The new-experiment workflow works end-to-end.

---

## Phase 4: User Story 2 — Vary one config knob without forking scripts (Priority: P2)

**Goal**: A researcher can run `scripts/backtest.py` with `--experiment-id <id>` and one or more `--config-override KEY=VALUE` flags; the resulting CSV rows are tagged with the experiment ID; the override is auto-recorded in `PARAMS.json`. (FR-005 through FR-011; SC-004.)

**Independent Test**: Per `contracts/backtest_extensions.md` test list. After T012-T017, an end-to-end run with `--experiment-id <id> --config-override pm_sees_debate=false --out experiments/<id>/results.csv` produces a CSV row with the experiment ID stamped and a populated `PARAMS.json`.

### Implementation (sequential — same file)

- [ ] T012 [US2] Modify `scripts/backtest.py`: add `--experiment-id` typer flag (string, optional, default empty). When non-empty, validate against `tradingagents.experiments.ids.validate_id`; refuse with clear error if invalid.
- [ ] T013 [US2] Modify `scripts/backtest.py`: add `experiment_id` field to `CSV_FIELDS` at the **end** (per R-004). When `--experiment-id` is set, populate the field on every row; otherwise leave empty.
- [ ] T014 [US2] Modify `scripts/backtest.py`: add repeatable `--config-override KEY=VALUE` typer flag. Use `tradingagents.experiments.overrides.apply_overrides` to merge into the runtime config dict before `TradingAgentsGraph(config=...)` is called.
- [ ] T015 [US2] Modify `scripts/backtest.py`: implement override-vs-named-flag precedence per FR-010. When `--config-override max_debate_rounds=N` AND `--debate-rounds M` both provided: override wins; warning is logged. Mirror for `--analysts`, `--debate-rounds`, `--anthropic-effort`.
- [ ] T016 [US2] Modify `scripts/backtest.py`: implement `PARAMS.json` auto-sync per R-007. After successful run, when `--experiment-id` AND any `--config-override` flag present: open `experiments/<id>/PARAMS.json`, update `config_overrides` key only if currently empty (refuse-overwrite-with-warning otherwise).

### Tests

- [ ] T017 [US2] Write `tests/test_backtest_extensions.py` covering the 10 tests listed in `contracts/backtest_extensions.md`. Use a mock for `TradingAgentsGraph.propagate` (already mocked in `tests/conftest.py` patterns) so tests don't hit the LLM API.

### Adjacent fix (different file — parallelizable with T012-T016)

- [ ] T018 [P] [US2] Update `scripts/analyze_backtest.py` to tolerate the `experiment_id` column (read with `pandas.read_csv`; if column absent, treat as empty for backward compat with pre-cleanup `pilot_results.csv`).

**Checkpoint**: US2 shippable on top of US1. Single-knob ablation experiments now expressible as one command line.

---

## Phase 5: User Story 3 — Scan past experiments at a glance (Priority: P3)

**Goal**: `findings.md` at project root summarizes every experiment with a one-line summary or "pending analysis" marker, ordered newest-first. (FR-012 through FR-016; SC-002, SC-005.)

**Independent Test**: Per `contracts/findings_aggregate_cli.md` test list. After T019-T022, running `python scripts/findings_aggregate.py` against an `experiments/` dir with mixed-state subdirs produces the correct output.

### Implementation (sequential — same file)

- [ ] T019 [US3] Implement `scripts/findings_aggregate.py` skeleton per `contracts/findings_aggregate_cli.md`: typer CLI with `--experiments-dir` and `--out` flags; walks `experiments/` for matching dirs; collects records.
- [ ] T020 [US3] Implement summary extraction in `scripts/findings_aggregate.py` per R-001 and `contracts/analysis_md_format.md`: first non-empty line that follows the top-level `# ` heading and appears before any other heading. Handle the 3 states (missing ANALYSIS.md / no summary / valid summary) per FR-014.
- [ ] T021 [US3] Implement output rendering + atomic write (tmp + rename) per `contracts/findings_aggregate_cli.md`. Sort newest first per R-002. Header includes timestamp, total/completed/pending counts.

### Tests

- [ ] T022 [US3] Write `tests/test_findings_aggregate.py` covering the 7 tests listed in `contracts/findings_aggregate_cli.md`: emits completed summary, marks missing analysis pending, marks missing summary, orders newest first, empty dir → placeholder, skips malformed dir names, atomic write doesn't leave partial files.

**Checkpoint**: US3 shippable. Lab-notebook view of the project exists.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, final integration smoke, validation.

- [ ] T023 [P] Generate initial `findings.md` by running `python scripts/findings_aggregate.py` (with empty `experiments/`, produces placeholder; commit the placeholder so the file exists in git).
- [ ] T024 [P] Update `CLAUDE.md` to add `scripts/new_experiment.py` and `scripts/findings_aggregate.py` to the Commands section + reference `experiments/` convention.
- [ ] T025 [P] Update `docs/EXPERIMENT.md` working notes with a dated entry: "Implemented experiments-scaffolding (spec 001). The Tier 1 ideas now have a clean experiment-creation workflow."
- [ ] T026 Update `CHANGELOG.md` Unreleased section with the implemented additions.
- [ ] T027 Run full `pytest tests/ -q`. Expect 92 (existing) + 30+ (new from T006-T008, T010, T017, T022) tests passing. Capture exact final count.
- [ ] T028 Manual smoke-test per `quickstart.md` — run the MR-1-style walkthrough end-to-end (without the cost — just the scaffolding, an empty `run.sh` placeholder, then verify `findings_aggregate` picks it up). Record outcome in a working note.
- [ ] T029 `/speckit.analyze` — post-hoc retrospective on whether the spec-kit workflow added value for this feature. Inputs: total time spent / docs written / bugs the spec caught vs missed. Output goes in `docs/EXPERIMENT.md` working notes.

---

## Dependencies (Story Completion Order)

```
Phase 1 (Setup) → Phase 2 (Foundational)
                    ↓
                  ┌─────────────────────────────────────┐
                  ↓                                     ↓
            Phase 3 (US1) ────────────→ Phase 4 (US2)  Phase 5 (US3)
                  ↓                          ↓                ↓
                  └──────────────┬───────────┘                ↓
                                 ↓                            ↓
                            Phase 6 (Polish) ←────────────────┘
```

- **Phase 1 → Phase 2**: Phase 2 needs the package directory.
- **Phase 2 → Phase 3, 4, 5**: All three user stories import from `tradingagents.experiments.*`.
- **Phase 3 (US1) → Phase 4 (US2)**: US2 references the experiment ID format US1 produces, but the contract is the regex (in `tradingagents.experiments.ids`), not US1's CLI. So strictly, US2 only needs Phase 2. Recommended order is US1 → US2 to validate the ID format end-to-end first.
- **Phase 5 (US3) is independent of US1 and US2**: can be built in parallel after Phase 2.
- **Phase 6**: after at least one user story is done.

## Parallel Execution Opportunities

**Within Phase 2** (after T001 + T002):
- T003, T004, T005 in parallel (different files)
- T006, T007, T008 in parallel after their respective implementation tasks

**Within Phase 4**:
- T012-T016 sequential (same file: `scripts/backtest.py`)
- T018 parallel with T012-T016 (different file: `scripts/analyze_backtest.py`)
- T017 (tests) after all of T012-T016

**Across phases** (after Phase 2 complete):
- US1 (Phase 3) and US3 (Phase 5) can be developed in parallel
- US2 (Phase 4) is best after US1 to validate the ID format

**Within Phase 6**:
- T023, T024, T025 in parallel
- T026 after T023-T025 (CHANGELOG references all of them)
- T027, T028, T029 sequential (each depends on prior state)

## MVP Scope

**Just User Story 1 + Phase 1 + Phase 2** delivers the foundational researcher experience: scaffold a new experiment with hypothesis and templated repro command. The researcher can run experiments by hand (any way they like) and the discipline of "everything in `experiments/<id>/`" is established.

US2 and US3 are quality-of-life upgrades on top.

**Recommended ship sequence**:
1. Phase 1 + Phase 2 + US1 → MVP. Land on `main`. ~half day.
2. US2 → backtest harness becomes experiment-aware. ~half day. Now Tier 1 ideas (WC-12, WC-11) are one-flag commands.
3. US3 → `findings.md` becomes living lab notebook. ~2 hours. Worth it once corpus reaches ~5 experiments.

## Implementation Strategy

- **TDD-ish, not strict TDD**: Write the implementation file and the test file in the same task block, but don't require red-then-green sequencing. The contracts already specify acceptance behavior precisely enough.
- **No mocking of the filesystem**: Use `tmp_path` pytest fixture. Real file I/O is fast enough at this scale.
- **No mocking of `mcp-reasoning` or `TradingAgentsGraph`**: US2's tests use the existing `mock_llm_client` fixture from `tests/conftest.py` so no API calls happen.
- **Pre-commit will catch**: ruff/format issues on new code. mypy is manual-only; run after each phase.
- **Constitution gate** (re-evaluate after Phase 6): does the implementation honor all 6 principles? If yes → commit. If no → refactor.

## Validation summary

- ✅ All tasks have a checkbox `- [ ]`
- ✅ All tasks have a Task ID (T001-T029)
- ✅ User-story-phase tasks have `[US1]`, `[US2]`, or `[US3]` labels
- ✅ Setup, Foundational, and Polish tasks have NO story label
- ✅ All tasks specify a file path
- ✅ Parallelizable tasks marked with `[P]`
- ✅ Dependencies between phases documented
- ✅ MVP scope identified (US1 + Phase 1 + Phase 2)
- ✅ Each user story is independently testable
