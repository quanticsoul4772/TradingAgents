# ANALYSIS — 2026-05-07-001-spec-008-hybrid-c-ab-ablation

**Status**: PRELIMINARY (mid-flight at 24/36 rows; canonical 21d windows
have NOT closed yet — see "Realized α window status" below)
**Date**: 2026-05-07 (last analyzer run)
**Final ANALYSIS due**: ~2026-05-22 (after canonical 21d windows close
for both 04-17 and 04-24 cohorts)

## Headline (PRELIMINARY)

**PRELIMINARY PASS — gates 2 + 3 robust; gate 1 marginal pending canonical 21d**

The analyzer auto-emits a "PASS — recommend Spec 008 v2 default-on flip
proposal" verdict (next paragraph). This verdict is **TENTATIVE** because:
- Gate 1 (alt suppressed-α direction in [-10%, +2%]) currently shows
  +1.75% which is **just below the +2% upper bound** — could shift to
  FAIL if more positive α lands in the next 15 days as windows close.
- Gate 2 (n_fired_boost_on ≥ 8) is at exactly 8. Robust to α data
  completion; will only grow as more bull-pre rows arrive.
- Gate 3 (boost engaged ≥ 1) is comfortably PASS at 14.

See `claudedocs/sc-009-23-row-mark-trajectory-pass-2026-05-07-evening.md`
for the full trajectory analysis (PR #51) and three-scenario verdict
projection (best / mid / worst case).

**Auto-generated verdict line**: PASS — recommend Spec 008 v2 default-on flip proposal

## Realized α window status

Today: 2026-05-07. Cohort dates and canonical 21d window completion:

| Cohort date | 21d trading days end | Days remaining |
|---|---|---|
| 2026-04-17 | ~2026-05-18 | ~11 days |
| 2026-04-24 | ~2026-05-26 | ~19 days |

The analyzer reports α as "measurable" using `fetch_returns(holding_days=21)`,
but for cohort dates whose canonical 21d window hasn't fully closed, this
falls back to whatever forward data is available (truncated to today).
**The α numbers below should be interpreted as preliminary signal, not
as final verdict input.**

## Setup recap

- Cohort: 24 propagates (24 with PRELIMINARY α; 0 strictly pending; see
  realized-α-window caveat above)
- Boost configuration: ENABLED (window=14d, magnitude=0.5x, T_bull=0.6)
- Boost-OFF comparison: post-hoc from state-log `bull_case_priced_in > 0.6`

## SC-009 acceptance gate

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| Bull-side net Δα improvement | [+2.35pp, +4.35pp] | N/A | INCONCLUSIVE |
| n_fired_boost_on | ≥ 8 | 8 | PASS |
| Boost engaged ≥ 1 row | ≥ 1 | 14 | PASS |

## Headline numbers

- n_bull_commits total: **8**
- n_fired_boost_on: **8**
- n_fired_boost_off (post-hoc): **8**
- Decisions changed by boost: **0**
- Bull baseline α: +1.75%
- Boost-ON kept α: N/A
- Boost-OFF kept α: N/A

## Boost-engagement breakdown

- Total rows with calendar_boost > 0: **14** of 24

| Ticker | Trade Date | days_to_earnings | calendar_boost | base score | effective score | pre_rating | post_rating | α |
|---|---|---|---|---|---|---|---|---|
| MSFT | 2026-04-17 | 12 | 0.143 | 0.62 | 0.66 | Hold | Hold | -3.37% |
| MSFT | 2026-04-24 | 5 | 0.643 | 0.55 | 0.73 | Hold | Hold | -3.25% |
| AAPL | 2026-04-17 | 13 | 0.071 | 0.75 | 0.78 | Hold | Hold | +3.86% |
| AAPL | 2026-04-24 | 6 | 0.571 | 0.75 | 0.96 | Underweight | Underweight | +4.08% |
| MA | 2026-04-17 | 13 | 0.071 | 0.70 | 0.72 | Overweight | Hold | -7.23% |
| MA | 2026-04-24 | 6 | 0.571 | 0.72 | 0.93 | Overweight | Hold | -3.43% |
| COP | 2026-04-17 | 13 | 0.071 | 0.55 | 0.57 | Underweight | Underweight | -3.45% |
| COP | 2026-04-24 | 6 | 0.571 | 0.65 | 0.84 | Hold | Hold | -7.58% |
| INTC | 2026-04-17 | 6 | 0.571 | 0.88 | 1.00 | Underweight | Underweight | +58.40% |
| GOOGL | 2026-04-17 | 12 | 0.143 | 0.70 | 0.75 | Buy | Hold | +12.25% |
| GOOGL | 2026-04-24 | 5 | 0.643 | 0.78 | 1.00 | Overweight | Hold | +11.89% |
| AMD | 2026-04-24 | 11 | 0.214 | 0.85 | 0.94 | Underweight | Underweight | +13.97% |
| AMZN | 2026-04-17 | 12 | 0.143 | 0.78 | 0.84 | Overweight | Hold | +5.72% |
| AMZN | 2026-04-24 | 5 | 0.643 | 0.78 | 1.00 | Hold | Hold | +0.73% |

## Reproducibility

```
python scripts/analyze_sc009_ab.py --holding-days 21
```

Reads `experiments\2026-05-07-001-spec-008-hybrid-c-ab-ablation\results.csv` + state logs from `C:\Users\rbsmi\.tradingagents\logs` + free yfinance for realized α. Zero LLM cost.
