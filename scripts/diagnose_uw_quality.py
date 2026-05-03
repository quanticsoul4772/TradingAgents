"""A1 — diagnostic on bull/bear debate quality for UW commits.

Compares debate properties between (a) AAPL UW dates where framework was
directionally correct at 21d (α<0) and (b) NVDA UW dates where framework
was heavily wrong at 21d (α>>0). Goal: identify a discriminator that
explains why UW works on AAPL but not NVDA.

Discriminator candidates examined per debate state log:
  - bull_history / bear_history character length
  - bull-vs-bear length ratio (asymmetry signal)
  - judge_decision (synthesis) — Underweight + length
  - investment_plan recommendation + length
  - keyword hits in synthesis: regime / valuation / momentum / sector /
    macro / earnings / margin / supply / demand
"""

from __future__ import annotations

import json
import re
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

LOGS_BASE = Path.home() / ".tradingagents" / "logs"

KEYWORDS = [
    "regime",
    "macro",
    "valuation",
    "momentum",
    "sector",
    "rotation",
    "earnings",
    "margin",
    "supply",
    "demand",
    "China",
    "AI",
    "memory",
    "guidance",
    "moat",
]


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


def _load_state(ticker: str, date: str) -> dict | None:
    p = LOGS_BASE / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{date}.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _extract_features(state: dict) -> dict:
    debate = state.get("investment_debate_state", {}) or {}
    bull = debate.get("bull_history", "") or ""
    bear = debate.get("bear_history", "") or ""
    judge = debate.get("judge_decision", "") or ""
    plan = state.get("investment_plan", "") or ""
    final = state.get("final_trade_decision", "") or ""

    bull_len = len(bull)
    bear_len = len(bear)
    ratio = bear_len / max(bull_len, 1)  # >1 = bear case dominates

    # Keyword frequency in synthesis (judge_decision + plan)
    synth = judge + " " + plan
    kw_hits = {
        k: len(re.findall(rf"\b{re.escape(k)}\b", synth, flags=re.IGNORECASE)) for k in KEYWORDS
    }

    # Conviction language in plan
    strong_words = ["clearly", "decisively", "overwhelming", "dominant", "convincing"]
    hedge_words = ["balanced", "uncertain", "ambiguous", "split", "two-sided", "mixed"]
    strong_count = sum(
        len(re.findall(rf"\b{w}\b", plan, flags=re.IGNORECASE)) for w in strong_words
    )
    hedge_count = sum(len(re.findall(rf"\b{w}\b", plan, flags=re.IGNORECASE)) for w in hedge_words)

    return {
        "bull_len": bull_len,
        "bear_len": bear_len,
        "bear_bull_ratio": ratio,
        "judge_len": len(judge),
        "plan_len": len(plan),
        "final_len": len(final),
        "kw_hits": kw_hits,
        "strong_words": strong_count,
        "hedge_words": hedge_count,
    }


@app.command()
def main(
    horizon: int = typer.Option(21, "--horizon"),
    out: Path = typer.Option(Path("claudedocs/uw-debate-diagnostic.md"), "--out"),
):
    csv_paths = sorted(Path().glob("experiments/*/results.csv"))
    rows = []
    tickers = set()
    dates = []
    for p in csv_paths:
        df = pd.read_csv(p)
        df = df[
            (df["error"].isna() | (df["error"] == ""))
            & (df["rating"].isin(["Underweight", "Sell"]))
        ]
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

    # Dedupe (ticker, date) with alpha
    seen = set()
    unique_pairs = []
    for r in rows:
        key = (r["ticker"], r["date"])
        if key in seen:
            continue
        seen.add(key)
        a = _alpha(cache[r["ticker"]], spy, r["date"], horizon)
        if a is None:
            continue
        unique_pairs.append({"ticker": r["ticker"], "date": r["date"], "alpha": a})

    # Load state + extract features
    enriched = []
    for p in unique_pairs:
        state = _load_state(p["ticker"], p["date"])
        if state is None:
            continue
        feats = _extract_features(state)
        # Tag: was framework directionally correct?
        # UW correct = α<0
        correct = p["alpha"] < 0
        enriched.append({**p, "correct": correct, **feats})

    df = pd.DataFrame(enriched)
    if df.empty:
        console.print("[yellow]No state logs found for UW pairs.[/yellow]")
        raise typer.Exit(0)

    # Per-ticker mean of features for AAPL vs NVDA
    cols_to_compare = [
        "bull_len",
        "bear_len",
        "bear_bull_ratio",
        "judge_len",
        "plan_len",
        "strong_words",
        "hedge_words",
    ]

    # Group: AAPL UW (correct) vs NVDA UW (wrong) — per ticker
    md = ["# UW debate-quality diagnostic (A1)\n"]
    md.append(f"_Generated {datetime.now().isoformat()}_\n")
    md.append(f"Horizon {horizon}d. Convention: UW correct ⇔ α<0.\n\n")

    md.append("## Per-ticker means of debate features\n")
    md.append(
        "| Ticker | n | mean α | correct % | bull_len | bear_len | bear/bull | judge_len | plan_len | strong_words | hedge_words |"
    )
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for ticker in sorted(df["ticker"].unique()):
        sub = df[df["ticker"] == ticker]
        md.append(
            f"| {ticker} | {len(sub)} | {sub['alpha'].mean():+.2f}% | "
            f"{sub['correct'].mean() * 100:.0f}% | "
            f"{sub['bull_len'].mean():.0f} | "
            f"{sub['bear_len'].mean():.0f} | "
            f"{sub['bear_bull_ratio'].mean():.2f} | "
            f"{sub['judge_len'].mean():.0f} | "
            f"{sub['plan_len'].mean():.0f} | "
            f"{sub['strong_words'].mean():.2f} | "
            f"{sub['hedge_words'].mean():.2f} |"
        )

    # Same for the per-row correct vs wrong split
    md.append("\n## Per-(ticker, correctness) split\n")
    md.append("| Group | n | mean α | bull_len | bear_len | bear/bull | hedge_words |")
    md.append("|---|---|---|---|---|---|---|")
    for ticker in sorted(df["ticker"].unique()):
        for label, mask in [
            ("correct (α<0)", df["correct"] == True),
            ("wrong (α>0)", df["correct"] == False),
        ]:
            sub = df[(df["ticker"] == ticker) & mask]
            if sub.empty:
                continue
            md.append(
                f"| {ticker} {label} | {len(sub)} | {sub['alpha'].mean():+.2f}% | "
                f"{sub['bull_len'].mean():.0f} | {sub['bear_len'].mean():.0f} | "
                f"{sub['bear_bull_ratio'].mean():.2f} | {sub['hedge_words'].mean():.2f} |"
            )

    # Keyword frequency comparison: AAPL UW vs NVDA UW
    md.append("\n## Keyword frequency in synthesis text (per-ticker mean per UW debate)\n")
    md.append("| Keyword | " + " | ".join(sorted(df["ticker"].unique())) + " |")
    md.append("|---|" + "---|" * len(df["ticker"].unique()))
    for kw in KEYWORDS:
        row = [kw]
        for ticker in sorted(df["ticker"].unique()):
            sub = df[df["ticker"] == ticker]
            mean_hits = sub["kw_hits"].apply(lambda h: h.get(kw, 0)).mean()
            row.append(f"{mean_hits:.2f}")
        md.append("| " + " | ".join(row) + " |")

    # Print rich table for terminal
    table = Table(title=f"UW debate features per ticker @ {horizon}d", box=box.SIMPLE)
    for col in ["Ticker", "n", "mean α", "correct%", "bull_len", "bear_len", "bear/bull", "hedge"]:
        table.add_column(col)
    for ticker in sorted(df["ticker"].unique()):
        sub = df[df["ticker"] == ticker]
        table.add_row(
            ticker,
            str(len(sub)),
            f"{sub['alpha'].mean():+.2f}%",
            f"{sub['correct'].mean() * 100:.0f}%",
            f"{sub['bull_len'].mean():.0f}",
            f"{sub['bear_len'].mean():.0f}",
            f"{sub['bear_bull_ratio'].mean():.2f}",
            f"{sub['hedge_words'].mean():.2f}",
        )
    console.print(table)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    console.print(f"\n[bold]Wrote {out}[/bold]")
    console.print(f"\nUnique UW (ticker, date) pairs analyzed: {len(df)}")


if __name__ == "__main__":
    app()
