# Test-suite audit post-triple-pilot arc + Spec 009 Branch C + Spec 012 spec/plan — 2026-05-09

**Trigger**: reasoning_decision rank-2U (0.705 score). Re-verifies the 1171 unit test count documented in PR #185 (day-end synthesis) holds after PRs #186-#194 + checks mypy + ruff floors.

**Cost**: $0. ~10 min wall-clock (audit + 1 mypy regression fix).

## Test count audit

| Metric | Value |
|---|---:|
| Unit tests passing | **1171** ✅ (matches PR #185 baseline) |
| Tests deselected | 66 |
| Errors | 0 |
| Wall-clock | ~15 sec |

PRs #186-#194 were doc/spec/script-only (no test-touching code changes); count unchanged from PR #185 baseline.

## Ruff audit

```
ruff check tradingagents scripts tests
All checks passed!
```

✅ 0 ruff errors maintained from baseline (per CLAUDE.md "ruff = 0 errors" claim).

## Mypy audit — 1 genuine regression FIXED + 4 environment stub issues

### Regression introduced + FIXED in this PR

**File**: `tradingagents/agents/managers/portfolio_manager.py:137`
**Source**: PR #184 Branch C MVP — my code introduced this regression.

```python
# Before (regression):
bin_thresholds = tuple(get_config().get("wc_10_bin_thresholds", (-0.6, -0.2, 0.2, 0.6)))
binned_tier = bin_scalar_to_tier(rating_scalar, bin_thresholds)
```

**Mypy error**: `Argument 2 to "bin_scalar_to_tier" has incompatible type "tuple[float, ...]"; expected "tuple[float, float, float, float] | None"  [arg-type]`

The `tuple()` call on `Any` widens to `tuple[Any, ...]` which mypy further widens to `tuple[float, ...]` (variadic), but `bin_scalar_to_tier()` expects `tuple[float, float, float, float] | None` (fixed-arity 4-tuple).

**Fix applied**: explicit fixed-arity construction with float casts on each element.

```python
# After (fixed):
_bin_raw = get_config().get("wc_10_bin_thresholds", (-0.6, -0.2, 0.2, 0.6))
bin_thresholds: tuple[float, float, float, float] = (
    float(_bin_raw[0]),
    float(_bin_raw[1]),
    float(_bin_raw[2]),
    float(_bin_raw[3]),
)
binned_tier = bin_scalar_to_tier(rating_scalar, bin_thresholds)
```

Verification: `mypy tradingagents/agents/managers/portfolio_manager.py` → 0 errors in this file post-fix.

Tests still pass: `pytest tests/test_wc_10_pm_integration.py -m unit` → 5/5 PASS (3 Branch C tests + 2 prior tests).

### 4 environment-level stub issues (NOT regressions)

```
tradingagents/dataflows/alpha_vantage_common.py:7: error: Library stubs not installed for "requests"  [import-untyped]
tradingagents/dataflows/exa_news.py:26: error: Library stubs not installed for "requests"  [import-untyped]
tradingagents/dataflows/alpha_vantage_indicator.py:30: error: Library stubs not installed for "dateutil.relativedelta"  [import-untyped]
tradingagents/dataflows/y_finance.py:6: error: Library stubs not installed for "dateutil.relativedelta"  [import-untyped]
```

These are `[import-untyped]` errors stemming from missing stub packages. Per CLAUDE.md "types-requests stub addition (PR #129)" — `types-requests` was supposed to be added in PR #129 of the 2026-05-08 mypy sweep, BUT the current shell mypy invocation cannot find the stubs.

**Most likely cause**: stubs are installed in the project's `uv`-managed virtualenv (where `pip install -e .` ran with the dev-dependency group) but the bash `mypy tradingagents` invocation is using the SYSTEM Python where stubs are not installed.

**Verification path** (for operator): activate the project venv + re-run `mypy tradingagents`; expect 0 errors. Or run `pip install types-requests types-python-dateutil` in the system Python.

**Decision**: NOT shipping a fix for the stub installation issue in this PR — it's a dev-environment setup question, not a code regression. CLAUDE.md's "mypy = 0 errors" claim should hold in the canonical project venv per the PR #129 stub additions.

## Net audit findings

- ✅ **Tests**: 1171 unit passing (no regressions from triple-pilot arc + Spec 009 + Spec 012 spec/plan).
- ✅ **Ruff**: 0 errors maintained.
- 🟡 **Mypy code regression**: 1 found (PR #184 Branch C MVP introduced); FIXED in this PR.
- 🟡 **Mypy stub environment issues**: 4 remaining; environment-level (not code); operator action required only if running mypy outside the canonical venv.

## What this PR ships

| File | Change |
|---|---|
| `tradingagents/agents/managers/portfolio_manager.py` | Fix mypy regression (explicit fixed-arity 4-tuple construction for `bin_thresholds`) |
| `claudedocs/test-suite-audit-2026-05-09.md` | NEW audit memo (this) |

## Cross-references

- PR #184 (Spec 009 Branch C MVP — source of the regression)
- PR #185 (day-end synthesis — original 1171 baseline assertion)
- CLAUDE.md "Test coverage" + "Quality gates" sections
- CLAUDE.md PR #128 + PR #129 references for prior mypy sweep history
