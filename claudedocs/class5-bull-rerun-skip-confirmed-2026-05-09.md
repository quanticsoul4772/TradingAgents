# Class 5 BULL fundamentals-delta retrospective re-run — SKIP verdict CONFIRMED at refreshed corpus

**Date**: 2026-05-09
**Trigger**: reasoning_decision rank-4JJ. Re-runs `scripts/forward_catalyst_class5_vs_class3_overlap.py` against today's expanded corpus to verify whether the 2026-05-06 SKIP verdict (per Constitution VIII v1.4.3 additive-to-existing-filter gate) holds.
**Cost**: $0 (yfinance + arithmetic; cached Class 3 Opus scores).
**Wall-clock**: ~2 min (single script invocation).

## Verdict — UNCHANGED from 2026-05-06

| Metric | 2026-05-06 (original) | 2026-05-09 (re-run) | Δ |
|---|---:|---:|---|
| Cohort: bull commits with computable surprise data | 47 | 47 | unchanged |
| Spec 007 alone: net Δα | +2.24pp | +2.24pp | identical |
| Spec 007 alone: hit rate | 88.9% | 88.9% | identical |
| Class 5 alone: net Δα | +4.37pp | +4.37pp | identical |
| Class 5 alone: hit rate | 96.3% | 96.3% | identical |
| Hybrid B union: net Δα | -1.85pp | -1.85pp | identical |
| Union improvement vs Spec 007 alone: net Δα | -4.09pp | -4.09pp | identical |
| Union improvement vs Spec 007 alone: hit | +7.4pp | +7.4pp | identical |
| Cohort_a (bull losers) overlap: caught by BOTH | 24/27 | 24/27 | identical |
| Cohort_a: caught by Spec 007 only | 0/27 | 0/27 | identical |
| Cohort_a: caught by Class 5 only | 2/27 | 2/27 | identical |
| **Verdict** | **REDUNDANT — SKIP Spec 010** | **REDUNDANT — SKIP Spec 010** | **identical** |

## Why corpus growth didn't change the numbers

The cohort the script analyzes is bound to bull commits (`pre_rating in {Buy, Overweight}`) WITH computable yfinance earnings surprise data. The new commits added since 2026-05-06 came from:

- **WC-10 v2** (n=80): wc_10 mode (filter-bypass; no Spec 007 fire decisions; emits scalars not 5-tier ratings the script reads)
- **WC-11** (n=20): NVDA × 4 analyst-order permutations; mostly Hold (per-permutation commit rate 0% → 40%)
- **BR-3** (n=20): NVDA + AAPL × prose vs structured; mostly Hold (only 2 commits in structured mode)

None of these added new commits to the script's cohort filter. The 47-row cohort is unchanged.

This is consistent with the **mechanism-overlap structural argument** the v1.4.3 SKIP was based on: Class 5 (EPS surprise) and Spec 007 (LLM-extracted "bull case priced in") are mechanistically correlated because both signal the same underlying reality — earnings information already absorbed by the market.

## Implications

1. **Class 5 BULL stays SKIP'd indefinitely** unless a NEW bull cohort emerges that materially expands the cohort beyond 47 commits AND has different overlap characteristics. The structural mechanism overlap won't change with corpus growth alone.

2. **Class 5 BULL retrospective tooling is preserved** in the codebase (`scripts/forward_catalyst_class5_*.py` exist). The SKIP verdict is a methodological output (per Constitution VIII v1.4.1 + v1.4.3 framework), not a "delete this code" outcome.

3. **No new ROADMAP changes needed**. The Class 5 row was already marked RESOLVED in PR #191 (2026-05-09 morning). This re-run reaffirms that resolution.

4. **Future Class 5 BULL re-evaluation triggers**:
   - A 100+ row corpus expansion in the bull cohort that includes high-surprise commits NOT correlated with Spec 007 fires
   - A change in Spec 007's threshold (currently 0.60) that materially shifts WHICH commits Spec 007 catches
   - A new mechanism class hypothesis that combines Class 5 with a non-Class-3 feature (out of scope for this re-run)

## Operational note: script side-effect

Running `scripts/forward_catalyst_class5_vs_class3_overlap.py` overwrites `claudedocs/forward-catalyst-class5-vs-class3-overlap-2026-05-06.md` (the script writes to that hardcoded path). For this re-run, the overwrite was reverted via `git checkout` to preserve the historical 2026-05-06 dated artifact. Future operators running this script should be aware of this side-effect — consider a `--out` flag if needed.

## Constitution adherence

- ✅ I (Save Everything): this memo + preserved 2026-05-06 original retrospective
- ✅ III (Stay Cheap): $0 LLM
- ✅ IV (No Production Claims): SKIP verdict held; no production deployment
- ✅ VIII v1.4.3: re-run confirms additive gate FAIL (union HURTS net Δα by -4.09pp)

## Cross-references

- `claudedocs/forward-catalyst-class5-vs-class3-overlap-2026-05-06.md` — original 2026-05-06 retrospective
- `scripts/forward_catalyst_class5_vs_class3_overlap.py` — reproducible script
- `claudedocs/forward-catalyst-class5-retrospective-2026-05-06.md` — Class 5 standalone retrospective
- ROADMAP.md Open Questions Class 5 row (RESOLVED 2026-05-06; PR #191 marked + this re-run reaffirms)
- Constitution VIII v1.4.3 (additive-to-existing-filter gate)
- Memory: `feedback_additive_filter_gate.md` — codifies the v1.4.3 discipline
