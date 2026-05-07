"""Class 5 vs Spec 007 (Class 3) overlap analysis.

Critical pre-Spec-010 question: when Class 5 (surprise > T_surprise) fires on
the same set of bull commits that Spec 007 (bull_case_priced_in > T_bull) fires
on, the marginal value of Spec 010 is zero — Spec 007 already catches them.
When the fire sets are disjoint, Spec 010 catches a different cohort and adds
incremental coverage.

Compute:
  - Intersection set: commits fired by BOTH Class 5 + Spec 007
  - Class-5-only set: commits fired by Class 5 but NOT Spec 007
  - Spec-007-only set: commits fired by Spec 007 but NOT Class 5
  - Union set: commits fired by EITHER

Per side metrics on each set:
  - n
  - mean α
  - cohort hit count
  - control_winner false-positive count

Then evaluate Hybrid B (union fire decision) against Constitution VIII v1.4.0
gate. If union improves over BOTH the Class 3 baseline AND Class 5 baseline
on at least one criterion (discrim / hit / Δα), Spec 010 as Hybrid B is
justified. Otherwise the standalone Spec 007 dominates.

Zero LLM cost — pure post-processing.
"""

from __future__ import annotations

import sys
from datetime import datetime
from functools import cache
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402

CLASS3_CSV = Path("claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv")
OUT_MD = Path("claudedocs/forward-catalyst-class5-vs-class3-overlap-2026-05-06.md")
OUT_CSV = Path("claudedocs/forward-catalyst-class5-vs-class3-overlap-2026-05-06.csv")

BULLISH_RATINGS = {"Buy", "Overweight"}

T_BULL = DEFAULT_CONFIG["forward_catalyst_bull_threshold"]  # 0.60
T_SURPRISE = 0.02  # Class 5 best from forward-catalyst-class5-retrospective-2026-05-06.md


@cache
def _fetch_earnings_history(ticker: str) -> pd.DataFrame:
    try:
        eh = yf.Ticker(ticker).earnings_history
        if eh is None or eh.empty:
            return pd.DataFrame()
        return eh
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] {ticker}: {exc}")
        return pd.DataFrame()


def _most_recent_surprise(ticker: str, trade_date: str) -> float | None:
    eh = _fetch_earnings_history(ticker)
    if eh.empty:
        return None
    try:
        td = datetime.fromisoformat(trade_date).date()
    except (ValueError, AttributeError):
        return None
    eh_idx_dates = [d.date() if hasattr(d, "date") else d for d in eh.index]
    past = [(d, eh.iloc[i]) for i, d in enumerate(eh_idx_dates) if d < td]
    if not past:
        return None
    past.sort(key=lambda r: r[0], reverse=True)
    surprise = past[0][1].get("surprisePercent")
    if surprise is None or pd.isna(surprise):
        return None
    return float(surprise)


def _summarize_set(df_set: pd.DataFrame, label: str) -> dict:
    """Compute n / mean α / cohort hit / winner FP for a fire-decision subset."""
    n = len(df_set)
    if n == 0:
        return {"label": label, "n": 0, "mean_alpha": float("nan"), "cohort_n": 0, "winner_n": 0}
    cohort_n = (df_set["sample_class"] == "cohort_a_bull_target").sum()
    winner_n = (df_set["sample_class"] == "control_bull_winner").sum()
    return {
        "label": label,
        "n": int(n),
        "mean_alpha": df_set["alpha_vs_spy_pct"].mean(),
        "cohort_n": int(cohort_n),
        "winner_n": int(winner_n),
    }


def main():
    print("# Class 5 vs Spec 007 (Class 3) overlap analysis")
    print()
    print(f"Spec 007 threshold: bull_case_priced_in > {T_BULL}")
    print(f"Class 5 threshold:  surprise_pct > {T_SURPRISE}")
    print()

    df = pd.read_csv(CLASS3_CSV)
    df = df.dropna(subset=["bull_case_priced_in", "bear_case_priced_in", "alpha_vs_spy_pct"]).copy()
    print(f"Loaded {len(df)} rows from {CLASS3_CSV}")

    # Compute surprise feature
    print("\nFetching earnings_history per ticker...")
    df["surprise_pct"] = df.apply(
        lambda r: _most_recent_surprise(r["ticker"], r["trade_date"]),
        axis=1,
    )
    n_with_surprise = df["surprise_pct"].notna().sum()
    print(f"  {n_with_surprise} of {len(df)} rows have surprise data")

    # Restrict to bull commits with surprise data (fair comparison)
    df_bull = df[df["rating"].isin(BULLISH_RATINGS) & df["surprise_pct"].notna()].copy()
    print(f"\nBull commits with surprise data: {len(df_bull)}")
    print(
        f"  Cohort_a (bull losers):       {(df_bull['sample_class'] == 'cohort_a_bull_target').sum()}"
    )
    print(
        f"  Control_winner (bull winners): {(df_bull['sample_class'] == 'control_bull_winner').sum()}"
    )

    # Fire decisions
    df_bull["fire_class3"] = df_bull["bull_case_priced_in"] > T_BULL
    df_bull["fire_class5"] = df_bull["surprise_pct"] > T_SURPRISE
    df_bull["fire_either"] = df_bull["fire_class3"] | df_bull["fire_class5"]
    df_bull["fire_both"] = df_bull["fire_class3"] & df_bull["fire_class5"]
    df_bull["fire_class3_only"] = df_bull["fire_class3"] & ~df_bull["fire_class5"]
    df_bull["fire_class5_only"] = ~df_bull["fire_class3"] & df_bull["fire_class5"]
    df_bull["fire_neither"] = ~df_bull["fire_class3"] & ~df_bull["fire_class5"]

    print()
    print("## Fire decision overlap matrix (bull commits only)")
    print()
    print("|  | Class 3 fires | Class 3 silent | Total |")
    print("|---|---|---|---|")
    print(
        f"| Class 5 fires | **{df_bull['fire_both'].sum()}** | "
        f"{df_bull['fire_class5_only'].sum()} | {df_bull['fire_class5'].sum()} |"
    )
    print(
        f"| Class 5 silent | {df_bull['fire_class3_only'].sum()} | "
        f"**{df_bull['fire_neither'].sum()}** | {(~df_bull['fire_class5']).sum()} |"
    )
    print(
        f"| Total | {df_bull['fire_class3'].sum()} | "
        f"{(~df_bull['fire_class3']).sum()} | {len(df_bull)} |"
    )

    # Per-set summaries
    sets = [
        ("BOTH fire (intersection)", df_bull[df_bull["fire_both"]]),
        ("Class 5 ONLY", df_bull[df_bull["fire_class5_only"]]),
        ("Class 3 (Spec 007) ONLY", df_bull[df_bull["fire_class3_only"]]),
        ("EITHER fires (union)", df_bull[df_bull["fire_either"]]),
        ("NEITHER fires (kept commits)", df_bull[df_bull["fire_neither"]]),
        ("ALL bull commits (baseline)", df_bull),
    ]

    print()
    print("## Per-set α + cohort breakdown")
    print()
    print("| Set | n | mean α | cohort_a | control_winner |")
    print("|---|---|---|---|---|")
    summaries = []
    for label, dfs in sets:
        s = _summarize_set(dfs, label)
        summaries.append(s)
        alpha_str = f"{s['mean_alpha']:+.2f}%" if not pd.isna(s["mean_alpha"]) else "N/A"
        print(f"| {label} | {s['n']} | {alpha_str} | {s['cohort_n']} | {s['winner_n']} |")

    # Hybrid B (union) vs each underlying filter alone
    print()
    print("## Hybrid B (union fire) vs underlying filters")
    print()

    baseline_bull = df_bull["alpha_vs_spy_pct"].mean()

    def _net_dalpha(fire_col: str) -> float:
        kept = df_bull[~df_bull[fire_col]]["alpha_vs_spy_pct"].mean()
        if pd.isna(kept):
            return 0.0
        return kept - baseline_bull

    def _hit_rate(fire_col: str) -> float:
        cohort_a = df_bull[df_bull["sample_class"] == "cohort_a_bull_target"]
        if len(cohort_a) == 0:
            return 0.0
        return cohort_a[fire_col].sum() / len(cohort_a) * 100

    def _discrim(fire_col: str) -> float:
        fired = df_bull[df_bull[fire_col]]
        cohort_fired = fired[fired["sample_class"] == "cohort_a_bull_target"]["alpha_vs_spy_pct"]
        winner_fired = fired[fired["sample_class"] == "control_bull_winner"]["alpha_vs_spy_pct"]
        if cohort_fired.empty or winner_fired.empty:
            return float("nan")
        return winner_fired.mean() - cohort_fired.mean()

    rows = []
    for label, fire_col in [
        ("Spec 007 alone (Class 3 @ 0.60)", "fire_class3"),
        ("Class 5 alone (surprise @ 0.02)", "fire_class5"),
        ("Hybrid B union (Class 3 OR Class 5)", "fire_either"),
        ("Hybrid B intersection (Class 3 AND Class 5)", "fire_both"),
    ]:
        n_fired = df_bull[fire_col].sum()
        net_dalpha = _net_dalpha(fire_col)
        hit_rate = _hit_rate(fire_col)
        discrim = _discrim(fire_col)
        rows.append(
            {
                "filter": label,
                "n_fired": int(n_fired),
                "net_dalpha_pp": net_dalpha,
                "cohort_hit_pct": hit_rate,
                "discrim_pp": discrim,
            }
        )

    print("| Filter | n_fired | net Δα | cohort hit% | discrim |")
    print("|---|---|---|---|---|")
    for r in rows:
        discrim_str = f"{r['discrim_pp']:+.2f}pp" if not pd.isna(r["discrim_pp"]) else "N/A"
        print(
            f"| {r['filter']} | {r['n_fired']} | {r['net_dalpha_pp']:+.2f}pp | "
            f"{r['cohort_hit_pct']:.1f}% | {discrim_str} |"
        )

    # Decision
    union_row = next(r for r in rows if "union" in r["filter"])
    spec007_row = next(r for r in rows if "Spec 007 alone" in r["filter"])
    class5_row = next(r for r in rows if "Class 5 alone" in r["filter"])

    print()
    print("## Marginal-value analysis")
    print()
    print(
        f"Spec 007 alone:    net Δα = {spec007_row['net_dalpha_pp']:+.2f}pp, "
        f"hit = {spec007_row['cohort_hit_pct']:.1f}%, discrim = {spec007_row['discrim_pp']:+.2f}pp"
    )
    print(
        f"Class 5 alone:     net Δα = {class5_row['net_dalpha_pp']:+.2f}pp, "
        f"hit = {class5_row['cohort_hit_pct']:.1f}%, discrim = {class5_row['discrim_pp']:+.2f}pp"
    )
    print(
        f"Hybrid B (union):  net Δα = {union_row['net_dalpha_pp']:+.2f}pp, "
        f"hit = {union_row['cohort_hit_pct']:.1f}%, discrim = {union_row['discrim_pp']:+.2f}pp"
    )
    print()

    union_vs_spec007 = union_row["net_dalpha_pp"] - spec007_row["net_dalpha_pp"]
    union_vs_class5 = union_row["net_dalpha_pp"] - class5_row["net_dalpha_pp"]
    union_hit_vs_spec007 = union_row["cohort_hit_pct"] - spec007_row["cohort_hit_pct"]
    union_hit_vs_class5 = union_row["cohort_hit_pct"] - class5_row["cohort_hit_pct"]

    print(
        f"Union improvement vs Spec 007 alone: net Δα {union_vs_spec007:+.2f}pp, "
        f"hit {union_hit_vs_spec007:+.1f}%"
    )
    print(
        f"Union improvement vs Class 5 alone:  net Δα {union_vs_class5:+.2f}pp, "
        f"hit {union_hit_vs_class5:+.1f}%"
    )

    # Verdict
    print()
    print("## Verdict")
    if union_vs_spec007 > 0.5 and union_vs_class5 > 0.5:
        verdict = "PASS-Hybrid B — invoke Spec 010 as Hybrid B (union fire); improves over BOTH underlying filters by >0.5pp"
    elif union_vs_spec007 > 0.5:
        verdict = "PARTIAL — union improves over Spec 007 but not Class 5; consider Spec 010 as Class 5 standalone (Spec 007 redundant on this corpus)"
    elif union_vs_class5 > 0.5:
        verdict = "REDUNDANT — union improves over Class 5 but not Spec 007; Class 5 adds nothing on top of Spec 007. SKIP Spec 010 standalone; consider Hybrid B only if cohort hit improvement is operationally meaningful"
    else:
        verdict = "REDUNDANT — union does NOT improve over either underlying filter; Class 5 + Spec 007 are largely correlated. SKIP Spec 010 entirely; Spec 007 dominates"
    print(f"  {verdict}")

    # Also: which class catches more of cohort_a?
    cohort_a_bull = df_bull[df_bull["sample_class"] == "cohort_a_bull_target"]
    print()
    print("## Cohort_a (bull losers) catch breakdown")
    print(
        f"  Caught by Spec 007 only: {cohort_a_bull['fire_class3_only'].sum()} of {len(cohort_a_bull)}"
    )
    print(
        f"  Caught by Class 5 only:  {cohort_a_bull['fire_class5_only'].sum()} of {len(cohort_a_bull)}"
    )
    print(f"  Caught by BOTH:          {cohort_a_bull['fire_both'].sum()} of {len(cohort_a_bull)}")
    print(
        f"  Caught by EITHER:        {cohort_a_bull['fire_either'].sum()} of {len(cohort_a_bull)}"
    )
    print(
        f"  MISSED by both:          {cohort_a_bull['fire_neither'].sum()} of {len(cohort_a_bull)}"
    )

    # Save
    overlap_df = pd.DataFrame(rows)
    overlap_df.to_csv(OUT_CSV, index=False)
    print()
    print(f"Wrote {OUT_CSV}")

    md = [
        f"# Class 5 vs Spec 007 (Class 3) overlap analysis — {pd.Timestamp.now().date().isoformat()}",
        "",
        f"**Spec 007 threshold**: `bull_case_priced_in > {T_BULL}`",
        f"**Class 5 threshold**: `surprise_pct > {T_SURPRISE}` (best from Class 5 retrospective)",
        f"**Cohort**: {len(df_bull)} bull commits with computable surprise data.",
        "",
        "## Fire decision overlap matrix",
        "",
        "|  | Class 3 fires | Class 3 silent | Total |",
        "|---|---|---|---|",
        f"| Class 5 fires | **{df_bull['fire_both'].sum()}** | {df_bull['fire_class5_only'].sum()} | {df_bull['fire_class5'].sum()} |",
        f"| Class 5 silent | {df_bull['fire_class3_only'].sum()} | **{df_bull['fire_neither'].sum()}** | {(~df_bull['fire_class5']).sum()} |",
        f"| Total | {df_bull['fire_class3'].sum()} | {(~df_bull['fire_class3']).sum()} | {len(df_bull)} |",
        "",
        "## Per-set α + cohort breakdown",
        "",
        "| Set | n | mean α | cohort_a | control_winner |",
        "|---|---|---|---|---|",
    ]
    for s in summaries:
        alpha_str = f"{s['mean_alpha']:+.2f}%" if not pd.isna(s["mean_alpha"]) else "N/A"
        md.append(f"| {s['label']} | {s['n']} | {alpha_str} | {s['cohort_n']} | {s['winner_n']} |")

    md.extend(
        [
            "",
            "## Filter comparison",
            "",
            "| Filter | n_fired | net Δα | cohort hit% | discrim |",
            "|---|---|---|---|---|",
        ]
    )
    for r in rows:
        discrim_str = f"{r['discrim_pp']:+.2f}pp" if not pd.isna(r["discrim_pp"]) else "N/A"
        md.append(
            f"| {r['filter']} | {r['n_fired']} | {r['net_dalpha_pp']:+.2f}pp | "
            f"{r['cohort_hit_pct']:.1f}% | {discrim_str} |"
        )

    md.extend(
        [
            "",
            "## Marginal-value analysis",
            "",
            f"- **Union vs Spec 007 alone**: net Δα {union_vs_spec007:+.2f}pp, hit {union_hit_vs_spec007:+.1f}%",
            f"- **Union vs Class 5 alone**:  net Δα {union_vs_class5:+.2f}pp, hit {union_hit_vs_class5:+.1f}%",
            "",
            f"## Verdict — {verdict}",
            "",
            "## Cohort_a (bull losers) catch breakdown",
            "",
            f"- Caught by Spec 007 only: **{cohort_a_bull['fire_class3_only'].sum()}** of {len(cohort_a_bull)}",
            f"- Caught by Class 5 only:  **{cohort_a_bull['fire_class5_only'].sum()}** of {len(cohort_a_bull)}",
            f"- Caught by BOTH:          **{cohort_a_bull['fire_both'].sum()}** of {len(cohort_a_bull)}",
            f"- Caught by EITHER:        **{cohort_a_bull['fire_either'].sum()}** of {len(cohort_a_bull)}",
            f"- MISSED by both:          **{cohort_a_bull['fire_neither'].sum()}** of {len(cohort_a_bull)}",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/forward_catalyst_class5_vs_class3_overlap.py",
            "```",
            "",
            "Reads cached Class 3 Opus scores + free yfinance.earnings_history. Zero LLM cost.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
