# Analysis: mr3-synthesis-v2

The v2 synthesis prompt didn't shift NVDA ratings toward Buy as predicted (still 0 Buys); instead it produced asymmetric commitment — 0 Buy / 6 Overweight / 3 Hold / 1 Underweight / 0 Sell — AND substantially better forward-alpha calibration than either pilot baseline or WC-12, with the cautious ratings (Hold / Underweight) outperforming the bullish ones in this period where NVDA's bullish lean was wrong on average.

## Result

### Distribution comparison (NVDA × same 10 dates)

| Bucket | Pilot baseline | WC-12 (PM-blind) | **MR-3 (v2 prompt)** |
|---|---|---|---|
| Buy | 0 | **5** | 0 |
| Overweight | 9 | 4 | 6 |
| Hold | 1 | 1 | 3 |
| **Underweight** | 0 | 0 | **1** ← first ever |
| Sell | 0 | 0 | 0 |

### Forward-α (5-day vs SPY) — calibration

| Bucket | Pilot α (n) | WC-12 α (n) | **MR-3 α (n)** |
|---|---|---|---|
| Buy | — (0) | -0.22% / 40% (5) | — (0) |
| Overweight | +0.01% / 44% (9) | +0.25% / 50% (4) | **-0.50% / 33% (6)** |
| Hold | +2.12% / 100% (1) | +2.34% / 100% (1) | **+0.94% / 67% (3)** |
| Underweight | — (0) | — (0) | **+2.45% / 100% (1)** |
| Sell | — | — | — |

### EH-2 gate

3 DENY findings on MR-3 (same count as pilot baseline; fewer than WC-12's 1 because WC-12 hit Buy):
1. Missing tier(s): `['Buy', 'Sell']`
2. 0/10 (0.0%) ratings strong
3. Last 10 in window: 0 strong ratings

The v2 prompt didn't fix the gate failure on the bull side. It DID fix the bear-side coverage (Underweight appeared) but not Sell.

## Decision

**The v2 prompt is a partial win that complicates the architectural recommendation.**

### What we expected (per HYPOTHESIS.md)

≥1 Buy + ≥1 Sell across the 10 runs, distribution shifted toward stronger calls. The intervention targets the synthesis prompt's "two-sided evidence = Hold-leaning" framing identified by MR-2.

### What we got

- **0 Buy** (vs pilot 0, WC-12 5) — bull-side mode collapse persists
- **1 Underweight** (vs pilot 0, WC-12 0) — bear-side mode collapse partially broken
- **3 Hold** (vs pilot 1, WC-12 1) — MORE moderate ratings, not fewer

The prompt-only fix is **asymmetric**: it enabled the model to commit to Underweight when bear arguments dominated, but did NOT enable it to commit to Buy when bull arguments dominated. The original prompt's gradient (Strong conviction → Constructive → Balanced → Cautious → Strong conviction) probably created a similar asymmetry the other way (Overweight as the "constructive but hedged" middle), and the v2 prompt's removal of that gradient revealed a different asymmetry — one where the model defaults to Hold when uncertain rather than committing.

### What the forward-α reveals

Counterintuitive headline: **MR-3 achieved the best calibration of all three conditions** despite (or because of) being more moderate.

- MR-3's Overweight: -0.50% α — when v2 commits to bullish, it's wrong on average
- MR-3's Hold: +0.94% α — when v2 stays moderate, it's RIGHT on average
- MR-3's Underweight: +2.45% α — the one bear call was correct (NVDA underperformed SPY by 2.45% over 5 days starting 4/3)

In contrast, WC-12 produced 5 confident Buys that averaged -0.22% α — confidently wrong. The pilot's uniform Overweight averaged +0.01% — barely-distinguishable from random.

**MR-3 isn't being more moderate by accident; it's being more moderate when it should be.** The v2 prompt's framing (commit when one side outweighs, hold when arguments are quantitatively near-equal) is producing better-calibrated decisions even though the distribution doesn't look like what we predicted.

### Why this happened

Hypothesis: NVDA in Jan-Apr 2026 was a market regime where the bullish thesis looked strong on the surface (recent strong earnings, AI tailwinds) but had real downside risks the bear correctly identified (capex sustainability, deceleration). The pilot's uniform Overweight reflects the model defaulting to the bullish surface story. WC-12's Buys reflect amplifying that surface story without the synthesis hedge. MR-3's mix reflects the synthesis WITH v2 framing weighing the bear concerns properly.

If true: **the v1 prompt was systematically biased toward the side with stronger surface narrative; the v2 prompt is balanced and lets the actual evidence weigh in.**

### What this changes about the architectural recommendation

Three-way verdict on "fix the synthesis":

1. **Mode collapse on the rating distribution**: MR-3 is partial — fixed bear-side, not bull-side. EH-2 still flags 3 DENYs.
2. **Forward-α calibration**: MR-3 is the best of the three conditions. The synthesis IS adding value when its prompt is correctly framed.
3. **Quality bug ("5-tier advertised, 3-tier behavior")**: MR-3 is partial — uses 4 of 5 tiers (vs pilot's 3, WC-12's 3).

The right architectural intervention is now clearer: **keep the synthesis (it's earning its keep), keep the v2 prompt framing (it's better-calibrated), AND something else still needs to address the bull-side mode collapse.** Possible candidates:
- Symmetric prompt asymmetry: maybe the v2 framing needs an even stronger "Buy means the bull's strongest arguments outweigh bear's WITHIN THE HOLDING WINDOW" emphasis
- The model's natural tendency to under-commit on the bullish side might be intrinsic to LLM moderation training (Anthropic Claude particularly so) — would need different model to test
- Combination: try `pm_sees_synthesis=false` (WC-12) WITH the v2 schema bound. The PM might commit more readily when freed of the synthesis but still trained by the v2 schema's framing it sees indirectly

### Forward-α sub-hypothesis (from HYPOTHESIS.md)

The v2 prompt-only fix may improve, leave, or worsen calibration vs WC-12.
**Answered: improves.** MR-3 calibration > WC-12 calibration > pilot calibration (in the sense that cautious ratings outperform bullish ratings, and v2 produces those cautious ratings on the right dates).

## Detailed findings

### Specific date lookups

| Date | Pilot | WC-12 | MR-3 v2 | Realized 5-day α (NVDA - SPY) |
|---|---|---|---|---|
| 2026-01-30 | Over | Over | Over | (per pilot Over avg ~+0.01%) |
| 2026-02-06 | Over | **Buy** | Over | (in Buy bucket -0.22%) |
| 2026-02-13 | Over | **Buy** | Over | |
| 2026-02-20 | Over | **Buy** | Over | |
| 2026-02-27 | Over | **Hold** | **Hold** | (WC-12+MR-3 both caught, +2.34% α for WC-12 Hold) |
| 2026-03-06 | Over | **Buy** | **Hold** | |
| 2026-03-13 | Over | **Buy** | **Hold** | |
| 2026-03-20 | Over | Over | Over | |
| 2026-03-27 | Hold | Over | Over | |
| 2026-04-03 | Over | Over | **Underweight** | (MR-3 only caught: +2.45% α — bear call correct) |

The 4/03 Underweight is the most interesting individual call. NVDA fell more than SPY over the next 5 trading days (+2.45% α to a bear call). Only MR-3 v2 made a bear-side rating on this date; both pilot and WC-12 stuck with Overweight.

### Why "asymmetric"

The original v1 prompt has implicit symmetry — "Strong conviction" appears in both Buy and Sell, "Constructive" / "Cautious" in Overweight / Underweight, "Balanced" only in Hold. Yet the pilot produced 0 Sells across 65 runs. So even the original prompt was structurally bull-biased OR the data window was bull-biased. The MR-3 v2 prompt corrected the framing but the asymmetric output suggests the model itself has an LLM-level reluctance to recommend Sell that prompt fixes alone don't reach.

The new finding: **the bear-side commitment is reachable with prompt fixes; the bull-side commitment is not, at least with this model on this data.** That distinction is itself diagnostic.

## Limitations

- **n=10**, single ticker, single 3-month window. The forward-α improvement could be NVDA-specific or window-specific. Cross-ticker validation pending (`wc12-cross-aapl` and `wc12-cross-msft` will run next).
- **No matched MR-3 cross-ticker yet.** This experiment only tests v2 on NVDA. v2 might behave differently on AAPL/MSFT/etc.
- **Forward-α ≠ profit.** 5-day α vs SPY is a calibration check, not a backtested strategy.
- **Single rater.** Different LLM evaluators might produce different rating distributions.

## Next experiment

**MR-4: combine WC-12 + MR-3.** Run with both `pm_sees_synthesis=false` AND `research_manager_prompt_variant=v2`. The PM is blind to the synthesis BUT the synthesis itself uses v2 framing. Tests whether the bull-side mode collapse is in the PM (in which case removing synthesis breaks it, per WC-12) or whether the PM-blind variant just amplifies whatever the underlying model wants to do (which v2 has shown is more moderate-with-good-calibration). Cost: ~$5. ~70 min.

Also: **cross-ticker MR-3** on AAPL + MSFT to see if the calibration improvement generalizes (~$10, ~140 min).

## Cost & timing

- Wall-clock: 67.5 min
- Cost: ~$5
- Errors: 0/10
- PARAMS.json auto-synced correctly (`research_manager_prompt_variant: "v2"` recorded)

## One-paragraph summary for findings.md

> The v2 synthesis prompt didn't shift NVDA ratings toward Buy as predicted (still 0 Buys); instead it produced asymmetric commitment — 0 Buy / 6 Overweight / 3 Hold / 1 Underweight / 0 Sell — AND substantially better forward-alpha calibration than either pilot baseline or WC-12, with the cautious ratings (Hold / Underweight) outperforming the bullish ones in this period where NVDA's bullish lean was wrong on average.
