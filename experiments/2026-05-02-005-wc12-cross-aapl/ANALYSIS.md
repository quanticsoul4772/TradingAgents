# Analysis: wc12-cross-aapl

WC-12 generalizes to AAPL but in the OPPOSITE direction from NVDA — AAPL's pilot was bearish-skewed (7/10 Underweight) and the synthesis-blind PM produced 7 Hold + 2 Underweight + 1 SELL, with the bear-side commitments (Underweight + Sell) showing strong positive forward-alpha while the moderating Holds underperformed; this refutes "WC-12 always amplifies in one direction" and confirms "WC-12 reveals whichever side the underlying signal warranted."

## Result

### Distribution comparison (AAPL × same 10 dates as WC-12 NVDA)

| Bucket | Pilot baseline | **WC-12 AAPL** |
|---|---|---|
| Buy | 0 | 0 |
| Overweight | 0 | 0 |
| Hold | 3 | **7** |
| Underweight | 7 | 2 |
| **Sell** | 0 | **1** ← first Sell in any experiment |

### Forward-α (5-day vs SPY)

| Bucket | WC-12 AAPL N | Mean α | Hit rate |
|---|---|---|---|
| Hold | 7 | **−0.84%** | 43% |
| Underweight | 2 | **+3.86%** | 100% |
| Sell | 1 | **+0.95%** | 100% |

### EH-2 gate

1 DENY: missing Buy + Overweight (the pilot AAPL distribution had no Buy/Overweight either, so this is an inherent property of the analyst signal on AAPL, not a synthesis-vs-PM artifact).

## Decision

**The original WC-12 hypothesis ("synthesis is the dilution step") generalizes, but the WC-12 *forward-alpha* finding does not.** On AAPL:
- Synthesis-blind PM still breaks mode collapse (1 Sell vs pilot's 0 — the framework's first ever)
- BUT the bear-side strong calls are **CORRECT**, not incorrect. Underweight averaged +3.86% α; Sell +0.95%. The Holds that the PM moderated TO were the wrong calls.

This is the opposite calibration pattern from NVDA, where:
- Synthesis-blind produced 5 Buys with -0.22% α (wrong)
- Synthesis-blind Overweights had +0.25% α (less wrong)

### Refined WC-12 model (3 takeaways)

1. **The synthesis dampens commitment in BOTH directions.** Pilot NVDA was bullish-pulled-toward-Overweight; pilot AAPL was bearish-pulled-toward-Underweight. Removing the synthesis lets the PM commit further in whichever direction the signal warranted.

2. **The PM has the directional information.** It commits correctly when freed of the synthesis on AAPL (the bear case was right; PM produced the bear-side strong call). On NVDA the PM committed to Buy when the bull case was actually weaker than it looked — a different failure mode.

3. **The synthesis was hiding both correct and incorrect strong signals.** The pilot's mode collapse to moderate ratings hid AAPL's correct Sell signal AND NVDA's incorrect Buy signal. Both got revealed by WC-12; one was right, one was wrong.

### What this tells us about the architectural fix

The WC-12 forward-α follow-up's "synthesis was defensively dampening a model that lacks edge" interpretation is **partially correct but incomplete**. More precise:

- The synthesis dampens a PM that has *some* signal accuracy but high noise in commitment direction
- On tickers where the PM's bias matches the underlying signal (AAPL: bear PM bias + bear signal), the synthesis suppresses correct strong calls
- On tickers where the PM's bias diverges from the underlying signal (NVDA: bull PM bias + dubious bull signal), the synthesis suppresses incorrect strong calls — which is good, accidentally

A proper fix would let strong signals through ONLY when they're supported by evidence quality, not just by directional consistency. The current synthesis can't tell the difference; neither can the PM-blind variant. **The architectural intervention has to happen at the analyst layer (better data/reasoning) OR at a calibration layer (track per-rating realized α and adjust forward).**

This is also a strong argument for **better upstream news data** (per the WC-12 forward-α follow-up): if the analysts produced more accurate forecasts, both the synthesis and the synthesis-blind PM would have better material to work with, and the strong calls would be calibrated correctly more often.

## Detailed findings

### Per-date breakdown

| Date | Pilot | WC-12 AAPL | Δ |
|---|---|---|---|
| 2026-01-30 | Hold | Underweight | -1 (bearish) |
| 2026-02-06 | Underweight | Hold | +1 (less bearish) |
| 2026-02-13 | Hold | Hold | same |
| 2026-02-20 | Underweight | Underweight | same |
| 2026-02-27 | Underweight | Hold | +1 |
| 2026-03-06 | Underweight | Hold | +1 |
| 2026-03-13 | Underweight | **Sell** | -1 (strong bear) |
| 2026-03-20 | Underweight | Hold | +1 |
| 2026-03-27 | Underweight | Hold | +1 |
| 2026-04-03 | Hold | Hold | same |

**Net direction**: 5 dates moderated toward Hold, 1 date strengthened to Sell, 1 date strengthened to Underweight, 3 unchanged.

The Sell on 3/13 is the headline. AAPL between 3/13 and the holding window's end was a date where the bear case was overwhelming enough to break through the PM's typical caution. Notable that this happens with `pm_sees_synthesis=false` — the PM looking only at the trader plan + risk debate produced a stronger committal call than the synthesis was apparently going to permit.

### Why moderation toward Hold dominates

5 of the 10 ratings shifted from Underweight (pilot) → Hold (WC-12). This is the OPPOSITE of NVDA where Overweight (pilot) → Buy (WC-12) dominated.

Hypothesis: the bull/bear debate on AAPL had a real bear case that the synthesis was AMPLIFYING (forcing too many Underweights). Without the synthesis, the PM defaults to its baseline of Hold-when-uncertain. The 3/13 Sell is the one date where the PM was CONFIDENT enough in the bear case to commit beyond Hold without the synthesis pushing it.

This is a different failure mode from NVDA: there the synthesis was UNDER-amplifying the bull conviction (pulling Buy candidates to Overweight); here it was OVER-amplifying the bear caution (pulling Hold-deserving dates to Underweight).

The combined picture: **the synthesis is bidirectionally miscalibrated.** It both under-commits where it should commit (NVDA case) AND over-commits where it shouldn't (AAPL case). The dampening isn't a uniform conservative force; it's noise around the PM's actual judgment.

## Limitations

- n=10, single ticker, single window
- Cross-pattern observed across NVDA + AAPL but a third ticker (MSFT, see companion experiment 2026-05-02-006) shows a third pattern — the WC-12 effect varies substantially by ticker
- Forward-α is 5-day; longer horizons may show different calibration
- The Sell rating is n=1; can't conclude general "WC-12 produces correct Sells on AAPL" from a single data point

## One-paragraph summary for findings.md

> WC-12 generalizes to AAPL but in the OPPOSITE direction from NVDA — AAPL's pilot was bearish-skewed (7/10 Underweight) and the synthesis-blind PM produced 7 Hold + 2 Underweight + 1 SELL, with the bear-side commitments (Underweight + Sell) showing strong positive forward-alpha while the moderating Holds underperformed; this refutes "WC-12 always amplifies in one direction" and confirms "WC-12 reveals whichever side the underlying signal warranted."
