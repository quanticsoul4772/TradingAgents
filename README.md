# TradingAgents — personal copy

Personal copy of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4 with my Anthropic config and a backtest harness on top. Upstream documentation lives in [`README.upstream.md`](README.upstream.md); upstream release history in [`CHANGELOG.md`](CHANGELOG.md).

## What's local

- **`main.py`** — Anthropic provider, Sonnet 4.6 deep / Haiku 4.5 quick, 1/1 debate rounds, checkpoint enabled.
- **`scripts/backtest.py`** — typer CLI that loops `propagate(ticker, date)` over a grid and appends to CSV. Resumable.
- **`scripts/analyze_backtest.py`** — alpha-vs-SPY analyzer for backtest output.
- **`tickers.txt`** — personal ticker universe (10 names, one per major sector). Picked up by `backtest.py` when `--tickers` is not given.
- **`claudedocs/SETUP.md`** — personal setup notes (state paths, provider switching, cost ranges, what not to touch).
- **`CLAUDE.md`** — Claude Code project context.

Single graph-layer change: `_fetch_returns` was extracted to a module-level `fetch_returns()` so the analyzer can import it without instantiating the full graph.

## Quick start

```bash
# Activate venv
.venv\Scripts\activate                    # Windows
source .venv/bin/activate                 # macOS/Linux

# One run with the baked-in config (NVDA, today's date in main.py)
python main.py

# Interactive menu, resume on crash
tradingagents analyze --checkpoint
```

Detailed setup, troubleshooting, and "what not to touch" list: [`claudedocs/SETUP.md`](claudedocs/SETUP.md).

## Backtest

```bash
# Uses tickers.txt by default; pass --tickers or --tickers-file to override.
python scripts/backtest.py \
    --start 2026-01-02 --end 2026-04-25 \
    --frequency W \
    --out backtest_results.csv

python scripts/analyze_backtest.py backtest_results.csv
```

Resumable: re-running with the same `--out` skips `(ticker, date)` pairs already present. Cost is gated by a confirmation prompt; `--yes` skips it.

## Current signal evidence

5 entries in `backtest_memory.md` (4 resolved, 1 pending). Sample is too small to claim an edge.

| Date       | Ticker | Call       | 5d return | Alpha vs SPY |
|------------|--------|------------|-----------|--------------|
| 2026-01-30 | NVDA   | Overweight | -3.0%     | -2.8%        |
| 2026-02-06 | NVDA   | Overweight | -1.4%     | -0.1%        |
| 2026-02-13 | NVDA   | Overweight | +4.8%     | +4.7%        |
| 2026-04-03 | AAPL   | Hold       | +0.1%     | -4.0%        |
| 2026-04-10 | AAPL   | Underweight | pending  |              |

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
