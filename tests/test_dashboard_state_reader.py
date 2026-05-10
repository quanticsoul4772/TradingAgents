"""Unit tests for dashboard state_reader (spec 250 Phase 2)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from tradingagents.dashboard import state_reader as sr


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Redirect ENGINE_DIR / LOGS_DIR / PAPER_DIR to tmp_path."""
    eng = tmp_path / "engine"
    logs = tmp_path / "logs"
    paper = tmp_path / "paper"
    monkeypatch.setattr(sr, "ENGINE_DIR", eng)
    monkeypatch.setattr(sr, "LOGS_DIR", logs)
    monkeypatch.setattr(sr, "PAPER_DIR", paper)
    monkeypatch.setattr(sr, "CURRENT_DIR", eng / "current")
    yield {"engine": eng, "logs": logs, "paper": paper}


def _now_iso(offset_sec: float = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_sec)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


@pytest.mark.unit
def test_read_progress_returns_none_when_missing(isolated_state):
    assert sr.read_progress() is None


@pytest.mark.unit
def test_read_progress_returns_dict_when_present(isolated_state):
    p = isolated_state["engine"] / "current" / "progress.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"run_id": "abc"}), encoding="utf-8")
    assert sr.read_progress() == {"run_id": "abc"}


@pytest.mark.unit
def test_is_run_stale_false_when_no_progress():
    assert sr.is_run_stale(None) is False


@pytest.mark.unit
def test_is_run_stale_false_when_recent_heartbeat():
    progress = {"heartbeat_at": _now_iso(0)}
    assert sr.is_run_stale(progress) is False


@pytest.mark.unit
def test_is_run_stale_true_when_old_heartbeat_no_terminal_event(isolated_state):
    progress = {"heartbeat_at": _now_iso(-300)}  # 5 min old
    assert sr.is_run_stale(progress) is True


@pytest.mark.unit
def test_is_run_stale_false_when_old_heartbeat_but_run_finished_event(isolated_state):
    """Per FR-027: even if heartbeat is stale, a terminal event clears STALE."""
    p = isolated_state["engine"] / "current" / "events.jsonl"
    p.parent.mkdir(parents=True)
    p.write_text(
        json.dumps({"event_type": "run_finished", "ts": _now_iso(-100)}) + "\n", encoding="utf-8"
    )
    progress = {"heartbeat_at": _now_iso(-300)}
    assert sr.is_run_stale(progress) is False


@pytest.mark.unit
def test_tail_events_empty_when_no_file(isolated_state):
    assert sr.tail_events() == []


@pytest.mark.unit
def test_tail_events_returns_last_n(isolated_state):
    p = isolated_state["engine"] / "current" / "events.jsonl"
    p.parent.mkdir(parents=True)
    lines = [json.dumps({"ts": f"2026-05-10T12:{i:02d}:00Z", "event_type": "x"}) for i in range(10)]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert len(sr.tail_events(limit=5)) == 5


@pytest.mark.unit
def test_tail_events_since_filter(isolated_state):
    p = isolated_state["engine"] / "current" / "events.jsonl"
    p.parent.mkdir(parents=True)
    lines = [
        json.dumps({"ts": "2026-05-10T12:00:00Z", "event_type": "a"}),
        json.dumps({"ts": "2026-05-10T12:30:00Z", "event_type": "b"}),
        json.dumps({"ts": "2026-05-10T13:00:00Z", "event_type": "c"}),
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = sr.tail_events(since_ts="2026-05-10T12:30:00Z")
    assert [e["event_type"] for e in out] == ["c"]


@pytest.mark.unit
def test_tail_events_skips_invalid_json(isolated_state):
    p = isolated_state["engine"] / "current" / "events.jsonl"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"ts": "x", "event_type": "ok"}) + "\nNOT JSON\n", encoding="utf-8")
    assert len(sr.tail_events()) == 1


@pytest.mark.unit
def test_read_ticker_state_log_returns_none_for_missing(isolated_state):
    assert sr.read_ticker_state_log("NVDA", "2026-05-08") is None


@pytest.mark.unit
def test_read_ticker_state_log_rejects_bad_ticker(isolated_state):
    assert sr.read_ticker_state_log("../etc/passwd", "2026-05-08") is None
    assert sr.read_ticker_state_log("BAD123", "2026-05-08") is None


@pytest.mark.unit
def test_read_ticker_state_log_rejects_bad_date(isolated_state):
    assert sr.read_ticker_state_log("NVDA", "not-a-date") is None
    assert sr.read_ticker_state_log("NVDA", "2026/05/08") is None


@pytest.mark.unit
def test_read_ticker_state_log_returns_log(isolated_state):
    log_path = (
        isolated_state["logs"]
        / "NVDA"
        / "TradingAgentsStrategy_logs"
        / "full_states_log_2026-05-08.json"
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(json.dumps({"final_trade_decision": "**Rating**: Buy"}), encoding="utf-8")
    log = sr.read_ticker_state_log("NVDA", "2026-05-08")
    assert log["final_trade_decision"] == "**Rating**: Buy"


@pytest.mark.unit
def test_list_tickers_for_date_finds_all(isolated_state):
    for t in ["NVDA", "AAPL"]:
        d = isolated_state["logs"] / t / "TradingAgentsStrategy_logs"
        d.mkdir(parents=True)
        (d / "full_states_log_2026-05-08.json").write_text("{}", encoding="utf-8")
    assert sr.list_tickers_for_date("2026-05-08") == ["AAPL", "NVDA"]


@pytest.mark.unit
def test_list_tickers_for_date_empty_when_no_logs(isolated_state):
    assert sr.list_tickers_for_date("2026-05-08") == []


@pytest.mark.unit
def test_validate_ticker_for_trigger_rejects_bad_regex(tmp_path):
    wl = tmp_path / "wl.txt"
    wl.write_text("NVDA\n", encoding="utf-8")
    ok, reason = sr.validate_ticker_for_trigger("not-a-ticker", watchlist_path=wl)
    assert not ok
    assert "regex" in reason


@pytest.mark.unit
def test_validate_ticker_for_trigger_rejects_not_in_watchlist(tmp_path):
    wl = tmp_path / "wl.txt"
    wl.write_text("NVDA\n", encoding="utf-8")
    ok, reason = sr.validate_ticker_for_trigger("AAPL", watchlist_path=wl)
    assert not ok
    assert "not in watchlist" in reason


@pytest.mark.unit
def test_validate_ticker_for_trigger_accepts_valid(tmp_path):
    wl = tmp_path / "wl.txt"
    wl.write_text("NVDA\nAAPL\n# comment\nMSFT  # inline comment\n", encoding="utf-8")
    ok, _ = sr.validate_ticker_for_trigger("MSFT", watchlist_path=wl)
    assert ok


@pytest.mark.unit
def test_validate_ticker_for_trigger_accepts_exchange_qualified(tmp_path):
    wl = tmp_path / "wl.txt"
    wl.write_text("BRK.B\n", encoding="utf-8")
    ok, _ = sr.validate_ticker_for_trigger("BRK.B", watchlist_path=wl)
    assert ok


@pytest.mark.unit
def test_summarize_progress_handles_none():
    s = sr.summarize_progress(None)
    assert s["exists"] is False
    assert s["completed_count"] == 0
    assert s["cost_so_far_usd"] == 0.0


@pytest.mark.unit
def test_summarize_progress_full_dict():
    progress = {
        "run_id": "r1",
        "trade_date": "2026-05-08",
        "watchlist": ["NVDA", "AAPL"],
        "completed_tickers": [{"ticker": "NVDA", "rating": "Buy", "completed_at": "x"}],
        "failed_tickers": [],
        "cost_so_far_usd": 4.20,
        "current_ticker": "AAPL",
        "current_agent_stage": "bull_researcher",
        "heartbeat_at": _now_iso(0),
    }
    s = sr.summarize_progress(progress)
    assert s["exists"] is True
    assert s["completed_count"] == 1
    assert s["watchlist_size"] == 2
    assert s["cost_so_far_usd"] == 4.20
    assert s["current_ticker"] == "AAPL"
    assert s["stale"] is False
