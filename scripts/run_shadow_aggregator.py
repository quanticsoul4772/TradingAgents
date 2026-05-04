"""Run the Phase 1 shadow aggregator against existing state logs.

For every ``full_states_log_<DATE>.json``, derive Signals from the analyst
prose reports, run ``aggregate(signals)``, and compare the shadow rating to
the actual PM rating extracted from the state log's final_trade_decision.

Reports the SC-001 acceptance metric: direction agreement between shadow
and actual ratings (target ≥80%).

Usage::

    python scripts/run_shadow_aggregator.py
    python scripts/run_shadow_aggregator.py --logs-dir /custom/logs
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tradingagents.agents.utils.rating import parse_rating
from tradingagents.signals.backfill import default_logs_dir, walk_state_logs
from tradingagents.signals.bots import shadow_aggregate_from_state_log

console = Console()
app = typer.Typer(add_completion=False)


_RATING_TO_DIRECTION = {
    "Buy": +1,
    "Overweight": +1,
    "Hold": 0,
    "Underweight": -1,
    "Sell": -1,
}


@app.command()
def main(
    logs_dir: Path = typer.Option(
        None, "--logs-dir", help="Path to the logs directory (default: ~/.tradingagents/logs)."
    ),
    out: Path = typer.Option(
        None,
        "--out",
        help="Markdown output path (default: claudedocs/shadow-aggregator-<date>.md).",
    ),
):
    """Run shadow aggregator across state logs; report agreement vs actual."""
    target = logs_dir or default_logs_dir()
    if not target.exists():
        console.print(f"[red]logs dir does not exist: {target}[/red]")
        raise typer.Exit(1)

    console.print(f"Logs dir: {target}\n")

    rows: list[dict] = []
    for ticker, log_path in walk_state_logs(target):
        try:
            with open(log_path, encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            console.print(f"[yellow]skip {log_path.name}: {exc}[/yellow]")
            continue

        trade_date = state.get("trade_date")
        if not trade_date:
            continue
        actual_md = state.get("final_trade_decision", "") or ""
        actual_rating = parse_rating(actual_md)

        signals, decision = shadow_aggregate_from_state_log(state)

        rows.append(
            {
                "ticker": ticker,
                "date": str(trade_date)[:10],
                "actual_rating": actual_rating,
                "shadow_rating": decision.rating,
                "shadow_confidence": decision.confidence,
                "shadow_direction_score": decision.direction_score,
                "n_signals": len(signals),
                "n_used": len(decision.bots_used),
                "n_abstained": len(decision.abstained),
            }
        )

    if not rows:
        console.print("[yellow]No state logs processed.[/yellow]")
        raise typer.Exit(0)

    # Compute agreement metrics
    n_total = len(rows)
    direction_match = 0
    rating_match = 0
    rating_within_one_tier = 0
    tier_order = {"Sell": 0, "Underweight": 1, "Hold": 2, "Overweight": 3, "Buy": 4}
    for r in rows:
        actual_d = _RATING_TO_DIRECTION.get(r["actual_rating"], 0)
        shadow_d = _RATING_TO_DIRECTION.get(r["shadow_rating"], 0)
        if actual_d == shadow_d:
            direction_match += 1
        if r["actual_rating"] == r["shadow_rating"]:
            rating_match += 1
        a_t = tier_order.get(r["actual_rating"])
        s_t = tier_order.get(r["shadow_rating"])
        if a_t is not None and s_t is not None and abs(a_t - s_t) <= 1:
            rating_within_one_tier += 1

    direction_pct = direction_match / n_total
    rating_pct = rating_match / n_total
    within_one_pct = rating_within_one_tier / n_total

    # Per-rating confusion table
    confusion: Counter = Counter()
    for r in rows:
        confusion[(r["actual_rating"], r["shadow_rating"])] += 1

    # Console output
    summary = Table(title="SC-001: Shadow vs Actual Rating Agreement")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", justify="right")
    summary.add_row("Total propagates", str(n_total))
    summary.add_row("Exact rating match", f"{rating_match} ({rating_pct:.1%})")
    summary.add_row("Within ±1 tier", f"{rating_within_one_tier} ({within_one_pct:.1%})")
    summary.add_row("Direction match", f"{direction_match} ({direction_pct:.1%})")
    summary.add_row(
        "SC-001 target (direction ≥80%)",
        "PASS" if direction_pct >= 0.80 else f"FAIL ({direction_pct:.1%} < 80%)",
    )
    console.print(summary)

    confusion_table = Table(title="Confusion: actual (rows) vs shadow (cols)")
    confusion_table.add_column("Actual / Shadow")
    ratings = ["Buy", "Overweight", "Hold", "Underweight", "Sell"]
    for r in ratings:
        confusion_table.add_column(r, justify="right")
    for actual in ratings:
        row = [actual]
        for shadow in ratings:
            row.append(str(confusion.get((actual, shadow), 0)))
        confusion_table.add_row(*row)
    console.print(confusion_table)

    # Markdown report
    if out is None:
        out = (
            Path("claudedocs")
            / f"shadow-aggregator-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Spec 001 Phase 1: Shadow Aggregator Report")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}._")
    lines.append("")
    lines.append(
        f"**Total propagates analyzed**: {n_total}\n"
        f"**Exact rating match**: {rating_match} ({rating_pct:.1%})\n"
        f"**Within ±1 tier**: {rating_within_one_tier} ({within_one_pct:.1%})\n"
        f"**Direction match**: {direction_match} ({direction_pct:.1%})\n"
        f"**SC-001 (direction ≥80%)**: "
        f"{'PASS' if direction_pct >= 0.80 else 'FAIL'}"
    )
    lines.append("")
    lines.append("## Confusion: actual (rows) × shadow (cols)")
    lines.append("")
    header = "| Actual \\ Shadow | " + " | ".join(ratings) + " |"
    lines.append(header)
    lines.append("|---|" + "|".join("---:" for _ in ratings) + "|")
    for actual in ratings:
        row_cells = [str(confusion.get((actual, shadow), 0)) for shadow in ratings]
        lines.append(f"| {actual} | " + " | ".join(row_cells) + " |")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "- Each propagate's analyst prose reports (market_report, news_report, "
        "fundamentals_report, sentiment_report when present, investment_plan) "
        "are featurized via `derive_signal_from_prose` to produce a Signal "
        "(direction in [-1, +1], magnitude in [0, 1], abstain bool).\n"
        "- The deterministic `aggregate(signals)` produces a 5-tier rating + "
        "confidence + direction_score using weights "
        "(market 0.25, news 0.20, fundamentals 0.30, sentiment 0.10, "
        "investment_plan 0.15).\n"
        "- Direction-agreement uses Buy/OW=+1, Hold=0, UW/Sell=-1 collapsing "
        "the 5-tier rating to a 3-tier directional bucket.\n"
        "- This is **shadow mode** (Phase 1) — production decisions remain the "
        "actual PM rating; the shadow aggregator is logged for comparison only."
    )
    lines.append("")
    lines.append("## Per-row data (first 30 rows shown)")
    lines.append("")
    lines.append(
        "| Ticker | Date | Actual | Shadow | Conf | Dir score | n signals | n used | n abstained |"
    )
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|")
    for r in rows[:30]:
        lines.append(
            f"| {r['ticker']} | {r['date']} | {r['actual_rating']} | {r['shadow_rating']} | "
            f"{r['shadow_confidence']:.2f} | {r['shadow_direction_score']:+.3f} | "
            f"{r['n_signals']} | {r['n_used']} | {r['n_abstained']} |"
        )
    if len(rows) > 30:
        lines.append("")
        lines.append(f"_({len(rows) - 30} more rows in the full corpus.)_")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"\nWrote {out}")


if __name__ == "__main__":
    app()
