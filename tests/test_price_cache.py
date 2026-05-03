"""Unit tests for PriceCache batch fetcher + helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.dataflows.price_cache import PriceCache


def _fake_history(dates: list[str], closes: list[float]) -> pd.DataFrame:
    """Build a yfinance-shaped frame with tz-aware UTC index."""
    idx = pd.DatetimeIndex(pd.to_datetime(dates)).tz_localize("UTC")
    return pd.DataFrame({"Close": closes}, index=idx)


@pytest.fixture
def fake_yf_history():
    """Patch yf.Ticker(...).history to return per-ticker fake frames."""
    frames = {
        "NVDA": _fake_history(
            [f"2026-01-{d:02d}" for d in range(1, 32)] + [f"2026-02-{d:02d}" for d in range(1, 29)],
            [100.0 + i * 0.5 for i in range(31 + 28)],
        ),
        "AAPL": _fake_history(
            [f"2026-01-{d:02d}" for d in range(1, 32)] + [f"2026-02-{d:02d}" for d in range(1, 29)],
            [200.0 - i * 0.3 for i in range(31 + 28)],
        ),
        "SPY": _fake_history(
            [f"2026-01-{d:02d}" for d in range(1, 32)] + [f"2026-02-{d:02d}" for d in range(1, 29)],
            [400.0 + i * 0.1 for i in range(31 + 28)],
        ),
    }

    def fake_ticker(t):
        m = MagicMock()
        m.history.return_value = frames.get(t, pd.DataFrame())
        return m

    with patch("tradingagents.dataflows.price_cache.yf.Ticker", side_effect=fake_ticker):
        yield frames


@pytest.mark.unit
def test_cache_fetches_every_ticker_plus_benchmark(fake_yf_history):
    cache = PriceCache(["NVDA", "AAPL"], ["2026-02-06"], horizon_days=21)
    # NVDA, AAPL, SPY all in cache
    assert not cache.frame("NVDA").empty
    assert not cache.frame("AAPL").empty
    assert not cache.benchmark_frame().empty


@pytest.mark.unit
def test_alpha_uses_cached_frames(fake_yf_history):
    cache = PriceCache(["NVDA"], ["2026-02-06"], horizon_days=5)
    # NVDA rises +0.5/day; SPY rises +0.1/day. 5-day forward → NVDA outperforms.
    a = cache.alpha("NVDA", "2026-02-06", holding_days=5)
    assert a is not None
    assert a > 0  # NVDA outperforms benchmark


@pytest.mark.unit
def test_alpha_unresolvable_window_returns_none(fake_yf_history):
    """A trade date too close to cache end can't resolve a long-horizon window."""
    cache = PriceCache(["NVDA"], ["2026-02-06"], horizon_days=5)
    # Request a 90-day forward from a date the fixture's history doesn't cover.
    a = cache.alpha("NVDA", "2026-02-25", holding_days=90)
    assert a is None


@pytest.mark.unit
def test_trailing_return_no_lookahead(fake_yf_history):
    """trailing_return must use prices strictly BEFORE trade_date."""
    cache = PriceCache(["NVDA"], ["2026-02-15"], horizon_days=5)
    # 30-day trailing from Feb 15 — should have enough history (cache pads pre-window)
    m = cache.trailing_return("NVDA", "2026-02-15", lookback_days=30)
    assert m is not None
    # NVDA is monotonically rising at +0.5/day, so 30d trailing is positive
    assert m > 0


@pytest.mark.unit
def test_trailing_return_insufficient_history(fake_yf_history):
    """Not enough prior data → None, not an error."""
    cache = PriceCache(["NVDA"], ["2026-02-15"], horizon_days=5)
    # 500-day lookback can't be satisfied
    m = cache.trailing_return("NVDA", "2026-02-15", lookback_days=500)
    assert m is None


@pytest.mark.unit
def test_unknown_ticker_returns_empty_frame(fake_yf_history):
    cache = PriceCache(["NVDA"], ["2026-02-06"], horizon_days=5)
    assert cache.frame("BOGUS").empty
    assert cache.alpha("BOGUS", "2026-02-06", holding_days=5) is None
    assert cache.trailing_return("BOGUS", "2026-02-06", lookback_days=30) is None


@pytest.mark.unit
def test_empty_dates_raises():
    with pytest.raises(ValueError):
        PriceCache(["NVDA"], dates=[], horizon_days=5)


@pytest.mark.unit
def test_custom_benchmark(fake_yf_history):
    """A non-default benchmark is added to the cache and used by alpha()."""
    cache = PriceCache(["NVDA"], ["2026-02-06"], horizon_days=5, benchmark="AAPL")
    # AAPL is in cache as the benchmark
    assert cache.benchmark == "AAPL"
    assert not cache.benchmark_frame().empty
