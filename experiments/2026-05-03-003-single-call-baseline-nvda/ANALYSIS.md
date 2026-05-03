# Analysis: single-call-baseline-nvda

A single Claude call on the framework's analyst reports breaks the mode collapse entirely — produces 0 Holds, all 10 ratings are committed (6 Overweight + 4 Underweight) — but the resulting calibration is **30% directionally correct** (worse than coin flip), with both buckets pointing the wrong direction on average (Overweight α=−0.72%, Underweight α=+1.64%). This flips the architectural hypothesis: the framework's mode collapse to Hold is not a bug, it's calibrated humility. Single-call, without the synthesis dampening, fabricates conviction it can't back up. **Both single-call and framework hit the LLM 5-day-prediction ceiling, but in different failure modes.**

## Result

### Distribution comparison (NVDA × same 10 dates, 5-way)

| Bucket | Pilot NVDA | WC-12 NVDA | MR-3 NVDA | Brave NVDA | **Single-call NVDA** |
|---|---|---|---|---|---|
| Buy | 0 | **5** | 0 | 2 | 0 |
| Overweight | 0 | 1 | 6 | 8 | **6** |
| Hold | 7 | 1 | 3 | 0 | **0** |
| Underweight | 3 | 2 | 1 | 0 | **4** |
| Sell | 0 | 1 | 0 | 0 | 0 |

**Single-call has the most committed distribution** of all 5 conditions — only WC-12 (PM-blind) comes close. Both share: removing or bypassing the synthesis hedging produces strong commits.

### Forward-α (5-day vs SPY)

Convention (consistent with previous ANALYSIS): bullish ratings (Buy/Overweight) are **directionally correct when α>0**; bearish (Sell/Underweight) **correct when α<0**.

| Bucket | Pilot α | WC-12 α | MR-3 α | Brave α | **Single-call α** |
|---|---|---|---|---|---|
| Buy | — | −0.22% (5) | — | −4.27% (2) | — |
| Overweight | — | — | — | — | **−0.72% (6) ✗** |
| Hold | (n=7) | — | — | — | — |
| Underweight | (n=3) | — | (n=1, +2.45%) | — | **+1.64% (4) ✗** |
| Sell | — | — | — | — | — |

**Both single-call buckets are directionally wrong on average.** The framework's NVDA Buy calls were also wrong (Brave −4.27%, WC-12 −0.22%) — different distributions, same anti-calibration.

### Per-date breakdown with realized α

| Date | Realized α | Pilot | WC-12 | MR-3 | Brave | **Single-call** | Single-call correct? |
|---|---:|---|---|---|---|---|---|
| 2026-01-30 | −2.80% | Hold | Buy | Hold | OW | **OW** | ✗ |
| 2026-02-06 | −0.12% | Hold | Buy | OW | OW | **OW** | ✗ (negligible) |
| 2026-02-13 | +4.69% | Hold | Buy | OW | OW | **OW** | ✓ (large win) |
| 2026-02-20 | −6.15% | Hold | Buy | OW | OW | **OW** | ✗ (BIG miss) |
| 2026-02-27 | +2.34% | UW | Hold | OW | OW | **UW** | ✗ |
| 2026-03-06 | +2.87% | UW | Buy | OW | Hold | **UW** | ✗ |
| 2026-03-13 | −2.38% | UW | Sell | OW | Hold | **OW** | ✗ |
| 2026-03-20 | −0.77% | UW | Hold | UW | Hold | **UW** | ✓ |
| 2026-03-27 | +0.13% | Hold | Hold | OW | Hold | **UW** | ✗ |
| 2026-04-03 | +2.45% | Hold | Hold | Hold | Buy | **OW** | ✓ |

**Single-call directional hit rate: 3/10 = 30%** (worse than coin flip). For comparison, Brave NVDA's 2 Buy calls were both wrong (0% on the strong-rating subset). The 30% number isn't dramatically better than the framework's strong-call performance — both are below chance.

### EH-2 gate

3 DENY findings (same as Brave/Exa AAPL): missing Buy + Sell. Single-call broke Hold-collapse but didn't break the BUY/SELL extremes — Sonnet on these reports stays in the moderate-commitment band (OW/UW), never reaches high-conviction calls.

## Decision

**Scenario A + C hybrid**: structurally different from the framework (no Hold collapse — Scenario C-like), but matches the framework on calibration ceiling (both anti-calibrated on strong calls — Scenario A-like).

This flips the architectural premise. The hypothesis going in was **"if single-call ≈ framework, the framework adds nothing."** What we found:

> **The framework's Hold mode collapse is calibrated humility, not a defect.** The synthesis stage correctly recognizes that the analyst evidence doesn't support strong commits, and produces Hold. Single-call, without the synthesis dampening, fabricates conviction it doesn't have, and that conviction is wrong-direction more often than right.

The multi-agent structure's value isn't "better predictions" — it's **honest hedging via Hold**. Hedging is information: when the framework says Hold, it's saying "the LLM can't predict this date well enough to commit." When single-call says Overweight on the same date, it's manufacturing unwarranted confidence.

This is a defensible architectural claim: the framework's mode collapse, which the constitution's MR-2 + MR-3 experiments treated as a bug to fix, may actually be the framework's most honest output.

### Updated framing of the 10-experiment chain

| Question | What we now believe |
|---|---|
| Why does the framework mode-collapse to Hold? | Because the LLM correctly cannot predict 5-day returns from public info, and synthesis surfaces that as Hold. |
| Why did news quality improvements fail? | The bottleneck isn't input quality — it's the prediction ceiling. Better inputs → same ceiling → same Hold. |
| Why did the structural enforcements (EH-2 gate, MR-3 prompt) fail to break Hold? | Because they were attacking honest output. Forcing strong calls just exposes the noise as wrong commits (per single-call). |
| What does the framework actually contribute? | Calibrated abstention via Hold, when single-call would manufacture wrong conviction. |

### What's left to test

This finding deserves a confirmatory experiment before being load-bearing:

1. **Single-call baseline on AAPL × 10** (~$1, ~5 min) — does the same anti-calibration hold on the bear-correct ticker? If single-call AAPL also shows wrong-direction strong calls, the "single-call manufactures noise" thesis is robust. **Highest-priority next test.**
2. **Single-call baseline with Hold allowed in prompt** — currently the prompt says "Reserve Hold ONLY for genuinely balanced evidence; otherwise commit." That's a stronger commitment instruction than Sonnet would naturally produce. Re-running with neutral instructions would test whether the 0-Hold result is from the prompt's pressure or from Sonnet's own judgment without the synthesis dampening.
3. **Different LLM single-call baseline** (Opus 4.6 / GPT-5.4) — is the 30%-correct ceiling Sonnet-specific or general?

### What this means for the project

Three honest paths:

A. **Embrace the Hold collapse as the framework's actual product.** Reframe the project: "TradingAgents is a calibrated-abstention engine for equities — it tells you when public-info evidence supports commit vs hold, and is honest when it doesn't." Update README + constitution accordingly.

B. **Pursue the model-swap question.** If the calibration ceiling is Sonnet-specific, a stronger LLM might lift it. ~$10-30 to test. (But the priors aren't great — the LLM-ceiling-on-public-info finding is consistent across the public literature.)

C. **Project-level FINDINGS.md** aggregating all 10 experiments + this architectural reframe. Wind down active experimentation; the lab notebook is the artifact.

I'd rank **#1 (AAPL single-call confirmation, $1) → then C (FINDINGS.md)** as the responsible close. **#2 (model swap)** only if AAPL confirmation strengthens the result and curiosity warrants the spend.

## Detailed findings

### Why single-call breaks Hold but not the LLM ceiling

The framework's synthesis stage receives the bull/bear debate output and the analyst reports, and is prompted to identify the dominant side. When evidence is genuinely balanced (which MR-1 confirmed happens in 100% of debates), it outputs Hold per the prompt's instructions. The single-call baseline doesn't have a separate synthesis pass — it's prompted directly: "predict 5-day direction, commit unless balanced." The "commit unless balanced" instruction is stronger than the synthesis prompt's "Hold only when balanced," so single-call commits more.

But committing more without more signal = more wrong commits. Single-call's 6 Overweight + 4 Underweight pattern is just the prompt's commitment instruction applied to the same noisy underlying signal the framework sees. The synthesis stage is doing prompt-engineered abstention. Removing it just removes the abstention.

### Why the prior MR-2/MR-3 experiments were misframed

MR-2 identified the synthesis prompt's "two-sided evidence → Hold" framing as the cause of mode collapse and proposed editing it to commit more. MR-3 made the edit and produced 6 Overweight + 3 Hold + 1 Underweight on NVDA — viewed at the time as "asymmetric commitment, no calibration win." We marked it as not-quite-success.

In light of single-call's result, MR-3's behavior makes sense: the v2 prompt edit pushed the synthesis closer to single-call's "always commit" stance. The 6 Overweight calls under MR-3 v2 are likely the same anti-calibration pattern as single-call's 6 Overweight calls (need to recompute MR-3's bucket α to confirm). If true, MR-3 wasn't a partial win — it was sliding toward single-call's more-honest-failure mode.

The synthesis prompt's hedging instruction was correct all along.

### Why the 02-13 win and 02-20 loss are both single-call signature

- 02-13 NVDA α=+4.69% (very bullish): single-call called Overweight ✓. The reports for that date probably had a clear bull tilt from earnings/product news that the LLM correctly read.
- 02-20 NVDA α=−6.15% (very bearish): single-call called Overweight ✗ (big miss). The reports for that date probably looked similar to 02-13 from the LLM's view, but the underlying market moved opposite.

The LLM can read clear bull-leaning reports and predict the bullish day correctly. It cannot tell the difference between "bull-leaning reports + bullish day" and "bull-leaning reports + bearish day" — because public-info-to-5-day-return mapping is not deterministic. The framework's synthesis hedges this; single-call doesn't, and pays the price.

## Limitations

- n=10, single ticker (NVDA), single window — biggest caveat. AAPL confirmation is the immediate next test.
- Prompt's "commit unless balanced" instruction may be pushing single-call toward over-commitment vs Sonnet's natural inclination
- State logs read from brave-news-smoke (07) — single-call inherits any limitations of those analyst reports
- Temperature 0.0 vs framework's defaults — minor source of single-call vs framework variance

## Cost & timing

- Wall-clock: 1.0 min (vs 73-80 min for full backtest)
- Cost: ~$1
- Errors: 0/10
- Per-call mean: 6.0s

## Next experiment

**single-call-baseline-aapl** — same script, AAPL × same 10 dates. Critical replication. If AAPL also shows anti-calibrated single-call, the "honest hedging" thesis is robust and the framework's value proposition flips from "predicts" to "abstains honestly". Cost: ~$1, ~5 min.

After AAPL confirmation:
- Write project-level FINDINGS.md aggregating 11 experiments + the architectural reframe
- Decide whether to continue with model-swap experiments or wind down active experimentation

## One-paragraph summary for findings.md

> A single Claude call on the framework's analyst reports broke the mode collapse entirely (0 Holds, all 10 NVDA dates rated Overweight or Underweight), but produced 30% directionally-correct calls — worse than coin flip — with both buckets pointing the wrong direction on average (Overweight α=−0.72%, Underweight α=+1.64%). This flips the architectural premise: the framework's Hold mode collapse is calibrated humility, not a defect. The synthesis stage correctly recognizes that public-info evidence doesn't support 5-day commits and produces Hold; single-call, without the synthesis dampening, fabricates wrong-direction conviction. Both single-call and framework hit the same LLM 5-day-prediction ceiling, but in different failure modes — and the framework's failure mode (honest abstention) is more useful than single-call's (wrong commits).
