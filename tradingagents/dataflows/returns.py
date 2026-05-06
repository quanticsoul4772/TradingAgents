"""Forward-return / alpha computation helpers — single source of truth.

This module owns the forward-α math. Three downstream consumers exist:

  - ``tradingagents.graph.trading_graph.fetch_returns`` — live propagate
    layer that fetches frames per-call and returns DECIMAL α with a
    truncated-window indicator. Wraps ``alpha_from_frames`` after fetching.

  - ``tradingagents.dataflows.price_cache.PriceCache.forward_alpha`` —
    batch-analysis cached-frame layer that returns PERCENT α with strict
    (None on partial-window) semantics. Wraps ``alpha_from_frames``.

  - ``scripts/analyze_backtest.py::_compute_returns`` — rendered-table
    layer that returns DECIMAL α with truncated-window semantics. Wraps
    ``alpha_from_frames``.

Each wrapper picks its own units (``as_percent``) and partial-window
behavior (``strict_window``); the math itself lives only here.

Prior to consolidation (2026-05-05) the math was inlined in three places
with subtly different partial-window semantics. The buffer-fix bug
documented in ``claudedocs/bear-bigram-artifact-check-2026-05-04.md``
was a symptom of this duplication — the "90d IC" was actually computed
over ~50d because ``fetch_returns`` returned partial windows silently.
The buffer fix widened the calendar buffer (commit ``24e009d``); this
refactor (commit pending) addresses the underlying duplication.
"""

from __future__ import annotations

import pandas as pd


def alpha_from_frames(
    stock_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    trade_date: str,
    holding_days: int,
    *,
    strict_window: bool = True,
    as_percent: bool = True,
) -> float | None:
    """Stock-minus-benchmark return over `holding_days` trading days starting
    from the first trading day on/after `trade_date`.

    Parameters
    ----------
    stock_df, bench_df
        yfinance-style price frames with a 'Close' column. Indexes are
        tz-normalized internally so callers may pass tz-aware frames.
    trade_date
        ISO date string (YYYY-MM-DD).
    holding_days
        Forward window in trading days.
    strict_window
        When True (default), returns None if the available forward window is
        shorter than ``holding_days``. When False, returns the truncated α
        over whatever window is available (matching the historical
        ``fetch_returns`` semantics — caller must check the actual window
        size separately if needed).
    as_percent
        When True (default), returns α as percent (e.g. 1.5 for 1.5%). When
        False, returns α as decimal (e.g. 0.015 for 1.5%).

    Returns
    -------
    α value, or None when frames don't have enough rows OR when
    ``strict_window=True`` and the partial-window check fails.
    """
    stock_slice, bench_slice = _slice_forward(stock_df, bench_df, trade_date)
    if len(stock_slice) < 2 or len(bench_slice) < 2:
        return None
    actual = min(holding_days, len(stock_slice) - 1, len(bench_slice) - 1)
    if strict_window and actual < holding_days:
        return None
    raw = float(
        (stock_slice["Close"].iloc[actual] - stock_slice["Close"].iloc[0])
        / stock_slice["Close"].iloc[0]
    )
    bench = float(
        (bench_slice["Close"].iloc[actual] - bench_slice["Close"].iloc[0])
        / bench_slice["Close"].iloc[0]
    )
    alpha = raw - bench
    return alpha * 100 if as_percent else alpha


def returns_from_frames(
    stock_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    trade_date: str,
    holding_days: int,
    *,
    as_percent: bool = False,
) -> tuple[float | None, float | None, int | None]:
    """Like ``alpha_from_frames`` but returns the raw and α components plus
    the actual holding window.

    Backwards-compatible support for callers that need all three values
    (the historical ``fetch_returns`` and ``analyze_backtest._compute_returns``
    shape). Always returns truncated α when partial — no strict-window flag
    here because the actual_days return value lets the caller decide.

    Returns
    -------
    (raw_return, alpha_return, actual_holding_days) — or (None, None, None)
    when frames don't have enough rows. Both returns are decimal by default
    (``as_percent=False``); pass ``as_percent=True`` for percent units.
    """
    stock_slice, bench_slice = _slice_forward(stock_df, bench_df, trade_date)
    if len(stock_slice) < 2 or len(bench_slice) < 2:
        return None, None, None
    actual = min(holding_days, len(stock_slice) - 1, len(bench_slice) - 1)
    raw = float(
        (stock_slice["Close"].iloc[actual] - stock_slice["Close"].iloc[0])
        / stock_slice["Close"].iloc[0]
    )
    bench = float(
        (bench_slice["Close"].iloc[actual] - bench_slice["Close"].iloc[0])
        / bench_slice["Close"].iloc[0]
    )
    alpha = raw - bench
    if as_percent:
        return raw * 100, alpha * 100, actual
    return raw, alpha, actual


def _slice_forward(
    stock_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    trade_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Slice both frames to rows on/after ``trade_date``.

    Real yfinance frames have a (possibly tz-aware) DatetimeIndex; the cached
    multi-date frames in ``analyze_backtest`` slice by date. The live
    ``fetch_returns`` path passes per-call frames already starting at
    ``trade_date`` and may use a non-datetime index (e.g. test fixtures using
    a ``RangeIndex``); for those we skip slicing and treat the whole frame
    as the forward window.
    """
    if not isinstance(stock_df.index, pd.DatetimeIndex):
        return stock_df, bench_df
    td = pd.Timestamp(trade_date)
    stock_idx = (
        stock_df.index.tz_localize(None) if stock_df.index.tz is not None else stock_df.index
    )
    bench_idx = (
        bench_df.index.tz_localize(None) if bench_df.index.tz is not None else bench_df.index
    )
    return stock_df.loc[stock_idx >= td], bench_df.loc[bench_idx >= td]
