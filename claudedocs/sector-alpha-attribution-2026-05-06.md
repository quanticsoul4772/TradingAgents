# Sector-α attribution analyzer — 2026-05-06

**Goal**: identify the 5th failure mode flagged by spec 004 SC-008
validation — bullish commits where the ticker underperforms BOTH
the broad market (SPY) AND its own sector ETF. This is stock-specific
weakness that no current filter (A3 / spec 003 / spec 003.5 / spec 004)
catches.

**Holding window**: 21 trading days
**Corpus**: 234 unique commits → 194 with sector + ETF + valid forward returns

## Cell taxonomy

For each commit, sign(α vs SPY) × sign(α vs sector ETF) defines 4 cells:

| Cell | α vs SPY | α vs sector | Meaning |
|---|---|---|---|
| `ticker_strong` | + | + | Outperformed both — pure win |
| `sector_tide_up` | + | − | Beat SPY but lagged sector (sector lifted the boat) |
| `sector_drag` | − | + | Lagged SPY but beat sector (stock-pick OK; sector down) |
| `ticker_weak` | − | − | Underperformed both — **5th failure mode (stock-specific)** |

## Bullish commits (n=79) — cell distribution + means

| Cell | n | share | mean α vs SPY | mean α vs sector | mean raw |
|---|---|---|---|---|---|
| `ticker_strong` | 28 | 35.4% | +8.72% | +7.71% | +12.16% |
| `sector_tide_up` | 18 | 22.8% | +2.40% | -3.26% | +7.18% |
| `sector_drag` | 6 | 7.6% | -3.87% | +2.66% | +5.80% |
| `ticker_weak` | 27 | 34.2% | -5.34% | -5.80% | -2.97% |

**5th-failure-mode rate among losing bullish commits**: 27/33 = **81.8%** — of bullish commits with α<0 vs SPY, 81.8% also had α<0 vs their sector. This fraction quantifies what % of bullish losses are stock-specific (not sector-rotation).

## Per-sector concentration: bullish `ticker_weak`

| Sector | ETF | n_bull | n_ticker_weak | share | mean α vs SPY | mean α vs sector |
|---|---|---|---|---|---|---|
| Communication Services | XLC | 5 | 0 | 0.0% | n/a | n/a |
| Consumer Cyclical | XLY | 1 | 0 | 0.0% | n/a | n/a |
| Energy | XLE | 1 | 1 | 100.0% | -16.16% | -5.93% |
| Financial Services | XLF | 9 | 2 | 22.2% | -11.39% | -4.98% |
| Healthcare | XLV | 2 | 0 | 0.0% | n/a | n/a |
| Technology | XLK | 61 | 24 | 39.3% | -4.39% | -5.86% |

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

## Bearish commits (n=37) — symmetry check

Inverse interpretation: for bearish commits, `ticker_strong` (α>0 vs both) and `sector_drag` (α<0 vs SPY but α>0 vs sector) are the 'wrong' cells (ticker rallied vs its sector despite the bear call). `ticker_weak` is the successful bearish call (ticker tanked harder than its sector).

| Cell | n | share | mean α vs SPY | mean α vs sector |
|---|---|---|---|---|
| `ticker_strong` | 18 | 48.6% | +28.02% | +25.33% |
| `sector_tide_up` | 6 | 16.2% | +2.16% | -2.50% |
| `sector_drag` | 0 | 0.0% | n/a | n/a |
| `ticker_weak` | 13 | 35.1% | -4.79% | -6.23% |

## Verdict — 5th failure mode is REAL, dominant, and Tech-concentrated

**Headline number**: **81.8% of losing bullish commits are 5th-failure-mode**
(α<0 vs both SPY and sector). This means the vast majority of bullish-commit
losses are stock-specific, NOT sector-rotation. The SC-003 Financials cohort
that originally motivated this analysis is NOT the dominant failure mode —
it's a small subset of a much broader pattern.

**Concentration**: 24 of the 27 bullish `ticker_weak` commits (88.9%) are in
Technology sector. AAPL + MSFT dominate the worst-10 list (8 of 10 entries).
NVDA contributes 2. The mechanism for these tickers is NOT sector rotation
(XLK was holding up); it's **per-ticker mean reversion after bullish-prose-
driven LLM commits on AAPL/MSFT/NVDA at local highs**. This is exactly what
spec 003's `bull_keyword_count` filter is designed to catch — but at default
80% threshold + N≥20 floor, it only fires on 11 eligible commits in the corpus.

**Bearish symmetry is even worse**: 18 of 37 bearish commits (48.6%) landed in
`ticker_strong` (α>0 vs both SPY and sector) with mean α-vs-SPY = **+28.02%**.
This is a massive anti-calibration signal for bearish commits — when the
framework calls Underweight/Sell, the ticker rallies hard against both broad
market and own sector. Reinforces existing project finding (Q4 NVDA bear
analysis): bearish commits are regime-asymmetric and frequently counter-trend.
A3 momentum filter only addresses the per-ticker-already-down case (-5%
threshold); the +28% mean shows there's a separate "bear call on a strong
ticker rallying against its sector" failure mode A3 misses.

## Implications for spec 005 design

The failure mode IS sector-mappable, but the mapping is the OPPOSITE of what
spec 004 was built to catch:

  - Spec 004 fires when sector ETF is DOWN >5% (mean reversion). This is the
    rare case (anti-predictive in corpus retrospective at -0.45pp).
  - The dominant 5th-failure-mode pattern is bullish commits on AAPL/MSFT/NVDA
    when XLK is FLAT-to-UP. The ticker reverses against a calm/rising sector.

**Spec 005 hypothesis to formalize**: a contrarian signal that fires when a
ticker is at an N-day high RELATIVE to its sector ETF (i.e. rolling
ticker-α-vs-sector at the 90th percentile of recent history). This is a
direct sector-relative analog of the spec 003 contrarian gate's per-ticker
bull-prose-percentile mechanism, but operating on price/return data instead
of debate-text features. Should be retrospect-able against the existing
194-row corpus before any spec 005 active-mode flip.

**Constitution III considered**: zero LLM cost (price-only signal); follows
Spec 003 retrospective-before-flip discipline; suppression target is Buy/OW →
Hold (matches existing filter family); per-sector backtest decomposition
already exists in this analyzer.

## Filter-portfolio updated picture

| Filter | Catches | Empirical support | Caveat |
|---|---|---|---|
| A3 momentum (bear/per-ticker) | bear commits on -5% mean-rev tickers | +0.70pp/n=43 | Misses the +28% bear-on-strong-ticker case (this analysis) |
| Spec 003 contrarian (bull/per-ticker prose) | bull commits with high own-history bull_kw | +0.65pp/n=11 | Tiny sample; only fires on NVDA + AAPL |
| Spec 003.5 sector-baseline (bull/sector prose) | cold-start tickers via sector pool | gates the gap | Doesn't help the 27-row 5th-failure-mode cohort (price-driven, not prose-driven) |
| Spec 004 sector-momentum (bull/sector ETF) | bull commits with -5% sector mean-rev | -0.45pp/n=73 anti-predictive | Built against a misread; rarely fires |
| **Spec 005 (proposed): ticker-vs-sector mean reversion** | bull commits on tickers at sector-relative highs | unmeasured | Direct analog to spec 003 in price space |

The portfolio now has a clear gap-and-fill thesis. Spec 003 catches prose-side
mean reversion; spec 005 would catch price-side mean reversion against sector;
together they would address the 27-row Tech-concentrated `ticker_weak` cohort
that today neither filter touches.

## Reproducibility

```
python scripts/sector_alpha_attribution.py --holding-days 21
```

Reads from `experiments/*/results.csv` + spec 002 sectors cache + yfinance
stock + SPY + sector-ETF prices. No LLM cost. Deterministic given a fixed
corpus + holding window.
