"""Unit tests for the 4 analyst agent factories.

Each analyst factory returns a node function with the same shape:
- Build a ChatPromptTemplate with system message + tools
- chain = prompt | llm.bind_tools(tools)
- result = chain.invoke(state["messages"])
- If result.tool_calls is empty → write result.content to a per-analyst
  report field. Otherwise → empty report (waiting for tool round-trip).
- Always returns {"messages": [result], "<analyst>_report": ...}

These were all at 19% coverage. Tests bring each to ~95%+ by mocking the
chain at llm.bind_tools level.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
from tradingagents.agents.analysts.market_analyst import create_market_analyst
from tradingagents.agents.analysts.news_analyst import create_news_analyst
from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst

ANALYSTS = [
    ("market", create_market_analyst, "market_report"),
    ("news", create_news_analyst, "news_report"),
    ("fundamentals", create_fundamentals_analyst, "fundamentals_report"),
    ("social", create_social_media_analyst, "sentiment_report"),
]


def _llm_returning_chain(content: str, tool_calls: list | None = None):
    """Build an llm whose bind_tools returns a Runnable-like object that,
    when piped on the right side of `prompt | bound_llm`, produces a chain
    whose .invoke() returns a result with the given content + tool_calls.

    Implemented by mocking ChatPromptTemplate.from_messages so the LangChain
    pipe machinery doesn't need real Runnables.
    """
    result = MagicMock()
    result.content = content
    result.tool_calls = tool_calls or []

    # The chain `prompt | bound_llm` is what gets `.invoke(state["messages"])`.
    chain = MagicMock()
    chain.invoke.return_value = result

    # The bound LLM (from llm.bind_tools(tools)). prompt | bound_llm → chain.
    bound_llm = MagicMock()
    # Make `prompt | bound_llm` resolve to our chain, regardless of which side
    # implements __or__. ChatPromptTemplate's __or__ is what fires.
    fake_prompt = MagicMock()
    fake_prompt.partial.return_value = fake_prompt
    fake_prompt.__or__ = MagicMock(return_value=chain)

    llm = MagicMock()
    llm.bind_tools.return_value = bound_llm
    return llm, result, fake_prompt


def _state(date: str = "2026-02-06") -> dict:
    return {
        "trade_date": date,
        "company_of_interest": "NVDA",
        "messages": [HumanMessage(content="prior")],
    }


def _patch_prompt(fake_prompt):
    """Context-manager helper: patch ChatPromptTemplate.from_messages in all
    4 analyst modules to return our fake_prompt."""
    return patch.multiple(
        "langchain_core.prompts.ChatPromptTemplate",
        from_messages=MagicMock(return_value=fake_prompt),
    )


@pytest.mark.unit
@pytest.mark.parametrize("name,factory,report_key", ANALYSTS)
def test_analyst_writes_content_to_report_when_no_tool_calls(name, factory, report_key):
    """When the LLM returns final text (no tool_calls), content lands in the
    per-analyst report field."""
    llm, result, prompt = _llm_returning_chain("ANALYST OUTPUT TEXT", tool_calls=[])
    node = factory(llm)
    with _patch_prompt(prompt):
        out = node(_state())
    assert out[report_key] == "ANALYST OUTPUT TEXT"
    assert out["messages"] == [result]


@pytest.mark.unit
@pytest.mark.parametrize("name,factory,report_key", ANALYSTS)
def test_analyst_returns_empty_report_when_tool_calls_present(name, factory, report_key):
    """When the LLM emits a tool call (mid-ReAct loop), the report field is
    blank — final report only lands once the loop exits."""
    llm, result, prompt = _llm_returning_chain(
        "", tool_calls=[{"name": "get_stock_data", "args": {}}]
    )
    node = factory(llm)
    with _patch_prompt(prompt):
        out = node(_state())
    assert out[report_key] == ""
    assert out["messages"] == [result]


@pytest.mark.unit
@pytest.mark.parametrize("name,factory,report_key", ANALYSTS)
def test_analyst_calls_bind_tools(name, factory, report_key):
    """Each analyst must wire its tools into the LLM via bind_tools."""
    llm, _result, prompt = _llm_returning_chain("ok")
    node = factory(llm)
    with _patch_prompt(prompt):
        node(_state())
    llm.bind_tools.assert_called_once()
    tools_arg = llm.bind_tools.call_args.args[0]
    assert len(tools_arg) >= 1  # each analyst declares at least one tool


@pytest.mark.unit
@pytest.mark.parametrize("name,factory,report_key", ANALYSTS)
def test_analyst_passes_state_messages_to_chain(name, factory, report_key):
    """The chain.invoke must be called with state['messages'] (the running
    conversation), not anything else."""
    llm, _result, prompt = _llm_returning_chain("ok")
    node = factory(llm)
    state = _state()
    sentinel_msgs = [HumanMessage(content="SENTINEL_X")]
    state["messages"] = sentinel_msgs
    with _patch_prompt(prompt):
        node(state)
    # The chain (mocked __or__ result) gets state["messages"] verbatim.
    chain = prompt.__or__.return_value
    chain.invoke.assert_called_once_with(sentinel_msgs)


@pytest.mark.unit
def test_market_analyst_uses_two_data_tools():
    """Market analyst declares get_stock_data + get_indicators."""
    llm, _r, prompt = _llm_returning_chain("ok")
    node = create_market_analyst(llm)
    with _patch_prompt(prompt):
        node(_state())
    tools = llm.bind_tools.call_args.args[0]
    tool_names = {t.name for t in tools}
    assert "get_stock_data" in tool_names
    assert "get_indicators" in tool_names


@pytest.mark.unit
def test_fundamentals_analyst_uses_four_data_tools():
    """Fundamentals declares fundamentals + balance + cashflow + income."""
    llm, _r, prompt = _llm_returning_chain("ok")
    node = create_fundamentals_analyst(llm)
    node(_state())
    tools = llm.bind_tools.call_args.args[0]
    tool_names = {t.name for t in tools}
    expected = {"get_fundamentals", "get_balance_sheet", "get_cashflow", "get_income_statement"}
    assert expected <= tool_names


@pytest.mark.unit
def test_news_analyst_uses_news_tools():
    """News analyst declares get_news + get_global_news (insider_transactions
    is in the trading_graph's tool node but not in the analyst's prompt-tool
    list — analyst doesn't ask for it directly)."""
    llm, _r, prompt = _llm_returning_chain("ok")
    node = create_news_analyst(llm)
    with _patch_prompt(prompt):
        node(_state())
    tools = llm.bind_tools.call_args.args[0]
    tool_names = {t.name for t in tools}
    assert "get_news" in tool_names
    assert "get_global_news" in tool_names
