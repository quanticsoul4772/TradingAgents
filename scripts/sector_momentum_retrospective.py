"""Spec 004 sector-momentum filter — corpus-wide retrospective threshold sweep.

For every bullish (Buy/Overweight) commit in `experiments/*/results.csv`,
simulate the sector-momentum filter at multiple thresholds. For each
threshold, report:

  - n_commits seen (eligible bullish; sector mappable; ETF data available)
  - n_fired (commits the filter would suppress at this threshold)
  - kept_alpha (mean realized 21d α of commits the filter LEFT alone)
  - fired_alpha (mean realized 21d α of commits the filter WOULD HAVE suppressed)
  - net_dalpha_pp (kept_alpha − baseline_alpha; positive = filter helps)

Per-sector breakdown shows where the filter fires + helps (vs hurts).

Mirrors the offline-replay methodology of:
  - scripts/uw_suppression_filter.py (A3 retrospective)
  - scripts/contrarian_gate_retrospective.py (spec 003 retrospective)

Zero LLM cost. The script is a corpus replay against existing results.csv +
yfinance ETF prices; no new propagates.

Spec gate: per spec 004 plan + the SC-008 validation doc, default-on flip
requires this retrospective to show positive net Δα at the chosen threshold
across the broader corpus (not just the SC-003 Financials cohort).

Usage:
    python scripts/sector_momentum_retrospective.py
    python scripts/sector_momentum_retrospective.py --thresholds -3,-5,-7.5,-10
    python scripts/sector_momentum_retrospective.py --holding-days 21
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add repo root to sys.path so the script can import tradingagents/* modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yfinance as yf  # noqa: E402

from tradingagents.agents.utils.sector_momentum_filter import (  # noqa: E402
    SECTOR_ETF_MAP,
    _compute_etf_30d_return_pct,
    clear_etf_cache,
)
from tradingagents.dataflows.returns import returns_from_frames  # noqa: E402
from tradingagents.paper.sectors import get_sector  # noqa: E402

EXPERIMENTS_DIR = Path("experiments")
SECTORS_CACHE = Path.home() / ".tradingagents" / "paper" / "sectors.json"
BENCHMARK = "SPY"
DEFAULT_THRESHOLDS = (-3.0, -5.0, -7.5, -10.0)
BULLISH_RATINGS = {"Buy", "Overweight"}


def _load_bullish_commits() -> pd.DataFrame:
    """Walk experiments/*/results.csv; return DataFrame of bullish commits."""
    rows = []
    for p in sorted(EXPERIMENTS_DIR.glob("*/results.csv")):
        try:
            df = pd.read_csv(p)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] failed to read {p}: {exc}")
            continue
        if "rating" not in df.columns or "ticker" not in df.columns:
            continue
        df = df[df["rating"].isin(BULLISH_RATINGS)]
        if "error" in df.columns:
            df = df[df["error"].isna() | (df["error"] == "")]
        for _, r in df.iterrows():
            rows.append(
                {
                    "experiment": p.parent.name,
                    "ticker": str(r["ticker"]).upper().strip(),
                    "trade_date": str(r["analysis_date"]).strip(),
                    "rating": r["rating"],
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.drop_duplicates(subset=["ticker", "trade_date"]).reset_index(drop=True)
    return out


def _compute_realized_alpha_pct(ticker: str, trade_date: str, holding_days: int) -> float | None:
    """21d α vs SPY for a (ticker, trade_date), expressed as percent."""
    from datetime import date as _date
    from datetime import timedelta as _td

    try:
        anchor = _date.fromisoformat(trade_date)
    except ValueError:
        return None
    end = (anchor + _td(days=int(holding_days * 1.5) + 7)).isoformat()
    try:
        stock = yf.Ticker(ticker).history(start=trade_date, end=end)
        bench = yf.Ticker(BENCHMARK).history(start=trade_date, end=end)
    except Exception:
        return None
    if stock.empty or bench.empty:
        return None
    raw, alpha, _ = returns_from_frames(stock, bench, trade_date, holding_days, as_percent=False)
    if alpha is None:
        return None
    return float(alpha) * 100.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--thresholds",
        default=",".join(str(t) for t in DEFAULT_THRESHOLDS),
        help="Comma-separated negative thresholds in percent (default: -3,-5,-7.5,-10)",
    )
    parser.add_argument(
        "--holding-days",
        type=int,
        default=21,
        help="Forward holding window in trading days for realized α (default 21)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Sector-ETF prior-N-day lookback for the filter (default 30)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("claudedocs/sector-momentum-retrospective-2026-05-06.md"),
        help="Output markdown path",
    )
    args = parser.parse_args()

    thresholds = tuple(sorted(float(t) for t in args.thresholds.split(",")))

    print("# Spec 004 sector-momentum retrospective — corpus threshold sweep")
    print()
    print(f"Holding window: {args.holding_days} trading days")
    print(f"ETF lookback: {args.lookback_days} trading days")
    print(f"Thresholds: {thresholds}")
    print()

    print("Loading bullish commits...")
    commits = _load_bullish_commits()
    print(f"  {len(commits)} unique (ticker, trade_date) bullish commits across the corpus")

    if commits.empty:
        print("[fatal] no bullish commits found")
        return

    # Resolve sectors + ETFs (skip unmapped tickers)
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
        f"  {n_eligible} commits with mappable sector/ETF (skipped {len(commits) - n_eligible} for Unknown/no-ETF)"
    )

    # Compute ETF prior-30d return + realized 21d α per commit
    print()
    print("Computing ETF returns + realized α (this hits yfinance; ~1s/commit)...")
    clear_etf_cache()
    etf_returns: list[float | None] = []
    realized_alphas: list[float | None] = []
    for i, r in enriched.iterrows():
        if i % 10 == 0 and i > 0:
            print(f"  [{i}/{n_eligible}]")
        etf_ret = _compute_etf_30d_return_pct(
            r["etf"], r["trade_date"], lookback_days=args.lookback_days
        )
        alpha = _compute_realized_alpha_pct(r["ticker"], r["trade_date"], args.holding_days)
        etf_returns.append(etf_ret)
        realized_alphas.append(alpha)
    enriched["etf_30d_return_pct"] = etf_returns
    enriched["realized_alpha_pct"] = realized_alphas

    # Drop rows without both ETF return + realized α
    valid = enriched.dropna(subset=["etf_30d_return_pct", "realized_alpha_pct"]).reset_index(
        drop=True
    )
    n_valid = len(valid)
    print(f"  {n_valid} commits with both ETF return + realized α (dropped {n_eligible - n_valid})")

    if n_valid == 0:
        print("[fatal] no commits with valid data")
        return

    baseline_mean = valid["realized_alpha_pct"].mean()
    print()
    print(f"## Baseline (no filter): n={n_valid}, mean α = {baseline_mean:+.2f}%")
    print()

    # Threshold sweep
    print("## Threshold sweep")
    print()
    print("| threshold | n_kept | n_fired | kept α | fired α | net Δα (kept − baseline) |")
    print("|---|---|---|---|---|---|")
    sweep_rows = []
    for thr in thresholds:
        fire_mask = valid["etf_30d_return_pct"] < thr
        kept = valid[~fire_mask]
        fired = valid[fire_mask]
        kept_mean = kept["realized_alpha_pct"].mean() if not kept.empty else float("nan")
        fired_mean = fired["realized_alpha_pct"].mean() if not fired.empty else float("nan")
        net_dalpha = kept_mean - baseline_mean if not kept.empty else 0.0
        print(
            f"| {thr:+.1f}% | {len(kept)} | {len(fired)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )
        sweep_rows.append(
            {
                "threshold": thr,
                "n_kept": len(kept),
                "n_fired": len(fired),
                "kept_mean": kept_mean,
                "fired_mean": fired_mean,
                "net_dalpha": net_dalpha,
            }
        )

    # Per-sector breakdown at default threshold (-5%)
    print()
    print("## Per-sector breakdown at threshold -5.0%")
    print()
    print("| Sector | ETF | n_total | n_fired | kept α | fired α | net Δα |")
    print("|---|---|---|---|---|---|---|")
    fire_mask_default = valid["etf_30d_return_pct"] < -5.0
    for sector in sorted(valid["sector"].unique()):
        sub = valid[valid["sector"] == sector]
        sub_fire = sub & fire_mask_default if False else sub[fire_mask_default[sub.index]]
        sub_kept = sub.drop(sub_fire.index)
        kept_mean = sub_kept["realized_alpha_pct"].mean() if not sub_kept.empty else float("nan")
        fired_mean = sub_fire["realized_alpha_pct"].mean() if not sub_fire.empty else float("nan")
        net_dalpha = kept_mean - sub["realized_alpha_pct"].mean() if not sub_kept.empty else 0.0
        etf = sub["etf"].iloc[0]
        print(
            f"| {sector} | {etf} | {len(sub)} | {len(sub_fire)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )

    # Build markdown output
    md_lines = [
        f"# Spec 004 sector-momentum retrospective — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Spec**: `specs/004-sector-momentum-filter/`",
        f"**Holding window**: {args.holding_days} trading days",
        f"**ETF lookback**: {args.lookback_days} trading days",
        f"**Corpus**: {len(commits)} unique bullish commits → {n_valid} with sector + ETF + α data",
        "",
        f"## Baseline (no filter): n={n_valid}, mean α = {baseline_mean:+.2f}%",
        "",
        "## Threshold sweep",
        "",
        "| threshold | n_kept | n_fired | kept α | fired α | net Δα |",
        "|---|---|---|---|---|---|",
    ]
    for r in sweep_rows:
        md_lines.append(
            f"| {r['threshold']:+.1f}% | {r['n_kept']} | {r['n_fired']} | "
            f"{r['kept_mean']:+.2f}% | {r['fired_mean']:+.2f}% | {r['net_dalpha']:+.2f}pp |"
        )
    md_lines.extend(
        [
            "",
            "## Verdict",
            "",
            "Default-on flip is justified iff the threshold sweep shows positive net Δα at the",
            "configured default (-5%). Net Δα is computed as `kept_mean - baseline_mean` —",
            "positive means the filter improves the bucket by removing losers; negative means",
            "the filter hurts the bucket by removing winners.",
            "",
            "**Empirical context**: today's spec 004 SC-008 validation",
            "(`claudedocs/spec-004-sc008-validation-2026-05-06.md`) showed the filter doesn't",
            "fire on the SC-003 Financials cohort that originally motivated the spec. This",
            "retrospective tests whether the filter helps SOMEWHERE ELSE in the corpus.",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/sector_momentum_retrospective.py",
            "```",
            "",
            "Reads from `experiments/*/results.csv` + spec 002 sectors cache + yfinance ETF",
            "prices. No LLM cost. Deterministic given a fixed corpus + threshold list.",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md_lines), encoding="utf-8")
    print()
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
