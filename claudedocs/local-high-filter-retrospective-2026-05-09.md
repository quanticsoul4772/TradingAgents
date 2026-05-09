# Per-ticker local-high BULL-side filter retrospective — 2026-05-09

**Trigger**: reasoning_decision rank-3PP (0.715). Tests the structural hypothesis identified in PR #203 Class 4 BULL SKIP analysis: "Per-ticker mean-reversion at local highs could be tested via a NEW Class N filter (price-vs-rolling-high)."

**Mechanism class**: per-ticker price-vs-30d-rolling-high. **NEW class** — distinct from A3 (per-ticker absolute mean-reversion via 30d-return) which uses 30d return; this uses 30d-rolling-MAX-distance. Shipping this would make the framework's 11th filter side.

**Cost**: $0 LLM (yfinance + arithmetic).

**Script**: `scripts/local_high_filter_retrospective.py` (NEW; ships with this PR).

## Cohort

Bull commits enumerated from `experiments/*/results.csv`: **86 bull commits**. With valid forward + sector + price data: **82 commits**. ticker_weak cohort: **27 commits** (mean α-vs-SPY = **-5.34%**; per `claudedocs/sector-alpha-attribution-2026-05-09.md`).

## Proximity-to-30d-high signature comparison

| Cell | n | mean prox % | n_below_-2% | n_below_-5% |
|---|---:|---:|---:|---:|
| `ticker_strong` (winners) | 29 | -8.19% | 27 | 20 |
| `sector_tide_up` (mixed) | 20 | -9.07% | 20 | 18 |
| `sector_drag` (mixed) | 6 | -5.62% | 6 | 3 |
| **`ticker_weak`** (5th-failure-mode) | **27** | **-5.75%** | **23** | **13** |

**Observation (counterintuitive)**: ticker_weak cohort committed at price LESS-far-below-30d-high (-5.75%) than ticker_strong (-8.19%) — i.e., ticker_weak commits ARE structurally closer to local highs. Mechanism hypothesis has SOME directional support.

**BUT**: cohort overlap is high. 13 of 27 ticker_weak (48%) had price already > 5% below high — these are NOT at local high but still failed. The discriminator is too noisy.

## Threshold sweep

Fire = SUPPRESS bull when `proximity > threshold` (price closer to high than threshold).

| Threshold | Fires | Cohort caught | FP | Net Δα/n | Cohort hit % |
|---:|---:|---:|---:|---:|---:|
| > -0.5% | 0 | 0/27 | 0 | n/a | n/a |
| > -1.0% | 2 | 2/27 | 0 | **+6.39pp** | **100%** |
| > -2.0% | 6 | 4/27 | 2 | **-7.09pp** | 67% |
| > -3.0% | 11 | 8/27 | 3 | -1.89pp | 73% |
| > -5.0% | 28 | 14/27 | 14 | -0.12pp | 50% |
| > -8.0% | 48 | 20/27 | 28 | -0.84pp | 42% |

## Constitution VIII gate evaluation — POTENTIAL PASS at sample-size floor

**Standalone gate (v1.4.0)**: net Δα ≥ +0.5pp AND cohort hit ≥ 40%

| Threshold | Δα | hit | Standalone PASS? |
|---|---:|---:|---|
| > -1.0% | +6.39pp | 100% | **TECHNICAL PASS** (n=2 — at sample-size floor) |
| > -2.0% | -7.09pp | 67% | FAIL (Δα < 0) |
| > -3.0% | -1.89pp | 73% | FAIL (Δα < 0) |
| > -5.0% | -0.12pp | 50% | FAIL (Δα ≈ 0) |
| > -8.0% | -0.84pp | 42% | FAIL (Δα < 0) |

**Verdict**: the mechanism shows PASS at the very narrow threshold (price within 1% of 30d high; n=2 fires in cohort; both correctly suppressed). At broader thresholds, the false-positive rate dominates and net Δα turns negative.

**Per Constitution VIII v1.4.0 small-sample-caution sub-clause**: n=2 is BELOW the conventional sample-size floor (Spec 012 launched at n=8 with shadow-mode-first; Spec X-1 at n=12 with shadow-mode-first; both already at the lower bound of statistical confidence).

## Recommendation: DEFER spec drafting; ship script + memo for corpus growth

The +6.39pp / 100% hit at threshold > -1% is real-but-thin evidence. Two options:

1. **DEFER**: ship the retrospective script + memo + revisit when corpus grows to 100+ bull commits (would yield ~5+ fires at threshold > -1%; n≥5 is the standard small-sample floor for v1.4.0)

2. **SHIP at default-SHADOW with very narrow threshold**: deploy as Spec 013 with `local_high_bull_threshold = -1.0%` default-shadow; let live shadow-mode fires accumulate; SC-010-style audit when n≥30 fires. But: at n=2 evidence base, even shadow-mode is over-confident.

**Recommended path: DEFER (option 1)**. Per the rank-driven shipping discipline + Constitution VIII v1.4.1 retrospective-first methodology, when standalone gate technically PASSES but only at sample-size floor, the right move is corpus growth before spec drafting. The script ships as durable tooling; the memo documents the finding + future re-evaluation criteria.

This keeps the framework at 10 production filter sides (post-Spec 012). An 11th filter waits on stronger empirical evidence than n=2 fires.

## What this DOES rule in for the future

- **The local-high mechanism is empirically valid** at narrow thresholds — it's not refuted, just sample-size-limited
- **Future re-evaluation triggers**:
  - Bull-cohort growth to 150+ commits (would yield n≥5 fires at threshold > -1%; meets v1.4.0 floor)
  - A modified mechanism (e.g., proximity to 60d high, or proximity-AND-bull_keyword_count combined) might reduce the FP rate at broader thresholds
  - A different measurement (e.g., distance to highest analyst PT instead of historical price high) might better separate ticker_weak from ticker_strong cohorts

## What this rules OUT

- **Broad-threshold local-high suppression FAILS** at every tested threshold beyond > -1.0%. The 27-row ticker_weak cohort cannot be cleanly separated from ticker_strong + sector_tide_up cohorts at proximity > -2% to > -8% range.
- **The "stock-specific mean-reversion at local highs" hypothesis is partially refuted** at corpus n=82: ticker_weak commits AT local high (within 1%) tend to fail (n=2/2), but ticker_weak commits NEAR local high (-2% to -5% from high) include many false-positives (winners in same threshold band).

## Constitution adherence

- ✅ I (Save Everything): this retrospective markdown + reproducible script
- ✅ III (Stay Cheap): $0 LLM
- ✅ IV (No Production Claims): DEFER verdict; no production deployment
- ✅ VIII v1.4.0: standalone gate evaluated at every threshold; PASS only at sample-size floor; DEFER per small-sample-caution
- ✅ VIII v1.4.1: retrospective ships before any spec drafting; SKIP (defer)-spec discipline preserved

## Cross-references

- `claudedocs/sector-alpha-attribution-2026-05-09.md` (PR #204 — refreshed cohort numbers)
- `claudedocs/class4-macro-bull-retrospective-2026-05-09.md` (PR #203 — bull-side macro SKIP that identified per-ticker-local-high as the structurally-correct response)
- `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193 — bear-side Class 4 PASS; sister methodology)
- `tradingagents/agents/utils/momentum_filter.py` (A3 — per-ticker absolute mean-reversion; closest existing filter)
- Constitution VIII v1.4.0 + v1.4.1
- Memory: `feedback_retrospective_first_pattern.md` (Constitution VIII v1.4.1 SKIP-saves-spec-cost discipline)
