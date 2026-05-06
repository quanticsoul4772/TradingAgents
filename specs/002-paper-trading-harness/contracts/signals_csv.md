# Contract: Signals CSV (input)

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Research**: [../research.md](../research.md) (R-9, R-10)

This contract defines the format of the CSV the harness consumes via `--signals-csv <path>`. Produced by `daily_signals.py --emit-csv` and compatible with the existing `experiments/<id>/results.csv` schema (the CSVs are interchangeable).

---

## File format

- **Encoding**: UTF-8 (per project convention; see CLAUDE.md "Always pass `encoding='utf-8'`")
- **Delimiter**: comma (standard)
- **Header row**: required; column order does not matter (parser uses column names, not positions)
- **Quoting**: standard CSV quoting; values containing commas must be quoted

---

## Required columns (the harness depends on these)

| Column | Type | Validation | Description |
|---|---|---|---|
| `ticker` | str | uppercase, ≤ 10 chars, optionally `.SUFFIX` | The equity symbol the signal applies to |
| `analysis_date` | str (ISO date YYYY-MM-DD) | parseable as `date.fromisoformat`; ≤ today | The trading date the signal was generated for |
| `rating` | str | one of: `Buy`, `Overweight`, `Hold`, `Underweight`, `Sell` | The 5-tier rating from the framework's Portfolio Manager |

---

## Optional columns (ignored by the harness; useful for analysis)

These columns appear in CSVs produced by `daily_signals.py --emit-csv` and `scripts/backtest.py`. The harness ignores them but does not error if present.

| Column | Type | Description |
|---|---|---|
| `gate_threshold` | int | Spec 003 contrarian gate percentile threshold used for this propagate |
| `a3_threshold` | float | A3 momentum filter threshold used for this propagate |
| `model_deep` | str | LLM identifier for the deep-think role (e.g. `claude-opus-4-7`) |
| `model_quick` | str | LLM identifier for the quick-think role |
| `run_seconds` | float | Wall-clock seconds the propagate took |
| `error` | str | Error message if propagate failed; empty string otherwise |
| `experiment_id` | str | The experiment this row belongs to (set by `scripts/backtest.py --experiment-id`) |

---

## Row-level rules

1. **One signal per (ticker, analysis_date)**: If multiple rows share the same `(ticker, analysis_date)`, the harness uses the LAST row in file order (per spec edge case). This is permissive — the producer should avoid emitting duplicates.
2. **Empty `rating` cell**: skipped silently (treated as no signal for that ticker on that date). Allows the producer to emit one row per ticker even when the propagate failed (with `error` populated and `rating` empty).
3. **`Hold`, `Underweight`, `Sell` ratings**: consumed for exit decisions on currently-held positions; do not open new positions.
4. **Unknown values in `rating`**: row is skipped with a warning logged via Python's `logging` module (the harness does not crash on unexpected values, supporting forward compatibility with future rating tiers).
5. **`analysis_date` in the future**: row is skipped silently (defensive; producer bug shouldn't crash consumer).

---

## Example

Compatible with both `daily_signals.py --emit-csv` output and existing `experiments/2026-05-05-003-signal-at-scale/results.csv`:

```csv
ticker,analysis_date,rating,error,run_seconds,deep_model,quick_model,debate_rounds,analysts,experiment_id
AAPL,2026-04-03,Hold,,534.31,claude-opus-4-7,claude-haiku-4-5,1,"market,news,fundamentals",2026-05-05-003-signal-at-scale
NVDA,2026-04-03,Overweight,,512.87,claude-opus-4-7,claude-haiku-4-5,1,"market,news,fundamentals",2026-05-05-003-signal-at-scale
GOOGL,2026-04-03,Overweight,,489.12,claude-opus-4-7,claude-haiku-4-5,1,"market,news,fundamentals",2026-05-05-003-signal-at-scale
CVX,2026-04-03,Underweight,,503.45,claude-opus-4-7,claude-haiku-4-5,1,"market,news,fundamentals",2026-05-05-003-signal-at-scale
ABBV,2026-04-03,Hold,,521.09,claude-opus-4-7,claude-haiku-4-5,1,"market,news,fundamentals",2026-05-05-003-signal-at-scale
```

---

## Producer contract (`daily_signals.py --emit-csv`)

The new `--emit-csv <path>` flag adds a CSV writer that:
- Writes the header row first
- Writes one row per ticker in the watchlist (regardless of rating value, including `Hold`)
- Includes all required columns + the optional columns produced by the existing daily_signals flow
- Writes the file atomically (temp file + rename) to avoid partial-write races against a concurrent `paper_trade step` consumer
- Overwrites any existing file at the path

---

## Consumer contract (`paper_trade.py`)

The harness:
- Reads the file once at command startup
- Indexes rows by `(ticker, analysis_date)` via pandas DataFrame
- Filters per `--date` (in `step` mode) or per trading day in the loop (in `replay` mode)
- Surfaces unparseable rows as a one-line error and exits with code 2

The consumer is FORWARD-COMPATIBLE: future addition of optional columns to the CSV does NOT require harness changes.
