# Constitution v1.4.4 amendment draft (text-only, NOT YET RATIFIED)

**Status**: DRAFT — eligible to ratify per memory codification threshold MET.
**Drafted**: 2026-05-07 late-afternoon (during SC-009 backtest, mid-flight).
**Ratification timing**: defer to 2026-05-08 or later, gated on 1+ additional
session of the behavioral-additive pattern holding (defensive against
post-hoc-coincidence on a single sweep date).

**Empirical basis**:
- 2026-05-07 morning: 4 NVDA/MSFT/AAPL Spec 003 cases (single mechanism class)
- 2026-05-07 mid-flight: COP-04-24 Spec 007 case (2nd mechanism class)
- 2026-05-07 late-afternoon **PR #41 cross-cohort sweep**: 23 cases across 6
  tickers in ALL 4 mechanism classes (Spec 003 + Spec 007 bull + Spec 007 bear
  + Spec 008)
- 2026-05-07 evening **PR #43 AMD-04-17 deep-dive**: cleanest L-8 sub-pattern 2
  case in corpus; PM verbalized the bull-priced-in mechanism in plain English
  ("42% rally" + "99th-percentile technical exhaustion" + "earnings repricing
  risk"); bull_score=0.85 (highest in SC-009)

**Why a draft, not direct constitution edit**:
- Per memory `reference_behavioral_additive_4th_interpretation.md`, drafting is
  eligible (4-mechanism-class threshold MET) but ratification is still gated.
- Risk of retraction is modest (descriptive framing, not predictive), but
  drafting separately costs $0 and unblocks tomorrow's planning.
- Tomorrow's `claudedocs/research-burst-2026-05-08.md` D-2 explicitly recommends
  this two-stage pattern.

---

## Proposed amendment to `.specify/memory/constitution.md`

### Section to add: "Behavioral-additive sub-case (4th interpretation)"

Append AFTER the existing "Additive-to-existing-filter gate" sub-section in
Principle VIII (around line 296 of the current v1.4.3 file).

Proposed text:

```markdown
### Behavioral-additive sub-case (4th interpretation; added 2026-05-08; v1.4.4)

The Additive-to-existing-filter gate (v1.4.3) defaults to evaluating overlap
ON ACTUAL FIRE DECISIONS — what the new filter F actually fires vs what the
existing portfolio actually fires. Three sub-cases of "additive" cover
most workflows:

1. **Cohort-additive**: F catches different cohort losers than existing.
   Empirical overlap matrix shows < 60% intersection on the cohort.
2. **Mechanism-additive**: F operates on a different mechanism class than
   existing (e.g., LLM-extracted vs prose-density vs backward-price). The
   v1.4.0 forward-catalyst-class gate distinguishes mechanism classes
   formally.
3. **Underlying-additive** (hybrid filters): F MODULATES an underlying
   validated filter and improves at least one of its criteria (covered by
   the v1.4.2 magnitude-fungibility section's adjacent principle).

A **4th interpretation** — **behavioral-additive** — applies when F's
operational fire-decisions appear redundant with existing filters'
fire-decisions, BUT both correlate with the same PM commit decisions.
The PM has internalized F's contrarian logic via Constitution VII's
Calibrated Abstention training, so F is REDUNDANT-ON-EXECUTION but
COMPLEMENTARY-ON-DESIGN.

**The framing applies broadly to PM decisions, not just to one mechanism
class**: empirical evidence shows the PM has internalized contrarian
logic across multiple mechanism classes simultaneously (across this
project's filter portfolio: prose-density, LLM-extracted bull,
LLM-extracted bear, calendar-boosted). The right operating framing is
**PM-as-multi-mechanism-validator**: PM's Calibrated Abstention
operationally validates consensus across the analyst+debate ensemble —
when multiple mechanism classes flag the same contrarian condition,
PM commits Hold or stricter even though no filter operationally fires.

**Operational test** (when applying the v1.4.3 additive gate):

1. Run the standard intersection / new-only / existing-only / neither
   matrix on **actual** fire decisions (existing v1.4.3 procedure).
2. **ALSO** run a counterfactual matrix on **would-fire-if-PM-committed**
   decisions — parse state-log score fields without gating on actual
   pre_rating. (Reusable harness: `scripts/behavioral_additive_sweep.py`.)
3. Decision tree:
   - **Operational PASS** (cohort-additive on actual matrix per v1.4.3):
     SHIP THE SPEC unconditionally per existing v1.4.3.
   - **Operational FAIL but Mechanistic PASS** (counterfactual matrix
     shows F's would-fire matches PM's commits, different mechanism
     class than existing filters): **behavioral-additive case** — SHIP
     THE SPEC with documented expectation that production fires will be
     sparse until PM regime shifts. Document the behavioral-additive
     status in the spec's retrospective.
   - **Operational FAIL and Mechanistic FAIL**: SKIP per v1.4.3.

**Empirical basis** (2026-05-07 cross-cohort sweep):

The cross-cohort behavioral-additive sweep
(`scripts/behavioral_additive_sweep.py`,
`claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md`) walked
all 236 state logs accumulated 2026-05-04 to 2026-05-07 and found:

| Mechanism class | Behavioral-additive cases | Per-instrumented-log rate |
|---|---|---|
| Spec 003 (prose-density) | 7 | 70% |
| Spec 007 bull (LLM-extracted) | 7 → 8 (post-AMD) | 47-50% |
| Spec 007 bear (LLM-extracted) | 3 | 20% |
| Spec 008 (calendar-boosted) | 6 | 40% |

**ALL 4 mechanism classes show evidence**, distributed across 7 tickers
(AAPL, AMD, COP, INTC, MSFT, NVDA, WFC). MSFT shows the pattern in all 4
classes; AAPL+INTC in 3 each. AMD-04-17 (`claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md`)
is the textbook case where PM verbalizes the bull-priced-in mechanism
in plain English — confirms the pattern is mechanistically interpretable,
not just numerically correlated.

**Three sub-patterns identified by the sweep**:

1. PM Hold + bull-priced-in scores high (original framing — "PM abstains
   when filter would suppress").
2. PM **stricter-than-Hold** (Underweight) + bull-priced-in scores high
   (extends original — "PM commits CONSISTENT-OR-STRICTER than the
   filter's would-be suppression"). AMD-04-17 + INTC×2 + AAPL-04-24
   are the canonical examples.
3. PM Hold + bear-priced-in scores high (BEAR-SIDE behavioral-additive;
   empirical kernel for Hybrid D candidate).

**Why this matters**: without the 4th interpretation, future filter
specs in mechanism classes the PM has internalized would all SKIP per
v1.4.3 — even though they provide robustness against PM regime drift
(if PM ever stops being Hold-prone, the filter starts firing on
previously-redundant cases). Codifying behavioral-additive prevents
SKIPPING mechanistically-valuable filter specs based on operational-
redundancy artifacts of the current PM regime.

**Risk acknowledged**: behavioral-additive is a permissive case. It
unlocks specs whose immediate operational impact is small. The risk is
shipping multiple specs whose fires never materialize in production.
Mitigation: behavioral-additive specs MUST also document a regime-shift
trigger (what PM behavior would cause F's fires to start materializing)
in the retrospective. If no plausible regime-shift exists, SKIP.

**Trigger criteria** (when this sub-case applies):

- Yes: new filter F PASSES the v1.4.3 standalone gate but FAILS the
  v1.4.3 additive overlap on actual fires.
- Yes: F's mechanism class is different from at least one existing
  default-active filter.
- Yes: counterfactual sweep shows F's would-fire correlates with PM's
  commits at ≥ 60% rate on the same cohort.
- No: F is in the SAME mechanism class as an existing default-active
  filter (then v1.4.3 standard applies — no behavioral-additive escape).

**Acceptable exception**: same as v1.4.3 broader gates — explicit
"shakeout" filters scoped to operator-opt-in (default-off, marked
`shakeout_filter: true` in PARAMS.json) skip both the standalone gate
AND the additive gate AND the behavioral-additive sub-case.
```

---

## Header changes (proposed at top of constitution.md)

```markdown
**Version**: 1.4.4
**Adopted**: 2026-05-01
**Last amended**: 2026-05-08 (per ratification — see CHANGELOG.md) —
appended a "Behavioral-additive sub-case (4th interpretation)" sub-section
to Principle VIII v1.4.3 Additive-to-existing-filter gate. Empirical
basis: cross-cohort behavioral-additive sweep
(`claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md`,
PR #41) found behavioral-additive evidence in ALL 4 mechanism classes
(23 cases across 7 tickers). Reframes PM operational role from
analyst+debate aggregator to multi-mechanism-validator. Without this
sub-case, future filter specs in mechanism classes the PM has
internalized would all SKIP per v1.4.3 — even though they provide
regime-drift robustness. v1.4.3 → v1.4.4 (PATCH per clarification rule).
**Prior version**: 1.4.3 — [existing text]
```

---

## CHANGELOG.md entry (proposed)

```markdown
## [1.4.4] - 2026-05-08

### Constitution

- Added "Behavioral-additive sub-case (4th interpretation)" to Principle
  VIII v1.4.3 Additive-to-existing-filter gate. Codifies the case where
  filter F's operational fires appear redundant with existing portfolio
  but the underlying mechanism class is novel and PM has internalized F's
  contrarian logic via Constitution VII training. Reframes PM as
  multi-mechanism-validator. Empirical basis: cross-cohort sweep
  (PR #41) + AMD-04-17 deep-dive (PR #43); 23 behavioral-additive cases
  across 7 tickers in all 4 mechanism classes. v1.4.3 → v1.4.4 (PATCH).
```

---

## Operational notes for the ratifying session

1. **Prerequisite check before ratifying**:
   - SC-009 backtest must finish without producing counter-evidence
     (e.g., a row where PM picked Buy on a 4-mechanism-contrarian-aligned
     ticker would refute the multi-mechanism-validator framing).
   - Re-run `scripts/behavioral_additive_sweep.py` after SC-009 finishes;
     verify the 4-mechanism-class pattern still holds.
2. **Ratification commit**: should be a single commit modifying:
   - `.specify/memory/constitution.md` (add sub-section + bump header)
   - `CHANGELOG.md` (add v1.4.4 entry)
   - Reference this draft doc in the commit body for traceability.
3. **No code changes required**: this is a methodology amendment, not
   an implementation change. The sweep script (`behavioral_additive_sweep.py`)
   already exists from PR #41.
4. **Test count remains 1138/1138**: no test changes needed.
5. **Spec invocation impact**: no current specs are blocked or affected.
   Future specs can invoke the behavioral-additive sub-case explicitly
   in their retrospectives.

---

## Decision matrix for ratification (Tuesday/Wednesday)

| Pre-ratification check | Status |
|---|---|
| 4+ mechanism classes show evidence | YES (per PR #41 sweep) |
| Pattern observed across 5+ tickers | YES (7 tickers per PR #41 + AMD added in PR #43) |
| ≥1 textbook case with mechanistic PM-prose validation | YES (AMD-04-17 per PR #43) |
| SC-009 finishes without counter-evidence | PENDING (in progress, ~17 more rows) |
| Memory deferral rule satisfied (3+ mechanism classes) | YES (4/4 — exceeded 3-class floor) |
| Risk-of-retraction acceptable (descriptive framing) | YES |
| Operational impact bounded (no current specs blocked) | YES |

**If all PENDING checks pass on Tuesday morning**: ratify v1.4.4.
**If SC-009 surfaces counter-evidence**: revise the sub-case framing or
hold the draft for further evidence collection.

## Sibling docs

- `claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md` —
  empirical basis (23 cases, 4 classes, 6 tickers from PR #41)
- `claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md` — textbook
  mechanistic-validation case (AMD-04-17 from PR #43; 7th ticker)
- `memory/reference_behavioral_additive_4th_interpretation.md` — operator
  memory; cross-references this draft and the sweep harness
- `claudedocs/research-burst-2026-05-08.md` — tomorrow's scaffold; D-2
  ratification timing decision references this draft
- `scripts/behavioral_additive_sweep.py` — re-runnable harness
