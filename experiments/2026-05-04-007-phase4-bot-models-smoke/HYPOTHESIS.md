# Hypothesis: phase4-bot-models-smoke

**Experiment ID**: `2026-05-04-007-phase4-bot-models-smoke`
**Created**: 2026-05-04
**Source idea**: Spec 001 Phase 4 end-to-end validation — single propagation with `bot_models` override against real Anthropic to confirm per-bot LLM routing works in a live graph
**Cost estimate**: ~$0.50 (1 NVDA propagation; market analyst on Sonnet, all other bots on defaults)
**Cost tier**: T1 (free exploration, $0 – $5)

## What we're testing

End-to-end validation of the Spec 001 Phase 4 `BotLLMFactory` shipped in commits `85ebdb8` (initial) + `2a55c01` (wrapper-vs-LLM bug fix). The factory now has 18 unit tests + 3 live-construction integration tests, but **zero live-propagate validation**. This experiment closes that gap: one full propagation with a single per-bot override and one without, comparing both for completeness.

The single-override config: `bot_models = {"market": "claude-sonnet-4-6"}`. The market analyst bumps from default Haiku → Sonnet; all other 11 bots use the framework defaults (Haiku for the 9 quick bots, Opus for research_manager + portfolio_manager). This is the minimum-viable test that exercises both code paths in a single run:

1. The **override path**: `_get_or_create_client` builds a real Sonnet client, caches it, returns the unwrapped LangChain LLM
2. The **default-fallback path**: 11 bots ask the factory for an LLM, get the framework defaults

What we want to verify:
1. **`BotLLMFactory: instantiated anthropic/claude-sonnet-4-6 for per-bot routing`** log line appears (proof the override path was taken)
2. **Propagate completes** — no crash at `llm.bind_tools(tools)` (the bug we caught with mocks-can't-catch-this; integration tests confirmed at construction level, this confirms at runtime)
3. **Rating extractable** — final_trade_decision parses to one of the 5 canonical ratings
4. **Other bots unaffected** — no warnings about wrong model for default-route bots

NVDA on 2026-01-30 (same date as 005/007 baseline). Same overall config as 005/007 plus the `bot_models` override.

## Why we expect a clean smoke test

- Phase 4 unit tests + live-construction integration tests cover the wiring; only runtime invocation remains untested
- The wrapper-vs-LLM bug (caught 2026-05-04) was the structural blocker; with that fixed, the routing should "just work"
- Sonnet for market-analyst is a known-good combination — Sonnet 4.6 supports tool-use ReAct loops
- Single date single ticker = bounded blast radius

## Predicted findings

**Scenario A (clean smoke, all 4 validations pass)** — ~85%
- Run completes 1/1 with 0 errors
- Log contains `BotLLMFactory: instantiated anthropic/claude-sonnet-4-6 for per-bot routing` exactly once
- Final decision parses to a canonical rating
- Phase 4 declared end-to-end-validated; the "wired-but-not-validated" caveat in RESEARCH_FINDINGS is removed

**Scenario B (Sonnet rejects effort kwarg)** — ~10%
- If `anthropic_effort` is set in config (even just from CLI default), the factory forwards it to the Sonnet client. Sonnet 4.6 may not accept `effort` (per CLI help: "Sonnet/Haiku reject it").
- Mitigation: omit `--anthropic-effort` flag; CLI default is empty so no kwarg gets forwarded.

**Scenario C (graceful degradation triggered)** — ~3%
- Sonnet structured-output behavior differs from Opus in some bot's `with_structured_output` chain
- Decision agents that hit Sonnet (none in this config — Sonnet is only on market analyst, which uses tool-use not structured-output) shouldn't be affected, but cross-check

**Scenario D (unexpected break)** — ~2%
- Some interaction between Phase 4 routing and the existing graph compilation / LangGraph caching
- Fix the bug, re-run

## Success criterion

- [ ] 1 propagation completes with 0 errors
- [ ] Log captures the BotLLMFactory instantiation line for `claude-sonnet-4-6`
- [ ] Final decision contains a parseable rating
- [ ] No warnings about model rejection or factory failure
- [ ] Total cost ≤ $1

## Notes

- **T1 tier** ($0.50 estimated, well within ≤$5 ceiling)
- **Single date single ticker** (NVDA 2026-01-30) — minimum viable smoke
- **Config**: `bot_models={"market": "claude-sonnet-4-6"}` on top of standard 005/007 config
- **No `anthropic_effort`** — explicitly omitted to avoid Sonnet/Haiku rejection
- **Memory log routed to experiment dir** — keep main memory log clean

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (clean smoke) | Phase 4 confirmed end-to-end. RESEARCH_FINDINGS updated; "wired-but-not-validated" caveat removed. |
| Scenario B (effort rejection) | Document the constraint in role_models docstring: `anthropic_effort` only forwards to Opus models. |
| Scenario C (graceful degradation) | Investigate which Sonnet path differs; document in role_models. |
| Scenario D (unexpected break) | Fix the bug; re-smoke-test. |

## Related work

- **Commit `85ebdb8`**: Phase 4 shipped — `BotLLMFactory` + GraphSetup integration + 18 unit tests
- **Commit `2a55c01`**: wrapper-vs-LLM bug fix + 3 live-construction integration tests
- **RESEARCH_FINDINGS Spec 001 Phase 4 section**: documents the wiring + the remaining live-propagate gap (which this experiment closes)
- **Constitution Principle VII (Calibrated Abstention)**: this smoke does not change the framework's calibration story; it's purely a wiring validation
