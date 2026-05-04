"""Signal registry — append-only JSONL of SignalDefinition snapshots.

Each line is a complete SignalDefinition snapshot. State mutations append a
new line rather than rewriting; the latest line per signal_id is the current
state. This is the source of truth for which signals exist + their state.

Per spec 002 FR-001 / FR-005 / FR-014. Phase 0 implements the storage layer
+ basic state-transition append; promotion / demotion / metric updates land
in Phase 1+.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tradingagents.signals.paths import get_registry_path

logger = logging.getLogger(__name__)


# Signal lifecycle states per docs/SIGNAL_LIFECYCLE.md "Signal lifecycle states".
VALID_STATES = ("candidate", "experimental", "production", "deprecated", "archived")


@dataclass
class StateTransition:
    """One state-change event in a SignalDefinition's history."""

    timestamp: str  # ISO 8601 UTC
    from_state: str | None
    to_state: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason": self.reason,
        }


@dataclass
class SignalDefinition:
    """One row in the signal registry. Snapshots are append-only.

    Fields per spec 002 FR-001. ``metrics`` is populated by the Phase 1
    evaluation harness; ``weight`` by Phase 3 reweight aggregator. Phase 0
    just records the definitional fields + state.
    """

    signal_id: str
    name: str
    fetcher: str  # dotted Python path to the fetcher
    inputs: list[str]  # argument names (e.g. ["ticker", "curr_date"])
    output_type: str  # "markdown" / "float" / "dict" / etc.
    horizon_days: int  # target prediction horizon (typically 21)
    introduced: str  # ISO 8601 UTC timestamp of first registration
    state: str  # one of VALID_STATES
    state_history: list[StateTransition] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    weight: float | None = None
    fetcher_version: str = "v1"

    def __post_init__(self):
        if self.state not in VALID_STATES:
            raise ValueError(f"Invalid state {self.state!r}; must be one of {VALID_STATES}")

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "name": self.name,
            "fetcher": self.fetcher,
            "inputs": list(self.inputs),
            "output_type": self.output_type,
            "horizon_days": self.horizon_days,
            "introduced": self.introduced,
            "state": self.state,
            "state_history": [t.to_dict() for t in self.state_history],
            "metrics": dict(self.metrics),
            "weight": self.weight,
            "fetcher_version": self.fetcher_version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SignalDefinition:
        history = [
            StateTransition(
                timestamp=t["timestamp"],
                from_state=t.get("from_state"),
                to_state=t["to_state"],
                reason=t.get("reason", ""),
            )
            for t in d.get("state_history", [])
        ]
        return cls(
            signal_id=d["signal_id"],
            name=d["name"],
            fetcher=d["fetcher"],
            inputs=list(d.get("inputs", [])),
            output_type=d.get("output_type", "markdown"),
            horizon_days=int(d.get("horizon_days", 21)),
            introduced=d["introduced"],
            state=d["state"],
            state_history=history,
            metrics=dict(d.get("metrics", {})),
            weight=d.get("weight"),
            fetcher_version=d.get("fetcher_version", "v1"),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_snapshot(sig: SignalDefinition, registry_path: Path | None = None) -> None:
    """Append a SignalDefinition snapshot as a JSON line to the registry."""
    path = registry_path or get_registry_path()
    line = json.dumps(sig.to_dict(), ensure_ascii=False)
    # Append-only write; one snapshot per call.
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_registry(registry_path: Path | None = None) -> dict[str, SignalDefinition]:
    """Read the registry and return the latest snapshot per signal_id.

    Replays all lines; later snapshots for the same signal_id win. Corrupted
    lines are skipped with a warning (resilient to partial writes per FR-014).
    """
    path = registry_path or get_registry_path()
    if not path.exists():
        return {}

    latest: dict[str, SignalDefinition] = {}
    with open(path, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                d = json.loads(raw)
                sig = SignalDefinition.from_dict(d)
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning("registry %s:%d: skipping malformed entry (%s)", path, lineno, exc)
                continue
            latest[sig.signal_id] = sig
    return latest


def register_signal(
    signal_id: str,
    name: str,
    fetcher: str,
    inputs: list[str],
    output_type: str = "markdown",
    horizon_days: int = 21,
    state: str = "production",
    fetcher_version: str = "v1",
    registry_path: Path | None = None,
) -> SignalDefinition:
    """Register a new signal OR re-register an existing one with updated metadata.

    Idempotent: re-calling with the same signal_id and identical metadata is a
    no-op (no new snapshot written). Re-calling with different metadata writes
    a new snapshot — but state transitions specifically should go through
    ``transition_state`` to record the reason.
    """
    existing = load_registry(registry_path).get(signal_id)
    now = _now_iso()
    if existing is None:
        sig = SignalDefinition(
            signal_id=signal_id,
            name=name,
            fetcher=fetcher,
            inputs=list(inputs),
            output_type=output_type,
            horizon_days=horizon_days,
            introduced=now,
            state=state,
            state_history=[
                StateTransition(
                    timestamp=now,
                    from_state=None,
                    to_state=state,
                    reason="initial registration",
                )
            ],
            fetcher_version=fetcher_version,
        )
        _append_snapshot(sig, registry_path)
        return sig

    # Existing — return as-is if metadata matches; otherwise write updated snapshot.
    new_inputs = list(inputs)
    metadata_unchanged = (
        existing.name == name
        and existing.fetcher == fetcher
        and existing.inputs == new_inputs
        and existing.output_type == output_type
        and existing.horizon_days == horizon_days
        and existing.state == state
        and existing.fetcher_version == fetcher_version
    )
    if metadata_unchanged:
        return existing

    updated = SignalDefinition(
        signal_id=signal_id,
        name=name,
        fetcher=fetcher,
        inputs=new_inputs,
        output_type=output_type,
        horizon_days=horizon_days,
        introduced=existing.introduced,
        state=state,
        state_history=existing.state_history,
        metrics=existing.metrics,
        weight=existing.weight,
        fetcher_version=fetcher_version,
    )
    _append_snapshot(updated, registry_path)
    return updated


def transition_state(
    signal_id: str,
    to_state: str,
    reason: str,
    registry_path: Path | None = None,
) -> SignalDefinition:
    """Transition a signal to a new state. Appends a snapshot with the event recorded.

    Raises if the signal is not registered or the target state is invalid.
    """
    if to_state not in VALID_STATES:
        raise ValueError(f"Invalid target state {to_state!r}; must be one of {VALID_STATES}")
    registry = load_registry(registry_path)
    existing = registry.get(signal_id)
    if existing is None:
        raise KeyError(f"Cannot transition unknown signal {signal_id!r}")

    if existing.state == to_state:
        return existing  # idempotent no-op

    now = _now_iso()
    history = list(existing.state_history)
    history.append(
        StateTransition(
            timestamp=now,
            from_state=existing.state,
            to_state=to_state,
            reason=reason,
        )
    )
    updated = SignalDefinition(
        signal_id=existing.signal_id,
        name=existing.name,
        fetcher=existing.fetcher,
        inputs=existing.inputs,
        output_type=existing.output_type,
        horizon_days=existing.horizon_days,
        introduced=existing.introduced,
        state=to_state,
        state_history=history,
        metrics=existing.metrics,
        weight=existing.weight,
        fetcher_version=existing.fetcher_version,
    )
    _append_snapshot(updated, registry_path)
    return updated


def get_signal(signal_id: str, registry_path: Path | None = None) -> SignalDefinition | None:
    """Look up a signal by id. Returns None if not registered."""
    return load_registry(registry_path).get(signal_id)


def list_signals(
    state: str | None = None, registry_path: Path | None = None
) -> list[SignalDefinition]:
    """List registered signals, optionally filtered by state."""
    all_sigs = list(load_registry(registry_path).values())
    if state is None:
        return all_sigs
    return [s for s in all_sigs if s.state == state]
