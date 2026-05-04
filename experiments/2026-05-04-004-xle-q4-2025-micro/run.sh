#!/usr/bin/env bash
# Repro command for experiment 2026-05-04-004-xle-q4-2025-micro
# Cross-period validation of sector-ETF bear-side accuracy from 003.
# Same XLE config as 003; date grid shifted to Q4 2025 (matching 008).
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-04-004-xle-q4-2025-micro" \
    --tickers XLE \
    --start 2025-11-07 \
    --end 2026-01-09 \
    --frequency W \
    --max-runs 10 \
    --analysts market,news \
    --debate-rounds 1 \
    --provider anthropic \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --config-override uw_momentum_filter_threshold=-5.0 \
    --out "experiments/2026-05-04-004-xle-q4-2025-micro/results.csv" \
    --yes
