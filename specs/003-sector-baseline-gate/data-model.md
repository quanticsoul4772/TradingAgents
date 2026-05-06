# Phase 1: Data Model — Sector-Baseline Fallback

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Date**: 2026-05-06

---

## Entity reference

### `SectorBaselineSource` (string enum)

A 3-valued string indicating which baseline the gate consulted when evaluating a propagate.

| Value | When |
|---|---|
| `"per_ticker"` | The per-ticker history had ≥ FR-004 floor observations; spec 003's original baseline was used; sector pool was NOT consulted |
| `"sector"` | Per-ticker history was below floor; sector-pool baseline was used and had ≥ FR-003 floor observations; sector percentile drove the decision |
| `"none"` | Both per-ticker and sector pools were below their floors; gate did not fire (regardless of `bull_keyword_count` value) |

### `GateAnnotation` (extended from spec 003)

The annotation dict emitted by the gate and persisted to `state["contrarian_gate"]` (per `trading_graph.py:425-453` whitelist after commit `4c14d0f`).

**Existing fields (unchanged from spec 003)**:

| Field | Type | Notes |
|---|---|---|
| `mode` | `Literal["off", "shadow", "active"]` | from `contrarian_gate_mode` config |
| `feature_value` | `float | None` | the current propagate's `bull_keyword_count` value; None if signal/feature unavailable |
| `percentile` | `float | None` | percentile rank of `feature_value` against the chosen baseline; None if no baseline qualified |
| `n_history` | `int | None` | size of the WHICHEVER baseline drove the decision (alias for backward compat) |
| `would_fire` | `bool` | True iff percentile ≥ threshold AND PM rating in {Buy, Overweight} |
| `gate_fired` | `bool` | True iff would_fire AND mode == "active" (i.e., decision was actually downgraded) |
| `pm_rating_pre_gate` | `str` | The 5-tier rating the PM emitted before this hook |
| `pm_rating_post_gate` | `str` | The 5-tier rating after this hook (may equal pre if mode != "active") |
| `skipped` | `Literal["mode_off", "insufficient_history", "missing_source_signal", "missing_featurizer"] | None` | reason gate didn't compute, None if it did |

**New fields (additive in this spec)**:

| Field | Type | Notes |
|---|---|---|
| `gate_baseline` | `Literal["per_ticker", "sector", "none"]` | which baseline was consulted; "none" iff both pools were below their floors |
| `n_history_per_ticker` | `int` | size of the per-ticker history pool considered (always populated, even when sector baseline ultimately fired) |
| `n_history_sector` | `int` | size of the sector pool considered (0 if sector lookup unavailable, current sector is `"Unknown"`, or feature flag is False) |

**Validation invariants** (asserted in `ContrarianGate.compute_annotation()`):
1. If `gate_baseline == "per_ticker"`: `n_history_per_ticker >= per_ticker_floor` AND `percentile is not None`.
2. If `gate_baseline == "sector"`: `n_history_per_ticker < per_ticker_floor` AND `n_history_sector >= sector_floor` AND `percentile is not None`.
3. If `gate_baseline == "none"`: BOTH `n_history_per_ticker < per_ticker_floor` AND `n_history_sector < sector_floor`. `percentile` is None. `would_fire` is False.
4. `n_history` (the alias) equals: `n_history_per_ticker` if `gate_baseline == "per_ticker"`, `n_history_sector` if `"sector"`, 0 if `"none"`.

### `SectorPool` (computed on-demand; not persisted)

A conceptual entity representing the aggregated `bull_keyword_count` history for one sector at one evaluation moment.

| Field | Type | Notes |
|---|---|---|
| `sector` | `str` | the sector name (e.g., `"Technology"`); never `"Unknown"` (sector-pool aggregator returns empty pool for `"Unknown"`) |
| `before_date` | `date` | strict-prior cutoff; pool excludes all observations on or after this date (FR-002) |
| `values` | `list[float]` | the pooled `bull_keyword_count` values across all same-sector tickers' state logs |
| `n` | `int` | `len(values)`; cached for convenience |
| `contributors` | `dict[str, int]` | per-ticker contribution count `{ticker: n_observations_from_that_ticker}`; useful for diagnostics, not used in v1 firing logic |

The `SectorPool` is computed by `aggregate_sector_pool(sector, before_date, ...)` in the new `tradingagents/signals/sector_baseline.py` module. It is NOT a dataclass that gets persisted; it's a function return value with these fields exposed via attribute access (or a NamedTuple / dataclass for clarity, at the implementer's discretion).

### Configuration extensions to `TradingAgentsConfig` (TypedDict)

Two new keys added to `tradingagents/default_config.py`:

| Key | Type | Default | Notes |
|---|---|---|---|
| `contrarian_gate_sector_fallback_enabled` | `bool` | `True` | per R-5; settable to `False` for ablation experiments |
| `contrarian_gate_sector_floor` | `int` | `20` | per FR-003; defaults to same as the per-ticker floor for symmetry |

Existing key `contrarian_gate_threshold` (default 80) is the percentile threshold for BOTH baselines (FR-004).

---

## State transitions

### Gate evaluation (extended)

```
PM emits Buy/Overweight rating for ticker T on date D
  └─> ContrarianGate.compute_annotation(ticker=T, market_report=..., pm_rating=...)
        ├─> if mode == "off":
        │     return GateAnnotation(skipped="mode_off", ...)
        │
        ├─> compute feature_value = bull_keyword_count(market_report)
        │
        ├─> per_ticker_history = load_per_ticker_history(T, before_date=D)
        ├─> if len(per_ticker_history) >= per_ticker_floor:
        │     percentile = percentile_of_value(per_ticker_history, feature_value)
        │     gate_baseline = "per_ticker"
        │     ─> proceed to firing decision with this percentile
        │
        ├─> elif config.contrarian_gate_sector_fallback_enabled:
        │     sector = get_sector(T)
        │     if sector == "Unknown":
        │       n_history_sector = 0  # gate_baseline = "none"
        │     else:
        │       sector_pool = aggregate_sector_pool(sector, before_date=D)
        │       if len(sector_pool) >= sector_floor:
        │         percentile = percentile_of_value(sector_pool, feature_value)
        │         gate_baseline = "sector"
        │         ─> proceed to firing decision with this percentile
        │
        └─> if no baseline qualified:
              gate_baseline = "none"
              return GateAnnotation(skipped="insufficient_history", ...)
```

Firing decision (unchanged from spec 003):
- `would_fire = percentile >= threshold AND pm_rating in {Buy, Overweight}`
- `gate_fired = would_fire AND mode == "active"`
- If `gate_fired`: PM rating is downgraded to `target` (Hold or Underweight per `contrarian_gate_target` config)

---

## Validation summary

All validation lives in `ContrarianGate.compute_annotation()` and `aggregate_sector_pool()`:

- The invariant table in `GateAnnotation` (above) is asserted before returning the annotation dict.
- `aggregate_sector_pool` validates inputs: `sector` is non-empty string (else returns empty pool); `before_date` is a `date` instance.
- Failed validation raises `ValueError` with operator-readable message; spec 003's existing `unexpected failure → log warning → return unmodified decision` pattern at `portfolio_manager.py:175-183` continues to apply (gate failure never breaks PM pipeline).

---

## Notes on persistence

- `GateAnnotation` is persisted to `state["contrarian_gate"]` per Spec 003 + the persistence fix in commit `4c14d0f`. The new fields ride that path automatically — no change to `trading_graph.py`'s state-log writer needed.
- `SectorPool` is NOT persisted; it's a per-evaluation transient.
- `TradingAgentsConfig` extensions are persisted via the existing JSON serialization in `default_config.py`.
