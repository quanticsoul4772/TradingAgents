# ANALYSIS — 2026-05-07-001-spec-008-hybrid-c-ab-ablation

**Status**: PARTIAL
**Date**: 2026-05-07

## Headline

**REGRESSION — boost not engaged on any row; investigate code/config**

## Setup recap

- Cohort: 10 propagates (0 with realized α at 21d, 10 pending)
- Boost configuration: ENABLED (window=14d, magnitude=0.5x, T_bull=0.6)
- Boost-OFF comparison: post-hoc from state-log `bull_case_priced_in > 0.6`

## SC-009 acceptance gate

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| Bull-side net Δα improvement | [+2.35pp, +4.35pp] | N/A | INCONCLUSIVE |
| n_fired_boost_on | ≥ 8 | 0 | FAIL |
| Boost engaged ≥ 1 row | ≥ 1 | 0 | FAIL |

## Headline numbers

- n_bull_commits total: **0**
- n_fired_boost_on: **0**
- n_fired_boost_off (post-hoc): **0**
- Decisions changed by boost: **0**
- Bull baseline α: N/A
- Boost-ON kept α: N/A
- Boost-OFF kept α: N/A

## Boost-engagement breakdown

- Total rows with calendar_boost > 0: **0** of 0

**No rows had boost engaged** — none of the cohort tickers had earnings within 14 days of trade date. SC-009 gate 3 FAILS; experiment did not exercise the boost mechanism.

## Reproducibility

```
python scripts/analyze_sc009_ab.py --holding-days 21
```

Reads `experiments\2026-05-07-001-spec-008-hybrid-c-ab-ablation\results.csv` + state logs from `C:\Users\rbsmi\.tradingagents\logs` + free yfinance for realized α. Zero LLM cost.
