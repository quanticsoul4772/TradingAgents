"""Class C-4 (institutional ownership delta) forward-catalyst retrospective.

Per PR #66 feasibility verdict: yfinance.institutional_holders returns
10-row × 6-col DataFrame with `pctChange` column (per-holder pctHeld
delta from prior 13F → current). Time-bounded retrospective: today's
snapshot reflects Q4 2025 13F state. Q1 2026 13Fs land ~2026-05-15;
this retrospective MUST run before that date for cohort-time-alignment
to hold.

Mechanism hypothesis (per PR #22 design doc): when top institutional
holders are ROTATING IN to a ticker (sum of positive pctChange across
top 10 holders), smart-money accumulation establishes a bull thesis
→ further bullish commits become contrarian-priced-in. Inverse: rotation
OUT (sum of negative pctChange) suggests bear thesis being established
→ further bearish commits become contrarian.

Operationalization:
  1. Fetch institutional_holders for each ticker (LRU-cached)
  2. Compute net_rotation_pct = sum(pctChange) across top 10 holders
  3. If net_rotation_pct > +T_inflow → suppress bullish commits
     If net_rotation_pct < -T_outflow → suppress bearish commits

Cohort scope: state logs from 2026-02-14 onwards (when Q4 2025 13Fs
became the most-recent-filed data). Earlier propagates used Q3 2025
data which is no longer reflected in today's yfinance snapshot.

Per Constitution VIII v1.4.0:
  - Discrim ≥ +5pp / cohort hit ≥ 60% / net Δα ≥ +0.5pp
  - OR shadow-mode-first if criteria 1+2 pass without 3
  - Plus v1.4.3 additive overlap vs Spec 007 (deferred to separate sweep)

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

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}

# Q4 2025 13F filings landed ~2026-02-14. Cohort dates before that used
# Q3 2025 13Fs at propagate time, which is no longer reflected in today's
# snapshot. Limit cohort to dates on or after this cutoff.
COHORT_CUTOFF = date(2026, 2, 14)


@lru_cache(maxsize=128)
def _fetch_institutional_rotation(ticker: str) -> float | None:
    """Return sum(pctChange) across top 10 holders, or None on failure."""
    try:
        import yfinance as yf

        ih = yf.Ticker(ticker).institutional_holders
        if ih is None or not hasattr(ih, "empty") or ih.empty:
            return None
        if "pctChange" not in ih.columns:
            return None
        # Top 10 (DataFrame is already sorted by pctHeld desc per yfinance)
        top10 = ih.head(10)
        # Sum pctChange; handle NaN
        net_rotation = float(top10["pctChange"].fillna(0).sum())
        return net_rotation
    except Exception:
        return None


def _walk_state_logs() -> list[dict]:
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
            if not m:
                continue
            out.append({"ticker": ticker_dir.name, "date": date_str, "pm_rating": m.group(1)})
    return out


def _enrich_with_alpha(rows: list[dict], holding_days: int) -> list[dict]:
    enriched = []
    for r in rows:
        try:
            _raw, alpha, _days = fetch_returns(r["ticker"], r["date"], holding_days=holding_days)
            if alpha is None:
                continue
            r["alpha_pct"] = float(alpha) * 100
            enriched.append(r)
        except Exception:
            continue
    return enriched


def _classify(rows: list[dict], inflow_threshold: float, outflow_threshold: float) -> dict:
    sup_bull, sup_bear, untouched = [], [], []
    for r in rows:
        rotation = _fetch_institutional_rotation(r["ticker"])
        if rotation is None:
            untouched.append(r)
            continue
        r["net_rotation_pct"] = rotation
        if rotation > inflow_threshold and r["pm_rating"] in BULLISH_RATINGS:
            sup_bull.append(r)
        elif rotation < -outflow_threshold and r["pm_rating"] in BEARISH_RATINGS:
            sup_bear.append(r)
        else:
            untouched.append(r)
    return {
        "sup_bull": sup_bull,
        "sup_bear": sup_bear,
        "untouched_bull": [r for r in untouched if r["pm_rating"] in BULLISH_RATINGS],
        "untouched_bear": [r for r in untouched if r["pm_rating"] in BEARISH_RATINGS],
    }


def _stats(group: list[dict], suppression: str) -> dict:
    if not group:
        return {"n": 0}
    alphas = [r["alpha_pct"] for r in group]
    mean_a = sum(alphas) / len(alphas)
    if suppression == "bullish":
        hits = sum(1 for a in alphas if a < 0)
    else:
        hits = sum(1 for a in alphas if a > 0)
    return {"n": len(group), "mean_alpha_pct": mean_a, "hit_rate_pct": hits / len(group) * 100}


def _gate(label: str, sup: dict, fp: dict, suppression: str) -> str:
    if sup["n"] == 0 or fp.get("n", 0) == 0:
        return f"{label}: SKIP — insufficient cohort (n_sup={sup['n']}, n_fp={fp.get('n', 0)})"
    discrim = sup["hit_rate_pct"] - fp["hit_rate_pct"]
    if suppression == "bullish":
        net_dalpha = -sup["mean_alpha_pct"]
    else:
        net_dalpha = sup["mean_alpha_pct"]
    g1 = discrim >= 5.0
    g2 = sup["hit_rate_pct"] >= 60.0
    g3 = net_dalpha >= 0.5
    verdict = "PASS" if (g1 and g2 and g3) else ("SHADOW-MODE-FIRST" if (g1 and g2) else "SKIP")
    return (
        f"{label}: {verdict}\n"
        f"  Gate 1 (discrim ≥ +5pp): {'PASS' if g1 else 'FAIL'} "
        f"({discrim:+.2f}pp; sup={sup['hit_rate_pct']:.1f}%, fp={fp['hit_rate_pct']:.1f}%)\n"
        f"  Gate 2 (cohort hit ≥ 60%): {'PASS' if g2 else 'FAIL'} ({sup['hit_rate_pct']:.1f}%)\n"
        f"  Gate 3 (net Δα ≥ +0.5pp): {'PASS' if g3 else 'FAIL'} ({net_dalpha:+.2f}pp)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inflow-threshold", type=float, default=0.05)
    parser.add_argument("--outflow-threshold", type=float, default=0.05)
    parser.add_argument("--holding-days", type=int, default=21)
    args = parser.parse_args()

    today = date.today()
    if today >= date(2026, 5, 15):
        print(
            "WARNING: today is on or after 2026-05-15. Q1 2026 13Fs may have landed; "
            "snapshot may diverge from cohort-propagate state. Verify before trusting verdict.",
            file=sys.stderr,
        )

    print("# Class C-4 (institutional ownership delta) retrospective")
    print()
    print(f"Cohort cutoff: dates ≥ {COHORT_CUTOFF}")
    print(f"Inflow threshold: net_rotation > +{args.inflow_threshold:.3f}")
    print(f"Outflow threshold: net_rotation < -{args.outflow_threshold:.3f}")
    print(f"Holding days: {args.holding_days}")
    print()

    print("Walking state logs...")
    rows = _walk_state_logs()
    print(f"  {len(rows)} state logs in cohort (date ≥ {COHORT_CUTOFF})")

    print()
    print("Enriching with realized α...")
    enriched = _enrich_with_alpha(rows, args.holding_days)
    print(f"  {len(enriched)} rows with measurable α at {args.holding_days}d")

    print()
    print("Applying institutional-rotation filter...")
    classified = _classify(enriched, args.inflow_threshold, args.outflow_threshold)

    bull = _stats(classified["sup_bull"], "bullish")
    bear = _stats(classified["sup_bear"], "bearish")
    fp_bull = _stats(classified["untouched_bull"], "bullish")
    fp_bear = _stats(classified["untouched_bear"], "bearish")

    print()
    print("## Summary")
    print()
    for label, s in [
        ("Suppressed bullish (rotation > inflow_threshold)", bull),
        ("Suppressed bearish (rotation < -outflow_threshold)", bear),
        ("Untouched bullish (FP cohort)", fp_bull),
        ("Untouched bearish (FP cohort)", fp_bear),
    ]:
        print(f"### {label}")
        print(f"  n: {s['n']}")
        if s["n"] > 0:
            print(f"  mean α: {s['mean_alpha_pct']:+.2f}%")
            print(f"  hit rate: {s['hit_rate_pct']:.1f}%")
        print()

    print("## Constitution VIII v1.4.0 standalone gate")
    print()
    print(_gate("Bull-side", bull, fp_bull, "bullish"))
    print()
    print(_gate("Bear-side", bear, fp_bear, "bearish"))
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
