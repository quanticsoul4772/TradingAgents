#!/usr/bin/env bash
# Q3 — Opus 4.7 swap on NVDA × same 10 dates as all prior NVDA experiments.
# Tests whether the framework's 21d bull-side lift (+1.59% OW α at n=30 across
# experiments) is Sonnet-specific or generalizes to a stronger model.
# Bull-side calls are noisy at 5d in pilot/Brave/MR-3 baselines; the 21d signal
# only appears post-hoc via horizon_sweep. Re-running with Opus tests if the
# pattern survives the model swap.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers NVDA \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --experiment-id "2026-05-03-005-opus47-swap-nvda" \
    --out "experiments/2026-05-03-005-opus47-swap-nvda/results.csv" \
    --yes
