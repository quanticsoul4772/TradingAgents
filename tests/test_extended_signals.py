"""Unit tests for extended signal fetchers added 2026-05-03 per docs/SIGNALS.md.

Covers the 6 new yfinance helpers in y_finance.py + the 2 macro helpers
in macro.py + the 8 corresponding @tool dispatchers.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.utils.fundamental_data_tools import (
    get_corporate_actions as tool_corporate_actions,
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_earnings_calendar as tool_earnings_calendar,
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_institutional_holders as tool_institutional_holders,
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_recommendations as tool_recommendations,
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_short_interest as tool_short_interest,
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_options_summary as tool_options_summary,
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_sector_etf_strength as tool_sector_etf,
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_vix as tool_vix,
)
from tradingagents.dataflows.macro import (
    SECTOR_ETF,
    get_sector_etf_strength,
    get_vix,
)
from tradingagents.dataflows.y_finance import (
    get_corporate_actions,
    get_earnings_calendar,
    get_institutional_holders,
    get_options_summary,
    get_recommendations,
    get_short_interest,
)

# --- y_finance: get_recommendations ----------------------------------------


@pytest.mark.unit
def test_get_recommendations_renders_history_and_upgrades():
    recs = pd.DataFrame({"Firm": ["Goldman"], "Action": ["upgrade"]})
    upgrades = pd.DataFrame({"Firm": ["Morgan"], "ToGrade": ["Buy"]})
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.recommendations = recs
        mock.return_value.upgrades_downgrades = upgrades
        out = get_recommendations("NVDA")
    assert "Goldman" in out
    assert "Morgan" in out
    assert "Recommendations history" in out
    assert "upgrades / downgrades" in out


@pytest.mark.unit
def test_get_recommendations_handles_missing_data():
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.recommendations = pd.DataFrame()
        mock.return_value.upgrades_downgrades = pd.DataFrame()
        out = get_recommendations("BOGUS")
    assert "No analyst recommendations" in out


@pytest.mark.unit
def test_get_recommendations_swallows_exceptions():
    with patch("tradingagents.dataflows.y_finance.yf.Ticker", side_effect=RuntimeError("net")):
        out = get_recommendations("NVDA")
    assert "Error retrieving recommendations" in out


# --- y_finance: get_earnings_calendar --------------------------------------


@pytest.mark.unit
def test_get_earnings_calendar_renders_dates():
    ed = pd.DataFrame(
        {"EPS Estimate": [2.5, 2.3]},
        index=pd.to_datetime(["2026-04-25", "2026-01-25"]),
    )
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.earnings_dates = ed
        mock.return_value.calendar = {"Earnings Date": ["2026-04-25"]}
        out = get_earnings_calendar("NVDA")
    assert "Earnings dates" in out
    assert "2026-04-25" in out


@pytest.mark.unit
def test_get_earnings_calendar_no_data_message():
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.earnings_dates = pd.DataFrame()
        mock.return_value.calendar = None
        out = get_earnings_calendar("BOGUS")
    assert "No earnings calendar data" in out


# --- y_finance: get_options_summary ---------------------------------------


@pytest.mark.unit
def test_get_options_summary_computes_pc_ratio_and_iv_skew():
    calls = pd.DataFrame(
        {
            "strike": [100, 110, 120],
            "openInterest": [100, 200, 50],
            "impliedVolatility": [0.20, 0.22, 0.25],
        }
    )
    puts = pd.DataFrame(
        {
            "strike": [100, 110, 120],
            "openInterest": [200, 100, 50],
            "impliedVolatility": [0.30, 0.28, 0.27],
        }
    )

    chain = MagicMock()
    chain.calls = calls
    chain.puts = puts

    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.options = ["2026-02-28", "2026-03-28"]
        mock.return_value.option_chain.return_value = chain
        out = get_options_summary("NVDA")

    assert "Put/call open interest ratio" in out
    assert "IV skew" in out
    assert "Max-OI strike" in out
    # Total call OI = 350, total put OI = 350, ratio = 1.0
    assert "1.000" in out


@pytest.mark.unit
def test_get_options_summary_no_options_message():
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.options = []
        out = get_options_summary("BOGUS")
    assert "No options data" in out


# --- y_finance: get_short_interest ---------------------------------------


@pytest.mark.unit
def test_get_short_interest_renders_known_fields():
    info = {
        "shortPercentOfFloat": 0.05,
        "shortRatio": 2.3,
        "sharesShort": 50_000_000,
        "heldPercentInsiders": 0.04,
        "heldPercentInstitutions": 0.78,
    }
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.info = info
        out = get_short_interest("NVDA")
    assert "Short Percent of Float: 0.05" in out
    assert "Short Ratio (days to cover): 2.3" in out
    assert "Held Percent Institutions: 0.78" in out


@pytest.mark.unit
def test_get_short_interest_empty_info():
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.info = {}
        out = get_short_interest("BOGUS")
    assert "No short interest" in out


# --- y_finance: get_institutional_holders --------------------------------


@pytest.mark.unit
def test_get_institutional_holders_renders_both_sections():
    inst = pd.DataFrame({"Holder": ["Vanguard"], "Shares": [50_000_000]})
    mf = pd.DataFrame({"Holder": ["Vanguard 500"], "Shares": [10_000_000]})
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.institutional_holders = inst
        mock.return_value.mutualfund_holders = mf
        out = get_institutional_holders("NVDA")
    assert "Institutional holders" in out
    assert "Mutual fund holders" in out
    assert "Vanguard" in out


# --- y_finance: get_corporate_actions ------------------------------------


@pytest.mark.unit
def test_get_corporate_actions_renders_dividends_and_esg():
    actions = pd.DataFrame(
        {"Dividends": [0.50, 0.50], "Stock Splits": [0.0, 0.0]},
        index=pd.to_datetime(["2025-12-15", "2026-03-15"]),
    )
    esg = pd.DataFrame({"Score": [8.5]}, index=["totalEsg"])
    with (
        patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock,
        patch("tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.actions = actions
        mock.return_value.sustainability = esg
        out = get_corporate_actions("NVDA")
    assert "Dividends + splits" in out
    assert "ESG sustainability" in out
    assert "0.5" in out


# --- macro: get_vix ------------------------------------------------------


@pytest.mark.unit
def test_get_vix_returns_level_change_and_regime():
    """VIX rising from 15 to 28 → fear regime classification."""
    closes = [15.0] * 35 + [28.0]  # last value 28
    df = pd.DataFrame({"Close": closes})
    with (
        patch("tradingagents.dataflows.macro.yf.Ticker") as mock,
        patch("tradingagents.dataflows.macro.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.history.return_value = df
        out = get_vix("2026-02-06", lookback_days=30)
    assert "Current level: 28.00" in out
    assert "fear" in out.lower()
    assert "30-day change" in out


@pytest.mark.unit
def test_get_vix_complacency_regime():
    closes = [12.0] * 36
    df = pd.DataFrame({"Close": closes})
    with (
        patch("tradingagents.dataflows.macro.yf.Ticker") as mock,
        patch("tradingagents.dataflows.macro.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.history.return_value = df
        out = get_vix("2026-02-06")
    assert "complacency" in out.lower()


@pytest.mark.unit
def test_get_vix_handles_empty_data():
    with (
        patch("tradingagents.dataflows.macro.yf.Ticker") as mock,
        patch("tradingagents.dataflows.macro.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.history.return_value = pd.DataFrame()
        out = get_vix("2026-02-06")
    assert "No VIX data" in out


# --- macro: get_sector_etf_strength --------------------------------------


@pytest.mark.unit
def test_get_sector_etf_strength_outperforms_sector():
    """NVDA up 10%, XLK up 5% → relative strength +5pp."""
    nvda_close = [100.0] * 35 + [110.0]
    xlk_close = [200.0] * 35 + [210.0]
    nvda_df = pd.DataFrame({"Close": nvda_close})
    xlk_df = pd.DataFrame({"Close": xlk_close})

    def fake_ticker(t):
        m = MagicMock()
        if t.upper() == "NVDA":
            m.info = {"sector": "Technology"}
            m.history.return_value = nvda_df
        else:  # XLK
            m.history.return_value = xlk_df
        return m

    with (
        patch("tradingagents.dataflows.macro.yf.Ticker", side_effect=fake_ticker),
        patch("tradingagents.dataflows.macro.yf_retry", side_effect=lambda fn: fn()),
    ):
        out = get_sector_etf_strength("NVDA", "2026-02-06", lookback_days=30)
    assert "Technology" in out
    assert "XLK" in out
    assert "+10.00%" in out
    assert "+5.00%" in out
    # Outperforming
    assert "outperforming" in out.lower()


@pytest.mark.unit
def test_get_sector_etf_strength_unknown_sector():
    with (
        patch("tradingagents.dataflows.macro.yf.Ticker") as mock,
        patch("tradingagents.dataflows.macro.yf_retry", side_effect=lambda fn: fn()),
    ):
        mock.return_value.info = {"sector": "Made-up Sector"}
        out = get_sector_etf_strength("XYZ", "2026-02-06")
    assert "No SPDR sector ETF mapping" in out


@pytest.mark.unit
def test_sector_etf_mapping_covers_major_sectors():
    """Map should include all 11 SPDR Select Sector ETFs."""
    expected_etfs = {"XLK", "XLE", "XLF", "XLV", "XLI", "XLY", "XLP", "XLU", "XLRE", "XLB", "XLC"}
    actual = set(SECTOR_ETF.values())
    assert expected_etfs <= actual


@pytest.mark.unit
@pytest.mark.parametrize("etf_ticker", ["XLK", "XLE", "XLF", "XLV", "XLI"])
def test_get_sector_etf_strength_short_circuits_on_etf_input(etf_ticker):
    """Short-circuit when ticker IS one of the sector ETFs themselves.

    Reason: yfinance Ticker.info call 404s on ETFs (no fundamentals data),
    producing noisy log output. The comparison is also self-referential.
    Short-circuit avoids both problems without invoking yfinance at all.
    Verified by patching yf.Ticker to raise if instantiated — the guard
    must run before any yfinance call.
    """
    with patch("tradingagents.dataflows.macro.yf.Ticker") as mock_ticker:
        mock_ticker.side_effect = AssertionError("yf.Ticker should not be called for ETF inputs")
        out = get_sector_etf_strength(etf_ticker, "2026-02-06")
    assert etf_ticker in out
    assert "sector ETF" in out
    assert "self" in out.lower() or "not meaningful" in out.lower()


@pytest.mark.unit
def test_get_sector_etf_strength_etf_input_lowercase_normalized():
    """The ETF-input guard works regardless of input case."""
    with patch("tradingagents.dataflows.macro.yf.Ticker") as mock_ticker:
        mock_ticker.side_effect = AssertionError("yf.Ticker should not be called for ETF inputs")
        out = get_sector_etf_strength("xlk", "2026-02-06")
    assert "XLK" in out


# --- @tool dispatch: extended fundamentals --------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "tool,method",
    [
        (tool_recommendations, "get_recommendations"),
        (tool_earnings_calendar, "get_earnings_calendar"),
        (tool_short_interest, "get_short_interest"),
        (tool_institutional_holders, "get_institutional_holders"),
        (tool_corporate_actions, "get_corporate_actions"),
    ],
)
def test_extended_fundamentals_tools_route(tool, method):
    with patch(
        "tradingagents.agents.utils.fundamental_data_tools.route_to_vendor",
        return_value=f"{method} result",
    ) as mock_route:
        result = tool.invoke({"ticker": "NVDA"})
    assert result == f"{method} result"
    mock_route.assert_called_once_with(method, "NVDA")


@pytest.mark.unit
def test_options_summary_tool_routes():
    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        return_value="opts",
    ) as mock_route:
        out = tool_options_summary.invoke({"ticker": "NVDA"})
    assert out == "opts"
    mock_route.assert_called_once_with("get_options_summary", "NVDA")


@pytest.mark.unit
def test_vix_tool_routes_with_default_lookback():
    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        return_value="vix",
    ) as mock_route:
        out = tool_vix.invoke({"curr_date": "2026-02-06"})
    assert out == "vix"
    mock_route.assert_called_once_with("get_vix", "2026-02-06", 30)


@pytest.mark.unit
def test_sector_etf_tool_routes_with_args():
    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        return_value="strength",
    ) as mock_route:
        out = tool_sector_etf.invoke(
            {"ticker": "NVDA", "curr_date": "2026-02-06", "lookback_days": 60}
        )
    assert out == "strength"
    mock_route.assert_called_once_with("get_sector_etf_strength", "NVDA", "2026-02-06", 60)
