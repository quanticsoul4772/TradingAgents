"""Cross-cohort behavioral-additive sweep.

L-8 pattern definition (per memory/reference_behavioral_additive_4th_interpretation.md):
A row is BEHAVIORAL-ADDITIVE if a filter F WOULD have fired (its
pre-conditions and score thresholds are met) but the PM independently
arrived at the same suppressed rating without the filter actually firing,
because pre_rating ≠ Buy/Overweight (for bull-side) or pre_rating ≠
Underweight/Sell (for bear-side).

We're hunting for the 3rd mechanism class to support eventual Constitution
v1.4.4 codification. Current evidence:
- Spec 003 prose-density mechanism: 4 NVDA/MSFT/AAPL cases (2026-05-07 morning)
- Spec 007 LLM-extracted mechanism: 1 COP-04-24 case (2026-05-07 mid-flight)

This sweep walks every state log under ~/.tradingagents/logs/<TICKER>/
and counts:

1. Spec 003 behavioral-additive: contrarian_gate.percentile >= threshold
   (FR-004 cohort) but pre_rating not in {Buy, Overweight}
2. Spec 007 behavioral-additive: forward_catalyst.bull_case_priced_in >
   T_bull but pre_rating not in {Buy, Overweight}
3. Spec 007 bear-side behavioral-additive: forward_catalyst.bear_case_priced_in
   > T_bear but pre_rating not in {Underweight, Sell}
4. Spec 008 behavioral-additive: effective_bull_score > T_bull but
   pre_rating not in {Buy, Overweight} (subset of #2 with calendar boost
   activating the score)

Output: per-mechanism counts + per-ticker breakdown + sample identification
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

LOG_BASE = Path(os.environ["USERPROFILE"]) / ".tradingagents/logs"

T_BULL = 0.60
T_BEAR = 0.50
SPEC_003_PERCENTILE_FR_004 = 80.0  # FR-004 threshold

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}


def _extract_pm_rating(state: dict) -> str | None:
    """Extract canonical PM rating from final_trade_decision markdown.

    Match the regex pattern that signal_processing.py uses
    (deterministic 5-tier extraction).
    """
    final = state.get("final_trade_decision", "") or ""
    if not final:
        return None
    import re

    m = re.search(r"\*\*Rating\*\*:\s*(Buy|Overweight|Hold|Underweight|Sell)\b", final)
    return m.group(1) if m else None


def sweep_log(log_path: Path) -> dict:
    """Inspect one state log JSON. Returns flags + extracted scores."""
    try:
        d = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"path": str(log_path), "error": f"{type(e).__name__}: {e}"}

    pm_rating = _extract_pm_rating(d)

    out = {
        "path": str(log_path),
        "pm_rating": pm_rating,
    }

    # Spec 003
    cg = d.get("contrarian_gate") or {}
    out["spec_003_percentile"] = cg.get("percentile")
    out["spec_003_baseline"] = cg.get("gate_baseline")
    out["spec_003_fired"] = cg.get("fired")
    out["spec_003_pre_rating"] = cg.get("pre_rating")

    # Spec 007 / 008
    fc = d.get("forward_catalyst") or {}
    out["spec_007_bull_score"] = fc.get("bull_case_priced_in")
    out["spec_007_bear_score"] = fc.get("bear_case_priced_in")
    out["spec_007_fired_bull"] = fc.get("fired_bull")
    out["spec_007_fired_bear"] = fc.get("fired_bear")
    out["spec_007_pre_rating"] = fc.get("pre_rating")
    out["spec_008_effective_bull"] = fc.get("effective_bull_score")
    out["spec_008_calendar_boost"] = fc.get("calendar_boost")

    # Behavioral-additive flags
    out["behav_add_spec_003"] = (
        out["spec_003_percentile"] is not None
        and float(out["spec_003_percentile"] or 0) >= SPEC_003_PERCENTILE_FR_004
        and out["spec_003_pre_rating"] not in BULLISH_RATINGS
    )
    out["behav_add_spec_007_bull"] = (
        out["spec_007_bull_score"] is not None
        and float(out["spec_007_bull_score"] or 0) > T_BULL
        and out["spec_007_pre_rating"] not in BULLISH_RATINGS
    )
    out["behav_add_spec_007_bear"] = (
        out["spec_007_bear_score"] is not None
        and float(out["spec_007_bear_score"] or 0) > T_BEAR
        and out["spec_007_pre_rating"] not in BEARISH_RATINGS
    )
    out["behav_add_spec_008"] = (
        out["spec_008_effective_bull"] is not None
        and float(out["spec_008_effective_bull"] or 0) > T_BULL
        and out["spec_007_pre_rating"] not in BULLISH_RATINGS
        and (out["spec_008_calendar_boost"] or 0) > 0  # boost actually engaged
    )

    return out


def main() -> int:
    print("# Cross-cohort behavioral-additive sweep — 2026-05-07\n")

    if not LOG_BASE.exists():
        print(f"ERROR: {LOG_BASE} does not exist")
        return 1

    rows = []
    n_logs = 0
    for ticker_dir in sorted(LOG_BASE.iterdir()):
        if not ticker_dir.is_dir():
            continue
        log_dir = ticker_dir / "TradingAgentsStrategy_logs"
        if not log_dir.exists():
            continue
        for log_file in sorted(log_dir.glob("full_states_log_*.json")):
            n_logs += 1
            r = sweep_log(log_file)
            r["ticker"] = ticker_dir.name
            rows.append(r)

    print(f"Total state logs scanned: {n_logs}\n")

    # Per-mechanism counts
    n_spec_003_aware = sum(1 for r in rows if r.get("spec_003_percentile") is not None)
    n_spec_007_aware = sum(1 for r in rows if r.get("spec_007_bull_score") is not None)
    n_spec_008_aware = sum(1 for r in rows if r.get("spec_008_effective_bull") is not None)

    print("## Mechanism-class instrumented coverage\n")
    print(
        f"- Spec 003 instrumented: {n_spec_003_aware}/{n_logs} ({n_spec_003_aware / n_logs * 100:.1f}%)"
    )
    print(
        f"- Spec 007 instrumented: {n_spec_007_aware}/{n_logs} ({n_spec_007_aware / n_logs * 100:.1f}%)"
    )
    print(
        f"- Spec 008 instrumented: {n_spec_008_aware}/{n_logs} ({n_spec_008_aware / n_logs * 100:.1f}%)"
    )
    print()

    # Behavioral-additive counts
    behav_add_003 = [r for r in rows if r.get("behav_add_spec_003")]
    behav_add_007_bull = [r for r in rows if r.get("behav_add_spec_007_bull")]
    behav_add_007_bear = [r for r in rows if r.get("behav_add_spec_007_bear")]
    behav_add_008 = [r for r in rows if r.get("behav_add_spec_008")]

    print("## Behavioral-additive case counts\n")
    print(f"- Spec 003 (prose-density): n = {len(behav_add_003)}")
    print(f"- Spec 007 bull (LLM-extracted): n = {len(behav_add_007_bull)}")
    print(f"- Spec 007 bear (LLM-extracted): n = {len(behav_add_007_bear)}")
    print(f"- Spec 008 (calendar-boosted): n = {len(behav_add_008)}")
    print()

    # Per-ticker × mechanism breakdown
    print("## Per-ticker × per-mechanism behavioral-additive cases\n")
    by_ticker_mech = defaultdict(lambda: defaultdict(int))
    for r in rows:
        t = r["ticker"]
        if r.get("behav_add_spec_003"):
            by_ticker_mech[t]["spec_003"] += 1
        if r.get("behav_add_spec_007_bull"):
            by_ticker_mech[t]["spec_007_bull"] += 1
        if r.get("behav_add_spec_007_bear"):
            by_ticker_mech[t]["spec_007_bear"] += 1
        if r.get("behav_add_spec_008"):
            by_ticker_mech[t]["spec_008"] += 1

    if by_ticker_mech:
        print("| Ticker | Spec 003 | Spec 007 bull | Spec 007 bear | Spec 008 |")
        print("|---|---|---|---|---|")
        for t in sorted(by_ticker_mech.keys()):
            d = by_ticker_mech[t]
            print(
                f"| {t} | {d.get('spec_003', 0)} | "
                f"{d.get('spec_007_bull', 0)} | "
                f"{d.get('spec_007_bear', 0)} | "
                f"{d.get('spec_008', 0)} |"
            )
        print()
    else:
        print("(no behavioral-additive cases found)\n")

    # Sample sightings
    print("## Sample behavioral-additive sightings\n")

    for label, sample in [
        ("Spec 003", behav_add_003),
        ("Spec 007 bull", behav_add_007_bull),
        ("Spec 007 bear", behav_add_007_bear),
        ("Spec 008", behav_add_008),
    ]:
        print(f"### {label} (n={len(sample)})")
        for r in sample[:5]:
            log_name = Path(r["path"]).stem.replace("full_states_log_", "")
            print(
                f"  - {r['ticker']}/{log_name}: "
                f"pm={r.get('pm_rating')}, "
                f"pre={r.get('spec_007_pre_rating') or r.get('spec_003_pre_rating')}, "
                f"spec_003_percentile={r.get('spec_003_percentile')}, "
                f"spec_007_bull={r.get('spec_007_bull_score')}, "
                f"spec_007_bear={r.get('spec_007_bear_score')}, "
                f"spec_008_eff_bull={r.get('spec_008_effective_bull')}"
            )
        if len(sample) > 5:
            print(f"  ...and {len(sample) - 5} more")
        print()

    # L-8 codification check
    print("## L-8 codification readiness check\n")
    mechanism_classes_with_evidence = sum(
        1
        for n in [
            len(behav_add_003),
            len(behav_add_007_bull),
            len(behav_add_007_bear),
            len(behav_add_008),
        ]
        if n > 0
    )
    print(
        f"Distinct mechanism classes with behavioral-additive evidence: {mechanism_classes_with_evidence}/4"
    )
    if mechanism_classes_with_evidence >= 3:
        print("→ MET the 3-mechanism-class threshold for v1.4.4 codification consideration.")
    else:
        print(
            "→ Below the 3-mechanism-class threshold. Continue accumulating evidence before codification."
        )
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
