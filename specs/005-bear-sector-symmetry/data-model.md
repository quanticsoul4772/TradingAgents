# Phase 1: Data Model — Bear-Sector-Symmetry Filter (Spec 006)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Date**: 2026-05-06

---

## Entity reference

### `BearSectorSymmetryAnnotation` (dict)

Emitted to LangGraph state at `state["bear_sector_symmetry"]`. Persisted to the JSON state log via the `_log_state` whitelist extension (R-5).

| Field | Type | Notes |
|---|---|---|
| `mode` | `Literal["off", "shadow", "active"]` | Filter's mode at evaluation time |
| `sector` | `str \| None` | GICS sector resolved (None if `"Unknown"` or lookup failed) |
| `etf` | `str \| None` | ETF symbol the sector maps to; None if no mapping or sector unknown |
| `ticker_30d_return_pct` | `float \| None` | Ticker's prior-30-trading-day return as percent (e.g., `+18.32`); None if data unavailable |
| `etf_30d_return_pct` | `float \| None` | Sector ETF's prior-30-trading-day return as percent (e.g., `+6.40`); None if data unavailable |
| `relative_strength_pct` | `float \| None` | `ticker_30d_return_pct − etf_30d_return_pct`; None if either component is missing |
| `threshold_pct` | `float \| None` | Configured threshold as percent (e.g., `+5.0`); None if disabled |
| `lookback_days` | `int` | Lookback period actually used (default 30) |
| `would_fire` | `bool` | True iff `relative_strength_pct > threshold_pct AND pre_rating in {Underweight, Sell}` |
| `fired` | `bool` | True iff `would_fire AND mode == "active"` (rating actually overridden) |
| `pre_rating` | `str` | Rating BEFORE this filter (post the prior filters in chain) |
| `post_rating` | `str` | Rating AFTER this filter (equals `pre_rating` if mode != "active" or didn't fire) |
| `skipped` | `Literal["off", "unknown_sector", "no_etf_mapping", "missing_ticker_data", "missing_etf_data", "rating_not_bearish", "invalid_threshold"] \| None` | Reason filter didn't compute a fire decision; None if it did |

**Validation invariants** (asserted in `maybe_suppress_bear_rating()` before returning):
1. If `skipped == "off"`: `mode == "off"`, all other fields default-valued or None, `would_fire is False`, `fired is False`, `post_rating == pre_rating`.
2. If `skipped == "unknown_sector"`: `sector is None`, `etf is None`, `ticker_30d_return_pct is None`, `etf_30d_return_pct is None`, `relative_strength_pct is None`, `would_fire is False`.
3. If `skipped == "no_etf_mapping"`: `sector is not None`, `etf is None`, `would_fire is False`.
4. If `skipped == "missing_ticker_data"`: `sector is not None`, `etf is not None`, `ticker_30d_return_pct is None`, `relative_strength_pct is None`, `would_fire is False`.
5. If `skipped == "missing_etf_data"`: `sector is not None`, `etf is not None`, `etf_30d_return_pct is None`, `relative_strength_pct is None`, `would_fire is False`.
6. If `skipped == "rating_not_bearish"`: `pre_rating in {"Buy", "Overweight", "Hold"}`, `would_fire is False`.
7. If `skipped == "invalid_threshold"`: `threshold_pct is not None AND threshold_pct < 0`, `would_fire is False`.
8. If `skipped is None`: all of `sector`, `etf`, `ticker_30d_return_pct`, `etf_30d_return_pct`, `relative_strength_pct`, `threshold_pct` are populated.
9. If `fired is True`: `would_fire is True` AND `mode == "active"` AND `pre_rating in {"Underweight", "Sell"}` AND `post_rating == "Hold"`.
10. Strict-greater-than threshold semantics (R-3): `would_fire is True` requires `relative_strength_pct > threshold_pct`. Equality does NOT fire.
11. `relative_strength_pct == ticker_30d_return_pct − etf_30d_return_pct` whenever both components are populated.

### `SECTOR_ETF_MAP` (reused module-level constant)

Imported from `tradingagents/agents/utils/sector_momentum_filter.py` per FR-004. NOT redefined in this spec's module — single source of truth preserved. The 11-entry SPDR mapping is unchanged from spec 004:

| GICS sector key | Variant key | ETF |
|---|---|---|
| `"Technology"` | — | `"XLK"` |
| `"Financial Services"` | `"Financials"` | `"XLF"` |
| `"Healthcare"` | — | `"XLV"` |
| `"Energy"` | — | `"XLE"` |
| `"Consumer Cyclical"` | `"Consumer Discretionary"` | `"XLY"` |
| `"Consumer Defensive"` | `"Consumer Staples"` | `"XLP"` |
| `"Industrials"` | — | `"XLI"` |
| `"Communication Services"` | — | `"XLC"` |
| `"Utilities"` | — | `"XLU"` |
| `"Real Estate"` | — | `"XLRE"` |
| `"Basic Materials"` | `"Materials"` | `"XLB"` |

Sectors yfinance reports outside this table cause `skipped="no_etf_mapping"`.

### `_etf_history` + `_ticker_history` (cached fetchers)

- `_etf_history` — IMPORTED from `sector_momentum_filter.py` (R-2). Single LRU cache shared between spec 004 and spec 006; cache hits when both filters request the same ETF on the same date range.
- `_ticker_history` — NEW in this module. `@lru_cache(maxsize=128)` keyed by `(ticker, start, end)`. Returns yfinance DataFrame; empty on failure.
- Both fetchers raise no exceptions; failures degrade to empty frame + warning log + `skipped` annotation.

### Configuration extensions to `TradingAgentsConfig` (TypedDict)

Three new keys added to `tradingagents/default_config.py`:

| Key | Type | Default | Notes |
|---|---|---|---|
| `bear_sector_symmetry_filter_mode` | `Literal["off", "shadow", "active"]` | `"off"` | per FR-008; matches A3 + spec 004 introduction patterns |
| `bear_sector_symmetry_filter_threshold_pct` | `float \| None` | `None` | per FR-013; `None` IS the off switch (mirrors A3 + spec 004); negative values rejected at config-load with logged warning + `skipped="invalid_threshold"` |
| `bear_sector_symmetry_filter_lookback_days` | `int` | `30` | per R-9; matches A3 + spec 004 lookback default |

### `AgentState` TypedDict extension

New optional key in `tradingagents/agents/utils/agent_states.py`:

```python
class AgentState(MessagesState):
    # ... existing fields ...
    bear_sector_symmetry: NotRequired[dict | None]  # spec 006
```

Per R-5 + the spec 003 + spec 004 precedents: undeclared keys are silently dropped from LangGraph state merges. Declaring this key in the TypedDict ensures `final_state["bear_sector_symmetry"]` is preserved end-to-end.

---

## State transitions

### Filter evaluation (with all modes)

```
PM emits rating R for ticker T on date D
  └─> maybe_suppress_bear_rating(decision_markdown, T, D, get_config())
        ├─> if mode == "off":
        │     return decision_markdown unchanged
        │     emit annotation: skipped="off", mode="off"
        │
        ├─> if R not in {Underweight, Sell}:
        │     return decision_markdown unchanged
        │     emit annotation: skipped="rating_not_bearish", pre=R, post=R
        │
        ├─> if threshold < 0:
        │     return decision_markdown unchanged
        │     emit skipped="invalid_threshold" (with warning log)
        │
        ├─> if threshold is None:
        │     should not happen (mode=="off" path catches it earlier;
        │     defense-in-depth: emit skipped="off")
        │
        ├─> sector = get_sector(T, sectors_cache_path)
        ├─> if sector == "Unknown":
        │     return decision_markdown unchanged
        │     emit annotation: skipped="unknown_sector"
        │
        ├─> etf = SECTOR_ETF_MAP.get(sector)
        ├─> if etf is None:
        │     return decision_markdown unchanged
        │     emit annotation: skipped="no_etf_mapping", sector=sector
        │
        ├─> ticker_30d_return = trailing_ticker_return(T, D, lookback_days)
        ├─> if ticker_30d_return is None:
        │     return decision_markdown unchanged
        │     emit annotation: skipped="missing_ticker_data", sector, etf
        │
        ├─> etf_30d_return = trailing_etf_return(etf, D, lookback_days)
        ├─> if etf_30d_return is None:
        │     return decision_markdown unchanged
        │     emit annotation: skipped="missing_etf_data", sector, etf, ticker_30d_return
        │
        ├─> relative_strength = ticker_30d_return − etf_30d_return
        │
        ├─> would_fire = relative_strength > threshold  (strict greater-than)
        │
        ├─> if would_fire AND mode == "active":
        │     decision_markdown = downgrade_to_hold(decision_markdown, ...)
        │     fired = True
        │     post_rating = "Hold"
        │
        └─> emit full annotation; return decision_markdown (modified or not)
```

### PM hook chain order (per R-4 / FR-012)

```
PM emits rating from LLM call
  ↓
A3 momentum filter (per-ticker absolute bear suppression on UW/Sell when ticker is DOWN ≥5%)
  ↓
Bear-sector-symmetry filter (THIS SPEC — sector-relative bear suppression on UW/Sell when ticker is UP ≥5% relative to sector)
  ↓
Spec 003 contrarian gate (within-ticker prose-density bull suppression on Buy/OW)
  + Spec 003.5 sector-baseline fallback (cross-sector prose-density)
  ↓
Spec 004 sector-momentum filter (sector-ETF momentum bull suppression on Buy/OW)
  ↓
Final rating persisted to state
```

The two bear filters (A3 + spec 006) operate on near-disjoint price-condition cohorts; if A3 fires (ticker down ≥5% absolute → Hold), this filter no-ops (`skipped="rating_not_bearish"` because pre-rating is now Hold). Bull/bear filters never see each other's input ratings.

---

## Validation summary

All validation lives in `maybe_suppress_bear_rating()`. Failures:
- Threshold < 0 → log warning, return unmodified, `skipped="invalid_threshold"` (filter degrades to off for this evaluation)
- yfinance / sector lookup failures → `skipped` annotation reflects the failure mode + rating unchanged
- Annotation invariants from above asserted before returning the dict

The filter NEVER raises into the PM pipeline (FR-010 + matches A3's + spec 004's existing resilience pattern).

---

## Notes on persistence

- `state["bear_sector_symmetry"]` is a dict (or None when mode="off") populated each propagate when the filter runs. Persisted via the `_log_state` whitelist extension (R-5; one-line addition mirroring the precedents from commit `4c14d0f` for `contrarian_gate` and spec 004 for `sector_momentum`).
- `AgentState` TypedDict extension prevents the LangGraph silent-drop bug — same precedent as spec 003 + spec 004.
- `SECTOR_ETF_MAP` is reused from spec 004; not persisted.
- `TradingAgentsConfig` extensions persisted via the existing JSON serialization pattern in `default_config.py`.

---

## Backward compatibility

- `TradingAgentsConfig` extensions are additive — existing experiments' `PARAMS.json` files don't need modification (defaults apply).
- New `state["bear_sector_symmetry"]` field is additive — existing consumers (`daily_signals.py`, `scripts/contrarian_gate_retrospective.py`, `scripts/sector_momentum_retrospective.py`) ignore unknown state keys.
- Filter ordering (FR-012) places this filter SECOND in the chain (after A3) — existing A3 behavior is unchanged when this filter is in the default `"off"` mode (SC-006). Bull-side filters are unaffected (different rating set).
