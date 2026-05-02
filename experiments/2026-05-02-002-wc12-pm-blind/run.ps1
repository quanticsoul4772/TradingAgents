#!/usr/bin/env pwsh
# Repro command for experiment 2026-05-02-002-wc12-pm-blind
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
$ErrorActionPreference = 'Stop'
python scripts/backtest.py `
    --experiment-id "2026-05-02-002-wc12-pm-blind" `
    --out "experiments/2026-05-02-002-wc12-pm-blind/results.csv" `
    --yes
