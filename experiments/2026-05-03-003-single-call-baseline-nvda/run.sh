#!/usr/bin/env bash
# Single-call baseline on NVDA × 10 dates.
# Reads existing state logs at ~/.tradingagents/logs/NVDA/TradingAgentsStrategy_logs/
# (most recently populated by brave-news-smoke), extracts the 3 analyst reports,
# and feeds them in ONE Claude call to ask for a 5-tier rating.
# Compare to: pilot NVDA, WC-12 NVDA (002), MR-3 NVDA (004), brave-news-smoke NVDA (007).
set -euo pipefail
uv run --no-sync python scripts/single_call_baseline.py \
    --ticker NVDA \
    --dates 2026-01-30,2026-02-06,2026-02-13,2026-02-20,2026-02-27,2026-03-06,2026-03-13,2026-03-20,2026-03-27,2026-04-03 \
    --experiment-id "2026-05-03-003-single-call-baseline-nvda" \
    --out "experiments/2026-05-03-003-single-call-baseline-nvda/results.csv" \
    --yes
