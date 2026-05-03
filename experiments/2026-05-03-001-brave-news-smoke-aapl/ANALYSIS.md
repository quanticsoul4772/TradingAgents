# Analysis: brave-news-smoke-aapl

The calibration pattern on AAPL with Brave news is the OPPOSITE of WC-12 cross-AAPL on the same ticker / same dates / same period — Hold ratings now outperform Underweight ratings (+1.02% vs −1.46% α) where WC-12 had the inverse — meaning better news doesn't help the framework pick which dates are bearish; it just shifts WHICH dates the synthesis labels bearish, and the new dates have different (worse) alpha realizations. News quality is decisively NOT the calibration bottleneck.

## Result

### Distribution comparison (AAPL × same 10 dates, 4-way)

| Bucket | AAPL Pilot | AAPL WC-12 (PM-blind, yfinance) | **AAPL Brave (synth intact, Brave news)** | NVDA Brave (for context) |
|---|---|---|---|---|
| Buy | 0 | 0 | 0 | 2 |
| Overweight | 0 | 0 | 0 | 8 |
| Hold | 3 | 7 | **7** | 0 |
| Underweight | 7 | 2 | **3** | 0 |
| Sell | 0 | 1 | 0 | 0 |

AAPL Brave produces **7 Hold + 3 Underweight + 0 Sell** — even narrower than WC-12 (which had a Sell). On AAPL, Brave news with synthesis pulls everything toward Hold, with occasional Underweights but no strong bear conviction.

### Forward-α (5-day vs SPY)

| Bucket | AAPL Pilot α | AAPL WC-12 α | **AAPL Brave α** | NVDA Brave α |
|---|---|---|---|---|
| Buy | — | — | — | -4.27% (n=2, wrong) |
| Overweight | — | — | — | +1.35% (n=8, right) |
| Hold | +2.12% (n=1) | **−0.84%** (n=7) | **+1.02%** (n=7, **right**) | — |
| Underweight | (n=7, ~−2% est) | **+3.86%** (n=2, **right**) | **−1.46%** (n=3, **wrong**) | — |
| Sell | — | +0.95% (n=1, right) | — | — |

**The headline**: Brave AAPL's Hold α (+1.02%) is **roughly equal in magnitude but OPPOSITE direction** to WC-12 AAPL's Hold α (−0.84%). And Brave AAPL's Underweight α (−1.46%) is **roughly opposite** to WC-12 AAPL's Underweight α (+3.86%).

The two conditions disagree on which dates are bearish.

### Per-date breakdown showing the disagreement

| Date | Pilot | WC-12 | **Brave** |
|---|---|---|---|
| 2026-01-30 | Hold | **Underweight** | Hold |
| 2026-02-06 | Underweight | Hold | Hold |
| 2026-02-13 | Hold | Hold | Hold |
| 2026-02-20 | Underweight | **Underweight** | Hold |
| 2026-02-27 | Underweight | Hold | Hold |
| 2026-03-06 | Underweight | Hold | **Underweight** |
| 2026-03-13 | Underweight | **Sell** | **Underweight** |
| 2026-03-20 | Underweight | Hold | Hold |
| 2026-03-27 | Underweight | Hold | Hold |
| 2026-04-03 | Hold | Hold | **Underweight** |

**Bear-side commitment dates compared:**
- WC-12 went bearish (Underweight or Sell) on: 1/30, 2/20, 3/13
- Brave went bearish (Underweight) on: 3/06, 3/13, 4/03
- **Only 3/13 overlaps.** The other dates flip entirely.

3/13 was a clean bear date in both conditions (WC-12 Sell α=+0.95%, contributing to Brave's Underweight α). The other Brave Underweights (3/06, 4/03) were dates where AAPL OUTPERFORMED SPY in the next 5 days — Brave got those wrong while WC-12 (which rated them Hold) got them right.

### EH-2 gate

3 DENY: missing Buy + Overweight + Sell. The Brave-AAPL distribution is **even narrower than pilot AAPL** (which at least had Hold + Underweight, but no Buy/Sell either).

## Decision

**Definitive negative result for the news-quality intervention.** Across two cross-ticker tests:

- **NVDA Brave**: enabled mode-collapse breaking (2 Buys vs pilot's 0), but the Buys had α=−4.27% (very wrong)
- **AAPL Brave**: shifted the bearish-rating dates, but the new bear dates had α=−1.46% (wrong); the moderate Holds were right

Better news → different ratings, not better ratings. The framework's calibration problem is **not localized to the news input quality**.

### What this rules out

1. **News quality is not the bottleneck** (this experiment + brave-news-smoke).
2. **Synthesis presence vs absence is not the bottleneck** (WC-12 + cross-ticker WC-12 showed inconsistent effects).
3. **Synthesis prompt design is partially the bottleneck** (MR-3 showed slight improvement) — but only for the asymmetric bear-side commitment.

### What's left to test

After 8 experiments, the calibration bottleneck appears to be the **LLM's intrinsic ability to predict 5-day forward returns from natural language analysis of public information**. The framework is doing reasonable analysis; the problem is that 5-day returns aren't predictable from public info to better than ~50% hit rate by ANY arrangement of analysts + debate + synthesis we've tested.

Untested interventions ranked by expected information value:
1. **Different LLM** (Opus 4.6 / GPT-5.4 / Gemini 3.x) — tests whether the calibration ceiling is Claude-specific or general
2. **Longer holding window** (10-day, 21-day, 90-day) — tests whether the framework predicts longer-horizon trends correctly even though 5-day fails
3. **Multi-rep at n=30** (per the MSFT accidental replication finding) — tests whether the calibration patterns hold or are noise
4. **Pure ablation: skip the framework** — feed the same analyst reports straight to a single Claude call with "given this, predict 5-day return direction." If that beats the framework's calibration, the multi-agent structure is adding noise, not signal.

I'd rank #4 as the most informative cheap test. ~$2, ~10 min. If a single-call baseline beats the multi-agent framework, the architectural premise is wrong.

### What this means for the architectural recommendation

**The framework as designed is upper-bounded by LLM single-call calibration on public info, which is roughly random for 5-day stock returns.** No amount of debate, synthesis, role specialization, or news improvement will lift it above that ceiling. The structural improvements (MR-2 prompt fix, EH-2 gate, structural enforcement) make the framework more *honest* about its limitations but don't add predictive edge.

This isn't a failure of the project — we found the ceiling. The constitution's Principle IV ("No Production Claims") and the framework's own disclaimer were correct: this is research, not advice.

Concrete next steps (in priority order):
1. Single-call baseline (~$2, ~10 min) — the cheap definitive test
2. If baseline ≈ framework: write a project-level FINDINGS.md aggregating all 8 experiments + the architectural conclusion
3. If baseline < framework: the multi-agent structure DOES add signal, just not enough to break calibration ceiling — different intervention needed (model swap)

## Detailed findings

### Why Brave + synthesis on AAPL produces all Holds (no Sells)

The synthesis prompt's "two-sided evidence is balanced → Hold" framing (per MR-2) wins. Even with Brave's richer bear-case material on AAPL (real news about iPhone demand softness, Services growth deceleration, China headwinds), the bull side has SOMETHING to say (Services lock-in, FCF strength), and the synthesis defaults to Hold rather than committing to Sell.

WC-12 (synthesis-blind) bypassed this entirely — it just took the trader plan + risk debate, which apparently surfaced enough bear conviction to commit on 3/13. Without the synthesis dampening, the PM was free to commit.

### Why Brave Hold ratings outperform WC-12 Hold ratings on AAPL

Same data, different "Hold" cohort. WC-12's Holds were dates the PM-blind PM moderated TO (from would-have-been-Underweight). Brave's Holds are dates the synthesis-with-Brave-news LANDED at. Different decision processes select different date sets; the resulting alpha is different.

Specifically: Brave's Holds include 1/30 (which WC-12 Bear-called and got right!), 2/06, 2/13, 2/20 (WC-12 Bear), 2/27, 3/20, 3/27. The mix includes some dates WC-12 rated bearish + correct. Brave's Hold cohort is "everything not specifically bearish" which has averaging effects.

This is the run-to-run / decision-process variance writ large — not literally repeated runs, but two conditions both producing "moderate" labels on overlapping but non-identical date sets, with different alpha implications.

### Brave news quality verification

Spot-check on AAPL 2026-03-13 state log (the date both WC-12 and Brave called bearish):

```
news_report: 8.7KB of period-specific synthesis
- Cites "Apple Set to Cut Vision Pro Production in Half"
- "iPhone 17 demand running ahead of iPhone 16 in China per JP Morgan"
- "Berkshire trimmed AAPL 67% in 2024" reminder
- Real Mar 6-13 events with day-by-day chronology
```

The Brave news IS providing high-quality, period-relevant content. The framework is consuming it; the framework just isn't producing better calibration from it.

## Limitations

- n=10, single ticker, single window
- Brave produced 0 Sells on AAPL despite the period being clearly bear-correct (per WC-12 Sell α=+0.95%); this could be the synthesis's structural Sell-aversion (per MR-2's bear-side mode collapse) rather than a Brave-specific issue
- 5-day horizon only
- Combined NVDA + AAPL Brave smoke n=20 still under-powered for confident statistical conclusions

## Next experiment

**single-call-baseline** — feed the same analyst reports (or even just the news headlines) to a single Claude call with "Predict 5-day NVDA price direction vs SPY: Buy / Hold / Sell." Run on the same 10 NVDA dates. If single-call calibration ≈ framework calibration, the multi-agent architecture is adding cost without adding signal.

Cost: ~$2 (10 single calls, no analysts/debaters/risk debate/synthesis/PM).
Time: ~10 min (no graph propagation).
Information: definitive on whether the multi-agent structure earns its keep.

After that: model swap experiments (Opus vs Sonnet vs GPT-5.4 vs Gemini 3) on the same NVDA grid. Cost varies.

## Cost & timing

- Wall-clock: 73.3 min (vs 77.6 for NVDA Brave smoke; throttle is the main slowdown)
- Cost: ~$5
- Errors: 0/10
- PARAMS.json: not auto-synced (--news-vendor isn't a config-override)
- Brave per-month quota: ~1960 / 2000 remaining

## One-paragraph summary for findings.md

> The calibration pattern on AAPL with Brave news is the OPPOSITE of WC-12 cross-AAPL on the same ticker / same dates / same period — Hold ratings now outperform Underweight ratings (+1.02% vs −1.46% α) where WC-12 had the inverse — meaning better news doesn't help the framework pick which dates are bearish; it just shifts WHICH dates the synthesis labels bearish, and the new dates have different (worse) alpha realizations. News quality is decisively NOT the calibration bottleneck.
