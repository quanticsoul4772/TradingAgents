# Class C-5 PRICE-REACTION variant retrospective — VERDICT: SKIP (mechanism inverted)

**Date**: 2026-05-07
**Script**: `scripts/forward_catalyst_class5_reaction_retrospective.py`
**Cost**: $0 LLM (yfinance + state-log reads)

## Verdict — SKIP both variants on both directions

| Variant | Direction | Verdict | Reason |
|---|---|---|---|
| magnitude (±5%) | bull | SKIP | n_sup=0 (no bullish commits had ±5% earnings reaction in lookback) |
| magnitude (±5%) | bear | SKIP | n_sup=1; -67pp discrim |
| magnitude (±0%; all-fires) | bull | SKIP | discrim -34pp; mechanism inverted |
| magnitude (±0%; all-fires) | bear | SKIP | discrim -17pp; insufficient cohort |
| aligned (±0%) | bull | SKIP | discrim -34pp; same as magnitude |
| aligned (±0%) | bear | SKIP | n_sup=0 |

## Mechanism finding: post-earnings reaction is MOMENTUM, not mean-reversion

The hypothesis (per PR #22 design doc) was that large recent earnings
reactions signal market-absorbed information → subsequent commits in
the reaction direction would be post-hoc chasing → suppress them.

The empirical data REFUTES this:

| Cohort (threshold=0) | n | mean α | hit rate (suppression-aligned) |
|---|---|---|---|
| Suppressed bullish (positive reaction → bullish) | 13 | **+4.87%** | 15.4% |
| Untouched bullish | 63 | +1.37% | 49.2% |
| Suppressed bearish (negative reaction → bearish) | 2 | +0.64% | 50.0% |
| Untouched bearish | 39 | +12.45% | 66.7% |

**The "should be suppressed" bullish cohort outperformed the "untouched"
cohort by +3.50pp on average**. Recent positive earnings reactions
predict CONTINUED upside on this cohort — momentum effect, not
mean-reversion.

This is the OPPOSITE direction from the EPS-surprise variant
(`forward_catalyst_class5_retrospective.py` — 2026-05-06) which had
discrim +11.92pp / hit 96.3% / Δα +4.37pp at threshold=0.02. The two
operationalizations measure different things despite both being "Class
C-5":

- **EPS surprise magnitude**: high surprise → bull case absorbed (mean-reversion). PASSED standalone, FAILED additive overlap.
- **Price reaction magnitude**: high reaction → upward momentum continues (continuation). FAILS standalone in opposite direction.

## Why this happens

The 30-day lookback window catches Q1 2026 earnings season for many
SC-009 cohort tickers. Tech megacaps (NVDA, MSFT, GOOGL, AMZN, META)
that beat + rallied tended to KEEP rallying through April. Suppressing
bullish commits on those tickers would have HURT by missing the
continued upside.

The earnings SURPRISE magnitude (different signal) captures something
different — possibly "magnitude of analyst-error" which is a more
contrarian signal than "raw price move."

## Bear-side cohort is too thin to evaluate

Across 252 state logs and 249 enriched α rows, only 1-2 rows had
bearish PM commits (UW/Sell) within 30 days of a negative earnings
reaction. Insufficient sample for a verdict. The bear-side hypothesis
remains untested but unsupported.

## SKIP-type taxonomy: empirical SKIP

This verdict is an EMPIRICAL SKIP per Constitution VIII v1.4.0 — gates
FAIL on the data, mechanism doesn't work as hypothesized. Joins:

| Class | Verdict | SKIP type |
|---|---|---|
| C-1 (insider transactions) | SKIP | empirical (PR #23) |
| C-3 (analyst PT delta) | NOT FEASIBLE | data-availability (PR #40) |
| C-5 EPS-surprise variant | SKIP | empirical-additive-FAIL (2026-05-06) |
| **C-5 PRICE-REACTION variant** | **SKIP** | **empirical-mechanism-inverted (this PR)** |
| C-6 (bear-news density) | SKIP | structural-redundant-Spec-003 (PR #67) |

3 of 6 mechanism classes have at least one variant tested (C-1, C-5
both variants, C-6 structural). All produced SKIP. C-5's TWO different
operationalizations both failed but in OPPOSITE directions —
strengthens the case that bear-side mechanism class space is genuinely
sparse.

## Bear-side scorecard final state (after this PR)

| Class | Verdict | Retrospective viable? | Verdict source |
|---|---|---|---|
| C-1 (insider transactions) | SKIP | NO | PR #23 |
| C-2 (short-interest delta) | PARTIAL <30d | YES (SC-009 only) | PR #65 |
| C-3 (analyst PT delta) | NOT FEASIBLE | NO | PR #40 |
| C-4 (institutional ownership) | PARTIAL within 13F window | YES (SC-009 only) | PR #66 |
| **C-5 EPS-surprise variant** | SKIP | empirically failed | 2026-05-06 |
| **C-5 PRICE-REACTION variant** | **SKIP** | **empirically failed (this PR)** | this PR |
| C-6 (bear-news density) | SKIP | NO | PR #67 |

**C-5 mechanism class is now closed**. Both major operationalizations
tested, both SKIPPED for different reasons (one structural-overlap,
one mechanism-inversion). Future bear-side mechanism class candidates
should look beyond C-5.

## Implications

1. **Bear-side mechanism class search is largely exhausted**: of 6
   candidate classes from PR #22, only C-2 + C-4 remain viable for
   retrospectives (both PARTIAL feasibility). C-5 is now CLOSED.
2. **Constitution VIII v1.4.1 retrospective-first methodology
   validated again**: 2-3h retrospective produced SKIP verdict; spec
   invocation avoided. Saved 6-8h of spec+impl work.
3. **The PR #22 design doc's "C-5 reaction-magnitude" hypothesis
   is empirically refuted**: post-earnings reactions are MOMENTUM
   (continuation) not mean-reversion in this cohort. Update PR #22
   if it ever gets revisited.

## Followups

1. **C-2 retrospective on SC-009 specifically** (~2-3h, $0): next
   bear-side candidate; PARTIAL feasibility within 30-day window.
2. **C-4 retrospective on SC-009 specifically** (~2-3h, $0): time-
   bounded until ~2026-05-15.
3. **No more C-5 work needed**: both major operationalizations
   tested.

## Sibling docs

- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` (PR #22
  design doc — original 6-class enumeration)
- `claudedocs/forward-catalyst-class5-retrospective-2026-05-06.md` (EPS-surprise variant — PASS standalone, FAIL additive)
- `claudedocs/class-c5-earnings-feasibility-2026-05-07.md` (PR #64
  feasibility verdict — confirmed yfinance has the data)
- `claudedocs/class-c6-bear-news-density-skip-2026-05-07.md` (PR #67
  closes 6/6 mechanism class survey)
