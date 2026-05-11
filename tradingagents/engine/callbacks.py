"""LangChain callback handlers — engine event emission + cost-meter
instrumentation (specs/250-dashboard-ui/ FR-001, FR-005, FR-019, SC-007).

Two handlers in this module:
  * EngineEventCallback — maps LangGraph node start/end to AgentStage events
  * TokenCostCallback — totals token usage from on_llm_end into USD cost

Per FR-002 events are per-NODE granularity, NOT token streaming.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from tradingagents.engine.schemas import AgentStage

# Map LangGraph node names (per tradingagents/graph/setup.py) to AgentStage enum.
# Node names are exactly as registered with workflow.add_node(...).
LANGGRAPH_NODE_TO_STAGE: dict[str, AgentStage] = {
    "Market Analyst": AgentStage.MARKET_ANALYST,
    "News Analyst": AgentStage.NEWS_ANALYST,
    "Social Analyst": AgentStage.SOCIAL_ANALYST,
    "Fundamentals Analyst": AgentStage.FUNDAMENTALS_ANALYST,
    "Bull Researcher": AgentStage.BULL_RESEARCHER,
    "Bear Researcher": AgentStage.BEAR_RESEARCHER,
    "Research Manager": AgentStage.RESEARCH_MANAGER,
    "Trader": AgentStage.TRADER,
    "Aggressive Analyst": AgentStage.AGGRESSIVE_RISK,
    "Conservative Analyst": AgentStage.CONSERVATIVE_RISK,
    "Neutral Analyst": AgentStage.NEUTRAL_RISK,
    "Portfolio Manager": AgentStage.PORTFOLIO_MANAGER,
}


class EngineEventCallback(BaseCallbackHandler):
    """Calls user-provided ``on_stage`` for each agent NODE start/end.

    The graph also runs many non-agent chains (tool nodes, msg-clear nodes,
    inner LLM Runnables). Those are filtered out by name lookup against
    LANGGRAPH_NODE_TO_STAGE.

    Args:
        on_stage_started: callable(stage: AgentStage) -> None, fired on node entry
        on_stage_finished: callable(stage: AgentStage) -> None, fired on node exit
    """

    def __init__(
        self,
        on_stage_started=None,
        on_stage_finished=None,
    ):
        super().__init__()
        self._on_started = on_stage_started
        self._on_finished = on_stage_finished

    def _resolve_stage(self, serialized: dict | None, name: str | None) -> AgentStage | None:
        """Try the chain name; fall back to serialized id last token."""
        candidate = name or (serialized.get("name") if serialized else None)
        if candidate and candidate in LANGGRAPH_NODE_TO_STAGE:
            return LANGGRAPH_NODE_TO_STAGE[candidate]
        return None

    def on_chain_start(  # type: ignore[override]
        self,
        serialized: dict[str, Any] | None,
        inputs: dict[str, Any],
        *,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        stage = self._resolve_stage(serialized, kwargs.get("name"))
        if stage is not None and self._on_started is not None:
            self._on_started(stage)

    def on_chain_end(  # type: ignore[override]
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        # on_chain_end doesn't always include the chain name; consult the run
        # context if available, else fall back to the outputs (some implementations
        # include "name" in kwargs).
        stage = self._resolve_stage(None, kwargs.get("name"))
        if stage is not None and self._on_finished is not None:
            self._on_finished(stage)


# ---------------------------------------------------------------------------
# Cost-meter callback (Phase 1c — FR-019, SC-007)
# ---------------------------------------------------------------------------

# Anthropic API pricing per million tokens (2026-05; checked against
# anthropic.com/pricing). Updated when Anthropic ships new tiers.
ANTHROPIC_PRICING_USD_PER_M = {
    # Opus 4.7 (deep_think_llm default)
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    # Haiku 4.5 (quick_think_llm default)
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    # Sonnet 4.6 (operator override)
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
}

# Conservative default for unknown models — prevents zero-cost when a new
# Claude SKU lands before this table is updated. Operator can override.
DEFAULT_PRICING_USD_PER_M = {"input": 5.00, "output": 25.00}


def _model_pricing(model: str) -> dict[str, float]:
    """Return per-million-token pricing for the given model name. Match by
    longest prefix to handle versioned variants (e.g. claude-opus-4-7-20260321)."""
    if not model:
        return DEFAULT_PRICING_USD_PER_M
    for known in sorted(ANTHROPIC_PRICING_USD_PER_M, key=len, reverse=True):
        if model.startswith(known):
            return ANTHROPIC_PRICING_USD_PER_M[known]
    return DEFAULT_PRICING_USD_PER_M


def _cost_for_call(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute USD cost for a single LLM call from token counts."""
    p = _model_pricing(model)
    return (input_tokens / 1_000_000.0) * p["input"] + (output_tokens / 1_000_000.0) * p["output"]


class TokenCostCallback(BaseCallbackHandler):
    """LangChain callback that totals input + output tokens from on_llm_end
    responses and converts to USD via the Anthropic pricing table.

    Args:
        on_cost_delta: callable(delta_usd: float, model: str, input_tokens: int,
            output_tokens: int) called once per LLM call. The engine wires this
            to emit a `cost_delta` event + bump progress.cost_so_far_usd.
    """

    def __init__(self, on_cost_delta=None):
        super().__init__()
        self._on_cost_delta = on_cost_delta

    def on_llm_end(  # type: ignore[override]
        self,
        response: Any,
        *,
        run_id: UUID | None = None,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        """Pull token usage from response.llm_output and emit a cost delta.

        LangChain's LLMResult has llm_output={"token_usage": {...},
        "model_name": "..."} for OpenAI-style providers. For ChatAnthropic
        the same shape is provided via langchain-anthropic. Falls back to
        scanning generations[0][0].generation_info if llm_output is absent.
        """
        if self._on_cost_delta is None:
            return
        usage, model = self._extract_usage(response)
        if usage is None:
            return
        in_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        out_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        if in_tokens == 0 and out_tokens == 0:
            return
        delta = _cost_for_call(model or "", in_tokens, out_tokens)
        try:
            self._on_cost_delta(delta, model or "", in_tokens, out_tokens)
        except Exception:  # noqa: BLE001
            # Cost-meter failures must never block the propagate.
            pass

    @staticmethod
    def _extract_usage(response: Any) -> tuple[dict | None, str | None]:
        """Best-effort token-usage extraction from a LangChain LLMResult."""
        llm_output = getattr(response, "llm_output", None) or {}
        if isinstance(llm_output, dict):
            usage = llm_output.get("token_usage") or llm_output.get("usage")
            model = llm_output.get("model_name") or llm_output.get("model")
            if usage:
                return usage, model
        # Fallback: scan generations for usage_metadata (langchain-anthropic path).
        generations = getattr(response, "generations", None)
        if generations:
            for batch in generations:
                for gen in batch:
                    msg = getattr(gen, "message", None)
                    if msg is None:
                        continue
                    usage_meta = getattr(msg, "usage_metadata", None)
                    if usage_meta:
                        model = getattr(msg, "response_metadata", {}).get("model_name") or getattr(
                            msg, "response_metadata", {}
                        ).get("model")
                        return dict(usage_meta), model
        return None, None
