# Feature Specification: Behavioral-Additive Operational Procedure (Spec 011)

**Feature Branch**: `011-behavioral-additive-procedure`
**Created**: 2026-05-08
**Status**: Codified (this spec is methodology/procedure, not code)
**Predecessor**: Constitution v1.4.6 sub-section "Behavioral-additive sub-case (4th interpretation)" within Principle VIII v1.4.3 Additive-to-existing-filter gate
**Input**: User description (excerpted): "Spec 011 behavioral-additive codification per v1.4.4 threshold-met. Cross-cohort sweep 2026-05-07 found 23+ → 44 cases / 13 tickers / 0 counter-evidence across all 4 mechanism classes. SHIP behavioral-additive specs for PM regime-drift robustness. Re-runnable harness: `scripts/behavioral_additive_sweep.py`."

## Why this spec exists

Constitution v1.4.6 codified the behavioral-additive 4th interpretation as a sub-section of Principle VIII v1.4.3. The amendment defines WHAT the escape clause is and WHY it matters. This spec defines HOW future filter specs should INVOKE it — the operational procedure that converts the constitutional principle into a concrete, repeatable filter-spec workflow.

Without Spec 011, the constitutional language risks ambiguous interpretation across future spec drafters: how strict is "≥60% PM-commit correlation"? what minimum sample size is required? what regime-shift trigger documentation suffices? Each new filter spec invoking the escape would re-litigate these decisions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Spec drafter invokes behavioral-additive escape on a new filter (Priority: P1)

**As a** spec drafter writing a new filter retrospective for filter F
**I want to** invoke the v1.4.6 behavioral-additive escape clause when F fails the v1.4.3 additive-on-actual-fires gate but passes the would-fire-counterfactual gate
**So that** F can SHIP rather than SKIP, providing PM regime-drift robustness without re-arguing the principle from scratch

**Acceptance criteria** (FRs below):

- The retrospective markdown includes the standard v1.4.3 actual-fires matrix AND the behavioral-additive counterfactual matrix
- The counterfactual sample size meets the v1.4.6 sample-size minimum (FR-002)
- A regime-shift trigger is documented per Constitution v1.4.6 risk-acknowledgement
- The verdict block explicitly states "behavioral-additive case per Constitution v1.4.6"

### User Story 2 - Future spec auditor verifies behavioral-additive invocations are consistent (Priority: P2)

**As a** later contributor auditing filter spec workflow consistency
**I want to** check that all filter specs invoking the v1.4.6 escape clause follow the same procedural pattern
**So that** the corpus of behavioral-additive specs is comparable and the escape clause doesn't degenerate into a catch-all loophole

**Acceptance criteria**:

- All retrospectives invoking v1.4.6 use the same headline-fields template (FR-001)
- The re-runnable harness is `scripts/behavioral_additive_sweep.py` (canonical; FR-005)
- Sample-size + ticker-coverage + mechanism-class-coverage thresholds are documented identically across specs

## Functional Requirements

### FR-001 — Standard retrospective fields (REQUIRED)

A behavioral-additive filter retrospective markdown MUST include at minimum:

1. **Standalone gate result block** (per Constitution VIII v1.3.0 / v1.4.0 depending on filter class)
2. **v1.4.3 actual-fires additive matrix** (intersection / new-only / existing-only / neither — same shape as Spec 007 + Spec X-1 retrospectives)
3. **Behavioral-additive counterfactual matrix** computed via `scripts/behavioral_additive_sweep.py`:
   - Per-mechanism-class case counts
   - Distinct-ticker count
   - Per-ticker × mechanism-class breakdown
   - Distribution of PM-commit-rating outcomes (Hold / Underweight / Sell for bear-side; Hold / Overweight / Buy for bull-side)
4. **Regime-shift trigger documentation** (Constitution v1.4.6 risk-acknowledgement requirement) — what PM behavior change would cause F's actual fires to start materializing? If no plausible regime-shift exists, the spec MUST SKIP per v1.4.6.
5. **Verdict block** explicitly stating: "behavioral-additive case per Constitution v1.4.6 — operational FAIL on v1.4.3 additive-on-actual-fires; mechanistic PASS on counterfactual; SHIP THE SPEC with documented expectation that production fires will be sparse until PM regime shifts."

### FR-002 — Minimum counterfactual sample size

The behavioral-additive counterfactual matrix MUST be computed on at least:

- **n ≥ 5 cases per mechanism class** in the relevant direction (bull or bear)
- **≥ 3 distinct tickers** contributing to the case set
- **≥ 4 of 4 mechanism classes** showing evidence in the cross-cohort sweep (i.e., the v1.4.6 codification basis must be MAINTAINED at retrospective time, not just at the codification snapshot)

If any threshold fails, the spec MUST defer the behavioral-additive verdict pending more state log accumulation. Document the gap explicitly in the retrospective; do NOT invoke the escape on insufficient evidence.

The current basis (post-v1.4.6 sweep refresh, `claudedocs/behavioral-additive-sweep-post-v1.4.6-ratification-2026-05-07.md`) is **44 cases / 13 tickers / 4-of-4 mechanism classes** — this is the bar to maintain or exceed.

### FR-003 — Regime-shift trigger specificity

The regime-shift trigger documentation MUST identify:

1. **What PM behavior would change**: e.g., "PM commits OW more often when bull_score < 0.4 instead of Hold-defaulting"
2. **What empirical signal would indicate the change**: e.g., "Hold rate drops below 50% on cohorts where bull_score < 0.4"
3. **What recovery time is plausible**: vague-but-bounded estimate (e.g., "if Sonnet → Opus model swap, change visible in next ~5 propagates")

Vague regime-shift triggers (e.g., "if PM ever changes") FAIL FR-003. The trigger MUST be concrete enough that a future operator can detect when the regime has shifted.

### FR-004 — Mechanism-class novelty check

Before invoking v1.4.6, the spec MUST establish that F's mechanism class is DIFFERENT from at least one existing default-active filter. Reference Constitution VIII v1.4.0's mechanism-class taxonomy:

- **Backward-price** (A3, Spec 004 sector-momentum)
- **Prose-density** (Spec 003, Spec 003.5 sector-fallback)
- **LLM-extracted forward-catalyst** (Spec 007 bull/bear)
- **Calendar-boosted hybrid** (Spec 008)
- **Quantitative-flow** (Spec X-1 institutional rotation)

If F is in the SAME mechanism class as an existing default-active filter (e.g., another prose-density filter), the v1.4.6 escape does NOT apply per Constitution v1.4.6 trigger criteria. The standard v1.4.3 gate applies; SKIP if it fails.

### FR-005 — Canonical re-runnable harness

The retrospective MUST cite `scripts/behavioral_additive_sweep.py` as the canonical harness. If the sweep needs methodology changes (e.g., new mechanism class added to the portfolio), update the harness and re-publish the sweep doc; do NOT invent a per-spec one-off harness.

The harness output format is the canonical input to the FR-001 retrospective fields. Spec drafters who need additional analysis SHOULD extend the harness rather than write parallel scripts.

### FR-006 — PR ordering with implementation

Behavioral-additive specs MUST land via the standard 6-PR spec-kit bundle (per `reference_speckit_6pr_workflow_pattern.md`):

1. spec.md (this PR pattern)
2. plan.md
3. tasks.md
4. MVP implementation
5. Tests
6. Polish

The retrospective markdown ships ALONGSIDE the spec.md PR (per Constitution VI v1.4.1 "spec ships its retrospective" sub-section). Do NOT defer the retrospective to a later PR.

## Out of scope (v1)

- **Automated enforcement**: a `scripts/behavioral_additive_validator.py` that lints new filter specs against FR-001 through FR-006 would be useful but is deferred. Manual checklist suffices for the current ~3-spec-per-quarter cadence.
- **Behavioral-additive case retroactive audit**: existing default-active filters were not retroactively required to demonstrate behavioral-additive evidence. Future deprecation decisions may use the harness output, but historical specs are grandfathered.
- **Cross-direction behavioral-additive**: the codification covers same-direction filters (bull vs bull, bear vs bear). Cross-direction interaction (e.g., does a bear filter's PM-commit pattern correlate with bull filter behavior?) is an open research question, not a spec procedure.

## Spec adherence to Constitution

- ✅ I (Save Everything): this spec.md is the only deliverable; future invocations will produce retrospective markdowns per FR-001
- ✅ II (One Experiment Per Change): N/A — this is a methodology spec, not an experiment
- ✅ III (Stay Cheap): $0 (procedural codification)
- ✅ IV (No Production Claims): the spec defines a procedure for invoking the v1.4.6 escape; it does NOT itself ship a filter
- ✅ VI (Spec Before Structural Change): this spec IS the structural change to filter-spec workflow
- ✅ VII (Calibrated Abstention v1.5.0): orthogonal — this spec governs filter-spec workflow, not PM behavior
- ✅ VIII (v1.4.6): this spec operationalizes the v1.4.6 sub-section

## Constitution implication

This spec doesn't trigger a constitution amendment. v1.4.6 already codifies the principle; Spec 011 codifies the operational procedure. If future filter specs reveal that one of FR-001 through FR-006 is too lax or too strict, that's the trigger for a v1.4.6 → v1.4.7 PATCH amendment.

## Test plan (for the spec itself, not code)

- [x] Spec text covers all 6 FRs with concrete acceptance criteria
- [x] Sample-size thresholds (FR-002) reference the current empirical basis (44 cases / 13 tickers / 4-of-4 classes)
- [x] FR-005 canonical harness reference matches `scripts/behavioral_additive_sweep.py`
- [x] FR-004 mechanism-class taxonomy matches Constitution VIII v1.4.0 + Spec X-1's quantitative-flow class
- [x] Constitution adherence checklist completed
- [ ] First future filter spec to invoke v1.4.6 cites Spec 011 in its retrospective (deferred — needs first invocation)

## Cross-references

- Constitution v1.4.6 sub-section "Behavioral-additive sub-case (4th interpretation)" (`.specify/memory/constitution.md`)
- `claudedocs/behavioral-additive-sweep-post-v1.4.6-ratification-2026-05-07.md` (current empirical basis)
- `claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md` (textbook qualitative case)
- `scripts/behavioral_additive_sweep.py` (re-runnable harness)
- Memory `reference_behavioral_additive_4th_interpretation.md`
- Memory `reference_speckit_6pr_workflow_pattern.md` (FR-006 PR ordering)
