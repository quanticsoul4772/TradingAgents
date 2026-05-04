"""CLI wrapper for ``tradingagents.signals.counterfactual``.

Runs a pre-built counterfactual rule against the cached final_trade_decision
history and reports the alpha delta.

Usage::

    python scripts/counterfactual_signal.py --rule hold-all-uw
    python scripts/counterfactual_signal.py --rule invert-all --horizon-days 21
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

from tradingagents.signals.cache import query_all
from tradingagents.signals.counterfactual import (
    hold_all_ow,
    hold_all_uw,
    invert_all_commits,
    render_counterfactual_report,
    run_counterfactual,
)

console = Console()
app = typer.Typer(add_completion=False)


_RULES = {
    "hold-all-uw": (hold_all_uw, "Hold on every UW/Sell date"),
    "hold-all-ow": (hold_all_ow, "Hold on every Buy/Overweight date"),
    "invert-all": (invert_all_commits, "Invert every directional commit (Buy↔Sell, OW↔UW)"),
}


@app.command()
def main(
    rule: str = typer.Option(
        "hold-all-uw",
        "--rule",
        help=f"Counterfactual rule. Choices: {', '.join(_RULES)}.",
    ),
    horizon_days: int = typer.Option(
        21, "--horizon-days", help="Forward-return horizon for alpha computation."
    ),
    out: Path = typer.Option(
        None,
        "--out",
        help="Markdown output path (default: claudedocs/counterfactual-<rule>-<date>.md).",
    ),
):
    """Run a counterfactual rule against cached final_trade_decision history."""
    if rule not in _RULES:
        console.print(f"[red]Unknown rule '{rule}'. Choices: {', '.join(_RULES)}[/red]")
        raise typer.Exit(1)

    rule_fn, rule_description = _RULES[rule]

    rows = query_all(signal_id="final_trade_decision")
    if not rows:
        console.print("[yellow]No cached final_trade_decision rows.[/yellow]")
        raise typer.Exit(0)

    console.print(f"Running counterfactual: '{rule}' over {len(rows)} cached pairs...")
    report = run_counterfactual(rows, rule_fn, horizon_days=horizon_days)

    console.print(
        f"Pairs: {report.n_total}, resolved: {report.n_resolved}, changed: {report.n_changed}"
    )
    if report.mean_alpha_delta is not None:
        console.print(
            f"Mean alpha delta: {report.mean_alpha_delta:+.3f}%   "
            f"Total alpha delta: {report.total_alpha_delta:+.3f}%"
        )

    if out is None:
        out = (
            Path("claudedocs")
            / f"counterfactual-{rule}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_counterfactual_report(report, description=rule_description),
        encoding="utf-8",
    )
    console.print(f"\nWrote {out}")


if __name__ == "__main__":
    app()
