#!/usr/bin/env bash
# Repro: 10 NVDA dates, MR-3 v2 synthesis prompt + schema (matched to
# WC-12's date set so we can compare distributions: pilot vs WC-12 vs MR-3).
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers NVDA \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --experiment-id "2026-05-02-004-mr3-synthesis-v2" \
    --out "experiments/2026-05-02-004-mr3-synthesis-v2/results.csv" \
    --config-override research_manager_prompt_variant=v2 \
    --yes
