"""Paper-trading harness — deterministic position-keeping simulator on top of
``scripts/daily_signals.py``. Spec: ``specs/002-paper-trading-harness/``.
"""

from tradingagents.paper.engine import PaperTradingEngine, StepResult
from tradingagents.paper.errors import PortfolioStateError
from tradingagents.paper.events import Event, EventType
from tradingagents.paper.policy import (
    DefaultPolicy,
    EntryDecision,
    ExitDecision,
    PolicySnapshot,
    policy_snapshot_hash,
)
from tradingagents.paper.portfolio import (
    ClosedPosition,
    EquityPoint,
    Portfolio,
    Position,
)

__all__ = [
    "ClosedPosition",
    "DefaultPolicy",
    "EntryDecision",
    "EquityPoint",
    "Event",
    "EventType",
    "ExitDecision",
    "PaperTradingEngine",
    "PolicySnapshot",
    "Portfolio",
    "PortfolioStateError",
    "Position",
    "StepResult",
    "policy_snapshot_hash",
]
