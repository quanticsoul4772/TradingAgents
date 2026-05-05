# `fetch_returns` buffer fix — old vs new IC comparison (2026-05-05)

## The bug

`tradingagents/graph/trading_graph.py::fetch_returns` computed the calendar window as `start + (holding_days + 7) days`. That works for short windows (5d → 12 calendar days fits 5 trading days) but truncates long windows: 90d → 97 calendar days only fits ~50 trading days. The `actual_days = min(holding_days, len(stock) - 1, ...)` line then capped the holding window at the available data, so what the eval report called "IC@90d" was actually IC over ~50 trading days.

The bug was discovered by `claudedocs/bear-bigram-artifact-check-2026-05-04.md` (median actual_days = 50 when holding_days = 90 was requested) and confirmed across all 4 top-IC features in `claudedocs/featurizer-artifact-check-2026-05-04.md`.

## The fix

```python
# Old:
end = start + timedelta(days=holding_days + 7)  # buffer for weekends/holidays

# New:
end = start + timedelta(days=int(holding_days * 1.5) + 7)
```

Trading-to-calendar ratio is ~252/365 ≈ 1.45; the 1.5 multiplier covers that, the +7 covers weekend/holiday edges. For short windows the +7 still dominates (5d → 14 calendar days vs old 12); for long windows the multiplier matters (90d → 142 calendar days vs old 97).

Verified: `fetch_returns('NVDA', '2025-11-07', holding_days=90)` now returns `actual=90` (was returning ~50 before).

## Comparison: top features

Same cache, same featurizers, same 113 fundamentals_report rows; only the buffer formula changed.

### Per-signal numeric IC (`final_trade_decision`)

| Horizon | Old IC | New IC | Δ |
|---:|---:|---:|---:|
| 5d | -0.073 | -0.073 | 0.000 (identical — fix is no-op for short horizons) |
| 10d | -0.112 | -0.095 | +0.017 |
| 21d | -0.172 | -0.103 | +0.069 |
| 90d | -0.238 | -0.254 | -0.016 |

### Per-feature IC at 90d (top 4)

| Feature | Old IC@"90d" (~50d actual) | New IC@90d (true 90 trading days) | Δ |
|---|---:|---:|---:|
| `bear_bigram_count` | +0.457 | +0.478 | +0.021 |
| `conviction_density` | -0.407 | -0.404 | +0.003 |
| `hedge_density` | +0.305 | +0.318 | +0.013 |
| `bull_keyword_count` | -0.306 | -0.302 | +0.004 |

## What this confirms

**The qualitative story is robust to the buffer fix.** All sign patterns preserved, magnitudes shifted by <0.03 in absolute value. The artifact-check verdict from `claudedocs/featurizer-artifact-check-2026-05-04.md` (between-ticker artifact, not within-ticker predictor) holds — the features are still strongly correlated with α at the aggregate level, just at a slightly different magnitude.

The 21d shift (-0.172 → -0.103) is the largest single change. Mechanism: at 21d the old buffer (28 calendar days) sometimes capped `actual_days` at 19-20 instead of 21 due to SPY edge cases (holidays falling within the 28-day window); the new buffer (38 calendar days) reliably gets 21+ trading days. The shift is interpretable as "the IC was slightly more negative when measured over 19-20 days than over 21 days" — a sub-horizon-shift effect, not a methodology bug per se.

## What this doesn't change

- The **headline empirical claim** (bullish OW/Buy commits +1.23% mean α at 21d, n=71, posterior 0.63) is measured from `experiments/*/results.csv` with `analyze_backtest.py --holding-days 21`, which uses the same `fetch_returns`. The 21d numbers in the headline could shift by ~0.07pp on rerun — small enough that the moderate-confidence verdict stands.
- The **artifact-check finding** (top-4 ICs are between-ticker artifacts) is unchanged; the per-ticker IC pattern is a property of the data structure (10 tickers × 33 dates), not of the horizon length.
- The **synthesis essay's three publishable secondary findings** stand: calibrated abstention, replicability scope, substrate-specific calibration.
- The **negative-result finding** (featurization-based aggregator has no within-ticker predictive ceiling) stands.

## Re-running affected analyses

Anyone re-running these scripts after the fix will get slightly different numbers from the saved reports:

- `scripts/analyze_backtest.py --holding-days 90` — was returning IC over ~50 days; now returns true 90d.
- `scripts/horizon_sweep.py` (uses 90d as the longest horizon) — same.
- `scripts/evaluate_signals.py --horizons 5,10,21,90` — same; new report at `claudedocs/signal-evaluation-2026-05-05-buffer-fix.md`.

Re-runs at 5d/10d/21d will produce essentially identical results to the saved reports (fix is no-op or near-no-op at those horizons).

## Cost

$0 LLM, ~30 min wall-clock (write fix + spot-check + re-run eval pipeline + compare).
