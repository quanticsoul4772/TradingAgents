"""Unit tests for the analyst_pt_snapshot Path C helper (PR #73)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.utils.analyst_pt_snapshot import (
    _fetch_pt_snapshot_cached,
    clear_cache,
    fetch_analyst_pt_snapshot,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clear_lru():
    """Reset the LRU cache between tests."""
    clear_cache()
    yield
    clear_cache()


# ---- Public API edge cases -----------------------------------------------


def test_returns_none_for_empty_string():
    assert fetch_analyst_pt_snapshot("") is None


def test_returns_none_for_non_string():
    assert fetch_analyst_pt_snapshot(None) is None  # type: ignore[arg-type]
    assert fetch_analyst_pt_snapshot(123) is None  # type: ignore[arg-type]


# ---- yfinance integration (mocked) ---------------------------------------


def _make_mock_ticker(pt: dict, recs: pd.DataFrame | None) -> MagicMock:
    mock = MagicMock()
    mock.analyst_price_targets = pt
    mock.recommendations = recs
    return mock


def test_returns_dict_with_pt_and_recommendations():
    fake_pt = {"current": 200.0, "high": 250.0, "low": 150.0, "mean": 225.0, "median": 220.0}
    fake_recs = pd.DataFrame(
        [{"period": "0m", "strongBuy": 5, "buy": 10, "hold": 3, "sell": 1, "strongSell": 0}]
    )
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = _make_mock_ticker(fake_pt, fake_recs)

    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        result = fetch_analyst_pt_snapshot("NVDA")

    assert result is not None
    assert "analyst_price_targets" in result
    assert result["analyst_price_targets"]["current"] == 200.0
    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) == 1


def test_returns_none_when_yfinance_raises_on_ticker_construction():
    mock_yf = MagicMock()
    mock_yf.Ticker.side_effect = RuntimeError("api down")

    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        result = fetch_analyst_pt_snapshot("NVDA")

    assert result is None


def test_returns_none_when_pt_is_empty():
    """ETFs return empty dict → snapshot is None (graceful per PR #40)."""
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = _make_mock_ticker({}, None)

    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        result = fetch_analyst_pt_snapshot("SPY")

    assert result is None


def test_recommendations_failure_does_not_break_pt_capture():
    """If recommendations fails but PT succeeds, snapshot still returns PT."""
    fake_pt = {"current": 100.0, "mean": 110.0}

    class _Ticker:
        analyst_price_targets = fake_pt

        @property
        def recommendations(self):
            raise RuntimeError("recs api down")

    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = _Ticker()

    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        result = fetch_analyst_pt_snapshot("NVDA")

    assert result is not None
    assert result["analyst_price_targets"] == fake_pt
    assert result["recommendations"] is None


def test_recommendations_empty_df_returns_none():
    fake_pt = {"current": 100.0, "mean": 110.0}
    empty_df = pd.DataFrame()
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = _make_mock_ticker(fake_pt, empty_df)

    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        result = fetch_analyst_pt_snapshot("NVDA")

    assert result is not None
    assert result["recommendations"] is None


# ---- LRU cache behavior --------------------------------------------------


def test_cache_only_calls_yfinance_once_per_ticker():
    fake_pt = {"current": 100.0, "mean": 110.0}
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = _make_mock_ticker(fake_pt, None)

    with patch.dict("sys.modules", {"yfinance": mock_yf}):
        fetch_analyst_pt_snapshot("NVDA")
        fetch_analyst_pt_snapshot("NVDA")
        fetch_analyst_pt_snapshot("nvda")  # case-normalized; cache hit

    # Only one yfinance.Ticker call despite 3 fetches
    assert mock_yf.Ticker.call_count == 1


def test_clear_cache_helper_resets_lru():
    """clear_cache() should reset the LRU stats."""
    clear_cache()
    info_after = _fetch_pt_snapshot_cached.cache_info()
    assert info_after.currsize == 0
