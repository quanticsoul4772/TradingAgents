#!/usr/bin/env bash
# Exa news on AAPL — third news vendor on the same 10-date AAPL grid as:
#   - pilot baseline (yfinance news)
#   - brave-news-smoke-aapl (Brave; flagged time-leak in HYPOTHESIS.md:46)
# Exa's startPublishedDate / endPublishedDate constrain ranking, not just
# post-hoc filter — closes the time-leak caveat that left "news quality is
# the bottleneck" only partially ruled out.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --tickers AAPL \
    --start 2026-01-30 \
    --end 2026-04-03 \
    --frequency W \
    --news-vendor exa \
    --experiment-id "2026-05-03-002-exa-news-smoke-aapl" \
    --out "experiments/2026-05-03-002-exa-news-smoke-aapl/results.csv" \
    --yes
