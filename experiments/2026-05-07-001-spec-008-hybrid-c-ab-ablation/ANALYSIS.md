# ANALYSIS — 2026-05-07-001-spec-008-hybrid-c-ab-ablation

**Status**: PRELIMINARY (backtest COMPLETE at 36/36 rows but canonical
21d windows have NOT closed yet — see "Realized α window status" below)
**Date**: 2026-05-07 (last analyzer run, post-backtest-completion)
**Final ANALYSIS due**: ~2026-05-22 (after canonical 21d windows close
for both 04-17 and 04-24 cohorts)

## Headline (PRELIMINARY at full sample)

**PRELIMINARY PASS-by-non-counterexample — gates 2+3 robust; recommend SHADOW-MODE-FIRST not default-on flip**

The analyzer auto-emits a "PASS — recommend Spec 008 v2 default-on flip
proposal" verdict (next paragraph). This verdict is **TENTATIVE AND
REFINED** by two material findings from PR #56 + PR #57:

1. **PASS-by-non-counterexample, NOT PASS-by-active-improvement**: across
   all 36 rows, **0 decisions changed by boost**. Boost-ON vs Boost-OFF
   would produce identical fire decisions on this cohort. ALL 13 bull-pre
   fires had base bull_score > T_bull = 0.60 (minimum 0.65). The boost
   mechanism's intended regime (borderline scores in [0.55, 0.65]) is
   unrepresented in this cohort — boost can't HURT but also can't show
   VALUE here.

2. **Recommendation: shadow-mode-first launch per Constitution VIII v1.4.0**,
   NOT direct default-on flip. The PASS reflects "boost didn't HURT" not
   "boost showed value." A future default-on flip needs cohort exercising
   the borderline regime (where the original Hybrid C retrofit showed
   +3.35pp improvement).

Gate 1 trajectory across 4 mid-flight marks shows monotone improvement
toward neutrality (-4.44% → +1.75% → +1.12% → **+0.43%** at full sample).
The +0.43% is comfortably in the [-10%, +2%] PASS band but on the
non-counterexample side (filter suppressed near-zero-α commits, not
clear losers).

See companion docs:
- `claudedocs/sc-009-backtest-complete-final-state-2026-05-07-night.md` (PR #57)
- `claudedocs/spec-007-calendar-independence-bac-gs-2026-05-07-late.md` (PR #56)
- `claudedocs/sc-009-27-row-mark-and-sweep-refresh-2026-05-07-late.md` (PR #53)
- `claudedocs/sc-009-23-row-mark-trajectory-pass-2026-05-07-evening.md` (PR #51)

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

- Cohort: **36 propagates COMPLETE** (36 with PRELIMINARY α; see
  realized-α-window caveat above)
- Boost configuration: ENABLED (window=14d, magnitude=0.5x, T_bull=0.6)
- Boost-OFF comparison: post-hoc from state-log `bull_case_priced_in > 0.6`
- Cohort composition: 18 tickers × 2 Fridays (2026-04-17, 2026-04-24)

## SC-009 acceptance gate (final at full sample)

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| Bull-side net Δα improvement (standard) | [+2.35pp, +4.35pp] | N/A (100% fire rate; alt fallback used) | undefined |
| Gate 1 alt (suppressed-α direction) | within [-10%, +2%] | **+0.43%** | PASS (non-counterexample) |
| Gate 2: n_fired_boost_on | ≥ 8 | **13** | PASS (61% above threshold) |
| Gate 3: Boost engaged ≥ 1 row | ≥ 1 | **18** | PASS (1800% above threshold) |

## Headline numbers (final at full sample)

- n_bull_commits total: **13**
- n_fired_boost_on: **13** (100% bull-fire rate sustained throughout)
- n_fired_boost_off (post-hoc): **13** (matches; boost changed nothing)
- **Decisions changed by boost: 0** (PASS-by-non-counterexample finding
  empirically confirmed at full sample)
- Bull baseline α: **+0.43%** (monotone-refining trajectory toward neutral)
- Boost-ON kept α: N/A (100% fire rate; no rows kept)
- Boost-OFF kept α: N/A
- Net Δα improvement: N/A (standard gate undefined; alt fallback used)

## Cohort breakdown by PM rating (final)

- Hold: 23 of 36 (64%)
- Underweight: 7 of 36 (19%)
- Overweight: 6 of 36 (17%)
- Buy: 0 of 36
- Sell: 0 of 36

## Bear-side cohort (informational — spec 007 bear in shadow mode)

7 Underweight commits: COP-04-17, INTC×2, AMD×2, CVX×2. All 7 had
bear_score < T_bear = 0.50 (calibrated correctly inert per shadow-mode
expectation). Strong evidence base for eventual bear-side default-flip
decision (n=7 calibrated inerts; needs n≥30 per Constitution VIII
shadow-mode evaluation timeline).

## Boost-engagement breakdown (18 of 36 rows)

α values omitted from this table — see "Realized α window status" caveat
above (canonical 21d windows still open). Final ANALYSIS.md (post
2026-05-22) will include α in the table.

| Ticker | Trade Date | days_to_earnings | calendar_boost | base score | effective score | pre_rating | post_rating |
|---|---|---|---|---|---|---|---|
| MSFT | 2026-04-17 | 12 | 0.143 | 0.62 | 0.664 | Hold | Hold |
| MSFT | 2026-04-24 | 5 | 0.643 | 0.55 | 0.727 | Hold | Hold |
| AAPL | 2026-04-17 | 13 | 0.071 | 0.75 | 0.777 | Hold | Hold |
| AAPL | 2026-04-24 | 6 | 0.571 | 0.75 | 0.964 | Underweight | Underweight |
| MA | 2026-04-17 | 13 | 0.071 | 0.70 | 0.725 | Overweight | Hold |
| MA | 2026-04-24 | 6 | 0.571 | 0.72 | 0.926 | Overweight | Hold |
| COP | 2026-04-17 | 13 | 0.071 | 0.55 | 0.570 | Underweight | Underweight |
| COP | 2026-04-24 | 6 | 0.571 | 0.65 | 0.836 | Hold | Hold |
| INTC | 2026-04-17 | 6 | 0.571 | 0.88 | 1.000 | Underweight | Underweight |
| GOOGL | 2026-04-17 | 12 | 0.143 | 0.70 | 0.750 | Buy | Hold |
| GOOGL | 2026-04-24 | 5 | 0.643 | 0.78 | 1.000 | Overweight | Hold |
| AMD | 2026-04-24 | 11 | 0.214 | 0.85 | 0.941 | Underweight | Underweight |
| AMZN | 2026-04-17 | 12 | 0.143 | 0.78 | 0.836 | Overweight | Hold |
| AMZN | 2026-04-24 | 5 | 0.643 | 0.78 | 1.000 | Hold | Hold |
| LLY | 2026-04-17 | 13 | 0.071 | 0.70 | 0.725 | Overweight | Hold |
| LLY | 2026-04-24 | 6 | 0.571 | 0.62 | 0.797 | Hold | Hold |
| CVX | 2026-04-24 | 7 | 0.500 | 0.50 | 0.625 | Underweight | Underweight |
| HON | 2026-04-17 | 6 | 0.571 | 0.55 | 0.707 | Hold | Hold |

**Note**: Rows with `pre_rating = post_rating` had no operational fire
(filter would only fire on Buy/OW pre_rating). Rows with `pre_rating →
post_rating = Hold` show actual fires. Of the 18 boost-engaged rows, **6
fired** (pre Buy/OW → post Hold): MA×2, GOOGL×2, AMZN-04-17, LLY-04-17.
The other 12 had boost computed but pre_rating wasn't bullish so no fire
applied (boost is operationally inert on non-bullish pre).

The remaining 7 bull-pre fires (13 - 6 = 7) come from rows with
calendar_boost = 0 (outside 14d window): BAC×2 (88d, 81d), GS-04-17
(88d), NVDA-04-24 (26d), and 3 others to identify (PR #57 followup #1).
These fires demonstrate spec 007 calendar-INDEPENDENCE per PR #56.

## Reproducibility

```
python scripts/analyze_sc009_ab.py --holding-days 21
```

Reads `experiments\2026-05-07-001-spec-008-hybrid-c-ab-ablation\results.csv` + state logs from `C:\Users\rbsmi\.tradingagents\logs` + free yfinance for realized α. Zero LLM cost.
