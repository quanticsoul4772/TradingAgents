# Phase 0 Research: Experiments Scaffolding

Resolves open design questions from `plan.md` Phase 0. Each entry is `Decision` / `Rationale` / `Alternatives considered`.

---

## R-001: One-line summary location in `ANALYSIS.md`

**Decision**: First non-empty line that follows the top-level `# ` heading and appears before any other heading. The line MAY be wrapped in `**Summary**: ...` for emphasis but the marker is not required — the *position* is the contract.

**Rationale**: The first-line-after-H1 convention requires no extra ceremony for the writer. Frontmatter would be cleaner for parsing but Markdown frontmatter is non-standard; people forget the YAML separators. The position rule degrades gracefully: a missing summary just means "the first paragraph after the title" gets used, which is approximately what a reader would scan for anyway.

**Alternatives considered**:
- *YAML frontmatter `summary:` field* — cleaner machine read but easy to forget; fails closed (no summary appears in `findings.md`) which violates FR-014.
- *HTML comment marker `<!-- SUMMARY: ... -->`* — robust but invisible in rendered Markdown; defeats the "human-scannable file" purpose.
- *Explicit `## Summary` section* — adds ceremony; not all experiments need a section, just a sentence.

---

## R-002: `findings.md` ordering — oldest first or newest first?

**Decision**: Newest first. Most recent experiment at the top of the file.

**Rationale**: A research-log file gets longer over time; the most recently relevant entries are at the top by default. Mirrors how a CHANGELOG works (Unreleased → most recent → older). Beats oldest-first scrolling friction at scale.

**Alternatives considered**:
- *Oldest first* — historically natural for journals but requires scrolling past stale work to find current state.
- *Grouped by status (active / completed / abandoned)* — too much structure for an aggregator-generated file; structure should live in the experiments themselves, not the index.

---

## R-003: `--config-override KEY=VALUE` value parsing — type coercion strategy?

**Decision**: Try literals in order: `int → float → bool ("true"/"false", case-insensitive) → null ("none"/"null", case-insensitive) → str` (fallback). Quoted values (`KEY="some string"`) skip coercion and are always treated as strings.

**Rationale**: Matches `argparse`-style ergonomics that users already expect. The order is "most specific first": `42` becomes int, not str; `1.5` becomes float; `true` becomes bool. The quoted-string escape hatch handles edge cases (`KEY="42"` for the rare case the user really means a string).

**Alternatives considered**:
- *Strings only* — simplest to implement but forces users to remember type coercion in the script's config-merging code; surprising when `max_debate_rounds=2` gets passed as `"2"` and breaks comparisons.
- *Explicit type prefix* (`KEY:int=2`) — most explicit but ugly and redundant for the common case.
- *JSON literal* (`KEY={"foo": 1}`) — overkill for the flat config dict TradingAgents uses; JSON values would also need shell escaping.

---

## R-004: `experiment_id` column position in CSV

**Decision**: Last column. `ticker, analysis_date, rating, error, run_seconds, deep_model, quick_model, debate_rounds, analysts, experiment_id`.

**Rationale**: Column-at-end is the only ordering that's both backward-compatible (`pandas.read_csv` on an old file with the new schema produces a column with NaN values that's easy to fill) and forward-compatible (we'll add more columns later for multi-variant runs, hash-chained event refs, etc.; appending stays clean). The existing `pilot_results.csv` from the cleanup commit can be re-read with the new schema and its rows will have `experiment_id = NaN`, which downstream code treats as "ungrouped baseline" per FR-007.

**Alternatives considered**:
- *Position 0 (leftmost)* — standard for "primary key" semantics but breaks every existing reader of the CSV.
- *After `analysis_date`* — visually grouped with run identity but still mid-table, still a reader-breaking change.

---

## R-005: New-experiment command location

**Decision**: New script at `scripts/new_experiment.py`. Not added to `cli/main.py`.

**Rationale**: `cli/main.py` is the user-facing TradingAgents analyst CLI (`tradingagents analyze`); the spec-kit workflow already pollutes the slash-command surface with `/speckit.*` and we don't want `tradingagents new-experiment` to coexist confusingly with `/speckit.specify` (which targets a different abstraction layer). `scripts/new_experiment.py` follows the convention set by `scripts/backtest.py` and `scripts/analyze_backtest.py` — self-contained scripts for operator workflows.

**Alternatives considered**:
- *Subcommand of `tradingagents analyze`* — wrong layer (analyze is for running the framework on a ticker, not for setting up experiments).
- *PowerShell-only script (mirroring `.specify/scripts/powershell/`)* — would limit reuse on macOS/Linux later; Python script with cross-platform stubs is more portable.

---

## R-006: `experiments/` empty-state file (.gitkeep convention)

**Decision**: Add `experiments/.gitkeep` so the directory exists in fresh clones even before any experiment lands.

**Rationale**: Researchers cloning the repo should see the `experiments/` directory exists and is meaningful, not have to read the spec to learn where to put things. `.gitkeep` is the long-standing convention for "track this empty directory."

**Alternatives considered**:
- *No placeholder* — directory only appears after the first experiment; first-time UX is worse.
- *`README.md` in `experiments/`* — overkill; the convention is documented in `docs/EXPERIMENT.md` and `.specify/memory/constitution.md`.

---

## R-007: How to keep `PARAMS.json` in sync when `--config-override` is used

**Decision**: When the runner is invoked with `--experiment-id <id>` AND `--config-override KEY=VALUE` flags, after the run completes successfully, the runner writes the effective overrides into `experiments/<id>/PARAMS.json` under a top-level `config_overrides` key. If the file already exists with non-empty `config_overrides`, the runner refuses to overwrite (preserves the manual record) and logs a warning. If the file doesn't exist, the runner creates it.

**Rationale**: Auto-syncing protects against the most common failure mode: the researcher remembers to use `--config-override` but forgets to update `PARAMS.json` by hand, and 6 months later can't reconstruct what was varied. The "refuse to overwrite" rule prevents the runner from silently destroying manual annotations the researcher added (e.g., links to other experiments, sub-explanations).

**Alternatives considered**:
- *Always overwrite* — destructive to manual annotations.
- *Never auto-sync* — convenient but violates Principle I (Save Everything) since the override gets lost.
- *Append to a `config_overrides_history` array* — over-engineered for the single-knob-at-a-time experiments this scaffolds.

---

## Summary table

| ID | Question | Decision | Affects FR |
|---|---|---|---|
| R-001 | Summary location in ANALYSIS.md | First non-empty line after H1 | FR-013 |
| R-002 | findings.md ordering | Newest first | FR-015 |
| R-003 | --config-override value parsing | int → float → bool → null → str; quoted = str | FR-008, FR-011 |
| R-004 | experiment_id column position | Last column | FR-006 |
| R-005 | new-experiment command location | scripts/new_experiment.py | FR-001 |
| R-006 | experiments/ empty state | .gitkeep placeholder | (Project structure) |
| R-007 | PARAMS.json sync from --config-override | Auto-sync into config_overrides key, refuse overwrite | FR-009 |

All open questions resolved. No `[NEEDS CLARIFICATION]` markers remain. Ready for Phase 1.
