# Contract: wc_10 module + integration points

**Module path**: `tradingagents/wc_10/` (new package)
**Approx LOC**: ~80 (bin function + package init)
**Integration touch points**: 5 existing modules

## Public API

```python
# tradingagents/wc_10/bin.py

DEFAULT_BIN_THRESHOLDS: tuple[float, float, float, float] = (-0.6, -0.2, 0.2, 0.6)


def bin_scalar_to_tier(
    rating: float,
    thresholds: tuple[float, float, float, float] | None = None,
) -> str:
    """Bin a continuous scalar rating to 5-tier categorical.

    Args:
        rating: float in [-1.0, +1.0]
        thresholds: 4-tuple of strictly-monotonic floats in [-1, +1].
            Defaults to DEFAULT_BIN_THRESHOLDS = (-0.6, -0.2, 0.2, 0.6).

    Returns:
        One of {"Buy", "Overweight", "Hold", "Underweight", "Sell"}.

    Raises:
        ValueError: if thresholds are not strictly monotonic OR out of [-1, +1].
        ValueError: if rating is out of [-1, +1].

    Boundary semantics: ≤ (right-inclusive at the bin's upper boundary).
    Lower bin claims the boundary value.
    """
    # ... implementation
```

## Behavioral contract

### Bin function determinism

Pure function with no side effects + deterministic mapping:

| Rating | Default thresholds | Returns |
|---|---|---|
| `-1.0` | `(-0.6, -0.2, 0.2, 0.6)` | `"Sell"` |
| `-0.6` | same | `"Sell"` (boundary; `<=` claims lower bin) |
| `-0.5` | same | `"Underweight"` |
| `-0.2` | same | `"Underweight"` (boundary) |
| `0.0` | same | `"Hold"` |
| `+0.2` | same | `"Hold"` (boundary) |
| `+0.5` | same | `"Overweight"` |
| `+0.6` | same | `"Overweight"` (boundary) |
| `+0.7` | same | `"Buy"` |
| `+1.0` | same | `"Buy"` |

### Validation contract

`bin_scalar_to_tier()` MUST raise `ValueError` on:
- thresholds not strictly monotonic increasing (`(0.5, 0.5, ...)` or `(0.6, 0.5, ...)`)
- thresholds outside `[-1.0, +1.0]`
- rating outside `[-1.0, +1.0]`

### Default-off integrity

When `wc_10_enabled=False` (the default):
- `bin_scalar_to_tier()` is NEVER called from production code paths
- No `state["wc_10"]` field added to state logs
- `PortfolioDecision.rating` resolves as the 5-tier `PortfolioRating` enum (not float)
- All 9 filters run as before

## Integration touch points

### 1. `tradingagents/agents/schemas.py`

```python
from typing import Union

class PortfolioDecision(BaseModel):
    rating: Union[PortfolioRating, float] = Field(
        ...,
        description=(
            "Final rating. When wc_10_enabled=False (default), expect a "
            "PortfolioRating enum value. When wc_10_enabled=True, expect a "
            "float in [-1.0, +1.0] (signed conviction magnitude)."
        ),
    )

    @validator("rating")
    def _validate_rating(cls, v):
        if isinstance(v, float):
            if not (-1.0 <= v <= 1.0):
                raise ValueError(f"Float rating must be in [-1, +1]; got {v}")
        return v
```

Pydantic Union resolution handles both cases.

### 2. `tradingagents/graph/signal_processing.py.SignalProcessor`

```python
def extract_rating(self, decision_markdown: str, parsed: PortfolioDecision | None) -> str | float:
    if self.config.get("wc_10_enabled") and isinstance(parsed.rating, float):
        # Scalar mode: return the float directly
        return parsed.rating
    # 5-tier mode (default): existing regex extraction
    return self._extract_5tier_rating(decision_markdown)
```

Pydantic-first; regex fallback only on the default-off path.

### 3. `tradingagents/agents/managers/portfolio_manager.py.portfolio_manager_node`

```python
def portfolio_manager_node(state: AgentState, config: TradingAgentsConfig) -> AgentState:
    # ... existing LLM call to produce final_trade_decision ...

    if config.get("wc_10_enabled") and config.get("wc_10_filter_mode") == "bypass":
        # WC-10 bypass mode: skip 9-filter chain entirely
        rating = parsed.rating  # float
        state["wc_10"] = {
            "rating_scalar": rating,
            "filter_mode": "bypass",
            "bin_thresholds_snapshot": tuple(config.get("wc_10_bin_thresholds", DEFAULT_BIN_THRESHOLDS)),
        }
        return state

    # ... existing 9-filter chain (A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → spec X-1) ...
```

Single early-return branch at top of the post-LLM-call portion of the node.

### 4. `tradingagents/agents/utils/agent_states.py.AgentState`

```python
class AgentState(MessagesState):
    # ... existing fields ...
    wc_10: NotRequired[dict[str, Any]]  # WC-10 annotation; absent when wc_10_enabled=False
```

`NotRequired` per the FR-006 backward-compat guarantee.

### 5. `tradingagents/graph/trading_graph.py._log_state`

Add `"wc_10"` to the existing `_log_state` whitelist (currently includes `forward_catalyst`, `contrarian_gate`, `sector_momentum`, `bear_sector_symmetry`).

## Test contract

### Unit tests (`tests/test_wc_10_bin.py`, ~6 tests)

| Test | Covers |
|---|---|
| `test_bin_buy_interior` (rating=0.7) | SC-002 |
| `test_bin_overweight_boundary` (rating=0.6) | SC-002 boundary |
| `test_bin_hold_interior` (rating=0.0) | SC-002 |
| `test_bin_sell_boundary` (rating=-0.6) | SC-002 boundary |
| `test_bin_sell_interior` (rating=-0.7) | SC-002 |
| `test_bin_rejects_invalid_thresholds` | validation contract |

### Integration tests (`tests/test_wc_10_pm_integration.py`, 2 tests)

| Test | Covers |
|---|---|
| `test_default_off_5tier_unchanged` | SC-003 (wc_10_enabled=False preserves 5-tier output + 9-filter chain) |
| `test_bypass_mode_skips_filters` | SC-001 + SC-004 (wc_10_enabled=True + bypass mode produces scalar + asserts NO filter from chain executes) |

## Pilot harness contract — `scripts/wc_10_pilot.py`

```python
def main():
    # 10 dates × 2 tickers (NVDA + AAPL) × 2 modes (wc_10 + 5tier_baseline)
    # Total: 40 propagates × ~$0.40 = ~$16
    # Output: experiments/<date>-001-wc-10-pilot/results.csv
    ...
```

CLI:
```
python scripts/wc_10_pilot.py [--dates 10] [--tickers NVDA,AAPL] [--out experiments/<dir>/]
```

Resumes-on-crash; appends to existing CSV. Mirrors `scripts/backtest.py` resume pattern.

## Test isolation requirement

Per `feedback_global_conftest_autouse_for_real_llm.md`: WC-10 introduces NO new lazy-LLM call (no LLM call beyond the existing PM call). The existing global `tests/conftest.py` autouse fixture for `create_llm_client` does NOT need extension.

The pilot harness DOES make real LLM calls but is operator-driven (not pytest); no fixture concern.
