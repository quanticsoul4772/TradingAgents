"""Filesystem paths for the signal registry + cache.

All Phase 0 storage lives under ``~/.tradingagents/signals/`` (or
overridden via ``TRADINGAGENTS_SIGNALS_DIR``):

- ``registry.jsonl`` — append-only signal definitions + state transitions
- ``cache.db``       — SQLite cache of per-(signal, ticker, date) values

Per spec 002 FR-001 / FR-002.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_signals_dir() -> Path:
    """Root directory for signal registry + cache.

    Override with ``TRADINGAGENTS_SIGNALS_DIR``; otherwise defaults to
    ``~/.tradingagents/signals``. The directory is created if it does not exist.
    """
    base = os.getenv("TRADINGAGENTS_SIGNALS_DIR")
    if base:
        path = Path(base)
    else:
        path = Path.home() / ".tradingagents" / "signals"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_registry_path() -> Path:
    """Path to the append-only registry file (registry.jsonl)."""
    return get_signals_dir() / "registry.jsonl"


def get_cache_path() -> Path:
    """Path to the SQLite cache (cache.db)."""
    return get_signals_dir() / "cache.db"
