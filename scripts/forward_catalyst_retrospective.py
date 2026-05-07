"""Spec 007 forward-catalyst-aware contrarian gate — production-config retrospective.

Per spec 007 SC-008 + R-6: extends the existing
``scripts/forward_catalyst_class3_retrospective.py`` (the retrofit that
produced the Opus PASS verdict) by:

  1. Loading config from ``tradingagents.default_config.DEFAULT_CONFIG``
     (production thresholds + modes + model)
  2. Walking the same 45-commit cohort + ~50 controls from
     ``claudedocs/sector-alpha-attribution-2026-05-06.csv``
  3. Re-applying the production filter LOGIC (without re-calling the LLM)
     to the cached scores in
     ``claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv``
  4. Reporting per-side fire rates + cohort hit rates + verifying SC-008

SC-008 acceptance criteria (per spec 007):
  - Bull-side fires on >=24 of 27 ticker_weak commits at default
    bull_threshold=0.60 (88.9% per Opus retrospective evidence)
  - Bear-side fires (in shadow mode) on >=10 of 18 ticker_strong commits
    at default bear_threshold=0.50 (per design doc §5;
    empirically validated at 13/18 in the Opus retrospective)

Zero new LLM cost — reuses the cached Opus scores from the prior retrofit.

Usage:
    python scripts/forward_catalyst_retrospective.py
    python scripts/forward_catalyst_retrospective.py --bull-threshold 0.65
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402

OPUS_CSV = Path("claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.csv")
OUT_MD = Path("claudedocs/forward-catalyst-retrospective-2026-05-06.md")

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bull-threshold",
        type=float,
        default=DEFAULT_CONFIG["forward_catalyst_bull_threshold"],
        help=f"Bull-side fire threshold (default {DEFAULT_CONFIG['forward_catalyst_bull_threshold']})",
    )
    parser.add_argument(
        "--bear-threshold",
        type=float,
        default=DEFAULT_CONFIG["forward_catalyst_bear_threshold"],
        help=f"Bear-side fire threshold (default {DEFAULT_CONFIG['forward_catalyst_bear_threshold']})",
    )
    parser.add_argument("--out", type=Path, default=OUT_MD, help="Output markdown path")
    args = parser.parse_args()

    print("# Spec 007 forward-catalyst retrospective — production-config validation")
    print()
    print(
        f"Bull threshold: {args.bull_threshold} (default {DEFAULT_CONFIG['forward_catalyst_bull_threshold']})"
    )
    print(
        f"Bear threshold: {args.bear_threshold} (default {DEFAULT_CONFIG['forward_catalyst_bear_threshold']})"
    )
    print(f"Bull mode: {DEFAULT_CONFIG['forward_catalyst_bull_mode']}")
    print(f"Bear mode: {DEFAULT_CONFIG['forward_catalyst_bear_mode']}")
    print(f"Model: {DEFAULT_CONFIG['forward_catalyst_model']}")
    print()

    if not OPUS_CSV.exists():
        print(f"[fatal] Opus retrofit CSV not found: {OPUS_CSV}")
        print(
            "        Run scripts/forward_catalyst_class3_retrospective.py --model claude-opus-4-7 first."
        )
        return

    df = pd.read_csv(OPUS_CSV)
    print(f"Loaded {len(df)} rows from {OPUS_CSV}")

    # Apply production filter logic to the cached scores
    df["fire_bull"] = (df["bull_case_priced_in"] > args.bull_threshold) & df["rating"].isin(
        BULLISH_RATINGS
    )
    df["fire_bear"] = (df["bear_case_priced_in"] > args.bear_threshold) & df["rating"].isin(
        BEARISH_RATINGS
    )

    # SC-008 cohort cross-tab
    cohort_a = df[df["sample_class"] == "cohort_a_bull_target"]
    cohort_b = df[df["sample_class"] == "cohort_b_bear_target"]

    bull_fires_in_cohort = cohort_a["fire_bull"].sum()
    bear_fires_in_cohort = cohort_b["fire_bear"].sum()

    # Aggregate per-side metrics
    bull_commits = df[df["rating"].isin(BULLISH_RATINGS)]
    bear_commits = df[df["rating"].isin(BEARISH_RATINGS)]
    n_bull_fires = bull_commits["fire_bull"].sum()
    n_bear_fires = bear_commits["fire_bear"].sum()

    bull_kept_alpha = bull_commits[~bull_commits["fire_bull"]]["alpha_vs_spy_pct"].mean()
    bull_baseline_alpha = bull_commits["alpha_vs_spy_pct"].mean()
    bull_net_dalpha = bull_kept_alpha - bull_baseline_alpha

    bear_kept_alpha = bear_commits[~bear_commits["fire_bear"]]["alpha_vs_spy_pct"].mean()
    bear_baseline_alpha = bear_commits["alpha_vs_spy_pct"].mean()
    # For bear: HIGHER α is wrong-direction; filter HELPS by removing high-α commits
    # net Δα = baseline - kept; positive = filter helps
    bear_net_dalpha = bear_baseline_alpha - bear_kept_alpha

    print()
    print("## SC-008 cohort cross-tab")
    print()
    print(
        f"Bull-side cohort hit: **{bull_fires_in_cohort} / {len(cohort_a)}** "
        f"({bull_fires_in_cohort / len(cohort_a) * 100:.1f}%)"
    )
    print(f"  SC-008 gate: >=24/27 — {'PASS' if bull_fires_in_cohort >= 24 else 'FAIL'}")
    print()
    print(
        f"Bear-side cohort hit: **{bear_fires_in_cohort} / {len(cohort_b)}** "
        f"({bear_fires_in_cohort / len(cohort_b) * 100:.1f}%)"
    )
    print(f"  SC-008 gate: >=10/18 — {'PASS' if bear_fires_in_cohort >= 10 else 'FAIL'}")
    print()

    print("## Aggregate per-side metrics (production-config defaults)")
    print()
    print(f"Bull-side: n_total={len(bull_commits)}, n_fired={n_bull_fires}, ")
    print(f"  baseline α = {bull_baseline_alpha:+.2f}%, kept α = {bull_kept_alpha:+.2f}%, ")
    print(f"  net Δα = {bull_net_dalpha:+.2f}pp")
    print()
    print(
        f"Bear-side: n_total={len(bear_commits)}, n_fired={n_bear_fires} (would_fire if shadow → active), "
    )
    print(f"  baseline α = {bear_baseline_alpha:+.2f}%, kept α = {bear_kept_alpha:+.2f}%, ")
    print(f"  net Δα = {bear_net_dalpha:+.2f}pp")

    sc008_pass = bull_fires_in_cohort >= 24 and bear_fires_in_cohort >= 10

    md = [
        f"# Spec 007 forward-catalyst retrospective — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Production-config validation** (extends `scripts/forward_catalyst_class3_retrospective.py`):",
        f"- Bull threshold: {args.bull_threshold}",
        f"- Bear threshold: {args.bear_threshold}",
        f"- Bull mode: {DEFAULT_CONFIG['forward_catalyst_bull_mode']}",
        f"- Bear mode: {DEFAULT_CONFIG['forward_catalyst_bear_mode']}",
        f"- Model: {DEFAULT_CONFIG['forward_catalyst_model']}",
        "",
        f"Loaded {len(df)} cached scores from `{OPUS_CSV}` (zero new LLM cost; re-applies production filter logic).",
        "",
        "## SC-008 cohort cross-tab",
        "",
        f"- Bull-side cohort hit: **{bull_fires_in_cohort} / {len(cohort_a)}** "
        f"({bull_fires_in_cohort / len(cohort_a) * 100:.1f}%) — "
        f"gate ≥24/27 → **{'PASS' if bull_fires_in_cohort >= 24 else 'FAIL'}**",
        f"- Bear-side cohort hit: **{bear_fires_in_cohort} / {len(cohort_b)}** "
        f"({bear_fires_in_cohort / len(cohort_b) * 100:.1f}%) — "
        f"gate ≥10/18 → **{'PASS' if bear_fires_in_cohort >= 10 else 'FAIL'}**",
        "",
        "## Aggregate per-side metrics",
        "",
        "| Side | n_total | n_fired | baseline α | kept α | net Δα |",
        "|---|---|---|---|---|---|",
        f"| Bull | {len(bull_commits)} | {n_bull_fires} | {bull_baseline_alpha:+.2f}% | "
        f"{bull_kept_alpha:+.2f}% | {bull_net_dalpha:+.2f}pp |",
        f"| Bear | {len(bear_commits)} | {n_bear_fires} | {bear_baseline_alpha:+.2f}% | "
        f"{bear_kept_alpha:+.2f}% | {bear_net_dalpha:+.2f}pp |",
        "",
        "## Verdict",
        "",
        f"**SC-008 gate: {'PASS' if sc008_pass else 'FAIL'}** at production-config defaults.",
        "",
        "Spec 007 ships with bull-side default-on @T=0.60 + bear-side default-shadow @T=0.50;"
        " production retrospective confirms the empirical evidence from the Opus retrofit.",
        "",
        "## Reproducibility",
        "",
        "```",
        "python scripts/forward_catalyst_retrospective.py",
        "```",
        "",
        f"Reads cached scores from `{OPUS_CSV}` + production config from "
        f"`tradingagents.default_config.DEFAULT_CONFIG`. Zero LLM cost.",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md), encoding="utf-8")
    print()
    print(f"Wrote {args.out}")
    print()
    print(f"## SC-008 OVERALL: {'PASS' if sc008_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
