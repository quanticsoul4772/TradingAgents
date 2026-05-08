> **⚠️ SUPERSEDED — RATIFIED via PR #83 on 2026-05-07**
>
> This draft was ratified AS-IS as Constitution v1.4.5 (Quality Gate #6 — Memory-log data-vs-prose discipline) via PR #83. The canonical text now lives in `.specify/memory/constitution.md` Quality Gates section. This draft file is preserved for traceability of the drafting → ratification flow.
>
> **Rename note**: this draft was originally numbered v1.4.5 and ratified at v1.4.5 (no rename needed). The sister v1.4.4 draft (`constitution-v1.4.4-draft-2026-05-07.md`) was ratified as v1.4.6 to preserve monotone numbering after this v1.4.5 was ratified first per reasoning_decision rank ordering.
>
> **For current canonical text, read**: `.specify/memory/constitution.md`. **Do not edit this draft** — historical record only.

---

# Constitution v1.4.5 amendment draft (text-only, NOT YET RATIFIED)

**Status**: ~~DRAFT — eligible to ratify per memory codification threshold MET.~~ **RATIFIED via PR #83.**
**Drafted**: 2026-05-07 night (after end-of-day documentation arc completed).
**Ratification timing**: ~~defer to 2026-05-08 or later. Per the v1.4.4 two-stage pattern (PR #44), ratification should happen in a SEPARATE session from the draft to avoid same-session-pattern over-fitting.~~ Same-session ratification proceeded after operator approval; n=3 hallucination threshold + cascade-failure documentation gave sufficient confidence to skip the same-session-defer rule.

**Empirical basis**:
- 2026-05-07 night PR #54 — single AMD-04-17 case discovered: memory log
  REFLECTION prose claims "captured the inflection correctly" while
  entry header data records +24.9% raw return (Underweight call FAILED).
  PM-04-24 then propagates the hallucinated reflection.
- 2026-05-07 night PR #55 sweep — `scripts/memory_log_integrity_check.py`
  walks all resolved entries in `backtest_memory.md` and finds 3 of 15
  (20% incidence rate) with rating-direction-vs-realized-return-sign
  contradictions, all carrying self-validating phrases:
  - COP-04-17 Underweight + raw +4.90% (1 phrase)
  - INTC-04-17 Underweight + raw +20.50% (1 phrase)
  - AMD-04-17 Underweight + raw +24.90% (5 phrases — canonical case)

The n=3 codification threshold from PR #54 followup is MET.

**Why a draft, not direct constitution edit**:
- Per the v1.4.4 PR #44 two-stage pattern: drafting separately costs $0
  and unblocks tomorrow's ratification.
- Drafting tonight + ratifying tomorrow = dual-ratification opportunity
  (v1.4.4 + v1.4.5 in same Tuesday commit cycle).
- Risk of retraction is low (descriptive framing) but the across-sessions
  defense is preserved by drafting separately first.

**Independence from v1.4.4**:
- v1.4.4 is about behavioral-additive multi-mechanism-validator framing
  (Constitution VIII v1.4.3 additive-gate sub-case for filter design)
- v1.4.5 is about memory-log integrity (operator-side reading discipline
  for `backtest_memory.md` / `trading_memory.md` entries)

These are SEPARATE methodology axes. Either amendment can ratify
independently of the other.

---

## Proposed amendment to `.specify/memory/constitution.md`

### Section to add: Quality-Gates section addition (NOT Principle VIII)

The amendment doesn't fit Principle VIII (forward-catalyst-class gate) or
Principle VI (Spec Before Structural Change). It's an OPERATOR-DISCIPLINE
amendment, more analogous to Constitution VII Calibrated Abstention.

Two placement options:

**Option A — append to Principle VII (Calibrated Abstention is a Valid Output)**:

The existing Principle VII says "filters parse rating, not prose"
(implicit; codified in `memory/reference_pm_hold_with_bullish_prose.md`).
v1.4.5 extends this: operators must parse memory-log DATA, not narrative.
Symmetric pattern: rating-vs-prose discipline at the propagate level →
data-vs-prose discipline at the historical-memory level.

**Option B — new "Quality Gates" sub-section** (under existing
"Quality Gates" section around line 302):

Add as Quality Gate #6:

```markdown
### Quality Gate #6 — Memory-log data-vs-prose discipline (added 2026-05-08; v1.4.5)

When operators read entries from any memory log file (`backtest_memory.md`,
`~/.tradingagents/memory/trading_memory.md`, or future variants),
operators MUST cross-check the entry's reflection prose against the
entry's header data (raw_return, alpha, holding_days). Reflection prose
can be hallucinated when the data contradicts the prior call's expected
direction; operators trusting prose over data risk propagating false
"lessons learned" into downstream decisions.

**Operational rule**:

1. **Read entry header FIRST**: extract date, ticker, rating, raw_return,
   alpha, holding_days.
2. **Check sign consistency**: bullish ratings (Buy, Overweight) expect
   raw_return ≥ 0; bearish ratings (Underweight, Sell) expect
   raw_return ≤ 0; Hold has no expected direction.
3. **If sign-mismatched, the reflection is SUSPECT**: do NOT cite
   reflection prose as evidence without verifying it acknowledges the
   data. Common hallucination phrases include "captured the inflection
   correctly," "validated the trim discipline," "directional call was
   correct" appearing on entries where the call DEMONSTRABLY failed at
   the holding-window horizon.
4. **In claudedocs / analysis**: distinguish "entry header says X" from
   "reflection narrates Y." Don't conflate.

**Empirical basis** (2026-05-07 PR #54 + PR #55):

`scripts/memory_log_integrity_check.py` walks any memory log and flags
sign-mismatched entries with reflection-phrase scoring. On
`experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/backtest_memory.md`
(15 resolved entries) it found:

| Ticker / Date | Rating | Raw return | Validation phrases in reflection |
|---|---|---|---|
| COP @ 2026-04-17 | Underweight | +4.90% | 1 |
| INTC @ 2026-04-17 | Underweight | +20.50% | 1 |
| AMD @ 2026-04-17 | Underweight | +24.90% | 5 (canonical) |

3 of 15 (20%) hallucinated reflections; ALL Underweight calls that went
UP; ALL with explicit self-validating phrases despite data refuting them.
PM-04-24 demonstrably trusted AMD-04-17's hallucinated reflection ("the
prior AMD lesson itself validates the trim discipline") rather than the
+24.9% raw return data — cascade-failure-mode documented.

**Mechanism explanation**: when `_resolve_pending_entries` writes a
reflection, the LLM generating the prose sees both the entry header data
AND the original DECISION prose. It faces "self-justification pressure"
when the realized data refutes the prior thesis: easier to write
narrative coherent with the prior thesis than to admit the call was
wrong. The framework has NO data-vs-prose consistency check on the
write; the prose can drift arbitrarily far from the data.

**Why this matters**:

- **Reflection-driven cascade failure**: PM trusts prior reflection
  prose over re-deriving from raw data. One bad reflection contaminates
  ALL downstream same-ticker runs until either (a) memory entry is
  manually corrected, or (b) realized data so strongly contradicts the
  cascading narrative that a future LLM generates a corrective
  reflection.
- **Operator-side defense is required**: framework provides no
  consistency check. Operators must parse data, not prose.
- **Symmetry with Constitution VII**: Principle VII says "filters parse
  rating, not prose" (in spirit, codified in
  `memory/reference_pm_hold_with_bullish_prose.md`). v1.4.5 extends to
  memory log: operators parse data, not prose.

**Tooling**:

`scripts/memory_log_integrity_check.py` (PR #55) is the canonical
reusable harness. Run periodically (or before any analysis that cites
memory log evidence) to surface suspect entries. Exit code 0 = clean,
1 = suspects found. CI-friendly.

**Acceptable exception**:

Hold-rating entries are exempt (no directional expectation). Reflection
prose on Hold entries can be checked using human judgment but isn't
flagged automatically.

**Trigger criteria** (when this gate applies):

- Yes: any operator analysis that cites prior memory log entries as
  evidence for current decisions.
- Yes: any spec retrospective that walks memory log to extract historical
  lessons.
- No: PM propagates themselves (framework-internal; framework lacks the
  consistency check to enforce). PM behavior is what THIS gate exists
  to protect operators against.
```

**Recommendation: Option B** (new Quality Gate #6). Quality Gates section
is the right home for operator-discipline rules; placing under Principle
VII would muddle the rating-vs-prose pattern with the reading-vs-prose
pattern.

---

## Header changes (proposed at top of constitution.md)

```markdown
**Version**: 1.4.5
**Adopted**: 2026-05-01
**Last amended**: 2026-05-08 (per ratification — see CHANGELOG.md) —
added Quality Gate #6 "Memory-log data-vs-prose discipline" requiring
operators to cross-check memory log entry reflection prose against
entry header data. Empirical basis: PR #54 single-case discovery of
LLM-generated reflection that contradicts entry header data + PR #55
sweep finding 3 of 15 entries (20% incidence rate) carry hallucinated
reflections with self-validating phrases despite data refuting them.
Cascade failure mode documented (PM trusts prior hallucinated reflection
over raw data, propagates contaminated narrative). v1.4.4 → v1.4.5
(PATCH per clarification rule).
**Prior version**: 1.4.4 — [v1.4.4 amendment text from PR #44 ratification]
**Prior version**: 1.4.3 — [existing text]
```

---

## CHANGELOG.md entry (proposed)

```markdown
## [1.4.5] - 2026-05-08

### Constitution

- Added Quality Gate #6 "Memory-log data-vs-prose discipline" requiring
  operators to cross-check memory log entry reflection prose against
  entry header data. Symmetry with Constitution VII (filters parse rating,
  not prose) extended to memory-log reading. Empirical basis: PR #54
  AMD-04-17 single-case + PR #55 sweep at 20% incidence rate. Tooling:
  `scripts/memory_log_integrity_check.py`. v1.4.4 → v1.4.5 (PATCH).
```

---

## Operational notes for the ratifying session

1. **Prerequisite check before ratifying**:
   - PR #55 sweep result still shows ≥3 hallucinated reflections (re-run
     `scripts/memory_log_integrity_check.py` to verify).
   - No code changes required since PR #54 discovered + PR #55 codified
     the finding.
2. **Ratification commit**: should be a single commit modifying:
   - `.specify/memory/constitution.md` (add Quality Gate #6 +
     bump header to v1.4.5)
   - `CHANGELOG.md` (add v1.4.5 entry)
   - Reference this draft doc + PR #54 + PR #55 in the commit body for
     traceability.
3. **No code changes required**: this is a methodology amendment. Tooling
   already exists (`scripts/memory_log_integrity_check.py` from PR #55).
4. **Test count remains 1162/1162**: no test changes needed.
5. **Spec invocation impact**: no current specs are blocked or affected.
   Future operators citing memory log evidence MUST follow Quality
   Gate #6 procedure.
6. **Sequencing with v1.4.4 ratification**: can be done in same Tuesday
   session OR as separate consecutive PRs. Recommend separate PRs to
   keep traceability clean (each amendment with its own commit).

---

## Decision matrix for ratification (Tuesday)

| Pre-ratification check | Status |
|---|---|
| n≥3 hallucinated reflections documented | YES (per PR #55: 3 found) |
| Tooling for ongoing monitoring exists | YES (PR #55 script + 12 unit tests) |
| Mechanism explanation documented | YES (M-1/M-2/M-3 in PR #54 + this draft) |
| Cross-cohort confirmation | NO (only SC-009 backtest_memory.md scanned; canonical user trading_memory.md doesn't exist yet) |
| Risk-of-retraction acceptable | YES (descriptive operator-discipline rule, not predictive) |
| Operational impact bounded | YES (tooling + memory operator must run before citing) |
| Operator-discipline (not framework-internal) | YES (no framework consistency check needed) |

**6 of 7 pre-ratification checks PASS.** The PENDING check (cross-cohort
confirmation) is gated on data availability — there's currently no
second memory log file to scan. Two options:

- **Defer ratification** until a second memory log file exists (next
  backtest, or canonical user trading_memory.md is populated).
- **Ratify with explicit "cross-cohort confirmation pending" caveat** —
  the n=3 single-cohort evidence is strong enough to ratify with the
  caveat noted in the amendment text.

Recommend: **ratify with caveat**. The single-cohort evidence is
sufficient because:
- The mechanism is well-explained (LLM self-justification pressure)
- Tooling exists for ongoing monitoring (`scripts/memory_log_integrity_check.py`)
- The amendment is operator-discipline (not framework-internal); operators
  can apply it to any future memory log without further evidence
- Risk of retraction is low (descriptive framing; can amend further if
  cross-cohort data surprises)

## Sibling docs

- `claudedocs/amd-memory-log-audit-hallucination-resolution-2026-05-07-late.md`
  — PR #54 single-case discovery
- `claudedocs/memory-log-integrity-systematic-finding-2026-05-07-late.md`
  — PR #55 sweep finding (20% incidence rate)
- `memory/reference_memory_log_reflection_hallucination.md` — operator
  memory; this draft incorporates the M-1/M-2/M-3 framework implications
- `claudedocs/constitution-v1.4.4-draft-2026-05-07.md` — PR #44 v1.4.4
  draft (sister amendment for tomorrow's potential dual-ratification)
- `scripts/memory_log_integrity_check.py` — tooling
- `scripts/v1_4_4_counter_evidence_watch.py` — separate v1.4.4 tooling
