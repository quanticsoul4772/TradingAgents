# Implementation Plan: Class 4 Macro-Environment Filter (Spec 012)

**Spec**: `specs/012-class-4-macro-filter/spec.md`
**Created**: 2026-05-09
**Status**: **CONDITIONAL PLAN** — covers Branch A (default-SHADOW initial launch) implementation. Branch B (default-ACTIVE) is a future spec amendment after live evidence accumulates.

## Pre-implementation gate

This plan is the second PR in the standard 6-PR spec-kit bundle (per `reference_speckit_6pr_workflow_pattern.md`). Bundle progression:

1. **THIS PR** — spec.md + plan.md (Branch A + B scaffold; conditional)
2. **PENDING** — tasks.md
3. **PENDING** — MVP implementation
4. **PENDING** — tests
5. **PENDING** — polish + per-spec retrospective

The plan can be drafted NOW because:
- Class 4 retrospective PASSED (PR #193, 2026-05-09)
- Mechanism-disjoint with A3 confirmed
- v1.4.3 additive gate PASSED at +24.07pp incremental
- Shadow-mode-first launch is the conservative recommendation per Constitution VIII v1.4.0 small-sample-caution sub-clause

## Architectural overview

Class 4 is a **per-propagate macro-environment fetch + threshold check + (optional) rating modification** pattern. Mirrors Spec X-1 (institutional rotation; PR #92) shape:
- Lightweight helper module (`macro_environment_filter.py`)
- PM hook chain integration in `portfolio_manager.py`
- yfinance-backed feature fetch (no LLM call; $0 per-propagate)
- LRU-cached for in-process performance
- 3 modes (off / shadow / active)
- State annotation in `state["class_4_macro"]` dict

No NEW mechanism class is introduced architecturally — this is the **FIRST instance of macro-environment-class** but the architectural pattern (yfinance + threshold + state annotation) is standard.

## Branch A implementation (default-SHADOW initial launch)

### Phase 1 — Helper module (P1 user story A.1)

**Module**: `tradingagents/agents/utils/macro_environment_filter.py`

**Public API**:

```python
def maybe_suppress_bear_macro(
    final_trade_decision: str,
    ticker: str,
    trade_date: str,
    bear_mode: Literal["off", "shadow", "active"] = "shadow",
    vix_threshold: float = 18.0,
) -> tuple[str, dict | None]:
    """Apply Class 4 macro-environment filter to a bear commit.

    Returns (post_rating_markdown, annotation_dict).
    annotation_dict has 7 fields per Spec 012 FR-008 OR None if mode == "off".

    In SHADOW mode: computes would_fire decision but never modifies the
    rating (post_rating == pre_rating).
    In ACTIVE mode: when would_fire AND pre_rating in {Underweight, Sell},
    overwrites Rating header to "Hold".
    """
```

Internal helpers:
- `_vix_snapshot(trade_date: str) -> float | None` — LRU-cached yfinance VIX history fetch
- `_macro_30d_changes(trade_date: str) -> dict` — VIX/TNX/DXY 30d trailing pct changes
- `_classify_bear_macro(vix: float, threshold: float) -> bool` — pure threshold logic

### Phase 2 — Config schema (FR-010)

**Module**: `tradingagents/default_config.py`

Add to `TradingAgentsConfig` TypedDict:
```python
class_4_macro_bear_mode: Literal["off", "shadow", "active"]
class_4_macro_bull_mode: Literal["off", "shadow", "active"]
class_4_macro_vix_threshold: float
```

DEFAULT_CONFIG entries:
```python
"class_4_macro_bear_mode": "shadow",  # Branch A initial
"class_4_macro_bull_mode": "off",     # Bull-side deferred
"class_4_macro_vix_threshold": 18.0,  # Per retrospective recommended default
```

### Phase 3 — PM hook chain integration (FR-004)

**Module**: `tradingagents/agents/managers/portfolio_manager.py`

Insert filter invocation BETWEEN A3 and Spec X-1 in the bear-side filter chain. Per CLAUDE.md filter-portfolio "smallest-sample last" ordering: A3 (n=43 cohort, runs first) → Class 4 (n=8 cohort, this insertion point) → Spec X-1 (n=12 cohort, runs last).

```python
# Class 4 macro-environment filter (Spec 012)
class_4_bear_mode = get_config().get("class_4_macro_bear_mode", "shadow")
if class_4_bear_mode != "off":
    final_trade_decision, class_4_dict = maybe_suppress_bear_macro(
        final_trade_decision,
        state["company_of_interest"],
        state["trade_date"],
        bear_mode=class_4_bear_mode,
        vix_threshold=float(get_config().get("class_4_macro_vix_threshold", 18.0)),
    )
    state_log_extras["class_4_macro"] = class_4_dict
```

### Phase 4 — AgentState declaration (FR-009)

**Module**: `tradingagents/agents/utils/agent_states.py`

Add `class_4_macro: Annotated[dict, ...]` to `AgentState` TypedDict per the Spec 003 silent-drop precedent.

### Phase 5 — State log persistence (FR-008)

**Module**: existing `_log_state` whitelist in graph node logic.

Add `class_4_macro` to the whitelist so the dict appears in saved state logs. Same pattern as Spec X-1 PR #92.

### Phase 6 — Tests (SC-001 through SC-009 + SC-011)

**New test files**:
- `tests/test_macro_environment_filter.py` — ~10 unit tests (helper module + threshold edge + LRU cache + yfinance mock failure)
- `tests/test_class_4_pm_integration.py` — ~3 PM integration tests (off / shadow / active modes)
- Extend `tests/test_state_log_persistence.py` — 2 new regression tests for `class_4_macro` field

### Phase 7 — Documentation

- `docs/SIGNALS.md` — new "Class 4 macro-environment filter" sub-section + cohort-validation table
- `CLAUDE.md` "Empirical filters" section — add Class 4 entry + mechanism-class table row
- `RESEARCH_FINDINGS.md` "Filter portfolio status" table — add Class 4 row

### Phase 8 — Per-spec retrospective markdown

**New file**: `claudedocs/spec-012-class-4-retrospective-2026-05-09.md` (or post-MVP date)

Documents the chain: 2026-05-09 retrospective PASS → spec drafting → MVP implementation → SHADOW mode launch. Per Constitution VIII v1.4.1 (spec ships its retrospective).

## Branch B implementation (future amendment, not this spec)

**Trigger**: 30+ live shadow-mode fires accumulate AND ablation re-validates the +24.07pp Δα.

**Deployment**: PR-level amendment to Spec 012 spec.md flips default `class_4_macro_bear_mode = "active"`. Cites live-mode ablation evidence.

**No new code**: just config default flip + retrospective markdown citing live evidence.

## Implementation effort estimates

| Phase | Effort | Notes |
|---|---|---|
| Phase 1 — helper module | ~1.5h | New module + 3 internal helpers + LRU cache |
| Phase 2 — config schema | ~10 min | 3 keys |
| Phase 3 — PM hook | ~30 min | Insertion + state_log_extras |
| Phase 4 — AgentState | ~5 min | TypedDict addition |
| Phase 5 — state log persistence | ~10 min | Whitelist addition |
| Phase 6 — tests | ~2h | ~15 tests across 2 files |
| Phase 7 — documentation | ~30 min | 3 doc updates |
| Phase 8 — retrospective | ~30 min | Markdown |
| **Total** | **~5h** | Across PRs #X+2 (tasks) + #X+3 (MVP) + #X+4 (tests) + #X+5 (polish) |

**Cost**: $0 LLM (pure plumbing + docs; same as Spec X-1).

## Constitution adherence (Branch A)

- ✅ I (Save Everything): retrospective markdown shipped per VI v1.4.1 (PR #193 + future Phase 8)
- ✅ II (One Experiment Per Change): single intervention (new filter)
- ✅ III (Stay Cheap): $0 LLM
- ✅ IV (No Production Claims): default-SHADOW per small-sample-caution; no production-readiness claim until 30+ live fires
- ✅ VI (Spec Before Structural Change): this plan + spec.md
- ✅ VII (Calibrated Abstention): orthogonal — Class 4 operates BEFORE PM commit (filter chain), not on the abstention decision itself
- ✅ VIII v1.4.0 + v1.4.3: PASSED in retrospective (PR #193); both gates documented in spec.md predecessor section

## Pre-implementation checks

Before invoking the next PR (tasks.md), verify:

- [x] Retrospective PASS confirmed (PR #193)
- [x] Mechanism-disjointness with A3 confirmed (retrospective Phase 4 analysis)
- [x] Constitution v1.4.0 + v1.4.3 gates explicitly cleared
- [x] Spec 012 spec.md scaffolded (this PR)
- [x] FR-004 hook ordering rationale documented (smallest-sample last)

## Cross-references

- `specs/012-class-4-macro-filter/spec.md` (this PR)
- `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193 — retrospective verdict)
- `specs/091-c4-institutional-rotation/plan.md` (Spec X-1 — same architectural pattern; reuse precedents)
- `specs/006-forward-catalyst-gate/plan.md` (Spec 007 — shadow-mode-first launch precedent)
- `specs/007-calendar-boost-filter/plan.md` (Spec 008 — yfinance LRU cache pattern; SC-009 ablation precedent)
- Memory: `reference_speckit_6pr_workflow_pattern.md` (the 6-PR bundle pattern this plan instantiates)
- Memory: `reference_conditional_branch_spec_pattern.md` (the conditional-branch pattern this plan + spec follow)
