# Spec 005 (proposed) retrospective — 2026-05-06

**Hypothesis under test**: backward-looking rolling-ticker-vs-sector signal can
identify the n=27 bullish ticker_weak cohort BEFORE spec-writing. Mirrors spec 006's
mechanism (threshold on rel-strength delta) but BULL side. Today's spec 006
retrospective failed; this retrospective tests whether the bull-side analog also
fails before any implementation work is done.

**Lookback**: 30 trading days
**Corpus**: 79 bullish commits with full data (from `claudedocs\sector-alpha-attribution-2026-05-06.csv`)
**Baseline (no filter)**: n=79, mean α vs SPY = +1.52%

## Rel-strength distribution

| stat | value |
|---|---|
| count | 79 |
| mean | -0.12% |
| std | 5.62% |
| min | -13.30% |
| p25 | -3.38% |
| p50 | -0.39% |
| p75 | +3.26% |
| p90 | +7.65% |
| p95 | +9.24% |
| max | +14.36% |

## Mechanism A — Absolute threshold sweep

Fire when `rel_strength_pct > threshold`. Net Δα = kept_α − baseline_α; positive
means the filter helps by removing losers.

| threshold | n_kept | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|
| +3.0% | 57 | 22 | +1.75% | +0.92% | +0.23pp |
| +5.0% | 66 | 13 | +1.70% | +0.59% | +0.18pp |
| +7.5% | 71 | 8 | +1.24% | +3.99% | -0.28pp |
| +10.0% | 76 | 3 | +1.83% | -6.31% | +0.31pp |

## Mechanism B — Percentile-based sweep

Fire when `rel_strength_pct > Nth percentile of bullish-corpus distribution`.
More noise-robust than absolute threshold (per-corpus normalized).

| percentile | cutoff | n_kept | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|---|
| p70 | +2.54% | 56 | 23 | +1.43% | +1.72% | -0.08pp |
| p80 | +3.97% | 63 | 16 | +1.75% | +0.60% | +0.23pp |
| p90 | +7.65% | 71 | 8 | +1.24% | +3.99% | -0.28pp |

## Per-sector breakdown at threshold +5.0%

| Sector | ETF | n_total | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|---|
| Communication Services | XLC | 5 | 0 | +9.28% | +nan% | +0.00pp |
| Consumer Cyclical | XLY | 1 | 1 | +nan% | +18.71% | +0.00pp |
| Energy | XLE | 1 | 1 | +nan% | -16.16% | +0.00pp |
| Financial Services | XLF | 9 | 0 | -3.84% | +nan% | +0.00pp |
| Healthcare | XLV | 2 | 0 | +8.16% | +nan% | +0.00pp |
| Technology | XLK | 61 | 11 | +1.68% | +0.47% | +0.22pp |

## Cross-tab: bullish `ticker_weak` cohort (n=27; the spec 005 target)

From today's sector-α attribution: bullish commits with α<0 vs SPY AND vs sector.
The spec 005 hypothesis predicts these losers were at sector-relative highs at
signal time → backward-looking rel-strength would catch them.

| cut | suppressed | hit rate of cohort | mean α of suppressed |
|---|---|---|---|
| +3.0% (abs) | 13 | 48.1% | -5.33% |
| +5.0% (abs) | 10 | 37.0% | -6.35% |
| +7.5% (abs) | 5 | 18.5% | -7.85% |
| +10.0% (abs) | 3 | 11.1% | -6.31% |
| p70 (+2.54%) | 13 | 48.1% | -5.33% |
| p80 (+3.97%) | 12 | 44.4% | -5.75% |
| p90 (+7.65%) | 5 | 18.5% | -7.85% |

## Verdict — SKIP spec 005; mechanism is partial-signal / high-noise

**Decision: do NOT write spec 005 as the absolute-threshold bull-side mechanism.** The retrospective shows split criteria — partial cohort discrimination but insufficient net Δα.

### Criterion 1 (net Δα ≥ +1pp): FAIL at every cut

| Cut | Net Δα |
|---|---|
| +3.0% | +0.23pp |
| +5.0% | +0.18pp |
| +7.5% | -0.28pp |
| +10.0% | +0.31pp |
| p70 | -0.08pp |
| p80 | +0.23pp |
| p90 | -0.28pp |

Max net Δα is +0.31pp at +10% threshold, well below the +1pp gate. The mechanism is too noisy to meaningfully improve the bullish bucket at any tested cut.

### Criterion 2 (cohort hit rate ≥ 40%): PASS at +3% / p70 / p80 only

The +3% absolute threshold + p70 percentile both catch 13 of 27 ticker_weak commits (48.1% hit rate). The suppressed cohort had mean α = **-5.33%** — real losers, not noise. So the signal CAN identify the failure-mode cohort, but at low specificity.

### Why the cohort hit rate doesn't translate to net Δα

Math: at +3% threshold, 22 commits fire total. 13 are ticker_weak (mean α = -5.33% → -69pp total). The OTHER **9 fired commits** are non-cohort (ticker_strong / sector_tide_up / sector_drag). Their fired_mean must be: (22 × +0.92%) − (13 × −5.33%) ≈ +89pp / 9 ≈ **+9.9% mean** — these are WINNERS that the filter incorrectly suppresses.

So the signal washes: cohort-loser suppression (good) is roughly cancelled by winner suppression (bad). The mechanism cannot DISCRIMINATE between losers and winners that share the same backward-looking pattern.

### Comparison to spec 006 retrospective

| Aspect | Spec 006 (bear) | Spec 005 candidate (bull) |
|---|---|---|
| Default-threshold net Δα | -0.71pp (anti-predictive) | +0.18pp (~zero) |
| Cohort hit rate at default | 27.8% (5/18) | 37.0% (10/27) |
| Maximum net Δα across cuts | +1.30pp at +10% (n=7) | +0.31pp at +10% (n=3) |
| Verdict | Default-off; ship as opt-in | SKIP spec entirely |

The bull-side mechanism is *less anti-predictive* than the bear-side, but the signal-to-noise ratio is also too weak to support a spec. Sector-relative ticker mean reversion exists in the corpus (per the cohort hit rates) but co-occurs with winner-momentum patterns at indistinguishable rel-strength values.

### Implication — Constitution VIII candidate

This is the **third backward-looking price filter** today (spec 004 absolute sector momentum, spec 006 bear sector-relative, spec 005 candidate bull sector-relative) that the retrospective gate has empirically rejected. The pattern across all three:

- Mechanism is intuitive and fits the failure-mode taxonomy
- Implementation is mechanical
- Empirical retrospective shows either anti-predictive (spec 004, spec 006) or signal-to-noise too weak for default-on (spec 005)

**Tentative Constitution amendment** (proposed Principle VIII or extension to Principle II):

> **Backward-looking price-derived filters require a corpus retrospective showing
> net Δα ≥ +1pp AT THE PROPOSED DEFAULT THRESHOLD before any spec is written.**
> The retrospective is `$0` LLM cost (offline replay) and runs in ~1h; the spec
> + implementation + tests cost ~6-8h of work. Today's three filter retrospectives
> show the cost asymmetry is severe enough that the retrospective gate must come
> FIRST. Spec-after-passing-retrospective remains the workflow.

Captured for follow-up; would land in a separate constitution amendment commit if accepted.

### What this DOES validate

- The 5th failure mode IS real (n=27 ticker_weak commits at -5.34% mean α; the cohort exists per today's sector-α attribution).
- Backward-looking rel-strength catches ~half the cohort — so the cohort isn't entirely catalyst-driven; some of it has prior-window signature.
- A more sophisticated mechanism (multi-factor, news-density, options-IV, prose features) might successfully discriminate cohort losers from similar-pattern winners. The price-only signal does not.

### What this DOES NOT change

- Spec 003's prose-density gate (fundamentally different mechanism class — within-ticker debate text density, not price)
- A3's per-ticker absolute mean-reversion (in-sample validated; orthogonal to sector-relative)
- The decision to ship spec 004 + spec 006 as default-off operator-opt-in tools (their retrospectives also failed but the implementations are correct + documented)

### Operational outcome

- **Skip writing spec 005** in the absolute-threshold form.
- **Defer the percentile-based per-ticker-history form** until either (a) corpus expansion provides 30+ history per ticker for percentile robustness, OR (b) a different signal class (forward-looking news / fundamental / LLM-extracted feature) shows promise on the same cohort.
- **Document the lesson**: today's retrospective methodology can cheaply ($0, ~1h) save 6-8h of implementation work on backward-looking-price-only mechanisms.

## Reproducibility

```
python scripts/ticker_sector_alpha_retrospective.py
```

Reads `claudedocs/sector-alpha-attribution-2026-05-06.csv` for forward α + cell;
fetches yfinance ticker + ETF prices for backward rel-strength; uses spec 002
sectors cache. No LLM cost. Deterministic given a fixed corpus + threshold list.
