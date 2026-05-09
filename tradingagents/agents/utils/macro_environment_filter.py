"""Spec 012 Class 4 Macro-Environment Filter.

FIRST macro-environment-aware filter in the framework. Suppresses
Underweight/Sell commits to Hold when the VIX snapshot at the trade_date
is below threshold (default 18.0; risk-on environment empirically
correlates with the +28pp bear-side ticker_strong cohort
counter-trend failures).

Empirical motivation (per claudedocs/class4-macro-filter-retrospective-2026-05-09.md):
- Standalone gate (PR #193): bear-side n=8 fires at VIX < 18, discrim
  +24.07pp, hit 75%, net Δα +24.07pp at 21d
- Additive gate vs A3 (PR #193): mechanism-disjoint (A3 catches 0 of
  22 ticker_strong cohort by definition; Class 4 catches 6).
  +24.07pp incremental.
- Discriminator: VIX 30d Δ% — ticker_strong cohort committed bear
  when VIX rising +10.50% over 30d vs other-bear-cells +22.96%.

Mechanism class distinction: distinct from per-ticker price (A3) /
per-sector (Spec 004/006) / prose-density (Spec 003) / LLM-extracted
(Spec 007/008) / institutional flow (Spec X-1). FIRST cross-asset
macro filter.

Naming: "Spec 012" / "Class 4" = Spec 008 design doc mechanism
classification. NOT to be confused with C-4 institutional rotation =
Spec X-1 (bear-side mechanism survey numbering).

Pattern reuse: mirrors tradingagents/agents/utils/institutional_rotation_filter.py
(Spec X-1) for module structure + state annotation. Mirrors
scripts/class4_macro_retrospective.py for the data-fetch semantics
(single source of truth for VIX snapshot).

Read-only against state["trade_date"]. Adds yfinance fetch
(LRU-cached per process) per propagate when bear_mode != "off".
Zero LLM cost (Constitution III T0).
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Literal

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

_BULLISH_RATINGS = {"Buy", "Overweight"}
_BEARISH_RATINGS = {"Underweight", "Sell"}
_VALID_MODES = ("off", "shadow", "active")

_RATING_LINE_RE = re.compile(
    r"\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?(Buy|Overweight|Hold|Underweight|Sell)",
    re.IGNORECASE,
)


# ---- Public API -----------------------------------------------------------


@lru_cache(maxsize=128)
def _vix_snapshot(trade_date: str) -> float | None:
    """Fetch VIX close on or before trade_date via yfinance.

    Returns None on yfinance exception, empty data, or missing column.
    Same semantics as scripts/class4_macro_retrospective.py
    (single source of truth for the data fetch).
    """
    try:
        end = pd.Timestamp(trade_date) + pd.Timedelta(days=1)
        start = pd.Timestamp(trade_date) - pd.Timedelta(days=10)
        df = yf.Ticker("^VIX").history(start=start, end=end, auto_adjust=False)
        if df is None or not hasattr(df, "empty") or df.empty:
            return None
        if "Close" not in df.columns:
            return None
        df_idx = df.index.tz_localize(None) if df.index.tz else df.index
        mask = df_idx <= pd.Timestamp(trade_date)
        valid = df[mask]
        if valid.empty:
            return None
        return float(valid["Close"].iloc[-1])
    except Exception:
        return None


def should_suppress_bear(vix_snapshot: float | None, threshold: float) -> bool:
    """Pure function: should the bear-side filter fire?

    Returns True iff vix_snapshot is not None AND vix_snapshot <
    threshold (strict less-than per FR-002 / SC-006, matching Spec
    007 + Spec X-1 boundary discipline).
    """
    return vix_snapshot is not None and vix_snapshot < threshold


# ---- Internal helpers -----------------------------------------------------


def _parse_pre_rating(decision_markdown: str) -> str:
    """Extract the rating from the PM markdown. Defaults to 'Hold' if unparseable."""
    if not decision_markdown:
        return "Hold"
    m = _RATING_LINE_RE.search(decision_markdown)
    if m is None:
        return "Hold"
    word = m.group(1)
    return word[:1].upper() + word[1:].lower()


def _downgrade_to_hold(decision_markdown: str, pre_rating: str, annotation: dict) -> str:
    """Replace the rating line with Hold + append a [Class 4 macro filter] note."""
    note = (
        "\n\n---\n\n"
        f"**[Class 4 Macro-Environment filter]** Original rating "
        f"**{pre_rating}** overridden to **Hold**. VIX snapshot at "
        f"trade_date = {annotation['vix_snapshot']:.2f} (below threshold "
        f"{annotation['vix_threshold']:.2f}). Empirical pattern (PR #193): "
        f"bear-side ticker_strong cohort committed counter-trend bear in "
        f"low-VIX (risk-on) environments; suppressing the bear commit "
        f"recovers alpha (n=8 retrospective fires; +24.07pp net Δα at 21d)."
        "\n\n---\n"
    )
    pattern = re.compile(
        r"(\*?\*?Rating\*?\*?\s*[:\-]\s*\*?\*?)" + re.escape(pre_rating),
        re.IGNORECASE,
    )
    modified = pattern.sub(r"\g<1>Hold", decision_markdown, count=1)
    if modified == decision_markdown:
        modified = note + decision_markdown
    else:
        modified = modified + note
    return modified


# ---- Main filter function -------------------------------------------------


def evaluate_macro_environment(
    decision_markdown: str,
    state: dict,
    *,
    bear_mode: Literal["off", "shadow", "active"],
    vix_threshold: float,
) -> tuple[str, dict | None]:
    """Apply the Class 4 macro-environment filter to a PM decision.

    Returns ``(possibly_modified_decision_markdown, annotation_dict)``.
    ``annotation_dict`` is ``None`` when bear_mode == "off"
    (preserves backward compat with baseline state log shape).

    See ``specs/012-class-4-macro-filter/spec.md`` for the full contract.
    """
    if bear_mode not in _VALID_MODES:
        logger.warning("macro_environment: unknown bear_mode %r; defaulting to 'off'", bear_mode)
        bear_mode = "off"

    # Bear-side off → no annotation, no fetch, no overhead
    if bear_mode == "off":
        return decision_markdown, None

    pre_rating = _parse_pre_rating(decision_markdown)
    trade_date = state.get("trade_date", "")

    # Fetch with graceful degradation (FR-007)
    vix = _vix_snapshot(trade_date) if trade_date else None

    # Bear-side suppression decision
    would_fire_bear = should_suppress_bear(vix, vix_threshold) and pre_rating in _BEARISH_RATINGS
    fired_bear = would_fire_bear and bear_mode == "active"
    post_rating = "Hold" if fired_bear else pre_rating

    annotation = {
        "vix_snapshot": vix,
        "vix_threshold": vix_threshold,
        "bear_mode": bear_mode,
        "would_fire_bear": would_fire_bear,
        "fired_bear": fired_bear,
        "pre_rating": pre_rating,
        "post_rating": post_rating,
    }

    if fired_bear:
        modified = _downgrade_to_hold(decision_markdown, pre_rating, annotation)
    else:
        modified = decision_markdown

    return modified, annotation
