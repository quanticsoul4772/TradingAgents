"""Sector-baseline pool aggregator for the contrarian-gate fallback path.

Spec: ``specs/003-sector-baseline-gate/`` (in particular
``contracts/sector_pool_function.md`` for the public function contract and
``data-model.md`` for the SectorPool entity definition).

When the spec 003 contrarian gate evaluates a ticker whose per-ticker history
is below the FR-004 N>=20 floor, it falls back to a pool aggregated across
all same-sector tickers. This module owns that aggregation.

**Data source**: the same signal cache (``~/.tradingagents/signals/cache.db``)
that the per-ticker baseline reads from. Aggregation happens by querying all
cache rows for a given signal_id, then filtering by sector (via
``tradingagents/paper/sectors.py::get_sector``) and by strict-prior date
(< before_date — prevents within-step look-ahead when multiple same-sector
tickers run in the same daily_signals invocation).

Read-only, deterministic, zero LLM cost.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SectorPool:
    """Aggregated featurizer-applied values for one sector at one moment.

    Frozen dataclass — once aggregated, the pool is read-only. Use
    ``aggregate_sector_pool`` to construct.
    """

    sector: str
    before_date: date
    values: list[float] = field(default_factory=list)
    n: int = 0
    contributors: dict[str, int] = field(default_factory=dict)


def aggregate_sector_pool(
    sector: str,
    before_date: date,
    *,
    sectors_cache_path: Path,
    signal_id: str,
    feature_callable: Callable[[str], float],
    cache_path: Path | None = None,
    sector_lookup: Callable[[str], str] | None = None,
) -> SectorPool:
    """Aggregate ``feature_callable(prose)`` values across all cached rows
    for ``signal_id`` whose ticker maps to ``sector``, strictly before
    ``before_date``.

    See ``specs/003-sector-baseline-gate/contracts/sector_pool_function.md``
    for the full contract.

    Returns an empty pool for ``sector == "Unknown"`` or empty string per R-4.
    Defaults the per-ticker sector lookup to
    ``tradingagents.paper.sectors.get_sector(ticker, sectors_cache_path)``;
    callers may inject a custom callable for tests.
    """
    if not sector or sector == "Unknown":
        return SectorPool(sector=sector, before_date=before_date)

    if sector_lookup is None:
        from tradingagents.paper.sectors import get_sector  # local to avoid hard dep at import

        def sector_lookup(ticker: str) -> str:
            return get_sector(ticker, sectors_cache_path)

    # Pull all cache rows for this signal across all tickers.
    try:
        from tradingagents.signals.cache import query_all  # local to avoid heavy import at startup

        rows = query_all(signal_id=signal_id, ticker=None, cache_path=cache_path)
    except Exception as exc:
        logger.warning(
            "Sector-pool aggregation: cache query failed for signal_id=%s (%s); empty pool returned",
            signal_id,
            exc,
        )
        return SectorPool(sector=sector, before_date=before_date)

    cutoff_iso = before_date.isoformat()
    # Cache sector-lookup results to avoid repeat yfinance hits on the same ticker.
    sector_cache: dict[str, str] = {}
    values: list[float] = []
    contributors: dict[str, int] = {}

    # Sort rows for deterministic iteration: by ticker, then date.
    for row in sorted(rows, key=lambda r: (r.get("ticker") or "", r.get("date") or "")):
        ticker = row.get("ticker") or ""
        row_date = row.get("date") or ""
        prose = row.get("value")

        if not ticker or not row_date or not prose or not isinstance(prose, str):
            continue
        # Strict-prior: exclude same-day and future observations
        if row_date >= cutoff_iso:
            continue

        if ticker not in sector_cache:
            try:
                sector_cache[ticker] = sector_lookup(ticker)
            except Exception as exc:
                logger.warning(
                    "Sector-pool aggregation: sector lookup failed for %s (%s); ticker excluded",
                    ticker,
                    exc,
                )
                sector_cache[ticker] = "Unknown"
        if sector_cache[ticker] != sector:
            continue

        try:
            value = float(feature_callable(prose))
        except Exception as exc:
            logger.warning(
                "Sector-pool aggregation: feature_callable raised on %s/%s (%s); observation skipped",
                ticker,
                row_date,
                exc,
            )
            continue

        values.append(value)
        contributors[ticker] = contributors.get(ticker, 0) + 1

    return SectorPool(
        sector=sector,
        before_date=before_date,
        values=values,
        n=len(values),
        contributors=contributors,
    )
