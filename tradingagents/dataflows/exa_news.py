"""Exa Search News API adapter for TradingAgents news_data category.

Third news vendor alongside yfinance (low-quality, free) and brave (good
quality but search ranking favors *currently popular* articles, which
leaks future information into historical backtests).

Exa's `startPublishedDate` / `endPublishedDate` parameters constrain
*ranking* (not just post-hoc filtering) — making it the right vendor for
honest historical backtest news, where Brave's ranking time-leak was the
caveat that left "news quality is the bottleneck" only partially ruled out
across the 8-experiment chain.

Exa Search API: https://api.exa.ai/search

Usage:
    config["data_vendors"]["news_data"] = "exa"
    # or per-tool: config["tool_vendors"] = {"get_news": "exa"}

Env: EXA_API_KEY (loaded via dotenv from .env at repo root, or shell env).
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timedelta

import requests

_SEARCH_ENDPOINT = "https://api.exa.ai/search"

# Exa free tier is ~5 req/s. 0.25s gap = 4 req/s ceiling — leaves headroom
# for parallel analysts in the same propagation without 429s.
_MIN_INTERVAL_SECONDS = 0.25
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


def _exa_headers() -> dict[str, str]:
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "EXA_API_KEY not set. Add it to .env or export in shell. "
            "Get a key from https://dashboard.exa.ai/api-keys."
        )
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }


def _to_iso8601(date_str: str, end_of_day: bool = False) -> str:
    """Convert a YYYY-MM-DD date to ISO 8601 with Z suffix.

    Exa's startPublishedDate / endPublishedDate accept ISO 8601 timestamps.
    end_of_day=True snaps to 23:59:59 so endPublishedDate includes the
    full day rather than only midnight.
    """
    suffix = "T23:59:59.999Z" if end_of_day else "T00:00:00.000Z"
    return f"{date_str}{suffix}"


def _format_results(results: list[dict], max_articles: int = 20) -> str:
    """Render Exa search results as a readable markdown digest for the LLM."""
    if not results:
        return "No news articles found in the requested window."

    lines = ["# News results (Exa Search)\n"]
    for i, r in enumerate(results[:max_articles], 1):
        title = r.get("title") or "Untitled"
        url = r.get("url", "")
        published = r.get("publishedDate", "")[:10]  # YYYY-MM-DD slice
        author = r.get("author") or ""
        text = r.get("text") or ""
        # Cap per-article body so the digest stays a digest. Exa returns full
        # article text by default; trim to keep total response reasonable.
        if len(text) > 1500:
            text = text[:1500].rsplit(" ", 1)[0] + "…"

        lines.append(f"## {i}. {title}")
        meta_parts = [p for p in (author, published) if p]
        if meta_parts:
            lines.append("*" + " · ".join(meta_parts) + "*")
        if text:
            lines.append(text)
        if url:
            lines.append(f"[link]({url})")
        lines.append("")

    if len(results) > max_articles:
        lines.append(f"*(showing first {max_articles} of {len(results)} results)*")
    return "\n".join(lines)


def _request_with_retry(payload: dict, max_retries: int = 2) -> dict:
    """POST against the search endpoint with throttle + 429 backoff.

    Per-second rate limit is enforced by _throttle() before every call.
    A 429 response triggers exponential backoff (2s, 4s) and one retry.
    Other 4xx/5xx errors propagate via raise_for_status().
    """
    last_response = None
    for attempt in range(max_retries + 1):
        _throttle()
        response = requests.post(
            _SEARCH_ENDPOINT,
            headers=_exa_headers(),
            json=payload,
            timeout=30,
        )
        last_response = response
        if response.status_code == 429 and attempt < max_retries:
            time.sleep(2.0 * (attempt + 1))
            continue
        break
    last_response.raise_for_status()
    return last_response.json()


def get_news_exa(ticker: str, start_date: str, end_date: str) -> str:
    """Get ticker-specific news from Exa Search API.

    Args:
        ticker: Stock symbol (e.g., "AAPL").
        start_date: ISO date YYYY-MM-DD.
        end_date: ISO date YYYY-MM-DD.

    Returns:
        Markdown-formatted news digest. Raises requests.HTTPError on API failure.
    """
    payload = {
        "query": f"{ticker} stock news",
        "numResults": 20,
        "type": "auto",
        "category": "news",
        "startPublishedDate": _to_iso8601(start_date),
        "endPublishedDate": _to_iso8601(end_date, end_of_day=True),
        "contents": {
            "text": {"maxCharacters": 2000},
        },
    }
    data = _request_with_retry(payload)
    results = data.get("results", []) or []
    return _format_results(results)


def get_global_news_exa(
    curr_date: str,
    look_back_days: int = 7,
    limit: int = 50,
) -> str:
    """Get general market news from Exa Search API.

    Args:
        curr_date: Reference date (YYYY-MM-DD).
        look_back_days: Window size in days.
        limit: Max articles to retrieve (capped at 100 by Exa per request).

    Returns:
        Markdown-formatted news digest.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d") if curr_date else datetime.now()
    start_dt = end_dt - timedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = end_dt.strftime("%Y-%m-%d")

    payload = {
        "query": "stock market financial news",
        "numResults": min(limit, 100),
        "type": "auto",
        "category": "news",
        "startPublishedDate": _to_iso8601(start_date),
        "endPublishedDate": _to_iso8601(end_date, end_of_day=True),
        "contents": {
            "text": {"maxCharacters": 2000},
        },
    }
    data = _request_with_retry(payload)
    results = data.get("results", []) or []
    return _format_results(results, max_articles=limit)
