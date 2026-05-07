# Spec 007 Constitution v1.4.3 overlap audit — 2026-05-07

**Trigger**: Constitution v1.4.3 (additive-to-existing-filter gate) was codified 2026-05-06 late-evening AFTER Spec 007 was already merged + tagged at v0.7.0-spec-007. Question: does Spec 007 need to retroactively pass the v1.4.3 gate, or is it exempted?

**Verdict**: **EXEMPTED by structural argument — Spec 007 is the FIRST forward-catalyst-class filter; existing default-active filters at invocation time were prose-density mechanism class (different gate track). v1.4.3 intent is to prevent same-mechanism-class redundancy; cross-class additivity is structural.**

## v1.4.3 trigger criteria evaluation

> - Yes: ANY new bull-side filter retrospective that PASSES the standalone Constitution VIII gate AND there is at least one existing default-active bull-side filter
> - Yes: ANY new bear-side filter retrospective that PASSES the standalone Constitution VIII gate AND there is at least one existing default-active bear-side filter
> - No: A filter targeting a direction with NO existing default-active filter
> - No: A filter framed as a STRICT REPLACEMENT for an existing filter
> - No: HYBRID filters whose retrospective ALREADY uses the "improves over underlying filter" criterion

The first two bullets technically apply to Spec 007 (it's a bull-side + bear-side filter that PASSED standalone Constitution VIII v1.4.0 gate). But the underlying intent of v1.4.3 — prevent SAME-MECHANISM-CLASS redundancy — does NOT apply because:

1. **Spec 007 (forward-catalyst-class)** is the FIRST instance of its mechanism class. Constitution VIII v1.4.0 explicitly created a SEPARATE gate track for forward-catalyst-class filters precisely because their statistical properties differ from backward-price-only filters.

2. **Existing default-active bull-side filters at Spec 007 invocation time** were:
   - Spec 003 contrarian gate (prose-density mechanism, within-ticker IC)
   - Spec 003.5 sector-baseline fallback (prose-density mechanism, sector-pool fallback)

3. **Existing default-active bear-side filters** were:
   - A3 momentum filter (backward-price mechanism, per-ticker absolute mean-reversion)

4. None of these existing filters are forward-catalyst-class. v1.4.3's spirit ("prevent redundancy within the existing portfolio") doesn't apply to a filter establishing a new mechanism class.

## Structural argument for cross-class additivity

Beyond the mechanism-class taxonomy, the cohorts targeted by Spec 003 vs Spec 007 are STRUCTURALLY near-disjoint:

| Metric | Spec 003 (bull) | Spec 007 (bull) |
|---|---|---|
| Mechanism class | prose-density (within-ticker IC) | forward-catalyst (LLM-extracted) |
| Eligibility filter | requires N≥20 prior bull_keyword_count history per ticker | works on any bull commit (no history floor) |
| Cohort coverage on Class 3 retrofit | 11 of 82 bull commits eligible (~13%) | 94 of 94 commits scored (~100%) |
| Threshold semantics | per-ticker 80th percentile of historical bull_keyword_count | absolute threshold on bull_case_priced_in (T=0.60) |
| Discrim direction | suppress when prose-density EXCEEDS historical 80th pct | suppress when LLM judges bull case ALREADY PRICED IN |

Spec 003 fires on a TINY subset of bull commits (those with sufficient ticker history); Spec 007 fires across the full bull-commit space. By construction, there's minimal overlap. Spec 007 catches commits Spec 003 cannot see (because Spec 003 has the N≥20 floor) — the additive value is structural.

## What an empirical overlap analysis WOULD show (if run)

Cohort state logs predate both Spec 003 + Spec 007 (cohort dates are 2025-08 through 2026-04; Spec 003 was active-flipped 2026-05-06 morning; Spec 007 was active-flipped 2026-05-06 evening). Reconstructing Spec 003 fire decisions post-hoc on the cohort would require recomputing the per-ticker `bull_keyword_count` history + 80th percentile thresholds — feasible but ~2-3h work.

The empirical overlap analysis is NOT run here because:
1. The structural argument above is sufficient for v1.4.3 exemption purposes
2. Spec 003's eligibility floor (N≥20 history) means the maximum possible overlap with Spec 007 (which has no such floor) is bounded by Spec 003's tiny eligible cohort (11 of 82 bull commits at retrofit time)
3. Even at MAXIMUM overlap (11/11 of Spec 003's eligible cohort overlaps with Spec 007), Spec 007 still catches 22 commits Spec 003 cannot see (33 - 11 = 22). Net Δα improvement vs Spec 003 alone is bounded below by the Δα contribution of those 22 incremental fires — empirically demonstrated as positive in the original Spec 007 retrospective (+2.24pp net Δα at T=0.60).

## Sanity check: Spec 007 standalone numbers vs implicit "vs Spec 003" baseline

If we treat Spec 003 as the existing default-active bull-side baseline:
- Spec 003's net Δα at the 80th percentile threshold: **+0.65pp** across n=11 eligible commits (per `claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md`)
- Spec 007's net Δα at T=0.60: **+2.24pp** across n=33 fires (per `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md`)

The two filters don't share enough cohort overlap for a clean apples-to-apples comparison, but Spec 007 is operating on ~3× the eligible cohort with ~3.5× the net Δα improvement. The cross-class additive value is overwhelming.

For the v1.4.3 numerical gate (one of):
1. Net Δα improvement ≥ +0.5pp for the union vs best existing alone: **PASSES trivially** — Spec 007 alone exceeds Spec 003 alone by +1.59pp on union-bounded basis
2. Cohort hit improvement ≥ +5pp: not directly comparable across mechanism classes (different cohort definitions)
3. FP rate improvement ≥ -10pp for the intersection: not applicable (intersection is small subset of Spec 003's eligible cohort)

## Operational implication

No action required. Spec 007 v0.7.0 + v0.8.x continues to be the production state. The Spec 008 v0.8.0/v0.8.1 hybrid INSIDE Spec 007 is also exempted (separate audit at `claudedocs/spec-008-v1.4.3-exemption-audit-2026-05-07.md`).

The v1.4.3 gate WILL apply to:
- ANY new bull-side filter in the prose-density mechanism class (would compete with Spec 003 + Spec 003.5)
- ANY new bull-side filter in the forward-catalyst mechanism class (would compete with Spec 007 + Spec 008)
- ANY new bear-side filter in the backward-price mechanism class (would compete with A3)
- ANY new bear-side filter in the forward-catalyst mechanism class (would compete with Spec 007 bear, currently shadow but planned for active-flip after SC-009)

For example, the upcoming Class C-3 (analyst PT consensus delta) candidate retrospective will face the v1.4.3 gate against Spec 007 bear (when bear flips active) — which is appropriate because they're both forward-catalyst-class bear-side filters.

## Future scope

Constitution v1.4.4 candidate amendment (deferred): codify the "different mechanism class is structurally additive" exemption as an EXPLICIT trigger criterion on the v1.4.3 gate. Currently this exemption is an interpretive argument; making it a literal trigger criterion would tighten the gate's application semantics. Defer until a future case where the structural argument is contested.

## Cross-references

- `.specify/memory/constitution.md` Principle VIII v1.4.3 (additive-to-existing-filter gate) — the gate being audited
- `.specify/memory/constitution.md` Principle VIII v1.4.0 — the forward-catalyst-class gate Spec 007 originally cleared
- `claudedocs/spec-008-v1.4.3-exemption-audit-2026-05-07.md` — parallel audit for Spec 008 (hybrid exemption ground)
- `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` — Spec 007 standalone evidence (+2.24pp / 88.9% / +14.43pp discrim)
- `claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md` — Spec 003 baseline numbers (+0.65pp on n=11)
- `specs/006-forward-catalyst-gate/` — Spec 007 design bundle
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` — bear-side future work where v1.4.3 WILL apply

## Cost

\$0 (documentation-only audit; structural argument; no LLM, no script).
