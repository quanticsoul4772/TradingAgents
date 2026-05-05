# Within-ticker artifact check — 2026-05-05

## Question

The within-ticker IC column added to `scripts/evaluate_signals.py` surfaced 3 candidates where the within-ticker median IC was materially stronger than the aggregate IC. Most striking: `market_report bull_keyword_count` showed within-ticker IC -0.489 with 9 of 9 tickers negative — unanimous direction agreement.

Are these REAL within-ticker predictors, or do they fall apart under closer artifact scrutiny (per-ticker bootstrap CIs include zero, period-instability, within-ticker permutation null is reachable)?

## Method

For each candidate `(signal, feature)` pair:
1. Pull all cached rows; compute featurizer + 90d forward α (post-buffer-fix)
2. Per-ticker IC + bootstrap 95% CI (n=5000)
3. **Within-ticker permutation test** (n=5000): shuffle α INDEPENDENTLY within each ticker, then recompute the within-ticker median IC. This preserves between-ticker structure and tests only the within-ticker null. Three p-values:
   - two-sided: shuffled |median| ≥ |observed|
   - one-sided: shuffled median in observed direction
   - unanimous-direction: shuffled max(n_pos, n_neg) ≥ observed
4. Per-period within-ticker stability (Q3'25 / Q4'25 / Q1'26)

## `market_report` × `bull_keyword_count`

**Expected (from eval report)**: within-ticker median IC = -0.489, sign agreement 0+/9−.

**Observed**: within-ticker median IC = -0.4890

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.0000
- p (one-sided, in observed direction): 0.0000
- p (unanimous direction agreement): 0.0050

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | -0.4890 | [-0.796, -0.054] | − |
| GOOGL | 12 | -0.6025 | [-0.923, +0.000] | − |
| INTC | 20 | -0.4757 | [-0.831, +0.028] | − |
| JPM | 12 | -0.2098 | [-0.771, +0.582] | − |
| MSFT | 13 | -0.6410 | [-0.899, -0.161] | − |
| NVDA | 33 | -0.4462 | [-0.703, -0.095] | − |
| XLE | 20 | -0.5064 | [-0.812, -0.092] | − |
| XLF | 10 | -0.5836 | [-0.962, +0.167] | − |
| XLK | 10 | -0.2371 | [-0.814, +0.599] | − |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | -0.7531 | 0 | 1 |
| Q4 2025 | 4 | -0.1914 | 0 | 4 |
| Q1 2026 | 9 | -0.5836 | 0 | 9 |

## `investment_plan` × `bull_keyword_count`

**Expected (from eval report)**: within-ticker median IC = -0.295, sign agreement 1+/8−.

**Observed**: within-ticker median IC = -0.2948

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.0068
- p (one-sided, in observed direction): 0.0040
- p (unanimous direction agreement): 0.0390

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | -0.4467 | [-0.715, -0.060] | − |
| GOOGL | 12 | -0.6925 | [-0.929, -0.160] | − |
| INTC | 20 | -0.5802 | [-0.898, -0.089] | − |
| JPM | 12 | -0.3018 | [-0.614, +0.340] | − |
| MSFT | 13 | -0.2948 | [-0.841, +0.418] | − |
| NVDA | 33 | -0.1423 | [-0.484, +0.242] | − |
| XLE | 20 | +0.0008 | [-0.433, +0.440] | + |
| XLF | 10 | -0.0307 | [-0.736, +0.686] | − |
| XLK | 10 | -0.1288 | [-0.696, +0.505] | − |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | +0.2833 | 1 | 0 |
| Q4 2025 | 4 | -0.3041 | 1 | 3 |
| Q1 2026 | 9 | -0.2948 | 1 | 8 |

## `investment_plan` × `hedge_density`

**Expected (from eval report)**: within-ticker median IC = -0.189, sign agreement 2+/7−.

**Observed**: within-ticker median IC = -0.1888

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.0894
- p (one-sided, in observed direction): 0.0444
- p (unanimous direction agreement): 0.0440

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | -0.1591 | [-0.610, +0.318] | − |
| GOOGL | 12 | -0.1888 | [-0.787, +0.650] | − |
| INTC | 20 | -0.0331 | [-0.562, +0.455] | − |
| JPM | 12 | -0.3497 | [-0.892, +0.333] | − |
| MSFT | 13 | -0.2912 | [-0.742, +0.292] | − |
| NVDA | 33 | -0.1390 | [-0.491, +0.232] | − |
| XLE | 20 | -0.1925 | [-0.623, +0.309] | − |
| XLF | 10 | +0.0061 | [-0.602, +0.748] | + |
| XLK | 10 | -0.2364 | [-0.787, +0.557] | − |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | -0.3333 | 0 | 1 |
| Q4 2025 | 4 | -0.1364 | 1 | 3 |
| Q1 2026 | 9 | -0.1879 | 2 | 7 |

## `fundamentals_report` × `sentiment_score`

**Expected (from eval report)**: within-ticker median IC = +0.166, sign agreement 4+/1−.

**Observed**: within-ticker median IC = +0.1135

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.3350
- p (one-sided, in observed direction): 0.1748
- p (unanimous direction agreement): 0.6900

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | +0.3231 | [-0.089, +0.638] | + |
| GOOGL | 12 | +0.2657 | [-0.433, +0.788] | + |
| INTC | 20 | +0.1151 | [-0.360, +0.536] | + |
| JPM | 12 | -0.5594 | [-0.889, +0.174] | − |
| MSFT | 13 | +0.0000 | [-0.593, +0.614] | 0 |
| NVDA | 33 | +0.1120 | [-0.255, +0.438] | + |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | +0.1667 | 1 | 0 |
| Q4 2025 | 3 | -0.0667 | 1 | 2 |
| Q1 2026 | 6 | -0.0165 | 2 | 3 |

## `fundamentals_report` × `negation_aware_sentiment_score`

**Expected (from eval report)**: within-ticker median IC = +0.167, sign agreement 5+/1−.

**Observed**: within-ticker median IC = +0.1152

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.3258
- p (one-sided, in observed direction): 0.1708
- p (unanimous direction agreement): 0.2218

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | +0.2955 | [-0.117, +0.628] | + |
| GOOGL | 12 | +0.2657 | [-0.433, +0.788] | + |
| INTC | 20 | +0.1181 | [-0.346, +0.547] | + |
| JPM | 12 | -0.5594 | [-0.889, +0.174] | − |
| MSFT | 13 | +0.0549 | [-0.564, +0.677] | + |
| NVDA | 33 | +0.1123 | [-0.246, +0.434] | + |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | +0.0333 | 1 | 0 |
| Q4 2025 | 3 | -0.0424 | 1 | 2 |
| Q1 2026 | 6 | +0.0055 | 3 | 3 |

## `fundamentals_report` × `bull_bear_keyword_ratio`

**Expected (from eval report)**: within-ticker median IC = +0.166, sign agreement 4+/1−.

**Observed**: within-ticker median IC = +0.1175

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.3158
- p (one-sided, in observed direction): 0.1636
- p (unanimous direction agreement): 0.6902

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | +0.3231 | [-0.089, +0.638] | + |
| GOOGL | 12 | +0.2657 | [-0.433, +0.788] | + |
| INTC | 20 | +0.1151 | [-0.360, +0.536] | + |
| JPM | 12 | -0.5594 | [-0.889, +0.174] | − |
| MSFT | 13 | +0.0000 | [-0.593, +0.614] | 0 |
| NVDA | 33 | +0.1200 | [-0.252, +0.443] | + |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | +0.1667 | 1 | 0 |
| Q4 2025 | 3 | -0.0667 | 1 | 2 |
| Q1 2026 | 6 | -0.0165 | 2 | 3 |

## `fundamentals_report` × `bear_keyword_count`

**Expected (from eval report)**: within-ticker median IC = -0.014, sign agreement 3+/3−.

**Observed**: within-ticker median IC = -0.0112

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.9266
- p (one-sided, in observed direction): 0.4732
- p (unanimous direction agreement): 1.0000

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | -0.0252 | [-0.459, +0.393] | − |
| GOOGL | 12 | -0.2601 | [-0.850, +0.493] | − |
| INTC | 20 | +0.2902 | [-0.181, +0.687] | + |
| JPM | 12 | +0.4483 | [-0.227, +0.783] | + |
| MSFT | 13 | +0.0028 | [-0.547, +0.578] | + |
| NVDA | 33 | -0.1552 | [-0.502, +0.231] | − |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | -0.0252 | 0 | 1 |
| Q4 2025 | 3 | +0.4303 | 2 | 1 |
| Q1 2026 | 6 | -0.0496 | 3 | 3 |

## `fundamentals_report` × `percent_mention_count`

**Expected (from eval report)**: within-ticker median IC = +0.010, sign agreement 3+/3−.

**Observed**: within-ticker median IC = +0.0114

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.9194
- p (one-sided, in observed direction): 0.4566
- p (unanimous direction agreement): 1.0000

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | +0.3015 | [-0.114, +0.624] | + |
| GOOGL | 12 | -0.4623 | [-0.885, +0.208] | − |
| INTC | 20 | +0.1937 | [-0.288, +0.694] | + |
| JPM | 12 | +0.0351 | [-0.719, +0.686] | + |
| MSFT | 13 | -0.0551 | [-0.650, +0.539] | − |
| NVDA | 33 | -0.0122 | [-0.374, +0.362] | − |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | +0.0333 | 1 | 0 |
| Q4 2025 | 3 | +0.1763 | 2 | 1 |
| Q1 2026 | 6 | -0.0397 | 2 | 4 |

## `market_report` × `question_density`

**Expected (from eval report)**: within-ticker median IC = -0.027, sign agreement 1+/3−.

**Observed**: within-ticker median IC = -0.0448

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.7430
- p (one-sided, in observed direction): 0.3780
- p (unanimous direction agreement): 0.6166

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | — | — | n<5 |
| GOOGL | 12 | -0.0753 | [-0.523, +0.340] | − |
| INTC | 20 | -0.2814 | [-0.550, -0.017] | − |
| JPM | 12 | — | — | n<5 |
| MSFT | 13 | — | — | n<5 |
| NVDA | 33 | +0.0557 | [-0.056, +0.201] | + |
| XLE | 20 | -0.0144 | [-0.406, +0.349] | − |
| XLF | 10 | — | — | n<5 |
| XLK | 10 | — | — | n<5 |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | +0.4108 | 1 | 0 |
| Q4 2025 | 2 | -0.1025 | 0 | 2 |
| Q1 2026 | 2 | -0.0666 | 0 | 2 |

## `news_report` × `bull_bigram_count`

**Expected (from eval report)**: within-ticker median IC = -0.269, sign agreement 2+/7−.

**Observed**: within-ticker median IC = -0.2688

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.0124
- p (one-sided, in observed direction): 0.0050
- p (unanimous direction agreement): 0.1742

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | -0.2918 | [-0.647, +0.133] | − |
| GOOGL | 12 | -0.0638 | [-0.737, +0.613] | − |
| INTC | 20 | +0.1990 | [-0.316, +0.683] | + |
| JPM | 12 | -0.1595 | [-0.717, +0.486] | − |
| MSFT | 13 | -0.4009 | [-0.853, +0.180] | − |
| NVDA | 33 | +0.0804 | [-0.285, +0.429] | + |
| XLE | 20 | -0.3487 | [-0.709, +0.099] | − |
| XLF | 10 | -0.5790 | [-0.887, +0.076] | − |
| XLK | 10 | -0.2688 | [-0.785, +0.440] | − |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | +0.0681 | 1 | 0 |
| Q4 2025 | 4 | -0.1808 | 1 | 3 |
| Q1 2026 | 9 | -0.2688 | 2 | 7 |

## `investment_plan` × `bear_bigram_count`

**Expected (from eval report)**: within-ticker median IC = -0.262, sign agreement 2+/7−.

**Observed**: within-ticker median IC = -0.2624

### Within-ticker permutation test

(shuffle α independently within each ticker — preserves between-ticker structure)

- p (two-sided, |IC|): 0.0206
- p (one-sided, in observed direction): 0.0102
- p (unanimous direction agreement): 0.1904

### Per-ticker IC + bootstrap CI

| Ticker | n | IC | 95% CI | Sign |
|---|---:|---:|---|---|
| AAPL | 23 | -0.2624 | [-0.616, +0.148] | − |
| GOOGL | 12 | -0.0393 | [-0.669, +0.599] | − |
| INTC | 20 | -0.5413 | [-0.826, -0.107] | − |
| JPM | 12 | -0.2752 | [-0.752, +0.322] | − |
| MSFT | 13 | -0.3586 | [-0.782, +0.230] | − |
| NVDA | 33 | -0.0644 | [-0.403, +0.272] | − |
| XLE | 20 | +0.1760 | [-0.325, +0.632] | + |
| XLF | 10 | +0.3190 | [-0.355, +0.817] | + |
| XLK | 10 | -0.4824 | [-0.935, +0.290] | − |

### Per-period within-ticker median IC

| Period | n tickers (n≥5) | median IC | n_pos | n_neg |
|---|---:|---:|---:|---:|
| Q3 2025 | 1 | -0.6384 | 0 | 1 |
| Q4 2025 | 4 | -0.3825 | 1 | 3 |
| Q1 2026 | 9 | -0.0393 | 4 | 5 |

## Verdict

**Of 11 candidates artifact-checked across all flagged Simpson's-paradox + inverse-pattern (signal, feature) pairs from the eval report: only 1 is a real within-ticker predictor (`market_report bull_keyword_count`, already validated). 5 are noise. 3 are marginal (pass α=0.05 but fail Bonferroni). 2 are not predictors.**

### Headline summary

| # | Signal × Feature | Within median IC | p (two-sided) | Bonferroni @ 0.05/280 | Verdict |
|---|---|---:|---:|---|---|
| 1 | `market_report` × `bull_keyword_count` | **-0.4890** | **0.0000** | **PASS** | ✅ **Real** (prior validation) |
| 2 | `investment_plan` × `bull_keyword_count` | -0.2948 | 0.0068 | FAIL | ⚠️ Marginal (prior) |
| 3 | `investment_plan` × `hedge_density` | -0.1888 | 0.0894 | FAIL | ❌ Not predictor (prior) |
| 4 | `fundamentals_report` × `sentiment_score` | +0.1135 | 0.3350 | FAIL | ❌ Not predictor |
| 5 | `fundamentals_report` × `negation_aware_sentiment_score` | +0.1152 | 0.3258 | FAIL | ❌ Not predictor |
| 6 | `fundamentals_report` × `bull_bear_keyword_ratio` | +0.1175 | 0.3158 | FAIL | ❌ Not predictor |
| 7 | `fundamentals_report` × `bear_keyword_count` | -0.0112 | 0.9266 | FAIL | ❌ Noise |
| 8 | `fundamentals_report` × `percent_mention_count` | +0.0114 | 0.9194 | FAIL | ❌ Noise |
| 9 | `market_report` × `question_density` | -0.0448 | 0.7430 | FAIL | ❌ Not predictor |
| 10 | `news_report` × `bull_bigram_count` | -0.2688 | 0.0124 | FAIL | ⚠️ Marginal |
| 11 | `investment_plan` × `bear_bigram_count` | -0.2624 | 0.0206 | FAIL | ⚠️ Marginal |

### What the 8 new candidates tell us

**5 not-a-predictor / noise outcomes** (candidates 4-9 minus 10): the Simpson's-paradox ⚠️ flags from the eval report were correctly identifying that the AGGREGATE IC was misleading, but the within-ticker IC in the OPPOSITE direction is mostly noise — not a signal in the other direction. The aggregate values (-0.279 for sentiment_score, etc.) don't translate into within-ticker predictive power either way. The features just don't carry within-ticker information.

This corroborates the negative-result finding from the morning's check: most fundamentals_report features carry between-ticker (ticker-class identification) information at the aggregate level, but their within-ticker predictive content is near-zero. The Simpson's-paradox flag was correctly catching the artifact; the inverse direction wasn't a separate finding.

**3 marginal candidates** (2, 10, 11): all pass α=0.05 but all fail Bonferroni for 280 tests:
- `investment_plan bull_keyword_count` — diluted version of the validated `market_report bull_keyword_count` finding (already known)
- `news_report bull_bigram_count` — interesting: news prose with high bull-bigram density shows weak negative within-ticker IC (-0.269, 7/9 tickers negative)
- `investment_plan bear_bigram_count` — bear-bigram density in synthesis prose shows weak negative within-ticker IC (-0.262, 7/9 negative)

The marginals all share the same direction (negative within-ticker IC) and similar magnitude (~-0.27). Three explanations:

1. **Independent confirmation of the recency-mean-reversion mechanism across analyst stages** — both bigram features encode high-conviction language densities that may be analyst-stage-specific manifestations of the same underlying mechanism documented in `claudedocs/finding4-mechanism-2026-05-05.md`
2. **Correlation between analyst-stage prose** — when one analyst writes high bull/bear density, others tend to also write high density (correlated regime detection); the marginal IC could be inheriting the validated `market_report` signal via correlated prose densities
3. **Type-S error from multiple comparisons** — failing Bonferroni means we can't rule out false-positive at the corpus level

Without an N≥30 fresh-data test these remain candidates. None warrant standalone publishable status; all three should be noted as "weak directional support for finding #4's mechanism extending across analyst stages" rather than as separate findings.

### Implications for spec 003

1. **The single real within-ticker predictor in the corpus remains `market_report bull_keyword_count`.** Spec 003's choice of this as the default `contrarian_gate_signal` + `contrarian_gate_feature` is correct — no alternative emerged that would warrant changing the default.
2. **Spec 003 User Story 4 (pluggable source) gains less value than initially hoped.** The artifact check on the 8 candidates didn't surface a second strong within-ticker predictor. The pluggable mechanism is still useful (cheap option to test future featurizers), but no immediate alternative is queued.
3. **The `news_report bull_bigram_count` and `investment_plan bear_bigram_count` marginals could motivate a composite-source signal in a future spec.** If both showed the same direction in fresh data (the SC-002 experiment would generate this evidence), a multi-source gate (mean of percentiles across signals) might be more robust than single-source. Currently OUT OF SCOPE for spec 003 per the spec text.

### Methodology contribution

The within-ticker permutation methodology (shuffle α independently within each ticker, preserve between-ticker structure) discriminates real within-ticker signals from Simpson's-paradox artifacts cleanly across this corpus:
- **Real signal**: p < 2e-4 (`market_report bull_keyword_count` only)
- **Marginal signals**: p in [0.005, 0.025] (3 candidates)
- **Non-predictors**: p > 0.3 across the board (5+ candidates including the entire sentiment_score family)

This three-band stratification is a cleaner taxonomy than the original eval report's single aggregate IC column. The within-ticker IC + permutation pair should be the standard methodology for evaluating any candidate within-ticker featurizer in this corpus.

### What this does NOT change

- Finding #4's headline (within-ticker IC -0.489, 8/8 unanimous direction across non-degenerate tickers) still stands.
- Negative-result finding (most featurization-based aggregator candidates carry between-ticker information, not within-ticker) is reinforced — 5 of 8 new candidates produced p > 0.3.
- Spec 003 Phase 1 + 2 implementation is unaffected — same default signal + feature.

### Cost

$0 LLM, ~5 min wall-clock (11 candidates × 5000 within-ticker permutations + 5000 bootstraps each), reusing existing cache + featurizers + `within_ticker_artifact_check.py` infrastructure.
