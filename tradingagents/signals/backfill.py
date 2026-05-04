"""Backfill signal cache from existing state logs (spec 002 Phase 0/1 helper).

Phase 0 added per-tool-call cache writes inside ``route_to_vendor``, but
only NEW propagates after the Phase 0 commit populate the cache.
Pre-existing state logs at ``~/.tradingagents/logs/<TICKER>/`` contain
ANALYST-SYNTHESIS-level outputs (market_report, news_report,
fundamentals_report, investment_plan, sentiment_report,
final_trade_decision) which are themselves valid signals at a coarser
grain than per-tool calls.

This module registers six synthesis-level signal_ids and walks every
``full_states_log_<DATE>.json`` to populate the cache from them.
Idempotent (uses INSERT OR REPLACE under the hood). Lives in the package
so the script CLI is a thin wrapper that tests can bypass.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

from tradingagents.signals.cache import record_value
from tradingagents.signals.registry import register_signal

# Synthesis-level signal definitions. signal_id is the field name in the
# state log JSON; fetcher is the framework component that produces it.
SYNTHESIS_SIGNALS: list[tuple[str, str, str]] = [
    (
        "market_report",
        "Market analyst synthesis (technicals + macro)",
        "tradingagents.agents.analysts.market_analyst",
    ),
    (
        "news_report",
        "News analyst synthesis (per-ticker + global news)",
        "tradingagents.agents.analysts.news_analyst",
    ),
    (
        "fundamentals_report",
        "Fundamentals analyst synthesis",
        "tradingagents.agents.analysts.fundamentals_analyst",
    ),
    (
        "sentiment_report",
        "Social/sentiment analyst synthesis",
        "tradingagents.agents.analysts.social_analyst",
    ),
    (
        "investment_plan",
        "Research manager bull/bear synthesis",
        "tradingagents.agents.managers.research_manager",
    ),
    (
        "final_trade_decision",
        "Portfolio manager final decision",
        "tradingagents.agents.managers.portfolio_manager",
    ),
]


def default_logs_dir() -> Path:
    """Default to ~/.tradingagents/logs/ unless overridden."""
    return Path(os.path.expanduser("~/.tradingagents/logs"))


def register_synthesis_signals() -> None:
    """Register the 6 synthesis-level signals (idempotent)."""
    for signal_id, name, fetcher in SYNTHESIS_SIGNALS:
        register_signal(
            signal_id=signal_id,
            name=name,
            fetcher=fetcher,
            inputs=["ticker", "trade_date"],
            output_type="markdown",
            horizon_days=21,
            state="production",
        )


def walk_state_logs(logs_dir: Path) -> Iterator[tuple[str, Path]]:
    """Yield (ticker, state_log_path) tuples from logs_dir."""
    for ticker_dir in sorted(logs_dir.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        strategy_logs = ticker_dir / "TradingAgentsStrategy_logs"
        if not strategy_logs.exists():
            continue
        for log_path in sorted(strategy_logs.glob("full_states_log_*.json")):
            yield ticker, log_path


def backfill_one(ticker: str, log_path: Path, dry_run: bool) -> dict:
    """Process one state log; return per-signal write counts."""
    counts: dict[str, int] = {sid: 0 for sid, _, _ in SYNTHESIS_SIGNALS}
    counts["__skipped__"] = 0
    try:
        with open(log_path, encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        counts["__skipped__"] += 1
        return counts

    trade_date = state.get("trade_date")
    state_ticker = state.get("company_of_interest", ticker)
    if not trade_date:
        counts["__skipped__"] += 1
        return counts

    trade_date = str(trade_date)[:10]

    for signal_id, _, _ in SYNTHESIS_SIGNALS:
        value = state.get(signal_id)
        if not value:
            continue
        if not isinstance(value, str):
            # investment_debate_state and risk_debate_state are dicts; skip.
            continue
        if not dry_run:
            record_value(
                signal_id=signal_id,
                ticker=state_ticker,
                date=trade_date,
                value=value,
                fetcher_version="synthesis_v1",
            )
        counts[signal_id] += 1
    return counts
