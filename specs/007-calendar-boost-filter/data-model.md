# Phase 1 Data Model — Spec 008 Hybrid C

**Branch**: `007-calendar-boost-filter` | **Date**: 2026-05-06

Spec 008 adds derived numeric values + cache state. No new persistence or schema changes.

## Entities

### CalendarBoost

| Field | Type | Constraints | Source |
|---|---|---|---|
| value | `float` | `[0.0, 1.0]` | Computed: `max(0.0, 1.0 - days_to_earnings / window)` when `days_to_earnings is not None and days_to_earnings >= 0`; else `0.0` |

**Derivation**: Pure function of `(days_to_earnings, window)`. Not persisted as an entity; flows through to `EffectiveScore`. Surfaced in state log as `state["forward_catalyst"]["calendar_boost"]`.

**Validation**: `0.0 ≤ value ≤ 1.0`. Boundary values: `value = 1.0` when `days_to_earnings == 0`; `value = 0.0` when `days_to_earnings >= window` OR `days_to_earnings is None` OR `days_to_earnings < 0`.

### EffectiveScore

| Field | Type | Constraints | Source |
|---|---|---|---|
| value | `float` | `[0.0, 1.0]` | Computed: `min(1.0, base_score × (1.0 + magnitude × calendar_boost))` |

**Derivation**: Pure function of `(base_score, calendar_boost, magnitude)`. The `min(1.0, ...)` clamp prevents super-saturation (e.g., base=0.95 + magnitude=0.5 + boost=1.0 raw = 1.425, clamped to 1.0). Surfaced as `state["forward_catalyst"]["effective_bull_score"]` and `state["forward_catalyst"]["effective_bear_score"]` (the bear field always equals `bear_case_priced_in` per FR-004).

**Validation**: `0.0 ≤ value ≤ 1.0`. When `calendar_boost == 0` (no earnings data, or earnings far away): `effective = base × (1 + 0) = base` (no change).

### DaysToNextEarnings

| Field | Type | Constraints | Source |
|---|---|---|---|
| value | `int \| None` | `value >= 0` if not None | Computed: `(next_earnings_after_trade_date - trade_date).days` from `EarningsCalendarCache[ticker]`; `None` if no upcoming earnings, ticker missing from cache, or trade_date unparseable |

**Derivation**: Lookup against the `EarningsCalendarCache` for the ticker. Filters cached datetimes by `>= trade_date`, returns delta to the earliest such date.

**Validation**: `None` is valid (signals no calendar data — graceful degradation per FR-010). When non-None: `value >= 0` (next earnings cannot be in the past relative to trade_date).

### EarningsCalendarCache

| Field | Type | Constraints | Source |
|---|---|---|---|
| `_fetch_earnings_dates(ticker)` cache | `functools.lru_cache(maxsize=None)` | tuple of `datetime` (immutable, hashable) | `yfinance.Ticker(ticker).earnings_dates` once per process per ticker |

**Lifecycle**:
- Created lazily on first call to `_fetch_earnings_dates(ticker)`
- Persisted in-process for entire process lifetime
- Cleared on process exit (no disk persistence)
- Cleared explicitly by tests via `_fetch_earnings_dates.cache_clear()` in autouse fixture

**Failure modes** (FR-010 + SC-003):
- yfinance raises (network failure, ticker not found): helper catches, returns empty tuple `()`. Subsequent `days_to_next_earnings` returns `None`. Cache stores the empty result so the failed lookup isn't retried within the process.
- yfinance returns `None` or empty DataFrame: same path — empty tuple cached.

## State annotation extensions

The existing `state["forward_catalyst"]` dict (declared in `tradingagents/agents/utils/agent_states.py` as `Annotated[dict, ...]` per spec 007) gains four new keys when `hybrid_c_calendar_boost_enabled=True`:

| Key | Type | Always present? | Description |
|---|---|---|---|
| `days_to_earnings` | `int \| None` | Only when boost enabled | Calendar days from trade_date to next earnings; None if unavailable. |
| `calendar_boost` | `float` | Only when boost enabled | Boost factor in `[0.0, 1.0]`. |
| `effective_bull_score` | `float` | Only when boost enabled | Boosted bull-side score in `[0.0, 1.0]` used in spec 007 fire decision. |
| `effective_bear_score` | `float` | Only when boost enabled | Equals `bear_case_priced_in` per FR-004 (bear-side never boosted). Included for symmetry and audit completeness. |

When boost is disabled (`hybrid_c_calendar_boost_enabled=False`, the default), these four keys are NOT added — `state["forward_catalyst"]` retains the exact spec 007 shape (FR-011 + SC-005).

## Configuration entity (TradingAgentsConfig)

Three new keys added to `tradingagents/default_config.py`:

| Key | Type | Default | Validation | FR |
|---|---|---|---|---|
| `hybrid_c_calendar_boost_enabled` | `bool` | `False` | n/a | FR-007 |
| `hybrid_c_calendar_boost_window_days` | `int` | `14` | `> 0` (operationally; not enforced at config load — operator's responsibility) | FR-008 |
| `hybrid_c_calendar_boost_magnitude` | `float` | `0.5` | `>= 0.0` (operationally; magnitude=0 would disable the boost effectively without disabling the helper invocation) | FR-009 |

Added to the `TradingAgentsConfig` TypedDict (in `default_config.py`) so `get_config()` consumers see the new keys with correct types. Mirror the spec 007 pattern (`forward_catalyst_bull_threshold: float`, `forward_catalyst_bear_threshold: float`, etc.).

## State transitions

There are no explicit state transitions — Hybrid C is a stateless function applied at one call site (within `forward_catalyst_filter.evaluate_forward_catalyst()`). The LRU cache is implementation detail; logically, the boost computation is deterministic given `(base_score, ticker, trade_date, window, magnitude)`.

The relevant "state transition" is the spec 007 fire-decision change:
- **Pre-Hybrid C decision input**: `bull_case_priced_in`
- **Post-Hybrid C decision input** (when enabled): `effective_bull_score = min(1.0, bull_case_priced_in × (1 + magnitude × boost))`
- **Decision rule**: identical (`> bull_threshold` strict greater-than, FR-013)

## Relationships

```
yfinance.Ticker(t).earnings_dates  ─┐
                                     ├──> EarningsCalendarCache (LRU)
                                     │
trade_date ──────────────────────────┴──> DaysToNextEarnings
                                                  │
hybrid_c_calendar_boost_window_days ─────────────┴──> CalendarBoost
                                                              │
bull_case_priced_in (from spec 007 LLM call) ────────────────┤
hybrid_c_calendar_boost_magnitude ───────────────────────────┴──> EffectiveScore
                                                                          │
forward_catalyst_bull_threshold (from spec 007 config) ──────────────────┤
                                                                          ▼
                                                              spec 007 fire decision (downgrade Buy/OW → Hold)
```
