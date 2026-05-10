# Bear-side (UW + Sell) α per ticker — Q4 diagnostic

_Generated 2026-05-10T07:18:33.600621_

Convention: bear-side ratings (Underweight/Sell) directionally CORRECT when α<0. `wrong_rate` = % of calls with α>0 (the wrong direction).

Question: is anti-calibration uniform across tickers or concentrated on bull-regime tickers?



## 5-day horizon

| Ticker | n | mean α | wrong_rate | interpretation |
|---|---|---|---|---|
| CVX | 3 | -1.86% | 67% | directionally correct |
| HON | 1 | -1.74% | 0% | directionally correct |
| XLE | 6 | -1.05% | 67% | directionally correct |
| XLK | 1 | -1.01% | 0% | directionally correct |
| XLF | 2 | -0.90% | 50% | directionally correct |
| MSFT | 5 | +0.25% | 60% | anti-calibrated (wrong dir) |
| WFC | 1 | +0.81% | 100% | anti-calibrated (wrong dir) |
| AAPL | 38 | +0.85% | 66% | anti-calibrated (wrong dir) |
| NVDA | 8 | +1.83% | 88% | anti-calibrated (wrong dir) |
| GOOGL | 1 | +2.46% | 100% | anti-calibrated (wrong dir) |
| COP | 1 | +4.39% | 100% | anti-calibrated (wrong dir) |
| INTC | 16 | +7.13% | 75% | anti-calibrated (wrong dir) |
| AMD | 2 | +13.56% | 100% | anti-calibrated (wrong dir) |
| **CROSS-TICKER** | **85** | **+2.12%** | **69%** | **anti-calibrated** |

## 21-day horizon

| Ticker | n | mean α | wrong_rate | interpretation |
|---|---|---|---|---|
| HON | 1 | -18.23% | 0% | directionally correct |
| CVX | 1 | -12.97% | 0% | directionally correct |
| XLF | 2 | -4.14% | 0% | directionally correct |
| AAPL | 36 | -0.18% | 42% | directionally correct |
| MSFT | 5 | +2.03% | 80% | anti-calibrated (wrong dir) |
| XLE | 6 | +2.07% | 67% | anti-calibrated (wrong dir) |
| XLK | 1 | +2.15% | 100% | anti-calibrated (wrong dir) |
| NVDA | 8 | +3.11% | 88% | anti-calibrated (wrong dir) |
| GOOGL | 1 | +9.68% | 100% | anti-calibrated (wrong dir) |
| INTC | 14 | +32.38% | 79% | anti-calibrated (wrong dir) |
| **CROSS-TICKER** | **75** | **+6.22%** | **57%** | **anti-calibrated** |

## Per-(ticker, date) detail at 21d

| Ticker | Date | Rating | 21d α | Experiments |
|---|---|---|---|---|
| AAPL | 2025-11-21 | Underweight | -4.07% | 2026-05-03-008-opus47-cross-period |
| AAPL | 2026-01-30 | Underweight | +3.33% | 2026-05-02-005-wc12-cross-aapl, 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-02-06 | Underweight | -4.27% | 2026-05-03-002-exa-news-smoke-aapl |
| AAPL | 2026-02-13 | Underweight | +1.00% | 2026-05-03-004-single-call-baseline-aapl, 2026-05-09-002-wc11-v2-disambiguation, 2026-05-09-003-br3-v2-news-fundamentals |
| AAPL | 2026-02-20 | Underweight | -0.01% | 2026-05-02-005-wc12-cross-aapl |
| AAPL | 2026-02-27 | Underweight | +1.23% | 2026-05-03-004-single-call-baseline-aapl, 2026-05-09-001-br3-squeak-market-analyst, 2026-05-09-002-wc11-v2-disambiguation, 2026-05-09-003-br3-v2-news-fundamentals |
| AAPL | 2026-03-06 | Underweight | +0.42% | 2026-05-03-001-brave-news-smoke-aapl, 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-03-13 | Sell | -1.38% | 2026-05-02-005-wc12-cross-aapl |
| AAPL | 2026-03-13 | Underweight | -1.38% | 2026-05-03-001-brave-news-smoke-aapl, 2026-05-03-002-exa-news-smoke-aapl, 2026-05-03-004-single-call-baseline-aapl, 2026-05-09-002-wc11-v2-disambiguation, 2026-05-09-003-br3-v2-news-fundamentals |
| AAPL | 2026-03-20 | Underweight | -1.23% | 2026-05-03-002-exa-news-smoke-aapl, 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-04-01 | Underweight | -0.39% | 2026-05-08-001-wc-10-pilot |
| AAPL | 2026-04-03 | Underweight | -0.06% | 2026-05-03-001-brave-news-smoke-aapl, 2026-05-03-002-exa-news-smoke-aapl, 2026-05-03-004-single-call-baseline-aapl |
| AAPL | 2026-04-08 | Underweight | +2.80% | 2026-05-08-001-wc-10-pilot |
| CVX | 2026-04-03 | Underweight | -12.97% | 2026-05-05-003-signal-at-scale |
| GOOGL | 2026-03-25 | Underweight | +9.68% | 2026-05-05-002-spec003-sc002 |
| HON | 2026-04-03 | Underweight | -18.23% | 2026-05-05-003-signal-at-scale |
| INTC | 2025-12-26 | Underweight | +34.01% | 2026-05-03-008-opus47-cross-period |
| INTC | 2026-01-02 | Underweight | +24.13% | 2026-05-03-008-opus47-cross-period |
| INTC | 2026-01-09 | Underweight | +3.75% | 2026-05-03-008-opus47-cross-period |
| INTC | 2026-02-06 | Underweight | -5.59% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-02-13 | Underweight | -4.23% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-02-20 | Underweight | +4.71% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-02-27 | Underweight | -1.82% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-03-04 | Underweight | +14.81% | 2026-05-05-002-spec003-sc002 |
| INTC | 2026-03-11 | Underweight | +29.55% | 2026-05-05-002-spec003-sc002 |
| INTC | 2026-03-18 | Underweight | +44.76% | 2026-05-05-002-spec003-sc002 |
| INTC | 2026-03-20 | Underweight | +42.48% | 2026-05-03-007-opus47-30pair-mixed |
| INTC | 2026-03-25 | Underweight | +66.25% | 2026-05-05-002-spec003-sc002 |
| INTC | 2026-04-01 | Underweight | +97.43% | 2026-05-05-002-spec003-sc002 |
| INTC | 2026-04-03 | Underweight | +103.14% | 2026-05-03-007-opus47-30pair-mixed |
| MSFT | 2026-02-06 | Underweight | +3.10% | 2026-05-02-006-wc12-cross-msft |
| MSFT | 2026-02-20 | Underweight | +1.36% | 2026-05-02-006-wc12-cross-msft |
| MSFT | 2026-03-13 | Underweight | -5.47% | 2026-05-02-006-wc12-cross-msft |
| MSFT | 2026-03-27 | Underweight | +8.08% | 2026-05-02-006-wc12-cross-msft |
| NVDA | 2025-11-07 | Underweight | -3.49% | 2026-05-08-003-wc-10-bear-regime-q4-2025-nvda |
| NVDA | 2026-02-27 | Underweight | +1.09% | 2026-05-03-003-single-call-baseline-nvda, 2026-05-08-004-wc11-order-randomization, 2026-05-09-003-br3-v2-news-fundamentals |
| NVDA | 2026-03-06 | Underweight | +2.11% | 2026-05-03-003-single-call-baseline-nvda |
| NVDA | 2026-03-20 | Underweight | +7.18% | 2026-05-03-003-single-call-baseline-nvda |
| NVDA | 2026-03-27 | Underweight | +15.01% | 2026-05-03-003-single-call-baseline-nvda |
| NVDA | 2026-04-03 | Underweight | +0.78% | 2026-05-02-004-mr3-synthesis-v2 |
| XLE | 2025-12-19 | Underweight | +9.60% | 2026-05-04-004-xle-q4-2025-micro |
| XLE | 2025-12-26 | Underweight | +12.50% | 2026-05-04-004-xle-q4-2025-micro |
| XLE | 2026-01-02 | Underweight | +12.26% | 2026-05-04-004-xle-q4-2025-micro |
| XLE | 2026-03-06 | Underweight | +8.30% | 2026-05-04-003-multi-sector-phase-d-q1-2026 |
| XLE | 2026-03-27 | Underweight | -19.99% | 2026-05-04-003-multi-sector-phase-d-q1-2026 |
| XLE | 2026-04-03 | Underweight | -10.23% | 2026-05-04-003-multi-sector-phase-d-q1-2026 |
| XLF | 2026-01-30 | Underweight | -2.49% | 2026-05-04-003-multi-sector-phase-d-q1-2026 |
| XLF | 2026-02-06 | Underweight | -5.79% | 2026-05-04-003-multi-sector-phase-d-q1-2026 |
| XLK | 2026-02-20 | Underweight | +2.15% | 2026-05-04-002-xlk-q1-2026-substrate |

## Headline


**Mixed**: 4 ticker(s) (HON, CVX, XLF, AAPL) have correctly-bearish UW; 6 ticker(s) (MSFT, XLE, XLK, NVDA, GOOGL, INTC) anti-calibrated. Supports REGIME-SPECIFIC hypothesis — bear-side wrongness concentrates on tickers that subsequently rallied.
