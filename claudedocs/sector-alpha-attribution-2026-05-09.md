# Sector-α attribution analyzer — 2026-05-09

**Goal**: identify the 5th failure mode flagged by spec 004 SC-008
validation — bullish commits where the ticker underperforms BOTH
the broad market (SPY) AND its own sector ETF. This is stock-specific
weakness that no current filter (A3 / spec 003 / spec 003.5 / spec 004)
catches.

**Holding window**: 21 trading days
**Corpus**: 300 unique commits → 260 with sector + ETF + valid forward returns

## Cell taxonomy

For each commit, sign(α vs SPY) × sign(α vs sector ETF) defines 4 cells:

| Cell | α vs SPY | α vs sector | Meaning |
|---|---|---|---|
| `ticker_strong` | + | + | Outperformed both — pure win |
| `sector_tide_up` | + | − | Beat SPY but lagged sector (sector lifted the boat) |
| `sector_drag` | − | + | Lagged SPY but beat sector (stock-pick OK; sector down) |
| `ticker_weak` | − | − | Underperformed both — **5th failure mode (stock-specific)** |

## Bullish commits (n=82) — cell distribution + means

| Cell | n | share | mean α vs SPY | mean α vs sector | mean raw |
|---|---|---|---|---|---|
| `ticker_strong` | 29 | 35.4% | +8.94% | +7.64% | +12.68% |
| `sector_tide_up` | 20 | 24.4% | +2.42% | -3.65% | +7.70% |
| `sector_drag` | 6 | 7.3% | -3.87% | +2.66% | +5.80% |
| `ticker_weak` | 27 | 32.9% | -5.34% | -5.80% | -2.97% |

**5th-failure-mode rate among losing bullish commits**: 27/33 = **81.8%** — of bullish commits with α<0 vs SPY, 81.8% also had α<0 vs their sector. This fraction quantifies what % of bullish losses are stock-specific (not sector-rotation).

## Per-sector concentration: bullish `ticker_weak`

| Sector | ETF | n_bull | n_ticker_weak | share | mean α vs SPY | mean α vs sector |
|---|---|---|---|---|---|---|
| Communication Services | XLC | 5 | 0 | 0.0% | +nan% | +nan% |
| Consumer Cyclical | XLY | 1 | 0 | 0.0% | +nan% | +nan% |
| Energy | XLE | 1 | 1 | 100.0% | -16.16% | -5.93% |
| Financial Services | XLF | 9 | 2 | 22.2% | -11.39% | -4.98% |
| Healthcare | XLV | 2 | 0 | 0.0% | +nan% | +nan% |
| Technology | XLK | 64 | 24 | 37.5% | -4.39% | -5.86% |

## Worst bullish 5th-failure-mode commits (top 10 by |α vs sector|)

| Ticker | Date | Sector | Rating | α vs SPY | α vs sector | raw |
|---|---|---|---|---|---|---|
| AAPL | 2026-03-27 | Technology | Overweight | -3.43% | -12.69% | +8.81% |
| AAPL | 2026-04-01 | Technology | Overweight | -0.39% | -10.40% | +9.59% |
| MSFT | 2026-03-11 | Technology | Overweight | -9.14% | -10.09% | -8.40% |
| AAPL | 2026-03-25 | Technology | Overweight | -1.40% | -9.85% | +7.30% |
| MSFT | 2026-03-06 | Technology | Overweight | -7.28% | -9.19% | -8.97% |
| MSFT | 2026-03-13 | Technology | Overweight | -5.76% | -8.89% | -0.62% |
| AAPL | 2025-12-12 | Technology | Overweight | -8.14% | -7.44% | -6.58% |
| AAPL | 2025-12-05 | Technology | Overweight | -7.48% | -6.72% | -6.62% |
| NVDA | 2025-08-22 | Technology | Overweight | -2.81% | -6.67% | +0.25% |
| NVDA | 2025-08-08 | Technology | Overweight | -8.60% | -6.32% | -6.54% |

## Bearish commits (n=50) — symmetry check

Inverse interpretation: for bearish commits, `ticker_strong` (α>0 vs both) and `sector_drag` (α<0 vs SPY but α>0 vs sector) are the 'wrong' cells (ticker rallied vs its sector despite the bear call). `ticker_weak` is the successful bearish call (ticker tanked harder than its sector).

| Cell | n | share | mean α vs SPY | mean α vs sector |
|---|---|---|---|---|
| `ticker_strong` | 22 | 44.0% | +32.64% | +28.98% |
| `sector_tide_up` | 9 | 18.0% | +2.82% | -3.53% |
| `sector_drag` | 1 | 2.0% | -5.26% | +0.12% |
| `ticker_weak` | 18 | 36.0% | -4.70% | -5.85% |

## Implications

- If `ticker_weak` share among bullish commits is HIGH and concentrated in a
  single sector → spec 005 needs a per-ticker-vs-sector α signal targeting that
  sector (matches the SC-003 Financials cohort prediction).
- If `ticker_weak` share is LOW → the 5th failure mode is rare and operator
  acceptance via Constitution VII calibrated abstention is the correct response.
- If `ticker_weak` is uniformly distributed → the failure mode is stock-specific
  but not sector-concentrated, and would need a different signal (per-ticker
  earnings risk, news sentiment, option-implied skew, etc.).

## Reproducibility

```
python scripts/sector_alpha_attribution.py --holding-days 21
```

Reads from `experiments/*/results.csv` + spec 002 sectors cache + yfinance
stock + SPY + sector-ETF prices. No LLM cost. Deterministic given a fixed
corpus + holding window.
