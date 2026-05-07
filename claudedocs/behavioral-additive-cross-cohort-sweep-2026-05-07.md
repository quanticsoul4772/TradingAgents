# Cross-cohort behavioral-additive sweep — 2026-05-07

**Goal**: Test whether the L-8 behavioral-additive pattern (memory:
`reference_behavioral_additive_4th_interpretation.md`) is local to today's
small SC-009 probe (n=1 mechanism class) or generalizes across the corpus.

**Method**: Walk every `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json` and check, per mechanism class, whether the
filter's score crossed its firing threshold but pre_rating prevented
operational fire. Sweep script: `scripts/behavioral_additive_sweep.py`.

## Coverage caveat

Spec 003 went live 2026-05-04; spec 007 and spec 008 went live 2026-05-06.
Most of the 236-log corpus predates these specs, so instrumented coverage
is thin:

| Mechanism | Instrumented logs | % of corpus |
|---|---|---|
| Spec 003 (prose-density) | 10/236 | 4.2% |
| Spec 007 bull (LLM-extracted) | 15/236 | 6.4% |
| Spec 007 bear (LLM-extracted) | 15/236 | 6.4% |
| Spec 008 (calendar-boosted) | 15/236 | 6.4% |

Despite the thin coverage, the behavioral-additive density per
*instrumented* log is striking.

## Headline result: all 4 mechanism classes have evidence

| Mechanism class | Behavioral-additive cases | Per-instrumented-log rate |
|---|---|---|
| Spec 003 (prose-density) | 7 | 70% |
| Spec 007 bull (LLM-extracted) | 7 | 47% |
| Spec 007 bear (LLM-extracted) | 3 | 20% |
| Spec 008 (calendar-boosted) | 6 | 40% |

**Total**: 23 behavioral-additive cases across the instrumented sub-corpus.
**Distinct mechanism classes**: 4/4 — meets and exceeds the 3-mechanism-class
threshold from `reference_behavioral_additive_4th_interpretation.md` for
v1.4.4 codification consideration.

## Per-ticker × mechanism breakdown

| Ticker | Spec 003 | Spec 007 bull | Spec 007 bear | Spec 008 |
|---|---|---|---|---|
| AAPL | 2 | 2 | 0 | 2 |
| COP | 0 | 1 | 0 | 1 |
| INTC | 2 | 2 | 0 | 1 |
| MSFT | 2 | 1 | 1 | 2 |
| NVDA | 1 | 1 | 1 | 0 |
| WFC | 0 | 0 | 1 | 0 |

The pattern is concentrated in 6 tickers but distributed across all 4
mechanism classes. AAPL, INTC, and MSFT each demonstrate behavioral-additive
across 3+ mechanism classes (all bull-side classes for AAPL and INTC; full
quad-class for MSFT including bear).

## Three sub-patterns identified

### Sub-pattern 1: PM Hold + bull-priced-in scores high (the original L-8)

PM picks Hold; bull-priced-in score is well above T_bull. This is the case
documented in this morning's `spec-003-fire-pattern-on-sc-009-cohort` and
COP-04-24 in mid-flight diagnostic.

Examples:
- AAPL/2026-04-17: pm=Hold, pre=Hold, spec_003_percentile=100.0, spec_007_bull=0.75, spec_008_eff_bull=0.78
- COP/2026-04-24: pm=Hold, pre=Hold, spec_007_bull=0.65, spec_008_eff_bull=0.84
- MSFT/2026-04-17: pm=Hold, pre=Hold, spec_003_percentile=98.0, spec_007_bull=0.62, spec_008_eff_bull=0.66
- NVDA/2026-04-17: pm=Hold, spec_003_percentile=90.0
- AAPL/2026-05-06: pm=Hold, spec_003_percentile=100.0

### Sub-pattern 2: PM more-bearish-than-Hold + bull-priced-in scores high (NEW, expanded L-8)

PM picks **Underweight** (one step past Hold), bull-priced-in score still
above threshold. Cleaner signal than sub-pattern 1: PM didn't just abstain
(Hold), PM committed bearishly. The bull filter's contrarian logic is
present in PM's reasoning AND PM extends past it.

Examples:
- AAPL/2026-04-24: pm=Underweight, pre=Underweight, spec_007_bull=0.75, spec_008_eff_bull=0.96
- INTC/2026-04-17: pm=Underweight, pre=Underweight, spec_003_percentile=90.0, spec_007_bull=0.88, spec_008_eff_bull=1.0 (clamped)
- INTC/2026-04-24: pm=Underweight, pre=Underweight, spec_003_percentile=90.0, spec_007_bull=0.85, spec_008_eff_bull=0.85

This expands the L-8 framing: behavioral-additive isn't just "PM internalizes
the filter's logic AND would have abstained." It's "PM internalizes the
filter's logic AND the PM's commit decision is consistent or stricter than
the filter's would-be suppression."

### Sub-pattern 3: PM Hold + bear-priced-in scores high (BEAR-SIDE behavioral-additive)

PM picks Hold; bear-priced-in score is above T_bear. PM passed up a
bullish commit on a ticker where the LLM thinks the bear case is also
priced in — i.e. the consensus is "everyone has digested both sides;
no edge to picking either direction."

Examples:
- MSFT/2026-04-24: pm=Hold, pre=Hold, spec_007_bear=0.65 (> T_bear=0.50)
- NVDA/2026-04-24: pm=Hold, pre=Overweight, spec_007_bull=0.82, spec_007_bear=0.55. **THIS IS A FILTER FIRE**: pre=OW, spec_007_bull=0.82 well above T_bull. The bull filter actually fired here, so this isn't purely behavioral-additive — but the bear_score crossing T_bear simultaneously is independent confirmation.
- WFC/2026-04-17: pm=Hold, pre=Hold, spec_007_bear=0.7

NVDA-04-24 is interesting: pre=Overweight downgraded to Hold, with bull
filter firing AND bear-priced-in score independently high. Both filters
agree this is a both-sides-priced-in row. This is the empirical kernel
for the **Hybrid D** candidate from yesterday's bear-side mid-flight
diagnostic F-4 finding.

## Implications

### Implication 1: L-8 codification readiness MET

We have evidence across 4 mechanism classes (vs. earlier 2) and across 6
tickers (vs. earlier 3 NVDA/MSFT/AAPL). Per
`reference_behavioral_additive_4th_interpretation.md`'s 3-mechanism-class
deferral rule, the codification threshold is met. Constitution v1.4.4
amendment for Principle VIII (formalize behavioral-additive as 4th case)
can be drafted.

**Caveat**: small sample sizes within each mechanism class. Spec 007 bear
has only n=3 cases. The codification should acknowledge "evidence-met but
sample-thin" and tie codification to ongoing instrumentation density rather
than committing to permanent-default until n grows.

### Implication 2: Hybrid D ("both-sides-priced-in") empirical motivation

NVDA-04-24 + MSFT-04-24 + WFC-04-17 + COP-04-24 + COP-04-17 (where bear=0.50
sits at boundary) all show simultaneous bull-and-bear-priced-in conditions.
A future Hybrid D filter could key on `max(bull_score, bear_score) > T_combined`
or `(bull_score + bear_score) > T_sum` to catch the "consensus exhaustion"
cohort. Empirical n is currently too thin (~5 candidate cases) to retrospect,
but the design framing has motivation now.

### Implication 3: PM is NOT just an aggregator — it's a consensus-validator

The 4-mechanism-class density of behavioral-additive cases suggests PM is
doing something operationally MORE than synthesizing the analyst+debate
ensemble. PM appears to be **validating consensus signals** — when
prose-density, LLM-extracted bull, AND calendar-aware all flag "bull case
priced in," PM picks Hold or bearish even though no filter operationally
fires. PM's Calibrated Abstention (Constitution VII) has internalized a
multi-mechanism contrarian logic.

This is a STRONGER claim than the original L-8 framing (which was
"PM-as-implicit-Spec-003"). The right framing is closer to
**PM-as-multi-mechanism-validator**: PM's Hold/bearish commits on
behavioral-additive rows correlate with the *agreement* of ≥2 contrarian
mechanism classes, not any single one.

### Implication 4: SC-009 verdict context

Of the 23 behavioral-additive cases, ~15 are in the SC-009 cohort dates
(2026-04-17 / 2026-04-24). This explains the high Hold rate from this
morning's mid-flight diagnostic: PM is operationally implementing a
multi-mechanism contrarian gate that pre-empts spec 007/008 bull-side
fires. The Hold-rate is a feature, not a bug — it's how Constitution VII
manifests when multiple contrarian signals align.

This also tightens the SC-009 verdict interpretation: gate-2 (n_fired ≥ 8)
is structurally hard to hit on this cohort because the filter chain's
contrarian logic is largely already absorbed by PM. Alt gate-1 (suppressed
α direction) becomes the dominant gate.

## Followups (deferred, listed in priority order)

1. **Draft Constitution v1.4.4 amendment** for L-8 behavioral-additive case
   formalization — text-only, no flip yet. ~45min, $0.
2. **Hybrid D feasibility**: design doc + retrospective sketch on the ~5
   both-sides-priced-in cases. Cohort too small for a proper retrospective
   today; defer until cohort grows to n≥15. ~30min, $0.
3. **PM-as-multi-mechanism-validator memory polish**: update
   `reference_behavioral_additive_4th_interpretation.md` to reflect the
   richer 4-mechanism-class framing. ~15min, $0.
4. **SC-009 final ANALYSIS.md framing**: explicitly call out that gate-2
   is structurally pre-empted by PM internalization → alt gate-1 is the
   dominant gate. Defer until backtest finishes.

## Sibling docs

- `claudedocs/spec-003-fire-pattern-on-sc-009-cohort-2026-05-07.md` —
  morning's first behavioral-additive evidence (Spec 003 only, n=4)
- `claudedocs/sc-009-bear-side-mid-flight-diagnostic-2026-05-07.md` —
  mid-flight COP+INTC bear-side diagnostic; F-3 introduced Spec 007
  mechanism-class evidence
- `memory/reference_behavioral_additive_4th_interpretation.md` — L-8
  pattern memory; 3-mechanism-class deferral rule
- `scripts/behavioral_additive_sweep.py` — reproducible sweep harness
  (run anytime to refresh the count as new instrumented logs accumulate)
