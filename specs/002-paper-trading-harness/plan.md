# Implementation Plan: Paper-Trading Harness

**Branch**: `002-paper-trading-harness` | **Date**: 2026-05-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/002-paper-trading-harness/spec.md`

## Summary

Build a deterministic position-keeping simulator on top of the existing `scripts/daily_signals.py` operator product. Consumes signal CSVs (new `daily_signals.py --emit-csv` flag), opens/closes virtual long-only positions per a versioned policy snapshot (default: 21d trading-day window, 8 max positions, 10% per slot, 50% per-sector cap, 5 bps each-side slippage, SPY benchmark), persists portfolio state as JSON + append-only event log under `~/.tradingagents/paper/`, and emits markdown daily digests with the Constitution Principle IV simulation disclaimer. Runs in two modes: **replay** (deterministic backtest over historical signals — must reproduce SC-003's +5.96% bullish-bucket within ±100 bps as the validation gate) and **step** (single-trading-day, idempotent, cron-able). Reuses the consolidated `tradingagents.dataflows.returns.returns_from_frames` primitive for all forward-α math (FR-012). Zero LLM cost in the harness itself (FR-011, SC-008).

## Technical Context

**Language/Version**: Python 3.10+ (per `pyproject.toml` `requires-python`); 3.12.8 in dev venv
**Primary Dependencies**: pandas, yfinance, typer, rich (all already in `pyproject.toml`); no new third-party dependencies
**Storage**: JSON state files + JSONL append-only event logs at `~/.tradingagents/paper/<portfolio_id>.json` + `<portfolio_id>.events.jsonl`; sectors cache at `~/.tradingagents/paper/sectors.json`. Honors `TRADINGAGENTS_CACHE_DIR` per FR-004.
**Testing**: pytest (markers: `unit`, `integration`); ~95% coverage target on new code (project standard); SC-001 reproduction encoded as `integration`-marked test per SC-007.
**Target Platform**: Cross-platform CLI (Windows + Linux + macOS); developed on Windows 11 / PowerShell + bash; CI parity via cross-platform path helpers (use `pathlib.Path`, `os.path.expanduser`, never hardcoded `/` separators).
**Project Type**: Python package + CLI script (matches existing `tradingagents/` package + `scripts/*.py` convention; no web/mobile/service surface)
**Performance Goals**: A single `step` invocation completes in ≤ 10 seconds for a 25-ticker watchlist with ≤ 8 open positions (yfinance frame fetch dominates; cache exploits the per-ticker fetch already done by `daily_signals.py`'s prior cycle). Replay over a 30-trading-day window completes in ≤ 60 seconds (one yfinance pull per ticker spanning the whole range).
**Constraints**: Zero LLM API calls in any harness command (SC-008); idempotent `step` (SC-002); reuse `returns_from_frames` for all forward-α math (FR-012); no broker integration / no real-money paths (Principle IV); no shorts (FR-007); whole-share sizing only (Assumption).
**Scale/Scope**: Single-operator personal use; one portfolio per `portfolio_id`; 25-ticker default watchlist; 8 open positions cap. State file size ≤ 100 KB per year of daily activity at typical usage; event log size ≤ 1 MB per year.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| **I. Save Everything** | ✅ N/A here | This is a *spec*, not an experiment. The harness's own daily digests + state files ARE a corpus that gets saved per FR-003/008/009 (event log + JSON state + daily digest), matching the spirit of Principle I for a long-running product surface vs. a discrete experiment. The first replay run validating SC-001 will produce an `experiments/2026-05-06-XXX-paper-harness-validation/` dir with HYPOTHESIS + ANALYSIS following the standard pattern. |
| **II. One Experiment Per Change** | ✅ Pass | This spec introduces ONE structural change (the harness package + CLI). The default policy is empirically motivated by SC-003; any future policy ablation (sector cap %, holding window, sizing) is a separate experiment varying one parameter against this spec's defaults. |
| **III. Stay Cheap** | ✅ Pass at T1 | The harness has zero LLM cost (FR-011, SC-008). The validation-gate test (SC-001) replays existing SC-003 signals without re-invoking propagate. T1 (≤$5) — actually $0. |
| **IV. No Production Claims** | ✅ Pass with explicit guard | FR-014 requires a Principle IV disclaimer in 100% of digests + operator docs; SC-005 measures it. The CLI itself is named `paper_trade.py` (paper, not real). The PolicySnapshot's `policy_version` is "v1-alpha" not "v1.0" to signal experimental status. |
| **V. Steal Liberally** | ✅ N/A | No cross-project pattern lift in this spec. (`agent-harness-v2`'s event-sourcing inspires the JSONL event log shape but the implementation is project-native.) |
| **VI. Spec Before Structural Change** | ✅ Pass | The spec exists (this is its plan). Structural changes covered: new persistent state convention under `~/.tradingagents/paper/`, new policy-snapshot interface, first signals-consumer in the codebase. |
| **VII. Calibrated Abstention** | ✅ Pass | The harness HONORS calibrated abstention: it never opens positions on Hold ratings (FR-005 only entries on Buy/Overweight); held positions ride through mid-window Hold (Assumption). The harness does NOT reduce the framework's Hold rate; it consumes the framework's existing rating distribution unchanged. The default policy's choice to mid-window-exit on UW/Sell but ignore mid-window Hold is consistent with Principle VII (Hold ≠ Sell signal). |

**Gate result**: All 7 principles pass. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-paper-trading-harness/
├── spec.md              # /speckit.specify output (already exists)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (/speckit.plan, this run)
├── data-model.md        # Phase 1 output (/speckit.plan, this run)
├── quickstart.md        # Phase 1 output (/speckit.plan, this run)
├── contracts/           # Phase 1 output (/speckit.plan, this run)
│   ├── cli.md           # paper_trade.py CLI surface
│   ├── signals_csv.md   # input CSV schema
│   ├── state_json.md    # portfolio state file schema
│   ├── events_jsonl.md  # event-log schema
│   └── digest_md.md     # daily digest output schema
├── checklists/
│   └── requirements.md  # spec quality checklist (already exists)
└── tasks.md             # /speckit.tasks output (NOT created here)
```

### Source Code (repository root)

```text
tradingagents/
├── paper/                          # NEW package — pure logic, importable, testable
│   ├── __init__.py                 # public exports (~10 LOC)
│   ├── portfolio.py                # Portfolio, Position, ClosedPosition dataclasses (~120 LOC)
│   ├── policy.py                   # SizingPolicy/EntryPolicy/ExitPolicy Protocols + DefaultPolicy (~200 LOC)
│   ├── engine.py                   # PaperTradingEngine.step(date, signals) → StepResult (~250 LOC)
│   ├── pricing.py                  # close-price fetcher + slippage wrapper around returns_from_frames (~80 LOC)
│   ├── state.py                    # JSON load/save + JSONL event append (~100 LOC)
│   ├── digest.py                   # markdown digest renderer (~180 LOC)
│   └── sectors.py                  # yfinance sector-info cache (~50 LOC)
├── default_config.py               # MODIFIED — add paper-harness config keys to TradingAgentsConfig (~10 LOC additions)
├── dataflows/returns.py            # UNCHANGED — reused via FR-012
└── graph/signal_processing.py      # UNCHANGED — reused for rating parsing

scripts/
├── paper_trade.py                  # NEW — typer CLI with replay/step/status subcommands (~250 LOC)
└── daily_signals.py                # MODIFIED — add --emit-csv option (~20 LOC additions)

data/
└── watchlists/
    └── tech_weighted.txt           # NEW — default ~25-ticker watchlist (~30 lines)

tests/
├── test_paper_portfolio.py         # NEW — Portfolio/Position/ClosedPosition dataclass tests (~80 LOC)
├── test_paper_policy.py            # NEW — sizing/entry/exit policy tests (~150 LOC)
├── test_paper_engine.py            # NEW — engine.step orchestration tests (~200 LOC)
├── test_paper_pricing.py           # NEW — close-fetch + slippage math (~80 LOC)
├── test_paper_state.py             # NEW — JSON round-trip + event-log idempotency (~100 LOC)
├── test_paper_digest.py            # NEW — markdown render smoke tests (~80 LOC)
├── test_paper_sectors.py           # NEW — sector cache behavior (~50 LOC)
├── test_paper_cli.py               # NEW — typer CLI invocation tests (~80 LOC)
├── test_paper_sc003_reproduction.py # NEW — integration-marked SC-003 reproduction (~100 LOC)
└── test_daily_signals.py           # MODIFIED — add --emit-csv test cases (~30 LOC additions)

docs/
└── PAPER_TRADING.md                # NEW — operator guide with Principle IV disclaimer (~150 LOC)

CLAUDE.md                           # MODIFIED — Architecture/Persistence + Commands sections (~25 LOC additions)
```

**Structure Decision**: Single-project layout (DEFAULT). The paper package lives under `tradingagents/paper/` matching the existing `tradingagents/{agents,signals,llm_clients,dataflows,graph}/` convention. CLI sits under `scripts/` matching `daily_signals.py`, `analyze_backtest.py`, etc. Tests under `tests/` matching the flat-test-files convention. No new top-level dirs; one new `data/watchlists/` subtree carrying the default watchlist file (chosen over `tradingagents/data/` because it's user-facing config, not Python-importable).

**Total LOC estimate**: ~1,030 implementation + ~950 tests + ~150 docs ≈ ~2,130 LOC across 16 new files + 4 small modifications. Test ratio ~92% (matches project standard).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Constitution check passes 7/7.

---

## Phase 0: Research

See [`research.md`](./research.md). Resolves the technical-context decisions surfaced during planning (price-data caching strategy, JSON-vs-other persistence, sector-info source selection, sizing-rounding strategy, idempotency-detection mechanism). All NEEDS CLARIFICATION items resolved.

## Phase 1: Design & Contracts

See:
- [`data-model.md`](./data-model.md) — entity field-by-field with validation rules + state transitions
- [`contracts/`](./contracts/) — 5 interface contracts (CLI surface, signals CSV, state JSON, events JSONL, digest markdown)
- [`quickstart.md`](./quickstart.md) — step-by-step "first replay run" + "first live step" walkthrough for the operator

## Constitution re-check (post-design)

After completing Phase 1: re-evaluate principles against the now-concrete data model + contracts.

| Principle | Pre-design | Post-design | Notes |
|---|---|---|---|
| I. Save Everything | ✅ | ✅ | Event log shape (one JSON line per state-changing event) is sufficient for full replay; state file is the materialized view. |
| II. One Experiment Per Change | ✅ | ✅ | Default policy locked in code; ablations are operator-provided overrides via PolicySnapshot. |
| III. Stay Cheap | ✅ | ✅ | Confirmed zero-LLM-call paths in all 3 subcommands (replay, step, status) by inspection of contracts. |
| IV. No Production Claims | ✅ | ✅ | Disclaimer wording fixed in `digest.py` template, asserted by SC-005 unit test. |
| V. Steal Liberally | ✅ | ✅ | Event-log JSONL pattern is loosely inspired by `agent-harness-v2` but implementation-native. |
| VI. Spec Before Structural Change | ✅ | ✅ | This spec is the structural-change record. |
| VII. Calibrated Abstention | ✅ | ✅ | Confirmed by data-model: ExitReason enum has no `mid_window_hold` value; only `window_elapsed`, `mid_window_signal`, `data_anomaly`. |

**Post-design gate result**: 7/7. Proceed to `/speckit.tasks`.
