# Contrarian gate retrospective — 2026-05-05

## Question

Spec 003 SC-002 asks: across N>=30 propagates, does the contrarian gate reproduce finding #4's within-ticker pattern in fresh data + improve mean α by suppressing bullish commits at high bull_keyword_count percentiles?

This script answers the same question OFFLINE against the existing 156 historical propagates in ~/.tradingagents/logs/states/. No new LLM cost.

**Key methodological constraint**: strict no-look-ahead. For propagate at (ticker, date), the percentile baseline uses ONLY prior dates of the same ticker, never data from after this date. Otherwise the gate would have unfair foresight that wouldn't exist in production.

## Method

1. Load all 156 state logs from `~/.tradingagents/logs/states/`
2. For each, compute `bull_keyword_count(market_report)` and parse the rating
3. Per ticker, sort by date ascending
4. For each (ticker, date) row at position i: history = first i rows of that ticker (strict prior). Take most-recent 20 of those as the percentile baseline.
5. Compute percentile of current bull_count vs baseline; would_fire = (percentile >= 80) AND (rating in {Buy, Overweight})
6. Fetch realized 21d + 90d α (post-buffer-fix `fetch_returns`)
7. Stratify α by would_fire bucket; project active-mode Δα
8. Run at two history floors (N>=5 permissive, N>=20 matches live gate FR-004)

## History floor: N>=5

### Per-ticker gate-fire rate (history floor N>=5)

| Ticker | n eligible | n bullish (Buy/OW) | n would_fire | fire rate over bullish |
|---|---:|---:|---:|---:|
| AAPL | 18 | 4 | 0 | 0.0% |
| GOOGL | 7 | 4 | 3 | 75.0% |
| INTC | 15 | 0 | 0 | 0.0% |
| JPM | 7 | 3 | 1 | 33.3% |
| MSFT | 8 | 6 | 3 | 50.0% |
| NVDA | 28 | 23 | 7 | 30.4% |
| XLE | 15 | 2 | 1 | 50.0% |
| XLF | 5 | 0 | 0 | 0.0% |
| XLK | 5 | 1 | 0 | 0.0% |

### α @ 21d (history floor N>=5)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 15 | +1.91% | -0.22% | 46.7% |
| Buy/OW where gate would NOT fire | 28 | +1.58% | +1.54% | 71.4% |
| Hold/UW/Sell (not in gate scope) | 65 | +7.92% | +1.92% | 64.6% |

**If active mode had been ON**: gate would have fired on 15 bullish commits, downgrading them to Hold. Cumulative Δα contribution = -28.69% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

### α @ 90d (history floor N>=5)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 15 | +1.14% | -1.83% | 33.3% |
| Buy/OW where gate would NOT fire | 28 | +0.54% | +0.71% | 53.6% |
| Hold/UW/Sell (not in gate scope) | 65 | +35.12% | +3.88% | 70.8% |

**If active mode had been ON**: gate would have fired on 15 bullish commits, downgrading them to Hold. Cumulative Δα contribution = -17.06% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

## History floor: N>=20

### Per-ticker gate-fire rate (history floor N>=20)

| Ticker | n eligible | n bullish (Buy/OW) | n would_fire | fire rate over bullish |
|---|---:|---:|---:|---:|
| AAPL | 3 | 0 | 0 | 0.0% |
| NVDA | 13 | 9 | 2 | 22.2% |

### α @ 21d (history floor N>=20)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 2 | -3.08% | -3.08% | 0.0% |
| Buy/OW where gate would NOT fire | 7 | +2.58% | +1.85% | 71.4% |
| Hold/UW/Sell (not in gate scope) | 7 | +0.93% | +1.37% | 85.7% |

**If active mode had been ON**: gate would have fired on 2 bullish commits, downgrading them to Hold. Cumulative Δα contribution = +6.15% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

### α @ 90d (history floor N>=20)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 2 | -1.89% | -1.89% | 0.0% |
| Buy/OW where gate would NOT fire | 7 | -0.17% | +1.10% | 57.1% |
| Hold/UW/Sell (not in gate scope) | 7 | +1.76% | +1.37% | 85.7% |

**If active mode had been ON**: gate would have fired on 2 bullish commits, downgrading them to Hold. Cumulative Δα contribution = +3.78% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

## Verdict

**Mixed and concerning. The retrospective does NOT validate spec 003's predicted Δα improvement at the permissive floor; the production floor has too little data to draw conclusions either way. The live SC-002 experiment is now MORE necessary after this retrospective, not less.**

### What the data shows

**At the permissive floor (N≥5)**, 15 commits would have fired offline. The gate-fired bucket had **HIGHER** mean α than the bullish-no-fire bucket at both horizons:

| Horizon | Gate-fired (n=15) | Bullish no-fire (n=28) | Δ |
|---|---:|---:|---:|
| 21d mean α | +1.91% | +1.58% | +0.33pp (gate-fired HIGHER) |
| 90d mean α | +1.14% | +0.54% | +0.60pp (gate-fired HIGHER) |

If active mode had been ON across these 15 commits, downgrading them all to Hold would have produced **cumulative Δα = -28.69% at 21d, -17.06% at 90d**. The gate would have HURT, not helped.

This is the OPPOSITE direction from what finding #4's mechanism (recency + mean-reversion) predicts. Three explanations to consider:

1. **Strict-prior history is too small at low N.** Finding #4's within-ticker IC of -0.489 was computed across all 113 fundamentals_report dates simultaneously, with all dates' returns visible. The gate at N=5-19 prior dates has a noisy percentile estimate that doesn't accurately identify "this ticker's high-bull-density moments". Mis-classification eats the predicted edge.
2. **The high-percentile commits were on different mean-reverting setups than finding #4 predicts.** The mechanism investigation showed the recency mechanism applies on most tickers but not XLF; perhaps the early-history high-percentile commits in this corpus happen to be on tickers/regimes where the mechanism is weaker.
3. **Finding #4's measurement had look-ahead bias from the corpus-aggregate IC.** The gate's strict-prior setting eliminates the look-ahead and produces the actual prospective Δα. If true, finding #4 may overstate the actionable predictive power.

**At the production floor (N≥20)**, only 2 commits would have fired (both NVDA) — the corpus doesn't have enough propagates per ticker to populate the strict-prior-N=20 history yet:

| Horizon | Gate-fired (n=2) | Bullish no-fire (n=7) | Δ |
|---|---:|---:|---:|
| 21d mean α | -3.08% | +2.58% | -5.66pp (gate-fired LOWER) |
| 90d mean α | -1.89% | -0.17% | -1.72pp (gate-fired LOWER) |

Cumulative Δα at 21d: **+6.15%** (gate would have helped by suppressing 2 negative-α commits). At 90d: +3.78%. **Suggestively positive but n=2 is anecdotal.**

### Two-floor tension

The two history floors give qualitatively opposite results:
- N≥5 (15 fires): gate would have HURT
- N≥20 (2 fires): gate would have HELPED

The N≥20 result aligns with finding #4's prediction; the N≥5 result contradicts it. Possible reading: the gate ONLY works once enough per-ticker history is accumulated, which happens to be exactly the FR-004 design floor. But n=2 isn't enough to bet on this reading.

### Per-ticker fire patterns (N≥5 floor)

GOOGL (75% bullish-fire-rate), NVDA (30%), and MSFT (50%) account for almost all the gate fires. INTC and XLF/XLK never fired bullish — consistent with INTC's bear-regime label and XLK/XLF's degenerate-window status documented in `claudedocs/degenerate-window-check-2026-05-05.md`.

### What this changes

1. **SC-002 live experiment is now more critical, not less.** The N≥20 retrospective was suggestively positive but n=2; the N≥5 retrospective was strongly negative. Without a fresh-data N≥30 experiment at the production floor, the gate's actual prospective Δα is unknown.
2. **Spec 003 should NOT be promoted to active mode by default until SC-002 lands with a clear positive result.** The retrospective is empirical reason to be cautious, not a green light.
3. **The mechanism interpretation may need revision.** Finding #4's within-ticker IC = -0.489 is real, but the actionable prospective predictive power on top-percentile commits may be weaker than the IC suggests. Could be a corpus-aggregate look-ahead bias in how the IC was measured.
4. **`investment_plan` and `news_report` marginal candidates are now LESS likely to be useful** — if the validated `market_report` signal doesn't translate to prospective Δα at low N, the marginals (which were already weaker in IC) won't either.

### What this does NOT change

- Finding #4's headline statistic (-0.489 within-ticker median IC) remains a real corpus-level correlation. It's the prospective gate translation that's the open question.
- Spec 003 implementation is unaffected; the gate's wiring is correct and well-tested. The empirical question is whether the gate should ever go to active mode — answer pending SC-002 fresh data.
- Constitution Principle VII (Calibrated Abstention) still applies — even if the gate doesn't help on net, downgrading bullish commits to Hold doesn't make calibration WORSE on this evidence (Hold is ~0% mean α at every horizon; the question is whether the suppressed commit's α was meaningfully positive on net).

### Implications for `findings.md` / RESEARCH_FINDINGS

Finding #4 should grow a paragraph noting this retrospective:

> Important caveat (2026-05-05): an offline retrospective of 156 historical propagates simulating the spec 003 gate at strict-prior N≥5 history shows the gate would have HURT cumulative α (-28.69% at 21d across 15 fires), contradicting finding #4's mechanism prediction. The N≥20 production-floor retrospective is consistent with the prediction but only 2 commits qualified. Finding #4's actionable predictive power on prospective gate decisions is unconfirmed pending the SC-002 live experiment. The within-ticker IC remains real at the corpus-aggregate level.

### Cost

$0 LLM, ~5 min wall-clock (156 state log loads + bull_keyword_count featurization + alpha fetches at 21d/90d for each + offline simulation at 2 history floors).
