# UW commit-suppression filter retrospective (A3)

_Generated 2026-05-03T06:45:54.405271_

> **Status**: in-sample retrospective on n=16 UW commits prior to A3 productionization. Superseded for the post-007 question of "does the filter behave correctly on a fresh run" by [`a3-filter-forensics-007.md`](a3-filter-forensics-007.md) — which showed the filter correctly stays inert on regime-mismatch failures (INTC × Q1 2026 was UP +11-33% at 4 of 6 UW dates, never in the suppression zone). This doc remains the in-sample evidence base for the filter's design rationale; do not cite it for "filter is/isn't generalizing" — cite the forensics doc instead.

Filter rule: suppress UW (treat as Hold) if ticker is in mean-reversion zone (tic_mom < downside_thr).
Hypothesis discovered in this analysis: wrong UW commits cluster on tickers already deeply down → forward 21d mean-reverts bullishly.
Horizon 21d. Convention: UW correct ⇔ α<0.


## Baseline (no filter)

- n = 16
- mean α = +1.97%
- correct rate (α<0) = 31%


## Threshold sweep (downside mean-reversion filter)

| downside_thr | n_kept | n_suppressed | kept α | suppressed α | kept correct% | improvement |
|---|---|---|---|---|---|---|
| -5.0% | 9 | 7 | +0.82% | +3.45% | 33% | +1.15pp |
| -7.5% | 10 | 6 | +1.07% | +3.47% | 30% | +0.90pp |
| -10.0% | 13 | 3 | +2.51% | -0.34% | 31% | -0.53pp |
| -12.5% | 13 | 3 | +2.51% | -0.34% | 31% | -0.53pp |
| -15.0% | 13 | 3 | +2.51% | -0.34% | 31% | -0.53pp |

## Per-(ticker, date) UW commit features

| Ticker | Date | 21d α | UW correct | SPY 30d mom | ticker 30d mom |
|---|---|---|---|---|---|
| AAPL | 2026-01-30 | +3.33% | ✗ | +1.96% | -5.78% |
| AAPL | 2026-02-06 | -4.27% | ✓ | -1.05% | +1.82% |
| AAPL | 2026-02-13 | +1.00% | ✗ | -0.84% | -4.16% |
| AAPL | 2026-02-20 | -0.01% | ✓ | -1.06% | -0.68% |
| AAPL | 2026-02-27 | +1.23% | ✗ | -0.64% | +4.56% |
| AAPL | 2026-03-06 | +0.42% | ✗ | -0.60% | +5.10% |
| AAPL | 2026-03-13 | -1.38% | ✓ | -4.22% | -0.27% |
| AAPL | 2026-03-20 | -1.23% | ✓ | -3.85% | -9.96% |
| MSFT | 2026-02-06 | +3.10% | ✗ | -1.05% | -18.82% |
| MSFT | 2026-02-20 | +1.36% | ✗ | -1.06% | -16.73% |
| MSFT | 2026-03-13 | -5.47% | ✓ | -4.22% | -16.56% |
| MSFT | 2026-03-27 | +8.08% | ✗ | -6.77% | -9.50% |
| NVDA | 2026-02-27 | +1.09% | ✗ | -0.64% | -0.50% |
| NVDA | 2026-03-06 | +2.11% | ✗ | -0.60% | +0.01% |
| NVDA | 2026-03-20 | +7.18% | ✗ | -3.85% | +2.51% |
| NVDA | 2026-03-27 | +15.01% | ✗ | -6.77% | -9.90% |

## Best operating point


**Suppress UW when ticker 30d momentum < -5.0%** (mean-reversion zone)

- Kept UW commits: n=9, mean α = **+0.82%** (baseline +1.97%)
- Suppressed commits: n=7
- α improvement: **+1.15pp**

_Caveat: in-sample validation on the same 16 commits that informed the hypothesis. Out-of-sample test requires fresh data._
