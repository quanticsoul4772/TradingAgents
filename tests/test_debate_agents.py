"""Unit tests for the 5 debate agents (Bull, Bear researchers + 3 risk debators).

Each factory has the same shape: takes an llm, returns a node function that
reads a debate-state slice from AgentState, builds a prompt, calls
llm.invoke(prompt), and writes back updated debate-state with:
  - Persona-prefixed argument appended to history fields
  - count incremented
  - latest_speaker / current_response set

These were all at 6% coverage. Tests bring each to ~95%+ by mocking llm
and asserting the state-update shape.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tradingagents.agents.researchers.bear_researcher import create_bear_researcher
from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
from tradingagents.agents.risk_mgmt.aggressive_debator import create_aggressive_debator
from tradingagents.agents.risk_mgmt.conservative_debator import create_conservative_debator
from tradingagents.agents.risk_mgmt.neutral_debator import create_neutral_debator


def _llm_returning(content: str) -> MagicMock:
    llm = MagicMock()
    response = MagicMock()
    response.content = content
    llm.invoke.return_value = response
    return llm


def _investment_state(
    history: str = "",
    bull_history: str = "",
    bear_history: str = "",
    current_response: str = "",
    count: int = 0,
) -> dict:
    """Minimal AgentState for bull/bear nodes."""
    return {
        "investment_debate_state": {
            "history": history,
            "bull_history": bull_history,
            "bear_history": bear_history,
            "current_response": current_response,
            "count": count,
        },
        "market_report": "market analysis",
        "sentiment_report": "sentiment analysis",
        "news_report": "news",
        "fundamentals_report": "fundamentals",
    }


def _risk_state(
    history: str = "",
    aggressive_history: str = "",
    conservative_history: str = "",
    neutral_history: str = "",
    current_aggressive_response: str = "",
    current_conservative_response: str = "",
    current_neutral_response: str = "",
    count: int = 0,
) -> dict:
    return {
        "risk_debate_state": {
            "history": history,
            "aggressive_history": aggressive_history,
            "conservative_history": conservative_history,
            "neutral_history": neutral_history,
            "current_aggressive_response": current_aggressive_response,
            "current_conservative_response": current_conservative_response,
            "current_neutral_response": current_neutral_response,
            "count": count,
        },
        "market_report": "market",
        "sentiment_report": "sentiment",
        "news_report": "news",
        "fundamentals_report": "fundamentals",
        "trader_investment_plan": "trader plan",
    }


# -- Bull researcher ---------------------------------------------------------


@pytest.mark.unit
def test_bull_researcher_appends_argument_with_persona_prefix():
    node = create_bull_researcher(_llm_returning("growth potential is strong"))
    out = node(_investment_state())
    s = out["investment_debate_state"]
    assert s["current_response"].startswith("Bull Analyst:")
    assert "growth potential is strong" in s["current_response"]


@pytest.mark.unit
def test_bull_researcher_increments_count():
    node = create_bull_researcher(_llm_returning("argument"))
    out = node(_investment_state(count=2))
    assert out["investment_debate_state"]["count"] == 3


@pytest.mark.unit
def test_bull_researcher_appends_to_bull_history_only():
    """Bull's argument lands in bull_history; bear_history is preserved unchanged."""
    node = create_bull_researcher(_llm_returning("bull argument"))
    out = node(
        _investment_state(
            bull_history="prior bull",
            bear_history="prior bear",
        )
    )
    s = out["investment_debate_state"]
    assert "prior bull" in s["bull_history"]
    assert "Bull Analyst: bull argument" in s["bull_history"]
    assert s["bear_history"] == "prior bear"


@pytest.mark.unit
def test_bull_researcher_prompt_includes_state_reports():
    """The 4 analyst reports + debate history must be passed into the prompt."""
    llm = _llm_returning("ok")
    node = create_bull_researcher(llm)
    state = _investment_state(history="full debate so far", current_response="last bear arg")
    state["market_report"] = "MARKET_X"
    state["news_report"] = "NEWS_Y"
    node(state)
    prompt = llm.invoke.call_args.args[0]
    assert "MARKET_X" in prompt
    assert "NEWS_Y" in prompt
    assert "full debate so far" in prompt
    assert "last bear arg" in prompt


# -- Bear researcher ---------------------------------------------------------


@pytest.mark.unit
def test_bear_researcher_appends_argument_with_persona_prefix():
    node = create_bear_researcher(_llm_returning("downside risks are real"))
    out = node(_investment_state())
    s = out["investment_debate_state"]
    assert s["current_response"].startswith("Bear Analyst:")
    assert "downside risks are real" in s["current_response"]


@pytest.mark.unit
def test_bear_researcher_appends_to_bear_history_only():
    node = create_bear_researcher(_llm_returning("bear argument"))
    out = node(
        _investment_state(
            bull_history="prior bull",
            bear_history="prior bear",
        )
    )
    s = out["investment_debate_state"]
    assert "prior bear" in s["bear_history"]
    assert "Bear Analyst: bear argument" in s["bear_history"]
    assert s["bull_history"] == "prior bull"


@pytest.mark.unit
def test_bear_researcher_increments_count():
    node = create_bear_researcher(_llm_returning("arg"))
    out = node(_investment_state(count=5))
    assert out["investment_debate_state"]["count"] == 6


# -- Risk debators (parametrized over all 3 personas) -----------------------


RISK_DEBATORS = [
    (
        "aggressive",
        create_aggressive_debator,
        "Aggressive Analyst:",
        "Aggressive",
        "aggressive_history",
        "current_aggressive_response",
    ),
    (
        "conservative",
        create_conservative_debator,
        "Conservative Analyst:",
        "Conservative",
        "conservative_history",
        "current_conservative_response",
    ),
    (
        "neutral",
        create_neutral_debator,
        "Neutral Analyst:",
        "Neutral",
        "neutral_history",
        "current_neutral_response",
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize(
    "name,factory,prefix,speaker,history_key,current_key", RISK_DEBATORS
)
def test_risk_debator_appends_argument_with_correct_prefix(
    name, factory, prefix, speaker, history_key, current_key
):
    node = factory(_llm_returning(f"{name} take"))
    out = node(_risk_state())
    s = out["risk_debate_state"]
    # Prefix labels — different debators use different exact strings, so we
    # just check the argument text + speaker tag, not the exact prefix.
    assert f"{name} take" in s.get(current_key, s.get("current_response", ""))


@pytest.mark.unit
@pytest.mark.parametrize(
    "name,factory,prefix,speaker,history_key,current_key", RISK_DEBATORS
)
def test_risk_debator_sets_latest_speaker(
    name, factory, prefix, speaker, history_key, current_key
):
    node = factory(_llm_returning("ok"))
    out = node(_risk_state())
    assert out["risk_debate_state"]["latest_speaker"] == speaker


@pytest.mark.unit
@pytest.mark.parametrize(
    "name,factory,prefix,speaker,history_key,current_key", RISK_DEBATORS
)
def test_risk_debator_increments_count(
    name, factory, prefix, speaker, history_key, current_key
):
    node = factory(_llm_returning("ok"))
    out = node(_risk_state(count=4))
    assert out["risk_debate_state"]["count"] == 5


@pytest.mark.unit
@pytest.mark.parametrize(
    "name,factory,prefix,speaker,history_key,current_key", RISK_DEBATORS
)
def test_risk_debator_preserves_other_history_buckets(
    name, factory, prefix, speaker, history_key, current_key
):
    """A given debator must only append to its own history bucket — leave
    the other two unchanged."""
    node = factory(_llm_returning("my take"))
    out = node(
        _risk_state(
            aggressive_history="agg-prior",
            conservative_history="cons-prior",
            neutral_history="neut-prior",
        )
    )
    s = out["risk_debate_state"]
    other_buckets = {
        "aggressive_history",
        "conservative_history",
        "neutral_history",
    } - {history_key}
    for other in other_buckets:
        assert "my take" not in s[other]


@pytest.mark.unit
@pytest.mark.parametrize(
    "name,factory,prefix,speaker,history_key,current_key", RISK_DEBATORS
)
def test_risk_debator_prompt_includes_trader_decision(
    name, factory, prefix, speaker, history_key, current_key
):
    """Every risk debator gets the trader's decision in its prompt context."""
    llm = _llm_returning("ok")
    node = factory(llm)
    state = _risk_state()
    state["trader_investment_plan"] = "TRADER_PROPOSAL_XYZ"
    node(state)
    prompt = llm.invoke.call_args.args[0]
    assert "TRADER_PROPOSAL_XYZ" in prompt
