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
def test_engine_runner_forwards_node_hooks_not_event_callback(monkeypatch):
    """G-8 / FR-005: _real_run_ticker must forward on_node_started + on_node_finished
    to _default_propagate, NOT pass an EngineEventCallback in the callbacks list.
    TokenCostCallback is the only callback expected in production runs."""
    from tradingagents.engine import runner as runner_module

    captured: dict = {}

    def fake_default_propagate(
        ticker,
        trade_date,
        callbacks=None,
        on_node_started=None,
        on_node_finished=None,
    ):
        captured["ticker"] = ticker
        captured["trade_date"] = trade_date
        captured["callbacks"] = list(callbacks or [])
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
    # Hooks must be wired (not None).
    assert callable(captured["on_node_started"]), "on_node_started must be forwarded"
    assert callable(captured["on_node_finished"]), "on_node_finished must be forwarded"
    # Only TokenCostCallback should be in the callbacks list — NOT EngineEventCallback.
    cb_class_names = [type(cb).__name__ for cb in captured["callbacks"]]
    assert "TokenCostCallback" in cb_class_names, "TokenCostCallback still required for cost meter"
    assert "EngineEventCallback" not in cb_class_names, (
        "FR-005 G-8 closure: EngineEventCallback must NOT be wired by the runner; "
        "per-node events come from the stream() loop instead"
    )


# ---------------------------------------------------------------------------
# TokenCostCallback (Phase 1c — FR-019, SC-007)
# ---------------------------------------------------------------------------

from tradingagents.engine.callbacks import (  # noqa: E402
    ANTHROPIC_PRICING_USD_PER_M,
    TokenCostCallback,
    _cost_for_call,
    _model_pricing,
)


@pytest.mark.unit
def test_pricing_table_has_required_models():
    """Cost meter MUST recognize the production-default models per spec FR-019."""
    assert "claude-opus-4-7" in ANTHROPIC_PRICING_USD_PER_M
    assert "claude-haiku-4-5" in ANTHROPIC_PRICING_USD_PER_M


@pytest.mark.unit
def test_pricing_match_by_longest_prefix():
    """Versioned variants (e.g. claude-haiku-4-5-20251001) must match base model."""
    p = _model_pricing("claude-haiku-4-5-20251001")
    assert p == ANTHROPIC_PRICING_USD_PER_M["claude-haiku-4-5-20251001"]


@pytest.mark.unit
def test_pricing_falls_back_to_default_for_unknown_model():
    """Unknown models get conservative default — never zero-cost."""
    p = _model_pricing("claude-future-7-9-20270101")
    assert p["input"] > 0
    assert p["output"] > 0


@pytest.mark.unit
def test_pricing_handles_empty_model_string():
    p = _model_pricing("")
    assert p["input"] > 0


@pytest.mark.unit
def test_cost_for_call_opus_math():
    """Opus 4.7: $15/M input + $75/M output. 10K in + 2K out → 0.15 + 0.15 = $0.30."""
    cost = _cost_for_call("claude-opus-4-7", 10_000, 2_000)
    assert abs(cost - 0.30) < 1e-9


@pytest.mark.unit
def test_cost_for_call_haiku_math():
    """Haiku 4.5: $1/M input + $5/M output. 10K in + 2K out → 0.01 + 0.01 = $0.02."""
    cost = _cost_for_call("claude-haiku-4-5", 10_000, 2_000)
    assert abs(cost - 0.02) < 1e-9


@pytest.mark.unit
def test_cost_for_call_zero_tokens_is_zero():
    assert _cost_for_call("claude-opus-4-7", 0, 0) == 0.0


@pytest.mark.unit
def test_cost_callback_no_handler_does_not_error():
    cb = TokenCostCallback()
    cb.on_llm_end(response=object())  # response with no llm_output is fine


@pytest.mark.unit
def test_cost_callback_extracts_from_llm_output_token_usage():
    """LLMResult.llm_output={"token_usage": ..., "model_name": ...} (OpenAI-style)."""
    deltas: list[tuple[float, str, int, int]] = []
    cb = TokenCostCallback(on_cost_delta=lambda d, m, i, o: deltas.append((d, m, i, o)))

    class FakeResp:
        llm_output = {
            "token_usage": {"prompt_tokens": 1000, "completion_tokens": 500},
            "model_name": "claude-opus-4-7",
        }
        generations = []

    cb.on_llm_end(response=FakeResp())
    assert len(deltas) == 1
    delta, model, in_tok, out_tok = deltas[0]
    assert model == "claude-opus-4-7"
    assert in_tok == 1000
    assert out_tok == 500
    # 1000 input @ $15/M + 500 output @ $75/M = 0.015 + 0.0375 = 0.0525
    assert abs(delta - 0.0525) < 1e-9


@pytest.mark.unit
def test_cost_callback_extracts_from_anthropic_input_output_tokens():
    """langchain-anthropic uses input_tokens/output_tokens (not prompt_/completion_)."""
    deltas: list = []
    cb = TokenCostCallback(on_cost_delta=lambda d, m, i, o: deltas.append((d, m, i, o)))

    class FakeResp:
        llm_output = {
            "token_usage": {"input_tokens": 2000, "output_tokens": 1000},
            "model_name": "claude-haiku-4-5",
        }
        generations = []

    cb.on_llm_end(response=FakeResp())
    assert len(deltas) == 1
    delta, _, in_tok, out_tok = deltas[0]
    assert in_tok == 2000
    assert out_tok == 1000


@pytest.mark.unit
def test_cost_callback_skips_when_no_usage_data():
    """No usage_metadata anywhere → silently skip (don't crash, don't fake cost)."""
    deltas: list = []
    cb = TokenCostCallback(on_cost_delta=lambda d, m, i, o: deltas.append((d, m, i, o)))

    class FakeResp:
        llm_output = None
        generations = []

    cb.on_llm_end(response=FakeResp())
    assert deltas == []


@pytest.mark.unit
def test_cost_callback_skips_when_zero_tokens():
    """Zero tokens both sides → no delta (some streaming paths fire on_llm_end with 0)."""
    deltas: list = []
    cb = TokenCostCallback(on_cost_delta=lambda d, m, i, o: deltas.append((d, m, i, o)))

    class FakeResp:
        llm_output = {"token_usage": {"input_tokens": 0, "output_tokens": 0}, "model_name": "x"}
        generations = []

    cb.on_llm_end(response=FakeResp())
    assert deltas == []


@pytest.mark.unit
def test_cost_callback_isolates_handler_exceptions():
    """A throwing on_cost_delta must not propagate (cost-meter MUST NEVER block propagate)."""

    def explode(d, m, i, o):
        raise RuntimeError("boom")

    cb = TokenCostCallback(on_cost_delta=explode)

    class FakeResp:
        llm_output = {
            "token_usage": {"input_tokens": 100, "output_tokens": 50},
            "model_name": "claude-haiku-4-5",
        }
        generations = []

    # Must NOT raise.
    cb.on_llm_end(response=FakeResp())
