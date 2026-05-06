# Spec 004 sector-momentum retrospective — 2026-05-06

**Spec**: `specs/004-sector-momentum-filter/`
**Holding window**: 21 trading days
**ETF lookback**: 30 trading days
**Corpus**: 77 unique bullish commits → 73 with sector + ETF + α data

## Baseline (no filter): n=73, mean α = +1.56%

## Threshold sweep

| threshold | n_kept | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|
| -10.0% | 73 | 0 | +1.56% | +nan% | +0.00pp |
| -7.5% | 68 | 5 | +1.77% | -1.32% | +0.21pp |
| -5.0% | 57 | 16 | +1.11% | +3.15% | -0.45pp |
| -3.0% | 36 | 37 | +2.74% | +0.41% | +1.18pp |

## Per-sector breakdown at threshold -5.0%

| Sector | ETF | n_total | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|---|
| Communication Services | XLC | 5 | 0 | +9.28% | n/a | +0.00pp |
| Consumer Cyclical | XLY | 1 | 1 | n/a | +18.71% | +0.00pp |
| Energy | XLE | 1 | 0 | -16.16% | n/a | +0.00pp |
| **Financial Services** | XLF | 9 | 3 | **-6.50%** | **+1.50%** | **-2.67pp** |
| Healthcare | XLV | 2 | 2 | n/a | +8.16% | +0.00pp |
| Technology | XLK | 55 | 10 | +1.60% | +1.08% | +0.10pp |

## Verdict — DO NOT flip default-on

**The retrospective falsifies default-on at the -5% threshold.**

At the spec's default threshold (-5%), the filter has **net Δα = -0.45pp** across the corpus — it removes WINNERS, not losers:

- 16 commits fire; their mean realized α was **+3.15%** (the filter would suppress profitable bullish commits).
- The kept-commits' α drops from the +1.56% baseline to +1.11% (worse than no filter).
- **The Financials sector specifically shows -2.67pp** — the 3 Financials commits the filter would have suppressed when XLF was below -5% had +1.50% mean α (they were correct OWs); the 6 it would have kept had -6.50% mean α (they were the actual losers, including the SC-003 cohort).

The filter at -5% is anti-predictive in the Financials sector. A sector-ETF down >5% in 30d turned out to be a contrarian BUY signal in the corpus, not a stay-out signal — at least over the realized 21d window.

Other thresholds:
- **-10% never fires** (no sector ETF was that deeply down at any commit date).
- **-7.5% gives a small positive +0.21pp** but only fires 5 times (small-n).
- **-3% gives +1.18pp** but fires 37 of 73 commits — half the corpus. The improvement is sample-shift noise (you remove half the commits and keep the easier half), not a calibrated mechanism.

## Empirical context

Today's spec 004 SC-008 validation (`claudedocs/spec-004-sc008-validation-2026-05-06.md`) showed the filter doesn't fire on the SC-003 Financials cohort at the -5% threshold (XLF was at -4.54%, above the threshold). This retrospective tested whether the filter helps SOMEWHERE ELSE in the corpus. **It doesn't, at the configured default.**

## Implications

1. **Spec 004 stays default-OFF permanently** based on this data. The implementation is correct, the mechanism is well-defined, but the empirical evidence in our corpus doesn't support a default flip.
2. **The "sector ETF down → suppress bullish commits" intuition is wrong in our regime.** In the corpus's market regimes, sector-ETF drawdowns appear to be contrarian buying opportunities (the suppressed commits had positive realized α), not stay-out signals.
3. **An operator with strong reason to believe a SPECIFIC sector is in regime change** can still opt-in via PARAMS.json. The filter is an operator-tool for those cases.
4. **The fourth failure mode (per-ticker-α-vs-rising-sector)** documented in the spec 004 validation doc is still uncaught by any current filter. If catching it becomes a priority, it'll need a different mechanism (e.g., ticker-relative-strength vs sector ETF).

## What would change the verdict

- **More corpus data**: 73 commits is small. If a 200+ commit corpus showed positive net Δα at -5%, revisit. (Multi-window SC-003 replication would expand the corpus by ~30 commits per date, T2 cost.)
- **Different lookback window**: this used 30 trading days. Shorter (10d) or longer (60d) windows might capture different regime signals. Out of scope for this retrospective; potential future work.
- **Different per-sector thresholds**: the data hints that XLF specifically is the wrong sector for this filter. A per-sector threshold table (e.g. -5% for Tech, never for Financials) might salvage the mechanism. Premature optimization without more data.

## Reproducibility

```
python scripts/sector_momentum_retrospective.py
```

Reads from `experiments/*/results.csv` + spec 002 sectors cache + yfinance ETF
prices. No LLM cost. Deterministic given a fixed corpus + threshold list.
