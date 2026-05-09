# Spec 011 first-invocation candidate audit — 2026-05-09

**Trigger**: reasoning_decision rank-9 (0.63 score). Audits whether today's 4 retrospectives (or earlier accumulated state-log evidence) surface a candidate for Spec 011's first-invocation pattern (Constitution v1.4.6 behavioral-additive escape clause).

**Cost**: $0. ~10 min wall-clock.

## Spec 011 first-invocation criteria

Per `reference_speckit_6pr_workflow_pattern.md` + `reference_behavioral_additive_4th_interpretation.md` + Constitution VIII v1.4.6 (codified by Spec 011, PR #136):

A filter is a Spec 011 first-invocation candidate if and only if it satisfies ALL:

1. **PASSES standalone v1.4.0 gate** (net Δα ≥ +0.5pp; cohort hit ≥ 40%) — mechanism is empirically valid
2. **FAILS v1.4.3 additive gate** (overlap with existing default-active filter prevents shipping as additional filter)
3. **The failure mode is structural** — PM has already internalized the contrarian signal across the cohort (e.g., pre_rating already Hold when filter would fire), NOT mechanistic mismatch
4. **Behavioral-additive evidence exists** — ≥1 documented case of PM-temporal-learning OR PM-multi-mechanism-validator behavior on the cohort

## Audit of today's 4 retrospectives

| PR | Retrospective | Verdict | Spec 011 candidate? |
|---|---|---|---|
| #193 | Class 4 macro BEAR | PASS standalone + PASS additive | NO — clean PASS, became Spec 012 |
| #202 | Class 5 BULL fundamentals-delta (re-run) | PASS standalone, FAIL additive | **PARTIAL FIT** — see analysis below |
| #203 | Class 4 macro BULL | FAIL standalone (-2.25pp) at every threshold | NO — fails before reaching v1.4.3 gate |
| #205 | Local-high BULL | TECHNICAL PASS at n=2 floor only | NO — sample-size limited (n=2 < n=8 floor); not behavioral-additive |

## Class 5 BULL — partial fit analysis

Class 5 BULL is the only candidate that PARTIALLY fits Spec 011 criteria:

- ✅ Criterion 1: PASSES standalone (n=47, discrim +11.92pp, hit 96.3%, net Δα +4.37pp)
- ✅ Criterion 2: FAILS v1.4.3 additive (89% overlap with Spec 007; union HURTS net Δα by -4.09pp; 31 of 41 Class 5 fires already caught by Spec 007)
- ❌ Criterion 3: failure mode is **mechanistic correlation** (Class 5 EPS-surprise + Spec 007 LLM-extracted "bull case priced in" signal the same underlying reality), NOT PM-temporal-learning. The v1.4.3 SKIP rationale is mechanism-redundancy, not behavioral-additive PM-internalization.
- ❌ Criterion 4: no documented behavioral-additive evidence (PM didn't pre-Hold the Class 5 cohort; PM committed Buy/OW pre-Spec-007, then Spec 007 suppressed; Class 5 then catches a near-identical subset).

**Verdict**: Class 5 BULL is a 2-of-4 PARTIAL fit. NOT a Spec 011 first-invocation candidate per the structural criterion.

## Audit of accumulated state-log evidence (passive accumulation)

Per the ROADMAP Open Questions row:

> Can the behavioral-additive escape clause (Constitution v1.4.6 + Spec 011) ever be invoked, or is bear-side mechanism survey COMPLETE making it dormant? | Future state-log accumulation may reveal new bull-side filter candidates that fail v1.4.3 actual-fires gate but pass v1.4.6 counterfactual gate. Bear-side survey is closed (6/6 evaluated, only C-4 spec-eligible). | $0 (passive — depends on accumulated state logs) | **deferred (Spec 011 first invocation)**

Reviewed accumulated state-log evidence in:
- `claudedocs/behavioral-additive-sweep-post-v1.4.6-ratification-2026-05-07.md` (4/4 mechanism-class behavioral-additive cases; ALL POST-FILTER-RATIFICATION)
- `reference_pre_rating_temporal_learning.md` (AMZN-04-17 → AMZN-04-24 case; n=1 in-flight)
- `reference_behavioral_additive_4th_interpretation.md` (cross-cohort sweep finding 23 cases across all 4 mechanism classes)

These accumulated cases ARE behavioral-additive observations, but they're for filters that ARE already production-default (Spec 003 + Spec 007 bull + Spec 007 bear + Spec 008). They demonstrate PM-internalization of CURRENT filter mechanisms, not a NEW filter candidate to draft via Spec 011.

**Verdict**: no accumulated state-log evidence surfaces a NEW filter candidate eligible for Spec 011 first-invocation today.

## Net audit verdict

**Spec 011 first-invocation: NO CANDIDATE FOUND.** The audit confirms the ROADMAP Open Questions row's existing "deferred" status.

The bear-side mechanism survey CONCLUDED at 6/6 in 2026-05-07; bull-side hasn't surfaced a Spec 011-eligible candidate at today's evidence basis. Future re-evaluation triggers:

1. **Bull-cohort growth** to 150+ commits would surface new filter candidates that might fail v1.4.3 additive (creating Spec 011 candidates) — same trigger as local-high re-evaluation
2. **A new mechanism class** outside the 6 bear-side + 6 spec-008-design-doc Class N classes might surface candidates
3. **Multi-window SC-003 replication** ($40 T3) would expand cohort sizes across multiple filter-eligibility checks

## Constitution adherence

- ✅ I (Save Everything): this audit memo
- ✅ III (Stay Cheap): $0 LLM
- ✅ VIII v1.4.1: audit precedes any Spec 011 invocation; no spec drafting triggered

## Cost

$0 LLM. ~10 min wall-clock.

## What ships

`claudedocs/spec-011-candidate-audit-2026-05-09.md` (this audit memo).

## Cross-references

- `specs/011-behavioral-additive-procedure/` (Spec 011 itself; PR #136)
- Memory: `reference_behavioral_additive_4th_interpretation.md`
- Memory: `reference_bear_side_mechanism_survey_complete.md` (bear-side closed)
- Memory: `reference_pre_rating_temporal_learning.md` (AMZN n=1 case)
- ROADMAP.md Open Questions row for Spec 011 first invocation (deferred status reaffirmed by this audit)
- Constitution VIII v1.4.6 (behavioral-additive 4th interpretation)
- 4 retrospectives shipped today (PRs #193 + #202 + #203 + #205)
