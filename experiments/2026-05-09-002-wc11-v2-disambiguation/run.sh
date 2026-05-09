#!/usr/bin/env bash
# Repro command for experiment 2026-05-09-002-wc11-v2-disambiguation
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
# `uv run` resolves to the project's .venv; bare `python` may resolve to
# the system interpreter, which doesn't have typer/anthropic/etc. installed.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-09-002-wc11-v2-disambiguation" \
    --out "experiments/2026-05-09-002-wc11-v2-disambiguation/results.csv" \
    --yes
