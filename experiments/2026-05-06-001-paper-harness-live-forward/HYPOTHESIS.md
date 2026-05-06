# Hypothesis: paper-harness live-forward 5-day exercise

**Experiment ID**: `2026-05-06-001-paper-harness-live-forward`
**Created**: 2026-05-06
**Source idea**: First end-to-end live-forward exercise of Spec 002 paper-trading harness (commit `b35a522` merged 2026-05-06)
**Cost estimate**: ~$10-20 (5 tickers × ~$0.40/propagate × 5 trading days = ~$10; +reserve for transient failures)
**Cost tier**: T2 (standard, $5-30)

## What we're testing

The harness was validated for P&L math (SC-001 reproduces SC-003 within 128 bps) and idempotency (SC-002 byte-identical re-run). What we have NOT exercised is the **end-to-end pipeline against fresh signals over multiple trading days**:

1. `daily_signals.py --emit-csv ...` writes a normalized CSV (Spec 002 contract)
2. `paper_trade.py step --signals-csv ...` consumes it, opens/closes positions per policy, persists state, writes digest
3. Repeat for 5 consecutive trading days
4. Inspect cumulative state evolution + P&L vs SPY

**Question**: does the operator-product surface (`daily_signals → paper_trade`) work end-to-end over a multi-day live run, or are there integration bugs that the SC-001 reproduction (single-shot replay) didn't catch?

## Setup

- **Watchlist**: 5 tickers, Tech-heavy (AAPL, MSFT, NVDA, GOOGL, AMZN). File: `experiments/2026-05-06-001-paper-harness-live-forward/watchlist.txt` — separate from the default `data/watchlists/tech_weighted.txt` to keep this experiment's universe explicit and reproducible.
- **Trading days**: 2026-05-06 through 2026-05-12 (Wed → Tue, 5 business days).
- **Signal-gen config**: standard product defaults (Opus deep + Haiku quick + 3 analysts + 1 round + exa news + A3 ON + spec 003 active).
- **Harness config**: DEFAULT policy (21d window, 8 max positions, 10% per slot, 50% sector cap, 5 bps slippage, SPY benchmark). $100k starting equity. portfolio_id = `live-forward-2026-05-06`.

## Predicted findings

**Scenario A (clean integration)** — ~70%
- 5 days run without errors
- Some bullish entries open at next-trading-day close
- State JSON evolves coherently across days (cash → positions → cash on close)
- Idempotency holds (re-running step for an already-processed day is no-op)
- Daily digests render with correct numbers

**Scenario B (integration bug surfaces)** — ~20%
- Some specific failure mode: signals CSV format mismatch, state corruption on re-run, sector-cap math edge case, etc.
- Recoverable by patching the bug; experiment continues
- Documents the bug + fix as the experiment's actual yield

**Scenario C (signal-gen fails)** — ~5%
- daily_signals.py errors on some ticker/day (network, exa quota, etc.)
- Partial signal coverage; harness handles missing rows correctly per SignalCSVRow rule 4

**Scenario D (no commits)** — ~5%
- All 5 days × 5 tickers produce Hold (calibrated abstention)
- Portfolio remains 100% cash; harness exercises only the no-op path
- Validates that no-trade days don't crash, but doesn't exercise position-opening flow

## Success criterion

- [ ] All 5 trading days complete without crashing the harness
- [ ] State JSON parseable + validates after each day
- [ ] Event log JSONL contains a `mark` event per day + entries/exits as appropriate
- [ ] Final digest's ITD α vs SPY directionally correct (positive if any bullish entries closed; near-zero if all-Hold)
- [ ] Total cost ≤ $20

## Methodology notes

- **Why 5 tickers not the full 25-ticker tech_weighted.txt**: budget constraint (25 tickers × 5 days ≈ $50 = T3 territory; not justified for first-exercise experiment). The 5-ticker subset still exercises sector-cap math (all Tech, well under 50% cap) and per-position-cap math.
- **Why not 5 tickers × 1 day**: doesn't exercise multi-day state evolution or idempotency in cron context.
- **Holding-window-elapsed exits won't fire**: 5 days < 21d window; experiment terminates with positions still open. Final digest will show unrealized P&L only.

## Reproducibility

- `run.sh` / `run.ps1` show the exact daily_signals + paper_trade command sequence
- Watchlist file: `experiments/<id>/watchlist.txt`
- Per-day signal CSVs persist at `~/.tradingagents/paper/signals-<date>.csv`
- Portfolio state at `~/.tradingagents/paper/live-forward-2026-05-06.json` + `.events.jsonl`
- Daily digests at `claudedocs/paper-live-forward-2026-05-06-<date>.md`
