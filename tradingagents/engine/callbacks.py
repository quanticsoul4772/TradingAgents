"""LangChain callback handlers — engine event emission.

EngineEventCallback maps LangGraph node start/end to AgentStage events
(retained for backward compatibility; the engine runner now consumes
graph.stream() chunks directly).
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
