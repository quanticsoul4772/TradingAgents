#!/usr/bin/env bash
# Repro command for experiment 2026-05-02-001-mr1-contradiction
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
set -euo pipefail
python scripts/backtest.py \
    --experiment-id "2026-05-02-001-mr1-contradiction" \
    --out "experiments/2026-05-02-001-mr1-contradiction/results.csv" \
    --yes
