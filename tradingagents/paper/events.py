"""Event log entities. Schema: ``contracts/events_jsonl.md``."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    SKIP_CAP = "skip_cap"
    SKIP_CASH = "skip_cash"
    MARK = "mark"
    DATA_ANOMALY = "data_anomaly"
    STEP_SKIPPED_ALREADY_PROCESSED = "step_skipped_already_processed"


@dataclass
class Event:
    """One JSON line in the event log."""

    event_type: EventType
    portfolio_id: str
    policy_snapshot_hash: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d
