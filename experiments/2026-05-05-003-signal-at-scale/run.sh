#!/usr/bin/env bash
# Spec product-build path step 1: signal at scale on 50-ticker batch
set -euo pipefail
uv run --no-sync python scripts/backtest.py \
    --experiment-id "2026-05-05-003-signal-at-scale" \
    --tickers "AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,AVGO,ORCL,ADBE,CRM,NFLX,CSCO,AMD,QCOM,JPM,BAC,WFC,GS,MS,V,MA,AXP,UNH,JNJ,LLY,PFE,MRK,ABBV,TMO,KO,PG,WMT,COST,HD,MCD,SBUX,NKE,GE,CAT,BA,HON,LMT,XOM,CVX,COP,T,VZ,INTC,ABT" \
    --start 2026-04-03 \
    --end 2026-04-03 \
    --frequency W \
    --max-runs 50 \
    --analysts market,news,fundamentals \
    --debate-rounds 1 \
    --provider anthropic \
    --deep-model claude-opus-4-7 \
    --quick-model claude-haiku-4-5 \
    --news-vendor exa \
    --config-override contrarian_gate_mode=shadow \
    --config-override uw_momentum_filter_threshold=-5.0 \
    --out experiments/2026-05-05-003-signal-at-scale/results.csv \
    --yes
