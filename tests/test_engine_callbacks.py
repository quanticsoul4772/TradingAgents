"""Tests for the engine LangChain callback handler (Phase 1b FR-001 + FR-005)."""

from __future__ import annotations

import pytest

from tradingagents.engine.callbacks import (
    LANGGRAPH_NODE_TO_STAGE,
    EngineEventCallback,
)
from tradingagents.engine.schemas import AgentStage


@pytest.mark.unit
def test_node_map_covers_all_twelve_agent_stages():
    """The map must surface every AgentStage so no node yields a dropped event."""
    assert set(LANGGRAPH_NODE_TO_STAGE.values()) == set(AgentStage)
    assert len(LANGGRAPH_NODE_TO_STAGE) == 12


@pytest.mark.unit
def test_node_map_uses_exact_setup_py_names():
    """Sanity: names match tradingagents/graph/setup.py:148-160 add_node calls."""
    assert "Bull Researcher" in LANGGRAPH_NODE_TO_STAGE
    assert "Bear Researcher" in LANGGRAPH_NODE_TO_STAGE
    assert "Portfolio Manager" in LANGGRAPH_NODE_TO_STAGE
    assert "Aggressive Analyst" in LANGGRAPH_NODE_TO_STAGE
    # Setup.py uses "{type.capitalize()} Analyst" for analyst nodes.
    assert "Market Analyst" in LANGGRAPH_NODE_TO_STAGE
    assert "Fundamentals Analyst" in LANGGRAPH_NODE_TO_STAGE


@pytest.mark.unit
def test_callback_fires_on_recognized_node_start():
    started: list[AgentStage] = []
    cb = EngineEventCallback(on_stage_started=started.append)
    cb.on_chain_start({"name": "Bull Researcher"}, inputs={})
    assert started == [AgentStage.BULL_RESEARCHER]


@pytest.mark.unit
def test_callback_silent_on_unknown_chain_name():
    """Inner LangChain Runnables (LLM calls, tool nodes, msg-clear) must NOT
    produce agent_started events."""
    started: list[AgentStage] = []
    cb = EngineEventCallback(on_stage_started=started.append)
    cb.on_chain_start({"name": "tools_market"}, inputs={})
    cb.on_chain_start({"name": "Msg Clear Market"}, inputs={})
    cb.on_chain_start({"name": "ChatAnthropic"}, inputs={})
    cb.on_chain_start({"name": None}, inputs={})
    cb.on_chain_start(None, inputs={})
    assert started == []


@pytest.mark.unit
def test_callback_resolves_via_kwargs_name():
    """When LangChain passes the node name via kwargs['name'] instead of serialized."""
    started: list[AgentStage] = []
    cb = EngineEventCallback(on_stage_started=started.append)
    cb.on_chain_start(serialized=None, inputs={}, name="Trader")
    assert started == [AgentStage.TRADER]


@pytest.mark.unit
def test_on_chain_end_fires_on_recognized_node():
    finished: list[AgentStage] = []
    cb = EngineEventCallback(on_stage_finished=finished.append)
    cb.on_chain_end(outputs={}, name="Portfolio Manager")
    assert finished == [AgentStage.PORTFOLIO_MANAGER]


@pytest.mark.unit
def test_callback_with_no_handlers_does_not_error():
    """Constructing without handlers + receiving events must be a no-op, not crash."""
    cb = EngineEventCallback()
    cb.on_chain_start({"name": "Bull Researcher"}, inputs={})
    cb.on_chain_end(outputs={}, name="Bull Researcher")
