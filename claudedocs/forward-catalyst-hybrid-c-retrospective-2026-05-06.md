# Hybrid C retrofit — 2026-05-06

**Config source**: production (`tradingagents.default_config.DEFAULT_CONFIG`).
Bull mode: `active` (active means fired commits actually downgrade in production).
Bear mode: `shadow` (shadow means fired commits are observed-only in production).

**Hypothesis** (Spec 008 design doc pivot): Class 3 (LLM-extracted `bull/bear_case_priced_in` scores, validated + shipped at v0.7.0-spec-007) combined with Class 6 (calendar features: days-to-next-earnings) improves discrimination beyond Class 3 alone, by amplifying the priced-in effect for commits close to forward catalysts (which are more likely to be already-absorbed by the market).

**Mechanism**: `effective_score = base_score × (1 + magnitude × boost)` where `boost = max(0, 1 - days_to_earnings / window)`. At earnings day, boost=1.0 → effective = base × (1+magnitude); at window+ days out, boost=0 → effective = base.

**Cohort**: 94 commits (cached Class 3 Opus scores + days-to-next-earnings via yfinance.earnings_dates for 18 of 18 unique tickers).

## Days-to-earnings distribution

| stat | value |
|---|---|
| count | 94 |
| mean | 44.5 |
| std | 24.0 |
| min | 5 |
| 25% | 27 |
| 50% | 42 |
| 75% | 62 |
| max | 90 |

## Class 3-alone baseline (T_bull=0.60, T_bear=0.50)

- Bull: n_fired=33, kept α=+2.16%, net Δα=+2.24pp, cohort hit=88.9%, discrim=+14.43pp
- Bear: n_fired=24, kept α=+12.00%, net Δα=+0.30pp, cohort hit=72.2%, discrim=+23.10pp

## Hybrid C sweep — improvement vs baseline

| window | magnitude | bull Δα Δ | bear Δα Δ | bull hit Δ | bear hit Δ | combined |
|---|---|---|---|---|---|---|
| 7d | 0.5x | +0.00pp | +0.00pp | +0.0% | +0.0% | +0.000 |
| 7d | 1.0x | +0.00pp | +0.00pp | +0.0% | +0.0% | +0.000 |
| 7d | 2.0x | +0.00pp | +0.00pp | +0.0% | +0.0% | +0.000 |
| 14d | 0.5x | +3.35pp | +0.00pp | +3.7% | +0.0% | +3.383 |
| 14d | 1.0x | +3.35pp | +0.00pp | +3.7% | +0.0% | +3.383 |
| 14d | 2.0x | +3.35pp | +0.00pp | +3.7% | +0.0% | +3.383 |
| 21d | 0.5x | +3.35pp | -2.52pp | +3.7% | +0.0% | +0.864 |
| 21d | 1.0x | +3.35pp | -2.52pp | +3.7% | +0.0% | +0.864 |
| 21d | 2.0x | +3.35pp | -3.50pp | +3.7% | +5.6% | -0.059 |

## Best config: window=14d, magnitude=0.5x

- Combined improvement: +3.383
- Bull net Δα change: +3.35pp
- Bull hit rate change: +3.7%
- Bear net Δα change: +0.00pp
- Bear hit rate change: +0.0%

## Verdict — PASS per Spec 008 design doc decision tree

Hybrid C produces meaningful improvement over Class 3 alone at the best-performing config. Per the Spec 008 design doc decision tree, this PASSES the gate to invoke `/speckit.specify` for a Spec 008 (Hybrid C as calendar-aware enhancement of the validated Class 3 filter).

Recommended next step: invoke `/speckit.specify` for Spec 008 with this retrospective + the Spec 008 design doc as load-bearing empirical evidence. The spec would extend the Class 3 filter (forward_catalyst_filter.py) with an optional calendar boost layer; default-off until production-config retrospective confirms the improvement holds at production thresholds.

## Reproducibility

```
python scripts/forward_catalyst_hybrid_c_retrospective.py
```

Reads cached Class 3 Opus scores from `claudedocs\forward-catalyst-class3-opus-retrospective-2026-05-06.csv` + free yfinance earnings_dates fetches (one per unique ticker; 18 tickers in cohort). Zero new LLM cost.
