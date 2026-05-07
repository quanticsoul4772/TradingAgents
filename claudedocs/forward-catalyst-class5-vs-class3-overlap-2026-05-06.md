# Class 5 vs Spec 007 (Class 3) overlap analysis — 2026-05-06

**Spec 007 threshold**: `bull_case_priced_in > 0.6`
**Class 5 threshold**: `surprise_pct > 0.02` (best from Class 5 retrospective)
**Cohort**: 47 bull commits with computable surprise data.

## Fire decision overlap matrix

|  | Class 3 fires | Class 3 silent | Total |
|---|---|---|---|
| Class 5 fires | **31** | 10 | 41 |
| Class 5 silent | 2 | **4** | 6 |
| Total | 33 | 14 | 47 |

## Per-set α + cohort breakdown

| Set | n | mean α | cohort_a | control_winner |
|---|---|---|---|---|
| BOTH fire (intersection) | 31 | -2.17% | 24 | 7 |
| Class 5 ONLY | 10 | +3.80% | 2 | 8 |
| Class 3 (Spec 007) ONLY | 2 | +16.73% | 0 | 2 |
| EITHER fires (union) | 43 | +0.09% | 26 | 17 |
| NEITHER fires (kept commits) | 4 | -1.93% | 1 | 3 |
| ALL bull commits (baseline) | 47 | -0.08% | 27 | 20 |

## Filter comparison

| Filter | n_fired | net Δα | cohort hit% | discrim |
|---|---|---|---|---|
| Spec 007 alone (Class 3 @ 0.60) | 33 | +2.24pp | 88.9% | +14.43pp |
| Class 5 alone (surprise @ 0.02) | 41 | +4.37pp | 96.3% | +11.92pp |
| Hybrid B union (Class 3 OR Class 5) | 43 | -1.85pp | 96.3% | +13.08pp |
| Hybrid B intersection (Class 3 AND Class 5) | 31 | +4.06pp | 88.9% | +12.35pp |

## Marginal-value analysis

- **Union vs Spec 007 alone**: net Δα -4.09pp, hit +7.4%
- **Union vs Class 5 alone**:  net Δα -6.22pp, hit +0.0%

## Verdict — REDUNDANT — union does NOT improve over either underlying filter; Class 5 + Spec 007 are largely correlated. SKIP Spec 010 entirely; Spec 007 dominates

## Cohort_a (bull losers) catch breakdown

- Caught by Spec 007 only: **0** of 27
- Caught by Class 5 only:  **2** of 27
- Caught by BOTH:          **24** of 27
- Caught by EITHER:        **26** of 27
- MISSED by both:          **1** of 27

## Reproducibility

```
python scripts/forward_catalyst_class5_vs_class3_overlap.py
```

Reads cached Class 3 Opus scores + free yfinance.earnings_history. Zero LLM cost.
