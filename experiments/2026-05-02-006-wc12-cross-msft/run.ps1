#!/usr/bin/env pwsh
# Repro command for experiment 2026-05-02-006-wc12-cross-msft
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
# `uv run` resolves to the project's .venv; bare `python` may resolve to
# the system interpreter, which doesn't have typer/anthropic/etc. installed.
$ErrorActionPreference = 'Stop'
uv run --no-sync python scripts/backtest.py `
    --experiment-id "2026-05-02-006-wc12-cross-msft" `
    --out "experiments/2026-05-02-006-wc12-cross-msft/results.csv" `
    --yes
