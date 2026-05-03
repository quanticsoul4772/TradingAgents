#!/usr/bin/env bash
# Single-call baseline on AAPL × 10 dates (replication of NVDA result).
# Reads existing AAPL state logs (most recently from exa-news-smoke-aapl, 002),
# extracts the 3 analyst reports, feeds them to ONE Claude call with the same
# 5-tier scale. Tests robustness of the "framework Hold-collapse is honest
# abstention, single-call manufactures wrong conviction" thesis on a different
# ticker with a known bear lean (per WC-12 cross-AAPL).
set -euo pipefail
uv run --no-sync python scripts/single_call_baseline.py \
    --ticker AAPL \
    --dates 2026-01-30,2026-02-06,2026-02-13,2026-02-20,2026-02-27,2026-03-06,2026-03-13,2026-03-20,2026-03-27,2026-04-03 \
    --experiment-id "2026-05-03-004-single-call-baseline-aapl" \
    --out "experiments/2026-05-03-004-single-call-baseline-aapl/results.csv" \
    --yes
