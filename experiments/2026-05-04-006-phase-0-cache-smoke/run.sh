#!/usr/bin/env bash
# Repro command for experiment 2026-05-04-006-phase-0-cache-smoke
# Spec 002 Phase 0 end-to-end smoke test: single NVDA propagation to
# verify the new signal cache populates from real route_to_vendor calls.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-04-006-phase-0-cache-smoke" \
    --tickers NVDA \
    --start 2026-01-30 \
    --end 2026-01-30 \
    --frequency W \
    --max-runs 1 \
    --analysts market,news,fundamentals \
    --debate-rounds 1 \
    --provider anthropic \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --out "experiments/2026-05-04-006-phase-0-cache-smoke/results.csv" \
    --yes
