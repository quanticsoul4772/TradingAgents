#!/usr/bin/env bash
# Spec 002 paper-trading harness live-forward 5-day exercise.
# One pass = one trading day. Loop must be invoked once per business day.
#
# Daily command (run by cron OR manually each business day):
set -euo pipefail
EXP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORTFOLIO_ID="live-forward-2026-05-06"
DATE="${1:-$(date +%Y-%m-%d)}"
SIGNALS_CSV="$HOME/.tradingagents/paper/signals-${DATE}.csv"

echo "=== Paper-harness live-forward day: ${DATE} ==="
echo "Step 1: generate signals"
uv run --no-sync python scripts/daily_signals.py \
    --tickers "${EXP_DIR}/watchlist.txt" \
    --date "${DATE}" \
    --emit-csv "${SIGNALS_CSV}"

echo "Step 2: update paper portfolio"
uv run --no-sync python scripts/paper_trade.py step \
    --signals-csv "${SIGNALS_CSV}" \
    --date "${DATE}" \
    --portfolio-id "${PORTFOLIO_ID}"

echo "Day ${DATE} complete."
