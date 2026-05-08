# Phase 1 Data Model: C-4 Institutional Rotation Filter (Spec X-1)

**Branch**: `091-c4-institutional-rotation` | **Date**: 2026-05-07

## Entities

### Entity 1 — Top 10 institutional holders snapshot

**Source**: `yfinance.Ticker(ticker).institutional_holders`

**Shape**: 10-row × 6-col pandas.DataFrame

**Columns** (per yfinance API contract):

| Column | Type | Description |
|---|---|---|
| `Holder` | str | Institution name (e.g., "Vanguard Group Inc.") |
| `pctHeld` | float | Current % of shares held |
| `Shares` | int | Current share count |
| `Value` | int | Current dollar value |
| `Date Reported` | str | Last 13F filing date |
| `pctChange` | float | Change in pctHeld since prior 13F (the field this spec consumes) |

**Validation rules**:

- DataFrame may be None, empty, or missing pctChange column for ETFs / very small caps / API outages → triggers FR-013 graceful degradation
- pctChange may contain NaN values → handled via `.fillna(0)` in the aggregation step
- Row count is normally 10; fewer rows is acceptable (sum operates on whatever is returned)

**Lifecycle**: Cached via LRU per process; resets on process restart.

---

### Entity 2 — net_rotation aggregate

**Type**: `float | None`

**Computation**: `df["pctChange"].fillna(0).sum()` over the top 10 rows
(or `None` when the source DataFrame is unavailable).

**Semantic ranges**:

| Range | Interpretation |
|---|---|
| `> +0.05` | Strong net inflow (institutions accumulating) |
| `[-0.05, +0.05]` | Mixed / no strong signal |
| `< -0.05` | Strong net outflow (institutions selling) — triggers bear-side suppression |
| `None` | Data unavailable; filter degrades to baseline (no fire) |

**Empirical reference**: PR #75 retrospective used `T_OUTFLOW = 0.05`;
this spec preserves that as the production default.

---

### Entity 3 — `state["forward_catalyst"]["institutional_rotation"]` annotation sub-dict

**Persistence**: Already on the `_log_state` whitelist via the parent `forward_catalyst` field declared in AgentState (per Spec 007).

**Schema** (when bear_mode != "off" or bull_mode != "off"):

| Field | Type | Default | Description |
|---|---|---|---|
| `net_rotation_pct` | `float \| None` | (computed) | Aggregate from yfinance fetch; None on data unavailability |
| `outflow_threshold` | `float` | 0.05 | Configured `institutional_rotation_outflow_threshold` value at fire time |
| `bear_mode` | `Literal["off","shadow","active"]` | "shadow" | `institutional_rotation_bear_mode` at fire time |
| `bull_mode` | `Literal["off","shadow","active"]` | "off" | `institutional_rotation_bull_mode` at fire time |
| `would_fire_bear` | `bool` | (computed) | True when `net_rotation < -outflow_threshold AND pre_rating ∈ {Underweight, Sell}` |
| `fired_bear` | `bool` | (computed) | True only when `bear_mode == "active" AND would_fire_bear == True` |
| `pre_rating` | `str` | (read from state) | One of {Buy, Overweight, Hold, Underweight, Sell} |
| `post_rating` | `str` | (computed) | "Hold" if `fired_bear == True`; else `pre_rating` |

**State transition**:

```
pre_rating ∈ {Underweight, Sell}
    ↓
fetch institutional_rotation
    ↓
if rotation is None → fired_bear=False, post_rating=pre_rating
elif rotation >= -threshold → fired_bear=False, post_rating=pre_rating
elif rotation < -threshold AND mode != "active" → would_fire_bear=True, fired_bear=False, post_rating=pre_rating
elif rotation < -threshold AND mode == "active" → would_fire_bear=True, fired_bear=True, post_rating="Hold"
```

**Annotation absence rule** (FR-011): When BOTH `bear_mode == "off"` AND `bull_mode == "off"`, the sub-dict is NOT added to `state["forward_catalyst"]`. State logs match the pre-Spec-X-1 baseline shape.

---

### Entity 4 — TradingAgentsConfig keys (4 new)

**Location**: `tradingagents/default_config.py` `TradingAgentsConfig` TypedDict + `DEFAULT_CONFIG` dict

| Key | Type | Default | Description |
|---|---|---|---|
| `institutional_rotation_bear_mode` | `Literal["off","shadow","active"]` | `"shadow"` | Operational mode for bear-side suppression |
| `institutional_rotation_bull_mode` | `Literal["off","shadow","active"]` | `"off"` | Reserved for future bull-side activation |
| `institutional_rotation_outflow_threshold` | `float` | `0.05` | Fractional threshold; filter fires when `net_rotation < -threshold` |
| `institutional_rotation_inflow_threshold` | `float` | `0.05` | Reserved for future bull-side activation; unused at default-off |

**Validation rules**:

- Mode values restricted by `Literal` type (mypy-checked at static time; runtime check in `apply_filter` for non-typed callers)
- Thresholds must be > 0 (negative or zero would cause non-deterministic behavior at the boundary)

---

## Relationships

```text
PARAMS.json
    ↓ (operator opt-in)
TradingAgentsConfig (4 new keys)
    ↓ (read by apply_filter)
institutional_rotation_filter.apply_filter()
    ↓ (delegates fetch)
_fetch_institutional_rotation(ticker)  [LRU-cached]
    ↓ (yfinance call)
yfinance.Ticker(ticker).institutional_holders
    ↓ (DataFrame returned)
sum(pctChange) → net_rotation
    ↓ (suppression decision)
should_suppress_bear(net_rotation, threshold)
    ↓ (annotation built)
state["forward_catalyst"]["institutional_rotation"]
    ↓ (rating mutation in active mode)
state["final_trade_decision"]  (rendered with new rating)
    ↓ (persisted via _log_state whitelist)
~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json
```

## State persistence

The annotation sub-dict is persisted via the existing `_log_state` whitelist in `tradingagents/graph/trading_graph.py`. The whitelist already includes `forward_catalyst` (per Spec 007's wiring); no new whitelist entries are required for this spec.

State logs after Spec X-1 deployment will include:

```json
{
  "forward_catalyst": {
    "model": "claude-opus-4-7",
    "bull_case_priced_in": 0.55,
    "bear_case_priced_in": 0.65,
    "...": "...other Spec 007 fields...",
    "institutional_rotation": {
      "net_rotation_pct": -0.0823,
      "outflow_threshold": 0.05,
      "bear_mode": "shadow",
      "bull_mode": "off",
      "would_fire_bear": true,
      "fired_bear": false,
      "pre_rating": "Underweight",
      "post_rating": "Underweight"
    }
  }
}
```

When both modes are off, the `institutional_rotation` sub-key is entirely absent (FR-011 backward-compatibility guarantee).
