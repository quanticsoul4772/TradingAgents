# Implementation Plan: Bear-Sector-Symmetry Filter (Spec 006)

**Branch**: `005-bear-sector-symmetry` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/005-bear-sector-symmetry/spec.md`

## Summary

Add a fifth rating-suppression filter to the framework — second on the bear side after A3 — targeting bearish commits on tickers that have outperformed their sector ETF beyond a configurable threshold. New module `tradingagents/agents/utils/bear_sector_symmetry_filter.py` (parallel placement to A3's `momentum_filter.py` + spec 004's `sector_momentum_filter.py`) exposes `maybe_suppress_bear_rating(...)` which: looks up the ticker's GICS sector via spec 002's yfinance cache (`tradingagents/paper/sectors.py`), maps to the canonical SPDR sector ETF using `SECTOR_ETF_MAP` imported from spec 004's module (no duplication per FR-004), computes both the ticker's prior-30-trading-day return and the sector ETF's prior-30-trading-day return via the consolidated `tradingagents.dataflows.returns.returns_from_frames` primitive, computes the relative-strength delta (ticker return − ETF return), fires when delta > threshold (default `+5%`), downgrades Underweight/Sell → Hold (never to Buy/OW per FR-007), emits a `state["bear_sector_symmetry"]` annotation. Three modes: off (default) / shadow / active. Wired in `tradingagents/agents/managers/portfolio_manager.py` AFTER the existing A3 hook + parallel to spec 003 + spec 004 hooks per FR-012. State-log writer + AgentState TypedDict extended for the new annotation field. Zero LLM cost. SC-008 empirical-validation gate verifies the filter would have suppressed ≥8 of 18 `ticker_strong`-bearish commits identified in `claudedocs/sector-alpha-attribution-2026-05-06.md` at the default `+5%` threshold.

## Technical Context

**Language/Version**: Python 3.10+ (per `pyproject.toml`); 3.12.8 dev venv.
**Primary Dependencies**: yfinance (already used everywhere); no new third-party deps. Reuses `tradingagents.paper.sectors.get_sector` (Spec 002), `tradingagents.dataflows.returns.returns_from_frames` (consolidated forward-α primitive), the A3 `trailing_momentum_pct` pattern, and spec 004's `SECTOR_ETF_MAP` + `_etf_history` LRU-cached fetcher.
**Storage**: read-only over yfinance API for ticker + ETF price history; sector membership from existing `<paper_state_dir>/sectors.json` cache (Spec 002). No new persistence.
**Testing**: pytest (`unit` marker for filter logic with mocked yfinance/sector lookups; `integration` marker for the SC-008 retrospective + the live yfinance round-trip). ≥90% coverage on new code per SC-007.
**Target Platform**: Cross-platform CLI (Windows + Linux + macOS); same as the rest of the framework.
**Project Type**: Python library extension — single-module addition + small wiring change in PM; no new CLI surface; no new persistence schema (just an additive state-log field).
**Performance Goals**: Filter completes in ≤500ms per propagate (yfinance ticker + ETF fetch dominates; LRU cache amortizes within a multi-ticker `daily_signals.py` run since the same sector ETF is reused across multiple tickers in that sector). Below the LLM-call boundary by orders of magnitude.
**Constraints**: Zero LLM API calls (SC-005); strict greater-than threshold semantics (FR-006/SC-002, inverted from spec 004's strict-less-than); never upgrade to Buy/OW (FR-007); default-off (SC-006 byte-identity vs no-filter baseline); reuse `returns_from_frames` and `SECTOR_ETF_MAP` (FR-004/FR-005); never break PM pipeline on yfinance/sector failure (FR-010).
**Scale/Scope**: 11 sector ETFs in the canonical mapping (reused from spec 004); typical operator runs 5-50 tickers per `daily_signals.py` invocation, so the filter sees ≤50 ticker fetches + ≤11 ETF fetches per day. LRU cache trivially amortizes ETF side; ticker fetches benefit when multiple dates per ticker run in the same process (e.g., backtest workflow).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| **I. Save Everything** | N/A here | This is a *spec*, not an experiment. The new `state["bear_sector_symmetry"]` annotation IS corpus per the existing state-log persistence path (whitelist extension precedent from commit `4c14d0f` adding `contrarian_gate` and from spec 004 adding `sector_momentum`). Future experiments using the filter follow the standard `experiments/<id>/HYPOTHESIS.md` pattern. |
| **II. One Experiment Per Change** | Pass | Default-off (spec FR-008) preserves the no-filter baseline. The threshold config key acts as the single ablation knob — experiments vary it cleanly. Default-on flip is explicitly OUT OF SCOPE for this spec; happens in a separate commit only after a SC-008-style retrospective justifies it (matches A3's + spec 004's introduction patterns). |
| **III. Stay Cheap** | Pass at T1 | Zero LLM cost (SC-005). Implementation cost: $0. Validation work (SC-008 retrospective) is also $0 — replays existing yfinance ticker + ETF history offline against the sector-α attribution corpus. T1 (≤$5). |
| **IV. No Production Claims** | Pass | This filter REMOVES bearish commits in regimes where they tend to lose hard (+28.02% mean α-vs-SPY for the cohort it targets). It doesn't add commits or claim signal beyond what's been measured. The default-off + retrospective-before-flip discipline preserves Principle IV's "research substrate, not signal" framing. |
| **V. Steal Liberally** | N/A | No cross-project pattern lift. The mechanism mirrors A3 + spec 004 wiring patterns that are already project-native; this spec is the bear-side relative-strength symmetric inverse of spec 004's bull-side absolute-momentum. |
| **VI. Spec Before Structural Change** | Pass | Spec exists (this is its plan). Structural changes covered: new module under `tradingagents/agents/utils/`, new wiring step in `portfolio_manager.py` PM hook chain, new `state["bear_sector_symmetry"]` field, three new `TradingAgentsConfig` keys, one-line whitelist extension in `trading_graph.py:_log_state`, one-key extension to `AgentState` TypedDict. |
| **VII. Calibrated Abstention** | Pass | Filter INCREASES Hold rate (suppresses bearish commits in counter-trend regimes). Constitution VII permits Hold-increasing changes without additional justification (the principle guards against Hold-DECREASING changes). The "more Holds = better when ticker is rallying vs sector" direction matches Principle VII's intent: when evidence is bear-biased but price action contradicts (ticker rallying despite the bear case), Hold is the calibrated output. |

**Gate result**: 7/7 pass. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/005-bear-sector-symmetry/
├── spec.md              # /speckit.specify output (already exists)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (this run)
├── data-model.md        # Phase 1 output (this run)
├── quickstart.md        # Phase 1 output (this run)
├── contracts/           # Phase 1 output (this run)
│   ├── annotation_schema.md   # state["bear_sector_symmetry"] dict schema
│   └── filter_function.md      # maybe_suppress_bear_rating function contract
├── checklists/
│   └── requirements.md  # spec quality checklist (already exists)
└── tasks.md             # /speckit.tasks output (NOT created here)
```

### Source Code (repository root)

```text
tradingagents/
├── agents/
│   ├── utils/
│   │   ├── momentum_filter.py                 # UNCHANGED — A3 (per-ticker bear suppression on absolute return)
│   │   ├── sector_momentum_filter.py          # UNCHANGED — Spec 004 (sector-ETF bull suppression on absolute return)
│   │   │                                      #             EXPORTS: SECTOR_ETF_MAP, _etf_history, clear_etf_cache
│   │   └── bear_sector_symmetry_filter.py     # NEW — sector-relative bear suppression on relative-strength delta (~190 LOC)
│   │   │                                      #       IMPORTS: SECTOR_ETF_MAP, _etf_history from sector_momentum_filter
│   │   └── agent_states.py                    # MODIFIED — add bear_sector_symmetry key to AgentState TypedDict (~3 LOC)
│   └── managers/
│       └── portfolio_manager.py               # MODIFIED — wire new filter after A3 hook + emit annotation (~30 LOC additions)
├── paper/sectors.py                           # UNCHANGED — sector lookup reused
├── dataflows/returns.py                       # UNCHANGED — `returns_from_frames` reused per FR-005
├── default_config.py                          # MODIFIED — add 3 keys to TypedDict + DEFAULT_CONFIG (~8 LOC additions)
└── graph/trading_graph.py                     # MODIFIED — extend _log_state whitelist (~1 LOC; mirrors `4c14d0f` precedent)

scripts/
└── bear_sector_symmetry_retrospective.py      # NEW — SC-008 empirical-validation script + future Δα retrospective (~180 LOC)

tests/
├── test_bear_sector_symmetry_filter.py        # NEW — unit tests (mocked yfinance/sector lookups) ~280 LOC
├── test_portfolio_manager_filter_integration.py # MODIFIED — add wiring + ordering tests for new filter (~60 LOC additions)
└── test_trading_graph.py                      # MODIFIED — add state-log persistence regression test (~25 LOC additions)

CLAUDE.md                                      # MODIFIED — Empirical filters section: add 5th bullet for spec 006 (~12 LOC additions)
```

**Structure Decision**: New module `tradingagents/agents/utils/bear_sector_symmetry_filter.py` parallel to A3's `momentum_filter.py` and spec 004's `sector_momentum_filter.py`. Rationale: The three filters share the broad shape ("price-condition mean-reversion suppression in PM hook chain") but differ in (a) bull vs bear side, (b) per-ticker absolute vs sector ETF absolute vs ticker-vs-sector relative input. Co-locating in `agents/utils/` gives all three filters the same "where does the project keep momentum-style suppressors?" answer for future readers, while keeping each filter's logic readable in isolation. The new module IMPORTS `SECTOR_ETF_MAP` + `_etf_history` from spec 004's module to avoid duplication per FR-004.

**Total LOC estimate**: ~190 implementation + ~365 tests + ~180 retrospective + ~12 docs + ~3 state-key + ~30 PM wiring + ~8 config + ~1 whitelist ≈ ~789 LOC across 2 new files + 6 modifications.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Constitution check passes 7/7.

---

## Phase 0: Research

See [`research.md`](./research.md). Resolves the technical-context decisions surfaced during planning (sector lookup integration via reuse, ETF + ticker fetch path with LRU caching, threshold semantics + boundary handling — symmetric inverse of spec 004, filter ordering in PM hook chain especially the A3↔spec-006 ordering question, annotation persistence path, retrospective script methodology, SC-008 empirical-validation approach using the n=18 ticker_strong-bear cohort, module placement vs extension question). All NEEDS CLARIFICATION items resolved.

## Phase 1: Design & Contracts

See:
- [`data-model.md`](./data-model.md) — `BearSectorSymmetryAnnotation` dict + 3 new `TradingAgentsConfig` keys + `AgentState` TypedDict extension + state transitions
- [`contracts/`](./contracts/) — 2 contracts: annotation schema (consumer-facing), filter function signature (internal API)
- [`quickstart.md`](./quickstart.md) — operator walkthrough: enable in shadow mode, inspect annotations, run SC-008 retrospective, ablation experiment pattern, default-on flip prerequisites

## Constitution re-check (post-design)

After completing Phase 1: re-evaluate principles against the now-concrete data model + contracts.

| Principle | Pre-design | Post-design | Notes |
|---|---|---|---|
| I. Save Everything | Pass | Pass | Annotation persistence via existing `_log_state` whitelist (one-line extension); state-log replay invariant preserved. AgentState TypedDict extension prevents the spec 003 silent-drop bug. |
| II. One Experiment Per Change | Pass | Pass | Threshold config key (default `None`) is the single on/off knob; mode key (default `"off"`) gates measurement-vs-active behavior. Two knobs total; one experiment varies one. |
| III. Stay Cheap | Pass | Pass | Confirmed by data-model: zero LLM calls; ETF + ticker fetches via existing yfinance dependency; LRU cache trivially amortizes within a multi-ticker daily_signals run; ticker-fetch cache also helps backtest workflows that hit the same ticker on multiple dates. |
| IV. No Production Claims | Pass | Pass | Default-off + retrospective-before-flip discipline confirmed in plan + quickstart; matches A3's + spec 004's introduction precedents. |
| V. Steal Liberally | Pass | Pass | N/A — project-native; symmetric inverse of spec 004 + spec 003 patterns. |
| VI. Spec Before Structural Change | Pass | Pass | This spec is the structural-change record. |
| VII. Calibrated Abstention | Pass | Pass | Confirmed: filter INCREASES Hold rate; never decreases. Permitted under VII without additional justification. |

**Post-design gate result**: 7/7. Proceed to `/speckit.tasks`.
