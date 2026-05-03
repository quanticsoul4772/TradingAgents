"""For B: identify the Hold-rated (ticker, date) pairs with the largest
realized alpha magnitude across the corpus, at 5d and 21d horizons.

Output: for each top-N pair, print ticker/date/experiment/realized_alpha plus
a one-paragraph evidence summary extracted from the state log. This feeds
the reasoning_counterfactual analysis.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import typer
import yfinance as yf
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(add_completion=False)

LOGS_BASE = Path.home() / ".tradingagents" / "logs"


def _alpha(stock_df, bench_df, trade_date: str, holding_days: int):
    td = pd.Timestamp(trade_date)
    si = stock_df.index.tz_localize(None) if stock_df.index.tz is not None else stock_df.index
    bi = bench_df.index.tz_localize(None) if bench_df.index.tz is not None else bench_df.index
    s = stock_df.loc[si >= td]
    b = bench_df.loc[bi >= td]
    if len(s) < 2 or len(b) < 2:
        return None
    n = min(holding_days, len(s) - 1, len(b) - 1)
    if n < holding_days:
        return None
    raw = float((s["Close"].iloc[n] - s["Close"].iloc[0]) / s["Close"].iloc[0])
    bench = float((b["Close"].iloc[n] - b["Close"].iloc[0]) / b["Close"].iloc[0])
    return (raw - bench) * 100


def _load_state_log(ticker: str, date: str) -> dict | None:
    p = LOGS_BASE / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{date}.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _evidence_summary(state: dict) -> str:
    """Pull a compact snapshot from the state log for counterfactual context."""
    parts = []
    plan = state.get("investment_plan", "")
    if plan:
        parts.append(f"PLAN: {plan[:600]}")
    decision = state.get("final_trade_decision", "")
    if decision:
        parts.append(f"PM_DECISION: {decision[:600]}")
    return "\n".join(parts)


@app.command()
def main(
    top_n: int = typer.Option(10, "--top-n"),
    horizon: int = typer.Option(21, "--horizon", help="5 or 21"),
):
    csv_paths = sorted(Path().glob("experiments/*/results.csv"))
    rows = []
    tickers = set()
    dates = []
    for p in csv_paths:
        df = pd.read_csv(p)
        df = df[(df["error"].isna() | (df["error"] == "")) & (df["rating"] == "Hold")]
        for _, r in df.iterrows():
            rows.append({"exp": p.parent.name, "ticker": r["ticker"], "date": r["analysis_date"]})
            tickers.add(r["ticker"])
            dates.append(r["analysis_date"])

    fetch_start = (datetime.strptime(min(dates), "%Y-%m-%d") - timedelta(days=7)).strftime(
        "%Y-%m-%d"
    )
    fetch_end = (datetime.strptime(max(dates), "%Y-%m-%d") + timedelta(days=horizon + 14)).strftime(
        "%Y-%m-%d"
    )
    cache = {
        t: yf.Ticker(t).history(start=fetch_start, end=fetch_end, auto_adjust=False)
        for t in tickers
    }
    spy = yf.Ticker("SPY").history(start=fetch_start, end=fetch_end, auto_adjust=False)

    enriched = []
    for r in rows:
        a = _alpha(cache[r["ticker"]], spy, r["date"], horizon)
        if a is None:
            continue
        enriched.append({**r, "alpha": a, "abs_alpha": abs(a)})

    df = pd.DataFrame(enriched).sort_values("abs_alpha", ascending=False)
    # Dedupe on (ticker, date) — multiple experiments may rate same date Hold;
    # report once with the experiments that produced it.
    df_unique = df.drop_duplicates(subset=["ticker", "date"]).head(top_n)

    table = Table(title=f"Top {top_n} Hold dates by |α| at {horizon}d")
    table.add_column("Ticker")
    table.add_column("Date")
    table.add_column(f"{horizon}d α")
    table.add_column("Experiments rating it Hold")
    out_lines = []
    for _, row in df_unique.iterrows():
        same = df[(df["ticker"] == row["ticker"]) & (df["date"] == row["date"])]
        exps = ", ".join(sorted(same["exp"].unique()))
        table.add_row(row["ticker"], row["date"], f"{row['alpha']:+.2f}%", exps)
        out_lines.append(
            {
                "ticker": row["ticker"],
                "date": row["date"],
                "alpha": float(row["alpha"]),
                "experiments": exps,
            }
        )

    console.print(table)
    out_path = Path("claudedocs") / f"hold-extremes-{horizon}d.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_lines, indent=2), encoding="utf-8")
    console.print(f"\n[bold]Wrote {out_path}[/bold]")

    # Also dump evidence summaries for top 3 (used as context for counterfactual calls)
    console.print("\n[bold]Evidence summaries for top 3 (for counterfactual context):[/bold]")
    for row in out_lines[:3]:
        state = _load_state_log(row["ticker"], row["date"])
        if state is None:
            console.print(f"\n[yellow]No state log for {row['ticker']} {row['date']}[/yellow]")
            continue
        console.print(
            f"\n[bold cyan]{row['ticker']} {row['date']} (α={row['alpha']:+.2f}% at {horizon}d)[/bold cyan]"
        )
        console.print(_evidence_summary(state)[:1200])


if __name__ == "__main__":
    app()
