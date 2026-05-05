# Analysis: phase4-bot-models-smoke

**Experiment ID**: `2026-05-04-007-phase4-bot-models-smoke`
**Run date**: 2026-05-04
**Status**: ✅ **Scenario A — clean smoke**, Phase 4 end-to-end validated

## Result

| Metric | Value |
|---|---|
| Propagations completed | 1/1 |
| Errors | 0 |
| Final rating | **Overweight** |
| Run seconds | 512.15 (8.5 min) |
| Override path log line | `BotLLMFactory: instantiated anthropic/claude-sonnet-4-6 for per-bot routing` |
| Override path taken | True |
| Cache populated | True (`('anthropic', 'claude-sonnet-4-6')` present after construction) |
| Estimated cost | ~$0.50 (Opus PM + Opus research_manager + Sonnet market analyst + Haiku for the 9 other quick bots) |

## All success criteria met

- [x] 1 propagation completes with 0 errors
- [x] Log captures the BotLLMFactory instantiation line for `claude-sonnet-4-6` (exactly once)
- [x] Final decision contains a parseable rating (`Overweight`)
- [x] No warnings about model rejection or factory failure
- [x] Total cost ≤ $1

## Comparison to baseline

Same ticker, same date, same overall config — only `bot_models = {"market": "claude-sonnet-4-6"}` added.

| Experiment | NVDA 2026-01-30 rating | Market analyst model | Run seconds |
|---|---|---|---|
| `2026-05-03-005-opus47-swap-nvda` | Overweight | Haiku (default quick) | 382.77 |
| `2026-05-03-007-opus47-30pair-mixed` | Overweight | Haiku (default quick) | 463.87 |
| **`2026-05-04-007-phase4-bot-models-smoke`** | **Overweight** | **Sonnet (Phase 4 override)** | **512.15** |

Same rating across all three, even with the market analyst on a different model. n=1 doesn't tell us whether bumping market → Sonnet would systematically change rating distribution; that's a separate, larger experiment. But the rating-stability is at least consistent with the framework's known low sensitivity to single-bot model perturbation (mode collapse to OW on bull-regime tickers).

Run-time +30% vs the 005 baseline — Sonnet is slower than Haiku for the market analyst's tool-using ReAct loop. Modest, expected.

## What this validates

The full Phase 4 wiring works end-to-end against real Anthropic:

1. **`BotLLMFactory._get_or_create_client` builds a real `ChatAnthropic`** for `claude-sonnet-4-6` and caches it (verified at construction time + via the post-run cache check).
2. **`GraphSetup._llm_for("market")` routes through the factory** and returns the unwrapped LangChain LLM (the one with `bind_tools`, not the wrapper). Without the wrapper-vs-LLM bug fix in commit `2a55c01`, this propagate would have crashed at `chain = prompt | llm.bind_tools(tools)` in `tradingagents/agents/analysts/market_analyst.py:88`.
3. **The market analyst's tool-using ReAct loop completes** with the override model — Sonnet handled the same indicator-selection + tool-call flow that Haiku handles by default.
4. **The other 11 bots transparently use the framework defaults** — no warnings, no failures, no need for explicit fallback logic in the analyst factories.
5. **The full graph propagates through to a parseable PM rating** — the override doesn't disrupt anything downstream of the market analyst (bull/bear debate → research_manager → trader → risk debate → PM).

## What this does NOT validate

- **Rating distribution shift under per-bot model changes** — n=1 can't measure whether Sonnet-on-market vs Haiku-on-market changes the framework's decisions systematically. Would need ≥10 propagates × matched baseline.
- **Multi-bot overrides** — only one bot was overridden. The factory cache + per-(provider, model) keying is unit-tested, but the multi-override live path is not separately exercised. Low risk; the failure modes would have showed up in the unit tests.
- **`anthropic_effort` forwarding to non-Opus models** — config omitted `anthropic_effort` per HYPOTHESIS Scenario B. The factory's effort-forwarding code path is unit-tested (kwargs passed correctly) but not live-tested against a Sonnet/Haiku endpoint that might reject `effort`. Documented constraint, not a gap.
- **Cost-savings claim** — bumping market → Sonnet *increased* cost slightly (Sonnet > Haiku $/token) and run-time. The Haiku-for-quick + Opus-for-deep cost-savings story is the inverse case (currently default behavior — no per-bot override needed). The interesting per-bot-routing application is the *other* direction: bumping a *deep* bot up further (e.g. an Opus-tuned PM with extra effort), which is left for future experiments.

## Constitution compliance

- **Principle I (Save Everything)**: HYPOTHESIS, PARAMS, drive.py, run.sh/run.ps1, results.csv, ANALYSIS.md all in place.
- **Principle II (One Experiment Per Change)**: only the Phase 4 wiring is being validated here; no other config or code change is bundled in. The drive.py is a one-purpose validator that doesn't extend shared infrastructure.
- **Principle III (Stay Cheap)**: estimated $0.50, ran within budget; total < $1.
- **Principle VII (Calibrated Abstention)**: this experiment does not change the framework's calibration story. Phase 4 is wiring, not a modification to decision logic.

## Decision

Phase 4 declared **end-to-end validated**. Update RESEARCH_FINDINGS Spec 001 Phase 4 section to remove the "wired but not yet validated against a live propagate" caveat. Phase 4 is now ready for operator use:

```python
config["bot_models"] = {"<bot_id>": "<model_name>", ...}
```

with the documented constraint that `anthropic_effort` only safely forwards to Opus models. Future cost-tier experiment (Haiku-for-quick + Opus-for-deep with per-bot tuning) can build on this foundation.
