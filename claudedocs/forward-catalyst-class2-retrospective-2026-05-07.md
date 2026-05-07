# Class C-2 (short-interest delta) retrospective — VERDICT: SKIP

**Date**: 2026-05-07
**Script**: `scripts/forward_catalyst_class2_retrospective.py`
**Cost**: $0 LLM (yfinance + state-log reads)
**Cohort**: 43 propagates within ~30 days of today (2026-04-07 onwards)

## Verdict — SKIP both directions

| Direction | Threshold | n_sup | Discrim | Net Δα | Verdict |
|---|---|---|---|---|---|
| Bull-side | ±10% | 2 | +0.00pp | +2.19pp | SKIP (gates 1+2 FAIL) |
| Bull-side | 0% | 3 | +66.67pp | +1.82pp | SKIP (n=3 statistically meaningless) |
| Bear-side | ±10% | 3 | **-85.71pp** | -3.93pp | SKIP (mechanism INVERTED) |
| Bear-side | 0% | 4 | **-100.00pp** | -3.64pp | SKIP (mechanism INVERTED) |

## Bear-side mechanism is INVERTED

Hypothesized: short-covering (delta < 0) → bear thesis unwinding →
suppress further bearish commits.

Empirical: when short interest has been COVERED (delta < 0) AND PM
picks Underweight/Sell, the bear commits had **0% hit rate** (4/4 with
negative α; the bears were RIGHT on all 4). Suppressing them would
have lost -3.64pp of α.

Mechanism interpretation: short covering is NOT a "bear thesis is
unwinding" signal on this cohort — it may instead reflect short-side
participants closing positions ahead of expected further weakness
(taking profits early). PM bearish commits coincident with covering
tend to be CORRECT, not contrarian.

## Bull-side cohort too thin

n=2-3 fires across the 43-row cohort. Statistically meaningless for
mechanism validation. The narrow ~30-day cohort window (PR #65
PARTIAL feasibility constraint) limits the sample significantly.

## Comparison vs C-4 (which PASSED bear-side)

C-4 (institutional ownership delta, PR #75) PASSED bear-side standalone
gate at n=12 with mechanism: institutional outflows are SLOW (lagging)
→ PM bear commits chasing the move = mean-reversion expected.

C-2 (short-interest delta, this PR) FAILS bear-side: short COVERING
implies short-side participants closing positions, which on this cohort
appears to PRECEDE further weakness rather than signal bear-thesis
collapse. Different temporal/market-microstructure dynamic than C-4's
13F flow data.

## Bear-side scorecard final state (after C-2)

| Class | Verdict | Pass status |
|---|---|---|
| C-1 (insider transactions) | SKIP | empirical FAIL on cohort |
| **C-2 (short-interest delta)** | **SKIP** | **mechanism INVERTED bear-side; n too thin bull-side** |
| C-3 (analyst PT delta) | NOT FEASIBLE | data-availability |
| C-4 (institutional ownership) | STANDALONE PASS bear-side | awaiting v1.4.3 additive analysis |
| C-5 EPS-surprise variant | SKIP | additive FAIL |
| C-5 PRICE-REACTION variant | SKIP | mechanism inverted |
| C-6 (bear-news density) | SKIP | structural redundancy |

**Final scorecard: 6 of 6 mechanism classes evaluated** (C-2 was the
last untested). 5 SKIP / 1 STANDALONE PASS (C-4) / 0 fully-spec-eligible.

## Implications

1. **Bear-side mechanism class space is largely exhausted**: of 6
   candidate classes, only C-4 has a viable path to a spec, and only
   pending v1.4.3 additive overlap analysis.

2. **Constitution VIII v1.4.1 retrospective-first methodology
   validated yet again**: C-2 retrospective produced SKIP in 30 minutes;
   spec invocation avoided. Saved 6-8h of spec+impl work.

3. **Two C-class mechanisms now show INVERTED behavior on bear-side**
   (C-5 price-reaction + C-2 short-covering). Both were originally
   hypothesized as mean-reversion signals; both empirically show
   momentum/continuation. The bear cohort on the SC-009-era data has a
   strong continuation bias that mean-reversion mechanisms can't
   exploit.

## Followups

1. **No more bear-side mechanism class probes needed** — survey complete.
2. **C-4 v1.4.3 additive overlap analysis** is the only remaining
   path to a bear-side spec. ~30min, $0. Per PR #75 followup.
3. **Update PR #22 design doc** with the empirical-inversion finding
   on C-5 + C-2 (both originally hypothesized as mean-reversion signals;
   both refuted in this direction). ~10min, $0.

## Sibling docs

- `claudedocs/class-c2-short-interest-feasibility-2026-05-07.md` (PR
  #65 feasibility verdict)
- `claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` (PR
  #75 — only standalone-PASS bear-side mechanism)
- `claudedocs/forward-catalyst-class5-reaction-retrospective-2026-05-07.md`
  (sister inverted-mechanism finding)
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` (PR #22
  design doc enumerating all 6 classes)
