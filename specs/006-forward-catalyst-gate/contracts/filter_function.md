# Contract: Filter Function

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Research**: [../research.md](../research.md) (R-1, R-2, R-3, R-8)

The function the PortfolioManager calls to apply the forward-catalyst filter. Lives at `tradingagents/agents/utils/forward_catalyst_filter.py` per R-8.

---

## Function signature

```python
def evaluate_forward_catalyst(
    decision_markdown: str,
    state: dict,
    *,
    bull_mode: Literal["off", "shadow", "active"],
    bear_mode: Literal["off", "shadow", "active"],
    bull_threshold: float,
    bear_threshold: float,
    model: str,
    max_rationale_chars: int = 2000,
    llm: Any | None = None,
) -> tuple[str, dict]:
    """Apply the forward-catalyst filter to a PM decision.

    Returns (possibly_modified_decision_markdown, annotation_dict).
    Annotation always populated (never None) but may have `skipped` set.
    Caller is expected to merge `state["forward_catalyst"] = annotation` and
    use the modified decision_markdown going forward.

    See ``specs/006-forward-catalyst-gate/contracts/annotation_schema.md``
    for the annotation dict shape.
    """
```

---

## Inputs

| Parameter | Type | Notes |
|---|---|---|
| `decision_markdown` | `str` | The PM's full markdown decision (containing the rating line). Same shape A3 + spec 003 + spec 004 + spec 006 receive. |
| `state` | `dict` | The full LangGraph state dict; must contain `market_report` / `sentiment_report` / `news_report` / `fundamentals_report` / `investment_plan` / `investment_debate_state.history`. The filter reads these to build the LLM prompt. |
| `bull_mode` | `Literal["off", "shadow", "active"]` | Bull-side mode. From config. |
| `bear_mode` | `Literal["off", "shadow", "active"]` | Bear-side mode. From config. |
| `bull_threshold` | `float` | Bull-side fire threshold in [0, 1]. From config. Outside-range causes `skipped="invalid_threshold"` for the bull side. |
| `bear_threshold` | `float` | Bear-side fire threshold in [0, 1]. From config. Outside-range causes `skipped="invalid_threshold"` for the bear side. |
| `model` | `str` | LLM model name (e.g., `"claude-opus-4-7"`). From config. Routed through `tradingagents.llm_clients.factory.create_llm_client`. |
| `max_rationale_chars` | `int` | Max length of the LLM's rationale string (Pydantic enforces). Default 2000. |
| `llm` | `Any | None` | Injection point for tests. When None, the filter constructs a fresh client via the factory. Production callers pass None. |

---

## Output

`(decision_markdown_after_filter, annotation_dict)` per the Annotation Schema contract. The decision_markdown is unchanged unless one of the two sides fires in active mode AND the pre-rating matches the side's bullish/bearish set, in which case the rating line is replaced with `"Hold"` and a `[Forward-catalyst filter]` note is appended (matching A3's + spec 004's + spec 006's annotation pattern).

---

## Behavior

1. **Both-modes-off check**: if `bull_mode == "off" AND bear_mode == "off"`, return immediately with annotation containing both modes off, all data fields None, `skipped="off"`. NO LLM call (zero cost per FR-009 / SC-006).

2. **Threshold validation**: if `bull_threshold` outside [0, 1], log warning + treat as `bull_mode="off"` for this evaluation. Same for `bear_threshold`. If both sides invalidated → emit `skipped="invalid_threshold"` and skip LLM call.

3. **LLM client construction**: if `llm` parameter is None, construct via `create_llm_client("anthropic", model)`. Operators using non-Anthropic models override `provider` indirectly via the model string (factory routes per `_OPENAI_COMPATIBLE` set or special-cases).

4. **Build prompt**: include the 4 analyst reports + bull/bear debate history + investment plan as context. Truncate each section to ≤6000 chars to keep total prompt under ~12K tokens (matches the retrofit script's `_trunc()` helper).

5. **Structured-output call**: `llm.with_structured_output(CasePricedInScore).invoke(prompt)`. On any exception (incl. Pydantic ValidationError), catch + log warning + return immediately with `skipped="llm_failed"` + `error=str(exc)` + rating unchanged.

6. **Parse pre-rating** from `decision_markdown` via the standard `parse_rating()` helper (existing pattern from A3 / spec 004 / spec 006). Defaults to "Hold" if unparseable (defensive).

7. **Compute would_fire_bull**: `(score.bull_case_priced_in > bull_threshold) AND (pre_rating in {Buy, Overweight}) AND (bull_mode != "off")`. Strict greater-than per R-3.

8. **Compute would_fire_bear**: `(score.bear_case_priced_in > bear_threshold) AND (pre_rating in {Underweight, Sell}) AND (bear_mode != "off")`. Strict greater-than per R-3.

9. **Active-mode override (bull side)**: if `would_fire_bull AND bull_mode == "active"`, replace the rating line with "Hold" and append the annotation note. Set `fired_bull = True`, `post_rating = "Hold"`.

10. **Active-mode override (bear side)**: if `would_fire_bear AND bear_mode == "active"`, replace the rating line with "Hold" and append the annotation note. Set `fired_bear = True`, `post_rating = "Hold"`. NOTE: `fired_bull` and `fired_bear` are mutually exclusive by construction (a bullish pre-rating can't trigger the bear branch and vice versa).

11. **Return** `(decision_markdown, annotation_dict)` with all 16 fields populated per the schema.

---

## Failure modes

| Condition | Behavior |
|---|---|
| Both modes off | Skip LLM call entirely; emit `skipped="off"` (zero cost). |
| `bull_threshold` outside [0, 1] | Log warning; treat bull as "off"; emit `skipped="invalid_threshold"` if bear also invalid OR continue with bear-only. |
| `bear_threshold` outside [0, 1] | Same as above for bear. |
| LLM provider doesn't support structured output | Caught; emit `skipped="llm_failed"` + `error=str(exc)`; rating unchanged. |
| LLM call raises (network, rate limit, API error) | Caught; emit `skipped="llm_failed"` + `error=str(exc)`; rating unchanged. |
| Pydantic ValidationError on response | Caught; same as LLM call exception. |
| `decision_markdown` parse fails (no rating line) | Treat as `pre_rating="Hold"` (defensive default); both sides no-op (Hold not bullish/bearish). |
| `state` missing one or more report fields | Empty string substituted for missing fields; LLM call proceeds with whatever is present. |
| Both sides could fire (impossible by construction; pre-rating can't be both) | Defensive assertion in code; if violated, `fired_bull` takes precedence and `fired_bear` set False. |

The function NEVER raises into the PM pipeline (FR-010).

---

## Determinism

Per FR-011, the DECISION (would_fire / fired) is deterministic given the same `(LLM scores, bull_threshold, bear_threshold, bull_mode, bear_mode, pre_rating)` tuple. The LLM call itself is non-deterministic (LLM stochasticity) but that's outside the filter's control. The structured output schema constrains the outputs to the required types.

---

## Performance

- Expected per-evaluation: 1 LLM call (Opus latency ~5-10s; Haiku ~1-2s). Dominates everything else in the function (sector lookups, threshold checks, Pydantic validation are all <10ms).
- Per-propagate cost: ~$0.025 Opus / ~$0.0025 Haiku.
- For typical operator workflow (`daily_signals.py` on 5-10 ticker watchlist daily): ~10 calls/day × $0.025 = $0.25/day cost addition. T1 ≤$5/experiment per Constitution III.
- Backtest workflows (100+ propagates): ~$2.50 cost addition; operators see this in `--yes` cost confirmation prompt.

---

## Test fixtures

- `tests/test_forward_catalyst_filter.py::test_both_modes_off_skips_llm_call_zero_cost` — mock LLM client; assert zero invocations when both modes off.
- `tests/test_forward_catalyst_filter.py::test_bull_threshold_invalid_warns_and_skips_bull` — out-of-range threshold; assert `skipped="invalid_threshold"`, bull side not fired.
- `tests/test_forward_catalyst_filter.py::test_bear_threshold_invalid_warns_and_skips_bear` — same for bear side.
- `tests/test_forward_catalyst_filter.py::test_llm_call_failure_skipped_with_error` — mock LLM raising; assert `skipped="llm_failed"` + `error` populated + rating unchanged.
- `tests/test_forward_catalyst_filter.py::test_pydantic_validation_failure_treated_as_llm_failure` — mock LLM returning malformed response; assert same as LLM exception.
- `tests/test_forward_catalyst_filter.py::test_bull_active_fires_on_overweight_above_threshold` — happy path bull side.
- `tests/test_forward_catalyst_filter.py::test_bull_active_fires_on_buy_above_threshold` — happy path bull side, Buy variant.
- `tests/test_forward_catalyst_filter.py::test_bull_active_no_fire_on_overweight_below_threshold` — score below threshold.
- `tests/test_forward_catalyst_filter.py::test_bull_active_no_fire_on_hold` — Hold pre-rating.
- `tests/test_forward_catalyst_filter.py::test_bull_active_no_fire_on_underweight` — UW pre-rating; bull branch no-ops.
- `tests/test_forward_catalyst_filter.py::test_bull_shadow_records_would_fire_only` — shadow mode + score above threshold + bullish pre-rating.
- `tests/test_forward_catalyst_filter.py::test_bear_active_fires_on_underweight_above_threshold` — happy path bear side.
- `tests/test_forward_catalyst_filter.py::test_bear_active_fires_on_sell_above_threshold` — happy path bear side, Sell variant.
- `tests/test_forward_catalyst_filter.py::test_bear_shadow_records_would_fire_only_no_override` — shadow mode + score above threshold + bearish pre-rating.
- `tests/test_forward_catalyst_filter.py::test_bear_shadow_default_does_not_modify_rating` — explicit assertion that `bear_mode="shadow"` (the default) never modifies the rating.
- `tests/test_forward_catalyst_filter.py::test_strict_greater_than_boundary_bull` — `bull_case_priced_in == bull_threshold` exactly does NOT fire.
- `tests/test_forward_catalyst_filter.py::test_strict_greater_than_boundary_bear` — same for bear.
- `tests/test_forward_catalyst_filter.py::test_decision_markdown_no_rating_line_defensive` — both sides no-op (defaults to Hold pre-rating).
- `tests/test_forward_catalyst_filter.py::test_state_missing_report_fields_empty_substituted` — robustness to incomplete state.
- `tests/test_forward_catalyst_filter.py::test_annotation_active_fires_populates_all_fields` — full populated dict with `fired_bull=True`, `post_rating="Hold"`.
- `tests/test_forward_catalyst_filter.py::test_annotation_off_returns_off_skipped` — both modes off → annotation with skipped="off".
- `tests/test_forward_catalyst_filter.py::test_annotation_invariant_fired_bull_implies_active_mode` — invariant 5 from data-model.
- `tests/test_forward_catalyst_filter.py::test_annotation_invariant_fired_bear_implies_active_mode` — invariant 6.
- `tests/test_forward_catalyst_filter.py::test_annotation_fired_bull_and_fired_bear_mutually_exclusive` — invariant 7.
- `tests/test_forward_catalyst_filter.py::test_audit_corpus_filter_by_fired_bull_and_score` — synthetic 6-annotation list filterable by `fired_bull` + `bull_case_priced_in > 0.7`.
- `tests/test_forward_catalyst_filter.py::test_haiku_model_routing_via_factory` — verify `create_llm_client("anthropic", "claude-haiku-4-5")` is called when config sets Haiku model.
- `tests/test_forward_catalyst_filter.py::test_opus_model_routing_via_factory` — verify default model routes to Opus.
- `tests/test_forward_catalyst_filter.py::test_invalid_mode_falls_back_to_off` — defensive default (per Pydantic Literal type or warning + skip).

---

## What this function does NOT do

- Compute α (the LLM scores are interpretable but not α; α is downstream / out-of-scope).
- Persist anything (caller integrates with state log via the `_log_state` whitelist extension).
- Cache LLM responses (per-propagate uniqueness; cache would invalidate on re-run anyway).
- Override Hold ratings (per FR-002 — only acts on Buy/Overweight on bull side, Underweight/Sell on bear side).
- Upgrade ratings (per FR-007 — suppression target is always Hold).
- Re-implement the LLM client factory (uses `tradingagents.llm_clients.factory.create_llm_client` per R-1).
- Re-implement structured-output parsing (uses Pydantic + `with_structured_output` per R-2).
- Ever raise into the PM pipeline (per FR-010).
