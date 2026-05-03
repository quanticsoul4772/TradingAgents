# Hypothesis: opus47-swap-aapl

**Experiment ID**: `2026-05-03-006-opus47-swap-aapl`
**Created**: 2026-05-03
**Source idea**: Pre-flight per ROADMAP active branch (post-005 result) — tests whether Opus's strong 21d OW signal on NVDA generalizes to AAPL (the bear-correct ticker per Q4) before committing $30 to the 30-pair re-pilot.
**Cost estimate**: ~$10 (10 AAPL propagations × ~$1 with Opus 4.7, ~80 min)

## What we're testing

Single variable: ticker NVDA → AAPL. Same model swap (Sonnet 4.6 → Opus 4.7), same 10 dates, same news vendor, same prompts. Mirrors experiment 005 (opus47-swap-nvda) which produced 10/10 Overweight with 21d OW α=+2.85% (n=9, 78% hit rate).

Why AAPL specifically:
- AAPL is the bear-correct ticker per Q4 per-ticker breakdown (UW @ 21d α=-0.18%, only ticker where framework UW commits were directionally correct)
- NVDA was bull-regime (UW @ 21d α=+6.35%, deeply anti-calibrated for bear commits)
- Tests whether the OW + 21d-correct pattern is bull-regime-specific or multi-regime

## Predicted findings

Three scenarios:

**Scenario A (Opus AAPL also OW-heavy with positive 21d α)** — ~50%
- Distribution similar to 005: heavy OW commit
- 21d OW α positive (~+1-3%)
- Implication: Opus's bull-side commit pattern is multi-regime, not just NVDA bull-regime artifact
- Decision: greenlight 30-pair Opus re-pilot at 21d ($30, 3.5h)

**Scenario B (Opus AAPL is mixed: some OW, some Hold/UW)** — ~30%
- Opus is more discriminating on AAPL than NVDA — produces some bear commits where the bear case is strong
- 21d α per bucket: depends on the mix
- Implication: Opus's mode collapse to OW was NVDA-specific; on AAPL Opus actually distinguishes bull vs bear evidence
- Decision: 30-pair re-pilot still worth running; expect more nuanced distribution

**Scenario C (Opus AAPL flips to UW/Hold dominant)** — ~20%
- Opus reads AAPL's bear-side evidence (memory chips, China headwinds, Evercore downgrade) and commits bearish
- 21d α: depends on direction
- Implication: 005's NVDA OW-collapse was bull-regime-specific; Opus does discriminate
- Decision: 30-pair re-pilot needs explicit ticker-mix design; may need to test on neutral-regime tickers

## Success criterion

- [ ] 10 AAPL Opus 4.7 propagations complete (0 errors target)
- [ ] Distribution comparison vs Sonnet AAPL pilot (3 Hold + 7 UW) and Opus NVDA (10 OW)
- [ ] horizon_sweep on results.csv → per-bucket 5d/10d/21d alphas
- [ ] EH-2 gate output recorded
- [ ] Per-date breakdown vs realized α at 21d (5 of these dates already known from prior AAPL analysis: 01-30 +7.38, 02-06 -6.66, 02-13 +3.97, 02-20 +0.35, 02-27 -0.56, 03-06 -1.35, 03-13 +0.95, 03-20 +2.56, 03-27 +0.13, 04-03 -3.99)
- [ ] Decision: 30-pair Opus re-pilot greenlit / needs revision

## Notes

- Same dates as all prior AAPL experiments (pilot, WC-12 cross-AAPL, brave-AAPL, exa-AAPL, single-call-AAPL).
- Quick model unchanged (Haiku 4.5).
- News vendor: yfinance (default). Per-vendor effect not the question here.
- AAPL realized 21d alphas span -7% to +15%, with mixed direction across the 10 dates. Opus has both bull AND bear evidence to choose from.

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (multi-regime confirmation) | 30-pair Opus re-pilot at 21d ($30) is well-grounded |
| Scenario B (Opus discriminates) | 30-pair re-pilot still go, with expectation of nuanced output |
| Scenario C (regime flip) | Revise 30-pair design; test broader ticker mix at smaller n first |

## Related experiments

- **005 opus47-swap-nvda**: 10/10 OW, 21d α +2.85% n=9 78% hit
- **AAPL pilot (Sonnet)**: 0/0/3/7/0
- **WC-12 cross-AAPL**: 0/0/7/2/1, bear bucket 21d α +2.89% (wrong direction, n=2)
- **brave-news-smoke-aapl**: 0/0/7/3/0, UW α -1.46% at 5d
- **exa-news-smoke-aapl**: 0/0/6/4/0, UW α -1.79% at 5d
- **single-call-baseline-aapl**: 0/3/0/7/0, OW α -2.06% (wrong direction)

Cross-AAPL Q4 finding: framework UW @ 21d on AAPL is directionally correct (-0.18%) — AAPL is where the framework's bear bucket actually works. Opus may either preserve this discrimination or commit OW like NVDA.
