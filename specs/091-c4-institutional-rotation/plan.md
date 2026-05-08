# Implementation Plan: C-4 Institutional Rotation Filter (Spec X-1)

**Branch**: `091-c4-institutional-rotation` | **Date**: 2026-05-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/091-c4-institutional-rotation/spec.md`

## Summary

Spec X-1 adds the FIRST quantitative-flow bear-side filter to the existing PM-stage filter chain. New helper module `tradingagents/agents/utils/institutional_rotation_filter.py` (~120 LOC) suppresses Underweight/Sell commits to Hold when the top 10 institutional holders' net pctChange rotation (sourced from yfinance.Ticker(t).institutional_holders, LRU-cached per process) falls below a configurable outflow threshold (default 0.05 fractional). Bear-side defaults to "shadow" mode per Constitution VIII v1.4.0 small-sample-caution sub-clause (n=12 cohort); bull-side defaults to "off" (n=1 evidence base too thin). Adds 4 new TradingAgentsConfig keys + extends `state["forward_catalyst"]` annotation dict with an `institutional_rotation` sub-dict. Filter ordering: appended LAST in the FR-012 chain after Spec 007. Zero LLM cost (pure yfinance + arithmetic).

Empirical justification: PR #75 standalone (n=12, +5.41pp net Δα, +10.29pp discrim, 75.0% hit) + PR #77 additive (+8.06pp Δα improvement, +69.23pp hit improvement vs Spec 007 bear union — C-4 catches 11 bearish commits Spec 007 entirely misses).

## Technical Context

**Language/Version**: Python 3.10 (per `[tool.ruff]` target in `pyproject.toml`)
**Primary Dependencies**: yfinance (existing); langchain (existing, for AgentState type compatibility); pytest + pytest-mock (existing test infrastructure)
**Storage**: N/A (state is process-scoped LRU cache + propagate-time state log persisted via existing `_log_state` whitelist)
**Testing**: pytest with markers `unit` (~14 unit tests in `tests/test_institutional_rotation_filter.py`) and `integration` (4 integration tests covering PM-hook with mode=off / shadow / active / yfinance failure)
**Target Platform**: Cross-platform Python (Windows / macOS / Linux per `pyproject.toml` classifiers); CI runs on Windows per current setup
**Project Type**: Single-package library extending the existing `tradingagents` Python package + script-driven research workflow
**Performance Goals**: yfinance fetch p95 < 200ms on cache miss (informational; SC-012); cache hit < 1ms; PM-hook overall latency unchanged on cache hit
**Constraints**: Zero LLM cost (Constitution III T0 free-tier), graceful degradation on yfinance errors (FR-013), strict less-than threshold semantics (FR-005, matches Spec 007 SC-002)
**Scale/Scope**: ~120 LOC for the helper module, ~14 unit + 4 integration tests, ~2 LOC delta in `portfolio_manager.py` for chain integration, 4 new config keys in `default_config.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate Status | Justification |
|---|---|---|
| **I. Save Everything** | PASS | New filter writes to existing `state["forward_catalyst"]` annotation persisted via existing `_log_state` whitelist; no new persistence schema. |
| **II. One Experiment Per Change** | PASS | This spec adds the filter mechanism + defaults; live-mode A/B ablation is deferred to a separate spec amendment per SC-010. |
| **III. Stay Cheap** | PASS | T0 (free) classification — no LLM cost addition; yfinance is a free data source. |
| **IV. No Production Claims** | PASS | Spec defaults to shadow mode + explicit live-validation gate (SC-010) before any production-default flip. |
| **V. Steal Liberally** | PASS | Pattern reuses spec 003 / 004 / 006 / 007 / 008 helper-module + state-annotation precedents; LRU cache pattern reuses Spec 007's prior precedent. |
| **VI. Spec Before Structural Change** | PASS | This plan IS the Spec Before Structural Change artifact; PR #88 shipped spec.md, this PR ships plan.md, implementation proceeds in subsequent PRs. |
| **VII. Calibrated Abstention is a Valid Output** | PASS | Filter fires INCREASE Hold rate; +5.41pp standalone Δα + +8.06pp additive Δα is the empirical justification per VII permission criterion. |
| **VIII. Forward-catalyst-class validation gate** (v1.4.0) | PASS | Pre-spec retrospective gate cleared at n=12 — discrim +10.29pp ≥ +5pp / cohort hit 75.0% ≥ 60% / net Δα +5.41pp ≥ +0.5pp. |
| **VIII v1.4.1 (Spec ships its retrospective + verdict)** | PASS | Two pre-existing retrospective markdowns referenced (PR #75 + PR #77) in spec.md sibling-docs section. |
| **VIII v1.4.3 (Additive-to-existing-filter gate)** | PASS | Cleared at PASS on 2 of 3 v1.4.3 criteria; per "at least 1 sufficient" rule, additive gate clears. |

**No gate violations**. Complexity Tracking section is empty.

## Project Structure

### Documentation (this feature)

```text
specs/091-c4-institutional-rotation/
├── spec.md                      # PR #88 (already shipped)
├── checklists/
│   └── requirements.md          # PR #88 (already shipped)
├── plan.md                      # This PR (/speckit.plan output)
├── research.md                  # This PR (Phase 0 output)
├── data-model.md                # This PR (Phase 1 output)
├── quickstart.md                # This PR (Phase 1 output)
├── contracts/
│   └── institutional_rotation_filter.md  # This PR (Phase 1 output)
└── tasks.md                     # Future PR (/speckit.tasks output)
```

### Source Code (repository root)

```text
tradingagents/
├── agents/
│   └── utils/
│       ├── institutional_rotation_filter.py   # NEW (~120 LOC)
│       ├── forward_catalyst_filter.py         # MODIFIED (chain integration ~2 LOC)
│       ├── momentum_filter.py                 # unchanged (Spec A3)
│       ├── sector_momentum_filter.py          # unchanged (Spec 004)
│       ├── bear_sector_symmetry_filter.py     # unchanged (Spec 006)
│       └── calendar_boost.py                  # unchanged (Spec 008)
├── agents/managers/
│   └── portfolio_manager.py                   # MODIFIED (chain hook ~3 LOC)
└── default_config.py                          # MODIFIED (4 new TypedDict keys)

tests/
├── test_institutional_rotation_filter.py      # NEW (~14 unit tests)
└── test_institutional_rotation_pm_integration.py  # NEW (4 integration tests)

scripts/
├── forward_catalyst_class4_retrospective.py   # unchanged (already exists; PR #75)
└── forward_catalyst_class4_vs_spec007_overlap.py  # unchanged (already exists; PR #77)
```

**Structure Decision**: Single-package extension. The new `institutional_rotation_filter.py` module lives alongside existing filter modules in `tradingagents/agents/utils/`. The PM-stage hook integration (~3 LOC) goes in `portfolio_manager.py` immediately after the Spec 007 hook call. Config keys (~4 lines) added to `default_config.py`'s TradingAgentsConfig TypedDict. Test files live in `tests/` with the existing convention (one unit-test file per module, one integration-test file for PM-hook).

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

No violations. This section intentionally empty.
