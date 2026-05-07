#!/usr/bin/env pwsh
# Spec 008 SC-009 live A/B ablation — kick off run
# 18 tickers × 2 Fridays (2026-04-17, 2026-04-24) = 36 propagates
# Boost ENABLED; boost-OFF comparison is post-hoc from bull_case_priced_in scores
# Cost: ~$18 (T2). Wall-clock: ~30min compute + ~15 days for 21d forward window.
$ErrorActionPreference = 'Stop'

uv run --no-sync python scripts/backtest.py `
    --experiment-id "2026-05-07-001-spec-008-hybrid-c-ab-ablation" `
    --tickers "NVDA,MSFT,AAPL,WFC,MA,COP,INTC,GOOGL,AMD,AMZN,AVGO,BAC,CSCO,GS,JPM,LLY,CVX,HON" `
    --start "2026-04-15" `
    --end "2026-04-30" `
    --frequency "W" `
    --max-runs 40 `
    --deep-model "claude-sonnet-4-6" `
    --quick-model "claude-haiku-4-5" `
    --news-vendor "exa" `
    --config-override "hybrid_c_calendar_boost_enabled=true" `
    --config-override "hybrid_c_calendar_boost_window_days=14" `
    --config-override "hybrid_c_calendar_boost_magnitude=0.5" `
    --out "experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv" `
    --yes
