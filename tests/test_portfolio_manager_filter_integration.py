"""End-to-end tests for the A3 momentum filter wired into PortfolioManager.

Unit tests for `maybe_suppress_bear_rating` already cover the filter logic
in isolation (tests/test_momentum_filter.py). This file tests the wiring
through the actual create_portfolio_manager → portfolio_manager_node path:

- Config flag actually controls whether the filter runs
- Filter sees the LLM's rendered markdown and operates on it correctly
- State fields (company_of_interest, trade_date) flow into the filter
- Absent-key fallback preserved (defensive regression guard)
- DEFAULT_CONFIG flips A3 ON post-2026-05-06 (regression guard)
- Bull ratings are never touched regardless of momentum
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.agents.managers.portfolio_manager import create_portfolio_manager
from tradingagents.agents.schemas import PortfolioDecision, PortfolioRating


@pytest.fixture(autouse=True)
def _disable_spec_007_in_legacy_tests():
    """Disable spec 007 forward-catalyst filter for all tests in this file
    by short-circuiting the LLM call to a fast no-op skip. Tests in
    test_forward_catalyst_filter.py exercise spec 007 directly via the
    `llm` injection point and bypass this patch.

    Without this fixture, every existing test triggers a real Opus call
    via the factory (spec 007 default-on at active mode + Opus model),
    which hits the API + adds 5-10s latency per test + can produce
    non-deterministic rating overrides that break tests asserting
    specific pre-spec-007 behavior.
    """
    # Patch the factory to raise; the spec 007 filter degrades to
    # skipped="llm_failed" + rating unchanged per FR-010 resilience pattern.
    with patch(
        "tradingagents.llm_clients.factory.create_llm_client",
        side_effect=RuntimeError("disabled by test fixture"),
    ):
        yield


def _state(ticker: str = "NVDA", trade_date: str = "2026-02-06") -> dict:
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


@pytest.fixture
def llm_returning_buy():
    """Mock LLM whose with_structured_output(...) returns a Buy."""
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision(PortfolioRating.BUY)
    llm.with_structured_output.return_value = structured
    return llm


@pytest.mark.unit
def test_filter_disabled_when_threshold_absent(llm_returning_underweight):
    """When `uw_momentum_filter_threshold` is missing from config (e.g. a
    caller passes a hand-built dict that doesn't include the key), the filter
    never fires — Underweight stays Underweight even on a deeply-down ticker.
    This is the defensive-fallback contract; the framework default in
    `DEFAULT_CONFIG` flipped to -5.0 on 2026-05-06 (see default_config.py)."""
    node = create_portfolio_manager(llm_returning_underweight)
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={"output_language": "English"},  # threshold missing
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-25.0,  # very down — would suppress if filter were on
        ),
    ):
        result = node(_state())
    assert "Underweight" in result["final_trade_decision"]
    assert "Hold" not in result["final_trade_decision"].split("Rating")[1].split("\n")[0]


@pytest.mark.unit
def test_default_config_activates_a3_filter():
    """Regression guard for the 2026-05-06 default flip — DEFAULT_CONFIG must
    keep A3 active at -5.0 so the framework's out-of-the-box behavior reflects
    the corpus-wide retrospective findings (see claudedocs/uw-suppression-filter.md
    and CLAUDE.md baseline section). Override in PARAMS.json to ablate."""
    from tradingagents.default_config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["uw_momentum_filter_threshold"] == -5.0
    assert DEFAULT_CONFIG["uw_momentum_filter_lookback_days"] == 30


@pytest.mark.unit
def test_default_config_activates_contrarian_gate():
    """Regression guard for the 2026-05-06 default flip — DEFAULT_CONFIG must
    keep the spec 003 contrarian gate in 'active' mode at the production
    N>=20 history floor (FR-004) and 80th-percentile threshold."""
    from tradingagents.default_config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["contrarian_gate_mode"] == "active"
    assert DEFAULT_CONFIG["contrarian_gate_threshold"] == 80


@pytest.mark.unit
def test_filter_enabled_suppresses_underweight_on_drawdown(llm_returning_underweight):
    """With threshold=-5 AND ticker -10% in last 30d, UW becomes Hold."""
    node = create_portfolio_manager(llm_returning_underweight)
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": -5.0,
                "uw_momentum_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-10.0,
        ),
    ):
        result = node(_state())
    md = result["final_trade_decision"]
    assert "**Rating**: Hold" in md
    # Original rating preserved in the suppression note
    assert "Underweight" in md
    assert "[A3 momentum filter]" in md
    assert "-10.00%" in md


@pytest.mark.unit
def test_filter_enabled_does_not_suppress_when_momentum_above_threshold(
    llm_returning_underweight,
):
    """Threshold=-5 but ticker only -2% in last 30d → keep the UW commit."""
    node = create_portfolio_manager(llm_returning_underweight)
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": -5.0,
            },
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-2.0,  # not in mean-reversion zone
        ),
    ):
        result = node(_state())
    md = result["final_trade_decision"]
    assert "**Rating**: Underweight" in md
    assert "[A3 momentum filter]" not in md


@pytest.mark.unit
def test_filter_does_not_touch_buy_ratings(llm_returning_buy):
    """The filter only suppresses UW/Sell. Buy stays Buy regardless of momentum."""
    node = create_portfolio_manager(llm_returning_buy)
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": -5.0,
            },
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-30.0,  # extreme drawdown
        ),
    ):
        result = node(_state())
    md = result["final_trade_decision"]
    assert "**Rating**: Buy" in md
    assert "[A3 momentum filter]" not in md


@pytest.mark.unit
def test_filter_uses_state_ticker_and_date(llm_returning_underweight):
    """The filter must pull ticker + trade_date from state, not from any
    hardcoded values."""
    node = create_portfolio_manager(llm_returning_underweight)

    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": -5.0,
            },
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-10.0,
        ) as mock_mom,
    ):
        node(_state(ticker="MSFT", trade_date="2026-03-13"))

    mock_mom.assert_called_once()
    args, kwargs = mock_mom.call_args
    # Args: (ticker, trade_date, lookback_days)
    assert args[0] == "MSFT"
    assert args[1] == "2026-03-13"


@pytest.mark.unit
def test_filter_lookback_days_config_override(llm_returning_underweight):
    """Custom uw_momentum_filter_lookback_days flows through to the call."""
    node = create_portfolio_manager(llm_returning_underweight)
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": -5.0,
                "uw_momentum_filter_lookback_days": 60,
            },
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-10.0,
        ) as mock_mom,
    ):
        node(_state())
    args, kwargs = mock_mom.call_args
    assert args[2] == 60  # 3rd positional is lookback_days


@pytest.mark.unit
def test_node_returns_consistent_judge_decision_after_suppression(
    llm_returning_underweight,
):
    """After suppression, the risk_debate_state.judge_decision must match
    the (now-Hold) final_trade_decision so downstream consumers see the
    suppressed version."""
    node = create_portfolio_manager(llm_returning_underweight)
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": -5.0,
            },
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-12.0,
        ),
    ):
        result = node(_state())
    assert result["risk_debate_state"]["judge_decision"] == result["final_trade_decision"]
    assert "**Rating**: Hold" in result["risk_debate_state"]["judge_decision"]


# ---- Spec 004 sector-momentum filter wiring tests --------------------------
# Mirror the A3 wiring-test pattern; mocks sector_momentum_filter helpers so
# the tests don't hit yfinance.


import pandas as pd  # noqa: E402


def _frame(closes: list[float], start: str = "2026-03-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=len(closes), freq="B")
    return pd.DataFrame({"Close": closes}, index=idx)


def _make_sector_lookup(sector: str):
    def lookup(_t: str) -> str:
        return sector

    return lookup


@pytest.mark.unit
def test_sector_filter_disabled_by_default_threshold_none(llm_returning_buy):
    """SC-006: when sector_momentum_filter_threshold_pct is None (default),
    filter does not modify the rating."""
    node = create_portfolio_manager(llm_returning_buy)
    with patch(
        "tradingagents.dataflows.config.get_config",
        return_value={
            "output_language": "English",
            "sector_momentum_filter_threshold_pct": None,
            "sector_momentum_filter_mode": "off",
        },
    ):
        result = node(_state())
    assert "**Rating**: Buy" in result["final_trade_decision"]
    # Annotation should reflect off-mode (or be absent — both valid per contract)
    if "sector_momentum" in result:
        assert result["sector_momentum"]["mode"] == "off"
        assert result["sector_momentum"]["fired"] is False


@pytest.mark.unit
def test_sector_filter_active_downgrades_overweight_when_etf_below_threshold(
    llm_returning_buy,
):
    """ETF down -8%, threshold -5%, active mode → Buy → Hold."""
    closes = [100.0] * 5 + [92.0] * 30  # -8% over the lookback window
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "sector_momentum_filter_threshold_pct": -5.0,
                "sector_momentum_filter_mode": "active",
                "sector_momentum_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.sector_momentum_filter._etf_history",
            return_value=_frame(closes),
        ),
        patch(
            "tradingagents.agents.utils.sector_momentum_filter.get_sector",
            new=_make_sector_lookup("Financial Services"),
            create=True,
        ),
    ):
        node = create_portfolio_manager(llm_returning_buy)
        result = node(_state(ticker="WFC"))
    assert "**Rating**: Hold" in result["final_trade_decision"]
    assert "[Sector-momentum filter]" in result["final_trade_decision"]
    assert result["sector_momentum"]["fired"] is True
    assert result["sector_momentum"]["pre_rating"] == "Buy"
    assert result["sector_momentum"]["post_rating"] == "Hold"


@pytest.mark.unit
def test_sector_filter_active_keeps_overweight_when_etf_above_threshold(
    llm_returning_buy,
):
    """ETF down only -2%, threshold -5%, active mode → no override."""
    closes = [100.0] * 5 + [98.0] * 30  # -2%
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "sector_momentum_filter_threshold_pct": -5.0,
                "sector_momentum_filter_mode": "active",
                "sector_momentum_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.sector_momentum_filter._etf_history",
            return_value=_frame(closes),
        ),
        patch(
            "tradingagents.agents.utils.sector_momentum_filter.get_sector",
            new=_make_sector_lookup("Financial Services"),
            create=True,
        ),
    ):
        node = create_portfolio_manager(llm_returning_buy)
        result = node(_state(ticker="WFC"))
    assert "**Rating**: Buy" in result["final_trade_decision"]
    assert result["sector_momentum"]["fired"] is False
    assert result["sector_momentum"]["would_fire"] is False


@pytest.mark.unit
def test_sector_filter_does_not_act_on_non_bullish_ratings(
    llm_returning_underweight,
):
    """ETF down -8%, but PM rating is Underweight (after A3 may have downgraded
    to Hold; either way, not Buy/OW) → filter skips."""
    closes = [100.0] * 5 + [92.0] * 30
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                # A3 disabled to keep UW rating intact for this test
                "uw_momentum_filter_threshold": None,
                "sector_momentum_filter_threshold_pct": -5.0,
                "sector_momentum_filter_mode": "active",
                "sector_momentum_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.sector_momentum_filter._etf_history",
            return_value=_frame(closes),
        ),
        patch(
            "tradingagents.agents.utils.sector_momentum_filter.get_sector",
            new=_make_sector_lookup("Financial Services"),
            create=True,
        ),
    ):
        node = create_portfolio_manager(llm_returning_underweight)
        result = node(_state(ticker="WFC"))
    assert "**Rating**: Underweight" in result["final_trade_decision"]
    assert "[Sector-momentum filter]" not in result["final_trade_decision"]
    assert result["sector_momentum"]["skipped"] == "rating_not_bullish"


@pytest.mark.unit
def test_default_config_has_sector_momentum_filter_off():
    """SC-006 regression-guard: DEFAULT_CONFIG ships with the filter off."""
    from tradingagents.default_config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["sector_momentum_filter_mode"] == "off"
    assert DEFAULT_CONFIG["sector_momentum_filter_threshold_pct"] is None
    assert DEFAULT_CONFIG["sector_momentum_filter_lookback_days"] == 30


# ---- Spec 006 bear-sector-symmetry filter wiring tests ---------------------
# Mirror the spec 004 wiring-test pattern; mocks bear_sector_symmetry_filter
# helpers so the tests don't hit yfinance.


# Standard frame inputs for spec 006 scenarios. Reuses _frame() defined above.
# Ticker frame: 100 → 118 → +18% return over the prior 31-row window
_BSS_TICKER_UP_18 = _frame([100.0] * 5 + [118.0] * 30)
# ETF frame: 100 → 106 → +6% return (delta vs ticker = +12%; above default +5% threshold)
_BSS_ETF_UP_6 = _frame([100.0] * 5 + [106.0] * 30)
# ETF frame: 100 → 114 → +14% return (delta vs ticker = +4%; below threshold)
_BSS_ETF_UP_14 = _frame([100.0] * 5 + [114.0] * 30)


@pytest.mark.unit
def test_bear_sector_symmetry_filter_disabled_by_default_threshold_none(
    llm_returning_underweight,
):
    """SC-006: when bear_sector_symmetry_filter_threshold_pct is None (default),
    filter does not modify the rating."""
    node = create_portfolio_manager(llm_returning_underweight)
    with patch(
        "tradingagents.dataflows.config.get_config",
        return_value={
            "output_language": "English",
            "uw_momentum_filter_threshold": None,  # disable A3 to isolate spec 006
            "bear_sector_symmetry_filter_threshold_pct": None,
            "bear_sector_symmetry_filter_mode": "off",
        },
    ):
        result = node(_state())
    assert "**Rating**: Underweight" in result["final_trade_decision"]
    if "bear_sector_symmetry" in result:
        assert result["bear_sector_symmetry"]["mode"] == "off"
        assert result["bear_sector_symmetry"]["fired"] is False


@pytest.mark.unit
def test_bear_sector_symmetry_filter_active_downgrades_underweight_when_relative_strength_above_threshold(
    llm_returning_underweight,
):
    """Ticker +18%, ETF +6%, delta +12%, threshold +5%, active mode → UW → Hold."""
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,  # disable A3 to isolate spec 006
                "bear_sector_symmetry_filter_threshold_pct": 5.0,
                "bear_sector_symmetry_filter_mode": "active",
                "bear_sector_symmetry_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._ticker_history",
            return_value=_BSS_TICKER_UP_18,
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._etf_history",
            return_value=_BSS_ETF_UP_6,
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter.get_sector",
            new=_make_sector_lookup("Technology"),
            create=True,
        ),
    ):
        node = create_portfolio_manager(llm_returning_underweight)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Hold" in result["final_trade_decision"]
    assert "[Bear-sector-symmetry filter]" in result["final_trade_decision"]
    assert result["bear_sector_symmetry"]["fired"] is True
    assert result["bear_sector_symmetry"]["pre_rating"] == "Underweight"
    assert result["bear_sector_symmetry"]["post_rating"] == "Hold"
    assert result["bear_sector_symmetry"]["relative_strength_pct"] == pytest.approx(12.0, abs=0.5)


@pytest.mark.unit
def test_bear_sector_symmetry_filter_active_keeps_underweight_when_relative_strength_below_threshold(
    llm_returning_underweight,
):
    """Ticker +18%, ETF +14%, delta +4%, threshold +5%, active mode → no override."""
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "bear_sector_symmetry_filter_threshold_pct": 5.0,
                "bear_sector_symmetry_filter_mode": "active",
                "bear_sector_symmetry_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._ticker_history",
            return_value=_BSS_TICKER_UP_18,
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._etf_history",
            return_value=_BSS_ETF_UP_14,
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter.get_sector",
            new=_make_sector_lookup("Technology"),
            create=True,
        ),
    ):
        node = create_portfolio_manager(llm_returning_underweight)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Underweight" in result["final_trade_decision"]
    assert result["bear_sector_symmetry"]["fired"] is False
    assert result["bear_sector_symmetry"]["would_fire"] is False


@pytest.mark.unit
def test_bear_sector_symmetry_filter_does_not_act_on_non_bearish_ratings(
    llm_returning_buy,
):
    """Ticker +18%, ETF +6%, delta +12% (would fire), but PM rating is Buy → filter skips."""
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "bear_sector_symmetry_filter_threshold_pct": 5.0,
                "bear_sector_symmetry_filter_mode": "active",
                "bear_sector_symmetry_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._ticker_history",
            return_value=_BSS_TICKER_UP_18,
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._etf_history",
            return_value=_BSS_ETF_UP_6,
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter.get_sector",
            new=_make_sector_lookup("Technology"),
            create=True,
        ),
    ):
        node = create_portfolio_manager(llm_returning_buy)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Buy" in result["final_trade_decision"]
    assert "[Bear-sector-symmetry filter]" not in result["final_trade_decision"]
    assert result["bear_sector_symmetry"]["skipped"] == "rating_not_bearish"


@pytest.mark.unit
def test_bear_sector_symmetry_filter_runs_after_a3_in_pm_hook_chain(
    llm_returning_underweight,
):
    """When A3 has already downgraded UW to Hold (ticker -10% absolute), the
    spec 006 filter sees Hold and skips with 'rating_not_bearish'.
    Covers FR-012 ordering + SC-009 disjoint-conditions guard."""
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": -5.0,  # A3 active
                "bear_sector_symmetry_filter_threshold_pct": 5.0,
                "bear_sector_symmetry_filter_mode": "active",
                "bear_sector_symmetry_filter_lookback_days": 30,
            },
        ),
        patch(
            "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
            return_value=-10.0,  # ticker DOWN absolute → A3 fires
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._ticker_history",
            return_value=_BSS_TICKER_UP_18,  # would NOT fire if reached
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter._etf_history",
            return_value=_BSS_ETF_UP_6,
        ),
        patch(
            "tradingagents.agents.utils.bear_sector_symmetry_filter.get_sector",
            new=_make_sector_lookup("Technology"),
            create=True,
        ),
    ):
        node = create_portfolio_manager(llm_returning_underweight)
        result = node(_state(ticker="NVDA"))
    # A3 fired first → rating became Hold → spec 006 saw Hold → skipped
    assert "**Rating**: Hold" in result["final_trade_decision"]
    assert "[A3 momentum filter]" in result["final_trade_decision"]
    assert "[Bear-sector-symmetry filter]" not in result["final_trade_decision"]
    assert result["bear_sector_symmetry"]["skipped"] == "rating_not_bearish"
    assert result["bear_sector_symmetry"]["fired"] is False


@pytest.mark.unit
def test_default_config_has_bear_sector_symmetry_filter_off():
    """SC-006 regression-guard: DEFAULT_CONFIG ships with the filter off."""
    from tradingagents.default_config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["bear_sector_symmetry_filter_mode"] == "off"
    assert DEFAULT_CONFIG["bear_sector_symmetry_filter_threshold_pct"] is None
    assert DEFAULT_CONFIG["bear_sector_symmetry_filter_lookback_days"] == 30


# ---- Spec 007 forward-catalyst filter wiring tests --------------------------
# Mirror the spec 004 / spec 006 wiring-test pattern; mocks the LLM client
# at the factory level so tests don't hit real Opus.


def _make_fc_llm(bull: float, bear: float, rationale: str = "test rationale"):
    """Build a mocked LLM that returns a CasePricedInScore."""
    from tradingagents.agents.utils.forward_catalyst_filter import CasePricedInScore

    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = CasePricedInScore(
        bull_case_priced_in=bull, bear_case_priced_in=bear, rationale=rationale
    )
    llm.with_structured_output.return_value = structured
    return llm


@pytest.fixture
def llm_returning_overweight():
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = _decision(PortfolioRating.OVERWEIGHT)
    llm.with_structured_output.return_value = structured
    return llm


@pytest.mark.unit
def test_forward_catalyst_disabled_when_both_modes_off(llm_returning_overweight):
    """SC-006: when both modes off, filter does not modify the rating + no LLM call."""
    node = create_portfolio_manager(llm_returning_overweight)
    with patch(
        "tradingagents.dataflows.config.get_config",
        return_value={
            "output_language": "English",
            "uw_momentum_filter_threshold": None,
            "forward_catalyst_bull_mode": "off",
            "forward_catalyst_bear_mode": "off",
        },
    ):
        result = node(_state())
    assert "**Rating**: Overweight" in result["final_trade_decision"]
    if "forward_catalyst" in result:
        assert result["forward_catalyst"]["bull_mode"] == "off"
        assert result["forward_catalyst"]["bear_mode"] == "off"
        assert result["forward_catalyst"]["fired_bull"] is False
        assert result["forward_catalyst"]["fired_bear"] is False


@pytest.mark.unit
def test_forward_catalyst_active_downgrades_overweight_when_bull_priced_in_above_threshold(
    llm_returning_overweight,
):
    """Bull score above threshold + active mode + Overweight → downgrade to Hold."""
    fc_llm = _make_fc_llm(bull=0.78, bear=0.45)
    fc_client = MagicMock()
    fc_client.get_llm.return_value = fc_llm
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "forward_catalyst_bull_mode": "active",
                "forward_catalyst_bear_mode": "shadow",
                "forward_catalyst_bull_threshold": 0.60,
                "forward_catalyst_bear_threshold": 0.50,
                "forward_catalyst_model": "claude-opus-4-7",
                "forward_catalyst_max_rationale_chars": 2000,
            },
        ),
        patch(
            "tradingagents.llm_clients.factory.create_llm_client",
            return_value=fc_client,
        ),
    ):
        node = create_portfolio_manager(llm_returning_overweight)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Hold" in result["final_trade_decision"]
    assert "[Forward-catalyst filter]" in result["final_trade_decision"]
    assert result["forward_catalyst"]["fired_bull"] is True
    assert result["forward_catalyst"]["pre_rating"] == "Overweight"
    assert result["forward_catalyst"]["post_rating"] == "Hold"


@pytest.mark.unit
def test_forward_catalyst_active_downgrades_buy_above_threshold(llm_returning_buy):
    """Buy variant of bull-side fire."""
    fc_llm = _make_fc_llm(bull=0.78, bear=0.45)
    fc_client = MagicMock()
    fc_client.get_llm.return_value = fc_llm
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "forward_catalyst_bull_mode": "active",
                "forward_catalyst_bear_mode": "shadow",
                "forward_catalyst_bull_threshold": 0.60,
                "forward_catalyst_bear_threshold": 0.50,
                "forward_catalyst_model": "claude-opus-4-7",
                "forward_catalyst_max_rationale_chars": 2000,
            },
        ),
        patch(
            "tradingagents.llm_clients.factory.create_llm_client",
            return_value=fc_client,
        ),
    ):
        node = create_portfolio_manager(llm_returning_buy)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Hold" in result["final_trade_decision"]
    assert result["forward_catalyst"]["fired_bull"] is True
    assert result["forward_catalyst"]["pre_rating"] == "Buy"


@pytest.mark.unit
def test_forward_catalyst_active_keeps_overweight_when_bull_priced_in_below_threshold(
    llm_returning_overweight,
):
    """Bull score below threshold → no fire; Overweight remains."""
    fc_llm = _make_fc_llm(bull=0.55, bear=0.45)  # below 0.60 threshold
    fc_client = MagicMock()
    fc_client.get_llm.return_value = fc_llm
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "forward_catalyst_bull_mode": "active",
                "forward_catalyst_bear_mode": "shadow",
                "forward_catalyst_bull_threshold": 0.60,
                "forward_catalyst_bear_threshold": 0.50,
                "forward_catalyst_model": "claude-opus-4-7",
                "forward_catalyst_max_rationale_chars": 2000,
            },
        ),
        patch(
            "tradingagents.llm_clients.factory.create_llm_client",
            return_value=fc_client,
        ),
    ):
        node = create_portfolio_manager(llm_returning_overweight)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Overweight" in result["final_trade_decision"]
    assert result["forward_catalyst"]["fired_bull"] is False
    assert result["forward_catalyst"]["would_fire_bull"] is False


@pytest.mark.unit
def test_forward_catalyst_bear_active_downgrades_underweight(llm_returning_underweight):
    """Bear score above threshold + bear mode active + UW → downgrade to Hold."""
    fc_llm = _make_fc_llm(bull=0.45, bear=0.65)  # bear > 0.50 threshold
    fc_client = MagicMock()
    fc_client.get_llm.return_value = fc_llm
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "forward_catalyst_bull_mode": "active",
                "forward_catalyst_bear_mode": "active",
                "forward_catalyst_bull_threshold": 0.60,
                "forward_catalyst_bear_threshold": 0.50,
                "forward_catalyst_model": "claude-opus-4-7",
                "forward_catalyst_max_rationale_chars": 2000,
            },
        ),
        patch(
            "tradingagents.llm_clients.factory.create_llm_client",
            return_value=fc_client,
        ),
    ):
        node = create_portfolio_manager(llm_returning_underweight)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Hold" in result["final_trade_decision"]
    assert result["forward_catalyst"]["fired_bear"] is True
    assert result["forward_catalyst"]["pre_rating"] == "Underweight"


@pytest.mark.unit
def test_forward_catalyst_bear_shadow_default_no_override(llm_returning_underweight):
    """Bear score above threshold + bear mode shadow (DEFAULT) → would_fire_bear=True; rating unchanged."""
    fc_llm = _make_fc_llm(bull=0.45, bear=0.65)
    fc_client = MagicMock()
    fc_client.get_llm.return_value = fc_llm
    with (
        patch(
            "tradingagents.dataflows.config.get_config",
            return_value={
                "output_language": "English",
                "uw_momentum_filter_threshold": None,
                "forward_catalyst_bull_mode": "active",
                "forward_catalyst_bear_mode": "shadow",  # the DEFAULT
                "forward_catalyst_bull_threshold": 0.60,
                "forward_catalyst_bear_threshold": 0.50,
                "forward_catalyst_model": "claude-opus-4-7",
                "forward_catalyst_max_rationale_chars": 2000,
            },
        ),
        patch(
            "tradingagents.llm_clients.factory.create_llm_client",
            return_value=fc_client,
        ),
    ):
        node = create_portfolio_manager(llm_returning_underweight)
        result = node(_state(ticker="NVDA"))
    assert "**Rating**: Underweight" in result["final_trade_decision"]
    assert result["forward_catalyst"]["would_fire_bear"] is True
    assert result["forward_catalyst"]["fired_bear"] is False


@pytest.mark.unit
def test_default_config_has_forward_catalyst_bull_active_bear_shadow():
    """SC-009 regression-guard: DEFAULT_CONFIG ships with bull-active + bear-shadow."""
    from tradingagents.default_config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG["forward_catalyst_bull_mode"] == "active"
    assert DEFAULT_CONFIG["forward_catalyst_bear_mode"] == "shadow"
    assert DEFAULT_CONFIG["forward_catalyst_bull_threshold"] == 0.60
    assert DEFAULT_CONFIG["forward_catalyst_bear_threshold"] == 0.50
    assert DEFAULT_CONFIG["forward_catalyst_model"] == "claude-opus-4-7"
    assert DEFAULT_CONFIG["forward_catalyst_max_rationale_chars"] == 2000
