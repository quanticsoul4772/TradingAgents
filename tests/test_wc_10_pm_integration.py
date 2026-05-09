"""Integration tests for WC-10 PM-hook bypass branch.

Covers tasks T008 from specs/108-wc-10-continuous-scalar-rating/tasks.md.
2 integration tests covering SC-001 + SC-003 + SC-004.

Pattern follows tests/test_institutional_rotation_pm_integration.py
(PR #92 precedent) — uses the actual create_portfolio_manager →
portfolio_manager_node path with LLM mocks + config injection.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.managers.portfolio_manager import create_portfolio_manager
from tradingagents.agents.schemas import PortfolioDecision, PortfolioRating

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _disable_spec_007_in_tests():
    """Short-circuit spec 007's LLM call so tests focus on WC-10 behavior.
    Mirrors the disable-fixture pattern from
    test_institutional_rotation_pm_integration.py.
    """
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        side_effect=RuntimeError("disabled by test fixture"),
    ):
        yield


def _state(ticker: str = "NVDA", trade_date: str = "2026-04-30") -> dict:
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


def _decision_5tier(rating: PortfolioRating) -> PortfolioDecision:
    return PortfolioDecision(
        rating=rating,
        executive_summary="test summary",
        investment_thesis="test thesis grounded in analyst evidence",
    )


def _decision_scalar(rating: float) -> PortfolioDecision:
    return PortfolioDecision(
        rating=rating,
        executive_summary="test summary",
        investment_thesis="test thesis grounded in analyst evidence",
    )


@pytest.fixture
def llm_returning_5tier_buy():
    """Mock LLM whose with_structured_output(...) returns a 5-tier Buy."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision_5tier(PortfolioRating.BUY)
    llm.with_structured_output.return_value = structured
    return llm


@pytest.fixture
def llm_returning_scalar_0_45():
    """Mock LLM whose with_structured_output(...) returns a scalar rating 0.45."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision_scalar(0.45)
    llm.with_structured_output.return_value = structured
    return llm


# ---- T008.1 (SC-003): default-off integrity ------------------------------


def test_default_off_5tier_unchanged(llm_returning_5tier_buy):
    """T008 SC-003: wc_10_enabled=False → state log shape identical to
    pre-WC-10 baseline; rating is 5-tier string; no `wc_10` field appears.
    """
    node = create_portfolio_manager(llm_returning_5tier_buy)

    with patch(
        "tradingagents.dataflows.config.get_config",
        return_value={
            "output_language": "English",
            "uw_momentum_filter_threshold": None,
            "wc_10_enabled": False,
        },
    ):
        result = node(_state())

    decision = result["final_trade_decision"]
    # 5-tier rating preserved
    assert "Buy" in decision
    # No wc_10 annotation in result (FR-006)
    assert "wc_10" not in result


# ---- T008.2 (SC-001 + SC-004): bypass mode skips filter chain -----------


def test_bypass_mode_skips_filters(llm_returning_scalar_0_45):
    """T008 SC-001 + SC-004: wc_10_enabled=True + wc_10_filter_mode="bypass"
    → rating is float, wc_10 annotation present with 3 fields, NO filter
    from chain (A3 / spec 003 / 004 / 006 / 007 / X-1) executes.
    """
    node = create_portfolio_manager(llm_returning_scalar_0_45)

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,  # A3 disabled
                "wc_10_enabled": True,
                "wc_10_filter_mode": "bypass",
                "wc_10_bin_thresholds": (-0.6, -0.2, 0.2, 0.6),
                # Active modes for filters that run by default — should still
                # be skipped per FR-005
                "contrarian_gate_mode": "active",
                "forward_catalyst_bull_mode": "active",
                "forward_catalyst_bear_mode": "shadow",
                "institutional_rotation_bear_mode": "shadow",
            },
        ),
        # Mock the filter modules to assert they are NOT called
        patch("tradingagents.agents.utils.momentum_filter.maybe_suppress_bear_rating") as a3_mock,
    ):
        result = node(_state())

    # SC-001: rating is float (rendered as "+0.4500") in markdown
    decision = result["final_trade_decision"]
    assert "+0.4500" in decision or "0.45" in decision
    # SC-007: wc_10 annotation has 3 fields
    wc_10 = result.get("wc_10", {})
    assert "rating_scalar" in wc_10
    assert wc_10["rating_scalar"] == pytest.approx(0.45)
    assert wc_10["filter_mode"] == "bypass"
    assert wc_10["bin_thresholds_snapshot"] == (-0.6, -0.2, 0.2, 0.6)
    # SC-004: A3 momentum filter NOT called (bypass mode skips ALL filters)
    a3_mock.assert_not_called()


# ---- Spec 009 Branch C: bin-then-output internal-only mode --------------


def test_branch_c_internal_only_emits_5tier(llm_returning_scalar_0_45):
    """Spec 009 Branch C: wc_10_internal_only=True overwrites the rendered
    Rating header with the binned 5-tier value while preserving the scalar
    in the wc_10 annotation. Scalar 0.45 with default thresholds bins to
    "Overweight" (0.2 < 0.45 <= 0.6).
    """
    node = create_portfolio_manager(llm_returning_scalar_0_45)

    with patch(
        "tradingagents.dataflows.config.get_config",
        return_value={
            "output_language": "English",
            "uw_momentum_filter_threshold": None,
            "wc_10_enabled": True,
            "wc_10_filter_mode": "bypass",
            "wc_10_bin_thresholds": (-0.6, -0.2, 0.2, 0.6),
            "wc_10_internal_only": True,
        },
    ):
        result = node(_state())

    decision = result["final_trade_decision"]
    # External output: 5-tier (binned), NOT scalar
    assert "**Rating**: Overweight" in decision
    assert "+0.4500" not in decision
    # Internal scalar preserved in wc_10 annotation
    wc_10 = result.get("wc_10", {})
    assert wc_10["rating_scalar"] == pytest.approx(0.45)
    assert wc_10["internal_only"] is True
    assert wc_10["filter_mode"] == "bypass"


def test_branch_c_internal_only_default_off_preserves_scalar(llm_returning_scalar_0_45):
    """Spec 009 Branch C default: wc_10_internal_only defaults False; rendered
    output retains the scalar Rating header (v1+v2 research-mode behavior).
    """
    node = create_portfolio_manager(llm_returning_scalar_0_45)

    with patch(
        "tradingagents.dataflows.config.get_config",
        return_value={
            "output_language": "English",
            "uw_momentum_filter_threshold": None,
            "wc_10_enabled": True,
            "wc_10_filter_mode": "bypass",
            "wc_10_bin_thresholds": (-0.6, -0.2, 0.2, 0.6),
            # wc_10_internal_only NOT set → defaults False
        },
    ):
        result = node(_state())

    decision = result["final_trade_decision"]
    # Default-off: scalar preserved in rendered Rating header
    assert "+0.4500" in decision or "0.45" in decision
    wc_10 = result.get("wc_10", {})
    assert wc_10.get("internal_only") is False


def test_branch_c_internal_only_negative_scalar_bins_to_underweight():
    """Spec 009 Branch C: scalar -0.35 (between -0.6 and -0.2 default
    thresholds) bins to Underweight under default thresholds.
    """
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision_scalar(-0.35)
    llm.with_structured_output.return_value = structured
    node = create_portfolio_manager(llm)

    with patch(
        "tradingagents.dataflows.config.get_config",
        return_value={
            "output_language": "English",
            "uw_momentum_filter_threshold": None,
            "wc_10_enabled": True,
            "wc_10_filter_mode": "bypass",
            "wc_10_bin_thresholds": (-0.6, -0.2, 0.2, 0.6),
            "wc_10_internal_only": True,
        },
    ):
        result = node(_state())

    decision = result["final_trade_decision"]
    assert "**Rating**: Underweight" in decision
    wc_10 = result["wc_10"]
    assert wc_10["rating_scalar"] == pytest.approx(-0.35)
    assert wc_10["internal_only"] is True
