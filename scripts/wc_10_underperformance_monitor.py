"""WC-10 underperformance monitor — flag cohorts where WC-10 mode produces worse realized α than 5-tier baseline.

Constitution v1.5.0 Principle VII sub-section ("Schema-induced abstention is
NOT calibrated abstention") carved out the case where the 5-tier scale collapses
one-directional moderate-magnitude evidence to Hold. WC-10 v1 confirmed this
empirically (3.6× commit ratio) BUT also showed asymmetric calibration: bullish-
side amplification was well-calibrated (NVDA Buy n=6 mean +4.67% α 21d), bearish-
side amplification was anti-calibrated on AAPL (n=6 mean +3.56% α — UW called
bearish but ticker rose).

The v1 ANALYSIS caveat: "WC-10 doesn't fix bear-side calibration; it amplifies
whatever signal the framework was already generating."

This script is the production-tier monitor for that caveat. Extension of
`scripts/memory_log_integrity_check.py` pattern (walk data → flag suspects →
output table), but operates on paired results CSVs instead of memory log
markdown.

When Spec 009 Branch A activates (WC-10 production deployment via
daily_signals.py), this script wires into nightly cron to:
1. Walk accumulated daily_signals.py output (with both --wc-10-enabled and
   baseline rows captured)
2. Compute per-pair realized α delta: α(WC-10_binned_rating) − α(5tier_rating)
3. Flag dates / tickers / cohorts where WC-10 underperforms 5-tier
4. Trigger an operator-alert markdown if cumulative underperformance exceeds
   threshold (default: 5 consecutive underperforming pairs OR cumulative
   delta < -5pp on n≥10 pairs)

For now (pre-Spec-009-Branch-A activation), the script consumes the WC-10 v1
pilot CSV (`experiments/2026-05-08-001-wc-10-pilot/results.csv`) as a smoke
test. After v2 + v3 land, it can also consume their CSVs.

Closes the Constitution v1.5.0 monitoring loop: makes the bear-regime caveat
operationally enforceable instead of documentation-only.

Sister script: `scripts/memory_log_integrity_check.py` (covers the orthogonal
"reflection prose hallucinates" failure mode).

Usage:
    python scripts/wc_10_underperformance_monitor.py
    python scripts/wc_10_underperformance_monitor.py --csv <path> [--alert-threshold-pp -5.0]
    python scripts/wc_10_underperformance_monitor.py --json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

DEFAULT_CSV = Path("experiments/2026-05-08-001-wc-10-pilot/results.csv")
DEFAULT_HOLDING_DAYS = 21

# Bullish / bearish bin sets (must match bin_scalar_to_tier output buckets)
BULLISH_BINS = {"Buy", "Overweight"}
BEARISH_BINS = {"Underweight", "Sell"}


def _load_paired_rows(csv_path: Path) -> dict[tuple[str, str], dict[str, dict]]:
    """Returns {(ticker, date): {mode: row}} for rows present in BOTH modes."""
    by_pair: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    with csv_path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("error"):
                continue
            key = (row["ticker"], row["date"])
            by_pair[key][row["mode"]] = row
    # Filter to keys with BOTH modes present
    return {k: v for k, v in by_pair.items() if "wc_10" in v and "5tier_baseline" in v}


def _alpha_for_rating(rating: str, alpha_pct: float) -> float:
    """Map a rating to the realized α attributed to it.

    Bullish ratings (Buy/OW): α attributed = realized α (the commit goes long).
    Bearish ratings (UW/Sell): α attributed = -realized α (the commit goes short).
    Hold: α attributed = 0 (no commitment).
    """
    if rating in BULLISH_BINS:
        return alpha_pct
    if rating in BEARISH_BINS:
        return -alpha_pct
    return 0.0  # Hold


def _compute_pair_deltas(
    pairs: dict[tuple[str, str], dict[str, dict]], holding_days: int = DEFAULT_HOLDING_DAYS
) -> list[dict]:
    """For each (ticker, date), compute α(WC-10) − α(5-tier) attributed-to-rating delta."""
    out: list[dict] = []
    for (ticker, date), modes in sorted(pairs.items()):
        wc = modes["wc_10"]
        bs = modes["5tier_baseline"]
        wc_bin = wc["binned_tier"]
        bs_rating = bs["rating"]
        raw, alpha, days = fetch_returns(ticker, date, holding_days=holding_days)
        if alpha is None:
            continue
        alpha_pct = alpha * 100.0
        wc_attr = _alpha_for_rating(wc_bin, alpha_pct)
        bs_attr = _alpha_for_rating(bs_rating, alpha_pct)
        delta = wc_attr - bs_attr
        out.append(
            {
                "ticker": ticker,
                "date": date,
                "wc_10_scalar": wc["rating"],
                "wc_10_bin": wc_bin,
                "5tier_rating": bs_rating,
                "alpha_pct": alpha_pct,
                "days": days,
                "wc_10_attributed_alpha": wc_attr,
                "5tier_attributed_alpha": bs_attr,
                "delta_pp": delta,
                "decisions_differ": wc_bin != bs_rating,
            }
        )
    return out


def _classify_alerts(rows: list[dict], alert_threshold_pp: float = -5.0) -> dict:
    """Apply alert criteria + return a dict with per-pair flags + cohort summary.

    Alert criteria (any triggers operator-alert):
    - Single-pair severe underperformance: |delta_pp| < alert_threshold_pp on a
      single pair (default: any pair with delta < -5pp)
    - Streak of underperformance: ≥5 consecutive pairs with delta < 0
    - Cumulative cohort underperformance: cumulative delta < alert_threshold_pp
      across n ≥ 10 pairs

    Returns dict with:
    - per_pair_alerts: list of pairs that meet single-pair criterion
    - streak_detected: bool + length + start/end indices
    - cohort_cumulative_delta: float
    - cohort_alert_triggered: bool
    """
    per_pair_alerts = [r for r in rows if r["delta_pp"] < alert_threshold_pp]

    # Streak detection: ≥5 consecutive negative deltas
    streak_detected = False
    streak_length = 0
    streak_start = None
    streak_end = None
    cur_run = 0
    cur_start = None
    for i, r in enumerate(rows):
        if r["delta_pp"] < 0:
            if cur_run == 0:
                cur_start = i
            cur_run += 1
            if cur_run > streak_length:
                streak_length = cur_run
                streak_start = cur_start
                streak_end = i
            if cur_run >= 5:
                streak_detected = True
        else:
            cur_run = 0
            cur_start = None

    # Cohort cumulative
    cum_delta = sum(r["delta_pp"] for r in rows)
    cohort_alert = len(rows) >= 10 and cum_delta < alert_threshold_pp

    return {
        "per_pair_alerts": per_pair_alerts,
        "streak_detected": streak_detected,
        "streak_length": streak_length,
        "streak_start_idx": streak_start,
        "streak_end_idx": streak_end,
        "cohort_cumulative_delta_pp": cum_delta,
        "cohort_n": len(rows),
        "cohort_alert_triggered": cohort_alert,
        "any_alert_triggered": bool(per_pair_alerts) or streak_detected or cohort_alert,
    }


def _render_text_report(rows: list[dict], alerts: dict, csv_path: Path) -> str:
    parts: list[str] = []
    parts.append("# WC-10 underperformance monitor\n")
    parts.append(f"Source: {csv_path.as_posix()}")
    parts.append(f"Paired rows: {len(rows)}")
    parts.append(
        f"Decisions differ: {sum(1 for r in rows if r['decisions_differ'])} of {len(rows)}"
    )
    parts.append(
        f"Cohort cumulative Δα (WC-10 minus 5-tier): {alerts['cohort_cumulative_delta_pp']:+.2f}pp"
    )
    parts.append("")
    parts.append("## Per-pair details")
    parts.append(
        f"{'ticker':6s} {'date':12s} {'wc_bin':12s} {'5tier':12s} {'α%':>8s} {'days':>5s} {'Δpp':>8s}"
    )
    for r in rows:
        differ_marker = "*" if r["decisions_differ"] else " "
        parts.append(
            f"{r['ticker']:6s} {r['date']:12s} {r['wc_10_bin']:12s} {r['5tier_rating']:12s} "
            f"{r['alpha_pct']:>+7.2f}% {r['days']:>5d} {r['delta_pp']:>+7.2f}pp {differ_marker}"
        )
    parts.append("")
    parts.append("## Alert summary")
    parts.append(f"Per-pair alerts (delta < threshold): {len(alerts['per_pair_alerts'])}")
    parts.append(f"Streak detected (≥5 consecutive negative): {alerts['streak_detected']}")
    if alerts["streak_detected"]:
        parts.append(
            f"  → streak length: {alerts['streak_length']} (rows {alerts['streak_start_idx']} to {alerts['streak_end_idx']})"
        )
    parts.append(
        f"Cohort alert (n≥10 + cumulative < threshold): {alerts['cohort_alert_triggered']}"
    )
    parts.append("")
    if alerts["any_alert_triggered"]:
        parts.append("**⚠ ALERT: WC-10 production deployment caveat may be active.**")
        parts.append(
            "See Constitution v1.5.0 Principle VII sub-section + Spec 009 FR-006 for remediation guidance."
        )
    else:
        parts.append("✓ No alerts. WC-10 mode performing within tolerance.")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"Paired-mode results.csv (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--holding-days",
        type=int,
        default=DEFAULT_HOLDING_DAYS,
        help=f"Forward-α holding window (default: {DEFAULT_HOLDING_DAYS})",
    )
    parser.add_argument(
        "--alert-threshold-pp",
        type=float,
        default=-5.0,
        help="Alert when single-pair delta < threshold, OR cohort cumulative delta < threshold (default: -5.0pp)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output instead of markdown report",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"ERROR: {args.csv} does not exist", file=sys.stderr)
        return 2

    pairs = _load_paired_rows(args.csv)
    if not pairs:
        print(
            f"ERROR: no paired (wc_10 + 5tier_baseline) rows found in {args.csv}", file=sys.stderr
        )
        return 1

    rows = _compute_pair_deltas(pairs, holding_days=args.holding_days)
    alerts = _classify_alerts(rows, alert_threshold_pp=args.alert_threshold_pp)

    if args.json:
        print(json.dumps({"rows": rows, "alerts": alerts}, indent=2))
    else:
        print(_render_text_report(rows, alerts, args.csv))

    # Exit code: 0 if no alerts, 1 if any alert
    return 1 if alerts["any_alert_triggered"] else 0


if __name__ == "__main__":
    sys.exit(main())
