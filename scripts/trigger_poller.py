"""Trigger poller daemon — drains ~/.tradingagents/triggers/*.req and spawns
the engine subprocess for each one.

Runs as the `agent` user under a USER systemd service
(deploy/systemd/tradingagents-trigger-poller.service). Does not require
root. Does not use systemctl. Just polls a directory and spawns subprocesses.

Pattern adapted from agent-harness-v2/runtime/src/agent_harness/events/intents.py
(SQLite operator_intents poller). Simplifications for TradingAgents:
- File-queue instead of SQLite (no event-bus to integrate with)
- Subprocess spawn instead of in-process (10-min propagates, crash isolation)
- No claimed/applying/applied status — engine writes its own progress.json

Lifecycle of a single trigger:
  1. Dashboard writes <TICKER>.req to TRIGGER_DIR (atomic temp+rename)
  2. Poller scan finds the file
  3. Poller skips if engine lock is held (re-checks AT spawn time, not earlier)
  4. Poller renames .req → .inflight (atomic)
  5. Poller spawns engine via subprocess.Popen, start_new_session=True
  6. Reaper thread waits on the subprocess; on exit:
       - exit 0 → unlink .inflight
       - non-zero → rename .inflight → .failed.<timestamp> for operator review

Failure modes handled:
- Bad filename / unparseable: rename to .failed at startup sweep
- Poller crash mid-run: orphan .inflight files quarantined to .failed at next start
- Two poller instances: flock on .poller-lock prevents
- Engine busy when poller fires: skip and try next tick (no spawn, no rename)
- subprocess.Popen failure: rename .inflight → .failed
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import signal
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

# fcntl is POSIX-only. The poller only runs on Linux (USER systemd unit
# on the VPS), but the test module imports this file on Windows too.
try:
    import fcntl  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — Windows
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger("tradingagents.trigger_poller")

# Match dashboard state_reader env-var conventions so a single env file
# can configure both processes.
TRIGGER_DIR = Path(
    os.environ.get("TA_TRIGGER_DIR", str(Path.home() / ".tradingagents" / "triggers"))
)
ENGINE_DIR = Path(os.environ.get("TA_ENGINE_DIR", str(Path.home() / ".tradingagents" / "engine")))
LOCK_FILE = ENGINE_DIR / "lock"
POLLER_LOCK = TRIGGER_DIR / ".poller-lock"

# Validation regex — same as the dashboard FR-011 check. The dashboard
# already validates before writing, but the poller treats arbitrary files
# in the queue dir defensively (filesystem could have stale .req from
# previous installs, manual operator pokes, etc.).
_TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")

# Polling cadence — agent-harness pattern: short interval when active,
# exponential backoff when idle, capped.
BASE_INTERVAL_SEC = 2.0
MAX_INTERVAL_SEC = 30.0


def _now_ts() -> str:
    """Compact UTC timestamp suffix for .failed file names."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _engine_lock_held() -> bool:
    """Cheap filesystem check — same semantics as dashboard's `read_engine_lock()`."""
    return LOCK_FILE.exists()


def _quarantine(req_or_inflight: Path, reason: str) -> None:
    """Move a request file to .failed.<timestamp> with a reason in the body."""
    failed = req_or_inflight.with_name(f"{req_or_inflight.stem}.failed.{_now_ts()}")
    try:
        # Append reason to the existing file body so operator sees context
        # when investigating.
        body = ""
        try:
            body = req_or_inflight.read_text(encoding="utf-8")
        except OSError:
            pass
        failed.write_text(f"{body}\nFAILED: {reason}\n", encoding="utf-8")
        req_or_inflight.unlink()
    except OSError as exc:
        logger.error("could not quarantine %s: %s", req_or_inflight, exc)


def _spawn_engine(ticker: str) -> subprocess.Popen[bytes]:
    """Spawn engine subprocess detached from poller's process group."""
    cmd = [sys.executable, "-m", "tradingagents.engine", "run", "--ticker", ticker]
    return subprocess.Popen(  # noqa: S603 — args are list, no shell, ticker validated
        cmd,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        # Engine writes its own logs to ~/.tradingagents/logs/<TICKER>/
        # via _log_state. No need to capture stdout/stderr here.
    )


def _reap(inflight: Path, proc: subprocess.Popen[bytes], ticker: str) -> None:
    """Wait on the engine subprocess and dispose of the .inflight file."""
    try:
        rc = proc.wait()
    except Exception as exc:  # noqa: BLE001
        logger.exception("reaper for %s crashed", ticker)
        _quarantine(inflight, f"reaper exception: {exc}")
        return
    if rc == 0:
        try:
            inflight.unlink()
        except OSError as exc:
            logger.warning("engine %s succeeded but could not unlink %s: %s", ticker, inflight, exc)
        else:
            logger.info("engine %s completed (rc=0); inflight cleared", ticker)
    else:
        logger.warning("engine %s exited rc=%s; quarantining", ticker, rc)
        _quarantine(inflight, f"engine exited rc={rc}")


def _process_one(req: Path) -> bool:
    """Process a single .req file. Returns True if a spawn happened."""
    ticker = req.stem
    if not _TICKER_RE.match(ticker):
        logger.warning("bad ticker filename: %s — quarantining", req.name)
        _quarantine(req, f"ticker regex fail: {ticker!r}")
        return False

    # Re-check lock immediately before spawn (not just at scan time —
    # daily timer or another adhoc could have acquired the lock between
    # scan and now).
    if _engine_lock_held():
        logger.info("engine busy at spawn time for %s — leaving in queue", ticker)
        return False

    inflight = req.with_suffix(".inflight")
    try:
        os.replace(req, inflight)
    except OSError as exc:
        logger.error("could not rename %s → .inflight: %s", req.name, exc)
        return False

    try:
        proc = _spawn_engine(ticker)
    except OSError as exc:
        logger.error("Popen failed for %s: %s", ticker, exc)
        _quarantine(inflight, f"Popen failed: {exc}")
        return False

    # Detached reaper thread — daemon so poller restart doesn't wait on it.
    t = threading.Thread(target=_reap, args=(inflight, proc, ticker), daemon=True)
    t.start()
    logger.info("spawned engine for %s (pid=%s)", ticker, proc.pid)
    return True


def _startup_sweep() -> None:
    """Quarantine any orphan .inflight files left by a previous poller crash.

    Why quarantine, not retry: we don't know if the engine subprocess is
    still running, finished successfully, or crashed. Safer to flag for
    operator review than to risk a duplicate spawn or assume success.

    .req files from before the restart are NOT quarantined — they're
    legitimate pending requests; the normal scan loop will pick them up.
    """
    if not TRIGGER_DIR.exists():
        return
    for inflight in sorted(TRIGGER_DIR.glob("*.inflight")):
        logger.warning("startup sweep: orphan inflight %s", inflight.name)
        _quarantine(inflight, "orphan from previous poller restart")


def _scan_once() -> int:
    """Scan the queue dir; process up to one .req per tick.

    Limit-one matches agent-harness's per-tick rate limit (their MAX is 20
    but each intent is fast; ours are 10-minute LLM runs, so 1 is plenty).
    The engine lock blocks anyway, so even if we scanned more we'd skip
    them all once the first spawned.
    """
    if not TRIGGER_DIR.exists():
        return 0
    reqs = sorted(TRIGGER_DIR.glob("*.req"))
    if not reqs:
        return 0
    if _engine_lock_held():
        return 0
    if _process_one(reqs[0]):
        return 1
    return 0


def _acquire_poller_lock() -> int:
    """Single-instance guard via flock. Returns the held fd. POSIX-only."""
    if fcntl is None:
        raise RuntimeError("trigger_poller requires POSIX (fcntl); cannot run on Windows")
    TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(POLLER_LOCK, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        logger.error("another poller already holds %s — exiting", POLLER_LOCK)
        sys.exit(1)
    os.write(fd, f"{os.getpid()}\n".encode())
    return fd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single scan + reap cycle (used by tests).",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("TA_LOG_LEVEL", "INFO"),
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    _acquire_poller_lock()
    _startup_sweep()

    if args.once:
        spawned = _scan_once()
        logger.info("--once mode: spawned=%s", spawned)
        return 0

    # Graceful shutdown on SIGTERM (systemd default stop signal).
    stop_event = threading.Event()

    def _on_term(_signum: int, _frame: object) -> None:
        logger.info("received SIGTERM — exiting after current scan")
        stop_event.set()

    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)

    interval = BASE_INTERVAL_SEC
    while not stop_event.is_set():
        try:
            spawned = _scan_once()
        except Exception:  # noqa: BLE001
            logger.exception("scan cycle failed; will retry")
            spawned = 0
        if spawned > 0:
            interval = BASE_INTERVAL_SEC
        else:
            interval = min(interval * 2, MAX_INTERVAL_SEC)
        stop_event.wait(interval)

    return 0


if __name__ == "__main__":
    sys.exit(main())
