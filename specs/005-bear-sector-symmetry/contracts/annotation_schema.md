# Contract: Bear-Sector-Symmetry Annotation Schema

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

The dict that lands at `state["bear_sector_symmetry"]` (and is persisted to the JSON state log via `_log_state` whitelist extension per R-5).

---

## Schema

```json
{
  "mode": "shadow",                              // off | shadow | active
  "sector": "Technology",                        // GICS sector or null
  "etf": "XLK",                                  // Sector ETF symbol or null
  "ticker_30d_return_pct": 18.32,                // Prior-N-day ticker return as percent or null
  "etf_30d_return_pct": 6.40,                    // Prior-N-day ETF return as percent or null
  "relative_strength_pct": 11.92,                // ticker - etf or null
  "threshold_pct": 5.0,                          // Configured threshold as percent or null
  "lookback_days": 30,                           // Lookback period actually used
  "would_fire": true,                            // strict-greater-than threshold AND bearish rating
  "fired": false,                                // would_fire AND mode == "active"
  "pre_rating": "Underweight",                   // Rating BEFORE this filter
  "post_rating": "Underweight",                  // Rating AFTER (== pre if mode != "active")
  "skipped": null                                // Reason filter didn't compute, or null if it did
}
```

---

## Examples

### Active mode, filter fires (Underweight → Hold)

```json
{
  "mode": "active",
  "sector": "Technology",
  "etf": "XLK",
  "ticker_30d_return_pct": 18.32,
  "etf_30d_return_pct": 6.40,
  "relative_strength_pct": 11.92,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": true,
  "fired": true,
  "pre_rating": "Underweight",
  "post_rating": "Hold",
  "skipped": null
}
```

### Active mode, filter fires (Sell → Hold)

```json
{
  "mode": "active",
  "sector": "Technology",
  "etf": "XLK",
  "ticker_30d_return_pct": 22.50,
  "etf_30d_return_pct": 6.40,
  "relative_strength_pct": 16.10,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": true,
  "fired": true,
  "pre_rating": "Sell",
  "post_rating": "Hold",
  "skipped": null
}
```

### Shadow mode, filter would fire (annotation only; no override)

```json
{
  "mode": "shadow",
  "sector": "Technology",
  "etf": "XLK",
  "ticker_30d_return_pct": 18.32,
  "etf_30d_return_pct": 6.40,
  "relative_strength_pct": 11.92,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": true,
  "fired": false,
  "pre_rating": "Underweight",
  "post_rating": "Underweight",
  "skipped": null
}
```

### Threshold not crossed (relative-strength delta below threshold)

```json
{
  "mode": "active",
  "sector": "Technology",
  "etf": "XLK",
  "ticker_30d_return_pct": 8.40,
  "etf_30d_return_pct": 6.40,
  "relative_strength_pct": 2.00,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Underweight",
  "post_rating": "Underweight",
  "skipped": null
}
```

### Off mode (filter disabled)

```json
{
  "mode": "off",
  "sector": null,
  "etf": null,
  "ticker_30d_return_pct": null,
  "etf_30d_return_pct": null,
  "relative_strength_pct": null,
  "threshold_pct": null,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Underweight",
  "post_rating": "Underweight",
  "skipped": "off"
}
```

In off mode the field MAY be `None` instead of an annotation dict, at the implementer's discretion. Both forms are documented as valid.

### Skipped: unknown sector

```json
{
  "mode": "active",
  "sector": null,
  "etf": null,
  "ticker_30d_return_pct": null,
  "etf_30d_return_pct": null,
  "relative_strength_pct": null,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Underweight",
  "post_rating": "Underweight",
  "skipped": "unknown_sector"
}
```

### Skipped: bearish-only filter sees Hold (e.g. A3 already fired)

```json
{
  "mode": "active",
  "sector": null,
  "etf": null,
  "ticker_30d_return_pct": null,
  "etf_30d_return_pct": null,
  "relative_strength_pct": null,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Hold",
  "post_rating": "Hold",
  "skipped": "rating_not_bearish"
}
```

### Skipped: missing ticker data (recently IPO'd, etc.)

```json
{
  "mode": "active",
  "sector": "Technology",
  "etf": "XLK",
  "ticker_30d_return_pct": null,
  "etf_30d_return_pct": null,
  "relative_strength_pct": null,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Underweight",
  "post_rating": "Underweight",
  "skipped": "missing_ticker_data"
}
```

### Skipped: missing ETF data (very early date pre-1998, etc.)

```json
{
  "mode": "active",
  "sector": "Technology",
  "etf": "XLK",
  "ticker_30d_return_pct": 12.40,
  "etf_30d_return_pct": null,
  "relative_strength_pct": null,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Underweight",
  "post_rating": "Underweight",
  "skipped": "missing_etf_data"
}
```

---

## Field invariants (asserted by `maybe_suppress_bear_rating`)

1. `skipped == "off"` ⇒ `mode == "off"`, all data fields default/None, `would_fire=False`, `fired=False`, `post_rating == pre_rating`.
2. `skipped == "unknown_sector"` ⇒ `sector is None`, `etf is None`, `ticker_30d_return_pct is None`, `etf_30d_return_pct is None`, `relative_strength_pct is None`, `would_fire=False`.
3. `skipped == "no_etf_mapping"` ⇒ `sector is not None`, `etf is None`, `would_fire=False`.
4. `skipped == "missing_ticker_data"` ⇒ `sector is not None`, `etf is not None`, `ticker_30d_return_pct is None`, `relative_strength_pct is None`, `would_fire=False`.
5. `skipped == "missing_etf_data"` ⇒ `sector is not None`, `etf is not None`, `etf_30d_return_pct is None`, `relative_strength_pct is None`, `would_fire=False`.
6. `skipped == "rating_not_bearish"` ⇒ `pre_rating in {"Buy", "Overweight", "Hold"}`, `would_fire=False`.
7. `skipped == "invalid_threshold"` ⇒ filter degrades to off for this evaluation; warning logged.
8. `skipped is None` ⇒ all of `sector`, `etf`, `ticker_30d_return_pct`, `etf_30d_return_pct`, `relative_strength_pct`, `threshold_pct` are populated.
9. `fired is True` ⇒ `would_fire is True` AND `mode == "active"` AND `pre_rating in {"Underweight", "Sell"}` AND `post_rating == "Hold"`.
10. Strict greater-than threshold: `would_fire is True` requires `relative_strength_pct > threshold_pct` (equality does NOT fire).
11. `relative_strength_pct == ticker_30d_return_pct − etf_30d_return_pct` whenever both components are populated.

---

## Persistence path

LangGraph state → `state["bear_sector_symmetry"]` → JSON state log via `trading_graph.py:_log_state` whitelist extension. Same path as Spec 003's `contrarian_gate` field (precedent: commit `4c14d0f`) and Spec 004's `sector_momentum` field. AgentState TypedDict extension prevents the LangGraph silent-drop bug (R-5).

---

## Backward compatibility

Additive change. Existing consumers ignore unknown state keys; existing analysis scripts continue to work. The `_log_state` whitelist extension + `AgentState` TypedDict extension are one-line changes that mirror the prior precedents.

---

## Test fixtures

- `tests/test_bear_sector_symmetry_filter.py::test_annotation_active_fires_on_underweight` — full populated dict with `fired=True`, `post_rating="Hold"`.
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_active_fires_on_sell` — same but on Sell.
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_shadow_records_would_fire_only` — `would_fire=True`, `fired=False`, `post_rating == pre_rating`.
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_off_returns_none_or_off_skipped` — `mode == "off"` produces None or off-skipped dict.
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_unknown_sector_skipped` — sector lookup returns "Unknown" → skipped="unknown_sector", rating unchanged.
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_no_etf_mapping_skipped` — synthetic sector not in SECTOR_ETF_MAP → skipped="no_etf_mapping".
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_missing_ticker_data_skipped` — yfinance ticker returns empty frame → skipped="missing_ticker_data".
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_missing_etf_data_skipped` — yfinance ETF returns empty frame → skipped="missing_etf_data".
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_rating_not_bearish_skipped` — Hold/Buy/OW → skipped="rating_not_bearish".
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_invariant_fired_implies_active_mode` — invariant 9.
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_strict_greater_than_threshold` — boundary: `relative_strength_pct == threshold_pct` does NOT fire.
- `tests/test_bear_sector_symmetry_filter.py::test_annotation_relative_strength_arithmetic` — invariant 11.
- `tests/test_trading_graph.py::test_state_log_persists_bear_sector_symmetry_field` — regression-guard for the `_log_state` whitelist extension (parallel to the spec 003 + spec 004 tests).
