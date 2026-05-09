# Constitution v1.5.3 conditional patch drafts — 2026-05-09

**Status**: PRE-SCAFFOLDED for WC-11 v2 verdict (in flight; ETA 2026-05-10). Each patch is verdict-conditional; when v2 lands, pick the matching patch + apply.

**Pattern source**: `claudedocs/constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md` (PR #144 — pre-scaffolded v1.5.1 patches per WC-10 v3 verdict; the matching patch was applied as PR #154 once v3 landed).

**Scope**: each patch updates Constitution VII v1.5.2 sub-section "Analyst-order scope" with the v2 empirical evidence. Tier (PATCH v1.5.3 vs MINOR v1.6.0 vs REVERT v1.5.1) depends on the verdict.

**Smoke verification (2026-05-09 evening)**: WC-11 v2 pipeline VERIFIED — 2 NVDA propagates landed (`market_news_fundamentals` + `news_fundamentals_market`; both Hold). No errors. Background `bwzris458` running.

## Decision matrix

| v2 verdict | Implication for v1.5.2 mandate | Patch tier | Patch ID |
|---|---|---|---|
| **NULL** (revised; v1 was stochastic) | REVERT v1.5.2 → v1.5.1 (analyst-order NOT a confounder) | **REVERT v1.5.1** | Patch B |
| **ALT-A confirmed** (news-first elevates ≥+15pp on ≥2/3 tickers) | STRENGTHEN v1.5.2 — recommend news-first OR document operator opt-in | **PATCH v1.5.3** | Patch A |
| **ALT-B confirmed** (market-last drops ≤-15pp on ≥2/3 tickers) | STRENGTHEN v1.5.2 — last-position confounder; reverse direction | **PATCH v1.5.3** | Patch C |
| **PARTIAL** (v1 NVDA reproduces but AAPL/MSFT differ) | v1.5.2 STAYS AS-IS; add ticker-conditional empirical paragraph | **PATCH v1.5.3** | Patch D |
| **INCONCLUSIVE** (v2 fails to reproduce v1 NVDA pattern) | v1.5.2 STAYS; add re-evaluation trigger at n=200+ | **PATCH v1.5.3** | Patch E |

## Patch B — REVERT v1.5.2 → v1.5.1

**Trigger**: WC-11 v2 NULL on per-permutation commit-rate (all 4 perms within ±10pp of pooled commit rate across all 3 tickers).

**Mechanism**: reverts `Analyst-order scope` paragraph from Replicability sub-section. v1.5.2 → v1.5.1 (REVERT per scope-narrowing rule going DOWN, not up).

```diff
**Version**: 1.5.2 → 1.5.1 (REVERT)
**Last amended**: 2026-05-10 (post-WC-11 v2) — REVERTED v1.5.2 "Analyst-order scope" paragraph per WC-11 v2 NULL verdict (n=60 across 3 tickers; all 4 permutations within ±10pp of pooled commit rate). v1 ALT-A + ALT-B was stochastic LLM variance; analyst-order is NOT an empirical confounder. Reverted to v1.5.1.
**Prior version**: 1.5.2 — added "Analyst-order scope" paragraph after WC-11 v1 PARTIAL ALT-A + ALT-B verdict; REVERTED 2026-05-10 per v2 NULL.
```

REMOVE the "Analyst-order scope" paragraph from constitution.md body (line ~136).

## Patch A — STRENGTHEN per ALT-A confirmation

**Trigger**: WC-11 v2 ALT-A confirmed (news-first elevates commit rate ≥+15pp vs DEFAULT across ≥2/3 tickers).

**Mechanism**: PATCH v1.5.2 → v1.5.3 by adding "ALT-A confirmation" paragraph to the existing Analyst-order scope sub-section.

```diff
**Version**: 1.5.2 → 1.5.3 (PATCH per scope-narrowing rule)
**Last amended**: 2026-05-10 (post-WC-11 v2) — strengthened "Analyst-order scope" paragraph per WC-11 v2 ALT-A confirmation. Empirical basis: `experiments/2026-05-09-002-wc11-v2-disambiguation/ANALYSIS.md` showed news-first permutations elevated commit rate by ≥+15pp vs DEFAULT across 2 of 3 tickers (n=60). First-speaker bias ratified at scale. New mandate: production deployment SHOULD use news-first analyst order (`selected_analysts = ["news", "market", "fundamentals"]`) by default; legacy DEFAULT order remains available via opt-in for backward-compat. v1.5.2 → v1.5.3 (PATCH per scope-narrowing rule).
```

ADD new paragraph to Analyst-order scope sub-section in constitution.md body — "**ALT-A confirmation (added 2026-05-10, post-WC-11 v2)**: ..."

## Patch C — STRENGTHEN per ALT-B confirmation

**Trigger**: WC-11 v2 ALT-B confirmed (market-last permutations DROP commit rate ≤-15pp vs DEFAULT across ≥2/3 tickers).

**Mechanism**: PATCH v1.5.2 → v1.5.3 by adding "ALT-B confirmation" paragraph to Analyst-order scope sub-section.

```diff
**Version**: 1.5.2 → 1.5.3 (PATCH per scope-narrowing rule)
**Last amended**: 2026-05-10 (post-WC-11 v2) — strengthened "Analyst-order scope" paragraph per WC-11 v2 ALT-B confirmation. Empirical basis: `experiments/2026-05-09-002-wc11-v2-disambiguation/ANALYSIS.md` showed market-last permutations DROPPED commit rate by ≤-15pp vs DEFAULT across 2 of 3 tickers (n=60). Last-speaker (recency) bias confirmed. New mandate: production deployment SHOULD avoid market-last analyst orderings; recommend news-last OR fundamentals-last as opt-in alternatives. v1.5.2 → v1.5.3 (PATCH per scope-narrowing rule).
```

## Patch D — STAYS AS-IS + ticker-conditional paragraph

**Trigger**: WC-11 v2 PARTIAL (NVDA reproduces v1 pattern but AAPL/MSFT differ).

**Mechanism**: PATCH v1.5.2 → v1.5.3 by adding "Ticker-conditional clarification" paragraph; v1.5.2 mandate stays AS-IS.

```diff
**Version**: 1.5.2 → 1.5.3 (PATCH per scope-narrowing rule)
**Last amended**: 2026-05-10 (post-WC-11 v2) — added "Ticker-conditional clarification" to Analyst-order scope sub-section per WC-11 v2 PARTIAL verdict. Empirical basis: `experiments/2026-05-09-002-wc11-v2-disambiguation/ANALYSIS.md` showed NVDA reproduces v1 first-/last-speaker effect at scale BUT AAPL + MSFT do NOT show the same pattern. Analyst-order effect is conditional on (model × ticker × regime), NOT framework-general. The v1.5.2 randomize-or-document mandate stays AS-IS but is now explicit that effect varies by ticker. v1.5.2 → v1.5.3 (PATCH per scope-narrowing rule).
```

## Patch E — STAYS + re-evaluation trigger

**Trigger**: WC-11 v2 INCONCLUSIVE (v2 fails to reproduce v1 NVDA pattern at all).

**Mechanism**: PATCH v1.5.2 → v1.5.3 by adding "Re-evaluation trigger" note. v1.5.2 mandate STAYS but flagged for n≥200 future test.

```diff
**Version**: 1.5.2 → 1.5.3 (PATCH per scope-narrowing rule)
**Last amended**: 2026-05-10 (post-WC-11 v2) — added "Re-evaluation trigger at n≥200" note to Analyst-order scope sub-section. Empirical basis: WC-11 v2 (n=60 across 3 tickers) failed to reproduce v1 NVDA pattern; stochastic LLM variance dominates at this n. The v1.5.2 mandate remains operative as a precautionary stance, BUT future ablations targeting commit-rate may RE-EVALUATE if a future v3+ cohort at n≥200 still fails to surface the v1 pattern. v1.5.2 → v1.5.3 (PATCH per scope-narrowing rule).
```

## Operational decision rule (when v2 lands)

```python
# Pseudo-code for verdict-to-patch mapping
def select_patch(v2_verdict):
    return {
        "NULL_revised": "Patch B (REVERT)",
        "ALT-A_confirmed": "Patch A (STRENGTHEN)",
        "ALT-B_confirmed": "Patch C (STRENGTHEN)",
        "PARTIAL": "Patch D (CLARIFY)",
        "INCONCLUSIVE": "Patch E (RE-EVAL trigger)",
    }[v2_verdict]
```

When v2 lands:
1. Compute verdict per ANALYSIS_TEMPLATE.md falsification framework
2. Apply matching patch (this doc shows the diff in advance)
3. Cite `experiments/2026-05-09-002-wc11-v2-disambiguation/ANALYSIS.md` as empirical basis
4. Bump `**Version**` field per the matching patch
5. Add/remove paragraphs per the matching patch's diff

Estimated wall-clock from v2 landing → Constitution patch PR open: ~15 min (deterministic pick + plug-in).

## Pre-scaffolding ROI projection

Without this pre-scaffolding: ~30-45 min draft from scratch when v2 lands (5 verdict branches × 6-9 min each to articulate the diff).
With this pre-scaffolding: ~15 min deterministic pick + plug-in.
**Savings: ~15-30 min per branch** (only one patch ships).

Pattern continues to validate the conditional-branch pre-scaffolding ROI noted in `reference_conditional_branch_spec_pattern.md`.

## Cross-references

- `claudedocs/constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md` (sister; PR #144)
- `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md` (v1; PR #177)
- `experiments/2026-05-09-002-wc11-v2-disambiguation/HYPOTHESIS.md` + `ANALYSIS_TEMPLATE.md` (v2)
- `claudedocs/dual-pilot-launch-playbook-2026-05-09.md` (PR #214 landing playbook)
- Constitution VII v1.5.2 "Analyst-order scope" sub-section (current; PR #179)
- Memory: `reference_conditional_branch_spec_pattern.md` (PR #151)
