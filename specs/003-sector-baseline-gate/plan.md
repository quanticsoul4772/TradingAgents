# Implementation Plan: Sector-Baseline Fallback for Contrarian Gate

**Branch**: `003-sector-baseline-gate` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/003-sector-baseline-gate/spec.md`

## Summary

Extend the spec 003 contrarian gate (`tradingagents/signals/contrarian_gate.py`) with a sector-level fallback baseline. When per-ticker history falls below the FR-004 N≥20 floor, the gate computes a percentile against the pooled `bull_keyword_count` history of all same-sector tickers (sector membership from the `tradingagents/paper/sectors.py` yfinance cache). Same threshold (80th percentile), same downgrade target (Buy/OW → Hold or Underweight), same modes (off/shadow/active), same signal/feature pluggability. New `gate_baseline` annotation field tells the operator which baseline fired (`per_ticker` / `sector` / `none`). Feature-flagged via `contrarian_gate_sector_fallback_enabled` (default True; settable False for ablation per Constitution II). Zero LLM cost (pure offline state-log scan). Empirical motivation: SC-003 Financials investigation showed 4 of 5 losing OW commits had zero per-ticker history, so spec 003 gate could not fire by construction.

## Technical Context

**Language/Version**: Python 3.10+ (per `pyproject.toml` `requires-python`); 3.12.8 in dev venv.
**Primary Dependencies**: existing — no new third-party deps. Reuses `tradingagents/paper/sectors.py` (yfinance sector cache) and existing state-log scan pattern from `scripts/contrarian_gate_retrospective.py` and `scripts/sc003_financials_gate_check.py`.
**Storage**: read-only over `~/.tradingagents/logs/<ticker>/TradingAgentsStrategy_logs/full_states_log_*.json`. No new persistence; sector pool computed on-demand per evaluation. Sectors cache at `~/.tradingagents/paper/sectors.json` (already exists per Spec 002).
**Testing**: pytest with `unit` marker; ~95% coverage target on new code (project standard); SC-002 byte-identity preservation as a regression-guard test against the existing spec 003 test corpus; SC-005 ablation flag preservation as another regression-guard test.
**Target Platform**: Cross-platform CLI (Windows + Linux + macOS); same as spec 003.
**Project Type**: Python library extension — single module (`tradingagents/signals/contrarian_gate.py`) gains the fallback path; no new CLI surface, no new persistence schema.
**Performance Goals**: sector-pool aggregation completes in ≤ 200ms even for sectors with 30+ tickers and 1000+ pooled observations (typical scan: O(N_tickers_in_sector × N_state_logs) filesystem reads, dominated by yfinance-info-cached sector lookups which are O(1) cache hits). Below the LLM-call boundary by orders of magnitude.
**Constraints**: Zero LLM API calls (SC-006); strict no-look-ahead within and across same-day evaluations (FR-002); byte-identical decisions on thick-history tickers vs spec 003 (SC-002); ablation flag must produce spec-003-identical decisions when False (SC-005); `gate_baseline` annotation field MUST appear in every emitted annotation post-fix (SC-003).
**Scale/Scope**: Single contrarian-gate module extension. Operator's typical `~/.tradingagents/logs/` has 9-50 tickers with 5-50 state logs each at the time of writing — well within the 200ms budget. No persistent cache needed in v1.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| **I. Save Everything** | ✅ N/A here | This is a *spec*, not an experiment. The gate annotations it emits ARE corpus per the existing spec 003 + the `contrarian_gate` field persisted by trading_graph.py (per commit `4c14d0f` 2026-05-06 fix). Future experiments using the sector fallback follow the standard `experiments/<id>/HYPOTHESIS.md` pattern. |
| **II. One Experiment Per Change** | ✅ Pass | This spec introduces ONE structural change (add fallback to existing gate). The ablation flag (FR-010, default True) makes spec-003-identical-vs-with-fallback a one-knob comparison; future experiments can vary the flag while holding everything else constant. |
| **III. Stay Cheap** | ✅ Pass at T1 | Zero LLM cost (FR-006/SC-006). Implementation cost: $0. Validation experiments: re-running the existing `contrarian_gate_retrospective.py` and `sc003_financials_gate_check.py` against the new fallback path is also $0. T1 (≤$5). |
| **IV. No Production Claims** | ✅ Pass | This feature does not change spec 003's "research substrate, not signal" framing. The new `gate_baseline` field arguably *strengthens* the no-production-claims guard by making operators distinguish high-confidence (per_ticker, finding-#4-validated) from lower-confidence (sector, novel mechanism) firings in audit. |
| **V. Steal Liberally** | ✅ N/A | No cross-project pattern lift. The sector-pool aggregator pattern is project-native. |
| **VI. Spec Before Structural Change** | ✅ Pass | Spec exists (this is its plan). Structural change covered: extends an existing structural feature (spec 003 gate) with an additive fallback path; preserves all existing semantics on the per-ticker path. |
| **VII. Calibrated Abstention** | ⚠️ Subtle | The gate downgrades Buy/OW to Hold — that REDUCES Hold rate's interpretability (some Holds were originally bullish commits the gate suppressed) but does not increase commit count. Spec 003 already has this property; the fallback extends it to more tickers. The HYPOTHESIS section in any experiment that relies on the fallback must address Constitution VII's operational test ("any new structural change that reduces Hold rate must justify..."). This spec INCREASES Hold-rate when the fallback fires; that's the opposite direction Constitution VII guards against, so the principle is satisfied. |

**Gate result**: 7/7 pass. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/003-sector-baseline-gate/
├── spec.md              # /speckit.specify output (already exists)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (/speckit.plan, this run)
├── data-model.md        # Phase 1 output (/speckit.plan, this run)
├── quickstart.md        # Phase 1 output (/speckit.plan, this run)
├── contracts/           # Phase 1 output (/speckit.plan, this run)
│   ├── gate_annotation_extended.md   # Schema delta on the spec 003 annotation
│   └── sector_pool_function.md        # Sector-pool aggregator function contract
├── checklists/
│   └── requirements.md  # spec quality checklist (already exists)
└── tasks.md             # /speckit.tasks output (NOT created here)
```

### Source Code (repository root)

```text
tradingagents/
├── signals/
│   ├── contrarian_gate.py         # MODIFIED — add fallback ladder + gate_baseline annotation field (~80 LOC additions)
│   └── sector_baseline.py         # NEW — sector-pool aggregator (~120 LOC)
├── default_config.py              # MODIFIED — add `contrarian_gate_sector_fallback_enabled` + `contrarian_gate_sector_floor` keys to TradingAgentsConfig (~6 LOC additions)
└── paper/sectors.py               # UNCHANGED — reused for sector-membership lookups

tests/
├── test_sector_baseline.py        # NEW — pool aggregator unit tests (~150 LOC)
├── test_contrarian_gate_fallback.py # NEW — fallback ladder + annotation extension tests (~180 LOC)
└── test_contrarian_gate.py        # MODIFIED — add SC-002 byte-identity regression-guard tests (~50 LOC additions)

CLAUDE.md                          # MODIFIED — Architecture/Empirical-filters section: note the fallback ladder + gate_baseline annotation (~15 LOC additions)
```

**Structure Decision**: Single-project Python library extension. The new `sector_baseline.py` module lives alongside the existing `contrarian_gate.py` in `tradingagents/signals/` so both files share the same import path. Tests in `tests/` (flat). No new CLI scripts; the change is internal to the gate's evaluation path.

**Total LOC estimate**: ~200 implementation + ~380 tests + ~15 docs ≈ ~595 LOC across 2 new files + 4 modifications.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Constitution check passes 7/7. Principle VII subtlety noted but satisfied (this feature INCREASES Hold rate when the fallback fires, which is the direction Constitution VII permits without additional justification).

---

## Phase 0: Research

See [`research.md`](./research.md). Resolves the technical-context decisions surfaced during planning (sector-pool aggregation algorithm, strict-prior cutoff handling within a single step, performance budget, "Unknown" sector handling, ablation-flag default, annotation backward-compat). All NEEDS CLARIFICATION items resolved.

## Phase 1: Design & Contracts

See:
- [`data-model.md`](./data-model.md) — extended GateAnnotation schema + SectorBaselineSource enum + SectorPool computed-on-demand entity
- [`contracts/`](./contracts/) — 2 contracts: extended gate annotation schema (consumer-facing); sector-pool aggregator function signature (internal API contract)
- [`quickstart.md`](./quickstart.md) — operator walkthrough: enabling the fallback flag, inspecting the new `gate_baseline` annotation, running the ablation comparison

## Constitution re-check (post-design)

After completing Phase 1: re-evaluate principles against the now-concrete data model + contracts.

| Principle | Pre-design | Post-design | Notes |
|---|---|---|---|
| I. Save Everything | ✅ | ✅ | Annotation extensions persist via the existing `contrarian_gate` field added to state log in commit `4c14d0f`; replay invariant holds. |
| II. One Experiment Per Change | ✅ | ✅ | Ablation flag confirmed in data-model as `contrarian_gate_sector_fallback_enabled: bool` config key; experiments can vary it cleanly. |
| III. Stay Cheap | ✅ | ✅ | Confirmed by data-model: SectorPool is computed on-demand from existing state logs; no new LLM/API calls; aggregator is filesystem-bound. |
| IV. No Production Claims | ✅ | ✅ | New `gate_baseline` field actually strengthens the audit story by surfacing baseline confidence. |
| V. Steal Liberally | ✅ | ✅ | N/A — project-native. |
| VI. Spec Before Structural Change | ✅ | ✅ | This spec is the structural-change record. |
| VII. Calibrated Abstention | ⚠️ | ✅ | Confirmed: the fallback INCREASES Hold rate (downgrades that previously couldn't fire now do). Constitution VII permits Hold-increasing changes without additional justification (the principle guards against Hold-DECREASING changes). |

**Post-design gate result**: 7/7. Proceed to `/speckit.tasks`.
