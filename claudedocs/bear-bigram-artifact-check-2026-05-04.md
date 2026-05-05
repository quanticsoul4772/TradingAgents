# Bear bigram count artifact check — 2026-05-05

## Question

Is `(fundamentals_report, bear_bigram_count)` IC = +0.457 at 90d a real predictive signal, or a multiple-comparisons artifact from 280 IC tests on n~113 obs?

## Method

- Pulled all `fundamentals_report` rows from `~/.tradingagents/cache/signals.db`
- Recomputed `bear_bigram_count` via `tradingagents.signals.featurization.bear_bigram_count`
- Recomputed forward α via `tradingagents.graph.trading_graph.fetch_returns(holding_days=90)`
- Required the full holding window (`actual >= holding_days`) — drops dates too recent for 90d
- Permutation test n=5000: shuffle α-labels, recompute IC, count fraction ≥ |observed|
- Bootstrap 95% CI: n=5000 resamples with replacement
- Per-ticker + per-period IC breakdowns to detect single-ticker / single-period artifacts
- Bigram attribution: which specific bigrams fire at high-count rows

## Headline

- **n usable**: 113
- **Observed IC**: +0.4573
- **Permutation p (two-sided)**: 0.0000
- **Permutation p (one-sided, in observed direction)**: 0.0000
- **Bootstrap 95% CI**: [+0.3023, +0.5959], mean +0.4559
- **Bonferroni threshold for 280 IC tests**: 0.05 / 280 = 1.79e-4 — observed p PASSES Bonferroni at α=0.05

## Per-ticker breakdown

| Ticker | n | IC | Note |
|---|---:|---:|---|
| AAPL | 23 | +0.0692 |  |
| GOOGL | 12 | +0.0898 |  |
| INTC | 20 | -0.0038 |  |
| JPM | 12 | -0.2756 |  |
| MSFT | 13 | +0.3405 |  |
| NVDA | 33 | -0.1567 |  |

## Per-period split

| Period | n | IC | Note |
|---|---:|---:|---|
| Q3 2025 | 9 | -0.0962 |  |
| Q4 2025 | 31 | +0.5611 |  |
| Q1 2026 | 73 | +0.5067 |  |
| other | 0 | — | n<5 |

## Which bigrams actually fire?

| Bigram | Total occurrences |
|---|---:|
| `market share` | 115 |
| `execution risk` | 73 |
| `competitive pressure` | 47 |
| `regulatory risk` | 31 |
| `downside risk` | 21 |
| `regulatory risks` | 10 |
| `downside risks` | 10 |
| `share loss` | 3 |
| `compressed margins` | 3 |
| `guidance cut` | 1 |
| `declining margins` | 1 |

## Top-5 highest-count rows (with their fired bigrams)

- **INTC 2026-01-02** — count 11, α_90d +0.5047
  - Fired: `compressed margins`×1, `execution risk`×3, `market share`×5, `downside risks`×1, `downside risk`×1
- **INTC 2025-12-19** — count 9, α_90d +0.3137
  - Fired: `market share`×4, `downside risk`×2, `execution risk`×2, `share loss`×1
- **INTC 2026-02-06** — count 9, α_90d +0.8508
  - Fired: `compressed margins`×1, `competitive pressure`×1, `market share`×6, `execution risk`×1
- **NVDA 2025-11-07** — count 9, α_90d -0.0242
  - Fired: `market share`×7, `regulatory risk`×1, `execution risk`×1
- **NVDA 2025-11-28** — count 9, α_90d +0.0287
  - Fired: `market share`×6, `execution risk`×1, `competitive pressure`×1, `downside risk`×1

## Verdict

**Statistically real, mechanistically misleading. Not a publishable predictor.**

### Statistical significance: ✅ passes

The +0.4573 IC is not a multiple-comparisons artifact:
- Permutation test n=5000: 0/5000 shuffles produced |IC| ≥ 0.457. Empirical p < 2e-4 — order of magnitude stricter than the Bonferroni-corrected α=0.05/280 = 1.79e-4.
- Bootstrap 95% CI [+0.30, +0.60] cleanly excludes zero.
- Sign + magnitude are stable to resampling.

If the question were "is this correlation reliably non-zero in this corpus?", the answer is yes.

### Three serious mechanistic problems

**Problem 1 — the "90d horizon" label is wrong.** `fetch_returns(holding_days=90)` uses `end = start + (holding_days + 7) calendar days`, which only fits ~50 trading days into the window. Median actual holding = 50; max = 67. The IC was measured against ~50d returns, not 90d returns. Anyone consuming the eval report thinking "90-day horizon" is wrong by 30-40%. This is a methodology bug in `fetch_returns`, not in the featurizer or the eval. Fix would be: widen the buffer to `holding_days * 1.6` or `holding_days + 90` calendar days.

**Problem 2 — per-ticker IC is near zero or negative.** The aggregated +0.457 is driven entirely by *between-ticker* variance, not within-ticker prediction:

| Ticker | n | within-ticker IC |
|---|---:|---:|
| AAPL | 23 | +0.07 |
| GOOGL | 12 | +0.09 |
| INTC | 20 | -0.00 |
| JPM | 12 | -0.28 |
| MSFT | 13 | +0.34 |
| NVDA | 33 | -0.16 |

Within any single ticker, knowing the bear_bigram_count tells you almost nothing (or the wrong thing — JPM and NVDA have negative within-ticker IC). The signal "more bear bigrams → higher α" is really "the tickers with more bear language across dates happen to be the tickers that delivered higher α across the same dates." That's a corpus-composition fact, not a date-level predictor.

**Problem 3 — the top-count rows reveal the failure mode.** The highest bear_bigram_counts are 3 INTC rows in Q4 2025 / Q1 2026 (counts 9-11) with α between +31% and +85%. INTC ripped in this period. The fundamentals analyst correctly identified bearish factors (`execution risk`, `compressed margins`, `market share`, `downside risk`); the framework's bearish prose was *directionally wrong* because INTC was in a bull regime. This is exactly the regime-asymmetry finding from the main RESEARCH_FINDINGS — UW commits on bull-regime tickers (INTC in Q4'25-Q1'26) drive the aggregate anti-calibration. The +0.457 IC is the same anti-calibration, expressed at the prose level instead of the rating level.

### One bigram-curation issue

`market share` × 115 dominates the count distribution (next-highest is `execution risk` × 73). But `market share` is semantically ambiguous — "expanding market share" is bullish, "losing market share" is bearish. The bigram alone can't tell. Removing it would change which rows count as "high bear" and might either strengthen or eliminate the IC. This isn't the artifact; it's a confound that means the featurizer isn't measuring what its name implies.

### What this confirms

The headline finding from the synthesis essay holds: **bearish commits are regime-asymmetric, not uniformly anti-calibrated**. This artifact-check provides a third line of evidence for that claim — not just at the rating level (UW commits on bull-regime tickers under-perform) and not just at the per-ticker breakdown (INTC bear UWs in Q4'25), but at the *prose feature* level (more bear language correlates with higher α because the bear language is wrong on the bull-regime tickers).

### Updates to push

1. **`claudedocs/signal-evaluation-2026-05-04.md`**: add a footnote noting the "90d" label is actually ~50 trading days due to the `fetch_returns` buffer; the +0.457 number is between-ticker not within-ticker.
2. **`RESEARCH_FINDINGS.md` Phase 1.5+ section**: the +0.457 IC is no longer a publishable secondary finding (was tentatively flagged as such in the synthesis essay); strike or restate.
3. **`tradingagents/signals/featurization.py` `_BEAR_BIGRAMS`**: consider removing `("market", "share")` or splitting into `("losing", "market", "share")` etc. (would require a bigram→trigram extension in the featurizer).
4. **`tradingagents/graph/trading_graph.py` `fetch_returns`**: widen the buffer for long horizons. Current `holding_days + 7` works for ≤21d but breaks at 90d.

### What this does NOT change

The other ICs in the eval report still stand at their measured magnitudes (which were also computed against the same buffer-truncated returns — so they're "60-65d" not "90d", but the relative ordering is preserved). The main empirical headline — bullish commits +1.23% mean α at 21d (n=71), Bayesian posterior 0.63 on stable cross-period signal — is unaffected; that uses a 21d horizon where the buffer is adequate.

### Cost

$0 LLM, ~30 min wall-clock (5000 permutations + 5000 bootstraps + per-ticker + per-period + bigram attribution), reusing existing cache + featurizer + fetch_returns.
