"""Dual-pilot synchronized monitor — WC-11 v2 + BR-3 v2 progress at a glance.

Per `claudedocs/dual-pilot-launch-playbook-2026-05-09.md` (PR #214). While
both pilots run in background simultaneously, operators (and Claude during
"merge → next ranked option" cycles) need a quick status check. This
script peeks both results.csv files + reports progress, ETA, and any
errors.

Cost: $0 (filesystem reads only).

Usage:
    python scripts/dual_pilot_monitor.py
    python scripts/dual_pilot_monitor.py --json
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

WC11_V2_CSV = Path("experiments/2026-05-09-002-wc11-v2-disambiguation/results.csv")
BR3_V2_CSV = Path("experiments/2026-05-09-003-br3-v2-news-fundamentals/results.csv")

# Total expected rows per pilot
WC11_V2_TOTAL = 60  # 3 tickers × 5 dates × 4 perms
BR3_V2_TOTAL = 40  # 2 tickers × 5 dates × 4 modes


def _stats(csv_path: Path, total: int) -> dict:
    """Return per-pilot status dict."""
    if not csv_path.exists():
        return {
            "csv": str(csv_path),
            "exists": False,
            "rows": 0,
            "completed": 0,
            "errored": 0,
            "total": total,
            "pct": 0.0,
            "rating_dist": {},
            "mean_run_seconds": None,
        }
    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    completed = sum(1 for r in rows if not r.get("error"))
    errored = sum(1 for r in rows if r.get("error"))
    rating_dist = dict(Counter(r["rating"] for r in rows if not r.get("error") and r.get("rating")))
    run_seconds = [
        float(r["run_seconds"]) for r in rows if not r.get("error") and r.get("run_seconds")
    ]
    mean_run_seconds = sum(run_seconds) / len(run_seconds) if run_seconds else None
    return {
        "csv": str(csv_path),
        "exists": True,
        "rows": len(rows),
        "completed": completed,
        "errored": errored,
        "total": total,
        "pct": 100 * len(rows) / total if total else 0.0,
        "rating_dist": rating_dist,
        "mean_run_seconds": mean_run_seconds,
    }


def _eta(stats: dict) -> str:
    """Estimate ETA based on mean propagate time + remaining rows."""
    if not stats["exists"] or stats["mean_run_seconds"] is None:
        return "N/A (no completed rows yet)"
    remaining = stats["total"] - stats["rows"]
    if remaining <= 0:
        return "COMPLETE"
    eta_seconds = remaining * stats["mean_run_seconds"]
    eta_hours = eta_seconds / 3600
    return f"~{eta_hours:.1f}h ({remaining} rows × ~{stats['mean_run_seconds']:.0f}s)"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    wc11 = _stats(WC11_V2_CSV, WC11_V2_TOTAL)
    br3 = _stats(BR3_V2_CSV, BR3_V2_TOTAL)
    wc11["eta"] = _eta(wc11)
    br3["eta"] = _eta(br3)

    if args.json:
        print(json.dumps({"wc11_v2": wc11, "br3_v2": br3}, indent=2))
        return

    print("=" * 70)
    print(
        f"{'Pilot':<12} {'rows':>6}/{'total':>6} {'pct':>6} {'errored':>8} {'mean s':>8} {'ETA':>20}"
    )
    print("-" * 70)
    for name, stats in [("WC-11 v2", wc11), ("BR-3 v2", br3)]:
        if stats["exists"]:
            print(
                f"{name:<12} {stats['rows']:>6}/{stats['total']:<6} {stats['pct']:>5.0f}% "
                f"{stats['errored']:>8} {stats['mean_run_seconds'] or 0:>7.0f}s "
                f"{stats['eta']:>20}"
            )
            if stats["rating_dist"]:
                rating_str = " | ".join(
                    f"{r}: {n}" for r, n in sorted(stats["rating_dist"].items())
                )
                print(f"  rating dist: {rating_str}")
        else:
            print(f"{name:<12} {'(no CSV yet)':<25} {stats['eta']:>20}")
    print("=" * 70)


if __name__ == "__main__":
    main()
