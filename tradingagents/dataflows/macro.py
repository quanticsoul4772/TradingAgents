"""Macro / regime signals — VIX level + change, sector ETF relative strength.

Per docs/SIGNALS.md P1 priorities:
- VIX is the regime classifier (extends A3 momentum filter from
  ticker-only to ticker+regime context — addresses Q4 mean-reversion
  finding directly).
- Sector ETF relative strength distinguishes stock-specific bear case
  from sector-wide selloff.

All data via yfinance — no new API key required.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import yfinance as yf

from .stockstats_utils import yf_retry

# Sector → SPDR ETF ticker mapping. yfinance Ticker.info["sector"] returns
# normalized sector names; this maps to the corresponding SPDR Select Sector ETF.
SECTOR_ETF: dict[str, str] = {
    "Technology": "XLK",
    "Information Technology": "XLK",
    "Energy": "XLE",
    "Financial Services": "XLF",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Health Care": "XLV",
    "Industrials": "XLI",
    "Consumer Cyclical": "XLY",
    "Consumer Discretionary": "XLY",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
    "Materials": "XLB",
    "Communication Services": "XLC",
}


def get_vix(
    curr_date: str,
    lookback_days: int = 30,
) -> str:
    """Current VIX level + N-day change. Markdown-formatted summary.

    VIX > 25 → fear regime (mean-reversion bullish bias plays out).
    VIX < 15 → complacency (potential bull-trap regime).
    Rapid VIX rise during ticker drawdown = the exact mean-reversion-bull
    regime Q4's per-ticker analysis identified as where UW commits fail.
    """
    try:
        end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=lookback_days * 2 + 7)
        vix = yf_retry(
            lambda: yf.Ticker("^VIX").history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                auto_adjust=False,
            )
        )
        if vix is None or vix.empty:
            return f"No VIX data for {curr_date}"

        current = float(vix["Close"].iloc[-1])
        if len(vix) > lookback_days:
            prior = float(vix["Close"].iloc[-1 - lookback_days])
            change_pct = ((current - prior) / prior) * 100
        else:
            prior = None
            change_pct = None

        # Regime classification
        if current > 25:
            regime = "fear (VIX > 25)"
        elif current > 20:
            regime = "elevated (20 < VIX <= 25)"
        elif current < 15:
            regime = "complacency (VIX < 15)"
        else:
            regime = "neutral (15 <= VIX <= 20)"

        lines = [
            f"# VIX (CBOE Volatility Index) as of {curr_date}",
            "",
            f"Current level: {current:.2f}",
            f"Regime: {regime}",
        ]
        if prior is not None and change_pct is not None:
            direction = "up" if change_pct > 0 else "down"
            lines.append(
                f"{lookback_days}-day change: {change_pct:+.2f}% (was {prior:.2f}, now {current:.2f}, trending {direction})"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"Error retrieving VIX: {e}"


def get_sector_etf_strength(
    ticker: str,
    curr_date: str,
    lookback_days: int = 30,
) -> str:
    """Ticker performance vs its sector ETF over the trailing N days.

    Output: relative strength (ticker_return - sector_etf_return) for
    distinguishing stock-specific moves from sector-wide moves. Q4
    showed UW commits fail when broad sector regime is bullish — this
    signal lets the framework see the sector context directly.

    Looks up the sector via Ticker.info["sector"] then maps to the
    corresponding SPDR Select Sector ETF (XLK, XLE, etc.).

    Short-circuits when the ticker is itself a known sector ETF —
    yfinance's Ticker.info call 404s on ETFs (no fundamentals data) and
    the comparison would be self-referential anyway. Without this guard
    every Phase D ETF backtest run prints an HTTP 404 from yfinance
    internals (non-fatal but noisy).
    """
    ticker_upper = ticker.upper()
    if ticker_upper in set(SECTOR_ETF.values()):
        return (
            f"'{ticker_upper}' is itself a sector ETF; relative-strength comparison "
            f"vs its own sector is not meaningful. Use ticker-vs-SPY or ticker-vs-other-sector instead."
        )

    try:
        ticker_obj = yf.Ticker(ticker_upper)
        info = yf_retry(lambda: ticker_obj.info)
        sector = info.get("sector") if info else None
        if not sector:
            return f"No sector classification found for '{ticker}'"

        etf = SECTOR_ETF.get(sector)
        if not etf:
            return f"No SPDR sector ETF mapping for sector '{sector}' (ticker {ticker})"

        end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=lookback_days * 2 + 7)

        ticker_hist = yf_retry(
            lambda: ticker_obj.history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                auto_adjust=False,
            )
        )
        etf_hist = yf_retry(
            lambda: yf.Ticker(etf).history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                auto_adjust=False,
            )
        )

        if ticker_hist is None or ticker_hist.empty or etf_hist is None or etf_hist.empty:
            return f"Insufficient price data to compute relative strength for {ticker} vs {etf}"

        if len(ticker_hist) < lookback_days + 1 or len(etf_hist) < lookback_days + 1:
            return f"Lookback window too short for {ticker} vs {etf}"

        # Trailing N-day returns (no look-ahead — uses prices up to curr_date)
        t_now = float(ticker_hist["Close"].iloc[-1])
        t_then = float(ticker_hist["Close"].iloc[-1 - lookback_days])
        ticker_ret = ((t_now - t_then) / t_then) * 100

        e_now = float(etf_hist["Close"].iloc[-1])
        e_then = float(etf_hist["Close"].iloc[-1 - lookback_days])
        etf_ret = ((e_now - e_then) / e_then) * 100

        rel_strength = ticker_ret - etf_ret

        if rel_strength > 5:
            interp = f"{ticker} significantly outperforming sector ({etf})"
        elif rel_strength > 0:
            interp = f"{ticker} modestly outperforming sector ({etf})"
        elif rel_strength > -5:
            interp = f"{ticker} modestly underperforming sector ({etf})"
        else:
            interp = f"{ticker} significantly underperforming sector ({etf})"

        return "\n".join(
            [
                f"# Sector Relative Strength: {ticker.upper()} vs {etf} ({sector})",
                "",
                f"As of {curr_date}, trailing {lookback_days} days:",
                f"  {ticker.upper()} return: {ticker_ret:+.2f}%",
                f"  {etf} return:           {etf_ret:+.2f}%",
                f"  Relative strength:      {rel_strength:+.2f}pp",
                "",
                interp,
            ]
        )

    except Exception as e:
        return f"Error computing sector ETF strength for {ticker}: {e}"
