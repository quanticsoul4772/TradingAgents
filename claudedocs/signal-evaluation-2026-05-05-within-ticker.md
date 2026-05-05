# Signal Evaluation Report — multi-horizon (spec 002 Phase 1 + 1.5)

_Generated 2026-05-05T04:29:23+00:00._

Horizons: **5d, 10d, 21d, 90d**. Total cached rows analyzed: **749**. Signals: **14**.

## Per-signal IC across horizons (Phase 1: numeric signals)

| Signal | n cached | Tickers | Dates | n eval | IC@5d | IC@10d | IC@21d | IC@90d | Within-IC@90d | HR@90d |
|---|---:|---:|---:|---:| ---: | ---: | ---: | ---: | ---: | ---:|
| `final_trade_decision` | 156 | 10 | 33 | 153 | -0.073 | -0.095 | -0.103 | -0.254 | -0.311 (9t: 2+/7−) | 65.4% |
| `investment_plan` | 156 | 10 | 33 | 0 | — | — | — | — | — | — |
| `market_report` | 156 | 10 | 33 | 0 | — | — | — | — | — | — |
| `news_report` | 156 | 10 | 33 | 0 | — | — | — | — | — | — |
| `fundamentals_report` | 116 | 7 | 33 | 0 | — | — | — | — | — | — |
| `get_balance_sheet` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_cashflow` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_fundamentals` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_global_news` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_income_statement` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_indicators` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_insider_transactions` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_news` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |
| `get_stock_data` | 1 | 1 | 1 | 0 | — | — | — | — | — | — |

## Per-(signal, feature) IC across horizons (Phase 1.5: prose signals)

Sorted by max |IC| across horizons descending — strongest horizon-stable correlations first.

| Signal | Feature | n eval | IC@5d | IC@10d | IC@21d | IC@90d | Within-IC@90d | HR@90d |
|---|---|---:| ---: | ---: | ---: | ---: | ---: | ---:|
| `fundamentals_report` | `bear_bigram_count` | 113 | +0.172 | +0.117 | +0.265 | +0.478 | +0.097 (6t: 5+/1−) | 61.1% |
| `fundamentals_report` | `conviction_density` | 113 | -0.024 | -0.047 | -0.162 | -0.404 | +0.017 ⚠️ (6t: 3+/3−) | 54.9% |
| `fundamentals_report` | `hedge_density` | 113 | +0.157 | +0.078 | +0.097 | +0.318 | -0.010 ⚠️ (6t: 3+/3−) | 55.8% |
| `fundamentals_report` | `bull_keyword_count` | 113 | -0.081 | -0.075 | -0.127 | -0.302 | -0.007 (6t: 3+/3−) | 55.8% |
| `fundamentals_report` | `bear_keyword_count` | 113 | +0.067 | +0.038 | +0.019 | +0.282 | -0.014 ⚠️ (6t: 3+/3−) | 55.8% |
| `fundamentals_report` | `sentiment_score` | 113 | -0.056 | -0.015 | -0.017 | -0.279 | +0.166 ⚠️ (6t: 4+/1−) | 38.9% |
| `fundamentals_report` | `bull_bear_keyword_ratio` | 113 | -0.056 | -0.015 | -0.017 | -0.279 | +0.166 ⚠️ (6t: 4+/1−) | 55.8% |
| `fundamentals_report` | `negation_aware_sentiment_score` | 113 | -0.057 | -0.020 | -0.020 | -0.278 | +0.167 ⚠️ (6t: 5+/1−) | 38.9% |
| `investment_plan` | `percent_mention_count` | 153 | -0.037 | -0.042 | -0.100 | -0.269 | -0.290 (9t: 3+/6−) | 57.5% |
| `investment_plan` | `sentiment_score` | 153 | -0.143 | -0.207 | -0.049 | -0.131 | -0.252 (9t: 2+/7−) | 52.3% |
| `investment_plan` | `bull_bear_keyword_ratio` | 153 | -0.143 | -0.207 | -0.049 | -0.131 | -0.252 (9t: 2+/7−) | 57.5% |
| `investment_plan` | `bull_keyword_count` | 153 | -0.178 | -0.206 | -0.056 | -0.199 | -0.295 (9t: 1+/8−) | 57.5% |
| `investment_plan` | `numeric_mention_count` | 153 | -0.098 | -0.076 | -0.116 | -0.204 | -0.135 (9t: 3+/6−) | 57.5% |
| `investment_plan` | `negation_aware_sentiment_score` | 153 | -0.120 | -0.197 | -0.054 | -0.115 | -0.267 (9t: 2+/7−) | 50.3% |
| `fundamentals_report` | `percent_mention_count` | 113 | -0.022 | -0.015 | -0.076 | -0.193 | +0.010 ⚠️ (6t: 3+/3−) | 55.8% |
| `market_report` | `sentiment_score` | 153 | -0.036 | -0.168 | -0.180 | -0.069 | -0.378 (9t: 0+/9−) | 46.4% |
| `market_report` | `bull_bear_keyword_ratio` | 153 | -0.036 | -0.168 | -0.180 | -0.069 | -0.378 (9t: 0+/9−) | 57.5% |
| `market_report` | `negation_aware_sentiment_score` | 153 | -0.037 | -0.169 | -0.179 | -0.066 | -0.370 (9t: 0+/9−) | 45.8% |
| `news_report` | `sentiment_score` | 153 | -0.084 | -0.175 | -0.049 | -0.088 | -0.112 (9t: 3+/6−) | 49.0% |
| `news_report` | `bull_bear_keyword_ratio` | 153 | -0.084 | -0.175 | -0.049 | -0.088 | -0.112 (9t: 3+/6−) | 57.5% |
| `market_report` | `question_density` | 153 | +0.028 | +0.074 | +0.072 | +0.174 | -0.027 ⚠️ (4t: 1+/3−) | 88.9% |
| `news_report` | `negation_aware_sentiment_score` | 153 | -0.081 | -0.167 | -0.041 | -0.083 | -0.187 (9t: 3+/6−) | 49.7% |
| `investment_plan` | `hedge_density` | 153 | -0.143 | -0.116 | -0.154 | -0.145 | -0.189 (9t: 2+/7−) | 57.5% |
| `fundamentals_report` | `question_density` | 113 | +0.027 | +0.086 | -0.004 | +0.152 | +0.081 (4t: 3+/1−) | 85.8% |
| `investment_plan` | `question_density` | 153 | +0.044 | +0.064 | +0.028 | +0.149 | +0.106 (6t: 5+/1−) | 88.2% |
| `market_report` | `bull_keyword_count` | 153 | -0.033 | -0.128 | -0.144 | -0.011 | -0.489 (9t: 0+/9−) | 57.5% |
| `news_report` | `bull_bigram_count` | 153 | -0.122 | -0.140 | -0.119 | +0.051 | -0.269 ⚠️ (9t: 2+/7−) | 71.2% |
| `market_report` | `bear_keyword_count` | 153 | +0.014 | +0.129 | +0.138 | +0.092 | +0.288 (9t: 8+/1−) | 57.5% |
| `fundamentals_report` | `dollar_mention_count` | 113 | +0.054 | +0.047 | -0.034 | +0.133 | +0.009 (6t: 3+/3−) | 55.8% |
| `news_report` | `conviction_density` | 153 | -0.112 | -0.128 | -0.054 | -0.122 | -0.133 (9t: 3+/6−) | 57.5% |
| `investment_plan` | `conviction_density` | 153 | -0.092 | -0.127 | -0.038 | -0.114 | -0.113 (9t: 3+/6−) | 58.2% |
| `fundamentals_report` | `value_length` | 113 | +0.066 | +0.109 | -0.038 | +0.124 | +0.015 (6t: 3+/3−) | 55.8% |
| `investment_plan` | `bear_bigram_count` | 153 | +0.049 | +0.034 | -0.117 | +0.046 | -0.262 ⚠️ (9t: 2+/7−) | 70.6% |
| `market_report` | `bear_bigram_count` | 153 | -0.003 | +0.061 | +0.117 | +0.089 | +0.123 (9t: 7+/2−) | 82.4% |
| `market_report` | `conviction_density` | 153 | +0.113 | +0.008 | -0.070 | -0.069 | -0.175 (9t: 2+/7−) | 57.5% |
| `news_report` | `bear_bigram_count` | 153 | +0.109 | +0.070 | +0.030 | +0.113 | +0.066 (9t: 5+/3−) | 73.2% |
| `investment_plan` | `dollar_mention_count` | 153 | -0.104 | -0.070 | -0.098 | +0.015 | -0.074 ⚠️ (9t: 3+/6−) | 58.2% |
| `market_report` | `percent_mention_count` | 153 | -0.024 | -0.103 | -0.051 | -0.059 | -0.264 (9t: 2+/7−) | 57.5% |
| `investment_plan` | `bear_keyword_count` | 153 | +0.017 | +0.095 | +0.022 | -0.014 | +0.067 ⚠️ (9t: 5+/4−) | 57.5% |
| `news_report` | `percent_mention_count` | 153 | +0.042 | +0.095 | -0.004 | +0.088 | -0.038 ⚠️ (8t: 2+/5−) | 71.9% |
| `news_report` | `bull_keyword_count` | 153 | +0.030 | -0.089 | -0.033 | -0.059 | -0.017 (9t: 4+/5−) | 57.5% |
| `fundamentals_report` | `bull_bigram_count` | 113 | -0.084 | -0.015 | -0.022 | -0.079 | +0.021 ⚠️ (6t: 4+/2−) | 60.2% |
| `investment_plan` | `value_length` | 153 | -0.080 | -0.041 | +0.028 | +0.061 | -0.043 ⚠️ (9t: 3+/6−) | 57.5% |
| `market_report` | `numeric_mention_count` | 153 | +0.078 | -0.015 | +0.009 | +0.061 | -0.172 ⚠️ (9t: 1+/8−) | 57.5% |
| `market_report` | `dollar_mention_count` | 153 | +0.075 | +0.023 | -0.021 | +0.002 | -0.129 ⚠️ (9t: 2+/7−) | 60.1% |
| `news_report` | `hedge_density` | 153 | -0.055 | -0.074 | +0.038 | -0.018 | +0.104 ⚠️ (9t: 5+/4−) | 57.5% |
| `market_report` | `hedge_density` | 153 | +0.073 | +0.066 | -0.011 | +0.064 | +0.207 (9t: 7+/2−) | 57.5% |
| `news_report` | `bear_keyword_count` | 153 | +0.031 | +0.068 | +0.002 | -0.002 | +0.014 ⚠️ (9t: 5+/4−) | 57.5% |
| `market_report` | `bull_bigram_count` | 153 | +0.068 | -0.006 | -0.036 | -0.050 | -0.067 (9t: 3+/6−) | 78.4% |
| `fundamentals_report` | `numeric_mention_count` | 113 | +0.008 | +0.010 | -0.059 | -0.031 | -0.024 (6t: 3+/3−) | 55.8% |
| `investment_plan` | `bull_bigram_count` | 153 | +0.057 | +0.012 | +0.039 | +0.012 | +0.070 (9t: 6+/3−) | 73.9% |
| `news_report` | `numeric_mention_count` | 153 | +0.016 | +0.052 | -0.047 | -0.004 | -0.098 (8t: 3+/5−) | 66.7% |
| `market_report` | `value_length` | 153 | +0.046 | -0.028 | -0.014 | +0.049 | -0.249 ⚠️ (9t: 2+/7−) | 57.5% |
| `news_report` | `question_density` | 153 | +0.032 | +0.014 | -0.044 | -0.038 | -0.152 (8t: 2+/6−) | 85.6% |
| `news_report` | `dollar_mention_count` | 153 | -0.010 | +0.017 | -0.038 | -0.007 | -0.176 (7t: 3+/4−) | 68.0% |
| `news_report` | `value_length` | 153 | +0.023 | +0.032 | -0.008 | +0.037 | -0.005 ⚠️ (9t: 4+/5−) | 57.5% |

## Notes

- **n eval** is the count of (ticker, date) pairs at the LAST horizon where both a numeric value AND a realized forward alpha are available. Earlier horizons typically have higher n eval (more dates have closed).
- **IC** = Spearman rank correlation between the signal/feature value and realized α at that horizon, computed across ALL (ticker, date) pairs.
- **Within-IC@<longest>** = MEDIAN of per-ticker ICs at the longest horizon. Per-ticker IC is computed only for tickers with n ≥ 5 obs. The trailing `(Nt: P+/Q−)` reads as: N tickers evaluated, P with positive IC, Q with negative IC. **A ⚠️ flag fires when the aggregate IC sign disagrees with the within-ticker median sign — that's a Simpson's-paradox / between-ticker artifact** (the aggregate is driven by ticker-class identification, not within-ticker prediction). See `claudedocs/featurizer-artifact-check-2026-05-04.md` for the methodology this surfaces. Without this column, between-ticker artifacts look like real predictive signal in the aggregate IC table.
- Negative IC = the higher the signal value, the lower the realized α (anti-predictive).
- **HR** = directional hit rate at the longest horizon. Hold (signal sign 0) counts as hit when |α| < 0.5%.

## Source data

- Cache: `~/.tradingagents/signals/cache.db` (749 rows)
- Registry: `~/.tradingagents/signals/registry.jsonl` (23 signals)
