# Phase 1: Data Model — Forward-Catalyst-Aware Contrarian Gate (Spec 007)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Date**: 2026-05-06

---

## Entity reference

### `CasePricedInScore` (Pydantic BaseModel)

The structured output schema for the LLM call. Defined at `tradingagents/agents/utils/forward_catalyst_filter.py`.

```python
from typing import Literal
from pydantic import BaseModel, Field

class CasePricedInScore(BaseModel):
    bull_case_priced_in: float = Field(
        ge=0.0, le=1.0,
        description="How widely is the bull case ALREADY ACCEPTED by the market...")
    bear_case_priced_in: float = Field(
        ge=0.0, le=1.0,
        description="How widely is the bear case ALREADY ACCEPTED by the market...")
    rationale: str = Field(
        max_length=2000,
        description="One short paragraph explaining both scores...")
```

Pydantic enforces:
- Both scores in [0, 1] (raises `ValidationError` if LLM returns outside)
- Rationale ≤ 2000 chars (raises `ValidationError` if LLM exceeds)

On any `ValidationError` or LLM exception, the filter degrades to `skipped="llm_failed"` per FR-010.

---

### `ForwardCatalystAnnotation` (dict)

Emitted to LangGraph state at `state["forward_catalyst"]`. Persisted to the JSON state log via the `_log_state` whitelist extension (R-5).

| Field | Type | Notes |
|---|---|---|
| `model` | `str` | The LLM model used (e.g., `"claude-opus-4-7"`) |
| `bull_case_priced_in` | `float \| None` | LLM's bull-side score; None if LLM failed |
| `bear_case_priced_in` | `float \| None` | LLM's bear-side score; None if LLM failed |
| `rationale` | `str \| None` | LLM's rationale; None if LLM failed |
| `bull_threshold` | `float \| None` | Configured bull threshold (e.g., `0.60`); None if `bull_mode="off"` |
| `bear_threshold` | `float \| None` | Configured bear threshold (e.g., `0.50`); None if `bear_mode="off"` |
| `bull_mode` | `Literal["off", "shadow", "active"]` | Bull-side mode at evaluation |
| `bear_mode` | `Literal["off", "shadow", "active"]` | Bear-side mode at evaluation |
| `would_fire_bull` | `bool` | True iff `bull_case_priced_in > bull_threshold AND pre_rating in {Buy, Overweight} AND bull_mode != "off"` |
| `would_fire_bear` | `bool` | True iff `bear_case_priced_in > bear_threshold AND pre_rating in {Underweight, Sell} AND bear_mode != "off"` |
| `fired_bull` | `bool` | True iff `would_fire_bull AND bull_mode == "active"` (rating actually overridden via bull branch) |
| `fired_bear` | `bool` | True iff `would_fire_bear AND bear_mode == "active"` (rating actually overridden via bear branch) |
| `pre_rating` | `str` | Rating BEFORE this filter ran |
| `post_rating` | `str` | Rating AFTER this filter ran (may equal `pre_rating` if no fire) |
| `skipped` | `Literal["off", "llm_failed", "invalid_threshold", "rating_not_actionable"] \| None` | Reason filter didn't compute / fire (None if it did) |
| `error` | `str \| None` | Exception summary if `skipped == "llm_failed"` (None otherwise) |

**Validation invariants** (asserted in `evaluate_forward_catalyst()` before returning):
1. If `skipped == "off"`: `bull_mode == "off" AND bear_mode == "off"`, all data fields default/None, `would_fire_*` False, `fired_*` False, `post_rating == pre_rating`.
2. If `skipped == "llm_failed"`: `bull_case_priced_in is None`, `bear_case_priced_in is None`, `rationale is None`, `error is not None`, `would_fire_*` False, `fired_*` False.
3. If `skipped == "invalid_threshold"`: at least one of `bull_threshold` / `bear_threshold` outside [0, 1]; filter degrades to off for that side; warning logged.
4. If `skipped is None`: both LLM scores populated, at least one mode != "off", both thresholds populated for the active side(s).
5. If `fired_bull is True`: `would_fire_bull is True` AND `bull_mode == "active"` AND `pre_rating in {"Buy", "Overweight"}` AND `post_rating == "Hold"`.
6. If `fired_bear is True`: `would_fire_bear is True` AND `bear_mode == "active"` AND `pre_rating in {"Underweight", "Sell"}` AND `post_rating == "Hold"`.
7. `fired_bull AND fired_bear` is impossible (pre_rating can be either bullish OR bearish, not both); enforced by structural check.
8. Strict greater-than threshold semantics (R-3): `would_fire_bull is True` requires `bull_case_priced_in > bull_threshold`. Equality does NOT fire. Same for bear.

---

### Configuration extensions to `TradingAgentsConfig` (TypedDict)

Six new keys added to `tradingagents/default_config.py`:

| Key | Type | Default | Notes |
|---|---|---|---|
| `forward_catalyst_bull_mode` | `Literal["off", "shadow", "active"]` | `"active"` | per FR-006; bull-side default-on per Class 3 Opus retrospective DECISIVE PASS |
| `forward_catalyst_bear_mode` | `Literal["off", "shadow", "active"]` | `"shadow"` | per FR-006 + R-7; bear-side shadow-mode-first per Constitution VIII shadow-mode condition (bear retrospective passed criteria 1+2 only) |
| `forward_catalyst_bull_threshold` | `float` | `0.60` | per FR-005 + R-7; sweet-spot from Opus retrospective threshold sweep; range [0, 1] |
| `forward_catalyst_bear_threshold` | `float` | `0.50` | per FR-005 + R-7; bear-side highest discrimination from Opus retrospective; range [0, 1] |
| `forward_catalyst_model` | `str` | `"claude-opus-4-7"` | per R-7; Opus required for bull-side default-on per the empirical evidence; operators can override to `"claude-haiku-4-5"` for cost-sensitive workflows with documented degradation |
| `forward_catalyst_max_rationale_chars` | `int` | `2000` | per FR-003; matches the Pydantic `max_length` constraint |

---

### `AgentState` TypedDict extension

New optional key in `tradingagents/agents/utils/agent_states.py`:

```python
class AgentState(MessagesState):
    # ... existing fields ...
    forward_catalyst: NotRequired[dict | None]  # spec 007
```

Per R-5 + the spec 003 + spec 004 + spec 006 precedents: undeclared keys are silently dropped from LangGraph state merges. Declaring this key in the TypedDict ensures `final_state["forward_catalyst"]` is preserved end-to-end.

---

## State transitions

### Filter evaluation (with all modes)

```
PM emits rating R for ticker T on date D
  └─> evaluate_forward_catalyst(decision_markdown, R, state, get_config())
        ├─> if bull_mode == "off" AND bear_mode == "off":
        │     return decision_markdown unchanged
        │     emit annotation: skipped="off", both modes "off", all data None
        │
        ├─> if bull_threshold not in [0, 1] OR bear_threshold not in [0, 1]:
        │     log warning("invalid threshold")
        │     skip the offending side (set its mode to "off" for this evaluation)
        │     emit annotation: skipped="invalid_threshold"
        │     continue with the valid side (or both-off → skipped above)
        │
        ├─> Build LLM prompt with the 4 analyst reports + bull/bear debate + investment plan
        ├─> Construct LLM client via factory(provider="anthropic", model=config["forward_catalyst_model"])
        │
        ├─> try:
        │     structured_llm = llm.with_structured_output(CasePricedInScore)
        │     score = structured_llm.invoke(prompt)
        │   except Exception as exc:
        │     log warning(f"forward_catalyst: LLM call failed: {exc}")
        │     return decision_markdown unchanged
        │     emit annotation: skipped="llm_failed", error=str(exc), bull/bear scores None
        │
        ├─> Compute would_fire_bull (strict greater-than per R-3):
        │     would_fire_bull = (
        │       score.bull_case_priced_in > bull_threshold
        │       AND R in {"Buy", "Overweight"}
        │       AND bull_mode != "off"
        │     )
        │
        ├─> Compute would_fire_bear:
        │     would_fire_bear = (
        │       score.bear_case_priced_in > bear_threshold
        │       AND R in {"Underweight", "Sell"}
        │       AND bear_mode != "off"
        │     )
        │
        ├─> If would_fire_bull AND bull_mode == "active":
        │     decision_markdown = downgrade_to_hold(decision_markdown, R, "bull", score, ...)
        │     fired_bull = True
        │     post_rating = "Hold"
        │
        ├─> Else if would_fire_bear AND bear_mode == "active":
        │     decision_markdown = downgrade_to_hold(decision_markdown, R, "bear", score, ...)
        │     fired_bear = True
        │     post_rating = "Hold"
        │
        └─> emit full annotation; return decision_markdown (modified or not)
```

### PM hook chain order (per R-4 / FR-012)

```
PM emits rating from LLM call
  ↓
A3 momentum filter (per-ticker absolute bear suppression on UW/Sell when ticker is DOWN ≥5%)
  ↓
Spec 006 bear-sector-symmetry filter (sector-relative bear suppression on UW/Sell when ticker is UP ≥5% relative to sector)
  ↓
Spec 003 contrarian gate (within-ticker prose-density bull suppression on Buy/OW)
  + Spec 003.5 sector-baseline fallback (cross-sector prose-density)
  ↓
Spec 004 sector-momentum filter (sector-ETF momentum bull suppression on Buy/OW)
  ↓
Spec 007 forward-catalyst filter (THIS SPEC — LLM-extracted case-priced-in suppression on both sides; LAST in chain)
  ↓
Final rating persisted to state
```

If a prior filter has already overridden the rating to Hold, spec 007 still calls the LLM (annotation captured for audit) but both bull-side and bear-side branches no-op (rating is Hold, neither bullish nor bearish per FR-002).

---

## Validation summary

All validation lives in `evaluate_forward_catalyst()`. Failures:
- Both modes off → skip LLM, emit `skipped="off"` (zero cost)
- Threshold outside [0, 1] → log warning, skip offending side, emit `skipped="invalid_threshold"`
- LLM call exception → log warning, skip both sides, emit `skipped="llm_failed"` + `error=str(exc)`
- Pydantic validation exception → same as LLM call exception (treated as LLM failure)

The filter NEVER raises into the PM pipeline (FR-010 + matches A3's + spec 004's + spec 006's existing resilience pattern + the Phase C `second_opinion.py` precedent).

---

## Notes on persistence

- `state["forward_catalyst"]` is a dict (or None when both modes="off") populated each propagate when the filter runs. Persisted via the `_log_state` whitelist extension (R-5; one-line addition mirroring the precedents from commit `4c14d0f` for `contrarian_gate`, spec 004 for `sector_momentum`, and spec 006 for `bear_sector_symmetry`).
- `AgentState` TypedDict extension prevents the LangGraph silent-drop bug — same precedent as spec 003 + spec 004 + spec 006.
- `TradingAgentsConfig` extensions persisted via the existing JSON serialization pattern in `default_config.py`.

---

## Backward compatibility

- `TradingAgentsConfig` extensions are additive — existing experiments' `PARAMS.json` files don't need modification (defaults apply).
- New `state["forward_catalyst"]` field is additive — existing consumers (`daily_signals.py`, `scripts/contrarian_gate_retrospective.py`, `scripts/sector_momentum_retrospective.py`, `scripts/bear_sector_symmetry_retrospective.py`) ignore unknown state keys.
- Filter ordering (FR-012) places this filter LAST in the chain — existing A3 + spec 003 + spec 003.5 + spec 004 + spec 006 behavior is unchanged.
- **NEW behavior**: every propagate now incurs an Opus LLM call by default (~$0.025). Operators wanting the prior behavior (no Spec 007 cost) set BOTH modes to `"off"` in PARAMS.json or config override (FR-013 escape hatch).
- **Breaking change**: ratings that previously committed to Buy/OW may now be suppressed to Hold by the bull-side filter. This is the intended behavior per the empirical retrospective evidence. Operators can ablate via `forward_catalyst_bull_mode = "off"`.
