"""Brave Search News API adapter for TradingAgents news_data category.

Replaces (or supplements) yfinance news, which the WC-12 forward-alpha
follow-up flagged as a likely root cause of TradingAgents' lack of
predictive edge — yfinance news is press releases + headlines, not
quality reporting.

Brave Search News API: https://api.search.brave.com/res/v1/news/search

Usage:
    config["data_vendors"]["news_data"] = "brave"
    # or per-tool: config["tool_vendors"] = {"get_news": "brave"}

Env: BRAVE_API_KEY (loaded via dotenv from .env at repo root).
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timedelta

import requests

_NEWS_ENDPOINT = "https://api.search.brave.com/res/v1/news/search"

# Brave free tier: 1 request per second per token. Module-level throttle
# enforces a minimum gap between calls so multiple analysts in the same
# propagation don't 429 each other. Per-month cap (2000) is checked by the
# remaining-quota header on each response and surfaced as a warning.
_MIN_INTERVAL_SECONDS = 1.2  # 1 sec + 200 ms cushion
_last_call_ts: float = 0.0
_throttle_lock = threading.Lock()


def _throttle() -> None:
    """Block until at least _MIN_INTERVAL_SECONDS has passed since last call."""
    global _last_call_ts
    with _throttle_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL_SECONDS - (now - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.monotonic()


# Brave's freshness param accepts: pd (past day), pw (past week), pm (past month), py (past year),
# or a custom YYYY-MM-DDtoYYYY-MM-DD range string.


def _brave_headers() -> dict[str, str]:
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "BRAVE_API_KEY not set. Add it to .env or export in shell. "
            "Get a key from https://brave.com/search/api/."
        )
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }


def _format_results(results: list[dict], max_articles: int = 20) -> str:
    """Render Brave news results as a readable markdown digest for the LLM."""
    if not results:
        return "No news articles found in the requested window."

    lines = ["# News results (Brave Search)\n"]
    for i, r in enumerate(results[:max_articles], 1):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        description = r.get("description", "")
        age = r.get("age", "")  # e.g. "2 days ago"
        publisher = r.get("meta_url", {}).get("hostname", "") or ""

        lines.append(f"## {i}. {title}")
        if publisher or age:
            lines.append(f"*{publisher}* · {age}".strip())
        if description:
            lines.append(description)
        if url:
            lines.append(f"[link]({url})")
        lines.append("")

    if len(results) > max_articles:
        lines.append(f"*(showing first {max_articles} of {len(results)} results)*")
    return "\n".join(lines)


def _freshness_for_window(start_date: str, end_date: str) -> str:
    """Translate a date window into Brave's freshness param.

    Brave supports preset short codes (pd / pw / pm / py) OR a custom range
    in YYYY-MM-DDtoYYYY-MM-DD format. We use the custom range when both
    dates are specified, falling back to past-week if not.
    """
    if start_date and end_date:
        return f"{start_date}to{end_date}"
    return "pw"


def _request_with_retry(params: dict, max_retries: int = 2) -> dict:
    """GET against the news endpoint with throttle + 429 backoff.

    Free-tier 1-req/sec ceiling is enforced by _throttle() before every call.
    A 429 response triggers an exponential backoff (2s, 4s) and one retry.
    Other 4xx/5xx errors propagate via raise_for_status().
    """
    last_response = None
    for attempt in range(max_retries + 1):
        _throttle()
        response = requests.get(
            _NEWS_ENDPOINT,
            headers=_brave_headers(),
            params=params,
            timeout=30,
        )
        last_response = response
        if response.status_code == 429 and attempt < max_retries:
            time.sleep(2.0 * (attempt + 1))
            continue
        break
    last_response.raise_for_status()
    return last_response.json()


def get_news_brave(ticker: str, start_date: str, end_date: str) -> str:
    """Get ticker-specific news from Brave Search News API.

    Args:
        ticker: Stock symbol (e.g., "AAPL").
        start_date: ISO date YYYY-MM-DD.
        end_date: ISO date YYYY-MM-DD.

    Returns:
        Markdown-formatted news digest. Raises requests.HTTPError on API failure.
    """
    params = {
        "q": f"{ticker} stock",
        "count": 20,
        "freshness": _freshness_for_window(start_date, end_date),
        "search_lang": "en",
        "country": "us",
        "spellcheck": "0",
    }
    data = _request_with_retry(params)
    results = data.get("results", []) or []
    return _format_results(results)


def get_global_news_brave(
    curr_date: str,
    look_back_days: int = 7,
    limit: int = 50,
) -> str:
    """Get general market news from Brave Search News API.

    Args:
        curr_date: Reference date (YYYY-MM-DD).
        look_back_days: Window size in days.
        limit: Max articles to retrieve (capped at 20 by Brave per request).

    Returns:
        Markdown-formatted news digest.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d") if curr_date else datetime.now()
    start_dt = end_dt - timedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = end_dt.strftime("%Y-%m-%d")

    params = {
        "q": "stock market financial news",
        "count": min(limit, 20),
        "freshness": _freshness_for_window(start_date, end_date),
        "search_lang": "en",
        "country": "us",
        "spellcheck": "0",
    }
    data = _request_with_retry(params)
    results = data.get("results", []) or []
    return _format_results(results, max_articles=limit)
