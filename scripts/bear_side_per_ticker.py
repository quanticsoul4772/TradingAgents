"""Q4 — per-ticker breakdown of bear-side (Underweight + Sell) α at 5d/21d.

Tests whether the framework's bear-side anti-calibration (UW α=+1.56% at 21d
in cross-experiment summary) is uniform across tickers or concentrated on
specific tickers (e.g. NVDA's Q1 2026 bull regime made all UW calls wrong
regardless of framework quality).

If concentrated on bull-regime tickers → anti-calibration is regime-specific,
not a structural framework bias.
If distributed across all tickers → structural bullish lean is real.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import typer
import yfinance as yf
from rich import box
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dataflows.returns import alpha_from_frames as _alpha  # noqa: E402

console = Console()
app = typer.Typer(add_completion=False)

BEAR_RATINGS = ["Underweight", "Sell"]


@app.command()
def main(
    horizons: str = typer.Option("5,21", "--horizons"),
    out: Path = typer.Option(Path("claudedocs/bear-side-per-ticker.md"), "--out"),
):
    horizon_list = [int(h) for h in horizons.split(",")]
    csv_paths = sorted(Path().glob("experiments/*/results.csv"))

    rows = []
    tickers = set()
    dates = []
    for p in csv_paths:
        df = pd.read_csv(p)
        df = df[(df["error"].isna() | (df["error"] == "")) & (df["rating"].isin(BEAR_RATINGS))]
        for _, r in df.iterrows():
            rows.append(
                {
                    "exp": p.parent.name,
                    "ticker": r["ticker"],
                    "date": r["analysis_date"],
                    "rating": r["rating"],
                }
            )
            tickers.add(r["ticker"])
            dates.append(r["analysis_date"])

    if not rows:
        console.print("[yellow]No bear-side ratings found.[/yellow]")
        raise typer.Exit(0)

    fetch_start = (datetime.strptime(min(dates), "%Y-%m-%d") - timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    fetch_end = (
        datetime.strptime(max(dates), "%Y-%m-%d") + timedelta(days=max(horizon_list) + 14)
    ).strftime("%Y-%m-%d")
    cache = {
        t: yf.Ticker(t).history(start=fetch_start, end=fetch_end, auto_adjust=False)
        for t in tickers
    }
    spy = yf.Ticker("SPY").history(start=fetch_start, end=fetch_end, auto_adjust=False)

    enriched = []
    for r in rows:
        for h in horizon_list:
            a = _alpha(cache[r["ticker"]], spy, r["date"], h)
            if a is None:
                continue
            enriched.append({**r, "horizon": h, "alpha": a})

    df = pd.DataFrame(enriched)

    # Per-ticker × horizon: count, mean alpha, hit rate (positive α = wrong call for bear bucket)
    agg = (
        df.groupby(["ticker", "horizon"])
        .agg(
            n=("alpha", "size"),
            mean_alpha=("alpha", "mean"),
            wrong_rate=("alpha", lambda s: (s > 0).mean()),  # positive α on bear call = wrong
        )
        .reset_index()
    )

    # Cross-ticker totals per horizon for comparison
    overall = (
        df.groupby("horizon")
        .agg(
            n=("alpha", "size"),
            mean_alpha=("alpha", "mean"),
            wrong_rate=("alpha", lambda s: (s > 0).mean()),
        )
        .reset_index()
    )

    md = ["# Bear-side (UW + Sell) α per ticker — Q4 diagnostic\n"]
    md.append(f"_Generated {datetime.now().isoformat()}_\n")
    md.append(
        "Convention: bear-side ratings (Underweight/Sell) directionally CORRECT when α<0. `wrong_rate` = % of calls with α>0 (the wrong direction).\n"
    )
    md.append(
        "Question: is anti-calibration uniform across tickers or concentrated on bull-regime tickers?\n\n"
    )

    # Per-ticker table per horizon
    for h in horizon_list:
        md.append(f"\n## {h}-day horizon\n")
        md.append("| Ticker | n | mean α | wrong_rate | interpretation |")
        md.append("|---|---|---|---|---|")
        sub = agg[agg["horizon"] == h].sort_values("mean_alpha")
        for _, row in sub.iterrows():
            interp = (
                "directionally correct" if row["mean_alpha"] < 0 else "anti-calibrated (wrong dir)"
            )
            md.append(
                f"| {row['ticker']} | {int(row['n'])} | {row['mean_alpha']:+.2f}% | {row['wrong_rate'] * 100:.0f}% | {interp} |"
            )
        ov = overall[overall["horizon"] == h].iloc[0]
        ov_interp = "directionally correct" if ov["mean_alpha"] < 0 else "anti-calibrated"
        md.append(
            f"| **CROSS-TICKER** | **{int(ov['n'])}** | **{ov['mean_alpha']:+.2f}%** | **{ov['wrong_rate'] * 100:.0f}%** | **{ov_interp}** |"
        )

        # Rich table for terminal
        table = Table(title=f"Bear-side α @ {h}d", box=box.SIMPLE)
        table.add_column("Ticker")
        table.add_column("n")
        table.add_column("mean α")
        table.add_column("wrong %")
        table.add_column("verdict")
        for _, row in sub.iterrows():
            verdict = "OK" if row["mean_alpha"] < 0 else "anti-cal"
            table.add_row(
                row["ticker"],
                str(int(row["n"])),
                f"{row['mean_alpha']:+.2f}%",
                f"{row['wrong_rate'] * 100:.0f}%",
                verdict,
            )
        table.add_row(
            "CROSS",
            str(int(ov["n"])),
            f"{ov['mean_alpha']:+.2f}%",
            f"{ov['wrong_rate'] * 100:.0f}%",
            ov_interp[:8],
        )
        console.print(table)

    # Per-(ticker, date) detail at 21d
    md.append("\n## Per-(ticker, date) detail at 21d\n")
    md.append("| Ticker | Date | Rating | 21d α | Experiments |")
    md.append("|---|---|---|---|---|")
    detail = df[df["horizon"] == 21].copy()
    grouped = (
        detail.groupby(["ticker", "date", "rating"])
        .agg(
            alpha=("alpha", "first"),
            exps=("exp", lambda s: ", ".join(sorted(set(s)))),
        )
        .reset_index()
        .sort_values(["ticker", "date"])
    )
    for _, row in grouped.iterrows():
        md.append(
            f"| {row['ticker']} | {row['date']} | {row['rating']} | {row['alpha']:+.2f}% | {row['exps']} |"
        )

    # Headline summary
    md.append("\n## Headline\n")
    h21 = agg[agg["horizon"] == 21].sort_values("mean_alpha")
    if not h21.empty:
        per_ticker_signs = h21.set_index("ticker")["mean_alpha"]
        all_anti = (per_ticker_signs > 0).all()
        any_correct = (per_ticker_signs < 0).any()
        if all_anti:
            md.append(
                f"\n**All {len(h21)} tickers show anti-calibrated bear bucket at 21d.** Bullish lean is uniform — supports STRUCTURAL framework bias hypothesis (not regime-specific).\n"
            )
        elif any_correct:
            correct = h21[h21["mean_alpha"] < 0]["ticker"].tolist()
            anti = h21[h21["mean_alpha"] > 0]["ticker"].tolist()
            md.append(
                f"\n**Mixed**: {len(correct)} ticker(s) ({', '.join(correct)}) have correctly-bearish UW; {len(anti)} ticker(s) ({', '.join(anti)}) anti-calibrated. Supports REGIME-SPECIFIC hypothesis — bear-side wrongness concentrates on tickers that subsequently rallied.\n"
            )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    console.print(f"\n[bold]Wrote {out}[/bold]")


if __name__ == "__main__":
    app()
