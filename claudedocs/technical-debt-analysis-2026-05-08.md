# Technical debt analysis — 2026-05-08

**Date**: 2026-05-08
**Cost**: $0 (multi-domain static scan; mypy + ruff + pytest --collect + grep + line counts)
**Project state**: 1211 tests collected; ruff 0 errors; mypy 126 errors (filter portfolio at 0); 80.5% coverage

## TL;DR — 13 findings, 1 HIGH-leverage candidate

| # | Finding | Severity | Effort | Status |
|---|---|---|---|---|
| 1 | `agents/utils/memory.py` 9.7% coverage + 5 mypy errors | **HIGH** | 2-3h | Identified PR #99 + #103 |
| 2 | LLM client modules: 93 mypy errors (74% of floor) | MEDIUM | 8-12h | DEFERRED per CLAUDE.md baseline |
| 3 | Vendor integrations: 39 mypy errors | MEDIUM | 15-20h | DEFERRED |
| 4 | `signals/evaluation.py`: 666 LOC + 62.7% coverage | MEDIUM | 3-4h refactor + tests | New finding |
| 5 | Stale `__pycache__` for removed `brave_news` + `yfinance_news` modules | LOW | 1min | New finding (cleanup) |
| 6 | 22 `except Exception` patterns (mostly graceful-degradation; deliberate) | LOW | n/a | Audited; no action |
| 7 | claudedocs/ growth: 104 markdown files / 13,273 lines | LOW | 15-20min | Identified PR #102; deferred to operator |
| 8 | scripts/ sprawl: 61 scripts; no subdirectory organization | LOW | 1-2h structural | Speculative; needs spec |
| 9 | README + CLAUDE.md missing WC-10 mention (just deployed) | LOW | 15min | Doc drift |
| 10 | `outdated` deps: 23+ packages with newer versions available | LOW | n/a | Cosmetic; no security urgency |
| 11 | 0 actionable TODO/FIXME/HACK comments in codebase | INFO | n/a | Healthy |
| 12 | Pydantic v2 patterns consistent (`field_validator` only) | INFO | n/a | Healthy |
| 13 | Test mock convention consistent (`unittest.mock` only; 0 pytest-mock usage) | INFO | n/a | Healthy |

**Project-wide health**: ruff 0 errors, mypy floor stable at 126 (down from 305 at scaffolding install + 175 prior baseline; 5 of 9 production filters now at 0 errors). 1211 tests collected. Doc + memory coverage strong (104 claudedocs + 27 cross-session memories).

## Detailed findings

### 1. HIGH — `agents/utils/memory.py` 9.7% coverage + 5 mypy errors

**Background**: TradingMemoryLog module — append-only markdown memory with `_resolve_pending_entries()` writing the reflection prose that triggered Quality Gate #6 (PR #54 + #55 found 20% hallucination incidence rate).

**Why HIGH**: Constitution v1.4.5 Quality Gate #6 codifies operator-side defense (cross-check entry header data against reflection prose). Module-level testing would extend code-side defense. Also: it's the only internal module with BOTH low test coverage AND mypy errors.

**Untested paths** (from PR #99 survey):
- Pending → resolved transition flow (cascade-failure-prone)
- Reflection prose writer (hallucination-prone subroutine)
- `<!-- ENTRY_END -->` separator parsing edge cases
- `memory_log_max_entries` rotation
- Empty / corrupt log resilience

**Recommendation**: Single-PR effort — add ~10-12 unit tests covering above paths + fix the 5 mypy errors. Pattern exists in `scripts/memory_log_integrity_check.py` (PR #55, 12 unit tests on the integrity-check tool). 2-3h estimated.

### 2. MEDIUM — LLM client modules: 93 mypy errors (74% of floor)

| Module | Errors |
|---|---|
| `llm_clients/google_client.py` | 26 |
| `llm_clients/azure_client.py` | 24 |
| `llm_clients/openai_client.py` | 23 |
| `llm_clients/anthropic_client.py` | 20 |

**Root cause**: per-call-site `isinstance` narrowing on langchain `BaseChatModel.invoke()` kwargs. Pattern is well-defined but tedious.

**Why DEFERRED**: low ROI per CLAUDE.md baseline note. These errors don't surface real bugs; the surfaces are well-tested by existing 80%+ coverage. Fixing them is type-noise reduction.

### 3. MEDIUM — Vendor integration modules: 39 mypy errors

`alpha_vantage_*` (17 errors), `y_finance.py` (12), `interface.py` (6), `exa_news.py` (6), `alpha_vantage_common.py` (4). Untyped pandas DataFrame surfaces. Hard to fix without writing Protocol classes for vendor data shapes.

**Why DEFERRED**: same as #2 — type-noise reduction without bug-surfacing value. Existing test isolation (yfinance mocks per Spec 003/X-1 pattern) catches real issues.

### 4. MEDIUM — `signals/evaluation.py`: 666 LOC, 62.7% coverage

Single file — full evaluation methodology used by `analyze_backtest.py`. 121 of 324 statements uncovered.

**Hypothesis**: missing coverage is concentrated in per-rule counterfactual + custom-rule paths (lines 428-558, 574-666 from PR #99 survey).

**Recommendation**: ~3-4h to split into smaller modules + add coverage. Lower priority than #1 because the existing 62.7% covers the most-used paths.

### 5. LOW — Stale `__pycache__` for removed modules

`tradingagents/dataflows/__pycache__/brave_news.cpython-312.pyc` + `yfinance_news.cpython-312.pyc` persist even though source modules were removed 2026-05-03. Could shadow real imports if Python's bytecode-cache logic ever resurrects them.

**Fix**: `find . -name "__pycache__" -exec rm -rf {} +` (1 min, $0). Not committed (gitignored) but cleans local dev env.

### 6. LOW — `except Exception` pattern (22 occurrences)

Distribution:
- `portfolio_manager.py`: 6 try/except blocks (one per filter for resilience) — deliberate per spec design; each has `logger.warning`
- `agents/utils/*_filter.py`: 8 (graceful degradation per spec FR-013 patterns)
- Various scripts + paper module: 8 (mostly resilience patterns)

**Audit verdict**: NOT debt. Most have `# noqa: BLE001` annotations + downstream consumers expect graceful degradation. Could surface metrics aggregation but not a current pain point.

### 7. LOW — claudedocs/ growth: 104 markdown files / 13,273 lines

Per PR #102 backlog grooming survey, 10 files (~10%) are cleanup candidates: 1 DELETE (`research-burst-2026-05-08.md` day-rollover scaffold) + 9 SUPERSEDED-banner additions on mid-flight diagnostics.

**Why LOW**: Constitution Principle I (Save Everything) preserves research output. Cleanup is operator-discretionary; deferred per PR #102 verdict.

### 8. LOW — scripts/ sprawl (61 scripts)

`scripts/` directory has 61 Python files spanning backtest harnesses, retrospectives, feasibility probes, integrity checks, pilot harnesses. No subdirectory organization. Future operators may struggle to find the right script.

**Hypothetical reorg**: `scripts/research/` (retrospectives + probes + sweeps) + `scripts/pilot/` (backtest, single_call_baseline, daily_signals, wc_10_pilot) + `scripts/ops/` (new_experiment, findings_aggregate, smoke tests). Would need spec per Constitution VI. 1-2h work; speculative leverage.

**Why LOW**: project still navigates fine via grep + the docs/PROJECT_STRUCTURE.md PR #112 added; reorg is cosmetic.

### 9. LOW — README + CLAUDE.md missing WC-10 mention

WC-10 is mid-deployment (PRs #107-#114; pilot running now). README headline-finding paragraph was deliberately trimmed in PR #112 rewrite to remove dense narrative. CLAUDE.md "empirical filters" section still lists 9 production filters; WC-10 isn't one (it's a Tier 2 experiment, not a production filter).

**Actionable when WC-10 v1 ANALYSIS.md ships**: add 1-line WC-10 entry to README headline + 1-line entry to CLAUDE.md filter portfolio "Tier 2 experiments" subsection (new). Wait until pilot completes + verdict known.

### 10. LOW — Outdated deps (23+ packages)

Cosmetic; no security advisories. Most are minor-version bumps. Notable: `claude-agent-sdk` 0.1.57 → 0.1.77 (still pre-1.0 churn; not project-critical).

**Why LOW**: dependency-hell risk in this project's specific area (langgraph 1.x already broke things — see `feedback_global_conftest_autouse_for_real_llm.md` + memory of langgraph<1.0 pin in `reference_speckit_6pr_workflow_pattern.md`). Stable pins preferred.

### 11. INFO — 0 actionable TODO/FIXME comments

Only 2 hits across codebase, both false positives:
- `tradingagents/paper/digest.py:30` — docstring example `$XXX,XXX.XX`
- `tests/test_memory_log.py:547` — fixture name `XXXXXFAKE`

**Verdict**: healthy. No accumulated "I'll fix this later" debt comments.

### 12. INFO — Pydantic v2 consistency

Only 1 `@field_validator` usage (`PortfolioDecision.rating` from WC-10 PR #110). All other Pydantic models use field-default approach without explicit validators. No mix of v1 (`@validator`) and v2 (`@field_validator`) patterns.

### 13. INFO — Test mock convention

41 test files use `unittest.mock`. 0 use `pytest_mock` (`mocker.` fixture). Per WC-10 PR #91 lesson (memory: `reference_speckit_6pr_workflow_pattern.md`), pre-commit pytest-fast hook runs in uv venv that doesn't have pytest-mock — convention is consistent + enforced by environment.

## Recommendations

### Immediate ($0 / <30min each)

1. **Stale `__pycache__` cleanup** (1 min): `find . -name __pycache__ -exec rm -rf {} +`. Not even worth a PR.
2. **Memory file the brave_news/yfinance_news removal artifact** as a known-pattern (already in CLAUDE.md note; could be promoted).

### Medium-leverage ($0 / 2-4h)

3. **HIGH-leverage Category C target — `agents/utils/memory.py`**: bring to >80% coverage + 0 mypy errors. Single PR; most valuable internal-debt reduction. Overlaps with PR #99 + #103 surveys' identified target.

### Operator-discretionary

4. **claudedocs cleanup PR per PR #102 survey**: 1 DELETE + 9 SUPERSEDED banners (~15-20min, $0).
5. **Update README + CLAUDE.md after WC-10 ANALYSIS.md ships** — defer until SC-007 verdict known.
6. **scripts/ subdirectory reorg** — hypothetical; needs spec; speculative leverage.

### DEFERRED (per CLAUDE.md baseline)

7. LLM client + vendor integration mypy floor reduction (8-20h each; type-noise without bug-surfacing value).

## What this analysis is NOT

- NOT a commit to acting on any finding
- NOT a regression report (project state is healthy: ruff 0, tests passing, coverage 80.5%)
- NOT a security audit (cosmetic dep updates only; no security advisories)
- NOT a performance audit (would require profiling + benchmarks)

The planning artifact for operator decision: which of the 5 actionable findings (1, 5, 7, 9, scripts-reorg) to advance.

## Sibling docs

- `claudedocs/test-coverage-gap-analysis-2026-05-08.md` — PR #99; identified `memory.py` as highest-value gap (cross-confirmed here)
- `claudedocs/mypy-floor-reduction-2026-05-08.md` — PR #103; identified Category C as next target (cross-confirmed here)
- `claudedocs/backlog-grooming-claudedocs-survey-2026-05-08.md` — PR #102; cleanup candidates list
- `claudedocs/constitutional-compliance-audit-2026-05-08.md` — PR #105; today's PRs all compliant
- `CLAUDE.md` baseline section — claimed mypy floor 126; this analysis confirms (no drift)
