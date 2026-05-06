# Implementation Plan: Sector-Momentum Filter

**Branch**: `004-sector-momentum-filter` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/004-sector-momentum-filter/spec.md`

## Summary

Add a third bullish-suppression filter to the framework (after spec 003 + spec 003.5) targeting sector-rotation losses. New module `tradingagents/agents/utils/sector_momentum_filter.py` (parallel to A3's `momentum_filter.py`) exposes `maybe_suppress_bull_rating(...)` which: looks up the ticker's GICS sector via spec 002's yfinance cache (`tradingagents/paper/sectors.py`), maps to the canonical SPDR sector ETF (XLK/XLF/XLV/...), computes the ETF's prior-30-trading-day return via the consolidated `tradingagents.dataflows.returns.returns_from_frames` primitive, fires when return < threshold (default -5%), downgrades Buy/OW → Hold (never UW per FR-007), emits a `state["sector_momentum"]` annotation. Three modes: off (default) / shadow / active. Wired in `tradingagents/agents/managers/portfolio_manager.py` AFTER the existing A3 + spec 003 hooks. State-log writer extended for the new annotation field. Zero LLM cost. SC-008 empirical-validation gate verifies the filter would have suppressed ≥3 of 5 SC-003 Financials losers (XLF empirically down >5% in 30d before 2026-04-03 — verify at impl time).

## Technical Context

**Language/Version**: Python 3.10+ (per `pyproject.toml`); 3.12.8 dev venv.
**Primary Dependencies**: yfinance (already used everywhere); no new third-party deps. Reuses `tradingagents.paper.sectors.get_sector` (Spec 002), `tradingagents.dataflows.returns.returns_from_frames` (consolidated forward-α primitive), the A3 `trailing_momentum_pct` pattern.
**Storage**: read-only over yfinance API for ETF price history; sector membership from existing `<paper_state_dir>/sectors.json` cache (Spec 002). No new persistence.
**Testing**: pytest (`unit` marker for filter logic with mocked yfinance/sector lookups; `integration` marker for the SC-003 Financials retrospective + the live yfinance round-trip). ≥90% coverage on new code per SC-007.
**Target Platform**: Cross-platform CLI (Windows + Linux + macOS); same as the rest of the framework.
**Project Type**: Python library extension — single-module addition + small wiring change in PM; no new CLI surface; no new persistence schema (just an additive state-log field).
**Performance Goals**: Filter completes in ≤500ms per propagate (yfinance ETF fetch dominates; LRU cache amortizes within a multi-ticker `daily_signals.py` run on tickers in the same sector). Below the LLM-call boundary by orders of magnitude.
**Constraints**: Zero LLM API calls (SC-005); strict less-than threshold semantics (FR-006/SC-002); never downgrade to UW (FR-007); default-off (SC-006 byte-identity vs no-filter baseline); reuse `returns_from_frames` (FR-005); never break PM pipeline on yfinance/sector failure (FR-010).
**Scale/Scope**: 11 sector ETFs in the canonical mapping; typical operator runs 5-50 tickers per `daily_signals.py` invocation, so the filter sees ≤50 sector lookups per day with a small (≤11) ETF-fetch set. LRU cache trivially amortizes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| **I. Save Everything** | ✅ N/A here | This is a *spec*, not an experiment. The new `state["sector_momentum"]` annotation IS corpus per the existing state-log persistence path (whitelist extension precedent from commit `4c14d0f`). Future experiments using the filter follow the standard `experiments/<id>/HYPOTHESIS.md` pattern. |
| **II. One Experiment Per Change** | ✅ Pass | Default-off (spec FR-008) preserves the no-filter baseline. The threshold config key acts as the single ablation knob — experiments vary it cleanly. Default-on flip is explicitly OUT OF SCOPE for this spec; happens in a separate commit only after a SC-008-style retrospective justifies it (matches A3's introduction pattern). |
| **III. Stay Cheap** | ✅ Pass at T1 | Zero LLM cost (SC-005). Implementation cost: $0. Validation work (SC-008 retrospective) is also $0 — replays existing yfinance ETF history offline. T1 (≤$5). |
| **IV. No Production Claims** | ✅ Pass | This filter REMOVES bullish commits in regimes where they tend to lose. It doesn't add commits or claim signal beyond what's been measured. The default-off + retrospective-before-flip discipline preserves Principle IV's "research substrate, not signal" framing. |
| **V. Steal Liberally** | ✅ N/A | No cross-project pattern lift. The mechanism mirrors A3 + spec 003 wiring patterns that are already project-native. |
| **VI. Spec Before Structural Change** | ✅ Pass | Spec exists (this is its plan). Structural changes covered: new module under `tradingagents/agents/utils/`, new wiring step in `portfolio_manager.py` PM hook chain, new `state["sector_momentum"]` field, three new `TradingAgentsConfig` keys, one-line whitelist extension in `trading_graph.py:_log_state`. |
| **VII. Calibrated Abstention** | ✅ Pass | Filter INCREASES Hold rate (suppresses bullish commits in sector-rotation regimes). Constitution VII permits Hold-increasing changes without additional justification (the principle guards against Hold-DECREASING changes). The "more Holds = better" direction matches Principle VII's intent: when evidence is weak (sector is in down regime), Hold is the calibrated output. |

**Gate result**: 7/7 pass. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-sector-momentum-filter/
├── spec.md              # /speckit.specify output (already exists)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (this run)
├── data-model.md        # Phase 1 output (this run)
├── quickstart.md        # Phase 1 output (this run)
├── contracts/           # Phase 1 output (this run)
│   ├── annotation_schema.md   # state["sector_momentum"] dict schema
│   └── filter_function.md      # maybe_suppress_bull_rating function contract
├── checklists/
│   └── requirements.md  # spec quality checklist (already exists)
└── tasks.md             # /speckit.tasks output (NOT created here)
```

### Source Code (repository root)

```text
tradingagents/
├── agents/
│   ├── utils/
│   │   ├── momentum_filter.py              # UNCHANGED — A3 (per-ticker bear suppression)
│   │   └── sector_momentum_filter.py       # NEW — sector-ETF bull suppression (~180 LOC)
│   └── managers/
│       └── portfolio_manager.py            # MODIFIED — wire new filter after spec 003 hook (~25 LOC additions)
├── paper/sectors.py                        # UNCHANGED — sector lookup reused
├── dataflows/returns.py                    # UNCHANGED — `returns_from_frames` reused per FR-005
├── default_config.py                       # MODIFIED — add 3 keys to TypedDict + DEFAULT_CONFIG (~8 LOC additions)
└── graph/trading_graph.py                  # MODIFIED — extend _log_state whitelist (~1 LOC; mirrors `4c14d0f` precedent)

scripts/
└── sector_momentum_retrospective.py        # NEW — SC-008 empirical-validation script + future Δα retrospective (~150 LOC)

tests/
├── test_sector_momentum_filter.py          # NEW — unit tests (mocked yfinance/sector lookups) ~250 LOC
└── test_portfolio_manager_filter_integration.py # MODIFIED — add wiring + ordering tests (~80 LOC additions)

CLAUDE.md                                   # MODIFIED — Empirical filters section: add 4th bullet for spec 004 (~12 LOC additions)
```

**Structure Decision**: New module `tradingagents/agents/utils/sector_momentum_filter.py` parallel to A3's `momentum_filter.py`. Rationale: A3 + this spec share filter shape (bullish vs bearish; per-ticker vs sector) but operate on different inputs and emit different annotations. Co-locating gives both filters the same "where does the project keep momentum-style suppressors?" answer for future readers, while keeping each filter's logic readable in isolation. Tests in `tests/` (flat).

**Total LOC estimate**: ~180 implementation + ~330 tests + ~150 retrospective + ~12 docs ≈ ~672 LOC across 2 new files + 4 modifications.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Constitution check passes 7/7.

---

## Phase 0: Research

See [`research.md`](./research.md). Resolves the technical-context decisions surfaced during planning (sector lookup integration, ETF data fetch path + caching, threshold semantics + boundary handling, filter ordering in PM hook chain, annotation persistence path, retrospective script methodology, SC-008 empirical-validation approach). All NEEDS CLARIFICATION items resolved.

## Phase 1: Design & Contracts

See:
- [`data-model.md`](./data-model.md) — `SectorMomentumAnnotation` dict + `SECTOR_ETF_MAP` constant + 3 new `TradingAgentsConfig` keys + state transitions
- [`contracts/`](./contracts/) — 2 contracts: annotation schema (consumer-facing), filter function signature (internal API)
- [`quickstart.md`](./quickstart.md) — operator walkthrough: enable in shadow mode, inspect annotations, run SC-008 retrospective, ablation experiment pattern, default-on flip prerequisites

## Constitution re-check (post-design)

After completing Phase 1: re-evaluate principles against the now-concrete data model + contracts.

| Principle | Pre-design | Post-design | Notes |
|---|---|---|---|
| I. Save Everything | ✅ | ✅ | Annotation persistence via existing `_log_state` whitelist (one-line extension); state-log replay invariant preserved. |
| II. One Experiment Per Change | ✅ | ✅ | Threshold config key (default `None`) is the single on/off knob; mode key (default `"off"`) gates measurement-vs-active behavior. Two knobs total; one experiment varies one. |
| III. Stay Cheap | ✅ | ✅ | Confirmed by data-model: zero LLM calls; ETF fetches via existing yfinance dependency; LRU cache trivially amortizes within a multi-ticker daily_signals run. |
| IV. No Production Claims | ✅ | ✅ | Default-off + retrospective-before-flip discipline confirmed in plan + quickstart; matches A3's introduction precedent. |
| V. Steal Liberally | ✅ | ✅ | N/A — project-native. |
| VI. Spec Before Structural Change | ✅ | ✅ | This spec is the structural-change record. |
| VII. Calibrated Abstention | ✅ | ✅ | Confirmed: filter INCREASES Hold rate; never decreases. Permitted under VII without additional justification. |

**Post-design gate result**: 7/7. Proceed to `/speckit.tasks`.
