"""Unit tests for tradingagents/signals/sector_baseline.py — pool aggregator.

Spec: specs/003-sector-baseline-gate/contracts/sector_pool_function.md

Data source: signal cache (`tradingagents/signals/cache.py`); these tests
patch `query_all` to return synthetic rows so the cache backend isn't
exercised in unit tests.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from tradingagents.signals.sector_baseline import SectorPool, aggregate_sector_pool


def _row(ticker: str, log_date: str, value: str) -> dict:
    """Build a synthetic cache row matching the shape returned by query_all."""
    return {
        "signal_id": "market_report",
        "ticker": ticker,
        "date": log_date,
        "value": value,
        "raw_json": None,
        "computed_at": "2026-05-01T00:00:00",
        "fetcher_version": "test",
    }


def _make_sector_lookup(mapping: dict[str, str]):
    def lookup(ticker: str) -> str:
        return mapping.get(ticker, "Unknown")

    return lookup


# Featurizer: count words in prose (deterministic + simple)
def _word_count(text: str) -> float:
    return float(len(text.split()))


@pytest.mark.unit
def test_empty_pool_for_unknown_sector(tmp_path):
    pool = aggregate_sector_pool(
        "Unknown",
        date(2026, 5, 6),
        sectors_cache_path=tmp_path / "sectors.json",
        signal_id="market_report",
        feature_callable=_word_count,
        sector_lookup=_make_sector_lookup({}),
    )
    assert isinstance(pool, SectorPool)
    assert pool.values == []
    assert pool.n == 0
    assert pool.contributors == {}


@pytest.mark.unit
def test_empty_pool_for_empty_string_sector(tmp_path):
    pool = aggregate_sector_pool(
        "",
        date(2026, 5, 6),
        sectors_cache_path=tmp_path / "sectors.json",
        signal_id="market_report",
        feature_callable=_word_count,
        sector_lookup=_make_sector_lookup({}),
    )
    assert pool.n == 0


@pytest.mark.unit
def test_strict_prior_cutoff_excludes_same_day_observations(tmp_path):
    rows = [
        _row("NVDA", "2026-05-05", "one two three"),
        _row("NVDA", "2026-05-06", "should be excluded"),
    ]
    with patch("tradingagents.signals.cache.query_all", return_value=rows):
        pool = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup({"NVDA": "Technology"}),
        )
    assert pool.n == 1
    assert pool.values == [3.0]
    assert pool.contributors == {"NVDA": 1}


@pytest.mark.unit
def test_aggregates_across_multiple_same_sector_tickers(tmp_path):
    rows = [
        _row("NVDA", "2026-05-01", "a b c"),  # 3
        _row("NVDA", "2026-05-02", "a b c d"),  # 4
        _row("MSFT", "2026-05-01", "x y"),  # 2
        _row("GOOGL", "2026-05-03", "p q r s t"),  # 5
        _row("JPM", "2026-05-01", "ignored — different sector"),
    ]
    sectors = {
        "NVDA": "Technology",
        "MSFT": "Technology",
        "GOOGL": "Technology",
        "JPM": "Financials",
    }
    with patch("tradingagents.signals.cache.query_all", return_value=rows):
        pool = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup(sectors),
        )
    assert pool.n == 4
    assert sorted(pool.values) == [2.0, 3.0, 4.0, 5.0]
    assert pool.contributors == {"GOOGL": 1, "MSFT": 1, "NVDA": 2}


@pytest.mark.unit
def test_iteration_order_deterministic(tmp_path):
    rows = [
        _row("NVDA", "2026-05-01", "a"),  # 1
        _row("AAPL", "2026-05-01", "x y"),  # 2
        _row("MSFT", "2026-05-01", "p q r"),  # 3
    ]
    sectors = {"NVDA": "Technology", "AAPL": "Technology", "MSFT": "Technology"}

    with patch("tradingagents.signals.cache.query_all", return_value=rows):
        pool1 = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup(sectors),
        )
    with patch("tradingagents.signals.cache.query_all", return_value=rows):
        pool2 = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup(sectors),
        )
    # Sorted by (ticker, date): AAPL=2, MSFT=3, NVDA=1
    assert pool1.values == [2.0, 3.0, 1.0]
    assert pool1.values == pool2.values
    assert pool1.contributors == pool2.contributors


@pytest.mark.unit
def test_feature_callable_failure_skips_observation(tmp_path, caplog):
    rows = [
        _row("NVDA", "2026-05-01", "good"),
        _row("MSFT", "2026-05-01", "BREAK"),
    ]

    def fragile_featurizer(text: str) -> float:
        if "BREAK" in text:
            raise ValueError("synthetic featurizer failure")
        return float(len(text))

    with (
        caplog.at_level("WARNING"),
        patch("tradingagents.signals.cache.query_all", return_value=rows),
    ):
        pool = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=fragile_featurizer,
            sector_lookup=_make_sector_lookup({"NVDA": "Technology", "MSFT": "Technology"}),
        )
    assert pool.n == 1
    assert pool.contributors == {"NVDA": 1}
    assert any("feature_callable" in m for m in caplog.messages)


@pytest.mark.unit
def test_cache_query_failure_returns_empty_pool(tmp_path, caplog):
    """If the cache query raises, return an empty pool with a logged warning."""
    with (
        caplog.at_level("WARNING"),
        patch("tradingagents.signals.cache.query_all", side_effect=RuntimeError("db locked")),
    ):
        pool = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup({"NVDA": "Technology"}),
        )
    assert pool.n == 0
    assert any("cache query failed" in m for m in caplog.messages)


@pytest.mark.unit
def test_tickers_with_unknown_sector_excluded(tmp_path):
    rows = [
        _row("NVDA", "2026-05-01", "a b c"),
        _row("MYSTERY", "2026-05-01", "x y"),
    ]
    sectors = {"NVDA": "Technology"}  # MYSTERY missing → "Unknown"

    with patch("tradingagents.signals.cache.query_all", return_value=rows):
        pool = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup(sectors),
        )
    assert pool.n == 1
    assert pool.contributors == {"NVDA": 1}


@pytest.mark.unit
def test_empty_cache_returns_empty_pool(tmp_path):
    with patch("tradingagents.signals.cache.query_all", return_value=[]):
        pool = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup({"NVDA": "Technology"}),
        )
    assert pool.n == 0
    assert pool.contributors == {}


@pytest.mark.unit
def test_non_string_value_skipped(tmp_path):
    """Cache rows with None or non-string `value` are skipped silently."""
    rows = [
        _row("NVDA", "2026-05-01", "valid"),
        {**_row("MSFT", "2026-05-01", ""), "value": None},
        {**_row("GOOGL", "2026-05-01", ""), "value": 12345},
    ]
    sectors = {"NVDA": "Technology", "MSFT": "Technology", "GOOGL": "Technology"}

    with patch("tradingagents.signals.cache.query_all", return_value=rows):
        pool = aggregate_sector_pool(
            "Technology",
            date(2026, 5, 6),
            sectors_cache_path=tmp_path / "sectors.json",
            signal_id="market_report",
            feature_callable=_word_count,
            sector_lookup=_make_sector_lookup(sectors),
        )
    assert pool.n == 1
    assert pool.contributors == {"NVDA": 1}
