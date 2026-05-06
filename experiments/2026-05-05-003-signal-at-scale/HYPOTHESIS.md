# Hypothesis: signal at scale (50-ticker batch)

**Experiment ID**: `2026-05-05-003-signal-at-scale`
**Created**: 2026-05-05
**Source idea**: Product-build path step 1 — validate the +1.23% mean α at 21d on bullish commits holds beyond the 9-ticker corpus before investing in paper-trading harness
**Cost estimate**: ~$20 (50 propagates × ~$0.40 each, Opus + Haiku)
**Cost tier**: T2 (standard, $5-30)

## What we're testing

The 24-experiment corpus established (RESEARCH_FINDINGS finding #1):
> Framework's bullish commits (Buy + Overweight) at 21d show **+1.23% mean α across n=71 cross-experiment commits (~61% hit rate)** — POSITIVE AT MODERATE CONFIDENCE.

But this was on a 9-ticker corpus (NVDA, AAPL, INTC, JPM, MSFT, GOOGL, XLE, XLF, XLK + 1 BRK.B). All large-cap tech-heavy. The signal might be:
- (A) **Universal**: holds across sectors and market caps → product-build proceeds
- (B) **Tech-specific**: only works on the original universe → narrow product scope
- (C) **Random**: 9-ticker n is too small to support generalization → product-build pause

This experiment runs the framework on **50 diversified tickers** at a single date with full 21d forward α data, then compares the bullish-bucket α to the 9-ticker corpus headline.

## Setup

- **50 tickers** spanning 8 sectors:
  - **Tech** (15): AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AVGO, ORCL, ADBE, CRM, NFLX, CSCO, AMD, QCOM
  - **Financials** (8): JPM, BAC, WFC, GS, MS, V, MA, AXP
  - **Healthcare** (7): UNH, JNJ, LLY, PFE, MRK, ABBV, TMO
  - **Consumer staples + discretionary** (8): KO, PG, WMT, COST, HD, MCD, SBUX, NKE
  - **Industrials** (5): GE, CAT, BA, HON, LMT
  - **Energy** (3): XOM, CVX, COP
  - **Comms** (2): T, VZ
  - **Other** (2): INTC, ABT
- **Date**: 2026-04-03 (Friday with full 21d forward α data as of 2026-05-05)
- **Mode**: shadow gates (`contrarian_gate_mode = "shadow"`, A3 filter ON) — measures the framework's raw output + gate annotations without modifying ratings
- **Config**: standard product-defaults (Opus deep + Haiku quick + 3 analysts + 1 round + exa news)

## Predicted findings

**Scenario A (signal generalizes)** — ~50%
- Bullish-bucket 21d α positive (≥ +0.5%) on the 50-ticker batch
- Hit rate ≥ 55% on bullish commits
- Rating distribution shows reasonable variety (not 100% Hold)
- Spec 003 gate fires on a meaningful subset (5-15% of bullish commits)
- → product-build path to paper-trading harness greenlit

**Scenario B (tech-specific signal)** — ~25%
- Bullish-bucket 21d α positive ONLY on tech subset
- Non-tech bullish commits show ~0% mean α
- Implication: narrow the product to tech-heavy universe; document the constraint

**Scenario C (mode-collapse to Hold across most tickers)** — ~15%
- Framework produces Hold on >70% of the 50 tickers
- Few bullish commits → small-n bullish bucket
- Implication: framework is over-abstaining at this universe size; either the 9-ticker corpus was unusual or the prompt needs adjustment for cross-sector use

**Scenario D (signal weakens but exists)** — ~7%
- Bullish-bucket α positive but < +0.5%
- Hit rate ~50% (coin-flip territory)
- Implication: signal exists but transaction costs would erode it; need filtering improvements before product

**Scenario E (signal flips negative)** — ~3%
- Bullish-bucket α actively negative on the broader universe
- Implication: 9-ticker corpus was a happy accident; abandon the product-build path or fundamentally rethink

## Success criterion

- [ ] 50 propagations complete with ≤4 errors (8% error tolerance)
- [ ] Rating distribution: at least 10 bullish (Buy + OW) commits across the 50
- [ ] Bullish bucket mean α: ≥ +0.5% (matches at least half of the 9-ticker headline +1.23%)
- [ ] Total cost ≤ $25

## Date-validity check

2026-04-03 (Friday) + 21 trading days ≈ 2026-05-04 (Monday). Today is 2026-05-05. Full 21d forward α should be available for all 50 tickers (subject to per-ticker delisting/data gaps).

## Notes

- **T2 tier** (~$20 estimated, well within $30 ceiling)
- **Single date** (one-experiment-per-change per Constitution II): only the universe expands vs the 9-ticker baseline
- **Shadow mode** preserves the framework's raw output for analysis; active gates can be applied retroactively from the gate annotations in the state log
- **No memory log routing** — this is using the operator's main flow as a real product test (the daily_signals.py product would behave the same way)
- **Wall-clock**: ~50 × 9min ≈ 7-8 hours. Background run.

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (generalizes) | Product path proceeds: build paper-trading harness on top of daily_signals.py |
| Scenario B (tech-specific) | Narrow product universe; document the constraint; proceed with smaller scope |
| Scenario C (over-abstention) | Investigate prompt; the framework may need universe-size-aware tuning |
| Scenario D (weak signal) | Filter improvements (composite-source spec 004) before product |
| Scenario E (negative) | Major reframe; abandon the 21d signal claim or restrict to original universe |

## Related work

- **Finding #1** (RESEARCH_FINDINGS headline): +1.23% mean α at 21d, n=71, 9-ticker corpus
- **Finding #4** (the within-ticker contrarian signal underlying spec 003): also 9-ticker corpus
- **`scripts/daily_signals.py`** (commit 2c11441): the product layer this experiment validates
- **Constitution Principle II** (One Experiment Per Change): only the ticker universe varies
- **Constitution Principle III** (Stay Cheap): T2 tier, $20 within ceiling
