# Implementation Plan: Hybrid C — Calendar-Boosted Forward-Catalyst Filter (Spec 008)

**Branch**: `007-calendar-boost-filter` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-calendar-boost-filter/spec.md`

## Summary

Hybrid C is a calendar-aware enhancement of the Spec 007 bull-side forward-catalyst filter. At PM stage, AFTER Spec 007 produces the `bull_case_priced_in` LLM score, multiply the score by `(1 + magnitude × boost)` where `boost = max(0, 1 - days_to_next_earnings / window)`. The Spec 007 fire decision then uses this `effective_bull_score` instead of the raw score. Bull-side only (FR-004); bear-side unchanged. Default-off (FR-007); operator opts in via PARAMS.json.

**Technical approach**: tiny new helper module (`calendar_boost.py`, ~80 LOC) wrapping the boost formula + an LRU-cached `yfinance.Ticker(t).earnings_dates` lookup. Integration into `forward_catalyst_filter.py` is a single `if config["hybrid_c_calendar_boost_enabled"]:` branch that substitutes effective scores before the existing fire-decision comparison. Three new `TradingAgentsConfig` keys (boolean enable + 2 numeric defaults). NO PM hook chain change. NO `AgentState` schema change (the `forward_catalyst` key is already declared as `Annotated[dict, ...]` in spec 007). NO Constitution amendment.

## Technical Context

**Language/Version**: Python 3.10+ (matches `pyproject.toml` target-version = "py310")
**Primary Dependencies**: `yfinance` (already in repo, used by spec 004 sector momentum filter + analyst tools), `pandas` (transitive via yfinance), `functools.lru_cache` (stdlib)
**Storage**: In-process LRU cache only (per-ticker `earnings_dates` snapshot). NO disk persistence; cache cleared on process exit.
**Testing**: pytest with markers (`unit`, `integration`); mocks via `unittest.mock` for yfinance HTTP calls; pytest-fast hook runs `pytest -m unit -q` on every commit
**Target Platform**: Cross-platform Linux + Windows (CI matches; existing project pattern)
**Project Type**: Python library (extension to existing `tradingagents/` package)
**Performance Goals**: ≤250 ms p99 latency on cache-cold ticker (single yfinance HTTP fetch); ≤5 ms on cache-warm ticker (in-memory dict lookup) — per SC-012
**Constraints**: ZERO LLM cost addition (Constitution III T0 — per FR-015 + SC-011); backward-compat with spec 007 baseline state logs (FR-011 + SC-005); strict-gt threshold semantics matching spec 007 SC-002 (FR-013 + SC-006)
**Scale/Scope**: ~80 LOC helper + ~50 LOC integration + 3 config keys + ≥16 net-new tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| **I. Save Everything** | N/A | Implementation, not experiment. Existing `_log_state` whitelist persists `state["forward_catalyst"]`. |
| **II. One Experiment Per Change** | N/A | Implementation. Default-off launch ensures no behavioral drift in existing experiments. |
| **III. Stay Cheap (T0 $0)** | PASS | FR-015: zero LLM cost. yfinance fetches are free. Per-propagate addition: $0 LLM. |
| **IV. No Production Claims** | PASS | Hybrid C is operator-opt-in research enhancement; no production-claim language in spec. |
| **V. Steal Liberally** | N/A | No cross-project pattern lifted. |
| **VI. Spec Before Structural Change** | PASS | This IS the spec. spec.md committed at `bddf00d` before any implementation. |
| **VI sub: Spec ships retrospective** | PASS | `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md` (production-config retrospective at commit `6cc7be9`) ships alongside. SC-008 makes the retrospective the post-merge regression check. |
| **VII. Calibrated Abstention** | PASS | Hybrid C bull-side fires INCREASE Hold rate (suppresses additional Buy/OW commits whose effective score crossed T=0.60). The +3.35pp net Δα improvement IS the empirical justification per VII operational test (a) — additional commits are calibrated rather than noise. |
| **VIII. Retrospective Before Spec — backward-price gate** | N/A | Hybrid C is forward-catalyst-aware (uses calendar features + LLM-extracted scores), not backward-price-only. The original VIII gate doesn't apply. |
| **VIII. Forward-catalyst-class validation gate** | PASS | Discrimination +11.30pp ≥ +5pp (PRIMARY); cohort hit rate 92.6% ≥ 60%; net Δα +5.58pp ≥ +0.5pp at boosted threshold (vs +2.24pp Class 3-alone baseline). All three criteria pass at boosted config. Improvement over Class 3-alone baseline ≥ 0.5pp on at least one criterion (+3.35pp net Δα + +3.7pp cohort hit) per the "Hybrid C must improve at least one criterion vs underlying filter" principle. |

**Constitution check verdict**: ALL gates PASS at design time. No amendment required. No `Complexity Tracking` violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/007-calendar-boost-filter/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (committed bddf00d)
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/           # Phase 1 output (this command)
│   └── calendar_boost_api.md   # Function signatures + invariants
├── checklists/
│   └── requirements.md  # Spec quality checklist (committed bddf00d)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

Existing single-package layout (no separation needed):

```text
tradingagents/
├── agents/
│   └── utils/
│       ├── calendar_boost.py          # NEW (~80 LOC) — helper module
│       ├── forward_catalyst_filter.py # MODIFY (~10 LOC integration delta) — spec 007
│       ├── momentum_filter.py         # (unrelated; A3)
│       ├── sector_momentum_filter.py  # (unrelated; spec 004)
│       └── ... (existing utils)
├── default_config.py                  # MODIFY (3 new keys + TypedDict additions)
├── graph/
│   └── trading_graph.py               # NO CHANGE (_log_state already whitelists "forward_catalyst")
└── ... (existing tree)

tests/
├── test_calendar_boost.py                              # NEW (≥12 unit tests)
├── test_forward_catalyst_filter_calendar_boost.py      # NEW (≥4 integration tests)
└── test_forward_catalyst_filter.py                     # NO CHANGE (spec 007 baseline; backward-compat verified by SC-005)
```

**Structure Decision**: Single-package extension. Spec 008 is a strict superset of Spec 007 — the new helper module sits in the same `tradingagents/agents/utils/` directory as A3, spec 004, and spec 007's filter, following the existing convention (one file per filter class). Tests follow the same `tests/test_<module>.py` convention. NO new sub-package, NO new directory tree.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

NO violations. Constitution check passed all 8 principles + the VIII forward-catalyst sub-gate at design time. Spec 008 is intentionally minimal: 3 new config keys, 1 new helper module, 1 modified module, ≥16 new tests, $0 LLM cost. The simplicity is the point — Hybrid C reuses the validated Spec 007 LLM call and adds only post-processing.
