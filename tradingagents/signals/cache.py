"""SQLite cache of per-(signal, ticker, date) computed values.

Schema per spec 002 FR-002:
    signal_values(
        signal_id TEXT,
        ticker TEXT,
        date TEXT,            -- ISO 8601 (YYYY-MM-DD), the trade_date
        value TEXT,           -- string-coerced value (markdown / number / etc.)
        raw_json TEXT,        -- optional JSON-serialized structured form
        computed_at TEXT,     -- ISO 8601 UTC timestamp of computation
        fetcher_version TEXT, -- registry-managed; v1 unless explicitly bumped
        PRIMARY KEY (signal_id, ticker, date, fetcher_version)
    )

The PK collapses repeats — re-running a propagate on the same (ticker, date)
overwrites the prior value. ``fetcher_version`` is part of the key so a
version bump preserves old values for historical queries.

Phase 0 implements: init_cache, record_value, query_value, query_all,
count_rows. Phase 1 (evaluation harness) reads from it; Phase 0 just
populates.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tradingagents.signals.paths import get_cache_path

logger = logging.getLogger(__name__)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS signal_values (
    signal_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    value TEXT,
    raw_json TEXT,
    computed_at TEXT NOT NULL,
    fetcher_version TEXT NOT NULL DEFAULT 'v1',
    PRIMARY KEY (signal_id, ticker, date, fetcher_version)
);

CREATE INDEX IF NOT EXISTS idx_signal_ticker_date ON signal_values (signal_id, ticker, date);
CREATE INDEX IF NOT EXISTS idx_ticker_date ON signal_values (ticker, date);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect(cache_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection. Uses default deferred isolation; ``with conn:``
    semantics handle commit/rollback automatically. Caller wraps DML in a
    ``with conn:`` block where transaction control matters; DDL and SELECT
    do not require explicit transaction management.
    """
    path = cache_path or get_cache_path()
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()


def init_cache(cache_path: Path | None = None) -> None:
    """Create the schema if it does not exist. Idempotent."""
    path = cache_path or get_cache_path()
    # Ensure parent dir exists; get_cache_path guarantees this for the default path.
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(cache_path) as conn:
        conn.executescript(_SCHEMA)


def record_value(
    signal_id: str,
    ticker: str,
    date: str,
    value: Any,
    raw_json: str | None = None,
    fetcher_version: str = "v1",
    cache_path: Path | None = None,
) -> None:
    """Write one signal value to the cache. Overwrites prior value for the same key.

    ``value`` is string-coerced (cache stores everything as TEXT for the
    minimal Phase 0 schema). For structured outputs, also pass ``raw_json``
    with a JSON-serialized structured form.

    Failures are logged-and-swallowed: cache writes must never break the
    backtest pipeline. If the cache is corrupt or the disk is full, the
    backtest still completes.
    """
    try:
        init_cache(cache_path)
        with _connect(cache_path) as conn:
            with conn:  # transactional INSERT — auto-commit/rollback
                conn.execute(
                    """
                    INSERT OR REPLACE INTO signal_values
                        (signal_id, ticker, date, value, raw_json, computed_at, fetcher_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        signal_id,
                        ticker.upper() if ticker else "",
                        date,
                        str(value) if value is not None else None,
                        raw_json,
                        _now_iso(),
                        fetcher_version,
                    ),
                )
    except Exception as exc:  # noqa: BLE001 — cache writes must never break callers
        logger.warning(
            "signals.cache.record_value failed for (%s, %s, %s): %s",
            signal_id,
            ticker,
            date,
            exc,
        )


def query_value(
    signal_id: str,
    ticker: str,
    date: str,
    fetcher_version: str = "v1",
    cache_path: Path | None = None,
) -> dict | None:
    """Look up a single cached value. Returns None if absent."""
    init_cache(cache_path)
    with _connect(cache_path) as conn:
        cur = conn.execute(
            """
            SELECT signal_id, ticker, date, value, raw_json, computed_at, fetcher_version
            FROM signal_values
            WHERE signal_id = ? AND ticker = ? AND date = ? AND fetcher_version = ?
            """,
            (signal_id, ticker.upper(), date, fetcher_version),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return _row_to_dict(row)


def query_all(
    signal_id: str | None = None,
    ticker: str | None = None,
    cache_path: Path | None = None,
) -> list[dict]:
    """Bulk read with optional signal_id and ticker filters.

    Returns rows in (signal_id, ticker, date) order for stable iteration.
    """
    init_cache(cache_path)
    where = []
    args: list[Any] = []
    if signal_id is not None:
        where.append("signal_id = ?")
        args.append(signal_id)
    if ticker is not None:
        where.append("ticker = ?")
        args.append(ticker.upper())
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT signal_id, ticker, date, value, raw_json, computed_at, fetcher_version
        FROM signal_values
        {where_sql}
        ORDER BY signal_id, ticker, date
    """
    with _connect(cache_path) as conn:
        cur = conn.execute(sql, args)
        return [_row_to_dict(r) for r in cur.fetchall()]


def count_rows(cache_path: Path | None = None) -> int:
    """Total count of cached signal values. Useful for SC-001 validation."""
    init_cache(cache_path)
    with _connect(cache_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM signal_values")
        return int(cur.fetchone()[0])


def _row_to_dict(row: tuple) -> dict:
    return {
        "signal_id": row[0],
        "ticker": row[1],
        "date": row[2],
        "value": row[3],
        "raw_json": json.loads(row[4]) if row[4] else None,
        "computed_at": row[5],
        "fetcher_version": row[6],
    }
