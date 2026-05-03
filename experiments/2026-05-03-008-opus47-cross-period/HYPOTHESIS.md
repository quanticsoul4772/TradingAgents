# Hypothesis: opus47-cross-period

**Experiment ID**: `2026-05-03-008-opus47-cross-period`
**Created**: 2026-05-03
**Source idea**: B-priority 2 per ANALYSIS-007: tests period-specificity of n=50 OW signal + per-ticker discrimination on shifted date range
**Cost estimate**: ~$30.00
**Cost tier**: T3 (scaled, $30 – $100)

## What we're testing

Cross-period validation of the n=50 21d-OW signal and the per-ticker discrimination pattern from 005/006/007. **Knob varied**: date range only. Same tickers (NVDA + AAPL + INTC), same model (Opus 4.7 deep + Haiku 4.5 quick), same A3 momentum filter (-5%/30d), same prompt structure, same news vendor (exa). Baseline is 007 (which used dates 2026-01-30 → 2026-04-03). This experiment shifts the grid to **2025-11-07 → 2026-01-09** (10 weekly Fridays prior to the 005/006/007 grid), giving 30 propagations matched 1:1 against 007 on every dimension except calendar period.

## Why we expect period-persistent bull-side signal + per-ticker discrimination

The 005/006/007 chain established three claims at the n=50 / 14-experiment milestone:

1. **OW 21d α is +1.99% (n=50, 65% hit)** — load-bearing across NVDA + AAPL + INTC + 9 prior experiments
2. **Per-ticker bucket distribution is regime-shaped** — Opus → ≥60% OW on bull-regime tickers, ≥70% Hold on mixed-regime tickers, ≥60% UW on bear-regime tickers
3. **Bear-side commits on bear-correct tickers are mostly directionally appropriate** when single-event tail outliers are excluded

If these claims are period-general (not specific to Q1 2026), then on a Q4 2025 grid we expect to see the same pattern: bull-regime tickers commit OW with positive 21d α, mixed-regime tickers hold, bear-regime tickers commit UW. The Q4 2025 regime context is different (different macro backdrop, different ticker-specific stories), so this is a real out-of-sample test rather than a rerun.

## Predicted findings

**Scenario A (period-general; signal persists)** — most likely, ~55%
- OW 21d α stays > +1.0% on the 008 grid alone
- Cross-experiment OW 21d α (now incorporating 008) stays > +1.5% n=80
- Bucket distribution per-ticker matches the 007 shape directionally (bull/mixed/bear → OW/Hold/UW leaning)
- Decision: signal validated as period-persistent; framework's 21d bull-side α is a stable property within the tested model+config

**Scenario B (signal partially dilutes)** — ~25%
- OW 21d α on 008 alone lands +0.3% to +1.0%
- Cross-experiment α drops to +1.3-1.7% range
- Decision: signal real but smaller than 005-007 suggested; investigate whether Q4 2025 had less directional clarity than Q1 2026, or whether the 005-007 result was period-favored

**Scenario C (signal collapses on shifted period)** — ~15%
- OW 21d α on 008 alone lands < +0.3% or negative
- Decision: 005-007 was period-specific; the n=50 milestone was sample-favored; reframe Q1 + Constitution VII to acknowledge period-conditional signal

**Scenario D (per-ticker discrimination fails)** — ~5%, orthogonal to A/B/C
- Bucket distributions don't match the 007 regime-shape (e.g. INTC produces OW commits, NVDA produces UW)
- Decision: discrimination is not regime-driven but data-noise-driven; reframe per-ticker claims

## Cost Justification (required for T3 / T4 — Constitution III)

**Why this scale** (vs. a smaller pilot):

Cross-period validation needs n large enough to distinguish "period-general signal" from "period-specific lucky-stretch." A 10-pair pilot (T2 ~$10) would produce per-bucket n of 2-7, too small to test claim (1) above with any power. The 30-pair scale matches 007 exactly, which makes the comparison apples-to-apples and adds 30 fresh observations to the cross-experiment corpus, taking it from n=50 to ~n=80 for the OW bucket. That's the n needed to credibly say "the signal is period-general."

**Cheaper alternatives considered** (and why rejected):

- **10-pair single-ticker pilot ($5-10, T2)**: too small to test both bucket distribution AND α magnitude with statistical power. Would produce inconclusive results either way.
- **30-pair single-ticker (only NVDA, $10 T2)**: tests OW-magnitude only, loses the per-ticker discrimination test. The discrimination claim is the more novel contribution from 006/007.
- **20-pair 2-ticker (NVDA + INTC, $20 T2)**: misses AAPL mixed-regime discrimination. Could land here as a fallback if T3 spend is denied.
- **Re-analysis of 007 alone (no new spend)**: doesn't address period-specificity at all.

**Outcome that would justify the spend**:

Cross-experiment OW 21d α stays > +1.5% at n=80 with hit rate ≥ 60%, AND bucket distribution per-ticker on 008 matches the 007 regime-shape directionally (NVDA OW-leaning, AAPL Hold-leaning, INTC UW-leaning). This would be the strongest single-experiment update to the load-bearing claim since 007 itself.

## Success criterion

- [ ] 30 propagations complete (10 each for NVDA, AAPL, INTC) with 0 errors
- [ ] horizon_sweep on the new CSV — per-experiment + cross-experiment update
- [ ] Per-ticker distribution tabulated against 007's distribution
- [ ] OW 21d α reported alone + cross-experiment merged
- [ ] EH-2 gate output recorded
- [ ] A3 filter activations counted (expect ≤ 3 given prior INTC behavior)
- [ ] Decision per scenario A/B/C/D
- [ ] Total cost ≤ $35 (small margin for retries)

## Notes

- **Date range chosen**: 2025-11-07 → 2026-01-09 (10 weekly Fridays). Picked for adjacency to 005-007 grid (no major regime epoch shift) while being a clean out-of-sample window.
- **Forward-21d data availability**: 2026-01-09 + 21 trading days ≈ 2026-02-09; we are at 2026-05-03 with ~3 months of post-grid data. All commits will resolve.
- **A3 filter ON** at -5%/30d (matches 007); helps validate that filter behavior is period-general.
- **Cost-tier first end-to-end test**: this is the first experiment scaffolded with the `--tier T3` flag from Constitution v1.2.0/v1.2.1. Validates the Cost-Justification scaffold as a functioning checklist.
- **Memory log**: fresh `backtest_memory.md` per 007 convention; no carryover.

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (period-general) | Strongest possible outcome. Mark Q1 (n=100+ scaling) as fully resolved positive. Update RESEARCH_FINDINGS to assert OW 21d α is period-persistent claim at n=80. Next: Phase C operationalization or Phase D substrate exploration. |
| Scenario B (partial dilution) | Investigate Q4 2025 regime characteristics; consider 008 as one-of-many windows needed for full period coverage. Plan a third cross-period pass at lower priority. |
| Scenario C (signal collapses) | Major reframe: 005-007 was period-favored. Constitution VII needs another amendment. Consider whether n=50 milestone claim was over-stated. |
| Scenario D (discrimination fails) | Per-ticker claims need reframing; the regime-shape pattern may be specific to the 005-007 ticker behavior in that period. |

## Related experiments

- **005 opus47-swap-nvda**: 10 OW (Q1 2026), 21d α +2.85% n=9
- **006 opus47-swap-aapl**: 8 Hold + 2 OW (Q1 2026), 21d α -0.07% n=2
- **007 opus47-30pair-mixed**: 9 OW + 15 Hold + 6 UW (Q1 2026), cross-experiment OW now n=50, +1.99%, 65% hit
- **A3 productionized** (commit 041786e): filter wired in PortfolioManager
- **A3 forensics on 007** (commit 6f04bdd): filter validated as correctly inert on regime-mismatch failure mode
