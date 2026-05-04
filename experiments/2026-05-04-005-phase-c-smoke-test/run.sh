#!/usr/bin/env bash
# Repro command for experiment 2026-05-04-005-phase-c-smoke-test
# Phase C end-to-end smoke test: single NVDA propagation with
# second_opinion_enabled=true. Validates the shipped Phase C module
# produces a real annotated decision against Anthropic Opus.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-04-005-phase-c-smoke-test" \
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
    --config-override second_opinion_enabled=true \
    --out "experiments/2026-05-04-005-phase-c-smoke-test/results.csv" \
    --yes
