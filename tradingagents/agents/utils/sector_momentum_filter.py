"""Sector-momentum filter — suppress Buy/Overweight to Hold when the ticker's
sector ETF is in mean-reversion zone (down more than a threshold over the
prior N trading days).

Spec: ``specs/004-sector-momentum-filter/`` (in particular
``contracts/filter_function.md`` for the public function contract and
``data-model.md`` for the SectorMomentumAnnotation entity definition).

Analogous to the A3 momentum filter in ``momentum_filter.py`` but operating
at SECTOR level instead of per-ticker. Empirical motivation:
``claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md``
showed the SC-003 Financials losers came from sector-rotation — a mechanism
neither A3 nor spec 003/003.5 catches.

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

logger = logging.getLogger(__name__)

# 11-entry SPDR sector-ETF mapping per FR-004 + R-10. Accepts both
# yfinance-canonical names ("Financial Services") and GICS-canonical
# names ("Financials") — both keys map to the same ETF symbol. Sectors
# yfinance reports outside this table cause skipped="no_etf_mapping".
SECTOR_ETF_MAP: dict[str, str] = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Consumer Cyclical": "XLY",
    "Consumer Discretionary": "XLY",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Communication Services": "XLC",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Basic Materials": "XLB",
    "Materials": "XLB",
}

_BULLISH_RATINGS = {"Buy", "Overweight"}
_VALID_MODES = ("off", "shadow", "active")


# ---- ETF history fetch (cached) -------------------------------------------


@lru_cache(maxsize=64)
def _etf_history(etf: str, start: str, end: str) -> pd.DataFrame:
    """LRU-cached yfinance fetch per (etf, start, end). Empty DataFrame on
    failure (caught + warning logged). Cache cleared via clear_etf_cache()."""
    try:
        return yf.Ticker(etf).history(start=start, end=end)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "sector_momentum_filter: yfinance fetch failed for %s [%s..%s] (%s)",
            etf,
            start,
            end,
            exc,
        )
        return pd.DataFrame()


def clear_etf_cache() -> None:
    """Clear the in-process ETF-history LRU cache. Useful for tests."""
    _etf_history.cache_clear()


def _compute_etf_30d_return_pct(
    etf: str,
    trade_date: str,
    lookback_days: int = 30,
    fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
) -> float | None:
    """Return the ETF's prior-N-trading-day return as a percent (e.g., -8.32),
    or None if insufficient history. ``fetcher`` is the injection point for
    tests (default: the LRU-cached _etf_history)."""
    if fetcher is None:
        fetcher = _etf_history
    try:
        anchor = datetime.strptime(trade_date, "%Y-%m-%d").date()
    except ValueError:
        logger.warning("sector_momentum_filter: invalid trade_date %r", trade_date)
        return None
    # Buffer: lookback * 1.5 + 7 calendar days covers weekends/holidays
    start = (anchor - timedelta(days=int(lookback_days * 1.5) + 7)).isoformat()
    end = anchor.isoformat()
    frame = fetcher(etf, start, end)
    if frame is None or frame.empty:
        return None
    if len(frame) < lookback_days + 1:
        return None
    closes = frame["Close"]
    # Take the most recent (lookback_days + 1) rows so the window ends at the
    # most recent close strictly before trade_date
    window = closes.iloc[-(lookback_days + 1) :]
    start_close = float(window.iloc[0])
    end_close = float(window.iloc[-1])
    if start_close == 0:
        return None
    return (end_close - start_close) / start_close * 100.0


# ---- Annotation builder ---------------------------------------------------


def _empty_annotation(
    *,
    mode: str,
    pre_rating: str,
    threshold_pct: float | None,
    lookback_days: int,
    skipped: str,
) -> dict:
    """Build a default annotation dict for skipped/no-fire paths.

    All 11 fields per contracts/annotation_schema.md are populated; the
    caller can override any field before returning.
    """
    return {
        "mode": mode,
        "sector": None,
        "etf": None,
        "etf_30d_return_pct": None,
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
    unparseable (defensive — matches A3's behavior)."""
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
    """Replace the rating line with Hold + append a [Sector-momentum filter]
    note. Mirrors A3's regex-replace pattern."""
    note = (
        "\n\n---\n\n"
        f"**[Sector-momentum filter]** Original rating **{pre_rating}** "
        f"overridden to **Hold**. The {annotation['sector']} sector ETF "
        f"({annotation['etf']}) is down "
        f"{annotation['etf_30d_return_pct']:.2f}% over the prior "
        f"{annotation['lookback_days']} trading days, below the configured "
        f"threshold ({annotation['threshold_pct']:.2f}%). Empirical pattern: "
        f"sector-rotation losses where the ticker isn't anomalous within "
        f"itself but the entire sector is down (mechanism distinct from the "
        f"within-ticker bull-prose mean-reversion that spec 003/003.5 catch). "
        f"See `claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md`."
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


def maybe_suppress_bull_rating(
    decision_markdown: str,
    ticker: str,
    trade_date: str,
    *,
    threshold_pct: float | None,
    lookback_days: int = 30,
    mode: Literal["off", "shadow", "active"] = "off",
    sectors_cache_path: Path | None = None,
    etf_history_fetcher: Callable[[str, str, str], pd.DataFrame] | None = None,
    sector_lookup: Callable[[str], str] | None = None,
) -> tuple[str, dict]:
    """Apply the sector-momentum filter to a PM decision.

    Returns ``(possibly_modified_decision_markdown, annotation_dict)``.
    See ``specs/004-sector-momentum-filter/contracts/filter_function.md``
    for the full contract.
    """
    # Normalize/validate mode
    if mode not in _VALID_MODES:
        logger.warning("sector_momentum_filter: unknown mode %r; defaulting to 'off'", mode)
        mode = "off"  # type: ignore[assignment]

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

    # 2. Bullish-only check
    if pre_rating not in _BULLISH_RATINGS:
        return decision_markdown, _empty_annotation(
            mode=mode,
            pre_rating=pre_rating,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            skipped="rating_not_bullish",
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
    if threshold_pct > 0:
        logger.warning(
            "sector_momentum_filter: positive threshold_pct=%s rejected (must be <= 0)",
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
        from tradingagents.paper.sectors import get_sector  # local import per spec 003.5 pattern

        def sector_lookup(t: str) -> str:
            return get_sector(t, sectors_cache_path)  # type: ignore[arg-type]

    try:
        sector = sector_lookup(ticker)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "sector_momentum_filter: sector lookup failed for %s (%s); skipped", ticker, exc
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

    # 6. ETF return computation
    etf_30d_return_pct = _compute_etf_30d_return_pct(
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
        return decision_markdown, ann

    # 7-8. Threshold check (strict less-than per R-3)
    would_fire = etf_30d_return_pct < threshold_pct  # bullish already verified above

    annotation: dict[str, Any] = {
        "mode": mode,
        "sector": sector,
        "etf": etf,
        "etf_30d_return_pct": etf_30d_return_pct,
        "threshold_pct": threshold_pct,
        "lookback_days": lookback_days,
        "would_fire": would_fire,
        "fired": False,
        "pre_rating": pre_rating,
        "post_rating": pre_rating,
        "skipped": None,
    }

    # 9. Active-mode override
    if would_fire and mode == "active":
        decision_markdown = _downgrade_to_hold(decision_markdown, pre_rating, annotation)
        annotation["fired"] = True
        annotation["post_rating"] = "Hold"

    return decision_markdown, annotation
