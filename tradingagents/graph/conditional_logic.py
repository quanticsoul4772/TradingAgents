# TradingAgents/graph/conditional_logic.py

from langchain_core.messages import AIMessage

from tradingagents.agents.utils.agent_states import AgentState


def _has_pending_tool_calls(state: AgentState) -> bool:
    """True iff the analyst's most recent reply is an AIMessage requesting tools.

    The LangGraph contract for the analyst→conditional→tools_X edge places an
    ``AIMessage`` at ``messages[-1]`` (the analyst's LLM response). The
    ``isinstance`` check narrows the 12-type ``BaseMessage`` union so
    ``tool_calls`` is statically resolvable, and is defensive against any
    future graph reshaping that might route a non-AIMessage to this edge.
    """
    last_message = state["messages"][-1]
    return isinstance(last_message, AIMessage) and bool(last_message.tool_calls)


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(self, max_debate_rounds: int = 1, max_risk_discuss_rounds: int = 1) -> None:
        """Initialize with configuration parameters."""
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_market(self, state: AgentState) -> str:
        """Determine if market analysis should continue."""
        return "tools_market" if _has_pending_tool_calls(state) else "Msg Clear Market"

    def should_continue_social(self, state: AgentState) -> str:
        """Determine if social media analysis should continue."""
        return "tools_social" if _has_pending_tool_calls(state) else "Msg Clear Social"

    def should_continue_news(self, state: AgentState) -> str:
        """Determine if news analysis should continue."""
        return "tools_news" if _has_pending_tool_calls(state) else "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState) -> str:
        """Determine if fundamentals analysis should continue."""
        return "tools_fundamentals" if _has_pending_tool_calls(state) else "Msg Clear Fundamentals"

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""

        if (
            state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds
        ):  # 3 rounds of back-and-forth between 2 agents
            return "Research Manager"
        if state["investment_debate_state"]["current_response"].startswith("Bull"):
            return "Bear Researcher"
        return "Bull Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        if (
            state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            return "Portfolio Manager"
        if state["risk_debate_state"]["latest_speaker"].startswith("Aggressive"):
            return "Conservative Analyst"
        if state["risk_debate_state"]["latest_speaker"].startswith("Conservative"):
            return "Neutral Analyst"
        return "Aggressive Analyst"
