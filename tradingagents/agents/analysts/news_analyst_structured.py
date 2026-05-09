"""BR-3 v2 — structured-output news analyst variant.

Per `experiments/2026-05-09-003-br3-v2-news-fundamentals/HYPOTHESIS.md`,
BR-3 v2 extends the BR-3 v1 market-analyst structured-output test to
the news + fundamentals analyst stages.

Mirrors `tradingagents/agents/analysts/market_analyst_structured.py`
exactly — same ReAct loop + second structured-output call pattern.
Only differences: tool list (news + global news + insider transactions)
and state field written (`news_report` vs `market_report`).

Activation: set `news_analyst_format: "structured"` in config.
Default `"prose"` preserves backward compat.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.schemas import (
    MarketAnalystSquared,
    render_analyst_squared,
)
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_global_news,
    get_insider_transactions,
    get_language_instruction,
    get_news,
)


def create_news_analyst_structured(llm):
    """Create the BR-3 v2 structured-output news analyst node."""

    def news_analyst_structured_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_news,
            get_global_news,
            get_insider_transactions,
        ]

        system_message = """You are a news analyst tasked with producing STRUCTURED output (BR-3 v2 mode).

Use the provided tools to gather evidence:
- get_news (company-specific news searches)
- get_global_news (broader macroeconomic news)
- get_insider_transactions (insider buy/sell activity)

When you have gathered sufficient evidence, summarize your analysis in SHORT structured form:
- bullish_score: continuous [-1.0, +1.0] (signed conviction; -1=max bear, 0=balanced, +1=max bull)
- confidence: 0.0-1.0
- key_drivers: up to 5 short bullets supporting the score (news catalysts; insider buying clusters)
- key_risks: up to 5 short bullets against the score (negative catalysts; insider selling)
- citations: short references to specific news items / insider events that informed your view

DO NOT write a long prose report. The downstream synthesis layer consumes
structured fields, not narrative. Emit your final analysis as a JSON object
matching the MarketAnalystSquared schema.""" + get_language_instruction()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a structured-output news analyst (BR-3 v2 mode)."
                    " Use the provided tools to gather evidence."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            try:
                structured_llm = llm.with_structured_output(MarketAnalystSquared)
                squared = structured_llm.invoke(
                    f"Convert the following news analysis into structured "
                    f"MarketAnalystSquared fields:\n\n{result.content}"
                )
                report = render_analyst_squared(squared, analyst_name="News Analyst")
            except Exception:  # noqa: BLE001 — fall back to prose if structured fails
                report = "## News Analyst (structured fallback) report\n\n" + result.content

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_structured_node
