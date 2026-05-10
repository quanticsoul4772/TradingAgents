"""Engine file lock tests (specs/250-dashboard-ui/ FR-004)."""

from __future__ import annotations

import os

import pytest

from tradingagents.engine import lock as lock_module


@pytest.fixture(autouse=True)
def isolated_lock(tmp_path, monkeypatch):
    """Redirect ENGINE_DIR + LOCK_FILE to a tmp dir for each test."""
    eng_dir = tmp_path / "engine"
    monkeypatch.setattr(lock_module, "ENGINE_DIR", eng_dir)
    monkeypatch.setattr(lock_module, "LOCK_FILE", eng_dir / "lock")
    yield


@pytest.mark.unit
def test_lock_acquired_and_released_in_clean_path():
    assert not lock_module.is_locked()
    with lock_module.engine_lock():
        assert lock_module.is_locked()
        assert lock_module.lock_holder_pid() == str(os.getpid())
    assert not lock_module.is_locked()


@pytest.mark.unit
def test_lock_released_on_exception():
    """Lock cleanup happens via finally; exceptions inside the block must
    not leave a stale lock file."""
    with pytest.raises(RuntimeError):
        with lock_module.engine_lock():
            raise RuntimeError("boom")
    assert not lock_module.is_locked()


@pytest.mark.unit
def test_concurrent_lock_acquisition_raises_busy():
    """FR-004 + FR-013: second acquire while first is held raises EngineBusyError."""
    with lock_module.engine_lock():
        with pytest.raises(lock_module.EngineBusyError):
            with lock_module.engine_lock():
                pytest.fail("should not reach inner block")


@pytest.mark.unit
def test_lock_holder_pid_returns_none_when_unlocked():
    assert lock_module.lock_holder_pid() is None


@pytest.mark.unit
def test_lock_holder_pid_returns_string_when_locked():
    with lock_module.engine_lock():
        pid = lock_module.lock_holder_pid()
        assert pid is not None
        assert int(pid) > 0


@pytest.mark.unit
def test_engine_dir_auto_created_on_lock_acquire():
    """ENGINE_DIR doesn't have to exist beforehand; lock acquire creates it."""
    assert not lock_module.ENGINE_DIR.exists()
    with lock_module.engine_lock():
        assert lock_module.ENGINE_DIR.exists()
