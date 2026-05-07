# Class C-1 forward-catalyst retrospective — insider transactions — 2026-05-07

**Hypothesis**: when insiders are net-buying their own stock, the bear case the LLM scored high may be priced-in / wrong-direction — suppress further bear commits with insider activity.

**Mechanism A (standalone)**: `fire_bear = (insider_buy_count_30d >= T) AND (rating in {Underweight, Sell})`

**Cohort**: same 94-commit Opus retrospective cohort. 7/18 unique tickers have ANY insider purchases (filtered via Text column 'Purchase'); 9 of 94 rows have insider buys in the prior 30-day window.

**Critical bear-cohort coverage**: 1 of 18 `cohort_b_bear_target` rows have insider purchases in the prior 30-day window.

## Standalone bear-side sweep

| threshold (≥X buys) | bear n_fired | bear net Δα | bear hit% | bear discrim |
|---|---|---|---|---|
| 1 | 5 | -2.23pp | 5.6% | +8.07pp |
| 2 | 0 | +0.00pp | 0.0% | N/A |
| 3 | 0 | +0.00pp | 0.0% | N/A |

## Best config: threshold=2, lookback=30d

- Bear net Δα: +0.00pp
- Bear cohort hit: 0.0%
- Bear discrim: N/A

## Constitution VIII v1.4.0 forward-catalyst-class gate (standalone)

- Discrim ≥ +5pp PRIMARY: **FAIL**
- Cohort hit rate ≥ 60%: **FAIL**
- Net Δα ≥ +0.5pp: **FAIL or shadow-mode-first**

## Standalone verdict — SKIP — Class C-1 fails primary criterion

## Reproducibility

```
python scripts/forward_catalyst_class_c1_insider_retrospective.py
```

Reads cached Class 3 Opus scores from `claudedocs\forward-catalyst-class3-opus-retrospective-2026-05-06.csv` + free yfinance.insider_transactions fetches (one per unique ticker; LRU-cached). Zero LLM cost.
