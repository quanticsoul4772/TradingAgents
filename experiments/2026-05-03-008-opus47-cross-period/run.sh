#!/usr/bin/env bash
# Repro command for experiment 2026-05-03-008-opus47-cross-period
# B-priority 2 cross-period validation: same config as 007 (Opus + A3 filter)
# but on Q4 2025 dates instead of Q1 2026.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-03-008-opus47-cross-period" \
    --tickers NVDA,AAPL,INTC \
    --start 2025-11-07 \
    --end 2026-01-09 \
    --frequency W \
    --max-runs 30 \
    --analysts market,news,fundamentals \
    --debate-rounds 1 \
    --provider anthropic \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --config-override uw_momentum_filter_threshold=-5.0 \
    --out "experiments/2026-05-03-008-opus47-cross-period/results.csv" \
    --yes
