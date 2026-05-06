# Contract: Sector-Momentum Annotation Schema

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

The dict that lands at `state["sector_momentum"]` (and is persisted to the JSON state log via `_log_state` whitelist extension per R-5).

---

## Schema

```json
{
  "mode": "shadow",                              // off | shadow | active
  "sector": "Financial Services",                // GICS sector or null
  "etf": "XLF",                                  // Sector ETF symbol or null
  "etf_30d_return_pct": -8.32,                   // Prior-N-day ETF return as percent or null
  "threshold_pct": -5.0,                         // Configured threshold as percent or null
  "lookback_days": 30,                           // Lookback period actually used
  "would_fire": true,                            // strict-less-than threshold AND bullish rating
  "fired": false,                                // would_fire AND mode == "active"
  "pre_rating": "Overweight",                    // Rating BEFORE this filter
  "post_rating": "Overweight",                   // Rating AFTER (== pre if mode != "active")
  "skipped": null                                // Reason filter didn't compute, or null if it did
}
```

---

## Examples

### Active mode, filter fires (Buy → Hold)

```json
{
  "mode": "active",
  "sector": "Financial Services",
  "etf": "XLF",
  "etf_30d_return_pct": -7.85,
  "threshold_pct": -5.0,
  "lookback_days": 30,
  "would_fire": true,
  "fired": true,
  "pre_rating": "Overweight",
  "post_rating": "Hold",
  "skipped": null
}
```

### Shadow mode, filter would fire (annotation only; no override)

```json
{
  "mode": "shadow",
  "sector": "Financial Services",
  "etf": "XLF",
  "etf_30d_return_pct": -7.85,
  "threshold_pct": -5.0,
  "lookback_days": 30,
  "would_fire": true,
  "fired": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
  "skipped": null
}
```

### Threshold not crossed (sector ETF return above threshold)

```json
{
  "mode": "active",
  "sector": "Technology",
  "etf": "XLK",
  "etf_30d_return_pct": -2.1,
  "threshold_pct": -5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
  "skipped": null
}
```

### Off mode (filter disabled)

```json
{
  "mode": "off",
  "sector": null,
  "etf": null,
  "etf_30d_return_pct": null,
  "threshold_pct": null,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
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
  "etf_30d_return_pct": null,
  "threshold_pct": -5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
  "skipped": "unknown_sector"
}
```

### Skipped: bullish-only filter sees Hold

```json
{
  "mode": "active",
  "sector": null,
  "etf": null,
  "etf_30d_return_pct": null,
  "threshold_pct": -5.0,
  "lookback_days": 30,
  "would_fire": false,
  "fired": false,
  "pre_rating": "Hold",
  "post_rating": "Hold",
  "skipped": "rating_not_bullish"
}
```

---

## Field invariants (asserted by `maybe_suppress_bull_rating`)

1. `skipped == "off"` ⇒ `mode == "off"`, all data fields default/None, `would_fire=False`, `fired=False`, `post_rating == pre_rating`.
2. `skipped == "unknown_sector"` ⇒ `sector is None`, `etf is None`, `etf_30d_return_pct is None`, `would_fire=False`.
3. `skipped == "no_etf_mapping"` ⇒ `sector is not None`, `etf is None`, `would_fire=False`.
4. `skipped == "missing_etf_data"` ⇒ `sector is not None`, `etf is not None`, `etf_30d_return_pct is None`, `would_fire=False`.
5. `skipped == "rating_not_bullish"` ⇒ `pre_rating in {"Hold", "Underweight", "Sell"}`, `would_fire=False`.
6. `skipped == "invalid_threshold"` ⇒ filter degrades to off for this evaluation; warning logged.
7. `skipped is None` ⇒ all of `sector`, `etf`, `etf_30d_return_pct`, `threshold_pct` are populated.
8. `fired is True` ⇒ `would_fire is True` AND `mode == "active"` AND `pre_rating in {"Buy", "Overweight"}` AND `post_rating == "Hold"`.
9. Strict less-than threshold: `would_fire is True` requires `etf_30d_return_pct < threshold_pct` (equality does NOT fire).

---

## Persistence path

LangGraph state → `state["sector_momentum"]` → JSON state log via `trading_graph.py:_log_state` whitelist extension. Same path as Spec 003's `contrarian_gate` field (precedent: commit `4c14d0f`).

---

## Backward compatibility

Additive change. Existing consumers ignore unknown state keys; existing analysis scripts continue to work. The `_log_state` whitelist extension is a one-line change that mirrors the prior precedent.

---

## Test fixtures

- `tests/test_sector_momentum_filter.py::test_annotation_active_fires_on_overweight` — full populated dict with `fired=True`, `post_rating="Hold"`.
- `tests/test_sector_momentum_filter.py::test_annotation_shadow_records_would_fire_only` — `would_fire=True`, `fired=False`, `post_rating == pre_rating`.
- `tests/test_sector_momentum_filter.py::test_annotation_off_returns_none_or_off_skipped` — `mode == "off"` produces None or off-skipped dict.
- `tests/test_sector_momentum_filter.py::test_annotation_unknown_sector_skipped` — sector lookup returns "Unknown" → skipped="unknown_sector", rating unchanged.
- `tests/test_sector_momentum_filter.py::test_annotation_no_etf_mapping_skipped` — synthetic sector not in SECTOR_ETF_MAP → skipped="no_etf_mapping".
- `tests/test_sector_momentum_filter.py::test_annotation_missing_etf_data_skipped` — yfinance returns empty frame → skipped="missing_etf_data".
- `tests/test_sector_momentum_filter.py::test_annotation_rating_not_bullish_skipped` — Hold/UW/Sell → skipped="rating_not_bullish".
- `tests/test_sector_momentum_filter.py::test_annotation_invariant_fired_implies_active_mode` — invariant 8.
- `tests/test_sector_momentum_filter.py::test_annotation_strict_less_than_threshold` — boundary: `etf_30d_return_pct == threshold_pct` does NOT fire.
