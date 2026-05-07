"""Path C snapshot helper — capture analyst PT panel + recommendations
distribution at propagate time so future C-3-class retrospectives can
backfill historical contrarian signals from accumulated state logs.

Per `claudedocs/class-c3-analyst-pt-feasibility-2026-05-07.md` (PR #40):
yfinance has no historical PT panels (only current snapshot), so
retrospective C-3 backfill is structurally impossible without per-propagate
snapshot accumulation. This module captures the snapshot at propagate
time and writes it to `state["forward_catalyst"]["analyst_pt_snapshot"]`
when enabled.

Design decisions:
- Default-OFF (Constitution III T0 + FR-013 escape hatch). Zero behavior
  impact when disabled.
- LRU-cached per (ticker, process). Same pattern as spec 008 calendar_boost
  (PR #71-style yfinance integration).
- Graceful fallback on yfinance errors → returns None (does not raise).
- Snapshot includes BOTH analyst_price_targets dict AND a serialized
  recommendations rating-distribution snapshot (per PR #40 sibling
  signals).

Cost: zero LLM. ~50-200ms latency per propagate (per PR #40 + PR #65
empirical timings).

Backfill semantics: each propagate writes ONE snapshot row keyed by
(ticker, propagate_date). Over N propagates per ticker, an
operator gets N data points to compute deltas, percentiles, etc.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def _fetch_pt_snapshot_cached(ticker: str) -> dict[str, Any] | None:
    """Fetch analyst PT panel + recommendations DataFrame summary for a ticker.

    LRU-cached per process so repeated reads (e.g., during a backtest
    iteration) only hit yfinance once per ticker.

    Returns None if yfinance call fails OR ticker has no analyst data
    (e.g., ETFs return empty per PR #40 + PR #66 graceful-degradation
    pattern). Caller should treat None as "no data available."
    """
    try:
        import yfinance as yf
    except Exception as exc:  # noqa: BLE001
        logger.warning("analyst_pt_snapshot: yfinance import failed (%s)", exc)
        return None

    try:
        t = yf.Ticker(ticker)
        pt = t.analyst_price_targets
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "analyst_pt_snapshot: yfinance.analyst_price_targets failed for %s (%s)",
            ticker,
            exc,
        )
        return None

    if not pt:
        return None

    out: dict[str, Any] = {"analyst_price_targets": dict(pt)}

    # Also serialize recommendations rating-distribution snapshot
    try:
        recs = t.recommendations
        if recs is not None and hasattr(recs, "shape") and not recs.empty:
            out["recommendations"] = recs.to_dict("records")
        else:
            out["recommendations"] = None
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "analyst_pt_snapshot: yfinance.recommendations failed for %s (%s)",
            ticker,
            exc,
        )
        out["recommendations"] = None

    return out


def fetch_analyst_pt_snapshot(ticker: str) -> dict[str, Any] | None:
    """Public API. Returns the snapshot dict or None on failure / no data.

    Snapshot shape (when populated):
        {
            "analyst_price_targets": {
                "current": float, "high": float, "low": float,
                "mean": float, "median": float
            },
            "recommendations": [
                {"period": "0m", "strongBuy": int, "buy": int, ...},
                {"period": "-1m", ...},
                ...
            ] | None
        }
    """
    if not ticker or not isinstance(ticker, str):
        return None
    return _fetch_pt_snapshot_cached(ticker.upper())


def clear_cache() -> None:
    """Test helper — clears the LRU cache between test runs.

    Production code shouldn't call this; the cache is process-lifetime.
    """
    _fetch_pt_snapshot_cached.cache_clear()
