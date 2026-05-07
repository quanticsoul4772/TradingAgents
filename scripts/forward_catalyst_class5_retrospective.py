"""Class 5 forward-catalyst retrospective — fundamentals delta (recent earnings surprise).

Per Spec 008+ design doc Class 5 entry: tests whether the most-recent
earnings-surprise magnitude (epsActual vs epsEstimate, in %) discriminates
bull-side commits whose realized α is poor.

Hypothesis: when a ticker has a recent POSITIVE earnings surprise, the bull
case the LLM scored high is more likely to already be priced in by the
market — further bull commits face limited upside. So bull commits with
recent surprise > threshold should be SUPPRESSED.

Mechanism (standalone variant — Mechanism A):
  fire_bull = (most_recent_surprise_pct > threshold) AND (rating in {Buy, OW})

Cohort: same 94-commit Opus retrospective cohort (forward-catalyst-class3-opus).

Constitution VIII v1.4.0 forward-catalyst-class gate:
  - Discrim ≥ +5pp in correct direction (PRIMARY)
  - Cohort hit rate ≥ 60% (when target cohort named)
  - Net Δα ≥ +0.5pp at proposed default OR shadow-mode-first

Decision tree:
  - Class 5 standalone PASSES gate → invoke Spec 010 (Class 5 standalone)
  - Class 5 fails standalone but improves over Class 3 baseline at hybrid-B
    config → consider invoking Spec 010 as Hybrid B (Class 3 × Class 5)
  - Class 5 neither passes standalone nor improves Class 3 → SKIP spec;
    document negative finding

Zero LLM cost — yfinance.Ticker(t).earnings_history is free.

Usage:
    python scripts/forward_catalyst_class5_retrospective.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from functools import cache
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402

CLASS3_CSV = Path("claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv")
OUT_MD = Path("claudedocs/forward-catalyst-class5-retrospective-2026-05-06.md")
OUT_CSV = Path("claudedocs/forward-catalyst-class5-retrospective-2026-05-06.csv")

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}

# Test thresholds for "recent surprise % triggers suppression"
# Surprise scale is fractional (0.05 = 5% beat); typical large-cap range 0-15%
DEFAULT_SURPRISE_THRESHOLDS = (0.02, 0.05, 0.08, 0.12)
DEFAULT_BULL_THRESHOLD_FOR_HYBRID = DEFAULT_CONFIG["forward_catalyst_bull_threshold"]


@cache
def _fetch_earnings_history(ticker: str) -> pd.DataFrame:
    """Fetch yfinance.earnings_history (epsActual / epsEstimate / surprisePercent)."""
    try:
        eh = yf.Ticker(ticker).earnings_history
        if eh is None or eh.empty:
            return pd.DataFrame()
        return eh
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] earnings_history fetch failed for {ticker}: {exc}")
        return pd.DataFrame()


def _most_recent_surprise(ticker: str, trade_date: str) -> float | None:
    """Return surprisePercent of the most recent earnings before trade_date."""
    eh = _fetch_earnings_history(ticker)
    if eh.empty:
        return None
    try:
        td = datetime.fromisoformat(trade_date).date()
    except (ValueError, AttributeError):
        return None
    # earnings_history index is quarter-end dates; filter to those before trade_date
    eh_idx_dates = [d.date() if hasattr(d, "date") else d for d in eh.index]
    past = [(d, eh.iloc[i]) for i, d in enumerate(eh_idx_dates) if d < td]
    if not past:
        return None
    # Most recent = max by date
    past.sort(key=lambda r: r[0], reverse=True)
    most_recent_row = past[0][1]
    surprise = most_recent_row.get("surprisePercent")
    if surprise is None or pd.isna(surprise):
        return None
    return float(surprise)


def _eval_standalone_bull_gate(df: pd.DataFrame, threshold: float) -> dict:
    """Standalone Class 5: fire bull when most_recent_surprise > threshold."""
    df = df.copy()
    df["fire_bull"] = (df["surprise_pct"] > threshold) & df["rating"].isin(BULLISH_RATINGS)

    cohort_a = df[df["sample_class"] == "cohort_a_bull_target"]
    bull_commits = df[df["rating"].isin(BULLISH_RATINGS)]

    bull_baseline = bull_commits["alpha_vs_spy_pct"].mean()
    bull_kept_alpha = bull_commits[~bull_commits["fire_bull"]]["alpha_vs_spy_pct"].mean()
    bull_net_dalpha = bull_kept_alpha - bull_baseline if not pd.isna(bull_kept_alpha) else 0.0

    bull_cohort_fired = cohort_a["fire_bull"].sum()
    bull_cohort_hit_rate = bull_cohort_fired / len(cohort_a) * 100 if len(cohort_a) else 0.0

    bull_fired = bull_commits[bull_commits["fire_bull"]]
    bull_fired_cohort = bull_fired[bull_fired["sample_class"] == "cohort_a_bull_target"]
    bull_fired_winner = bull_fired[bull_fired["sample_class"] == "control_bull_winner"]
    bull_fired_cohort_alpha = (
        bull_fired_cohort["alpha_vs_spy_pct"].mean()
        if not bull_fired_cohort.empty
        else float("nan")
    )
    bull_fired_winner_alpha = (
        bull_fired_winner["alpha_vs_spy_pct"].mean()
        if not bull_fired_winner.empty
        else float("nan")
    )
    # Discrim = noncohort_α − cohort_α; positive = filter catches losers correctly
    bull_discrim = (
        (bull_fired_winner_alpha - bull_fired_cohort_alpha)
        if (not bull_fired_cohort.empty and not bull_fired_winner.empty)
        else float("nan")
    )

    return {
        "bull_n_fired": int(bull_commits["fire_bull"].sum()),
        "bull_baseline_alpha": bull_baseline,
        "bull_kept_alpha": bull_kept_alpha,
        "bull_net_dalpha": bull_net_dalpha,
        "bull_cohort_hit_rate": bull_cohort_hit_rate,
        "bull_discrim": bull_discrim,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--surprise-thresholds",
        default=",".join(str(t) for t in DEFAULT_SURPRISE_THRESHOLDS),
        help="Comma-separated surprise %% thresholds (fractional; e.g. 0.05=5%%)",
    )
    args = parser.parse_args()

    thresholds = tuple(float(t) for t in args.surprise_thresholds.split(","))

    print(
        "# Class 5 forward-catalyst retrospective — fundamentals delta (recent earnings surprise)"
    )
    print()
    print(f"Surprise thresholds (fractional): {thresholds}")
    print("Mechanism A (standalone): fire bull when surprise_pct > T")
    print()

    if not CLASS3_CSV.exists():
        print(f"[fatal] Class 3 Opus CSV missing: {CLASS3_CSV}")
        return

    df = pd.read_csv(CLASS3_CSV)
    df = df.dropna(subset=["bull_case_priced_in", "bear_case_priced_in", "alpha_vs_spy_pct"]).copy()
    print(f"Loaded {len(df)} rows from {CLASS3_CSV}")

    print()
    print("Building earnings-history cache (one yfinance call per unique ticker)...")
    tickers = sorted(df["ticker"].unique().tolist())
    print(f"  {len(tickers)} unique tickers")
    n_with_history = 0
    for t in tickers:
        eh = _fetch_earnings_history(t)
        if not eh.empty:
            n_with_history += 1
    print(f"  {n_with_history} of {len(tickers)} have earnings_history available")

    df["surprise_pct"] = df.apply(
        lambda r: _most_recent_surprise(r["ticker"], r["trade_date"]),
        axis=1,
    )

    n_with_surprise = df["surprise_pct"].notna().sum()
    print(f"  {n_with_surprise} of {len(df)} rows have computable surprise_pct")
    print()
    print("Surprise distribution (where available):")
    print(df["surprise_pct"].dropna().describe())
    print()

    # Drop rows without surprise data for fair gate evaluation
    df_with_surprise = df.dropna(subset=["surprise_pct"]).copy()
    print(f"Evaluating gate on {len(df_with_surprise)} rows with surprise data")
    print()

    print("## Standalone Class 5 sweep — bull-side")
    print()
    print("| threshold | bull n_fired | bull net Δα | bull hit% | bull discrim |")
    print("|---|---|---|---|---|")

    sweep_rows = []
    for t in thresholds:
        metrics = _eval_standalone_bull_gate(df_with_surprise, t)
        print(
            f"| {t:.2f} | {metrics['bull_n_fired']} | {metrics['bull_net_dalpha']:+.2f}pp | "
            f"{metrics['bull_cohort_hit_rate']:.1f}% | {metrics['bull_discrim']:+.2f}pp |"
        )
        sweep_rows.append({"threshold": t, **metrics})

    sweep_df = pd.DataFrame(sweep_rows)

    # Find best by net_dalpha (primary criterion for standalone)
    best = sweep_df.loc[sweep_df["bull_net_dalpha"].idxmax()]
    print()
    print(f"## Best Class 5 standalone config: threshold={best['threshold']:.2f}")
    print(f"  Bull net Δα: {best['bull_net_dalpha']:+.2f}pp")
    print(f"  Bull cohort hit: {best['bull_cohort_hit_rate']:.1f}%")
    print(f"  Bull discrim: {best['bull_discrim']:+.2f}pp")

    primary_pass = best["bull_discrim"] >= 5
    cohort_pass = best["bull_cohort_hit_rate"] >= 60
    net_pass = best["bull_net_dalpha"] >= 0.5

    print()
    print("## Constitution VIII v1.4.0 forward-catalyst-class gate")
    print(
        f"  Discrim ≥ +5pp PRIMARY: {'PASS' if primary_pass else 'FAIL'} ({best['bull_discrim']:+.2f}pp)"
    )
    print(
        f"  Cohort hit rate ≥ 60%: {'PASS' if cohort_pass else 'FAIL'} ({best['bull_cohort_hit_rate']:.1f}%)"
    )
    print(
        f"  Net Δα ≥ +0.5pp: {'PASS' if net_pass else 'FAIL or shadow-mode-first if 1+2 pass'} ({best['bull_net_dalpha']:+.2f}pp)"
    )

    if primary_pass and cohort_pass and net_pass:
        verdict = "PASS — invoke Spec 010 (Class 5 standalone, default-on at best threshold)"
    elif primary_pass and cohort_pass:
        verdict = "PASS-shadow — invoke Spec 010 with shadow-mode-first condition"
    elif primary_pass:
        verdict = (
            "PARTIAL — discrim passes but cohort hit < 60%; SKIP standalone, consider Hybrid B"
        )
    else:
        verdict = "SKIP — Class 5 fails primary discrim criterion"

    print()
    print(f"## Verdict (standalone): {verdict}")

    sweep_df.to_csv(OUT_CSV, index=False)
    print()
    print(f"Wrote {OUT_CSV}")

    md = [
        f"# Class 5 forward-catalyst retrospective — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Hypothesis**: when a ticker has a recent POSITIVE earnings surprise, the bull case the LLM "
        "scored high is more likely to already be priced in by the market — further bull commits face "
        "limited upside. So bull commits with recent surprise > threshold should be SUPPRESSED.",
        "",
        "**Mechanism A (standalone)**: `fire_bull = (most_recent_surprise_pct > threshold) AND (rating in {Buy, OW})`",
        "",
        f"**Cohort**: same 94-commit Opus retrospective cohort. {n_with_surprise} of {len(df)} rows "
        f"have computable surprise data ({n_with_history}/{len(tickers)} tickers have earnings_history).",
        "",
        "## Surprise distribution",
        "",
        "| stat | value |",
        "|---|---|",
        f"| count | {df['surprise_pct'].notna().sum()} |",
        f"| mean | {df['surprise_pct'].mean():.4f} |",
        f"| std | {df['surprise_pct'].std():.4f} |",
        f"| min | {df['surprise_pct'].min():.4f} |",
        f"| 25% | {df['surprise_pct'].quantile(0.25):.4f} |",
        f"| 50% | {df['surprise_pct'].quantile(0.50):.4f} |",
        f"| 75% | {df['surprise_pct'].quantile(0.75):.4f} |",
        f"| max | {df['surprise_pct'].max():.4f} |",
        "",
        "## Standalone bull-side gate sweep",
        "",
        "| threshold | bull n_fired | bull net Δα | bull hit% | bull discrim |",
        "|---|---|---|---|---|",
    ]
    for _, r in sweep_df.iterrows():
        md.append(
            f"| {r['threshold']:.2f} | {int(r['bull_n_fired'])} | {r['bull_net_dalpha']:+.2f}pp | "
            f"{r['bull_cohort_hit_rate']:.1f}% | {r['bull_discrim']:+.2f}pp |"
        )

    md.extend(
        [
            "",
            f"## Best Class 5 standalone config: threshold={best['threshold']:.2f}",
            "",
            f"- Bull net Δα: {best['bull_net_dalpha']:+.2f}pp",
            f"- Bull cohort hit: {best['bull_cohort_hit_rate']:.1f}%",
            f"- Bull discrim: {best['bull_discrim']:+.2f}pp",
            "",
            "## Constitution VIII v1.4.0 forward-catalyst-class gate",
            "",
            f"- Discrim ≥ +5pp PRIMARY: **{'PASS' if primary_pass else 'FAIL'}** ({best['bull_discrim']:+.2f}pp)",
            f"- Cohort hit rate ≥ 60%: **{'PASS' if cohort_pass else 'FAIL'}** ({best['bull_cohort_hit_rate']:.1f}%)",
            f"- Net Δα ≥ +0.5pp: **{'PASS' if net_pass else 'shadow-mode-first if 1+2 pass'}** ({best['bull_net_dalpha']:+.2f}pp)",
            "",
            f"## Verdict — {verdict}",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/forward_catalyst_class5_retrospective.py",
            "```",
            "",
            f"Reads cached Class 3 Opus scores from `{CLASS3_CSV}` + free yfinance.earnings_history "
            f"fetches (one per unique ticker; LRU-cached). Zero LLM cost.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
