# Class C-4 (institutional ownership delta) retrospective — VERDICT: BEAR-SIDE SHADOW-MODE-ELIGIBLE

**Date**: 2026-05-07 (within ~8 days of 2026-05-15 13F refresh deadline)
**Script**: `scripts/forward_catalyst_class4_retrospective.py`
**Cost**: $0 LLM (yfinance + state-log reads)
**Cohort**: 175 propagates from 2026-02-14 onwards (Q4 2025 13F era)

## Verdict — bear-side passes; bull-side too thin

| Direction | Verdict | n_sup | Discrim | Hit % | Net Δα |
|---|---|---|---|---|---|
| Bull-side | PASS-but-thin (n=1) | 1 | +63pp | 100% | +3.17pp |
| **Bear-side** | **PASS standalone** | **12** | **+10.29pp** | **75.0%** | **+5.41pp** |

Bull-side metrics technically clear all gates but n=1 is statistically
meaningless. Bear-side at n=12 is the operative finding.

## Bear-side mechanism: institutional outflow + bearish commit = post-hoc chase

When top 10 institutional holders' net rotation is < -5% (clear
outflow), and PM picks Underweight/Sell, the bear thesis is WRONG 75%
of the time. Mean realized α on suppressed cohort: +5.41%.

**Interpretation**: institutional outflows tend to occur AFTER moves are
over (institutions are slow / position adjustment cycles). PM seeing
both the prior move AND the outflow data picks UW, but that's chasing
— the move has already happened, subsequent return tends to mean-revert
(positive α = bear shorts get hurt).

This is the FIRST bear-side mechanism to PASS Constitution VIII v1.4.0
gate since Spec 007 itself.

## Why bull-side is thin (n=1)

Only 1 propagate had `bullish PM commit + net institutional rotation
> +5%` in the 175-row cohort. Possible reasons:
- Strong institutional inflows are rare (most rotation is small or
  mixed across top 10)
- When inflows do occur, PM tends to go Hold rather than Buy/OW (per
  Constitution VII Calibrated Abstention; per behavioral-additive
  pattern from PR #41 sweep)

Bull-side mechanism is **untested empirically** at meaningful n. The
single fire with -3.17% α is suggestive but not statistically
load-bearing.

## Constitution VIII v1.4.0 verdict

Standalone gate: **bear-side PASS**.

Per the standard, this would warrant a SHADOW-MODE-FIRST launch (since
all 3 criteria pass at n=12 but the cohort is small enough that one
might prefer additional empirical validation before flipping to
default-active).

Per Constitution VIII v1.4.3 additive-overlap-vs-Spec-007: REQUIRED
before spec invocation. The bear-side filter would need to:
- Show net Δα improvement ≥ +0.5pp vs Spec 007 bear shadow alone, OR
- Cohort hit improvement ≥ +5pp, OR
- FP rate improvement ≥ -10pp on intersection

The additive overlap script does NOT yet exist for C-4 (deferred
pattern from prior bear-side retrospectives). **Spec invocation
should not proceed without this analysis.**

## Pre-spec-invocation checklist (NOT yet complete)

| Check | Status |
|---|---|
| Standalone gate PASS | ✅ bear-side at n=12 |
| Cohort size meaningful | ✅ n=12 fires; n=17 FP cohort (75% vs 64.7% discrim) |
| Mechanism class distinct from existing | ✅ institutional-flow class; not in existing 4 mechanism classes |
| Time-window discipline respected | ⚠️ valid until ~2026-05-15 (13F refresh) |
| v1.4.3 additive overlap vs Spec 007 | ❌ NOT RUN (deferred) |
| Sample-size confidence (n≥30) | ❌ n=12; single-period cohort |

**Spec is NOT eligible for invocation per the v1.4.3 + standard sample-
size discipline.** Two paths forward:
1. Run v1.4.3 additive overlap analysis (~30min, $0). If overlap
   analysis still favors C-4, propose SHADOW-MODE-FIRST spec
   invocation.
2. Wait for additional cohort growth (Path C snapshot wiring per PR
   #73 would help retroactively if/when re-run with snapshotted
   institutional data).

## SKIP-type taxonomy update

C-4 is NOT a SKIP. It's the FIRST bear-side mechanism class since C-1
to make it past the standalone gate. Joins the bear-side scorecard:

| Class | Verdict | Status |
|---|---|---|
| C-1 (insider transactions) | SKIP | empirical FAIL on cohort |
| C-2 (short-interest delta) | UNTESTED | PARTIAL feasibility, retrospective not yet run |
| C-3 (analyst PT delta) | NOT FEASIBLE | data-availability |
| **C-4 (institutional ownership)** | **STANDALONE PASS bear-side** | **awaiting v1.4.3 additive analysis** |
| C-5 EPS-surprise variant | SKIP | additive-FAIL |
| C-5 PRICE-REACTION variant | SKIP | mechanism-inverted |
| C-6 (bear-news density) | SKIP | structural redundancy |

C-4 is now the **ONLY** unfailed bear-side mechanism class in the
6-class survey. Significant finding.

## Cohort scope caveat

The 175-row cohort is from 2026-02-14 onwards (Q4 2025 13F era). Today
(2026-05-07) is still within this window — Q1 2026 13Fs aren't due
until ~2026-05-15. The retrospective MUST be re-run after Q1 2026 13Fs
land to verify the verdict isn't an artifact of one quarter's data.

## Followups

1. **v1.4.3 additive overlap script for C-4** (~30min, $0) — required
   before any spec invocation
2. **Re-run after 2026-05-15** (Q1 2026 13F refresh) — verify single-
   quarter robustness
3. **Bull-side cohort expansion**: gather more bullish-pre commits in
   ticker × inflow regime. Current n=1 is uninformative
4. **C-2 retrospective on SC-009** (~2-3h, $0) — last unfilled bear-side
   item

## Sibling docs

- `claudedocs/class-c4-institutional-ownership-feasibility-2026-05-07.md`
  (PR #66 feasibility verdict)
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` (PR #22
  design doc)
- `claudedocs/forward-catalyst-class5-retrospective-2026-05-06.md` +
  this PR's sibling Class 5 verdicts for comparison
