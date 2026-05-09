# WC-10 underperformance monitor — v2 cross-corpus extension scope design

**Date**: 2026-05-09
**Trigger**: reasoning_decision rank #3O (0.775 score). Design doc for the cross-corpus extension identified as future work in `claudedocs/wc-10-underperformance-monitor-smoke-test-post-branch-c-2026-05-09.md` (PR #186).
**Status**: design only; NOT shipped. Implementation deferred per Cost-vs-yield analysis below.
**Cost**: $0 (design doc only).

## Problem statement

Per PR #186 audit, `scripts/wc_10_underperformance_monitor.py` (PR #146) requires PAIRED rows per (ticker, date) — both `wc_10` mode and `5tier_baseline` mode present in the same CSV. v1 (`experiments/2026-05-08-001-wc-10-pilot/results.csv`) was designed paired (40 rows = 20 wc_10 + 20 5tier); v2 (`experiments/2026-05-08-002-wc-10-v2-ticker-expansion/results.csv`) was designed wc_10-only (80 rows, no 5-tier column) per Constitution III T2 cost discipline.

The monitor exits with "Paired rows: 0" on v2's CSV → no comparison possible without a cross-corpus pairing extension.

## Empirical yield analysis (corpus walk performed today)

Walked `experiments/*/results.csv` (excluding WC-10 experiments themselves) to count overlap with v2's 80 (ticker, date) keys:

| Source experiment | Matched rows | Notes |
|---|---:|---|
| **2026-05-02-006-wc12-cross-msft** | 20 | WC-12 PM-blind variant on MSFT (mode-altering — NOT directly comparable) |
| **2026-05-03-007-opus47-30pair-mixed** | 20 | Opus 4.7 baseline on Q1 2026 dates — **directly comparable** |
| **2026-05-08-004-wc11-order-randomization** | 20 | WC-11 (4-permutation; filter to DEFAULT only → 5 directly comparable) |
| **2026-05-09-001-br3-squeak-market-analyst** | 20 | BR-3 (2-mode; filter to "prose" mode only → 10 directly comparable) |
| 2026-05-02-002-wc12-pm-blind | 10 | WC-12 NVDA — NOT directly comparable (config-altered) |
| 2026-05-02-004-mr3-synthesis-v2 | 10 | MR-3 prompt variant — NOT directly comparable |
| 2026-05-02-005-wc12-cross-aapl | 10 | WC-12 AAPL — NOT directly comparable |
| 2026-05-02-007-brave-news-smoke | 10 | DEFUNCT brave news vendor — NOT directly comparable |
| 2026-05-03-001-brave-news-smoke-aapl | 10 | DEFUNCT brave news vendor — NOT directly comparable |
| 2026-05-03-002-exa-news-smoke-aapl | 10 | exa news smoke (config-altered) |
| 2026-05-03-003-single-call-baseline-nvda | 10 | single-call architectural variant — NOT directly comparable |
| 2026-05-03-004-single-call-baseline-aapl | 10 | single-call — NOT directly comparable |
| 2026-05-03-005-opus47-swap-nvda | 10 | **directly comparable** (model-swap baseline) |
| 2026-05-03-006-opus47-swap-aapl | 10 | **directly comparable** (model-swap baseline) |
| 2026-05-05-003-signal-at-scale | 7 | SC-003 50-ticker single-date — partially comparable |
| 4 misc smoke experiments | 4 | individual rows; trivial |
| **TOTAL ROW-INSTANCES** | **191** | — |
| **Directly-comparable subset** | **~55** | (20 + 5 + 10 + 10 + 10 = 5 sources × directly-comparable rows) |

The directly-comparable subset (~55 paired rows) is meaningfully larger than the ~30-40 estimate in PR #186, but still well below the n≥200 threshold cited as the deferral criterion.

## Comparability gotchas

1. **DEFAULT-config-only**: per WC-11 finding (Constitution v1.5.2), analyst-order is a confounder. Cross-corpus pairing must restrict to DEFAULT order only. WC-11's 20-row contribution shrinks to 5 (the 1 of 4 permutations that matches DEFAULT).

2. **DEFAULT-data-vendor-only**: brave news (deprecated 2026-05-03) experiments use DIFFERENT data → 30 of 191 rows excluded.

3. **DEFAULT-prompt-only**: MR-3 + WC-12 + single-call experiments use altered prompts/configs → another 50+ rows excluded.

4. **Filter-portfolio-version-mismatch**: experiments dated BEFORE 2026-05-06 ran with empirical filters OFF; experiments AFTER 2026-05-06 had A3 + Spec 003 + 003.5 active. v2 was filter-bypass mode. Cross-corpus pairs must account for filter-cohort-version when interpreting Δα. Solution: bin v2 to 5-tier, then compare against the filter-bypass-equivalent rating (which for the prior corpus means the `pre_rating` not `post_rating`).

5. **Memory-log non-isolation**: prior experiments shared memory log writes; v2 had memory-log isolation. Memory-log content can subtly affect PM decision per the Constitution VIII v1.4.5 memory-log-discipline framework. Risk: 5-tier baseline rows from same-day-cluster experiments may be biased by accumulated memory entries.

## Implementation shape (when shipped)

### CLI extension

```
python scripts/wc_10_underperformance_monitor.py \
  --csv experiments/2026-05-08-002-wc-10-v2-ticker-expansion/results.csv \
  --cross-corpus \
  --baseline-corpus-glob "experiments/2026-05-03-007-opus47-30pair-mixed/results.csv,experiments/2026-05-03-005-opus47-swap-nvda/results.csv,experiments/2026-05-03-006-opus47-swap-aapl/results.csv" \
  --baseline-config-filter "default-prompt,default-vendor,default-order,filter-bypass-aware"
```

### Module changes

`scripts/wc_10_underperformance_monitor.py`:
- New function `_load_cross_corpus_baseline()` accepting glob pattern + config-filter spec
- New CLI flag `--cross-corpus` enabling the cross-corpus path
- New CLI flag `--baseline-corpus-glob` (comma-separated list of CSVs)
- New CLI flag `--baseline-config-filter` (comma-separated comparability checks)
- New stderr warning when matched-pair count < N (e.g., 10) — operator should expand baseline corpus before relying on small-n alerts

### Per-pair Δα computation

Same as existing single-CSV path; bin v2's wc_10 scalar to 5-tier via `bin_scalar_to_tier()` BEFORE comparison; treat the 5-tier baseline rating as the comparison anchor. Output table format unchanged.

## When to ship

**Defer until ANY of**:

1. Corpus growth to n≥200 paired-comparable rows (per RESEARCH_FINDINGS Open Questions v4+ expansion entry). Current directly-comparable count is ~55.
2. Concrete operator need for cross-corpus comparison (e.g., investigating why a specific ticker × date in v2 underperforms baseline).
3. New v3+ WC-10 cohort that's wc_10-only AND requires cross-corpus comparison for verdict (would need to budget both the new cohort cost + this script extension).

The 55-row directly-comparable subset is meaningful but doesn't yet support strong statistical claims:
- Per Constitution VII Replicability scope: bucket-level claims hold; date-level claims are within run-to-run stochastic variance bounds.
- Run-to-run variance on identical inputs (005-vs-007 NVDA case: 10/10 OW → 6/10 OW + 4 Hold) suggests cross-experiment Δα at small n risks being dominated by stochastic variance rather than the WC-10 effect.

**Implementation effort estimate**: ~2-3 hours for the cross-corpus pairing logic + CLI integration + 4-5 unit tests + documentation. Deferred work has been in this state since PR #186 (yesterday-by-calendar / today-by-clock); shipping cost is small but the value is gated on corpus growth or concrete operator need.

## Alternative: per-experiment baseline regeneration

A different approach to the same problem: re-run a SUBSET of v2's 80 propagates in 5-tier mode (e.g., 20 of 80 = $8 LLM) to create paired rows directly. This avoids cross-corpus comparability gotchas entirely.

**Cost-vs-effort comparison**:

| Approach | $ Cost | Time | Pros | Cons |
|---|---:|---|---|---|
| Cross-corpus extension | $0 | 2-3h | Reuses existing data | Comparability gotchas; ~55 directly-comparable rows max |
| Re-run 20-row baseline | $8 | overnight | Clean paired data; no gotchas | $8 budget; data lag |
| Re-run full 80-row baseline | $32 | overnight | Maximum statistical power | $32 budget; 50% bigger than v2 itself |

**Recommendation when shipping**: prefer the 20-row re-run baseline ($8) over the cross-corpus extension. The $8 buys clean data without the comparability-gotcha analysis overhead, and the resulting CSV directly drops into the existing monitor's paired-row path. The cross-corpus extension is only worth building if multiple future v_N runs need it (amortized value increases with reuse count).

## Cross-references

- WC-10 monitor smoke test post-Branch C: `claudedocs/wc-10-underperformance-monitor-smoke-test-post-branch-c-2026-05-09.md` (PR #186 — identifies the v2 cross-corpus extension as future work)
- WC-10 v2 ANALYSIS: `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md` (PR #181)
- Constitution VII Replicability scope (date-level vs bucket-level claim distinction)
- Constitution VIII v1.4.5 memory-log discipline (memory-log non-isolation risk)
- Constitution v1.5.2 Analyst-order scope (DEFAULT-order-only filter)
- RESEARCH_FINDINGS.md Open Questions table — v4+ corpus expansion entry
