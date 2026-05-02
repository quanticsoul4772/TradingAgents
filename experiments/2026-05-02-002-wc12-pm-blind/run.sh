#!/usr/bin/env bash
# Repro command for experiment 2026-05-02-002-wc12-pm-blind
# 10 NVDA weekly Fridays (2026-01-30 → 2026-04-03) with synthesis withheld
# from the Portfolio Manager (pm_sees_synthesis=false). Compare resulting
# ratings to the pilot data for the same dates (pilot_results.csv on disk).
set -euo pipefail
# `uv run` resolves to the project's .venv (same fix as the pre-commit
# pytest hook). Bare `python` may resolve to the system interpreter,
# which doesn't have typer/anthropic/etc. installed.
uv run --no-sync python scripts/backtest.py \
    --tickers NVDA \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --experiment-id "2026-05-02-002-wc12-pm-blind" \
    --out "experiments/2026-05-02-002-wc12-pm-blind/results.csv" \
    --config-override pm_sees_synthesis=false \
    --yes
