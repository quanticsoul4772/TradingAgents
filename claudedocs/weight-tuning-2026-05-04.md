# Spec 001 Phase 5: Weight Tuning Report (objective=ic)

_Generated 2026-05-04T23:24:19+00:00._

**Horizon**: 21d. **Train/test split**: 70% date-ordered. Train n=109, test n=47.

## Default vs tuned weights — train and test metrics

| Metric | Default (train) | Default (test) | Tuned (train) | Tuned (test) |
|---|---:|---:|---:|---:|
| IC vs α | -0.172 | -0.191 | +0.079 | -0.062 |
| Direction agreement | 46.8% | 31.9% | 57.8% | 38.3% |
| Within ±1 tier | 95.4% | 91.5% | 95.4% | 95.7% |

## Tuned weights

| Bot | Default | Tuned | Δ |
|---|---:|---:|---:|
| `market_report` | 0.25 | 0.00 | -0.25 |
| `news_report` | 0.20 | 0.00 | -0.20 |
| `fundamentals_report` | 0.30 | 0.00 | -0.30 |
| `sentiment_report` | 0.10 | 0.00 | -0.10 |
| `investment_plan` | 0.15 | 0.50 | +0.35 |

## Methodology

- Coarse grid search over weights in [0.0, 0.5] step 0.1 across 5 bots = 7776 combinations.
- Objective='ic': maximize Spearman IC of aggregator's direction_score vs realized α.
- Train/test split is date-ordered: oldest 70% → train, newest → test. Tuning on train; reporting on both train AND test for overfitting check (SC-006 requires test ±0.3pp of train).
- Aggregator (`tradingagents/signals/bots.py::aggregate`) is unchanged; only WEIGHTS are tuned.
