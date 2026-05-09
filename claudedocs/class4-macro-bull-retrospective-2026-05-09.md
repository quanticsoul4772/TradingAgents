# Class 4 (cross-asset/macro) BULL-side filter retrospective — 2026-05-09

**Trigger**: reasoning_decision rank-5DD (0.565). Sister to today's bear-side Class 4 retrospective (PR #193 PASSED). Tests whether macro features (VIX-snapshot threshold) can identify the 27-row bull-side `ticker_weak` cohort (5th-failure-mode; mean α-vs-SPY -5.34% per `claudedocs/sector-alpha-attribution-2026-05-06.md`) BEFORE the framework commits Buy/Overweight.

**Hypothesis**: by symmetric logic to bear-side, bull commits in HIGH VIX (risk-off) environments should be more likely to fail (counter-trend bullish in a fearful market).

**Cost**: $0 LLM (yfinance + arithmetic).

**Script**: `scripts/class4_macro_bull_retrospective.py` (NEW; ships with this PR).

## Cohort

Bull commits enumerated from `experiments/*/results.csv` (Buy + Overweight ratings; non-error rows): **86 bull commits**. With valid forward + sector + macro data: **82 commits**. ticker_weak cohort: **27 commits** (α-vs-SPY < 0 AND α-vs-sector < 0; mean α-vs-SPY = **-5.34%**).

The 27-row bull ticker_weak cohort EXACTLY matches the 2026-05-06 sector-α attribution count — stable cohort across the corpus growth (because new commits since then were all Hold or wc_10-mode, not bull-pre).

## Macro signature comparison (ticker_weak vs other bull cells)

| Metric | ticker_weak (n=27) | Other bull cells (n=55) | Δ |
|---|---:|---:|---:|
| **VIX (snapshot)** | **20.64** | **22.65** | **-2.01** |
| **VIX 30d Δ%** | **+20.41%** | **+26.36%** | **-5.95pp** |

**Headline (counterintuitive)**: ticker_weak bull commits were made in environments where VIX was LOWER than other-bull-cell environments — the OPPOSITE of the symmetric-to-bear-side hypothesis. The losing bullish commits did NOT cluster in high-VIX (risk-off) environments; they clustered in NORMAL-to-low VIX environments.

**Mechanistic interpretation**: per the 2026-05-06 sector-α attribution analysis, the bull ticker_weak cohort is **stock-specific weakness** (88.9% Tech-concentrated; AAPL/MSFT/NVDA dominate the worst-10 list). The mechanism is per-ticker mean-reversion after bullish-prose-driven LLM commits at local highs — NOT macro environment failure. Macro environment is therefore NOT the discriminator for this cohort.

## Threshold sweep — VIX-snapshot > threshold suppresses bull call

| VIX_thresh | Fires | Cohort caught | FP | Net Δα/n | Cohort hit % |
|---:|---:|---:|---:|---:|---:|
| 16.0 | 67 | 20/27 | 47 | **-2.25pp** | 30% |
| 18.0 | 62 | 18/27 | 44 | **-2.30pp** | 29% |
| 20.0 | 55 | 13/27 | 42 | **-2.86pp** | 24% |
| 22.0 | 45 | 10/27 | 35 | **-3.57pp** | 22% |
| 25.0 | 19 | 5/27 | 14 | **-2.42pp** | 26% |
| 28.0 | 7 | 2/27 | 5 | **-4.44pp** | 29% |
| 30.0 | 4 | 1/27 | 3 | **-8.67pp** | 25% |

**EVERY threshold yields NEGATIVE net Δα** — suppressing bull commits when VIX is high HURTS realized alpha. The best threshold (VIX > 16; broadest fire) still loses -2.25pp.

**Net Δα convention**: positive = good. For bull suppression: net_delta = sum(-alpha_spy on fires) — i.e., suppressing a bull call where realized α was POSITIVE (correct call) costs us alpha; suppressing where alpha was NEGATIVE (wrong call) saves us alpha.

The negative net Δα across the entire sweep means: the 67-row "fire" cohort at VIX > 16 had MORE positive-α bull commits (correct calls being suppressed) than negative-α bull commits (wrong calls correctly suppressed). Mostly false-positive suppression.

## Constitution VIII v1.4.0 gate evaluation — FAIL → SKIP

| Threshold | n_fired | Net Δα | Cohort hit % | Standalone PASS? |
|---|---:|---:|---:|---|
| VIX > 16 | 67 | -2.25pp | 30% | **FAIL** (Δα < +0.5pp; cohort hit < 40%) |
| All other thresholds | varies | -2.30pp to -8.67pp | 22-30% | FAIL |

**Verdict: FAIL → SKIP** at every threshold tested. Bull-side Class 4 macro filter is empirically refuted.

No need to evaluate v1.4.3 additive gate — standalone gate fails at every threshold.

## Implications

1. **Mechanism asymmetry confirmed**: bear-side macro-environment matters (PASS at PR #193); bull-side does NOT (this SKIP). Asymmetric cohort failure mechanisms:
   - Bear-side ticker_strong cohort = counter-trend bear in risk-on environment (low VIX) → MACRO-DRIVEN failure; suppressible
   - Bull-side ticker_weak cohort = stock-specific mean-reversion (88.9% Tech-concentrated; AAPL/MSFT/NVDA local-high commits) → STOCK-SPECIFIC failure; NOT macro-suppressible

2. **The asymmetry is consistent with project framing**: bear-side commits are regime-asymmetric (per Constitution VII Replicability scope); bull-side commits at 21d are well-calibrated overall (+1.23% across n=71 cross-experiment per RESEARCH_FINDINGS Empirical core). The losing bullish subset is structural per-ticker mean-reversion, not macro mismatch.

3. **Class 4 BULL stays SKIP'd** unless a NEW bull cohort emerges with macro-driven (not stock-specific) failure characteristics. The 27-row ticker_weak cohort is the operational target; that cohort is empirically not macro-driven.

4. **Spec 012 BULL-side activation NOT recommended**: `class_4_macro_bull_mode = "off"` default in DEFAULT_CONFIG (per Spec 012 plan.md FR-005) is empirically correct; no future amendment to flip default-on for bull-side justified.

5. **Constitution VIII v1.4.1 retrospective-first methodology validated again**: ~$0 + ~30 min retrospective avoided ~6-8h of empty-spec implementation that would have been wasted.

## What this DOES rule in for the future

- **Stock-specific bull-loser cohort needs a different mechanism class**: per-ticker prose-density (Spec 003 — already shipped) is the structural fit; corpus growth in the 003 cohort is the path forward, not macro features.
- **Per-ticker mean-reversion at local highs** could be tested via a NEW Class N filter (price-vs-rolling-high; e.g., suppress bull when price within 2% of 30d high). Not in scope for this retrospective.

## Constitution adherence

- ✅ I (Save Everything): this retrospective markdown
- ✅ III (Stay Cheap): $0 LLM
- ✅ IV (No Production Claims): SKIP verdict; no production deployment
- ✅ VIII v1.4.0: standalone gate FAILED → SKIP at every threshold; methodology output
- ✅ VIII v1.4.1: retrospective ships before any spec drafting

## Cross-references

- `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193 — bear-side PASSED)
- `claudedocs/sector-alpha-attribution-2026-05-06.md` (cohort identification: bull ticker_weak n=27)
- `claudedocs/spec-012-class-4-deployment-retrospective-2026-05-09.md` (PR #200 — Spec 012 bear-side deployment)
- `scripts/class4_macro_retrospective.py` (sister bear-side script)
- `scripts/class4_macro_bull_retrospective.py` (this PR — reproducible script)
- Constitution VIII v1.4.0 + v1.4.1
- Memory: `feedback_retrospective_first_pattern.md` (Constitution VIII v1.4.1 SKIP-saves-spec-cost discipline)
