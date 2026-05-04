"""CLI wrapper for ``tradingagents.signals.drift``.

Detects rolling-IC degradation + KS-distribution drift across all cached
signals (and their featurizations). See the module for thresholds and
methodology.

Usage::

    python scripts/detect_signal_drift.py
    python scripts/detect_signal_drift.py --horizon-days 21 --n-recent 30
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tradingagents.signals.cache import query_all
from tradingagents.signals.drift import (
    analyze_all_signals,
    apply_drift_actions,
    render_drift_report,
)

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    horizon_days: int = typer.Option(
        21, "--horizon-days", help="Forward-return horizon for IC computation."
    ),
    n_recent: int = typer.Option(
        30, "--n-recent", help="Last N rows per signal counted as 'recent'."
    ),
    ic_decline_threshold: float = typer.Option(
        0.05, "--ic-decline-threshold", help="Alert if IC dropped >= this in absolute terms."
    ),
    ks_drift_threshold: float = typer.Option(
        0.2,
        "--ks-drift-threshold",
        help="Alert if KS-statistic > this between recent and baseline.",
    ),
    out: Path = typer.Option(
        None,
        "--out",
        help="Markdown output path (default: claudedocs/signal-drift-<date>.md).",
    ),
    apply_actions: bool = typer.Option(
        False,
        "--apply-actions",
        help=(
            "Phase 2.5: auto-transition signals down the demotion ladder "
            "(production -> deprecated -> archived) when IC-decline alerts "
            "fire. Default off — runs in report-only mode. Use --dry-run-actions "
            "to preview what would happen without mutating the registry."
        ),
    ),
    dry_run_actions: bool = typer.Option(
        False,
        "--dry-run-actions",
        help="Preview Phase 2.5 auto-transitions without mutating the registry.",
    ),
):
    """Run drift detection across all cached signals."""
    all_rows = query_all()
    rows_by_signal: dict[str, list[dict]] = {}
    for r in all_rows:
        rows_by_signal.setdefault(r["signal_id"], []).append(r)

    if not rows_by_signal:
        console.print("[yellow]No cached signals to analyze.[/yellow]")
        raise typer.Exit(0)

    console.print(f"Analyzing {len(rows_by_signal)} signals across {len(all_rows)} cached rows...")
    reports = analyze_all_signals(
        rows_by_signal,
        horizon_days=horizon_days,
        n_recent=n_recent,
        ic_decline_threshold=ic_decline_threshold,
        ks_drift_threshold=ks_drift_threshold,
    )

    alerts = [r for r in reports if r.has_alert()]

    table = Table(title=f"Drift alerts ({len(alerts)} of {len(reports)} reports)")
    table.add_column("Signal", style="cyan")
    table.add_column("Feature", style="magenta")
    table.add_column("IC baseline", justify="right")
    table.add_column("IC recent", justify="right")
    table.add_column("IC decline", justify="right")
    table.add_column("KS", justify="right")
    table.add_column("Alerts", style="red")
    for r in sorted(alerts, key=lambda x: -(x.ic_decline or 0)):
        ic_b = f"{r.ic_baseline:+.3f}" if r.ic_baseline is not None else "—"
        ic_r = f"{r.ic_recent:+.3f}" if r.ic_recent is not None else "—"
        ic_d = f"{r.ic_decline:+.3f}" if r.ic_decline is not None else "—"
        ks = f"{r.ks_statistic:.3f}" if r.ks_statistic is not None else "—"
        flags = ", ".join(
            x
            for x in [
                "IC" if r.ic_decline_alert else "",
                "KS" if r.ks_drift_alert else "",
            ]
            if x
        )
        feat = r.feature or "—"
        table.add_row(r.signal_id, feat, ic_b, ic_r, ic_d, ks, flags)
    console.print(table)

    # Phase 2.5: auto-state-transitions on IC-decline alerts
    if apply_actions or dry_run_actions:
        actions = apply_drift_actions(reports, dry_run=dry_run_actions)
        action_label = "WOULD APPLY" if dry_run_actions else "APPLIED"
        if actions:
            action_table = Table(title=f"Phase 2.5 state transitions ({action_label})")
            action_table.add_column("Signal", style="cyan")
            action_table.add_column("From state", style="yellow")
            action_table.add_column("To state", style="red")
            action_table.add_column("Reason", style="white")
            for a in actions:
                action_table.add_row(a.signal_id, a.from_state, a.to_state, a.reason)
            console.print(action_table)
        else:
            console.print(
                "[green]No drift actions to apply (no IC-decline alerts on production/deprecated signals).[/green]"
            )

    if out is None:
        out = (
            Path("claudedocs")
            / f"signal-drift-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_drift_report(reports, horizon_days), encoding="utf-8")
    console.print(f"\nWrote {out}")


if __name__ == "__main__":
    app()
