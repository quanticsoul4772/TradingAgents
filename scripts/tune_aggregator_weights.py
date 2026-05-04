"""Phase 5 — grid-search weights for the deterministic aggregator.

Walks state logs, derives Signals, computes realized 21d alpha, then runs
grid search over WEIGHTS to maximize either IC vs alpha or agreement with
PM ratings. Reports best weights + train/test evaluation per SC-006.

Usage::

    python scripts/tune_aggregator_weights.py --objective ic
    python scripts/tune_aggregator_weights.py --objective agreement
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tradingagents.signals.backfill import default_logs_dir, walk_state_logs
from tradingagents.signals.bots import DEFAULT_WEIGHTS
from tradingagents.signals.evaluation import _compute_alpha
from tradingagents.signals.weight_tuning import (
    build_tuning_corpus,
    evaluate_weights,
    grid_search_weights,
    split_train_test,
)

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    logs_dir: Path = typer.Option(
        None, "--logs-dir", help="Path to logs directory (default: ~/.tradingagents/logs)."
    ),
    objective: str = typer.Option(
        "ic",
        "--objective",
        help="'ic' = max Spearman IC vs alpha; 'agreement' = max direction match with PM.",
    ),
    horizon_days: int = typer.Option(
        21, "--horizon-days", help="Forward-return horizon for alpha computation."
    ),
    train_fraction: float = typer.Option(
        0.7, "--train-fraction", help="Date-ordered train/test split fraction."
    ),
    out: Path = typer.Option(
        None,
        "--out",
        help="Markdown output path (default: claudedocs/weight-tuning-<date>.md).",
    ),
):
    """Tune aggregator WEIGHTS via grid search on the historical corpus."""
    target = logs_dir or default_logs_dir()
    if not target.exists():
        console.print(f"[red]logs dir does not exist: {target}[/red]")
        raise typer.Exit(1)

    console.print(f"Loading state logs from {target}...")

    # Step 1: load state logs + compute realized alpha
    state_log_data: list[tuple[str, dict, float | None]] = []
    for ticker, log_path in walk_state_logs(target):
        try:
            with open(log_path, encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        trade_date = state.get("trade_date")
        if not trade_date:
            continue
        date_str = str(trade_date)[:10]
        alpha = _compute_alpha(ticker, date_str, holding_days=horizon_days)
        state_log_data.append((ticker, state, alpha))

    if not state_log_data:
        console.print("[yellow]No state logs to evaluate.[/yellow]")
        raise typer.Exit(0)

    console.print(
        f"Loaded {len(state_log_data)} state logs; "
        f"{sum(1 for _, _, a in state_log_data if a is not None)} resolved at {horizon_days}d."
    )

    rows = build_tuning_corpus(state_log_data, horizon_days)

    # Step 2: train/test split
    train, test = split_train_test(rows, train_fraction=train_fraction)
    console.print(f"Train: {len(train)} rows ({train[0].date} → {train[-1].date})")
    console.print(f"Test:  {len(test)} rows ({test[0].date} → {test[-1].date})")
    console.print()

    # Step 3: baseline (DEFAULT_WEIGHTS) on both sets
    base_train = evaluate_weights(train, DEFAULT_WEIGHTS)
    base_test = evaluate_weights(test, DEFAULT_WEIGHTS)

    # Step 4: grid search on train set
    console.print(f"Grid searching weights to maximize objective='{objective}'...")
    best_weights, best_train = grid_search_weights(train, objective=objective)

    # Step 5: evaluate best_weights on test set
    best_test = evaluate_weights(test, best_weights)

    # Console output
    table = Table(title=f"Phase 5 weight tuning — objective={objective}, horizon={horizon_days}d")
    table.add_column("Metric", style="cyan")
    table.add_column("Default (train)", justify="right")
    table.add_column("Default (test)", justify="right")
    table.add_column("Tuned (train)", justify="right")
    table.add_column("Tuned (test)", justify="right")

    def _ic(ev):
        return f"{ev.ic:+.3f}" if ev.ic is not None else "—"

    def _pct(x):
        return f"{x:.1%}"

    table.add_row(
        "n total",
        str(base_train.n_total),
        str(base_test.n_total),
        str(best_train.n_total),
        str(best_test.n_total),
    )
    table.add_row(
        "n resolved",
        str(base_train.n_resolved),
        str(base_test.n_resolved),
        str(best_train.n_resolved),
        str(best_test.n_resolved),
    )
    table.add_row(
        "IC vs alpha",
        _ic(base_train),
        _ic(base_test),
        _ic(best_train),
        _ic(best_test),
    )
    table.add_row(
        "Direction agreement",
        _pct(base_train.direction_agreement),
        _pct(base_test.direction_agreement),
        _pct(best_train.direction_agreement),
        _pct(best_test.direction_agreement),
    )
    table.add_row(
        "Within ±1 tier",
        _pct(base_train.rating_within_one_tier),
        _pct(base_test.rating_within_one_tier),
        _pct(best_train.rating_within_one_tier),
        _pct(best_test.rating_within_one_tier),
    )
    console.print(table)

    weight_table = Table(title="Tuned vs default weights")
    weight_table.add_column("Bot", style="cyan")
    weight_table.add_column("Default", justify="right")
    weight_table.add_column("Tuned", justify="right")
    for bot in DEFAULT_WEIGHTS:
        weight_table.add_row(
            bot,
            f"{DEFAULT_WEIGHTS[bot]:.2f}",
            f"{best_weights.get(bot, 0.0):.2f}",
        )
    console.print(weight_table)

    # Markdown report
    if out is None:
        out = (
            Path("claudedocs")
            / f"weight-tuning-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"# Spec 001 Phase 5: Weight Tuning Report (objective={objective})")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}._")
    lines.append("")
    lines.append(
        f"**Horizon**: {horizon_days}d. **Train/test split**: {train_fraction:.0%} "
        f"date-ordered. Train n={len(train)}, test n={len(test)}."
    )
    lines.append("")
    lines.append("## Default vs tuned weights — train and test metrics")
    lines.append("")
    lines.append("| Metric | Default (train) | Default (test) | Tuned (train) | Tuned (test) |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(
        f"| IC vs α | {_ic(base_train)} | {_ic(base_test)} | {_ic(best_train)} | {_ic(best_test)} |"
    )
    lines.append(
        f"| Direction agreement | {_pct(base_train.direction_agreement)} | "
        f"{_pct(base_test.direction_agreement)} | "
        f"{_pct(best_train.direction_agreement)} | "
        f"{_pct(best_test.direction_agreement)} |"
    )
    lines.append(
        f"| Within ±1 tier | {_pct(base_train.rating_within_one_tier)} | "
        f"{_pct(base_test.rating_within_one_tier)} | "
        f"{_pct(best_train.rating_within_one_tier)} | "
        f"{_pct(best_test.rating_within_one_tier)} |"
    )
    lines.append("")
    lines.append("## Tuned weights")
    lines.append("")
    lines.append("| Bot | Default | Tuned | Δ |")
    lines.append("|---|---:|---:|---:|")
    for bot in DEFAULT_WEIGHTS:
        d = DEFAULT_WEIGHTS[bot]
        t = best_weights.get(bot, 0.0)
        lines.append(f"| `{bot}` | {d:.2f} | {t:.2f} | {t - d:+.2f} |")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        f"- Coarse grid search over weights in [0.0, 0.5] step 0.1 across "
        f"{len(DEFAULT_WEIGHTS)} bots = {6 ** len(DEFAULT_WEIGHTS)} combinations.\n"
        f"- Objective='{objective}': "
        + (
            "maximize Spearman IC of aggregator's direction_score vs realized α."
            if objective == "ic"
            else "maximize 3-tier direction agreement with actual PM rating."
        )
        + "\n"
        f"- Train/test split is date-ordered: oldest {train_fraction:.0%} → train, "
        f"newest → test. Tuning on train; reporting on both train AND test for "
        f"overfitting check (SC-006 requires test ±0.3pp of train).\n"
        f"- Aggregator (`tradingagents/signals/bots.py::aggregate`) is unchanged; "
        f"only WEIGHTS are tuned."
    )
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"\nWrote {out}")


if __name__ == "__main__":
    app()
