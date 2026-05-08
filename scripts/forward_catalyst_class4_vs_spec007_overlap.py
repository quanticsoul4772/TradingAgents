"""C-4 (institutional ownership delta) vs Spec 007 bear additive overlap analysis.

Per Constitution VIII v1.4.3 additive-to-existing-filter gate (REQUIRED
before C-4 spec invocation per PR #75 followup): a new bear-side filter
that PASSES the standalone gate must ALSO show:
  - Net Δα improvement ≥ +0.5pp for union vs best existing bear filter, OR
  - Cohort hit improvement ≥ +5pp for union, OR
  - FP rate improvement ≥ -10pp for intersection (intersection variant)

Existing bear-side filter: Spec 007 bear (currently shadow mode per
default config, so it doesn't actively suppress; but its would_fire_bear
field captures the decision).

This script computes the 2x2 overlap matrix on bearish commits in the
C-4-eligible cohort (state logs ≥ 2026-02-14, Q4 2025 13F era):

  | C-4 fires? \\ Spec 007 fires? | YES | NO |
  |---|---|---|
  | YES | both (intersection) | C-4 only |
  | NO  | Spec 007 only | neither |

Per cell: n, mean α, hit rate (suppression-aligned: positive α for
suppressed bearish = "we caught a bad bear thesis"). FP rate = bearish
commits with positive α that we DID NOT suppress (would-have missed
catching a bad bear).

Cost: $0 LLM. yfinance + state-log reads only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

LOG_BASE = Path(os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.expanduser("~/.tradingagents/logs")))

BEARISH_RATINGS = {"Underweight", "Sell"}

# Match C-4 retrospective cohort (PR #75)
COHORT_CUTOFF = date(2026, 2, 14)
T_BEAR = 0.50  # Spec 007 bear threshold per default config
# C-4 default cover-side threshold. Note: pctChange column from yfinance is
# a FRACTION (0.05 = 5%), so threshold here matches PR #75 default of 0.05.
T_OUTFLOW = 0.05


@lru_cache(maxsize=128)
def _fetch_institutional_rotation(ticker: str) -> float | None:
    try:
        import yfinance as yf

        ih = yf.Ticker(ticker).institutional_holders
        if ih is None or not hasattr(ih, "empty") or ih.empty:
            return None
        if "pctChange" not in ih.columns:
            return None
        top10 = ih.head(10)
        return float(top10["pctChange"].fillna(0).sum())
    except Exception:
        return None


def _walk_bearish_commits() -> list[dict]:
    """Walk state logs and yield bearish PM commits in cohort window."""
    out = []
    if not LOG_BASE.exists():
        return out
    rating_re = re.compile(r"\*\*Rating\*\*:\s*(Buy|Overweight|Hold|Underweight|Sell)\b")
    for ticker_dir in sorted(LOG_BASE.iterdir()):
        if not ticker_dir.is_dir():
            continue
        log_dir = ticker_dir / "TradingAgentsStrategy_logs"
        if not log_dir.exists():
            continue
        for log_file in sorted(log_dir.glob("full_states_log_*.json")):
            date_str = log_file.stem.replace("full_states_log_", "")
            try:
                propagate_dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if propagate_dt < COHORT_CUTOFF:
                continue
            try:
                d = json.loads(log_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            final = d.get("final_trade_decision", "") or ""
            m = rating_re.search(final)
            if not m or m.group(1) not in BEARISH_RATINGS:
                continue
            fc = d.get("forward_catalyst") or {}
            out.append(
                {
                    "ticker": ticker_dir.name,
                    "date": date_str,
                    "pm_rating": m.group(1),
                    "spec007_bear_score": fc.get("bear_case_priced_in"),
                    "spec007_would_fire_bear": bool(fc.get("would_fire_bear", False)),
                }
            )
    return out


def _enrich(rows: list[dict], holding_days: int) -> list[dict]:
    enriched = []
    for r in rows:
        try:
            _raw, alpha, _days = fetch_returns(r["ticker"], r["date"], holding_days=holding_days)
            if alpha is None:
                continue
            r["alpha_pct"] = float(alpha) * 100
            # C-4 fire decision (recompute from yfinance snapshot)
            rotation = _fetch_institutional_rotation(r["ticker"])
            r["c4_rotation"] = rotation
            r["c4_would_fire"] = rotation is not None and rotation < -T_OUTFLOW
            enriched.append(r)
        except Exception:
            continue
    return enriched


def _classify_overlap(rows: list[dict]) -> dict[str, list[dict]]:
    cells: dict[str, list[dict]] = {
        "both": [],
        "c4_only": [],
        "spec007_only": [],
        "neither": [],
    }
    for r in rows:
        c4 = r["c4_would_fire"]
        s7 = r["spec007_would_fire_bear"]
        if c4 and s7:
            cells["both"].append(r)
        elif c4:
            cells["c4_only"].append(r)
        elif s7:
            cells["spec007_only"].append(r)
        else:
            cells["neither"].append(r)
    return cells


def _stats(group: list[dict]) -> dict:
    if not group:
        return {"n": 0}
    alphas = [r["alpha_pct"] for r in group]
    mean_a = sum(alphas) / len(alphas)
    # For BEARISH commits: positive α = bear thesis was wrong = "good catch" if suppressed
    hits = sum(1 for a in alphas if a > 0)
    return {"n": len(group), "mean_alpha_pct": mean_a, "hit_rate_pct": hits / len(group) * 100}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holding-days", type=int, default=21)
    args = parser.parse_args()

    print("# C-4 vs Spec 007 bear additive overlap analysis (Constitution VIII v1.4.3)")
    print()
    print(f"Cohort: bearish commits with date ≥ {COHORT_CUTOFF}")
    print(
        f"C-4 fire condition: net institutional rotation < {-T_OUTFLOW} (fractional; = -{T_OUTFLOW * 100:.1f}%)"
    )
    print(f"Spec 007 fire condition: bear_case_priced_in > {T_BEAR}")
    print(f"Holding days: {args.holding_days}")
    print()

    print("Walking state logs for bearish commits...")
    bear_rows = _walk_bearish_commits()
    print(f"  {len(bear_rows)} bearish commits in cohort")

    print()
    print("Enriching with realized α + C-4 rotation values...")
    enriched = _enrich(bear_rows, args.holding_days)
    print(f"  {len(enriched)} enriched (α-measurable + rotation-resolvable)")
    print()

    cells = _classify_overlap(enriched)

    print("## 2×2 overlap matrix")
    print()
    print("| Cell | n | mean α | hit % (sup-aligned) |")
    print("|---|---|---|---|")
    for cell_name in ("both", "c4_only", "spec007_only", "neither"):
        s = _stats(cells[cell_name])
        if s["n"] > 0:
            print(
                f"| {cell_name} | {s['n']} | {s['mean_alpha_pct']:+.2f}% | "
                f"{s['hit_rate_pct']:.1f}% |"
            )
        else:
            print(f"| {cell_name} | 0 | — | — |")
    print()

    # Compute baselines + union
    spec007_alone = cells["both"] + cells["spec007_only"]
    c4_alone = cells["both"] + cells["c4_only"]
    union = cells["both"] + cells["c4_only"] + cells["spec007_only"]
    intersection = cells["both"]

    s_spec007 = _stats(spec007_alone)
    s_c4 = _stats(c4_alone)
    s_union = _stats(union)
    s_intersection = _stats(intersection)

    print("## Baseline + variant comparison")
    print()
    print("| Configuration | n | mean α | hit % |")
    print("|---|---|---|---|")
    for label, s in [
        ("Spec 007 bear alone", s_spec007),
        ("C-4 alone", s_c4),
        ("Union (C-4 OR Spec 007)", s_union),
        ("Intersection (C-4 AND Spec 007)", s_intersection),
    ]:
        if s["n"] > 0:
            print(
                f"| {label} | {s['n']} | {s['mean_alpha_pct']:+.2f}% | {s['hit_rate_pct']:.1f}% |"
            )
        else:
            print(f"| {label} | 0 | — | — |")
    print()

    # Constitution VIII v1.4.3 additive gate
    print("## Constitution VIII v1.4.3 additive gate evaluation")
    print()
    print("Compares UNION (best new + existing) vs BEST EXISTING (Spec 007 bear alone).")
    print("Spec invocation requires improvement on AT LEAST ONE of:")
    print("  - Net Δα ≥ +0.5pp")
    print("  - Cohort hit ≥ +5pp")
    print("  - FP rate ≥ -10pp (via INTERSECTION variant)")
    print()

    if s_spec007["n"] == 0:
        print("**SKIP — Spec 007 bear has zero fires in cohort; baseline undefined.**")
        return 0

    # Suppression Δα: for bearish suppression, positive α gain = beneficial suppression
    # → suppression net Δα ≈ mean α of suppressed cohort
    union_dalpha = s_union["mean_alpha_pct"]
    spec007_dalpha = s_spec007["mean_alpha_pct"]

    delta_dalpha_union = union_dalpha - spec007_dalpha
    delta_hit_union = s_union["hit_rate_pct"] - s_spec007["hit_rate_pct"]
    # FP rate: bearish commits with positive α that we DID suppress / total bearish
    # When INTERSECTING, FP rate goes DOWN if intersection has higher hit rate than union
    delta_fp_intersection = (
        s_intersection["hit_rate_pct"] - s_spec007["hit_rate_pct"]
        if s_intersection["n"] > 0
        else None
    )

    g_alpha = delta_dalpha_union >= 0.5
    g_hit = delta_hit_union >= 5.0
    g_fp = delta_fp_intersection is not None and delta_fp_intersection >= 10.0

    print(
        f"  Net Δα improvement (union vs Spec 007 alone): {delta_dalpha_union:+.2f}pp "
        f"({'PASS' if g_alpha else 'FAIL'}; gate ≥ +0.5pp)"
    )
    print(
        f"  Hit rate improvement (union vs Spec 007 alone): {delta_hit_union:+.2f}pp "
        f"({'PASS' if g_hit else 'FAIL'}; gate ≥ +5pp)"
    )
    if delta_fp_intersection is not None:
        print(
            f"  FP rate improvement (intersection vs Spec 007 alone): {delta_fp_intersection:+.2f}pp "
            f"({'PASS' if g_fp else 'FAIL'}; gate ≥ +10pp)"
        )
    print()

    overall_pass = g_alpha or g_hit or g_fp
    if overall_pass:
        print(
            "**VERDICT: ADDITIVE PASS** — C-4 adds incremental value vs Spec 007 alone. "
            "Spec invocation eligible (subject to remaining checklist items: "
            "sample-size confidence + time-window discipline)."
        )
    else:
        print(
            "**VERDICT: ADDITIVE FAIL** — C-4 does NOT add measurable value vs Spec 007 "
            "alone on any of the 3 v1.4.3 criteria. Per the gate, spec invocation should "
            "be SKIPPED. Document the redundancy."
        )
    print()
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
