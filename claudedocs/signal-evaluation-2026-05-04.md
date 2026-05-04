# Signal Evaluation Report (spec 002 Phase 1 + 1.5)

_Generated 2026-05-04T22:16:48+00:00._

Horizon: **21 days**. Total cached rows analyzed: **749**. Signals evaluated: **14**.

## Coverage + IC + Hit Rate per signal (Phase 1)

| Signal | n cached | Tickers | Dates | Mean value length | n eval | IC | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| `final_trade_decision` | 156 | 10 | 33 | 4587 | 153 | -0.172 | 70.6% |
| `investment_plan` | 156 | 10 | 33 | 5242 | 0 | — | — |
| `market_report` | 156 | 10 | 33 | 10824 | 0 | — | — |
| `news_report` | 156 | 10 | 33 | 10433 | 0 | — | — |
| `fundamentals_report` | 116 | 7 | 33 | 16643 | 0 | — | — |
| `get_balance_sheet` | 1 | 1 | 1 | 5913 | 0 | — | — |
| `get_cashflow` | 1 | 1 | 1 | 4049 | 0 | — | — |
| `get_fundamentals` | 1 | 1 | 1 | 711 | 0 | — | — |
| `get_global_news` | 1 | 1 | 1 | 17016 | 0 | — | — |
| `get_income_statement` | 1 | 1 | 1 | 3054 | 0 | — | — |
| `get_indicators` | 1 | 1 | 1 | 1470 | 0 | — | — |
| `get_insider_transactions` | 1 | 1 | 1 | 15592 | 0 | — | — |
| `get_news` | 1 | 1 | 1 | 34949 | 0 | — | — |
| `get_stock_data` | 1 | 1 | 1 | 3049 | 0 | — | — |

## Per-feature IC for prose signals (Phase 1.5)

Each prose signal is featurized via 7 feature extractors. Below: IC + hit rate per (signal, feature) pair, sorted by |IC| desc to surface the strongest correlations first.

| Signal | Feature | n eval | IC | Hit rate |
|---|---|---:|---:|---:|
| `market_report` | `sentiment_score` | 153 | -0.185 | 40.5% |
| `fundamentals_report` | `conviction_density` | 113 | -0.162 | 56.6% |
| `investment_plan` | `hedge_density` | 153 | -0.162 | 56.9% |
| `fundamentals_report` | `hedge_density` | 113 | +0.154 | 55.8% |
| `market_report` | `bull_keyword_count` | 153 | -0.149 | 56.9% |
| `market_report` | `bear_keyword_count` | 153 | +0.144 | 56.9% |
| `fundamentals_report` | `bull_keyword_count` | 113 | -0.132 | 55.8% |
| `investment_plan` | `numeric_mention_count` | 153 | -0.126 | 56.9% |
| `investment_plan` | `bull_keyword_count` | 153 | -0.113 | 56.9% |
| `fundamentals_report` | `bear_keyword_count` | 113 | +0.112 | 55.8% |
| `fundamentals_report` | `sentiment_score` | 113 | -0.095 | 47.8% |
| `news_report` | `conviction_density` | 153 | -0.083 | 56.9% |
| `investment_plan` | `sentiment_score` | 153 | -0.079 | 56.2% |
| `news_report` | `sentiment_score` | 153 | -0.076 | 49.0% |
| `market_report` | `conviction_density` | 153 | -0.070 | 56.9% |
| `news_report` | `value_length` | 153 | +0.047 | 56.9% |
| `investment_plan` | `conviction_density` | 153 | -0.046 | 57.5% |
| `news_report` | `hedge_density` | 153 | +0.041 | 56.9% |
| `fundamentals_report` | `value_length` | 113 | +0.034 | 55.8% |
| `news_report` | `bear_keyword_count` | 153 | +0.032 | 56.9% |
| `market_report` | `value_length` | 153 | -0.031 | 56.9% |
| `investment_plan` | `value_length` | 153 | +0.017 | 56.9% |
| `news_report` | `numeric_mention_count` | 153 | +0.016 | 65.4% |
| `market_report` | `hedge_density` | 153 | +0.007 | 56.9% |
| `fundamentals_report` | `numeric_mention_count` | 113 | +0.007 | 55.8% |
| `market_report` | `numeric_mention_count` | 153 | -0.007 | 56.9% |
| `investment_plan` | `bear_keyword_count` | 153 | -0.002 | 56.9% |
| `news_report` | `bull_keyword_count` | 153 | -0.001 | 56.9% |

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

- Cache: `~/.tradingagents/signals/cache.db` (749 rows)
- Registry: `~/.tradingagents/signals/registry.jsonl` (23 signals)
