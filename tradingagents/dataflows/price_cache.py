"""PriceCache: batch yfinance fetching + alpha/momentum helpers.

Analysis scripts that operate over many (ticker, date) pairs hit the same
boilerplate: figure out the fetch window, pull each ticker's history once,
include the benchmark (SPY) too, then slice the cached frames per row.

Subtle bug surface eliminated by centralizing here:
- Date-padding inconsistencies (one script padded +14 days end, another +30)
- Forgetting to include the benchmark in the cache
- Forward window vs trailing window — same pad logic but applied differently

Usage:
    cache = PriceCache(["NVDA", "AAPL"], dates=["2026-01-30", ...], horizon_days=21)
    a = cache.alpha("NVDA", "2026-02-06", holding_days=21)
    m = cache.trailing_return("AAPL", "2026-03-13", lookback_days=30)
    df = cache.frame("NVDA")  # raw access if a script needs it

For the in-propagate momentum filter (single-ticker, single-date, no batch
context), use `tradingagents.agents.utils.momentum_filter.trailing_momentum_pct`
instead — it fetches live yfinance per call.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from tradingagents.dataflows.returns import alpha_from_frames

# Padding around the date span. _PRE pad ensures trailing-momentum lookups
# (e.g. 30d trailing) have data; _POST pad ensures forward-return lookups
# at the chosen horizon have enough trading days even after weekends/holidays.
# These were derived from the existing-script defaults — bumped slightly to
# cover all observed call sites uniformly.
_PRE_PAD_DAYS = 60
_POST_PAD_DAYS = 21  # added on top of horizon_days


class PriceCache:
    """Batch yfinance history cache + alpha/momentum helpers.

    Fetches each ticker once over the full span, then serves slices for
    per-(ticker, date) computations without re-hitting the network.
    """

    def __init__(
        self,
        tickers: Iterable[str],
        dates: Iterable[str],
        horizon_days: int = 21,
        benchmark: str = "SPY",
    ) -> None:
        self.benchmark = benchmark
        ticker_set = set(tickers)
        ticker_set.add(benchmark)
        date_list = list(dates)
        if not date_list:
            raise ValueError("PriceCache requires at least one date.")

        min_date = datetime.strptime(min(date_list), "%Y-%m-%d")
        max_date = datetime.strptime(max(date_list), "%Y-%m-%d")
        fetch_start = (min_date - timedelta(days=_PRE_PAD_DAYS)).strftime("%Y-%m-%d")
        fetch_end = (max_date + timedelta(days=horizon_days + _POST_PAD_DAYS)).strftime("%Y-%m-%d")

        self._cache: dict[str, pd.DataFrame] = {}
        for t in ticker_set:
            self._cache[t] = yf.Ticker(t).history(
                start=fetch_start, end=fetch_end, auto_adjust=False
            )

    def frame(self, ticker: str) -> pd.DataFrame:
        """Raw cached DataFrame for a ticker (empty if fetch failed)."""
        return self._cache.get(ticker, pd.DataFrame())

    def benchmark_frame(self) -> pd.DataFrame:
        return self._cache[self.benchmark]

    def alpha(
        self, ticker: str, trade_date: str, holding_days: int
    ) -> float | None:
        """Forward α of ticker vs benchmark over `holding_days` trading days
        starting at the first trading day on/after `trade_date`. None when
        forward window is unresolvable.
        """
        stock = self.frame(ticker)
        if stock.empty:
            return None
        return alpha_from_frames(stock, self.benchmark_frame(), trade_date, holding_days)

    def trailing_return(
        self, ticker: str, trade_date: str, lookback_days: int
    ) -> float | None:
        """% return of `ticker` over the `lookback_days` trading days BEFORE
        `trade_date`. No look-ahead. None when insufficient prior data.
        """
        df = self.frame(ticker)
        if df.empty:
            return None
        td = pd.Timestamp(trade_date)
        idx = df.index.tz_localize(None) if df.index.tz is not None else df.index
        past = df.loc[idx < td]
        if len(past) < lookback_days + 1:
            return None
        p_now = float(past["Close"].iloc[-1])
        p_then = float(past["Close"].iloc[-1 - lookback_days])
        return ((p_now - p_then) / p_then) * 100
