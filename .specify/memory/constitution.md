# tradingagents-lab Constitution

**Project**: Personal experimental fork of TradingAgents — a research playground for studying multi-agent LLM debate dynamics, using equity-decision-making as the substrate because it has cheap, objective ground truth.

**Version**: 1.0.0
**Adopted**: 2026-05-01

This constitution governs how this project evolves. The commitments below are intentionally short and few. They are constraints, not aspirations — when in conflict with convenience, they win.

---

## Core Principles

### I. Save Everything (NON-NEGOTIABLE)

Every experiment writes its full output to `experiments/<YYYY-MM-DD>-<id>-<short-name>/`. The corpus is the research output, not the code. A run that doesn't save its full state log, params, and analysis is a wasted run.

**Required per experiment dir**:
- `HYPOTHESIS.md` — what we're testing, predicted outcome, success criterion
- `PARAMS.json` — exact knobs varied vs baseline
- `results.csv` (or equivalent) — raw output (gitignored, retained on disk)
- `ANALYSIS.md` — what we found, decision, one-line summary at top
- `run.sh` (or `run.ps1`) — one-line repro command

**Why**: Mode collapse, debate failures, and other phenomena we care about only become visible across many runs. The strategic doc this project produces is `findings.md` aggregated from `experiments/*/ANALYSIS.md` first lines, not commit messages.

### II. One Experiment Per Change

Each experiment varies **one** parameter against a documented baseline. If you can't write the experiment as "we varied X, holding everything else equal," it's not an experiment — it's a fork.

**Why**: The corpus must be interpretable as ablation data, not as a pile of one-off configurations. Two-variable experiments compound noise into uninterpretability.

**Acceptable exception**: a "shakeout run" of a new architecture against the existing baseline grid. Document explicitly as `shakeout_run: true` in `PARAMS.json`.

### III. Stay Cheap

Each experimental run defaults to ≤ $30 in LLM API spend. Crossing that ceiling requires explicit deliberation in the experiment's `HYPOTHESIS.md` ("we expect this to cost $X because Y").

**Why**: The pilot taught us that a 50-run grid is enough to detect signal-vs-noise. Bigger runs trade money for confidence intervals that we mostly don't need until late-stage findings. Default cheap; scale up only when the signal warrants it.

**Implementation**: `scripts/backtest.py` already prints a cost estimate and gates on `--yes`. Future experiment runners follow the same pattern.

### IV. No Production Claims

The upstream disclaimer ("for research purposes... not investment advice") is load-bearing and we restate it. Nothing produced by this project may be presented as a trading recommendation, signal, or advice. The pilot proved the framework's ratings are anti-correlated with realized alpha; that finding is itself part of why this principle is non-negotiable.

**Why**: Beyond the obvious legal reasons: presenting research output as advice would corrupt the experimental discipline. We are studying *how the agents fail*, not *whether they succeed at picking stocks*.

### V. Steal Liberally

Patterns from sibling projects in the portfolio are fair game without abstraction-purity tax:
- `agent-harness-v2` — event sourcing, structural enforcement, gates, knowledge digestion, antibodies
- `ladybird` — separate-process enforcement plane (Sentinel pattern)
- `battlecode2026` ratbot6 — value function over assigned roles, structured signaling
- `bruno-swarm` — multi-agent coordination patterns, abliteration for specialization
- `mcp-reasoning`, `branch-thinking`, `logic-thinking` — structured reasoning tools

Copy ideas, copy code, restate provenance in commit messages. The point is to test cross-project synthesis, not to maintain ten clean abstractions.

**Why**: This project's value is the cross-pollination, not the codebase. A "pure" abstraction we never reuse is worse than a messy direct copy that produces a finding.

### VI. Spec Before Structural Change

Any change to one of the following requires a spec under `.specify/specs/<id>-<name>/spec.md` before code:
- The event log schema (when introduced)
- Gate definitions and gate-firing logic (when introduced)
- Worker structures (the trading worker variant pattern)
- The `experiments/` directory convention itself
- The constitution

Use the spec-kit slash commands: `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

**Why**: The pilot showed the upstream framework had no spec for "the PM should produce all 5 ratings" — it was an implicit assumption that was violated emergently. Specs protect against the same class of failure here.

**Acceptable exception**: ad-hoc scripts under `scripts/` that don't touch structural state can skip the spec workflow. Bias toward writing the spec when in doubt.

---

## Quality Gates

These are derived from the principles above. They must pass before any commit lands.

1. **All tests pass** — `pytest tests/ -q`. Currently 92/92.
2. **Ruff clean for new files** — pre-commit runs ruff on staged files. Existing baseline (305 errors) is grandfathered; new code adds zero new violations.
3. **No new tracked artifacts** — pilot CSVs, event logs, and experiment outputs go to gitignored paths. `git status` after a successful experiment should show only intentional doc/code changes.
4. **Spec exists for structural changes** — see Principle VI.
5. **`HYPOTHESIS.md` exists for experiment runs** — Principle I enforced; CI/pre-commit cannot enforce this directly, so the discipline is operator-enforced and visible in `findings.md` aggregation.

---

## Workflow

### Standard experimental loop

1. Pick an idea from `docs/EXPERIMENT.md` Tier 1 / 2 / 3.
2. Create `experiments/<date>-<id>-<name>/` with `HYPOTHESIS.md` and `PARAMS.json`.
3. If structural change required → `/speckit.specify` first.
4. Run: `bash run.sh` (or `pwsh run.ps1`) — produces `results.csv`.
5. Analyze: `scripts/analyze_backtest.py` (or experiment-specific analyzer) → `ANALYSIS.md`.
6. One-line summary at top of `ANALYSIS.md`.
7. Aggregate: `scripts/findings_aggregate.py` (when built) regenerates `findings.md`.
8. Commit: docs + scripts only; experiment outputs stay gitignored.

### Spec lifecycle (for structural changes)

1. `/speckit.constitution` — verify or amend constitution if needed.
2. `/speckit.specify <feature>` — generates `.specify/specs/<id>-<name>/spec.md`.
3. `/speckit.clarify` — if open questions exist, resolve interactively.
4. `/speckit.plan` — generates implementation plan.
5. `/speckit.tasks` — generates task list.
6. `/speckit.implement` — execute (or do by hand following the task list).
7. `/speckit.analyze` — post-mortem.

---

## Governance

This constitution is amendable. Amendments follow the spec-kit constitution flow (`/speckit.constitution`). Amendments must:

1. Be discussed in commit message body (not just title).
2. Bump the version (PATCH for clarification, MINOR for added principle, MAJOR for removed/redefined principle).
3. Update the "Adopted" date at the top.
4. Note the change in `CHANGELOG.md` under the relevant version entry.

The principles above are themselves up for amendment if they prove ceremonial rather than load-bearing. The test: after one month of use, are we honoring this principle because it's helping or because it's written down? If the latter, amend or remove.

**Version**: 1.0.0 — initial adoption
**Last amended**: 2026-05-01 (initial)
