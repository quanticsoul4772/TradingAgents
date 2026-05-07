#!/usr/bin/env pwsh
# Spec 008 SC-009 EXPANSION cohort — risk-mitigation against original 2026-05-07-001 all-Hold pattern
# 13 tickers x 2 Fridays (2026-04-10, 2026-04-24) = 26 propagates
# CONDITIONAL kick-off: only run after original 2026-05-07-001 confirms gate-2 risk
#   (≥30/36 rows return Hold AND n_fired_boost_on < 4 per analyzer output)
# Cost: ~$13 (T2). Wall-clock: ~4h compute + ~15 days for 21d forward window.
$ErrorActionPreference = 'Stop'

uv run --no-sync python scripts/backtest.py `
    --experiment-id "2026-05-07-002-sc-009-expansion" `
    --tickers "TSLA,BA,PARA,NIO,F,NFLX,META,COIN,PYPL,SNAP,LLY,INTC,COP" `
    --start "2026-04-08" `
    --end "2026-04-30" `
    --frequency "W" `
    --max-runs 30 `
    --deep-model "claude-sonnet-4-6" `
    --quick-model "claude-haiku-4-5" `
    --news-vendor "exa" `
    --config-override "hybrid_c_calendar_boost_enabled=true" `
    --config-override "hybrid_c_calendar_boost_window_days=14" `
    --config-override "hybrid_c_calendar_boost_magnitude=0.5" `
    --out "experiments/2026-05-07-002-sc-009-expansion/results.csv" `
    --yes
