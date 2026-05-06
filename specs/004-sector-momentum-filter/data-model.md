# Phase 1: Data Model — Sector-Momentum Filter

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Date**: 2026-05-06

---

## Entity reference

### `SectorMomentumAnnotation` (dict)

Emitted to LangGraph state at `state["sector_momentum"]`. Persisted to the JSON state log via the `_log_state` whitelist extension (R-5).

| Field | Type | Notes |
|---|---|---|
| `mode` | `Literal["off", "shadow", "active"]` | Filter's mode at evaluation time |
| `sector` | `str \| None` | GICS sector resolved (None if `"Unknown"` or lookup failed) |
| `etf` | `str \| None` | ETF symbol the sector maps to; None if no mapping or sector unknown |
| `etf_30d_return_pct` | `float \| None` | Sector ETF's prior-30-trading-day return as percent (e.g., `-8.32`); None if data unavailable |
| `threshold_pct` | `float \| None` | Configured threshold as percent (e.g., `-5.0`); None if disabled |
| `lookback_days` | `int` | Lookback period actually used (default 30) |
| `would_fire` | `bool` | True iff `etf_30d_return_pct < threshold_pct AND pre_rating in {Buy, Overweight}` |
| `fired` | `bool` | True iff `would_fire AND mode == "active"` (rating actually overridden) |
| `pre_rating` | `str` | Rating BEFORE this filter (post the prior filters in chain) |
| `post_rating` | `str` | Rating AFTER this filter (equals `pre_rating` if mode != "active" or didn't fire) |
| `skipped` | `Literal["off", "unknown_sector", "no_etf_mapping", "missing_etf_data", "rating_not_bullish", "invalid_threshold"] \| None` | Reason filter didn't compute a fire decision; None if it did |

**Validation invariants** (asserted in `maybe_suppress_bull_rating()` before returning):
1. If `skipped == "off"`: `mode == "off"`, all other fields default-valued or None, `would_fire is False`, `fired is False`, `post_rating == pre_rating`.
2. If `skipped == "unknown_sector"`: `sector is None`, `etf is None`, `etf_30d_return_pct is None`, `would_fire is False`.
3. If `skipped == "no_etf_mapping"`: `sector is not None`, `etf is None`, `would_fire is False`.
4. If `skipped == "missing_etf_data"`: `sector is not None`, `etf is not None`, `etf_30d_return_pct is None`, `would_fire is False`.
5. If `skipped == "rating_not_bullish"`: `pre_rating in {"Hold", "Underweight", "Sell"}`, `would_fire is False`.
6. If `skipped is None`: all of `sector`, `etf`, `etf_30d_return_pct`, `threshold_pct` are populated.
7. If `fired is True`: `would_fire is True` AND `mode == "active"` AND `pre_rating in {"Buy", "Overweight"}` AND `post_rating == "Hold"`.
8. Strict-less-than threshold semantics (R-3): `would_fire is True` requires `etf_30d_return_pct < threshold_pct`. Equality does NOT fire.

### `SECTOR_ETF_MAP` (module-level constant)

Hardcoded dict at `tradingagents/agents/utils/sector_momentum_filter.py`. Maps GICS sector names (yfinance + GICS canonical variants) to SPDR sector ETF symbols per FR-004 and R-10.

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

Implementation as a simple dict with both keys mapping to the same ETF (no normalization layer needed). Sectors yfinance reports outside this table cause `skipped="no_etf_mapping"`.

### Configuration extensions to `TradingAgentsConfig` (TypedDict)

Three new keys added to `tradingagents/default_config.py`:

| Key | Type | Default | Notes |
|---|---|---|---|
| `sector_momentum_filter_mode` | `Literal["off", "shadow", "active"]` | `"off"` | per FR-008; matches A3 introduction pattern |
| `sector_momentum_filter_threshold_pct` | `float \| None` | `None` | per FR-013; `None` IS the off switch (mirrors A3); positive values rejected at config-load with logged warning + `skipped="invalid_threshold"` |
| `sector_momentum_filter_lookback_days` | `int` | `30` | per R-9; matches A3's lookback default |

---

## State transitions

### Filter evaluation (with all modes)

```
PM emits rating R for ticker T on date D
  └─> maybe_suppress_bull_rating(decision_markdown, T, D, get_config())
        ├─> if mode == "off":
        │     return decision_markdown unchanged
        │     emit annotation: skipped="off", mode="off"
        │
        ├─> if R not in {Buy, Overweight}:
        │     return decision_markdown unchanged
        │     emit annotation: skipped="rating_not_bullish", pre=R, post=R
        │
        ├─> if threshold > 0 OR threshold is None:
        │     return decision_markdown unchanged
        │     if threshold > 0: emit skipped="invalid_threshold" (with warning log)
        │     if threshold is None: should not happen (mode=="off" path catches it earlier)
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
        ├─> etf_30d_return = trailing_etf_return(etf, D, lookback_days)
        ├─> if etf_30d_return is None:
        │     return decision_markdown unchanged
        │     emit annotation: skipped="missing_etf_data", sector, etf
        │
        ├─> would_fire = etf_30d_return < threshold  (strict less-than)
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
A3 momentum filter (bear suppression)
  ↓
Spec 003 contrarian gate (within-ticker prose-density bull suppression)
  + Spec 003.5 sector-baseline fallback (cross-sector prose-density)
  ↓
Spec 004 sector-momentum filter (sector-ETF momentum bull suppression)
  ↓
Final rating persisted to state
```

Each filter sees the rating left by the previous filter. If a prior filter has already turned the rating to Hold (e.g. spec 003 fired), this filter no-ops (`skipped="rating_not_bullish"`).

---

## Validation summary

All validation lives in `maybe_suppress_bull_rating()`. Failures:
- Threshold > 0 → log warning, return unmodified, `skipped="invalid_threshold"` (filter degrades to off for this evaluation)
- yfinance / sector lookup failures → `skipped` annotation reflects the failure mode + rating unchanged
- Annotation invariants from above asserted before returning the dict

The filter NEVER raises into the PM pipeline (FR-010 + matches A3's existing resilience pattern at `momentum_filter.py:93-104`).

---

## Notes on persistence

- `state["sector_momentum"]` is a dict (or None when mode="off") populated each propagate when the gate runs. Persisted via the `_log_state` whitelist extension (R-5; one-line addition mirroring the precedent set by commit `4c14d0f` for `contrarian_gate`).
- `SECTOR_ETF_MAP` is a module-level constant; not persisted.
- `TradingAgentsConfig` extensions persisted via the existing JSON serialization pattern in `default_config.py`.

---

## Backward compatibility

- `TradingAgentsConfig` extensions are additive — existing experiments' `PARAMS.json` files don't need modification (defaults apply).
- New `state["sector_momentum"]` field is additive — existing consumers (`daily_signals.py`, `scripts/contrarian_gate_retrospective.py`) ignore unknown state keys.
- Filter ordering (FR-012) places this filter LAST in the chain — existing A3 + spec 003 / 003.5 behavior is unchanged when this filter is in the default `"off"` mode (SC-006).
