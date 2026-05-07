"""Unit tests for Spec 008 Hybrid C calendar-boost helper.

Covers SC-001 through SC-004 + SC-006 + invariants I-1..I-6 from
``specs/007-calendar-boost-filter/contracts/calendar_boost_api.md``.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.utils.calendar_boost import (
    _fetch_earnings_dates,
    apply_calendar_boost,
    calendar_boost,
    days_to_next_earnings,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clear_lru_cache():
    """Clear the LRU cache before each test (R-7) so tests are order-independent."""
    _fetch_earnings_dates.cache_clear()
    yield
    _fetch_earnings_dates.cache_clear()


# ---- calendar_boost() unit tests (I-1, I-3 boundaries + zero-paths) -------


def test_calendar_boost_at_zero_days_equals_one():
    """I-1 boundary: days=0 → boost=1.0 (max boost on earnings day)."""
    assert calendar_boost(0, window=14) == 1.0


def test_calendar_boost_at_window_equals_zero():
    """SC-001 strict path: days==window → boost=0 (>= window check)."""
    assert calendar_boost(14, window=14) == 0.0


def test_calendar_boost_returns_zero_for_none_days():
    """I-3 graceful degradation: None days → boost=0."""
    assert calendar_boost(None, window=14) == 0.0


def test_calendar_boost_returns_zero_for_negative_days():
    """I-6 defensive guard: negative days → boost=0."""
    assert calendar_boost(-1, window=14) == 0.0


def test_calendar_boost_returns_zero_for_zero_window():
    """Defensive guard: window <= 0 → boost=0."""
    assert calendar_boost(7, window=0) == 0.0


def test_calendar_boost_linear_decay():
    """Linear interpolation: days=window/2 → boost=0.5."""
    assert calendar_boost(7, window=14) == 0.5


def test_calendar_boost_returns_zero_for_days_above_window():
    """SC-001 strict path: days > window → boost=0."""
    assert calendar_boost(20, window=14) == 0.0


# ---- apply_calendar_boost() unit tests (I-3, I-4, SC-001 happy path) ------


def test_apply_calendar_boost_no_op_when_boost_zero():
    """I-3 no-boost identity: boost=0 → effective == base."""
    assert apply_calendar_boost(0.50, days_to_earnings=14, window=14, magnitude=0.5) == 0.50
    assert apply_calendar_boost(0.50, days_to_earnings=None, window=14, magnitude=0.5) == 0.50
    assert apply_calendar_boost(0.50, days_to_earnings=20, window=14, magnitude=0.5) == 0.50


def test_apply_calendar_boost_saturation_clamp():
    """I-4 clamp: base * (1 + m * boost) capped at 1.0."""
    # base=0.95 + magnitude=0.5 + boost=1.0: raw = 0.95 * 1.5 = 1.425, clamped to 1.0
    assert apply_calendar_boost(0.95, days_to_earnings=0, window=14, magnitude=0.5) == 1.0
    # base=1.0 + any boost: should stay at 1.0
    assert apply_calendar_boost(1.0, days_to_earnings=0, window=14, magnitude=0.5) == 1.0


def test_apply_calendar_boost_normal_case():
    """SC-001 happy path: 0.50 * (1 + 0.5 * 0.5) = 0.625 (days=7, window=14, magnitude=0.5)."""
    result = apply_calendar_boost(0.50, days_to_earnings=7, window=14, magnitude=0.5)
    assert result == pytest.approx(0.625)


def test_apply_calendar_boost_at_earnings_day():
    """SC-001 boundary: days=0 → effective = base * (1 + magnitude)."""
    assert apply_calendar_boost(
        0.50, days_to_earnings=0, window=14, magnitude=0.5
    ) == pytest.approx(0.75)


# ---- I-1 + I-2 monotonicity ----------------------------------------------


@pytest.mark.parametrize(
    "days,expected_boost",
    [
        (0, 1.0),
        (1, 13 / 14),
        (7, 0.5),
        (13, 1 / 14),
        (14, 0.0),
        (15, 0.0),
        (30, 0.0),
    ],
)
def test_calendar_boost_monotonicity(days, expected_boost):
    """I-1: boost(d) is non-strictly decreasing in d."""
    assert calendar_boost(days, window=14) == pytest.approx(expected_boost)


def test_effective_score_monotonicity():
    """I-2: effective(d) is non-strictly decreasing in d (SC-002)."""
    base = 0.50
    sweep = [0, 1, 7, 13, 14, 15, 30]
    effectives = [
        apply_calendar_boost(base, days_to_earnings=d, window=14, magnitude=0.5) for d in sweep
    ]
    # Non-strictly decreasing
    for i in range(len(effectives) - 1):
        assert effectives[i] >= effectives[i + 1], (
            f"Monotonicity violated at days={sweep[i]} → {sweep[i + 1]}: "
            f"{effectives[i]} < {effectives[i + 1]}"
        )


# ---- yfinance integration tests (mocked) ---------------------------------


def _make_earnings_dataframe(dates: list[datetime]) -> pd.DataFrame:
    """Build a DataFrame matching yfinance.earnings_dates shape (tz-aware index)."""
    if not dates:
        return pd.DataFrame()
    idx = pd.DatetimeIndex(dates).tz_localize("US/Eastern")
    return pd.DataFrame({"EPS Estimate": [None] * len(dates)}, index=idx)


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_yfinance_failure_returns_none(mock_ticker):
    """SC-003: yfinance.Ticker raises → days_to_next_earnings returns None."""
    mock_ticker.return_value.earnings_dates = property(
        lambda self: (_ for _ in ()).throw(RuntimeError("simulated network failure"))
    )

    # Use a side_effect on the property access via PropertyMock alternative:
    # set the attribute access to raise directly
    mock_instance = MagicMock()
    type(mock_instance).earnings_dates = property(
        lambda self: (_ for _ in ()).throw(RuntimeError("simulated"))
    )
    mock_ticker.return_value = mock_instance

    result = days_to_next_earnings("FAKE", "2026-05-06")
    assert result is None


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_yfinance_empty_calendar_returns_none(mock_ticker):
    """SC-003: yfinance returns empty DataFrame → days_to_next_earnings returns None."""
    mock_ticker.return_value.earnings_dates = _make_earnings_dataframe([])
    result = days_to_next_earnings("SPY", "2026-05-06")
    assert result is None


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_days_to_next_earnings_returns_correct_delta(mock_ticker):
    """Happy path: ticker has earnings 7 days after trade_date → returns 7."""
    earnings = [datetime(2026, 5, 13)]  # 7 days after 2026-05-06
    mock_ticker.return_value.earnings_dates = _make_earnings_dataframe(earnings)
    result = days_to_next_earnings("NVDA", "2026-05-06")
    assert result == 7


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_days_to_next_earnings_skips_past_earnings(mock_ticker):
    """When all cached earnings are strictly before trade_date → returns None."""
    earnings = [datetime(2026, 1, 1), datetime(2026, 2, 1)]
    mock_ticker.return_value.earnings_dates = _make_earnings_dataframe(earnings)
    result = days_to_next_earnings("NVDA", "2026-05-06")
    assert result is None


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_days_to_next_earnings_picks_earliest_upcoming(mock_ticker):
    """When multiple future earnings, return delta to the EARLIEST one."""
    earnings = [datetime(2026, 8, 1), datetime(2026, 5, 13), datetime(2026, 11, 1)]
    mock_ticker.return_value.earnings_dates = _make_earnings_dataframe(earnings)
    result = days_to_next_earnings("NVDA", "2026-05-06")
    assert result == 7  # 2026-05-13 is earliest >= 2026-05-06


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_days_to_next_earnings_unparseable_date_returns_none(mock_ticker):
    """Defensive: unparseable trade_date string → returns None (no exception)."""
    mock_ticker.return_value.earnings_dates = _make_earnings_dataframe([datetime(2026, 5, 13)])
    result = days_to_next_earnings("NVDA", "not-a-date")
    assert result is None


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_lru_cache_idempotency(mock_ticker):
    """SC-004 + I-5: two calls for same ticker → exactly one yfinance.Ticker call."""
    mock_ticker.return_value.earnings_dates = _make_earnings_dataframe([datetime(2026, 5, 13)])

    # Two calls, same ticker
    days_to_next_earnings("NVDA", "2026-05-06")
    days_to_next_earnings("NVDA", "2026-05-07")

    # yfinance.Ticker should be invoked exactly ONCE (cached after first call)
    assert mock_ticker.call_count == 1
    mock_ticker.assert_called_with("NVDA")


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_lru_cache_different_tickers_separate_fetches(mock_ticker):
    """LRU cache keyed by ticker: different tickers → separate fetches."""
    mock_ticker.return_value.earnings_dates = _make_earnings_dataframe([datetime(2026, 5, 13)])

    days_to_next_earnings("NVDA", "2026-05-06")
    days_to_next_earnings("MSFT", "2026-05-06")
    days_to_next_earnings("NVDA", "2026-05-07")  # cached, should not refetch
    days_to_next_earnings("AAPL", "2026-05-06")

    # 3 distinct tickers → 3 fetches; the second NVDA call hits cache
    assert mock_ticker.call_count == 3
