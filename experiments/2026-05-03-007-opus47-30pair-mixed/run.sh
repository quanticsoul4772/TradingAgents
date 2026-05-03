#!/usr/bin/env bash
# 30-pair Opus 4.7 re-pilot at 21d horizon, A3 momentum filter enabled.
# Mixed ticker basket per ROADMAP active branch:
#   NVDA — bull regime (per 005: 10/10 OW, 21d OW α=+2.85% n=9 78% hit)
#   AAPL — mixed regime (per 006: 8 Hold + 2 OW, 21d OW α=-0.07% n=2 50% hit)
#   INTC — bear-leaning semis (untested with Opus; expect mostly Hold or some UW
#          per the framework's bear-correct-ticker pattern from Q4)
# 10 dates × 3 tickers = 30 propagations, ~$30 (at Principle III ceiling),
# ~3.5h wall-clock.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers NVDA,AAPL,INTC \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --config-override uw_momentum_filter_threshold=-5.0 \
    --experiment-id "2026-05-03-007-opus47-30pair-mixed" \
    --out "experiments/2026-05-03-007-opus47-30pair-mixed/results.csv" \
    --yes
