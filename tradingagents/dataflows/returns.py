"""Forward-return / alpha computation helpers for backtest analysis.

The full graph layer's `fetch_returns()` (in `tradingagents/graph/trading_graph.py`)
fetches from yfinance per-call, which is the right shape for live propagation
but wasteful for batch analysis where the same ticker history gets sliced for
many trade dates. This module is the cached-frame variant: callers fetch each
ticker's history once, then call `alpha_from_frames` per (trade_date, horizon)
without hitting the network again.

Used by all post-hoc analysis scripts (horizon_sweep, identify_hold_extremes,
bear_side_per_ticker, uw_suppression_filter, diagnose_uw_quality).
"""

from __future__ import annotations

import pandas as pd


def alpha_from_frames(
    stock_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    trade_date: str,
    holding_days: int,
) -> float | None:
    """% return of stock minus benchmark over `holding_days` trading days
    starting from the first trading day on/after `trade_date`.

    Returns None when either frame doesn't have enough forward data —
    callers should treat that as "horizon unresolved" rather than fabricate
    a partial-window result.

    Indexes are tz-normalized internally so callers can pass tz-aware
    yfinance frames without preprocessing.
    """
    td = pd.Timestamp(trade_date)
    stock_idx = (
        stock_df.index.tz_localize(None) if stock_df.index.tz is not None else stock_df.index
    )
    bench_idx = (
        bench_df.index.tz_localize(None) if bench_df.index.tz is not None else bench_df.index
    )
    stock_slice = stock_df.loc[stock_idx >= td]
    bench_slice = bench_df.loc[bench_idx >= td]
    if len(stock_slice) < 2 or len(bench_slice) < 2:
        return None
    actual = min(holding_days, len(stock_slice) - 1, len(bench_slice) - 1)
    if actual < holding_days:
        return None
    raw = float(
        (stock_slice["Close"].iloc[actual] - stock_slice["Close"].iloc[0])
        / stock_slice["Close"].iloc[0]
    )
    bench = float(
        (bench_slice["Close"].iloc[actual] - bench_slice["Close"].iloc[0])
        / bench_slice["Close"].iloc[0]
    )
    return (raw - bench) * 100
