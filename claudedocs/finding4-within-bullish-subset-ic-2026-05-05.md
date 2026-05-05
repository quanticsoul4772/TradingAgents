# Finding #4 within-bullish-subset IC test — 2026-05-05

## Question

The strict-prior IC test ruled out look-ahead bias as the explanation for the gap between finding #4's IC = -0.489 and the gate's prospective Δα. This script tests **explanation #2 (within-bullish-subset Δα is a different statistic than all-dates rank IC)** by computing the within-ticker IC over ONLY Buy + Overweight commits per ticker.

**If within-bullish-subset IC ≈ all-dates IC (~-0.49)**: mechanism transfers to bullish subset → explanation #2 REJECTED → low-N noise (explanation #1) is the residual cause.

**If within-bullish-subset IC ≈ 0 or positive**: mechanism doesn't transfer → explanation #2 CONFIRMED → the gate's premise is broken at the bullish-bucket level even with infinite history.

## Method

1. Load `market_report` + `final_trade_decision` from cache; join by (ticker, date)
2. Per ticker, sort by date asc; compute strict-prior percentile of bull_count + realized 90d α via `fetch_returns`
3. Per ticker, compute Spearman IC of (strict_prior_percentile, α) for three subsets (require n ≥ 5):
   - All dates (matches the prior strict-prior IC test)
   - Bullish subset (rating ∈ {Buy, Overweight}) — the gate's actual scope
   - Non-bullish subset (rating ∈ {Hold, Underweight, Sell}) — control
4. Take median across tickers; compare

## Headline

| Subset | Median IC across tickers | n tickers eligible | Direction |
|---|---:|---:|---|
| All dates | **-0.3788** | 9 | 1+ / 8− |
| **Bullish subset (Buy/OW)** | **-0.3012** | 5 | 1+ / 4− |
| Non-bullish subset | **-0.3092** | 9 | 1+ / 8− |

## Per-ticker breakdown

| Ticker | All n | All IC | Bullish n | Bullish IC | Non-bull n | Non-bull IC |
|---|---:|---:|---:|---:|---:|---:|
| AAPL | 27 | -0.202 | 7 | +0.162 | 20 | -0.334 |
| BRK.B | 0 | (0, n<5) | 0 | (0, n<5) | 0 | (0, n<5) |
| GOOGL | 16 | -0.572 | 9 | -0.769 | 7 | -0.036 |
| INTC | 24 | -0.391 | 0 | (0, n<5) | 24 | -0.391 |
| JPM | 16 | -0.411 | 8 | -0.301 | 8 | -0.732 |
| MSFT | 17 | -0.379 | 11 | -0.202 | 6 | -0.319 |
| NVDA | 32 | -0.420 | 27 | -0.400 | 5 | -0.100 |
| XLE | 19 | -0.288 | 2 | (2, n<5) | 17 | -0.309 |
| XLF | 9 | -0.271 | 0 | (0, n<5) | 9 | -0.271 |
| XLK | 9 | +0.034 | 1 | (1, n<5) | 8 | +0.220 |

## Verdict

(Verdict written by hand after reviewing tables.)
