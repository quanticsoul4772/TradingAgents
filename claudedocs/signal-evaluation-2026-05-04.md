# Signal Evaluation Report — multi-horizon (spec 002 Phase 1 + 1.5)

_Generated 2026-05-04T23:08:07+00:00._

> ⚠️ **Superseded by `claudedocs/signal-evaluation-2026-05-05-buffer-fix.md`** (2026-05-05). The "90d horizon" column in this report was actually computed over ~50 trading days due to a `fetch_returns` buffer bug (`holding_days+7` calendar-day window only fits ~50 trading days at the 90d setting). Fixed in commit pending; rerun report at true 90 trading days has the correct numbers. Top-4 IC patterns + signs are robust to the fix; magnitudes shifted by <0.03. See `claudedocs/buffer-fix-comparison-2026-05-05.md` for the delta analysis.

Horizons: **5d, 10d, 21d, 90d**. Total cached rows analyzed: **749**. Signals: **14**.

## Per-signal IC across horizons (Phase 1: numeric signals)

| Signal | n cached | Tickers | Dates | n eval | IC@5d | IC@10d | IC@21d | IC@90d | HR@90d |
|---|---:|---:|---:|---:| ---: | ---: | ---: | ---: | ---:|
| `final_trade_decision` | 156 | 10 | 33 | 153 | -0.073 | -0.112 | -0.172 | -0.238 | 70.6% |
| `investment_plan` | 156 | 10 | 33 | 0 | — | — | — | — | — |
| `market_report` | 156 | 10 | 33 | 0 | — | — | — | — | — |
| `news_report` | 156 | 10 | 33 | 0 | — | — | — | — | — |
| `fundamentals_report` | 116 | 7 | 33 | 0 | — | — | — | — | — |
| `get_balance_sheet` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_cashflow` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_fundamentals` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_global_news` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_income_statement` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_indicators` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_insider_transactions` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_news` | 1 | 1 | 1 | 0 | — | — | — | — | — |
| `get_stock_data` | 1 | 1 | 1 | 0 | — | — | — | — | — |

## Per-(signal, feature) IC across horizons (Phase 1.5: prose signals)

Sorted by max |IC| across horizons descending — strongest horizon-stable correlations first.

| Signal | Feature | n eval | IC@5d | IC@10d | IC@21d | IC@90d | HR@90d |
|---|---|---:| ---: | ---: | ---: | ---: | ---:|
| `fundamentals_report` | `bear_bigram_count` | 113 | +0.172 | +0.140 | +0.284 | +0.457 | 64.6% |
| `fundamentals_report` | `conviction_density` | 113 | -0.024 | -0.041 | -0.162 | -0.407 | 59.3% |
| `fundamentals_report` | `bull_keyword_count` | 113 | -0.081 | -0.117 | -0.132 | -0.306 | 59.3% |
| `fundamentals_report` | `hedge_density` | 113 | +0.157 | +0.113 | +0.154 | +0.305 | 59.3% |
| `fundamentals_report` | `bear_keyword_count` | 113 | +0.067 | +0.074 | +0.112 | +0.276 | 59.3% |
| `fundamentals_report` | `sentiment_score` | 113 | -0.056 | -0.060 | -0.095 | -0.266 | 42.5% |
| `fundamentals_report` | `bull_bear_keyword_ratio` | 113 | -0.056 | -0.060 | -0.095 | -0.266 | 59.3% |
| `fundamentals_report` | `negation_aware_sentiment_score` | 113 | -0.057 | -0.065 | -0.098 | -0.266 | 42.5% |
| `investment_plan` | `percent_mention_count` | 153 | -0.037 | -0.044 | -0.091 | -0.234 | 60.1% |
| `investment_plan` | `sentiment_score` | 153 | -0.143 | -0.213 | -0.079 | -0.129 | 52.3% |
| `investment_plan` | `bull_bear_keyword_ratio` | 153 | -0.143 | -0.213 | -0.079 | -0.129 | 60.1% |
| `investment_plan` | `negation_aware_sentiment_score` | 153 | -0.120 | -0.206 | -0.082 | -0.107 | 50.3% |
| `investment_plan` | `numeric_mention_count` | 153 | -0.098 | -0.077 | -0.126 | -0.204 | 60.1% |
| `investment_plan` | `bull_keyword_count` | 153 | -0.178 | -0.194 | -0.113 | -0.195 | 60.1% |
| `fundamentals_report` | `percent_mention_count` | 113 | -0.022 | -0.044 | -0.071 | -0.190 | 59.3% |
| `market_report` | `negation_aware_sentiment_score` | 153 | -0.037 | -0.168 | -0.185 | -0.049 | 45.8% |
| `market_report` | `sentiment_score` | 153 | -0.036 | -0.165 | -0.185 | -0.052 | 46.4% |
| `market_report` | `bull_bear_keyword_ratio` | 153 | -0.036 | -0.165 | -0.185 | -0.052 | 60.1% |
| `market_report` | `question_density` | 153 | +0.028 | +0.062 | +0.088 | +0.169 | 92.2% |
| `investment_plan` | `hedge_density` | 153 | -0.143 | -0.143 | -0.162 | -0.156 | 60.1% |
| `investment_plan` | `question_density` | 153 | +0.044 | +0.095 | +0.025 | +0.156 | 92.2% |
| `news_report` | `sentiment_score` | 153 | -0.084 | -0.156 | -0.076 | -0.105 | 49.0% |
| `news_report` | `bull_bear_keyword_ratio` | 153 | -0.084 | -0.156 | -0.076 | -0.105 | 60.1% |
| `market_report` | `bull_keyword_count` | 153 | -0.033 | -0.128 | -0.149 | -0.001 | 60.1% |
| `news_report` | `negation_aware_sentiment_score` | 153 | -0.081 | -0.148 | -0.068 | -0.103 | 49.7% |
| `news_report` | `bull_bigram_count` | 153 | -0.122 | -0.147 | -0.109 | +0.045 | 73.2% |
| `fundamentals_report` | `question_density` | 113 | +0.027 | +0.089 | +0.100 | +0.146 | 90.3% |
| `fundamentals_report` | `dollar_mention_count` | 113 | +0.054 | +0.074 | +0.058 | +0.146 | 59.3% |
| `news_report` | `conviction_density` | 153 | -0.112 | -0.144 | -0.083 | -0.139 | 60.1% |
| `market_report` | `bear_keyword_count` | 153 | +0.014 | +0.123 | +0.144 | +0.073 | 60.1% |
| `fundamentals_report` | `value_length` | 113 | +0.066 | +0.095 | +0.034 | +0.130 | 59.3% |
| `investment_plan` | `bear_keyword_count` | 153 | +0.017 | +0.126 | -0.002 | -0.014 | 60.1% |
| `investment_plan` | `conviction_density` | 153 | -0.092 | -0.120 | -0.046 | -0.124 | 60.8% |
| `news_report` | `bear_bigram_count` | 153 | +0.109 | +0.057 | +0.045 | +0.119 | 75.8% |
| `market_report` | `conviction_density` | 153 | +0.113 | +0.006 | -0.070 | -0.040 | 60.1% |
| `investment_plan` | `dollar_mention_count` | 153 | -0.104 | -0.084 | -0.113 | -0.019 | 60.8% |
| `news_report` | `percent_mention_count` | 153 | +0.042 | +0.073 | +0.055 | +0.100 | 74.5% |
| `news_report` | `bull_keyword_count` | 153 | +0.030 | -0.091 | -0.001 | -0.047 | 60.1% |
| `investment_plan` | `bear_bigram_count` | 153 | +0.049 | +0.048 | -0.087 | +0.090 | 75.8% |
| `news_report` | `hedge_density` | 153 | -0.055 | -0.085 | +0.041 | -0.028 | 60.1% |
| `market_report` | `percent_mention_count` | 153 | -0.024 | -0.078 | -0.084 | -0.071 | 60.1% |
| `fundamentals_report` | `bull_bigram_count` | 113 | -0.084 | -0.057 | +0.001 | -0.067 | 67.3% |
| `market_report` | `bear_bigram_count` | 153 | -0.003 | +0.045 | +0.082 | +0.076 | 84.3% |
| `investment_plan` | `value_length` | 153 | -0.080 | -0.006 | +0.017 | +0.047 | 60.1% |
| `market_report` | `hedge_density` | 153 | +0.073 | +0.036 | +0.007 | +0.079 | 60.1% |
| `market_report` | `numeric_mention_count` | 153 | +0.078 | +0.015 | -0.007 | +0.053 | 60.1% |
| `market_report` | `bull_bigram_count` | 153 | +0.068 | +0.008 | -0.058 | -0.078 | 80.4% |
| `market_report` | `dollar_mention_count` | 153 | +0.075 | +0.042 | +0.011 | -0.003 | 62.1% |
| `investment_plan` | `bull_bigram_count` | 153 | +0.057 | +0.016 | +0.035 | -0.007 | 77.8% |
| `news_report` | `bear_keyword_count` | 153 | +0.031 | +0.048 | +0.032 | +0.015 | 60.1% |
| `news_report` | `value_length` | 153 | +0.023 | +0.037 | +0.047 | +0.044 | 60.1% |
| `market_report` | `value_length` | 153 | +0.046 | -0.015 | -0.031 | +0.042 | 60.1% |
| `news_report` | `question_density` | 153 | +0.032 | +0.037 | +0.002 | -0.045 | 88.9% |
| `news_report` | `numeric_mention_count` | 153 | +0.016 | +0.038 | +0.016 | +0.021 | 69.3% |
| `fundamentals_report` | `numeric_mention_count` | 113 | +0.008 | +0.002 | +0.007 | -0.018 | 59.3% |
| `news_report` | `dollar_mention_count` | 153 | -0.010 | +0.011 | +0.011 | +0.015 | 70.6% |

## Notes

- **n eval** is the count of (ticker, date) pairs at the LAST horizon where both a numeric value AND a realized forward alpha are available. Earlier horizons typically have higher n eval (more dates have closed).
- **IC** = Spearman rank correlation between the signal/feature value and realized α at that horizon.
- Negative IC = the higher the signal value, the lower the realized α (anti-predictive).
- **HR** = directional hit rate at the longest horizon. Hold (signal sign 0) counts as hit when |α| < 0.5%.

## Source data

- Cache: `~/.tradingagents/signals/cache.db` (749 rows)
- Registry: `~/.tradingagents/signals/registry.jsonl` (23 signals)
