"""Unit tests for yfinance_news.py — default news vendor.

Previously 7% covered. yfinance returns articles in two formats (legacy
flat + new nested 'content' shape); these tests cover both, plus date
filtering, dedup, error handling, and the global-news look-ahead guard.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.dataflows.yfinance_news import (
    _extract_article_data,
    get_global_news_yfinance,
    get_news_yfinance,
)


# -- _extract_article_data -------------------------------------------------


@pytest.mark.unit
def test_extract_article_nested_content_format():
    """Modern yfinance format: {'content': {'title': ..., 'provider': {...}}}"""
    article = {
        "content": {
            "title": "AAPL Q1 earnings beat",
            "summary": "Apple beat estimates",
            "provider": {"displayName": "Bloomberg"},
            "canonicalUrl": {"url": "https://bloomberg.com/x"},
            "pubDate": "2026-02-06T14:30:00Z",
        }
    }
    out = _extract_article_data(article)
    assert out["title"] == "AAPL Q1 earnings beat"
    assert out["summary"] == "Apple beat estimates"
    assert out["publisher"] == "Bloomberg"
    assert out["link"] == "https://bloomberg.com/x"
    assert out["pub_date"] is not None
    assert out["pub_date"].year == 2026


@pytest.mark.unit
def test_extract_article_flat_legacy_format():
    """Older yfinance format with flat keys."""
    article = {
        "title": "Old format article",
        "summary": "summary text",
        "publisher": "Reuters",
        "link": "https://reuters.com/y",
    }
    out = _extract_article_data(article)
    assert out["title"] == "Old format article"
    assert out["publisher"] == "Reuters"
    assert out["pub_date"] is None  # flat format has no parsed date


@pytest.mark.unit
def test_extract_article_falls_back_to_clickThroughUrl():
    """When canonicalUrl is missing, use clickThroughUrl."""
    article = {
        "content": {
            "title": "T",
            "provider": {"displayName": "P"},
            "clickThroughUrl": {"url": "https://click.com/z"},
        }
    }
    assert _extract_article_data(article)["link"] == "https://click.com/z"


@pytest.mark.unit
def test_extract_article_handles_invalid_pub_date():
    """A malformed pubDate string should not raise — pub_date stays None."""
    article = {
        "content": {
            "title": "T",
            "provider": {"displayName": "P"},
            "pubDate": "garbage-not-iso",
        }
    }
    assert _extract_article_data(article)["pub_date"] is None


@pytest.mark.unit
def test_extract_article_missing_title_uses_default():
    article = {"content": {}}
    out = _extract_article_data(article)
    assert out["title"] == "No title"
    assert out["publisher"] == "Unknown"


# -- get_news_yfinance ------------------------------------------------------


@pytest.fixture
def patch_yf_ticker():
    """Patch yf.Ticker AND yf_retry inside the module under test."""
    with patch("tradingagents.dataflows.yfinance_news.yf.Ticker") as mock_ticker, patch(
        "tradingagents.dataflows.yfinance_news.yf_retry", side_effect=lambda fn: fn()
    ):
        yield mock_ticker


@pytest.mark.unit
def test_get_news_returns_no_news_message_when_empty(patch_yf_ticker):
    """No articles returned → friendly 'No news found' string."""
    patch_yf_ticker.return_value.get_news.return_value = []
    result = get_news_yfinance("NVDA", "2026-01-01", "2026-02-01")
    assert "No news found for NVDA" in result


@pytest.mark.unit
def test_get_news_filters_by_date_range(patch_yf_ticker):
    """Articles outside the requested date window are dropped."""
    in_window = {
        "content": {
            "title": "Inside window",
            "provider": {"displayName": "X"},
            "pubDate": "2026-02-01T00:00:00Z",
        }
    }
    out_of_window = {
        "content": {
            "title": "Outside window",
            "provider": {"displayName": "X"},
            "pubDate": "2025-06-01T00:00:00Z",
        }
    }
    patch_yf_ticker.return_value.get_news.return_value = [in_window, out_of_window]
    result = get_news_yfinance("NVDA", "2026-01-01", "2026-03-01")
    assert "Inside window" in result
    assert "Outside window" not in result


@pytest.mark.unit
def test_get_news_filters_all_returns_no_match_message(patch_yf_ticker):
    """When date filter eliminates all articles, distinct 'no news between dates' message."""
    article = {
        "content": {
            "title": "Way before",
            "provider": {"displayName": "X"},
            "pubDate": "2020-01-01T00:00:00Z",
        }
    }
    patch_yf_ticker.return_value.get_news.return_value = [article]
    result = get_news_yfinance("NVDA", "2026-01-01", "2026-03-01")
    assert "between 2026-01-01 and 2026-03-01" in result


@pytest.mark.unit
def test_get_news_includes_articles_without_pub_date(patch_yf_ticker):
    """Articles with no parseable pub_date are kept (can't filter, so include)."""
    article = {
        "title": "Old format, no date",
        "publisher": "X",
        "link": "https://x.com/a",
    }
    patch_yf_ticker.return_value.get_news.return_value = [article]
    result = get_news_yfinance("NVDA", "2026-01-01", "2026-03-01")
    assert "Old format, no date" in result


@pytest.mark.unit
def test_get_news_swallows_exceptions(patch_yf_ticker):
    """yfinance raising → returns error string, not raises."""
    patch_yf_ticker.return_value.get_news.side_effect = RuntimeError("network down")
    result = get_news_yfinance("NVDA", "2026-01-01", "2026-03-01")
    assert "Error fetching news" in result
    assert "network down" in result


@pytest.mark.unit
def test_get_news_includes_summary_and_link_when_present(patch_yf_ticker):
    article = {
        "content": {
            "title": "T",
            "summary": "Summary text here.",
            "provider": {"displayName": "Pub"},
            "canonicalUrl": {"url": "https://example.com"},
            "pubDate": "2026-02-01T00:00:00Z",
        }
    }
    patch_yf_ticker.return_value.get_news.return_value = [article]
    result = get_news_yfinance("NVDA", "2026-01-01", "2026-03-01")
    assert "Summary text here." in result
    assert "https://example.com" in result


# -- get_global_news_yfinance ----------------------------------------------


@pytest.fixture
def patch_yf_search():
    """Patch yf.Search class + yf_retry."""
    with patch("tradingagents.dataflows.yfinance_news.yf.Search") as mock_search, patch(
        "tradingagents.dataflows.yfinance_news.yf_retry", side_effect=lambda fn: fn()
    ):
        yield mock_search


@pytest.mark.unit
def test_get_global_news_dedupes_by_title(patch_yf_search):
    """Same title across multiple search queries → only included once."""
    article1 = {"content": {"title": "Same Title", "provider": {"displayName": "X"}}}
    article2 = {"content": {"title": "Same Title", "provider": {"displayName": "X"}}}
    article3 = {"content": {"title": "Different", "provider": {"displayName": "Y"}}}
    search_instance = MagicMock()
    search_instance.news = [article1, article2, article3]
    patch_yf_search.return_value = search_instance

    result = get_global_news_yfinance("2026-02-06", limit=10)
    # "Same Title" appears once even though it was returned twice
    assert result.count("Same Title") == 1
    assert "Different" in result


@pytest.mark.unit
def test_get_global_news_returns_empty_message_when_no_news(patch_yf_search):
    search_instance = MagicMock()
    search_instance.news = []
    patch_yf_search.return_value = search_instance

    result = get_global_news_yfinance("2026-02-06")
    assert "No global news found" in result


@pytest.mark.unit
def test_get_global_news_skips_lookahead_articles(patch_yf_search):
    """An article with pub_date AFTER curr_date is dropped (no look-ahead)."""
    article_future = {
        "content": {
            "title": "Future article",
            "provider": {"displayName": "X"},
            "pubDate": "2026-12-31T00:00:00Z",
        }
    }
    article_past = {
        "content": {
            "title": "Past article",
            "provider": {"displayName": "X"},
            "pubDate": "2026-01-01T00:00:00Z",
        }
    }
    search_instance = MagicMock()
    search_instance.news = [article_future, article_past]
    patch_yf_search.return_value = search_instance

    result = get_global_news_yfinance("2026-02-06")
    assert "Future article" not in result
    assert "Past article" in result


@pytest.mark.unit
def test_get_global_news_swallows_exceptions(patch_yf_search):
    patch_yf_search.side_effect = RuntimeError("search broken")
    result = get_global_news_yfinance("2026-02-06")
    assert "Error fetching global news" in result


@pytest.mark.unit
def test_get_global_news_handles_flat_format_articles(patch_yf_search):
    """Flat-format (legacy) articles should still render."""
    article = {"title": "Flat T", "publisher": "Pub", "link": "https://x"}
    search_instance = MagicMock()
    search_instance.news = [article]
    patch_yf_search.return_value = search_instance
    result = get_global_news_yfinance("2026-02-06")
    assert "Flat T" in result
