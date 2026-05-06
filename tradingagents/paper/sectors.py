"""Sector metadata cache backed by yfinance.

Spec: research.md R-3. Lazy fetch on first lookup; persistent JSON cache at
``~/.tradingagents/paper/sectors.json``. Tickers without sector data default
to ``"Unknown"`` (graceful degradation).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)

UNKNOWN_SECTOR = "Unknown"


def _load_cache(cache_path: Path) -> dict[str, str]:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Sector cache at %s is corrupted; ignoring: %s", cache_path, e)
        return {}


def _save_cache(cache_path: Path, cache: dict[str, str]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_path.with_suffix(cache_path.suffix + ".tmp")
    tmp.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(cache_path)


def _fetch_sector_from_yfinance(ticker: str) -> str:
    """Best-effort sector lookup; returns UNKNOWN_SECTOR on any failure."""
    try:
        info: Any = yf.Ticker(ticker).info or {}
        sector = info.get("sector")
        if isinstance(sector, str) and sector.strip():
            return sector
        return UNKNOWN_SECTOR
    except Exception as e:
        logger.warning("yfinance sector lookup failed for %s: %s", ticker, e)
        return UNKNOWN_SECTOR


def get_sector(ticker: str, cache_path: Path) -> str:
    """Return the GICS sector for ``ticker``, fetching on cache miss.

    Cache hits are O(1); misses pay one yfinance round-trip and persist the
    result. Failures degrade to ``UNKNOWN_SECTOR``.
    """
    cache = _load_cache(cache_path)
    if ticker in cache:
        return cache[ticker]
    sector = _fetch_sector_from_yfinance(ticker)
    cache[ticker] = sector
    _save_cache(cache_path, cache)
    return sector
