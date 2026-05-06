"""Unit tests for tradingagents/paper/pricing.py — slippage math + cached
yfinance frame fetches + alpha reconciliation against returns_from_frames.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.paper import pricing


def _frame(closes: list[float], start: str = "2026-04-03") -> pd.DataFrame:
    """Build a yfinance-shaped frame with a DatetimeIndex starting at start."""
    idx = pd.date_range(start, periods=len(closes), freq="B")  # business days
    return pd.DataFrame({"Close": closes}, index=idx)


@pytest.fixture(autouse=True)
def _clear_cache():
    pricing.clear_price_cache()
    yield
    pricing.clear_price_cache()


@pytest.mark.unit
def test_next_trading_day_close_buy_applies_positive_slippage():
    frame = _frame([100.0, 101.0, 102.0])
    with patch("tradingagents.paper.pricing._fetch_history", return_value=frame):
        result = pricing.next_trading_day_close(
            "FAKE",
            date(2026, 4, 3),
            slippage_bps=Decimal("10"),
            direction="buy",
        )
    assert result is not None
    next_date, price = result
    # next trading day after 2026-04-03 (Friday) is 2026-04-06 (Mon)
    assert next_date == date(2026, 4, 6)
    # 101.0 * (1 + 10/10000) = 101.101
    assert price == Decimal("101.0") * (Decimal("1") + Decimal("10") / Decimal("10000"))


@pytest.mark.unit
def test_next_trading_day_close_sell_applies_negative_slippage():
    frame = _frame([200.0, 198.0, 199.0])
    with patch("tradingagents.paper.pricing._fetch_history", return_value=frame):
        result = pricing.next_trading_day_close(
            "FAKE",
            date(2026, 4, 3),
            slippage_bps=Decimal("10"),
            direction="sell",
        )
    assert result is not None
    _, price = result
    assert price == Decimal("198.0") * (Decimal("1") - Decimal("10") / Decimal("10000"))


@pytest.mark.unit
def test_next_trading_day_close_zero_slippage_returns_raw():
    frame = _frame([100.0, 101.0])
    with patch("tradingagents.paper.pricing._fetch_history", return_value=frame):
        result = pricing.next_trading_day_close("FAKE", date(2026, 4, 3))
    assert result is not None
    _, price = result
    assert price == Decimal("101.0")


@pytest.mark.unit
def test_next_trading_day_close_returns_none_on_empty_frame():
    with patch("tradingagents.paper.pricing._fetch_history", return_value=pd.DataFrame()):
        result = pricing.next_trading_day_close("DELISTED", date(2026, 4, 3))
    assert result is None


@pytest.mark.unit
def test_close_on_or_before_picks_latest_eligible_row():
    frame = _frame([100.0, 101.0, 102.0, 103.0], start="2026-04-01")
    with patch("tradingagents.paper.pricing._fetch_history", return_value=frame):
        result = pricing.close_on_or_before("FAKE", date(2026, 4, 3))
    assert result is not None
    eligible_date, price = result
    # 2026-04-03 IS a business day (Friday). Frame starts 4-01 (Wed) with
    # business-day cadence: 4-01=100, 4-02=101, 4-03=102; 4-06 (Mon)=103 is later.
    assert eligible_date == date(2026, 4, 3)
    assert price == Decimal("102.0")


@pytest.mark.unit
def test_trading_days_after_n_returns_correct_index():
    frame = _frame([100.0] * 10, start="2026-04-03")
    with patch("tradingagents.paper.pricing._fetch_history", return_value=frame):
        result = pricing.trading_days_after("FAKE", date(2026, 4, 3), 3)
    # 3 business days after 2026-04-03 (Fri) → 2026-04-08 (Wed)
    assert result == date(2026, 4, 8)


@pytest.mark.unit
def test_compute_realized_alpha_delegates_to_returns_from_frames():
    stock_frame = _frame([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])  # +5%
    bench_frame = _frame([400.0, 402.0, 404.0, 406.0, 408.0, 410.0])  # +2.5%

    def fake_history(ticker, start, end):
        return stock_frame if ticker == "NVDA" else bench_frame

    with patch("tradingagents.paper.pricing._fetch_history", side_effect=fake_history):
        result = pricing.compute_realized_alpha("NVDA", date(2026, 4, 3), 5, "SPY")
    assert result is not None
    raw, alpha = result
    assert raw == pytest.approx(Decimal("0.05"), abs=Decimal("0.001"))
    assert alpha == pytest.approx(Decimal("0.025"), abs=Decimal("0.001"))


@pytest.mark.unit
def test_compute_realized_alpha_returns_none_on_empty_frame():
    with patch("tradingagents.paper.pricing._fetch_history", return_value=pd.DataFrame()):
        result = pricing.compute_realized_alpha("BOGUS", date(2026, 4, 3), 5)
    assert result is None


@pytest.mark.unit
def test_lru_cache_avoids_refetch():
    fetch_calls = []
    real_frame = _frame([100.0, 101.0])

    def counted_fetch(ticker, start, end):
        fetch_calls.append((ticker, start, end))
        return real_frame

    with patch("tradingagents.paper.pricing._fetch_history", side_effect=counted_fetch):
        pricing.next_trading_day_close("CACHED", date(2026, 4, 3))
        pricing.next_trading_day_close("CACHED", date(2026, 4, 3))
        pricing.next_trading_day_close("CACHED", date(2026, 4, 3))
    # Only one underlying fetch despite three calls
    assert len(fetch_calls) == 1
