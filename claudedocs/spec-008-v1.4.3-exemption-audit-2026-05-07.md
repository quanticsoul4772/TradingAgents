# Spec 008 Constitution v1.4.3 exemption audit — 2026-05-07

**Trigger**: Constitution v1.4.3 (additive-to-existing-filter gate) was codified 2026-05-06 late-evening AFTER Spec 008 was already merged + tagged at v0.8.0-spec-008. Question: does Spec 008 need to retroactively pass the v1.4.3 gate, or is it exempted?

**Verdict**: **EXEMPTED** by the v1.4.3 trigger criteria. Spec 008 is correctly grandfathered.

## v1.4.3 trigger criteria (verbatim from constitution)

> **Trigger criteria** (which retrospectives this gate applies to):
>
> - Yes: ANY new bull-side filter retrospective that PASSES the standalone Constitution VIII gate AND there is at least one existing default-active bull-side filter
> - Yes: ANY new bear-side filter retrospective that PASSES the standalone Constitution VIII gate AND there is at least one existing default-active bear-side filter
> - No: A filter targeting a direction with NO existing default-active filter in the portfolio (the additive comparison is vacuous)
> - No: A filter framed as a STRICT REPLACEMENT for an existing filter (different decision tree; out of scope for additive gate)
> - **No: HYBRID filters whose retrospective ALREADY uses the "improves over underlying filter" criterion (e.g., Spec 008 Hybrid C — already covered by the v1.4.2 magnitude-fungibility section's adjacent principle of "must improve at least one criterion vs underlying filter")**

The 5th bullet (No) explicitly names **Spec 008 Hybrid C** as the canonical example of the hybrid-filter exemption.

## Why Spec 008 fits the hybrid-filter exemption

1. **Mechanism class**: Hybrid C is structurally INSIDE Spec 007 (per FR-014 + plan.md "Constitution Check" section). It's not a parallel filter in the PM hook chain; it modulates Spec 007's `bull_case_priced_in` score before Spec 007's fire decision. Disabling Spec 008 = boost coefficient zero, returning Spec 007's baseline behavior.

2. **Retrospective improvement criterion already applied**: Spec 008's retrospective (`claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`) explicitly evaluates "Hybrid C must improve at least one criterion vs underlying filter (Class 3 alone)" — this is the "improves over underlying filter" gate. The retrospective verdict (window=14d, magnitude=0.5x):
   - Bull-side improvement vs Class 3 alone: +3.35pp net Δα
   - Bull-side cohort hit: +3.7pp (88.9% → 92.6%)
   - Bull-side discrim: -3.13pp (+14.43pp → +11.30pp; lower but still ≥+5pp gate)

   The "≥ +0.5pp net Δα improvement" sub-criterion of v1.4.3 (translated for hybrid filters) is already PASSED at +3.35pp.

3. **Default-off launch reduces risk**: Spec 008 ships default-OFF per FR-007 + SC-009 live-mode A/B ablation requirement. Even if the v1.4.3 retroactive analysis were to fail, default-off behavior means no operator is exposed without explicit opt-in. The SC-009 live ablation IS the v1.4.3-spirit additive validation, just delayed for forward-cohort evidence.

## Verification: would Spec 008 PASS the additive gate if applied retroactively?

Even though exempted, sanity-check whether Spec 008 WOULD pass v1.4.3 if treated as a parallel filter (it's not; this is a thought experiment).

For "Spec 008 Hybrid C" as a parallel filter to "Spec 007 Class 3":
- Their fire decisions are NOT independent — Spec 008's effective_bull_score = base × (1 + magnitude × boost), so when Spec 007 fires (base > 0.60), Spec 008 ALSO fires (effective ≥ base > 0.60). When Spec 007 doesn't fire (base ≤ 0.60), Spec 008 might still fire if base × (1 + boost) > 0.60.
- Therefore: Spec 008 fire-set ⊇ Spec 007 fire-set (Spec 008 is a strict superset under any positive boost).
- Union(007, 008) = Spec 008 fire-set
- Intersection(007, 008) = Spec 007 fire-set

Per the v1.4.3 gate (one of):
1. Net Δα improvement ≥ +0.5pp for the union over the best existing filter alone:
   - Union = Spec 008 = +5.58pp (kept α at boosted threshold) vs Spec 007 baseline = +2.24pp
   - Improvement: +3.34pp ≥ +0.5pp → **PASS**
2. Cohort hit improvement ≥ +5pp: +3.7pp < +5pp → not satisfied
3. False-positive-rate improvement ≥ -10pp for the intersection: intersection = Spec 007 alone = no improvement → not satisfied

**Spec 008 PASSES criterion 1 of the v1.4.3 gate** (with margin). The retroactive verdict is consistent with the proper exemption: hybrid filters that improve their underlying filter's net Δα by ≥+0.5pp are valid spec invocations.

## Operational implication

No action required. Spec 008 v0.8.0-spec-008 + the forthcoming v0.8.1-spec-008.5 latency benchmark continue to be the production state. The forthcoming Spec 008 SC-009 live A/B ablation experiment (`experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/`) will provide the FORWARD-validation that v1.4.3 procedurally implies.

If a future operator considers extending Hybrid C with another mechanism (e.g., Hybrid D = Class 3 × Class 5 — the spec 010 path that was retroactively SKIPPED), the v1.4.3 trigger criteria SHOULD apply to that new spec's pre-spec retrospective. Hybrid D would not be exempted — it's a NEW underlying-filter combination, not a modulation of Spec 008.

## Cost

\$0 (pure documentation audit).
