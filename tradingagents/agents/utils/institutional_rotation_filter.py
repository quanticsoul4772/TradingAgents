"""Spec X-1 C-4 Institutional Rotation Filter.

FIRST quantitative-flow bear-side filter. Suppresses Underweight/Sell
commits to Hold when top 10 institutional holders' net pctChange
rotation (from yfinance.Ticker(t).institutional_holders) falls below
a configurable outflow threshold (default -5%).

Empirical motivation (per claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md
+ claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md):
- Standalone gate (PR #75): bear-side n=12, discrim +10.29pp, hit 75.0%,
  net Δα +5.41pp at T_outflow=0.05
- Additive gate vs Spec 007 bear (PR #77): +8.06pp Δα improvement,
  +69.23pp hit improvement on union; C-4 catches 11 bearish commits
  Spec 007 entirely misses

Mechanism class distinction: Spec 007 bear is LLM-extracted semantic
reasoning; C-4 is institutional ownership rotation (quantitative 13F
flow). LITERALLY different signal sources.

Pattern reuse: mirrors tradingagents/agents/utils/forward_catalyst_filter.py
(Spec 007) for module structure + state annotation; mirrors
scripts/forward_catalyst_class4_retrospective.py for the data-fetch
semantics (single source of truth).

Read-only against state["company_of_interest"]. Adds yfinance fetch
(LRU-cached per process) per propagate when at least one mode != "off".
Zero LLM cost (Constitution III T0).
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Literal

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
def _fetch_institutional_rotation(ticker: str) -> float | None:
    """Fetch sum(pctChange) across top 10 institutional holders.

    Returns None when yfinance returns None, empty DataFrame, missing
    pctChange column, or raises an exception. Mirrors the same
    semantics as scripts/forward_catalyst_class4_retrospective.py
    (single source of truth for the data fetch).
    """
    try:
        ih = yf.Ticker(ticker).institutional_holders
        if ih is None or not hasattr(ih, "empty") or ih.empty:
            return None
        if "pctChange" not in ih.columns:
            return None
        top10 = ih.head(10)
        return float(top10["pctChange"].fillna(0).sum())
    except Exception:
        return None


def should_suppress_bear(net_rotation: float | None, threshold: float) -> bool:
    """Pure function: should the bear-side filter fire?

    Returns True iff net_rotation is not None AND net_rotation <
    -threshold (strict less-than per FR-005 / SC-002, matching Spec
    007 SC-002 boundary discipline).
    """
    return net_rotation is not None and net_rotation < -threshold


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
    """Replace the rating line with Hold + append a [C-4 filter] note."""
    note = (
        "\n\n---\n\n"
        f"**[C-4 Institutional Rotation filter]** Original rating "
        f"**{pre_rating}** overridden to **Hold**. Top 10 institutional "
        f"holders' net pctChange rotation = "
        f"{annotation['net_rotation_pct']:.4f} (below outflow threshold "
        f"-{annotation['outflow_threshold']:.4f}). Empirical pattern "
        f"(PR #75 + #77): institutional outflows tend to occur AFTER "
        f"price moves; PM picks UW chasing the move; suppressing the bear "
        f"commit recovers alpha (n=12 standalone net Δα +5.41pp; +8.06pp "
        f"additive vs Spec 007 bear)."
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


def evaluate_institutional_rotation(
    decision_markdown: str,
    state: dict,
    *,
    bear_mode: Literal["off", "shadow", "active"],
    bull_mode: Literal["off", "shadow", "active"],
    outflow_threshold: float,
) -> tuple[str, dict | None]:
    """Apply the C-4 institutional rotation filter to a PM decision.

    Returns ``(possibly_modified_decision_markdown, annotation_dict)``.
    ``annotation_dict`` is ``None`` when both modes are "off" (FR-011 —
    preserves backward compat with Spec 007 baseline state log shape).

    See ``specs/091-c4-institutional-rotation/contracts/institutional_rotation_filter.md``
    for the full contract.
    """
    # Normalize modes
    if bear_mode not in _VALID_MODES:
        logger.warning(
            "institutional_rotation: unknown bear_mode %r; defaulting to 'off'", bear_mode
        )
        bear_mode = "off"
    if bull_mode not in _VALID_MODES:
        logger.warning(
            "institutional_rotation: unknown bull_mode %r; defaulting to 'off'", bull_mode
        )
        bull_mode = "off"

    # FR-011: both modes off → no annotation, no fetch, no overhead
    if bear_mode == "off" and bull_mode == "off":
        return decision_markdown, None

    pre_rating = _parse_pre_rating(decision_markdown)
    ticker = state.get("company_of_interest", "")

    # Fetch with graceful degradation (FR-013)
    net_rotation = _fetch_institutional_rotation(ticker) if ticker else None

    # Bear-side suppression decision
    would_fire_bear = (
        should_suppress_bear(net_rotation, outflow_threshold) and pre_rating in _BEARISH_RATINGS
    )
    fired_bear = would_fire_bear and bear_mode == "active"
    post_rating = "Hold" if fired_bear else pre_rating

    annotation = {
        "net_rotation_pct": net_rotation,
        "outflow_threshold": outflow_threshold,
        "bear_mode": bear_mode,
        "bull_mode": bull_mode,
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
