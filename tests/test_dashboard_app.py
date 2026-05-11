"""Route-level integration tests for the dashboard FastAPI app (spec 250 Phase 2)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from tradingagents.dashboard import app as app_module
from tradingagents.dashboard import state_reader as sr


@pytest.fixture
def isolated_dashboard(tmp_path, monkeypatch):
    eng = tmp_path / "engine"
    logs = tmp_path / "logs"
    paper = tmp_path / "paper"
    monkeypatch.setattr(sr, "ENGINE_DIR", eng)
    monkeypatch.setattr(sr, "LOGS_DIR", logs)
    monkeypatch.setattr(sr, "PAPER_DIR", paper)
    monkeypatch.setattr(sr, "CURRENT_DIR", eng / "current")
    yield {"engine": eng, "logs": logs, "paper": paper}


@pytest.fixture
def client(isolated_dashboard):
    return TestClient(app_module.app)


def _write_progress(isolated_dashboard, **fields):
    p = isolated_dashboard["engine"] / "current" / "progress.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "run_id": "2026-05-10T120000Z",
        "started_at": "2026-05-10T12:00:00Z",
        "trade_date": "2026-05-08",
        "watchlist": ["NVDA"],
        "heartbeat_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "completed_tickers": [],
        "failed_tickers": [],
        "cost_so_far_usd": 0.0,
    }
    base.update(fields)
    p.write_text(json.dumps(base), encoding="utf-8")


# ---------------------------------------------------------------- /health, /api/poll


@pytest.mark.unit
def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.text == "ok"


@pytest.mark.unit
def test_api_poll_empty_state(client):
    r = client.get("/api/poll")
    assert r.status_code == 200
    j = r.json()
    assert j["progress"] is None
    assert j["events"] == []
    assert j["stale"] is False


@pytest.mark.unit
def test_api_poll_with_progress(client, isolated_dashboard):
    _write_progress(
        isolated_dashboard,
        completed_tickers=[{"ticker": "NVDA", "rating": "Buy", "completed_at": "x"}],
    )
    r = client.get("/api/poll")
    assert r.status_code == 200
    j = r.json()
    assert j["progress"] is not None
    assert len(j["progress"]["completed_tickers"]) == 1


# ---------------------------------------------------------------- GET /


@pytest.mark.unit
def test_home_empty_state_when_no_runs(client):
    """SC-004: GET / on day 0 returns 'No runs yet' page."""
    r = client.get("/")
    assert r.status_code == 200
    assert "No runs yet" in r.text
    # FR-018 paper banner removed per user request (PR #257); spec amendment pending.


@pytest.mark.unit
def test_home_with_completed_run(client, isolated_dashboard):
    _write_progress(
        isolated_dashboard,
        completed_tickers=[
            {"ticker": "NVDA", "rating": "Buy", "completed_at": "2026-05-10T12:09:00Z"},
            {"ticker": "AAPL", "rating": "Hold", "completed_at": "2026-05-10T12:10:00Z"},
        ],
    )
    r = client.get("/")
    assert r.status_code == 200
    assert "NVDA" in r.text
    assert "AAPL" in r.text
    assert "Hold" in r.text  # FR-017: Hold renders as first-class
    assert "Trade date 2026-05-08" in r.text


# ---------------------------------------------------------------- GET /live


@pytest.mark.unit
def test_live_renders_when_no_run(client):
    r = client.get("/live")
    assert r.status_code == 200
    assert "Engine idle" in r.text


@pytest.mark.unit
def test_live_renders_in_flight(client, isolated_dashboard):
    _write_progress(
        isolated_dashboard,
        current_ticker="NVDA",
        current_agent_stage="bull_researcher",
    )
    r = client.get("/live")
    assert r.status_code == 200
    assert "in flight" in r.text
    assert "NVDA" in r.text
    assert "bull_researcher" in r.text


@pytest.mark.unit
def test_live_page_includes_htmx_polling_attributes(client):
    """Phase 3: /live page must declare HTMX hx-get + hx-trigger so the
    browser auto-polls /live/partial without manual refresh."""
    r = client.get("/live")
    assert r.status_code == 200
    # HTMX wiring on the live-content div
    assert 'hx-get="/trading/live/partial"' in r.text
    assert "every 3s" in r.text
    assert 'hx-swap="innerHTML"' in r.text
    # HTMX library loaded
    assert "htmx.org" in r.text


@pytest.mark.unit
def test_live_partial_route_returns_inner_only(client, isolated_dashboard):
    """/live/partial returns the inner content fragment WITHOUT the base layout
    — for HTMX hx-swap=innerHTML on the parent /live page."""
    _write_progress(
        isolated_dashboard,
        current_ticker="NVDA",
        current_agent_stage="bull_researcher",
    )
    r = client.get("/live/partial")
    assert r.status_code == 200
    # Has the in-flight content
    assert "NVDA" in r.text
    assert "bull_researcher" in r.text
    # Does NOT include base layout (no <html> or top nav)
    assert "<html" not in r.text.lower()
    assert "TradingAgents" not in r.text  # nav brand absent


@pytest.mark.unit
def test_live_partial_renders_idle_when_no_run(client):
    r = client.get("/live/partial")
    assert r.status_code == 200
    assert "Engine idle" in r.text


@pytest.mark.unit
def test_live_partial_renders_stale_banner(client, isolated_dashboard):
    """STALE banner shows when heartbeat > 90s + no terminal event (FR-027)."""
    from datetime import datetime, timedelta, timezone

    old_hb = (datetime.now(timezone.utc) - timedelta(seconds=300)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_progress(isolated_dashboard, heartbeat_at=old_hb)
    r = client.get("/live/partial")
    assert r.status_code == 200
    assert "STALE" in r.text


# ---------------------------------------------------------------- GET /tickers/{date}


@pytest.mark.unit
def test_tickers_rejects_bad_date(client):
    r = client.get("/tickers/not-a-date")
    assert r.status_code == 400


@pytest.mark.unit
def test_tickers_empty_when_no_logs(client):
    r = client.get("/tickers/2026-05-08")
    assert r.status_code == 200
    assert "No state logs found" in r.text


@pytest.mark.unit
def test_tickers_lists_with_ratings(client, isolated_dashboard):
    log_dir = isolated_dashboard["logs"] / "NVDA" / "TradingAgentsStrategy_logs"
    log_dir.mkdir(parents=True)
    (log_dir / "full_states_log_2026-05-08.json").write_text(
        json.dumps({"final_trade_decision": "**Rating**: Buy\nblah"}), encoding="utf-8"
    )
    r = client.get("/tickers/2026-05-08")
    assert r.status_code == 200
    assert "NVDA" in r.text
    assert "Buy" in r.text


# --------------------------------------------------- GET /ticker/{ticker}/{date}


@pytest.mark.unit
def test_ticker_detail_404_when_missing(client):
    r = client.get("/ticker/NVDA/2026-05-08")
    assert r.status_code == 404


@pytest.mark.unit
def test_ticker_detail_400_on_bad_ticker(client):
    r = client.get("/ticker/badticker/2026-05-08")
    assert r.status_code == 400


@pytest.mark.unit
def test_ticker_detail_renders_debate(client, isolated_dashboard):
    log_dir = isolated_dashboard["logs"] / "NVDA" / "TradingAgentsStrategy_logs"
    log_dir.mkdir(parents=True)
    (log_dir / "full_states_log_2026-05-08.json").write_text(
        json.dumps(
            {
                "final_trade_decision": "**Rating**: Overweight\nrationale here",
                "investment_debate_state": {"history": "Bull says X. Bear says Y."},
                "market_report": "tech indicators look good",
            }
        ),
        encoding="utf-8",
    )
    r = client.get("/ticker/NVDA/2026-05-08")
    assert r.status_code == 200
    assert "NVDA" in r.text
    assert "Overweight" in r.text
    assert "Bull says X" in r.text


# ---------------------------------------------------------------- GET /portfolio


@pytest.mark.unit
def test_portfolio_no_state(client):
    r = client.get("/portfolio")
    assert r.status_code == 200
    assert "No portfolio at" in r.text


@pytest.mark.unit
def test_portfolio_renders_state(client, isolated_dashboard):
    p = isolated_dashboard["paper"] / "live.json"
    p.parent.mkdir(parents=True)
    p.write_text(
        json.dumps(
            {
                "cash_usd": 75000.0,
                "open_positions": [{"ticker": "NVDA", "entry_date": "2026-05-08", "shares": 10}],
                "events": [{"date": "2026-05-08", "type": "ENTRY", "ticker": "NVDA"}],
            }
        ),
        encoding="utf-8",
    )
    r = client.get("/portfolio")
    assert r.status_code == 200
    assert "75000" in r.text
    assert "NVDA" in r.text


# ---------------------------------------------------------- POST /trigger/{ticker}


@pytest.mark.unit
def test_trigger_rejects_invalid_ticker(client, monkeypatch):
    """FR-011: regex validation rejects without spawning anything."""
    spawned = []
    monkeypatch.setattr(
        "tradingagents.dashboard.app.subprocess.run",
        lambda *a, **kw: (
            spawned.append(a) or type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()
        ),
    )
    r = client.post("/trigger/badticker")
    assert r.status_code == 400
    assert spawned == []


@pytest.mark.unit
def test_trigger_rejects_ticker_not_in_watchlist(client, tmp_path, monkeypatch):
    """FR-011: watchlist membership rejection."""
    wl = tmp_path / "wl.txt"
    wl.write_text("NVDA\n", encoding="utf-8")
    monkeypatch.setenv("TA_WATCHLIST", str(wl))
    spawned = []
    monkeypatch.setattr(
        "tradingagents.dashboard.app.subprocess.run",
        lambda *a, **kw: (
            spawned.append(a) or type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()
        ),
    )
    r = client.post("/trigger/AAPL")
    assert r.status_code == 400
    assert spawned == []


@pytest.mark.unit
def test_trigger_returns_409_when_engine_locked(client, tmp_path, monkeypatch):
    """FR-013: 409 when engine lock held."""
    wl = tmp_path / "wl.txt"
    wl.write_text("NVDA\n", encoding="utf-8")
    monkeypatch.setenv("TA_WATCHLIST", str(wl))
    monkeypatch.setattr("tradingagents.engine.lock.is_locked", lambda: True)
    monkeypatch.setattr("tradingagents.engine.lock.lock_holder_pid", lambda: "12345")
    r = client.post("/trigger/NVDA")
    assert r.status_code == 409
    assert "12345" in r.json()["detail"]


@pytest.mark.unit
def test_trigger_spawns_systemd_unit(client, tmp_path, monkeypatch):
    wl = tmp_path / "wl.txt"
    wl.write_text("NVDA\n", encoding="utf-8")
    monkeypatch.setenv("TA_WATCHLIST", str(wl))
    monkeypatch.setattr("tradingagents.engine.lock.is_locked", lambda: False)
    monkeypatch.setattr(
        "tradingagents.dashboard.app.shutil.which", lambda x: "/usr/bin/systemd-run"
    )
    captured = []

    def fake_run(cmd, **kw):
        captured.append(cmd)
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr("tradingagents.dashboard.app.subprocess.run", fake_run)
    r = client.post("/trigger/NVDA")
    assert r.status_code == 200
    assert r.json()["status"] == "started"
    assert r.json()["ticker"] == "NVDA"
    assert "systemctl" in captured[0][0]
    assert "tradingagents-engine-adhoc@NVDA.service" in captured[0]
