# Implementation Plan: Experiments Scaffolding

**Branch**: `001-experiments-scaffolding` | **Date**: 2026-05-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-experiments-scaffolding/spec.md`

## Summary

Adds a per-experiment directory convention (`experiments/<YYYY-MM-DD>-<NNN>-<short-name>/`), an `experiment_id` column on `scripts/backtest.py` CSV output, a `--config-override KEY=VALUE` flag for varying single config knobs without forking the runner, and a `findings_aggregate` tool that walks `experiments/*/ANALYSIS.md` to produce a project-root `findings.md`. All four pieces share a single concept (the `<id>` string) and a single mental model (one directory = one experiment = one row in `findings.md`). Total new code: ~250 lines across two new scripts plus a small modification to `scripts/backtest.py`.

## Technical Context

**Language/Version**: Python 3.10 (matches `requires-python` in `pyproject.toml`)
**Primary Dependencies**: `typer` (already in deps; used by `scripts/backtest.py`), `pandas` (already in deps; CSV manipulation), `pathlib` (stdlib), `datetime` (stdlib), `json` (stdlib), `re` (stdlib)
**Storage**: Filesystem only — markdown (`HYPOTHESIS.md`, `ANALYSIS.md`, `findings.md`), JSON (`PARAMS.json`), CSV (`results.csv` per experiment, plus existing `pilot_results.csv`-style files), and shell scripts (`run.sh` / `run.ps1`)
**Testing**: `pytest` with the existing `unit` marker (already in `pyproject.toml`); new tests under `tests/test_experiments_scaffolding.py`
**Target Platform**: Cross-platform — Windows (primary developer env, Git Bash + PowerShell), macOS, Linux. Both `run.sh` and `run.ps1` stubs are produced so either shell works.
**Project Type**: CLI tools / scripts — extends the existing `scripts/` convention, no new packages.
**Performance Goals**: `findings_aggregate` completes in <1 sec for 10 experiments (SC-005). New-experiment command completes in <500 ms (file I/O bound).
**Constraints**: Must not break existing `scripts/backtest.py` invocations (CSVs without `experiment_id` column must still be readable by `scripts/analyze_backtest.py`). Must preserve the existing typer flag surface — only additions, no removals.
**Scale/Scope**: 4 new files, 2 modified files, ~250 LOC new + ~30 LOC modifications to `backtest.py`. Adds no new package dependencies (all stdlib + already-installed).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reviewing against `.specify/memory/constitution.md` (v1.0.0):

| Principle | How this feature complies | Status |
|---|---|---|
| **I. Save Everything (NON-NEGOTIABLE)** | This feature *is* the enforcement mechanism for this principle. Every artifact required by Principle I (`HYPOTHESIS.md`, `PARAMS.json`, `results.csv`, `ANALYSIS.md`, `run.sh`) is produced or templated by the scaffolding. | ✅ PASS |
| **II. One Experiment Per Change** | The scaffolding itself is one feature with one purpose: enable single-knob experimentation. The `--config-override` flag is the operational expression of this principle. | ✅ PASS |
| **III. Stay Cheap** | Zero LLM costs to build. Zero LLM costs at runtime (pure file I/O + CSV manipulation). | ✅ PASS |
| **IV. No Production Claims** | Internal tooling, no user-facing trading output. N/A. | ✅ PASS |
| **V. Steal Liberally** | Convention is informed by agent-harness-v2's `specs/<id>/` pattern (using directory as unit of work) and ladybird's auto-generated weekly divergence reports (using a top-level summary file as living lab notebook). No abstraction-purity tax. | ✅ PASS |
| **VI. Spec Before Structural Change** | This spec exists. The plan exists. No code lands before `/speckit.tasks` and `/speckit.implement`. | ✅ PASS |

**No violations. No `Complexity Tracking` entries needed.** Re-evaluation gate after Phase 1 design: still PASS — the design adds no new complexity, just files in conventional locations.

## Project Structure

### Documentation (this feature)

```text
specs/001-experiments-scaffolding/
├── plan.md              # This file
├── research.md          # Phase 0 output — resolve open design questions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — first-experiment walkthrough
├── contracts/
│   ├── new_experiment_cli.md        # CLI contract for new_experiment.py
│   ├── backtest_extensions.md       # New flags on scripts/backtest.py
│   ├── findings_aggregate_cli.md    # CLI contract for findings_aggregate.py
│   └── analysis_md_format.md        # Format contract for ANALYSIS.md one-line summary
├── checklists/
│   └── requirements.md  # Already produced by /speckit.specify
└── tasks.md             # Phase 2 output — produced by /speckit.tasks (NOT created here)
```

### Source Code (repository root)

```text
TradingAgents/
├── scripts/
│   ├── backtest.py              # MODIFIED: add --experiment-id, --config-override flags + experiment_id CSV column
│   ├── analyze_backtest.py      # MODIFIED: tolerate experiment_id column (group-by support is a follow-up)
│   ├── new_experiment.py        # NEW: typer CLI to create experiments/<id>/ skeleton
│   └── findings_aggregate.py    # NEW: typer CLI to walk experiments/*/ANALYSIS.md → findings.md
│
├── tradingagents/
│   └── experiments/             # NEW: small helper module (reusable by future runners)
│       ├── __init__.py
│       ├── ids.py               # NEW: generate / validate experiment IDs (format, sequence numbers)
│       ├── overrides.py         # NEW: parse and apply --config-override KEY=VALUE flags
│       └── templates.py         # NEW: load HYPOTHESIS.md / run.sh / PARAMS.json templates
│
├── tests/
│   └── test_experiments_scaffolding.py  # NEW: unit tests for ids/overrides/templates + integration test for the four new flag/file behaviors
│
├── experiments/                 # NEW: tracked directory, holds per-experiment subdirs
│   ├── 2026-05-02-001-mr1-contradiction/   # Example (created by Phase 3 first real experiment)
│   │   ├── HYPOTHESIS.md
│   │   ├── PARAMS.json
│   │   ├── results.jsonl       # gitignored
│   │   ├── ANALYSIS.md
│   │   └── run.sh
│   └── .gitkeep                 # NEW: placeholder so empty experiments/ exists in fresh checkouts
│
├── findings.md                  # NEW: project-root aggregation of one-line summaries (tracked)
└── .gitignore                   # already covers experiments/*/results.csv + experiments/*/events.db per cleanup commit
```

**Structure Decision**: Single-project Python with new module under `tradingagents/experiments/` for shared logic, two new scripts under `scripts/` for CLI surfaces, and the `experiments/` directory as the experiment artifact storage. No new packages, no new top-level dirs beyond `experiments/`. Module placement (`tradingagents/experiments/` rather than `scripts/_lib/`) chosen because the override-parsing and ID-generation logic is reusable by future runners (the contradiction-analyzer, the gate-tester, an event-log emitter) — putting it in `tradingagents/` keeps the scripts thin.

## Complexity Tracking

No complexity violations to justify. Constitution Check passes cleanly.

---

## Phase 0 — Outline & Research (artifacts)

See `research.md` (generated alongside this plan). Resolves the following open design questions surfaced during spec writing:

1. One-line summary location in `ANALYSIS.md` — what marker, what fallback?
2. `findings.md` ordering — oldest first or newest first?
3. `--config-override KEY=VALUE` value parsing — type coercion strategy?
4. `experiment_id` column position in CSV — last column (back-compat-friendly) or specific position?
5. New-experiment command location — `scripts/new_experiment.py` or extend `cli/main.py`?

## Phase 1 — Design & Contracts (artifacts)

See `data-model.md` (entities formalized), `contracts/*.md` (CLI flag and file format contracts), `quickstart.md` (walkthrough).

Agent context update: run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude` after this plan is committed to refresh `CLAUDE.md` with feature-specific context.

## Stop point

Per `/speckit.plan` semantics, this command stops after Phase 1 planning artifacts are produced. **It does NOT create `tasks.md`** — that's `/speckit.tasks`, the next workflow step.

## Next moves after this plan lands

1. `/speckit.tasks` — generate `tasks.md` with concrete implementable tasks
2. `/speckit.implement` (or just write the code by hand following `tasks.md`)
3. `/speckit.analyze` — post-merge retrospective: did the spec-kit workflow add value for this feature?
