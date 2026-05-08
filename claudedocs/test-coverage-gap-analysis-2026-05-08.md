# Test coverage gap analysis — 2026-05-08

**Date**: 2026-05-08
**Cost**: $0 (pytest --cov; corpus analysis)
**Project total**: 80.5% (4178 of 5193 statements covered across 98 files)
**Test count**: 1134 unit + 2 integration passing

## Project-level summary

| Metric | Value |
|---|---|
| Total statements | 5193 |
| Covered statements | 4178 |
| Missing statements | 1015 |
| Project coverage | **80.5%** |
| Files at 100% coverage | ~50 (estimated from full report) |
| Files below 80% with ≥20 stmts | **16** |

## Gap inventory (16 modules below 80%, ≥20 statements)

Sorted ascending by coverage %:

| Cov % | Missing | Total | Module | Category |
|---|---|---|---|---|
| 0.0 | 20 | 20 | `tradingagents/llm_clients/azure_client.py` | External-API-bound (Azure not default) |
| 2.6 | 74 | 76 | `tradingagents/dataflows/alpha_vantage_indicator.py` | External-API-bound (Alpha Vantage vendor) |
| 9.7 | 168 | **186** | `tradingagents/agents/utils/memory.py` | **Internal — REAL gap** |
| 20.0 | 52 | 65 | `tradingagents/dataflows/alpha_vantage_common.py` | External-API-bound |
| 26.6 | 47 | 64 | `tradingagents/dataflows/stockstats_utils.py` | External-lib wrapper |
| 26.8 | 41 | 56 | `tradingagents/graph/checkpointer.py` | Internal — SQLite/checkpoint |
| 30.0 | 14 | 20 | `tradingagents/dataflows/alpha_vantage_fundamentals.py` | External-API-bound |
| 62.7 | 121 | **324** | `tradingagents/signals/evaluation.py` | **Internal — large gap** |
| 65.4 | 56 | 162 | `tradingagents/graph/trading_graph.py` | Internal — graph orchestration |
| 66.7 | 7 | 21 | `tradingagents/agents/utils/agent_utils.py` | Internal — small gap |
| 68.0 | 39 | 122 | `tradingagents/signals/counterfactual.py` | Internal |
| 68.6 | 88 | 280 | `tradingagents/dataflows/y_finance.py` | External-vendor (yfinance) |
| 71.9 | 9 | 32 | `tradingagents/llm_clients/google_client.py` | External-API-bound |
| 72.7 | 47 | 172 | `tradingagents/signals/drift.py` | Internal |
| 72.9 | 13 | 48 | `tradingagents/signals/backfill.py` | Internal |
| 78.6 | 15 | 70 | `tradingagents/dataflows/macro.py` | External-vendor partial |

## Categorization

### Legitimately hard to cover (external/optional)

7 modules. Coverage gaps here are largely STRUCTURAL — testing requires real API credentials (Azure, Alpha Vantage, Google) or extensive vendor-specific mocks. These should NOT be a priority:

- `azure_client.py` (0%) — Azure provider; not the default. Testing requires Azure creds.
- `alpha_vantage_indicator.py` / `alpha_vantage_common.py` / `alpha_vantage_fundamentals.py` (2-30%) — Alpha Vantage vendor integrations. Testing requires API key.
- `stockstats_utils.py` (26%) — wrapper around stockstats library; integration-tested via downstream (technical_indicators_tools.py).
- `y_finance.py` (68%) — yfinance vendor integration. Partially mocked by Spec 003/X-1 tests; the remaining 32% gap is yfinance-specific calls that are operator-affordable but not necessary at unit scope.
- `google_client.py` (71%) — Google Gemini provider; not default. Testing requires Google creds.
- `macro.py` (78%) — macro data integrations (VIX, sector ETF strength); partial coverage via downstream filter tests.

**Total "structural gap" missing lines**: ~360 (35.5% of the 1015 missing statements). Bringing project total to ~86.5% if these were ignored (4,178 / 4,833 ≈ 86.5%).

### Internal — actionable gaps

8 modules (≥20 statements). These are real gaps in framework-internal code where tests COULD exist:

| Module | Cov | Priority | Rationale |
|---|---|---|---|
| `agents/utils/memory.py` | **9.7%** | **HIGH** | TradingMemoryLog. Just had Constitution Quality Gate #6 added (Memory-log data-vs-prose discipline) — system that operators must trust to read accurately. 168 missing lines is the largest internal gap. |
| `signals/evaluation.py` | 62.7% | MEDIUM | Full evaluation methodology (324 stmts). Used by `analyze_backtest.py`. 121 missing — likely covers per-rule counterfactual + custom-rule paths. |
| `graph/trading_graph.py` | 65.4% | MEDIUM | Graph orchestration core. Lines 303-338 + 343-421 are uncovered — likely `_resolve_pending_entries` (memory-log resolution path) + checkpointer integration. |
| `signals/counterfactual.py` | 68.0% | LOW | 122 stmts, 39 missing. Counterfactual analysis used by analyzer. Lines 172-235 likely the analyzer-CSV-write path. |
| `graph/checkpointer.py` | 26.8% | LOW | Checkpoint/resume; opt-in via `checkpoint_enabled=True`. Default-off in main.py. Tested behaviorally via `tests/test_checkpoint_resume.py`. |
| `signals/drift.py` | 72.7% | LOW | Drift detection. Lines 367-438 missing — likely advanced drift modes. |
| `signals/backfill.py` | 72.9% | LOW | Cache backfill. Validated end-to-end via PR #71 (254-row backfill). Missing lines are edge cases. |
| `agent_utils.py` | 66.7% | LOW | Tiny module (21 stmts, 7 missing). Lines 22 + 64-67 likely langchain helper code. |

### Recently-deployed code (Spec X-1) — already well-covered

- `tradingagents/agents/utils/institutional_rotation_filter.py` — NOT in the gap list. Estimated ~95% coverage based on PR #91/#92 test counts (15 unit tests). Verified by absence from the <80% list.

## Highest-value gap target: `agents/utils/memory.py`

**186 statements, 9.7% covered** — the largest internal gap.

This module implements `TradingMemoryLog`:
- `append_entry()` — write pending entry after each propagate
- `_resolve_pending_entries()` — write reflection prose + realized-α data after subsequent same-ticker run
- `read_recent_entries()` — read for PM context
- File I/O with `<!-- ENTRY_END -->` separator parsing
- Memory log rotation (resolved entries pruning at `memory_log_max_entries`)

**Why this matters**: Constitution v1.4.5 Quality Gate #6 (added 2026-05-07) addresses the **memory-log reflection-prose hallucination** failure mode that PR #54 + #55 surfaced (20% incidence rate; PM cascade failures from trusting hallucinated prose). The framework's memory log is now under formal Quality Gate discipline — but the module implementing it has 9.7% coverage.

**What's untested**:
- Pending → resolved transition flow (the cascade-failure-prone path)
- Reflection prose writer (the hallucination-prone subroutine)
- `<!-- ENTRY_END -->` separator parsing edge cases
- `memory_log_max_entries` rotation
- Empty / corrupt log resilience
- Concurrent-write safety (if any)

**Estimated effort to bring to ~80%**: 2-3h. Module is small enough (186 stmts) and the methodology already exists (`scripts/memory_log_integrity_check.py` PR #55 has 12 unit tests on the integrity-check tool — extend pattern to the underlying writer).

**Recommendation**: NOT autonomously launching a test-writing arc. This survey is the planning artifact. Operator decides whether to advance.

## Spec X-1 absence from gap list — confirmation

Recently-deployed `tradingagents/agents/utils/institutional_rotation_filter.py` is NOT in the <80% list. This confirms the PR #91/#92 test bundle achieved >80% coverage on the new module out-of-the-box. Spec deployment quality gate (~14 unit + 4 integration tests for ~190 LOC module) produced expected coverage.

## What this survey is NOT

- NOT a commit to writing more tests
- NOT a quality-gate failure
- NOT a regression report — 80.5% project coverage is stable + matches CLAUDE.md's claimed "81%+ project coverage" baseline

## Bigger picture

The project's testing posture is **mature for its research-substrate purpose**:

- Production-critical filter modules (Spec 003/004/006/007/008/X-1) all have dedicated test files at >80%
- Integration test coverage proves filter chain ordering + state log persistence
- External-API-bound modules legitimately stay low without harming research validity
- The single largest gap (memory.py at 9.7%) is in INTERNAL framework code that operators interact with via Quality Gate #6 (data-vs-prose discipline) — the gate codifies operator-side defense; module-level testing would extend code-side defense

The 80.5% baseline is healthy. The 9.7% memory.py gap is the only one that warrants targeted action — and only IF operators want to extend code-side defense beyond the existing operator-side discipline.

## Sibling docs

- `claudedocs/SETUP.md` section 10 — operator-facing filter portfolio guide
- `RESEARCH_FINDINGS.md` test-count line ("1134 unit + 2 integration passing")
- `.specify/memory/constitution.md` Quality Gate #6 — memory-log data-vs-prose discipline (operator-side defense for the under-tested memory.py module)
- `scripts/memory_log_integrity_check.py` — PR #55 reusable harness for memory-log integrity (the test pattern to extend if memory.py coverage is targeted)
