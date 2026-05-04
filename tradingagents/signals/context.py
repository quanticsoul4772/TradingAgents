"""Per-propagate context for transparent cache instrumentation.

Spec 002 FR-003 says every analyst tool call invoked during a backtest MUST
write its computed value to the cache transparently. The hook point is
``route_to_vendor`` in ``dataflows/interface.py`` — but route_to_vendor's
positional args differ per tool (some take ticker first, some take date
first, some take neither). Walking the args at the dispatch site is brittle.

Instead, the propagate sets a ``(ticker, trade_date)`` context once at the
start of a run; route_to_vendor reads it after a successful dispatch and
writes the computed value to the cache using that context. ContextVar gives
us thread-safe / async-safe storage without globals.

Tools called outside a propagate (e.g., in unit tests or scripts) see
``get_propagate_context() is None`` and the cache write is skipped — no
spurious rows.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TypedDict


class PropagateContext(TypedDict):
    """The (ticker, trade_date) tuple in scope for the current propagate."""

    ticker: str
    trade_date: str


_current: ContextVar[PropagateContext | None] = ContextVar(
    "tradingagents_propagate_context", default=None
)


@contextmanager
def propagate_context(ticker: str, trade_date: str) -> Iterator[None]:
    """Set the current ticker + trade_date for the duration of a propagate.

    Used by ``TradingAgentsGraph.propagate``. Tool dispatchers inside the
    pipeline can read the context via ``get_propagate_context()``. The
    context is reset on exit (including exceptions).
    """
    ctx: PropagateContext = {"ticker": ticker, "trade_date": trade_date}
    token = _current.set(ctx)
    try:
        yield
    finally:
        _current.reset(token)


def get_propagate_context() -> PropagateContext | None:
    """Return the current propagate context, or None if not in a propagate."""
    return _current.get()
