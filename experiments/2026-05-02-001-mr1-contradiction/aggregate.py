"""Compute summary stats from results.jsonl.

Reads the per-pair classifications and prints:
- Distribution of labels (count + %)
- Mean / median contradiction_score (overall and per-label)
- Per-ticker breakdown
- The 3 most-contradicting and 3 least-contradicting pairs (for ANALYSIS.md
  illustrative excerpts)

Output is plain text to stdout. Pipe into ANALYSIS.md or read by hand.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(add_completion=False)

LABEL_ORDER = [
    "REAL_CONTRADICTION",
    "PARTIAL_OVERLAP",
    "STRAWMAN",
    "PARALLEL_MONOLOGUE",
]


@app.command()
def main(
    results: Path = typer.Option(
        Path(__file__).parent / "results.jsonl",
        "--results",
        help="Input JSONL produced by analyze_contradictions.py",
    ),
):
    rows = []
    with open(results, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    if not rows:
        console.print("[red]No rows in results.jsonl[/red]")
        raise typer.Exit(1)

    n_total = len(rows)
    n_err = sum(1 for r in rows if r.get("error"))
    ok = [r for r in rows if not r.get("error") and r.get("label")]
    n_ok = len(ok)

    console.print(f"\n[bold]MR-1 contradiction analysis — {n_ok} pairs, {n_err} errors[/bold]\n")

    # ---- Distribution by label
    counts = Counter(r["label"] for r in ok)
    dist = Table(title="Distribution of labels", show_header=True)
    dist.add_column("Label")
    dist.add_column("N", justify="right")
    dist.add_column("%", justify="right")
    dist.add_column("Mean score", justify="right")
    dist.add_column("Median score", justify="right")
    for label in LABEL_ORDER:
        n = counts.get(label, 0)
        if n == 0:
            dist.add_row(label, "0", "0.0%", "—", "—")
            continue
        scores = [r["contradiction_score"] for r in ok if r["label"] == label]
        dist.add_row(
            label,
            str(n),
            f"{n / n_ok * 100:.1f}%",
            f"{mean(scores):.2f}",
            f"{median(scores):.2f}",
        )
    console.print(dist)

    all_scores = [r["contradiction_score"] for r in ok]
    console.print(
        f"\n[bold]Overall contradiction_score:[/bold] mean={mean(all_scores):.2f}, "
        f"median={median(all_scores):.2f}, "
        f"min={min(all_scores):.2f}, max={max(all_scores):.2f}"
    )

    # ---- Per-ticker breakdown
    by_ticker = defaultdict(list)
    for r in ok:
        by_ticker[r["ticker"]].append(r)

    pt = Table(title="\nPer-ticker breakdown", show_header=True)
    pt.add_column("Ticker")
    pt.add_column("N", justify="right")
    pt.add_column("Mean score", justify="right")
    for label in LABEL_ORDER:
        pt.add_column(label.split("_")[0][:4], justify="right")  # short header
    for ticker in sorted(by_ticker):
        ticker_rows = by_ticker[ticker]
        ticker_scores = [r["contradiction_score"] for r in ticker_rows]
        ticker_counts = Counter(r["label"] for r in ticker_rows)
        cells = [str(ticker_counts.get(label, 0)) for label in LABEL_ORDER]
        pt.add_row(
            ticker,
            str(len(ticker_rows)),
            f"{mean(ticker_scores):.2f}",
            *cells,
        )
    console.print(pt)

    # ---- Top + bottom 3 (for ANALYSIS.md excerpts)
    sorted_by_score = sorted(ok, key=lambda r: r["contradiction_score"], reverse=True)

    console.print("\n[bold]Top 3 most-contradicting pairs:[/bold]\n")
    for r in sorted_by_score[:3]:
        console.print(
            f"- {r['ticker']} {r['trade_date']} → {r['label']} "
            f"(score={r['contradiction_score']:.2f})"
        )
        console.print(f"    rationale: {r['rationale'][:200]}...")
        if r.get("shared_claims"):
            console.print(f"    shared claims: {r['shared_claims'][:2]}")

    console.print("\n[bold]Bottom 3 least-contradicting pairs:[/bold]\n")
    for r in sorted_by_score[-3:]:
        console.print(
            f"- {r['ticker']} {r['trade_date']} → {r['label']} "
            f"(score={r['contradiction_score']:.2f})"
        )
        console.print(f"    rationale: {r['rationale'][:200]}...")
        if r.get("bull_only_topics") or r.get("bear_only_topics"):
            console.print(f"    bull-only: {r.get('bull_only_topics', [])[:2]}")
            console.print(f"    bear-only: {r.get('bear_only_topics', [])[:2]}")


if __name__ == "__main__":
    app()
