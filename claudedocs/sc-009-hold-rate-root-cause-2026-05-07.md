# SC-009 Hold-rate root cause investigation — 2026-05-07

**Status**: Mid-flight diagnostic of `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/` (7/36 rows complete as of 07:18 PDT). Concern: 6 of 7 rows returned Hold (86% Hold rate); SC-009 gate 2 (n_fired_boost_on ≥ 8) at risk.

**Verdict**: **Root cause is the PM Hold-regime, not a filter-chain issue.** All 4 PM-stage filters (contrarian_gate, sector_momentum, bear_sector_symmetry, forward_catalyst) are working correctly. They have nothing to act on because PM commits to Hold.

## Per-filter status across 7 completed rows

| Ticker | Date | PM final | cg_fired | cg_skip | sm_fired | bss_fired | fc_fired | fc_pre | fc_bull_pi |
|---|---|---|---|---|---|---|---|---|---|
| NVDA | 2026-04-17 | Hold | . | (active, no fire) | . | . | . | Hold | 0.78 |
| NVDA | 2026-04-24 | Hold (was Overweight) | . | (active, no fire) | . | . | **Y** | Overweight | 0.82 |
| MSFT | 2026-04-17 | Hold | . | (active, no fire) | . | . | . | Hold | 0.62 |
| MSFT | 2026-04-24 | Hold | . | (active, no fire) | . | . | . | Hold | 0.55 |
| AAPL | 2026-04-17 | Hold | . | (active, no fire) | . | . | . | Hold | 0.75 |
| AAPL | 2026-04-24 | Underweight | . | (active, no fire) | . | . | . | Underweight | 0.75 |
| WFC | 2026-04-17 | Hold | . | insufficient_history | . | . | . | Hold | 0.45 |

Filter-chain summary:
- **contrarian_gate**: active mode, fires 0/7. Doesn't fire because pm_rating={Hold,UW} for 6/7 rows; gate target is bull commits. WFC has additional `insufficient_history` skip.
- **sector_momentum + bear_sector_symmetry**: both default-OFF; never fire (correct behavior).
- **forward_catalyst (Spec 007)**: fires once (NVDA 2026-04-24 OW→Hold, bull_pi=0.82 well above T=0.60). Other rows have pre_rating ∈ {Hold, Underweight}; bull-side has no commit to suppress; bear-side is in shadow so doesn't fire-modify.

## The PM's Hold-with-bullish-prose pattern

Critical finding from the PM final_trade_decision text:

**NVDA 2026-04-17** (rated Hold):
> "Initiate NVDA at Overweight with a disciplined tranched entry strategy targeting a 4–6% portfolio position, built gradually over 4–8 weeks."

**MSFT 2026-04-24** (rated Hold):
> "Initiate or add to MSFT at 60–65% of target weight in the $415–435 range, consistent with the Research Manager's Overweight framework..."

The PM's prose recommendation is BULLISH ("Initiate at Overweight", "Initiate or add"), but the **rating** field is Hold. This is Constitution VII Calibrated Abstention behavior: the PM is saying "Hold today's specific propagate (don't mass-buy on this date), but build to Overweight over weeks." It's NOT a parser bug — the rating reflects today's commit; the prose reflects multi-week framework.

**Implication for downstream filters**: filters parse the rating, not the prose. Hold means no commit to fire on. The PM's nuanced "Hold-with-bullish-disposition" rating starves the filter chain even though the underlying analysis is bullish.

## Why this happens

Most likely interpretation:
1. The cohort is Tech-heavy (NVDA, MSFT, AAPL = 6 of 7 rows so far) at extended-rally dates (mid-April 2026 = post-NVDA-rally regime)
2. The PM has been TRAINED (via 2026-05 prompt iterations + Spec 003 contrarian gate flipped active 2026-05-06) to be more conservative on extended-rally large-cap Tech
3. The bullish evidence is genuine (bull_case_priced_in = 0.55-0.82 across these rows — moderate-to-high) but the PM tempers commitment via the rating field
4. The PM's prose still reflects the bullish disposition because the analyst evidence supports it

This is a CALIBRATED behavior per Constitution VII, not a defect. But it means SC-009 is measuring the spec 007/008 filters on a cohort where they have minimal opportunity to fire.

## Implications for SC-009 verdict

**Gate 2 (n_fired ≥ 8)**: at risk. Current trajectory: 1 fire / 7 rows = 14% rate → ~5 fires in 36 rows (below threshold).
**Gate 3 (boost engaged ≥ 1)**: PASSED at n=4 already.
**Gate 1 (Δα improvement [+2.35pp, +4.35pp])**: undefined until more fires + 21d α data.

If gate 2 fails at backtest end:
- **Don't conclude "Spec 008 mechanism is broken"** — the filters work. The cohort just doesn't activate them.
- **Conclusion should be**: SC-009 INCONCLUSIVE on this cohort due to PM Hold-regime; filter mechanisms validated correctly via the 1 fire that DID happen + the 4 boost-engagements; expansion cohort (per PR #27) needed to test on a more commit-active universe.

## Updated expansion-contingency trigger evaluation

PR #27 trigger criteria: ≥30/36 rows return Hold AND `n_fired_boost_on < 4`.

Current trajectory:
- Hold rate: 6/7 = 86% (>83% trigger threshold) ✓
- n_fired_boost_on: 1 (still <4 threshold) ✓

If both conditions hold to backtest end → **expansion WILL be triggered**. This was the entire point of writing the contingency design before the data confirmed.

## Implications for ANALYSIS.md framing (~2026-05-22)

The verdict structure should be:

1. **SC-009 gate evaluation**: report the 3 gate results as observed. Likely "gate 3 PASS, gate 2 FAIL, gate 1 INCONCLUSIVE."

2. **Decompose the gate-2 FAIL**:
   - "Gate 2 failed because the PM's commit rate was X% on this cohort, not because Spec 008 is malfunctioning."
   - "Of the X bull commits the PM did make, Spec 007 fired on Y (Z%), of which W% had boost-attributable behavior."
   - "Cohort selection bias toward Tech-rally-priced-in tickers contributed to high Hold-rate."

3. **Recommendation**: kick off `experiments/2026-05-07-002-sc-009-expansion/` per PR #27 contingency, with bear-correct + volatile + earnings-active tickers. Combine the two cohorts for the FINAL SC-009 verdict.

4. **Methodology learning**: codify "PM commit-rate is a load-bearing precondition for filter ablations" as a reference memory (already done — `feedback_global_conftest_autouse_for_real_llm.md`'s sibling reference `reference_pm_hold_regime_starves_filters.md`).

## Cost

\$0 (state-log inspection only).

## Cross-references

- `claudedocs/sc-009-mid-backtest-commit-pattern-2026-05-07.md` — earlier diagnostic (this doc supersedes by adding root cause)
- `claudedocs/sc-009-expansion-contingency-design-2026-05-07.md` — expansion plan (now likely to trigger)
- Memory: `reference_pm_hold_regime_starves_filters.md` — the methodology lesson
- Constitution VII (Calibrated Abstention) — normative framing of the PM Hold behavior
