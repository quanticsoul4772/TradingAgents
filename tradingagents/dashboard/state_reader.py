"""Read-only adapters over engine state, log files, and paper portfolio
(spec 250-dashboard-ui FR-003).

The dashboard backend NEVER writes through this module. Engine writes are
atomic (PR #249); readers either see the prior complete file or the new
complete file, never partial.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Paths can be overridden by env vars (used by the container Quadlet to
# bind-mount host dirs to /var/lib/tradingagents/* read-only).
ENGINE_DIR = Path(os.environ.get("TA_ENGINE_DIR", str(Path.home() / ".tradingagents" / "engine")))
LOGS_DIR = Path(os.environ.get("TA_LOGS_DIR", str(Path.home() / ".tradingagents" / "logs")))
PAPER_DIR = Path(os.environ.get("TA_PAPER_DIR", str(Path.home() / ".tradingagents" / "paper")))

CURRENT_DIR = ENGINE_DIR / "current"

# Per-ticker validation: regex from spec FR-011 + watchlist membership check.
TICKER_REGEX = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

HEARTBEAT_TTL_SEC = 90  # FR-027


# ----------------------------------------------------------------- progress.json


def read_progress() -> dict | None:
    """Return current run's progress.json, or None if no run has happened."""
    p = CURRENT_DIR / "progress.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def is_run_stale(progress: dict | None) -> bool:
    """FR-027: heartbeat older than 90 sec without a terminal event = STALE."""
    if not progress:
        return False
    hb = progress.get("heartbeat_at")
    if not hb:
        return False
    try:
        hb_dt = datetime.fromisoformat(hb.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - hb_dt).total_seconds()
    except (ValueError, AttributeError):
        return False
    if age <= HEARTBEAT_TTL_SEC:
        return False
    # Terminal event in events.jsonl means the run finished cleanly even if
    # heartbeat is stale (e.g., engine exited and never refreshed heartbeat).
    for evt in tail_events(limit=50):
        if evt.get("event_type") in ("run_finished", "ticker_failed"):
            return False
    return True


# ------------------------------------------------------------------- events.jsonl


def tail_events(limit: int = 100, since_ts: str | None = None) -> list[dict]:
    """Return the last `limit` events. If since_ts is provided, return only
    events with ts > since_ts (FR-014 — incremental polling)."""
    p = CURRENT_DIR / "events.jsonl"
    if not p.exists():
        return []
    out: list[dict] = []
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if since_ts and evt.get("ts", "") <= since_ts:
            continue
        out.append(evt)
    return out[-limit:] if limit else out


# ------------------------------------------------------------------- state logs


def read_ticker_state_log(ticker: str, trade_date: str) -> dict | None:
    """Read the full per-ticker state log (~400KB of agent prose) for one date."""
    if not TICKER_REGEX.match(ticker) or not DATE_REGEX.match(trade_date):
        return None
    p = LOGS_DIR / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{trade_date}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def list_tickers_for_date(trade_date: str) -> list[str]:
    """Find all tickers that have a state log for the given date.

    Walks LOGS_DIR/<TICKER>/TradingAgentsStrategy_logs/ for matching files.
    """
    if not DATE_REGEX.match(trade_date):
        return []
    if not LOGS_DIR.exists():
        return []
    out = []
    for ticker_dir in sorted(LOGS_DIR.iterdir()):
        if not ticker_dir.is_dir():
            continue
        log_path = ticker_dir / "TradingAgentsStrategy_logs" / f"full_states_log_{trade_date}.json"
        if log_path.exists():
            out.append(ticker_dir.name)
    return out


# ----------------------------------------------------------------- paper portfolio


def list_portfolio_ids() -> list[str]:
    """Return paper-trading portfolio IDs (one .json per portfolio)."""
    if not PAPER_DIR.exists():
        return []
    return sorted(p.stem for p in PAPER_DIR.glob("*.json") if p.stem != "sectors")


def read_portfolio(portfolio_id: str = "live") -> dict | None:
    """Read the paper portfolio state JSON."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", portfolio_id):
        return None
    p = PAPER_DIR / f"{portfolio_id}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


# ------------------------------------------------------------------ trigger validation


def validate_ticker_for_trigger(
    ticker: str, watchlist_path: Path | None = None
) -> tuple[bool, str]:
    """FR-011: validate a ticker against regex AND watchlist membership.

    Returns (ok, reason). ok=False with reason explains why the trigger is rejected.
    """
    if not TICKER_REGEX.match(ticker):
        return False, f"ticker {ticker!r} fails regex {TICKER_REGEX.pattern}"
    if watchlist_path is None:
        # Default: project's tech_weighted.txt
        watchlist_path = Path(os.environ.get("TA_WATCHLIST", "data/watchlists/tech_weighted.txt"))
    if not watchlist_path.exists():
        return False, f"watchlist file not found: {watchlist_path}"
    watchlist = _parse_watchlist(watchlist_path)
    if ticker not in watchlist:
        return False, f"ticker {ticker!r} not in watchlist {watchlist_path.name}"
    return True, "ok"


def _parse_watchlist(path: Path) -> set[str]:
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        token = line.split("#", 1)[0].strip()
        if token:
            out.add(token)
    return out


# ------------------------------------------------------------------ summarizers


def summarize_progress(progress: dict | None) -> dict[str, Any]:
    """Compact view used by templates: one dict with all the fields a homepage
    template needs, with safe defaults for None / missing keys."""
    if not progress:
        return {
            "exists": False,
            "trade_date": None,
            "run_id": None,
            "completed_count": 0,
            "failed_count": 0,
            "watchlist_size": 0,
            "current_ticker": None,
            "current_agent_stage": None,
            "stale": False,
            "completed": [],
            "failed": [],
        }
    completed = progress.get("completed_tickers", []) or []
    failed = progress.get("failed_tickers", []) or []
    watchlist = progress.get("watchlist", []) or []
    return {
        "exists": True,
        "trade_date": progress.get("trade_date"),
        "run_id": progress.get("run_id"),
        "started_at": progress.get("started_at"),
        "completed_count": len(completed),
        "failed_count": len(failed),
        "watchlist_size": len(watchlist),
        "current_ticker": progress.get("current_ticker"),
        "current_agent_stage": progress.get("current_agent_stage"),
        "stale": is_run_stale(progress),
        "completed": completed,
        "failed": failed,
    }
