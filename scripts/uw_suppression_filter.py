"""A3 — retrospective commit-suppression filter on historical UW commits.

Per A1: framework UW commits are wrong when broader bull regime overrides
stock-specific bear case. Test whether SPY 30-day momentum + ticker-
specific 30-day momentum BEFORE the trade date (no look-ahead) would
have caught the wrong UW commits.

For each historical UW commit:
  1. Compute SPY % return over the 30 trading days BEFORE trade date
  2. Compute ticker % return over the 30 trading days BEFORE trade date
  3. Apply filter: suppress UW → Hold if either signal exceeds threshold
  4. Recompute mean α at 21d for the surviving UW set
  5. Show the suppressed commits and what their α was

Tests multiple thresholds to find the operating point that maximizes
post-filter UW α correctness without losing too many calls.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import typer
from rich import box
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.dataflows.price_cache import PriceCache  # noqa: E402

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    horizon: int = typer.Option(21, "--horizon"),
    lookback: int = typer.Option(30, "--lookback", help="Trading days for momentum signal."),
    out: Path = typer.Option(Path("claudedocs/uw-suppression-filter.md"), "--out"),
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

    cache = PriceCache(tickers, dates, horizon_days=horizon)

    # Dedupe (ticker, date) and compute features
    seen = set()
    enriched = []
    for r in rows:
        key = (r["ticker"], r["date"])
        if key in seen:
            continue
        seen.add(key)
        a = cache.alpha(r["ticker"], r["date"], horizon)
        if a is None:
            continue
        spy_mom = cache.trailing_return(cache.benchmark, r["date"], lookback)
        tic_mom = cache.trailing_return(r["ticker"], r["date"], lookback)
        if spy_mom is None or tic_mom is None:
            continue
        enriched.append(
            {
                "ticker": r["ticker"],
                "date": r["date"],
                "alpha": a,
                "spy_mom": spy_mom,
                "tic_mom": tic_mom,
                "correct": a < 0,
            }
        )

    df = pd.DataFrame(enriched)
    if df.empty:
        console.print("[yellow]No UW pairs.[/yellow]")
        raise typer.Exit(0)

    md = ["# UW commit-suppression filter retrospective (A3)\n"]
    md.append(f"_Generated {datetime.now().isoformat()}_\n")
    md.append(
        f"Filter rule: suppress UW (treat as Hold) if ticker is in mean-reversion zone (tic_mom < downside_thr).\n"
        f"Hypothesis discovered in this analysis: wrong UW commits cluster on tickers already deeply down → forward 21d mean-reverts bullishly.\n"
        f"Horizon {horizon}d. Convention: UW correct ⇔ α<0.\n\n"
    )

    # Baseline (no filter)
    md.append("## Baseline (no filter)\n")
    md.append(f"- n = {len(df)}")
    md.append(f"- mean α = {df['alpha'].mean():+.2f}%")
    md.append(f"- correct rate (α<0) = {df['correct'].mean() * 100:.0f}%\n")

    # Mean-reversion suppression sweep: suppress UW when ticker is already deeply down
    downside_thresholds = [-5.0, -7.5, -10.0, -12.5, -15.0]

    md.append("\n## Threshold sweep (downside mean-reversion filter)\n")
    md.append(
        "| downside_thr | n_kept | n_suppressed | kept α | suppressed α | kept correct% | improvement |"
    )
    md.append("|---|---|---|---|---|---|---|")

    table = Table(
        title=f"UW suppression: ticker_mom < downside_thr → suppress @ {horizon}d", box=box.SIMPLE
    )
    for col in ["downside_thr", "n_kept", "n_supp", "kept α", "supp α", "kept_OK%", "Δα"]:
        table.add_column(col)

    baseline_alpha = df["alpha"].mean()
    best = None
    for d_thr in downside_thresholds:
        mask_supp = df["tic_mom"] < d_thr  # ticker already down too much → mean-reversion likely
        kept = df[~mask_supp]
        supp = df[mask_supp]
        kept_alpha = kept["alpha"].mean() if not kept.empty else float("nan")
        supp_alpha = supp["alpha"].mean() if not supp.empty else float("nan")
        kept_correct = kept["correct"].mean() * 100 if not kept.empty else 0
        improvement = baseline_alpha - kept_alpha  # positive = filter improved (more negative α)
        md.append(
            f"| {d_thr:+.1f}% | {len(kept)} | {len(supp)} | "
            f"{kept_alpha:+.2f}% | {supp_alpha:+.2f}% | {kept_correct:.0f}% | "
            f"{improvement:+.2f}pp |"
        )
        table.add_row(
            f"{d_thr:+.1f}%",
            str(len(kept)),
            str(len(supp)),
            f"{kept_alpha:+.2f}%",
            f"{supp_alpha:+.2f}%" if not supp.empty else "—",
            f"{kept_correct:.0f}%",
            f"{improvement:+.2f}pp",
        )
        if len(kept) >= 5 and (best is None or kept_alpha < best[1]):
            best = (d_thr, kept_alpha, len(kept), len(supp))
    console.print(table)

    # Show the per-(ticker, date) detail with momentum features
    md.append("\n## Per-(ticker, date) UW commit features\n")
    md.append("| Ticker | Date | 21d α | UW correct | SPY 30d mom | ticker 30d mom |")
    md.append("|---|---|---|---|---|---|")
    for _, r in df.sort_values(["ticker", "date"]).iterrows():
        verdict = "✓" if r["correct"] else "✗"
        md.append(
            f"| {r['ticker']} | {r['date']} | {r['alpha']:+.2f}% | {verdict} | {r['spy_mom']:+.2f}% | {r['tic_mom']:+.2f}% |"
        )

    md.append("\n## Best operating point\n")
    if best:
        d_thr, kept_alpha, n_kept, n_supp = best
        md.append(f"\n**Suppress UW when ticker 30d momentum < {d_thr}%** (mean-reversion zone)\n")
        md.append(
            f"- Kept UW commits: n={n_kept}, mean α = **{kept_alpha:+.2f}%** (baseline {baseline_alpha:+.2f}%)"
        )
        md.append(f"- Suppressed commits: n={n_supp}")
        md.append(f"- α improvement: **{baseline_alpha - kept_alpha:+.2f}pp**")
        md.append(
            "\n_Caveat: in-sample validation on the same 16 commits that informed the hypothesis. Out-of-sample test requires fresh data._"
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    console.print(f"\n[bold]Wrote {out}[/bold]")
    if best:
        console.print(
            f"\n[bold green]Best: spy_thr>{best[0]}% OR tic_thr>{best[1]}% — kept α {best[2]:+.2f}% (baseline {baseline_alpha:+.2f}%)[/bold green]"
        )


if __name__ == "__main__":
    app()
