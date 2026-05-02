# Contract: `scripts/backtest.py` extensions

Two new flags + one new CSV column added to the existing `scripts/backtest.py`. **No flags removed; no existing behavior changes for invocations that don't use the new flags.**

## New flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--experiment-id <id>` | string | empty | Stamps every output row with this ID. Validated against the Experiment ID regex (`data-model.md`). When non-empty, also triggers `PARAMS.json` auto-sync per R-007. |
| `--config-override KEY=VALUE` | repeatable | none | Overlays the value onto the runtime config dict for this run only. Repeatable for multiple overrides. |

## CSV schema change

The `experiment_id` column is appended to the existing schema (last position, per R-004):

**Before**:
```
ticker, analysis_date, rating, error, run_seconds, deep_model, quick_model, debate_rounds, analysts
```

**After**:
```
ticker, analysis_date, rating, error, run_seconds, deep_model, quick_model, debate_rounds, analysts, experiment_id
```

## `--config-override` parsing rules

(Per R-003.)

Each `--config-override KEY=VALUE` flag is parsed as follows:

1. Split on first `=`. The left side is `KEY`; everything after is `VALUE_RAW`.
2. If `VALUE_RAW` is wrapped in double quotes (`"..."`), strip the quotes and treat as string. Skip type coercion.
3. Otherwise attempt coercion in order:
   - Integer (`int(VALUE_RAW)`) — e.g., `"2"` → `2`
   - Float (`float(VALUE_RAW)`) — e.g., `"1.5"` → `1.5`
   - Boolean (case-insensitive `"true"` / `"false"`) — e.g., `"true"` → `True`
   - Null (case-insensitive `"none"` / `"null"`) — e.g., `"none"` → `None`
   - Fallback: string

4. Apply to the runtime config dict: `config[KEY] = COERCED_VALUE`. If `KEY` doesn't exist in `DEFAULT_CONFIG`, log a warning but proceed (allows future config keys without modifying this script).

## Precedence rules

(Per FR-010.)

When both `--debate-rounds N` (named flag) and `--config-override max_debate_rounds=M` (override) are present:
- The **override wins** (M is used).
- A warning is logged: `"--config-override max_debate_rounds=M overrides --debate-rounds N"`.

This mirrors the principle that `--config-override` is the more powerful tool — if the user reaches for it, they mean it.

## PARAMS.json auto-sync

(Per R-007 and FR-009.)

When `--experiment-id <id>` is non-empty AND any `--config-override` flag is present:

1. Resolve `experiments/<id>/PARAMS.json`. If the file doesn't exist, create it with the schema in `data-model.md`.
2. If the file exists and `config_overrides` is empty (`{}`), populate it with the effective override map.
3. If the file exists and `config_overrides` is non-empty, log a warning and skip the sync (preserves manual annotations). Do NOT raise.

## Behavior unchanged

- All existing flags continue to work as before.
- CSVs without `experiment_id` column remain readable (DataFrame missing the column → downstream code treats as empty).
- `pilot_results.csv` from prior runs is unaffected.

## Tests

- `test_backtest_writes_experiment_id_when_flag_present` — FR-005 enforcement
- `test_backtest_writes_empty_experiment_id_when_flag_absent` — FR-007 backward compat
- `test_config_override_int_coercion` — `--config-override max_debate_rounds=2` produces int 2
- `test_config_override_bool_coercion` — `--config-override pm_sees_debate=false` produces bool False
- `test_config_override_quoted_string` — `--config-override KEY="42"` produces str "42"
- `test_config_override_warns_on_unknown_key` — warning emitted, no exit
- `test_config_override_precedence_over_named_flag` — override wins, warning emitted
- `test_params_json_autosync_creates_file` — fresh experiment dir + override → PARAMS.json populated
- `test_params_json_autosync_preserves_manual_overrides` — existing non-empty config_overrides → warning + skip
- `test_old_csv_readable_with_new_schema` — pandas reads pilot_results.csv after the schema change without error
