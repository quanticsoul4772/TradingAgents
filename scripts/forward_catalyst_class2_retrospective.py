"""Class C-2 (short-interest delta) forward-catalyst retrospective.

Per PR #65 feasibility verdict: yfinance.info exposes sharesShort +
sharesShortPriorMonth (delta-computable; 1 prior month). Time-bounded
retrospective: today's snapshot reflects the most recent FINRA report
(~bi-monthly cadence with 2-week lag). Cohort dates within ~30 days of
today are aligned (their propagate-time state matches today's snapshot).

Mechanism hypothesis (per PR #22 design doc): when short interest has
SPIKED recently, sophisticated short-side participants are establishing
a bear thesis → further bullish commits become contrarian-priced-out.
Inverse: short-covering (delta < 0) → further bearish commits become
contrarian.

Operationalization:
  1. Fetch sharesShort + sharesShortPriorMonth for each ticker (LRU-cached)
  2. Compute short_interest_delta_pct = (current - prior) / prior * 100
  3. If delta > +T_spike → suppress bullish commits
     If delta < -T_cover → suppress bearish commits

Cohort scope: state logs from 2026-04-07 onwards (within ~30 days of
today's 2026-05-07 probe). This is approximately the SC-009 cohort.

Per Constitution VIII v1.4.0:
  - Discrim ≥ +5pp / cohort hit ≥ 60% / net Δα ≥ +0.5pp
  - OR shadow-mode-first
  - Plus v1.4.3 additive overlap vs Spec 007 (deferred)

Cost: $0 LLM. yfinance + state-log reads only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

LOG_BASE = Path(os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.expanduser("~/.tradingagents/logs")))

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}

# Snapshot-time-alignment cutoff: today minus 30 calendar days. Cohort
# propagates within this window had access to roughly the same FINRA
# report state as today's snapshot.
COHORT_CUTOFF = date.today() - timedelta(days=30)


@lru_cache(maxsize=128)
def _fetch_short_interest_delta(ticker: str) -> float | None:
    """Return short_interest_delta_pct = (current - prior) / prior * 100.

    Returns None on failure or empty data (e.g., ETFs).
    """
    try:
        import yfinance as yf

        info = yf.Ticker(ticker).info
        if not info:
            return None
        current = info.get("sharesShort")
        prior = info.get("sharesShortPriorMonth")
        if current is None or prior is None or prior == 0:
            return None
        return (float(current) - float(prior)) / float(prior) * 100.0
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


def _classify(rows: list[dict], spike_threshold: float, cover_threshold: float) -> dict:
    sup_bull, sup_bear, untouched = [], [], []
    for r in rows:
        delta = _fetch_short_interest_delta(r["ticker"])
        if delta is None:
            untouched.append(r)
            continue
        r["short_interest_delta_pct"] = delta
        if delta > spike_threshold and r["pm_rating"] in BULLISH_RATINGS:
            sup_bull.append(r)
        elif delta < -cover_threshold and r["pm_rating"] in BEARISH_RATINGS:
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
    parser.add_argument("--spike-threshold", type=float, default=10.0)
    parser.add_argument("--cover-threshold", type=float, default=10.0)
    parser.add_argument("--holding-days", type=int, default=21)
    args = parser.parse_args()

    print("# Class C-2 (short-interest delta) retrospective")
    print()
    print(f"Cohort cutoff: dates ≥ {COHORT_CUTOFF} (today minus 30 days)")
    print(f"Spike threshold: short_interest_delta > +{args.spike_threshold}%")
    print(f"Cover threshold: short_interest_delta < -{args.cover_threshold}%")
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
    print("Applying short-interest filter...")
    classified = _classify(enriched, args.spike_threshold, args.cover_threshold)

    bull = _stats(classified["sup_bull"], "bullish")
    bear = _stats(classified["sup_bear"], "bearish")
    fp_bull = _stats(classified["untouched_bull"], "bullish")
    fp_bear = _stats(classified["untouched_bear"], "bearish")

    print()
    print("## Summary")
    print()
    for label, s in [
        ("Suppressed bullish (delta > spike_threshold)", bull),
        ("Suppressed bearish (delta < -cover_threshold)", bear),
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
