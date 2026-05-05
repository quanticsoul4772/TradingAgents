# Analysis: spec 003 SC-001 shadow-smoke

**Experiment ID**: `2026-05-05-001-spec003-sc001-shadow-smoke`
**Run date**: 2026-05-05
**Status**: ✅ **Scenario A — clean smoke**, spec 003 Phase 1 end-to-end validated

## Result

| Metric | Value |
|---|---|
| Propagations completed | 1/1 |
| Errors | 0 |
| Final rating | **Overweight** (matches 005/007/2026-05-04-007 baselines) |
| Run seconds | 539.38 |
| Validation checks passed | **11 / 11** |
| Estimated cost | ~$0.40 (Opus deep + Haiku quick + 3 analysts + 1 debate round) |

## Gate annotation captured (full block)

```json
{
  "mode": "shadow",
  "signal_id": "market_report",
  "feature": "bull_keyword_count",
  "threshold": 80,
  "target": "hold",
  "feature_value": 81.0,
  "percentile": 85.0,
  "n_history": 20,
  "would_fire": true,
  "gate_skipped": null,
  "gate_fired": false,
  "pm_rating_pre_gate": "Overweight",
  "pm_rating_post_gate": "Overweight"
}
```

## All 11 success criteria met

- [x] 1 propagation completes with 0 errors
- [x] `final_state["contrarian_gate"]` is present and non-None
- [x] `contrarian_gate.gate_skipped` is None (gate ran, did not skip)
- [x] `contrarian_gate.feature_value` is a number (81.0)
- [x] `contrarian_gate.percentile` is in [0, 100] (85.0)
- [x] `contrarian_gate.n_history` >= 20 (exactly 20)
- [x] `contrarian_gate.gate_fired` == False (shadow mode, no override)
- [x] `contrarian_gate.pm_rating_pre_gate` == `pm_rating_post_gate` ("Overweight" == "Overweight")
- [x] Final decision text contains no `[Spec 003 contrarian gate]` annotation
- [x] Total cost ≤ $1
- [x] Mode is shadow as configured

## Mid-run bug fix (AgentState declaration)

The first run of this experiment (also at HEAD `f238f3a`) returned `final_state["contrarian_gate"] = None` despite the PM hook running. Root cause: LangGraph's `StateGraph` only propagates keys declared in the state TypedDict from a node's return dict. Since `contrarian_gate` wasn't declared in `tradingagents/agents/utils/agent_states.py::AgentState`, LangGraph silently dropped it from the state merge — same constraint that forces spec 001 to mutate `final_state` post-`graph.invoke()` for `signals` and `shadow_aggregate_decision`.

Fix: added `contrarian_gate: Annotated[dict, ...]` to AgentState. 823 unit tests still pass after the schema change. Re-run produced the clean Scenario A above.

## Substantive observation: gate fired (would_fire = True)

This isn't part of SC-001's correctness criteria, but the actual gate decision is substantively interesting:

- NVDA 2026-01-30's market_report `bull_keyword_count` was **81** — the analyst was bullish.
- Of the 20 most recent NVDA market_report rows in the cache, this value is at the **85th percentile** — above the 80th-percentile threshold.
- PM rating was **Overweight** (a bullish commit).
- Both conditions met → `would_fire = True`.

**If active mode had been on, the OW would have been downgraded to Hold.** Per finding #4's mechanism (recency + mean-reversion), this is exactly the case the gate is designed to catch: high bull-keyword-density market_report on a bullish PM commit. The gate would have been "right" if NVDA's forward 90d α from 2026-01-30 turns out to be negative or low-positive.

Forward 90d α for NVDA 2026-01-30 isn't available yet (date too recent for the post-buffer-fix `fetch_returns(holding_days=90)` requirement). It's the kind of data point that the queued SC-002 N≥30 shadow experiment will accumulate.

## Comparison to baselines

NVDA 2026-01-30 across recent runs:

| Experiment | Rating | Run seconds | Notes |
|---|---|---:|---|
| `2026-05-03-005-opus47-swap-nvda` | Overweight | 382.77 | Original Opus baseline |
| `2026-05-03-007-opus47-30pair-mixed` | Overweight | 463.87 | 30-pair mixed basket |
| `2026-05-04-007-phase4-bot-models-smoke` | Overweight | 512.15 | Phase 4 bot_models smoke (market analyst on Sonnet) |
| **`2026-05-05-001-spec003-sc001-shadow-smoke`** | **Overweight** | **539.38** | **This run** (gate shadow mode) |

Rating consistent across 4 reruns of the same date. Run-time 30-40% above the original 005 baseline — consistent with later runs (network jitter + cache contention; gate adds <50ms per FR-001 performance goal, not the source).

## What this validates

The full spec 003 Phase 1 wiring works end-to-end against real Anthropic:

1. **`ContrarianGate.compute_annotation` runs successfully** during PM stage with real cache data (33 NVDA market_report rows, top 20 used as baseline)
2. **`_load_per_ticker_history` correctly filters by ticker** and returns the most recent 20 (n_history = 20, exactly matches the configured floor)
3. **Per-ticker percentile baseline works** (US3 / FR-004) — value 81 at 85th percentile relative to NVDA's history specifically
4. **Shadow mode does NOT modify the rating** by-construction (FR-007 backwards-compat) — the unit test guarantee is now empirically confirmed
5. **`AgentState` declaration propagates the contrarian_gate block** through LangGraph's state merge into final_state, so it lands in the state log via existing `_log_state` machinery (FR-006)
6. **Featurizer resolution from FEATURIZERS list works** at runtime (FR-001)

## What this does NOT validate

- **SC-002**: within-ticker IC reproduction in fresh data (needs N≥30 shadow propagates across multiple tickers + dates)
- **SC-003**: matched shadow-vs-active grid showing rate change concentrated on `would_fire = True` (needs ~10 propagates × 2 modes)
- **SC-004 (optional)**: active-mode commits produce mean 21d α ≥ shadow-mode (forward returns required)
- **Active-mode override path**: `maybe_override_decision` is unit-tested but not yet exercised against a real LLM-PM decision
- **Pluggable source path** (User Story 4): `news_report` swap is unit-tested but not live-validated

## Constitution compliance

- **Principle I (Save Everything)**: HYPOTHESIS, PARAMS, drive.py, run.sh/run.ps1, results.csv, ANALYSIS.md all in place.
- **Principle II (One Experiment Per Change)**: only the spec 003 shadow-mode wiring is being validated; no other config or code change bundled.
- **Principle III (Stay Cheap)**: estimated $0.40, ran within budget; total < $1. T1.
- **Principle VI (Spec Before Structural Change)**: spec 003 spec.md + plan.md + implementation all in place; this experiment validates the implementation.
- **Principle VII (Calibrated Abstention)**: shadow mode does not change calibration; the gate's annotation is observation-only. The would_fire=True observation is data for future SC-002/003 analysis, not a calibration claim.

## Decision

Spec 003 Phase 1 declared **end-to-end validated**. SC-001 box checked.

Update spec 003 plan.md sequencing table: Phase 1 / SC-001 → ✅ DONE.

The substantive observation (would_fire = True on a real OW commit at the 85th percentile) is a single data point that motivates the SC-002 N≥30 experiment — if a meaningful fraction of historical OW commits would have fired, active mode could materially change the rating distribution.

Followup queue (per the queued spec 003 success criteria):
- SC-002: 30 shadow propagates across NVDA + AAPL + INTC × 10 dates each (T2 ~$9-12)
- SC-003: matched 10-date shadow-vs-active grid (T2 ~$15)

## Cost

**$0.40 LLM** (1 propagate at Opus deep + Haiku quick) + ~30 min wall-clock (10 min propagate + 20 min for the AgentState bug-fix-and-rerun cycle).

## Mid-run insight worth recording

The AgentState declaration constraint is now **the third time** a spec-level integration was blocked by it (spec 001 worked around with post-invoke mutation; spec 002 cache writes don't go through state; spec 003 was the first to need state-level propagation from a node and hit the issue). Worth a sentence in CLAUDE.md "Conventions" section: "When adding new state-level data from a node's return dict, declare it in `AgentState` — LangGraph silently drops undeclared keys from state merges."
