# Phase 0 Research — Spec 008 Hybrid C

**Branch**: `007-calendar-boost-filter` | **Date**: 2026-05-06

The spec is empirically grounded; almost all "research" was done in the retrospective phase (`claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`). This document resolves the few remaining technical-context unknowns before Phase 1.

## R-1: yfinance.earnings_dates API characteristics

**Decision**: Use `yfinance.Ticker(t).earnings_dates`, return value is a `pandas.DataFrame` indexed by tz-aware `DatetimeIndex` (US/Eastern timezone for US equities). Strip tz via `.tz_convert(None)` and convert to `list[datetime]` via `.to_pydatetime().tolist()`. Sort ascending. The Hybrid C retrospective script (`scripts/forward_catalyst_hybrid_c_retrospective.py:80`) already uses exactly this pattern — copy verbatim.

**Rationale**: Verified working in the retrospective for 18 of 18 unique tickers in the SC-008 cohort (NVDA, MSFT, AAPL, WFC, MA, COP, INTC, GOOGL, AMD, AMZN, AVGO, BAC, CSCO, GS, JPM, LLY, CVX, HON). The DataFrame can be empty (e.g., for ETFs); the helper's empty-result + exception paths both must return `None`. Index timezone differs across listings (e.g., London-listed tickers use Europe/London) — `.tz_convert(None)` normalizes.

**Alternatives considered**:
- `yfinance.Ticker(t).calendar` — returns NEXT earnings only, single value. Rejected because we need historical earnings as well for backtesting (a trade_date in 2025-Q4 needs earnings data from that period, not "the next earnings as of today's process invocation").
- Alpha Vantage `EARNINGS_CALENDAR` — would add API key dependency for what yfinance already provides for free.
- Hard-coded earnings calendar JSON — rejected as data freshness liability.

## R-2: LRU caching pattern

**Decision**: Use `functools.lru_cache(maxsize=None)` on the helper function `_fetch_earnings_dates(ticker: str) -> tuple[datetime, ...]`. Return tuple (immutable) so the cache value is hashable + read-only. The wrapping `days_to_next_earnings(ticker, trade_date)` calls `_fetch_earnings_dates` and computes the day delta; the inner function is the cache key.

**Rationale**: Stdlib, zero new dependency, well-understood semantics, automatic per-process scoping (cleared on process exit per FR-006 + SC-004). `maxsize=None` is acceptable because the typical universe is ≤50 tickers per propagate (most are 1-10) and `earnings_dates` payloads are small (~1 KB each).

**Alternatives considered**:
- Custom dict-based cache: equivalent semantics but boilerplate.
- `cachetools.LRUCache` with TTL: TTL not needed (cache scope is process lifetime per assumption "LRU cache scope is process lifetime"); adds external dependency.
- `@functools.cache` (Py3.9+, simpler API): equivalent; we use `lru_cache(maxsize=None)` for explicitness.

## R-3: Strict greater-than threshold semantics

**Decision**: The fire decision uses `effective_bull_score > forward_catalyst_bull_threshold` (strict `>`). This matches Spec 007 SC-002 + the existing comparison operator in `forward_catalyst_filter.py`.

**Rationale**: Existing precedent. SC-006 makes this a regression-tested boundary semantic. Loose `>=` would allow scores that exactly equal the threshold to fire, which conflicts with spec 007's contract (operators relying on threshold-exact-no-fire semantics).

**Alternatives considered**: Loose `>=`: rejected per spec 007 precedent.

## R-4: State annotation persistence path

**Decision**: Add the four new fields (`days_to_earnings`, `calendar_boost`, `effective_bull_score`, `effective_bear_score`) to the existing `state["forward_catalyst"]` dict that spec 007 already populates. The persistence layer (`tradingagents/graph/trading_graph.py:_log_state`) already whitelists `"forward_catalyst"`, so no whitelist changes needed. The `AgentState` TypedDict already declares `forward_catalyst: Annotated[dict, ...]`, so the new dict keys flow through without schema changes.

**Rationale**: Reuses spec 007 plumbing. The "spec 003 state-merge bug" precedent (LangGraph silently drops undeclared keys from state merges) does NOT apply here because `forward_catalyst` is already declared — adding nested dict keys to an already-typed dict slot doesn't trigger the merge-drop behavior.

**Alternatives considered**:
- New top-level `state["calendar_boost"]` dict: would require AgentState schema addition + `_log_state` whitelist extension. Rejected as over-engineering for what's structurally an enhancement of an existing field.
- Promote `effective_bull_score` to a top-level `state["forward_catalyst_effective"]`: rejected for same reason.

## R-5: Backward-compat path (default-off integrity)

**Decision**: When `config["hybrid_c_calendar_boost_enabled"]` is `False`, the helper module is NOT invoked AT ALL. The `forward_catalyst_filter.py` integration is a single early-exit branch:

```python
if config.get("hybrid_c_calendar_boost_enabled", False):
    effective_bull = apply_calendar_boost(
        score=bull_case_priced_in,
        days_to_earnings=days_to_next_earnings(ticker, trade_date),
        window=config["hybrid_c_calendar_boost_window_days"],
        magnitude=config["hybrid_c_calendar_boost_magnitude"],
    )
    state["forward_catalyst"].update({...four fields...})
else:
    effective_bull = bull_case_priced_in
    # state["forward_catalyst"] not modified
```

The four new fields are added ONLY in the True branch; the False branch leaves the dict shape byte-equivalent to spec 007 baseline (FR-011 + SC-005).

**Rationale**: Default-off means literal no-op. SC-005's "dict-key equivalence" assertion is satisfied trivially.

**Alternatives considered**:
- Always populate the four fields with sentinel values (e.g., `{days_to_earnings: None, calendar_boost: 0, ...}`): rejected because it changes the shape of existing-operator state logs without their opt-in. The corpus-aggregation scripts (`findings_aggregate.py`, `analyze_backtest.py`, `forward_catalyst_retrospective.py`) would see new keys without a config flag indicating Spec 008 was active.

## R-6: Test mocking strategy for yfinance

**Decision**: Mock `yfinance.Ticker` at the import site in `calendar_boost.py` (i.e., `tradingagents.agents.utils.calendar_boost.yf.Ticker`). Use `unittest.mock.patch` with `return_value` shaped to match the real `earnings_dates` DataFrame (DatetimeIndex tz-aware). For the LRU cache test (SC-004), mock at the same site and assert `mock.call_count == 1` after two calls with the same ticker.

**Rationale**: Standard pytest pattern. Existing `tests/test_sector_momentum_filter.py` (spec 004) uses the same mocking strategy for yfinance — copy that pattern for consistency.

**Alternatives considered**:
- pytest-mock `mocker.patch`: equivalent; project uses unittest.mock directly elsewhere, stay consistent.
- VCR-style HTTP fixtures: overkill for a deterministic helper with a single API surface.

## R-7: Cache invalidation on test runs

**Decision**: Tests that exercise the LRU cache MUST explicitly clear it via `_fetch_earnings_dates.cache_clear()` in setup/teardown. Otherwise, test order can leak cached values between tests.

**Rationale**: Standard `functools.lru_cache` hygiene. The pytest fixture pattern: `@pytest.fixture(autouse=True)` at module level that calls `cache_clear()` before each test.

**Alternatives considered**:
- `lru_cache` per-call: defeats the purpose of caching.
- Skip the `autouse` fixture and accept test-order dependency: rejected per pytest best practices (tests should be order-independent).

## All NEEDS CLARIFICATION resolved

The plan's Technical Context has no remaining `NEEDS CLARIFICATION` markers. Phase 1 can proceed.
