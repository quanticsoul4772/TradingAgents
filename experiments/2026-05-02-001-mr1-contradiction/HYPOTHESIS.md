# Hypothesis: mr1-contradiction

**Experiment ID**: `2026-05-02-001-mr1-contradiction`
**Created**: 2026-05-02
**Source idea**: MR-1 (from `docs/EXPERIMENT.md`)
**Cost estimate**: ~$3-5 (Haiku 4.5, 65 pairs × ~10k tokens each)

## What we're testing

Given the 65 saved bull/bear debate pairs from the original pilot (in
`~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<date>.json`,
fields `investment_debate_state.bull_history` and `investment_debate_state.bear_history`),
classify each pair into one of:

- **REAL_CONTRADICTION** — bull and bear identify the same specific claims and reach
  opposite conclusions on them. (e.g., bull says "P/E of 32 is justified by 60% data-center
  growth"; bear says "P/E of 32 ignores cyclical-peak earnings risk".)
- **PARALLEL_MONOLOGUE** — bull and bear argue about *different things* that don't
  intersect; no overlapping claims to actually contradict. (e.g., bull talks about
  Blackwell ramp, bear talks about regulatory risk; both could be true.)
- **PARTIAL_OVERLAP** — some shared claims with opposite conclusions, but the bulk
  of each side's argument doesn't engage the other.
- **STRAWMAN** — one side characterizes the other's position inaccurately and rebuts
  the misrepresentation rather than the actual argument.

## Why we expect mostly PARALLEL_MONOLOGUE

The pilot's mode-collapse finding (0 Buys, 0 Sells across 65 runs) is consistent
with debates that don't actually disagree — if bull and bear are talking past each
other, the synthesizer (Research Manager) has no genuine disagreement to resolve
and defaults to moderate ratings. **Predicted distribution**: at least 50%
PARALLEL_MONOLOGUE, fewer than 25% REAL_CONTRADICTION.

If this prediction holds, it shifts the diagnosis of TradingAgents' mode collapse
from "the rating logic is broken" to "the debate structure is theatrical" — which
has different implications (the architectural alternative is value-function-style
single-model decisions per battlecode2026 ratbot6, not just better PM prompting).

If the prediction is **wrong** (most pairs are REAL_CONTRADICTION) then the debate
DOES surface real disagreement and the mode collapse must be located downstream
(at the Research Manager synthesis or the Portfolio Manager final call).

## Success criterion

- [ ] Per-pair classification recorded for all 65 pairs (or documented reason for
      exclusion if any fail)
- [ ] Aggregate distribution computed (% REAL_CONTRADICTION / PARALLEL_MONOLOGUE /
      PARTIAL_OVERLAP / STRAWMAN)
- [ ] Per-ticker breakdown (do tech stocks debate differently than financials?)
- [ ] At least 3 illustrative pair-level excerpts captured in ANALYSIS.md so the
      classification methodology is auditable
- [ ] Decision recorded: confirms or refutes the mode-collapse-via-parallel-monologue
      hypothesis

## Notes

- Originally planned to use `mcp-reasoning_contradiction` per `docs/EXPERIMENT.md`
  Tier 1, but the mcp-reasoning Rust server doesn't expose a direct contradiction
  tool. Closest fits (`reasoning_detect`, `reasoning_relate`) target single-document
  fallacy detection or session-level relationship analysis, not pairwise contradiction
  scoring. Switched to direct Anthropic structured-output call against a rubric for
  honest semantics.
- Bull/bear histories are 17k-22k chars each, so per-pair token cost is non-trivial.
  Haiku 4.5 is sufficient for this classification task (the rubric is well-defined).
- This experiment doesn't change the framework. It's pure analysis on existing data.

## Related experiments

None yet. This is the foundational debate-dynamics finding.
