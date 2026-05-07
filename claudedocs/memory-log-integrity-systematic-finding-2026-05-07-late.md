# Memory log integrity systematic finding — n=3 hallucinated reflections found

**Trigger**: PR #54 followup #1 (memory log integrity check tooling).
Built `scripts/memory_log_integrity_check.py` + 12 unit tests; ran on
SC-009 backtest_memory.md.

## Headline result

**3 of 15 resolved entries (20%) have suspect reflection prose** — all 3
are Underweight calls on extended-rally Tech (5-day window):

| Entry | Rating | Raw return | Validation phrases in reflection |
|---|---|---|---|
| COP @ 2026-04-17 | Underweight | +4.90% | 1 ("directional call was correct") |
| INTC @ 2026-04-17 | Underweight | +20.50% | 1 ("directional call was correct") |
| AMD @ 2026-04-17 | Underweight | +24.90% | 5 (canonical case from PR #54) |

Per the PR #54 deferred Constitution-amendment-candidate criteria
("defer until n≥3 hallucinated reflections accumulate"), **the
threshold is now MET**. Constitution-amendment proposal becomes
drafting-eligible.

## Methodology generalization

PR #54 framed AMD-04-17 as a single-case anomaly. This sweep shows the
hallucination is **systematic**, not anecdotal:

- **20% of resolved entries** have rating-direction-vs-realized-return-sign
  contradictions
- **All 3 cases** are Underweight calls that went UP — a unidirectional
  failure mode (LLM doesn't seem to flag "I was wrong about going down")
- **All 3 reflections** contain at least one self-validating phrase
  ("directional call was correct" being the most common)
- AMD-04-17 had FIVE validation phrases (most extreme case); COP and INTC
  had ONE each — suggesting hallucination intensity varies but the
  pattern is consistent

The 5-day holding window is too short for many of these calls to play out;
several Underweight calls on extended-rally Tech were destined to "fail"
at the 5d horizon even if they would succeed at 21d. But the LLM's
reflection treats the 5d data as definitive validation.

## Per-case observations

### COP-04-17 Underweight
- Raw 5d return: +4.90% (UP) → trim FAILED short-term
- Reflection contains "directional call was correct"
- Lower-magnitude hallucination than AMD; only 1 self-validating phrase
- COP at the time was an Energy-sector contrarian play; the +5% move was
  modest enough that the LLM may not have recognized it as a clear
  Underweight failure

### INTC-04-17 Underweight
- Raw 5d return: +20.50% (UP) → trim FAILED catastrophically
- Reflection contains "directional call was correct"
- Same hallucination pattern as AMD but earlier-discovered Tech-cyclical case
- The LLM's "directional call was correct" prose for a +20.5% raw return is
  a clear data-vs-prose contradiction

### AMD-04-17 Underweight (canonical PR #54 case)
- Raw 5d return: +24.90% (UP) → trim FAILED catastrophically
- Reflection contains 5 self-validating phrases (highest in cohort):
  "captured the inflection", "validated the trim", "directional call was
  correct", "trim discipline", "proved predictive"
- Highest-intensity hallucination case
- Cascade failure documented in PR #54: PM-04-24 propagated this
  hallucinated reflection into its own decision

## Why this matters for v1.4.4 ratification

Still **INDEPENDENT** of v1.4.4. The behavioral-additive +
multi-mechanism-validator framing is about COMMIT-DECISION CORRELATION
with contrarian signals, NOT about memory-log integrity. The 3
hallucinated reflections found here are about REFLECTION-PROSE
HALLUCINATION — a different concern entirely.

But the 20% systematic incidence rate is operationally significant for
how operators read memory logs going forward.

## Constitution-amendment proposal becomes drafting-eligible

Per PR #54 deferred amendment text:

> "Reflection-prose is operator-distrustable. When reading memory log
> entries, operators MUST cross-check reflection prose against
> entry-header realized return data. Reflections may be hallucinated
> when the data contradicts the prior thesis. The data is canonical;
> the reflection is descriptive at best, hallucinated at worst."

The n=3 threshold is now met. **Drafting eligible**, but ratification
should still wait for at least one cross-cohort confirmation (e.g.,
running this tooling on `~/.tradingagents/memory/trading_memory.md`
when that exists, or on a fresh backtest_memory.md from a future
experiment) to ensure the pattern isn't local to this single SC-009
backtest's LLM run.

This is a parallel codification candidate to the v1.4.4 behavioral-
additive amendment but on a DIFFERENT axis (memory-log integrity vs.
filter-additivity classification).

## Tooling delivered (this PR)

1. **`scripts/memory_log_integrity_check.py`** — walks any memory log
   file, parses resolved (non-pending) entries, flags rating-direction-
   vs-realized-return-sign mismatches. Heuristic scan for self-
   validating phrases when a mismatch is flagged.

2. **`tests/test_memory_log_integrity_check.py`** — 12 unit tests:
   - 4 HEADER_RE regex tests (canonical entries, negative returns,
     pending exclusion, dotted tickers like BRK.B)
   - 2 parse_entries tests (one-per-entry returned; empty-reflection
     handling)
   - 6 flag_inconsistencies tests (Underweight+UP flagged; Overweight+DOWN
     flagged; Hold never flagged; Underweight+DOWN not flagged;
     Buy+UP not flagged; sign-mismatch alone is enough)
3. **Empirical validation**: ran on SC-009 backtest_memory.md (1194
   lines, 15 resolved entries, 3 suspect entries surfaced).

## Followups (deferred)

1. **Cross-cohort truthfulness audit**: when canonical
   `~/.tradingagents/memory/trading_memory.md` exists or another
   backtest's memory log is available, run the same check. Builds
   evidence base for whether the 20% rate is universal.
2. **Constitution v1.4.5 amendment draft** (when the n≥1 cross-cohort
   confirmation lands): draft the "reflection-prose is
   operator-distrustable" amendment text. Defer until tomorrow's
   session at earliest.
3. **Reflection regeneration option** (PR #54 followup #2): spec
   amendment proposing the framework's `_resolve_pending_entries`
   should prepend a data-summary line that the LLM MUST acknowledge
   before writing reflective prose. Not built today.

## Sibling docs

- `claudedocs/amd-memory-log-audit-hallucination-resolution-2026-05-07-late.md`
  — PR #54 single-case finding that motivated this tooling
- `memory/reference_memory_log_reflection_hallucination.md` — operator
  memory documenting the M-1/M-2/M-3 framework implications
- `memory/reference_pm_hold_with_bullish_prose.md` — Constitution VII
  rating-vs-prose pattern (sister memory)
- `tradingagents/agents/utils/memory.py` — TradingMemoryLog source
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/backtest_memory.md`
  — source of truth for this sweep
