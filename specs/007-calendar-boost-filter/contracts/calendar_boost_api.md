# Contract: `tradingagents.agents.utils.calendar_boost`

**Branch**: `007-calendar-boost-filter` | **Date**: 2026-05-06

This contract defines the public API of the new helper module, the integration point in `forward_catalyst_filter.py`, and the configuration surface added to `default_config.py`. Implementation MUST satisfy these signatures and invariants exactly.

## Module: `tradingagents/agents/utils/calendar_boost.py`

### Public functions

```python
from datetime import datetime
import yfinance as yf
from functools import lru_cache


@lru_cache(maxsize=None)
def _fetch_earnings_dates(ticker: str) -> tuple[datetime, ...]:
    """Fetch earnings dates for a ticker, cached process-wide.

    Returns a sorted tuple of tz-naive datetimes (ascending). Empty tuple
    when yfinance fails OR returns empty calendar (ETFs, new IPOs, etc.).

    LRU cache: `maxsize=None` so all distinct tickers stay cached for
    process lifetime. Tests MUST call `_fetch_earnings_dates.cache_clear()`
    in setup/teardown to ensure ordering independence.
    """


def days_to_next_earnings(ticker: str, trade_date: str | datetime) -> int | None:
    """Calendar days from trade_date to the next earnings date >= trade_date.

    Returns None when:
        - Ticker has no earnings calendar (e.g., ETF, new IPO)
        - yfinance fetch fails
        - trade_date is unparseable (when passed as str)
        - All cached earnings are strictly before trade_date

    Otherwise returns int >= 0.

    Args:
        ticker: Equity ticker symbol (e.g., "NVDA"). May include exchange
            suffix (e.g., ".TO", ".L", ".HK", ".T") per project convention.
        trade_date: ISO 8601 date string ("YYYY-MM-DD") or datetime object.
    """


def calendar_boost(days_to_earnings: int | None, window: int) -> float:
    """Compute boost factor in [0.0, 1.0].

    Formula: max(0.0, 1.0 - days_to_earnings / window)

    Returns 0.0 when:
        - days_to_earnings is None
        - days_to_earnings < 0 (defensive; shouldn't happen)
        - days_to_earnings >= window
        - window <= 0 (defensive; operator config error)

    Otherwise: 1.0 at days=0, linearly decreasing to 0.0 at days=window.
    """


def apply_calendar_boost(
    score: float,
    days_to_earnings: int | None,
    window: int,
    magnitude: float,
) -> float:
    """Compute effective_score = min(1.0, score × (1 + magnitude × boost)).

    Where: boost = calendar_boost(days_to_earnings, window).

    Always returns a float in [0.0, 1.0]. The min(1.0, ...) clamp prevents
    super-saturation past the conventional [0, 1] score range.

    When boost = 0 (any of the calendar_boost zero-paths above), the
    effective score equals the input score (no change).
    """
```

### Invariants

- **I-1 (Boost monotonicity)**: For fixed `(window, magnitude)`, `calendar_boost(d1, w) >= calendar_boost(d2, w)` whenever `d1 <= d2` (boost is non-strictly decreasing in days).
- **I-2 (Effective score monotonicity)**: For fixed `(score, window, magnitude)`, `apply_calendar_boost(s, d1, w, m) >= apply_calendar_boost(s, d2, w, m)` whenever `d1 <= d2` (effective score is non-strictly decreasing in days). Verified by SC-002.
- **I-3 (No-boost identity)**: `apply_calendar_boost(s, None, w, m) == apply_calendar_boost(s, w, w, m) == s` for all `s in [0, 1]`, `w > 0`, `m >= 0` (when boost = 0, effective = score).
- **I-4 (Saturation clamp)**: `apply_calendar_boost(s, d, w, m) <= 1.0` for all valid inputs (the `min(1.0, ...)` clamp).
- **I-5 (Cache idempotency)**: Two calls to `_fetch_earnings_dates(t)` with the same `t` in the same process result in exactly one `yfinance.Ticker(t).earnings_dates` invocation. Verified by SC-004 mock-call-count test.
- **I-6 (Failure resilience)**: All four functions MUST NOT raise on any combination of `(None, negative, very large)` inputs OR yfinance failures. Verified by SC-003 mocked-failure test.

### Out-of-band contracts

- **C-1 (No global state mutation)**: The module MUST NOT mutate any global state other than the LRU cache on `_fetch_earnings_dates`. No log writes at INFO/WARNING/ERROR; DEBUG-level logging acceptable for cache misses.
- **C-2 (No new dependencies)**: Imports limited to: `from __future__ import annotations`, `from datetime import datetime`, `from functools import lru_cache`, `import yfinance as yf`. No new entries in `pyproject.toml` `[project.dependencies]`.
- **C-3 (UTF-8 file encoding)**: All file ops (none in this module) follow project convention `encoding="utf-8"`. N/A here since the module makes no file IO.

## Integration: `tradingagents/agents/utils/forward_catalyst_filter.py`

### Existing entry point (spec 007)

The function `evaluate_forward_catalyst(state, config) -> dict` is the spec 007 entry point. It currently:
1. Reads `bull_case_priced_in` and `bear_case_priced_in` from the LLM call output
2. Compares against `config["forward_catalyst_bull_threshold"]` / `config["forward_catalyst_bear_threshold"]`
3. Decides whether to fire based on `pm_rating`, mode (off/shadow/active), and threshold
4. Returns updated state with `state["forward_catalyst"]` annotation dict

### Spec 008 modification

Add a single conditional branch BEFORE the threshold comparison:

```python
# Spec 008 — Hybrid C calendar boost (FR-001..FR-009)
if config.get("hybrid_c_calendar_boost_enabled", False):
    from tradingagents.agents.utils.calendar_boost import (
        days_to_next_earnings,
        calendar_boost,
        apply_calendar_boost,
    )
    days = days_to_next_earnings(ticker, trade_date)
    boost = calendar_boost(days, config["hybrid_c_calendar_boost_window_days"])
    effective_bull = apply_calendar_boost(
        bull_case_priced_in,
        days,
        config["hybrid_c_calendar_boost_window_days"],
        config["hybrid_c_calendar_boost_magnitude"],
    )
    effective_bear = bear_case_priced_in  # FR-004: bull-only
    state["forward_catalyst"].update({
        "days_to_earnings": days,
        "calendar_boost": boost,
        "effective_bull_score": effective_bull,
        "effective_bear_score": effective_bear,
    })
else:
    effective_bull = bull_case_priced_in
    effective_bear = bear_case_priced_in
    # state["forward_catalyst"] not modified (FR-011)

# Then the existing spec 007 fire-decision logic uses effective_bull / effective_bear
```

### Integration invariants

- **II-1 (Decision-substitution scope)**: When the boost is enabled, `effective_bull` (NOT `bull_case_priced_in`) MUST be the input to the spec 007 bull-side fire-decision comparison. Bear-side comparison is unchanged (uses `bear_case_priced_in` directly per FR-004).
- **II-2 (Default-off identity)**: When `hybrid_c_calendar_boost_enabled=False`, `effective_bull == bull_case_priced_in` and `state["forward_catalyst"]` retains spec 007 baseline shape. Verified by SC-005.
- **II-3 (Spec 007 mode independence)**: The boost layer applies to score computation regardless of spec 007 mode (off/shadow/active). When spec 007 mode is "off", `evaluate_forward_catalyst` early-exits (existing behavior) BEFORE reaching the score computation, so the boost layer is never invoked. When spec 007 mode is "shadow", the boost still applies; the would-fire annotations reflect the boosted-score decision. When spec 007 mode is "active", the boost applies and fires actually downgrade.
- **II-4 (No PM hook chain change)**: The `evaluate_forward_catalyst` call site in `tradingagents/agents/managers/portfolio_manager.py` is unchanged. Spec 008 modifications are entirely INSIDE `evaluate_forward_catalyst`. Verified by absence of changes to `portfolio_manager.py` in the implementation diff.

## Configuration: `tradingagents/default_config.py`

### TypedDict additions

In the `TradingAgentsConfig` TypedDict, add (alphabetically near existing `forward_catalyst_*` keys):

```python
class TradingAgentsConfig(TypedDict):
    # ... existing keys ...
    hybrid_c_calendar_boost_enabled: bool
    hybrid_c_calendar_boost_window_days: int
    hybrid_c_calendar_boost_magnitude: float
    # ... existing keys ...
```

### DEFAULT_CONFIG entries

In the `DEFAULT_CONFIG` literal:

```python
DEFAULT_CONFIG: TradingAgentsConfig = {
    # ... existing entries ...
    "hybrid_c_calendar_boost_enabled": False,         # FR-007
    "hybrid_c_calendar_boost_window_days": 14,        # FR-008
    "hybrid_c_calendar_boost_magnitude": 0.5,         # FR-009
    # ... existing entries ...
}
```

### Configuration invariants

- **III-1 (Default-off)**: `DEFAULT_CONFIG["hybrid_c_calendar_boost_enabled"] is False` (literal boolean False, not 0 or "false").
- **III-2 (Type narrowing)**: `get_config()` returns `TradingAgentsConfig` per the existing pattern; the three new keys are typed and accessible via standard dict indexing.
- **III-3 (Operator override path)**: PARAMS.json + scripts/backtest.py `--config-override` mechanism (existing) MUST accept `hybrid_c_calendar_boost_enabled=true` and the two numeric overrides without changes — JSON literals already map to bool/int/float per existing pattern.

## Test contract surface

`tests/test_calendar_boost.py` MUST cover (per SC-001 + SC-002 + SC-003 + SC-004 + SC-006 + SC-010):

- I-1, I-2, I-3, I-4, I-5, I-6 invariants (one test each, minimum)
- Boundary: `days_to_earnings == window` exactly → boost = 0 (per the `>= window` strict path)
- Boundary: `score = 1.0` + `boost = 1.0` + `magnitude = 0.5` → effective = `min(1.0, 1.5)` = 1.0
- Mock test: yfinance raises → empty tuple cached, days_to_next_earnings returns None
- Mock test: yfinance returns empty DataFrame → empty tuple cached
- Mock test: same ticker called twice → mock.call_count == 1
- Parametrized monotonicity sweep over `days_to_earnings ∈ {0, 1, 7, 13, 14, 15, 30}`
- `_fetch_earnings_dates.cache_clear()` autouse fixture

`tests/test_forward_catalyst_filter_calendar_boost.py` MUST cover (per SC-005 + SC-007):

- Default-off: state["forward_catalyst"] dict-key set equals spec 007 baseline (no new keys)
- Enabled + earnings near: state["forward_catalyst"] gains all four new keys; `effective_bull_score > bull_case_priced_in`; rating downgrades to Hold
- Enabled + earnings far OR no calendar: state["forward_catalyst"] gains keys with `calendar_boost == 0` and `effective_bull_score == bull_case_priced_in`; no rating change
- Enabled + yfinance failure: same as far-earnings path (graceful degradation per SC-003 path-through)
