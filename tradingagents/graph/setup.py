# TradingAgents/graph/setup.py
# ruff: noqa: F403, F405, B006

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState

from .conditional_logic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: Any,
        deep_thinking_llm: Any,
        tool_nodes: dict[str, ToolNode],
        conditional_logic: ConditionalLogic,
        bot_llm_factory: Any = None,
    ):
        """Initialize with required components.

        ``bot_llm_factory`` (spec 001 Phase 4) is an optional
        ``BotLLMFactory`` that routes per-bot LLM lookups when
        ``config["bot_models"]`` is non-empty. When None (default), every
        bot uses the framework's quick_thinking_llm / deep_thinking_llm
        as before (FR-007 backwards-compat).
        """
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.conditional_logic = conditional_logic
        self.bot_llm_factory = bot_llm_factory

    def _llm_for(self, bot_id: str, role: str = "quick") -> Any:
        """Per-bot LLM lookup. When a factory is wired, defer to it;
        otherwise return the role default."""
        if self.bot_llm_factory is not None:
            return self.bot_llm_factory.get_llm_for_bot(bot_id, role)
        return self.deep_thinking_llm if role == "deep" else self.quick_thinking_llm

    def setup_graph(self, selected_analysts=["market", "social", "news", "fundamentals"]):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        if "market" in selected_analysts:
            # BR-3 Squeak: route to structured-output variant when
            # config["market_analyst_format"] == "structured". Default
            # "prose" preserves existing behavior.
            from tradingagents.dataflows.config import get_config

            cfg = get_config()
            if cfg.get("market_analyst_format", "prose") == "structured":
                from tradingagents.agents.analysts.market_analyst_structured import (
                    create_market_analyst_structured,
                )

                analyst_nodes["market"] = create_market_analyst_structured(self._llm_for("market"))
            else:
                analyst_nodes["market"] = create_market_analyst(self._llm_for("market"))
            delete_nodes["market"] = create_msg_delete()
            tool_nodes["market"] = self.tool_nodes["market"]

        if "social" in selected_analysts:
            analyst_nodes["social"] = create_social_media_analyst(self._llm_for("social"))
            delete_nodes["social"] = create_msg_delete()
            tool_nodes["social"] = self.tool_nodes["social"]

        if "news" in selected_analysts:
            # BR-3 v2: route to structured-output variant when
            # config["news_analyst_format"] == "structured". Default
            # "prose" preserves existing behavior.
            from tradingagents.dataflows.config import get_config

            cfg = get_config()
            if cfg.get("news_analyst_format", "prose") == "structured":
                from tradingagents.agents.analysts.news_analyst_structured import (
                    create_news_analyst_structured,
                )

                analyst_nodes["news"] = create_news_analyst_structured(self._llm_for("news"))
            else:
                analyst_nodes["news"] = create_news_analyst(self._llm_for("news"))
            delete_nodes["news"] = create_msg_delete()
            tool_nodes["news"] = self.tool_nodes["news"]

        if "fundamentals" in selected_analysts:
            # BR-3 v2: route to structured-output variant when
            # config["fundamentals_analyst_format"] == "structured".
            from tradingagents.dataflows.config import get_config

            cfg = get_config()
            if cfg.get("fundamentals_analyst_format", "prose") == "structured":
                from tradingagents.agents.analysts.fundamentals_analyst_structured import (
                    create_fundamentals_analyst_structured,
                )

                analyst_nodes["fundamentals"] = create_fundamentals_analyst_structured(
                    self._llm_for("fundamentals")
                )
            else:
                analyst_nodes["fundamentals"] = create_fundamentals_analyst(
                    self._llm_for("fundamentals")
                )
            delete_nodes["fundamentals"] = create_msg_delete()
            tool_nodes["fundamentals"] = self.tool_nodes["fundamentals"]

        # Create researcher and manager nodes (per-bot routing for each)
        bull_researcher_node = create_bull_researcher(self._llm_for("bull_researcher"))
        bear_researcher_node = create_bear_researcher(self._llm_for("bear_researcher"))
        research_manager_node = create_research_manager(
            self._llm_for("research_manager", role="deep")
        )
        trader_node = create_trader(self._llm_for("trader"))

        # Create risk analysis nodes
        aggressive_analyst = create_aggressive_debator(self._llm_for("aggressive_debator"))
        neutral_analyst = create_neutral_debator(self._llm_for("neutral_debator"))
        conservative_analyst = create_conservative_debator(self._llm_for("conservative_debator"))
        portfolio_manager_node = create_portfolio_manager(
            self._llm_for("portfolio_manager", role="deep")
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", node)
            workflow.add_node(f"Msg Clear {analyst_type.capitalize()}", delete_nodes[analyst_type])
            workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Aggressive Analyst", aggressive_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Conservative Analyst", conservative_analyst)
        workflow.add_node("Portfolio Manager", portfolio_manager_node)

        # Define edges
        # Start with the first analyst
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            # Add conditional edges for current analyst
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst or to Bull Researcher if this is the last analyst
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i + 1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")
        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Conservative Analyst": "Conservative Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )

        workflow.add_edge("Portfolio Manager", END)

        return workflow
