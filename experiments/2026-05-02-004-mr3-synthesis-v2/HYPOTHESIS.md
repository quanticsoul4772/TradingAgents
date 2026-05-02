# Hypothesis: mr3-synthesis-v2

**Experiment ID**: `2026-05-02-004-mr3-synthesis-v2`
**Created**: 2026-05-02
**Source idea**: MR-3 (per MR-2 finding)
**Cost estimate**: ~$5 (10 NVDA propagations × ~$0.50 each, ~70 min)

## What we're testing

MR-2 identified that the Research Manager's synthesis prompt + the `ResearchPlan` schema both literally instruct the model to map "two-sided evidence" → Hold-leaning ratings, and MR-1 confirmed two-sided evidence exists in 100% of debates. The prediction: editing those instructions to decouple "two-sided evidence" from "Hold-leaning" should shift the synthesis distribution toward more Buy/Sell ratings — which the PM should then propagate.

The MR-3 fix is a **prompt + schema variant** controlled by config flag `research_manager_prompt_variant`:
- `default` / `v1` = original behavior
- `v2` = the MR-3 rewrite

The v2 rewrite changes:
1. **Rating scale definitions** in the prompt: replaces the "Strong conviction" → "Constructive" → "Balanced" gradient with criteria phrased in terms of *which side outweighs* + *what bears on the holding window*.
2. **The framing instruction** in the prompt: explicitly says "Two-sided evidence is the NORM in stock debates and does NOT by itself warrant Hold."
3. **The `ResearchPlanV2.recommendation` field description**: matches the prompt framing (otherwise the schema's "reserve Hold for balanced" instruction would partially cancel the prompt fix).

## Predicted finding

Synthesis-step rating distribution shifts from the pilot's:
- Buy: 1.5%, Overweight: 43.1%, Hold: 36.9%, Underweight: 18.5%, Sell: 0%

To something like:
- Buy: 15-30%, Overweight: 30-40%, Hold: 5-15%, Underweight: 15-25%, Sell: 5-15%

Specifically: **at least 1 Buy and 1 Sell across the 10 NVDA runs** (pilot had 0 of either). PM ratings should propagate the shift, producing more Buy than the original pilot but less than WC-12 (which got 5/10 Buy by removing synthesis entirely).

## Forward-alpha sub-hypothesis

The WC-12 follow-up showed stronger ratings ≠ better calibrated. MR-3 might do better because:
- The prompt-level fix preserves the synthesis as a reasoning step
- The synthesis can still hedge AGAINST stronger calls when the evidence genuinely warrants it
- We're not just removing a moderating force; we're recalibrating it

OR MR-3 might NOT help calibration because:
- The underlying analyst inputs are still flawed (per WC-12 forward-α)
- Better-distributed labels on bad signal = same noise, just relabeled

This experiment should answer: does the prompt fix improve calibration, leave it unchanged, or make it worse?

## Success criterion

- [ ] 10 NVDA propagations complete with `research_manager_prompt_variant=v2`
- [ ] PARAMS.json auto-synced with the override
- [ ] Synthesis-step distribution computed (extracted from JSON state logs) — compare to pilot baseline + WC-12
- [ ] PM-step distribution computed — compare to pilot + WC-12
- [ ] EH-2 gate output recorded (does v2 pass the rating-distribution gate that pilot+WC-12 fail?)
- [ ] Forward-alpha computed and compared to pilot + WC-12
- [ ] Decision: prompt fix sufficient / partially sufficient / insufficient

## Notes

- Same 10 NVDA dates as WC-12 (2026-01-30 through 2026-04-03 weekly Fridays). Three-way comparison: pilot baseline / WC-12 (synthesis-blind) / MR-3 (synthesis-v2).
- This is the FIRST experiment that tests a *constructive* fix rather than a diagnostic strip-down. WC-12 removed the synthesis; MR-3 redesigns it. If MR-3 works, we have a real architectural improvement, not just a confirmed problem.

## Related experiments

- **MR-1** (2026-05-02-001) — debates are real two-sided
- **MR-2** (2026-05-02-003) — diagnosed prompt+schema cause, prescribed fix
- **WC-12** (2026-05-02-002) — ablation: removing synthesis breaks mode collapse
- **WC-12 forward-α** (in WC-12 ANALYSIS.md) — broken mode collapse but bad calibration
- **Future MR-4** — re-run the WC-12 PM-blind variant with v2 schema to see whether the PM still committed to Buy as often when the upstream analysis was the same. Would tease apart synthesis-quality vs synthesis-presence.
