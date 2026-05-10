"""TradingAgents dashboard — FastAPI app (spec 250-dashboard-ui Phase 2 MVP).

7 routes per FR-009:
  GET  /                           today's run summary
  GET  /live                       current-run viewer (HTML)
  GET  /tickers/{date}             ratings table for a date
  GET  /ticker/{ticker}/{date}     full debate prose
  GET  /portfolio                  paper portfolio panel
  GET  /api/poll                   JSON polling endpoint (FR-014)
  POST /trigger/{ticker}           ad-hoc run (firewalled per FR-010)

Per FR-018 every page shows the "Simulation only — not financial advice"
banner (Constitution IV).
Per FR-017 Hold renders as a first-class rating, not as empty.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from tradingagents.dashboard import state_reader as sr

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(
    title="TradingAgents Dashboard",
    description="Read-only operator surface (Phase 2 MVP).",
    version="0.2.0",
)


# ----------------------------------------------------------------- HEALTH/POLL


@app.get("/health", response_class=PlainTextResponse)
def health() -> str:
    """Liveness probe for systemd / Caddy."""
    return "ok"


@app.get("/api/poll")
def api_poll(since: str | None = None) -> JSONResponse:
    """FR-014: JSON polling for the live page. Returns current progress + new
    events since the `since` timestamp (incremental update for the frontend)."""
    progress = sr.read_progress()
    events = sr.tail_events(limit=100, since_ts=since)
    return JSONResponse(
        {
            "progress": progress,
            "events": events,
            "stale": sr.is_run_stale(progress),
        }
    )


# ------------------------------------------------------------------- TODAY (GET /)


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    summary = sr.summarize_progress(sr.read_progress())
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "summary": summary,
            "title": f"Trade date {summary['trade_date'] or '(none)'}",
        },
    )


# ----------------------------------------------------------------- LIVE (GET /live)


@app.get("/live", response_class=HTMLResponse)
def live(request: Request) -> HTMLResponse:
    summary = sr.summarize_progress(sr.read_progress())
    events = sr.tail_events(limit=50)
    return templates.TemplateResponse(
        request=request,
        name="live.html",
        context={
            "summary": summary,
            "events": events,
            "title": "Live run",
        },
    )


# -------------------------------------------------------- TICKERS (GET /tickers/{date})


@app.get("/tickers/{date}", response_class=HTMLResponse)
def tickers_for_date(request: Request, date: str) -> HTMLResponse:
    if not sr.DATE_REGEX.match(date):
        raise HTTPException(400, f"date must be ISO YYYY-MM-DD; got {date!r}")
    tickers = sr.list_tickers_for_date(date)
    # Build per-ticker summary from the state log (rating + filter audit).
    rows = []
    for t in tickers:
        log = sr.read_ticker_state_log(t, date)
        if log is None:
            continue
        rating = _extract_rating(log.get("final_trade_decision", ""))
        rows.append({"ticker": t, "rating": rating})
    return templates.TemplateResponse(
        request=request,
        name="tickers.html",
        context={
            "trade_date": date,
            "rows": rows,
            "title": f"Tickers — {date}",
        },
    )


def _extract_rating(decision_md: str) -> str:
    """Pull the 5-tier rating from the PM's markdown (same regex SignalProcessor uses)."""
    m = re.search(r"\*\*Rating\*\*:\s*(Buy|Overweight|Hold|Underweight|Sell)", decision_md)
    return m.group(1) if m else "?"


# ------------------------------------------------- TICKER (GET /ticker/{ticker}/{date})


@app.get("/ticker/{ticker}/{date}", response_class=HTMLResponse)
def ticker_detail(request: Request, ticker: str, date: str) -> HTMLResponse:
    if not sr.TICKER_REGEX.match(ticker):
        raise HTTPException(400, f"ticker fails regex {sr.TICKER_REGEX.pattern}")
    if not sr.DATE_REGEX.match(date):
        raise HTTPException(400, f"date must be ISO YYYY-MM-DD; got {date!r}")
    log = sr.read_ticker_state_log(ticker, date)
    if log is None:
        raise HTTPException(404, f"no state log for {ticker} on {date}")
    return templates.TemplateResponse(
        request=request,
        name="ticker.html",
        context={
            "ticker": ticker,
            "trade_date": date,
            "log": log,
            "rating": _extract_rating(log.get("final_trade_decision", "")),
            "title": f"{ticker} — {date}",
        },
    )


# ------------------------------------------------------ PORTFOLIO (GET /portfolio)


@app.get("/portfolio", response_class=HTMLResponse)
def portfolio(request: Request, portfolio_id: str = "live") -> HTMLResponse:
    p = sr.read_portfolio(portfolio_id)
    return templates.TemplateResponse(
        request=request,
        name="portfolio.html",
        context={
            "portfolio_id": portfolio_id,
            "portfolio": p,
            "all_ids": sr.list_portfolio_ids(),
            "title": f"Portfolio: {portfolio_id}",
        },
    )


# ----------------------------------------------- TRIGGER (POST /trigger/{ticker})


@app.post("/trigger/{ticker}")
def trigger_ticker(ticker: str) -> JSONResponse:
    """FR-011 + FR-012 + FR-013: validate ticker + spawn engine via systemd-run.

    FR-010: this endpoint is only reachable from 127.0.0.1 (Caddy doesn't proxy
    /trigger/*). The dashboard itself binds 0.0.0.0 inside the container; the
    Quadlet PublishPort=127.0.0.1:8000 ensures only-localhost from the host side.
    """
    ok, reason = sr.validate_ticker_for_trigger(ticker)
    if not ok:
        raise HTTPException(400, reason)

    # FR-013: refuse if engine already running.
    from tradingagents.engine.lock import is_locked, lock_holder_pid

    if is_locked():
        raise HTTPException(409, f"engine busy (lock held by PID {lock_holder_pid() or 'unknown'})")

    # FR-012: systemd-run --user --unit=...
    if not shutil.which("systemd-run"):
        raise HTTPException(500, "systemd-run not available on this host")

    unit_name = f"tradingagents-engine-adhoc@{ticker}"
    cmd = [
        "systemctl",
        "start",
        f"{unit_name}.service",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise HTTPException(
            500,
            f"systemctl start failed (rc={result.returncode}): {result.stderr.strip()[:300]}",
        )

    return JSONResponse({"status": "started", "ticker": ticker, "unit": unit_name})
