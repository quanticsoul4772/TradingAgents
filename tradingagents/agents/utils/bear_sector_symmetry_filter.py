"""Bear-sector-symmetry filter — suppress Underweight/Sell to Hold when the
ticker has outperformed its sector ETF by more than a configurable threshold
over the prior N trading days (counter-trend bear suppression).

Spec: ``specs/005-bear-sector-symmetry/`` (in particular
``contracts/filter_function.md`` for the public function contract and
``data-model.md`` for the BearSectorSymmetryAnnotation entity definition).

Sector-relative inverse of A3 (`tradingagents/agents/utils/momentum_filter.py`):
A3 fires when ticker is DOWN ≥5% absolute (mean-reversion zone for buyers);
spec 006 fires when ticker is UP relative to its sector (counter-trend zone
for sellers). The two filter conditions are nearly disjoint by construction.

Empirical motivation: ``claudedocs/sector-alpha-attribution-2026-05-06.md``
found 18 of 37 bearish commits in the 194-row corpus (48.6%) landed in
the ``ticker_strong`` cell with mean realized α-vs-SPY = +28.02% — a cohort
A3 misses entirely.

Reuses ``SECTOR_ETF_MAP`` + ``_etf_history`` from spec 004's module per
FR-004; new ``_ticker_history`` LRU cache for the ticker side per R-2.

Read-only against yfinance, deterministic given (ticker, trade_date,
threshold, lookback, mode), zero LLM cost.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yfinance as yf

# Reuse spec 004's mapping + ETF cache (FR-004, R-2). Single source of truth.
from tradingagents.agents.utils.sector_momentum_filter import (
    SECTOR_ETF_MAP,
    _etf_history,
    clear_etf_cache,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SECTOR_ETF_MAP",
    "_etf_history",
    "clear_etf_cache",
    "clear_ticker_cache",
    "maybe_suppress_bear_rating",
]

_BEARISH_RATINGS = {"Underweight", "Sell"}
_VALID_MODES = ("off", "shadow", "active")


# ---- Ticker history fetch (cached) ----------------------------------------


@lru_cache(maxsize=128)
def _ticker_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    """LRU-cached yfinance fetch per (ticker, start, end). Empty DataFrame on
    failure (caught + warning logged). Cache cleared via clear_ticker_cache()."""
    try:
        return yf.Ticker(ticker).history(start=start, end=end)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "bear_sector_symmetry_filter: yfinance fetch failed for %s [%s..%s] (%s)",
            ticker,
            start,
            end,
            exc,
        )
        return pd.DataFrame()


def clear_ticker_cache() -> None:
    """Clear the in-process ticker-history LRU cache. Useful for tests."""
    _ticker_history.cache_clear()


def _compute_30d_return_pct(
    frame: pd.DataFrame,
    lookback_days: int,
) -> float | None:
    """Return the prior-N-trading-day return from a price frame as a percent
    (e.g., +18.32). Returns None if the frame has fewer than `lookback_days+1`
    rows."""
    if frame is None or frame.empty:
        return None
    if len(frame) < lookback_days + 1:
        return None
    closes = frame["Close"]
    window = closes.iloc[-(lookback_days + 1) :]
    start_close = float(window.iloc[0])
    end_close = float(window.iloc[-1])
    if start_close == 0:
        return None
    return (end_close - start_close) / start_close * 100.0


def _compute_ticker_30d_return_pct(
    ticker: str,
    trade_date: str,
    lookback_days: int = 30,
    fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
) -> float | None:
    """Return the ticker's prior-N-trading-day return as a percent, or None if
    insufficient history. ``fetcher`` is the injection point for tests
    (default: the LRU-cached _ticker_history)."""
    if fetcher is None:
        fetcher = _ticker_history
    try:
        anchor = datetime.strptime(trade_date, "%Y-%m-%d").date()
    except ValueError:
        logger.warning("bear_sector_symmetry_filter: invalid trade_date %r", trade_date)
        return None
    start = (anchor - timedelta(days=int(lookback_days * 1.5) + 7)).isoformat()
    end = anchor.isoformat()
    frame = fetcher(ticker, start, end)
    return _compute_30d_return_pct(frame, lookback_days)


def _compute_etf_30d_return_pct_local(
    etf: str,
    trade_date: str,
    lookback_days: int = 30,
    fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
) -> float | None:
    """Return the ETF's prior-N-trading-day return as a percent. Uses spec
    004's `_etf_history` LRU cache by default (cache hit when both filters
    fetch the same ETF on the same date range)."""
    if fetcher is None:
        fetcher = _etf_history
    try:
        anchor = datetime.strptime(trade_date, "%Y-%m-%d").date()
    except ValueError:
        return None
    start = (anchor - timedelta(days=int(lookback_days * 1.5) + 7)).isoformat()
    end = anchor.isoformat()
    frame = fetcher(etf, start, end)
    return _compute_30d_return_pct(frame, lookback_days)


# ---- Annotation builder ---------------------------------------------------


def _empty_annotation(
    *,
    mode: str,
    pre_rating: str,
    threshold_pct: float | None,
    lookback_days: int,
    skipped: str,
) -> dict:
    """Build a default annotation dict for skipped/no-fire paths. All 13
    fields per contracts/annotation_schema.md are populated; the caller
    can override any field before returning."""
    return {
        "mode": mode,
        "sector": None,
        "etf": None,
        "ticker_30d_return_pct": None,
        "etf_30d_return_pct": None,
        "relative_strength_pct": None,
        "threshold_pct": threshold_pct,
        "lookback_days": lookback_days,
        "would_fire": False,
        "fired": False,
        "pre_rating": pre_rating,
        "post_rating": pre_rating,
        "skipped": skipped,
    }


# ---- Rating extraction (defensive; mirrors A3's pattern) ------------------


_RATING_LINE_RE = re.compile(
    r"\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?(Buy|Overweight|Hold|Underweight|Sell)",
    re.IGNORECASE,
)


def _parse_pre_rating(decision_markdown: str) -> str:
    """Extract the rating from the PM markdown. Defaults to 'Hold' if
    unparseable (defensive — matches A3's + spec 004's behavior)."""
    if not decision_markdown:
        return "Hold"
    m = _RATING_LINE_RE.search(decision_markdown)
    if m is None:
        return "Hold"
    word = m.group(1)
    return word[:1].upper() + word[1:].lower()  # normalize case to "Buy"/"Hold"/etc.


def _downgrade_to_hold(
    decision_markdown: str,
    pre_rating: str,
    annotation: dict,
) -> str:
    """Replace the rating line with Hold + append a [Bear-sector-symmetry filter]
    note. Mirrors A3's + spec 004's regex-replace pattern."""
    note = (
        "\n\n---\n\n"
        f"**[Bear-sector-symmetry filter]** Original rating **{pre_rating}** "
        f"overridden to **Hold**. Ticker {annotation['etf'] and 'in ' + annotation['sector']} "
        f"prior-{annotation['lookback_days']}d return is "
        f"{annotation['ticker_30d_return_pct']:+.2f}%, while the {annotation['sector']} "
        f"sector ETF ({annotation['etf']}) returned {annotation['etf_30d_return_pct']:+.2f}% "
        f"over the same window — relative-strength delta = "
        f"{annotation['relative_strength_pct']:+.2f}%, above the configured threshold "
        f"({annotation['threshold_pct']:+.2f}%). Empirical pattern: bearish commits on "
        f"tickers rallying vs their own sector tend to be wrong (counter-trend bear calls; "
        f"+28.02% mean α-vs-SPY across the n=18 ticker_strong-bear cohort identified in "
        f"`claudedocs/sector-alpha-attribution-2026-05-06.md`)."
        "\n\n---\n"
    )
    pattern = re.compile(
        r"(\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?)" + re.escape(pre_rating),
        re.IGNORECASE,
    )
    modified = pattern.sub(r"\g<1>Hold", decision_markdown, count=1)
    if modified == decision_markdown:
        # Couldn't substitute; prepend note
        modified = note + decision_markdown
    else:
        modified = modified + note
    return modified


# ---- Main filter function -------------------------------------------------


def maybe_suppress_bear_rating(
    decision_markdown: str,
    ticker: str,
    trade_date: str,
    *,
    threshold_pct: float | None,
    lookback_days: int = 30,
    mode: Literal["off", "shadow", "active"] = "off",
    sectors_cache_path: Path | None = None,
    etf_history_fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
    ticker_history_fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
    sector_lookup: Callable[[str], str] | None = None,
) -> tuple[str, dict]:
    """Apply the bear-sector-symmetry filter to a PM decision.

    Returns ``(possibly_modified_decision_markdown, annotation_dict)``.
    See ``specs/005-bear-sector-symmetry/contracts/filter_function.md``
    for the full contract.
    """
    # Normalize/validate mode
    if mode not in _VALID_MODES:
        logger.warning(
            "bear_sector_symmetry_filter: unknown mode %r; defaulting to 'off'",
            mode,
        )
        mode = "off"

    pre_rating = _parse_pre_rating(decision_markdown)

    # 1. Off mode
    if mode == "off":
        return decision_markdown, _empty_annotation(
            mode="off",
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="off",
        )

    # 2. Bearish-only check
    if pre_rating not in _BEARISH_RATINGS:
        return decision_markdown, _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="rating_not_bearish",
        )

    # 3. Threshold validation
    if threshold_pct is None:
        return decision_markdown, _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=None,
            lookback_days=lookback_days,
            skipped="off",
        )
    if threshold_pct < 0:
        logger.warning(
            "bear_sector_symmetry_filter: negative threshold_pct=%s rejected (must be >= 0)",
            threshold_pct,
        )
        return decision_markdown, _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="invalid_threshold",
        )

    # 4. Sector lookup
    if sector_lookup is None:
        if sectors_cache_path is None:
            sectors_cache_path = Path.home() / ".tradingagents" / "paper" / "sectors.json"
        from tradingagents.paper.sectors import get_sector  # local import per spec 004 pattern

        def sector_lookup(t: str) -> str:
            return get_sector(t, sectors_cache_path)

    try:
        sector = sector_lookup(ticker)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "bear_sector_symmetry_filter: sector lookup failed for %s (%s); skipped",
            ticker,
            exc,
        )
        ann = _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="unknown_sector",
        )
        return decision_markdown, ann
    if not sector or sector == "Unknown":
        ann = _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="unknown_sector",
        )
        return decision_markdown, ann

    # 5. ETF mapping
    etf = SECTOR_ETF_MAP.get(sector)
    if etf is None:
        ann = _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="no_etf_mapping",
        )
        ann["sector"] = sector
        return decision_markdown, ann

    # 6. Ticker return computation
    ticker_30d_return_pct = _compute_ticker_30d_return_pct(
        ticker, trade_date, lookback_days, fetcher=ticker_history_fetcher
    )
    if ticker_30d_return_pct is None:
        ann = _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="missing_ticker_data",
        )
        ann["sector"] = sector
        ann["etf"] = etf
        return decision_markdown, ann

    # 7. ETF return computation
    etf_30d_return_pct = _compute_etf_30d_return_pct_local(
        etf, trade_date, lookback_days, fetcher=etf_history_fetcher
    )
    if etf_30d_return_pct is None:
        ann = _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="missing_etf_data",
        )
        ann["sector"] = sector
        ann["etf"] = etf
        ann["ticker_30d_return_pct"] = ticker_30d_return_pct
        return decision_markdown, ann

    # 8. Relative-strength delta
    relative_strength_pct = ticker_30d_return_pct - etf_30d_return_pct

    # 9. Threshold check (strict greater-than per R-3)
    would_fire = relative_strength_pct > threshold_pct  # bearish already verified above

    annotation: dict[str, Any] = {
        "mode": mode,
        "sector": sector,
        "etf": etf,
        "ticker_30d_return_pct": ticker_30d_return_pct,
        "etf_30d_return_pct": etf_30d_return_pct,
        "relative_strength_pct": relative_strength_pct,
        "threshold_pct": threshold_pct,
        "lookback_days": lookback_days,
        "would_fire": would_fire,
        "fired": False,
        "pre_rating": pre_rating,
        "post_rating": pre_rating,
        "skipped": None,
    }

    # 10. Active-mode override
    if would_fire and mode == "active":
        decision_markdown = _downgrade_to_hold(decision_markdown, pre_rating, annotation)
        annotation["fired"] = True
        annotation["post_rating"] = "Hold"

    return decision_markdown, annotation
