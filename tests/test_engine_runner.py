"""EngineRunner integration tests (specs/250-dashboard-ui/).

Verifies the runner writes valid progress.json + events.jsonl in both
real-run mode (with injected propagate_fn) and dry-run mode (FR-008).
"""

from __future__ import annotations

import json

import pytest

from tradingagents.engine import lock as lock_module
from tradingagents.engine.runner import EngineRunner
from tradingagents.engine.schemas import (
    AgentStage,
    Event,
    EventType,
    ProgressFile,
)


@pytest.fixture(autouse=True)
def isolated_engine_state(tmp_path, monkeypatch):
    """Redirect engine lock + run_dir to tmp_path."""
    eng_dir = tmp_path / "engine"
    monkeypatch.setattr(lock_module, "ENGINE_DIR", eng_dir)
    monkeypatch.setattr(lock_module, "LOCK_FILE", eng_dir / "lock")
    yield eng_dir


@pytest.fixture
def runner(tmp_path) -> EngineRunner:
    return EngineRunner(run_dir=tmp_path / "run")


def _read_events(path) -> list[Event]:
    return [
        Event.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines()
    ]


# ---------------------------------------------------------------------------
# Dry-run mode (FR-008)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_dry_run_emits_per_agent_stage_events(runner):
    """FR-008: dry-run emits one agent_started + agent_finished per stage,
    for each ticker. No LLM calls."""
    final = runner.run(["NVDA", "AAPL"], dry_run=True)

    assert isinstance(final, ProgressFile)
    assert len(final.completed_tickers) == 2
    assert len(final.failed_tickers) == 0
    assert all(t.rating == "Hold" for t in final.completed_tickers)

    events = _read_events(runner.events_path)
    # 2 tickers × (1 ticker_started + 12 agent_started + 12 agent_finished + 1 ticker_finished)
    # + 1 run_started + 1 run_finished = 53
    assert len(events) == 2 * 26 + 2

    # Verify agent_started and agent_finished come in matched pairs per stage.
    nvda_starts = [
        e for e in events if e.ticker == "NVDA" and e.event_type == EventType.AGENT_STARTED
    ]
    nvda_finishes = [
        e for e in events if e.ticker == "NVDA" and e.event_type == EventType.AGENT_FINISHED
    ]
    assert len(nvda_starts) == 12
    assert len(nvda_finishes) == 12
    assert {e.agent_stage for e in nvda_starts} == set(AgentStage)


@pytest.mark.unit
def test_dry_run_writes_valid_progress_json(runner):
    runner.run(["NVDA"], dry_run=True)
    raw = runner.progress_path.read_text(encoding="utf-8")
    parsed = ProgressFile.model_validate_json(raw)
    assert parsed.run_id == runner.run_id
    assert parsed.watchlist == ["NVDA"]
    assert parsed.current_ticker is None  # cleared after run finishes
    assert parsed.current_agent_stage is None
    assert len(parsed.completed_tickers) == 1


@pytest.mark.unit
def test_dry_run_progress_file_is_atomic(runner):
    """Run dry-run; verify only the final progress.json exists, no .tmp leftover.

    The atomic-write contract (PR #249 sister) means readers never observe a
    .tmp file after a write completes.
    """
    runner.run(["NVDA"], dry_run=True)
    files = sorted(runner.run_dir.iterdir())
    # progress.json + events.jsonl. No .tmp.
    file_names = {f.name for f in files}
    assert "progress.json" in file_names
    assert "events.jsonl" in file_names
    assert not any(f.name.endswith(".tmp") for f in files)


# ---------------------------------------------------------------------------
# Real-run mode with injected propagate_fn (no LLM)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_real_run_with_stub_propagate_emits_ticker_events(tmp_path):
    """Inject a stub propagate that returns deterministic ratings.

    Verifies the runner emits ticker_started + ticker_finished and
    populates completed_tickers correctly. Per-agent events for real
    runs are deferred to Phase 1b (graph.astream wiring).
    """
    calls = []

    def stub_propagate(ticker: str, trade_date: str) -> str:
        calls.append((ticker, trade_date))
        return {"NVDA": "Buy", "AAPL": "Hold"}.get(ticker, "Hold")

    runner = EngineRunner(run_dir=tmp_path / "run", propagate_fn=stub_propagate)
    final = runner.run(["NVDA", "AAPL"], dry_run=False)

    assert calls == [("NVDA", runner.trade_date), ("AAPL", runner.trade_date)]
    assert len(final.completed_tickers) == 2
    assert final.completed_tickers[0].rating == "Buy"
    assert final.completed_tickers[1].rating == "Hold"

    events = _read_events(runner.events_path)
    event_types = [e.event_type for e in events]
    assert EventType.RUN_STARTED in event_types
    assert EventType.RUN_FINISHED in event_types
    assert event_types.count(EventType.TICKER_STARTED) == 2
    assert event_types.count(EventType.TICKER_FINISHED) == 2


@pytest.mark.unit
def test_real_run_captures_propagate_failure_per_ticker(tmp_path):
    """A failing propagate becomes a ticker_failed event + a FailedTicker entry,
    but does not abort the run — subsequent tickers still process."""

    def stub_propagate(ticker: str, trade_date: str) -> str:
        if ticker == "BAD":
            raise ValueError(f"boom on {ticker}")
        return "Hold"

    runner = EngineRunner(run_dir=tmp_path / "run", propagate_fn=stub_propagate)
    final = runner.run(["NVDA", "BAD", "AAPL"], dry_run=False)

    assert len(final.completed_tickers) == 2
    assert {t.ticker for t in final.completed_tickers} == {"NVDA", "AAPL"}
    assert len(final.failed_tickers) == 1
    assert final.failed_tickers[0].ticker == "BAD"
    assert "boom on BAD" in final.failed_tickers[0].error

    events = _read_events(runner.events_path)
    failed_events = [e for e in events if e.event_type == EventType.TICKER_FAILED]
    assert len(failed_events) == 1
    assert failed_events[0].ticker == "BAD"


# ---------------------------------------------------------------------------
# Concurrency lock (FR-004)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_two_concurrent_runs_blocked_by_lock(tmp_path):
    """FR-004: second runner attempting to start while first holds the lock
    must raise EngineBusyError without writing any events."""
    runner2 = EngineRunner(run_dir=tmp_path / "run2")

    # Manually acquire lock outside a real run to simulate "engine 1 in flight".
    lock_module.ENGINE_DIR.mkdir(parents=True, exist_ok=True)
    lock_module.LOCK_FILE.write_text("99999", encoding="utf-8")

    try:
        with pytest.raises(lock_module.EngineBusyError):
            runner2.run(["NVDA"], dry_run=True)
        # runner2 must NOT have written anything.
        assert not runner2.events_path.exists() or runner2.events_path.read_text() == ""
    finally:
        lock_module.LOCK_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# events.jsonl line format
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_events_jsonl_one_object_per_line(runner):
    """events.jsonl must be parseable line-by-line. Each line is one Event."""
    runner.run(["NVDA"], dry_run=True)
    lines = runner.events_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        # Must be valid JSON.
        obj = json.loads(line)
        # Must contain the canonical event fields.
        assert "ts" in obj
        assert "run_id" in obj
        assert "event_type" in obj


@pytest.mark.unit
def test_events_jsonl_resets_per_run(tmp_path):
    """Each run replaces events.jsonl (one file per run; FR-021 + dashboard
    tails the current/ dir)."""
    runner = EngineRunner(run_dir=tmp_path / "run")
    runner.run(["NVDA"], dry_run=True)
    first_run_lines = len(runner.events_path.read_text(encoding="utf-8").splitlines())

    # Second run with a fresh runner (new run_id) re-uses the same events.jsonl path.
    runner2 = EngineRunner(run_dir=tmp_path / "run")
    runner2.run(["AAPL"], dry_run=True)
    second_run_lines = len(runner2.events_path.read_text(encoding="utf-8").splitlines())

    # Second run's file is independent (was reset).
    assert second_run_lines == first_run_lines  # same number of events for same scope
    # And contains AAPL, not NVDA.
    events = _read_events(runner2.events_path)
    aapl_tickers = {e.ticker for e in events if e.ticker is not None}
    assert aapl_tickers == {"AAPL"}
