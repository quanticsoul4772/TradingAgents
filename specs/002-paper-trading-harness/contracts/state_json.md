# Contract: Portfolio state JSON

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

The materialized state of a paper-trading portfolio. One JSON file per `portfolio_id` at `~/.tradingagents/paper/<portfolio_id>.json`.

---

## File format

- **Path**: `<state-dir>/<portfolio_id>.json` where `<state-dir>` defaults to `<TRADINGAGENTS_CACHE_DIR or ~/.tradingagents>/paper/`
- **Encoding**: UTF-8
- **Indentation**: 2 spaces (consistency, not minified — supports diff inspection)
- **Decimal handling**: serialized as JSON strings (`"123.45"` not `123.45`) to preserve precision; reader uses `Decimal(s)` to parse
- **Date handling**: ISO 8601 dates as JSON strings (`"2026-05-06"`)

---

## Schema (top-level)

```json
{
  "portfolio_id": "default",
  "schema_version": 1,
  "inception_date": "2026-05-06",
  "starting_equity": "100000.00",
  "cash": "32500.55",
  "positions": {
    "NVDA": {
      "ticker": "NVDA",
      "qty": 25,
      "entry_date": "2026-05-07",
      "entry_price": "475.18",
      "entry_rating": "Overweight",
      "intended_close_date": "2026-06-09",
      "sector": "Technology"
    },
    "GOOGL": { ... }
  },
  "closed": [
    {
      "ticker": "AAPL",
      "qty": 50,
      "entry_date": "2026-04-04",
      "entry_price": "180.55",
      "entry_rating": "Overweight",
      "intended_close_date": "2026-05-05",
      "sector": "Technology",
      "exit_date": "2026-05-05",
      "exit_price": "175.21",
      "exit_reason": "window_elapsed",
      "raw_return": "-0.02958",
      "alpha_return": "-0.04231",
      "actual_holding_days": 21
    }
  ],
  "equity_curve": [
    { "date": "2026-04-04", "equity": "100000.00", "benchmark_equity": "100000.00" },
    { "date": "2026-04-07", "equity": "99875.50", "benchmark_equity": "100120.00" }
  ],
  "policy_snapshot": {
    "policy_version": "v1-alpha",
    "holding_window_trading_days": 21,
    "target_per_position_pct": "10.0",
    "n_max_positions": 8,
    "cash_buffer_pct": "10.0",
    "per_sector_cap_pct": "50.0",
    "per_position_cap_pct": "15.0",
    "entry_slippage_bps": "5.0",
    "exit_slippage_bps": "5.0",
    "benchmark": "SPY",
    "mid_window_exit_on_bear_signal": true,
    "re_entry_cooldown_trading_days": 0
  }
}
```

---

## Field-level notes

- **`schema_version`**: integer, currently `1`. Bumped on incompatible schema changes (with a migration step required).
- **`positions`**: dict keyed by ticker for O(1) lookup of "is this ticker held?" — avoids list scans.
- **`closed`**: list ordered by `exit_date` ascending. Append-only.
- **`equity_curve`**: list ordered by `date` ascending. One entry per processed trading day. Used for idempotency check (R-5).
- **`policy_snapshot`**: immutable for the portfolio's lifetime. Mid-life policy change requires explicit operator action (out of scope for v1; spec edge case).

---

## Atomic write

State writes use temp-file-plus-rename to guarantee atomicity:

```python
tmp = state_path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
tmp.replace(state_path)  # atomic on POSIX; near-atomic on Windows
```

This protects against partial writes on crash mid-step.

---

## Backwards compatibility

- New optional fields can be added without bumping `schema_version`. Loader uses `.get(key, default)` for all non-required reads.
- New required fields require a `schema_version` bump + a one-shot migration script.
- Removing or renaming fields is forbidden in v1; if needed, deprecate with a comment in the loader and bump `schema_version`.

---

## Validation on load

The `state.load_portfolio(state_path) -> Portfolio` function:
1. Reads + parses JSON; on parse failure raises `PortfolioStateError(f"Corrupt state file at {state_path}: {e}")`.
2. Constructs `Portfolio` dataclass; runs `Portfolio.validate()` (per data-model.md).
3. Returns the validated `Portfolio`.

If validation fails, the operator gets a one-line error pointing at the file path + the failing invariant. The state file is NOT auto-repaired; operator restores from backup or restarts the portfolio.

---

## What this file does NOT contain

- Per-event audit trail — that lives in the JSONL event log (separate contract).
- Per-day digests — those are emitted to `claudedocs/paper-<id>-<date>.md`.
- Daily signal CSVs — those are operator-provided inputs, not harness-managed state.
- LLM API state, prompts, or token counts — the harness has zero LLM exposure.
- Sector lookup cache — that lives in `<state-dir>/sectors.json` (separate file, shared across portfolios on the same machine).
