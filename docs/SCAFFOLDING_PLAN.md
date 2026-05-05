# Scaffolding plan for tradingagents-lab

**Status**: INSTALLED 2026-05-01 → 2026-05-03 evening (cost-tier scaffolding added) → 2026-05-04 (Spec 001 Phases 1-5 + Spec 002 Phases 0-2.5 implemented; live-validated). spec-kit at `.specify/`, ruff + mypy + pre-commit all wired, 785 tests passing, Constitution v1.2.2.
**Date**: 2026-05-01 (original); see CHANGELOG.md for installation history
**Companion docs**: `EXPERIMENT.md` (what we're building toward), `MULTI_AGENT_DEBATE_RESEARCH.md` (strategic context, superseded by `ROADMAP.md`)

## Goal

Bring this project up to roughly the engineering discipline level of `agent-harness-v2` so that experimental work has a clear surface (spec → plan → tasks → code → tests), automated quality gates, and reproducible setup. **Specifically**: install GitHub spec-kit like agent-harness-v2 uses, plus the minimum surrounding scaffolding (linter, type checker, pre-commit, CI) needed for spec-kit to be useful rather than ceremonial.

This is a *design* doc. Install commands and config files are scoped, but nothing is executed until approval.

## What agent-harness-v2 actually uses (reference)

Pulled from `runtime/pyproject.toml`, `.specify/`, `.github/workflows/`:

| Tool | Role | Notes |
|---|---|---|
| **spec-kit** (GitHub) | Spec-driven development workflow | `.specify/` directory: `memory/constitution.md`, `templates/`, `scripts/bash/`, `integrations/`, `workflows/`. Provides `/specify`, `/plan`, `/tasks`, `/analyze` slash commands |
| **ruff** ≥0.8 | Formatter + linter | `target-version = "py312"`, `line-length = 100`, broad rule set including imports/style/bugs |
| **mypy** ≥1.13 | Static type checking | With per-module overrides for untyped third-party deps |
| **pytest** ≥8 + **pytest-asyncio** + **pytest-cov** ≥6 | Test runner + async + coverage | `asyncio_mode = "auto"` |
| **hypothesis** ≥6.100 | Property-based testing | Used for invariants like hash-chain integrity |
| **GitHub Actions** | CI | 9 workflows: `ci.yml`, `spec-downstream-sync-check.yml`, `injection-scan.yml`, `claude-code-review.yml`, etc. |
| **structlog** ≥25 | Structured logging | (Runtime dep — not strictly scaffolding but worth noting) |
| **msgspec** ≥0.19 | Fast typed serialization | (Used for event types) |

What they explicitly *don't* use: pre-commit, black, isort, flake8, poetry, mkdocs, sphinx. Lean stack.

## What we should install (recommended)

Three tiers by priority. Tier 1 = install now; Tier 2 = install when the corresponding work starts; Tier 3 = consider later.

### Tier 1 — install now

| Tool | Why this project needs it | Install |
|---|---|---|
| **spec-kit** | The whole point of this plan. Brings spec → plan → tasks discipline + slash commands + a constitution that records the project's commitments durably. Currently we have brainstorm docs in `docs/` but no enforced workflow. Spec-kit gives us one. | `uvx --from specify-cli specify init --here` (in-place, in current repo) |
| **ruff** | TradingAgents has zero linting today. Adds 30 seconds to install, catches whole categories of bugs (unused imports, common mistakes), and is used by agent-harness-v2 with the same target Python version. | `uv pip install -e ".[dev]"` after dev group added |
| **mypy** | TradingAgents has light type hints (`Dict[str, Any]` mostly). Mypy with `--ignore-missing-imports` will catch the obvious wrong-type errors without forcing us to type the whole codebase. | Same dev group |
| **pytest-asyncio** + **pytest-cov** | Already have `pytest`. Adding these two means async tests work and coverage runs as part of the normal test command. | Same dev group |
| **pre-commit** | agent-harness-v2 doesn't use it, but they have CI as a backstop. We don't have CI yet. Pre-commit gives us the same effect locally: ruff + mypy + pytest run before every commit, refusing to commit broken code. | `uv pip install pre-commit` + `pre-commit install` |

### Tier 2 — install when corresponding work starts

| Tool | When | Why |
|---|---|---|
| **hypothesis** | When we land EH-2 (rating distribution gate) and start writing gate tests | Property-based tests are the right shape for "across N runs, distribution must include all 5 tiers" type assertions |
| **datasette** | When we land EH-1 (SQLite event log) | Zero-config browser-based SQL over the event log; lets us figure out which queries matter before committing to Grafana panel design (per `EXPERIMENT.md` §5 EH-1 note) |
| **msgspec** | When we land EH-1 (event types) | Fast typed serialization for event payloads. agent-harness-v2 uses this; same pattern transfers cleanly |
| **structlog** | When we want consistent log output across CLI + scripts + future event-bus emitter | One JSON-line-per-event format that's grep-able + dashboard-able |
| **GitHub Actions** | When we push to GitHub fork | Mirror agent-harness-v2's `ci.yml` pattern: ruff + mypy + pytest on PR. Skip the trading-specific checks until we have the structures to check |

### Tier 3 — consider later, not now

| Tool | When (if ever) |
|---|---|
| **mkdocs-material** | If `docs/` grows past ~10 files and we want a static site. Right now flat markdown is fine. |
| **commitizen** / **commitlint** | If we ever co-author with others. Currently only enforced by convention via commit message style. |
| **sqlite-vec** | If we ever add embedding-based memory (per `EXPERIMENT.md` EH-5 antibodies idea). Defer until use case is real. |
| **claude-agent-sdk** (Python) | Only if we ever fold this into agent-harness-v2 (rejected per `EXPERIMENT.md` Part 1) or build a long-lived runtime variant. Currently TradingAgents uses LangGraph, not the Anthropic agent SDK. |

## Detailed install plan (Tier 1)

Order matters: each step is verifiable before moving to the next.

### Step 1 — Add a `[dev]` optional dependency group to `pyproject.toml`

Mirror agent-harness-v2's structure:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=6.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "pre-commit>=4.0.0",
]
```

Install: `uv pip install -e ".[dev]"`

Verify: `ruff --version && mypy --version && pytest --version && pre-commit --version` all return.

### Step 2 — Add `[tool.ruff]` and `[tool.mypy]` config to `pyproject.toml`

Conservative starting point — enough to be useful, not enough to fail on the existing codebase:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"      # match requires-python from project block

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "UP",   # pyupgrade
]
ignore = [
    "E501",   # line length handled by formatter
    "B008",   # function calls in default args (typer pattern)
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["B011"]   # asserts are fine in tests

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true
warn_unused_ignores = true
warn_return_any = false        # too noisy for current codebase
disallow_untyped_defs = false  # gradual; tighten later

[[tool.mypy.overrides]]
module = ["yfinance", "yfinance.*", "stockstats", "stockstats.*", "parsel", "parsel.*", "questionary", "questionary.*", "langgraph.*"]
ignore_missing_imports = true
```

Verify: `ruff check .` runs; `mypy tradingagents` runs. Expect failures in both — that's the baseline. Capture for `findings.md`.

### Step 3 — Initialize spec-kit

```bash
uvx --from specify-cli specify init --here
```

This creates `.specify/` directory with: `memory/constitution.md` (template), `templates/` (spec, plan, tasks, checklist, constitution templates), `scripts/bash/`, `integrations/` (likely Claude Code + Cursor + Windsurf), `workflows/`, plus root metadata files (`feature.json`, `init-options.json`, `integration.json`).

Then customize `.specify/memory/constitution.md` with project-specific commitments. **Do not just copy agent-harness-v2's commitments verbatim** — they were written for a long-lived autonomous agent runtime; we're a research playground. Suggested first-pass commitments for `tradingagents-lab`:

1. **Save everything** — every experiment writes to `experiments/<date>-<id>/`; corpus is the research output.
2. **One experiment per change** — vary one parameter at a time so the corpus is interpretable as ablation data.
3. **Stay cheap** — individual experiment runs ≤ $30 default ceiling.
4. **No production claims** — disclaimer is load-bearing; this is research, not advice.
5. **Steal liberally** — patterns from `agent-harness-v2` / `ladybird` / `battlecode2026` / `bruno-swarm` are fair game; no abstraction-purity tax.
6. **Spec before structural change** — any change to event log, gates, or worker structure starts with a spec under `.specify/specs/<id>/`.

(These are first-draft; will iterate during install.)

### Step 4 — Install pre-commit + add config

Create `.pre-commit-config.yaml` at root:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (unit tests only)
        entry: pytest -m unit -q
        language: system
        types: [python]
        pass_filenames: false
```

Install: `pre-commit install`

Verify: make a trivial change, attempt to commit; hooks should run.

**Note** — running mypy on every commit is too slow for our case. mypy stays a manual / CI step.

### Step 5 — Update CLAUDE.md to reference the new structure

Add a "Read the spec first" section pointing at `.specify/memory/constitution.md` and `.specify/specs/`, mirroring agent-harness-v2's CLAUDE.md pattern.

### Step 6 — Update `EXPERIMENT.md` working notes with what was installed

One-line entry per tool, dated. Lab notebook discipline.

## File-by-file changes summary

| File | Action |
|---|---|
| `pyproject.toml` | Add `[project.optional-dependencies]` dev group, `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.per-file-ignores]`, `[tool.mypy]`, `[[tool.mypy.overrides]]` blocks |
| `.pre-commit-config.yaml` | NEW |
| `.specify/` | NEW (directory tree created by `specify init --here`) |
| `.specify/memory/constitution.md` | EDIT after init — replace template with our 6 commitments |
| `CLAUDE.md` | Add "Spec-first discipline" section + ref to `.specify/memory/constitution.md` |
| `docs/EXPERIMENT.md` | Working note dated today: "Installed spec-kit + ruff + mypy + pre-commit per `SCAFFOLDING_PLAN.md`" |
| `.gitignore` | Add `.ruff_cache/` (already there), `.mypy_cache/`, `.pre-commit-cache/` if missing |

Estimated total: ~6 file changes, ~half day of work, zero LLM API cost.

## Validation gates (each must pass before next step)

1. After Step 1: `uv pip install -e ".[dev]"` succeeds, all 5 tools present.
2. After Step 2: `ruff check . | wc -l` produces a finite number (baseline noise count); `mypy tradingagents 2>&1 | wc -l` same. Capture both as "where we started" in `EXPERIMENT.md`.
3. After Step 3: `.specify/memory/constitution.md` exists with our 6 commitments (not template placeholders).
4. After Step 4: pre-commit hook runs on a trivial commit; ruff actually catches a manually-introduced bug.
5. After Step 5: CLAUDE.md has a clear "spec first" section.
6. After Step 6: `EXPERIMENT.md` working notes section updated.

After all 6 steps: re-run `pytest tests/ -q` — should still be 92/92 passing (no behavioral changes).

## What this enables

Once installed, the **common scaffolding for `EXPERIMENT.md` Tier 1 ideas** (`experiments/` directory, `experiment_id` column, `findings_aggregate.py`, `--config-override`) becomes a *spec* under `.specify/specs/001-experiment-scaffolding/spec.md`, with plan, tasks, checklist generated by spec-kit slash commands. That's the first real test of whether the workflow adds value.

Then EH-2 (rating distribution gate), MR-1 (contradiction analysis), WC-12 (PM-blind), WC-11 (order randomization) each become specs under `.specify/specs/00X-<name>/`.

## Out of scope

- Adopting agent-harness-v2's full constitution (those commitments are for a different system). We write our own.
- GitHub Actions CI — defer until we push to a remote (or want to). Pre-commit covers the local case.
- Type-perfecting the existing TradingAgents code — gradual typing, mypy stays permissive.
- Renaming the import path from `tradingagents` (only the distribution name changed in the cleanup commit; import surface untouched on purpose).
- Fork divergence reports like ladybird auto-generates. We're not actively merging upstream; if we ever do, revisit.

## Open questions (decide before install)

1. **`uvx` vs `pip install` for spec-kit**: `uvx --from specify-cli specify init --here` is the recommended path; alternative is `pip install specify-cli` then `specify init --here`. uvx is cleaner (doesn't pollute the venv). **Default: uvx.**
2. **Pre-commit pytest scope**: just `-m unit` (fast subset), full suite, or no pytest in pre-commit at all (rely on manual / CI)? **Default: `-m unit` for speed; full suite is a CI step later.**
3. **Constitution commitments — keep at 6 or fewer**: agent-harness-v2 has 10 (the "Layer 0 commitments"). For an experimental playground, 6 is probably already too many. Could trim to 3-4. **Default: start with 6, prune after first 2 weeks of use.**
4. **Whether to install `claude-agent-sdk`**: if we ever want to use Claude Code's spec-kit slash command integration (`/specify`, `/plan`, `/tasks`), we may need it. Worth checking. **Default: skip until needed.**

## Recommended sequence

1. **Approve this plan** (or push back).
2. Execute Steps 1-6 in order, ~30 minutes total.
3. **First spec** = the common scaffolding for Tier 1 ideas (`experiments/` convention + `experiment_id` column + `--config-override` + `findings_aggregate.py`). Use it as the proof-of-value test for the spec-kit workflow.
4. If spec-kit feels useful: continue applying it to EH-2, MR-1, WC-12, WC-11.
5. If spec-kit feels like ceremony: keep ruff + mypy + pre-commit (independent value), drop the spec-kit workflow.

## References

- spec-kit: https://github.com/github/spec-kit
- ruff: https://docs.astral.sh/ruff/
- mypy: https://mypy.readthedocs.io/
- pre-commit: https://pre-commit.com/
- agent-harness-v2 reference files used in this design:
  - `C:/Development/Projects/agent-harness-v2/runtime/pyproject.toml`
  - `C:/Development/Projects/agent-harness-v2/.specify/memory/constitution.md`
  - `C:/Development/Projects/agent-harness-v2/CLAUDE.md` (spec-first discipline section)
  - `C:/Development/Projects/agent-harness-v2/.github/workflows/` (CI patterns to mirror later)
