# Quickstart: Paper-Trading Harness

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Operator-facing walkthrough: from zero to "first replay run reproducing SC-003" to "first daily live-forward step." Once implementation lands, this doc moves to `docs/PAPER_TRADING.md`.

---

## Prerequisites

- `tradingagents-lab` installed editable: `pip install -e .`
- Python 3.10+ (3.12.8 recommended; matches dev venv)
- yfinance access (no API key required)
- Optional: existing `experiments/2026-05-05-003-signal-at-scale/results.csv` if you want to run the SC-001 reproduction validation gate; otherwise the unit tests + a synthetic CSV are sufficient

---

## Walkthrough 1 — First replay run (validation gate)

The first thing to do with the harness is verify it reproduces SC-003 within tolerance. This is the SC-001 validation gate.

### Step 1: Generate a temp watchlist from the SC-003 CSV

```bash
python -c "import pandas as pd; df = pd.read_csv('experiments/2026-05-05-003-signal-at-scale/results.csv'); print('\\n'.join(sorted(df['ticker'].unique())))" > /tmp/sc003-watchlist.txt
```

(The default `data/watchlists/tech_weighted.txt` is a different ~25-ticker universe; for SC-001 reproduction we use the exact 50 SC-003 tickers.)

### Step 2: Run the replay

```bash
python scripts/paper_trade.py replay \
    --signals-csv experiments/2026-05-05-003-signal-at-scale/results.csv \
    --watchlist /tmp/sc003-watchlist.txt \
    --start 2026-04-03 \
    --end 2026-05-04 \
    --portfolio-id sc003-validation \
    --yes
```

Expected wall-clock: < 60 seconds (yfinance fetches dominate).

### Step 3: Inspect the output digest

```bash
cat claudedocs/paper-sc003-validation-2026-05-04.md
```

Look for the ITD α vs SPY line in the Summary table. Expected value: within ±100 bps of +5.96% (SC-003 bullish-bucket mean α). The harness applies the per-position cap (15%) and per-sector cap (50%), which may dampen the headline number; ±100 bps tolerates that.

### Step 4: Run the validation test directly

```bash
pytest tests/test_paper_sc003_reproduction.py -v
```

This is the same logic as steps 1-3 wrapped in an integration-marked test. Pass = green; failure = check whether the SC-003 CSV is present and the harness logic is correct.

---

## Walkthrough 2 — Live-forward step (cron-able daily flow)

For daily use, the operator runs two commands in sequence: signal generation, then portfolio update.

### Step 1: Generate today's signals

```bash
python scripts/daily_signals.py \
    --tickers data/watchlists/tech_weighted.txt \
    --emit-csv ~/.tradingagents/paper/today-signals.csv
```

Cost: ~$2-4 in LLM calls per run (Opus + Haiku) for a 25-ticker watchlist. This is the only LLM-incurring step in the daily flow.

### Step 2: Update the paper portfolio

```bash
python scripts/paper_trade.py step \
    --signals-csv ~/.tradingagents/paper/today-signals.csv
```

Cost: $0 LLM. Wall-clock: < 10 seconds. Outputs:
- Updates `~/.tradingagents/paper/default.json`
- Appends events to `~/.tradingagents/paper/default.events.jsonl`
- Writes `claudedocs/paper-default-<today>.md`
- Prints one-line summary to stdout (e.g. `step OK: D=2026-05-06, equity=$103,247.12, +0.31% vs SPY, opens=2, closes=1`)

### Step 3: (Recommended) wrap in a cron / scheduled task

**Linux/macOS** (crontab, weekday after market close at 17:00 ET):

```cron
0 17 * * 1-5 cd /path/to/tradingagents-lab && \
    .venv/bin/python scripts/daily_signals.py --tickers data/watchlists/tech_weighted.txt --emit-csv ~/.tradingagents/paper/today-signals.csv && \
    .venv/bin/python scripts/paper_trade.py step --signals-csv ~/.tradingagents/paper/today-signals.csv >> ~/.tradingagents/paper/cron.log 2>&1
```

**Windows** (Task Scheduler with PowerShell):

```powershell
$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-Command `"cd C:\Development\Projects\TradingAgents; .\.venv\Scripts\python.exe scripts\daily_signals.py --tickers data\watchlists\tech_weighted.txt --emit-csv $env:USERPROFILE\.tradingagents\paper\today-signals.csv; .\.venv\Scripts\python.exe scripts\paper_trade.py step --signals-csv $env:USERPROFILE\.tradingagents\paper\today-signals.csv`""
$trigger = New-ScheduledTaskTrigger -Daily -At "5:00PM"
Register-ScheduledTask -TaskName "tradingagents-paper-daily" -Action $action -Trigger $trigger
```

Idempotency (per FR-010, SC-002): if the cron fires twice on the same day, the second invocation is a no-op.

---

## Walkthrough 3 — Inspect portfolio at any time

```bash
python scripts/paper_trade.py status
```

Renders the current state digest to stdout without modifying anything. Useful for quick check-ins between cron runs.

For a different portfolio_id:

```bash
python scripts/paper_trade.py status --portfolio-id tech-only
```

---

## Walkthrough 4 — Multiple portfolios (e.g. ablating policy)

The harness supports multiple portfolios via `--portfolio-id`. Each gets its own state file + event log. Useful for A/B comparison of different policies (e.g. 21d vs 30d holding window).

### Setup the alternative-policy portfolio

Create a policy override JSON file (e.g. `policy-30d.json`):

```json
{
  "policy_version": "v1-alpha-30d",
  "holding_window_trading_days": 30,
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
```

### Run replay with the override

```bash
python scripts/paper_trade.py replay \
    --signals-csv ... \
    --watchlist ... \
    --start 2026-01-01 --end 2026-04-30 \
    --portfolio-id policy-30d \
    --policy policy-30d.json \
    --yes
```

Compare to a baseline portfolio of the same dates with the default policy. Per Constitution Principle II, this is a one-experiment-per-change ablation: only `holding_window_trading_days` varies.

---

## State file inspection

State files are human-readable JSON; inspect with any text editor or `jq`:

```bash
jq '.cash, .positions | keys, .closed | length' ~/.tradingagents/paper/default.json
```

Event log (one JSON object per line):

```bash
tail -20 ~/.tradingagents/paper/default.events.jsonl | jq .
```

Filter to entries only:

```bash
grep '"event_type": "entry"' ~/.tradingagents/paper/default.events.jsonl | jq .payload
```

---

## Backup

The harness does NOT auto-backup. Operator responsibility:

```bash
# Daily snapshot
cp -r ~/.tradingagents/paper ~/.tradingagents/paper.$(date +%Y-%m-%d).bak
```

Or a Git repo dedicated to the state dir, committed daily.

---

## Troubleshooting

### "No portfolio found"

`status` couldn't find a state file at the expected path. Either:
- The `portfolio_id` is wrong (typo)
- No `step` or `replay` has ever run for this id (first-time use; expected)
- `TRADINGAGENTS_CACHE_DIR` env var is set differently than when the state was written

### "Corrupt state file"

Validation failed on load. Either:
- Manual edit broke the schema → restore from backup
- Power loss / crash mid-write → check for `.json.tmp` file in same dir; can restore from it if it parses
- Schema version mismatch (after upgrade) → run the migration script (when published; v1 has no migrations)

### "Already processed"

`step` exited early because today's date is in the equity_curve. Expected behavior on cron re-fire. To force a re-run (rare; e.g. data correction), delete that day's `mark` event from the JSONL and remove the equity_curve entry from the JSON state — but this is an unsafe manual operation and breaks the replay invariant. Better: start a new portfolio_id.

### "Insufficient cash" on every entry

The cash_buffer_pct floor is being hit. Check `policy_snapshot.cash_buffer_pct` and consider raising starting_equity or lowering target_per_position_pct.

### "Per-sector cap exceeded"

The signals are clustering in one sector. The harness is correctly applying the cap; the skip events in the digest tell you which entries were turned away. To override (e.g. for a tech-only portfolio), provide a custom policy with `per_sector_cap_pct: 100`.

---

## What this harness does NOT do (per spec scope)

- Execute real trades (broker integration: out of scope, Principle IV)
- Open short positions (FR-007)
- Tax-lot accounting
- Fractional shares (v1 limitation)
- Auto-back-fill missed days (operator-initiated via `replay`)
- Generate signals (use `daily_signals.py` separately)
- Send notifications (no email, Slack, push — operator reads the digest)

---

## Next reading

- `spec.md` — full feature specification (functional requirements, success criteria)
- `plan.md` — implementation plan (file-by-file delta)
- `data-model.md` — entity definitions + state transitions
- `contracts/` — wire-format contracts (CLI, CSV, JSON state, JSONL events, digest markdown)
- `research.md` — technical-decision rationale
