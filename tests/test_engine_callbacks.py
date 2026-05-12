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
    cb.on_chain_end(outputs={}, name="Bull Receiver")


# ---------------------------------------------------------------------------
# FR-005 stream-iteration path (Spec 250 G-8 closure)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_propagate_signature_accepts_node_hooks():
    """G-8 / FR-005 contract: TradingAgentsGraph.propagate must accept
    on_node_started + on_node_finished kwargs so the engine can supply them.
    Pinned via signature inspection — no graph instantiation needed."""
    import inspect

    from tradingagents.graph.trading_graph import TradingAgentsGraph

    sig = inspect.signature(TradingAgentsGraph.propagate)
    params = sig.parameters
    assert "on_node_started" in params, "propagate() must accept on_node_started kwarg"
    assert "on_node_finished" in params, "propagate() must accept on_node_finished kwarg"
    assert params["on_node_started"].kind == inspect.Parameter.KEYWORD_ONLY
    assert params["on_node_finished"].kind == inspect.Parameter.KEYWORD_ONLY


@pytest.mark.unit
def test_run_graph_signature_accepts_node_hooks():
    """G-8 / FR-005 contract: _run_graph must accept on_node_started +
    on_node_finished kwargs so propagate can forward them. The actual
    stream-vs-invoke routing is exercised by the engine integration suite."""
    import inspect

    from tradingagents.graph.trading_graph import TradingAgentsGraph

    sig = inspect.signature(TradingAgentsGraph._run_graph)
    params = sig.parameters
    assert "on_node_started" in params
    assert "on_node_finished" in params


@pytest.mark.unit
def test_engine_runner_forwards_node_hooks(monkeypatch):
    """_real_run_ticker forwards on_node_started + on_node_finished to
    _default_propagate. Per-node events come from the stream() loop in
    TradingAgentsGraph._run_graph, not from a LangChain BaseCallbackHandler."""
    from tradingagents.engine import runner as runner_module

    captured: dict = {}

    def fake_default_propagate(
        ticker,
        trade_date,
        on_node_started=None,
        on_node_finished=None,
    ):
        captured["ticker"] = ticker
        captured["trade_date"] = trade_date
        captured["on_node_started"] = on_node_started
        captured["on_node_finished"] = on_node_finished
        return "Hold"

    monkeypatch.setattr(runner_module, "_default_propagate", fake_default_propagate)

    r = runner_module.EngineRunner(run_dir=__import__("pathlib").Path("/tmp/ta-test-engine-hooks"))
    r._progress = runner_module.ProgressFile(
        run_id="test",
        started_at="2026-05-11T00:00:00Z",
        trade_date="2026-05-11",
        watchlist=["NVDA"],
        heartbeat_at="2026-05-11T00:00:00Z",
    )
    r._real_run_ticker("NVDA")

    assert captured["ticker"] == "NVDA"
    assert callable(captured["on_node_started"]), "on_node_started must be forwarded"
    assert callable(captured["on_node_finished"]), "on_node_finished must be forwarded"
