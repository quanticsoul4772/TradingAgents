"""Class C-5 PRICE-REACTION variant retrospective (NEW operationalization).

Distinct from `scripts/forward_catalyst_class5_retrospective.py` (which
tests the EPS surprise-magnitude variant — verdict PASS standalone +
FAIL additive vs Spec 007 per PR #22 / Constitution v1.4.3).

This script tests a DIFFERENT C-5 operationalization per PR #22 design
doc: the announcement-day STOCK PRICE REACTION magnitude (previous close
to earnings-day close move, including overnight gaps) as the contrarian
signal, not the EPS surprise itself. A stock can have small surprise +
large reaction (driven by guidance / commentary) or vice versa — these
are correlated but not identical signals.

Mechanism hypothesis: when a stock has had a recent EARNINGS DAY
PRICE REACTION of large magnitude, the reaction signals information
already absorbed by the market (the consensus view of the print + any
guidance interpretation). Subsequent commits in the direction of the
reaction are post-hoc chasing.

Two operationalizations:
  1. **--variant magnitude**: at propagate time, look back to most
     recent earnings event in prior 30 calendar days. If announcement
     reaction >= +T_react%, suppress bullish commits (Buy/OW). If
     <= -T_react%, suppress bearish commits (UW/Sell). Default T = 5.0%.
  2. **--variant aligned**: same as #1 but ALSO requires reaction
     direction to match EPS surprise direction (beat + UP, miss + DOWN).
     Beat + UP + bullish commit = post-hoc chasing pattern.

Per Constitution VIII v1.4.0 + v1.4.3:
  - Standalone gate: discrim ≥ +5pp / cohort hit ≥ 60% / net Δalpha ≥ +0.5pp
  - Additive overlap vs Spec 007 + Spec 008 (deferred)

Cost: ZERO LLM. yfinance + state-log reads only.

Usage:
    python scripts/forward_catalyst_class5_reaction_retrospective.py
    python scripts/forward_catalyst_class5_reaction_retrospective.py --threshold 7.5
    python scripts/forward_catalyst_class5_reaction_retrospective.py --variant aligned
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

LOG_BASE = Path(os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.expanduser("~/.tradingagents/logs")))

BULLISH_RATINGS = {"Buy", "Overweight"}
BEARISH_RATINGS = {"Underweight", "Sell"}
LOOKBACK_DAYS = 30


@lru_cache(maxsize=128)
def _earnings_dates_df(ticker: str):
    try:
        import yfinance as yf

        ed = yf.Ticker(ticker).earnings_dates
        if ed is None or not hasattr(ed, "empty") or ed.empty:
            return None
        return ed
    except Exception:  # noqa: BLE001  # intentionally broad: yfinance can raise many undocumented exception types
        return None


@lru_cache(maxsize=128)
def _price_history(ticker: str):
    try:
        import yfinance as yf

        hist = yf.Ticker(ticker).history(period="2y", auto_adjust=False)
        if hist is None or not hasattr(hist, "empty") or hist.empty:
            return None
        return hist
    except Exception:  # noqa: BLE001  # intentionally broad: yfinance can raise many undocumented exception types
        return None


def _most_recent_earnings_event(ticker: str, propagate_date_str: str) -> dict | None:
    """Return dict with event_date / surprise_pct / reaction_pct or None."""
    ed = _earnings_dates_df(ticker)
    if ed is None:
        return None

    propagate_dt = datetime.strptime(propagate_date_str, "%Y-%m-%d").date()
    window_start = propagate_dt - timedelta(days=LOOKBACK_DAYS)

    candidates = []
    for idx, row in ed.iterrows():
        try:
            event_date = idx.date() if hasattr(idx, "date") else idx
        except Exception:
            continue
        if not (window_start <= event_date < propagate_dt):
            continue
        surprise = row.get("Surprise(%)")
        try:
            surprise_val = float(surprise)
            if surprise_val != surprise_val:  # NaN
                continue
        except (TypeError, ValueError):
            continue
        candidates.append((event_date, surprise_val))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    event_date, surprise_pct = candidates[0]

    hist = _price_history(ticker)
    if hist is None:
        return None
    try:
        hist_dates = [d.date() for d in hist.index]
    except Exception:
        return None
    if event_date in hist_dates:
        post_idx = hist_dates.index(event_date)
    else:
        future = [d for d in hist_dates if d >= event_date]
        if not future:
            return None
        post_idx = hist_dates.index(future[0])
    if post_idx == 0:
        return None
    pre_close = float(hist.iloc[post_idx - 1]["Close"])
    post_close = float(hist.iloc[post_idx]["Close"])
    if pre_close <= 0:
        return None
    reaction_pct = (post_close / pre_close - 1.0) * 100.0

    return {
        "event_date": str(event_date),
        "surprise_pct": surprise_pct,
        "reaction_pct": reaction_pct,
    }


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
            date = log_file.stem.replace("full_states_log_", "")
            try:
                d = json.loads(log_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            final = d.get("final_trade_decision", "") or ""
            m = rating_re.search(final)
            if not m:
                continue
            out.append({"ticker": ticker_dir.name, "date": date, "pm_rating": m.group(1)})
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


def _classify(rows: list[dict], threshold: float, variant: str) -> dict:
    sup_bull, sup_bear, untouched = [], [], []
    for r in rows:
        event = _most_recent_earnings_event(r["ticker"], r["date"])
        if event is None:
            untouched.append(r)
            continue
        r["earnings_event"] = event
        reaction = event["reaction_pct"]
        if variant == "aligned":
            surprise = event["surprise_pct"]
            same_sign = (reaction > 0 and surprise > 0) or (reaction < 0 and surprise < 0)
            if not same_sign:
                untouched.append(r)
                continue
        if reaction >= threshold and r["pm_rating"] in BULLISH_RATINGS:
            sup_bull.append(r)
        elif reaction <= -threshold and r["pm_rating"] in BEARISH_RATINGS:
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
    return {
        "n": len(group),
        "mean_alpha_pct": mean_a,
        "hit_rate_pct": hits / len(group) * 100,
    }


def _gate(label: str, sup: dict, fp: dict, suppression: str) -> str:
    if sup["n"] == 0 or fp.get("n", 0) == 0:
        return f"{label}: SKIP — insufficient cohort (n_sup={sup['n']}, n_fp={fp.get('n', 0)})"
    discrim = sup["hit_rate_pct"] - fp["hit_rate_pct"]
    # net Δalpha from suppressing = if bullish, suppression gain = -realized alpha (we avoided losses)
    # if bearish, suppression gain = +realized alpha (we avoided gains we would have missed shorting)
    # Standardize: gain from suppression = signed value such that positive = beneficial
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
        f"  Gate 1 (discrim ≥ +5pp): {'PASS' if g1 else 'FAIL'} ({discrim:+.2f}pp; sup={sup['hit_rate_pct']:.1f}%, fp={fp['hit_rate_pct']:.1f}%)\n"
        f"  Gate 2 (cohort hit ≥ 60%): {'PASS' if g2 else 'FAIL'} ({sup['hit_rate_pct']:.1f}%)\n"
        f"  Gate 3 (net Δalpha ≥ +0.5pp): {'PASS' if g3 else 'FAIL'} ({net_dalpha:+.2f}pp)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=5.0)
    parser.add_argument("--holding-days", type=int, default=21)
    parser.add_argument("--variant", choices=("magnitude", "aligned"), default="magnitude")
    args = parser.parse_args()

    print("# Class C-5 PRICE-REACTION variant retrospective")
    print()
    print(f"Variant: {args.variant}")
    print(f"Reaction threshold: ±{args.threshold}%")
    print(f"Lookback: {LOOKBACK_DAYS} days")
    print(f"Holding days: {args.holding_days}")
    print()

    print("Walking state logs...")
    rows = _walk_state_logs()
    print(f"  {len(rows)} state logs with parseable PM ratings")

    print()
    print("Enriching with realized alpha (yfinance, slow)...")
    enriched = _enrich_with_alpha(rows, args.holding_days)
    print(f"  {len(enriched)} rows with measurable alpha at {args.holding_days}d")

    print()
    print(f"Applying {args.variant} filter at ±{args.threshold}%...")
    classified = _classify(enriched, args.threshold, args.variant)

    bull = _stats(classified["sup_bull"], "bullish")
    bear = _stats(classified["sup_bear"], "bearish")
    fp_bull = _stats(classified["untouched_bull"], "bullish")
    fp_bear = _stats(classified["untouched_bear"], "bearish")

    print()
    print("## Summary")
    print()
    for label, s in [
        ("Suppressed bullish", bull),
        ("Suppressed bearish", bear),
        ("Untouched bullish (FP cohort)", fp_bull),
        ("Untouched bearish (FP cohort)", fp_bear),
    ]:
        print(f"### {label}")
        print(f"  n: {s['n']}")
        if s["n"] > 0:
            print(f"  mean alpha: {s['mean_alpha_pct']:+.2f}%")
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
