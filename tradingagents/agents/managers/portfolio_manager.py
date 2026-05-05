"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses LangChain's ``with_structured_output`` so the LLM produces a typed
``PortfolioDecision`` directly, in a single call.  The result is rendered
back to markdown for storage in ``final_trade_decision`` so memory log,
CLI display, and saved reports continue to consume the same shape they do
today.  When a provider does not expose structured output, the agent falls
back gracefully to free-text generation.
"""

from __future__ import annotations

from tradingagents.agents.schemas import PortfolioDecision, render_pm_decision
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)
from tradingagents.agents.utils.momentum_filter import maybe_suppress_bear_rating
from tradingagents.agents.utils.rating import parse_rating
from tradingagents.agents.utils.second_opinion import (
    annotate_decision,
    evaluate_pm_decision,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_portfolio_manager(llm):
    structured_llm = bind_structured(llm, PortfolioDecision, "Portfolio Manager")

    def portfolio_manager_node(state) -> dict:
        # Lazy import to avoid circular reference at module load.
        from tradingagents.dataflows.config import get_config

        instrument_context = build_instrument_context(state["company_of_interest"])

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        past_context = state.get("past_context", "")
        lessons_line = (
            f"- Lessons from prior decisions and outcomes:\n{past_context}\n"
            if past_context
            else ""
        )

        # WC-12 (synthesis-blind variant): when False, withhold the Research
        # Manager's investment_plan from the PM. Default True = current behavior.
        # Drives experiments/2026-05-02-002-wc12-pm-blind/.
        pm_sees_synthesis = get_config().get("pm_sees_synthesis", True)
        if pm_sees_synthesis:
            research_plan_line = f"- Research Manager's investment plan: **{research_plan}**\n"
        else:
            research_plan_line = (
                "- Research Manager's investment plan: "
                "*[withheld by experimental config; build your decision from the "
                "trader plan and risk debate alone]*\n"
            )

        prompt = f"""As the Portfolio Manager, synthesize the risk analysts' debate and deliver the final trading decision.

{instrument_context}

---

**Rating Scale** (use exactly one):
- **Buy**: Strong conviction to enter or add to position
- **Overweight**: Favorable outlook, gradually increase exposure
- **Hold**: Maintain current position, no action needed
- **Underweight**: Reduce exposure, take partial profits
- **Sell**: Exit position or avoid entry

**Context:**
{research_plan_line}- Trader's transaction proposal: **{trader_plan}**
{lessons_line}
**Risk Analysts Debate History:**
{history}

---

Be decisive and ground every conclusion in specific evidence from the analysts.{get_language_instruction()}"""

        final_trade_decision = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_pm_decision,
            "Portfolio Manager",
        )

        # A3 momentum filter: suppress UW/Sell commits when ticker is deeply
        # down (mean-reversion zone). Disabled by default — set
        # `uw_momentum_filter_threshold` (e.g. -5.0) in config to enable.
        threshold = get_config().get("uw_momentum_filter_threshold")
        if threshold is not None:
            lookback = get_config().get("uw_momentum_filter_lookback_days", 30)
            final_trade_decision, _ = maybe_suppress_bear_rating(
                final_trade_decision,
                state["company_of_interest"],
                state["trade_date"],
                threshold_pct=float(threshold),
                lookback_days=int(lookback),
            )

        # Phase C second-opinion: independent reviewer evaluates the framework's
        # commit. Asymmetric handling (agreement augments, disagreement flags for
        # review). Disabled by default — set `second_opinion_enabled = True` in
        # config to enable. NEVER modifies the PM rating; advisory only.
        if get_config().get("second_opinion_enabled", False):
            try:
                opinion = evaluate_pm_decision(
                    pm_rating=parse_rating(final_trade_decision),
                    market_report=state.get("market_report", ""),
                    news_report=state.get("news_report", ""),
                    fundamentals_report=state.get("fundamentals_report", ""),
                    investment_plan=research_plan,
                    risk_debate_history=history,
                    ticker=state["company_of_interest"],
                    trade_date=state["trade_date"],
                    llm=llm,
                )
                if opinion is not None:
                    final_trade_decision = annotate_decision(
                        final_trade_decision,
                        opinion,
                        pm_rating=parse_rating(final_trade_decision),
                        agree_threshold=float(
                            get_config().get("second_opinion_agree_threshold", 0.6)
                        ),
                        disagree_threshold=float(
                            get_config().get("second_opinion_disagree_threshold", 0.4)
                        ),
                    )
            except Exception as exc:
                # Never let second-opinion failure break the PM pipeline.
                # The decision proceeds unannotated.
                import logging

                logging.getLogger(__name__).warning(
                    "second_opinion: unexpected failure in PM hook (%s); "
                    "proceeding with unannotated decision",
                    exc,
                )

        # Spec 003: analyst-stage contrarian gate. When active, downgrades
        # Buy/Overweight commits to Hold (or UW per target) if the market
        # analyst's bull_keyword_count percentile crosses the threshold.
        # Default "off" => no annotation, no override. See
        # .specify/specs/003-analyst-contrarian-gate/spec.md.
        contrarian_gate_dict: dict | None = None
        try:
            from tradingagents.signals.contrarian_gate import ContrarianGate

            gate = ContrarianGate(get_config())
            pre_gate_rating = parse_rating(final_trade_decision)
            annotation = gate.compute_annotation(
                ticker=state["company_of_interest"],
                market_report_text=state.get("market_report", ""),
                pm_rating=pre_gate_rating,
            )
            modified_decision, gate_fired = gate.maybe_override_decision(
                final_trade_decision, annotation
            )
            final_trade_decision = modified_decision
            post_gate_rating = parse_rating(final_trade_decision)
            contrarian_gate_dict = annotation.to_dict() | {
                "gate_fired": gate_fired,
                "pm_rating_pre_gate": pre_gate_rating,
                "pm_rating_post_gate": post_gate_rating,
            }
        except Exception as exc:
            # Never let gate failure break the PM pipeline.
            import logging

            logging.getLogger(__name__).warning(
                "contrarian_gate: unexpected failure in PM hook (%s); "
                "proceeding with unmodified decision",
                exc,
            )

        new_risk_debate_state = {
            "judge_decision": final_trade_decision,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        result: dict = {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": final_trade_decision,
        }
        if contrarian_gate_dict is not None:
            result["contrarian_gate"] = contrarian_gate_dict
        return result

    return portfolio_manager_node
