#!/usr/bin/env pwsh
# Repro command for experiment 2026-05-04-001-nvda-q3-2025-micro
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
# `uv run` resolves to the project's .venv; bare `python` may resolve to
# the system interpreter, which doesn't have typer/anthropic/etc. installed.
$ErrorActionPreference = 'Stop'
uv run --no-sync python scripts/backtest.py `
    --experiment-id "2026-05-04-001-nvda-q3-2025-micro" `
    --out "experiments/2026-05-04-001-nvda-q3-2025-micro/results.csv" `
    --yes
