# Spec 001 Phase 1: Shadow Aggregator Report

_Generated 2026-05-04T23:16:58+00:00._

**Total propagates analyzed**: 156
**Exact rating match**: 66 (42.3%)
**Within ±1 tier**: 147 (94.2%)
**Direction match**: 66 (42.3%)
**SC-001 (direction ≥80%)**: FAIL

## Confusion: actual (rows) × shadow (cols)

| Actual \ Shadow | Buy | Overweight | Hold | Underweight | Sell |
|---|---:|---:|---:|---:|---:|
| Buy | 0 | 0 | 1 | 0 | 0 |
| Overweight | 0 | 20 | 30 | 2 | 0 |
| Hold | 1 | 19 | 40 | 18 | 0 |
| Underweight | 0 | 5 | 14 | 6 | 0 |
| Sell | 0 | 0 | 0 | 0 | 0 |

## Methodology

- Each propagate's analyst prose reports (market_report, news_report, fundamentals_report, sentiment_report when present, investment_plan) are featurized via `derive_signal_from_prose` to produce a Signal (direction in [-1, +1], magnitude in [0, 1], abstain bool).
- The deterministic `aggregate(signals)` produces a 5-tier rating + confidence + direction_score using weights (market 0.25, news 0.20, fundamentals 0.30, sentiment 0.10, investment_plan 0.15).
- Direction-agreement uses Buy/OW=+1, Hold=0, UW/Sell=-1 collapsing the 5-tier rating to a 3-tier directional bucket.
- This is **shadow mode** (Phase 1) — production decisions remain the actual PM rating; the shadow aggregator is logged for comparison only.

## Per-row data (first 30 rows shown)

| Ticker | Date | Actual | Shadow | Conf | Dir score | n signals | n used | n abstained |
|---|---|---|---|---:|---:|---:|---:|---:|
| AAPL | 2025-11-07 | Hold | Hold | 0.18 | +0.035 | 4 | 4 | 0 |
| AAPL | 2025-11-14 | Hold | Hold | 0.16 | -0.005 | 4 | 4 | 0 |
| AAPL | 2025-11-21 | Underweight | Hold | 0.18 | +0.097 | 4 | 4 | 0 |
| AAPL | 2025-11-28 | Hold | Hold | 0.19 | +0.127 | 4 | 4 | 0 |
| AAPL | 2025-12-05 | Overweight | Hold | 0.16 | +0.027 | 4 | 4 | 0 |
| AAPL | 2025-12-12 | Overweight | Hold | 0.15 | +0.018 | 4 | 4 | 0 |
| AAPL | 2025-12-19 | Hold | Hold | 0.19 | +0.086 | 4 | 4 | 0 |
| AAPL | 2025-12-26 | Hold | Overweight | 0.18 | +0.313 | 4 | 4 | 0 |
| AAPL | 2026-01-02 | Hold | Underweight | 0.19 | -0.231 | 4 | 4 | 0 |
| AAPL | 2026-01-09 | Hold | Hold | 0.18 | -0.042 | 4 | 4 | 0 |
| AAPL | 2026-01-30 | Overweight | Hold | 0.17 | +0.038 | 4 | 4 | 0 |
| AAPL | 2026-02-06 | Overweight | Overweight | 0.16 | +0.492 | 4 | 4 | 0 |
| AAPL | 2026-02-13 | Overweight | Hold | 0.14 | -0.067 | 4 | 4 | 0 |
| AAPL | 2026-02-20 | Hold | Hold | 0.17 | -0.100 | 4 | 4 | 0 |
| AAPL | 2026-02-27 | Hold | Hold | 0.16 | -0.073 | 4 | 4 | 0 |
| AAPL | 2026-03-06 | Hold | Hold | 0.16 | +0.014 | 4 | 4 | 0 |
| AAPL | 2026-03-13 | Hold | Underweight | 0.16 | -0.301 | 4 | 4 | 0 |
| AAPL | 2026-03-20 | Hold | Underweight | 0.16 | -0.303 | 4 | 4 | 0 |
| AAPL | 2026-03-27 | Hold | Overweight | 0.17 | +0.228 | 4 | 4 | 0 |
| AAPL | 2026-04-03 | Hold | Hold | 0.18 | +0.032 | 4 | 4 | 0 |
| AAPL | 2026-04-10 | Underweight | Overweight | 0.15 | +0.329 | 4 | 4 | 0 |
| AAPL | 2026-04-17 | Hold | Overweight | 0.18 | +0.377 | 4 | 4 | 0 |
| AAPL | 2026-04-24 | Hold | Overweight | 0.16 | +0.464 | 4 | 4 | 0 |
| BRK.B | 2026-02-06 | Hold | Overweight | 0.16 | +0.569 | 4 | 2 | 2 |
| BRK.B | 2026-02-13 | Hold | Overweight | 0.15 | +0.384 | 4 | 2 | 2 |
| BRK.B | 2026-02-20 | Hold | Buy | 0.12 | +0.666 | 4 | 3 | 1 |
| GOOGL | 2026-02-06 | Overweight | Overweight | 0.15 | +0.369 | 4 | 4 | 0 |
| GOOGL | 2026-02-13 | Hold | Hold | 0.17 | +0.148 | 4 | 4 | 0 |
| GOOGL | 2026-02-20 | Overweight | Hold | 0.17 | +0.195 | 4 | 4 | 0 |
| GOOGL | 2026-02-27 | Hold | Hold | 0.16 | +0.087 | 4 | 4 | 0 |

_(126 more rows in the full corpus.)_
