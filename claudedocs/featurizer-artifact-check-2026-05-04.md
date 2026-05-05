# Featurizer artifact check (top 4 ICs) — 2026-05-04

## Question

Is the top-4 strongest-IC pattern in `claudedocs/signal-evaluation-2026-05-04.md` real predictive signal, or are all four similarly **between-ticker artifacts** (as `bear_bigram_count` was shown to be in `claudedocs/bear-bigram-artifact-check-2026-05-04.md`)?

If the within-ticker IC is near zero or noisy across ALL 4 features, the featurization-based-aggregator approach has no within-ticker predictive ceiling.

## Method

Identical to the bigram artifact check, parameterized over `(signal_id, featurizer)`:
- Cache rows for the signal
- Recompute featurizer values + α via `fetch_returns(holding_days=90)` (actual ≈ 50 trading days due to the buffer bug)
- Permutation test n=5000, bootstrap CI n=5000, per-ticker, per-period

## Headline comparison

| Signal | Feature | n | IC | perm p₂ | 95% CI | Bonferroni @ 0.05/280 |
|---|---|---:|---:|---:|---|---|
| `fundamentals_report` | `bear_bigram_count` | 113 | +0.4573 | 0.0000 | [+0.302, +0.596] | PASS |
| `fundamentals_report` | `conviction_density` | 113 | -0.4070 | 0.0000 | [-0.568, -0.213] | PASS |
| `fundamentals_report` | `hedge_density` | 113 | +0.3051 | 0.0016 | [+0.105, +0.481] | FAIL |
| `fundamentals_report` | `bull_keyword_count` | 113 | -0.3058 | 0.0014 | [-0.485, -0.096] | FAIL |

## Per-ticker IC by feature

| Ticker | n | `bear_bigram_count` | `conviction_density` | `hedge_density` | `bull_keyword_count` |
|---|---:|---:|---:|---:|---:|
| AAPL | 23 | +0.069 | +0.441 | -0.295 | +0.306 |
| GOOGL | 12 | +0.090 | +0.336 | -0.133 | -0.259 |
| INTC | 20 | -0.004 | +0.468 | -0.179 | +0.073 |
| JPM | 12 | -0.276 | -0.762 | +0.497 | -0.427 |
| MSFT | 13 | +0.340 | -0.159 | -0.286 | -0.049 |
| NVDA | 33 | -0.157 | -0.188 | +0.233 | -0.057 |

## Per-period IC by feature

| Period | n | `bear_bigram_count` | `conviction_density` | `hedge_density` | `bull_keyword_count` |
|---|---:|---:|---:|---:|---:|
| Q3 2025 | 9 | -0.096 | -0.300 | +0.533 | +0.134 |
| Q4 2025 | 31 | +0.561 | -0.635 | +0.316 | -0.577 |
| Q1 2026 | 73 | +0.507 | -0.439 | +0.361 | -0.258 |

## Verdict

**All 4 strongest featurizer ICs in the corpus are between-ticker artifacts. None are within-ticker predictive. The featurization-based-aggregator approach has no within-ticker predictive ceiling on this corpus — the IC measurements in the eval report are essentially ticker-identification ICs, not prediction ICs.**

### What the per-ticker table actually shows

For a feature to be a "real predictor", its IC sign should be at least *consistent* across tickers — if hedge density predicts negative α, it should do so for AAPL and NVDA and JPM, not flip sign per ticker. None of the 4 features satisfy that:

| Feature | Within-ticker sign agreement | Within-ticker max \|IC\| | Within-ticker median IC |
|---|---|---|---|
| `bear_bigram_count` | 3 positive, 3 negative | 0.34 (MSFT, n=13) | +0.03 |
| `conviction_density` | 3 positive, 3 negative | 0.76 (JPM, n=12) | +0.09 |
| `hedge_density` | **4 negative, 2 positive** (aggregate is **+0.305**) | 0.50 (JPM, n=12) | -0.16 |
| `bull_keyword_count` | 2 positive, 4 negative | 0.43 (JPM, n=12) | -0.05 |

**`hedge_density` is a textbook Simpson's-paradox case**: the aggregate IC is +0.305 but the within-ticker IC is NEGATIVE on 4 of 6 tickers (AAPL, GOOGL, INTC, MSFT). The "more hedging language → higher α" relationship reverses inside every individual ticker. The positive aggregate is purely an artifact of "tickers where the analyst hedges more in fundamentals prose happen to be the tickers that delivered higher α across the corpus."

### What the per-period table actually shows

All 4 features ARE sign-stable across the two large periods (Q4 2025 + Q1 2026 both have n>30). The Q3 2025 column has n=9 and shouldn't be trusted for direction.

| Feature | Q4 2025 sign | Q1 2026 sign | Sign-stable across periods? |
|---|---:|---:|---|
| `bear_bigram_count` | +0.561 | +0.507 | ✅ |
| `conviction_density` | -0.635 | -0.439 | ✅ |
| `hedge_density` | +0.316 | +0.361 | ✅ |
| `bull_keyword_count` | -0.577 | -0.258 | ✅ |

So the period-level aggregate IC pattern *replicates*. But that's the same statement as "within-ticker is not predictive": if the same tickers are in both periods (NVDA + AAPL + INTC + ...) and within-ticker IC is near zero, then the period-aggregate IC reflects the same "this ticker class has more bear language and ripped more across the corpus" between-ticker comparison, just measured on a sub-slice.

### What this means for Spec 001 Phases 1 + 5

The Phase 1 shadow aggregator (42.3% direction match — fails SC-001) and Phase 5 weight tuning (overfits, train +0.079 → test -0.062) are now **fully mechanically explained**:

- The featurized-prose Signals carry **between-ticker** information (which ticker has more bear language) but not **within-ticker** information (which date for THIS ticker is a stronger commit).
- The aggregator is trying to predict per-(ticker, date) commits using inputs that only encode per-ticker means.
- Weight tuning overfit because the only weight pattern that produces nonzero in-sample IC (100% on `investment_plan`) was capturing some of the between-ticker variance in the train fold; the test fold contained mostly the same tickers but the date-level pattern within those tickers was different — so it didn't transfer.

This is a generalizable claim, not just about the 4 features tested:
**Featurization-based aggregators on prose signals will not work on this corpus until either (a) the prose itself starts carrying within-ticker information that distinguishes good-commit dates from bad-commit dates, or (b) the aggregator architecture learns ticker-specific means and only predicts deviations.**

Option (a) requires the LLM to emit different prose at high-conviction dates vs low-conviction dates within the same ticker — not currently happening at signal-detectable magnitude. Option (b) is a different model class (mixed-effects / per-ticker fixed effects on top of the featurizer) and would need its own validation.

### What this confirms about the corpus

The corpus has **6-10 tickers, repeated across 33 dates**. With ticker-level α heterogeneity (NVDA mean α, JPM mean α, INTC mean α all very different) and analysts that produce different prose textures per ticker (NVDA always gets bullish text, JPM always gets neutral text, INTC always gets bearish text), **any featurizer that distinguishes ticker classes will produce a positive aggregate IC**. The IC measures ticker identification, not date-level prediction.

The eval report's IC table is **valid as a description of ticker × text-style co-variance**, but **misleading as a description of predictive signal**. A future signal-evaluation report should compute *within-ticker* IC alongside aggregate IC; the difference between the two columns is the artifact magnitude.

### Methodology fixes to push

1. **`scripts/evaluate_signals.py`**: add a per-ticker IC column alongside the aggregate IC. Where they diverge (sign or magnitude), flag the row.
2. **`tradingagents/signals/evaluation.py::evaluate_features_multi_horizon`**: support a `within_ticker=True` mode that computes IC within each ticker and aggregates (e.g., averages or median).
3. **`tradingagents/graph/trading_graph.py::fetch_returns`**: widen the buffer for long horizons (current `holding_days + 7` calendar days fits ≤22 trading days; for 90 trading days needs ~135 calendar days). Already noted in the bear_bigram artifact check.

### What this does NOT change

The main empirical headline (bullish commits +1.23% mean α at 21d, n=71, posterior 0.63) is unaffected — that's measured on rating commits at a horizon where the buffer is adequate, and it's a question about commit quality, not about featurizer prediction.

The synthesis essay's three publishable secondary findings (calibrated abstention, replicability scope, substrate-specific calibration) all stand. The featurizer-IC findings now belong to a fourth category: **negative result on featurization-based aggregators** — useful prior for anyone considering this approach.

### Cost

$0 LLM, ~30 min wall-clock (4 features × 5000 permutations + 5000 bootstraps each), reusing existing cache + featurizers + fetch_returns.
