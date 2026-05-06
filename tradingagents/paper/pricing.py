"""Price-fetch + slippage + alpha helpers.

Spec: research.md R-1, R-6, R-7, R-8. Wraps yfinance for close-price marking
and delegates forward-α math to ``tradingagents.dataflows.returns.returns_from_frames``
per FR-012 (single source of truth for forward-α math).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from functools import lru_cache

import pandas as pd
import yfinance as yf

from tradingagents.dataflows.returns import returns_from_frames

logger = logging.getLogger(__name__)

BPS_DENOM = Decimal("10000")


def _to_decimal(x: float | int) -> Decimal:
    return Decimal(str(x))


def _fetch_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Bare yfinance history fetch with conservative buffer; not cached here."""
    return yf.Ticker(ticker).history(start=start, end=end)


@lru_cache(maxsize=512)
def _cached_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    """In-process LRU per (ticker, start, end). Per R-1 — short-lived caching
    within a single command invocation; cleared between commands by Python
    process exit."""
    return _fetch_history(ticker, start, end)


def clear_price_cache() -> None:
    """Clear the in-process price cache. Useful for tests."""
    _cached_history.cache_clear()


def next_trading_day_close(
    ticker: str,
    after_date: date,
    *,
    slippage_bps: Decimal = Decimal("0"),
    direction: str = "buy",
) -> tuple[date, Decimal] | None:
    """Return (trading_date, close_price_with_slippage) for the first trading
    day strictly AFTER ``after_date`` for ``ticker``.

    ``direction``: ``"buy"`` adds slippage (price goes up); ``"sell"`` subtracts.
    Returns None if no trading day in the next 7 calendar days (R-6 buffer).
    """
    start = after_date.isoformat()
    end = (after_date + timedelta(days=8)).isoformat()
    frame = _cached_history(ticker, start, end)
    if frame.empty:
        return None
    # Filter to rows strictly after `after_date`
    idx = frame.index
    if isinstance(idx, pd.DatetimeIndex):
        idx_naive = idx.tz_localize(None) if idx.tz is not None else idx
    else:
        idx_naive = idx
    cutoff = pd.Timestamp(after_date)
    later = frame.loc[idx_naive > cutoff]
    if later.empty:
        return None
    first = later.iloc[0]
    next_date = later.index[0]
    if isinstance(next_date, pd.Timestamp):
        next_date_value = next_date.date()
    else:
        next_date_value = next_date
    raw_close = _to_decimal(float(first["Close"]))
    multiplier = Decimal("1") + (slippage_bps / BPS_DENOM) * (
        Decimal("1") if direction == "buy" else Decimal("-1")
    )
    return next_date_value, raw_close * multiplier


def close_on_or_before(
    ticker: str,
    target_date: date,
    *,
    lookback_days: int = 7,
) -> tuple[date, Decimal] | None:
    """Return (trading_date, close_price) for the latest trading day <= ``target_date``.

    Used for mark-to-market and `status` digests. No slippage applied (this is
    the unbiased mark, not a transaction).
    """
    start = (target_date - timedelta(days=lookback_days)).isoformat()
    end = (target_date + timedelta(days=2)).isoformat()
    frame = _cached_history(ticker, start, end)
    if frame.empty:
        return None
    idx = frame.index
    if isinstance(idx, pd.DatetimeIndex):
        idx_naive = idx.tz_localize(None) if idx.tz is not None else idx
    else:
        idx_naive = idx
    cutoff = pd.Timestamp(target_date)
    eligible = frame.loc[idx_naive <= cutoff]
    if eligible.empty:
        return None
    last = eligible.iloc[-1]
    last_date = eligible.index[-1]
    if isinstance(last_date, pd.Timestamp):
        last_date_value = last_date.date()
    else:
        last_date_value = last_date
    return last_date_value, _to_decimal(float(last["Close"]))


def trading_days_after(ticker: str, anchor: date, n: int) -> date | None:
    """Return the date that is ``n`` trading days after ``anchor`` for ``ticker``.

    Used to compute ``intended_close_date`` for new positions per R-7. Falls
    back to (anchor + n calendar days) if yfinance can't supply enough rows.
    """
    if n <= 0:
        return anchor
    # Fetch enough buffer to cover n trading days even with weekends/holidays
    end = (anchor + timedelta(days=int(n * 1.5) + 7)).isoformat()
    frame = _cached_history(ticker, anchor.isoformat(), end)
    if frame.empty:
        return anchor + timedelta(days=n)
    idx = frame.index
    if isinstance(idx, pd.DatetimeIndex):
        idx_naive = idx.tz_localize(None) if idx.tz is not None else idx
    else:
        return anchor + timedelta(days=n)
    cutoff = pd.Timestamp(anchor)
    later = frame.loc[idx_naive >= cutoff]
    if len(later) <= n:
        return anchor + timedelta(days=n)
    target = later.index[n]
    if isinstance(target, pd.Timestamp):
        return target.date()
    return anchor + timedelta(days=n)


def compute_realized_alpha(
    ticker: str,
    entry_date: date,
    actual_holding_days: int,
    benchmark: str = "SPY",
) -> tuple[Decimal, Decimal] | None:
    """Decimal-units (raw_return, alpha_return) for the closed window. Delegates
    to ``returns_from_frames`` so the harness shares forward-α math with the
    framework's analyzer (FR-012 + reconciliation invariant SC-004)."""
    if actual_holding_days < 1:
        return None
    end = (entry_date + timedelta(days=int(actual_holding_days * 1.5) + 7)).isoformat()
    stock = _cached_history(ticker, entry_date.isoformat(), end)
    bench = _cached_history(benchmark, entry_date.isoformat(), end)
    if stock.empty or bench.empty:
        return None
    raw, alpha, _ = returns_from_frames(
        stock, bench, entry_date.isoformat(), actual_holding_days, as_percent=False
    )
    if raw is None or alpha is None:
        return None
    return _to_decimal(raw), _to_decimal(alpha)
