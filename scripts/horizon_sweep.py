"""Cross-experiment horizon sweep: for every saved experiment CSV, compute
forward alpha at 5/10/21/90-day windows. Output a single matrix:
experiment × horizon → bucket (count, mean_alpha, hit_rate).

Tests whether the calibration ceiling found at 5-day holds at longer horizons,
or whether the framework actually does predict longer trends correctly.

Usage:
    python scripts/horizon_sweep.py
    python scripts/horizon_sweep.py --horizons 5,10,21,90 --out claudedocs/horizon-sweep.md
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import typer
import yfinance as yf
from rich import box
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(add_completion=False)

RATING_ORDER = ["Buy", "Overweight", "Hold", "Underweight", "Sell"]


def _compute_alpha(stock_df, bench_df, trade_date: str, holding_days: int):
    td = pd.Timestamp(trade_date)
    stock_idx = (
        stock_df.index.tz_localize(None) if stock_df.index.tz is not None else stock_df.index
    )
    bench_idx = (
        bench_df.index.tz_localize(None) if bench_df.index.tz is not None else bench_df.index
    )

    stock_slice = stock_df.loc[stock_idx >= td]
    bench_slice = bench_df.loc[bench_idx >= td]
    if len(stock_slice) < 2 or len(bench_slice) < 2:
        return None
    actual = min(holding_days, len(stock_slice) - 1, len(bench_slice) - 1)
    if actual < holding_days:
        # Don't fabricate a partial-window result; mark missing.
        return None
    raw = float(
        (stock_slice["Close"].iloc[actual] - stock_slice["Close"].iloc[0])
        / stock_slice["Close"].iloc[0]
    )
    bench = float(
        (bench_slice["Close"].iloc[actual] - bench_slice["Close"].iloc[0])
        / bench_slice["Close"].iloc[0]
    )
    return (raw - bench) * 100


def _fetch_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)


@app.command()
def main(
    horizons: str = typer.Option("5,10,21,90", "--horizons"),
    pattern: str = typer.Option("experiments/*/results.csv", "--pattern"),
    out: Path = typer.Option(Path("claudedocs/horizon-sweep.md"), "--out"),
):
    horizon_list = [int(h) for h in horizons.split(",")]
    csv_paths = sorted(Path().glob(pattern))
    console.print(f"[bold]Found {len(csv_paths)} experiment CSVs; horizons={horizon_list}[/bold]\n")

    # Per-ticker price cache. Pull once per ticker over the full window.
    all_dates, all_tickers = [], set()
    for p in csv_paths:
        df = pd.read_csv(p)
        df = df[df["error"].isna() | (df["error"] == "")]
        all_dates.extend(df["analysis_date"].tolist())
        all_tickers.update(df["ticker"].unique())

    min_date = min(all_dates)
    max_date = max(all_dates)
    fetch_end = (
        datetime.strptime(max_date, "%Y-%m-%d") + timedelta(days=max(horizon_list) + 14)
    ).strftime("%Y-%m-%d")
    fetch_start = (datetime.strptime(min_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

    console.print(f"Fetching {len(all_tickers)} ticker histories: {fetch_start} → {fetch_end}")
    cache = {t: _fetch_history(t, fetch_start, fetch_end) for t in all_tickers}
    spy = _fetch_history("SPY", fetch_start, fetch_end)

    # Long-format result table.
    rows = []
    for csv_path in csv_paths:
        exp_id = csv_path.parent.name
        df = pd.read_csv(csv_path)
        df = df[df["error"].isna() | (df["error"] == "")]
        for h in horizon_list:
            for _, row in df.iterrows():
                ticker = row["ticker"]
                stock_df = cache.get(ticker)
                if stock_df is None or stock_df.empty:
                    continue
                alpha = _compute_alpha(stock_df, spy, row["analysis_date"], h)
                if alpha is None:
                    continue
                rows.append(
                    {
                        "exp": exp_id,
                        "horizon": h,
                        "rating": row["rating"],
                        "ticker": ticker,
                        "alpha": alpha,
                    }
                )

    raw = pd.DataFrame(rows)

    # Aggregate per (experiment, horizon, rating).
    agg = (
        raw.groupby(["exp", "horizon", "rating"])
        .agg(
            n=("alpha", "size"),
            mean_alpha=("alpha", "mean"),
            hit_rate=("alpha", lambda s: (s > 0).mean()),
        )
        .reset_index()
    )

    # Build tables per experiment.
    md_lines = ["# Horizon sweep — bucket alpha across 5/10/21/90-day windows\n"]
    md_lines.append(f"_Generated {datetime.now().isoformat()}_\n")
    md_lines.append(
        "Convention: Underweight/Sell directionally correct when α<0; Buy/Overweight correct when α>0; Hold neutral. Hit rate = % positive α.\n\n"
    )
    md_lines.append(
        f"_horizons: {horizon_list}; experiments: {len(csv_paths)}; total resolved (rating, horizon) cells: {len(raw)}_\n"
    )

    for exp_id in sorted(raw["exp"].unique()):
        sub = agg[agg["exp"] == exp_id]
        md_lines.append(f"\n## {exp_id}\n")
        # Pivot: rating × horizon → mean_alpha (n, hit%)
        rich_table = Table(title=exp_id, box=box.SIMPLE)
        rich_table.add_column("Rating")
        for h in horizon_list:
            rich_table.add_column(f"{h}d α (n, hit%)")
        md_lines.append(
            "| Rating | " + " | ".join(f"{h}d α (n, hit%)" for h in horizon_list) + " |"
        )
        md_lines.append("|" + "---|" * (len(horizon_list) + 1))
        for r in RATING_ORDER:
            row_vals = [r]
            md_row = [r]
            for h in horizon_list:
                cell = sub[(sub["rating"] == r) & (sub["horizon"] == h)]
                if cell.empty:
                    row_vals.append("—")
                    md_row.append("—")
                else:
                    n = int(cell["n"].iloc[0])
                    a = float(cell["mean_alpha"].iloc[0])
                    hr = float(cell["hit_rate"].iloc[0]) * 100
                    s = f"{a:+.2f}% (n={n}, {hr:.0f}%)"
                    row_vals.append(s)
                    md_row.append(s)
            rich_table.add_row(*row_vals)
            md_lines.append("| " + " | ".join(md_row) + " |")
        console.print(rich_table)

    # Cross-experiment summary: for each horizon, average bucket alpha across all experiments.
    md_lines.append(
        "\n## Cross-experiment summary (mean α across experiments per horizon × bucket)\n"
    )
    md_lines.append("| Rating | " + " | ".join(f"{h}d mean α (Σn)" for h in horizon_list) + " |")
    md_lines.append("|" + "---|" * (len(horizon_list) + 1))
    cross = (
        raw.groupby(["horizon", "rating"])
        .agg(
            n=("alpha", "size"),
            mean_alpha=("alpha", "mean"),
            hit_rate=("alpha", lambda s: (s > 0).mean()),
        )
        .reset_index()
    )
    for r in RATING_ORDER:
        md_row = [r]
        for h in horizon_list:
            cell = cross[(cross["rating"] == r) & (cross["horizon"] == h)]
            if cell.empty:
                md_row.append("—")
            else:
                n = int(cell["n"].iloc[0])
                a = float(cell["mean_alpha"].iloc[0])
                hr = float(cell["hit_rate"].iloc[0]) * 100
                md_row.append(f"{a:+.2f}% (n={n}, {hr:.0f}%)")
        md_lines.append("| " + " | ".join(md_row) + " |")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md_lines), encoding="utf-8")
    console.print(f"\n[bold]Wrote {out}[/bold]")
    console.print(
        f"Resolved {len(raw)} cells across {len(csv_paths)} experiments × {len(horizon_list)} horizons"
    )


if __name__ == "__main__":
    app()
