"""Extract the 5-tier portfolio rating from the Portfolio Manager's decision.

The Portfolio Manager produces a typed ``PortfolioDecision`` via structured
output and renders it to markdown that always carries a ``**Rating**: X``
header (see :func:`tradingagents.agents.schemas.render_pm_decision`).  The
deterministic heuristic in :mod:`tradingagents.agents.utils.rating` is more
than sufficient to extract that rating; no extra LLM call is needed.

This module exists for backwards compatibility with callers that expect a
``SignalProcessor.process_signal(text)`` interface.

WC-10 (specs/108-wc-10-continuous-scalar-rating/): when wc_10_enabled=True,
the rendered Rating header is a signed float (e.g., "+0.4567") rather than
a 5-tier categorical. The :func:`extract_scalar_rating` function handles
that case; ``process_signal`` retains the 5-tier behavior for backward
compat.
"""

from __future__ import annotations

import re
from typing import Any

from tradingagents.agents.utils.rating import parse_rating

_SCALAR_RATING_RE = re.compile(r"\*\*Rating\*\*:\s*([+-]?\d+\.?\d*)")


def extract_scalar_rating(full_signal: str) -> float | None:
    """Extract a continuous scalar rating from PM markdown when wc_10_enabled.

    Returns None if no scalar rating found (caller should fall back to
    5-tier path or raise per FR-002).
    """
    if not full_signal:
        return None
    m = _SCALAR_RATING_RE.search(full_signal)
    if m is None:
        return None
    try:
        return float(m.group(1))
    except (ValueError, IndexError):
        return None


class SignalProcessor:
    """Read the 5-tier rating out of a Portfolio Manager decision."""

    def __init__(self, quick_thinking_llm: Any = None):
        # The LLM argument is accepted for backwards compatibility but no
        # longer used: the PM's structured output guarantees the rating is
        # parseable from the rendered markdown without a second LLM call.
        self.quick_thinking_llm = quick_thinking_llm

    def process_signal(self, full_signal: str) -> str:
        """Return one of Buy / Overweight / Hold / Underweight / Sell."""
        return parse_rating(full_signal)
