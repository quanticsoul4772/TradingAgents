#!/usr/bin/env bash
# Brave news on AAPL — companion to brave-news-smoke (NVDA).
# AAPL was bear-correct in this period (WC-12 cross-AAPL: Underweight α=+3.86%,
# Sell α=+0.95%). If Brave news produces more Sells AND those Sells continue to
# outperform, we have the calibration win we've been hunting.
# Same 10 dates as all NVDA experiments for matched comparison.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers AAPL \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --news-vendor brave \
    --experiment-id "2026-05-03-001-brave-news-smoke-aapl" \
    --out "experiments/2026-05-03-001-brave-news-smoke-aapl/results.csv" \
    --yes
