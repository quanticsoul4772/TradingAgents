# XLF mechanism investigation — 2026-05-05

## Question

XLF is the one ticker (of 9) where finding #4's bull_keyword_count anti-signal (future 90d IC -0.58) does NOT fit the recency mechanism documented in `claudedocs/finding4-mechanism-2026-05-05.md`. While 8 of 9 tickers show a positive prior 30d IC (analyst's bull keywords track recent strength), XLF shows -0.27 — **the bullish prose density on XLF is NEGATIVELY correlated with recent strength**.

What's different about XLF? Four hypotheses:
- **H1 macro-driven**: bullish XLF prose follows macro / sector catalysts (yield curve, rate cycle, financial-sector tailwinds), not recent price action
- **H2 bigram pollution**: the bull_keyword set isn't well-calibrated for financial-sector prose (e.g., 'strong' + 'earnings' fire for sector-specific reasons unrelated to recent strength)
- **H3 noise**: XLF has only n=10 cached rows; per-ticker IC noisier than the others
- **H4 sample-window artifact**: XLF's 10 dates cluster in a single regime with structurally different prose patterns

## Method

1. Dump every XLF market_report row's (bull_keyword_count, prior 30d/60d/90d α, future 90d α)
2. For each XLF row, list which specific bull keywords fired and how many times
3. Same view for AAPL (a strong-mechanism ticker, prior 30d IC +0.33) for direct contrast
4. Aggregate keyword usage across rows to spot pattern differences

## XLF (10 cached market_report rows)

Date range: 2026-01-30 → 2026-04-03

### Per-row data

| Date | bull_count | prior_30d α | prior_60d α | prior_90d α | future_90d α | keywords fired |
|---|---:|---:|---:|---:|---:|---|
| 2026-01-30 | 58 | -4.53% | +0.55% | -5.50% | — | `bullish`×17, `momentum`×10, `breakout`×10, `uptrend`×5, `strong`×3, `strength`×2 |
| 2026-02-06 | 40 | -2.62% | +0.03% | -3.40% | — | `momentum`×14, `long`×8, `bullish`×6, `uptrend`×6, `strength`×2, `breakout`×1 |
| 2026-02-13 | 35 | -5.49% | -2.79% | -5.55% | — | `strong`×9, `momentum`×5, `strength`×4, `long`×4, `expanding`×4, `bullish`×3 |
| 2026-02-20 | 76 | -6.48% | -2.81% | -4.14% | — | `momentum`×19, `bullish`×10, `long`×8, `strong`×8, `breakout`×7, `uptrend`×5 |
| 2026-02-27 | 35 | -2.55% | -2.38% | -2.86% | — | `bullish`×12, `momentum`×10, `long`×3, `uptrend`×2, `upside`×2, `strength`×2 |
| 2026-03-06 | 49 | -3.57% | -3.89% | -3.87% | — | `momentum`×12, `bullish`×7, `strong`×6, `long`×5, `upside`×4, `accelerating`×3 |
| 2026-03-13 | 30 | -3.63% | -8.81% | -4.45% | — | `momentum`×8, `long`×7, `strong`×5, `accelerating`×3, `bullish`×2, `breakout`×2 |
| 2026-03-20 | 43 | -5.36% | -7.30% | -4.92% | — | `momentum`×10, `long`×6, `breakout`×5, `strong`×4, `bullish`×4, `strength`×3 |
| 2026-03-27 | 38 | +0.00% | -4.92% | -3.15% | — | `momentum`×12, `long`×6, `positive`×6, `strong`×4, `strength`×3, `accelerating`×2 |
| 2026-04-03 | 44 | -0.61% | -6.79% | -3.33% | — | `momentum`×11, `long`×5, `bullish`×5, `breakout`×5, `catalyst`×4, `uptrend`×3 |

### Aggregate bull_keyword usage across all rows

| Keyword | Total occurrences |
|---|---:|
| `momentum` | 111 |
| `bullish` | 68 |
| `long` | 54 |
| `strong` | 43 |
| `breakout` | 34 |
| `uptrend` | 24 |
| `strength` | 24 |
| `accelerating` | 16 |
| `upside` | 15 |
| `positive` | 14 |
| `catalyst` | 10 |
| `buy` | 8 |
| `expanding` | 7 |
| `rally` | 6 |
| `accumulate` | 3 |
| `buying` | 3 |
| `favorable` | 2 |
| `adding` | 2 |
| `accelerate` | 2 |
| `add` | 1 |
| `tailwinds` | 1 |

## AAPL (23 cached market_report rows)

Date range: 2025-11-07 → 2026-04-24

### Per-row data

| Date | bull_count | prior_30d α | prior_60d α | prior_90d α | future_90d α | keywords fired |
|---|---:|---:|---:|---:|---:|---|
| 2025-11-07 | 73 | +3.16% | +11.39% | +21.13% | -4.66% | `momentum`×14, `strong`×12, `bullish`×12, `breakout`×8, `uptrend`×7, `upside`×4 |
| 2025-11-14 | 77 | +5.83% | +15.28% | +21.56% | -3.49% | `momentum`×14, `long`×11, `uptrend`×9, `rally`×7, `strong`×6, `bullish`×5 |
| 2025-11-21 | 62 | +7.68% | +14.43% | +22.13% | -5.12% | `long`×10, `momentum`×9, `bullish`×8, `uptrend`×7, `buy`×7, `breakout`×4 |
| 2025-11-28 | 89 | +9.24% | +10.62% | +21.35% | -6.49% | `momentum`×17, `uptrend`×14, `rally`×10, `strong`×9, `breakout`×9, `bullish`×7 |
| 2025-12-05 | 54 | +6.23% | +18.67% | +25.11% | -7.13% | `momentum`×12, `uptrend`×7, `positive`×5, `strong`×5, `bullish`×5, `breakout`×4 |
| 2025-12-12 | 55 | +2.93% | +11.61% | +27.25% | -7.82% | `momentum`×9, `uptrend`×8, `bullish`×7, `strong`×6, `rally`×6, `long`×5 |
| 2025-12-19 | 65 | +1.02% | +5.66% | +13.09% | -3.72% | `uptrend`×13, `momentum`×13, `long`×9, `rally`×9, `strong`×6, `bullish`×3 |
| 2025-12-26 | 61 | -1.90% | +3.70% | +10.77% | — | `momentum`×17, `long`×10, `bullish`×8, `breakout`×6, `strong`×5, `uptrend`×5 |
| 2026-01-02 | 63 | -1.10% | +4.18% | +13.20% | — | `momentum`×16, `long`×10, `rally`×8, `breakout`×6, `uptrend`×5, `upside`×3 |
| 2026-01-09 | 35 | -9.53% | +0.40% | +4.19% | — | `momentum`×12, `accelerating`×7, `uptrend`×5, `strong`×3, `buying`×3, `long`×2 |
| 2026-01-30 | 50 | -8.03% | -6.44% | +0.43% | — | `momentum`×16, `bullish`×9, `long`×6, `uptrend`×4, `accelerating`×4, `breakout`×4 |
| 2026-02-06 | 71 | +2.88% | +1.58% | +5.42% | — | `bullish`×15, `strong`×13, `momentum`×10, `positive`×7, `uptrend`×5, `long`×4 |
| 2026-02-13 | 56 | -3.23% | -5.52% | -0.47% | — | `momentum`×16, `positive`×10, `long`×9, `uptrend`×6, `strong`×5, `bullish`×3 |
| 2026-02-20 | 39 | +0.47% | -7.24% | +0.48% | — | `momentum`×14, `bullish`×7, `uptrend`×5, `long`×4, `positive`×2, `strength`×2 |
| 2026-02-27 | 45 | +5.30% | -3.19% | +5.87% | — | `momentum`×15, `breakout`×7, `long`×6, `bullish`×5, `uptrend`×4, `positive`×2 |
| 2026-03-06 | 41 | +5.80% | -6.20% | -1.26% | — | `momentum`×10, `long`×9, `uptrend`×8, `bullish`×5, `strong`×2, `positive`×2 |
| 2026-03-13 | 36 | +4.05% | -5.99% | -3.85% | — | `momentum`×14, `long`×5, `positive`×4, `accelerating`×2, `bullish`×2, `strong`×2 |
| 2026-03-20 | 42 | -6.03% | -5.89% | -6.26% | — | `momentum`×11, `long`×8, `strong`×8, `accelerating`×5, `bullish`×2, `strength`×2 |
| 2026-03-27 | 49 | -1.69% | -1.58% | -3.80% | — | `momentum`×14, `bullish`×11, `long`×6, `strength`×4, `positive`×4, `strong`×3 |
| 2026-04-03 | 71 | +2.14% | +2.58% | -4.87% | — | `momentum`×20, `bullish`×13, `breakout`×9, `positive`×8, `long`×7, `strength`×6 |
| 2026-04-10 | 42 | -3.37% | +2.11% | -6.66% | — | `bullish`×18, `momentum`×5, `upside`×4, `strong`×3, `long`×3, `uptrend`×3 |
| 2026-04-17 | 65 | -2.36% | +3.03% | -9.18% | — | `bullish`×14, `strong`×9, `momentum`×9, `uptrend`×7, `breakout`×7, `strength`×4 |
| 2026-04-24 | 79 | -0.20% | +3.83% | -4.95% | — | `strong`×14, `momentum`×13, `bullish`×13, `uptrend`×10, `breakout`×6, `positive`×5 |

### Aggregate bull_keyword usage across all rows

| Keyword | Total occurrences |
|---|---:|
| `momentum` | 300 |
| `bullish` | 175 |
| `long` | 139 |
| `uptrend` | 136 |
| `strong` | 119 |
| `breakout` | 88 |
| `positive` | 69 |
| `rally` | 63 |
| `strength` | 55 |
| `buying` | 33 |
| `buy` | 33 |
| `accelerating` | 28 |
| `upside` | 26 |
| `expanding` | 9 |
| `add` | 9 |
| `robust` | 8 |
| `catalyst` | 6 |
| `accumulate` | 5 |
| `accelerate` | 5 |
| `constructive` | 4 |
| `favorable` | 3 |
| `adding` | 3 |
| `compelling` | 2 |
| `raising` | 1 |
| `beat` | 1 |

## Verdict

**XLF's "different mechanism" is mostly a sample-window degeneracy, not a structurally different mechanism. H4 (sample-window artifact) explains it; H1/H2/H3 are partial contributors at most.**

### Two structural facts about XLF's data

**Fact 1 — XLF underperformed SPY across the entire backtest window.** Prior 30d α for the 10 XLF dates: -4.53%, -2.62%, -5.49%, -6.48%, -2.55%, -3.57%, -3.63%, -5.36%, +0.00%, -0.61%. Range: -6.48% to 0%. **Every single date had non-positive prior α.** The variance in prior α is small (~6pp range, all in negative territory).

**Fact 2 — bull_keyword_count is consistently high on XLF anyway.** Counts: 58, 40, 35, 76, 35, 49, 30, 43, 38, 44. Range 30-76. The market analyst was writing 30-76 bull-keyword-count prose for XLF on every single date even though XLF was underperforming SPY by 2-7% in the prior 30 days on each of those dates.

### What this means

For 8 of 9 tickers (the recency-mechanism cluster), the analyst's bull keywords TRACK prior strength: bullish prose follows recent gains. For XLF, the analyst's bull keywords PERSIST during a sustained underperformance regime. The data range of "prior strength" on XLF is too narrow (entirely negative-to-zero) to support a recency relationship — there's no high-prior-α data point on XLF to anchor the positive end of any correlation.

The within-ticker IC of -0.27 (prior 30d) and -0.58 (future 90d) for XLF aren't measuring "the analyst tracks prior weakness then mean-reverts" — they're measuring "noise in a degenerate window where one variable has almost no variance."

### The future_90d data is also missing

All 10 XLF dates are 2026-01-30 → 2026-04-03 (the most recent dates in the backtest). 90 trading days from those dates extends past today. With the new buffer fix (`int(holding_days * 1.5) + 7` calendar days), `fetch_returns(holding_days=90)` requires 142 calendar days of forward data; XLF dates have at most ~95 calendar days available. So:
- The within-ticker IC of -0.58 from finding #4 was computed with the OLD buffer (`holding_days + 7`) over truncated `actual_days` (median 50 trading days across the corpus, even less for XLF specifically because its dates are the most recent)
- After the buffer fix, XLF's future_90d IC is essentially undefined for this dataset

### AAPL contrast (recency mechanism active)

AAPL's prior 30d α range: **-9.53% to +9.24%** — wide, mixed signs. Bull_count varies 35-89. With both axes spanning real range, the within-ticker correlation (-0.49 future / +0.33 prior) is mathematically meaningful. Not the case for XLF.

### Hypothesis adjudication

| Hypothesis | Verdict |
|---|---|
| H1 macro-driven | Partial. The analyst's bullish XLF prose is independent of recent price action, but I can't determine here whether it's macro-tracking specifically (would need yield-curve / VIX correlation, which is an unlit follow-up). |
| H2 bigram pollution | **Rejected.** The XLF bull keywords are normal — momentum, bullish, breakout, uptrend, strong — same vocabulary as AAPL. No financial-sector-specific vocabulary anomalies. |
| H3 noise from small n | **Contributing.** n=10 vs n=23 for AAPL means wider CIs, more noise sensitivity. |
| H4 sample-window artifact | **Primary cause.** All 10 XLF dates fall in a single regime where (a) XLF underperformed SPY, (b) prior α has tiny variance, (c) future_90d data is mostly truncated. The within-ticker correlation is degenerate by construction. |

### Implications for spec 003

1. **FR-004 should require N >= 20 historical propagates for the per-ticker percentile baseline** (not the current N >= 5 floor). With only N=10, XLF would have triggered the gate based on a degenerate-window distribution. Bumping the floor to 20 would correctly skip XLF until enough history accumulates.

2. **The contrarian-gate validation grid should EXCLUDE XLF** until at least 20 propagates exist on it AND at least one positive-prior-α date is in the cache. Otherwise the gate's "high bull_keyword_count percentile" detector would fire on every XLF date (since they're all high) without the recency mechanism actually being active.

3. **Update spec 003 SC-002 caveat**: don't expect within-ticker IC reproduction on tickers where prior-α variance is collapsed. Add a precondition: tickers in the validation grid must have prior 30d α range >= 10pp (i.e., contain both meaningfully positive and meaningfully negative prior α observations).

### What this does NOT change

- Finding #4's headline finding (within-ticker IC -0.489, 9/9 unanimous direction) is robust at the population level. XLF being a degenerate-window case doesn't affect the 8 tickers where the recency mechanism IS clearly operating.
- The mechanism investigation (`claudedocs/finding4-mechanism-2026-05-05.md`) verdict stands: recency + mean-reversion is the primary mechanism on the tickers where finding #4 has discriminating data.
- Spec 003 remains motivated. The XLF caveat refines the validation grid, doesn't invalidate the spec.

### Cost

$0 LLM, ~3 min wall-clock (10 + 23 row dumps + yfinance prior-window fetches), reusing existing cache + featurizer.
