# Contract: `scripts/new_experiment.py` CLI

## Synopsis

```bash
python scripts/new_experiment.py <short-name> [--source-idea <id>] [--cost <usd>]
```

## Arguments

| Arg | Required | Description |
|---|---|---|
| `<short-name>` | yes | 2-4 word kebab-case slug, validated against `^[a-z0-9][a-z0-9-]{0,38}[a-z0-9]$` |

## Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--source-idea` | string | empty | Reference to entry in `docs/EXPERIMENT.md` (e.g., `MR-1`, `WC-12`, `EH-2`). Pre-fills the corresponding section of `HYPOTHESIS.md`. |
| `--cost` | float | empty | Pre-fills the cost-estimate line in `HYPOTHESIS.md`. Empty for zero-cost experiments. |
| `--date` | string | today UTC | Override the date prefix (advanced/testing only). |

## Behavior

1. Compute experiment ID:
   - `<date>` defaults to `datetime.now(UTC).strftime("%Y-%m-%d")`
   - Find next free sequence: scan `experiments/` for existing `<date>-NNN-*` dirs, take max + 1, zero-pad to 3 digits
   - Construct ID: `<date>-<NNN>-<short-name>`

2. Validate ID against the full regex (`data-model.md` Experiment validation rules). Exit 1 with a clear error if invalid.

3. Refuse if `experiments/<id>/` already exists (FR-003). Exit 1 with the conflict path.

4. Create directory and populate from templates (`tradingagents/experiments/templates.py`):
   - `HYPOTHESIS.md` — populated with experiment ID, date, source idea (if given), cost (if given), and section scaffolding per `data-model.md`
   - `PARAMS.json` — `{"config_overrides": {}, "explicit_flags": {}, "baseline": "", "notes": ""}`
   - `run.sh` — one-line stub: `#!/bin/bash\npython scripts/backtest.py --experiment-id "<id>" --out "experiments/<id>/results.csv" --yes`
   - `run.ps1` — PowerShell equivalent

5. Print:
   ```
   Created experiments/<id>/
   Next steps:
     1. Edit experiments/<id>/HYPOTHESIS.md
     2. Edit experiments/<id>/run.sh (or run.ps1) with the actual command
     3. Run: bash experiments/<id>/run.sh
     4. After it completes, write experiments/<id>/ANALYSIS.md
   ```

6. Exit 0.

## Exit codes

- `0` — success
- `1` — invalid short-name, conflict with existing dir, or filesystem error

## Tests

- `test_new_experiment_creates_dir_and_files` — happy path
- `test_new_experiment_refuses_duplicate` — FR-003 enforcement
- `test_new_experiment_rejects_invalid_short_name` — regex validation
- `test_new_experiment_increments_sequence_within_day` — multiple invocations same date
- `test_new_experiment_with_source_idea_prefills_hypothesis` — flag handling
