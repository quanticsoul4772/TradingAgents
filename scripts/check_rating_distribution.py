"""EH-2: rating distribution gate.

Pure post-hoc check: read any backtest CSV, assert the framework's declared
5-tier rating scale (Buy / Overweight / Hold / Underweight / Sell) is honored
across the rows, and emit structured warnings (reason / purpose / fix) per
the agent-harness-v2 enforcement-as-deny-with-context pattern.

Use cases:
  python scripts/check_rating_distribution.py pilot_results.csv
  python scripts/check_rating_distribution.py experiments/2026-05-02-002-wc12-pm-blind/results.csv
  python scripts/check_rating_distribution.py --window 10 pilot_results.csv

Exit codes:
  0 = clean (or only WARN-level findings)
  1 = at least one DENY-level finding
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd
import typer
from rich import box
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(add_completion=False)

CANONICAL_TIERS = ["Buy", "Overweight", "Hold", "Underweight", "Sell"]
STRONG_TIERS = {"Buy", "Sell"}
MODERATE_TIERS = {"Overweight", "Hold", "Underweight"}


def _check_window(ratings: list[str], n: int, label: str) -> tuple[str | None, str | None]:
    """Return (severity, message) if the last `n` ratings violate the 5-tier promise.

    severity: 'DENY' if 0 strong ratings in the window OR a tier is missing
              from the window AND the framework has had enough runs to use it;
              'WARN' for milder violations; None for clean.
    """
    if len(ratings) < n:
        return None, None
    window = ratings[-n:]
    counts = Counter(window)
    strong_count = sum(counts[t] for t in STRONG_TIERS if t in counts)

    if strong_count == 0:
        return (
            "DENY",
            f"Last {n} {label}: 0 strong (Buy/Sell) ratings. "
            "The 5-tier scale is not being honored — rating bucket has collapsed.",
        )
    return None, None


def _check_full_corpus(
    ratings: list[str],
) -> list[tuple[str, str, str, str]]:
    """Check the full corpus for structural rating-distribution violations.

    Returns list of (severity, reason, purpose, fix) tuples.
    """
    findings = []
    counts = Counter(ratings)
    n = len(ratings)
    if n == 0:
        return findings

    # 1. Tier coverage
    missing_tiers = [t for t in CANONICAL_TIERS if counts.get(t, 0) == 0]
    if missing_tiers:
        if any(t in STRONG_TIERS for t in missing_tiers):
            severity = "DENY"
        else:
            severity = "WARN"
        findings.append(
            (
                severity,
                f"Missing tier(s) across {n} runs: {missing_tiers}",
                "The framework declares a 5-tier rating scale (Buy / Overweight / "
                "Hold / Underweight / Sell). Each tier should appear at least once "
                "across a sufficiently large sample.",
                "Either (a) honestly remove the unused tiers from the declared "
                "scale, or (b) investigate why the tier is unreachable. See MR-2 "
                "experiment for the synthesis-prompt cause and MR-3 for the fix.",
            )
        )

    # 2. Strong-rating fraction
    strong_count = sum(counts[t] for t in STRONG_TIERS if t in counts)
    strong_pct = 100 * strong_count / n
    if strong_pct < 5.0:
        findings.append(
            (
                "DENY" if strong_pct == 0 else "WARN",
                f"Only {strong_count}/{n} ({strong_pct:.1f}%) ratings are strong (Buy or Sell).",
                "A 5-tier scale where <5% of ratings are strong calls is "
                "effectively a 3-tier scale.",
                "If the framework genuinely lacks conviction this often, document "
                "that in the rating-scale definitions. Otherwise the synthesis "
                "or PM step is over-hedging.",
            )
        )

    # 3. Distribution skew (any tier > 60%)
    for tier, count in counts.most_common(1):
        pct = 100 * count / n
        if pct > 60.0:
            findings.append(
                (
                    "WARN",
                    f"{tier} accounts for {count}/{n} ({pct:.1f}%) of ratings.",
                    "A single tier dominating >60% of a corpus suggests the "
                    "rating logic isn't responsive to underlying signal "
                    "differences.",
                    "Investigate whether the analyst inputs vary meaningfully "
                    "across runs OR whether the synthesis is collapsing "
                    "different signals to the same rating.",
                )
            )

    return findings


@app.command()
def main(
    csv_path: Path = typer.Argument(..., help="Backtest CSV produced by scripts/backtest.py"),
    window: int = typer.Option(
        10,
        "--window",
        "-w",
        help="Rolling-window size for the consecutive-misses check.",
    ),
):
    """Read `csv_path` and report rating-distribution violations."""
    if not csv_path.exists():
        console.print(f"[red]File not found: {csv_path}[/red]")
        raise typer.Exit(2)

    df = pd.read_csv(csv_path)
    if "rating" not in df.columns:
        console.print(f"[red]No 'rating' column in {csv_path}[/red]")
        raise typer.Exit(2)

    df = df[df["error"].fillna("") == ""].copy()
    ratings = [r for r in df["rating"].fillna("").astype(str) if r]
    n = len(ratings)
    if n == 0:
        console.print("[yellow]No successful ratings in CSV.[/yellow]")
        raise typer.Exit(0)

    counts = Counter(ratings)

    # Distribution table
    dist = Table(title=f"Rating distribution ({n} runs from {csv_path.name})", box=box.SIMPLE_HEAVY)
    dist.add_column("Tier")
    dist.add_column("Count", justify="right")
    dist.add_column("%", justify="right")
    for tier in CANONICAL_TIERS:
        c = counts.get(tier, 0)
        pct = 100 * c / n
        dist.add_row(tier, str(c), f"{pct:.1f}%")
    console.print(dist)

    # Findings
    findings = _check_full_corpus(ratings)
    win_severity, win_msg = _check_window(ratings, window, "rows in chronological order")
    if win_msg:
        findings.append(
            (
                win_severity,
                win_msg,
                f"A rolling window of {window} runs without any Buy/Sell suggests "
                "structural mode collapse, not random absence.",
                "Run MR-3-style synthesis-prompt fix; if that fails, investigate "
                "PM prompt + memory-log conditioning.",
            )
        )

    if not findings:
        console.print("[green]✅ No rating-distribution violations.[/green]")
        raise typer.Exit(0)

    severity_table = Table(title="Findings", box=box.SIMPLE_HEAVY)
    severity_table.add_column("Severity")
    severity_table.add_column("Reason")
    severity_table.add_column("Purpose")
    severity_table.add_column("Fix")
    for severity, reason, purpose, fix in findings:
        color = {"DENY": "red", "WARN": "yellow"}.get(severity, "white")
        severity_table.add_row(f"[{color}]{severity}[/{color}]", reason, purpose, fix)
    console.print(severity_table)

    has_deny = any(sev == "DENY" for sev, *_ in findings)
    if has_deny:
        console.print(
            f"\n[red]✗ {sum(1 for sev, *_ in findings if sev == 'DENY')} DENY finding(s). "
            "Exit 1.[/red]"
        )
        raise typer.Exit(1)
    console.print(f"\n[yellow]⚠ {len(findings)} WARN finding(s) only. Exit 0.[/yellow]")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
