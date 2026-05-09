# WC-10 v2 ticker expansion — ANALYSIS template

> **STATUS**: TEMPLATE awaiting data. Background pilot in flight (~12h ETA from 2026-05-08 evening kickoff). Replace `<TODO>` placeholders + numerical TBDs with computed values once `results.csv` reaches 80 rows. Then move/rename this file to `ANALYSIS.md`.

**Experiment ID**: `2026-05-08-002-wc-10-v2-ticker-expansion`
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/`
**Run date**: 2026-05-08 → <TODO completion timestamp>
**Total LLM cost**: ~$32 (80 propagates × ~$0.40)
**Predecessor**: `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1, n=20 paired)

## Headline verdict (TBD post-data)

The SC-005(b) signed-rating × 21d-α correlation at n=100 (combining v1+v2 WC-10 cohorts) resolved to **<STRONG | MODERATE | NULL>**:

- `|r| > 0.30` → STRONG: scalar magnitude meaningfully predicts α magnitude beyond binary commit/abstain
- `0.197 < |r| < 0.30` → MODERATE: statistically detectable but small effect
- `|r| < 0.197` → NULL: scalar carries no information beyond what the bin captures

ALT-A (categorical bottleneck) at distribution level: **<CONFIRMED ON N TICKERS / GENERALIZES / TICKER-SPECIFIC>** (n_tickers with `commit_rate ≥ 80%` was X of 8).

## SC-005(b) — signed-rating × 21d-α correlation (PRIMARY)

Pooled across all 100 WC-10 propagates (20 from v1 + 80 from v2):

| Statistic | Value | Critical (p=0.05) | Verdict |
|---|---|---|---|
| Pearson r | <TBD> | ±0.197 | <SIG / NS> |
| Spearman ρ | <TBD> | ±0.197 | <SIG / NS> |

Per-ticker correlation (within-ticker IC over n=10-20 each):

| Ticker | n | Pearson r | Mean WC-10 rating | Mean 21d α |
|---|---:|---:|---:|---:|
| NVDA | <TBD> | <TBD> | <TBD> | <TBD> |
| AAPL | <TBD> | <TBD> | <TBD> | <TBD> |
| MSFT | <TBD> | <TBD> | <TBD> | <TBD> |
| GOOG | <TBD> | <TBD> | <TBD> | <TBD> |
| AMZN | <TBD> | <TBD> | <TBD> | <TBD> |
| JPM | <TBD> | <TBD> | <TBD> | <TBD> |
| JNJ | <TBD> | <TBD> | <TBD> | <TBD> |
| XOM | <TBD> | <TBD> | <TBD> | <TBD> |

## SC-007 ALT-A generalization across tickers (SECONDARY)

Per-ticker fraction of `|rating| > 0.2` (committed):

| Ticker | n | Committed | % | Buy/OW | UW/Sell | Hold-bin |
|---|---:|---:|---:|---:|---:|---:|
| NVDA | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| AAPL | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| MSFT | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| GOOG | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| AMZN | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| JPM | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| JNJ | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| XOM | <TBD> | <TBD> | <TBD>% | <TBD> | <TBD> | <TBD> |
| **Total** | **80** | **<TBD>** | **<TBD>%** | <TBD> | <TBD> | <TBD> |

ALT-A predicts ≥ 80% commit rate per ticker, matching v1's NVDA pattern. Counter-finding: any ticker that collapses to Hold even under continuous-scalar mode would suggest the schema bottleneck is partially ticker-specific (or cohort-specific to NVDA/AAPL volatility profiles).

## SC-005(c) — per-bucket realized α generalization (TERTIARY)

Compares v2's per-bucket means to v1 (the v1 NVDA Buy +4.67% finding was the most architecturally consequential WC-10 result):

| Bucket | v1 n | v1 mean α | v2 n | v2 mean α | Δ |
|---|---:|---:|---:|---:|---:|
| Buy | 6 | +4.67% | <TBD> | <TBD> | <TBD> |
| Overweight | 6 | +2.34% | <TBD> | <TBD> | <TBD> |
| Hold | 2 | +4.29% | <TBD> | <TBD> | <TBD> |
| Underweight | 6 | +3.56% | <TBD> | <TBD> | <TBD> |
| Sell | 0 | — | <TBD> | <TBD> | <TBD> |

If v2 Buy mean α stays positive and broad-magnitude (≥+2%) across the new 6 tickers, the bullish-side amplification finding generalizes. If v2 Buy α collapses to near zero on the new tickers, the v1 finding was NVDA-specific.

## Combined v1+v2 full breakdown (n=100)

| Metric | v1 (n=20) | v2 (n=80) | Combined (n=100) |
|---|---:|---:|---:|
| Commit rate (`\|rating\|>0.2`) | 90% | <TBD> | <TBD> |
| Mean rating | <TBD> | <TBD> | <TBD> |
| Std rating | <TBD> | <TBD> | <TBD> |
| Mean 21d α | <TBD> | <TBD> | <TBD> |
| Pearson r (rating × α) | +0.065 | <TBD> | <TBD> |

## Cohort + period notes

v2 dates span Q1 2026 (2026-01-30 → 2026-04-03), v1 dates span April 2026 (2026-04-01 → 2026-04-30). Date overlap: 2026-04-01 + 2026-04-02 (NVDA + AAPL only). Combined cohort therefore spans Q1 2026 (broad Tech rally) into early Q2 2026; per Constitution VII v1.5.0 + cross-period scope, the realized-α property is **period-conditional**.

## Constitution v1.5.0 implication update (TBD)

If v2 confirms ALT-A on the broader ticker base, the v1.5.0 amendment's "schema-induced abstention" carve-out generalizes beyond NVDA/AAPL. If v2 shows a subset of tickers retaining Hold-collapse under continuous-scalar mode, those tickers fall back into the original VII (genuine-balance) sub-population — and we have empirical heuristics for distinguishing the two.

## Constitution adherence checklist

- ✅ I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / wc10_pilot_memory.md isolated to v2 dir
- ✅ II (One Experiment Per Change): same intervention as v1 (continuous-scalar schema). v2 is SCALE expansion only.
- ⚠️ III (Stay Cheap): T2-boundary at $32; explicit deliberation in HYPOTHESIS.md per principle's escape hatch
- ✅ IV (No Production Claims): bullish-amplification generalization is the data; production-readiness call deferred
- ✅ VI (Spec Before Structural Change): per spec bundle 108
- <TBD VII> (Calibrated Abstention v1.5.0): result feeds back into the carve-out's empirical scope

## Next steps (for operator decision; populate after data lands)

<TBD per verdict — possibilities include:>

1. If SC-005(b) STRONG (`|r| > 0.30`) → push WC-10 toward operator-opt-in production via daily_signals.py integration spec
2. If SC-005(b) MODERATE (`0.197 < |r| < 0.30`) → keep WC-10 as research mode; consider v3 expansion to n=200 for narrower CIs
3. If SC-005(b) NULL (`|r| < 0.197`) → bin-then-output pattern (continuous internal, 5-tier external) for the ergonomic gain without false-precision claim
4. If ALT-A generalizes → memory + RESEARCH_FINDINGS update reframing mode collapse as predominantly schema-driven
5. If ALT-A is NVDA/AAPL-specific → carve out a "tickers where WC-10 helps" heuristic; original VII applies elsewhere
