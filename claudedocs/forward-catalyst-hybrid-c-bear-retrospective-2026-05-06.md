# Hybrid C BEAR-SIDE retrofit — INVERTED boost — 2026-05-06

**Config source**: production (`tradingagents.default_config.DEFAULT_CONFIG`).
Bear threshold: `0.5` (= spec 007 default).

**Hypothesis**: For bear commits, INVERTED boost direction (`effective = max(0, base * (1 - magnitude * boost))`) — boost DECREASES the effective bear score near earnings. Rationale: earnings often rally → priced-in bear cases fade as the rally arrives. Suppressing bear commits LESS aggressively near earnings (vs Spec 008's bull-direction boost which suppresses MORE) lets bear cases play out their natural fade-pattern.

**Mechanism**: `effective_bear = max(0, bear_case_priced_in * (1 - magnitude * boost))` where `boost = max(0, 1 - days_to_earnings / window)`.

**Cohort**: 94 commits (cached Class 3 Opus scores + days-to-next-earnings via yfinance for 18 of 18 unique tickers).

## Class 3-alone bear baseline

- Bear: n_fired=24, kept α=+12.00%, net Δα=+0.30pp, cohort hit=72.2%, discrim=+23.10pp

## Hybrid C BEAR INVERTED sweep — improvement vs baseline

| window | magnitude | bear Δα Δ | bear hit Δ | bear discrim Δ |
|---|---|---|---|---|
| 7d | 0.5x | +0.00pp | +0.0% | +0.00pp |
| 7d | 1.0x | +0.00pp | +0.0% | +0.00pp |
| 7d | 2.0x | +0.00pp | +0.0% | +0.00pp |
| 14d | 0.5x | +0.00pp | +0.0% | +0.00pp |
| 14d | 1.0x | +0.00pp | +0.0% | +0.00pp |
| 14d | 2.0x | +0.00pp | +0.0% | +0.00pp |
| 21d | 0.5x | +0.00pp | +0.0% | +0.00pp |
| 21d | 1.0x | +0.00pp | +0.0% | +0.00pp |
| 21d | 2.0x | +0.00pp | +0.0% | +0.00pp |

## Best inverted config: window=7d, magnitude=0.5x

- Bear net Δα change vs baseline: +0.00pp
- Bear cohort hit change vs baseline: +0.0%
- Bear discrim change vs baseline: +0.00pp
- Absolute bear net Δα: +0.30pp
- Absolute bear cohort hit: 72.2%
- Absolute bear discrim: +23.10pp

## Constitution VIII v1.4.0 forward-catalyst-class gate

- Discrim ≥ +5pp PRIMARY: **PASS** (+23.10pp)
- Cohort hit rate ≥ 60%: **PASS** (72.2%)
- Net Δα ≥ +0.5pp OR shadow-mode-first: **shadow-mode-first if criteria 1+2 pass** (+0.30pp)
- Improves over Class 3 baseline: **NO**

## Verdict — SKIP — bear-inverted does NOT improve over Class 3 baseline

## Reproducibility

```
python scripts/forward_catalyst_hybrid_c_bear_retrospective.py
```

Reads cached Class 3 Opus scores from `claudedocs\forward-catalyst-class3-opus-retrospective-2026-05-06.csv` + free yfinance fetches. Zero LLM cost.
