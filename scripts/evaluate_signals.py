"""CLI wrapper for ``tradingagents.signals.evaluation``.

Reads the signal cache + computes per-signal performance metrics against
realized forward alpha. See ``tradingagents/signals/evaluation.py`` for
the math primitives + MVP scope.

Usage::

    python scripts/evaluate_signals.py
    python scripts/evaluate_signals.py --horizons 5,10,21,90
    python scripts/evaluate_signals.py --horizons 21 --out claudedocs/signal-eval.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tradingagents.signals.cache import query_all
from tradingagents.signals.evaluation import (
    evaluate_features_multi_horizon,
    evaluate_multi_horizon,
    render_multi_horizon_report,
)

console = Console()
app = typer.Typer(add_completion=False)


def _parse_horizons(spec: str) -> list[int]:
    """Comma-separated list of horizon days, e.g. '5,10,21,90'."""
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return sorted(set(out))


@app.command()
def main(
    horizons: str = typer.Option(
        "5,10,21,90",
        "--horizons",
        help="Comma-separated forward-return horizons in days (default '5,10,21,90').",
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
    """Evaluate cached signals against realized forward alpha across one or more horizons."""
    horizon_list = _parse_horizons(horizons)
    if not horizon_list:
        console.print("[red]No valid horizons given.[/red]")
        raise typer.Exit(1)

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

    horizon_label = ", ".join(f"{h}d" for h in horizon_list)
    console.print(f"Evaluating at horizons: {horizon_label}")

    multi_evaluations: dict[str, dict[int, dict]] = {}
    multi_feature_evaluations: list[dict] = []
    alpha_cache: dict[tuple[str, str, int], float | None] = {}

    for signal_id, rows in rows_by_signal.items():
        multi_evaluations[signal_id] = evaluate_multi_horizon(
            signal_id, rows, horizon_list, alpha_cache
        )
        multi_feature_evaluations.extend(
            evaluate_features_multi_horizon(signal_id, rows, horizon_list, alpha_cache)
        )

    # Console table — IC across horizons per signal
    table = Table(title=f"Per-signal IC across horizons ({horizon_label})")
    table.add_column("Signal", style="cyan")
    table.add_column("n cached", justify="right")
    table.add_column("Tickers", justify="right")
    table.add_column("n eval", justify="right")
    for h in horizon_list:
        table.add_column(f"IC@{h}d", justify="right")
    table.add_column(f"HR@{horizon_list[-1]}d", justify="right")

    by_n = sorted(
        multi_evaluations.items(),
        key=lambda kv: kv[1][horizon_list[0]]["n"],
        reverse=True,
    )
    for signal_id, by_horizon in by_n:
        ref = by_horizon[horizon_list[0]]
        ic_cells = [
            f"{by_horizon[h]['ic']:+.3f}" if by_horizon[h]["ic"] is not None else "—"
            for h in horizon_list
        ]
        last = by_horizon[horizon_list[-1]]
        hr = f"{last['hit_rate']:.1%}" if last["hit_rate"] is not None else "—"
        table.add_row(
            signal_id,
            str(ref["n"]),
            str(ref["tickers"]),
            str(last["n_eval"]),
            *ic_cells,
            hr,
        )
    console.print(table)

    # Console table — top 15 (signal, feature) by max |IC| across horizons
    if multi_feature_evaluations:
        groups: dict[tuple[str, str], dict[int, dict]] = {}
        for ev in multi_feature_evaluations:
            groups.setdefault((ev["signal_id"], ev["feature"]), {})[ev["horizon"]] = ev

        def _max_abs_ic(g: dict[int, dict]) -> float:
            ics = [g[h]["ic"] for h in horizon_list if g[h]["ic"] is not None]
            return max((abs(x) for x in ics), default=-1.0)

        sorted_groups = sorted(groups.items(), key=lambda kv: -_max_abs_ic(kv[1]))[:15]

        feat_table = Table(title="Top 15 prose features by max |IC| across horizons")
        feat_table.add_column("Signal", style="cyan")
        feat_table.add_column("Feature", style="magenta")
        feat_table.add_column("n eval", justify="right")
        for h in horizon_list:
            feat_table.add_column(f"IC@{h}d", justify="right")

        for (signal_id, feature), by_h in sorted_groups:
            ic_cells = [
                f"{by_h[h]['ic']:+.3f}" if by_h.get(h) and by_h[h]["ic"] is not None else "—"
                for h in horizon_list
            ]
            last = by_h.get(horizon_list[-1])
            n_eval_str = str(last["n_eval"]) if last else "0"
            feat_table.add_row(signal_id, feature, n_eval_str, *ic_cells)
        console.print(feat_table)

    if out is None:
        out = (
            Path("claudedocs")
            / f"signal-evaluation-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    report = render_multi_horizon_report(
        rows_by_signal,
        multi_evaluations,
        multi_feature_evaluations,
        horizon_list,
    )
    out.write_text(report, encoding="utf-8")
    console.print(f"\nWrote {out}")


if __name__ == "__main__":
    app()
