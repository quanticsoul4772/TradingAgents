#!/usr/bin/env bash
# Repro command for experiment 2026-05-04-003-multi-sector-phase-d-q1-2026
# Phase D substrate generalization: XLF + XLE on same Q1 2026 dates as XLK.
# --analysts market,news (no fundamentals — ETFs return 404 from yfinance fundamentals).
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-04-003-multi-sector-phase-d-q1-2026" \
    --tickers XLF,XLE \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --max-runs 20 \
    --analysts market,news \
    --debate-rounds 1 \
    --provider anthropic \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --config-override uw_momentum_filter_threshold=-5.0 \
    --out "experiments/2026-05-04-003-multi-sector-phase-d-q1-2026/results.csv" \
    --yes
