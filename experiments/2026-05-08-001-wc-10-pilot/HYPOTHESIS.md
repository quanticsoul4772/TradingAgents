# WC-10 Continuous Scalar Rating — v1 pilot HYPOTHESIS

**Experiment ID**: `2026-05-08-001-wc-10-pilot`
**Source idea**: WC-10 (per `docs/EXPERIMENT.md` Tier 2)
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/`
**Date**: 2026-05-08

## Question

Does replacing the framework's 5-tier categorical `PortfolioRating` enum with a continuous scalar in `[-1, +1]` change the rating distribution in a way that surfaces signal the categorical scale was throwing away?

## 3 falsifiable predictions (per spec.md SC-007)

| Prediction | What it means | Empirical signature |
|---|---|---|
| **NULL** | Continuous scalar doesn't change behavior; framework outputs cluster near 0 (=Hold) at the same rate as 5-tier collapse to Hold. Calibrated Abstention is genuine. | Fraction of `\|rating\| > 0.2` (= committed) ≈ fraction of non-Hold in 5-tier baseline |
| **ALT-A** | Distribution less collapsed; bull/bear signal that 5-tier scale was throwing away surfaces in scalar magnitude. Categorical bottleneck confirmed. | Fraction `\|rating\| > 0.2` SUBSTANTIALLY > fraction of non-Hold in 5-tier baseline |
| **ALT-B** | Continuous scalar bins ex-post to match 5-tier distribution. Calibrated abstention is mode-collapsed regardless of output type. | Per-bucket means after `bin_scalar_to_tier()` ≈ per-bucket means in 5-tier baseline (within ±150 bps) |

At least ONE prediction must be empirically distinguishable. INCONCLUSIVE is permitted under Constitution Principle IV.

## Test grid

10 dates × 2 tickers × 2 modes = **40 propagates**.

- **Tickers**: NVDA + AAPL (rich existing 5-tier baseline corpora)
- **Dates**: 2026-04-01 through 2026-05-01 weekly Friday cadence (10 dates)
- **Modes**:
  - `wc_10_enabled=True` + `wc_10_filter_mode="bypass"` (WC-10 v1)
  - `wc_10_enabled=False` (5-tier baseline; same dates for direct comparison)

## Cost estimate

40 propagates × ~$0.40 = **~$16 LLM**. Constitution III T2 (≤$30).

## Headline metrics (per spec.md SC-005)

1. **Fraction of `|rating| > 0.2`** in WC-10 mode vs **fraction of non-Hold** in 5-tier baseline mode
2. **Signed-rating × 21d-forward-α correlation** (Pearson + Spearman)
3. **Bin-ex-post-to-5-tier** (via `bin_scalar_to_tier()`) and compare bucket means to 5-tier baseline

## Falsification verdict (per SC-007)

Determined post-run; documented in `ANALYSIS.md`. One of: NULL / ALT-A / ALT-B / INCONCLUSIVE.

## Constitution adherence

- II One Experiment Per Change: SINGLE intervention (schema)
- III Stay Cheap: T2 ≤$30; total ~$16
- IV No Production Claims: NULL/INCONCLUSIVE valid
- VI Spec Before Structural Change: per PRs #107/#108/#109
- VII Calibrated Abstention: directly tests VII
