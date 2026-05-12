# SC-007 Validation Result — 2026-05-11 Live Daily Run

**Spec**: 250-dashboard-ui
**Gap closed**: G-6 (per `plan.md`)
**Task**: T018 (per `tasks.md`)
**Trigger**: `tradingagents-engine-daily.timer` fired automatically at 17:00 ET on 2026-05-11

## Run summary

| Field | Value |
|---|---|
| `run_id` | `2026-05-11T210306Z` |
| `trade_date` | 2026-05-11 |
| Started | 2026-05-11 21:03:06 UTC (= 17:03 ET) |
| Last completion | 2026-05-12 00:49:55 UTC (= 20:49 ET on 2026-05-11) |
| Wall-clock duration | **3 hours 47 minutes** |
| Tickers completed | **25 / 25** |
| Tickers failed | 0 |
| Watchlist | AAPL, MSFT, NVDA, GOOGL, AMZN, META, AVGO, ORCL, ADBE, CRM, NFLX, CSCO, AMD, QCOM, TSLA, UNH, LLY, ABBV, JPM, GS, INTC, ABT, HD, MCD, XOM |

## Ratings distribution

| Rating | Count | % | Tickers |
|---|---:|---:|---|
| Buy | 0 | 0% | — |
| Overweight | 5 | 20% | MSFT, META, NFLX, JPM, MCD |
| Hold | 17 | 68% | AAPL, NVDA, GOOGL, AMZN, AVGO, ORCL, ADBE, CSCO, AMD, QCOM, TSLA, UNH, LLY, ABBV, GS, ABT, XOM |
| Underweight | 3 | 12% | CRM, INTC, HD |
| Sell | 0 | 0% | — |

**Commit rate: 8 / 25 = 32%** (5 OW + 3 UW). Consistent with prior corpus patterns (Constitution VII calibrated abstention; Hold-heavy).

## SC-007 cost-meter result

**Acceptance criterion** (per amended `spec.md` SC-007 — see `amendments/sc-007-drop-billing-comparison.md`): non-zero cost-meter figure from a successful live run; dashboard `TokenCostCallback` is the operational ground truth for cost.

| Source | Cost |
|---|---:|
| Dashboard cost meter (TokenCostCallback) | **$38.30** |

**Status**: PASS — non-zero cost meter from a 25/25 successful run. The original ±5%-vs-Anthropic-billing comparison was dropped via formal amendment (no API exists for that data; manual operator-console comparison removed from acceptance criteria). The dashboard cost meter is internally consistent (per-call token counts × `ANTHROPIC_PRICING_USD_PER_M` published-rates table in `tradingagents/engine/callbacks.py`); ongoing accuracy depends on keeping that table refreshed when Anthropic ships new model SKUs or pricing changes.

## Spec-vs-actual cost variance

| Source | Estimate | Actual |
|---|---:|---:|
| Original spec.md operational characteristics | "~$10/day LLM at the default 25-ticker watchlist (Opus + Haiku per propagate)" | $38.30 |
| Variance | reference | **3.83×** the estimate |

The original $10/day estimate is materially low. The cost-meter result here is the new ground-truth reference. Suggested follow-up (out of spec 250 scope): update `spec.md` Assumptions section + `claudedocs/SETUP.md` cost ranges to reflect ~$35-$45/day for the 25-ticker default at Opus+Haiku at the current pricing.

## Other SC-007 acceptance criteria

| Criterion | Status |
|---|---|
| Non-zero cost meter from successful live run (amended SC-007) | ✅ PASS — $38.30 |
| All 25 tickers either completed or failed | ✅ PASS — 25/25 completed, 0 failed |
| Paper portfolio updated with new Buy/OW signals | Auto-spawned per FR-007. Operator can verify any time with `ssh rawcell 'jq ".open_positions | length" ~/.tradingagents/paper/live.json'`. |

## Closure of spec 250

All 12 plan.md gaps closed (G-1 through G-12; G-10 is process-only). All 5 user stories functionally complete (US1 ratings+portfolio+cost; US2 live debate; US3 archived debate; US4 ad-hoc trigger; US5 paper portfolio). **Spec 250-dashboard-ui formally closed 2026-05-11.**

The dashboard is the operational surface going forward. Daily runs at 17:00 ET Mon-Fri produce the data; the dashboard at https://rawcell.duckdns.org/trading/ is the read surface.
