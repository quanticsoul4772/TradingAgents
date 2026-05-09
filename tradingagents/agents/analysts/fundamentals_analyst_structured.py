"""BR-3 v2 — structured-output fundamentals analyst variant.

Per `experiments/2026-05-09-003-br3-v2-news-fundamentals/HYPOTHESIS.md`,
BR-3 v2 extends the BR-3 v1 market-analyst structured-output test to
the news + fundamentals analyst stages.

Mirrors `tradingagents/agents/analysts/market_analyst_structured.py`
exactly. Only differences: tool list (full fundamentals + extended
signals) and state field written (`fundamentals_report`).

Activation: set `fundamentals_analyst_format: "structured"` in config.
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
    get_balance_sheet,
    get_cashflow,
    get_fundamentals,
    get_income_statement,
    get_language_instruction,
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_corporate_actions,
    get_earnings_calendar,
    get_institutional_holders,
    get_recommendations,
    get_short_interest,
)


def create_fundamentals_analyst_structured(llm):
    """Create the BR-3 v2 structured-output fundamentals analyst node."""

    def fundamentals_analyst_structured_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_fundamentals,
            get_balance_sheet,
            get_cashflow,
            get_income_statement,
            get_recommendations,
            get_earnings_calendar,
            get_short_interest,
            get_institutional_holders,
            get_corporate_actions,
        ]

        system_message = """You are a fundamentals analyst tasked with producing STRUCTURED output (BR-3 v2 mode).

Use the provided tools to gather evidence:
- get_fundamentals + get_balance_sheet + get_cashflow + get_income_statement (financials)
- get_recommendations (analyst consensus + upgrades/downgrades)
- get_earnings_calendar (upcoming earnings dates)
- get_short_interest (short pressure / squeeze potential)
- get_institutional_holders (positioning)
- get_corporate_actions (dividends / splits / ESG)

When you have gathered sufficient evidence, summarize your analysis in SHORT structured form:
- bullish_score: continuous [-1.0, +1.0] (signed conviction; -1=max bear, 0=balanced, +1=max bull)
- confidence: 0.0-1.0
- key_drivers: up to 5 short bullets supporting the score (financial strengths; positive earnings outlook)
- key_risks: up to 5 short bullets against the score (financial weaknesses; downward revisions; bearish ownership trends)
- citations: short references to specific financial metrics / analyst calls / events that informed your view

DO NOT write a long prose report. The downstream synthesis layer consumes
structured fields, not narrative. Emit your final analysis as a JSON object
matching the MarketAnalystSquared schema.""" + get_language_instruction()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a structured-output fundamentals analyst (BR-3 v2 mode)."
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
                    f"Convert the following fundamentals analysis into structured "
                    f"MarketAnalystSquared fields:\n\n{result.content}"
                )
                report = render_analyst_squared(squared, analyst_name="Fundamentals Analyst")
            except Exception:  # noqa: BLE001 — fall back to prose if structured fails
                report = "## Fundamentals Analyst (structured fallback) report\n\n" + result.content

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_structured_node
