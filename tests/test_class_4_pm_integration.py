"""Integration tests for Spec 012 Class 4 macro-environment filter PM-hook integration.

Covers task T011 from specs/012-class-4-macro-filter/tasks.md.
≥3 PM integration tests covering off / shadow / active modes per
SC-003 + SC-004 + SC-005 + SC-006.

Pattern follows tests/test_institutional_rotation_pm_integration.py
(Spec X-1 PR #92 precedent).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.managers.portfolio_manager import create_portfolio_manager
from tradingagents.agents.schemas import PortfolioDecision, PortfolioRating

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _disable_other_llm_filters():
    """Short-circuit Spec 007 + Spec X-1 LLM/yfinance fetches so tests focus on Class 4."""
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        side_effect=RuntimeError("disabled by test fixture"),
    ):
        yield


def _state(ticker: str = "AAPL", trade_date: str = "2026-04-30") -> dict:
    """Minimal AgentState shape that portfolio_manager_node reads from."""
    return {
        "company_of_interest": ticker,
        "trade_date": trade_date,
        "investment_plan": "research synthesis prose",
        "trader_investment_plan": "trader proposal prose",
        "past_context": "",
        "risk_debate_state": {
            "history": "full risk debate history",
            "aggressive_history": "agg",
            "conservative_history": "cons",
            "neutral_history": "neut",
            "current_aggressive_response": "agg latest",
            "current_conservative_response": "cons latest",
            "current_neutral_response": "neut latest",
            "count": 3,
        },
    }


def _decision(rating: PortfolioRating) -> PortfolioDecision:
    return PortfolioDecision(
        rating=rating,
        executive_summary="test summary",
        investment_thesis="test thesis grounded in analyst evidence",
    )


@pytest.fixture
def llm_returning_underweight():
    """Mock LLM whose with_structured_output(...) returns an Underweight decision."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision(PortfolioRating.UNDERWEIGHT)
    llm.with_structured_output.return_value = structured
    return llm


@pytest.fixture
def llm_returning_hold():
    """Mock LLM whose with_structured_output(...) returns a Hold decision."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision(PortfolioRating.HOLD)
    llm.with_structured_output.return_value = structured
    return llm


# ---- T011 SC-003 + SC-004: shadow mode integrates without modifying ----


def test_shadow_mode_produces_annotation_no_modification(llm_returning_underweight):
    """T011 SC-005: shadow mode + would_fire → annotation present in
    state['class_4_macro'] with 7 fields; rating unchanged.
    """
    node = create_portfolio_manager(llm_returning_underweight)

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,  # A3 disabled
                "wc_10_enabled": False,
                "class_4_macro_bear_mode": "shadow",
                "class_4_macro_vix_threshold": 18.0,
                "institutional_rotation_bear_mode": "off",  # disable Spec X-1 to isolate Class 4
                "forward_catalyst_bull_mode": "off",
                "forward_catalyst_bear_mode": "off",
            },
        ),
        patch(
            "tradingagents.agents.utils.macro_environment_filter._vix_snapshot",
            return_value=15.0,  # below 18 → would_fire
        ),
    ):
        result = node(_state())

    decision = result["final_trade_decision"]
    # Rating is preserved (shadow does NOT modify)
    assert "**Rating**: Underweight" in decision
    # Annotation in state with all 7 fields
    c4 = result.get("class_4_macro", {})
    assert c4 is not None
    assert c4["bear_mode"] == "shadow"
    assert c4["would_fire_bear"] is True
    assert c4["fired_bear"] is False
    assert c4["pre_rating"] == "Underweight"
    assert c4["post_rating"] == "Underweight"
    assert c4["vix_snapshot"] == pytest.approx(15.0)


# ---- T011 SC-006: active mode suppresses to Hold -----------------------


def test_active_mode_suppresses_underweight_to_hold(llm_returning_underweight):
    """T011 SC-006: active mode + would_fire + Underweight → post_rating=Hold."""
    node = create_portfolio_manager(llm_returning_underweight)

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "wc_10_enabled": False,
                "class_4_macro_bear_mode": "active",
                "class_4_macro_vix_threshold": 18.0,
                "institutional_rotation_bear_mode": "off",
                "forward_catalyst_bull_mode": "off",
                "forward_catalyst_bear_mode": "off",
            },
        ),
        patch(
            "tradingagents.agents.utils.macro_environment_filter._vix_snapshot",
            return_value=15.0,
        ),
    ):
        result = node(_state())

    decision = result["final_trade_decision"]
    # Rating SUPPRESSED to Hold
    assert "**Rating**: Hold" in decision
    assert "[Class 4 Macro-Environment filter]" in decision
    # Annotation reflects the fire
    c4 = result["class_4_macro"]
    assert c4["fired_bear"] is True
    assert c4["pre_rating"] == "Underweight"
    assert c4["post_rating"] == "Hold"


# ---- T011: off mode skips integration entirely -------------------------


def test_off_mode_no_annotation(llm_returning_hold):
    """T011 SC-002: bear_mode='off' → no class_4_macro key in result; no fetch."""
    node = create_portfolio_manager(llm_returning_hold)

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "wc_10_enabled": False,
                "class_4_macro_bear_mode": "off",
                "class_4_macro_vix_threshold": 18.0,
                "institutional_rotation_bear_mode": "off",
                "forward_catalyst_bull_mode": "off",
                "forward_catalyst_bear_mode": "off",
            },
        ),
        patch("tradingagents.agents.utils.macro_environment_filter._vix_snapshot") as mock_fetch,
    ):
        result = node(_state())

    # No class_4_macro key when off mode
    assert "class_4_macro" not in result
    # No yfinance fetch
    mock_fetch.assert_not_called()
