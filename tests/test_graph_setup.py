"""Unit tests for graph/setup.py — agent-graph wiring.

Previously 12% coverage on the file that defines the entire pipeline shape.
These tests mock all agent factories + ConditionalLogic so the test runs
without LLM clients, then introspects the resulting StateGraph for the
expected nodes, edges, and conditional branches.

Failure modes targeted:
- Adding a new analyst without updating REPORT_SECTIONS/ANALYST_MAPPING in
  the CLI (CLAUDE.md flags this) — these tests catch missing/extra nodes.
- Reordering analysts and breaking the linear chain.
- Forgetting to wire one of the risk-debate conditional edges.
- Removing a node from the canonical pipeline.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.graph.setup import GraphSetup


@pytest.fixture
def setup_with_mocks():
    """GraphSetup with every agent-factory call patched to return a noop.

    The agent factories are imported via `from tradingagents.agents import *`
    inside graph.setup, so we patch the names AS REBOUND in graph.setup's
    module namespace.
    """
    factories = [
        "create_market_analyst",
        "create_social_media_analyst",
        "create_news_analyst",
        "create_fundamentals_analyst",
        "create_bull_researcher",
        "create_bear_researcher",
        "create_research_manager",
        "create_trader",
        "create_aggressive_debator",
        "create_neutral_debator",
        "create_conservative_debator",
        "create_portfolio_manager",
        "create_msg_delete",
    ]
    patches = []
    for name in factories:
        p = patch(f"tradingagents.graph.setup.{name}", return_value=MagicMock())
        p.start()
        patches.append(p)
    try:
        tool_nodes = {a: MagicMock() for a in ("market", "social", "news", "fundamentals")}
        cond_logic = MagicMock()
        # Conditional functions need to exist as attributes since setup binds
        # them via getattr (should_continue_market, _social, _news, _fundamentals).
        for a in ("market", "social", "news", "fundamentals"):
            setattr(cond_logic, f"should_continue_{a}", MagicMock())
        cond_logic.should_continue_debate = MagicMock()
        cond_logic.should_continue_risk_analysis = MagicMock()

        gs = GraphSetup(
            quick_thinking_llm=MagicMock(),
            deep_thinking_llm=MagicMock(),
            tool_nodes=tool_nodes,
            conditional_logic=cond_logic,
        )
        yield gs
    finally:
        for p in patches:
            p.stop()


@pytest.mark.unit
def test_empty_analysts_raises(setup_with_mocks):
    with pytest.raises(ValueError, match="no analysts selected"):
        setup_with_mocks.setup_graph(selected_analysts=[])


@pytest.mark.unit
def test_default_four_analysts_produces_full_node_set(setup_with_mocks):
    """All 4 analysts → 12 analyst-related nodes (4 × {Analyst, Msg Clear, tools})
    + 8 downstream nodes (Bull, Bear, Research Manager, Trader, Aggressive,
    Neutral, Conservative, Portfolio Manager) = 20 total."""
    workflow = setup_with_mocks.setup_graph()  # default = all 4
    nodes = set(workflow.nodes.keys())
    expected_analyst_nodes = {
        "Market Analyst",
        "Msg Clear Market",
        "tools_market",
        "Social Analyst",
        "Msg Clear Social",
        "tools_social",
        "News Analyst",
        "Msg Clear News",
        "tools_news",
        "Fundamentals Analyst",
        "Msg Clear Fundamentals",
        "tools_fundamentals",
    }
    expected_downstream = {
        "Bull Researcher",
        "Bear Researcher",
        "Research Manager",
        "Trader",
        "Aggressive Analyst",
        "Neutral Analyst",
        "Conservative Analyst",
        "Portfolio Manager",
    }
    assert expected_analyst_nodes <= nodes
    assert expected_downstream <= nodes
    assert len(nodes) == 20


@pytest.mark.unit
def test_subset_of_analysts_omits_unused_nodes(setup_with_mocks):
    """Selecting only market + news must NOT create social or fundamentals nodes."""
    workflow = setup_with_mocks.setup_graph(selected_analysts=["market", "news"])
    nodes = set(workflow.nodes.keys())
    assert "Market Analyst" in nodes
    assert "News Analyst" in nodes
    assert "Social Analyst" not in nodes
    assert "Fundamentals Analyst" not in nodes
    assert "Msg Clear Social" not in nodes
    assert "tools_fundamentals" not in nodes


@pytest.mark.unit
def test_start_edge_points_to_first_analyst(setup_with_mocks):
    """The graph entry point should be the first analyst in the selected order."""
    workflow = setup_with_mocks.setup_graph(selected_analysts=["fundamentals", "market"])
    assert ("__start__", "Fundamentals Analyst") in workflow.edges


@pytest.mark.unit
def test_analysts_chain_in_selected_order(setup_with_mocks):
    """Msg Clear of analyst N → Analyst N+1, and last analyst's Msg Clear →
    Bull Researcher."""
    workflow = setup_with_mocks.setup_graph(selected_analysts=["market", "news", "fundamentals"])
    edges = set(workflow.edges)
    assert ("Msg Clear Market", "News Analyst") in edges
    assert ("Msg Clear News", "Fundamentals Analyst") in edges
    assert ("Msg Clear Fundamentals", "Bull Researcher") in edges


@pytest.mark.unit
def test_research_to_trader_to_risk_chain(setup_with_mocks):
    """Research Manager → Trader → Aggressive Analyst is hardcoded."""
    workflow = setup_with_mocks.setup_graph()
    edges = set(workflow.edges)
    assert ("Research Manager", "Trader") in edges
    assert ("Trader", "Aggressive Analyst") in edges


@pytest.mark.unit
def test_portfolio_manager_to_end(setup_with_mocks):
    """The pipeline always terminates at PortfolioManager → END."""
    workflow = setup_with_mocks.setup_graph()
    assert ("Portfolio Manager", "__end__") in workflow.edges


@pytest.mark.unit
def test_tools_loop_back_to_analyst(setup_with_mocks):
    """Each analyst's tools node loops back to its analyst (ReAct pattern)."""
    workflow = setup_with_mocks.setup_graph(selected_analysts=["market", "news"])
    edges = set(workflow.edges)
    assert ("tools_market", "Market Analyst") in edges
    assert ("tools_news", "News Analyst") in edges


@pytest.mark.unit
def test_debate_branches_wired(setup_with_mocks):
    """Bull and Bear Researcher both have conditional edges to either each
    other or Research Manager."""
    workflow = setup_with_mocks.setup_graph()
    branches = workflow.branches
    assert "Bull Researcher" in branches
    assert "Bear Researcher" in branches


@pytest.mark.unit
def test_risk_debate_branches_wired(setup_with_mocks):
    """All three risk personas have conditional edges (each can continue to
    next or terminate to Portfolio Manager)."""
    workflow = setup_with_mocks.setup_graph()
    branches = workflow.branches
    assert "Aggressive Analyst" in branches
    assert "Conservative Analyst" in branches
    assert "Neutral Analyst" in branches


@pytest.mark.unit
def test_analyst_branches_wired(setup_with_mocks):
    """Each selected analyst has a conditional edge (tools or msg clear)."""
    workflow = setup_with_mocks.setup_graph(selected_analysts=["market", "fundamentals"])
    branches = workflow.branches
    assert "Market Analyst" in branches
    assert "Fundamentals Analyst" in branches
    # Unselected analysts must not appear
    assert "Social Analyst" not in branches
    assert "News Analyst" not in branches


@pytest.mark.unit
def test_single_analyst_chains_directly_to_bull_researcher(setup_with_mocks):
    """When only 1 analyst is selected, its Msg Clear must wire directly to
    Bull Researcher (no intermediate analyst)."""
    workflow = setup_with_mocks.setup_graph(selected_analysts=["market"])
    edges = set(workflow.edges)
    assert ("Msg Clear Market", "Bull Researcher") in edges
    # And the entry point should be Market Analyst
    assert ("__start__", "Market Analyst") in edges


@pytest.mark.unit
def test_quick_llm_used_for_analysts_and_researchers(setup_with_mocks):
    """quick_thinking_llm goes to analysts, researchers, trader, risk personas.
    deep_thinking_llm goes only to research_manager and portfolio_manager."""
    setup_with_mocks.setup_graph()

    # Inspect the patched factory call_args via sys.modules introspection
    import tradingagents.graph.setup as setup_mod

    # Quick-LLM consumers
    quick = setup_with_mocks.quick_thinking_llm
    deep = setup_with_mocks.deep_thinking_llm
    setup_mod.create_market_analyst.assert_called_with(quick)
    setup_mod.create_bull_researcher.assert_called_with(quick)
    setup_mod.create_trader.assert_called_with(quick)
    setup_mod.create_aggressive_debator.assert_called_with(quick)
    # Deep-LLM consumers
    setup_mod.create_research_manager.assert_called_with(deep)
    setup_mod.create_portfolio_manager.assert_called_with(deep)
