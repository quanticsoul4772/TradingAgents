#!/usr/bin/env bash
# Repro command for experiment 2026-05-04-001-nvda-q3-2025-micro
# B-priority 2b micro-pilot: NVDA-only Q3 2025 cross-period test.
# Same config as 007 + 008 (Opus + Haiku + A3 filter + exa + 3 analysts + 1 round).
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-04-001-nvda-q3-2025-micro" \
    --tickers NVDA \
    --start 2025-08-01 \
    --end 2025-10-10 \
    --frequency W \
    --max-runs 10 \
    --analysts market,news,fundamentals \
    --debate-rounds 1 \
    --provider anthropic \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --config-override uw_momentum_filter_threshold=-5.0 \
    --out "experiments/2026-05-04-001-nvda-q3-2025-micro/results.csv" \
    --yes
