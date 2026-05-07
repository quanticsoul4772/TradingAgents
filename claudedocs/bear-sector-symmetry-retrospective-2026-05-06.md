# Spec 006 bear-sector-symmetry retrospective — 2026-05-06

**Spec**: `specs/005-bear-sector-symmetry/`
**Holding window**: 21 trading days
**Ticker + ETF lookback**: 30 trading days
**Corpus**: 45 unique bearish commits → 36 with sector + ETF + α data

## Baseline (no filter): n=36, mean α = +12.69%

Note: for bearish commits, HIGHER baseline α means the collective bear call was wrong (the ticker rallied after the bear commit). The filter aims to suppress those commits to Hold. Net Δα = baseline − kept; positive means the filter is correctly removing high-α bearish commits.

## Threshold sweep

| threshold | n_kept | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|
| +3.0% | 22 | 14 | +14.10% | +10.46% | -1.42pp |
| +5.0% | 25 | 11 | +13.40% | +11.06% | -0.71pp |
| +7.5% | 26 | 10 | +12.82% | +12.34% | -0.13pp |
| +10.0% | 29 | 7 | +11.39% | +18.06% | +1.30pp |

## Per-sector breakdown at threshold +5.0%

| Sector | ETF | n_total | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|---|
| Communication Services | XLC | 1 | 0 | +9.68% | +nan% | +0.00pp |
| Energy | XLE | 1 | 0 | -12.97% | +nan% | +0.00pp |
| Industrials | XLI | 1 | 0 | -18.23% | +nan% | +0.00pp |
| Technology | XLK | 33 | 11 | +16.21% | +11.06% | -1.71pp |

## SC-008 cross-tab against `ticker_strong`-bearish cohort

At threshold +5.0%: **5 of 18** `ticker_strong`-bearish cohort commits would be suppressed.

SC-008 gate: ≥8 of 18 fire at +5.0% → **FAIL**

Cohort is loaded from `claudedocs/sector-alpha-attribution-2026-05-06.csv` filtered to `rating in (Underweight, Sell) AND cell == 'ticker_strong'`.

## Verdict — KEEP default-off; SC-008 FAILS at +5%

**The data does NOT support a default-on flip at the +5% threshold.** Two independent failures:

1. **SC-008 cohort gate fails**: only 5 of 18 ticker_strong-bearish commits fire at +5% (target was ≥8). The spec's motivating premise — "ticker-vs-sector relative-strength was empirically >5% in the prior 30 trading days for ≥8 of 18 cohort dates" — does NOT hold for ≥10 of the cohort dates. The +28.02%-mean-α `ticker_strong` cohort is real (validated by today's sector-α attribution) but the filter mechanism doesn't reliably catch it at the prior-30-day lookback + +5% threshold combination.

2. **Net Δα is NEGATIVE at +5%**: kept_α = +13.40% vs baseline_α = +12.69% → net Δα = **-0.71pp**. The filter at +5% is anti-predictive on the corpus — it's preferentially removing the LESS-wrong bearish commits (fired_α = +11.06% vs kept_α = +13.40%), so the kept bucket is HIGHER α (more wrong) after suppression. Same anti-predictive pattern as spec 004's retrospective at -5%.

## Threshold sensitivity — only +10% is net-positive

| threshold | n_fired | net Δα |
|---|---|---|
| +3.0% | 14 | -1.42pp (anti-predictive) |
| +5.0% (default) | 11 | **-0.71pp (anti-predictive)** |
| +7.5% | 10 | -0.13pp (~zero) |
| +10.0% | 7 | **+1.30pp (positive)** |

The +10% threshold becomes net-positive (n=7 fires with mean α +18.06% vs baseline +12.69%), but only marginally and on small sample. **Tightening to +10% might be justifiable as an operator-opt-in tool** for tech-rally regimes specifically (per-sector: only Technology has fires; XLK 11 of 33 at +5%), but not as a default. The +10% threshold also fails the SC-008 cohort gate (would suppress ≤7 of 18).

## Operational recommendation — three options

1. **Keep default-off** (recommended). Filter ships as operator-opt-in; documented as not validated at any threshold for default-on. Mirrors spec 004's outcome.
2. **Tighten default to +10%** (operator-opt-in path). Net Δα = +1.30pp on n=7 fires; tech-only in current corpus. Requires explicit operator decision per Constitution II ablation discipline; SC-008 cohort gate still fails.
3. **Investigate longer lookback** (60d / 90d). The +28%-mean-α cohort showed huge realized α; the buildup may be visible in longer windows. Out-of-scope for this spec; could be a follow-up retrospective with `--lookback-days 60`.

## Why the cohort isn't caught at +5%

The 18 ticker_strong-bear cohort had mean α-vs-SPY = +28.02% over 21 trading days FORWARD. But the filter looks BACKWARD at the prior-30-day relative-strength. Possible explanations:

- The cohort's outsized rally happened intra-window after the trade date (not pre-buildup). The filter has no way to know this at signal-generation time.
- Many cohort tickers were drifting sideways or modestly up vs sector before the bear commit; the +28% rally was driven by news/catalysts post-commit. Lookback features can't catch forward-only catalysts.
- Per-sector concentration in Technology means the filter mostly fires on XLK (11 of 11 fires at +5%). The non-Tech cohort entries don't show enough relative-strength buildup at any tested threshold.

This is the same lesson as the spec 004 SC-008 validation: backward-looking price filters miss cohorts whose realized α comes from forward catalysts the filter doesn't see.

## What this changes

- **Spec 006 stays default-off.** The implementation is correct + tested + the retrospective is documented; the empirical case for default-on at +5% does not hold.
- **Constitution II discipline validated again.** This is the third filter (after spec 004 and spec 003.5) where the retrospective gate empirically rejected an obvious default. The discipline is doing exactly what it's designed for.
- **Bear-side anti-calibration is REAL but not captured by relative-strength.** The +12.69% baseline α on n=36 bearish commits confirms the broader bear-side anti-calibration finding, but a different signal would be needed to reliably suppress the wrong-direction bear commits — possibly news-driven, options-implied-volatility, or an LLM-extracted "the bull case was already priced in" feature.

**Empirical context**: today's sector-α attribution analysis
(`claudedocs/sector-alpha-attribution-2026-05-06.md`) found 18 of 37 bearish
commits (48.6%) landed in `ticker_strong` with mean α-vs-SPY = +28.02% — a
cohort A3 misses entirely. Spec 006 was built to catch that cohort but the
backward-looking price-only signal is insufficient.

## Reproducibility

```
python scripts/bear_sector_symmetry_retrospective.py
```

Reads from `experiments/*/results.csv` + spec 002 sectors cache + yfinance ticker
+ ETF prices. Cross-tab uses `claudedocs/sector-alpha-attribution-2026-05-06.csv`
if available. No LLM cost. Deterministic given a fixed corpus + threshold list.
