"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses LangChain's ``with_structured_output`` so the LLM produces a typed
``PortfolioDecision`` directly, in a single call.  The result is rendered
back to markdown for storage in ``final_trade_decision`` so memory log,
CLI display, and saved reports continue to consume the same shape they do
today.  When a provider does not expose structured output, the agent falls
back gracefully to free-text generation.
"""

from __future__ import annotations

from pathlib import Path

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
                trade_date=state.get("trade_date"),
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

        # Spec 004: sector-momentum filter. When active, downgrades Buy/OW
        # commits to Hold if the ticker's sector ETF is in mean-reversion
        # zone (down >threshold% in prior N trading days). Default off; set
        # `sector_momentum_filter_threshold_pct` (e.g. -5.0) + mode to enable.
        # Wired AFTER A3 + spec 003 contrarian gate per FR-012 ordering.
        # See specs/004-sector-momentum-filter/spec.md.
        sector_momentum_dict: dict | None = None
        try:
            from tradingagents.agents.utils.sector_momentum_filter import (
                maybe_suppress_bull_rating,
            )

            sm_threshold = get_config().get("sector_momentum_filter_threshold_pct")
            sm_mode = get_config().get("sector_momentum_filter_mode", "off")
            sm_lookback = int(get_config().get("sector_momentum_filter_lookback_days", 30))
            paper_state_dir = get_config().get("paper_state_dir")
            sm_sectors_cache = (
                Path(paper_state_dir) / "sectors.json"
                if paper_state_dir
                else Path.home() / ".tradingagents" / "paper" / "sectors.json"
            )
            modified_decision, sector_momentum_dict = maybe_suppress_bull_rating(
                final_trade_decision,
                state["company_of_interest"],
                state["trade_date"],
                threshold_pct=float(sm_threshold) if sm_threshold is not None else None,
                lookback_days=sm_lookback,
                mode=sm_mode,
                sectors_cache_path=sm_sectors_cache,
            )
            final_trade_decision = modified_decision
        except Exception as exc:
            # Never let filter failure break the PM pipeline.
            import logging

            logging.getLogger(__name__).warning(
                "sector_momentum_filter: unexpected failure in PM hook (%s); "
                "proceeding with unmodified decision",
                exc,
            )

        # Spec 006: bear-sector-symmetry filter. When active, downgrades
        # Underweight/Sell commits to Hold if the ticker has outperformed
        # its sector ETF by more than threshold% (default +5%) in the prior
        # N trading days (counter-trend bear suppression). Default off; set
        # `bear_sector_symmetry_filter_threshold_pct` (e.g. 5.0) + mode to enable.
        # Wired AFTER A3 (per FR-012 ordering); the two bear filters fire on
        # near-disjoint price-condition cohorts (A3 needs ticker DOWN absolute,
        # spec 006 needs ticker UP relative to sector).
        # See specs/005-bear-sector-symmetry/spec.md.
        bear_sector_symmetry_dict: dict | None = None
        try:
            from tradingagents.agents.utils.bear_sector_symmetry_filter import (
                maybe_suppress_bear_rating as bss_suppress_bear,
            )

            bss_threshold = get_config().get("bear_sector_symmetry_filter_threshold_pct")
            bss_mode = get_config().get("bear_sector_symmetry_filter_mode", "off")
            bss_lookback = int(get_config().get("bear_sector_symmetry_filter_lookback_days", 30))
            paper_state_dir = get_config().get("paper_state_dir")
            bss_sectors_cache = (
                Path(paper_state_dir) / "sectors.json"
                if paper_state_dir
                else Path.home() / ".tradingagents" / "paper" / "sectors.json"
            )
            modified_decision, bear_sector_symmetry_dict = bss_suppress_bear(
                final_trade_decision,
                state["company_of_interest"],
                state["trade_date"],
                threshold_pct=float(bss_threshold) if bss_threshold is not None else None,
                lookback_days=bss_lookback,
                mode=bss_mode,
                sectors_cache_path=bss_sectors_cache,
            )
            final_trade_decision = modified_decision
        except Exception as exc:
            # Never let filter failure break the PM pipeline.
            import logging

            logging.getLogger(__name__).warning(
                "bear_sector_symmetry_filter: unexpected failure in PM hook (%s); "
                "proceeding with unmodified decision",
                exc,
            )

        # Spec 007: forward-catalyst-aware contrarian gate. FIRST forward-
        # catalyst-aware filter — invokes an LLM (Opus default) to score how
        # widely the bull/bear case is already absorbed by the market.
        # Bull-side default-on @T=0.60 (Class 3 Opus retrospective DECISIVE
        # PASS: discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp on n=33
        # fires). Bear-side default-shadow per Constitution VIII shadow-mode-
        # first condition. Wired LAST in the chain per FR-012; consumes ALL
        # pre-filter outputs as input via the analyst reports + debate.
        # Adds ~$0.025/propagate Opus cost; set BOTH modes to "off" to
        # disable + zero cost (FR-013 escape hatch).
        # See specs/006-forward-catalyst-gate/spec.md.
        forward_catalyst_dict: dict | None = None
        try:
            from tradingagents.agents.utils.forward_catalyst_filter import (
                evaluate_forward_catalyst,
            )

            fc_bull_mode = get_config().get("forward_catalyst_bull_mode", "active")
            fc_bear_mode = get_config().get("forward_catalyst_bear_mode", "shadow")
            fc_bull_threshold = float(get_config().get("forward_catalyst_bull_threshold", 0.60))
            fc_bear_threshold = float(get_config().get("forward_catalyst_bear_threshold", 0.50))
            fc_model = get_config().get("forward_catalyst_model", "claude-opus-4-7")
            fc_max_chars = int(get_config().get("forward_catalyst_max_rationale_chars", 2000))
            # Spec 008 Hybrid C calendar boost (default-off per FR-007). Adds
            # ZERO LLM cost when enabled (post-processing of spec 007's score).
            hc_enabled = bool(get_config().get("hybrid_c_calendar_boost_enabled", False))
            hc_window = int(get_config().get("hybrid_c_calendar_boost_window_days", 14))
            hc_magnitude = float(get_config().get("hybrid_c_calendar_boost_magnitude", 0.5))
            # Path C analyst PT snapshot wiring (PR #73, default-off). Captures
            # historical signals forward-going at zero LLM cost.
            pt_snap_enabled = bool(get_config().get("analyst_pt_snapshot_enabled", False))
            modified_decision, forward_catalyst_dict = evaluate_forward_catalyst(
                final_trade_decision,
                state,
                bull_mode=fc_bull_mode,
                bear_mode=fc_bear_mode,
                bull_threshold=fc_bull_threshold,
                bear_threshold=fc_bear_threshold,
                model=fc_model,
                max_rationale_chars=fc_max_chars,
                hybrid_c_calendar_boost_enabled=hc_enabled,
                hybrid_c_calendar_boost_window_days=hc_window,
                hybrid_c_calendar_boost_magnitude=hc_magnitude,
                analyst_pt_snapshot_enabled=pt_snap_enabled,
            )
            final_trade_decision = modified_decision
        except Exception as exc:
            # Never let filter failure break the PM pipeline.
            import logging

            logging.getLogger(__name__).warning(
                "forward_catalyst_filter: unexpected failure in PM hook (%s); "
                "proceeding with unmodified decision",
                exc,
            )

        # Spec X-1 (specs/091-c4-institutional-rotation/): C-4 institutional
        # rotation filter. Runs LAST in FR-012 chain (smallest evidence
        # base n=12 → least gating priority). Annotation lives as sub-dict
        # of forward_catalyst per spec 003/004/006/007/008 precedent.
        # Zero LLM cost; ~50-200ms latency on yfinance cache miss.
        try:
            from tradingagents.agents.utils.institutional_rotation_filter import (
                evaluate_institutional_rotation,
            )

            ir_bear_mode = get_config().get("institutional_rotation_bear_mode", "shadow")
            ir_bull_mode = get_config().get("institutional_rotation_bull_mode", "off")
            ir_outflow_threshold = float(
                get_config().get("institutional_rotation_outflow_threshold", 0.05)
            )
            ir_modified_decision, ir_annotation = evaluate_institutional_rotation(
                final_trade_decision,
                state,
                bear_mode=ir_bear_mode,
                bull_mode=ir_bull_mode,
                outflow_threshold=ir_outflow_threshold,
            )
            final_trade_decision = ir_modified_decision
            if ir_annotation is not None:
                if forward_catalyst_dict is None:
                    forward_catalyst_dict = {}
                forward_catalyst_dict["institutional_rotation"] = ir_annotation
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "institutional_rotation_filter: unexpected failure in PM hook (%s); "
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
        if sector_momentum_dict is not None:
            result["sector_momentum"] = sector_momentum_dict
        if bear_sector_symmetry_dict is not None:
            result["bear_sector_symmetry"] = bear_sector_symmetry_dict
        if forward_catalyst_dict is not None:
            result["forward_catalyst"] = forward_catalyst_dict
        return result

    return portfolio_manager_node
