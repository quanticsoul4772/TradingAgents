# Counterfactual Signal Report (spec 002 Phase 2)

_Generated 2026-05-04T22:53:42+00:00._

**Counterfactual**: Hold on every UW/Sell date
**Horizon**: 21d
**Total pairs**: 156
**Resolved (have realized alpha)**: 153
**Changed (alternative ≠ actual)**: 25
**Mean alpha delta**: +0.015%
**Total alpha delta**: +2.232%

## Changed pairs (alternative ≠ actual)

| Ticker | Date | Actual | Alternative | Realized α | Actual contrib | Alt contrib | Δ |
|---|---|---|---|---:|---:|---:|---:|
| INTC | 2026-04-03 | Underweight | Hold | +0.77% | -0.77% | +0.00% | +0.77% |
| INTC | 2025-12-26 | Underweight | Hold | +0.50% | -0.50% | +0.00% | +0.50% |
| INTC | 2026-03-20 | Underweight | Hold | +0.48% | -0.48% | +0.00% | +0.48% |
| INTC | 2026-01-02 | Underweight | Hold | +0.22% | -0.22% | +0.00% | +0.22% |
| XLE | 2026-03-27 | Underweight | Hold | -0.21% | +0.21% | -0.00% | -0.21% |
| XLE | 2025-12-26 | Underweight | Hold | +0.11% | -0.11% | +0.00% | +0.11% |
| XLE | 2026-04-03 | Underweight | Hold | -0.09% | +0.09% | -0.00% | -0.09% |
| XLE | 2026-01-02 | Underweight | Hold | +0.09% | -0.09% | +0.00% | +0.09% |
| INTC | 2026-02-20 | Underweight | Hold | +0.09% | -0.09% | +0.00% | +0.09% |
| INTC | 2026-01-09 | Underweight | Hold | +0.08% | -0.08% | +0.00% | +0.08% |
| INTC | 2026-02-06 | Underweight | Hold | -0.08% | +0.08% | -0.00% | -0.08% |
| XLE | 2026-03-06 | Underweight | Hold | +0.08% | -0.08% | +0.00% | +0.08% |
| XLE | 2025-12-19 | Underweight | Hold | +0.07% | -0.07% | +0.00% | +0.07% |
| MSFT | 2026-03-27 | Underweight | Hold | +0.05% | -0.05% | +0.00% | +0.05% |
| XLF | 2026-02-06 | Underweight | Hold | -0.04% | +0.04% | -0.00% | -0.04% |
| MSFT | 2026-02-06 | Underweight | Hold | +0.04% | -0.04% | +0.00% | +0.04% |
| JPM | 2026-02-27 | Underweight | Hold | +0.03% | -0.03% | +0.00% | +0.03% |
| XLK | 2026-02-20 | Underweight | Hold | +0.03% | -0.03% | +0.00% | +0.03% |
| INTC | 2026-02-27 | Underweight | Hold | +0.02% | -0.02% | +0.00% | +0.02% |
| AAPL | 2025-11-21 | Underweight | Hold | -0.02% | +0.02% | -0.00% | -0.02% |
| MSFT | 2026-02-20 | Underweight | Hold | +0.02% | -0.02% | +0.00% | +0.02% |
| XLF | 2026-01-30 | Underweight | Hold | -0.01% | +0.01% | -0.00% | -0.01% |
| GOOGL | 2026-03-06 | Underweight | Hold | +0.01% | -0.01% | +0.00% | +0.01% |
| INTC | 2026-02-13 | Underweight | Hold | -0.01% | +0.01% | -0.00% | -0.01% |
| AAPL | 2026-04-10 | Underweight | Hold | +0.01% | -0.01% | +0.00% | +0.01% |

## Methodology

- **Alpha contribution** = direction(rating) × realized_alpha. Direction maps Buy/Overweight to +1, Hold to 0, Underweight/Sell to -1.
- A bullish commit on a positive-α date contributes positively; on a negative-α date, negatively. A Hold contributes 0 by construction.
- **Alpha delta** = alternative contribution − actual contribution. Positive delta = the counterfactual rating would have produced better alpha than the actual.
- This MVP does NOT simulate a deterministic aggregator (spec 001). It compares the actual PM rating to whatever alternative the caller provides via a function.
