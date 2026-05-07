# Implementation Plan: Forward-Catalyst-Aware Contrarian Gate (Spec 007)

**Branch**: `006-forward-catalyst-gate` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/006-forward-catalyst-gate/spec.md`

## Summary

Add the FIRST forward-catalyst-aware rating-suppression filter to the framework. New module `tradingagents/agents/utils/forward_catalyst_filter.py` (parallel placement to A3 + spec 004 + spec 006) exposes `evaluate_forward_catalyst(...)` which: invokes an LLM (default `claude-opus-4-7`; configurable via `forward_catalyst_model`) on the 4 analyst reports + bull/bear debate + investment plan; receives structured `CasePricedInScore` output (bull_case_priced_in + bear_case_priced_in + rationale); applies bull-side fire when `bull_case_priced_in > bull_threshold (0.60 default) AND pre_rating in {Buy, Overweight} AND bull_mode == "active"`; applies bear-side fire when `bear_case_priced_in > bear_threshold (0.50 default) AND pre_rating in {Underweight, Sell} AND bear_mode == "active"`; downgrades to Hold + emits `state["forward_catalyst"]` annotation. Bull-side default-on at active mode (justified by Class 3 Opus retrospective DECISIVE PASS); bear-side default-shadow per Constitution VIII shadow-mode-first condition. Wired in `tradingagents/agents/managers/portfolio_manager.py` LAST in the chain (after A3 + spec 006 + spec 003/003.5 + spec 004) per FR-012. State-log writer + AgentState TypedDict extended for the new annotation field. Adds ~$0.025/propagate Opus cost (Constitution III T1 classification). SC-008 empirical-validation gate verifies the filter would have suppressed ≥24 of 27 ticker_weak-bull cohort + ≥10 of 18 ticker_strong-bear cohort per the Opus retrospective evidence. **Spec includes Constitution v1.4.0 amendment** (FR-015) extending Principle VIII with the forward-catalyst-class validation gate.

## Technical Context

**Language/Version**: Python 3.10+ (per `pyproject.toml`); 3.12.8 dev venv.
**Primary Dependencies**: `tradingagents.llm_clients.factory.create_llm_client` (existing infrastructure); `pydantic` (already a dep) for `CasePricedInScore` BaseModel + structured output via `llm.with_structured_output(...)`. NO new third-party deps. Reuses the structured-output pattern from `tradingagents/agents/utils/structured.py` + `tradingagents/agents/utils/second_opinion.py` (Phase C precedent for adding LLM calls to PM hooks).
**Storage**: read-only over the analyst-reports + debate state already in `AgentState`. Per-propagate LLM call returns scores; cached only via the natural state-log persistence (no separate caching layer needed).
**Testing**: pytest (`unit` marker for filter logic with mocked LLM; `integration` marker for the SC-008 retrospective + the live LLM round-trip). ≥90% coverage on new code per SC-007.
**Target Platform**: Cross-platform CLI (Windows + Linux + macOS); same as the rest of the framework.
**Project Type**: Python library extension — single-module addition + small wiring change in PM + Constitution amendment + state-log + AgentState extensions; no new CLI surface; one new persistence schema field (state["forward_catalyst"]).
**Performance Goals**: Filter completes in ≤10s per propagate (Opus latency dominates; Haiku ~1-2s alternative). Acceptable as a PM-stage hook because it runs ONCE per propagate (vs analyst loops which can iterate). Below the deep-think LLM-call latency by similar magnitude.
**Constraints**: Per-call cost ≤ $0.025 Opus (SC-005); strict greater-than threshold semantics (FR-005/SC-002, mirrors A3 + spec 004 + spec 006 boundary); never upgrade ratings (FR-007); both-modes-off honored as zero-cost no-op (SC-006); reuses existing factory + structured-output pattern; never breaks PM pipeline on LLM failure (FR-010); deterministic decision GIVEN scores (FR-011 — LLM stochasticity is outside spec scope).
**Scale/Scope**: 1 LLM call per propagate. For typical operator workflow (`daily_signals.py` on 5-10 ticker watchlist, daily cadence): ~10 calls/day × $0.025 = $0.25/day cost addition. For backtest workflow (100+ propagates): ~$2.50 cost addition; operators see this in `--yes` cost confirmation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| **I. Save Everything** | N/A here | This is a *spec*, not an experiment. The new `state["forward_catalyst"]` annotation IS corpus per the existing state-log persistence path (whitelist extension precedent from commit `4c14d0f` + spec 004 + spec 006). Future experiments using the filter follow the standard `experiments/<id>/HYPOTHESIS.md` pattern. |
| **II. One Experiment Per Change** | Pass | Two pairs of knobs (bull/bear thresholds + bull/bear modes); experiments vary one at a time cleanly. Default-on bull is empirically justified by the Class 3 Opus retrospective; bear-side defaults to shadow per VIII shadow-mode-first condition. |
| **III. Stay Cheap** | Pass at T1 | Per-propagate cost ~$0.025 Opus = ~$0.25/day for typical 10-ticker operator workflow. Backtest workflow adds ~$2.50 per 100-propagate run. T1 (≤$5/experiment) classification holds for typical use; backtest workflows should document the cost tier in HYPOTHESIS.md. |
| **IV. No Production Claims** | Pass | This filter REMOVES bullish commits where the bull case is widely priced in (and bearish commits where bear case is priced in). It doesn't add commits or claim signal beyond what's been measured. The default-on (bull) + default-shadow (bear) discipline preserves Principle IV's "research substrate, not signal" framing. |
| **V. Steal Liberally** | N/A | The mechanism mirrors the Phase C `second_opinion.py` pattern (independent LLM call on PM evidence) which is already project-native. No cross-project pattern lift. |
| **VI. Spec Before Structural Change** | Pass | Spec exists (this is its plan). Structural changes covered: new module under `tradingagents/agents/utils/`, new wiring step in `portfolio_manager.py` PM hook chain, new `state["forward_catalyst"]` field, six new `TradingAgentsConfig` keys, one-line whitelist extension in `trading_graph.py:_log_state`, one-key extension to `AgentState` TypedDict, **Constitution v1.4.0 amendment** (FR-015). |
| **VII. Calibrated Abstention** | Pass | Filter INCREASES Hold rate on both branches (suppresses Buy/OW where bull case is priced in; suppresses UW/Sell where bear case is priced in). Constitution VII permits Hold-increasing changes without additional justification. The "more Holds when consensus is widely accepted = better" direction matches Principle VII's intent: when the market has already absorbed the thesis, the framework's commit is unlikely to add value beyond the consensus → Hold is the calibrated output. |
| **VIII. Retrospective Before Spec for Backward-Looking Price Filters** | Pass + Amendment | Class 3 Opus retrospective DECISIVELY PASSED the bull-side gate (discrim +14.43pp / cohort hit rate 88.9% / net Δα +2.24pp at T=0.60). Bear-side passed criteria 1+2 with shadow-mode-first condition. The spec is empirically justified per the methodology. **Spec includes Constitution v1.4.0 amendment** extending Principle VIII to add the forward-catalyst-class validation gate (FR-015 + SC-009). |

**Gate result**: 8/8 pass + 1 amendment. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/006-forward-catalyst-gate/
├── spec.md              # /speckit.specify output (already exists)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (this run)
├── data-model.md        # Phase 1 output (this run)
├── quickstart.md        # Phase 1 output (this run)
├── contracts/           # Phase 1 output (this run)
│   ├── annotation_schema.md   # state["forward_catalyst"] dict schema
│   └── filter_function.md      # evaluate_forward_catalyst function contract
├── checklists/
│   └── requirements.md  # spec quality checklist (already exists)
└── tasks.md             # /speckit.tasks output
```

### Source Code (repository root)

```text
tradingagents/
├── agents/
│   ├── utils/
│   │   ├── momentum_filter.py                 # UNCHANGED — A3 (per-ticker bear)
│   │   ├── sector_momentum_filter.py          # UNCHANGED — Spec 004 (sector ETF bull)
│   │   ├── bear_sector_symmetry_filter.py     # UNCHANGED — Spec 006 (ticker-vs-sector bear)
│   │   ├── second_opinion.py                  # PATTERN-REUSED (Phase C — Pydantic + structured output)
│   │   └── forward_catalyst_filter.py         # NEW — LLM-extracted case-priced-in feature (~250 LOC)
│   │   └── agent_states.py                    # MODIFIED — add `forward_catalyst` to AgentState TypedDict (~3 LOC)
│   └── managers/
│       └── portfolio_manager.py               # MODIFIED — wire new filter LAST in chain (~30 LOC additions)
├── llm_clients/
│   └── factory.py                             # UNCHANGED — `create_llm_client` already supports Anthropic
├── default_config.py                          # MODIFIED — add 6 keys to TypedDict + DEFAULT_CONFIG (~12 LOC additions)
└── graph/trading_graph.py                     # MODIFIED — extend _log_state whitelist (~1 LOC)

scripts/
├── forward_catalyst_class3_retrospective.py   # UNCHANGED — the retrofit script that produced the Opus PASS verdict
└── forward_catalyst_retrospective.py          # NEW — production-config retrospective (consumes default_config; ~150 LOC)

tests/
├── test_forward_catalyst_filter.py            # NEW — unit tests with mocked LLM (~350 LOC)
├── test_portfolio_manager_filter_integration.py # MODIFIED — add Spec 007 wiring tests (~80 LOC additions)
└── test_trading_graph.py                      # MODIFIED — state-log persistence regression test (~30 LOC additions)

.specify/memory/
└── constitution.md                            # MODIFIED — Principle VIII v1.4.0 amendment (FR-015; ~30 LOC additions)

CHANGELOG.md                                   # MODIFIED — v1.4.0 amendment entry + spec 007 entry (~12 LOC additions)
CLAUDE.md                                      # MODIFIED — Empirical filters section: add 6th bullet for spec 007 (~12 LOC additions)
```

**Structure Decision**: New module `tradingagents/agents/utils/forward_catalyst_filter.py` parallel to A3 + spec 004 + spec 006. Rationale: same "PM hook stage filter" placement; differentiates from the prior 3 backward-price filters by adding an LLM call (which is the only filter doing so). The Phase C `second_opinion.py` pattern is the established precedent for "LLM call inside PM hook with Pydantic structured output + graceful fallback" — Spec 007 reuses that pattern.

**Total LOC estimate**: ~250 implementation + ~460 tests + ~150 retrospective + ~30 constitution + ~12 changelog + ~12 CLAUDE.md + ~12 config + ~3 AgentState + ~30 PM wiring + ~1 whitelist ≈ **~960 LOC** across 2 new files + 8 modifications.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Constitution check passes 8/8 + 1 amendment per FR-015.

---

## Phase 0: Research

See [`research.md`](./research.md). Resolves the technical-context decisions surfaced during planning (LLM client integration via existing factory, Pydantic structured output via `with_structured_output` + `second_opinion.py` precedent, threshold semantics + boundary handling — strict greater-than mirrors prior filters, filter ordering in PM hook chain — last per FR-012, annotation persistence path, retrospective script methodology — extends existing Class 3 retrofit, default model + threshold justification from Opus retrospective, cost discipline + per-propagate impact, naming convention Spec 007 vs branch dir 006). All NEEDS CLARIFICATION items resolved.

## Phase 1: Design & Contracts

See:
- [`data-model.md`](./data-model.md) — `CasePricedInScore` Pydantic schema + `ForwardCatalystAnnotation` dict + 6 new `TradingAgentsConfig` keys + `AgentState` TypedDict extension + state transitions
- [`contracts/`](./contracts/) — 2 contracts: annotation schema (consumer-facing), filter function signature (internal API)
- [`quickstart.md`](./quickstart.md) — operator walkthrough: enable in shadow mode, inspect annotations, run SC-008 retrospective, ablation experiment pattern, bear-side default-on flip prerequisites

## Constitution re-check (post-design)

After completing Phase 1: re-evaluate principles against the now-concrete data model + contracts.

| Principle | Pre-design | Post-design | Notes |
|---|---|---|---|
| I. Save Everything | Pass | Pass | Annotation persistence via existing `_log_state` whitelist (one-line extension); state-log replay invariant preserved. AgentState TypedDict extension prevents the spec 003 silent-drop bug. |
| II. One Experiment Per Change | Pass | Pass | Two pairs of knobs (modes + thresholds), six total config keys; experiments vary one at a time. Default-on bull is empirically justified; default-shadow bear is per VIII shadow-mode-first. |
| III. Stay Cheap | Pass | Pass | Confirmed by data-model: Opus call = ~$0.025/propagate; both-modes-off escape hatch = zero cost (FR-009 + SC-006). T1 holds for typical workflows. |
| IV. No Production Claims | Pass | Pass | Default-on bull + default-shadow bear discipline confirmed; never claims signal beyond the +14.43pp discrimination + 88.9% cohort hit rate the Opus retrospective measured. |
| V. Steal Liberally | Pass | Pass | N/A — pattern reuse from `second_opinion.py` (project-native). |
| VI. Spec Before Structural Change | Pass | Pass | This spec is the structural-change record. Constitution amendment FR-015 included as part of spec implementation. |
| VII. Calibrated Abstention | Pass | Pass | Confirmed: filter INCREASES Hold rate on both branches; never decreases. Permitted under VII without additional justification. |
| VIII. Retrospective Before Spec | Pass + amendment | Pass + amendment | Class 3 Opus retrospective DECISIVELY PASSED on bull side; bear side passes 1+2 with shadow-mode-first. Constitution v1.4.0 amendment formalizes the forward-catalyst-class gate (FR-015). |

**Post-design gate result**: 8/8 + 1 amendment. Proceed to `/speckit.tasks`.
