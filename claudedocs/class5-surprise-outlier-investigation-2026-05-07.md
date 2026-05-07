# Class 5 surprise outlier investigation — 2026-05-07

**Trigger**: Class 5 retrospective (`claudedocs/forward-catalyst-class5-retrospective-2026-05-06.md`)
noted distribution outliers: mean=0.95 (95%!), max=31.21 (3,121%!), std=4.39.
Class 5 was retroactively SKIPPED via Constitution v1.4.3 additive-overlap gate, but the
outlier issue would surface in any future Class 5 revival (different cohort, different
thresholds) — documenting the data-cleanup needed.

**Cohort**: 18 tickers from the Spec 007/008 retrofit.

## Outlier summary (|surprisePercent| > 1.0 i.e. > 100%)

Found **3 outlier rows** across 1 ticker(s):

| ticker | quarter | epsActual | epsEstimate | surprisePercent | as % |
|---|---|---|---|---|---|
| INTC | 2025-06-30 | -0.1000 | 0.0085 | -12.8064 | -1,281% |
| INTC | 2025-09-30 | 0.2300 | 0.0071 | 31.2129 | 3,121% |
| INTC | 2026-03-31 | 0.2900 | 0.0131 | 21.0868 | 2,109% |

## Mechanism

yfinance computes `surprisePercent = (epsActual - epsEstimate) / abs(epsEstimate)`.
When `epsEstimate` is near zero (loss-flipping quarter, restructuring charge, one-time
items, etc.), the ratio blows up — even a small dollar miss becomes thousands of percent.

## Production-filter mitigations (any of)

1. **Clamp** `surprisePercent` to `[-2.0, +2.0]` (cap at 200% beat/miss). Simplest;
   preserves rank-ordering.
2. **Log-transform**: `sign(surprise) × log1p(abs(surprise))`. Preserves sign + tames
   tails; loses linear interpretability.
3. **Absolute-dollar difference**: `abs(epsActual - epsEstimate)`. Loses scale-
   invariance across tickers; not recommended.
4. **Exclude rows** where `abs(epsEstimate) < 0.10`. Data-quality filter; loses
   data points but cleanest semantically.

Recommended for any future Class 5 revival: **clamp at ±2.0 OR exclude rows with
`abs(epsEstimate) < 0.10`**, document either choice in the retrospective preamble.

## Reproducibility

```
python scripts/inspect_class5_surprise_outliers.py
```

Free yfinance.earnings_history fetches; one HTTP call per ticker. Zero LLM cost.
