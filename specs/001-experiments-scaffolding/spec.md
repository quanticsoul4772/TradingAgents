# Feature Specification: Experiments Scaffolding

**Feature Branch**: `001-experiments-scaffolding`
**Created**: 2026-05-02
**Status**: Draft
**Input**: User description: "Common scaffolding for experiments/ directory: per-experiment HYPOTHESIS/PARAMS/results/ANALYSIS structure, experiment_id column in backtest CSV, --config-override flag for varying knobs without forking the script, and a findings_aggregate.py tool that walks experiments/*/ANALYSIS.md and produces findings.md from one-line summaries"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set up a new experiment with hypothesis and parameters (Priority: P1)

A researcher has identified an idea from `docs/EXPERIMENT.md` (e.g., MR-1 contradiction analysis, WC-12 PM-blind, EH-2 distribution gate, WC-11 order randomization) and wants to start a new experiment. They need a place to record what they're testing, what they predict, what knobs are being varied, and where the results will land — all before running anything that costs money or time. The convention must make it impossible to "forget to write down what we were trying" because the next experiment's directory creation forces it.

**Why this priority**: Constitution Principle I (Save Everything) is non-negotiable. Nothing else in this feature matters if a researcher can run an experiment without first recording its hypothesis. This is the foundational discipline.

**Independent Test**: A researcher can run a single new-experiment command, get a populated directory with empty-but-templated `HYPOTHESIS.md` and `PARAMS.json`, fill them out, and run an experiment whose results land in the same directory automatically. Tested without any other story being implemented.

**Acceptance Scenarios**:

1. **Given** the researcher is in the project root with no prior experiments, **When** they invoke the new-experiment command with a short name "mr1-contradiction", **Then** a directory `experiments/2026-05-02-001-mr1-contradiction/` is created containing `HYPOTHESIS.md` (template), `PARAMS.json` (empty object), and `run.sh` (one-line repro command stub).
2. **Given** an experiment directory exists with completed `HYPOTHESIS.md` and `PARAMS.json`, **When** the researcher runs the experiment, **Then** raw output (`results.csv` or equivalent) is written into the same directory, not the project root.
3. **Given** a researcher tries to run an experiment without writing the hypothesis first, **When** they invoke the runner, **Then** a clear error tells them which file is missing and what it should contain.

---

### User Story 2 - Vary one config knob without forking scripts (Priority: P2)

A researcher wants to test "what happens when the Portfolio Manager doesn't see the bull/bear debate" (idea WC-12). They don't want to copy `scripts/backtest.py` into a new file, modify the config, and lose track of which file does what. Instead, they want to invoke the existing runner with a single override flag, run it against the standard ticker grid, and have the resulting CSV rows tagged with which experiment they belong to so they can be analyzed alongside or separately from baseline runs.

**Why this priority**: Constitution Principle II (One Experiment Per Change). Without this, every experiment becomes a fork of the runner, the corpus becomes uninterpretable, and the researcher loses the ability to compare runs.

**Independent Test**: A researcher can invoke the backtest runner with `--config-override pm_sees_debate=false --experiment-id 2026-05-02-002-pm-blind`, get a CSV where the new rows carry that experiment ID, and combine those rows with prior baseline rows in pandas to compute the difference.

**Acceptance Scenarios**:

1. **Given** an existing pilot CSV with rows from prior runs, **When** the researcher runs the backtest with `--experiment-id <id>` and `--out` pointing at the same CSV, **Then** new rows are appended with the experiment ID stamped in the corresponding column, and old rows retain their original (possibly empty) experiment ID.
2. **Given** the researcher runs with `--config-override KEY=VALUE`, **When** the experiment executes, **Then** the override is reflected in the run's config and recorded in the experiment's `PARAMS.json`.
3. **Given** the researcher runs with multiple `--config-override` flags, **When** the experiment executes, **Then** all overrides are applied; precedence over baseline config is documented.

---

### User Story 3 - Scan past experiments at a glance (Priority: P3)

After running 5+ experiments, the researcher needs to remember "what did we try, and what did we find?" without reading every `ANALYSIS.md`. They want a single `findings.md` at the project root that lists every experiment chronologically with a one-line summary, so a 30-second scan reveals which experiments produced strong findings, which were inconclusive, and which haven't been analyzed yet.

**Why this priority**: Important for maintaining research momentum, but not critical until the corpus grows beyond what fits in working memory. P1/P2 deliver value with N=1; this story delivers value at N≥5.

**Independent Test**: A researcher runs the aggregation tool against an `experiments/` directory containing 5 experiment subdirs (with varying completion states), gets a `findings.md` at the project root listing all 5 with their one-line summaries (or a "pending" marker for incomplete ones).

**Acceptance Scenarios**:

1. **Given** an `experiments/` directory containing 3 completed experiments and 1 in-progress, **When** the aggregator runs, **Then** `findings.md` lists all 4 in chronological order, with one-line summaries for completed ones and a "pending analysis" marker for the in-progress one.
2. **Given** an experiment's `ANALYSIS.md` is missing the one-line summary marker, **When** the aggregator runs, **Then** the experiment appears in the listing with a "summary missing" marker (not silently omitted).

---

### Edge Cases

- **Experiment directory already exists**: the new-experiment command refuses to overwrite; provides clear error with the conflict path.
- **`experiment_id` missing from existing CSV rows**: backward-compatible — the column is optional in older rows; analyzer treats absent values as "baseline" or "ungrouped".
- **`--config-override KEY=VALUE` with malformed VALUE**: command refuses to start, reports parse error with the offending flag.
- **`--config-override` conflicts with an explicit named flag** (e.g., `--debate-rounds 1 --config-override max_debate_rounds=2`): later override wins; precedence is documented; warning is emitted.
- **`ANALYSIS.md` exists but has no one-line summary**: aggregator includes the experiment with a "summary missing" marker.
- **Aggregator run when `experiments/` is empty**: produces `findings.md` with a "no experiments yet" placeholder, not an error.
- **`PARAMS.json` is invalid JSON**: runner refuses to start; clear error with the file path.
- **Two experiments started on the same date**: the directory naming (`<date>-<seq>-<name>`) handles this via the sequence number.

## Requirements *(mandatory)*

### Functional Requirements

#### Directory convention

- **FR-001**: A new-experiment command MUST create a directory at `experiments/<YYYY-MM-DD>-<NNN>-<short-name>/` where `<NNN>` is a zero-padded sequence number that increments within the same day.
- **FR-002**: The new-experiment command MUST populate the directory with a templated `HYPOTHESIS.md`, an empty `PARAMS.json` (`{}`), and a stub `run.sh` (or `run.ps1`) containing a one-line repro command.
- **FR-003**: The new-experiment command MUST refuse to overwrite an existing experiment directory; the error MUST clearly identify the conflict.
- **FR-004**: The `experiments/<id>/` directory MUST be the canonical location for that experiment's `HYPOTHESIS.md`, `PARAMS.json`, raw output (e.g., `results.csv`), and `ANALYSIS.md`.

#### experiment_id column

- **FR-005**: The backtest runner MUST accept an `--experiment-id <id>` flag that, when provided, stamps every output row with that ID.
- **FR-006**: The backtest CSV schema MUST include an `experiment_id` column; the column MUST be optional (older rows without the value are not malformed).
- **FR-007**: When `--experiment-id` is omitted, the corresponding column value in new rows MUST be empty (treated as "ungrouped" / "baseline" by downstream analysis).

#### Config override

- **FR-008**: The backtest runner MUST accept a repeatable `--config-override KEY=VALUE` flag that overlays the value onto the runtime config dict for the duration of the run.
- **FR-009**: When `--config-override` is used, the effective key/value MUST be recorded in the experiment's `PARAMS.json` automatically (no manual sync required).
- **FR-010**: When `--config-override KEY=VALUE` conflicts with an explicit named flag (e.g., `--debate-rounds`), the system MUST resolve precedence in a documented and predictable way (specifically: the override wins; a warning is emitted).
- **FR-011**: Malformed `--config-override` values (non-parseable VALUE, unknown KEY) MUST cause the runner to refuse to start with a clear error message.

#### Aggregator

- **FR-012**: A `findings_aggregate` tool MUST walk every directory matching `experiments/<YYYY-MM-DD>-<NNN>-<short-name>/` and emit a single `findings.md` at the project root.
- **FR-013**: The aggregator MUST extract the one-line summary from each experiment's `ANALYSIS.md` from a documented location (e.g., the first line, or a specific marker like a frontmatter field).
- **FR-014**: For experiments missing `ANALYSIS.md` or missing the one-line summary marker, the aggregator MUST include the experiment in the output with an explicit "pending analysis" or "summary missing" marker (not silently omit).
- **FR-015**: The output `findings.md` MUST be ordered chronologically (oldest experiment first, or newest — to be decided in design but consistent).
- **FR-016**: `findings.md` MUST be tracked in git so it functions as a project-level lab notebook visible on the repo's GitHub page.

### Key Entities

- **Experiment**: A single test of one variation against a baseline. Identified by `<YYYY-MM-DD>-<NNN>-<short-name>`. Owns a directory containing hypothesis, parameters, raw output, and analysis. Has a one-line summary suitable for aggregation.
- **HYPOTHESIS file**: Markdown record of what the experiment tests, predicted outcome, success criterion, link to the brainstorm idea (e.g., MR-1, WC-12) it traces back to.
- **PARAMS file**: JSON record of the exact knobs varied vs the baseline. Auto-populated by the runner when `--config-override` is used; manually populated otherwise.
- **Results file**: Raw output of the experiment (typically `results.csv` from the backtest runner). Gitignored.
- **ANALYSIS file**: Markdown record of what was found, decisions made, with a one-line summary at a documented location.
- **findings.md**: Project-root aggregation of one-line summaries from all experiments. Living lab notebook.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A researcher can go from "I have an idea" to "I'm running an experiment with the hypothesis on disk" in under 2 minutes (i.e., the new-experiment command + filling out HYPOTHESIS.md + invoking the runner).
- **SC-002**: A researcher can answer "what experiments have I run?" by reading a single file in under 30 seconds, regardless of how many experiments have been run.
- **SC-003**: 100% of completed experiments have their hypothesis, parameters, and results stored in the same directory and remain reconstructable from disk for at least 6 months without external context.
- **SC-004**: A new experiment that varies a single config knob can be set up by adding one `--config-override` flag and one `--experiment-id` flag, without copying or modifying the runner script.
- **SC-005**: When the corpus reaches 10 experiments, the aggregator produces `findings.md` in under 1 second on a developer laptop.
- **SC-006**: An experiment whose hypothesis was written down can be re-run by anyone (including future-self) by executing the `run.sh` (or `run.ps1`) in its directory, with no out-of-directory context required beyond the API key.

## Assumptions

- The backtest runner (`scripts/backtest.py`) is the primary experiment harness; the scaffolding extends it rather than replacing it. Future experiment runners (event-log-based, gate-tester, contradiction-analyzer) follow the same `experiment_id` + `--config-override` pattern.
- The one-line summary in `ANALYSIS.md` lives at a fixed location (default assumption: the first non-empty line after a top-level `# ` heading; subject to refinement in `/speckit.plan`).
- `findings.md` is meant to be human-scanned, not consumed by an automated tool downstream. If automation is needed later, the structured `ANALYSIS.md` files remain the source of truth.
- Sequence numbers within a day reset across days; cross-day uniqueness comes from the date prefix.
- The `experiments/` directory itself is tracked in git; only specific files inside it (`results.csv`, `events.db`) are gitignored per the existing `.gitignore` patterns. `HYPOTHESIS.md`, `PARAMS.json`, `ANALYSIS.md`, and `run.sh` ARE tracked — they are the corpus.
- Experiments may produce non-CSV outputs (JSONL for contradiction analysis, logs, plots). The convention accommodates these; the gitignore patterns already cover `results.csv` and `events.db` and can be extended as new output types appear.
