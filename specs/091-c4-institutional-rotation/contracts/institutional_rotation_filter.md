# Contract: institutional_rotation_filter module

**Module path**: `tradingagents/agents/utils/institutional_rotation_filter.py`
**Source of truth for fetch semantics**: `scripts/forward_catalyst_class4_retrospective.py:_fetch_institutional_rotation`
**Approx LOC**: 120

## Public API

```python
from functools import lru_cache
from typing import Any, Literal

from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.default_config import TradingAgentsConfig


@lru_cache(maxsize=128)
def _fetch_institutional_rotation(ticker: str) -> float | None:
    """Fetch top 10 institutional holders' net pctChange rotation.

    Returns:
        net_rotation: Sum of pctChange across top 10 holders.
        None: If yfinance returns None / empty DataFrame / missing
            pctChange column / raises an exception.
    """


def should_suppress_bear(
    net_rotation: float | None,
    threshold: float,
) -> bool:
    """Pure function: should the filter fire on the bear-side?

    Returns True iff net_rotation is not None AND
    net_rotation < -threshold (strict less-than per FR-005).
    """


def apply_filter(
    state: AgentState,
    config: TradingAgentsConfig,
) -> AgentState:
    """Apply C-4 filter at PM stage.

    Reads:
        - config["institutional_rotation_bear_mode"]
        - config["institutional_rotation_bull_mode"]
        - config["institutional_rotation_outflow_threshold"]
        - state["company_of_interest"] (ticker symbol)
        - state["final_trade_decision"] (current rendered PM markdown)

    Writes:
        - state["forward_catalyst"]["institutional_rotation"] (8 fields)
        - Mutates state["final_trade_decision"] to replace rating
            string when fired_bear == True (active mode only)

    Returns:
        Updated state dict.
    """
```

## Behavioral contract

### Mode interactions

| `bear_mode` | `bull_mode` | Behavior |
|---|---|---|
| `"off"` | `"off"` | Helper module not invoked; no annotation in state log |
| `"off"` | `"shadow"` | Helper invoked for bull-side measurement only (v1: bull-side is no-op since bull-side suppression isn't implemented; annotation field still populated for future expansion) |
| `"off"` | `"active"` | Same as above for v1 (bull-side no-op; annotation populated) |
| `"shadow"` | any | Helper invoked; would_fire_bear computed; fired_bear=False always; pre_rating preserved |
| `"active"` | any | Helper invoked; would_fire_bear computed; fired_bear=True iff conditions met; pre_rating mutated to "Hold" on fire |

**Note**: bull-side modes are reserved scaffolding for future expansion (per Decision 5 in research.md). At v1, only the bear-side suppression path is functional. Bull-side modes "shadow"/"active" populate the annotation fields but do NOT mutate ratings.

### Pre-rating eligibility

The bear-side filter only operates on bearish pre-ratings:

- pre_rating ∈ {Underweight, Sell} → eligible for suppression check
- pre_rating ∈ {Buy, Overweight, Hold} → bear-side filter no-op (would_fire_bear=False)

### Annotation field defaults when filter is no-op (but mode != "off")

When the filter runs but conditions are not met:

```python
{
    "net_rotation_pct": <fetched_value or None>,
    "outflow_threshold": 0.05,
    "bear_mode": <config_value>,
    "bull_mode": <config_value>,
    "would_fire_bear": False,  # conditions not met
    "fired_bear": False,
    "pre_rating": <observed>,
    "post_rating": <observed>,  # == pre_rating
}
```

### Strict less-than boundary (FR-005, SC-002)

The threshold comparison uses `<`, not `<=`:

```python
# net_rotation = -0.05, threshold = 0.05
should_suppress_bear(-0.05, 0.05)  # → False (boundary not crossed)

# net_rotation = -0.0500001, threshold = 0.05
should_suppress_bear(-0.0500001, 0.05)  # → True
```

### Graceful degradation (FR-013, SC-003)

When `_fetch_institutional_rotation` returns None, the filter MUST:

1. Set `net_rotation_pct = None` in annotation
2. Set `would_fire_bear = False`
3. Set `fired_bear = False`
4. NOT mutate `pre_rating`
5. NOT raise an exception

### LRU cache (FR-003, SC-004)

`_fetch_institutional_rotation` is decorated with `@lru_cache(maxsize=128)`. Test contract:

```python
def test_lru_cache_correctness(mocker):
    mock_yf = mocker.patch("yfinance.Ticker")
    _fetch_institutional_rotation("NVDA")
    _fetch_institutional_rotation("NVDA")  # second call
    assert mock_yf.call_count == 1  # only one fetch
```

## Integration contract — `portfolio_manager.py` hook

Insertion point: AFTER the existing Spec 007 forward-catalyst-filter hook call, BEFORE the final state return.

```python
# tradingagents/agents/managers/portfolio_manager.py (illustrative)

from tradingagents.agents.utils import (
    momentum_filter,
    bear_sector_symmetry_filter,
    contrarian_gate,
    sector_momentum_filter,
    forward_catalyst_filter,
    institutional_rotation_filter,  # NEW
)

def portfolio_manager_node(state: AgentState, config: TradingAgentsConfig) -> AgentState:
    # ... LLM call to produce initial rating ...

    state = momentum_filter.apply_filter(state, config)
    state = bear_sector_symmetry_filter.apply_filter(state, config)
    state = contrarian_gate.apply_filter(state, config)
    state = sector_momentum_filter.apply_filter(state, config)
    state = forward_catalyst_filter.apply_filter(state, config)
    state = institutional_rotation_filter.apply_filter(state, config)  # NEW; LAST in chain

    return state
```

The exact insertion is a 1-line addition after the existing
`forward_catalyst_filter.apply_filter` call. Filter ordering is
preserved (A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → spec X-1).

## Config contract — `default_config.py`

Add 4 keys to `TradingAgentsConfig` TypedDict + `DEFAULT_CONFIG` dict:

```python
class TradingAgentsConfig(TypedDict, total=False):
    # ... existing fields ...
    institutional_rotation_bear_mode: Literal["off", "shadow", "active"]
    institutional_rotation_bull_mode: Literal["off", "shadow", "active"]
    institutional_rotation_outflow_threshold: float
    institutional_rotation_inflow_threshold: float


DEFAULT_CONFIG: TradingAgentsConfig = {
    # ... existing entries ...
    "institutional_rotation_bear_mode": "shadow",
    "institutional_rotation_bull_mode": "off",
    "institutional_rotation_outflow_threshold": 0.05,
    "institutional_rotation_inflow_threshold": 0.05,
}
```

## Test contract

### Unit tests (`tests/test_institutional_rotation_filter.py`, ~14 tests)

See research.md Decision 8 for the full enumeration. Each test maps to
one or more SCs:

| Test | SCs covered |
|---|---|
| Fetch happy path | (background; enables others) |
| Fetch returns None on yfinance None | SC-003 |
| Fetch returns None on empty DataFrame | SC-003 |
| Fetch returns None on missing pctChange | SC-003 |
| Fetch returns None on yfinance exception | SC-003 |
| Fetch LRU cache correctness | SC-004 |
| Fetch handles NaN pctChange | FR-002 |
| should_suppress_bear True when below threshold | SC-001 |
| should_suppress_bear boundary (==) returns False | SC-002 |
| should_suppress_bear above threshold returns False | SC-001 |
| should_suppress_bear None input returns False | SC-003 |
| apply_filter active mode annotation | SC-007, SC-008 |
| apply_filter shadow mode annotation | SC-006 |
| apply_filter both modes off → no annotation | SC-005 |

### Integration tests (`tests/test_institutional_rotation_pm_integration.py`, 4 tests)

| Test | SCs covered |
|---|---|
| PM-hook bear=off + bull=off → no fetch, no annotation | SC-005 |
| PM-hook bear=shadow + cohort fires → would_fire=True, fired=False | SC-006 |
| PM-hook bear=active + cohort fires → fired=True, post_rating="Hold" | SC-001, SC-007, SC-008 |
| PM-hook bear=active + yfinance raises → graceful, no fire, propagate completes | SC-003 |

## Test isolation requirement

Per `feedback_global_conftest_autouse_for_real_llm.md` memory, this
spec adds NO LLM calls (Constitution III T0). The existing global
`tests/conftest.py` autouse fixture for `create_llm_client` does NOT
need extension for this filter.

However, the new helper module DOES make `yfinance.Ticker(...)` calls.
Tests MUST mock `yfinance.Ticker` to avoid network calls and test
non-determinism. Recommended pattern:

```python
@pytest.fixture(autouse=True)
def _mock_yfinance(mocker):
    """Prevent real yfinance calls in this test module."""
    return mocker.patch(
        "tradingagents.agents.utils.institutional_rotation_filter.yf.Ticker"
    )
```

This fixture should be defined in `tests/test_institutional_rotation_filter.py`
itself OR added to `tests/conftest.py` if other test modules will need
the same protection in the future.
