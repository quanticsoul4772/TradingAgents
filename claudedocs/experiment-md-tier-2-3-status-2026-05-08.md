# EXPERIMENT.md Tier 2/3 status survey

**Date**: 2026-05-08
**Cost**: $0 (corpus survey, no LLM calls)
**Purpose**: Update EXPERIMENT.md Tier 2/3 status against the 27-experiment corpus + identify the highest-leverage untouched candidate for the next experimental arc.

## Tier 1 — original "would do tomorrow" set (FINAL: all done or absorbed)

| Item | Status | Notes |
|---|---|---|
| MR-1 (contradiction analysis on bull/bear) | ✅ DONE | `experiments/2026-05-02-001-mr1-contradiction/` |
| WC-12 (PM blind to debate) | ✅ DONE × 3 variants | `experiments/2026-05-02-002-wc12-pm-blind/` + `005-wc12-cross-aapl/` + `006-wc12-cross-msft/` |
| EH-2 (rating distribution gate) | ✅ ABSORBED | Spec 003 contrarian gate (active @ 80th percentile) is the production-grade form |
| WC-11 (order randomization) | ⚠️ NOT YET | Original Tier 1; deferred. Cost ~$10 if pursued. Lower priority post-Spec 003 (gates for first-speaker effects via filter portfolio) |

## Tier 2 — original "medium investment, medium signal" set (FINAL: 1 of 4 done)

| Item | Status | Notes |
|---|---|---|
| **BR-1** (value-function — single model emits rating distribution, no debate) | ⚠️ **PARTIAL** | `experiments/2026-05-03-003-single-call-baseline-nvda/` + `004-single-call-baseline-aapl/` exercised the "no-debate single-LLM-call" angle but used FREE-TEXT rating output, not the BR-1-specific `scoreAllRatings()` distribution emission. **The full BR-1 (rating distribution Pydantic schema + score-then-pick) is NOT yet tested.** |
| MR-3 (reasoning_decision weighted scoring instead of free-text PM) | ✅ DONE | `experiments/2026-05-02-004-mr3-synthesis-v2/` shipped the v2 prompt variant |
| **WC-10** (continuous scalar rating, [-1, +1] float instead of categorical) | ❌ **UNTOUCHED** | NOT in any HYPOTHESIS.md, script, or claudedoc. Tests core categorical-bottleneck hypothesis: does the 5-tier scale itself drive mode collapse to Hold? Cost ~$20. |
| **WC-2** (multi-temporal debate — same analysts at 5d/30d/90d/1yr lookbacks) | ❌ **UNTOUCHED** | NOT in any HYPOTHESIS.md, script, or claudedoc. Tests time-horizon bias hypothesis: does the implicit time-frame assumption shape calibration? Cost ~$30 (4× run cost on small grid). |

## Tier 3 — original "bigger swing" set (FINAL: 0 of 4 fully done; 2 partially absorbed)

| Item | Status | Notes |
|---|---|---|
| EH-1 (hash-chained event log) | ⚠️ PARTIALLY ABSORBED | Spec 002 signal-lifecycle pipeline (Phases 0-2.5) provides cache + event-log primitives but not full hash-chaining or replay-rebuild. The full EH-1 vision (Grafana panels + datasette + 6 initial dashboards) is unimplemented. |
| BR-3 (structured signaling instead of natural-language debate) | ❌ UNTOUCHED | Pydantic schemas for analyst output exist (analyst factories ship structured-output) but the bull/bear debate itself is still natural-language. BR-3 would replace debate prose with `bull.confidence=0.7 / bear.contradiction=[3,7]` shared-array signals. Significant engineering. |
| WC-4 (5 debate topologies in parallel) | ❌ UNTOUCHED | Round-robin / all-vs-all / hierarchical / swarm / single-model-with-self-debate. Cost ~$50. |
| BS-2 (local Ollama for high-volume agents) | ⚠️ PARTIALLY ABSORBED | Ollama provider already exists in the framework (`tradingagents/llm_clients/`). Operator can opt to local models via config. Full BS-2 (Qwen2.5-Coder for analysts + Sonnet for PM) is not the production default but is operator-flippable. |

## Cross-cutting observations

1. **Filter portfolio approach displaced several Tier 1/2 ideas**. EH-2 morphed into Spec 003 (statistically rigorous gate vs naive distribution check). MR-3 became `research_manager_prompt_variant` config knob. The filter-portfolio paradigm proved more durable than per-experiment toggles.

2. **Single-call architectural baseline changed BR-1's information value**. The `scripts/single_call_baseline.py` already exists and the 4 single-call experiments run. Per CLAUDE.md, the single-call baseline tested the "framework architecture vs single LLM call on same inputs" question. BR-1 specifically would extend this with a structured rating-distribution output schema (vs free-text), but the architectural-premise question is largely answered: single calls and the multi-agent framework produce similar ratings (corpus IC -0.489 finding).

3. **WC-10 + WC-2 are the highest-information-value untouched candidates** because they test fundamentally different hypotheses than the filter-portfolio work has explored:
   - **WC-10** tests the categorical-output bottleneck hypothesis. If the framework's mode collapse is driven by the 5-tier rating scale forcing discrete commitment, a continuous scalar [−1, +1] output would surface signal that the categorical bucket erases. This is a CORE architectural question that the existing experiments don't address.
   - **WC-2** tests the time-horizon assumption hypothesis. If different lookback windows produce different ratings on the same date, the implicit time-frame assumption is the hidden bias. Empirically: Q3/Q4 2025 vs Q1 2026 cross-period validation already showed period-conditional alpha; WC-2 would distinguish whether that's MARKET regime (period-conditional) vs ANALYSIS regime (lookback-conditional).

## Recommendation: WC-10 (continuous scalar rating) as the next experimental arc

**Why WC-10 over WC-2**:

- **Lower cost** (~$20 vs ~$30)
- **Cleaner mechanistic test**: removes the categorical scale, holds everything else constant. Single intervention, single hypothesis.
- **Higher information**: the 5-tier scale is a direct architectural choice; testing continuous scalar gives a clean answer about whether the categorical bottleneck causes mode collapse.
- **Aligns with current research thread**: Constitution VII (Calibrated Abstention is a Valid Output) says the Hold-collapse is calibrated. WC-10 tests an alternative framing: maybe the COMPLETE distribution of confidence is the calibrated output, and the 5-tier discretization is throwing away information.

**Pre-WC-10 design questions** (would shape spec.md if pursued):

1. **Rating schema change scope**: Pydantic `PortfolioDecision.rating` field type changes from `PortfolioRating` enum to `float in [-1, +1]`. Is the SignalProcessor (deterministic regex extraction over 5-tier scale) replaceable with a continuous-aware extractor? Probably yes via a new schema variant.
2. **Filter portfolio interaction**: All 9 production filters operate on the 5-tier scale (e.g., `pre_rating in {Underweight, Sell}`). WC-10 would need to either (a) bin the scalar to the 5-tier scale for filter compatibility, or (b) ablate filters during the WC-10 experiment and compare unfiltered scalar vs filtered categorical baselines.
3. **Realized-α attribution**: how to compare WC-10 scalar ratings to existing 5-tier corpus? Options: (a) bin scalar to 5-tier ex-post via thresholds and compare bucket means, (b) compute correlation between scalar and realized α directly, (c) both.
4. **Test-grid size**: 20 dates × 1-3 tickers? Or 10 dates × 5 tickers? Smaller grid keeps cost down; SC-003 50-ticker pattern is too expensive for a hypothesis-test arc.

**Pre-spec retrospective gate** (per Constitution VIII v1.4.1): WC-10 is a structural experiment, not a filter, so the v1.4.0/v1.4.3 forward-catalyst-class gates don't apply. But Constitution II (One Experiment Per Change) discipline applies — single intervention, single hypothesis, single deliverable.

## Recommendation: WC-2 (multi-temporal debate) as the alternative if regime-vs-lookback distinction is the higher-priority question

If the operator considers the period-conditional alpha finding (Q4 2025 negative outlier vs Q1 2026 positive) more pressing than the categorical-bottleneck question, WC-2 is the right arc. Both are valid; WC-10 is recommended primarily on cost + cleanness grounds.

## What this survey is NOT

- This is NOT a commit to launching WC-10 or WC-2.
- This is NOT a spec.md or feature description draft.
- This is the planning artifact that lets the operator decide whether to advance Tier 2 work or continue with the deferred-gate-only mode (waiting for Spec X-1 SC-009 ~2026-05-15 / SC-010 n≥30 / Spec 008 SC-009 ~2026-05-22+).

## What's NOT recommended for the next arc

- **WC-11 (order randomization)**: would surface first-speaker effects, but the filter-portfolio approach already mitigates several order-effect risks (filters fire at PM stage, after debate). Lower information per cost.
- **EH-1 (hash-chained event log)**: significant engineering with no new research signal. Spec 002 already provides cache primitives. Deferred.
- **BR-3 (structured signaling)**: significant prompt engineering + uncertain how to score whether structured signals improve calibration. Deferred.
- **WC-4 (5 debate topologies)**: ~$50 cost for an exploratory comparison; at this stage the filter-portfolio approach has higher leverage than topology-space exploration.

## Sibling docs

- `docs/EXPERIMENT.md` — original brainstorm + Tier 1/2/3 + Backlog filter (2026-05-01)
- `RESEARCH_FINDINGS.md` — synthesis across the 27-experiment corpus + 5 open questions
- `ROADMAP.md` — forward-looking exploration map; Open Work section currently calendar-anchored only
- `CLAUDE.md` — `Filter portfolio` section + 9 production filters reference
- `experiments/2026-05-03-003-single-call-baseline-nvda/` — closest existing experiment to BR-1 (architecturally adjacent)
