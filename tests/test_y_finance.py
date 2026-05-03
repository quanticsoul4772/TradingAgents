"""Unit tests for dataflows/y_finance.py — primary stock/technical/fundamental vendor.

Previously 11% covered (152 stmts). Tests focus on the public functions
the framework actually calls: get_YFin_data_online, get_fundamentals,
get_balance_sheet, get_cashflow, get_income_statement, get_insider_transactions.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.dataflows.y_finance import (
    get_balance_sheet,
    get_cashflow,
    get_fundamentals,
    get_income_statement,
    get_insider_transactions,
    get_YFin_data_online,
)


def _ohlcv_frame() -> pd.DataFrame:
    """yfinance-shaped frame with OHLCV columns."""
    idx = pd.DatetimeIndex(pd.to_datetime(["2026-01-30", "2026-01-31", "2026-02-01"])).tz_localize("UTC")
    return pd.DataFrame(
        {
            "Open": [100.0, 101.5, 102.3],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.5, 101.0, 102.0],
            "Close": [100.50, 101.75, 102.80],
            "Adj Close": [100.50, 101.75, 102.80],
            "Volume": [1_000_000, 1_100_000, 1_050_000],
        },
        index=idx,
    )


# -- get_YFin_data_online -------------------------------------------------


@pytest.mark.unit
def test_get_yfin_data_online_returns_csv_with_header():
    """Happy path: returns CSV-formatted string prefixed with metadata header."""
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.history.return_value = _ohlcv_frame()
        result = get_YFin_data_online("NVDA", "2026-01-30", "2026-02-01")
    assert "# Stock data for NVDA" in result
    assert "# Total records: 3" in result
    assert "Close" in result
    # Round to 2 decimals
    assert "100.5" in result


@pytest.mark.unit
def test_get_yfin_data_online_empty_returns_no_data_message():
    """Empty yfinance response → friendly message, not exception."""
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        result = get_YFin_data_online("BOGUS", "2026-01-30", "2026-02-01")
    assert "No data found" in result


@pytest.mark.unit
def test_get_yfin_data_online_uppercases_symbol():
    """Lowercased ticker is uppercased for yf.Ticker call."""
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.history.return_value = _ohlcv_frame()
        get_YFin_data_online("nvda", "2026-01-30", "2026-02-01")
    mock_ticker.assert_called_once_with("NVDA")


@pytest.mark.unit
def test_get_yfin_data_online_strips_timezone_from_index():
    """tz-aware index is converted to tz-naive in the output."""
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.history.return_value = _ohlcv_frame()
        result = get_YFin_data_online("NVDA", "2026-01-30", "2026-02-01")
    # tz suffix would look like +00:00 or 'Z'; should not appear
    assert "+00:00" not in result


# -- get_fundamentals -----------------------------------------------------


@pytest.mark.unit
def test_get_fundamentals_renders_known_fields():
    """Each field in the .info dict that has a non-None value gets a line."""
    info = {
        "longName": "NVIDIA Corporation",
        "sector": "Technology",
        "marketCap": 2_500_000_000_000,
        "trailingPE": 65.4,
        "ebitda": None,  # None values dropped
    }
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.info = info
        result = get_fundamentals("NVDA")
    assert "Name: NVIDIA Corporation" in result
    assert "Sector: Technology" in result
    assert "Market Cap: 2500000000000" in result
    # Field with None value should NOT appear
    assert "EBITDA:" not in result


@pytest.mark.unit
def test_get_fundamentals_empty_info_returns_no_data_message():
    """Empty info dict → friendly message."""
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.info = {}
        result = get_fundamentals("BOGUS")
    assert "No fundamentals data" in result


@pytest.mark.unit
def test_get_fundamentals_swallows_exceptions():
    """yfinance raising → returns error string."""
    with patch(
        "tradingagents.dataflows.y_finance.yf.Ticker",
        side_effect=RuntimeError("network down"),
    ):
        result = get_fundamentals("NVDA")
    assert "Error retrieving fundamentals" in result


# -- get_balance_sheet (representative; cashflow + income same pattern) ---


@pytest.fixture
def mock_yf_for_financials():
    """Patch yf.Ticker + yf_retry + filter_financials_by_date for the
    financial-statement helpers (balance_sheet, cashflow, income_statement)."""
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ), patch(
        "tradingagents.dataflows.y_finance.filter_financials_by_date",
        side_effect=lambda df, _d: df,  # passthrough — no date filtering
    ):
        yield mock_ticker


@pytest.mark.unit
def test_get_balance_sheet_quarterly_default(mock_yf_for_financials):
    """Default freq=quarterly → calls quarterly_balance_sheet."""
    fake_bs = pd.DataFrame({"2025-12-31": [100, 200, 300]}, index=["Cash", "Receivables", "Inventory"])
    mock_yf_for_financials.return_value.quarterly_balance_sheet = fake_bs
    result = get_balance_sheet("NVDA", curr_date="2026-02-06")
    assert "# Balance Sheet" in result
    assert "Cash" in result


@pytest.mark.unit
def test_get_balance_sheet_annual_freq(mock_yf_for_financials):
    """freq=annual → calls balance_sheet (not quarterly_*)."""
    fake_bs = pd.DataFrame({"2025": [1000]}, index=["Total Assets"])
    mock_yf_for_financials.return_value.balance_sheet = fake_bs
    result = get_balance_sheet("NVDA", freq="annual", curr_date="2026-02-06")
    assert "Total Assets" in result


@pytest.mark.unit
def test_get_balance_sheet_empty_returns_no_data(mock_yf_for_financials):
    mock_yf_for_financials.return_value.quarterly_balance_sheet = pd.DataFrame()
    result = get_balance_sheet("NVDA", curr_date="2026-02-06")
    assert "No balance sheet data" in result


@pytest.mark.unit
def test_get_cashflow_renders_csv(mock_yf_for_financials):
    fake_cf = pd.DataFrame({"2025-12-31": [500]}, index=["Operating Cash Flow"])
    mock_yf_for_financials.return_value.quarterly_cashflow = fake_cf
    result = get_cashflow("NVDA", curr_date="2026-02-06")
    assert "Operating Cash Flow" in result


@pytest.mark.unit
def test_get_income_statement_renders_csv(mock_yf_for_financials):
    fake_is = pd.DataFrame({"2025-12-31": [10000]}, index=["Total Revenue"])
    mock_yf_for_financials.return_value.quarterly_income_stmt = fake_is
    result = get_income_statement("NVDA", curr_date="2026-02-06")
    assert "Total Revenue" in result


# -- get_insider_transactions --------------------------------------------


@pytest.mark.unit
def test_get_insider_transactions_renders_csv():
    fake_insider = pd.DataFrame(
        {
            "Insider": ["Jensen Huang"],
            "Transaction": ["Sale"],
            "Shares": [10_000],
        }
    )
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.insider_transactions = fake_insider
        result = get_insider_transactions("NVDA")
    assert "# Insider Transactions data for NVDA" in result
    assert "Jensen Huang" in result


@pytest.mark.unit
def test_get_insider_transactions_none_returns_no_data():
    """yfinance can return None for insider_transactions on some tickers."""
    with patch("tradingagents.dataflows.y_finance.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.y_finance.yf_retry", side_effect=lambda fn: fn()
    ):
        mock_ticker.return_value.insider_transactions = None
        result = get_insider_transactions("NVDA")
    assert "No insider transactions" in result


@pytest.mark.unit
def test_get_insider_transactions_swallows_exceptions():
    with patch(
        "tradingagents.dataflows.y_finance.yf.Ticker",
        side_effect=RuntimeError("network"),
    ):
        result = get_insider_transactions("NVDA")
    assert "Error retrieving insider transactions" in result
