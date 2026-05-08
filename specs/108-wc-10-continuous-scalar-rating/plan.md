# Implementation Plan: WC-10 Continuous Scalar Rating

**Branch**: `108-wc-10-continuous-scalar-rating` | **Date**: 2026-05-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/108-wc-10-continuous-scalar-rating/spec.md`

## Summary

WC-10 replaces the 5-tier categorical `PortfolioRating` enum with a continuous scalar in `[-1, +1]` for the Portfolio Manager's output, gated behind `wc_10_enabled` (default False). When enabled, filter-bypass mode (the v1 default) skips the entire 9-filter PM chain so the experiment is a clean single-intervention test of the categorical-bottleneck hypothesis. A `bin_scalar_to_tier()` helper provides 5-tier compatibility for ex-post analysis. Empirical pilot: 10 dates × 2 tickers (NVDA + AAPL) v1 grid for ~$8 LLM, plus 5-tier baseline comparison for ~$8 = **~$16 total**.

3 falsifiable predictions per spec.md SC-007: NULL (no behavior change), ALT-A (categorical-bottleneck-confirmed; less collapsed), ALT-B (signal-equivalent; bins ex-post to match 5-tier). At least ONE must be empirically distinguishable.

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: pydantic (existing); langchain (existing); pytest + pytest-mock (existing)
**Storage**: N/A (process-scoped + propagate-time state log; new `wc_10` field added to `_log_state` whitelist)
**Testing**: pytest with `unit` (~6 tests) + `integration` (~2 tests) markers
**Target Platform**: Cross-platform Python; CI on Windows
**Project Type**: Single-package extension to existing `tradingagents`
**Performance Goals**: zero-overhead when `wc_10_enabled=False`; minimal latency when enabled
**Constraints**: Constitution III T2 ≤$30 budget; default-off prevents accidental cost
**Scale/Scope**: ~150-200 LOC; 1 schema mutation + 1 SignalProcessor branch + 1 bin function + 1 portfolio_manager_node bypass branch + 3 new config keys + 1 new AgentState field + ~8 tests + 1 pilot script

## Constitution Check

| Principle | Gate Status | Justification |
|---|---|---|
| I. Save Everything | PASS | Pilot persists to `experiments/<date>-001-wc-10-pilot/` per Principle I; state logs include `wc_10` annotation; analyzer output saved as ANALYSIS.md |
| II. One Experiment Per Change | PASS | SINGLE intervention — schema 5-tier → continuous scalar. Filter-bypass is intentional consequence, not separate intervention |
| III. Stay Cheap | PASS | T2 ≤$30; v1 ~$16. Default-off prevents accidental cost |
| IV. No Production Claims | PASS | NULL or INCONCLUSIVE explicitly permitted per SC-007 |
| V. Steal Liberally | PASS | Reuses Spec X-1 6-PR-bundle, PARAMS.json opt-in, AgentState extension, Pydantic schema mutation patterns |
| VI. Spec Before Structural Change | PASS | This plan + spec.md (PR #107) + subsequent tasks.md provide the discipline |
| VII. Calibrated Abstention | PASS | WC-10 directly tests VII; any of 3 predictions is valid evidence |
| VIII. Forward-catalyst-class gate | N/A | WC-10 is output-schema experiment, not a forward-catalyst filter |

**No gate violations**. Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/108-wc-10-continuous-scalar-rating/
├── spec.md                      # PR #107
├── checklists/requirements.md   # PR #107
├── plan.md                      # This PR
├── research.md                  # This PR (Phase 0)
├── data-model.md                # This PR (Phase 1)
├── quickstart.md                # This PR (Phase 1)
├── contracts/wc_10_module.md    # This PR (Phase 1)
└── tasks.md                     # Future PR (/speckit.tasks)
```

### Source Code

```text
tradingagents/
├── agents/
│   ├── schemas.py                              # MODIFIED (PortfolioDecision.rating Union)
│   ├── utils/agent_states.py                   # MODIFIED (add wc_10 to AgentState)
│   └── managers/portfolio_manager.py           # MODIFIED (bypass branch)
├── graph/
│   ├── signal_processing.py                    # MODIFIED (scalar-aware extractor)
│   └── trading_graph.py                        # MODIFIED (_log_state whitelist)
├── default_config.py                           # MODIFIED (3 new keys)
└── wc_10/                                      # NEW PACKAGE
    ├── __init__.py
    └── bin.py                                  # bin_scalar_to_tier() pure function

tests/
├── test_wc_10_bin.py                           # NEW (~6 unit tests)
└── test_wc_10_pm_integration.py                # NEW (2 integration tests)

experiments/
└── 2026-05-08-001-wc-10-pilot/                 # NEW
    ├── HYPOTHESIS.md
    ├── PARAMS.json
    ├── results.csv
    ├── ANALYSIS.md
    ├── run.sh / run.ps1

scripts/
└── wc_10_pilot.py                              # NEW (~120 LOC harness)
```

**Structure Decision**: New `tradingagents/wc_10/` package houses the bin function + future expansion. Schema uses Union type for backward compat. Pilot harness in `scripts/` per existing experiment-runner pattern.

## Complexity Tracking

No violations. Section intentionally empty.
