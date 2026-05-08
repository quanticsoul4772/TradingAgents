"""v1.4.4 ratification counter-evidence watch.

Scans all state logs under ~/.tradingagents/logs/<TICKER>/ for any rows
that would REFUTE the multi-mechanism-validator framing of the proposed
Constitution v1.4.4 amendment (per
`claudedocs/constitution-v1.4.4-draft-2026-05-07.md`).

A refuting row is one where PM committed bullishly (Buy or Overweight)
DESPITE strong contrarian-bull-priced-in signals. Specifically, ANY of:

1. PM rating in {Buy, Overweight} AND spec_007 bull_score >= 0.80
2. PM rating in {Buy, Overweight} AND spec_007 bear_score >= 0.60
3. PM rating in {Buy, Overweight} AND spec_003 percentile >= 95

Such a row would contradict the framing: "PM internalizes multi-mechanism
contrarian logic via Constitution VII Calibrated Abstention training."
If found, the v1.4.4 ratification framing must be revised before
ratification.

This script is the operational gate for tomorrow's ratification check.
Run before ratifying; ratification is BLOCKED if counter-evidence count
> 0.

Usage:
    python scripts/v1_4_4_counter_evidence_watch.py
    python scripts/v1_4_4_counter_evidence_watch.py --strict   # also flags PM=Hold counter-evidence
    python scripts/v1_4_4_counter_evidence_watch.py --json      # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

LOG_BASE = Path(os.environ.get("USERPROFILE") or os.environ["HOME"]) / ".tradingagents/logs"

T_BULL_SCORE_REFUTING = 0.80
T_BEAR_SCORE_REFUTING = 0.60
SPEC_003_PERCENTILE_REFUTING = 95.0

BULLISH_RATINGS = {"Buy", "Overweight"}


def _extract_pm_rating(state: dict) -> str | None:
    """Extract canonical PM rating from final_trade_decision markdown."""
    final = state.get("final_trade_decision", "") or ""
    if not final:
        return None
    m = re.search(r"\*\*Rating\*\*:\s*(Buy|Overweight|Hold|Underweight|Sell)\b", final)
    return m.group(1) if m else None


def check_log(log_path: Path) -> dict | None:
    """Check one state log. Returns dict if it's counter-evidence; None otherwise."""
    try:
        d = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "path": str(log_path),
            "error": f"{type(e).__name__}: {e}",
            "counter_evidence_type": "load_error",
        }

    pm_rating = _extract_pm_rating(d)
    if pm_rating not in BULLISH_RATINGS:
        return None

    fc = d.get("forward_catalyst") or {}
    cg = d.get("contrarian_gate") or {}

    bull_score = fc.get("bull_case_priced_in")
    bear_score = fc.get("bear_case_priced_in")
    percentile = cg.get("percentile")

    refutations = []
    if bull_score is not None and float(bull_score) >= T_BULL_SCORE_REFUTING:
        refutations.append(f"bull_score={bull_score:.2f} ≥ {T_BULL_SCORE_REFUTING:.2f}")
    if bear_score is not None and float(bear_score) >= T_BEAR_SCORE_REFUTING:
        refutations.append(f"bear_score={bear_score:.2f} ≥ {T_BEAR_SCORE_REFUTING:.2f}")
    if percentile is not None and float(percentile) >= SPEC_003_PERCENTILE_REFUTING:
        refutations.append(
            f"spec_003_percentile={percentile:.1f} ≥ {SPEC_003_PERCENTILE_REFUTING:.1f}"
        )

    if not refutations:
        return None

    return {
        "path": str(log_path),
        "pm_rating": pm_rating,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "spec_003_percentile": percentile,
        "refutations": refutations,
        "counter_evidence_type": "v1_4_4_refuting",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan state logs for v1.4.4 ratification counter-evidence."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only output if counter-evidence is found (silent on clean).",
    )
    args = parser.parse_args()

    if not LOG_BASE.exists():
        print(f"ERROR: {LOG_BASE} does not exist", file=sys.stderr)
        return 2

    n_logs = 0
    counter_evidence_rows: list[dict] = []
    errors: list[dict] = []

    for ticker_dir in sorted(LOG_BASE.iterdir()):
        if not ticker_dir.is_dir():
            continue
        log_dir = ticker_dir / "TradingAgentsStrategy_logs"
        if not log_dir.exists():
            continue
        for log_file in sorted(log_dir.glob("full_states_log_*.json")):
            n_logs += 1
            row = check_log(log_file)
            if row is None:
                continue
            row["ticker"] = ticker_dir.name
            row["log_file"] = log_file.name
            if row.get("counter_evidence_type") == "load_error":
                errors.append(row)
            else:
                counter_evidence_rows.append(row)

    result = {
        "scanned_logs": n_logs,
        "counter_evidence_count": len(counter_evidence_rows),
        "counter_evidence_rows": counter_evidence_rows,
        "load_errors": len(errors),
        "load_error_rows": errors,
        "thresholds": {
            "bull_score": T_BULL_SCORE_REFUTING,
            "bear_score": T_BEAR_SCORE_REFUTING,
            "spec_003_percentile": SPEC_003_PERCENTILE_REFUTING,
        },
        "ratification_blocked": len(counter_evidence_rows) > 0,
    }

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    elif args.quiet and len(counter_evidence_rows) == 0:
        pass  # silent on clean
    else:
        print("# v1.4.4 ratification counter-evidence watch")
        print()
        print(f"Scanned: {n_logs} state logs")
        print(f"Counter-evidence rows found: {len(counter_evidence_rows)}")
        print(f"Load errors: {len(errors)}")
        print()
        print("## Refuting thresholds")
        print(f"- bull_case_priced_in ≥ {T_BULL_SCORE_REFUTING:.2f} AND PM in {{Buy, Overweight}}")
        print(f"- bear_case_priced_in ≥ {T_BEAR_SCORE_REFUTING:.2f} AND PM in {{Buy, Overweight}}")
        print(
            f"- spec_003 percentile ≥ {SPEC_003_PERCENTILE_REFUTING:.1f} AND PM in {{Buy, Overweight}}"
        )
        print()
        if counter_evidence_rows:
            print("## ⚠ Counter-evidence rows")
            print()
            for r in counter_evidence_rows:
                print(f"- {r['ticker']}/{r['log_file']}: pm={r['pm_rating']}")
                for refutation in r["refutations"]:
                    print(f"    {refutation}")
            print()
            print("## VERDICT: v1.4.4 ratification BLOCKED")
            print()
            print("Counter-evidence found. Per the v1.4.4 draft decision matrix,")
            print("ratification requires zero refuting rows across the corpus.")
            print("Either:")
            print("  1. Investigate each counter-evidence row to determine whether")
            print("     the framing needs revision, OR")
            print("  2. Tighten the refuting thresholds (with empirical justification)")
            print("     and re-run.")
        else:
            print("## ✓ Counter-evidence count: 0")
            print()
            print("## VERDICT: v1.4.4 ratification UNBLOCKED on counter-evidence axis")
            print()
            print("Zero refuting rows across the corpus. Per the v1.4.4 draft decision")
            print("matrix, this satisfies the counter-evidence pre-ratification check.")
            print("Other pre-ratification checks (SC-009 finishing, etc.) still apply")
            print("independently — see claudedocs/constitution-v1.4.4-draft-2026-05-07.md.")

        if errors:
            print()
            print("## Load errors (informational)")
            for e in errors:
                print(f"- {e['path']}: {e.get('error')}")

    return 1 if counter_evidence_rows else 0


if __name__ == "__main__":
    sys.exit(main())
