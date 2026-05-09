# Tests inventory audit — 2026-05-09

**Trigger**: reasoning_decision rank-10J (0.535 score). Audits the test inventory post 1193-test count for organization + marker discipline + structural health.

**Cost**: $0. ~10 min wall-clock.

## Headline numbers

| Metric | Value |
|---|---:|
| Total tests collected | **1259** |
| Test files | **76** (excluding conftest.py) |
| Unit-marked tests (`-m unit`) | **1193** (94.8%) |
| Integration-marked tests (`-m integration`) | 2 (0.2%) |
| Smoke-marked tests (`-m smoke`) | 0 (0%) |
| Unmarked tests | 64 (5.1%) |

## Marker discipline

✅ **Strong unit-marker discipline**: 94.8% of tests are explicitly unit-marked. The `-m unit` filter (which CLAUDE.md describes as the canonical test command) reliably scopes to the intended test surface.

✅ **Integration tests are sparse (2)** — by design. The project has historically folded integration patterns into unit-marked tests using mock fixtures (per `tests/test_institutional_rotation_pm_integration.py` precedent + Spec 012's `tests/test_class_4_pm_integration.py`). PM-integration tests use `@pytest.mark.unit` + LLM/yfinance mocks rather than the integration marker. This is intentional + working.

✅ **No smoke tests** — smoke tests are operator-runs via standalone `scripts/smoke_*.py` files (per CLAUDE.md "Commands" section), not pytest tests. Healthy separation.

🟡 **64 unmarked tests** (~5%) — these typically don't need the unit marker because they're dataflow/helper tests that don't fit the unit/integration/smoke trichotomy cleanly. Acceptable but slight inconsistency with the dominant unit-marker pattern.

## Top test files by test count

| File | Tests | Domain |
|---|---:|---|
| `test_signals_phase15_featurization.py` | 65 | Spec 001 Phase 1.5 (within-IC featurization) |
| `test_memory_log.py` | 61 | TradingMemoryLog (decision log) |
| `test_signals_bots_phase1.py` | 44 | Spec 001 Phase 1 (bots architecture) |
| `test_experiments_ids.py` | 38 | scripts/new_experiment.py id generation |
| `test_extended_signals.py` | 37 | extended fundamental data tools |
| `test_daily_signals.py` | 32 | scripts/daily_signals.py operator surface |
| `test_signals_phase2.py` | 31 | Spec 001 Phase 2 |
| `test_signals_phase0.py` | 31 | Spec 001 Phase 0 |
| `test_experiments_templates.py` | 30 | scripts/new_experiment.py templates |
| `test_contrarian_gate.py` | 30 | Spec 003 |
| `test_second_opinion.py` | 29 | Phase C reasoning_evidence |
| `test_forward_catalyst_filter.py` | 29 | Spec 007 |
| `test_bear_sector_symmetry_filter.py` | 28 | Spec 006 |
| `test_portfolio_manager_filter_integration.py` | 27 | PM integration (cross-spec) |
| `test_calendar_boost.py` | 27 | Spec 008 |

The distribution is well-balanced across:
- Spec 001 (signals/bots architecture): 65 + 44 + 31 + 31 = 171 tests (largest category; consistent with multi-phase scope)
- Filter modules (Spec 003-008 + X-1 + Spec 012): ~180 tests across 9 files
- Operator-surface scripts (daily_signals, new_experiment): ~70 tests
- TradingMemoryLog + state-log: ~80 tests
- LLM clients + analyst factories: ~50 tests

## Spec 012 contribution to test count

Today's Spec 012 5-PR bundle added 22 net-new tests:
- `tests/test_macro_environment_filter.py`: 13 unit tests
- `tests/test_class_4_pm_integration.py`: 4 PM integration tests
- `tests/test_class4_macro_shadow_audit.py`: 3 audit-script tests
- `tests/test_trading_graph.py`: +2 state-log persistence regression tests

Cumulative test growth across the 4-day arc: ~1022 → **1193 unit tests** (+171; ~17% increase).

## Mypy + ruff floor verification

Per PR #207 end-of-day verification + PR #195 mypy regression fix:
- mypy code regressions: 0 (1 introduced + fixed today)
- mypy env-stub errors: 3 (env-level; not regressions; documented per PR #195)
- ruff errors: 0 maintained

## Structural observations

1. **Test files mirror production module structure** — every production filter module has a matching `test_<filter>.py` file (verified: A3 momentum_filter has tests via test_portfolio_manager_filter_integration; Spec 003-008 + X-1 + Spec 012 all have dedicated test files).

2. **PM integration test pattern** is now established + reusable: `test_<filter>_pm_integration.py` (Spec X-1 PR #92 precedent; Spec 012 PR #198 follow). All future filter specs should follow.

3. **State-log persistence regression tests** are concentrated in `test_trading_graph.py` (cumulative file size grew today via Spec 012 +2 tests). This file is the canonical "filter annotation persists" guard.

4. **Conftest autouse fixtures** are stable — `tests/conftest.py` provides placeholder API keys for all providers + autouse-disable LLM client creation for tests that need to enforce LLM-call-free paths (per memory `feedback_global_conftest_autouse_for_real_llm.md`).

## No action items

The test inventory is healthy. Marker discipline is strong (94.8% unit-marked). Module-test pairing is consistent. No file consolidations or refactors warranted. No stale skip markers (none found in the audit grep).

## Future cleanup triggers

Trigger a tests inventory re-audit when:
- Test count exceeds 1500 (would warrant test-file consolidation review)
- New test marker introduced (e.g., `slow` or `network` if test runtime grows)
- Unmarked test percentage exceeds 10% (suggests marker discipline drift)

Currently: 1259 collected / 5.1% unmarked → all metrics within healthy bounds.

## Cost

$0 LLM. ~10 min wall-clock.

## Cross-references

- PR #207 end-of-day verification (1193 unit-test floor)
- PR #195 mypy regression fix
- PR #198 Spec 012 MVP test additions (+17 net-new)
- PR #199 Spec 012 audit-script tests (+5 net-new)
- Memory: `feedback_global_conftest_autouse_for_real_llm.md` (autouse fixture pattern)
- CLAUDE.md "Quality gates" section
