#!/usr/bin/env bash
# Pre-flight before 30-pair Opus re-pilot. Same script + flags as 005, ticker
# swap NVDA → AAPL. Tests whether the 005 result (10/10 Overweight; 21d OW
# α=+2.85% n=9 78% hit) generalizes from a bull-regime ticker to AAPL (the
# bear-correct ticker per Q4 per-ticker breakdown — UW @ 21d α=-0.18% on AAPL,
# +6.35% on NVDA).
#
# Decision criterion: if Opus AAPL also shows OW commits AND positive 21d α,
# the bull-side signal is multi-regime and the 30-pair Opus re-pilot at scale
# is well-grounded. If Opus AAPL flips to UW or shows negative 21d α, the
# 005 result was bull-regime-specific and the 30-pair plan needs revision.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers AAPL \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --experiment-id "2026-05-03-006-opus47-swap-aapl" \
    --out "experiments/2026-05-03-006-opus47-swap-aapl/results.csv" \
    --yes
