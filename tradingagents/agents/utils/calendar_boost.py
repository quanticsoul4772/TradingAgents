"""Spec 008 Hybrid C — calendar-boosted forward-catalyst filter helper.

Pure post-processing of Spec 007's `bull_case_priced_in` LLM score:
multiplies the score by `(1 + magnitude * boost)` where `boost` is a
linear function of `days_to_next_earnings`. Earnings-proximate commits
get a higher effective score → more likely to fire the spec 007
suppression. Empirical motivation:
``claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md``.

Zero LLM cost (Constitution III T0). yfinance.earnings_dates fetch is
free + LRU-cached per ticker per process. Bull-only (per spec 008 FR-004).
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import cache

import yfinance as yf

logger = logging.getLogger(__name__)


@cache
def _fetch_earnings_dates(ticker: str) -> tuple[datetime, ...]:
    """Return sorted tuple of tz-naive earnings datetimes for the ticker.

    Empty tuple when yfinance fails OR returns empty calendar (ETFs, new
    IPOs, etc.). LRU-cached process-wide; tests must call
    ``_fetch_earnings_dates.cache_clear()`` between tests.
    """
    try:
        ed = yf.Ticker(ticker).earnings_dates
        if ed is None or ed.empty:
            return ()
        return tuple(sorted(ed.index.tz_convert(None).to_pydatetime().tolist()))
    except Exception as exc:  # noqa: BLE001
        logger.debug("calendar_boost: earnings_dates fetch failed for %s: %s", ticker, exc)
        return ()


def days_to_next_earnings(ticker: str, trade_date: str | datetime) -> int | None:
    """Calendar days from ``trade_date`` to the next earnings >= ``trade_date``.

    Returns ``None`` when the ticker has no earnings calendar, yfinance
    fails, ``trade_date`` is unparseable, or all cached earnings are
    strictly before ``trade_date``.
    """
    if isinstance(trade_date, str):
        try:
            td = datetime.fromisoformat(trade_date)
        except ValueError:
            return None
    else:
        td = trade_date
    cache = _fetch_earnings_dates(ticker)
    upcoming = [e for e in cache if e >= td]
    if not upcoming:
        return None
    return (upcoming[0] - td).days


def calendar_boost(days_to_earnings: int | None, window: int) -> float:
    """Boost factor in [0.0, 1.0]. Linear: 1.0 at days=0, 0.0 at days>=window.

    Returns 0.0 for any None/negative days, days >= window, or window <= 0.
    """
    if window <= 0:
        return 0.0
    if days_to_earnings is None or days_to_earnings < 0:
        return 0.0
    if days_to_earnings >= window:
        return 0.0
    return 1.0 - (days_to_earnings / window)


def apply_calendar_boost(
    score: float,
    days_to_earnings: int | None,
    window: int,
    magnitude: float,
) -> float:
    """Effective = min(1.0, score * (1 + magnitude * calendar_boost(...))).

    When ``calendar_boost`` returns 0 (any zero-path above), effective == score.
    The min(1.0, ...) clamp prevents super-saturation past the [0, 1] convention.
    """
    boost = calendar_boost(days_to_earnings, window)
    return min(1.0, score * (1.0 + magnitude * boost))
