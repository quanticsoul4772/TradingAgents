"""De-risk probe for yfinance.analyst_price_targets — does it return what
we'd need for a Class C-3 (analyst PT delta) forward-catalyst-class
retrospective?

What C-3 would need (per Constitution VIII v1.4.0 forward-catalyst-class
gate methodology):
1. Per-ticker, current analyst PT panel (mean / median / high / low + count)
2. Per-ticker, HISTORICAL PT panels on dates matching our backtest cohort
   so we can compute "PT delta over prior 14d" as the catalyst signal
3. Coverage breadth — does it work for our usual cohort (Tech megacaps +
   diverse-sector tickers used in SC-003 / SC-009)?
4. Missing-data behavior — graceful None vs exception?
5. Latency + LRU-cacheability — analogous to spec 008 calendar boost
   yfinance fetch pattern

This script is read-only / network-only — no state changes, no commits to
the experiment corpus. Output goes to stdout; user can paste into
claudedocs/ for the design doc.
"""

from __future__ import annotations

import sys
import time
import traceback
from typing import Any

import yfinance as yf

PROBE_TICKERS = [
    # SC-003 + SC-009 reps
    "NVDA",
    "AAPL",
    "MSFT",
    "META",
    "TSLA",  # Tech megacaps
    "JPM",
    "GS",
    "BAC",  # Financials
    "XOM",
    "COP",
    "CVX",  # Energy
    "JNJ",
    "PFE",  # Healthcare
    "MA",
    "INTC",  # also in current SC-009 cohort
    "SPY",
    "XLF",  # ETFs (do they work?)
]


def probe(ticker: str) -> dict[str, Any]:
    """Probe one ticker. Returns dict of observed shape + latency."""
    out: dict[str, Any] = {"ticker": ticker}

    t0 = time.perf_counter()
    try:
        t = yf.Ticker(ticker)
        # The new API in yfinance >=0.2.40
        pt = t.analyst_price_targets
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out

    out["type"] = type(pt).__name__
    if pt is None:
        out["value"] = None
        return out

    if isinstance(pt, dict):
        out["keys"] = sorted(pt.keys())
        out["sample"] = {k: pt.get(k) for k in sorted(pt.keys())[:8]}
    else:
        try:
            out["repr"] = repr(pt)[:200]
        except Exception as e:
            out["repr_error"] = str(e)

    # Also probe `recommendations` and `recommendations_summary` for
    # historical PT delta angles
    try:
        recs = t.recommendations
        out["recommendations_type"] = type(recs).__name__
        if hasattr(recs, "shape"):
            out["recommendations_shape"] = list(recs.shape)
            out["recommendations_columns"] = (
                list(recs.columns) if hasattr(recs, "columns") else None
            )
            if not recs.empty:
                out["recommendations_head"] = recs.head(3).to_dict("records")
    except Exception as e:
        out["recommendations_error"] = f"{type(e).__name__}: {e}"

    return out


def main() -> int:
    print("# yfinance analyst_price_targets probe — 2026-05-07\n")
    print(f"yfinance version: {yf.__version__}\n")
    print(f"Probing {len(PROBE_TICKERS)} tickers...\n")

    results = []
    for t in PROBE_TICKERS:
        try:
            r = probe(t)
        except Exception:
            r = {"ticker": t, "fatal": traceback.format_exc()[:500]}
        results.append(r)

    # Summary
    print("## Per-ticker results\n")
    for r in results:
        print(f"### {r['ticker']}")
        for k, v in r.items():
            if k == "ticker":
                continue
            if isinstance(v, str) and len(v) > 200:
                print(f"  - {k}: {v[:200]}...")
            else:
                print(f"  - {k}: {v}")
        print()

    print("## Aggregate stats\n")
    n_total = len(results)
    n_error = sum(1 for r in results if "error" in r or "fatal" in r)
    n_none = sum(1 for r in results if r.get("value") is None and "error" not in r)
    n_dict = sum(1 for r in results if r.get("type") == "dict")
    n_with_recs = sum(
        1 for r in results if r.get("recommendations_type") and "recommendations_error" not in r
    )

    latencies_ms = [r["latency_ms"] for r in results if "latency_ms" in r]
    if latencies_ms:
        avg_ms = sum(latencies_ms) / len(latencies_ms)
        max_ms = max(latencies_ms)
    else:
        avg_ms = max_ms = 0.0

    print(f"- Total probed: {n_total}")
    print(f"- Errored: {n_error}")
    print(f"- None / no data: {n_none}")
    print(f"- Returned dict: {n_dict}")
    print(f"- Has recommendations DataFrame: {n_with_recs}")
    print(f"- Mean latency (success): {avg_ms:.0f}ms")
    print(f"- Max latency (success): {max_ms:.0f}ms")

    return 0


if __name__ == "__main__":
    sys.exit(main())
