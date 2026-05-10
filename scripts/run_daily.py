"""Live signals product — daily orchestrator.

Runs the full daily flow as one command:
    1. `daily_signals.py` — generate today's signals digest + CSV
    2. `paper_trade.py step` — apply signals to the paper portfolio
    3. `paper_trade.py status` — print portfolio state

Cost: ~$2-4 LLM (1 Opus + 1 Haiku per ticker × ~25 tickers via the
default `data/watchlists/tech_weighted.txt`). Step 2 + 3 are $0.

State persists at `~/.tradingagents/paper/<portfolio_id>.{json,events.jsonl}`.
Re-running on the same date is idempotent (paper_trade step checks for
duplicate event-IDs).

Per Constitution Principle IV (No Production Claims): this is paper
trading. No real capital. Past performance of simulated trades does not
predict future results.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import typer

app = typer.Typer(help=__doc__)

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = Path.home() / ".tradingagents" / "paper"


def _last_business_day(d: date) -> date:
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def _count_tickers(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


@app.command()
def main(
    tickers: Path = typer.Option(
        REPO_ROOT / "data" / "watchlists" / "tech_weighted.txt",
        "--tickers",
        help="Watchlist file (one ticker per line; # comments OK).",
    ),
    portfolio_id: str = typer.Option("live", "--portfolio-id"),
    target_date: str = typer.Option(
        "", "--date", help="ISO date (YYYY-MM-DD); default today/last-business-day."
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip cost-confirmation prompt."),
    skip_signals: bool = typer.Option(
        False, "--skip-signals", help="Skip step 1 (use existing CSV at default path)."
    ),
):
    """Run the full daily flow: signals → paper-trade step → status."""
    PAPER_DIR.mkdir(parents=True, exist_ok=True)

    if target_date:
        d = date.fromisoformat(target_date)
    else:
        d = _last_business_day(date.today())
    iso = d.isoformat()

    csv_path = PAPER_DIR / f"{portfolio_id}-{iso}-signals.csv"
    digest_path = REPO_ROOT / "claudedocs" / f"daily-signals-{iso}.md"

    n_tickers = _count_tickers(tickers)
    est_cost = n_tickers * 0.40

    typer.echo(f"\n=== live signals product — {iso} ===")
    typer.echo(f"  watchlist: {tickers} ({n_tickers} tickers)")
    typer.echo(f"  portfolio: {portfolio_id}")
    typer.echo(f"  digest:    {digest_path}")
    typer.echo(f"  csv:       {csv_path}")
    typer.echo(f"  est cost:  ~${est_cost:.2f} LLM (signals step only)")

    if not skip_signals and not yes:
        ok = typer.confirm("Proceed?", default=False)
        if not ok:
            raise typer.Exit(1)

    if not skip_signals:
        typer.echo("\n[1/3] daily_signals.py …")
        subprocess.check_call(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "daily_signals.py"),
                "--tickers",
                str(tickers),
                "--date",
                iso,
                "--out",
                str(digest_path),
                "--emit-csv",
                str(csv_path),
            ]
        )
    else:
        typer.echo("\n[1/3] daily_signals.py — skipped (--skip-signals)")

    typer.echo("\n[2/3] paper_trade.py step …")
    subprocess.check_call(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "paper_trade.py"),
            "step",
            "--signals-csv",
            str(csv_path),
            "--portfolio-id",
            portfolio_id,
            "--date",
            iso,
        ]
    )

    typer.echo("\n[3/3] paper_trade.py status …")
    subprocess.check_call(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "paper_trade.py"),
            "status",
            "--portfolio-id",
            portfolio_id,
        ]
    )

    typer.echo(f"\n=== done — digest at {digest_path} ===")


if __name__ == "__main__":
    app()
