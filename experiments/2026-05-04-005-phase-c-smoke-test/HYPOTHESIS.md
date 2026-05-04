# Hypothesis: phase-c-smoke-test

**Experiment ID**: `2026-05-04-005-phase-c-smoke-test`
**Created**: 2026-05-04
**Source idea**: Phase C end-to-end validation — single propagation with second_opinion_enabled=True against real Anthropic to confirm shipped code works
**Cost estimate**: ~$2.00 (1 NVDA propagation Opus + Haiku + 1 extra Opus call for second-opinion)
**Cost tier**: T1 (free exploration, $0 – $5)

## What we're testing

End-to-end validation of the Phase C `second_opinion` module shipped in commit `5d68d33`. The module has 29 unit tests with mocks but ZERO real-LLM smoke tests. This experiment is the smoke test: one full propagation with `second_opinion_enabled=True` to verify:

1. **`with_structured_output(SecondOpinionResult)` works against Anthropic Opus** — the actual LLM produces valid SecondOpinionResult JSON
2. **`annotate_decision()` renders into final_trade_decision** — the markdown annotation appears in the saved decision
3. **PM doesn't break** — the rating is still extracted correctly; the run completes cleanly
4. **Graceful degradation paths NOT triggered in happy path** — no warnings about structured-output or invocation failure

NVDA on 2026-01-30 (first date of the 005/007 grid). Same config as 005/007 plus `second_opinion_enabled=true` override.

## Why we expect a clean smoke test

Pre-conditions are favorable:
- Anthropic Opus supports `with_structured_output` (validated by all the structured-output decision agents — research_manager, trader, portfolio_manager — using the same pattern)
- Single propagation = bounded scope; if anything breaks, the failure is localized
- Default `second_opinion_enabled = False` means no other code path needs to change

## Predicted findings

**Scenario A (clean smoke, all 4 validations pass)** — ~80%
- Run completes 1/1 with 0 errors
- Final decision markdown contains a `[Phase C second-opinion]` annotation block
- PM rating is parseable from the annotated decision
- No warnings logged about second-opinion failure

**Scenario B (LLM produces valid schema but annotation is awkward)** — ~10%
- Mechanics work but the second-opinion text reveals prompt issues (unclear tone, weak reasoning, low-quality evidence bullets)
- Iterate on the prompt in `second_opinion.py` after observing real output

**Scenario C (graceful degradation triggers)** — ~5%
- Anthropic Opus refuses or malforms the structured output
- The graceful-degradation path returns None
- Decision proceeds unannotated — the failure is exactly what the design predicted

**Scenario D (unexpected break)** — ~5%
- Pydantic validation crashes on a real LLM response edge case
- Or the annotation renders incorrectly
- Fix the bug, re-run

## Success criterion

- [ ] 1 propagation completes with 0 errors
- [ ] Final decision contains the `[Phase C second-opinion]` annotation block
- [ ] PM rating is parseable
- [ ] No warning about second-opinion failure in stderr
- [ ] Total cost ≤ $3

## Notes

- **T1 tier** ($2 estimated, well within ≤$5 ceiling)
- **Single date single ticker** (NVDA 2026-01-30) — minimum viable smoke
- **Config**: `second_opinion_enabled=true` override + standard 005/007 config
- **Forward 21d data** available; not strictly needed for the smoke test
- **Memory log fresh**

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (clean smoke) | Phase C confirmed end-to-end. RESEARCH_FINDINGS gets a "Phase C validated" note. Ready to ship Phase C as opt-in feature. |
| Scenario B (output quality issue) | Iterate on the second_opinion prompt; smoke-test again after edit. |
| Scenario C (graceful degradation) | Phase C ships as designed but is non-functional in practice on Opus. Document the failure mode; investigate provider compatibility. |
| Scenario D (unexpected break) | Fix the bug; re-smoke-test. |

## Related experiments

- **Commit `5d68d33`**: Phase C shipped — `tradingagents/agents/utils/second_opinion.py` + 29 unit tests + PM wiring + 3 config flags. Default disabled.
- **RESEARCH_FINDINGS Q5**: original divergent reasoning that motivated asymmetric handling
- **Constitution Principle VII**: this smoke test does NOT alter calibration claims — Phase C is advisory only, never modifies PM rating
