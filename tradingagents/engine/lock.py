"""File lock for engine concurrency control (spec FR-004).

Prevents two engine processes from running simultaneously and writing
conflicting progress.json / events.jsonl. The dashboard's POST /trigger/{ticker}
endpoint checks this lock and returns 409 Conflict if held (FR-013).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

ENGINE_DIR = Path.home() / ".tradingagents" / "engine"
LOCK_FILE = ENGINE_DIR / "lock"


class EngineBusyError(RuntimeError):
    """Raised when the engine lock is already held by another process."""


def is_locked() -> bool:
    """Return True if the engine lock file exists."""
    return LOCK_FILE.exists()


def lock_holder_pid() -> str | None:
    """Return the PID written in the lock file, or None if no lock."""
    if not LOCK_FILE.exists():
        return None
    try:
        return LOCK_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None


@contextmanager
def engine_lock():
    """Context manager: acquire the engine file lock for the duration of a run.

    Raises EngineBusyError if another process holds the lock. Cleans up the
    lock file on exit (success or exception).
    """
    ENGINE_DIR.mkdir(parents=True, exist_ok=True)
    if LOCK_FILE.exists():
        held_by = lock_holder_pid() or "unknown"
        raise EngineBusyError(
            f"Engine lock held by PID {held_by} at {LOCK_FILE}. "
            f"Wait for the in-flight run to finish, or remove the lock manually "
            f"if the previous run crashed."
        )

    try:
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
        yield LOCK_FILE
    finally:
        if LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except OSError:
                pass
