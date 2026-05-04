"""CLI wrapper for ``tradingagents.signals.backfill``.

Backfill the signal cache from existing state logs. Synthesis-level
signal_ids (market_report, news_report, fundamentals_report,
sentiment_report, investment_plan, final_trade_decision) are populated
from ``~/.tradingagents/logs/<TICKER>/full_states_log_<DATE>.json``.

Usage::

    python scripts/backfill_signal_cache.py
    python scripts/backfill_signal_cache.py --dry-run
    python scripts/backfill_signal_cache.py --logs-dir /path/to/logs
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from tradingagents.signals.backfill import (
    SYNTHESIS_SIGNALS,
    backfill_one,
    default_logs_dir,
    register_synthesis_signals,
    walk_state_logs,
)

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    logs_dir: Path = typer.Option(
        None,
        "--logs-dir",
        help="Path to the logs directory (default: ~/.tradingagents/logs).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Walk logs and report what would be written; do not modify the cache.",
    ),
):
    """Backfill the signal cache from existing state logs."""
    target = logs_dir or default_logs_dir()
    if not target.exists():
        console.print(f"[red]logs dir does not exist: {target}[/red]")
        raise typer.Exit(1)

    console.print(f"Logs dir: {target}")
    console.print(f"Dry run: {dry_run}")
    console.print()

    if not dry_run:
        register_synthesis_signals()
        console.print(f"Registered {len(SYNTHESIS_SIGNALS)} synthesis-level signals.")
        console.print()

    total_counts: dict[str, int] = {sid: 0 for sid, _, _ in SYNTHESIS_SIGNALS}
    total_counts["__skipped__"] = 0
    log_count = 0
    ticker_set: set[str] = set()

    for ticker, log_path in walk_state_logs(target):
        log_count += 1
        ticker_set.add(ticker)
        counts = backfill_one(ticker, log_path, dry_run)
        for k, v in counts.items():
            total_counts[k] = total_counts.get(k, 0) + v

    console.print(f"\nProcessed {log_count} state logs across {len(ticker_set)} tickers.")
    console.print()
    console.print("[bold]Per-signal cache writes:[/bold]")
    for signal_id, _, _ in SYNTHESIS_SIGNALS:
        n = total_counts.get(signal_id, 0)
        console.print(f"  {signal_id:30s} {n:5d}")
    skipped = total_counts.get("__skipped__", 0)
    if skipped:
        console.print(f"  [yellow]skipped logs: {skipped}[/yellow]")

    written_total = sum(total_counts.get(sid, 0) for sid, _, _ in SYNTHESIS_SIGNALS)
    console.print(
        f"\n[bold]Total cache rows {'(would be) ' if dry_run else ''}written: {written_total}[/bold]"
    )


if __name__ == "__main__":
    app()
