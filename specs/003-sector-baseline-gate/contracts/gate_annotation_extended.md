# Contract: Extended Gate Annotation Schema

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

The dict that lands at `state["contrarian_gate"]` (per Spec 003 + the persistence fix in commit `4c14d0f`). This contract defines the schema delta vs Spec 003's original annotation. **Backward-compatible**: existing fields are unchanged; new fields are additive.

---

## Spec 003 fields (unchanged)

```json
{
  "mode": "shadow",                        // off | shadow | active
  "feature_value": 75.0,                   // bull_keyword_count of current market_report
  "percentile": 92.0,                      // percentile of feature_value vs whichever baseline drove the decision
  "n_history": 13,                         // alias for whichever baseline's pool size
  "would_fire": true,                      // percentile >= threshold AND PM rating in {Buy, Overweight}
  "gate_fired": false,                     // would_fire AND mode == "active"
  "pm_rating_pre_gate": "Overweight",      // 5-tier rating before the hook
  "pm_rating_post_gate": "Overweight",     // 5-tier rating after the hook (== pre if mode != "active")
  "skipped": null                          // null | mode_off | insufficient_history | missing_source_signal | missing_featurizer
}
```

---

## New fields (additive in this spec)

```json
{
  "gate_baseline": "sector",               // per_ticker | sector | none — which baseline drove the decision
  "n_history_per_ticker": 13,              // size of per-ticker pool considered (always populated)
  "n_history_sector": 80                   // size of sector pool considered (0 if "Unknown" sector or feature flag False)
}
```

---

## Full extended annotation example

```json
{
  "mode": "shadow",
  "feature_value": 75.0,
  "percentile": 92.0,
  "n_history": 80,                         // alias points to sector pool because gate_baseline=="sector"
  "would_fire": true,
  "gate_fired": false,                     // shadow mode
  "pm_rating_pre_gate": "Overweight",
  "pm_rating_post_gate": "Overweight",
  "skipped": null,
  "gate_baseline": "sector",
  "n_history_per_ticker": 13,              // per-ticker had insufficient history (< 20)
  "n_history_sector": 80                   // sector pool was sufficient (>= 20)
}
```

---

## Field invariants (asserted by `ContrarianGate.compute_annotation`)

1. If `gate_baseline == "per_ticker"`: `n_history_per_ticker >= per_ticker_floor` (default 20) AND `percentile is not None` AND `n_history == n_history_per_ticker`.
2. If `gate_baseline == "sector"`: `n_history_per_ticker < per_ticker_floor` AND `n_history_sector >= sector_floor` (default 20) AND `percentile is not None` AND `n_history == n_history_sector`.
3. If `gate_baseline == "none"`: BOTH `n_history_per_ticker < per_ticker_floor` AND `n_history_sector < sector_floor`. `percentile is None`. `would_fire is False`. `gate_fired is False`. `n_history` is 0 (or absent — implementer's choice; consumers should accept either). `skipped == "insufficient_history"`.
4. If `mode == "off"`: NO annotation is emitted at all (state["contrarian_gate"] is None or absent). Same as Spec 003.

---

## Backward-compatibility guarantees

- Existing consumers (`scripts/contrarian_gate_retrospective.py`, `scripts/sc003_financials_gate_check.py`, `scripts/contrarian_gate_retrospective.py`, `daily_signals.py`) read field names directly. Existing fields keep their existing meaning. Adding fields does not break them.
- `n_history` semantics shift slightly: previously it was always the per-ticker pool size; now it's the SIZE OF WHICHEVER POOL DROVE THE DECISION (per-ticker if `gate_baseline=="per_ticker"`, sector if `"sector"`, 0 if `"none"`). Consumers that displayed `n_history` as "per-ticker history N" should use `n_history_per_ticker` instead going forward; their existing display still produces a meaningful number, just one with different semantics.
- The `skipped` field's `"insufficient_history"` value now means "neither per-ticker nor sector pool qualified" rather than just "per-ticker pool insufficient." Same string; broader semantics.

---

## Persistence path

- LangGraph state → `state["contrarian_gate"]` → JSON state log via `trading_graph.py:425-453` whitelist (per commit `4c14d0f` 2026-05-06 fix).
- Future event-log integration (e.g., the paper-trading harness emitting one event per gate firing) is out of scope for this spec.

---

## Test fixtures

- `tests/test_contrarian_gate_fallback.py::test_gate_baseline_per_ticker_when_history_thick` — per-ticker N≥20, sector path NOT consulted.
- `tests/test_contrarian_gate_fallback.py::test_gate_baseline_sector_when_per_ticker_thin` — per-ticker N<20, sector N≥20, sector percentile drives decision.
- `tests/test_contrarian_gate_fallback.py::test_gate_baseline_none_when_both_thin` — both pools below floor, gate doesn't fire.
- `tests/test_contrarian_gate_fallback.py::test_n_history_alias_matches_active_baseline` — `n_history` value matches whichever pool fired.
- `tests/test_contrarian_gate.py::test_byte_identity_with_fallback_disabled` (NEW; SC-002) — running with `contrarian_gate_sector_fallback_enabled=False` produces byte-identical decisions vs spec 003 base behavior.
