"""Unit tests for graph/trading_graph.py — module-level fetch_returns,
provider-kwarg routing, state logging, and pending-entry resolution.

Previously 53% — these tests target the unmocked-paths gap. Skips the
full propagate() integration (too much LLM/graph machinery) — those are
covered indirectly by checkpoint_resume.py.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.graph.trading_graph import TradingAgentsGraph, fetch_returns

# -- fetch_returns (module-level) --------------------------------------------


def _fake_history(closes: list[float]) -> pd.DataFrame:
    """yfinance-shaped frame with the given Close prices."""
    return pd.DataFrame({"Close": closes})


@pytest.mark.unit
def test_fetch_returns_happy_path():
    """Stock and SPY both have enough data → (raw, alpha, days) returned."""
    stock_frame = _fake_history([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])  # +5%
    spy_frame = _fake_history([400.0, 402.0, 404.0, 406.0, 408.0, 410.0])  # +2.5%

    def fake_ticker(t):
        m = MagicMock()
        m.history.return_value = stock_frame if t == "NVDA" else spy_frame
        return m

    with patch("tradingagents.graph.trading_graph.yf.Ticker", side_effect=fake_ticker):
        raw, alpha, days = fetch_returns("NVDA", "2026-02-06", holding_days=5)

    assert raw == pytest.approx(0.05)
    assert alpha == pytest.approx(0.025)
    assert days == 5


@pytest.mark.unit
def test_fetch_returns_insufficient_stock_data_returns_none():
    """Stock frame too short → (None, None, None)."""
    short_frame = _fake_history([100.0])  # only 1 row
    spy_frame = _fake_history([400.0, 402.0, 404.0, 406.0, 408.0, 410.0])

    def fake_ticker(t):
        m = MagicMock()
        m.history.return_value = short_frame if t == "NVDA" else spy_frame
        return m

    with patch("tradingagents.graph.trading_graph.yf.Ticker", side_effect=fake_ticker):
        raw, alpha, days = fetch_returns("NVDA", "2026-02-06", holding_days=5)

    assert raw is None
    assert alpha is None
    assert days is None


@pytest.mark.unit
def test_fetch_returns_swallows_exceptions():
    """yfinance raising (network, delisted, etc.) → (None, None, None) with log."""

    def raise_yf(t):
        raise RuntimeError("network down")

    with patch("tradingagents.graph.trading_graph.yf.Ticker", side_effect=raise_yf):
        raw, alpha, days = fetch_returns("BOGUS", "2026-02-06")

    assert (raw, alpha, days) == (None, None, None)


@pytest.mark.unit
def test_fetch_returns_uses_actual_days_when_window_is_short():
    """If actual stock data has fewer days than holding_days, use what's there."""
    stock_frame = _fake_history([100.0, 102.0, 104.0])  # only 3 rows for 5-day request
    spy_frame = _fake_history([400.0, 402.0, 404.0])

    def fake_ticker(t):
        m = MagicMock()
        m.history.return_value = stock_frame if t == "NVDA" else spy_frame
        return m

    with patch("tradingagents.graph.trading_graph.yf.Ticker", side_effect=fake_ticker):
        _raw, _alpha, days = fetch_returns("NVDA", "2026-02-06", holding_days=5)

    # min(5, 3-1, 3-1) = 2
    assert days == 2


# -- _get_provider_kwargs ----------------------------------------------------


@pytest.fixture
def mocked_graph(tmp_path):
    """TradingAgentsGraph instance with all heavy initialization mocked.

    Patches LLM client creation, memory log, and graph setup so __init__
    completes without API keys or actual graph compilation. Returns the
    instance for unit testing of the lighter-weight methods.
    """
    config = {
        "llm_provider": "anthropic",
        "deep_think_llm": "claude-sonnet-4-6",
        "quick_think_llm": "claude-haiku-4-5",
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
        "data_cache_dir": str(tmp_path / "cache"),
        "results_dir": str(tmp_path / "results"),
        "memory_log_path": str(tmp_path / "memory.md"),
        "data_vendors": {
            "core_stock_apis": "yfinance",
            "technical_indicators": "yfinance",
            "fundamental_data": "yfinance",
            "news_data": "yfinance",
        },
        "tool_vendors": {},
        "memory_log_max_entries": 50,
    }
    with (
        patch("tradingagents.graph.trading_graph.create_llm_client") as _create,
        patch("tradingagents.graph.trading_graph.TradingMemoryLog") as _mem,
        patch("tradingagents.graph.trading_graph.GraphSetup") as _gs,
        patch("tradingagents.graph.trading_graph.SignalProcessor") as _sp,
        patch("tradingagents.graph.trading_graph.Reflector") as _ref,
    ):
        _create.return_value.get_llm.return_value = MagicMock()
        _gs.return_value.setup_graph.return_value = MagicMock()
        graph = TradingAgentsGraph(config=config)
        graph._mem_mock = _mem  # for tests that need the memory mock
        yield graph


@pytest.mark.unit
def test_get_provider_kwargs_anthropic_with_effort(mocked_graph):
    mocked_graph.config = {
        **mocked_graph.config,
        "llm_provider": "anthropic",
        "anthropic_effort": "high",
    }
    kwargs = mocked_graph._get_provider_kwargs()
    assert kwargs == {"effort": "high"}


@pytest.mark.unit
def test_get_provider_kwargs_anthropic_without_effort(mocked_graph):
    mocked_graph.config = {**mocked_graph.config, "llm_provider": "anthropic"}
    mocked_graph.config.pop("anthropic_effort", None)
    kwargs = mocked_graph._get_provider_kwargs()
    assert kwargs == {}


@pytest.mark.unit
def test_get_provider_kwargs_google_with_thinking_level(mocked_graph):
    mocked_graph.config = {
        **mocked_graph.config,
        "llm_provider": "google",
        "google_thinking_level": "deep",
    }
    kwargs = mocked_graph._get_provider_kwargs()
    assert kwargs == {"thinking_level": "deep"}


@pytest.mark.unit
def test_get_provider_kwargs_openai_with_reasoning_effort(mocked_graph):
    mocked_graph.config = {
        **mocked_graph.config,
        "llm_provider": "openai",
        "openai_reasoning_effort": "medium",
    }
    kwargs = mocked_graph._get_provider_kwargs()
    assert kwargs == {"reasoning_effort": "medium"}


@pytest.mark.unit
def test_get_provider_kwargs_unknown_provider_returns_empty(mocked_graph):
    mocked_graph.config = {**mocked_graph.config, "llm_provider": "deepseek"}
    kwargs = mocked_graph._get_provider_kwargs()
    assert kwargs == {}


# -- _log_state -------------------------------------------------------------


@pytest.mark.unit
def test_log_state_writes_json_with_expected_shape(mocked_graph, tmp_path):
    mocked_graph.ticker = "NVDA"
    mocked_graph.config["results_dir"] = str(tmp_path)
    final_state = {
        "company_of_interest": "NVDA",
        "trade_date": "2026-02-06",
        "market_report": "market text",
        "sentiment_report": "sentiment text",
        "news_report": "news text",
        "fundamentals_report": "fundamentals text",
        "investment_debate_state": {
            "bull_history": "bull",
            "bear_history": "bear",
            "history": "full",
            "current_response": "Bear: ...",
            "judge_decision": "Hold",
        },
        "trader_investment_plan": "trader plan",
        "risk_debate_state": {
            "aggressive_history": "agg",
            "conservative_history": "cons",
            "neutral_history": "neut",
            "history": "full risk",
            "judge_decision": "PM judge",
        },
        "investment_plan": "investment plan",
        "final_trade_decision": "**Rating**: Hold\n",
    }

    mocked_graph._log_state("2026-02-06", final_state)

    log_path = tmp_path / "NVDA" / "TradingAgentsStrategy_logs" / "full_states_log_2026-02-06.json"
    assert log_path.exists()
    saved = json.loads(log_path.read_text(encoding="utf-8"))
    assert saved["company_of_interest"] == "NVDA"
    assert saved["trade_date"] == "2026-02-06"
    assert saved["market_report"] == "market text"
    assert saved["investment_debate_state"]["judge_decision"] == "Hold"
    # Renamed field: trader_investment_plan → trader_investment_decision
    assert saved["trader_investment_decision"] == "trader plan"
    assert saved["final_trade_decision"] == "**Rating**: Hold\n"


# -- _resolve_pending_entries ------------------------------------------------


@pytest.mark.unit
def test_resolve_pending_entries_no_pending_is_noop(mocked_graph):
    """Empty pending list → no calls to fetch_returns or batch_update."""
    mocked_graph.memory_log.get_pending_entries = MagicMock(return_value=[])
    mocked_graph.memory_log.batch_update_with_outcomes = MagicMock()
    with patch.object(mocked_graph, "_fetch_returns") as fetch:
        mocked_graph._resolve_pending_entries("NVDA")
    fetch.assert_not_called()
    mocked_graph.memory_log.batch_update_with_outcomes.assert_not_called()


@pytest.mark.unit
def test_resolve_pending_entries_skips_unresolved_returns(mocked_graph):
    """Pending entries whose price data isn't available yet are SKIPPED, not errored."""
    mocked_graph.memory_log.get_pending_entries = MagicMock(
        return_value=[{"ticker": "NVDA", "date": "2026-04-30", "decision": "Hold"}]
    )
    mocked_graph.memory_log.batch_update_with_outcomes = MagicMock()
    with patch.object(mocked_graph, "_fetch_returns", return_value=(None, None, None)):
        mocked_graph._resolve_pending_entries("NVDA")
    # No batch update because no resolvable outcomes
    mocked_graph.memory_log.batch_update_with_outcomes.assert_not_called()


@pytest.mark.unit
def test_resolve_pending_entries_only_processes_matching_ticker(mocked_graph):
    """Pending entries for OTHER tickers must be ignored."""
    mocked_graph.memory_log.get_pending_entries = MagicMock(
        return_value=[
            {"ticker": "AAPL", "date": "2026-02-06", "decision": "Hold"},
            {"ticker": "MSFT", "date": "2026-02-06", "decision": "Hold"},
        ]
    )
    mocked_graph.memory_log.batch_update_with_outcomes = MagicMock()
    with patch.object(mocked_graph, "_fetch_returns") as fetch:
        mocked_graph._resolve_pending_entries("NVDA")
    fetch.assert_not_called()
    mocked_graph.memory_log.batch_update_with_outcomes.assert_not_called()


@pytest.mark.unit
def test_resolve_pending_entries_writes_resolved_outcomes(mocked_graph):
    """Resolvable returns flow through reflector and into a single batch update."""
    mocked_graph.memory_log.get_pending_entries = MagicMock(
        return_value=[{"ticker": "NVDA", "date": "2026-02-06", "decision": "Hold"}]
    )
    mocked_graph.memory_log.batch_update_with_outcomes = MagicMock()
    mocked_graph.reflector.reflect_on_final_decision = MagicMock(return_value="reflection text")

    with patch.object(mocked_graph, "_fetch_returns", return_value=(0.05, 0.025, 5)):
        mocked_graph._resolve_pending_entries("NVDA")

    mocked_graph.memory_log.batch_update_with_outcomes.assert_called_once()
    [call] = mocked_graph.memory_log.batch_update_with_outcomes.call_args_list
    updates = call.args[0]
    assert len(updates) == 1
    assert updates[0]["ticker"] == "NVDA"
    assert updates[0]["raw_return"] == 0.05
    assert updates[0]["alpha_return"] == 0.025
    assert updates[0]["holding_days"] == 5
    assert updates[0]["reflection"] == "reflection text"


# -- _fetch_returns instance wrapper ----------------------------------------


@pytest.mark.unit
def test_instance_fetch_returns_delegates_to_module_function(mocked_graph):
    """The class method is a thin wrapper around the module-level fetch_returns."""
    with patch(
        "tradingagents.graph.trading_graph.fetch_returns",
        return_value=(0.1, 0.05, 5),
    ) as mock_fr:
        result = mocked_graph._fetch_returns("NVDA", "2026-02-06")
    assert result == (0.1, 0.05, 5)
    mock_fr.assert_called_once_with("NVDA", "2026-02-06", 5)


# -- process_signal --------------------------------------------------------


@pytest.mark.unit
def test_process_signal_delegates_to_signal_processor(mocked_graph):
    """process_signal hands the markdown text to the SignalProcessor."""
    mocked_graph.signal_processor.process_signal = MagicMock(return_value="Hold")
    result = mocked_graph.process_signal("**Rating**: Hold\nblah blah")
    assert result == "Hold"
    mocked_graph.signal_processor.process_signal.assert_called_once()


# -- state-log persistence --------------------------------------------------


@pytest.mark.unit
def test_state_log_persists_contrarian_gate_field(mocked_graph, tmp_path):
    """Regression guard for the 2026-05-06 fix.

    The state-log writer at trading_graph.py:425-453 whitelists fields from
    final_state. Before the fix, `contrarian_gate` was missing from that
    whitelist, so shadow-mode annotations from spec 003 were silently
    dropped — discovered by sc003_financials_gate_check.py."""
    final_state = {
        "company_of_interest": "NVDA",
        "trade_date": "2026-04-03",
        "market_report": "",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
            "judge_decision": "",
        },
        "trader_investment_plan": "",
        "risk_debate_state": {
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "history": "",
            "judge_decision": "",
        },
        "investment_plan": "",
        "final_trade_decision": "**Rating**: Overweight",
        "contrarian_gate": {
            "mode": "shadow",
            "feature_value": 75.0,
            "percentile": 92.0,
            "n_history": 13,
            "would_fire": True,
            "gate_fired": False,
        },
    }
    mocked_graph.ticker = "NVDA"
    mocked_graph._log_state("2026-04-03", final_state)

    log_path = (
        tmp_path
        / "results"
        / "NVDA"
        / "TradingAgentsStrategy_logs"
        / "full_states_log_2026-04-03.json"
    )
    assert log_path.exists()
    persisted = json.loads(log_path.read_text(encoding="utf-8"))
    assert "contrarian_gate" in persisted, (
        "contrarian_gate field missing from persisted state log "
        "(would silently lose shadow-mode gate annotations)"
    )
    assert persisted["contrarian_gate"]["percentile"] == 92.0


@pytest.mark.unit
def test_state_log_contrarian_gate_is_none_when_field_absent(mocked_graph, tmp_path):
    """When mode='off' the PM doesn't add contrarian_gate; persisted value is None."""
    final_state = {
        "company_of_interest": "NVDA",
        "trade_date": "2026-04-03",
        "market_report": "",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
            "judge_decision": "",
        },
        "trader_investment_plan": "",
        "risk_debate_state": {
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "history": "",
            "judge_decision": "",
        },
        "investment_plan": "",
        "final_trade_decision": "**Rating**: Hold",
        # No contrarian_gate key
    }
    mocked_graph.ticker = "NVDA"
    mocked_graph._log_state("2026-04-03", final_state)
    log_path = (
        tmp_path
        / "results"
        / "NVDA"
        / "TradingAgentsStrategy_logs"
        / "full_states_log_2026-04-03.json"
    )
    persisted = json.loads(log_path.read_text(encoding="utf-8"))
    assert persisted["contrarian_gate"] is None
