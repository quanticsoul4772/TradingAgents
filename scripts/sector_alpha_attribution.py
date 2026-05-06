"""Sector-α attribution analyzer — corpus-wide 5th-failure-mode discovery.

For every commit in `experiments/*/results.csv`, compute three forward
returns at the configured holding window:

  - raw_return     — stock close-to-close return
  - alpha_vs_SPY   — stock return − SPY return (the α we usually report)
  - alpha_vs_sector — stock return − sector-ETF return (the new dimension)

Aggregate by rating bucket and cross-tab `sign(α_vs_SPY) × sign(α_vs_sector)`
to identify the 5th failure mode flagged by today's spec 004 SC-008
validation:

  α_vs_SPY < 0 AND α_vs_sector < 0
  → ticker underperformed BOTH the broad market AND its own sector
  → stock-specific weakness, NOT sector-rotation
  → no current filter (A3 / spec 003 / spec 003.5 / spec 004) catches this

Per-sector breakdown shows which sectors concentrate the 5th-failure-mode
cohort (SC-003 validation predicts Financials).

Mirrors the offline-replay methodology of:
  - scripts/sector_momentum_retrospective.py (spec 004 retrospective)
  - scripts/contrarian_gate_threshold_sweep.py (spec 003 retrospective)

Zero LLM cost. Reuses cached prices via yfinance + `_etf_history` LRU.

Usage:
    python scripts/sector_alpha_attribution.py
    python scripts/sector_alpha_attribution.py --holding-days 5
    python scripts/sector_alpha_attribution.py --rating Buy,Overweight
"""

from __future__ import annotations

import argparse
import sys
from datetime import date as _date
from datetime import timedelta as _td
from functools import lru_cache
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yfinance as yf  # noqa: E402

from tradingagents.agents.utils.sector_momentum_filter import (  # noqa: E402
    SECTOR_ETF_MAP,
    clear_etf_cache,
)
from tradingagents.dataflows.returns import returns_from_frames  # noqa: E402
from tradingagents.paper.sectors import get_sector  # noqa: E402

EXPERIMENTS_DIR = Path("experiments")
SECTORS_CACHE = Path.home() / ".tradingagents" / "paper" / "sectors.json"
BENCHMARK = "SPY"
DEFAULT_RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")
BULLISH = {"Buy", "Overweight"}
BEARISH = {"Underweight", "Sell"}


# ---- Price fetching (cached) ----------------------------------------------


@lru_cache(maxsize=512)
def _stock_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).history(start=start, end=end)
    except Exception:
        return pd.DataFrame()


def _fetch_window_frames(
    ticker: str, sector_etf: str, trade_date: str, holding_days: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (stock_df, spy_df, sector_etf_df) for the forward window."""
    try:
        anchor = _date.fromisoformat(trade_date)
    except ValueError:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    end = (anchor + _td(days=int(holding_days * 1.5) + 7)).isoformat()
    stock = _stock_history(ticker, trade_date, end)
    spy = _stock_history(BENCHMARK, trade_date, end)
    etf = _stock_history(sector_etf, trade_date, end)
    return stock, spy, etf


def _compute_three_returns(
    ticker: str, sector_etf: str, trade_date: str, holding_days: int
) -> tuple[float | None, float | None, float | None]:
    """Return (raw%, α_vs_SPY%, α_vs_sector%) at the configured holding window.

    None for any value when there isn't enough forward data (strict-window
    semantics via returns_from_frames).
    """
    stock, spy, etf = _fetch_window_frames(ticker, sector_etf, trade_date, holding_days)
    if stock.empty or spy.empty or etf.empty:
        return None, None, None
    raw, alpha_spy, _ = returns_from_frames(stock, spy, trade_date, holding_days, as_percent=True)
    _, alpha_sector, _ = returns_from_frames(stock, etf, trade_date, holding_days, as_percent=True)
    return raw, alpha_spy, alpha_sector


# ---- Corpus loading -------------------------------------------------------


def _load_commits(rating_filter: set[str]) -> pd.DataFrame:
    """Walk experiments/*/results.csv; return DataFrame of unique commits."""
    rows = []
    for p in sorted(EXPERIMENTS_DIR.glob("*/results.csv")):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if "rating" not in df.columns or "ticker" not in df.columns:
            continue
        df = df[df["rating"].isin(rating_filter)]
        if "error" in df.columns:
            df = df[df["error"].isna() | (df["error"] == "")]
        for _, r in df.iterrows():
            rows.append(
                {
                    "experiment": p.parent.name,
                    "ticker": str(r["ticker"]).upper().strip(),
                    "trade_date": str(r["analysis_date"]).strip(),
                    "rating": str(r["rating"]).strip(),
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        # Keep one row per (ticker, date, rating) — different experiments
        # may have produced the same commit, take the first.
        out = out.drop_duplicates(subset=["ticker", "trade_date", "rating"]).reset_index(drop=True)
    return out


# ---- Cell classification --------------------------------------------------


def _classify(alpha_spy: float | None, alpha_sector: float | None) -> str:
    """Map (sign α_vs_SPY, sign α_vs_sector) to a 4-cell label."""
    if alpha_spy is None or alpha_sector is None:
        return "no_data"
    spy_pos = alpha_spy > 0
    sec_pos = alpha_sector > 0
    if spy_pos and sec_pos:
        return "ticker_strong"  # beat both
    if spy_pos and not sec_pos:
        return "sector_tide_up"  # beat SPY, lagged sector — sector lifted boat
    if not spy_pos and sec_pos:
        return "sector_drag"  # lagged SPY, beat sector — sector dragged boat
    return "ticker_weak"  # underperformed both — 5th failure mode


CELL_DESCRIPTIONS = {
    "ticker_strong": "α_SPY>0 & α_sector>0 — ticker outperformed both broad market AND own sector (pure win)",
    "sector_tide_up": "α_SPY>0 & α_sector<0 — ticker beat SPY but lagged sector (sector tide raised the boat)",
    "sector_drag": "α_SPY<0 & α_sector>0 — ticker lagged SPY but beat sector (stock-pick OK; sector underperformed broad market)",
    "ticker_weak": "α_SPY<0 & α_sector<0 — ticker underperformed BOTH broad market AND own sector (5th failure mode — stock-specific weakness)",
}


# ---- Main -----------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--holding-days",
        type=int,
        default=21,
        help="Forward holding window in trading days (default 21)",
    )
    parser.add_argument(
        "--ratings",
        default=",".join(DEFAULT_RATINGS),
        help="Comma-separated ratings to include (default: all 5 tiers)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("claudedocs/sector-alpha-attribution-2026-05-06.md"),
        help="Output markdown path",
    )
    parser.add_argument(
        "--export-csv",
        type=Path,
        default=None,
        help="Optional CSV with full per-row enrichment (for downstream analysis)",
    )
    args = parser.parse_args()

    rating_filter = {r.strip() for r in args.ratings.split(",")}

    print("# Sector-α attribution analyzer — corpus walk")
    print()
    print(f"Holding window: {args.holding_days} trading days")
    print(f"Rating filter: {sorted(rating_filter)}")
    print()

    print("Loading commits...")
    commits = _load_commits(rating_filter)
    print(f"  {len(commits)} unique (ticker, date, rating) commits")

    if commits.empty:
        print("[fatal] no commits found")
        return

    # Resolve sectors + ETFs
    print()
    print("Resolving sectors + ETFs...")
    sector_cache: dict[str, str] = {}
    enriched_rows = []
    for _, r in commits.iterrows():
        ticker = r["ticker"]
        if ticker not in sector_cache:
            try:
                sector_cache[ticker] = get_sector(ticker, SECTORS_CACHE)
            except Exception:
                sector_cache[ticker] = "Unknown"
        sector = sector_cache[ticker]
        etf = SECTOR_ETF_MAP.get(sector)
        if etf is None:
            continue
        enriched_rows.append({**r.to_dict(), "sector": sector, "etf": etf})
    enriched = pd.DataFrame(enriched_rows)
    n_eligible = len(enriched)
    print(
        f"  {n_eligible} commits with mappable sector/ETF "
        f"(skipped {len(commits) - n_eligible} for Unknown/no-ETF)"
    )

    if enriched.empty:
        print("[fatal] no eligible commits")
        return

    # Compute three returns per commit
    print()
    print(f"Fetching prices + computing α vs SPY + α vs sector ETF for {n_eligible} commits...")
    clear_etf_cache()
    raws: list[float | None] = []
    alphas_spy: list[float | None] = []
    alphas_sector: list[float | None] = []
    for i, r in enriched.iterrows():
        if i > 0 and i % 25 == 0:
            print(f"  [{i}/{n_eligible}]")
        raw, a_spy, a_sec = _compute_three_returns(
            r["ticker"], r["etf"], r["trade_date"], args.holding_days
        )
        raws.append(raw)
        alphas_spy.append(a_spy)
        alphas_sector.append(a_sec)
    enriched["raw_pct"] = raws
    enriched["alpha_vs_spy_pct"] = alphas_spy
    enriched["alpha_vs_sector_pct"] = alphas_sector
    enriched["cell"] = enriched.apply(
        lambda x: _classify(x["alpha_vs_spy_pct"], x["alpha_vs_sector_pct"]), axis=1
    )

    valid = enriched[enriched["cell"] != "no_data"].copy()
    print(f"  {len(valid)} commits with valid forward returns (dropped {n_eligible - len(valid)})")

    if valid.empty:
        print("[fatal] no commits with valid forward returns")
        return

    # ---- Per-rating × cell cross-tab --------------------------------------

    print()
    print("## Cross-tab: rating × cell (counts)")
    print()
    ct = pd.crosstab(valid["rating"], valid["cell"]).reindex(
        columns=["ticker_strong", "sector_tide_up", "sector_drag", "ticker_weak", "no_data"],
        fill_value=0,
    )
    ct = ct.reindex(index=DEFAULT_RATINGS, fill_value=0)
    ct["total"] = ct.sum(axis=1)
    print(ct.to_string())

    # ---- Bullish-only deep dive (the cohort spec 004 was meant to help) ---

    bull = valid[valid["rating"].isin(BULLISH)].copy()
    print()
    print(f"## Bullish commits (n={len(bull)}) — cell distribution + means")
    print()
    print("| Cell | n | share | mean α vs SPY | mean α vs sector | mean raw |")
    print("|---|---|---|---|---|---|")
    for cell in ["ticker_strong", "sector_tide_up", "sector_drag", "ticker_weak"]:
        sub = bull[bull["cell"] == cell]
        n = len(sub)
        share = n / len(bull) * 100 if bull.shape[0] else 0
        a_spy = sub["alpha_vs_spy_pct"].mean() if n else float("nan")
        a_sec = sub["alpha_vs_sector_pct"].mean() if n else float("nan")
        raw = sub["raw_pct"].mean() if n else float("nan")
        print(f"| {cell} | {n} | {share:.1f}% | {a_spy:+.2f}% | {a_sec:+.2f}% | {raw:+.2f}% |")

    # 5th-failure-mode rate among LOSING bullish commits
    losing_bull = bull[bull["alpha_vs_spy_pct"] < 0]
    if not losing_bull.empty:
        ticker_weak_losing = losing_bull[losing_bull["cell"] == "ticker_weak"]
        rate = len(ticker_weak_losing) / len(losing_bull) * 100
        print()
        print(
            f"**5th-failure-mode rate among losing bullish commits**: "
            f"{len(ticker_weak_losing)}/{len(losing_bull)} = {rate:.1f}% — "
            f"of bullish commits with α<0 vs SPY, {rate:.1f}% also had α<0 vs their sector "
            f"(stock-specific weakness, not sector-rotation)"
        )

    # ---- Per-sector breakdown of bullish 5th-failure-mode cohort ----------

    print()
    print("## Per-sector concentration: bullish ticker_weak (5th failure mode)")
    print()
    print("| Sector | ETF | n_bull | n_ticker_weak | share | mean α vs SPY | mean α vs sector |")
    print("|---|---|---|---|---|---|---|")
    for sector in sorted(bull["sector"].unique()):
        sub = bull[bull["sector"] == sector]
        sub_weak = sub[sub["cell"] == "ticker_weak"]
        n_total = len(sub)
        n_weak = len(sub_weak)
        share = n_weak / n_total * 100 if n_total else 0
        a_spy = sub_weak["alpha_vs_spy_pct"].mean() if n_weak else float("nan")
        a_sec = sub_weak["alpha_vs_sector_pct"].mean() if n_weak else float("nan")
        etf = sub["etf"].iloc[0]
        print(
            f"| {sector} | {etf} | {n_total} | {n_weak} | {share:.1f}% | "
            f"{a_spy:+.2f}% | {a_sec:+.2f}% |"
        )

    # ---- Specific outliers (worst 5th-failure-mode commits) ---------------

    print()
    print("## Worst bullish 5th-failure-mode commits (top 10 by |α vs sector|)")
    print()
    weak = bull[bull["cell"] == "ticker_weak"].copy()
    if not weak.empty:
        weak["abs_alpha_sector"] = weak["alpha_vs_sector_pct"].abs()
        worst = weak.nlargest(min(10, len(weak)), "abs_alpha_sector")
        print("| Ticker | Date | Sector | Rating | α vs SPY | α vs sector | raw |")
        print("|---|---|---|---|---|---|---|")
        for _, r in worst.iterrows():
            print(
                f"| {r['ticker']} | {r['trade_date']} | {r['sector']} | {r['rating']} | "
                f"{r['alpha_vs_spy_pct']:+.2f}% | {r['alpha_vs_sector_pct']:+.2f}% | "
                f"{r['raw_pct']:+.2f}% |"
            )

    # ---- Bearish symmetry check (do bear commits also show ticker_strong?) -

    bear = valid[valid["rating"].isin(BEARISH)].copy()
    if not bear.empty:
        print()
        print(f"## Bearish commits (n={len(bear)}) — symmetry check")
        print()
        print("| Cell | n | share | mean α vs SPY | mean α vs sector |")
        print("|---|---|---|---|---|")
        for cell in ["ticker_strong", "sector_tide_up", "sector_drag", "ticker_weak"]:
            sub = bear[bear["cell"] == cell]
            n = len(sub)
            share = n / len(bear) * 100 if bear.shape[0] else 0
            a_spy = sub["alpha_vs_spy_pct"].mean() if n else float("nan")
            a_sec = sub["alpha_vs_sector_pct"].mean() if n else float("nan")
            print(f"| {cell} | {n} | {share:.1f}% | {a_spy:+.2f}% | {a_sec:+.2f}% |")
        # For bearish, "ticker_strong" + "sector_drag" are the "wrong" cells
        # (ticker actually rallied vs sector despite bear commit)

    # ---- Optional CSV export ----------------------------------------------

    if args.export_csv is not None:
        args.export_csv.parent.mkdir(parents=True, exist_ok=True)
        valid.to_csv(args.export_csv, index=False)
        print()
        print(f"Wrote per-row enrichment CSV: {args.export_csv}")

    # ---- Markdown output --------------------------------------------------

    md_lines = [
        f"# Sector-α attribution analyzer — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Goal**: identify the 5th failure mode flagged by spec 004 SC-008",
        "validation — bullish commits where the ticker underperforms BOTH",
        "the broad market (SPY) AND its own sector ETF. This is stock-specific",
        "weakness that no current filter (A3 / spec 003 / spec 003.5 / spec 004)",
        "catches.",
        "",
        f"**Holding window**: {args.holding_days} trading days",
        f"**Corpus**: {len(commits)} unique commits → "
        f"{len(valid)} with sector + ETF + valid forward returns",
        "",
        "## Cell taxonomy",
        "",
        "For each commit, sign(α vs SPY) × sign(α vs sector ETF) defines 4 cells:",
        "",
        "| Cell | α vs SPY | α vs sector | Meaning |",
        "|---|---|---|---|",
        "| `ticker_strong` | + | + | Outperformed both — pure win |",
        "| `sector_tide_up` | + | − | Beat SPY but lagged sector (sector lifted the boat) |",
        "| `sector_drag` | − | + | Lagged SPY but beat sector (stock-pick OK; sector down) |",
        "| `ticker_weak` | − | − | Underperformed both — **5th failure mode (stock-specific)** |",
        "",
    ]

    # Bullish table
    md_lines.append(f"## Bullish commits (n={len(bull)}) — cell distribution + means")
    md_lines.append("")
    md_lines.append("| Cell | n | share | mean α vs SPY | mean α vs sector | mean raw |")
    md_lines.append("|---|---|---|---|---|---|")
    for cell in ["ticker_strong", "sector_tide_up", "sector_drag", "ticker_weak"]:
        sub = bull[bull["cell"] == cell]
        n = len(sub)
        share = n / len(bull) * 100 if bull.shape[0] else 0
        a_spy = sub["alpha_vs_spy_pct"].mean() if n else float("nan")
        a_sec = sub["alpha_vs_sector_pct"].mean() if n else float("nan")
        raw = sub["raw_pct"].mean() if n else float("nan")
        md_lines.append(
            f"| `{cell}` | {n} | {share:.1f}% | {a_spy:+.2f}% | {a_sec:+.2f}% | {raw:+.2f}% |"
        )
    md_lines.append("")

    if not losing_bull.empty:
        ticker_weak_losing = losing_bull[losing_bull["cell"] == "ticker_weak"]
        rate = len(ticker_weak_losing) / len(losing_bull) * 100
        md_lines.append(
            f"**5th-failure-mode rate among losing bullish commits**: "
            f"{len(ticker_weak_losing)}/{len(losing_bull)} = **{rate:.1f}%** — "
            f"of bullish commits with α<0 vs SPY, {rate:.1f}% also had α<0 vs their sector. "
            f"This fraction quantifies what % of bullish losses are stock-specific "
            f"(not sector-rotation)."
        )
        md_lines.append("")

    # Per-sector concentration
    md_lines.append("## Per-sector concentration: bullish `ticker_weak`")
    md_lines.append("")
    md_lines.append(
        "| Sector | ETF | n_bull | n_ticker_weak | share | mean α vs SPY | mean α vs sector |"
    )
    md_lines.append("|---|---|---|---|---|---|---|")
    for sector in sorted(bull["sector"].unique()):
        sub = bull[bull["sector"] == sector]
        sub_weak = sub[sub["cell"] == "ticker_weak"]
        n_total = len(sub)
        n_weak = len(sub_weak)
        share = n_weak / n_total * 100 if n_total else 0
        a_spy = sub_weak["alpha_vs_spy_pct"].mean() if n_weak else float("nan")
        a_sec = sub_weak["alpha_vs_sector_pct"].mean() if n_weak else float("nan")
        etf = sub["etf"].iloc[0]
        md_lines.append(
            f"| {sector} | {etf} | {n_total} | {n_weak} | {share:.1f}% | "
            f"{a_spy:+.2f}% | {a_sec:+.2f}% |"
        )
    md_lines.append("")

    # Worst outliers
    if not weak.empty:
        weak = weak.copy()
        weak["abs_alpha_sector"] = weak["alpha_vs_sector_pct"].abs()
        worst = weak.nlargest(min(10, len(weak)), "abs_alpha_sector")
        md_lines.append("## Worst bullish 5th-failure-mode commits (top 10 by |α vs sector|)")
        md_lines.append("")
        md_lines.append("| Ticker | Date | Sector | Rating | α vs SPY | α vs sector | raw |")
        md_lines.append("|---|---|---|---|---|---|---|")
        for _, r in worst.iterrows():
            md_lines.append(
                f"| {r['ticker']} | {r['trade_date']} | {r['sector']} | {r['rating']} | "
                f"{r['alpha_vs_spy_pct']:+.2f}% | {r['alpha_vs_sector_pct']:+.2f}% | "
                f"{r['raw_pct']:+.2f}% |"
            )
        md_lines.append("")

    # Bearish symmetry check
    if not bear.empty:
        md_lines.append(f"## Bearish commits (n={len(bear)}) — symmetry check")
        md_lines.append("")
        md_lines.append(
            "Inverse interpretation: for bearish commits, `ticker_strong` (α>0 vs both) "
            "and `sector_drag` (α<0 vs SPY but α>0 vs sector) are the 'wrong' cells "
            "(ticker rallied vs its sector despite the bear call). `ticker_weak` is the "
            "successful bearish call (ticker tanked harder than its sector)."
        )
        md_lines.append("")
        md_lines.append("| Cell | n | share | mean α vs SPY | mean α vs sector |")
        md_lines.append("|---|---|---|---|---|")
        for cell in ["ticker_strong", "sector_tide_up", "sector_drag", "ticker_weak"]:
            sub = bear[bear["cell"] == cell]
            n = len(sub)
            share = n / len(bear) * 100 if bear.shape[0] else 0
            a_spy = sub["alpha_vs_spy_pct"].mean() if n else float("nan")
            a_sec = sub["alpha_vs_sector_pct"].mean() if n else float("nan")
            md_lines.append(f"| `{cell}` | {n} | {share:.1f}% | {a_spy:+.2f}% | {a_sec:+.2f}% |")
        md_lines.append("")

    md_lines.extend(
        [
            "## Implications",
            "",
            "- If `ticker_weak` share among bullish commits is HIGH and concentrated in a",
            "  single sector → spec 005 needs a per-ticker-vs-sector α signal targeting that",
            "  sector (matches the SC-003 Financials cohort prediction).",
            "- If `ticker_weak` share is LOW → the 5th failure mode is rare and operator",
            "  acceptance via Constitution VII calibrated abstention is the correct response.",
            "- If `ticker_weak` is uniformly distributed → the failure mode is stock-specific",
            "  but not sector-concentrated, and would need a different signal (per-ticker",
            "  earnings risk, news sentiment, option-implied skew, etc.).",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/sector_alpha_attribution.py --holding-days 21",
            "```",
            "",
            "Reads from `experiments/*/results.csv` + spec 002 sectors cache + yfinance",
            "stock + SPY + sector-ETF prices. No LLM cost. Deterministic given a fixed",
            "corpus + holding window.",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md_lines), encoding="utf-8")
    print()
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
