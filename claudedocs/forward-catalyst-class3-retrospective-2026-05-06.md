# Class 3 forward-catalyst retrospective — 2026-05-06

**Hypothesis**: an LLM-extracted feature scoring how widely the bull/bear case is
ALREADY ACCEPTED by the market can discriminate cohort losers (where the framework
committed in the direction the market had already absorbed) from non-cohort winners
(where the framework's commit aligned with under-priced movement).

**Scored**: 94 commits (cohort A bullish ticker_weak + cohort B bearish ticker_strong + bull/bear winner controls + Hold baselines)
**LLM**: claude-haiku-4-5
**Cost**: ~$0.19 (Haiku ceiling)

## Per-sample-class mean scores

If the hypothesis holds:
  - cohort_a (bullish ticker_weak target) should have HIGH mean bull_case_priced_in
  - cohort_b (bearish ticker_strong target) should have HIGH mean bear_case_priced_in
  - control_bull_winner should have LOW mean bull_case_priced_in
  - control_bear_winner should have LOW mean bear_case_priced_in

| sample_class | n | mean bull_priced_in | mean bear_priced_in |
|---|---|---|---|
| `cohort_a_bull_target` | 27 | 0.718 | 0.522 |
| `cohort_b_bear_target` | 18 | 0.684 | 0.602 |
| `control_bear_winner` | 19 | 0.705 | 0.609 |
| `control_bull_winner` | 20 | 0.670 | 0.628 |
| `control_hold` | 10 | 0.721 | 0.531 |

## Bull-side threshold sweep

Filter fires when `bull_case_priced_in > T_bull`. Net Δα = kept_α − baseline_α (positive means filter helped by removing losers). Discrimination = noncohort_α − cohort_α among fires (positive means filter correctly catches cohort losers and not non-cohort winners; primary gate per design doc §5).

| T_bull | n_fired | kept α | fired α | net Δα | cohort hit rate | discrim |
|---|---|---|---|---|---|---|
| 0.50 | 45 | +3.74% | -0.25% | +3.81pp | 96.3% | +11.44pp |
| 0.60 | 44 | +9.04% | -0.70% | +9.12pp | 96.3% | +10.70pp |
| 0.70 | 33 | -0.38% | +0.05% | -0.30pp | 85.2% | +17.54pp |
| 0.80 | 0 | -0.08% | +nan% | +0.00pp | 0.0% | +nanpp |

## Bear-side threshold sweep

Filter fires when `bear_case_priced_in > T_bear`. For BEAR commits, HIGHER α means the bear call was wrong (ticker rallied). Filter HELPS by removing high-α commits. Net Δα = baseline_α − kept_α (positive = filter helps). Discrimination = cohort_α − noncohort_α (positive = filter catches rallying cohort tickers and not actual-loser non-cohort).

| T_bear | n_fired | kept α | fired α | net Δα | cohort hit rate | discrim |
|---|---|---|---|---|---|---|
| 0.50 | 32 | +22.73% | +10.67% | -10.44pp | 83.3% | +26.77pp |
| 0.60 | 17 | +12.07% | +12.57% | +0.23pp | 55.6% | +20.06pp |
| 0.70 | 7 | +11.54% | +15.54% | +0.76pp | 16.7% | +36.95pp |
| 0.80 | 1 | +12.61% | +1.10% | -0.31pp | 0.0% | +nanpp |

## Verdict — Class 3 with Haiku is BORDERLINE; recommend Opus rerun before spec

Per `claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md` §5 the proposed gate is:

  1. **Discrimination ≥ +5pp in correct direction (PRIMARY)**
  2. Cohort hit rate ≥ 60%
  3. Net Δα ≥ +0.5pp OR shadow-mode-first

### Criterion 1 (discrimination) — STRONG PASS on both sides

Bull: +10.70pp at T=0.60 / +17.54pp at T=0.70. Bear: +20.06pp at T=0.60 / +36.95pp at T=0.70. The LLM-extracted feature DOES discriminate cohort losers from similar-pattern winners — fires-of-cohort have systematically lower α than fires-of-non-cohort. This is the criterion spec 005 candidate FAILED catastrophically (-15pp wrong-sign). Class 3 PASSES the primary gate decisively.

### Criterion 2 (cohort hit rate) — bull-side strongly passes; bear-side marginally fails

Bull T=0.60: **96.3%** (26 of 27 cohort caught). Bull T=0.70: **85.2%** (23 of 27). Both pass.
Bear T=0.60: **55.6%** (10 of 18). Just below the 60% gate. Bear T=0.70: 16.7% (3 of 18). Fails badly.

The bear cohort doesn't cluster at high `bear_case_priced_in` scores because **per-class means are essentially identical**: cohort_b bear=0.602 vs control_bear_winner bear=0.609. The LLM rates bear-cohort and bear-winner commits the same. The mechanism doesn't separate them on this feature.

### Criterion 3 (net Δα) — bull-side passes BUT with caveat; bear-side fails

Bull T=0.60: +9.12pp (very strong). Bull T=0.70: -0.30pp. Bear T=0.60: +0.23pp (just below). Bear T=0.70: +0.76pp.

**The bull T=0.60 +9.12pp number is suspect** — the filter fires on 44 of 47 bull commits (94% fire rate). The "kept α = +9.04%" is the mean of only 3 commits, which is essentially noise. The discrimination metric is the more reliable signal because it compares like-for-like (cohort fires vs non-cohort fires); net Δα at high fire rates collapses to "kept population is 3 outliers."

### Per-class means — the deeper concern

| sample_class | bull_priced_in | bear_priced_in |
|---|---|---|
| cohort_a (bull target) | 0.718 | 0.522 |
| cohort_b (bear target) | 0.684 | **0.602** |
| control_bull_winner | 0.670 | 0.628 |
| control_bear_winner | 0.705 | **0.609** |
| control_hold | 0.721 | 0.531 |

Cohort_a vs control_bull_winner on bull_priced_in: gap = **+0.048** (5pp).
Cohort_b vs control_bear_winner on bear_priced_in: gap = **−0.007** (essentially zero).

The bull side has a small but real separation; the bear side has none. The discrimination column passes because of EDGE-case fires (the few high-bear-priced-in commits happen to be cohort) rather than systematic separation.

### Score distribution — too tight

bull_priced_in: mean=0.699, std=0.071 — 75% of commits sit in [0.680, 0.720]. Threshold tuning on a 4pp band is inherently brittle.
bear_priced_in: mean=0.578, std=0.120 — wider distribution but cohort doesn't cluster at the high end.

**Haiku appears to be saturating the score** — almost everything reads as "moderately to highly priced in" because the analyst reports for ANY ticker contain bull/bear arguments worth discussing. The model isn't discriminating well between "thoroughly priced in" and "moderately priced in."

## Operational outcome

**Three options**, in decreasing preference:

### Option A (recommended): Opus rerun before any spec

Re-run the same retrospective with `claude-opus-4-7` instead of Haiku. Cost ~$2 (Opus is ~10× Haiku). Hypothesis: Opus produces a wider, more discriminating score distribution because it parses subtler "consensus vs contrarian" framings.

If Opus passes the gate cleanly (discriminative + bear-side hit rate ≥ 60% + non-suspect net Δα at meaningful fire rates) → invoke `/speckit.specify`.

If Opus also produces the same tight distribution + marginal bear-side → fall back to Option C.

### Option B: Spec with shadow-mode-first condition (bull-side only)

The bull side passes the spec gate per the design doc (criteria 1+2 strong; criterion 3 either passes at T=0.60 with caveat or fails at T=0.70). Per §5 design-doc guidance, this permits the spec WITH shadow-mode-first condition (observe n≥20 fresh propagates before active-mode flip).

Risk: Haiku score distribution is too tight to be operationally useful as a default-on filter. The shadow-mode observation period would essentially be a longer-form re-validation of what this retrospective already shows: the signal is real but weak.

### Option C: Skip Class 3 entirely; consider Class 2 (options-IV) as fallback

Per design doc §4, if Class 3 doesn't pass cleanly, Class 2 (options-implied volatility) is the next candidate. Different mechanism class — forward-looking via options pricing rather than LLM synthesis. Cost ~$0-5 + ~5h. Could catch Cohort B (the +28% rally cohort) where options markets often pre-price expected upside.

## Decision

**Recommend Option A**: spend ~$2 + ~30 min to re-run with Opus before committing to Option B or C. If Opus shows the same tight distribution + marginal bear-side, fall through to Option C. The Class 3 mechanism class isn't ruled out; the Haiku-specific saturation might be the primary issue.

**No spec invocation today.** Today's work delivered the negative-but-actionable finding that the Class 3 mechanism passes the discrimination gate but produces too-tight scores at Haiku-level model capability. Captured for follow-up.

## What this DOES validate

- The forward-catalyst-aware mechanism class IS tractable in principle — discrimination at +10-37pp is real signal, well above the design doc's +5pp gate
- The cohort A signal (bullish ticker_weak) IS detectable at the 5pp-mean-separation level
- The retrospective methodology works — pre-spec validation is cheap and informative ($0.19 + ~25 min runtime here)

## What this DOES NOT validate

- Haiku as the operational LLM for this feature class — score saturation is too tight for clean threshold tuning
- The cohort B signal (bearish ticker_strong) — per-class means are essentially equal between cohort and control on `bear_case_priced_in`
- The +9.12pp net Δα at T=0.60 bull side — almost-everything-fires regime makes the "kept α" a 3-commit noise sample

## Constitution VIII alignment

This retrospective followed Constitution VIII discipline: pre-spec validation BEFORE any `/speckit.specify` invocation. It found borderline-but-not-clean signal. Per design doc §5 + Constitution VIII spirit, the spec should NOT be written yet — re-run with Opus first, then re-evaluate. **The pre-spec retrospective methodology itself is now battle-tested across 4 mechanism classes** (spec 004, spec 006, spec 005-candidate, Class 3), all of which produced actionable verdicts at $0-2 cost vs ~6-8h spec-writing avoided.

## Reproducibility

```
python scripts/forward_catalyst_class3_retrospective.py
```

Reads `claudedocs/sector-alpha-attribution-2026-05-06.csv` for cohort + controls;
loads cached state logs from `~/.tradingagents/logs/<ticker>/...`; calls Haiku via
`tradingagents.llm_clients.factory.create_llm_client`; saves per-row scores to
`claudedocs\forward-catalyst-class3-retrospective-2026-05-06.csv`. Resume-on-rerun supported (only re-scores rows missing from CSV).
Cost: ~$0.10-0.20 in Haiku at default ~95-commit sample.
