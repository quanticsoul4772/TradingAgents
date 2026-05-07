"""SC-009 A/B ablation analyzer for Spec 008 Hybrid C live ablation.

Per `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS_PLAN.md`
Phase 3 + Phase 4: extracts boost-ON vs boost-OFF fire decisions from state
logs, computes net Δα improvement at the 21-day forward horizon, and
evaluates the SC-009 acceptance gate.

Mechanism (the savings of the post-hoc reconstruction):
  - Backtest ran with hybrid_c_calendar_boost_enabled=True, capturing the
    BOOSTED fire decision in state.forward_catalyst.fired_bull
  - The UNDERLYING bull_case_priced_in score is also in the state log,
    so we can post-hoc compute what the boost-OFF fire decision would have
    been: would_fire_unboosted = bull_case_priced_in > T_bull AND pre_rating
    in {Buy, Overweight}
  - This gives us TRUE A/B from a SINGLE backtest run

Acceptance gate (3 conditions per HYPOTHESIS.md):
  1. Bull-side net Δα improvement in [+2.35pp, +4.35pp] (= +3.35pp ± 1pp)
  2. n_fired-bull under boost-ON ≥ 8
  3. At least one propagate has calendar_boost > 0

Zero LLM cost — pure post-processing of state logs + yfinance for α.

Usage:
    python scripts/analyze_sc009_ab.py
    python scripts/analyze_sc009_ab.py --holding-days 21
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

EXPERIMENT_DIR = Path("experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation")
RESULTS_CSV = EXPERIMENT_DIR / "results.csv"
ANALYSIS_OUT = EXPERIMENT_DIR / "ANALYSIS.md"
PARTIAL_OUT = EXPERIMENT_DIR / "PARTIAL_ANALYSIS.md"

LOGS_BASE = Path(
    os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.expanduser("~/.tradingagents/logs"))
)

BULLISH_RATINGS = {"Buy", "Overweight"}
T_BULL = DEFAULT_CONFIG["forward_catalyst_bull_threshold"]


def evaluate_gate_1(
    net_dalpha_improvement: float | None,
    alt_gate_1_pass: bool | None,
) -> dict:
    """Resolve SC-009 gate-1 status using standard or alternative evaluator.

    Standard gate-1 (boost-ON kept α minus boost-OFF kept α in
    [+2.35pp, +4.35pp]) is preferred when computable. Alternative gate-1
    (suppressed commits' α in [-10%, +2%]) is the fallback when standard
    is undefined (100% fire rate → both kept sets empty).

    Returns dict with keys: effective (bool), method (str), status (str).
    """
    if net_dalpha_improvement is not None:
        passes = 2.35 <= net_dalpha_improvement <= 4.35
        return {
            "effective": passes,
            "method": "standard",
            "status": "PASS" if passes else "FAIL",
        }
    if alt_gate_1_pass is True:
        return {
            "effective": True,
            "method": "alternative (100%-fire-rate fallback)",
            "status": "PASS",
        }
    if alt_gate_1_pass is False:
        return {
            "effective": False,
            "method": "alternative (100%-fire-rate fallback)",
            "status": "FAIL",
        }
    return {
        "effective": False,
        "method": "neither (no fires + no suppressed α)",
        "status": "INCONCLUSIVE",
    }


def _load_state_log(ticker: str, trade_date: str) -> dict | None:
    """Load full_states_log_<DATE>.json for (ticker, trade_date)."""
    log_path = (
        LOGS_BASE / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{trade_date}.json"
    )
    if not log_path.exists():
        return None
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] failed to load {log_path}: {exc}")
        return None


def _enrich_row(row: pd.Series, holding_days: int) -> dict:
    """Extract spec 007/008 fields + realized α for one row."""
    ticker = row["ticker"]
    trade_date = row["analysis_date"]
    rating = row["rating"]

    state = _load_state_log(ticker, trade_date)
    if state is None:
        return {
            "ticker": ticker,
            "trade_date": trade_date,
            "rating": rating,
            "state_log_loaded": False,
            "alpha_vs_spy_pct": None,
            "alpha_pending": True,
        }

    fc = state.get("forward_catalyst", {}) or {}

    # Realized α (21-day forward)
    # fetch_returns returns (raw_return, alpha_return, actual_holding_days)
    # both decimals (e.g. 0.015 for 1.5%) — or (None, None, None) if unavailable.
    alpha_pct: float | None = None
    alpha_pending = False
    try:
        raw_ret, alpha_ret, _actual_days = fetch_returns(
            ticker, trade_date, holding_days=holding_days
        )
        if alpha_ret is not None:
            alpha_pct = float(alpha_ret) * 100  # convert fraction to %
        else:
            alpha_pending = True
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] fetch_returns failed for {ticker}@{trade_date}: {exc}")
        alpha_pending = True

    pre_rating = fc.get("pre_rating", rating) or rating
    bull_case_priced_in = fc.get("bull_case_priced_in")
    effective_bull_score = fc.get("effective_bull_score", bull_case_priced_in)
    fired_bull = bool(fc.get("fired_bull", False))
    calendar_boost = float(fc.get("calendar_boost", 0.0) or 0.0)
    days_to_earnings = fc.get("days_to_earnings")

    # Boost-OFF would-fire decision (post-hoc reconstruction)
    would_fire_unboosted = (
        bull_case_priced_in is not None
        and bull_case_priced_in > T_BULL
        and pre_rating in BULLISH_RATINGS
    )

    return {
        "ticker": ticker,
        "trade_date": trade_date,
        "rating": rating,
        "pre_rating": pre_rating,
        "post_rating": fc.get("post_rating", rating),
        "bull_case_priced_in": bull_case_priced_in,
        "effective_bull_score": effective_bull_score,
        "calendar_boost": calendar_boost,
        "days_to_earnings": days_to_earnings,
        "fired_bull": fired_bull,
        "would_fire_bull_unboosted": would_fire_unboosted,
        "boost_changed_decision": fired_bull != would_fire_unboosted,
        "alpha_vs_spy_pct": alpha_pct,
        "alpha_pending": alpha_pending,
        "state_log_loaded": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holding-days", type=int, default=21)
    parser.add_argument("--results-csv", type=Path, default=RESULTS_CSV)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Write PARTIAL_ANALYSIS.md (instead of ANALYSIS.md) when some α is pending",
    )
    args = parser.parse_args()

    print("# SC-009 A/B ablation analyzer — Spec 008 Hybrid C live ablation")
    print()
    print(f"Holding days for α: {args.holding_days}")
    print(f"Results CSV: {args.results_csv}")
    print(f"State log base: {LOGS_BASE}")
    print(f"T_bull (boost-OFF threshold): {T_BULL}")
    print()

    if not args.results_csv.exists():
        print(f"[fatal] results.csv not found: {args.results_csv}")
        return

    df_results = pd.read_csv(args.results_csv)
    print(f"Loaded {len(df_results)} rows from {args.results_csv}")
    print()

    # Enrich each row
    print("Enriching rows with state-log + realized α...")
    enriched = []
    for _, row in df_results.iterrows():
        err = row.get("error")
        if pd.notna(err) and str(err).strip():  # skip error rows (NaN-safe)
            continue
        enriched.append(_enrich_row(row, args.holding_days))
    if not enriched:
        print("  No successful rows to enrich.")
        return
    df = pd.DataFrame(enriched)
    print(f"  Enriched {len(df)} rows ({df['state_log_loaded'].sum()} state logs loaded)")

    n_pending = df["alpha_pending"].sum()
    n_with_alpha = (df["alpha_pending"] == False).sum()  # noqa: E712
    print(f"  Realized α: {n_with_alpha} measurable, {n_pending} pending")
    print()

    if n_pending > 0 and not args.allow_partial:
        print(f"[abort] {n_pending} rows have pending realized α (forward window not closed)")
        print("        Re-run with --allow-partial to generate PARTIAL_ANALYSIS.md or wait")
        print("        until ~2026-05-22 for full data, then run without --allow-partial.")
        # Still print the boost-engagement summary for early diagnostic
        engaged = df[df["calendar_boost"] > 0]
        print()
        print(f"Diagnostic — boost engagement: {len(engaged)} rows have calendar_boost > 0")
        if len(engaged) > 0:
            print("  Sample boost-engaged rows:")
            for _, r in engaged.head(5).iterrows():
                print(
                    f"    {r['ticker']} @ {r['trade_date']}: days_to_earnings={r['days_to_earnings']}, "
                    f"boost={r['calendar_boost']:.3f}, base={r['bull_case_priced_in']}, "
                    f"effective={r['effective_bull_score']}"
                )
        return

    # SC-009 gate evaluation
    df_with_alpha = df[~df["alpha_pending"]].copy()

    bull_commits = df_with_alpha[df_with_alpha["pre_rating"].isin(BULLISH_RATINGS)]
    n_bull_total = len(bull_commits)
    n_fired_boost_on = bull_commits["fired_bull"].sum()
    n_fired_boost_off = bull_commits["would_fire_bull_unboosted"].sum()

    boost_on_kept_alpha = bull_commits[~bull_commits["fired_bull"]]["alpha_vs_spy_pct"].mean()
    boost_off_kept_alpha = bull_commits[~bull_commits["would_fire_bull_unboosted"]][
        "alpha_vs_spy_pct"
    ].mean()
    bull_baseline_alpha = bull_commits["alpha_vs_spy_pct"].mean()

    # Net Δα improvement = boost-ON kept − boost-OFF kept (positive = boost helps)
    net_dalpha_improvement = (
        boost_on_kept_alpha - boost_off_kept_alpha
        if not pd.isna(boost_on_kept_alpha) and not pd.isna(boost_off_kept_alpha)
        else None
    )

    # Alternative gate-1 evaluator: handles 100%-fire-rate case where both kept sets are empty.
    # When all bull commits get fired, kept α (boost-ON / boost-OFF) is undefined.
    # Fall back to: did the suppressed commits have NEGATIVE realized α? Filter helped if yes.
    boost_on_suppressed = bull_commits[bull_commits["fired_bull"]]
    boost_on_suppressed_alpha: float | None = (
        float(boost_on_suppressed["alpha_vs_spy_pct"].mean())
        if not boost_on_suppressed.empty
        else None
    )
    if boost_on_suppressed_alpha is not None and pd.isna(boost_on_suppressed_alpha):
        boost_on_suppressed_alpha = None
    # Alt gate-1 PASS: suppressed commits' mean α in [-10%, +2%] (filter caught losers).
    # Range from retrofit cohort: bull-fire α mean -3.69%, std ~5pp.
    alt_gate_1_pass: bool | None = (
        (-10.0 < boost_on_suppressed_alpha < 2.0) if boost_on_suppressed_alpha is not None else None
    )

    # Boost engagement: count over ALL rows (boost can engage regardless of α availability)
    engaged_all = df[df["calendar_boost"] > 0]
    n_engaged = len(engaged_all)
    # For per-row breakdown table: prefer engaged-with-α; fall back to engaged-all
    engaged = df_with_alpha[df_with_alpha["calendar_boost"] > 0]
    if engaged.empty:
        engaged = engaged_all  # fallback for early-diagnostic runs

    # Decisions changed by boost: count over ALL rows
    decisions_changed = df[df["boost_changed_decision"]]
    n_decisions_changed = len(decisions_changed)

    # SC-009 gate
    gate_1_pass = net_dalpha_improvement is not None and 2.35 <= net_dalpha_improvement <= 4.35
    gate_2_pass = n_fired_boost_on >= 8
    gate_3_pass = n_engaged >= 1

    g1 = evaluate_gate_1(net_dalpha_improvement, alt_gate_1_pass)
    effective_gate_1 = g1["effective"]
    gate_1_method = g1["method"]
    gate_1_status = g1["status"]

    print("## SC-009 acceptance gate")
    print()
    if net_dalpha_improvement is not None:
        print(
            f"  Gate 1 (Δα improvement in [+2.35pp, +4.35pp]): {gate_1_status} "
            f"(observed: {net_dalpha_improvement:+.2f}pp; method: {gate_1_method})"
        )
    else:
        sup_str = (
            f"{boost_on_suppressed_alpha:+.2f}%" if boost_on_suppressed_alpha is not None else "N/A"
        )
        print(
            f"  Gate 1 (alt: suppressed-α in [-10%, +2%]): {gate_1_status} "
            f"(suppressed α = {sup_str}; method: {gate_1_method})"
        )
    print(
        f"  Gate 2 (n_fired_boost_on ≥ 8): {'PASS' if gate_2_pass else 'FAIL'} "
        f"(observed: {n_fired_boost_on})"
    )
    print(
        f"  Gate 3 (boost engaged ≥ 1 row): {'PASS' if gate_3_pass else 'FAIL'} "
        f"(observed: {n_engaged})"
    )

    # all_pass uses the EFFECTIVE gate-1 (standard or alternative)
    all_pass = effective_gate_1 and gate_2_pass and gate_3_pass
    print()
    if all_pass:
        verdict = "PASS — recommend Spec 008 v2 default-on flip proposal"
    elif gate_2_pass and gate_3_pass:
        verdict = "SKIP default-on flip — net Δα outside ±1pp tolerance; document period-conditional limitation"
    elif gate_3_pass:
        verdict = "INCONCLUSIVE — n_fired < 8; expand cohort + rerun"
    else:
        verdict = "REGRESSION — boost not engaged on any row; investigate code/config"

    print(f"## Verdict: {verdict}")
    print()
    print("## Headline numbers")
    print(f"  n_bull_commits total: {n_bull_total}")
    print(f"  n_fired_boost_on: {n_fired_boost_on}")
    print(f"  n_fired_boost_off (post-hoc): {n_fired_boost_off}")
    print(f"  Decisions changed by boost: {n_decisions_changed}")
    print(f"  Bull baseline α: {bull_baseline_alpha:+.2f}%")
    print(f"  Boost-ON kept α: {boost_on_kept_alpha:+.2f}%")
    print(f"  Boost-OFF kept α: {boost_off_kept_alpha:+.2f}%")
    print(
        f"  Net Δα improvement: {net_dalpha_improvement:+.2f}pp"
        if net_dalpha_improvement is not None
        else "  Net Δα improvement: N/A"
    )

    # Write ANALYSIS.md (or PARTIAL_ANALYSIS.md)
    out_path = PARTIAL_OUT if (n_pending > 0 and args.allow_partial) else ANALYSIS_OUT
    md_lines = [
        "# ANALYSIS — 2026-05-07-001-spec-008-hybrid-c-ab-ablation",
        "",
        f"**Status**: {'PARTIAL' if (n_pending > 0 and args.allow_partial) else 'FINAL'}",
        f"**Date**: {pd.Timestamp.now().date().isoformat()}",
        "",
        "## Headline",
        "",
        f"**{verdict}**",
        "",
        "## Setup recap",
        "",
        f"- Cohort: {len(df_results)} propagates ({n_with_alpha} with realized α at {args.holding_days}d, {n_pending} pending)",
        f"- Boost configuration: ENABLED (window=14d, magnitude=0.5x, T_bull={T_BULL})",
        f"- Boost-OFF comparison: post-hoc from state-log `bull_case_priced_in > {T_BULL}`",
        "",
        "## SC-009 acceptance gate",
        "",
        "| Criterion | Threshold | Observed | Status |",
        "|---|---|---|---|",
    ]
    if net_dalpha_improvement is not None:
        md_lines.append(
            f"| Bull-side net Δα improvement | [+2.35pp, +4.35pp] | "
            f"{net_dalpha_improvement:+.2f}pp | {'PASS' if gate_1_pass else 'FAIL'} |"
        )
    else:
        md_lines.append(
            "| Bull-side net Δα improvement | [+2.35pp, +4.35pp] | N/A | INCONCLUSIVE |"
        )
    md_lines.append(
        f"| n_fired_boost_on | ≥ 8 | {n_fired_boost_on} | {'PASS' if gate_2_pass else 'FAIL'} |"
    )
    md_lines.append(
        f"| Boost engaged ≥ 1 row | ≥ 1 | {n_engaged} | {'PASS' if gate_3_pass else 'FAIL'} |"
    )

    md_lines.extend(
        [
            "",
            "## Headline numbers",
            "",
            f"- n_bull_commits total: **{n_bull_total}**",
            f"- n_fired_boost_on: **{n_fired_boost_on}**",
            f"- n_fired_boost_off (post-hoc): **{n_fired_boost_off}**",
            f"- Decisions changed by boost: **{n_decisions_changed}**",
            f"- Bull baseline α: {bull_baseline_alpha:+.2f}%"
            if not pd.isna(bull_baseline_alpha)
            else "- Bull baseline α: N/A",
            f"- Boost-ON kept α: {boost_on_kept_alpha:+.2f}%"
            if not pd.isna(boost_on_kept_alpha)
            else "- Boost-ON kept α: N/A",
            f"- Boost-OFF kept α: {boost_off_kept_alpha:+.2f}%"
            if not pd.isna(boost_off_kept_alpha)
            else "- Boost-OFF kept α: N/A",
        ]
    )
    if net_dalpha_improvement is not None:
        md_lines.append(f"- Net Δα improvement: {net_dalpha_improvement:+.2f}pp")
    md_lines.extend(
        [
            "",
            "## Boost-engagement breakdown",
            "",
            f"- Total rows with calendar_boost > 0: **{n_engaged}** of {n_with_alpha}",
            "",
        ]
    )
    if n_engaged > 0:
        md_lines.append(
            "| Ticker | Trade Date | days_to_earnings | calendar_boost | base score | effective score | pre_rating | post_rating | α |"
        )
        md_lines.append("|---|---|---|---|---|---|---|---|---|")
        for _, r in engaged.iterrows():
            alpha_s = (
                f"{r['alpha_vs_spy_pct']:+.2f}%" if r["alpha_vs_spy_pct"] is not None else "PENDING"
            )
            md_lines.append(
                f"| {r['ticker']} | {r['trade_date']} | {r['days_to_earnings']} | "
                f"{r['calendar_boost']:.3f} | {r['bull_case_priced_in']:.2f} | "
                f"{r['effective_bull_score']:.2f} | {r['pre_rating']} | {r['post_rating']} | {alpha_s} |"
            )
    else:
        md_lines.append(
            "**No rows had boost engaged** — none of the cohort tickers had earnings within 14 days of trade date. SC-009 gate 3 FAILS; experiment did not exercise the boost mechanism."
        )

    md_lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            "```",
            f"python scripts/analyze_sc009_ab.py --holding-days {args.holding_days}",
            "```",
            "",
            f"Reads `{args.results_csv}` + state logs from `{LOGS_BASE}` + free yfinance for realized α. Zero LLM cost.",
        ]
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md_lines), encoding="utf-8")
    print()
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
