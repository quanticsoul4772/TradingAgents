#!/usr/bin/env bash
# Smoke test for the Brave-news re-pilot.
# 10 NVDA dates × Brave news (instead of yfinance) — same matched dates as
# WC-12 + MR-3 so we get a 4-way comparison: pilot / WC-12 / MR-3 / Brave.
# All other knobs at default. If forward-α improves, scale to full 65-pair.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers NVDA \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --news-vendor brave \
    --experiment-id "2026-05-02-007-brave-news-smoke" \
    --out "experiments/2026-05-02-007-brave-news-smoke/results.csv" \
    --yes
