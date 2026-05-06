# Contrarian gate retrospective — 2026-05-06

## Question

Spec 003 SC-002 asks: across N>=30 propagates, does the contrarian gate reproduce finding #4's within-ticker pattern in fresh data + improve mean α by suppressing bullish commits at high bull_keyword_count percentiles?

This script answers the same question OFFLINE against the existing 156 historical propagates in ~/.tradingagents/logs/states/. No new LLM cost.

**Key methodological constraint**: strict no-look-ahead. For propagate at (ticker, date), the percentile baseline uses ONLY prior dates of the same ticker, never data from after this date. Otherwise the gate would have unfair foresight that wouldn't exist in production.

## Method

1. Load all 205 state logs from `~/.tradingagents/logs/states/`
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
| AAPL | 23 | 6 | 0 | 0.0% |
| GOOGL | 12 | 8 | 4 | 50.0% |
| INTC | 20 | 0 | 0 | 0.0% |
| JPM | 12 | 8 | 3 | 37.5% |
| MSFT | 13 | 11 | 5 | 45.5% |
| NVDA | 28 | 23 | 7 | 30.4% |
| XLE | 15 | 2 | 1 | 50.0% |
| XLF | 5 | 0 | 0 | 0.0% |
| XLK | 5 | 1 | 0 | 0.0% |

### α @ 21d (history floor N>=5)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 20 | +1.24% | -1.28% | 45.0% |
| Buy/OW where gate would NOT fire | 39 | +2.08% | +1.23% | 69.2% |
| Hold/UW/Sell (not in gate scope) | 74 | +10.46% | +3.19% | 68.9% |

**If active mode had been ON**: gate would have fired on 20 bullish commits, downgrading them to Hold. Cumulative Δα contribution = -24.87% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

### α @ 90d (history floor N>=5)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 20 | +0.93% | -2.26% | 35.0% |
| Buy/OW where gate would NOT fire | 39 | +1.60% | +0.78% | 56.4% |
| Hold/UW/Sell (not in gate scope) | 74 | +39.44% | +5.11% | 75.7% |

**If active mode had been ON**: gate would have fired on 20 bullish commits, downgrading them to Hold. Cumulative Δα contribution = -18.52% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

## History floor: N>=20

### Per-ticker gate-fire rate (history floor N>=20)

| Ticker | n eligible | n bullish (Buy/OW) | n would_fire | fire rate over bullish |
|---|---:|---:|---:|---:|
| AAPL | 8 | 2 | 0 | 0.0% |
| INTC | 5 | 0 | 0 | 0.0% |
| NVDA | 13 | 9 | 2 | 22.2% |

### α @ 21d (history floor N>=20)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 2 | -3.23% | -3.23% | 0.0% |
| Buy/OW where gate would NOT fire | 9 | +1.71% | +0.78% | 55.6% |
| Hold/UW/Sell (not in gate scope) | 15 | +26.56% | +2.58% | 73.3% |

**If active mode had been ON**: gate would have fired on 2 bullish commits, downgrading them to Hold. Cumulative Δα contribution = +6.46% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

### α @ 90d (history floor N>=20)

| Bucket | n | Mean α | Median α | Hit rate (α>0) |
|---|---:|---:|---:|---:|
| Gate would fire (Buy/OW + percentile>=80) | 2 | -2.21% | -2.21% | 0.0% |
| Buy/OW where gate would NOT fire | 9 | -0.04% | +0.78% | 66.7% |
| Hold/UW/Sell (not in gate scope) | 15 | +41.74% | +3.24% | 86.7% |

**If active mode had been ON**: gate would have fired on 2 bullish commits, downgrading them to Hold. Cumulative Δα contribution = +4.42% (positive = gate would have helped; negative = gate would have hurt by suppressing winning bullish commits).

## Verdict

(Verdict written by hand after reviewing tables.)
