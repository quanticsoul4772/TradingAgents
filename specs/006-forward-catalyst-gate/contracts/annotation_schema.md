# Contract: Forward-Catalyst Annotation Schema

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

The dict that lands at `state["forward_catalyst"]` (and is persisted to the JSON state log via `_log_state` whitelist extension per R-5).

---

## Schema

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.78,
  "bear_case_priced_in": 0.45,
  "rationale": "The bull case (iPhone 17 supercycle, services growth) is widely covered...",
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "shadow",
  "would_fire_bull": true,
  "would_fire_bear": false,
  "fired_bull": true,
  "fired_bear": false,
  "pre_rating": "Overweight",
  "post_rating": "Hold",
  "skipped": null,
  "error": null
}
```

---

## Examples

### Active mode bull side, filter fires (Overweight → Hold)

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.78,
  "bear_case_priced_in": 0.45,
  "rationale": "...",
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "shadow",
  "would_fire_bull": true,
  "would_fire_bear": false,
  "fired_bull": true,
  "fired_bear": false,
  "pre_rating": "Overweight",
  "post_rating": "Hold",
  "skipped": null,
  "error": null
}
```

### Active mode bear side, filter fires (Underweight → Hold; bear active)

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.45,
  "bear_case_priced_in": 0.65,
  "rationale": "...",
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "active",
  "would_fire_bull": false,
  "would_fire_bear": true,
  "fired_bull": false,
  "fired_bear": true,
  "pre_rating": "Underweight",
  "post_rating": "Hold",
  "skipped": null,
  "error": null
}
```

### Shadow mode bear side (default), filter would fire but does NOT override

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.45,
  "bear_case_priced_in": 0.65,
  "rationale": "...",
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "shadow",
  "would_fire_bull": false,
  "would_fire_bear": true,
  "fired_bull": false,
  "fired_bear": false,
  "pre_rating": "Underweight",
  "post_rating": "Underweight",
  "skipped": null,
  "error": null
}
```

### Threshold not crossed (both scores below thresholds)

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.45,
  "bear_case_priced_in": 0.40,
  "rationale": "...",
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "shadow",
  "would_fire_bull": false,
  "would_fire_bear": false,
  "fired_bull": false,
  "fired_bear": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
  "skipped": null,
  "error": null
}
```

### Both modes off (no LLM call; zero cost)

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": null,
  "bear_case_priced_in": null,
  "rationale": null,
  "bull_threshold": null,
  "bear_threshold": null,
  "bull_mode": "off",
  "bear_mode": "off",
  "would_fire_bull": false,
  "would_fire_bear": false,
  "fired_bull": false,
  "fired_bear": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
  "skipped": "off",
  "error": null
}
```

In both-modes-off, the field MAY be `None` instead of an annotation dict, at the implementer's discretion. Both forms are documented as valid.

### LLM call failed

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": null,
  "bear_case_priced_in": null,
  "rationale": null,
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "shadow",
  "would_fire_bull": false,
  "would_fire_bear": false,
  "fired_bull": false,
  "fired_bear": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
  "skipped": "llm_failed",
  "error": "anthropic.APITimeoutError: Request timed out after 30s"
}
```

### Invalid threshold (bull side)

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.78,
  "bear_case_priced_in": 0.40,
  "rationale": "...",
  "bull_threshold": 1.5,
  "bear_threshold": 0.50,
  "bull_mode": "off",
  "bear_mode": "shadow",
  "would_fire_bull": false,
  "would_fire_bear": false,
  "fired_bull": false,
  "fired_bear": false,
  "pre_rating": "Overweight",
  "post_rating": "Overweight",
  "skipped": "invalid_threshold",
  "error": null
}
```

(LLM was still called because bear side was valid; bull side reduced to "off" for this evaluation.)

### Pre-filter chain produced Hold (rating not actionable)

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.78,
  "bear_case_priced_in": 0.45,
  "rationale": "...",
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "shadow",
  "would_fire_bull": false,
  "would_fire_bear": false,
  "fired_bull": false,
  "fired_bear": false,
  "pre_rating": "Hold",
  "post_rating": "Hold",
  "skipped": null,
  "error": null
}
```

(LLM was called; annotation captured for audit; both sides no-op because Hold is neither bullish nor bearish.)

---

## Field invariants (asserted by `evaluate_forward_catalyst`)

1. `skipped == "off"` ⇒ `bull_mode == "off" AND bear_mode == "off"`, all data fields default/None, `would_fire_*` False, `fired_*` False, `post_rating == pre_rating`.
2. `skipped == "llm_failed"` ⇒ `bull_case_priced_in is None`, `bear_case_priced_in is None`, `rationale is None`, `error is not None`, `would_fire_*` False, `fired_*` False.
3. `skipped == "invalid_threshold"` ⇒ at least one of `bull_threshold` / `bear_threshold` outside [0, 1]; filter degrades to off for that side; warning logged.
4. `skipped is None` ⇒ both LLM scores populated, at least one mode != "off", both thresholds populated for the active side(s).
5. `fired_bull is True` ⇒ `would_fire_bull is True` AND `bull_mode == "active"` AND `pre_rating in {"Buy", "Overweight"}` AND `post_rating == "Hold"`.
6. `fired_bear is True` ⇒ `would_fire_bear is True` AND `bear_mode == "active"` AND `pre_rating in {"Underweight", "Sell"}` AND `post_rating == "Hold"`.
7. `fired_bull AND fired_bear` is impossible (pre_rating can be either bullish OR bearish, not both); enforced by structural check in `evaluate_forward_catalyst`.
8. Strict greater-than threshold semantics: `would_fire_bull is True` requires `bull_case_priced_in > bull_threshold` (equality does NOT fire). Same for bear.

---

## Persistence path

LangGraph state → `state["forward_catalyst"]` → JSON state log via `trading_graph.py:_log_state` whitelist extension. Same path as Spec 003's `contrarian_gate` field, Spec 004's `sector_momentum` field, and Spec 006's `bear_sector_symmetry` field. AgentState TypedDict extension prevents the LangGraph silent-drop bug (R-5).

---

## Backward compatibility

Additive change. Existing consumers ignore unknown state keys; existing analysis scripts continue to work. The `_log_state` whitelist extension + `AgentState` TypedDict extension are one-line changes that mirror the prior precedents.

**NEW behavior**: every propagate now incurs an LLM call by default (Opus ~$0.025). Operators can disable via setting BOTH `forward_catalyst_bull_mode` AND `forward_catalyst_bear_mode` to `"off"` in PARAMS.json or config override (FR-013 escape hatch).

---

## Test fixtures

- `tests/test_forward_catalyst_filter.py::test_annotation_active_bull_fires_full_dict` — full populated dict with `fired_bull=True`, `post_rating="Hold"`.
- `tests/test_forward_catalyst_filter.py::test_annotation_active_bear_fires_full_dict` — full populated dict with `fired_bear=True`, `post_rating="Hold"`.
- `tests/test_forward_catalyst_filter.py::test_annotation_shadow_bull_records_would_fire_only` — `would_fire_bull=True`, `fired_bull=False`, `post_rating == pre_rating`.
- `tests/test_forward_catalyst_filter.py::test_annotation_shadow_bear_records_would_fire_only` — same for bear side; default behavior when `bear_mode="shadow"`.
- `tests/test_forward_catalyst_filter.py::test_annotation_off_returns_off_skipped_or_none` — both modes off → annotation with skipped="off" OR None.
- `tests/test_forward_catalyst_filter.py::test_annotation_llm_failure_skipped_with_error` — LLM exception → `skipped="llm_failed"` + `error` populated + scores None.
- `tests/test_forward_catalyst_filter.py::test_annotation_invalid_threshold_skipped` — out-of-range threshold → `skipped="invalid_threshold"`.
- `tests/test_forward_catalyst_filter.py::test_annotation_invariant_fired_bull_implies_active_mode_buy_overweight` — invariant 5.
- `tests/test_forward_catalyst_filter.py::test_annotation_invariant_fired_bear_implies_active_mode_underweight_sell` — invariant 6.
- `tests/test_forward_catalyst_filter.py::test_annotation_strict_greater_than_threshold_bull` — boundary: `bull_case_priced_in == bull_threshold` does NOT fire.
- `tests/test_forward_catalyst_filter.py::test_annotation_strict_greater_than_threshold_bear` — same for bear.
- `tests/test_forward_catalyst_filter.py::test_annotation_fired_mutually_exclusive` — invariant 7.
- `tests/test_trading_graph.py::test_state_log_persists_forward_catalyst_field` — regression-guard for the `_log_state` whitelist extension (parallel to spec 003 + spec 004 + spec 006 tests).
- `tests/test_trading_graph.py::test_state_log_forward_catalyst_is_none_when_field_absent` — when both modes off OR field omitted, persisted log has `"forward_catalyst": null`.
