"""Spec 006 bear-sector-symmetry filter — corpus-wide retrospective threshold sweep.

For every bearish (Underweight/Sell) commit in `experiments/*/results.csv`,
simulate the filter at multiple thresholds. For each threshold, report:

  - n_kept (commits the filter LEAVES alone)
  - n_fired (commits the filter would suppress at this threshold)
  - kept_alpha (mean realized 21d α-vs-SPY of kept commits)
  - fired_alpha (mean realized 21d α-vs-SPY of fired commits)
  - net_dalpha_pp (kept_alpha − baseline_alpha; positive = filter helps because
    suppressing high-α-bear commits is GOOD on the bear-side: those bear
    commits LOST money when the ticker rallied)

Per-sector breakdown shows where the filter fires + helps (vs hurts).

Cross-tab against the cells from `claudedocs/sector-alpha-attribution-2026-05-06.csv`:
on the n=18 ticker_strong-bearish cohort the spec was built to address,
how many would the filter fire at each threshold? SC-008 gate: ≥8 of 18
at threshold = +5%.

Mirrors the offline-replay methodology of:
  - scripts/uw_suppression_filter.py (A3)
  - scripts/contrarian_gate_retrospective.py (spec 003)
  - scripts/sector_momentum_retrospective.py (spec 004)
  - scripts/contrarian_gate_threshold_sweep.py (spec 003 default-on validation)

Zero LLM cost. The script is a corpus replay against existing results.csv +
yfinance ticker + ETF prices; no new propagates.

Usage:
    python scripts/bear_sector_symmetry_retrospective.py
    python scripts/bear_sector_symmetry_retrospective.py --thresholds 3,5,7.5,10
    python scripts/bear_sector_symmetry_retrospective.py --holding-days 21
"""

from __future__ import annotations

import argparse
import sys
from datetime import date as _date
from datetime import timedelta as _td
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yfinance as yf  # noqa: E402

from tradingagents.agents.utils.bear_sector_symmetry_filter import (  # noqa: E402
    SECTOR_ETF_MAP,
    _compute_etf_30d_return_pct_local,
    _compute_ticker_30d_return_pct,
    clear_etf_cache,
    clear_ticker_cache,
)
from tradingagents.dataflows.returns import returns_from_frames  # noqa: E402
from tradingagents.paper.sectors import get_sector  # noqa: E402

EXPERIMENTS_DIR = Path("experiments")
SECTORS_CACHE = Path.home() / ".tradingagents" / "paper" / "sectors.json"
BENCHMARK = "SPY"
DEFAULT_THRESHOLDS = (3.0, 5.0, 7.5, 10.0)
BEARISH_RATINGS = {"Underweight", "Sell"}


def _load_bearish_commits() -> pd.DataFrame:
    """Walk experiments/*/results.csv; return DataFrame of bearish commits."""
    rows = []
    for p in sorted(EXPERIMENTS_DIR.glob("*/results.csv")):
        try:
            df = pd.read_csv(p)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] failed to read {p}: {exc}")
            continue
        if "rating" not in df.columns or "ticker" not in df.columns:
            continue
        df = df[df["rating"].isin(BEARISH_RATINGS)]
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
        help="Comma-separated positive thresholds in percent (default: 3,5,7.5,10)",
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
        help="Ticker + ETF prior-N-day lookback for the filter (default 30)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md"),
        help="Output markdown path",
    )
    args = parser.parse_args()

    thresholds = tuple(sorted(float(t) for t in args.thresholds.split(",")))

    print("# Spec 006 bear-sector-symmetry retrospective — corpus threshold sweep")
    print()
    print(f"Holding window: {args.holding_days} trading days")
    print(f"Ticker + ETF lookback: {args.lookback_days} trading days")
    print(f"Thresholds: {thresholds}")
    print()

    print("Loading bearish commits...")
    commits = _load_bearish_commits()
    print(f"  {len(commits)} unique (ticker, trade_date) bearish commits across the corpus")

    if commits.empty:
        print("[fatal] no bearish commits found")
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

    # Compute ticker prior-30d return + ETF prior-30d return + realized α per commit
    print()
    print("Computing ticker + ETF returns + realized α (this hits yfinance; ~2s/commit)...")
    clear_etf_cache()
    clear_ticker_cache()
    ticker_returns: list[float | None] = []
    etf_returns: list[float | None] = []
    realized_alphas: list[float | None] = []
    for i, r in enriched.iterrows():
        if i > 0 and i % 10 == 0:
            print(f"  [{i}/{n_eligible}]")
        t_ret = _compute_ticker_30d_return_pct(
            r["ticker"], r["trade_date"], lookback_days=args.lookback_days
        )
        e_ret = _compute_etf_30d_return_pct_local(
            r["etf"], r["trade_date"], lookback_days=args.lookback_days
        )
        alpha = _compute_realized_alpha_pct(r["ticker"], r["trade_date"], args.holding_days)
        ticker_returns.append(t_ret)
        etf_returns.append(e_ret)
        realized_alphas.append(alpha)
    enriched["ticker_30d_return_pct"] = ticker_returns
    enriched["etf_30d_return_pct"] = etf_returns
    enriched["realized_alpha_pct"] = realized_alphas
    enriched["relative_strength_pct"] = enriched["ticker_30d_return_pct"].astype(float) - enriched[
        "etf_30d_return_pct"
    ].astype(float)

    # Drop rows without all three
    valid = enriched.dropna(
        subset=["ticker_30d_return_pct", "etf_30d_return_pct", "realized_alpha_pct"]
    ).reset_index(drop=True)
    n_valid = len(valid)
    print(
        f"  {n_valid} commits with full data (dropped {n_eligible - n_valid} for missing prices/α)"
    )

    if n_valid == 0:
        print("[fatal] no commits with valid data")
        return

    baseline_mean = valid["realized_alpha_pct"].mean()
    print()
    print(f"## Baseline (no filter): n={n_valid}, mean α = {baseline_mean:+.2f}%")
    print()
    print(
        "Note: HIGHER baseline α means the bearish commits collectively LOST money "
        "(the bear call was wrong; ticker went up). The spec 006 filter aims to "
        "SUPPRESS those commits to Hold. Net Δα = kept_α − baseline_α; positive "
        "means the filter is removing the worst (highest-α-on-the-bear-side) commits."
    )
    print()

    # Threshold sweep
    print("## Threshold sweep")
    print()
    print("| threshold | n_kept | n_fired | kept α | fired α | net Δα (kept − baseline) |")
    print("|---|---|---|---|---|---|")
    sweep_rows = []
    for thr in thresholds:
        fire_mask = valid["relative_strength_pct"] > thr
        kept = valid[~fire_mask]
        fired = valid[fire_mask]
        kept_mean = kept["realized_alpha_pct"].mean() if not kept.empty else float("nan")
        fired_mean = fired["realized_alpha_pct"].mean() if not fired.empty else float("nan")
        net_dalpha = baseline_mean - kept_mean if not kept.empty else 0.0
        # For BEAR commits: high α means the bear call was WRONG (ticker rallied).
        # Filter HELPS by removing high-α commits — so we want kept_mean LOWER
        # than baseline. net_dalpha = baseline - kept (positive = filter helps).
        print(
            f"| +{thr:.1f}% | {len(kept)} | {len(fired)} | "
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

    # Per-sector breakdown at default threshold (+5%)
    print()
    print("## Per-sector breakdown at threshold +5.0%")
    print()
    print("| Sector | ETF | n_total | n_fired | kept α | fired α | net Δα |")
    print("|---|---|---|---|---|---|---|")
    fire_mask_default = valid["relative_strength_pct"] > 5.0
    for sector in sorted(valid["sector"].unique()):
        sub = valid[valid["sector"] == sector]
        sub_fire = sub[fire_mask_default[sub.index]]
        sub_kept = sub.drop(sub_fire.index)
        kept_mean = sub_kept["realized_alpha_pct"].mean() if not sub_kept.empty else float("nan")
        fired_mean = sub_fire["realized_alpha_pct"].mean() if not sub_fire.empty else float("nan")
        sub_baseline = sub["realized_alpha_pct"].mean() if not sub.empty else float("nan")
        net_dalpha = sub_baseline - kept_mean if not sub_kept.empty else 0.0
        etf = sub["etf"].iloc[0]
        print(
            f"| {sector} | {etf} | {len(sub)} | {len(sub_fire)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )

    # SC-008 cross-tab against today's ticker_strong cohort
    sc008_count = None
    sc008_total = None
    attribution_csv = Path("claudedocs/sector-alpha-attribution-2026-05-06.csv")
    if attribution_csv.exists():
        print()
        print("## SC-008 cross-tab: ticker_strong-bearish cohort")
        print()
        attr = pd.read_csv(attribution_csv)
        ts = attr[(attr["rating"].isin(BEARISH_RATINGS)) & (attr["cell"] == "ticker_strong")]
        sc008_total = len(ts)
        # Reuse same enriched data — match by (ticker, trade_date)
        keys_in_cohort = set(
            zip(ts["ticker"].astype(str), ts["trade_date"].astype(str), strict=False)
        )
        in_cohort = valid[
            valid.apply(lambda r: (r["ticker"], r["trade_date"]) in keys_in_cohort, axis=1)
        ]
        fired_in_cohort = in_cohort[in_cohort["relative_strength_pct"] > 5.0]
        sc008_count = len(fired_in_cohort)
        print(
            f"At threshold +5.0%: {sc008_count} of {sc008_total} ticker_strong-bearish "
            f"cohort commits would be suppressed."
        )
        print()
        print(
            f"SC-008 gate: ≥8 of {sc008_total} fire at +5.0% → "
            f"**{'PASS' if sc008_count >= 8 else 'FAIL'}**"
        )
        if sc008_count < 8:
            print(
                "FAIL means the spec's motivating premise (ticker-vs-sector "
                "relative-strength was empirically >5% in the prior 30d for ≥8 "
                "of 18 cohort commits) doesn't hold — revisit threshold or accept "
                "filter as default-off operator-opt-in."
            )
    else:
        print()
        print(f"## SC-008 cross-tab: SKIPPED (attribution CSV missing at {attribution_csv})")

    # Build markdown output
    md_lines = [
        f"# Spec 006 bear-sector-symmetry retrospective — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Spec**: `specs/005-bear-sector-symmetry/`",
        f"**Holding window**: {args.holding_days} trading days",
        f"**Ticker + ETF lookback**: {args.lookback_days} trading days",
        f"**Corpus**: {len(commits)} unique bearish commits → {n_valid} with sector + ETF + α data",
        "",
        f"## Baseline (no filter): n={n_valid}, mean α = {baseline_mean:+.2f}%",
        "",
        "Note: for bearish commits, HIGHER baseline α means the collective bear call "
        "was wrong (the ticker rallied after the bear commit). The filter aims to "
        "suppress those commits to Hold. Net Δα = baseline − kept; positive means "
        "the filter is correctly removing high-α bearish commits.",
        "",
        "## Threshold sweep",
        "",
        "| threshold | n_kept | n_fired | kept α | fired α | net Δα |",
        "|---|---|---|---|---|---|",
    ]
    for r in sweep_rows:
        md_lines.append(
            f"| +{r['threshold']:.1f}% | {r['n_kept']} | {r['n_fired']} | "
            f"{r['kept_mean']:+.2f}% | {r['fired_mean']:+.2f}% | {r['net_dalpha']:+.2f}pp |"
        )
    md_lines.extend(
        [
            "",
            "## Per-sector breakdown at threshold +5.0%",
            "",
            "| Sector | ETF | n_total | n_fired | kept α | fired α | net Δα |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for sector in sorted(valid["sector"].unique()):
        sub = valid[valid["sector"] == sector]
        sub_fire = sub[fire_mask_default[sub.index]]
        sub_kept = sub.drop(sub_fire.index)
        kept_mean = sub_kept["realized_alpha_pct"].mean() if not sub_kept.empty else float("nan")
        fired_mean = sub_fire["realized_alpha_pct"].mean() if not sub_fire.empty else float("nan")
        sub_baseline = sub["realized_alpha_pct"].mean() if not sub.empty else float("nan")
        net_dalpha = sub_baseline - kept_mean if not sub_kept.empty else 0.0
        etf = sub["etf"].iloc[0]
        md_lines.append(
            f"| {sector} | {etf} | {len(sub)} | {len(sub_fire)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )

    if sc008_count is not None:
        md_lines.extend(
            [
                "",
                "## SC-008 cross-tab against `ticker_strong`-bearish cohort",
                "",
                f"At threshold +5.0%: **{sc008_count} of {sc008_total}** "
                f"`ticker_strong`-bearish cohort commits would be suppressed.",
                "",
                f"SC-008 gate: ≥8 of {sc008_total} fire at +5.0% → "
                f"**{'PASS' if sc008_count >= 8 else 'FAIL'}**",
                "",
                "Cohort is loaded from `claudedocs/sector-alpha-attribution-2026-05-06.csv` "
                "filtered to `rating in (Underweight, Sell) AND cell == 'ticker_strong'`.",
            ]
        )

    md_lines.extend(
        [
            "",
            "## Verdict",
            "",
            "Default-on flip is justified iff the threshold sweep shows positive net Δα at the",
            "configured default (+5%) AND SC-008 passes. Net Δα is computed as ",
            "`baseline_mean - kept_mean` — positive means the filter improves the bucket by ",
            "removing high-α (i.e. wrong-direction) bearish commits.",
            "",
            "**Empirical context**: today's sector-α attribution analysis ",
            "(`claudedocs/sector-alpha-attribution-2026-05-06.md`) found 18 of 37 bearish ",
            "commits (48.6%) landed in `ticker_strong` with mean α-vs-SPY = +28.02% — a ",
            "cohort A3 misses entirely. Spec 006 was built to catch that cohort.",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/bear_sector_symmetry_retrospective.py",
            "```",
            "",
            "Reads from `experiments/*/results.csv` + spec 002 sectors cache + yfinance ticker",
            "+ ETF prices. Cross-tab uses `claudedocs/sector-alpha-attribution-2026-05-06.csv`",
            "if available. No LLM cost. Deterministic given a fixed corpus + threshold list.",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md_lines), encoding="utf-8")
    print()
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
