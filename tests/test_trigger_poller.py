"""Tests for scripts/trigger_poller.py.

The integration test runs the actual engine --dry-run subprocess (no LLM
cost, no network), which exercises the real spawn path the production
poller will take. The unit-marker tests cover the pure-Python logic
(quarantine, regex rejection, lock-skip).
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Resolve poller module via direct path (not on PYTHONPATH by default).
_POLLER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "trigger_poller.py"
_spec = importlib.util.spec_from_file_location("trigger_poller", _POLLER_PATH)
assert _spec is not None and _spec.loader is not None
poller = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(poller)


@pytest.fixture
def queue_dir(tmp_path, monkeypatch):
    """Isolated TRIGGER_DIR + ENGINE_DIR + LOCK_FILE for one test."""
    triggers = tmp_path / "triggers"
    engine = tmp_path / "engine"
    triggers.mkdir()
    engine.mkdir()
    monkeypatch.setattr(poller, "TRIGGER_DIR", triggers)
    monkeypatch.setattr(poller, "ENGINE_DIR", engine)
    monkeypatch.setattr(poller, "LOCK_FILE", engine / "lock")
    monkeypatch.setattr(poller, "POLLER_LOCK", triggers / ".poller-lock")
    yield {"triggers": triggers, "engine": engine}


@pytest.mark.unit
def test_bad_filename_quarantined(queue_dir, monkeypatch):
    """A .req with an invalid ticker is quarantined to .failed.<ts>, not spawned."""
    monkeypatch.setattr(poller, "_spawn_engine", lambda t: pytest.fail("must not spawn"))
    bad = queue_dir["triggers"] / "not-a-ticker.req"
    bad.write_text("ts", encoding="utf-8")
    poller._scan_once()
    assert not bad.exists()
    failed = list(queue_dir["triggers"].glob("not-a-ticker.failed.*"))
    assert len(failed) == 1
    assert "regex fail" in failed[0].read_text(encoding="utf-8")


@pytest.mark.unit
def test_lock_held_skips_spawn(queue_dir, monkeypatch):
    """When ENGINE_DIR/lock exists, no spawn happens; .req stays in queue."""
    monkeypatch.setattr(poller, "_spawn_engine", lambda t: pytest.fail("must not spawn"))
    (queue_dir["engine"] / "lock").write_text("12345", encoding="utf-8")
    req = queue_dir["triggers"] / "NVDA.req"
    req.write_text("ts", encoding="utf-8")
    poller._scan_once()
    assert req.exists(), "request must remain queued while engine busy"


@pytest.mark.unit
def test_startup_sweep_quarantines_orphan_inflight(queue_dir):
    """Orphan .inflight from a previous poller crash gets quarantined,
    NOT retried (we can't know if the previous engine succeeded)."""
    orphan = queue_dir["triggers"] / "AAPL.inflight"
    orphan.write_text("from-crashed-poller", encoding="utf-8")
    poller._startup_sweep()
    assert not orphan.exists()
    failed = list(queue_dir["triggers"].glob("AAPL.failed.*"))
    assert len(failed) == 1
    assert "orphan" in failed[0].read_text(encoding="utf-8")


@pytest.mark.unit
def test_unlink_before_spawn_ordering(queue_dir, monkeypatch):
    """Critical invariant (v4 fix): .req must be renamed to .inflight BEFORE
    _spawn_engine is called. If spawn raises, .inflight gets quarantined."""
    rename_then_spawn_order: list[str] = []

    def fake_replace(src, dst):
        rename_then_spawn_order.append("rename")
        os.rename(src, dst)

    def fake_spawn(ticker):
        rename_then_spawn_order.append("spawn")

        # Return a Popen-like object whose wait() returns 0 immediately.
        class _Done:
            pid = 99999

            def wait(self):
                return 0

        return _Done()

    monkeypatch.setattr(poller.os, "replace", fake_replace)
    monkeypatch.setattr(poller, "_spawn_engine", fake_spawn)
    req = queue_dir["triggers"] / "NVDA.req"
    req.write_text("ts", encoding="utf-8")
    poller._scan_once()
    # Poll briefly for the reaper thread to clean up.
    for _ in range(20):
        if not (queue_dir["triggers"] / "NVDA.inflight").exists():
            break
        time.sleep(0.05)
    assert rename_then_spawn_order == ["rename", "spawn"]


@pytest.mark.unit
def test_popen_failure_quarantines_inflight(queue_dir, monkeypatch):
    """If _spawn_engine raises OSError, the .inflight is renamed to .failed
    instead of leaking."""

    def explode(ticker):
        raise OSError(2, "no such executable")

    monkeypatch.setattr(poller, "_spawn_engine", explode)
    req = queue_dir["triggers"] / "MSFT.req"
    req.write_text("ts", encoding="utf-8")
    poller._scan_once()
    assert not req.exists()
    assert not (queue_dir["triggers"] / "MSFT.inflight").exists()
    failed = list(queue_dir["triggers"].glob("MSFT.failed.*"))
    assert len(failed) == 1


@pytest.mark.unit
def test_engine_failure_rc_quarantines_inflight(queue_dir, monkeypatch):
    """Engine subprocess exits non-zero → reaper renames .inflight to .failed."""

    class _Fail:
        pid = 11111

        def wait(self):
            return 17

    monkeypatch.setattr(poller, "_spawn_engine", lambda t: _Fail())
    req = queue_dir["triggers"] / "TSLA.req"
    req.write_text("ts", encoding="utf-8")
    poller._scan_once()
    # Wait briefly for reaper.
    for _ in range(40):
        if not (queue_dir["triggers"] / "TSLA.inflight").exists():
            break
        time.sleep(0.05)
    failed = list(queue_dir["triggers"].glob("TSLA.failed.*"))
    assert len(failed) == 1
    assert "rc=17" in failed[0].read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Integration test — runs a REAL engine subprocess via --dry-run mode.
# Marked integration so the pre-commit `pytest -m unit` hook stays fast.
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_real_engine_dry_run_subprocess(queue_dir, monkeypatch, tmp_path):
    """End-to-end: rename + spawn + reap with the actual engine in --dry-run.

    No LLM cost (dry-run emits fake events without invoking propagate).
    Verifies the spawn path that the production poller will use — the
    same gap that let prior regressions ship under TestClient mocks.
    """
    # Override _spawn_engine to use --dry-run + isolated state-dir so we
    # don't write to the operator's real ~/.tradingagents/engine/.
    state_dir = tmp_path / "engine-state"
    state_dir.mkdir()

    def real_spawn_dry_run(ticker: str) -> subprocess.Popen:
        return subprocess.Popen(  # noqa: S603
            [
                sys.executable,
                "-m",
                "tradingagents.engine",
                "run",
                "--ticker",
                ticker,
                "--dry-run",
                "--state-dir",
                str(state_dir),
            ],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    monkeypatch.setattr(poller, "_spawn_engine", real_spawn_dry_run)

    req = queue_dir["triggers"] / "NVDA.req"
    req.write_text("ts", encoding="utf-8")
    poller._scan_once()

    # Wait for the engine subprocess + reaper. Dry-run takes ~1-2s.
    deadline = time.time() + 30
    while time.time() < deadline:
        if not (queue_dir["triggers"] / "NVDA.inflight").exists() and not req.exists():
            break
        time.sleep(0.2)

    # On clean exit (rc=0), the .inflight is unlinked. Verify the engine
    # actually wrote its progress.json (proves the subprocess ran end-to-end).
    progress = state_dir / "current" / "progress.json"
    assert progress.exists(), f"engine did not write progress.json under {state_dir}"
    failed = list(queue_dir["triggers"].glob("NVDA.failed.*"))
    assert failed == [], f"unexpected quarantine: {failed}"
