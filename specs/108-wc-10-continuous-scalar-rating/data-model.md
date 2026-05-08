# Phase 1 Data Model: WC-10 Continuous Scalar Rating

**Branch**: `108-wc-10-continuous-scalar-rating` | **Date**: 2026-05-08

## Entities

### Entity 1 — Continuous scalar rating

**Type**: `float` in `[-1.0, +1.0]`

**Semantics**:

| Range | Interpretation |
|---|---|
| `-1.0` | Maximum bearish conviction (Sell-magnitude) |
| `-0.6 ≤ r < -0.2` | Underweight-equivalent |
| `-0.2 ≤ r ≤ +0.2` | Hold-equivalent (mode-collapse zone) |
| `+0.2 < r < +0.6` | Overweight-equivalent |
| `+0.6 ≤ r ≤ +1.0` | Buy-magnitude (max bullish at +1.0) |

**Validation**: Pydantic `Field(ge=-1.0, le=+1.0)` rejects out-of-range values at the LLM-output boundary.

**Lifecycle**: emitted by the Portfolio Manager LLM; flows through state to `final_trade_decision`; persisted in state log when `wc_10_enabled=True`.

---

### Entity 2 — 5-tier bin function output

**Source**: `bin_scalar_to_tier(rating: float, thresholds: tuple[float, float, float, float] | None = None) -> str`

**Output type**: `str` ∈ {Buy, Overweight, Hold, Underweight, Sell}

**Computation** (default thresholds `(-0.6, -0.2, +0.2, +0.6)`):

```
if rating <= -0.6: return "Sell"
elif rating <= -0.2: return "Underweight"
elif rating <= +0.2: return "Hold"
elif rating <= +0.6: return "Overweight"
else: return "Buy"
```

**Boundary semantics**: `<=` (right-inclusive at the bin's upper boundary). Lower bin claims the boundary value.

**Validation**: thresholds must be strictly monotonically increasing AND all in `[-1.0, +1.0]`. `bin_scalar_to_tier()` raises `ValueError` on invalid thresholds.

---

### Entity 3 — `state["wc_10"]` annotation

**Persistence**: added to the `_log_state` whitelist in `tradingagents/graph/trading_graph.py`.

**Schema** (when `wc_10_enabled=True`):

| Field | Type | Default | Description |
|---|---|---|---|
| `rating_scalar` | `float` | (extracted from PM output) | The continuous scalar rating in [-1, +1] |
| `filter_mode` | `Literal["bypass","passthrough"]` | "bypass" | The active mode at fire time |
| `bin_thresholds_snapshot` | `tuple[float, float, float, float]` | `(-0.6, -0.2, +0.2, +0.6)` | The thresholds active at fire time |

**Annotation absence rule**: when `wc_10_enabled=False`, the `wc_10` top-level state key is NOT added (FR-006 backward-compatibility guarantee).

---

### Entity 4 — TradingAgentsConfig keys (3 new)

**Location**: `tradingagents/default_config.py` `TradingAgentsConfig` TypedDict + `DEFAULT_CONFIG` dict.

| Key | Type | Default | Description |
|---|---|---|---|
| `wc_10_enabled` | `bool` | `False` | Master toggle for the WC-10 continuous scalar rating mode |
| `wc_10_filter_mode` | `Literal["bypass", "passthrough"]` | `"bypass"` | When enabled: "bypass" skips the 9-filter chain; "passthrough" deferred to v2 (raises error or warns in v1) |
| `wc_10_bin_thresholds` | `tuple[float, float, float, float]` | `(-0.6, -0.2, +0.2, +0.6)` | 4 boundary values for `bin_scalar_to_tier()` |

**Validation rules**:
- `wc_10_filter_mode` restricted to Literal at static-type time; runtime check rejects other values
- `wc_10_bin_thresholds` validated for strict monotonic + range at config-load time

---

## Relationships

```text
PARAMS.json
    ↓ (operator opt-in)
TradingAgentsConfig (3 new keys)
    ↓ (read by portfolio_manager_node + signal_processor)
PortfolioDecision Pydantic model
    ↓ (Union[PortfolioRating, float])
LLM output → Pydantic parse → rating field (str OR float depending on wc_10_enabled)
    ↓
SignalProcessor extraction (scalar-aware branch when wc_10_enabled)
    ↓
state["final_trade_decision"]  (rendered with float rating)
    ↓ (when wc_10_filter_mode="bypass")
[9-filter chain SKIPPED]
    ↓
state["wc_10"]  (3-field annotation; persisted via _log_state whitelist)
    ↓
~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json
```

## State persistence

State log when `wc_10_enabled=True` includes a new top-level field:

```json
{
  "final_trade_decision": "**Rating**: 0.45\n\nBody...",
  "wc_10": {
    "rating_scalar": 0.45,
    "filter_mode": "bypass",
    "bin_thresholds_snapshot": [-0.6, -0.2, 0.2, 0.6]
  }
}
```

When `wc_10_enabled=False`, the `wc_10` key is absent (FR-006 backward-compat).

## Backward compatibility matrix

| `wc_10_enabled` | `final_trade_decision` rating type | 9-filter chain | `state["wc_10"]` field | Memory log compatibility |
|---|---|---|---|---|
| False (default) | str (5-tier) | Runs as before | ABSENT | Identical |
| True + bypass mode | float (scalar) | SKIPPED | Present | Bin to 5-tier when writing memory log entry |
| True + passthrough mode (v2) | float bins to str | Runs (deferred to v2) | Present | Same as bypass for v1 |

## Empirical pilot data shape

`experiments/2026-05-08-001-wc-10-pilot/results.csv`:

| Column | Type | Description |
|---|---|---|
| `ticker` | str | NVDA or AAPL |
| `date` | str | YYYY-MM-DD |
| `mode` | str | "wc_10" or "5tier_baseline" |
| `rating` | str (mode="5tier_baseline") OR float (mode="wc_10") | The PM rating in the corresponding format |
| `binned_tier` | str | When mode="wc_10": result of `bin_scalar_to_tier(rating)` (5-tier compatibility); when mode="5tier_baseline": same as `rating` |
| `realized_alpha_21d` | float | 21-day forward alpha vs SPY (computed by analyzer) |
| `committed` | bool | When mode="wc_10": `abs(rating) > 0.2`; when mode="5tier_baseline": rating != "Hold" |

Total rows: 40 (10 dates × 2 tickers × 2 modes).
