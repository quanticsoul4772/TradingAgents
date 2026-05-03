# Hypothesis: opus47-30pair-mixed

**Experiment ID**: `2026-05-03-007-opus47-30pair-mixed`
**Created**: 2026-05-03
**Source idea**: ROADMAP active branch — out-of-sample validation of the 21d bull lift (005) + per-ticker discrimination (006), at scale and across regime types.
**Cost estimate**: ~$30 (30 propagations × ~$1 with Opus 4.7, ~3.5h wall-clock)

## Cost deliberation (Principle III)

This experiment sits **AT** the Constitution Principle III ceiling of $30 per session. Justification for spending the full ceiling on a single experiment:

1. The 21d bull-side α claim (+1.79% across n=41) is currently the project's most load-bearing finding. Out-of-sample validation at scale is the right place to spend the budget.
2. Cross-experiment OW commits are heavily NVDA-anchored (n=37 of 41 are on NVDA). A 30-pair mixed-ticker run roughly doubles the n and tests cross-regime generalization.
3. 005 + 006 produced contradictory commit-rates (10/10 OW vs 2/10 OW on the same model). A clean basket-test discriminates "Opus generalizes per ticker" from "Opus is unstable across tickers."
4. The A3 filter has been wired and unit-tested but never validated end-to-end on a fresh run with multiple bear-leaning ticker dates.

Falls within the per-session ceiling; does not require Constitution amendment.

## What we're testing

Three questions in one run:

1. **Does the 21d OW α signal hold at scale?** — currently anchored on n=37 NVDA-heavy commits. After this run we'll have n=37 + ~10-30 fresh commits (depending on Opus distribution per ticker). If OW 21d α stays > +1%, the signal is robust.
2. **Does per-ticker discrimination produce a clean cross-regime distribution?** — expectation per ROADMAP:
   - NVDA → mostly OW (per 005 pattern, bull regime)
   - AAPL → mostly Hold + some OW (per 006 pattern, mixed regime)
   - INTC → mostly Hold or some UW (untested; INTC has been bear-leaning per its multi-quarter slide)
3. **Does the A3 momentum filter behave correctly on a mixed run?** — INTC has been deeply down (the filter SHOULD suppress any UW commits the framework produces). Tests the wiring + the filter's appropriateness on a real bear-leaning ticker.

## Predicted findings

**Scenario A (signal holds + clean discrimination + filter helps)** — most likely, ~50%
- NVDA: 8-10 OW commits, 21d α > +1.5%
- AAPL: ~5-7 Hold + ~2-4 OW, OW 21d α near zero
- INTC: ~7-9 Hold + 1-2 UW (at least 1 suppressed by filter), 0-1 OW
- Cross-experiment OW 21d α stays > +1.0% (load-bearing)
- Decision: signal validated, framework demonstrably works at the 21d horizon on bull-regime tickers; documents the regime-conditional caveat

**Scenario B (signal partially dilutes)** — ~30%
- NVDA still strong but smaller-magnitude
- AAPL + INTC contribute mostly Hold + low-α commits
- Cross-experiment OW 21d α drops to +0.5-1.0%
- Decision: signal real but smaller than 005 suggested; need cross-period validation next

**Scenario C (signal collapses)** — ~15%
- NVDA OW lift doesn't replicate even on the same dates with same model
- Cross-experiment OW 21d α drops < +0.5%
- Decision: 005 was a sample-period artifact; reframe needed

**Scenario D (filter misfires badly)** — ~5%, orthogonal to A/B/C
- Filter suppresses commits that would have been correct on INTC
- Suppressed commits' 21d α was negative (correctly bearish)
- Decision: filter threshold needs tuning; A3 in-sample win was period-specific

## Success criterion

- [ ] 30 propagations complete (10 each for NVDA, AAPL, INTC)
- [ ] horizon_sweep on the new CSV — per-experiment + cross-experiment update
- [ ] Per-ticker distribution tabulated
- [ ] A3 filter activations counted (how many UW commits suppressed?)
- [ ] EH-2 gate output recorded
- [ ] Decision per scenario A/B/C/D

## Notes

- **Same 10 dates as all prior NVDA + AAPL experiments** — keeps comparability with 005 + 006.
- **INTC** chosen as bear-leaning ticker because (a) it's been in a multi-quarter slide, providing real bear-side evidence the framework can read, (b) it's same sector as NVDA (semis) so sector-rotation noise is shared between bull and bear pairs.
- **A3 momentum filter ENABLED** at threshold -5% for the first time in a backtest. Will write a note in ANALYSIS counting filter activations and their per-date impact.
- **Quick model unchanged** (Haiku 4.5).
- **Error budget**: 0/30 errors target. Opus has been reliable on prior runs (1 retry on 005 run 9).

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (signal + discrimination + filter helps) | Strongest possible outcome. Update RESEARCH_FINDINGS to mark Q1 (scale) as resolved positive. Write project-level summary + push. |
| Scenario B (partial dilution) | Schedule 30-pair cross-period validation (different date range) at $30 to triangulate. |
| Scenario C (signal collapses) | Major reframe: 005 was sample-period luck. Constitution Principle VII needs another amendment. |
| Scenario D (filter misfires) | Disable filter default, document threshold tuning as open work. |

## Related experiments

- **005 opus47-swap-nvda**: 10/10 OW, 21d α +2.85% n=9 78%
- **006 opus47-swap-aapl**: 8 Hold + 2 OW, 21d α -0.07% n=2 50%
- **All prior AAPL/NVDA Sonnet experiments**: same 10 dates, framework comparison baseline
- **A3 productionized** (commit 041786e): filter wired in PortfolioManager, gated by config flag
