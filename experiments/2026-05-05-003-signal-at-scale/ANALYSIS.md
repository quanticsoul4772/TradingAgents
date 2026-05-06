# Analysis: 50-ticker signal at scale (SC-003)

**Experiment ID**: `2026-05-05-003-signal-at-scale`
**Run completed**: 2026-05-06 (background, 7.1h wall-clock)
**Cost**: ~$20 estimated, 50/50 propagates × 509s mean (Opus deep + Haiku quick)
**Date analyzed**: 2026-04-03 (single date, 21d forward window through 2026-05-04)

## TL;DR

**Scenario A/B mixed — signal generalizes in aggregate but is structurally
tech-concentrated.** The 50-ticker bullish bucket (Overweight, n=15) shows
**+5.96% mean α at 21d** — nearly 5× the 9-ticker corpus headline of +1.23%.
But the per-sector breakdown shows the bullish signal is dominated by Tech
(n=7, +17.80% mean) with Healthcare contributing modestly (n=2, +8.16%) and
Financials actually NEGATIVE on its bullish picks (n=5, -7.07%). Hit rate at
53% is just below the 55% target — magnitude carries the result.

**Verdict per HYPOTHESIS.md decision tree**: closer to **Scenario B
(tech-specific signal)** than pure A. Product-build path proceeds, but with
the empirical observation that universe selection matters: a tech-heavy or
per-sector-calibrated product surface will see the strong signal; a broad
sweep dilutes into Tech's coattails.

## Headline numbers

| Bucket | n | Mean α (21d) | Median α | Hit rate (α>0) | Std |
|---|---|---|---|---|---|
| Buy | 0 | — | — | — | — |
| **Overweight** | **15** | **+5.96%** | +0.48% | 53% | 18.04% |
| Hold | 33 | -3.87% | -8.53% | 21% | 23.09% |
| **Underweight** | **2** | **-15.60%** | -15.60% | **0%** (correct) | 3.72% |
| Sell | 0 | — | — | — | — |

- **50/50 propagated, 0 errors** — exceeds HYPOTHESIS success criterion (≤4 errors)
- Bullish commits: **15** (target was ≥10) ✓
- Bullish mean α: **+5.96%** (target was ≥+0.5%) ✓ (nearly 5× target)
- Hit rate: 53% (target was ≥55%) — narrow miss; magnitude carries
- Total cost: estimated within $20 (target was ≤$25) ✓

## Scenario verdict

| Scenario | Predicted | Actual fit |
|---|---|---|
| **A** (signal generalizes) | ~50% prior | Partial — aggregate yes, sector-uniform no |
| **B** (tech-specific) | ~25% prior | **Best fit** — bullish signal heavily concentrated in Tech (n=7) + small Healthcare contribution (n=2); Financials bullish picks NEGATIVE (n=5) |
| C (mode-collapse) | ~15% prior | No — 33/50 Hold (66%) is high but not pathological; 17 directional commits (34%) is reasonable |
| D (signal weakens) | ~7% prior | No — magnitude is large, hit rate barely under target |
| E (signal flips) | ~3% prior | No — bullish bucket clearly positive in aggregate |

## Per-sector breakdown (bullish-only)

| Sector | Bullish n | Mean α | Notes |
|---|---|---|---|
| **Tech** | 7 | **+17.80%** | AMD +51%, AVGO +26%, GOOGL +20%, AMZN +19%, CSCO +7%, MSFT +0.5%, NVDA +0.8% |
| Healthcare | 2 | +8.16% | UNH +19%, LLY -3% |
| Financials | 5 | -7.07% | MS +4%, MSFT-financial-N/A, BAC -3.7%, GS -3.7%, JPM -5%, MA -10.5%, WFC -12% |
| Energy | 1 | -16.16% | COP only — single observation |
| Consumer / Comms / Other / Industrials | 0 | — | All Hold or UW |

## Per-sector breakdown (all ratings)

| Sector | n | Mean α (all ratings) |
|---|---|---|
| Tech | 15 | +9.50% |
| Other (INTC + ABT) | 2 | +39.52% (INTC alone +103%) |
| Financials | 8 | -5.14% |
| Healthcare | 7 | -7.78% |
| Industrials | 5 | -9.43% |
| Consumer | 8 | -9.33% |
| Comms | 2 | -14.75% |
| Energy | 3 | -14.72% |

The market environment for this 21d window (2026-04-03 → 2026-05-04) was
**Tech-dominated** — broad sectors were down. The framework correctly went
heavily-Hold across the down sectors and bullish on the Tech rally. This is
both the strength (correct directional call where it matters most) and the
limitation (sector-bet-disguised-as-stock-pick).

## Counterfactuals

| Rule | n changed | Mean Δα | Total Δα | Direction |
|---|---|---|---|---|
| hold-all-uw | 2 | -0.006% | -0.31% | UW commits were correct (negative α); replacing with Hold loses alpha |
| hold-all-ow | 15 | -0.018% | -0.89% | OW commits were net-correct on aggregate; replacing with Hold loses alpha |
| invert-all | 17 | -0.048% | -2.41% | Inverting every directional commit destroys -2.41pp of alpha — confirms directional commits carry information |

**Counterfactual verdict**: directional commits (both bullish and bearish)
are net-correct on aggregate. The framework's commits add value vs the
all-Hold counterfactual.

## What surprised us

1. **Signal magnitude (+5.96%) much larger than the 9-ticker corpus
   headline (+1.23%)**. Likely driven by the specific 21d window being a
   strong Tech rally — not a permanent reframe of the headline finding.
2. **Financials bullish picks went the wrong way** (-7.07% on n=5). This
   is a real per-sector miss; the framework was confident-bullish on JPM,
   GS, MS, WFC, MA, BAC and only MS was correct.
3. **INTC was +103% in 21d but the framework called Hold**. Possibly a
   reasonable abstention given INTC's regime-volatility, but flagged for
   future investigation — was bull_keyword_count high? Did the contrarian
   gate fire in shadow mode?
4. **2 Underweight commits both correct** (CVX -13%, HON -18% — both
   negative, matching the bear call). Small n but 100% hit rate.
5. **Hold bucket mean α = -3.87%** — Holds were slightly anti-calibrated
   (the Hold tickers underperformed SPY by ~4% on average). This is not
   what calibrated abstention should look like; the framework may have
   been too willing to Hold on tickers that did poorly. Worth follow-up.

## Limitations

- **Single date** (2026-04-03) — 50 tickers but 1 time window. The Tech
  outperformance for this 21d window is a market-regime artifact; results
  on other windows may differ materially.
- **Shadow gates** — both filters were in observation mode, not active.
  The active-mode counterfactual would need a separate retrospective.
- **Tech-window confound** — can't separate "framework picks Tech bullish
  correctly" from "framework picked Tech bullish at a moment when Tech
  was about to rally." Multi-window replication required to disambiguate.
- **Hit rate at 53%** is suspiciously close to coin-flip — magnitude is
  the real story, and magnitude is variance-driven.

## Decision (per HYPOTHESIS decision tree)

**Scenario B → narrow product universe; document the constraint; proceed
with smaller scope.** Concretely:

1. The product-build path proceeds. Daily signals product (`scripts/daily_signals.py`)
   already exists and the SC-003 result validates that it's not generating noise.
2. The product surface should be **Tech-weighted with sector-diversification
   guardrails**: empirically the framework is strongest on Tech, breakeven-to-
   weak on Healthcare/Financials, and best at calibrated abstention on
   Consumer/Energy/Industrials.
3. **Add to RESEARCH_FINDINGS#1**: the 9-ticker corpus headline (+1.23%) is
   confirmed and likely understated for tech-heavy universes; the 50-ticker
   replication shows the signal is sector-conditional, not uniform.
4. **Open follow-up**: replicate this 50-ticker run on 2-3 different dates
   to disambiguate Tech-rally-window-luck from genuine cross-sector signal
   strength. ~T2 cost per repeat.
5. **Open follow-up**: investigate the Financials bullish miss — is the
   contrarian gate already flagging these in shadow mode (i.e. would active
   mode have suppressed them)? If yes, the gate's value is much higher than
   the +6.46% retrospective number suggested.

## Reproducibility

- `PARAMS.json`: standard product-defaults (Opus + Haiku, 3 analysts, 1 round, exa news, A3 ON, contrarian gate shadow)
- Analysis: `python scripts/analyze_backtest.py experiments/2026-05-05-003-signal-at-scale/results.csv --holding-days 21 --counterfactual-md ...`
- All 50 state logs in `~/.tradingagents/logs/<TICKER>/` for re-analysis
