# Bear-side (UW + Sell) α per ticker — Q4 diagnostic

_Generated 2026-05-03T19:58:39.365842_

Convention: bear-side ratings (Underweight/Sell) directionally CORRECT when α<0. `wrong_rate` = % of calls with α>0 (the wrong direction).

Question: is anti-calibration uniform across tickers or concentrated on bull-regime tickers?



## 5-day horizon

| Ticker | n | mean α | wrong_rate | interpretation |
|---|---|---|---|---|
| MSFT | 5 | +0.25% | 60% | anti-calibrated (wrong dir) |
| AAPL | 18 | +0.45% | 61% | anti-calibrated (wrong dir) |
| NVDA | 5 | +1.80% | 80% | anti-calibrated (wrong dir) |
| INTC | 6 | +2.13% | 50% | anti-calibrated (wrong dir) |
| **CROSS-TICKER** | **34** | **+0.92%** | **62%** | **anti-calibrated** |

## 21-day horizon

| Ticker | n | mean α | wrong_rate | interpretation |
|---|---|---|---|---|
| AAPL | 15 | -0.44% | 40% | directionally correct |
| MSFT | 5 | +2.03% | 80% | anti-calibrated (wrong dir) |
| NVDA | 4 | +6.35% | 100% | anti-calibrated (wrong dir) |
| INTC | 5 | +7.11% | 40% | anti-calibrated (wrong dir) |
| **CROSS-TICKER** | **29** | **+2.23%** | **55%** | **anti-calibrated** |

## Per-(ticker, date) detail at 21d

| Ticker | Date | Rating | 21d α | Experiments |
|---|---|---|---|---|
| AAPL | 2025-11-21 | Underweight | -4.07% | 2026-05-03-008-opus47-cross-period |
| AAPL | 2026-01-30 | Underweight | +3.33% | 2026-05-02-005-wc12-cross-aapl, 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-02-06 | Underweight | -4.27% | 2026-05-03-002-exa-news-smoke-aapl |
| AAPL | 2026-02-13 | Underweight | +1.00% | 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-02-20 | Underweight | -0.01% | 2026-05-02-005-wc12-cross-aapl |
| AAPL | 2026-02-27 | Underweight | +1.23% | 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-03-06 | Underweight | +0.42% | 2026-05-03-001-brave-news-smoke-aapl, 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-03-13 | Sell | -1.38% | 2026-05-02-005-wc12-cross-aapl |
| AAPL | 2026-03-13 | Underweight | -1.38% | 2026-05-03-001-brave-news-smoke-aapl, 2026-05-03-002-exa-news-smoke-aapl, 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-03-20 | Underweight | -1.23% | 2026-05-03-002-exa-news-smoke-aapl, 2026-05-03-004-single-call-baseline-aapl |
| INTC | 2026-02-06 | Underweight | -5.59% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-02-13 | Underweight | -4.23% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-02-20 | Underweight | +4.71% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-02-27 | Underweight | -1.82% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-03-20 | Underweight | +42.48% | 2026-05-03-007-opus47-30pair-mixed |
| MSFT | 2026-02-06 | Underweight | +3.10% | 2026-05-02-006-wc12-cross-msft |
| MSFT | 2026-02-20 | Underweight | +1.36% | 2026-05-02-006-wc12-cross-msft |
| MSFT | 2026-03-13 | Underweight | -5.47% | 2026-05-02-006-wc12-cross-msft |
| MSFT | 2026-03-27 | Underweight | +8.08% | 2026-05-02-006-wc12-cross-msft |
| NVDA | 2026-02-27 | Underweight | +1.09% | 2026-05-03-003-single-call-baseline-nvda |
| NVDA | 2026-03-06 | Underweight | +2.11% | 2026-05-03-003-single-call-baseline-nvda |
| NVDA | 2026-03-20 | Underweight | +7.18% | 2026-05-03-003-single-call-baseline-nvda |
| NVDA | 2026-03-27 | Underweight | +15.01% | 2026-05-03-003-single-call-baseline-nvda |

## Headline


**Mixed**: 1 ticker(s) (AAPL) have correctly-bearish UW; 3 ticker(s) (MSFT, NVDA, INTC) anti-calibrated. Supports REGIME-SPECIFIC hypothesis — bear-side wrongness concentrates on tickers that subsequently rallied.
