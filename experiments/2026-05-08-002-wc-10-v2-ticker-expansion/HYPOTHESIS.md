# WC-10 Continuous Scalar Rating — v2 ticker expansion HYPOTHESIS

**Experiment ID**: `2026-05-08-002-wc-10-v2-ticker-expansion`
**Source**: ranked next-step from reasoning_decision (rank #5; user-authorized after rank #1+#2 codification work shipped via PRs #131 + #132)
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/` (same as v1)
**Predecessor**: `experiments/2026-05-08-001-wc-10-pilot/` (v1 pilot, n=20 paired)
**Date**: 2026-05-08

## Question

v1 confirmed SC-007 ALT-A (categorical-bottleneck-confirmed) at distribution level (3.6× commit ratio, 75% paired-decision-changed). But SC-005(b) — signed-rating × 21d-α correlation — was INCONCLUSIVE at n=20 (Pearson r=+0.065, Spearman ρ=+0.009; critical r at n=20/p=0.05 = 0.444, far above observed). v2 expands n→100 in WC-10 mode to test:

1. **(Primary) Does scalar magnitude predict α magnitude at meaningful n?** Critical r at n=100/p=0.05 drops to ~0.197. If the true correlation is in the 0.10-0.20 range, v2 may still miss it. If it's >0.20, v2 should detect it. If r remains near 0 at n=100, the verdict tightens to "scalar magnitude carries no information beyond the binary commit-vs-abstain decision the bin already captures."

2. **(Secondary) Does the categorical bottleneck (v1 ALT-A) generalize across tickers beyond NVDA + AAPL?** v1 was 2-ticker; v2 adds 6 tickers spanning mega-cap tech (MSFT, GOOG, AMZN), financials (JPM), healthcare (JNJ), energy (XOM). The 90% commit rate observed in v1 is hypothesized to generalize; if some sectors collapse to Hold even under continuous-scalar mode, that's evidence the schema artifact is partially ticker-specific.

## Test grid

8 tickers × 10 dates × 1 mode (WC-10 only) = **80 propagates**.

- **Tickers** (8): NVDA, AAPL, MSFT, GOOG, AMZN, JPM, JNJ, XOM
- **Dates** (10): weekly Fridays 2026-01-30 → 2026-04-03 (Q1 2026 — predates v1's April dates; ample 21d realization for analysis at any time after 2026-05-08)
- **Mode**: `wc_10_enabled=True` + `wc_10_filter_mode="bypass"` (matching v1 design — isolates schema effect from filter behavior)

5-tier baseline mode is NOT re-run for v2. v1 paired baseline (n=20) is retained as the SC-006 reference; v2 adds 80 unpaired WC-10 datapoints purely for SC-005(b) correlation power and ticker-generalization at distribution level.

## Combined n at analysis time

- WC-10 mode: 20 (v1) + 80 (v2) = **n=100**
- 5-tier baseline mode: 20 (v1; unchanged) — paired comparison stays at v1 sample
- Tickers covered: 8 (NVDA, AAPL + 6 new from v2)
- Date coverage: Q1 2026 (v2: Jan 30 - Apr 3) + April 2026 (v1: Apr 1 - Apr 30); minimal overlap (NVDA + AAPL on Apr 1 + Apr 2 are duplicated, but weekly cadence keeps the rest disjoint)

## Cost estimate

80 propagates × ~$0.40 = **~$32 LLM**.

**Constitution III deliberation**: $32 exceeds the default T2 cap of ≤$30 by $2. The cost overshoot is explicitly authorized by the operator (per reasoning_decision rank #5 selection 2026-05-08 evening). The marginal $2 is justified by:

1. Reaching exactly n=100 (the SC-005(b) statistical-power threshold) requires the full 8×10 grid; truncating to 7×10 = 70 propagates would leave n=90 (under threshold) at $28 cost.
2. The bullish-side amplification finding from v1 (NVDA Buy n=6 mean +4.67% α) is the most architecturally consequential WC-10 result. Confirming or refuting it on a wider ticker basis requires diversification beyond NVDA + AAPL.
3. Cost asymmetry favors completing the run: each previously-spent dollar (v1's $16) becomes more interpretable with the additional sample, while marginal new spend is small relative to total knowledge yield.

Per Constitution III, this deliberation block satisfies the "explicit deliberation in HYPOTHESIS.md" requirement for crossing the cap.

## Headline metrics (per spec.md SC-005)

1. **(Primary, SC-005b)** Signed-rating × 21d-forward-α Pearson + Spearman correlation across the pooled n=100 WC-10 cohort. Critical r at n=100/p=0.05 = ±0.197. Verdicts:
   - `|r| > 0.30`: STRONG signal (scalar magnitude meaningfully predicts α magnitude)
   - `0.197 < |r| < 0.30`: MODERATE signal (statistically detectable but small effect size)
   - `|r| < 0.197`: NULL on (b) (scalar carries no information beyond binary commit decision)

2. **(Secondary, SC-007 ALT-A generalization)** Per-ticker fraction of `|rating| > 0.2`. Hypothesis: ≥6 of 8 tickers exhibit ≥80% commit rate (matching the v1 NVDA pattern). Counter-finding: any ticker that collapses to Hold even under continuous-scalar mode would suggest the schema bottleneck is ticker-specific.

3. **(Tertiary)** Per-bucket realized 21d-α via `bin_scalar_to_tier()`. Compares v2 bullish-bucket mean to v1 (NVDA Buy +4.67%) — does the bullish-side amplification quality generalize beyond NVDA?

## Falsification verdict (per SC-007 v2)

Determined post-run; documented in `ANALYSIS.md`. Beyond the SC-005(b) verdict above, v2 also re-tests v1's ALT-A confirmation on the broader ticker base.

## Constitution adherence

- I (Save Everything): full per-propagate state log + this HYPOTHESIS + PARAMS + results.csv + ANALYSIS.md
- II (One Experiment Per Change): same intervention as v1 (continuous-scalar schema). v2 is a SCALE expansion, not a separate intervention.
- III (Stay Cheap): T2-boundary at $32; explicit deliberation above per the principle's escape hatch
- IV (No Production Claims): v2 does not commit to deploying WC-10 in production; it informs the architectural decision
- VI (Spec Before Structural Change): no spec change; v2 is a re-run of the existing spec 108 design with expanded grid
- VII (Calibrated Abstention v1.5.0): v2 directly extends the empirical case for v1.5.0's "schema-induced abstention" carve-out

## Operational note

v2 reuses `scripts/wc_10_pilot.py` (v1's harness) with `--tickers`, `--dates`, `--modes wc_10`, and `--out experiments/2026-05-08-002-wc-10-v2-ticker-expansion/results.csv` overrides. No code change needed. Resume-on-crash semantics from v1 carry over.

Estimated wall-clock: 80 propagates × ~9 min = ~12 hours.
