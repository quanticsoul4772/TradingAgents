# Signal Evaluation Report (spec 002 Phase 1)

_Generated 2026-05-04T21:30:47+00:00._

Horizon: **21 days**. Total cached rows analyzed: **156**. Signals evaluated: **1**.

## Coverage + IC + Hit Rate per signal

| Signal | n cached | Tickers | Dates | Mean value length | n eval | IC | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| `final_trade_decision` | 156 | 10 | 33 | 4587 | 153 | -0.172 | 70.6% |

## Notes

- **n eval** is the count of (ticker, date) pairs where both a numeric signal value AND a realized forward alpha are available. Smaller than n cached when the trade date is too recent for forward-return data.
- **IC** = Spearman rank correlation between signal numeric value and realized 21-day alpha. Only computable for signals whose values can be coerced to numbers. Phase 1 MVP supports only `final_trade_decision` (parsed 5-tier rating); prose signals report coverage stats only.
- **Hit rate** = fraction of pairs where signal direction (bullish / neutral / bearish) matches realized alpha sign. Hold counts as hit when |α| < 0.5%.

## What this report does NOT include (deferred to Phase 1.5+)

- Featurization of prose signals (would unlock IC for market_report, news_report, fundamentals_report, investment_plan, sentiment_report)
- Quintile gradient (top vs bottom quintile alpha spread)
- Info ratio (IC / std)
- Per-horizon comparison (5d / 10d / 21d)
- Cross-signal correlation matrix
- Auto-promote / auto-demote state transitions

## Source data

- Cache: `~/.tradingagents/signals/cache.db` (156 rows)
- Registry: `~/.tradingagents/signals/registry.jsonl` (23 signals)
