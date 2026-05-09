# WC-10 Bear-Regime Test — Q4 2025 NVDA HYPOTHESIS

**Experiment ID**: `2026-05-08-003-wc-10-bear-regime-q4-2025-nvda`
**Source**: ranked next-step from reasoning_decision (rank #7; user-authorized 2026-05-08 evening after rank #5 v2 expansion kicked off)
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/` (same as v1 + v2)
**Predecessors**:
- `experiments/2026-05-08-001-wc-10-pilot/` (v1 pilot, n=20 paired)
- `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/` (v2 in-flight)
- `experiments/2026-05-03-008-opus47-cross-period/` (Q4 2025 NVDA 5-tier baseline corpus, Opus model)

**Date**: 2026-05-08

## Question

WC-10 v1 showed asymmetric calibration: bullish-side amplification was well-calibrated (NVDA Buy n=6 mean +4.67% α 21d), bearish-side amplification was anti-calibrated (AAPL UW n=6 mean +3.56% α — UW called bearish but ticker rose +3-6%). The v1 caveat in ANALYSIS.md noted: "WC-10 doesn't fix bear-side calibration; it amplifies whatever signal the framework was already generating."

This experiment directly tests that caveat by running WC-10 on **Q4 2025 NVDA** — the period where the framework's commits FAILED most clearly per the corpus headline (5-tier 21d α = -0.47% n=9, 22% hit rate). Per experiment 008, Opus on Q4 2025 NVDA went 7/8 Overweight + 1 Hold. The bullish-leaning commits were directionally wrong (NVDA fell over the period).

## Three predictions (paralleling v1's SC-007 framework)

| Prediction | What it means | Empirical signature |
|---|---|---|
| **NULL (regime-neutral)** | WC-10 makes Q4 2025 NVDA outcomes statistically indistinguishable from 5-tier baseline. Schema fix has no regime-conditional effect. | mean WC-10 21d α ≈ mean 5-tier 21d α (within ±100 bps) |
| **ALT-A (bear-regime AMPLIFIES failure)** | WC-10 commits MORE bullishly on Q4 2025 NVDA (matching v1's 90% commit rate + 008's 7/8 OW) → more wrong-direction commits → WORSE realized α. Schema fix is regime-conditional. | WC-10 commit rate ≥ 80%, WC-10 mean 21d α < 5-tier mean 21d α by ≥ 100 bps |
| **ALT-B (bear-regime CORRECTS direction)** | WC-10 surfaces bearish reads on Q4 2025 NVDA that 5-tier was suppressing. Schema fix surfaces direction-correct signal independent of bull/bear regime. | WC-10 commit rate ≥ 80%, ≥ 30% of WC-10 commits bin to UW/Sell, WC-10 mean 21d α > 5-tier by ≥ 100 bps |

If outcomes are mixed (e.g., ALT-A on direction but no statistical α difference), the verdict is **PARTIAL ALT-A** — WC-10 amplifies framework reads with regime-asymmetric calibration, exactly as the v1 caveat predicted.

## Test grid

8 dates × 1 ticker × 2 modes = **16 propagates**.

- **Ticker**: NVDA only (concentrate sample on the period's hardest case)
- **Dates** (8, matching experiment 008's Q4 2025 cohort for direct cross-experiment comparison): 2025-11-07, 2025-11-14, 2025-11-21, 2025-11-28, 2025-12-05, 2025-12-12, 2025-12-19, 2025-12-26
- **Modes**: WC-10 + 5-tier baseline (paired)

Note: 008 used Opus 4.7; this experiment uses Sonnet 4.6 (matching v1 + v2). Direct numerical comparison to 008 is approximate; the within-experiment WC-10 vs 5-tier comparison is the load-bearing measurement.

## Cost estimate

16 propagates × ~$0.40 = **~$6.40 LLM**. Constitution III T1 (≤$10).

## Headline metrics

1. **(Primary) Mean 21d α delta**: `mean_α(WC-10) - mean_α(5-tier)`. Sign + magnitude determines NULL / ALT-A / ALT-B verdict.
2. **(Secondary) Direction distribution**: WC-10 binned tier counts vs 5-tier rating counts. Tests whether WC-10 amplifies the same direction as 5-tier (ALT-A pattern) or surfaces a different direction (ALT-B pattern).
3. **(Tertiary) Per-date paired α delta**: for each date, `α(WC-10_binned_tier) - α(5tier_rating)` mapped via the corpus's per-bucket means. Identifies any single-date outlier driving the aggregate.

## Falsification verdict

Determined post-run; documented in `ANALYSIS.md`. The verdict feeds back into the Constitution VII v1.5.0 amendment's WC-10 caveat:

- ALT-A confirmation → strengthens v1.5.0 caveat that bear-regime validation IS load-bearing for universalizing the schema fix
- ALT-B confirmation (unlikely per v1 pattern) → weakens the caveat; WC-10 may be universally beneficial
- NULL → schema fix is regime-neutral; the v1.5.0 caveat may be over-cautious

## Constitution adherence

- I (Save Everything): full per-propagate state log + this HYPOTHESIS + PARAMS + results.csv + ANALYSIS.md
- II (One Experiment Per Change): same intervention as v1 + v2 (continuous-scalar schema). v3 differs only in cohort (bear regime).
- III (Stay Cheap): T1 (≤$10) at $6.40. No deliberation override needed.
- IV (No Production Claims): bear-regime result informs the universalize-or-not decision; does not commit
- VI (Spec Before Structural Change): no spec change; reuses spec 108 design with bear-regime cohort
- VII (Calibrated Abstention v1.5.0): direct test of the v1.5.0 amendment's regime-asymmetry caveat

## Operational note

Reuses `scripts/wc_10_pilot.py` with `--tickers NVDA`, the 8-date list, both modes, and `--out experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv`. No code change needed.

Estimated wall-clock: 16 propagates × ~9 min = ~2.5 hours.

Note: this experiment is INDEPENDENT of the v2 expansion (different cohorts, different output paths). Both can run concurrently.
