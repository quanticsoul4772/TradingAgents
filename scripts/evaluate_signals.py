"""CLI wrapper for ``tradingagents.signals.evaluation``.

Reads the signal cache + computes per-signal performance metrics against
realized forward alpha. See ``tradingagents/signals/evaluation.py`` for
the math primitives + MVP scope.

Usage::

    python scripts/evaluate_signals.py
    python scripts/evaluate_signals.py --horizon-days 21 --out claudedocs/signal-eval.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tradingagents.signals.cache import query_all
from tradingagents.signals.evaluation import _evaluate_signal, render_report

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    horizon_days: int = typer.Option(
        21, "--horizon-days", help="Forward-return horizon for IC + hit rate (default 21)."
    ),
    out: Path = typer.Option(
        None,
        "--out",
        help="Markdown output path (default: claudedocs/signal-evaluation-<date>.md).",
    ),
    signal: str = typer.Option(
        None,
        "--signal",
        help="Limit evaluation to a single signal_id (otherwise: all cached).",
    ),
):
    """Evaluate cached signals against realized forward alpha."""
    if signal:
        rows = query_all(signal_id=signal)
        rows_by_signal = {signal: rows}
        console.print(f"Loaded {len(rows)} cached rows for signal '{signal}'.")
    else:
        all_rows = query_all()
        rows_by_signal: dict[str, list[dict]] = {}
        for r in all_rows:
            rows_by_signal.setdefault(r["signal_id"], []).append(r)
        console.print(f"Loaded {len(all_rows)} cached rows across {len(rows_by_signal)} signals.")

    if not rows_by_signal:
        console.print(
            "[yellow]No cached signals to evaluate. Run a propagate first or use backfill_signal_cache.py.[/yellow]"
        )
        raise typer.Exit(0)

    console.print(f"Evaluating at {horizon_days}-day horizon...")
    evaluations: list[dict] = []
    for signal_id, rows in rows_by_signal.items():
        ev = _evaluate_signal(signal_id, rows, horizon_days)
        evaluations.append(ev)

    table = Table(title=f"Signal evaluation summary ({horizon_days}d horizon)")
    table.add_column("Signal", style="cyan")
    table.add_column("n cached", justify="right")
    table.add_column("Tickers", justify="right")
    table.add_column("Dates", justify="right")
    table.add_column("n eval", justify="right")
    table.add_column("IC", justify="right")
    table.add_column("Hit rate", justify="right")
    for ev in sorted(evaluations, key=lambda x: x["n"], reverse=True):
        ic_str = f"{ev['ic']:+.3f}" if ev["ic"] is not None else "—"
        hit_str = f"{ev['hit_rate']:.1%}" if ev["hit_rate"] is not None else "—"
        table.add_row(
            ev["signal_id"],
            str(ev["n"]),
            str(ev["tickers"]),
            str(ev["dates"]),
            str(ev["n_eval"]),
            ic_str,
            hit_str,
        )
    console.print(table)

    if out is None:
        out = (
            Path("claudedocs")
            / f"signal-evaluation-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(rows_by_signal, evaluations, horizon_days)
    out.write_text(report, encoding="utf-8")
    console.print(f"\nWrote {out}")


if __name__ == "__main__":
    app()
