# Bear-side mechanism class survey RE-CHECK post Spec 012 — 2026-05-09

**Trigger**: reasoning_decision rank-8E (0.59 score). Re-evaluates the 2026-05-07 bear-side mechanism class survey verdict (6/6 evaluated; 1 PASS / 5 SKIP) against the 2 days of work since.

**Cost**: $0. ~10 min wall-clock.

## 2026-05-07 baseline (per memory `reference_bear_side_mechanism_survey_complete.md`)

| Class | Standalone Gate | Additive Gate | Spec-eligible? | Source |
|---|---|---|---|---|
| C-1 (insider transactions) | SKIP (anti-pred) | n/a | NO | PR #23 |
| C-2 (short-interest delta) | SKIP (mechanism INVERTED) | n/a | NO | PR #76 |
| C-3 (analyst PT delta) | NOT FEASIBLE (no historical) | n/a | NO | PR #40 |
| **C-4 (institutional ownership)** | **PASS (n=12, +5.41pp)** | **PASS (+8.06pp / +69pp)** | **YES (shadow-mode-first)** | PR #75 + PR #77 |
| C-5 (EPS surprise — BULL) | PASS standalone | FAIL additive (89% overlap) | NO | 2026-05-06 |
| C-5 (PRICE-REACTION) | SKIP (mechanism INVERTED) | n/a | NO | PR #74 |
| C-6 (bear-news density) | SKIP (structural redundant) | n/a | NO | PR #67 |

**Scorecard**: 1 PASS (C-4 institutional rotation; deployed as Spec X-1) / 5 SKIP.

## Updates since 2026-05-07 (today's bear-side-relevant work)

### NEW bear-side mechanism class evaluated + PASSED (Class 4 macro)

**Mechanism**: cross-asset macro environment (VIX-snapshot threshold)
**Source**: `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193)
**Standalone gate**: PASS at n=8 fires (VIX < 18); discrim +24.07pp; hit 75%; net Δα +24.07pp
**Additive gate vs A3**: PASS — mechanism-disjoint (A3 catches 0 of 22 ticker_strong by definition; Class 4 catches 6 of 22)
**Spec-eligible**: YES — DEPLOYED end-to-end as Spec 012 via 5-PR bundle (PRs #194-#200)
**Default mode**: SHADOW per Constitution VIII v1.4.0 small-sample-caution
**Mechanism-class novelty**: distinct from per-ticker price (A3) / per-sector (Spec 004/006) / prose-density (Spec 003) / LLM-extracted (Spec 007/008) / institutional flow (Spec X-1 = bear-side C-4). FIRST cross-asset macro filter.

### Bear-side bull-cohort retrospectives that DIDN'T add to bear-side survey

- **Class 5 BULL fundamentals-delta re-run** (PR #202): re-confirmed 2026-05-06 SKIP. NOT a bear-side test.
- **Class 4 BULL macro retrospective** (PR #203): SKIP. NOT a bear-side test (was bull-side analog of Spec 012 BEAR; failed at every threshold).
- **Local-high BULL retrospective** (PR #205): DEFER. NOT a bear-side test.

### Constitution amendments not affecting survey

- v1.5.0 + v1.5.1 + v1.5.2 (WC-10 + WC-11): all affect Principle VII (Calibrated Abstention); orthogonal to bear-side mechanism survey scope.

## Updated scorecard (2026-05-09)

| Class | Verdict | Spec |
|---|---|---|
| C-1 (insider transactions) | SKIP | NO |
| C-2 (short-interest delta) | SKIP (INVERTED) | NO |
| C-3 (analyst PT delta) | NOT FEASIBLE | NO |
| **C-4 (institutional ownership)** | **PASS** | **YES — Spec X-1 deployed 2026-05-07** |
| C-5 (EPS surprise — BULL) | SKIP additive | NO |
| C-5 (PRICE-REACTION) | SKIP (INVERTED) | NO |
| C-6 (bear-news density) | SKIP (redundant) | NO |
| **Class 4 cross-asset/macro** (NEW since 2026-05-07) | **PASS** | **YES — Spec 012 deployed 2026-05-09** |

**Updated scorecard: 7 mechanism classes evaluated; 2 PASS (C-4 institutional rotation = Spec X-1 + Class 4 macro = Spec 012) / 5 SKIP / 1 NOT FEASIBLE.**

The 6/6 "survey complete" framing per memory `reference_bear_side_mechanism_survey_complete.md` is now updated to **7 evaluated / 2 PASS**.

## Methodology validation

The 3 SKIP-types codified in 2026-05-07 still hold:
- **Empirical SKIP** (C-1 anti-predictive; C-2 INVERTED; C-5 INVERTED) — mechanism evaluated empirically + refuted
- **Data-availability SKIP** (C-3 no historical) — feasibility check rules out
- **Structural SKIP** (C-6 redundant) — mechanism is correlated with existing filter

**NEW pattern observation**: today's Class 4 BULL SKIP (PR #203) demonstrates a 4th SKIP-type:
- **Asymmetric SKIP** — bear-side analog passes (Spec 012 BEAR PASSED) but bull-side same-mechanism FAILS. The mechanism IS empirically valid on one direction (bear) but empirically refuted on the other (bull). Mechanism is direction-conditional.

This 4th SKIP-type is consistent with broader project finding (bear commits are regime-asymmetric; bull-side / bear-side mechanism failures often have different root causes).

## Implications for future bear-side survey work

1. **C-4 institutional rotation + Class 4 macro are MECHANISM-DISJOINT** despite both being bear-side: institutional rotation = quantitative 13F flow; macro = cross-asset VIX. Both deployed; both default-shadow per small-sample-caution; can be mutually-additive in PM hook chain (verified by Spec 012 implementation putting Class 4 LAST after Spec X-1).

2. **The "survey complete" framing was correct at 2026-05-07** but is incomplete-by-design: future mechanism class candidates can still surface (Class 4 macro is the empirical proof). The methodology is open-ended; the survey is "all currently-hypothesized classes evaluated" not "all possible classes evaluated."

3. **Spec 011 first-invocation candidate audit still NO CANDIDATE** (PR #213) — neither today's Class 4 BEAR nor Class 4 BULL nor local-high meet the 4-of-4 v1.4.6 behavioral-additive criteria. Bear-side spec-eligibility now relies on NEW mechanism class hypotheses outside the 7 already evaluated.

## Recommended memory update

The memory entry `reference_bear_side_mechanism_survey_complete.md` should be updated to reflect:
- 6 → 7 evaluated
- 1 PASS → 2 PASS (add Class 4 macro = Spec 012)
- 3 SKIP-types → 4 SKIP-types (add asymmetric SKIP)
- Note that "complete" was historically-true at 2026-05-07 but the survey is open-ended

Will be applied as a separate memory cleanup edit (not in this PR; per memory cleanup r2 discipline at PR #208 — surgical edits when triggered by new findings).

## Cost

$0 LLM. ~10 min wall-clock (audit + memo).

## What ships

`claudedocs/bear-side-survey-recheck-post-spec012-2026-05-09.md` (this audit memo).

## Cross-references

- Memory: `reference_bear_side_mechanism_survey_complete.md` (2026-05-07 baseline)
- PR #193: Class 4 BEAR macro retrospective PASS
- PR #200: Spec 012 deployment retrospective
- PR #203: Class 4 BULL macro retrospective SKIP
- PR #213: Spec 011 first-invocation candidate audit (NO CANDIDATE)
- Memory cleanup r2: PR #208
