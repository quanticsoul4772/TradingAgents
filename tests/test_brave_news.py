"""Tests for tradingagents.dataflows.brave_news.

Mocks the requests layer so tests don't hit the live Brave API. The integration
test against the real API lives in scripts/ as a manual smoke check.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.dataflows.brave_news import (
    _format_results,
    _freshness_for_window,
    get_global_news_brave,
    get_news_brave,
)

pytestmark = pytest.mark.unit


# ---- _freshness_for_window ----------------------------------------------


def test_freshness_with_full_window():
    assert _freshness_for_window("2026-04-15", "2026-04-22") == "2026-04-15to2026-04-22"


def test_freshness_falls_back_to_past_week():
    assert _freshness_for_window("", "") == "pw"
    assert _freshness_for_window("", "2026-04-22") == "pw"
    assert _freshness_for_window("2026-04-15", "") == "pw"


# ---- _format_results -----------------------------------------------------


def test_format_empty_results():
    assert "No news articles found" in _format_results([])


def test_format_includes_title_publisher_description_and_link():
    results = [
        {
            "title": "NVDA hits new high",
            "url": "https://example.com/nvda",
            "description": "Nvidia stock rallied on AI demand.",
            "age": "2 days ago",
            "meta_url": {"hostname": "example.com"},
        },
    ]
    out = _format_results(results)
    assert "NVDA hits new high" in out
    assert "https://example.com/nvda" in out
    assert "Nvidia stock rallied on AI demand." in out
    assert "2 days ago" in out
    assert "example.com" in out


def test_format_caps_at_max_articles():
    results = [
        {"title": f"Article {i}", "url": "", "description": "", "age": "", "meta_url": {}}
        for i in range(30)
    ]
    out = _format_results(results, max_articles=5)
    assert "Article 0" in out
    assert "Article 4" in out
    assert "Article 5" not in out
    assert "showing first 5 of 30 results" in out


def test_format_handles_missing_optional_fields():
    results = [{"title": "Bare-minimum article"}]
    out = _format_results(results)
    assert "Bare-minimum article" in out


# ---- get_news_brave (mocked) --------------------------------------------


def test_get_news_brave_calls_correct_endpoint(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "test-key-123")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "title": "AAPL earnings beat",
                "url": "https://example.com/aapl",
                "description": "Apple reported strong Q1 earnings.",
                "age": "1 day ago",
                "meta_url": {"hostname": "example.com"},
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch(
        "tradingagents.dataflows.brave_news.requests.get", return_value=mock_response
    ) as mock_get:
        out = get_news_brave("AAPL", "2026-04-15", "2026-04-22")

    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert "https://api.search.brave.com/res/v1/news/search" in call_kwargs.args[0]
    assert call_kwargs.kwargs["params"]["q"] == "AAPL stock"
    assert call_kwargs.kwargs["params"]["freshness"] == "2026-04-15to2026-04-22"
    assert call_kwargs.kwargs["headers"]["X-Subscription-Token"] == "test-key-123"
    assert "AAPL earnings beat" in out


def test_get_news_brave_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="BRAVE_API_KEY not set"):
        get_news_brave("AAPL", "2026-04-15", "2026-04-22")


def test_get_news_brave_propagates_http_error(monkeypatch):
    import requests

    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("422 Unprocessable Entity")
    with patch("tradingagents.dataflows.brave_news.requests.get", return_value=mock_response):
        with pytest.raises(requests.HTTPError):
            get_news_brave("AAPL", "2026-04-15", "2026-04-22")


# ---- get_global_news_brave (mocked) -------------------------------------


def test_get_global_news_brave_uses_lookback_window(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch(
        "tradingagents.dataflows.brave_news.requests.get", return_value=mock_response
    ) as mock_get:
        get_global_news_brave("2026-04-22", look_back_days=7, limit=10)

    params = mock_get.call_args.kwargs["params"]
    assert params["q"] == "stock market financial news"
    # Custom freshness range should bracket the requested window.
    assert "2026-04-15to2026-04-22" in params["freshness"]
    assert params["count"] == 10


def test_get_global_news_brave_caps_count_at_brave_limit(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch(
        "tradingagents.dataflows.brave_news.requests.get", return_value=mock_response
    ) as mock_get:
        get_global_news_brave("2026-04-22", look_back_days=7, limit=999)

    # Brave API caps at 20 per request; our adapter respects that.
    assert mock_get.call_args.kwargs["params"]["count"] == 20
