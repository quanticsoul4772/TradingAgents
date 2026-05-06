from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_fundamentals,
            get_balance_sheet,
            get_cashflow,
            get_income_statement,
            # Extended signals (added 2026-05-03 per docs/SIGNALS.md):
            get_recommendations,  # analyst consensus + recent rating changes
            get_earnings_calendar,  # upcoming earnings dates (changes 21d-window prediction)
            get_short_interest,  # short interest + ownership concentration
            get_institutional_holders,  # institutional + mutual-fund positioning
            get_corporate_actions,  # dividend / split history + ESG
        ]

        system_message = (
            "You are a researcher tasked with analyzing fundamental information about a company. "
            "Write a comprehensive report covering financials, company profile, analyst consensus, "
            "earnings calendar, ownership / short interest, and corporate actions. Make sure to include "
            "as much detail as possible. Provide specific, actionable insights with supporting evidence "
            "to help traders make informed decisions."
            + " Make sure to append a Markdown table at the end of the report to organize key points."
            + " Use the available tools: `get_fundamentals` (overview), `get_balance_sheet`, `get_cashflow`, "
            "`get_income_statement` (statements), `get_recommendations` (analyst ratings + upgrades / "
            "downgrades — predictive at 1-3 month horizon), `get_earnings_calendar` (upcoming earnings — "
            "critical because the framework's measurement window may include earnings), `get_short_interest` "
            "(short pressure + ownership concentration — squeeze potential), `get_institutional_holders` "
            "(institutional positioning), `get_corporate_actions` (dividends + splits + ESG ratings)."
            + get_language_instruction(),
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
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
            report = result.content

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
