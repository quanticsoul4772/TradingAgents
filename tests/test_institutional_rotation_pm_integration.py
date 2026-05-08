"""End-to-end integration tests for Spec X-1 C-4 institutional rotation
filter wired into PortfolioManager.

Covers PR-B tasks T017, T023, T026 from
specs/091-c4-institutional-rotation/tasks.md.

Pattern follows tests/test_portfolio_manager_filter_integration.py — uses
the actual create_portfolio_manager → portfolio_manager_node path with
LLM mocks + config injection + yfinance mocks.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.managers.portfolio_manager import create_portfolio_manager
from tradingagents.agents.schemas import PortfolioDecision, PortfolioRating
from tradingagents.agents.utils import institutional_rotation_filter as irf

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _disable_spec_007_in_tests():
    """Short-circuit spec 007's LLM call so tests focus on Spec X-1 behavior.
    Mirrors the disable-fixture pattern from test_portfolio_manager_filter_integration.py.
    """
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        side_effect=RuntimeError("disabled by test fixture"),
    ):
        yield


@pytest.fixture(autouse=True)
def _clear_lru_cache():
    """Clear the LRU cache before each test for deterministic behavior."""
    irf._fetch_institutional_rotation.cache_clear()
    yield
    irf._fetch_institutional_rotation.cache_clear()


def _state(ticker: str = "NVDA", trade_date: str = "2026-04-24") -> dict:
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


def _decision(rating: PortfolioRating, summary: str = "test summary") -> PortfolioDecision:
    return PortfolioDecision(
        rating=rating,
        executive_summary=summary,
        investment_thesis="test thesis grounded in analyst evidence",
    )


@pytest.fixture
def llm_returning_underweight():
    """Mock LLM whose with_structured_output(...) returns an Underweight."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision(PortfolioRating.UNDERWEIGHT)
    llm.with_structured_output.return_value = structured
    return llm


def _make_outflow_dataframe() -> pd.DataFrame:
    """Build a 10-row DataFrame with strong net outflow (-0.10)."""
    return pd.DataFrame(
        {
            "Holder": [f"H{i}" for i in range(10)],
            "pctHeld": [0.05] * 10,
            "Shares": [1000000] * 10,
            "Value": [10000000] * 10,
            "Date Reported": ["2026-01-31"] * 10,
            "pctChange": [-0.01] * 10,  # net = -0.10
        }
    )


# ---- T017 (US2): shadow mode no rating mutation --------------------------


def test_pm_hook_shadow_mode_no_mutation(llm_returning_underweight):
    """T017 (SC-006): PM-hook with bear_mode=shadow + outflow conditions →
    would_fire_bear=True, fired_bear=False, post_rating == pre_rating,
    final_trade_decision NOT mutated.
    """
    node = create_portfolio_manager(llm_returning_underweight)
    mock_yf_ticker = MagicMock()
    mock_yf_ticker.institutional_holders = _make_outflow_dataframe()

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,  # disable A3 for clarity
                "institutional_rotation_bear_mode": "shadow",
                "institutional_rotation_bull_mode": "off",
                "institutional_rotation_outflow_threshold": 0.05,
            },
        ),
        patch.object(irf, "yf") as mock_yf,
    ):
        mock_yf.Ticker.return_value = mock_yf_ticker
        result = node(_state())

    decision = result["final_trade_decision"]
    # Shadow mode preserves rating; Underweight stays Underweight
    assert "Underweight" in decision
    assert "[C-4 Institutional Rotation filter]" not in decision
    # Annotation should still be present (sub-dict of forward_catalyst)
    fc = result.get("forward_catalyst", {})
    ir = fc.get("institutional_rotation", {})
    assert ir.get("bear_mode") == "shadow"
    assert ir.get("would_fire_bear") is True
    assert ir.get("fired_bear") is False
    assert ir.get("pre_rating") == "Underweight"
    assert ir.get("post_rating") == "Underweight"


# ---- T023 (US3): yfinance failure graceful degradation -------------------


def test_pm_hook_yfinance_failure_graceful(llm_returning_underweight):
    """T023 (SC-003): PM-hook with bear_mode=active + yfinance raises →
    no exception, fired_bear=False, post_rating == pre_rating, propagate
    completes.
    """
    node = create_portfolio_manager(llm_returning_underweight)

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "institutional_rotation_bear_mode": "active",
                "institutional_rotation_bull_mode": "off",
                "institutional_rotation_outflow_threshold": 0.05,
            },
        ),
        patch.object(irf, "yf") as mock_yf,
    ):
        mock_yf.Ticker.side_effect = ConnectionError("simulated yfinance outage")
        result = node(_state())

    decision = result["final_trade_decision"]
    # Graceful degradation: rating unchanged, no filter note appended
    assert "Underweight" in decision
    assert "[C-4 Institutional Rotation filter]" not in decision
    # Annotation should record the failure (net_rotation_pct=None)
    fc = result.get("forward_catalyst", {})
    ir = fc.get("institutional_rotation", {})
    assert ir.get("net_rotation_pct") is None
    assert ir.get("would_fire_bear") is False
    assert ir.get("fired_bear") is False


# ---- T026 (US4): mode=off baseline state log shape -----------------------


def test_pm_hook_both_modes_off_baseline_state_log(llm_returning_underweight):
    """T026 (SC-005, FR-011): PM-hook with both modes off → no
    institutional_rotation sub-dict in forward_catalyst (preserves
    pre-Spec-X-1 baseline state log shape).
    """
    node = create_portfolio_manager(llm_returning_underweight)

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "institutional_rotation_bear_mode": "off",
                "institutional_rotation_bull_mode": "off",
                "institutional_rotation_outflow_threshold": 0.05,
            },
        ),
        patch.object(irf, "yf") as mock_yf,
    ):
        result = node(_state())
        # yfinance.Ticker MUST NOT have been called (zero overhead opt-out)
        mock_yf.Ticker.assert_not_called()

    decision = result["final_trade_decision"]
    assert "Underweight" in decision
    assert "[C-4 Institutional Rotation filter]" not in decision
    # forward_catalyst sub-dict MUST NOT contain institutional_rotation key
    fc = result.get("forward_catalyst", {})
    assert "institutional_rotation" not in fc
