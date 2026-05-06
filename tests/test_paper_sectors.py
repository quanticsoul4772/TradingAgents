"""Unit tests for tradingagents/paper/sectors.py — yfinance sector cache."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.paper import sectors


@pytest.mark.unit
def test_first_lookup_fetches_and_caches(tmp_path):
    cache = tmp_path / "sectors.json"
    mock_ticker = MagicMock()
    mock_ticker.info = {"sector": "Technology"}
    with patch("tradingagents.paper.sectors.yf.Ticker", return_value=mock_ticker):
        result = sectors.get_sector("NVDA", cache)
    assert result == "Technology"
    assert json.loads(cache.read_text(encoding="utf-8")) == {"NVDA": "Technology"}


@pytest.mark.unit
def test_subsequent_lookup_hits_cache(tmp_path):
    cache = tmp_path / "sectors.json"
    cache.write_text(json.dumps({"NVDA": "Technology"}), encoding="utf-8")
    with patch("tradingagents.paper.sectors.yf.Ticker") as mock:
        result = sectors.get_sector("NVDA", cache)
    assert result == "Technology"
    mock.assert_not_called()  # cache hit means no network


@pytest.mark.unit
def test_yfinance_failure_returns_unknown(tmp_path):
    cache = tmp_path / "sectors.json"
    with patch("tradingagents.paper.sectors.yf.Ticker", side_effect=RuntimeError("network down")):
        result = sectors.get_sector("BOGUS", cache)
    assert result == sectors.UNKNOWN_SECTOR
    # Still cached so we don't re-attempt the failed fetch
    assert json.loads(cache.read_text(encoding="utf-8")) == {"BOGUS": "Unknown"}


@pytest.mark.unit
def test_missing_sector_field_returns_unknown(tmp_path):
    cache = tmp_path / "sectors.json"
    mock_ticker = MagicMock()
    mock_ticker.info = {}  # no "sector" key
    with patch("tradingagents.paper.sectors.yf.Ticker", return_value=mock_ticker):
        result = sectors.get_sector("ETF", cache)
    assert result == sectors.UNKNOWN_SECTOR


@pytest.mark.unit
def test_empty_string_sector_returns_unknown(tmp_path):
    cache = tmp_path / "sectors.json"
    mock_ticker = MagicMock()
    mock_ticker.info = {"sector": ""}
    with patch("tradingagents.paper.sectors.yf.Ticker", return_value=mock_ticker):
        result = sectors.get_sector("X", cache)
    assert result == sectors.UNKNOWN_SECTOR


@pytest.mark.unit
def test_corrupt_cache_falls_back_to_fresh_fetch(tmp_path):
    cache = tmp_path / "sectors.json"
    cache.write_text("{not json", encoding="utf-8")
    mock_ticker = MagicMock()
    mock_ticker.info = {"sector": "Healthcare"}
    with patch("tradingagents.paper.sectors.yf.Ticker", return_value=mock_ticker):
        result = sectors.get_sector("UNH", cache)
    assert result == "Healthcare"
