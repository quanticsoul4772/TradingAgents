# C-4 vs Spec 007 bear additive overlap — VERDICT: ADDITIVE PASS

**Date**: 2026-05-07
**Script**: `scripts/forward_catalyst_class4_vs_spec007_overlap.py`
**Cost**: $0 LLM
**Cohort**: 29 bearish commits with date ≥ 2026-02-14

## Verdict — ADDITIVE PASS on 2 of 3 v1.4.3 criteria

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| Net Δα improvement (union vs Spec 007 alone) | ≥ +0.5pp | **+8.06pp** | **PASS** |
| Hit rate improvement (union vs Spec 007 alone) | ≥ +5pp | **+69.23pp** | **PASS** |
| FP rate improvement (intersection vs Spec 007 alone) | ≥ +10pp | +0.00pp | FAIL |

Per Constitution VIII v1.4.3, **at least 1 of 3 criteria PASSING is
sufficient** for spec eligibility. C-4 passes 2.

**This is the FIRST bear-side filter to clear both:**
1. Standalone gate (PR #75: discrim +10.29pp / hit 75% / Δα +5.41pp at n=12)
2. v1.4.3 additive overlap (this PR: +8.06pp Δα improvement / +69.23pp hit improvement)

## 2×2 overlap matrix

| Cell | n | mean α | hit % (sup-aligned) |
|---|---|---|---|
| both | 1 | -2.80% | 0.0% |
| c4_only | **11** | **+6.16%** | **81.8%** |
| spec007_only | 1 | -3.93% | 0.0% |
| neither | 16 | +21.74% | 68.8% |

The `c4_only` cell is the operative finding: C-4 catches 11 bearish
commits Spec 007 ENTIRELY MISSES. Mean α on these +6.16%; suppressing
them would have HIT 81.8% of the time (9/11 had positive α — bear
thesis was wrong, suppression was correct).

## Baseline + variant comparison

| Configuration | n | mean α | hit % |
|---|---|---|---|
| Spec 007 bear alone | 2 | -3.37% | 0.0% |
| **C-4 alone** | **12** | **+5.41%** | **75.0%** |
| **Union (C-4 OR Spec 007)** | **13** | **+4.69%** | **69.2%** |
| Intersection (C-4 AND Spec 007) | 1 | -2.80% | 0.0% |

Spec 007 bear shadow mode caught only 2 cohort members; both were
bear-correct (mean α -3.37% = bear thesis was right; suppressing would
have HURT). C-4 alone catches 12 (mostly different cohort from Spec
007); union dominated by C-4's good fires.

## Why C-4 catches what Spec 007 misses

Mechanism class distinction:
- **Spec 007 bear** = LLM-extracted bear-priced-in score (semantic
  reasoning over analyst+debate text)
- **C-4** = institutional ownership rotation (quantitative flow signal
  from 13F filings)

These are LITERALLY different signal sources. Spec 007 sees what the
analyst+debate ensemble synthesizes about the bear thesis; C-4 sees
what institutional money did about it. The 11 c4_only fires are bear
commits where:
- LLM didn't read the bear thesis as priced-in (bear_score ≤ 0.50), AND
- Institutions had been rotating OUT (selling)
- → PM picked UW chasing the move; suppressing was correct

This is a clean cross-mechanism-class additive case — exactly what the
Constitution VIII v1.4.3 gate is designed to identify.

## Pre-spec-invocation checklist (NOW updated post-overlap)

| Check | Status |
|---|---|
| Standalone gate PASS (PR #75) | ✅ bear-side at n=12 |
| Mechanism class distinct from existing (PR #75) | ✅ institutional-flow class |
| **v1.4.3 additive overlap vs Spec 007** | **✅ PASS on 2 of 3 criteria (this PR)** |
| Time-window discipline | ⚠️ valid until ~2026-05-15 (Q1 2026 13F refresh) |
| Sample-size confidence | ⚠️ n=12 fires; single-period cohort |
| Constitution VI (Spec Before Structural Change) | ⚠️ requires `/speckit.specify` invocation if pursuing |

**Spec invocation is now ELIGIBLE per the v1.4.0 + v1.4.3 gates**.
Recommend SHADOW-MODE-FIRST launch per Constitution VIII v1.4.0
(criteria 1+2 pass at n=12, but sample size warrants extra caution
before flipping to default-active).

## Decision tree

If proceeding with spec:
1. **Spec X-1 (C-4 institutional rotation, shadow mode bear-only)**:
   - New `tradingagents/agents/utils/institutional_rotation_filter.py` module
   - Hooks into PM hook chain after Spec 007 (parallel mechanism, not nested)
   - Default config: shadow mode at -5% rotation threshold (matching this analysis)
   - State annotation: `state["institutional_rotation"]` with rotation_pct, would_fire, fired
   - Tests: ~12 unit tests (rotation computation + threshold semantics + LRU cache + ETF graceful)
   - Cost: $0 LLM (yfinance-only signal)

If NOT proceeding:
- Document the SHADOW-MODE-FIRST verdict; defer spec invocation pending
  - Q1 2026 13F refresh (~2026-05-15) re-validation
  - Sample-size growth (next backtest cohort)
  - Operator preference

## Bear-side scorecard final status

C-4 is now the ONLY bear-side mechanism class to clear ALL pre-spec
criteria (v1.4.0 standalone + v1.4.3 additive + mechanism distinctness):

| Class | Standalone | Additive | Spec-eligible? |
|---|---|---|---|
| C-1 | SKIP | n/a | NO |
| C-2 | SKIP | n/a | NO |
| C-3 | NOT FEASIBLE | n/a | NO |
| **C-4** | **PASS** | **PASS** | **YES (shadow-mode-first recommended)** |
| C-5 (both) | SKIP | n/a | NO |
| C-6 | SKIP | n/a | NO |

**1 of 6 mechanism classes is spec-eligible**. The bear-side mechanism
class survey conclusively narrows to C-4 (institutional ownership
delta) as the sole viable extension to the bear-side filter portfolio.

## Followups

1. **Decision**: invoke `/speckit.specify` for C-4 institutional
   rotation filter (shadow-mode-first), OR defer pending re-validation
   after 2026-05-15 13F refresh.
2. **Memory polish**: capture the C-4 overlap-PASS finding + the
   "bear-side mechanism class survey concludes C-4 as sole viable
   extension" framing as cross-session memory. ~15min.
3. **Re-run overlap analysis after 2026-05-15**: same script; if
   Q1 2026 13F refresh changes the rotation values, the verdict may
   shift.

## Sibling docs

- `claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` (PR
  #75 standalone gate verdict)
- `claudedocs/class-c4-institutional-ownership-feasibility-2026-05-07.md`
  (PR #66 feasibility verdict)
- `claudedocs/forward-catalyst-class5-vs-class3-overlap-2026-05-06.md`
  (sister overlap analysis structure for Class 5)
- `.specify/memory/constitution.md` Principle VIII v1.4.3 additive gate
