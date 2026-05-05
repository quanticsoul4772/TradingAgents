"""Analyze backtest CSV — compute realized forward returns and report by rating.

Reads the CSV produced by scripts/backtest.py, fetches forward prices for
each (ticker, date) row from yfinance (cached per-ticker — one history
pull per ticker, sliced in-memory), and prints rating-bucket statistics.

The central question this answers: does mean alpha by rating bucket form a
monotonic Buy → Sell gradient, or is it noise?
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

from tradingagents.signals.counterfactual import (
    hold_all_ow,
    hold_all_uw,
    invert_all_commits,
    render_counterfactual_report,
    run_counterfactual,
)

console = Console()
app = typer.Typer(add_completion=False)

RATING_ORDER = ["Buy", "Overweight", "Hold", "Underweight", "Sell"]


def _compute_returns(
    stock_df: pd.DataFrame, bench_df: pd.DataFrame, trade_date: str, holding_days: int
) -> tuple[float | None, float | None, int | None]:
    """Mirror of fetch_returns math, operating on cached frames."""
    try:
        td = pd.Timestamp(trade_date)
        # Drop tz so .loc comparisons don't blow up against tz-aware yfinance index.
        stock_idx = (
            stock_df.index.tz_localize(None) if stock_df.index.tz is not None else stock_df.index
        )
        bench_idx = (
            bench_df.index.tz_localize(None) if bench_df.index.tz is not None else bench_df.index
        )

        stock_slice = stock_df.loc[stock_idx >= td]
        bench_slice = bench_df.loc[bench_idx >= td]

        if len(stock_slice) < 2 or len(bench_slice) < 2:
            return None, None, None

        actual_days = min(holding_days, len(stock_slice) - 1, len(bench_slice) - 1)
        raw = float(
            (stock_slice["Close"].iloc[actual_days] - stock_slice["Close"].iloc[0])
            / stock_slice["Close"].iloc[0]
        )
        bench_ret = float(
            (bench_slice["Close"].iloc[actual_days] - bench_slice["Close"].iloc[0])
            / bench_slice["Close"].iloc[0]
        )
        return raw, raw - bench_ret, actual_days
    except Exception:
        return None, None, None


def _fetch_history_cached(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    cache: dict[str, pd.DataFrame] = {}
    for t in tickers:
        df = yf.Ticker(t).history(start=start, end=end)
        cache[t] = df
    return cache


def _hit_rate(series: pd.Series) -> float:
    if len(series) == 0:
        return float("nan")
    return float((series > 0).mean())


@app.command()
def main(
    csv_path: Path = typer.Argument(..., help="CSV produced by scripts/backtest.py"),
    holding_days: int = typer.Option(5, "--holding-days", help="Forward-return window."),
    benchmark: str = typer.Option(
        "SPY",
        "--benchmark",
        help='Benchmark ticker. NOTE: only "SPY" is honored — fetch_returns hardcodes SPY at trading_graph.py:205.',
    ),
    export: Path | None = typer.Option(
        None, "--export", help="Optional path to write enriched CSV with return columns appended."
    ),
    counterfactual_md: Path | None = typer.Option(
        None,
        "--counterfactual-md",
        help=(
            "Optional path to write the rendered counterfactual reports as markdown. "
            "Always prints a counterfactual summary table to console; this flag adds "
            "full per-rule markdown (changed-pairs tables) for paste-into-ANALYSIS.md use."
        ),
    ),
    skip_counterfactual: bool = typer.Option(
        False,
        "--skip-counterfactual",
        help="Suppress the counterfactual section entirely (default: print to console).",
    ),
):
    if benchmark != "SPY":
        console.print(
            f"[yellow]Warning:[/yellow] --benchmark={benchmark} accepted but only SPY is currently honored "
            f"(SPY hardcoded in fetch_returns); falling back to SPY for the comparison."
        )

    df = pd.read_csv(csv_path)
    n_total = len(df)
    n_err = int(df["error"].fillna("").astype(bool).sum())
    df = df[df["error"].fillna("") == ""].copy()
    if df.empty:
        console.print("[red]No successful runs in CSV. Nothing to analyze.[/red]")
        raise typer.Exit(1)

    df["analysis_date"] = pd.to_datetime(df["analysis_date"]).dt.strftime("%Y-%m-%d")

    tickers = sorted(df["ticker"].unique().tolist())
    min_date = df["analysis_date"].min()
    max_date = df["analysis_date"].max()
    fetch_start = min_date
    fetch_end = (
        datetime.strptime(max_date, "%Y-%m-%d") + timedelta(days=holding_days + 14)
    ).strftime("%Y-%m-%d")

    console.print(
        f"[cyan]Fetching price history[/cyan]  {len(tickers)} tickers + SPY  {fetch_start} → {fetch_end}"
    )
    cache = _fetch_history_cached(tickers + ["SPY"], fetch_start, fetch_end)
    spy_df = cache["SPY"]

    raws, alphas, holds = [], [], []
    for _, row in df.iterrows():
        stock_df = cache.get(row["ticker"])
        if stock_df is None or stock_df.empty:
            raws.append(None)
            alphas.append(None)
            holds.append(None)
            continue
        r, a, h = _compute_returns(stock_df, spy_df, row["analysis_date"], holding_days)
        raws.append(r)
        alphas.append(a)
        holds.append(h)

    df["raw_return"] = raws
    df["alpha_return"] = alphas
    df["holding_days_actual"] = holds

    n_resolved = int(df["alpha_return"].notna().sum())
    n_unresolved = int(df["alpha_return"].isna().sum())

    # ---- Headline ----
    head = Table(title="Backtest summary", box=box.SIMPLE_HEAVY)
    head.add_column("Metric")
    head.add_column("Value", justify="right")
    head.add_row("Total rows in CSV", str(n_total))
    head.add_row("Errored runs (skipped)", str(n_err))
    head.add_row("Resolved (have forward return)", str(n_resolved))
    head.add_row("Unresolved (price data missing)", str(n_unresolved))
    head.add_row("Mean run time (sec)", f"{df['run_seconds'].mean():.1f}")
    head.add_row("Holding window (days)", str(holding_days))
    head.add_row("Benchmark", "SPY")
    console.print(head)

    resolved = df.dropna(subset=["alpha_return"])
    if resolved.empty:
        console.print(
            "[red]No rows have forward-return data yet. Wait a few trading days and re-run.[/red]"
        )
        if export:
            df.to_csv(export, index=False)
            console.print(f"[cyan]Wrote enriched CSV (with empty return columns):[/cyan] {export}")
        raise typer.Exit(0)

    # ---- Mean alpha by rating bucket ----
    bucket = Table(title="Mean alpha by rating", box=box.SIMPLE_HEAVY)
    bucket.add_column("Rating")
    bucket.add_column("N", justify="right")
    bucket.add_column("Mean α", justify="right")
    bucket.add_column("Median α", justify="right")
    bucket.add_column("Hit rate (α>0)", justify="right")
    bucket.add_column("Std α", justify="right")
    for r in RATING_ORDER:
        sub = resolved[resolved["rating"] == r]["alpha_return"]
        if sub.empty:
            bucket.add_row(r, "0", "—", "—", "—", "—")
            continue
        bucket.add_row(
            r,
            str(len(sub)),
            f"{sub.mean() * 100:+.2f}%",
            f"{sub.median() * 100:+.2f}%",
            f"{_hit_rate(sub) * 100:.0f}%",
            f"{sub.std() * 100:.2f}%",
        )
    console.print(bucket)

    # ---- Spread ----
    buy = resolved[resolved["rating"] == "Buy"]["alpha_return"]
    sell = resolved[resolved["rating"] == "Sell"]["alpha_return"]
    if not buy.empty and not sell.empty:
        spread = buy.mean() - sell.mean()
        verdict = (
            "[green]signal[/green]"
            if spread > 0.005
            else ("[yellow]ambiguous[/yellow]" if spread > -0.005 else "[red]inverse[/red]")
        )
        console.print(
            f"\n[bold]Buy − Sell spread:[/bold] {spread * 100:+.2f}%  ({verdict})  "
            f"[dim](N_buy={len(buy)}, N_sell={len(sell)})[/dim]"
        )
    else:
        console.print(
            "\n[yellow]Buy − Sell spread:[/yellow] not computable (need both Buy and Sell ratings)"
        )

    # ---- Calibration: strong vs weak ratings ----
    strong = resolved[resolved["rating"].isin(["Buy", "Sell"])]["alpha_return"].abs()
    weak = resolved[resolved["rating"].isin(["Overweight", "Underweight"])]["alpha_return"].abs()
    if not strong.empty and not weak.empty:
        console.print(
            f"[bold]Calibration:[/bold]  |α| on strong ratings (Buy/Sell): {strong.mean() * 100:.2f}%   "
            f"|α| on weak ratings (Over/Underweight): {weak.mean() * 100:.2f}%"
        )

    # ---- By ticker × rating ----
    pivot = resolved.pivot_table(
        index="ticker", columns="rating", values="alpha_return", aggfunc="mean"
    ).reindex(columns=RATING_ORDER)
    by_t = Table(title="Mean α by ticker × rating", box=box.SIMPLE_HEAVY)
    by_t.add_column("Ticker")
    for r in RATING_ORDER:
        by_t.add_column(r, justify="right")
    for ticker in pivot.index:
        cells = []
        for r in RATING_ORDER:
            v = pivot.at[ticker, r] if r in pivot.columns else None
            cells.append("—" if pd.isna(v) else f"{v * 100:+.2f}%")
        by_t.add_row(ticker, *cells)
    console.print(by_t)

    if export:
        df.to_csv(export, index=False)
        console.print(f"\n[cyan]Wrote enriched CSV:[/cyan] {export}")

    # ---- Counterfactual auto-analysis (spec 002 Phase 2 wired into ANALYSIS.md) ----
    #
    # For each of the 3 standard counterfactual rules (hold_all_uw, hold_all_ow,
    # invert_all_commits), computes the alpha delta vs the actual ratings using
    # the SAME alpha cache the analyzer just populated (no extra yfinance fetches).
    # Operator can paste the summary table + the rendered markdown reports
    # (--counterfactual-md) directly into the experiment's ANALYSIS.md.
    if not skip_counterfactual:
        # Build counterfactual-shaped rows from the resolved subset
        cf_rows = [
            {
                "ticker": row["ticker"],
                "date": row["analysis_date"],
                "value": f"**Rating**: {row['rating']}",
            }
            for _, row in resolved.iterrows()
        ]
        # Pre-populate the alpha cache so run_counterfactual doesn't re-fetch
        cf_alpha_cache: dict[tuple[str, str, int], float | None] = {
            (row["ticker"].upper(), row["analysis_date"], holding_days): row["alpha_return"]
            for _, row in resolved.iterrows()
        }

        cf_rules = [
            ("hold-all-uw", hold_all_uw, "Hold on every UW/Sell date"),
            ("hold-all-ow", hold_all_ow, "Hold on every Buy/Overweight date"),
            ("invert-all", invert_all_commits, "Invert every directional commit (Buy↔Sell, OW↔UW)"),
        ]
        cf_reports: dict[str, tuple[str, object]] = {}
        for rule_name, fn, desc in cf_rules:
            report = run_counterfactual(
                cf_rows,
                fn,
                horizon_days=holding_days,
                alpha_cache=cf_alpha_cache,
            )
            cf_reports[rule_name] = (desc, report)

        cf_table = Table(
            title=f"Counterfactual Δα by rule (horizon = {holding_days}d)",
            box=box.SIMPLE_HEAVY,
        )
        cf_table.add_column("Rule")
        cf_table.add_column("Description")
        cf_table.add_column("n changed", justify="right")
        cf_table.add_column("Mean Δα", justify="right")
        cf_table.add_column("Total Δα", justify="right")
        for rule_name, (desc, report) in cf_reports.items():
            mean_str = (
                f"{report.mean_alpha_delta:+.3f}%" if report.mean_alpha_delta is not None else "—"
            )
            total_str = (
                f"{report.total_alpha_delta:+.3f}%" if report.total_alpha_delta is not None else "—"
            )
            cf_table.add_row(rule_name, desc, str(report.n_changed), mean_str, total_str)
        console.print()
        console.print(cf_table)
        console.print(
            "[dim]Counterfactual semantics: alpha contribution = direction(rating) × realized α. "
            "Positive Δα means the alternative rating would have produced better alpha than the actual.[/dim]"
        )

        if counterfactual_md is not None:
            md_lines: list[str] = []
            md_lines.append("# Counterfactual auto-analysis\n")
            md_lines.append(
                f"Auto-generated by `scripts/analyze_backtest.py` for `{csv_path}` "
                f"at horizon {holding_days}d. Counterfactual semantics defined in "
                "`tradingagents/signals/counterfactual.py` (spec 002 Phase 2).\n"
            )
            for rule_name, (desc, report) in cf_reports.items():
                md_lines.append(f"\n---\n\n## Rule: `{rule_name}` — {desc}\n")
                md_lines.append(render_counterfactual_report(report, description=desc))
            counterfactual_md.parent.mkdir(parents=True, exist_ok=True)
            counterfactual_md.write_text("\n".join(md_lines), encoding="utf-8")
            console.print(f"\n[cyan]Wrote counterfactual markdown:[/cyan] {counterfactual_md}")


if __name__ == "__main__":
    app()
