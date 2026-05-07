# ANALYSIS — 2026-05-07-001-spec-008-hybrid-c-ab-ablation

**Status**: FINAL
**Date**: 2026-05-07

## Headline

**INCONCLUSIVE — n_fired < 8; expand cohort + rerun**

## Setup recap

- Cohort: 10 propagates (10 with realized α at 21d, 0 pending)
- Boost configuration: ENABLED (window=14d, magnitude=0.5x, T_bull=0.6)
- Boost-OFF comparison: post-hoc from state-log `bull_case_priced_in > 0.6`

## SC-009 acceptance gate

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| Bull-side net Δα improvement | [+2.35pp, +4.35pp] | N/A | INCONCLUSIVE |
| n_fired_boost_on | ≥ 8 | 3 | FAIL |
| Boost engaged ≥ 1 row | ≥ 1 | 6 | PASS |

## Headline numbers

- n_bull_commits total: **3**
- n_fired_boost_on: **3**
- n_fired_boost_off (post-hoc): **3**
- Decisions changed by boost: **0**
- Bull baseline α: -4.22%
- Boost-ON kept α: N/A
- Boost-OFF kept α: N/A

## Boost-engagement breakdown

- Total rows with calendar_boost > 0: **6** of 10

| Ticker | Trade Date | days_to_earnings | calendar_boost | base score | effective score | pre_rating | post_rating | α |
|---|---|---|---|---|---|---|---|---|
| MSFT | 2026-04-17 | 12 | 0.143 | 0.62 | 0.66 | Hold | Hold | -3.27% |
| MSFT | 2026-04-24 | 5 | 0.643 | 0.55 | 0.73 | Hold | Hold | -3.15% |
| AAPL | 2026-04-17 | 13 | 0.071 | 0.75 | 0.78 | Hold | Hold | +4.06% |
| AAPL | 2026-04-24 | 6 | 0.571 | 0.75 | 0.96 | Underweight | Underweight | +4.28% |
| MA | 2026-04-17 | 13 | 0.071 | 0.70 | 0.72 | Overweight | Hold | -7.99% |
| MA | 2026-04-24 | 6 | 0.571 | 0.72 | 0.93 | Overweight | Hold | -4.20% |

## Reproducibility

```
python scripts/analyze_sc009_ab.py --holding-days 21
```

Reads `experiments\2026-05-07-001-spec-008-hybrid-c-ab-ablation\results.csv` + state logs from `C:\Users\rbsmi\.tradingagents\logs` + free yfinance for realized α. Zero LLM cost.
