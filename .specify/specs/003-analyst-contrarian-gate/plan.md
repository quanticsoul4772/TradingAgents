# Implementation Plan: Analyst-stage Contrarian Gate

**Branch**: `main` (no feature branch — single-developer fork) | **Date**: 2026-05-05 | **Spec**: [`spec.md`](./spec.md)
**Input**: Feature specification from `.specify/specs/003-analyst-contrarian-gate/spec.md`

## Summary

A Portfolio-Manager-stage gate that uses the market analyst's `bull_keyword_count` percentile (computed within ticker over the most recent N=20 cached propagates) to suppress Buy/Overweight commits when the percentile exceeds a configurable threshold. Empirically motivated by finding #4 (`market_report bull_keyword_count` anti-predicts within-ticker α at 90d, within-ticker median IC -0.489, 8/8 non-degenerate tickers with unanimous direction) and the recency-mean-reversion mechanism (`claudedocs/finding4-mechanism-2026-05-05.md`: bull keywords correlate +0.47 with prior 30d α, which mean-reverts).

Three-phase rollout matching the spec's user story priorities:
- **Phase 1 (P1)**: shadow-mode gate emits annotation to state log; rating unchanged. Validation: gate annotation appears in 10/10 propagates with byte-identical `final_trade_decision` to no-gate baseline.
- **Phase 2 (P2)**: active mode + per-ticker percentile baseline. When gate fires AND PM rating is Buy/OW, downgrade to Hold (configurable to UW). Per-ticker percentile (not pooled) is the critical correctness requirement.
- **Phase 3 (P3)**: pluggable source (`contrarian_gate_signal` + `contrarian_gate_feature` config) so future within-ticker findings can use the same gate machinery.

## Technical Context

**Language/Version**: Python 3.10+ (project min; 3.12 in dev `.venv`).
**Primary Dependencies**: existing — `tradingagents.signals.cache.query_all` (SQLite), `tradingagents.signals.featurization.bull_keyword_count`, `pytest` for tests. No new dependencies.
**Storage**: existing `~/.tradingagents/signals/cache.db` (SQLite, WAL mode) — read-only access from the gate; no new tables. State log additions are JSON inside existing per-propagate state log files.
**Testing**: `pytest -m unit` (per Constitution Quality Gate 1; pre-commit-hooked). Coverage target: ≥95% for the new `contrarian_gate.py` module (Spec 002 / Spec 001 set the precedent).
**Target Platform**: Local dev (Windows + Linux dev shells in repo). No production deploy.
**Project Type**: Library extension to an existing Python framework. No external interfaces (no API, no CLI surface change beyond a new `scripts/analyze_contrarian_gate.py`).
**Performance Goals**: gate must add < 50ms wall-clock per propagate (cache query is single SELECT against a small SQLite DB; no per-propagate concern).
**Constraints**: must not break the 793-test pre-commit suite. FR-007 backwards-compat: `contrarian_gate_mode = "off"` default → byte-identical `final_trade_decision` content vs pre-spec-003.
**Scale/Scope**: 9-ticker corpus today, growing. Single-process, single-developer; no concurrency concerns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Save Everything | N/A | Spec 003 doesn't introduce new experiments; existing experiment scaffolding consumed unchanged. |
| II. One Experiment Per Change | N/A | No new experiment from gate code itself. Validation experiments (SC-001/002/003) follow standard one-variable-at-a-time pattern. |
| III. Stay Cheap | ✅ | Gate is $0/propagate. SC-002 validation needs N≥30 shadow-mode propagates → T2 (~$9) at default Opus + Haiku config. HYPOTHESIS will state. |
| IV. No Production Claims | ✅ | Gate is a research feature; doesn't change "research substrate, not signal" framing. |
| V. Steal Liberally | ✅ | Direct mirror of A3 momentum filter pattern (`tradingagents/agents/utils/momentum_filter.py`). Provenance noted in spec. |
| VI. Spec Before Structural Change | ✅ | This plan IS the spec-kit workflow per Principle VI. spec.md exists; this is `/speckit.plan`. |
| VII. Calibrated Abstention | ✅ | Active-mode override DOWNGRADES bullish commits to Hold. HYPOTHESIS will be: gate-suppressed commits should improve mean α — fewer commits, expected better α. Direction matches Principle VII. |

**Gate result**: pass on all applicable principles. No clarifications needed; no constitutional waivers required.

## Project Structure

### Documentation (this feature)

```text
.specify/specs/003-analyst-contrarian-gate/
├── spec.md              # Feature specification (committed e5dcd46, amended 08f94ed)
├── plan.md              # This file
├── research.md          # Phase 0 output — empirical foundation summary (consolidates 4 claudedocs)
├── data-model.md        # Phase 1 output — gate annotation schema + state log additions
├── quickstart.md        # Phase 1 output — operator usage examples
├── contracts/           # Phase 1 output — Python API contracts
│   └── contrarian_gate.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan; future /speckit.tasks)
```

### Source Code (repository root)

**New files**:
```
tradingagents/signals/contrarian_gate.py        # ContrarianGate class (FR-001)
scripts/analyze_contrarian_gate.py              # Post-hoc gate-impact analyzer (FR-008)
tests/test_contrarian_gate.py                   # Unit tests (target ~25 tests)
```

**Modified files**:
```
tradingagents/default_config.py                 # Add contrarian_gate_mode/_threshold/_target/_signal/_feature (FR-003)
tradingagents/agents/managers/portfolio_manager.py    # Wire gate after PM decision, before rating extraction (FR-002, FR-005)
tradingagents/graph/trading_graph.py            # Emit contrarian_gate block in state log (FR-006)
RESEARCH_FINDINGS.md                            # Note spec 003 implementation status
ROADMAP.md                                      # Mark Phase B / Spec 003 progress
```

**No changes**:
```
tests/conftest.py                               # No new fixtures needed
.pre-commit-config.yaml                         # No new hooks
pyproject.toml                                  # No new dependencies
```

## Phase 0: Outline & Research

The empirical foundation is complete from prior work — research.md is essentially a consolidation pointer rather than new investigation:

**Resolved unknowns** (from spec):
- *What featurizer?* `bull_keyword_count` from `tradingagents/signals/featurization.py`. Validated by finding #4 + mechanism investigation.
- *What baseline window?* N=20 most recent cached values per ticker (matches BOTS / drift-detector convention; bumped from N=5 after XLF investigation).
- *What threshold?* Default 80th percentile per FR-003. Tuning is downstream of Phase 1 shadow data.
- *Active-mode target rating?* Default "hold" (calibrated abstention per Principle VII). "underweight" available as a config option but unsupported by current evidence.
- *Per-ticker vs pooled percentile?* Per-ticker. Established by `claudedocs/featurizer-artifact-check-2026-05-04.md`.
- *Interaction with A3 filter?* Independent. Both can fire; both annotations logged; no arbitration. Per spec OQ-4.
- *Degenerate-window handling?* OQ-5 unresolved — Phase 1 shadow data will inform. Default per FR-004: skip when N<20.

**Remaining NEEDS CLARIFICATION**: none — all questions resolved by spec + amendments + linked claudedocs.

**Output (research.md)** consolidates:
- `claudedocs/within-ticker-artifact-check-2026-05-05.md` — finding #4 validation
- `claudedocs/finding4-mechanism-2026-05-05.md` — recency + mean-reversion mechanism
- `claudedocs/xlf-mechanism-2026-05-05.md` — XLF as degenerate window
- `claudedocs/degenerate-window-check-2026-05-05.md` — XLF + XLK both degenerate; 8/8 restated headline

## Phase 1: Design & Contracts

### data-model.md (gate annotation schema)

Single Python `dataclass` (no Pydantic needed for internal-only data; matches `tradingagents.signals.cache._row_to_dict` pattern):

```python
@dataclass(frozen=True)
class GateAnnotation:
    # Always-emitted fields
    mode: Literal["off", "shadow", "active"]
    signal_id: str                  # source signal (default "market_report")
    feature: str                    # source feature (default "bull_keyword_count")
    threshold: int                  # percentile threshold
    target: Literal["hold", "underweight"]

    # Computed fields (None when gate_skipped is non-empty)
    feature_value: float | None     # featurizer value for THIS propagate
    percentile: float | None        # 0-100, within-ticker percentile
    n_history: int | None           # how many cached values backed the percentile
    would_fire: bool | None         # threshold crossed AND PM rating is Buy/OW
    gate_fired: bool | None         # True iff active-mode rating override applied

    # Skip diagnostic
    gate_skipped: str | None        # "insufficient_history" / "missing_source_signal" / "degenerate_window" / "mode_off" / None
```

State log JSON shape (added to existing per-propagate state log file):
```json
{
  "contrarian_gate": {
    "mode": "shadow",
    "signal_id": "market_report",
    "feature": "bull_keyword_count",
    "threshold": 80,
    "target": "hold",
    "feature_value": 67.0,
    "percentile": 95.0,
    "n_history": 22,
    "would_fire": true,
    "gate_fired": false,
    "gate_skipped": null,
    "pm_rating_pre_gate": "Overweight",
    "pm_rating_post_gate": "Overweight"
  }
}
```

### contracts/contrarian_gate.md (Python API contract)

```python
class ContrarianGate:
    def __init__(self, config: dict, cache_path: Path | None = None) -> None:
        """Reads gate config from config dict; cache_path defaults to ~/.tradingagents/signals/cache.db."""

    def compute_annotation(
        self,
        ticker: str,
        market_report_text: str,
        pm_rating: str,
    ) -> GateAnnotation:
        """Compute the gate annotation for THIS propagate.

        Always returns a GateAnnotation; never raises (cache failures swallowed
        per cache.py convention). When mode == "off", returns annotation with
        gate_skipped="mode_off" and feature_value/percentile/etc all None.
        """

    def maybe_override_rating(
        self,
        annotation: GateAnnotation,
        pm_rating: str,
    ) -> tuple[str, bool]:
        """Returns (final_rating, override_applied).

        Override only applies when:
          - annotation.mode == "active"
          - annotation.would_fire is True
          - pm_rating in ("Buy", "Overweight")
        Otherwise returns (pm_rating, False).
        """
```

### quickstart.md (operator usage)

```python
# Shadow mode (default after enabling — measure before changing)
config["contrarian_gate_mode"] = "shadow"

# Active mode with default Hold target
config["contrarian_gate_mode"] = "active"

# Active mode with Underweight target (aggressive, unvalidated)
config["contrarian_gate_mode"] = "active"
config["contrarian_gate_target"] = "underweight"

# Pluggable source — try news_report instead
config["contrarian_gate_signal"] = "news_report"
config["contrarian_gate_feature"] = "bull_keyword_count"

# Threshold tuning
config["contrarian_gate_threshold"] = 90  # only fire on top-decile bull-prose moments
```

Post-hoc analysis:
```bash
python scripts/analyze_contrarian_gate.py \
    --state-logs ~/.tradingagents/logs/states/ \
    --out claudedocs/contrarian-gate-analysis-<date>.md
```

### Agent context update

Skipping `.specify/scripts/powershell/update-agent-context.ps1`. Spec 001 + 002 didn't run it (no precedent for `/speckit.plan` in this repo); project-level `CLAUDE.md` already lists the constitution + RESEARCH_FINDINGS as the single source of truth and is updated manually as part of doc-refresh commits.

## Constitution re-check (post-design)

Same gates as Phase 0. No changes:
- No new dependencies introduced (Principle V — minimal additive)
- Backwards-compat preserved (FR-007)
- Active-mode behavior aligns with Principle VII (downgrade to Hold = calibrated abstention)
- Gate is self-contained within `tradingagents/signals/` + a single PM hook (Principle VI — structural change kept narrow)

## Sequencing & dependencies

| Phase | Estimated effort | Dependencies | Validation |
|---|---|---|---|
| Phase 1 (P1 — shadow only) | 2-3h | None | SC-001 (10-date NVDA shadow propagate, byte-identical rating) |
| Phase 2a (P2 — per-ticker baseline) | 1h | Phase 1 | Unit test: synthetic per-ticker percentile case |
| Phase 2b (P2 — active mode override) | 1-2h | Phase 1, Phase 2a | SC-003 (matched 10-date shadow vs active grid; rate change concentrated on `would_fire = True`) |
| Phase 3 (P3 — pluggable source) | 1h | Phase 1 | Unit test: swap signal_id and verify percentile uses new cache rows |
| **SC-002 validation** (separate) | 30 propagates × ~$0.30 = ~$9 (T2) | All phases | Empirical reproduction of finding #4 in fresh data |

Total implementation: ~5-7h ($0). Validation experiment: T2 ~$9.

## Stop and report

Plan ends here. Branch is `main`; IMPL_PLAN at `.specify/specs/003-analyst-contrarian-gate/plan.md`. Generated artifacts (research.md, data-model.md, quickstart.md, contracts/contrarian_gate.md) are outlined inline in this plan rather than as separate files since the spec is internal-only and the contracts are short. If `/speckit.tasks` is invoked next, it should produce a `tasks.md` with file-level work items aligned to the Sequencing table above.

**Phase 2 (tasks generation) is NOT executed by /speckit.plan** — separate `/speckit.tasks` invocation.
