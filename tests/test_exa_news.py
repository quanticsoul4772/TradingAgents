"""Unit tests for exa_news.py — primary news vendor.

Previously 23% covered. Tests cover: API request shape, response rendering,
date-window translation, throttle behavior, retry on 429, missing API key
error, empty result handling.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tradingagents.dataflows import exa_news as exa_mod
from tradingagents.dataflows.exa_news import (
    _exa_headers,
    _format_results,
    _request_with_retry,
    _throttle,
    _to_iso8601,
    get_global_news_exa,
    get_news_exa,
)

# -- _to_iso8601 -----------------------------------------------------------


@pytest.mark.unit
def test_to_iso8601_default_is_midnight():
    """YYYY-MM-DD → YYYY-MM-DDT00:00:00.000Z by default."""
    assert _to_iso8601("2026-02-06") == "2026-02-06T00:00:00.000Z"


@pytest.mark.unit
def test_to_iso8601_end_of_day_uses_2359():
    """end_of_day=True → 23:59:59.999 so endPublishedDate includes full day."""
    assert _to_iso8601("2026-02-06", end_of_day=True) == "2026-02-06T23:59:59.999Z"


# -- _exa_headers ----------------------------------------------------------


@pytest.mark.unit
def test_exa_headers_uses_env_key():
    with patch.dict("os.environ", {"EXA_API_KEY": "test-key-abc"}, clear=False):
        headers = _exa_headers()
    assert headers["x-api-key"] == "test-key-abc"
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"


@pytest.mark.unit
def test_exa_headers_raises_when_key_missing():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="EXA_API_KEY not set"):
            _exa_headers()


# -- _format_results -------------------------------------------------------


@pytest.mark.unit
def test_format_results_empty_returns_no_articles_message():
    out = _format_results([])
    assert "No news articles found" in out


@pytest.mark.unit
def test_format_results_renders_title_author_date_text_link():
    results = [
        {
            "title": "AAPL Q1 beats",
            "author": "John Doe",
            "publishedDate": "2026-02-06T14:30:00.000Z",
            "text": "Apple beat estimates by $5B.",
            "url": "https://example.com/aapl",
        }
    ]
    out = _format_results(results)
    assert "## 1. AAPL Q1 beats" in out
    assert "John Doe" in out
    assert "2026-02-06" in out  # date sliced to YYYY-MM-DD
    assert "Apple beat estimates by $5B." in out
    assert "https://example.com/aapl" in out


@pytest.mark.unit
def test_format_results_handles_missing_optional_fields():
    """Articles with no author / no text / no url still render."""
    results = [{"title": "Bare", "publishedDate": "2026-02-06"}]
    out = _format_results(results)
    assert "Bare" in out
    # No crash on missing fields


@pytest.mark.unit
def test_format_results_truncates_long_text():
    """Per-article body capped at ~1500 chars with ellipsis."""
    long_text = "x" * 5000
    results = [{"title": "T", "text": long_text, "publishedDate": "2026-02-06"}]
    out = _format_results(results)
    # The capped text + ellipsis should be present
    assert "…" in out
    # The full 5000-char string should NOT be present
    assert len([line for line in out.splitlines() if len(line) > 4000]) == 0


@pytest.mark.unit
def test_format_results_default_title_when_missing():
    out = _format_results([{"publishedDate": "2026-02-06"}])
    assert "Untitled" in out


@pytest.mark.unit
def test_format_results_caps_at_max_articles_with_count_note():
    """When more results than max_articles, include 'showing first N of M' note."""
    results = [{"title": f"Article {i}"} for i in range(30)]
    out = _format_results(results, max_articles=5)
    assert "Article 0" in out
    assert "Article 4" in out
    assert "Article 5" not in out  # 6th article not rendered
    assert "showing first 5 of 30" in out


# -- _throttle -------------------------------------------------------------


@pytest.mark.unit
def test_throttle_sleeps_to_enforce_rate_limit():
    """When called twice in quick succession, second call sleeps."""
    # Reset module-level state
    exa_mod._last_call_ts = 0.0
    with (
        patch("tradingagents.dataflows.exa_news.time.sleep") as mock_sleep,
        patch(
            "tradingagents.dataflows.exa_news.time.monotonic",
            side_effect=[100.0, 100.05, 100.05, 100.30],
            # First call: now=100.0, set _last_call_ts=100.05
            # Second call: now=100.05, gap=0.05 → wait=0.20, then set ts to 100.30
        ),
    ):
        _throttle()
        _throttle()
    mock_sleep.assert_called_once()
    sleep_arg = mock_sleep.call_args.args[0]
    assert sleep_arg > 0  # had to wait
    assert sleep_arg <= 0.25  # no more than the throttle interval


@pytest.mark.unit
def test_throttle_skips_sleep_when_enough_time_has_passed():
    """When enough time has passed since last call, no sleep."""
    exa_mod._last_call_ts = 0.0
    with (
        patch("tradingagents.dataflows.exa_news.time.sleep") as mock_sleep,
        patch(
            "tradingagents.dataflows.exa_news.time.monotonic",
            side_effect=[100.0, 100.0, 200.0, 200.0],  # large gap between calls
        ),
    ):
        _throttle()
        _throttle()
    mock_sleep.assert_not_called()


# -- _request_with_retry --------------------------------------------------


@pytest.mark.unit
def test_request_with_retry_returns_json_on_success():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"results": [{"title": "A"}]}
    fake_response.raise_for_status = MagicMock()
    with (
        patch("tradingagents.dataflows.exa_news.requests.post", return_value=fake_response),
        patch("tradingagents.dataflows.exa_news._throttle"),
        patch.dict("os.environ", {"EXA_API_KEY": "k"}, clear=False),
    ):
        result = _request_with_retry({"query": "test"})
    assert result == {"results": [{"title": "A"}]}


@pytest.mark.unit
def test_request_with_retry_retries_on_429():
    """First response 429, second response 200 — both attempts should fire."""
    response_429 = MagicMock()
    response_429.status_code = 429

    response_200 = MagicMock()
    response_200.status_code = 200
    response_200.json.return_value = {"results": []}
    response_200.raise_for_status = MagicMock()

    with (
        patch(
            "tradingagents.dataflows.exa_news.requests.post",
            side_effect=[response_429, response_200],
        ),
        patch("tradingagents.dataflows.exa_news._throttle"),
        patch("tradingagents.dataflows.exa_news.time.sleep"),
        patch.dict("os.environ", {"EXA_API_KEY": "k"}, clear=False),
    ):
        result = _request_with_retry({"query": "test"})
    assert result == {"results": []}


@pytest.mark.unit
def test_request_with_retry_raises_on_non_429_error():
    """4xx other than 429 → raise_for_status fires (RequestException)."""
    fake_response = MagicMock()
    fake_response.status_code = 401
    import requests as _requests

    fake_response.raise_for_status.side_effect = _requests.HTTPError("401 Unauthorized")
    with (
        patch("tradingagents.dataflows.exa_news.requests.post", return_value=fake_response),
        patch("tradingagents.dataflows.exa_news._throttle"),
        patch.dict("os.environ", {"EXA_API_KEY": "k"}, clear=False),
    ):
        with pytest.raises(_requests.HTTPError):
            _request_with_retry({"query": "test"})


# -- get_news_exa ----------------------------------------------------------


@pytest.mark.unit
def test_get_news_exa_sends_correct_payload():
    fake_data = {"results": [{"title": "AAPL up", "publishedDate": "2026-02-06"}]}
    with patch(
        "tradingagents.dataflows.exa_news._request_with_retry", return_value=fake_data
    ) as mock_req:
        out = get_news_exa("AAPL", "2026-01-30", "2026-02-06")
    payload = mock_req.call_args.args[0]
    assert payload["query"] == "AAPL stock news"
    assert payload["category"] == "news"
    assert payload["numResults"] == 20
    assert payload["startPublishedDate"] == "2026-01-30T00:00:00.000Z"
    assert payload["endPublishedDate"] == "2026-02-06T23:59:59.999Z"
    assert "AAPL up" in out


@pytest.mark.unit
def test_get_news_exa_handles_empty_results():
    with patch(
        "tradingagents.dataflows.exa_news._request_with_retry", return_value={"results": []}
    ):
        out = get_news_exa("BOGUS", "2026-01-30", "2026-02-06")
    assert "No news articles found" in out


@pytest.mark.unit
def test_get_news_exa_handles_missing_results_key():
    """Some Exa responses might omit 'results' entirely → treat as empty."""
    with patch("tradingagents.dataflows.exa_news._request_with_retry", return_value={}):
        out = get_news_exa("BOGUS", "2026-01-30", "2026-02-06")
    assert "No news articles found" in out


# -- get_global_news_exa --------------------------------------------------


@pytest.mark.unit
def test_get_global_news_exa_default_lookback():
    """Default lookback is 7 days."""
    fake_data = {"results": []}
    with patch(
        "tradingagents.dataflows.exa_news._request_with_retry", return_value=fake_data
    ) as mock_req:
        get_global_news_exa("2026-02-06")
    payload = mock_req.call_args.args[0]
    # 7-day window: start = 2026-02-06 minus 7 = 2026-01-30
    assert payload["startPublishedDate"] == "2026-01-30T00:00:00.000Z"
    assert payload["endPublishedDate"] == "2026-02-06T23:59:59.999Z"


@pytest.mark.unit
def test_get_global_news_exa_custom_lookback_and_limit():
    fake_data = {"results": []}
    with patch(
        "tradingagents.dataflows.exa_news._request_with_retry", return_value=fake_data
    ) as mock_req:
        get_global_news_exa("2026-02-06", look_back_days=14, limit=80)
    payload = mock_req.call_args.args[0]
    assert payload["numResults"] == 80
    assert payload["startPublishedDate"] == "2026-01-23T00:00:00.000Z"


@pytest.mark.unit
def test_get_global_news_exa_caps_limit_at_100():
    """Exa enforces numResults max=100; the function caps user input."""
    fake_data = {"results": []}
    with patch(
        "tradingagents.dataflows.exa_news._request_with_retry", return_value=fake_data
    ) as mock_req:
        get_global_news_exa("2026-02-06", limit=500)
    payload = mock_req.call_args.args[0]
    assert payload["numResults"] == 100


@pytest.mark.unit
def test_get_global_news_exa_uses_market_query():
    fake_data = {"results": []}
    with patch(
        "tradingagents.dataflows.exa_news._request_with_retry", return_value=fake_data
    ) as mock_req:
        get_global_news_exa("2026-02-06")
    payload = mock_req.call_args.args[0]
    assert "market" in payload["query"].lower() or "financial" in payload["query"].lower()
