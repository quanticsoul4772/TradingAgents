"""Unit tests for graph/conditional_logic.py — debate-termination + tool-routing.

The framework's debate-round count and routing logic was at 21% coverage.
These pure-Python branch tests bring it to ~95% without needing real LLM
or graph machinery.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from tradingagents.graph.conditional_logic import ConditionalLogic

# -- Analyst tool-routing helpers --------------------------------------------


def _state_with_last_message(tool_calls):
    """State stub whose last message has the given tool_calls.

    Uses ``spec=AIMessage`` so the conditional's ``isinstance(msg, AIMessage)``
    narrowing accepts the mock — matching the LangGraph contract that the
    analyst's last message is always an AIMessage.
    """
    msg = MagicMock(spec=AIMessage)
    msg.tool_calls = tool_calls
    return {"messages": [msg]}


@pytest.mark.unit
def test_should_continue_market_routes_to_tools_when_tool_calls_present():
    cl = ConditionalLogic()
    state = _state_with_last_message(["fake_tool_call"])
    assert cl.should_continue_market(state) == "tools_market"


@pytest.mark.unit
def test_should_continue_market_routes_to_msg_clear_when_no_tool_calls():
    cl = ConditionalLogic()
    state = _state_with_last_message([])
    assert cl.should_continue_market(state) == "Msg Clear Market"


@pytest.mark.unit
def test_should_continue_social_branches():
    cl = ConditionalLogic()
    assert cl.should_continue_social(_state_with_last_message(["x"])) == "tools_social"
    assert cl.should_continue_social(_state_with_last_message([])) == "Msg Clear Social"


@pytest.mark.unit
def test_should_continue_news_branches():
    cl = ConditionalLogic()
    assert cl.should_continue_news(_state_with_last_message(["x"])) == "tools_news"
    assert cl.should_continue_news(_state_with_last_message([])) == "Msg Clear News"


@pytest.mark.unit
def test_should_continue_fundamentals_branches():
    cl = ConditionalLogic()
    assert cl.should_continue_fundamentals(_state_with_last_message(["x"])) == "tools_fundamentals"
    assert cl.should_continue_fundamentals(_state_with_last_message([])) == "Msg Clear Fundamentals"


# -- Bull/Bear debate termination --------------------------------------------


def _debate_state(count: int, current_response: str = "Bull: ..."):
    return {
        "investment_debate_state": {
            "count": count,
            "current_response": current_response,
        }
    }


@pytest.mark.unit
def test_debate_continues_to_bear_after_bull_speaks():
    """Bull just spoke (current_response starts with 'Bull') → next is Bear."""
    cl = ConditionalLogic(max_debate_rounds=2)
    # count=1 (well under 2 * max_debate_rounds=4)
    assert cl.should_continue_debate(_debate_state(1, "Bull: argues...")) == "Bear Researcher"


@pytest.mark.unit
def test_debate_continues_to_bull_after_bear_speaks():
    """current_response not starting with 'Bull' → next is Bull (default)."""
    cl = ConditionalLogic(max_debate_rounds=2)
    assert cl.should_continue_debate(_debate_state(1, "Bear: counters...")) == "Bull Researcher"


@pytest.mark.unit
def test_debate_terminates_at_max_rounds():
    """Once count >= 2 * max_debate_rounds, exit to Research Manager."""
    cl = ConditionalLogic(max_debate_rounds=1)
    assert cl.should_continue_debate(_debate_state(2, "Bear: ...")) == "Research Manager"


@pytest.mark.unit
def test_debate_terminates_at_higher_max_rounds():
    cl = ConditionalLogic(max_debate_rounds=3)
    # 3 rounds * 2 agents = 6; count=6 should terminate
    assert cl.should_continue_debate(_debate_state(6, "Bull: ...")) == "Research Manager"
    # count=5 still continues
    assert cl.should_continue_debate(_debate_state(5, "Bull: ...")) == "Bear Researcher"


# -- Risk debate termination (3 personas) ------------------------------------


def _risk_state(count: int, latest_speaker: str = "Aggressive"):
    return {
        "risk_debate_state": {
            "count": count,
            "latest_speaker": latest_speaker,
        }
    }


@pytest.mark.unit
def test_risk_continues_to_conservative_after_aggressive():
    cl = ConditionalLogic(max_risk_discuss_rounds=2)
    assert (
        cl.should_continue_risk_analysis(_risk_state(1, "Aggressive Analyst"))
        == "Conservative Analyst"
    )


@pytest.mark.unit
def test_risk_continues_to_neutral_after_conservative():
    cl = ConditionalLogic(max_risk_discuss_rounds=2)
    assert (
        cl.should_continue_risk_analysis(_risk_state(2, "Conservative Analyst"))
        == "Neutral Analyst"
    )


@pytest.mark.unit
def test_risk_continues_to_aggressive_after_neutral():
    """Default cycle: after Neutral (or anyone unknown) → Aggressive."""
    cl = ConditionalLogic(max_risk_discuss_rounds=2)
    assert (
        cl.should_continue_risk_analysis(_risk_state(3, "Neutral Analyst")) == "Aggressive Analyst"
    )


@pytest.mark.unit
def test_risk_terminates_at_max_rounds():
    """count >= 3 * max_risk_discuss_rounds → exit to Portfolio Manager."""
    cl = ConditionalLogic(max_risk_discuss_rounds=1)
    # 1 round * 3 agents = 3
    assert cl.should_continue_risk_analysis(_risk_state(3, "Neutral")) == "Portfolio Manager"


@pytest.mark.unit
def test_risk_terminates_at_higher_max_rounds():
    cl = ConditionalLogic(max_risk_discuss_rounds=2)
    # 2 rounds * 3 = 6
    assert cl.should_continue_risk_analysis(_risk_state(6, "Aggressive")) == "Portfolio Manager"
    # 5 still continues
    assert cl.should_continue_risk_analysis(_risk_state(5, "Aggressive")) == "Conservative Analyst"


@pytest.mark.unit
def test_default_max_rounds_is_one():
    """Constructor defaults match documented framework defaults."""
    cl = ConditionalLogic()
    assert cl.max_debate_rounds == 1
    assert cl.max_risk_discuss_rounds == 1
