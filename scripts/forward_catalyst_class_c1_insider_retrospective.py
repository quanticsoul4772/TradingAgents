"""Class C-1 forward-catalyst retrospective — insider transactions (cluster buying).

Per `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` Class C-1 entry:
tests whether insider PURCHASES in the prior 30/60/90 days catch the
+28pp ticker_strong-bear cohort that Spec 007 misses on net Δα.

Hypothesis: when insiders are net-buying their own stock, the bear case
the LLM scored high may be priced-in / wrong-direction — suppress further
bear commits.

Mechanism (standalone variant — Mechanism A):
  fire_bear = (insider_buy_count_30d >= threshold) AND (rating in {Underweight, Sell})

Cohort: same 94-commit Opus retrospective cohort (forward-catalyst-class3-opus).

Constitution VIII v1.4.0 forward-catalyst-class gate:
  - Discrim ≥ +5pp in correct direction (PRIMARY)
  - Cohort hit rate ≥ 60% (when target cohort named)
  - Net Δα ≥ +0.5pp at proposed default OR shadow-mode-first

Plus Constitution VIII v1.4.3 additive-to-existing-filter gate:
  - Net Δα improvement ≥ +0.5pp for the union vs Spec 007 bear baseline, OR
  - Cohort hit improvement ≥ +5pp, OR
  - FP-rate improvement ≥ -10pp for the intersection

Decision tree:
  - C-1 PASSES both gates → invoke Spec 010 (Class C-1 standalone)
  - C-1 PASSES standalone but FAILS additive → consider Hybrid D-1 (Spec 007 × C-1 intersection)
  - C-1 FAILS standalone → SKIP entirely; pivot to Class C-3 (analyst PT delta)

Zero LLM cost — yfinance.Ticker(t).insider_transactions is free.

Usage:
    python scripts/forward_catalyst_class_c1_insider_retrospective.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402

CLASS3_CSV = Path("claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv")
OUT_MD = Path("claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.md")
OUT_CSV = Path("claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.csv")

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}

# Test thresholds for "insider buy count in prior N days triggers suppression"
DEFAULT_BUY_COUNT_THRESHOLDS = (1, 2, 3)
DEFAULT_LOOKBACK_DAYS = (30, 60, 90)
DEFAULT_BEAR_THRESHOLD = DEFAULT_CONFIG["forward_catalyst_bear_threshold"]


@cache
def _fetch_insider_transactions(ticker: str) -> pd.DataFrame:
    """Fetch yfinance.insider_transactions; filter to true Purchase events."""
    try:
        it = yf.Ticker(ticker).insider_transactions
        if it is None or it.empty:
            return pd.DataFrame()
        # Filter to actual purchases via Text column (Stock Gifts, Awards, Conversions are NOT real buys)
        if "Text" in it.columns:
            mask = it["Text"].str.contains("Purchase", case=False, na=False)
            buys = it[mask].copy()
            return buys
        return pd.DataFrame()
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] insider_transactions fetch failed for {ticker}: {exc}")
        return pd.DataFrame()


def _insider_buy_features(ticker: str, trade_date: str, lookback_days: int) -> tuple[int, float]:
    """Return (buy_count, total_buy_dollar) over the prior lookback_days."""
    buys = _fetch_insider_transactions(ticker)
    if buys.empty:
        return 0, 0.0
    try:
        td = datetime.fromisoformat(trade_date)
    except (ValueError, AttributeError):
        return 0, 0.0
    window_start = td - timedelta(days=lookback_days)
    # Convert Start Date to pandas datetime for filter
    buys = buys.copy()
    buys["Start Date"] = pd.to_datetime(buys["Start Date"], errors="coerce")
    in_window = buys[(buys["Start Date"] >= window_start) & (buys["Start Date"] < td)]
    if in_window.empty:
        return 0, 0.0
    buy_count = len(in_window)
    buy_dollar = in_window["Value"].fillna(0).sum() if "Value" in in_window.columns else 0.0
    return int(buy_count), float(buy_dollar)


def _eval_standalone_bear_gate(df: pd.DataFrame, threshold: int) -> dict:
    """Standalone Class C-1: fire bear when insider_buy_count >= threshold."""
    df = df.copy()
    df["fire_bear"] = (df["insider_buy_count"] >= threshold) & df["rating"].isin(BEARISH_RATINGS)

    cohort_b = df[df["sample_class"] == "cohort_b_bear_target"]
    bear_commits = df[df["rating"].isin(BEARISH_RATINGS)]

    bear_baseline = bear_commits["alpha_vs_spy_pct"].mean()
    bear_kept_alpha = bear_commits[~bear_commits["fire_bear"]]["alpha_vs_spy_pct"].mean()
    # For bear: HIGH α is wrong; filter HELPS by removing high-α
    # net Δα = baseline - kept; positive = filter helps
    bear_net_dalpha = bear_baseline - bear_kept_alpha if not pd.isna(bear_kept_alpha) else 0.0

    bear_cohort_fired = cohort_b["fire_bear"].sum()
    bear_cohort_hit_rate = bear_cohort_fired / len(cohort_b) * 100 if len(cohort_b) else 0.0

    bear_fired = bear_commits[bear_commits["fire_bear"]]
    bear_fired_cohort = bear_fired[bear_fired["sample_class"] == "cohort_b_bear_target"]
    bear_fired_winner = bear_fired[bear_fired["sample_class"] == "control_bear_winner"]
    bear_fired_cohort_alpha = (
        bear_fired_cohort["alpha_vs_spy_pct"].mean()
        if not bear_fired_cohort.empty
        else float("nan")
    )
    bear_fired_winner_alpha = (
        bear_fired_winner["alpha_vs_spy_pct"].mean()
        if not bear_fired_winner.empty
        else float("nan")
    )
    # For bear: discrim = cohort_α − winner_α; positive = filter correctly catches rallying cohort
    bear_discrim = (
        (bear_fired_cohort_alpha - bear_fired_winner_alpha)
        if (not bear_fired_cohort.empty and not bear_fired_winner.empty)
        else float("nan")
    )

    return {
        "bear_n_fired": int(bear_commits["fire_bear"].sum()),
        "bear_baseline_alpha": bear_baseline,
        "bear_kept_alpha": bear_kept_alpha,
        "bear_net_dalpha": bear_net_dalpha,
        "bear_cohort_hit_rate": bear_cohort_hit_rate,
        "bear_discrim": bear_discrim,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Lookback window for insider purchases (default 30)",
    )
    parser.add_argument(
        "--buy-count-thresholds",
        default=",".join(str(t) for t in DEFAULT_BUY_COUNT_THRESHOLDS),
    )
    args = parser.parse_args()

    thresholds = tuple(int(t) for t in args.buy_count_thresholds.split(","))

    print("# Class C-1 forward-catalyst retrospective — insider transactions (cluster buying)")
    print()
    print(f"Lookback days: {args.lookback_days}")
    print(f"Buy-count thresholds: {thresholds}")
    print("Mechanism A (standalone bear suppression): fire bear when insider_buy_count >= T")
    print()

    if not CLASS3_CSV.exists():
        print(f"[fatal] Class 3 Opus CSV missing: {CLASS3_CSV}")
        return

    df = pd.read_csv(CLASS3_CSV)
    df = df.dropna(subset=["bull_case_priced_in", "bear_case_priced_in", "alpha_vs_spy_pct"]).copy()
    print(f"Loaded {len(df)} rows from {CLASS3_CSV}")

    # Pre-fetch insider transactions per unique ticker
    tickers = sorted(df["ticker"].unique().tolist())
    print()
    print(
        f"Pre-fetching insider transactions for {len(tickers)} unique tickers (one yfinance call each)..."
    )
    n_with_buys = 0
    total_buys = 0
    for t in tickers:
        buys = _fetch_insider_transactions(t)
        if not buys.empty:
            n_with_buys += 1
            total_buys += len(buys)
            print(f"  {t}: {len(buys)} purchase events")
        else:
            print(f"  {t}: no purchase events")
    print(
        f"  Total: {n_with_buys}/{len(tickers)} tickers have insider purchases ({total_buys} total)"
    )

    # Compute features per row
    df["insider_buy_count"] = df.apply(
        lambda r: _insider_buy_features(r["ticker"], r["trade_date"], args.lookback_days)[0],
        axis=1,
    )
    df["insider_buy_dollar"] = df.apply(
        lambda r: _insider_buy_features(r["ticker"], r["trade_date"], args.lookback_days)[1],
        axis=1,
    )

    n_with_buys_in_window = (df["insider_buy_count"] > 0).sum()
    print()
    print(
        f"Of {len(df)} rows, {n_with_buys_in_window} have insider purchases in the prior {args.lookback_days} days"
    )
    print()
    print("Insider buy count distribution (where > 0):")
    nonzero = df[df["insider_buy_count"] > 0]["insider_buy_count"]
    if not nonzero.empty:
        print(nonzero.describe())
        print()
        # Per-cohort breakdown
        print("By sample_class:")
        for sc in df["sample_class"].unique():
            sub = df[df["sample_class"] == sc]
            sub_nonzero = sub[sub["insider_buy_count"] > 0]
            print(
                f"  {sc}: {len(sub_nonzero)}/{len(sub)} rows have insider buys "
                f"(max count={sub_nonzero['insider_buy_count'].max() if not sub_nonzero.empty else 0})"
            )
    else:
        print("  No rows have any insider purchases in the lookback window.")
    print()

    # Bear-side cohort focus
    bear_cohort = df[df["sample_class"] == "cohort_b_bear_target"]
    bear_cohort_with_buys = bear_cohort[bear_cohort["insider_buy_count"] > 0]
    print(
        f"Critical: cohort_b_bear_target ({len(bear_cohort)} rows) — "
        f"{len(bear_cohort_with_buys)} have insider buys in prior {args.lookback_days}d"
    )

    # Sweep thresholds
    print()
    print("## Standalone Class C-1 sweep — bear-side")
    print()
    print("| threshold (≥X buys) | bear n_fired | bear net Δα | bear hit% | bear discrim |")
    print("|---|---|---|---|---|")

    sweep_rows = []
    for t in thresholds:
        metrics = _eval_standalone_bear_gate(df, t)
        discrim_str = (
            f"{metrics['bear_discrim']:+.2f}pp" if not pd.isna(metrics["bear_discrim"]) else "N/A"
        )
        print(
            f"| {t} | {metrics['bear_n_fired']} | {metrics['bear_net_dalpha']:+.2f}pp | "
            f"{metrics['bear_cohort_hit_rate']:.1f}% | {discrim_str} |"
        )
        sweep_rows.append({"threshold": t, "lookback_days": args.lookback_days, **metrics})

    sweep_df = pd.DataFrame(sweep_rows)

    # Pick the best by net_dalpha (primary criterion)
    if not sweep_df.empty and not sweep_df["bear_net_dalpha"].isna().all():
        best = sweep_df.loc[sweep_df["bear_net_dalpha"].idxmax()]
        print()
        print(
            f"## Best Class C-1 standalone config: threshold={int(best['threshold'])}, lookback={int(best['lookback_days'])}d"
        )
        print(f"  Bear net Δα: {best['bear_net_dalpha']:+.2f}pp")
        print(f"  Bear cohort hit: {best['bear_cohort_hit_rate']:.1f}%")
        print(
            f"  Bear discrim: {best['bear_discrim']:+.2f}pp"
            if not pd.isna(best["bear_discrim"])
            else "  Bear discrim: N/A"
        )

        primary_pass = (not pd.isna(best["bear_discrim"])) and best["bear_discrim"] >= 5
        cohort_pass = best["bear_cohort_hit_rate"] >= 60
        net_pass = best["bear_net_dalpha"] >= 0.5

        print()
        print("## Constitution VIII v1.4.0 forward-catalyst-class gate (standalone)")
        print(f"  Discrim ≥ +5pp PRIMARY: {'PASS' if primary_pass else 'FAIL'}")
        print(f"  Cohort hit rate ≥ 60%: {'PASS' if cohort_pass else 'FAIL'}")
        print(f"  Net Δα ≥ +0.5pp: {'PASS' if net_pass else 'FAIL or shadow-mode-first'}")

        if primary_pass and cohort_pass and net_pass:
            standalone_verdict = "PASS — proceed to v1.4.3 additive overlap analysis"
        elif primary_pass and cohort_pass:
            standalone_verdict = "PASS-shadow — proceed to v1.4.3 with shadow-mode-first condition"
        elif primary_pass:
            standalone_verdict = "PARTIAL — discrim passes but cohort hit < 60%"
        else:
            standalone_verdict = "SKIP — Class C-1 fails primary criterion"

        print()
        print(f"## Standalone verdict: {standalone_verdict}")
    else:
        print()
        print("## NO FIRES at any threshold — insider purchases too rare on this cohort")
        print()
        print("## Standalone verdict: SKIP — insufficient signal events")
        best = None

    # Save CSV
    sweep_df.to_csv(OUT_CSV, index=False)
    print()
    print(f"Wrote {OUT_CSV}")

    md_lines = [
        f"# Class C-1 forward-catalyst retrospective — insider transactions — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Hypothesis**: when insiders are net-buying their own stock, the bear case the LLM scored "
        "high may be priced-in / wrong-direction — suppress further bear commits with insider activity.",
        "",
        f"**Mechanism A (standalone)**: `fire_bear = (insider_buy_count_{args.lookback_days}d >= T) "
        "AND (rating in {Underweight, Sell})`",
        "",
        f"**Cohort**: same 94-commit Opus retrospective cohort. {n_with_buys}/{len(tickers)} unique "
        f"tickers have ANY insider purchases (filtered via Text column 'Purchase'); {n_with_buys_in_window} "
        f"of {len(df)} rows have insider buys in the prior {args.lookback_days}-day window.",
        "",
        f"**Critical bear-cohort coverage**: {len(bear_cohort_with_buys)} of {len(bear_cohort)} "
        f"`cohort_b_bear_target` rows have insider purchases in the prior {args.lookback_days}-day window.",
        "",
        "## Standalone bear-side sweep",
        "",
        "| threshold (≥X buys) | bear n_fired | bear net Δα | bear hit% | bear discrim |",
        "|---|---|---|---|---|",
    ]
    for _, r in sweep_df.iterrows():
        discrim_str = f"{r['bear_discrim']:+.2f}pp" if not pd.isna(r["bear_discrim"]) else "N/A"
        md_lines.append(
            f"| {int(r['threshold'])} | {int(r['bear_n_fired'])} | {r['bear_net_dalpha']:+.2f}pp | "
            f"{r['bear_cohort_hit_rate']:.1f}% | {discrim_str} |"
        )

    if best is not None:
        md_lines.extend(
            [
                "",
                f"## Best config: threshold={int(best['threshold'])}, lookback={int(best['lookback_days'])}d",
                "",
                f"- Bear net Δα: {best['bear_net_dalpha']:+.2f}pp",
                f"- Bear cohort hit: {best['bear_cohort_hit_rate']:.1f}%",
                f"- Bear discrim: {best['bear_discrim']:+.2f}pp"
                if not pd.isna(best["bear_discrim"])
                else "- Bear discrim: N/A",
                "",
                "## Constitution VIII v1.4.0 forward-catalyst-class gate (standalone)",
                "",
                f"- Discrim ≥ +5pp PRIMARY: **{'PASS' if primary_pass else 'FAIL'}**",
                f"- Cohort hit rate ≥ 60%: **{'PASS' if cohort_pass else 'FAIL'}**",
                f"- Net Δα ≥ +0.5pp: **{'PASS' if net_pass else 'FAIL or shadow-mode-first'}**",
                "",
                f"## Standalone verdict — {standalone_verdict}",
            ]
        )
    else:
        md_lines.extend(
            [
                "",
                "## Result: NO FIRES at any threshold — insider purchases too rare on this cohort",
                "",
                "## Standalone verdict — SKIP (insufficient signal events)",
                "",
                "**Implication**: Class C-1 (insider transactions) is not a viable mechanism on the "
                "cohort's universe of 18 large-cap tickers. Insider purchases at large-cap tech are "
                "extremely rare events; even when they happen (e.g., INTC), they don't cluster with "
                "the bear cohort's trade dates.",
                "",
                "**Implication for Spec 010 candidate**: per the bear-side design doc decision tree, "
                "C-1 SKIP triggers a pivot to **Class C-3 (analyst PT consensus delta)** as the next "
                "candidate. Analyst PT data is structured + frequent (vs sparse insider purchases) "
                "and historically available via yfinance.",
            ]
        )

    md_lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/forward_catalyst_class_c1_insider_retrospective.py",
            "```",
            "",
            f"Reads cached Class 3 Opus scores from `{CLASS3_CSV}` + free yfinance.insider_transactions "
            f"fetches (one per unique ticker; LRU-cached). Zero LLM cost.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
