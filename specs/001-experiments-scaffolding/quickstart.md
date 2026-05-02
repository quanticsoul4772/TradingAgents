# Quickstart: Experiments Scaffolding

Once `001-experiments-scaffolding` lands on `main`, here's the workflow for running your first experiment.

## Setup (one-time)

```bash
# Already done if you've followed the project setup
source .venv/Scripts/activate    # Git Bash on Windows
```

## Workflow

### 1. Create the experiment

```bash
python scripts/new_experiment.py mr1-contradiction --source-idea MR-1
```

Output:
```
Created experiments/2026-05-02-001-mr1-contradiction/
Next steps:
  1. Edit experiments/2026-05-02-001-mr1-contradiction/HYPOTHESIS.md
  2. Edit experiments/2026-05-02-001-mr1-contradiction/run.sh (or run.ps1) with the actual command
  3. Run: bash experiments/2026-05-02-001-mr1-contradiction/run.sh
  4. After it completes, write experiments/2026-05-02-001-mr1-contradiction/ANALYSIS.md
```

### 2. Fill in the hypothesis

Open `experiments/2026-05-02-001-mr1-contradiction/HYPOTHESIS.md`. Fill the templated sections:

- **What we're testing**: "Run mcp-reasoning_contradiction on the 65 bull/bear pairs from the original pilot to measure how often the debate is parallel monologue vs. real disagreement."
- **Why we expect <prediction>**: "Predict <30% will exhibit substantive contradiction (mode collapse hypothesis)."
- **Success criterion**: "Per-pair contradiction score recorded; aggregate distribution computed."
- **Source idea**: `MR-1`
- **Cost estimate**: ~$0 (no LLM calls; uses local mcp-reasoning).

### 3. Edit the run command

Open `experiments/2026-05-02-001-mr1-contradiction/run.sh`. The default stub assumes you'll run the backtest harness; for MR-1 (contradiction analysis on existing data), replace it:

```bash
#!/bin/bash
python scripts/extract_debates.py \
    --logs ~/.tradingagents/logs/ \
    --out experiments/2026-05-02-001-mr1-contradiction/debates.jsonl
python scripts/analyze_contradictions.py \
    --in experiments/2026-05-02-001-mr1-contradiction/debates.jsonl \
    --out experiments/2026-05-02-001-mr1-contradiction/results.jsonl
```

(Those two scripts don't exist yet — they'd be a subsequent feature. The point is `run.sh` is yours to tailor per experiment.)

### 4. Run

```bash
bash experiments/2026-05-02-001-mr1-contradiction/run.sh
```

Results land in `experiments/2026-05-02-001-mr1-contradiction/results.jsonl` (gitignored).

### 5. Write the analysis

Open `experiments/2026-05-02-001-mr1-contradiction/ANALYSIS.md`. Use the template from `data-model.md`:

```markdown
# Analysis: mr1-contradiction

22 of 65 bull/bear pairs (34%) exhibit substantive contradiction; 43 (66%) are parallel monologue.

## Result

[the table, plot references, etc.]

## Decision

[Confirms/refutes the hypothesis. Implications for next experiment.]
```

The first line after the H1 IS the one-line summary that lands in `findings.md`.

### 6. Aggregate

```bash
python scripts/findings_aggregate.py
```

Updates `findings.md` at the project root with the new experiment at the top. Commit it:

```bash
git add findings.md experiments/2026-05-02-001-mr1-contradiction/
git commit -m "experiment: 2026-05-02-001-mr1-contradiction — 34% substantive contradiction"
```

(Note: `experiments/<id>/results.jsonl` is gitignored. `HYPOTHESIS.md`, `PARAMS.json`, `ANALYSIS.md`, `run.sh` ARE tracked.)

## Workflow for the second class of experiment: varying a backtest knob

Example: WC-12 (PM blind to debate). This uses the existing backtest harness with one config knob varied.

### 1. Create

```bash
python scripts/new_experiment.py pm-blind --source-idea WC-12 --cost 10
```

### 2. Fill HYPOTHESIS.md

What's varied: `pm_sees_debate=false`. Baseline: 10 dates from the pilot. Predict: ratings unchanged in >80% of cases (debate is decorative).

### 3. Edit run.sh — use the standard backtest harness

```bash
#!/bin/bash
python scripts/backtest.py \
    --tickers NVDA,AAPL \
    --start 2026-02-01 --end 2026-04-15 \
    --frequency W \
    --experiment-id 2026-05-02-002-pm-blind \
    --out experiments/2026-05-02-002-pm-blind/results.csv \
    --config-override pm_sees_debate=false \
    --yes
```

The `--experiment-id` flag stamps every CSV row. The `--config-override` flag varies the single knob and auto-syncs into `PARAMS.json`.

### 4. Run, analyze, aggregate

Same as before.

## Common questions

**Q: What if I run the same experiment twice?**
The new-experiment command refuses (FR-003). Either delete the old dir or pick a new short-name.

**Q: What if I vary two config knobs?**
Don't (Constitution Principle II). If you must, use multiple `--config-override` flags but the experiment is no longer a clean ablation. Document in `HYPOTHESIS.md` why.

**Q: Where do experiment results go if I forget `--out`?**
The default of `scripts/backtest.py` is `backtest_results.csv` at the project root (unchanged). The convention is to set `--out experiments/<id>/results.csv` so results land alongside the hypothesis. The `run.sh` stub created by `new_experiment.py` does this for you.

**Q: How do I find a past experiment?**
`cat findings.md` — newest first. Each entry links to its HYPOTHESIS and ANALYSIS files.

**Q: Can I re-run someone else's experiment?**
Yes. `bash experiments/<id>/run.sh` is meant to be a complete reproduction command, requiring only the API key in `.env`. (SC-006.)
