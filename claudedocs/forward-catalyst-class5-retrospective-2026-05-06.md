# Class 5 forward-catalyst retrospective — 2026-05-06

**Hypothesis**: when a ticker has a recent POSITIVE earnings surprise, the bull case the LLM scored high is more likely to already be priced in by the market — further bull commits face limited upside. So bull commits with recent surprise > threshold should be SUPPRESSED.

**Mechanism A (standalone)**: `fire_bull = (most_recent_surprise_pct > threshold) AND (rating in {Buy, OW})`

**Cohort**: same 94-commit Opus retrospective cohort. 94 of 94 rows have computable surprise data (18/18 tickers have earnings_history).

## Surprise distribution

| stat | value |
|---|---|
| count | 94 |
| mean | 0.9513 |
| std | 4.3853 |
| min | -0.0391 |
| 25% | 0.0452 |
| 50% | 0.0634 |
| 75% | 0.0705 |
| max | 31.2129 |

## Standalone bull-side gate sweep

| threshold | bull n_fired | bull net Δα | bull hit% | bull discrim |
|---|---|---|---|---|
| 0.02 | 41 | +4.37pp | 96.3% | +11.92pp |
| 0.05 | 28 | -2.21pp | 48.1% | +11.68pp |
| 0.08 | 6 | -0.87pp | 3.7% | +26.39pp |
| 0.12 | 4 | -1.28pp | 0.0% | +nanpp |

## Best Class 5 standalone config: threshold=0.02

- Bull net Δα: +4.37pp
- Bull cohort hit: 96.3%
- Bull discrim: +11.92pp

## Constitution VIII v1.4.0 forward-catalyst-class gate

- Discrim ≥ +5pp PRIMARY: **PASS** (+11.92pp)
- Cohort hit rate ≥ 60%: **PASS** (96.3%)
- Net Δα ≥ +0.5pp: **PASS** (+4.37pp)

## Verdict — PASS — invoke Spec 010 (Class 5 standalone, default-on at best threshold)

## Reproducibility

```
python scripts/forward_catalyst_class5_retrospective.py
```

Reads cached Class 3 Opus scores from `claudedocs\forward-catalyst-class3-opus-retrospective-2026-05-06.csv` + free yfinance.earnings_history fetches (one per unique ticker; LRU-cached). Zero LLM cost.
