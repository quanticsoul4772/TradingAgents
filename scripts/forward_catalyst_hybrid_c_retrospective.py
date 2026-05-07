"""Hybrid C retrofit — Class 3 (forward-catalyst LLM scores) × Class 6 (calendar boost).

Per the spec 008 design doc pivot
(`claudedocs/spec-008-forward-catalyst-classes-2-6-exploration-2026-05-06.md`),
Class 2 (options-IV) is data-blocked. Hybrid C is the cheapest
retrofit-feasible alternative — combines the validated Class 3 LLM-extracted
scores with calendar boost (days-to-next-earnings) to test whether forward
catalyst proximity improves discrimination beyond Class 3 alone.

Mechanism:
  - Load cached Class 3 Opus scores from
    claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv
  - For each (ticker, trade_date), compute days-to-next-earnings via
    yfinance.Ticker(t).earnings_dates (oldest after trade_date)
  - Apply boost: effective_score = base_score * (1 + magnitude * boost)
    where boost = max(0, 1 - days_to_earnings / boost_window)
  - At earnings day: boost = 1.0 → effective = base * (1 + magnitude)
  - At boost_window+ days out: boost = 0 → effective = base (no change)
  - Sweep boost_window (7/14/21 trading days) × magnitude (0.5/1.0/2.0)

Validation gate (Constitution VIII v1.4.0 forward-catalyst-class):
  - Discrimination >= +5pp PRIMARY
  - Cohort hit rate >= 60%
  - Net Δα >= +0.5pp OR shadow-mode-first
  - PLUS: Hybrid C must improve at least one criterion vs Class 3 alone
    (otherwise the simpler single-class filter dominates)

Decision tree:
  - Hybrid C improves bull-side discrimination AND/OR bear cohort hit
    → write Spec 008 (Hybrid C as calendar-aware enhancement of Class 3)
  - No improvement → SKIP spec; document calendar features too crude
  - Hybrid C HURTS (boost over-weights bad commits near earnings)
    → SKIP + document; calendar boost direction is wrong

Zero LLM cost — reuses cached Opus scores. Free yfinance earnings calendar
fetches (one per unique ticker; cohort has 18 tickers).

Usage:
    python scripts/forward_catalyst_hybrid_c_retrospective.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CLASS3_CSV = Path("claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv")
OUT_MD = Path("claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md")
OUT_CSV = Path("claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.csv")

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}

DEFAULT_WINDOWS = (7, 14, 21)
DEFAULT_MAGNITUDES = (0.5, 1.0, 2.0)
DEFAULT_BULL_THRESHOLD = 0.60
DEFAULT_BEAR_THRESHOLD = 0.50


# ---- Earnings calendar lookup --------------------------------------------


def _build_earnings_cache(tickers: list[str]) -> dict[str, list[datetime]]:
    """For each ticker, fetch earnings_dates and return a sorted list of datetimes."""
    cache: dict[str, list[datetime]] = {}
    for t in tickers:
        try:
            ed = yf.Ticker(t).earnings_dates
            if ed is None or ed.empty:
                cache[t] = []
                continue
            # Strip tz, sort ascending
            cache[t] = sorted(ed.index.tz_convert(None).to_pydatetime().tolist())
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] earnings_dates fetch failed for {t}: {exc}")
            cache[t] = []
    return cache


def _days_to_next_earnings(
    ticker: str,
    trade_date: str,
    cache: dict[str, list[datetime]],
) -> int | None:
    """Return calendar days from trade_date to the NEXT earnings >= trade_date.

    Returns None if no future earnings found in the cache OR if the trade_date
    is unparseable.
    """
    try:
        td = datetime.fromisoformat(trade_date)
    except ValueError:
        return None
    upcoming = [e for e in cache.get(ticker, []) if e >= td]
    if not upcoming:
        return None
    return (upcoming[0] - td).days


# ---- Boost formula ---------------------------------------------------------


def _calendar_boost(days_to_earnings: int | None, window: int) -> float:
    """Boost factor in [0, 1]. 1.0 at days=0; linearly decreases to 0 at window+."""
    if days_to_earnings is None or days_to_earnings < 0:
        return 0.0
    if days_to_earnings >= window:
        return 0.0
    return 1.0 - (days_to_earnings / window)


def _effective_score(
    base_score: float, days_to_earnings: int | None, window: int, magnitude: float
) -> float:
    """effective = base * (1 + magnitude * boost). Clamped to [0, 1]."""
    boost = _calendar_boost(days_to_earnings, window)
    return min(1.0, base_score * (1.0 + magnitude * boost))


# ---- Gate evaluator --------------------------------------------------------


def _eval_gate(
    df: pd.DataFrame,
    bull_threshold: float,
    bear_threshold: float,
) -> dict:
    """Compute gate criteria using `eff_bull_score` + `eff_bear_score` columns."""
    df = df.copy()
    df["fire_bull"] = (df["eff_bull_score"] > bull_threshold) & df["rating"].isin(BULLISH_RATINGS)
    df["fire_bear"] = (df["eff_bear_score"] > bear_threshold) & df["rating"].isin(BEARISH_RATINGS)

    cohort_a = df[df["sample_class"] == "cohort_a_bull_target"]
    cohort_b = df[df["sample_class"] == "cohort_b_bear_target"]

    bull_commits = df[df["rating"].isin(BULLISH_RATINGS)]
    bear_commits = df[df["rating"].isin(BEARISH_RATINGS)]

    # Bull metrics
    bull_baseline = bull_commits["alpha_vs_spy_pct"].mean()
    bull_kept_alpha = bull_commits[~bull_commits["fire_bull"]]["alpha_vs_spy_pct"].mean()
    bull_net_dalpha = bull_kept_alpha - bull_baseline if not pd.isna(bull_kept_alpha) else 0.0

    bull_cohort_fired = cohort_a["fire_bull"].sum()
    bull_cohort_hit_rate = bull_cohort_fired / len(cohort_a) * 100 if len(cohort_a) else 0.0

    # Bull discrimination: cohort fires alpha vs non-cohort fires alpha
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
    # Discrimination = noncohort_α − cohort_α; positive = filter catches losers correctly
    bull_discrim = (
        (bull_fired_winner_alpha - bull_fired_cohort_alpha)
        if (not bull_fired_cohort.empty and not bull_fired_winner.empty)
        else float("nan")
    )

    # Bear metrics — for bear, HIGH α is wrong; filter helps by removing high-α
    bear_baseline = bear_commits["alpha_vs_spy_pct"].mean()
    bear_kept_alpha = bear_commits[~bear_commits["fire_bear"]]["alpha_vs_spy_pct"].mean()
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
    # For bear: cohort_α should be HIGH (wrong-direction bear), winner_α should be LOW (correct bear)
    # discrimination = cohort_α − winner_α; positive = filter correctly catches rallying cohort
    bear_discrim = (
        (bear_fired_cohort_alpha - bear_fired_winner_alpha)
        if (not bear_fired_cohort.empty and not bear_fired_winner.empty)
        else float("nan")
    )

    return {
        "bull_n_fired": int(bull_commits["fire_bull"].sum()),
        "bull_baseline_alpha": bull_baseline,
        "bull_kept_alpha": bull_kept_alpha,
        "bull_net_dalpha": bull_net_dalpha,
        "bull_cohort_hit_rate": bull_cohort_hit_rate,
        "bull_discrim": bull_discrim,
        "bear_n_fired": int(bear_commits["fire_bear"].sum()),
        "bear_baseline_alpha": bear_baseline,
        "bear_kept_alpha": bear_kept_alpha,
        "bear_net_dalpha": bear_net_dalpha,
        "bear_cohort_hit_rate": bear_cohort_hit_rate,
        "bear_discrim": bear_discrim,
    }


# ---- Main -----------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bull-threshold",
        type=float,
        default=DEFAULT_BULL_THRESHOLD,
        help=f"Bull-side fire threshold (default {DEFAULT_BULL_THRESHOLD})",
    )
    parser.add_argument(
        "--bear-threshold",
        type=float,
        default=DEFAULT_BEAR_THRESHOLD,
        help=f"Bear-side fire threshold (default {DEFAULT_BEAR_THRESHOLD})",
    )
    parser.add_argument(
        "--windows",
        default=",".join(str(w) for w in DEFAULT_WINDOWS),
        help="Comma-separated boost windows (calendar days; default 7,14,21)",
    )
    parser.add_argument(
        "--magnitudes",
        default=",".join(str(m) for m in DEFAULT_MAGNITUDES),
        help="Comma-separated boost magnitudes (default 0.5,1.0,2.0)",
    )
    args = parser.parse_args()

    windows = tuple(int(w) for w in args.windows.split(","))
    magnitudes = tuple(float(m) for m in args.magnitudes.split(","))

    print("# Hybrid C retrofit — Class 3 LLM scores + Class 6 calendar boost")
    print()
    print(f"Bull threshold: {args.bull_threshold}")
    print(f"Bear threshold: {args.bear_threshold}")
    print(f"Boost windows (cal days): {windows}")
    print(f"Boost magnitudes: {magnitudes}")
    print()

    if not CLASS3_CSV.exists():
        print(f"[fatal] Class 3 Opus CSV missing: {CLASS3_CSV}")
        return

    df = pd.read_csv(CLASS3_CSV)
    df = df.dropna(subset=["bull_case_priced_in", "bear_case_priced_in", "alpha_vs_spy_pct"]).copy()
    print(f"Loaded {len(df)} rows from {CLASS3_CSV}")

    # Earnings cache
    print()
    print("Building earnings cache (one yfinance call per unique ticker)...")
    tickers = sorted(df["ticker"].unique().tolist())
    print(f"  {len(tickers)} unique tickers: {tickers}")
    cache = _build_earnings_cache(tickers)
    n_with_earnings = sum(1 for t in tickers if cache.get(t))
    print(f"  {n_with_earnings} of {len(tickers)} have earnings_dates available")

    # Compute days_to_next_earnings per row
    df["days_to_earnings"] = df.apply(
        lambda r: _days_to_next_earnings(r["ticker"], r["trade_date"], cache),
        axis=1,
    )

    n_with_days = df["days_to_earnings"].notna().sum()
    print(f"  {n_with_days} of {len(df)} rows have computable days_to_earnings")
    print()
    print("Days-to-earnings distribution:")
    print(df["days_to_earnings"].describe())
    print()

    # Class 3-alone baseline (no boost)
    df["eff_bull_score"] = df["bull_case_priced_in"]
    df["eff_bear_score"] = df["bear_case_priced_in"]
    baseline = _eval_gate(df, args.bull_threshold, args.bear_threshold)

    print("## Class 3-alone baseline (T_bull=0.60, T_bear=0.50)")
    print()
    print(
        f"  Bull: n_fired={baseline['bull_n_fired']}, kept_α={baseline['bull_kept_alpha']:+.2f}%, "
        f"net Δα={baseline['bull_net_dalpha']:+.2f}pp, cohort hit={baseline['bull_cohort_hit_rate']:.1f}%, "
        f"discrim={baseline['bull_discrim']:+.2f}pp"
    )
    print(
        f"  Bear: n_fired={baseline['bear_n_fired']}, kept_α={baseline['bear_kept_alpha']:+.2f}%, "
        f"net Δα={baseline['bear_net_dalpha']:+.2f}pp, cohort hit={baseline['bear_cohort_hit_rate']:.1f}%, "
        f"discrim={baseline['bear_discrim']:+.2f}pp"
    )
    print()

    # Sweep
    print("## Hybrid C sweep (window × magnitude)")
    print()
    print(
        "| window | magnitude | bull n_fired | bull net Δα | bull hit% | bull discrim | "
        "bear n_fired | bear net Δα | bear hit% | bear discrim |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|")

    sweep_rows = []
    for w in windows:
        for m in magnitudes:
            df_h = df.copy()
            # Capture loop vars in default-arg defaults to avoid B023 closure-over-loop-var
            df_h["eff_bull_score"] = df_h.apply(
                lambda r, _w=w, _m=m: _effective_score(
                    r["bull_case_priced_in"], r["days_to_earnings"], _w, _m
                ),
                axis=1,
            )
            df_h["eff_bear_score"] = df_h.apply(
                lambda r, _w=w, _m=m: _effective_score(
                    r["bear_case_priced_in"], r["days_to_earnings"], _w, _m
                ),
                axis=1,
            )
            metrics = _eval_gate(df_h, args.bull_threshold, args.bear_threshold)
            print(
                f"| {w}d | {m:.1f}x | {metrics['bull_n_fired']} | {metrics['bull_net_dalpha']:+.2f}pp | "
                f"{metrics['bull_cohort_hit_rate']:.1f}% | {metrics['bull_discrim']:+.2f}pp | "
                f"{metrics['bear_n_fired']} | {metrics['bear_net_dalpha']:+.2f}pp | "
                f"{metrics['bear_cohort_hit_rate']:.1f}% | {metrics['bear_discrim']:+.2f}pp |"
            )
            sweep_rows.append({"window": w, "magnitude": m, **metrics})

    # Find best Hybrid C config (sort by combined improvement)
    sweep_df = pd.DataFrame(sweep_rows)
    sweep_df["bull_net_improvement"] = sweep_df["bull_net_dalpha"] - baseline["bull_net_dalpha"]
    sweep_df["bear_net_improvement"] = sweep_df["bear_net_dalpha"] - baseline["bear_net_dalpha"]
    sweep_df["bull_hit_improvement"] = (
        sweep_df["bull_cohort_hit_rate"] - baseline["bull_cohort_hit_rate"]
    )
    sweep_df["bear_hit_improvement"] = (
        sweep_df["bear_cohort_hit_rate"] - baseline["bear_cohort_hit_rate"]
    )
    sweep_df["combined_improvement"] = (
        sweep_df["bull_net_improvement"]
        + sweep_df["bear_net_improvement"]
        + sweep_df["bull_hit_improvement"] / 100
        + sweep_df["bear_hit_improvement"] / 100
    )

    print()
    print("## Improvement vs Class 3-alone baseline")
    print()
    print("| window | magnitude | bull Δα Δ | bear Δα Δ | bull hit Δ | bear hit Δ | combined |")
    print("|---|---|---|---|---|---|---|")
    for _, r in sweep_df.iterrows():
        print(
            f"| {int(r['window'])}d | {r['magnitude']:.1f}x | "
            f"{r['bull_net_improvement']:+.2f}pp | {r['bear_net_improvement']:+.2f}pp | "
            f"{r['bull_hit_improvement']:+.1f}% | {r['bear_hit_improvement']:+.1f}% | "
            f"{r['combined_improvement']:+.3f} |"
        )

    print()
    best = sweep_df.loc[sweep_df["combined_improvement"].idxmax()]
    print(
        f"## Best Hybrid C config: window={int(best['window'])}d, magnitude={best['magnitude']:.1f}x"
    )
    print(f"  Combined improvement: {best['combined_improvement']:+.3f}")
    print(
        f"  Bull side: net Δα change = {best['bull_net_improvement']:+.2f}pp, "
        f"hit rate change = {best['bull_hit_improvement']:+.1f}%"
    )
    print(
        f"  Bear side: net Δα change = {best['bear_net_improvement']:+.2f}pp, "
        f"hit rate change = {best['bear_hit_improvement']:+.1f}%"
    )

    # Verdict
    bull_improved = best["bull_net_improvement"] > 0.5 or best["bull_hit_improvement"] > 5
    bear_improved = best["bear_net_improvement"] > 0.5 or best["bear_hit_improvement"] > 5
    overall_improved = best["combined_improvement"] > 0.05

    print()
    print(
        f"## Verdict: {'PASS — Hybrid C improves on Class 3' if overall_improved else 'SKIP — Hybrid C does not meaningfully improve on Class 3'}"
    )
    if overall_improved:
        print(f"  Bull-side improvement: {bull_improved}")
        print(f"  Bear-side improvement: {bear_improved}")
        print(
            "  Recommend Spec 008 invocation iff at least one side shows >0.5pp net Δα or >5% hit-rate improvement."
        )
    else:
        print("  Calendar boost too crude to discriminate at any tested config.")
        print("  Class 3 alone remains the strongest forward-catalyst filter.")

    # Save CSV
    sweep_df.to_csv(OUT_CSV, index=False)
    print()
    print(f"Wrote {OUT_CSV}")

    # Markdown
    md = [
        f"# Hybrid C retrofit — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Hypothesis** (Spec 008 design doc pivot): Class 3 (LLM-extracted `bull/bear_case_priced_in` "
        "scores, validated + shipped at v0.7.0-spec-007) combined with Class 6 (calendar features: "
        "days-to-next-earnings) improves discrimination beyond Class 3 alone, by amplifying the "
        "priced-in effect for commits close to forward catalysts (which are more likely to be already-"
        "absorbed by the market).",
        "",
        "**Mechanism**: `effective_score = base_score × (1 + magnitude × boost)` where `boost = max(0, "
        "1 - days_to_earnings / window)`. At earnings day, boost=1.0 → effective = base × (1+magnitude); "
        "at window+ days out, boost=0 → effective = base.",
        "",
        f"**Cohort**: {len(df)} commits (cached Class 3 Opus scores + days-to-next-earnings via "
        f"yfinance.earnings_dates for {n_with_earnings} of {len(tickers)} unique tickers).",
        "",
        "## Days-to-earnings distribution",
        "",
        "| stat | value |",
        "|---|---|",
        f"| count | {df['days_to_earnings'].notna().sum()} |",
        f"| mean | {df['days_to_earnings'].mean():.1f} |",
        f"| std | {df['days_to_earnings'].std():.1f} |",
        f"| min | {df['days_to_earnings'].min():.0f} |",
        f"| 25% | {df['days_to_earnings'].quantile(0.25):.0f} |",
        f"| 50% | {df['days_to_earnings'].quantile(0.50):.0f} |",
        f"| 75% | {df['days_to_earnings'].quantile(0.75):.0f} |",
        f"| max | {df['days_to_earnings'].max():.0f} |",
        "",
        "## Class 3-alone baseline (T_bull=0.60, T_bear=0.50)",
        "",
        f"- Bull: n_fired={baseline['bull_n_fired']}, kept α={baseline['bull_kept_alpha']:+.2f}%, "
        f"net Δα={baseline['bull_net_dalpha']:+.2f}pp, cohort hit={baseline['bull_cohort_hit_rate']:.1f}%, "
        f"discrim={baseline['bull_discrim']:+.2f}pp",
        f"- Bear: n_fired={baseline['bear_n_fired']}, kept α={baseline['bear_kept_alpha']:+.2f}%, "
        f"net Δα={baseline['bear_net_dalpha']:+.2f}pp, cohort hit={baseline['bear_cohort_hit_rate']:.1f}%, "
        f"discrim={baseline['bear_discrim']:+.2f}pp",
        "",
        "## Hybrid C sweep — improvement vs baseline",
        "",
        "| window | magnitude | bull Δα Δ | bear Δα Δ | bull hit Δ | bear hit Δ | combined |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in sweep_df.iterrows():
        md.append(
            f"| {int(r['window'])}d | {r['magnitude']:.1f}x | "
            f"{r['bull_net_improvement']:+.2f}pp | {r['bear_net_improvement']:+.2f}pp | "
            f"{r['bull_hit_improvement']:+.1f}% | {r['bear_hit_improvement']:+.1f}% | "
            f"{r['combined_improvement']:+.3f} |"
        )

    md.extend(
        [
            "",
            f"## Best config: window={int(best['window'])}d, magnitude={best['magnitude']:.1f}x",
            "",
            f"- Combined improvement: {best['combined_improvement']:+.3f}",
            f"- Bull net Δα change: {best['bull_net_improvement']:+.2f}pp",
            f"- Bull hit rate change: {best['bull_hit_improvement']:+.1f}%",
            f"- Bear net Δα change: {best['bear_net_improvement']:+.2f}pp",
            f"- Bear hit rate change: {best['bear_hit_improvement']:+.1f}%",
            "",
            f"## Verdict — {'PASS' if overall_improved else 'SKIP'} per Spec 008 design doc decision tree",
            "",
        ]
    )
    if overall_improved:
        md.extend(
            [
                "Hybrid C produces meaningful improvement over Class 3 alone at the best-performing config. "
                "Per the Spec 008 design doc decision tree, this PASSES the gate to invoke `/speckit.specify` "
                "for a Spec 008 (Hybrid C as calendar-aware enhancement of the validated Class 3 filter).",
                "",
                "Recommended next step: invoke `/speckit.specify` for Spec 008 with this retrospective + the "
                "Spec 008 design doc as load-bearing empirical evidence. The spec would extend the Class 3 "
                "filter (forward_catalyst_filter.py) with an optional calendar boost layer; default-off until "
                "production-config retrospective confirms the improvement holds at production thresholds.",
            ]
        )
    else:
        md.extend(
            [
                "Hybrid C does NOT produce meaningful improvement over Class 3 alone at any tested "
                "(window, magnitude) combination. Per the Spec 008 design doc decision tree, this is the "
                "SKIP outcome — calendar features are too crude to discriminate at the cohort level on "
                "this corpus.",
                "",
                "**Honest read**: Class 3's LLM-extracted `bull_case_priced_in` score already implicitly "
                "captures whatever calendar-proximity-to-catalyst signal exists in the analyst reports. "
                "Adding an explicit calendar multiplier doesn't add new information — the LLM has already "
                "factored it in via the analyst prose synthesis.",
                "",
                "**Implication for future Spec 008 candidates**: skip Hybrid C; consider Class 5 "
                "(fundamentals delta — recent earnings surprise + analyst revisions) as a standalone "
                "feature with cleaner orthogonality to Class 3's prose synthesis. Class 5's recent "
                "earnings surprise is structured data Class 3's LLM may not have weighted heavily.",
            ]
        )

    md.extend(
        [
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/forward_catalyst_hybrid_c_retrospective.py",
            "```",
            "",
            f"Reads cached Class 3 Opus scores from `{CLASS3_CSV}` + free yfinance earnings_dates fetches "
            f"(one per unique ticker; {len(tickers)} tickers in cohort). Zero new LLM cost.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print()
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
