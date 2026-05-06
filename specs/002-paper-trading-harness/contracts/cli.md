# Contract: `paper_trade.py` CLI surface

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

This contract defines the CLI surface of `scripts/paper_trade.py`. The CLI is a typer app with three subcommands: `replay`, `step`, `status`. Plus the `daily_signals.py --emit-csv` addition this spec depends on.

---

## `paper_trade replay`

Deterministic backtest over a date range using a fixed signals CSV.

```
python scripts/paper_trade.py replay \
    --signals-csv <path> \
    --watchlist <path> \
    --start <YYYY-MM-DD> \
    --end <YYYY-MM-DD> \
    [--portfolio-id <str>] \
    [--starting-equity <Decimal>] \
    [--policy <path-to-policy-json>] \
    [--digest-dir <path>] \
    [--state-dir <path>] \
    [--no-write-state] \
    [--yes]
```

**Required arguments**:
- `--signals-csv <path>` — input CSV per `signals_csv.md` contract
- `--watchlist <path>` — newline-separated tickers (`#` comments OK)
- `--start <YYYY-MM-DD>` — first signal date to process (inclusive)
- `--end <YYYY-MM-DD>` — last signal date to process (inclusive)

**Optional arguments** (defaults shown):
- `--portfolio-id default` — `[a-zA-Z0-9_-]+`, ≤ 64 chars
- `--starting-equity 100000` — Decimal-parseable
- `--policy <path>` — path to a JSON file matching the PolicySnapshot schema; if absent, uses default policy
- `--digest-dir claudedocs/` — where per-day digests are written (`paper-<id>-<date>.md`)
- `--state-dir <TRADINGAGENTS_CACHE_DIR>/paper/` — where state JSON + events JSONL live
- `--no-write-state` — flag; if set, runs in dry-mode (no state file or event log writes; digests still emitted to console). Useful for sanity checking before committing to a portfolio.
- `--yes` — flag; skip the cost-confirmation prompt (the prompt prints "0 LLM API calls expected" and waits for ENTER unless `--yes` is set).

**Behavior**:
1. Load existing state for `portfolio_id` if present; otherwise initialize empty Portfolio with `inception_date=start`.
2. For each trading day from `start` to `end` inclusive (skipping weekends/holidays):
   - Filter signals CSV to today's `analysis_date` rows.
   - Run `engine.step(today, todays_signals_dict)`.
   - Append events to JSONL.
   - Write today's digest.
3. After all days processed, print summary to console: total entries, total exits, final equity, ITD α vs benchmark.
4. Exit code 0 on success; nonzero on validation failure.

**Idempotency**: each day's `step` call honors R-5 (skip if already in equity_curve). Re-running replay for an already-processed range is a no-op.

---

## `paper_trade step`

Process a single trading day. Designed to be cron-able.

```
python scripts/paper_trade.py step \
    --signals-csv <path> \
    [--date <YYYY-MM-DD>] \
    [--portfolio-id <str>] \
    [--digest-dir <path>] \
    [--state-dir <path>] \
    [--no-write-state]
```

**Required arguments**:
- `--signals-csv <path>` — input CSV per `signals_csv.md` contract; the CSV must contain at least one row whose `analysis_date == --date` (or today, if `--date` omitted)

**Optional arguments**:
- `--date <YYYY-MM-DD>` — defaults to today's date (system local)
- `--portfolio-id default`
- `--digest-dir claudedocs/`
- `--state-dir <TRADINGAGENTS_CACHE_DIR>/paper/`
- `--no-write-state` — dry-run

**Behavior**:
1. Load state for `portfolio_id`; if missing, initialize empty Portfolio with `inception_date=date`.
2. Filter signals CSV to `--date` rows.
3. If `--date` is already in `equity_curve`, exit early with a one-line message; append `step_skipped_already_processed` event.
4. Otherwise run `engine.step(date, signals)`, persist state + event log, write digest.
5. Print one-line summary to console: e.g. `step OK: D=2026-05-06, equity=$103,247.12, +0.31% vs SPY, opens=2, closes=1`.
6. Exit code 0 on success; nonzero on validation failure.

**Required idempotency property**: byte-identical state file before/after re-run for same `--date` (SC-002).

---

## `paper_trade status`

Read-only inspection of current state.

```
python scripts/paper_trade.py status \
    [--portfolio-id <str>] \
    [--state-dir <path>] \
    [--mark-to-date <YYYY-MM-DD>]
```

**Optional arguments**:
- `--portfolio-id default`
- `--state-dir <TRADINGAGENTS_CACHE_DIR>/paper/`
- `--mark-to-date <YYYY-MM-DD>` — re-mark open positions to the close on this date (for "what's my unrealized P&L right now"); defaults to today

**Behavior**:
1. Load state for `portfolio_id`. If file does not exist, print "No portfolio found" and exit 0.
2. Fetch latest close prices for all open positions + benchmark.
3. Compute unrealized P&L per position; aggregate equity + α vs benchmark.
4. Render the standard digest to stdout (no file writes).
5. Exit 0.

**Important**: `status` MUST NOT modify state. It reads, marks, renders. No event log appends. No state file writes.

---

## `daily_signals.py --emit-csv` (modified)

The existing `daily_signals.py` gains a new option:

```
python scripts/daily_signals.py \
    [...existing options...] \
    --emit-csv <path>
```

When set, after running propagates over the watchlist, also writes a CSV with the schema defined in `signals_csv.md`. The markdown digest output (existing behavior) is unaffected. CSV is overwritten if it already exists.

---

## Error handling

All subcommands handle the following failure modes:
- Missing required CSV file → exit 2 with one-line error
- Malformed CSV (missing required columns, unparseable dates) → exit 2 with the offending row
- Corrupted state JSON → exit 3 with offset of failed parse + suggestion to inspect the file
- Network failure during yfinance fetch → retry once; on second failure log a `data_anomaly` event and continue (per FR-016)
- PolicySnapshot validation failure on load → exit 4 with the failing field

No exceptions propagate as Python tracebacks to operator stdout; all errors land as one-line messages with an `[error]` prefix.

---

## What the CLI MUST NOT do

- Make LLM API calls (SC-008). The CLI is a pure consumer of pre-generated signals.
- Open short positions (FR-007). `Sell` and `Underweight` ratings only trigger exits.
- Auto-invoke `daily_signals.py` to generate signals on demand (out of scope for v1; per spec assumption "signal generation cost is operator's responsibility").
- Write to anywhere outside `<state-dir>` and `<digest-dir>`.
- Modify any framework-level state (memory log, signals cache, checkpoint DBs).
