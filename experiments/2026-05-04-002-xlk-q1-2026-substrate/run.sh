#!/usr/bin/env bash
# Repro command for experiment 2026-05-04-002-xlk-q1-2026-substrate
# Phase D substrate exploration: sector ETF (XLK) on same Q1 2026 dates as 007's NVDA half.
# --analysts market,news (no fundamentals — ETFs return 404 from yfinance fundamentals).
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-04-002-xlk-q1-2026-substrate" \
    --tickers XLK \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --max-runs 10 \
    --analysts market,news \
    --debate-rounds 1 \
    --provider anthropic \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --config-override uw_momentum_filter_threshold=-5.0 \
    --out "experiments/2026-05-04-002-xlk-q1-2026-substrate/results.csv" \
    --yes
