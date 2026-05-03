"""Unit tests for the @tool-decorated data dispatch functions.

Each tool is a thin wrapper around route_to_vendor("<method>", *args).
The interesting behavior is:
- Argument forwarding (LLM tool-call args reach the vendor router intact)
- Default values applied correctly
- get_indicators splits comma-separated indicator strings (LLMs sometimes
  pack multiple indicators into one string)

Coverage targets:
- core_stock_tools.py: 83% → 100%
- technical_indicators_tools.py: 38% → 100% (the comma-split branch)
- fundamental_data_tools.py: 73% → 100% (4 tools)
- news_data_tools.py: 75% → 100% (3 tools)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

# All @tool decorators wrap the function — call .invoke() to exercise it.
from tradingagents.agents.utils.core_stock_tools import get_stock_data
from tradingagents.agents.utils.fundamental_data_tools import (
    get_balance_sheet,
    get_cashflow,
    get_fundamentals,
    get_income_statement,
)
from tradingagents.agents.utils.news_data_tools import (
    get_global_news,
    get_insider_transactions,
    get_news,
)
from tradingagents.agents.utils.technical_indicators_tools import get_indicators


# -- core_stock_tools --------------------------------------------------------


@pytest.mark.unit
def test_get_stock_data_routes_to_vendor():
    with patch(
        "tradingagents.agents.utils.core_stock_tools.route_to_vendor",
        return_value="ohlcv csv",
    ) as mock_route:
        result = get_stock_data.invoke(
            {"symbol": "NVDA", "start_date": "2026-01-01", "end_date": "2026-02-01"}
        )
    assert result == "ohlcv csv"
    mock_route.assert_called_once_with("get_stock_data", "NVDA", "2026-01-01", "2026-02-01")


# -- technical_indicators_tools ---------------------------------------------


@pytest.mark.unit
def test_get_indicators_single_indicator():
    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        return_value="rsi df",
    ) as mock_route:
        result = get_indicators.invoke(
            {"symbol": "NVDA", "indicator": "rsi", "curr_date": "2026-02-06"}
        )
    assert result == "rsi df"
    mock_route.assert_called_once_with("get_indicators", "NVDA", "rsi", "2026-02-06", 30)


@pytest.mark.unit
def test_get_indicators_splits_comma_separated_input():
    """LLMs sometimes pack multiple indicators into one string. The tool
    splits on commas, lowercases, and calls route_to_vendor once per indicator,
    joining results with double newline."""
    call_results = ["rsi result", "macd result", "boll result"]
    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        side_effect=call_results,
    ) as mock_route:
        result = get_indicators.invoke(
            {"symbol": "NVDA", "indicator": "RSI, MACD, boll", "curr_date": "2026-02-06"}
        )
    assert mock_route.call_count == 3
    assert "rsi result" in result
    assert "macd result" in result
    assert "boll result" in result
    # Lowercased + stripped
    [c0, c1, c2] = mock_route.call_args_list
    assert c0.args[2] == "rsi"
    assert c1.args[2] == "macd"
    assert c2.args[2] == "boll"


@pytest.mark.unit
def test_get_indicators_handles_value_error_per_indicator():
    """If route_to_vendor raises ValueError for one indicator, that indicator's
    error message is captured and the others still process."""
    def side_effect(method, symbol, ind, curr_date, look_back_days):
        if ind == "garbage":
            raise ValueError("unknown indicator: garbage")
        return f"{ind} ok"

    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        side_effect=side_effect,
    ):
        result = get_indicators.invoke(
            {"symbol": "NVDA", "indicator": "rsi, garbage, macd", "curr_date": "2026-02-06"}
        )
    assert "rsi ok" in result
    assert "unknown indicator: garbage" in result
    assert "macd ok" in result


@pytest.mark.unit
def test_get_indicators_skips_empty_strings_in_split():
    """'rsi,, macd' → only 'rsi' and 'macd' processed (empty strings skipped)."""
    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        side_effect=["rsi ok", "macd ok"],
    ) as mock_route:
        get_indicators.invoke(
            {"symbol": "NVDA", "indicator": "rsi,, macd", "curr_date": "2026-02-06"}
        )
    assert mock_route.call_count == 2


@pytest.mark.unit
def test_get_indicators_custom_lookback_days():
    with patch(
        "tradingagents.agents.utils.technical_indicators_tools.route_to_vendor",
        return_value="ok",
    ) as mock_route:
        get_indicators.invoke(
            {"symbol": "NVDA", "indicator": "rsi", "curr_date": "2026-02-06", "look_back_days": 90}
        )
    mock_route.assert_called_once_with("get_indicators", "NVDA", "rsi", "2026-02-06", 90)


# -- fundamental_data_tools --------------------------------------------------


@pytest.mark.unit
def test_get_fundamentals_routes_to_vendor():
    with patch(
        "tradingagents.agents.utils.fundamental_data_tools.route_to_vendor",
        return_value="fund report",
    ) as mock_route:
        result = get_fundamentals.invoke({"ticker": "NVDA", "curr_date": "2026-02-06"})
    assert result == "fund report"
    mock_route.assert_called_once_with("get_fundamentals", "NVDA", "2026-02-06")


@pytest.mark.unit
@pytest.mark.parametrize(
    "tool_func,method_name",
    [
        (get_balance_sheet, "get_balance_sheet"),
        (get_cashflow, "get_cashflow"),
        (get_income_statement, "get_income_statement"),
    ],
)
def test_financial_statement_tool_default_freq_quarterly(tool_func, method_name):
    """Balance sheet / cashflow / income all default freq='quarterly'."""
    with patch(
        f"tradingagents.agents.utils.fundamental_data_tools.route_to_vendor",
        return_value="ok",
    ) as mock_route:
        tool_func.invoke({"ticker": "NVDA", "curr_date": "2026-02-06"})
    mock_route.assert_called_once_with(method_name, "NVDA", "quarterly", "2026-02-06")


@pytest.mark.unit
@pytest.mark.parametrize(
    "tool_func,method_name",
    [
        (get_balance_sheet, "get_balance_sheet"),
        (get_cashflow, "get_cashflow"),
        (get_income_statement, "get_income_statement"),
    ],
)
def test_financial_statement_tool_explicit_freq_annual(tool_func, method_name):
    with patch(
        "tradingagents.agents.utils.fundamental_data_tools.route_to_vendor",
        return_value="ok",
    ) as mock_route:
        tool_func.invoke(
            {"ticker": "NVDA", "freq": "annual", "curr_date": "2026-02-06"}
        )
    mock_route.assert_called_once_with(method_name, "NVDA", "annual", "2026-02-06")


# -- news_data_tools ---------------------------------------------------------


@pytest.mark.unit
def test_get_news_routes_to_vendor():
    with patch(
        "tradingagents.agents.utils.news_data_tools.route_to_vendor",
        return_value="news",
    ) as mock_route:
        result = get_news.invoke(
            {"ticker": "NVDA", "start_date": "2026-01-30", "end_date": "2026-02-06"}
        )
    assert result == "news"
    mock_route.assert_called_once_with("get_news", "NVDA", "2026-01-30", "2026-02-06")


@pytest.mark.unit
def test_get_global_news_default_args():
    """look_back_days defaults to 7, limit to 5."""
    with patch(
        "tradingagents.agents.utils.news_data_tools.route_to_vendor",
        return_value="global",
    ) as mock_route:
        get_global_news.invoke({"curr_date": "2026-02-06"})
    mock_route.assert_called_once_with("get_global_news", "2026-02-06", 7, 5)


@pytest.mark.unit
def test_get_global_news_custom_args():
    with patch(
        "tradingagents.agents.utils.news_data_tools.route_to_vendor",
        return_value="global",
    ) as mock_route:
        get_global_news.invoke({"curr_date": "2026-02-06", "look_back_days": 14, "limit": 20})
    mock_route.assert_called_once_with("get_global_news", "2026-02-06", 14, 20)


@pytest.mark.unit
def test_get_insider_transactions_routes_to_vendor():
    with patch(
        "tradingagents.agents.utils.news_data_tools.route_to_vendor",
        return_value="insider",
    ) as mock_route:
        result = get_insider_transactions.invoke({"ticker": "NVDA"})
    assert result == "insider"
    mock_route.assert_called_once_with("get_insider_transactions", "NVDA")
