"""Mean-reversion suppression filter for Underweight / Sell commits.

Empirically motivated by experiment A3 (`scripts/uw_suppression_filter.py`):
historical UW commits cluster on tickers that were already deeply down in
the trailing 30 days, and those tickers tend to mean-revert bullishly over
the next 21d. A simple filter — suppress UW/Sell when ticker 30d momentum
is below a threshold — improved the in-sample UW bucket α from +1.97% to
+0.82% (n=16).

Usage in PortfolioManager: when config["uw_momentum_filter_threshold"] is
set (e.g. -5.0 for "down >5% in 30d"), ratings of Underweight or Sell are
overridden to Hold and the markdown decision is annotated with the reason.

Default: disabled (config value is None). Set in default_config.py or via
backtest --config-override.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

import yfinance as yf

from tradingagents.agents.utils.rating import parse_rating

logger = logging.getLogger(__name__)

_BEAR_RATINGS = {"Underweight", "Sell"}


def trailing_momentum_pct(ticker: str, trade_date: str, lookback_days: int = 30) -> float | None:
    """Return % change in ticker close over the lookback_days trading days
    BEFORE trade_date. Returns None if data is insufficient or fetch fails.
    No look-ahead — strictly uses prices before trade_date.
    """
    try:
        td = datetime.strptime(trade_date, "%Y-%m-%d")
        # Pull a generous window (lookback in trading days ≈ lookback*1.5 calendar days)
        # plus 7-day cushion for weekends/holidays at the edges.
        start = (td - timedelta(days=lookback_days * 2 + 7)).strftime("%Y-%m-%d")
        end = trade_date  # exclusive in yfinance
        df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
        if len(df) < lookback_days + 1:
            return None
        p_now = float(df["Close"].iloc[-1])
        p_then = float(df["Close"].iloc[-1 - lookback_days])
        return ((p_now - p_then) / p_then) * 100
    except Exception as e:
        logger.warning(f"momentum_filter: fetch failed for {ticker} @ {trade_date}: {e}")
        return None


def maybe_suppress_bear_rating(
    decision_markdown: str,
    ticker: str,
    trade_date: str,
    threshold_pct: float,
    lookback_days: int = 30,
) -> tuple[str, bool]:
    """Inspect the PM's decision markdown. If the extracted rating is
    Underweight or Sell AND the ticker's trailing momentum is below the
    threshold (e.g. -5.0 → "down more than 5% in 30d"), override the rating
    to Hold and annotate the markdown with the suppression reason.

    Returns (possibly_modified_markdown, suppressed_bool).
    """
    rating = parse_rating(decision_markdown, default="Hold")
    if rating not in _BEAR_RATINGS:
        return decision_markdown, False

    momentum = trailing_momentum_pct(ticker, trade_date, lookback_days)
    if momentum is None:
        # Don't fabricate suppression on missing data — leave decision intact.
        return decision_markdown, False

    if momentum >= threshold_pct:
        # Ticker not in mean-reversion zone; trust the bear call.
        return decision_markdown, False

    # Suppress: override to Hold + append reason.
    note = (
        f"\n\n---\n\n"
        f"**[A3 momentum filter]** Original rating **{rating}** overridden to **Hold**. "
        f"Ticker {ticker} trailing {lookback_days}d momentum is {momentum:+.2f}% "
        f"(threshold {threshold_pct:+.2f}%). Empirical pattern from the A3 retrospective: "
        f"framework UW/Sell commits on tickers already deeply down tend to be wrong "
        f"because forward 21d returns mean-revert bullishly. See "
        f"`claudedocs/uw-suppression-filter.md` for the in-sample data.\n\n"
        f"---\n"
    )
    # Replace the rating line. Both Research Manager and PM use "Rating: X" or
    # "**Rating**: X" patterns; we substitute conservatively.
    pattern = re.compile(
        r"(\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?)" + re.escape(rating), re.IGNORECASE
    )
    modified = pattern.sub(r"\1Hold", decision_markdown, count=1)
    if modified == decision_markdown:
        # Couldn't find the rating to substitute — fall back to prepending a note.
        modified = note + decision_markdown
    else:
        modified = modified + note
    return modified, True
