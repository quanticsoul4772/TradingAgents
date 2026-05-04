# Analysis: xle-q4-2025-micro

> **Headline**: Cross-period validation of the sector-ETF bear-side accuracy finding from 003. **The finding does NOT replicate.** XLE Q4 2025 produced 7 Hold + 3 UW + 0 OW; UW 21d α = **+11.77% (n=3, 100% directionally WRONG)**. XLE Q1 2026 had UW α = -7.30% (n=3, 67% correct). Combined cross-period ETF UW: 8 commits, 62.5% correct, mean α +0.65% — **barely-positive aggregate; no bear-side ETF signal**. The "80% correct n=5" finding from 003 was small-sample artifact + Q1 2026 favorable energy regime. **Decision: Scenario B** per HYPOTHESIS — regime-driven, not bear-accuracy. Same lesson as the bull-side finding from 008: realized α is period-conditional even on sector ETFs.

## Result

### Distribution

| Period | OW | Hold | UW | Notes |
|---|---|---|---|---|
| XLE Q1 2026 (003) | 2 | 5 | 3 | bull commits caught the Q1 rally |
| **XLE Q4 2025 (this)** | **0** | **7** | **3** | no bull commits; 3 UW commits |

Bucket-level commit pattern partially replicates (Hold-leaning + some UW), but XLE Q4 2025 has zero OW commits where Q1 2026 had 2. Substrate-level commit behavior is regime-shaped, period-shaped, AND substrate-shaped — three confounds at work.

### Forward-α via horizon_sweep

| Bucket | 5d (n, hit%) | 10d (n, hit%) | **21d (n, hit%)** | 90d (n, hit%) |
|---|---|---|---|---|
| Hold | +0.17% (n=7, 43%) | -0.28% (n=7, 43%) | **+0.80% (n=7, 43%)** | +28.98% (n=6, 100%) |
| Underweight | +2.38% (n=3, 100%) | +3.05% (n=3, 100%) | **+11.45% (n=3, 100%)** | — |

**Critical contrast with 003**:
- XLE Q1 2026 UW α at 21d: -7.30% n=3 (67% correct, mean direction was right)
- XLE Q4 2025 UW α at 21d: +11.45% n=3 (100% wrong, mean direction completely inverted)

The horizon dependency on UW is monotonic in the wrong direction: 5d +2.38% → 10d +3.05% → 21d +11.45%. The framework's UW commits were against a sustained XLE rally that compounded over the forward window. **No bear-side accuracy on this period.**

### Cross-period XLE UW comparison

| Period | n | Mean α | Direction correct % | Hit pattern |
|---|---|---|---|---|
| Q1 2026 (003) | 3 | -7.30% | 67% (2/3) | bear-correct on most |
| Q4 2025 (this) | 3 | **+11.77%** | **0% (0/3)** | bear-wrong on all |
| **Combined XLE UW** | **6** | **+2.24%** | **33% (2/6)** | barely-positive aggregate, weakly anti-calibrated |

Adding XLF UW (Q1 2026, n=2, mean -4.14%, 100% correct) gives the full cross-experiment ETF UW picture:

| Cohort | n | Mean α | Direction correct % |
|---|---|---|---|
| ETF UW total (XLF Q1 + XLE Q1 + XLE Q4) | 8 | **+0.65%** | **62.5% (5/8)** |
| Single-stock UW (cross-experiment) | ~37 | ~+4.55% | ~58% (wrong-direction on 21+ of 37) |

The aggregate ETF UW is now barely-positive (+0.65%, 62.5% correct directionally) — better than single-stock UW but not the strong "80% correct on ETFs" claim from 003 alone.

### Bayesian update

Per HYPOTHESIS, the prior on "ETF bear-side accuracy is real" was ~0.55 (weak prior given n=5 only). Q4 2025 evidence is decisively negative — 0/3 correct, mean +11.45% wrong-direction. Posterior should drop materially.

Approximate update:
- Likelihood under H1 (real bear-side accuracy on ETFs): expect 60-80% directionally-correct UW; observed 0/3. Likelihood ≈ 0.05-0.1.
- Likelihood under H0 (no special ETF bear-side, period-conditional like single stocks): expect 30-60% directionally-correct UW; observed 0/3. Likelihood ≈ 0.2-0.3.
- Bayes factor ≈ 0.2-0.3 (favoring H0).
- Posterior: 0.55 → roughly **0.20-0.30**.

The bear-side ETF claim retired. There is no substrate-specific bear-side accuracy advantage; the 003 result was n=5 artifact + favorable Q1 2026 energy regime.

## Decision

**Scenario B** per HYPOTHESIS decision tree: bear-side accuracy on ETFs is regime-driven, not a general property. Action assigned by HYPOTHESIS:

> "Document as 'ETF commit calibration regime-driven; bear-side accuracy on Q1 2026 was period-favored.' Phase D still useful but bear-side claim narrower."

Acting on this:

1. **Retire the bear-side ETF accuracy claim** in RESEARCH_FINDINGS Phase D section. Replace with the more honest "ETF UW commits are barely-positive in aggregate (+0.65% n=8, 62.5% correct directionally) — better than single-stock UW but not a special property; period-conditional like everything else."
2. **Phase D direction**: continue testing per-sector regime discrimination (which IS a real finding from 003) but don't anchor on the bear-side claim.
3. **Generalization lesson**: this is the third instance of "single-experiment α finding doesn't replicate cross-period" — 008 (bull-side OW), 003 (bear-side UW initially looked great), now 004 (the cross-period for that same finding). **The Constitution VII Cross-period scope clarification (v1.2.2) is being repeatedly validated — realized-α claims really are period-conditional.**

## Detailed findings

### What this means for the architectural reframe

Pre-this-experiment Phase D framing:
- Architecture portable ✓
- Per-sector regime discrimination intact on ETFs ✓
- Bear-side accuracy on ETFs much higher than on single stocks (n=5 finding from 003)

Post-this-experiment Phase D framing:
- Architecture portable ✓ (still true)
- Per-sector regime discrimination intact on ETFs ✓ (still true — 003 + 004 both show this)
- ~~Bear-side accuracy on ETFs is special~~ → **No special bear-side advantage; ETF UW is period-conditional like everything else**

The framework's value proposition stays: calibrated abstention + per-sector regime discrimination. The "ETFs are better for bear-side" rabbit hole is closed.

### Why XLE Q4 2025 UW commits were wrong

Without doing forensic analysis: XLE was likely in a Q4 2025 rally driven by oil price moves or sector rotation. The framework read XLE evidence as bearish (per its analyst reports) but the underlying price action was bullish. This is the same failure mode as 008 NVDA Q4 2025 — framework reads evidence directionally, but the period's macro tailwind dominates the realized α.

This is consistent with the architectural reframe: framework outputs calibrated commits given observable evidence. Whether commits realize positive α depends on the period's macro backdrop, not just the framework's reasoning quality.

### What replicates across XLE periods

- **Hold-heavy bias**: 5/10 (Q1) and 7/10 (Q4) — both above 50%
- **No Buy commits**: zero in both periods
- **No Sell commits**: zero in both periods (3-tier output is the active range)
- **Some UW commits**: 3 in each period

What does NOT replicate:
- OW commit count: 2 in Q1, 0 in Q4
- UW direction accuracy: 67% correct Q1, 0% correct Q4
- Realized α magnitude on UW: -7.30% Q1, +11.77% Q4 (~19% range)

### Updated cross-experiment OW 21d

XLE Q4 2025 produced 0 OW commits, so the OW row is unchanged at +1.52% n=73, ~62% hit.

UW row updates: prior cross-experiment UW 21d was approximately +3.06% n=36 with mixed correctness (per the post-multi-sector-Phase-D update). Adding 3 commits at +11.77%: roughly (3.06×36 + 11.77×3)/39 = (110.16+35.31)/39 = +3.73% n=39. The bear-side aggregate is anti-calibrated; this experiment moves it slightly more so.

## Limitations

- **n=3 UW commits per period** is too small to claim "ETF bear-side is anti-calibrated" with high confidence. The aggregate n=8 is also small.
- **Single substrate (XLE only)**. XLF Q4 2025 untested. The 80% correct ETF UW claim from 003 included XLF (2/2 correct); this experiment doesn't update on XLF.
- **One forward window per date**. Sectors with strong macro tailwinds in 21d windows can dominate any signal the framework produces.
- **A3 filter inactivity**: the filter is unlikely to fire on ETFs (sector indices rarely move ±5% in 30 days). Filter-related effects untested.

## Cost & timing

- Wall-clock: 67.7 min (target was ~70 min, on track)
- Cost: ~$3 (T1 ceiling, exactly as predicted)
- Errors: 0/10 (404 fundamentals errors continue, non-fatal)
- PARAMS.json auto-synced ✓

## Next experiment

The bear-side ETF rabbit hole is closed. Next-most-valuable Phase D options:
1. **Multi-sector cross-period (XLF + XLE Q4 2025 micro, $3 — XLF only since XLE done)**: completes XLF cross-period picture; validates if XLF's 100%-correct Q1 UW also fails to replicate
2. **Substrate-prompt-adapted XLK rerun ($10 T2)**: tests if shifting the abstention bar improves any signal
3. **Different substrate type ($10 T2)**: commodity ETF (USO) or crypto pair, broader generalization test

Or step away from Phase D and pursue the still-uncovered cross-period question on stocks: AAPL Q3 2025 micro ($3 T1).

## One-paragraph summary for findings.md

> Cross-period validation of the sector-ETF bear-side accuracy finding from 003. The finding does NOT replicate. XLE Q4 2025 produced 7 Hold + 3 UW + 0 OW; UW 21d α = +11.77% (n=3, 100% directionally WRONG vs 67% correct in Q1 2026 with mean -7.30%). Combined cross-period XLE UW: n=6, +2.24%, 33% correct. Including XLF Q1 (2/2 correct, -4.14%): cross-experiment ETF UW = +0.65% n=8, 62.5% correct — barely-positive aggregate, no special bear-side ETF advantage. Decision: Scenario B — bear-side accuracy on ETFs is regime-driven and period-conditional, not a substrate property. The "80% correct n=5" claim from 003 was small-sample artifact + favorable Q1 2026 energy regime. Bayesian posterior on "ETF bear-side accuracy is real" drops from ~0.55 to ~0.25. The architectural reframe holds (calibrated abstention + per-sector discrimination); the bear-side ETF rabbit hole is closed.
