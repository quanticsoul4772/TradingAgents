# Spec 010 (Hybrid D) — bear-side calendar-boosted forward-catalyst filter retrospective

**Trigger**: PR #85 sweep refresh confirmed bear-side behavioral-additive
cases at n=5 across 5 distinct tickers (HON, LLY, MSFT, NVDA, WFC). Per
Constitution VIII v1.4.1 retrospective-FIRST pattern, build the
retrospective markdown BEFORE invoking `/speckit.specify` for Spec 010.

**Verdict (one line)**: **SKIP** — Spec 010 calendar-boost mechanism is
structurally PM-rating-gated. The behavioral-additive bear cohort
(n=5) has 4-of-5 cases with `pre_rating = Hold` (cannot suppress what
isn't bullish in the first place); the 1 remaining case (NVDA-04-24
`pre_rating = Overweight`) has `bear_case_priced_in = 0.55` already
above `T_bear = 0.50`, so Spec 007 bear's would-fire decision is
unchanged by the boost. Calendar-boost mechanism on bear-side has been
comprehensively tested across windows × magnitudes × directions and on
both operational and behavioral-additive cohorts; further specs in this
mechanism class are not viable.

## Methodological context

This retrospective formally closes the "Spec 010 (Hybrid D — bear-side
calendar-boosted forward-catalyst filter; analog of Spec 008 for bear
side)" candidate. The empirical kernel (n=5 ticker-distinct
behavioral-additive bear cases per `claudedocs/behavioral-additive-sweep-post-v1.4.6-ratification-2026-05-07.md`)
was the trigger for evaluation per Constitution VIII v1.4.0 sample-size
guidance.

The retrospective approach: rather than re-running the calendar-boost
sweep on a new cohort (which would replicate the prior null results
documented in `claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.md`
and the original Spec 008 bear-side retrofit), this analysis examines
the **structural compatibility** of the calendar-boost mechanism with
the behavioral-additive bear cohort.

## The 5 bear-side behavioral-additive cases

Per `scripts/behavioral_additive_sweep.py` post-v1.4.6 refresh:

| Ticker | Date | pm_rating | pre_rating | spec_007_bull | spec_007_bear | T_bear |
|---|---|---|---|---|---|---|
| HON | 2026-04-24 | Hold | Hold | 0.45 | **0.60** | 0.50 |
| LLY | 2026-04-24 | Hold | Hold | 0.62 | **0.55** | 0.50 |
| MSFT | 2026-04-24 | Hold | Hold | 0.55 | **0.65** | 0.50 |
| NVDA | 2026-04-24 | Hold | **Overweight** | 0.82 | **0.55** | 0.50 |
| WFC | 2026-04-17 | Hold | Hold | 0.45 | **0.70** | 0.50 |

**Key observations**:

1. **All 5 cases have `bear_case_priced_in > T_bear = 0.50`** — Spec 007
   bear's would-fire condition is already met at the base score for
   every case in the cohort.
2. **4 of 5 cases have `pre_rating = Hold`** — Spec 007 bear's actual
   fire decision is constrained: the filter only fires when
   `pre_rating ∈ {Buy, Overweight}` (the bear-priced-in case applies
   to bullish pre-ratings that should be suppressed). With Hold
   pre-rating, there's nothing for the bear-side filter to suppress.
3. **1 of 5 cases (NVDA-04-24) has `pre_rating = Overweight`** — Spec
   007 bear could theoretically fire here. Base bear_score = 0.55 > 0.50
   means it ALREADY would fire without any calendar boost.

## Structural argument: why Spec 010 cannot fire on this cohort

Spec 010 (Hybrid D) calendar-boost formula (analog of Spec 008's bull
formula): `effective_bear_score = bear_case_priced_in × (1 + magnitude × boost)`
where `boost = max(0, 1 - days_to_next_earnings / window)`.

The mechanism increases bear_score near earnings. Spec 007 bear then
compares effective_bear_score against T_bear to decide downgrade.

For Spec 010 to provide additional value over Spec 007 bear baseline,
it would need to either:
- **(a)** Move a base bear_score that's BELOW T_bear to ABOVE T_bear via
  the boost, AND have pre_rating ∈ {Buy, Overweight} for the fire to
  produce a downgrade. Net effect: additional fires that Spec 007 bear
  baseline missed.
- **(b)** Change a fire decision such that PM internalizes the
  contrarian logic differently and the filter's would-fire becomes
  operational. (This would be a v1.4.6 behavioral-additive case.)

**Path (a) fails on this cohort**: all 5 cases have base bear_score
already > T_bear. Boost does not move any score from "below threshold"
to "above threshold" because every score is already above. Boost is
redundant.

**Path (b) fails on this cohort**: 4 of 5 cases have pre_rating = Hold.
PM has already committed to no-bullish; there's nothing for any bear-
side filter to operationally suppress. The 1 NVDA case has
pre_rating = Overweight, but Spec 007 bear ALREADY would fire at base
score 0.55 — Spec 010 doesn't change Spec 007's would-fire decision,
just makes it more emphatically true. The behavioral-additive
interpretation requires a counterfactual where Spec 010 fires AND Spec
007 bear baseline does not — that counterfactual doesn't exist on this
cohort.

## Cross-evidence from prior retrospectives

The calendar-boost mechanism on the bear side has been tested
exhaustively prior to this retrospective:

1. **Original Spec 008 bear-side retrofit** (within `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`):
   tested SAME-DIRECTION boost (analog of Spec 008's bull) on the Spec
   007 bear operational fire cohort. Result: NEUTRAL at 14d (no boost
   effect at production T_bear=0.50), HURTS at 21d (-2.52 to -3.50pp
   net Δα).
2. **Hybrid C bear INVERTED retrospective** (`claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.md`):
   tested INVERTED-DIRECTION boost (decreases bear suppression near
   earnings — opposite of Spec 008's bull direction). Result: 0.00pp
   delta at every window × magnitude combination. SKIP verdict.

Both directions of calendar-boost on the bear side have failed on the
operational cohort. This retrospective adds the third closure: the
behavioral-additive bear cohort (n=5) is structurally incompatible with
the mechanism.

## Constitution VIII v1.4.0 forward-catalyst-class gate evaluation

Mechanical evaluation against the standard 3-criteria gate:

- **Discrim ≥ +5pp PRIMARY**: NOT EVALUABLE — no fires on this cohort.
- **Cohort hit rate ≥ 60%**: NOT EVALUABLE — no fires on this cohort.
- **Net Δα ≥ +0.5pp OR shadow-mode-first**: NOT EVALUABLE — no fires
  changes mean Δα = 0pp by definition. Shadow-mode-first criterion
  requires criteria 1+2 PASS, which requires fires; without fires,
  shadow-mode-first is also not applicable.

The gate cannot be applied because the mechanism produces zero fires
on the cohort. This is the structural-incompatibility outcome — not a
gate FAIL via insufficient performance, but a structural reason the
gate cannot operate.

## Constitution VIII v1.4.3 additive-to-existing-filter gate

Vacuous — no fires means no overlap with Spec 007 bear baseline. There's
nothing additive to evaluate.

## Constitution VIII v1.4.6 behavioral-additive 4th interpretation

The behavioral-additive sub-case applies when filter F's operational
fires appear redundant with existing portfolio fires BUT both correlate
with the same PM commit decisions. For this to apply to Spec 010:

- F (Spec 010) needs to have at least some hypothetical operational
  fires that overlap with existing portfolio fires.
- Spec 010 has ZERO operational fires on this cohort (per the
  structural argument above).

Without fires of any kind, the behavioral-additive interpretation
cannot apply. The 4th interpretation extends additive analysis but
cannot rescue a filter that produces no fires whatsoever.

## Verdict — SKIP

Spec 010 (Hybrid D — bear-side calendar-boosted forward-catalyst
filter) is **NOT spec-eligible** under any of:

- Constitution VIII v1.4.0 standalone gate (cannot be applied — 0 fires)
- Constitution VIII v1.4.3 additive gate (vacuous — 0 fires)
- Constitution VIII v1.4.6 behavioral-additive 4th interpretation (0
  fires precondition fails)

Per Constitution II discipline (one experiment per change) and
Constitution VI (Spec Before Structural Change), this retrospective
formally closes the calendar-boost-bear-side candidate. **Do not invoke
`/speckit.specify` for Spec 010.**

## Methodological lesson

The bear-side calendar-boost mechanism class is **closed**. Three
distinct evaluations (Spec 008 original retrofit, Hybrid C bear
INVERTED, this Spec 010 behavioral-additive analysis) all converge on
the same result: calendar boost cannot improve bear-side discrimination
because the bear-side empirical pattern is fundamentally different from
the bull-side pattern (per the original Hybrid C bear hypothesis: bear
cases tend to fade on rallies near earnings rather than crystallize).

**Future bear-side specs should explore non-calendar mechanism classes**.
Per the bear-side mechanism survey
(`claudedocs/bear-side-mechanism-exploration-2026-05-07.md`), C-4
(institutional ownership delta) is the SOLE spec-eligible bear-side
mechanism class identified — Spec X-1 implementation is the next
forward bear-side filter spec.

## Constitution VIII v1.4.1 retrospective-FIRST pattern adherence

This retrospective ships BEFORE any `/speckit.specify` invocation for
Spec 010, exactly as VIII v1.4.1 prescribes. The SKIP verdict is the
artifact that should accompany any future "why no Spec 010" question —
the structural argument is preserved in the corpus.

## Sibling docs

- `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md` —
  Spec 008 original retrofit (bull PASS, bear NEUTRAL/HURTS)
- `claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.md` —
  Hybrid C bear INVERTED retrospective (SKIP at all configs)
- `claudedocs/behavioral-additive-sweep-post-v1.4.6-ratification-2026-05-07.md` —
  source of the n=5 bear-side cohort
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` — survey
  showing C-4 is SOLE spec-eligible bear-side mechanism class
- `.specify/memory/constitution.md` Principle VIII v1.4.6 — behavioral-
  additive 4th interpretation governing this analysis

## Reproducibility

This retrospective is corpus-analytical, not LLM-cost. Re-runnable
verification:

```bash
python scripts/behavioral_additive_sweep.py 2>&1 | grep -A 10 "Spec 007 bear"
```

Should reproduce the 5-row bear-side behavioral-additive cohort. If
the cohort grows substantively (say, n≥15 with multiple cases at
pre_rating ∈ {Buy, Overweight}), re-evaluate the structural argument —
specifically check whether the new cases have base bear_score below
T_bear AND pre_rating bullish (the path-(a) condition). If yes,
re-evaluate Spec 010 viability per this retrospective's structural
framework.

Until such cohort growth, **SKIP stands**.
