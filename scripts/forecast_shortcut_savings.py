"""Phase 3 — forecast convergence-shortcut token savings on the historical corpus.

Walks the cached state logs, derives Signals from analyst prose, and asks
"would the convergence shortcut (skip debate when 3+ Signals share a
direction with magnitude > 0.7) have fired here?" Reports skip-rate +
projected token savings before committing to the production change.

SC-004 acceptance: ≥30% reduction on shortcut-fires AND ≥15% overall.

Token-savings projection assumes the bull/bear debate stage costs roughly
N% of total propagate tokens (configurable via --debate-cost-fraction).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tradingagents.signals.backfill import default_logs_dir, walk_state_logs
from tradingagents.signals.bots import shadow_aggregate_from_state_log
from tradingagents.signals.shortcut import (
    DEFAULT_MAGNITUDE_THRESHOLD,
    DEFAULT_MIN_CONVERGING_SIGNALS,
    analyze_shortcut_corpus,
)

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    logs_dir: Path = typer.Option(
        None, "--logs-dir", help="Path to logs directory (default: ~/.tradingagents/logs)."
    ),
    min_converging: int = typer.Option(
        DEFAULT_MIN_CONVERGING_SIGNALS,
        "--min-converging",
        help="Min number of bots that must share a strong direction.",
    ),
    magnitude_threshold: float = typer.Option(
        DEFAULT_MAGNITUDE_THRESHOLD,
        "--magnitude-threshold",
        help="Per-bot magnitude threshold (in [0, 1]) to count as 'strong'.",
    ),
    debate_cost_fraction: float = typer.Option(
        0.30,
        "--debate-cost-fraction",
        help="Estimated fraction of per-propagate token cost attributable to "
        "the bull/bear debate stage. SC-004 expects ≥30% reduction when "
        "shortcut fires; a debate-cost-fraction of 0.30 means 'all debate "
        "cost saved when shortcut fires'.",
    ),
    out: Path = typer.Option(
        None,
        "--out",
        help="Markdown output (default: claudedocs/shortcut-forecast-<date>.md).",
    ),
):
    """Forecast shortcut savings across the historical corpus."""
    target = logs_dir or default_logs_dir()
    if not target.exists():
        console.print(f"[red]logs dir does not exist: {target}[/red]")
        raise typer.Exit(1)

    console.print(f"Loading state logs from {target}...")

    signals_per_propagate: list[list] = []
    for _ticker, log_path in walk_state_logs(target):
        try:
            with open(log_path, encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if not state.get("trade_date"):
            continue
        signals, _ = shadow_aggregate_from_state_log(state)
        signals_per_propagate.append(signals)

    if not signals_per_propagate:
        console.print("[yellow]No state logs to analyze.[/yellow]")
        raise typer.Exit(0)

    report = analyze_shortcut_corpus(
        signals_per_propagate,
        min_converging=min_converging,
        magnitude_threshold=magnitude_threshold,
    )

    # Token-savings projection: of the propagates that would skip, the
    # debate-cost-fraction is saved. Overall savings = skip_rate × debate_cost_fraction.
    fire_savings_pct = debate_cost_fraction  # per-fire savings
    overall_savings_pct = report.skip_rate * debate_cost_fraction

    table = Table(
        title=f"Shortcut forecast: min_converging={min_converging}, "
        f"magnitude>{magnitude_threshold}, debate_cost={debate_cost_fraction:.0%}"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Total propagates", str(report.n_total))
    table.add_row(
        "Would-skip (any)",
        f"{report.n_would_skip} ({report.skip_rate:.1%})",
    )
    table.add_row("  Bullish convergence", str(report.n_bullish_skip))
    table.add_row("  Bearish convergence", str(report.n_bearish_skip))
    table.add_row(
        "Per-fire token savings",
        f"{fire_savings_pct:.0%} (assumed)",
    )
    table.add_row(
        "Overall corpus savings",
        f"{overall_savings_pct:.1%}",
    )
    table.add_row(
        "SC-004 (overall ≥15%)",
        "PASS" if overall_savings_pct >= 0.15 else f"FAIL ({overall_savings_pct:.1%} < 15%)",
    )
    table.add_row(
        "SC-004 (per-fire ≥30%)",
        "PASS" if fire_savings_pct >= 0.30 else f"FAIL ({fire_savings_pct:.0%} < 30%)",
    )
    console.print(table)

    if out is None:
        out = (
            Path("claudedocs")
            / f"shortcut-forecast-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Spec 001 Phase 3: Convergence-Shortcut Forecast")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}._")
    lines.append("")
    lines.append(
        f"**Corpus**: {report.n_total} state logs.\n"
        f"**Threshold**: {min_converging}+ bots with magnitude>{magnitude_threshold} sharing a direction.\n"
        f"**Debate cost assumption**: {debate_cost_fraction:.0%} of per-propagate tokens.\n"
    )
    lines.append("## Forecast")
    lines.append("")
    lines.append(
        f"| Outcome | Count | % |\n"
        f"|---|---:|---:|\n"
        f"| Would skip debate | {report.n_would_skip} | {report.skip_rate:.1%} |\n"
        f"| - bullish convergence | {report.n_bullish_skip} | "
        f"{report.n_bullish_skip / max(1, report.n_total):.1%} |\n"
        f"| - bearish convergence | {report.n_bearish_skip} | "
        f"{report.n_bearish_skip / max(1, report.n_total):.1%} |\n"
        f"| Would NOT skip | {report.n_total - report.n_would_skip} | "
        f"{1 - report.skip_rate:.1%} |"
    )
    lines.append("")
    lines.append(
        f"**Projected per-fire token savings**: {fire_savings_pct:.0%}\n"
        f"**Projected overall corpus token savings**: {overall_savings_pct:.1%}\n"
    )
    lines.append("## SC-004 acceptance")
    lines.append("")
    lines.append(
        f"- Overall ≥15%: "
        f"{'PASS' if overall_savings_pct >= 0.15 else 'FAIL'}\n"
        f"- Per-fire ≥30%: "
        f"{'PASS' if fire_savings_pct >= 0.30 else 'FAIL (assumption)'}\n"
    )
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "- Each historical propagate's analyst prose reports are featurized "
        "into Signals via `derive_signal_from_prose` (Phase 1.5+ unigram +"
        " bigram features).\n"
        "- `should_skip_debate(signals)` checks if 3+ Signals share a strong "
        "direction (magnitude > 0.7).\n"
        "- This is a **forecast**: the actual debate-cost fraction is an "
        "assumption (default 30%), not measured. Production wiring (Phase 3.5) "
        "would replace the assumption with measured per-stage token spend.\n"
        "- The shortcut is intentionally conservative: it requires "
        f"{min_converging} bots agreeing on direction with high magnitude. "
        "Tuning these thresholds is part of Phase 3.5."
    )
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"\nWrote {out}")


if __name__ == "__main__":
    app()
