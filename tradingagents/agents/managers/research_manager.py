"""Research Manager: turns the bull/bear debate into a structured investment plan for the trader."""

from __future__ import annotations

from tradingagents.agents.schemas import (
    ResearchPlan,
    ResearchPlanV2,
    render_research_plan,
    render_research_plan_v2,
)
from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)

# v1 ("default"): the original prompt. Reserved Hold for "genuinely balanced
# evidence", which mechanically pulled most ratings toward Overweight/Hold/
# Underweight because MR-1 confirmed two-sided evidence is the norm (100%
# of debates in the pilot).
_PROMPT_V1 = """As the Research Manager and debate facilitator, your role is to critically evaluate this round of debate and deliver a clear, actionable investment plan for the trader.

{instrument_context}

---

**Rating Scale** (use exactly one):
- **Buy**: Strong conviction in the bull thesis; recommend taking or growing the position
- **Overweight**: Constructive view; recommend gradually increasing exposure
- **Hold**: Balanced view; recommend maintaining the current position
- **Underweight**: Cautious view; recommend trimming exposure
- **Sell**: Strong conviction in the bear thesis; recommend exiting or avoiding the position

Commit to a clear stance whenever the debate's strongest arguments warrant one; reserve Hold for situations where the evidence on both sides is genuinely balanced.

---

**Debate History:**
{history}"""


# v2 (MR-3): rewrites the rating-scale ladder so the criteria don't push
# toward the middle. The key change: replaces the "Strong conviction" /
# "Constructive" / "Balanced" / "Cautious" gradient (which interpreted
# any two-sided debate as Hold-leaning) with criteria phrased in terms of
# *which side outweighs* and what fraction of the other side is likely
# to play out within the holding window. Reserves Hold for the much
# narrower case of quantitatively near-equal arguments.
_PROMPT_V2 = """As the Research Manager and debate facilitator, your role is to critically evaluate this round of debate and deliver a clear, actionable investment plan for the trader.

{instrument_context}

---

**Important framing**: Two-sided evidence is the NORM in stock debates, not the exception. The bear will have legitimate concerns even when the bull is correct, and vice versa. The presence of a substantive bear argument does not by itself warrant a moderate rating. Your job is to weigh which side's strongest arguments more directly bear on the next 5 trading days.

**Rating Scale** (use exactly one):
- **Buy**: Bull's strongest arguments outweigh bear's. No specific bear arguments are likely to play out within the holding window. The bear may have valid long-term concerns that simply don't matter on this timeframe.
- **Overweight**: Bull's strongest arguments outweigh bear's, but some bear concerns may play out and partially offset the upside.
- **Hold**: Bull and bear arguments are *quantitatively near-equal* in conviction — similar evidence quality, similar specificity, similar timeframe relevance. Reserve this for genuinely close calls; do NOT use it as a default when both sides have valid points.
- **Underweight**: Bear's strongest arguments outweigh bull's, but some bull theses may play out and partially offset the downside.
- **Sell**: Bear's strongest arguments outweigh bull's. No specific bull arguments are likely to play out within the holding window. The bull may have valid long-term theses that simply don't matter on this timeframe.

Commit to Buy or Sell when one side's arguments more directly bear on the holding window, even if the other side has legitimate points on a different timeframe.

---

**Debate History:**
{history}"""


def create_research_manager(llm):
    # Bind both schemas at construction; pick at runtime based on the
    # variant config flag. Cheap — just a couple of LangChain wrapper
    # objects. Avoids reconstructing the structured-output binding per call.
    structured_v1 = bind_structured(llm, ResearchPlan, "Research Manager (v1)")
    structured_v2 = bind_structured(llm, ResearchPlanV2, "Research Manager (v2)")

    def research_manager_node(state) -> dict:
        # Lazy import to avoid circular reference at module load.
        from tradingagents.dataflows.config import get_config

        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        investment_debate_state = state["investment_debate_state"]

        # MR-3: select prompt + schema variant. Default "default" = v1 =
        # current behavior. Drives experiments/2026-05-02-004-mr3-synthesis-v2/.
        # The schema's field descriptions also flip; otherwise the schema's
        # "reserve Hold for balanced" instruction would partially cancel
        # the v2 prompt's "two-sided is the norm" framing.
        variant = get_config().get("research_manager_prompt_variant", "default")
        if variant in ("default", "v1"):
            template = _PROMPT_V1
            structured_llm = structured_v1
            renderer = render_research_plan
        elif variant == "v2":
            template = _PROMPT_V2
            structured_llm = structured_v2
            renderer = render_research_plan_v2
        else:
            raise ValueError(
                f"Unknown research_manager_prompt_variant {variant!r}; valid: 'default'/'v1', 'v2'."
            )

        prompt = template.format(
            instrument_context=instrument_context,
            history=history,
        )

        investment_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            renderer,
            "Research Manager",
        )

        new_investment_debate_state = {
            "judge_decision": investment_plan,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": investment_plan,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": investment_plan,
        }

    return research_manager_node
