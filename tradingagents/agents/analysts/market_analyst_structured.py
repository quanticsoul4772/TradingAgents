"""BR-3 Squeak — structured-output market analyst variant.

Per `experiments/2026-05-09-001-br3-squeak-market-analyst/HYPOTHESIS.md`,
BR-3 tests whether the analyst-stage prose-to-structured bottleneck is
analogous to WC-10's confirmed PM-stage bottleneck.

Implementation Option A from HYPOTHESIS: this module is a FORK of
`market_analyst.py` that uses the same tools (technical indicators,
OHLCV, VIX, sector ETF, options) but emits a structured Pydantic
object (`MarketAnalystSquared`) instead of free-form prose. The
structured output is rendered as a SHORT markdown table so downstream
consumers (research manager, bull/bear, PM) see a structured-but-
markdown `state["market_report"]` and don't need to change.

Activation: set `market_analyst_format: "structured"` in config.
Default `"prose"` preserves backward compat with the existing prose
analyst module.

Architecture:

1. ReAct loop with `bind_tools` (same as prose analyst) — agent
   gathers data via tool calls
2. When the agent terminates the ReAct loop (no more tool_calls),
   take the final message + do a SECOND structured-output call to
   distill the analysis into MarketAnalystSquared fields
3. Render structured fields as compact markdown table for
   `state["market_report"]`

The second LLM call adds ~$0.05-0.10 per propagate. Total cost per
propagate stays under T2 (~$0.40-0.50).
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.schemas import (
    MarketAnalystSquared,
    render_market_analyst_squared,
)
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_indicators,
    get_language_instruction,
    get_stock_data,
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_options_summary,
    get_sector_etf_strength,
    get_vix,
)


def create_market_analyst_structured(llm):
    """Create the BR-3 Squeak structured-output market analyst node."""

    def market_analyst_structured_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_stock_data,
            get_indicators,
            get_vix,
            get_sector_etf_strength,
            get_options_summary,
        ]

        # System message instructs the agent to gather evidence via tools
        # then emit a STRUCTURED summary (different from prose analyst's
        # narrative report instruction).
        system_message = """You are a market analyst tasked with producing STRUCTURED output (BR-3 Squeak mode).

Use the provided tools to gather evidence:
- get_stock_data + get_indicators (up to 8 complementary indicators per the standard list)
- get_vix (macro regime)
- get_sector_etf_strength (ticker vs sector ETF)
- get_options_summary (IV, put/call ratio, max-pain)

When you have gathered sufficient evidence, summarize your analysis in SHORT structured form:
- bullish_score: continuous [-1.0, +1.0] (signed conviction; -1=max bear, 0=balanced, +1=max bull)
- confidence: 0.0-1.0
- key_drivers: up to 5 short bullets supporting the score
- key_risks: up to 5 short bullets against the score
- citations: short references to specific tool outputs that informed your view

DO NOT write a long prose report. The downstream synthesis layer consumes
structured fields, not narrative. Emit your final analysis as a JSON object
matching the MarketAnalystSquared schema.""" + get_language_instruction()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a structured-output market analyst (BR-3 Squeak mode)."
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

        # Phase 1: ReAct loop — agent gathers data via tool calls
        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            # Phase 2: ReAct terminated — distill into structured output via
            # second LLM call. Result.content is the agent's final prose
            # synthesis; we ask the LLM to convert it to structured fields.
            try:
                structured_llm = llm.with_structured_output(MarketAnalystSquared)
                squared = structured_llm.invoke(
                    f"Convert the following market analysis into structured "
                    f"MarketAnalystSquared fields:\n\n{result.content}"
                )
                report = render_market_analyst_squared(squared)
            except Exception:  # noqa: BLE001 — fall back to prose if structured fails
                # Defensive: if structured-output call fails (provider issue,
                # parsing error, etc.), fall back to prose so the propagate
                # doesn't crash. Test will catch the structured path.
                report = "## Market Analyst (structured fallback) report\n\n" + result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_structured_node
