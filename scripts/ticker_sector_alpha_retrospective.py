"""Spec 005 (proposed) retrospective — corpus-wide validation of the per-ticker-vs-sector
mean-reversion contrarian gate hypothesis BEFORE writing any spec.

Mechanism under test: when a ticker has OUTPERFORMED its sector ETF by more
than threshold% over the prior N trading days (ticker is at sector-relative
high → mean-reversion zone for buyers), suppress the ticker's Buy/Overweight
commit to Hold. Symmetric inverse of spec 006 (which catches BEARS on
relatively strong tickers); spec 005 would catch BULLS on relatively strong
tickers under the mean-reversion thesis.

Empirical motivation: today's sector-α attribution analysis
(claudedocs/sector-alpha-attribution-2026-05-06.md) found 27 of 79 bullish
commits (34.2%) landed in `ticker_weak` (α<0 vs both SPY AND sector) with
mean realized α-vs-SPY = -5.34%. The cohort is 88.9% Tech-concentrated
(AAPL/MSFT/NVDA). Spec 005 hypothesis: these losers were at sector-relative
highs at signal time, so a backward-looking rel-strength filter would catch
them.

This retrospective tests the hypothesis BEFORE spec-writing. If the filter
is anti-predictive at the natural defaults (mirroring spec 004's and spec
006's retrospective failures), spec 005 doesn't get written — saving the
work of another empty implementation.

Methodology mirrors:
  - scripts/sector_momentum_retrospective.py (spec 004)
  - scripts/bear_sector_symmetry_retrospective.py (spec 006)

Two threshold semantics tested:
  A. Absolute threshold sweep (+3% / +5% / +7.5% / +10%): fire when
     rel_strength_pct > threshold.
  B. Percentile-based: fire when rel_strength_pct > the Nth percentile
     of the entire bullish-commit corpus rel_strength distribution.

Cross-tab against the n=27 ticker_weak-bullish cohort: how many would
the filter fire on at each cut?

Zero LLM cost. Reuses the existing per-row enrichment CSV from
sector_alpha_attribution.py + computes BACKWARD rel-strength via spec 006's
helpers.

Usage:
    python scripts/ticker_sector_alpha_retrospective.py
    python scripts/ticker_sector_alpha_retrospective.py --thresholds 3,5,7.5,10
    python scripts/ticker_sector_alpha_retrospective.py --percentiles 70,80,90
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.agents.utils.bear_sector_symmetry_filter import (  # noqa: E402
    SECTOR_ETF_MAP,
    _compute_etf_30d_return_pct_local,
    _compute_ticker_30d_return_pct,
    clear_etf_cache,
    clear_ticker_cache,
)
from tradingagents.paper.sectors import get_sector  # noqa: E402

EXPERIMENTS_DIR = Path("experiments")
SECTORS_CACHE = Path.home() / ".tradingagents" / "paper" / "sectors.json"
ATTRIBUTION_CSV = Path("claudedocs/sector-alpha-attribution-2026-05-06.csv")
DEFAULT_THRESHOLDS = (3.0, 5.0, 7.5, 10.0)
DEFAULT_PERCENTILES = (70.0, 80.0, 90.0)
BULLISH_RATINGS = {"Buy", "Overweight"}


def _load_bullish_commits_with_alpha() -> pd.DataFrame:
    """Load bullish commits from the sector-α attribution CSV. Has alpha
    vs SPY + alpha vs sector + cell classification already."""
    if not ATTRIBUTION_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(ATTRIBUTION_CSV)
    df = df[df["rating"].isin(BULLISH_RATINGS)]
    return df.reset_index(drop=True)


def _ensure_sector_etf(df: pd.DataFrame) -> pd.DataFrame:
    """Add `sector` + `etf` columns by yfinance lookup (cached)."""
    sector_cache: dict[str, str] = {}
    rows = []
    for _, r in df.iterrows():
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
        rows.append({**r.to_dict(), "sector": sector, "etf": etf})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--thresholds",
        default=",".join(str(t) for t in DEFAULT_THRESHOLDS),
        help="Comma-separated positive thresholds in percent (default: 3,5,7.5,10)",
    )
    parser.add_argument(
        "--percentiles",
        default=",".join(str(p) for p in DEFAULT_PERCENTILES),
        help="Comma-separated percentile cuts of the bullish-corpus rel-strength distribution",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Ticker + ETF prior-N-day lookback for the BACKWARD-looking rel-strength (default 30)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md"),
        help="Output markdown path",
    )
    args = parser.parse_args()

    thresholds = tuple(sorted(float(t) for t in args.thresholds.split(",")))
    percentiles = tuple(sorted(float(p) for p in args.percentiles.split(",")))

    print("# Spec 005 (proposed) retrospective — backward-looking ticker-vs-sector signal")
    print()
    print(f"Lookback: {args.lookback_days} trading days")
    print(f"Threshold sweep: {thresholds}")
    print(f"Percentile sweep: {percentiles}")
    print()

    print(f"Loading bullish commits from {ATTRIBUTION_CSV}...")
    df = _load_bullish_commits_with_alpha()
    if df.empty:
        print(f"[fatal] attribution CSV missing or no bullish rows: {ATTRIBUTION_CSV}")
        return
    print(f"  {len(df)} bullish commits loaded (with cached forward α + cell)")

    df = _ensure_sector_etf(df)
    n_eligible = len(df)
    print(f"  {n_eligible} commits with mappable sector/ETF")

    if df.empty:
        print("[fatal] no commits with mappable sectors")
        return

    # Compute BACKWARD-looking ticker prior-30d return + ETF prior-30d return + delta
    print()
    print("Computing backward-looking rel-strength (ticker-30d - ETF-30d via yfinance LRU)...")
    clear_etf_cache()
    clear_ticker_cache()
    ticker_returns: list[float | None] = []
    etf_returns: list[float | None] = []
    for i, r in df.iterrows():
        if i > 0 and i % 25 == 0:
            print(f"  [{i}/{n_eligible}]")
        t_ret = _compute_ticker_30d_return_pct(
            r["ticker"], r["trade_date"], lookback_days=args.lookback_days
        )
        e_ret = _compute_etf_30d_return_pct_local(
            r["etf"], r["trade_date"], lookback_days=args.lookback_days
        )
        ticker_returns.append(t_ret)
        etf_returns.append(e_ret)
    df["ticker_30d_return_pct"] = ticker_returns
    df["etf_30d_return_pct"] = etf_returns
    df["rel_strength_pct"] = df["ticker_30d_return_pct"].astype(float) - df[
        "etf_30d_return_pct"
    ].astype(float)

    valid = df.dropna(
        subset=["ticker_30d_return_pct", "etf_30d_return_pct", "alpha_vs_spy_pct"]
    ).reset_index(drop=True)
    n_valid = len(valid)
    print(f"  {n_valid} commits with full data (forward α + backward rel-strength)")

    if n_valid == 0:
        print("[fatal] no commits with valid data")
        return

    baseline_mean = valid["alpha_vs_spy_pct"].mean()
    print()
    print(f"## Baseline (no filter): n={n_valid}, mean α vs SPY = {baseline_mean:+.2f}%")
    print()
    print(
        "For BULLISH commits: HIGHER baseline α means the bull call was right (ticker rallied). "
        "The filter aims to suppress losers (commits with α<0 vs SPY → wrong calls). "
        "Net Δα = kept_α − baseline_α; positive means the filter is correctly removing losers."
    )
    print()

    # ---- Distribution summary ---------------------------------------------

    print("## Rel-strength distribution across bullish corpus")
    print()
    print(f"  count: {n_valid}")
    print(f"  mean : {valid['rel_strength_pct'].mean():+.2f}%")
    print(f"  std  : {valid['rel_strength_pct'].std():.2f}%")
    print(f"  min  : {valid['rel_strength_pct'].min():+.2f}%")
    pct_summary = valid["rel_strength_pct"].quantile([0.25, 0.5, 0.75, 0.9, 0.95])
    print(f"  p25  : {pct_summary.iloc[0]:+.2f}%")
    print(f"  p50  : {pct_summary.iloc[1]:+.2f}%")
    print(f"  p75  : {pct_summary.iloc[2]:+.2f}%")
    print(f"  p90  : {pct_summary.iloc[3]:+.2f}%")
    print(f"  p95  : {pct_summary.iloc[4]:+.2f}%")
    print(f"  max  : {valid['rel_strength_pct'].max():+.2f}%")

    # ---- Threshold sweep --------------------------------------------------

    print()
    print("## Mechanism A — Absolute threshold sweep")
    print()
    print("Fire when rel_strength_pct > threshold (ticker outperformed sector by >X%).")
    print("Net Δα = kept_α − baseline_α; positive = filter helps by removing losers.")
    print()
    print("| threshold | n_kept | n_fired | kept α | fired α | net Δα |")
    print("|---|---|---|---|---|---|")
    threshold_rows = []
    for thr in thresholds:
        fire_mask = valid["rel_strength_pct"] > thr
        kept = valid[~fire_mask]
        fired = valid[fire_mask]
        kept_mean = kept["alpha_vs_spy_pct"].mean() if not kept.empty else float("nan")
        fired_mean = fired["alpha_vs_spy_pct"].mean() if not fired.empty else float("nan")
        net_dalpha = kept_mean - baseline_mean if not kept.empty else 0.0
        print(
            f"| +{thr:.1f}% | {len(kept)} | {len(fired)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )
        threshold_rows.append(
            {
                "threshold": thr,
                "n_kept": len(kept),
                "n_fired": len(fired),
                "kept_mean": kept_mean,
                "fired_mean": fired_mean,
                "net_dalpha": net_dalpha,
            }
        )

    # ---- Percentile sweep -------------------------------------------------

    print()
    print("## Mechanism B — Percentile-based sweep (corpus distribution)")
    print()
    print("Fire when rel_strength_pct > Nth percentile of the bullish-corpus distribution.")
    print("More noise-robust than absolute threshold (per-corpus normalized).")
    print()
    print("| percentile | cutoff | n_kept | n_fired | kept α | fired α | net Δα |")
    print("|---|---|---|---|---|---|---|")
    percentile_rows = []
    for pct in percentiles:
        cutoff = float(valid["rel_strength_pct"].quantile(pct / 100.0))
        fire_mask = valid["rel_strength_pct"] > cutoff
        kept = valid[~fire_mask]
        fired = valid[fire_mask]
        kept_mean = kept["alpha_vs_spy_pct"].mean() if not kept.empty else float("nan")
        fired_mean = fired["alpha_vs_spy_pct"].mean() if not fired.empty else float("nan")
        net_dalpha = kept_mean - baseline_mean if not kept.empty else 0.0
        print(
            f"| p{pct:.0f} | +{cutoff:.2f}% | {len(kept)} | {len(fired)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )
        percentile_rows.append(
            {
                "percentile": pct,
                "cutoff": cutoff,
                "n_kept": len(kept),
                "n_fired": len(fired),
                "kept_mean": kept_mean,
                "fired_mean": fired_mean,
                "net_dalpha": net_dalpha,
            }
        )

    # ---- Per-sector breakdown at default threshold (+5%) ------------------

    print()
    print("## Per-sector breakdown at threshold +5.0%")
    print()
    print("| Sector | ETF | n_total | n_fired | kept α | fired α | net Δα |")
    print("|---|---|---|---|---|---|---|")
    fire_default = valid["rel_strength_pct"] > 5.0
    for sector in sorted(valid["sector"].unique()):
        sub = valid[valid["sector"] == sector]
        sub_fire = sub[fire_default[sub.index]]
        sub_kept = sub.drop(sub_fire.index)
        kept_mean = sub_kept["alpha_vs_spy_pct"].mean() if not sub_kept.empty else float("nan")
        fired_mean = sub_fire["alpha_vs_spy_pct"].mean() if not sub_fire.empty else float("nan")
        sub_baseline = sub["alpha_vs_spy_pct"].mean() if not sub.empty else float("nan")
        net_dalpha = kept_mean - sub_baseline if not sub_kept.empty else 0.0
        etf = sub["etf"].iloc[0]
        print(
            f"| {sector} | {etf} | {len(sub)} | {len(sub_fire)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )

    # ---- ticker_weak cohort cross-tab -------------------------------------

    print()
    print("## Cross-tab: bullish `ticker_weak` cohort (the spec 005 target)")
    print()
    print("From today's sector-α attribution: 27 bullish commits in the ticker_weak cell")
    print("(α<0 vs both SPY AND sector). The spec 005 hypothesis predicts these losers were")
    print("at sector-relative highs at signal time → backward-looking rel-strength catches them.")
    print()
    target_cohort = valid[valid["cell"] == "ticker_weak"]
    n_cohort = len(target_cohort)
    print(f"Cohort size in this retrospective (after filtering for valid data): {n_cohort}")
    print()
    print("| cut | suppressed | hit rate (%) | mean α suppressed |")
    print("|---|---|---|---|")
    for thr in thresholds:
        sup = target_cohort[target_cohort["rel_strength_pct"] > thr]
        hr = (len(sup) / n_cohort * 100.0) if n_cohort else 0.0
        sup_alpha = sup["alpha_vs_spy_pct"].mean() if not sup.empty else float("nan")
        print(f"| +{thr:.1f}% (abs) | {len(sup)} | {hr:.1f}% | {sup_alpha:+.2f}% |")
    for pct in percentiles:
        cutoff = float(valid["rel_strength_pct"].quantile(pct / 100.0))
        sup = target_cohort[target_cohort["rel_strength_pct"] > cutoff]
        hr = (len(sup) / n_cohort * 100.0) if n_cohort else 0.0
        sup_alpha = sup["alpha_vs_spy_pct"].mean() if not sup.empty else float("nan")
        print(f"| p{pct:.0f} (+{cutoff:.2f}%) | {len(sup)} | {hr:.1f}% | {sup_alpha:+.2f}% |")

    # ---- Build markdown output --------------------------------------------

    md = [
        f"# Spec 005 (proposed) retrospective — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Hypothesis under test**: backward-looking rolling-ticker-vs-sector signal can",
        "identify the n=27 bullish ticker_weak cohort BEFORE spec-writing. Mirrors spec 006's",
        "mechanism (threshold on rel-strength delta) but BULL side. Today's spec 006",
        "retrospective failed; this retrospective tests whether the bull-side analog also",
        "fails before any implementation work is done.",
        "",
        f"**Lookback**: {args.lookback_days} trading days",
        f"**Corpus**: {n_valid} bullish commits with full data (from `{ATTRIBUTION_CSV}`)",
        f"**Baseline (no filter)**: n={n_valid}, mean α vs SPY = {baseline_mean:+.2f}%",
        "",
        "## Rel-strength distribution",
        "",
        "| stat | value |",
        "|---|---|",
        f"| count | {n_valid} |",
        f"| mean | {valid['rel_strength_pct'].mean():+.2f}% |",
        f"| std | {valid['rel_strength_pct'].std():.2f}% |",
        f"| min | {valid['rel_strength_pct'].min():+.2f}% |",
        f"| p25 | {pct_summary.iloc[0]:+.2f}% |",
        f"| p50 | {pct_summary.iloc[1]:+.2f}% |",
        f"| p75 | {pct_summary.iloc[2]:+.2f}% |",
        f"| p90 | {pct_summary.iloc[3]:+.2f}% |",
        f"| p95 | {pct_summary.iloc[4]:+.2f}% |",
        f"| max | {valid['rel_strength_pct'].max():+.2f}% |",
        "",
        "## Mechanism A — Absolute threshold sweep",
        "",
        "Fire when `rel_strength_pct > threshold`. Net Δα = kept_α − baseline_α; positive",
        "means the filter helps by removing losers.",
        "",
        "| threshold | n_kept | n_fired | kept α | fired α | net Δα |",
        "|---|---|---|---|---|---|",
    ]
    for r in threshold_rows:
        md.append(
            f"| +{r['threshold']:.1f}% | {r['n_kept']} | {r['n_fired']} | "
            f"{r['kept_mean']:+.2f}% | {r['fired_mean']:+.2f}% | {r['net_dalpha']:+.2f}pp |"
        )
    md.extend(
        [
            "",
            "## Mechanism B — Percentile-based sweep",
            "",
            "Fire when `rel_strength_pct > Nth percentile of bullish-corpus distribution`.",
            "More noise-robust than absolute threshold (per-corpus normalized).",
            "",
            "| percentile | cutoff | n_kept | n_fired | kept α | fired α | net Δα |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for r in percentile_rows:
        md.append(
            f"| p{r['percentile']:.0f} | +{r['cutoff']:.2f}% | {r['n_kept']} | {r['n_fired']} | "
            f"{r['kept_mean']:+.2f}% | {r['fired_mean']:+.2f}% | {r['net_dalpha']:+.2f}pp |"
        )

    md.extend(
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
        sub_fire = sub[fire_default[sub.index]]
        sub_kept = sub.drop(sub_fire.index)
        kept_mean = sub_kept["alpha_vs_spy_pct"].mean() if not sub_kept.empty else float("nan")
        fired_mean = sub_fire["alpha_vs_spy_pct"].mean() if not sub_fire.empty else float("nan")
        sub_baseline = sub["alpha_vs_spy_pct"].mean() if not sub.empty else float("nan")
        net_dalpha = kept_mean - sub_baseline if not sub_kept.empty else 0.0
        etf = sub["etf"].iloc[0]
        md.append(
            f"| {sector} | {etf} | {len(sub)} | {len(sub_fire)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )

    md.extend(
        [
            "",
            f"## Cross-tab: bullish `ticker_weak` cohort (n={n_cohort}; the spec 005 target)",
            "",
            "From today's sector-α attribution: bullish commits with α<0 vs SPY AND vs sector.",
            "The spec 005 hypothesis predicts these losers were at sector-relative highs at",
            "signal time → backward-looking rel-strength would catch them.",
            "",
            "| cut | suppressed | hit rate of cohort | mean α of suppressed |",
            "|---|---|---|---|",
        ]
    )
    for thr in thresholds:
        sup = target_cohort[target_cohort["rel_strength_pct"] > thr]
        hr = (len(sup) / n_cohort * 100.0) if n_cohort else 0.0
        sup_alpha = sup["alpha_vs_spy_pct"].mean() if not sup.empty else float("nan")
        md.append(f"| +{thr:.1f}% (abs) | {len(sup)} | {hr:.1f}% | {sup_alpha:+.2f}% |")
    for pct in percentiles:
        cutoff = float(valid["rel_strength_pct"].quantile(pct / 100.0))
        sup = target_cohort[target_cohort["rel_strength_pct"] > cutoff]
        hr = (len(sup) / n_cohort * 100.0) if n_cohort else 0.0
        sup_alpha = sup["alpha_vs_spy_pct"].mean() if not sup.empty else float("nan")
        md.append(f"| p{pct:.0f} (+{cutoff:.2f}%) | {len(sup)} | {hr:.1f}% | {sup_alpha:+.2f}% |")

    # Verdict block — to be filled in after seeing the numbers (placeholder
    # text + decision criteria for operator).
    md.extend(
        [
            "",
            "## Verdict (manual fill-in after numbers)",
            "",
            "**Spec 005 should be written iff** at least ONE of the threshold/percentile cuts",
            "above shows BOTH:",
            "",
            "1. Net Δα ≥ +1pp at the chosen cut (filter improves the bucket by removing losers)",
            "2. Cohort hit rate ≥ 40% (filter actually catches the ticker_weak commits the spec",
            "   was built to address; ≥11 of 27)",
            "",
            "**Spec 005 should be SKIPPED if**:",
            "",
            "- All cuts show net Δα ≤ 0 (filter is anti-predictive at every threshold)",
            "- OR cohort hit rate is < 30% at every cut (filter doesn't catch the target cohort)",
            "",
            "Spec 006's retrospective failed both criteria. If this bull-side analog fails the",
            "same way, the broader lesson is that backward-looking price filters cannot catch",
            "cohorts whose realized α comes from forward-only catalysts — irrespective of bull",
            "or bear side. Constitution VIII candidate.",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/ticker_sector_alpha_retrospective.py",
            "```",
            "",
            "Reads `claudedocs/sector-alpha-attribution-2026-05-06.csv` for forward α + cell;",
            "fetches yfinance ticker + ETF prices for backward rel-strength; uses spec 002",
            "sectors cache. No LLM cost. Deterministic given a fixed corpus + threshold list.",
        ]
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md), encoding="utf-8")
    print()
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
