#!/usr/bin/env bash
# Cross-ticker WC-12 validation: MSFT × 10 dates with synthesis withheld.
# Tests whether WC-12's NVDA-specific finding (5/10 Buy) generalizes.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers MSFT \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --experiment-id "2026-05-02-006-wc12-cross-msft" \
    --out "experiments/2026-05-02-006-wc12-cross-msft/results.csv" \
    --config-override pm_sees_synthesis=false \
    --yes
