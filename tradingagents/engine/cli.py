"""Engine CLI entry points.

Usage:
    python -m tradingagents.engine run --watchlist data/watchlists/tech_weighted.txt
    python -m tradingagents.engine run --ticker NVDA
    python -m tradingagents.engine run --watchlist X.txt --dry-run

The --dry-run mode emits fake per-agent-stage events to ~/.tradingagents/engine/current/
without LLM calls. Used for dashboard development + Phase 5 SC-007 validation.
"""

from __future__ import annotations

from pathlib import Path

import typer

from tradingagents.engine.runner import EngineRunner

app = typer.Typer(help=__doc__, no_args_is_help=True)


@app.callback()
def _root() -> None:
    """Engine CLI root — forces subcommand syntax (e.g., `run`)."""


def _parse_watchlist(path: Path) -> list[str]:
    """Read tickers from a file, one per line. Comments (#) + blanks ignored."""
    tickers = []
    for line in path.read_text(encoding="utf-8").splitlines():
        # Strip inline comments + whitespace.
        token = line.split("#", 1)[0].strip()
        if token:
            tickers.append(token)
    return tickers


@app.command()
def run(
    watchlist: Path | None = typer.Option(
        None, "--watchlist", help="Path to a watchlist file (one ticker per line)."
    ),
    ticker: str | None = typer.Option(
        None, "--ticker", help="Single ticker to run (alternative to --watchlist)."
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Emit fake per-agent-stage events without LLM calls (FR-008).",
    ),
    state_dir: Path | None = typer.Option(
        None,
        "--state-dir",
        help=(
            "Override the engine state dir (default: ~/.tradingagents/engine). "
            "Used by dashboard_smoke.sh to isolate dry-run writes from production state."
        ),
    ),
):
    """Run the engine over a watchlist or a single ticker."""
    if watchlist and ticker:
        typer.echo("ERROR: pass either --watchlist OR --ticker, not both", err=True)
        raise typer.Exit(2)
    if not watchlist and not ticker:
        typer.echo("ERROR: pass either --watchlist or --ticker", err=True)
        raise typer.Exit(2)

    tickers = [ticker] if ticker else _parse_watchlist(watchlist)
    typer.echo(f"Running engine over {len(tickers)} ticker(s); dry_run={dry_run}")

    if state_dir is not None:
        runner = EngineRunner(run_dir=state_dir / "current")
    else:
        runner = EngineRunner()
    final = runner.run(tickers, dry_run=dry_run)

    typer.echo(
        f"\nrun_id={final.run_id}  trade_date={final.trade_date}  "
        f"completed={len(final.completed_tickers)}  failed={len(final.failed_tickers)}  "
        f"cost=${final.cost_so_far_usd:.2f}"
    )


def main() -> None:
    """Entry point for `python -m tradingagents.engine`."""
    app()


if __name__ == "__main__":
    main()
