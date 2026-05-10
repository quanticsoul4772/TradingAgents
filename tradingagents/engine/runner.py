"""Engine runner — orchestrates propagates over a watchlist with progress.json
heartbeat + events.jsonl per-stage events (specs/250-dashboard-ui/spec.md).

This module is the writer side of the dashboard contract. The dashboard backend
(tradingagents/dashboard/, future Phase 2) is the read-only consumer.
"""

from __future__ import annotations

import csv
import logging
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from tradingagents.engine.lock import ENGINE_DIR, engine_lock
from tradingagents.engine.schemas import (
    AgentStage,
    CompletedTicker,
    Event,
    EventType,
    FailedTicker,
    ProgressFile,
)

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SEC = 10


def _now_iso() -> str:
    """ISO 8601 UTC timestamp with seconds precision (FR-006)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_run_id() -> str:
    """run_id format per FR-024: <ISO date>T<HHMMSS>Z UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _trade_date_today() -> str:
    """trade_date per FR-025: ISO date in America/New_York."""
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


PropagateFn = Callable[[str, str], str]
"""Type of a propagate callable: (ticker, trade_date) -> rating."""


class EngineRunner:
    """Wraps the existing TradingAgentsGraph.propagate orchestration with
    progress.json + events.jsonl heartbeat writes for the dashboard.

    Per FR-001 + FR-005, the engine is the place where per-agent-stage events
    will be wired via graph.astream() in Phase 1b. This MVP emits coarse
    ticker_started / ticker_finished events for real runs and full per-stage
    fake events for --dry-run mode.
    """

    def __init__(
        self,
        run_dir: Path = ENGINE_DIR / "current",
        propagate_fn: PropagateFn | None = None,
    ):
        """
        Args:
            run_dir: directory where progress.json + events.jsonl are written.
                Defaults to ~/.tradingagents/engine/current.
            propagate_fn: callable (ticker, trade_date) -> rating. Defaults to
                lazily-imported TradingAgentsGraph.propagate. Test injection
                point — pass a stub to avoid importing the framework.
        """
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.progress_path = self.run_dir / "progress.json"
        self.events_path = self.run_dir / "events.jsonl"
        self.run_id = _generate_run_id()
        self.trade_date = _trade_date_today()
        self._propagate_fn = propagate_fn
        self._heartbeat_thread: threading.Thread | None = None
        self._heartbeat_stop = threading.Event()
        self._progress: ProgressFile | None = None

    # ------------------------------------------------------------------ writers

    def _write_progress_atomic(self) -> None:
        """Atomic write to progress.json (FR-006). Refreshes heartbeat_at."""
        if self._progress is None:
            return
        self._progress.heartbeat_at = _now_iso()
        tmp = self.progress_path.with_suffix(".json.tmp")
        tmp.write_text(self._progress.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp, self.progress_path)

    def _emit_event(
        self,
        event_type: EventType,
        *,
        ticker: str | None = None,
        agent_stage: AgentStage | None = None,
        payload: dict | None = None,
    ) -> None:
        """Append one line to events.jsonl per FR-021."""
        evt = Event(
            ts=_now_iso(),
            run_id=self.run_id,
            ticker=ticker,
            agent_stage=agent_stage,
            event_type=event_type,
            payload=payload or {},
        )
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(evt.model_dump_json() + "\n")

    # ------------------------------------------------------------- heartbeat

    def _heartbeat_loop(self) -> None:
        """Refresh progress.json heartbeat_at every HEARTBEAT_INTERVAL_SEC."""
        while not self._heartbeat_stop.wait(HEARTBEAT_INTERVAL_SEC):
            try:
                self._write_progress_atomic()
            except Exception as exc:  # noqa: BLE001
                logger.warning("heartbeat write failed: %s", exc)

    # ------------------------------------------------------------- public API

    def run(self, watchlist: list[str], dry_run: bool = False) -> ProgressFile:
        """Run engine over watchlist. Acquires lock, writes progress + events.

        Args:
            watchlist: list of tickers to propagate
            dry_run: if True, emit fake per-stage events without LLM calls
                (FR-008). Used for dashboard development + Phase 5 SC-007 dry-run.

        Returns:
            Final ProgressFile state.

        Raises:
            EngineBusyError: another engine process is running (FR-004).
        """
        with engine_lock():
            self._progress = ProgressFile(
                run_id=self.run_id,
                started_at=_now_iso(),
                trade_date=self.trade_date,
                watchlist=watchlist,
                heartbeat_at=_now_iso(),
            )
            # Reset events.jsonl for this run (one file per run; dashboard
            # tails the current/ dir).
            if self.events_path.exists():
                self.events_path.unlink()

            self._write_progress_atomic()
            self._emit_event(
                EventType.RUN_STARTED, payload={"watchlist": watchlist, "dry_run": dry_run}
            )

            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

            try:
                for ticker in watchlist:
                    self._run_ticker(ticker, dry_run=dry_run)
            finally:
                self._heartbeat_stop.set()
                self._heartbeat_thread.join(timeout=5)
                self._progress.current_ticker = None
                self._progress.current_ticker_started_at = None
                self._progress.current_agent_stage = None
                self._write_progress_atomic()
                # FR-007: paper-trade integration after the run completes.
                # Skipped on dry-run (signals are fake; would corrupt paper portfolio).
                if not dry_run and self._progress.completed_tickers:
                    try:
                        self._run_paper_trade_step()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("paper_trade.py step failed: %s", exc)
                        self._emit_event(
                            EventType.ERROR,
                            payload={"phase": "paper_trade_step", "error": str(exc)},
                        )
                self._emit_event(EventType.RUN_FINISHED)

            return self._progress

    # ----------------------------------------------------------- per-ticker

    def _run_ticker(self, ticker: str, dry_run: bool = False) -> None:
        assert self._progress is not None
        self._progress.current_ticker = ticker
        self._progress.current_ticker_started_at = _now_iso()
        self._progress.current_agent_stage = None
        self._write_progress_atomic()
        self._emit_event(EventType.TICKER_STARTED, ticker=ticker)

        try:
            rating = self._dry_run_ticker(ticker) if dry_run else self._real_run_ticker(ticker)
            self._progress.completed_tickers.append(
                CompletedTicker(ticker=ticker, rating=rating, completed_at=_now_iso())
            )
            self._emit_event(EventType.TICKER_FINISHED, ticker=ticker, payload={"rating": rating})
        except Exception as exc:  # noqa: BLE001
            self._progress.failed_tickers.append(
                FailedTicker(ticker=ticker, error=str(exc), failed_at=_now_iso())
            )
            self._emit_event(
                EventType.TICKER_FAILED,
                ticker=ticker,
                payload={"error": str(exc)},
            )
            logger.exception("ticker %s failed", ticker)
        finally:
            self._write_progress_atomic()

    def _dry_run_ticker(self, ticker: str) -> str:
        """FR-008: emit fake per-agent-stage events without LLM calls.

        Walks all 12 AgentStage enum values, emitting agent_started + agent_finished
        with a small sleep between to keep timestamps distinct. Returns "Hold".
        """
        assert self._progress is not None
        for stage in AgentStage:
            self._progress.current_agent_stage = stage
            self._write_progress_atomic()
            self._emit_event(EventType.AGENT_STARTED, ticker=ticker, agent_stage=stage)
            time.sleep(0.05)
            self._emit_event(EventType.AGENT_FINISHED, ticker=ticker, agent_stage=stage)
        return "Hold"

    def _real_run_ticker(self, ticker: str) -> str:
        """Real run with per-agent-stage events (FR-001 + FR-005).

        Wires an EngineEventCallback into propagate's callbacks chain so each
        LangGraph node start/end becomes an agent_started/agent_finished event.
        Test injection: the propagate_fn override path skips the callback wiring
        (tests pass a stub returning a string directly).
        """
        if self._propagate_fn is not None:
            return self._propagate_fn(ticker, self.trade_date)

        # Lazy import to avoid pulling LangChain into test process startup.
        from tradingagents.engine.callbacks import EngineEventCallback

        assert self._progress is not None

        def _on_started(stage: AgentStage) -> None:
            assert self._progress is not None
            self._progress.current_agent_stage = stage
            self._write_progress_atomic()
            self._emit_event(EventType.AGENT_STARTED, ticker=ticker, agent_stage=stage)

        def _on_finished(stage: AgentStage) -> None:
            self._emit_event(EventType.AGENT_FINISHED, ticker=ticker, agent_stage=stage)

        callback = EngineEventCallback(on_stage_started=_on_started, on_stage_finished=_on_finished)
        return _default_propagate(ticker, self.trade_date, callbacks=[callback])

    # ---------------------------------------------------------- paper trade

    def _signals_csv_path(self) -> Path:
        return self.run_dir / "signals.csv"

    def _write_signals_csv(self) -> Path:
        """Write completed_tickers as a paper_trade.py-consumable CSV per
        specs/002-paper-trading-harness/contracts/signals_csv.md.

        Required columns: ticker, analysis_date, rating.
        """
        assert self._progress is not None
        csv_path = self._signals_csv_path()
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["ticker", "analysis_date", "rating", "error"])
            writer.writeheader()
            for ct in self._progress.completed_tickers:
                writer.writerow(
                    {
                        "ticker": ct.ticker,
                        "analysis_date": self.trade_date,
                        "rating": ct.rating,
                        "error": "",
                    }
                )
            for ft in self._progress.failed_tickers:
                writer.writerow(
                    {
                        "ticker": ft.ticker,
                        "analysis_date": self.trade_date,
                        "rating": "Hold",
                        "error": ft.error,
                    }
                )
        return csv_path

    def _run_paper_trade_step(self) -> None:
        """FR-007: spawn `paper_trade.py step --signals-csv ... --portfolio-id live`.

        Subprocess (not in-process) so paper_trade's typer/exit semantics are
        clean and a paper_trade crash doesn't propagate into the engine. Run
        synchronously after all tickers finish so the dashboard sees the
        portfolio update reflected in the same poll cycle as RUN_FINISHED.
        """
        csv_path = self._write_signals_csv()
        repo_root = Path(__file__).resolve().parents[2]
        script = repo_root / "scripts" / "paper_trade.py"
        cmd = [
            sys.executable,
            str(script),
            "step",
            "--signals-csv",
            str(csv_path),
            "--portfolio-id",
            "live",
            "--date",
            self.trade_date,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(
                f"paper_trade.py step exited {result.returncode}: {result.stderr.strip()[:500]}"
            )


def _default_propagate(ticker: str, trade_date: str, callbacks: list | None = None) -> str:
    """Lazy-import the framework so test code can construct EngineRunner without
    pulling in TradingAgentsGraph (which loads LLM clients).

    Spec 250 Phase 1b: propagates ``callbacks`` through to the LangGraph for
    per-agent-stage event emission (FR-005).
    """
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    ta = TradingAgentsGraph(config=DEFAULT_CONFIG.copy())
    _, rating = ta.propagate(ticker, trade_date, callbacks=callbacks)
    return rating
