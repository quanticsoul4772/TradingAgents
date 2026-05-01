"""Backtest harness — loop propagate() over a (ticker, date) grid.

Writes one row per run to a CSV. Resumable: re-running with the same --out
skips (ticker, date) pairs already present (errors included, to avoid
re-burning tokens on deterministic failures).

The companion analyzer (scripts/analyze_backtest.py) reads this CSV and
computes realized 5-day forward returns + alpha vs SPY per row to evaluate
whether the framework's ratings carry signal.
"""

from __future__ import annotations

import csv
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from dotenv import load_dotenv
from rich.console import Console

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

load_dotenv()
load_dotenv(".env.enterprise", override=False)

console = Console()
app = typer.Typer(add_completion=False)

CSV_FIELDS = [
    "ticker",
    "analysis_date",
    "rating",
    "error",
    "run_seconds",
    "deep_model",
    "quick_model",
    "debate_rounds",
    "analysts",
]

# Rough average for Anthropic Sonnet-deep + Haiku-quick + 1/1 rounds + 3 analysts.
# Per-run cost varies with report length; this is intentionally a single estimate
# rather than a per-token integration that would need re-tuning per provider.
COST_PER_RUN_USD = 0.50

FREQ_MAP = {
    "W": "W-FRI",      # weekly Fridays
    "2W": "2W-FRI",
    "M": "BM",          # business month end
}


def _parse_csv_list(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def _build_grid(
    tickers: list[str],
    start: str,
    end: str,
    frequency: str,
) -> list[tuple[str, str]]:
    """Cross-product of tickers × dates, snapped to business days, future-trimmed."""
    pd_freq = FREQ_MAP.get(frequency, frequency)
    raw_dates = pd.date_range(start=start, end=end, freq=pd_freq)
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=7)
    dates = []
    for d in raw_dates:
        if d > cutoff:
            continue
        # Snap weekend dates to the preceding Friday.
        if d.weekday() >= 5:
            d = d - pd.Timedelta(days=d.weekday() - 4)
        dates.append(d.strftime("%Y-%m-%d"))
    # Dedupe while preserving order.
    seen = set()
    dates = [d for d in dates if not (d in seen or seen.add(d))]
    return [(t, d) for t in tickers for d in dates]


def _load_done(out_path: Path) -> set[tuple[str, str]]:
    if not out_path.exists():
        return set()
    with open(out_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {(row["ticker"], row["analysis_date"]) for row in reader}


def _ensure_header(out_path: Path) -> None:
    if out_path.exists():
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()


def _append_row(out_path: Path, row: dict) -> None:
    with open(out_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(row)


@app.command()
def main(
    tickers: str = typer.Option(
        "NVDA,AAPL,MSFT,JPM,JNJ",
        "--tickers",
        help="Comma-separated ticker symbols.",
    ),
    start: Optional[str] = typer.Option(
        None,
        "--start",
        help="ISO date (YYYY-MM-DD). Defaults to 90 days before --end.",
    ),
    end: Optional[str] = typer.Option(
        None,
        "--end",
        help="ISO date (YYYY-MM-DD). Defaults to today.",
    ),
    frequency: str = typer.Option(
        "W", "--frequency", help="Cadence: W (weekly Fridays), 2W, or M (business month end)."
    ),
    out: Path = typer.Option(
        Path("backtest_results.csv"), "--out", help="Output CSV path."
    ),
    max_runs: int = typer.Option(
        50, "--max-runs", help="Safety cap on the total number of propagate() calls."
    ),
    analysts: str = typer.Option(
        "market,news,fundamentals",
        "--analysts",
        help="Comma-separated subset of {market, social, news, fundamentals}.",
    ),
    debate_rounds: int = typer.Option(
        1, "--debate-rounds", help="Sets both max_debate_rounds and max_risk_discuss_rounds."
    ),
    provider: str = typer.Option("anthropic", "--provider"),
    deep_model: str = typer.Option("claude-sonnet-4-6", "--deep-model"),
    quick_model: str = typer.Option("claude-haiku-4-5", "--quick-model"),
    anthropic_effort: str = typer.Option(
        "",
        "--anthropic-effort",
        help='"low" / "medium" / "high" — only set if your Anthropic model supports extended thinking (Opus). '
        "Sonnet/Haiku reject it. Default empty = unset.",
    ),
    sleep_seconds: float = typer.Option(
        1.0, "--sleep", help="Pause between runs (rate-limit cushion)."
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip cost-estimate confirmation."),
):
    """Run propagate() over a grid and append results to CSV."""
    today = datetime.now().date()
    end_dt = datetime.strptime(end, "%Y-%m-%d").date() if end else today
    start_dt = datetime.strptime(start, "%Y-%m-%d").date() if start else end_dt - timedelta(days=90)

    ticker_list = _parse_csv_list(tickers)
    analyst_list = _parse_csv_list(analysts)

    grid = _build_grid(ticker_list, start_dt.isoformat(), end_dt.isoformat(), frequency)
    if not grid:
        console.print("[red]Empty grid (no business days in range after the 7-day future cutoff). Exiting.[/red]")
        raise typer.Exit(1)

    done = _load_done(out)
    pending = [pair for pair in grid if pair not in done]

    if not pending:
        console.print(f"[yellow]All {len(grid)} grid points already in {out}. Nothing to do.[/yellow]")
        raise typer.Exit(0)

    truncated = False
    if len(pending) > max_runs:
        pending = pending[:max_runs]
        truncated = True

    est_cost = len(pending) * COST_PER_RUN_USD
    console.print(f"[cyan]Backtest plan[/cyan]")
    console.print(f"  Tickers:        {ticker_list}")
    console.print(f"  Date range:     {start_dt} → {end_dt} ({frequency})")
    console.print(f"  Analysts:       {analyst_list}")
    console.print(f"  Models:         deep={deep_model} quick={quick_model} effort={anthropic_effort}")
    console.print(f"  Debate rounds:  {debate_rounds}/{debate_rounds}")
    console.print(f"  Output:         {out}")
    console.print(f"  Grid:           {len(grid)} pairs ({len(done)} already done, {len(pending)} pending)")
    if truncated:
        console.print(f"  [yellow]Truncated to --max-runs={max_runs}[/yellow]")
    console.print(f"  Est. cost:      ~${est_cost:.2f} (rough; ${COST_PER_RUN_USD:.2f}/run avg for current Anthropic config)")

    if not yes:
        if not typer.confirm("Proceed?"):
            raise typer.Exit(0)

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = provider
    config["deep_think_llm"] = deep_model
    config["quick_think_llm"] = quick_model
    if anthropic_effort:
        config["anthropic_effort"] = anthropic_effort
    config["max_debate_rounds"] = debate_rounds
    config["max_risk_discuss_rounds"] = debate_rounds
    config["checkpoint_enabled"] = False  # per-node SQLite writes are pure overhead at this scale
    config["memory_log_path"] = str(out.parent.resolve() / "backtest_memory.md")
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }

    console.print(f"\n[cyan]Building graph...[/cyan]")
    ta = TradingAgentsGraph(
        selected_analysts=analyst_list,
        debug=False,  # quiet mode — we don't want chunk-by-chunk noise across 50+ runs
        config=config,
    )

    _ensure_header(out)

    n_ok = 0
    n_err = 0
    wall_start = time.perf_counter()

    for i, (ticker, date) in enumerate(pending, 1):
        console.print(f"\n[cyan]Run {i}/{len(pending)}[/cyan]  {ticker}  {date}")
        t0 = time.perf_counter()
        row = {
            "ticker": ticker,
            "analysis_date": date,
            "rating": "",
            "error": "",
            "run_seconds": 0.0,
            "deep_model": deep_model,
            "quick_model": quick_model,
            "debate_rounds": debate_rounds,
            "analysts": ",".join(analyst_list),
        }
        try:
            _, rating = ta.propagate(ticker, date)
            row["rating"] = str(rating).strip()
            n_ok += 1
            console.print(f"  → rating: [green]{row['rating']}[/green]")
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            n_err += 1
            console.print(f"  → [red]error:[/red] {row['error']}")
        row["run_seconds"] = round(time.perf_counter() - t0, 2)
        _append_row(out, row)

        if i < len(pending):
            time.sleep(sleep_seconds)

    elapsed = time.perf_counter() - wall_start
    console.print(f"\n[cyan]Done.[/cyan]  {n_ok} ok, {n_err} errors, {elapsed/60:.1f} min wall-clock")
    console.print(f"  Output: {out.resolve()}")
    console.print(f"  Next:   python scripts/analyze_backtest.py {out}")


if __name__ == "__main__":
    app()
