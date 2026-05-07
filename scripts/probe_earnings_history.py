"""De-risk probe for yfinance.earnings_history — does it return what
Class C-5 (earnings price reaction) retrospective would need?

What C-5 would need (per Constitution VIII v1.4.0 forward-catalyst-class
gate methodology):

1. Per-ticker earnings dates (announcement timestamps)
2. Per-earnings-date EPS surprise (% beat/miss)
3. Per-earnings-date stock price reaction (open-to-close move on
   announcement day, or 1-day forward, or 5-day forward)
4. Coverage breadth across our usual cohort
5. Historical depth — does it cover dates from 6+ months ago for
   retrospective backfill?

This script is read-only / network-only — no state changes, no commits
to the experiment corpus.

Mirrors the PR #40 probe pattern that determined C-3 NOT-FEASIBLE.
"""

from __future__ import annotations

import sys
import time
import traceback
from typing import Any

import yfinance as yf

PROBE_TICKERS = [
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
    "LLY",  # Healthcare
    "MA",
    "INTC",
    "AMD",  # SC-009 representatives
    "SPY",
    "XLF",  # ETFs (do they work?)
]


def probe(ticker: str) -> dict[str, Any]:
    """Probe one ticker for earnings_history shape + latency."""
    out: dict[str, Any] = {"ticker": ticker}

    t0 = time.perf_counter()
    try:
        t = yf.Ticker(ticker)
        eh = t.earnings_history
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out

    out["type"] = type(eh).__name__
    if eh is None:
        out["value"] = None
        return out

    if hasattr(eh, "shape"):
        out["shape"] = list(eh.shape)
        out["columns"] = list(eh.columns) if hasattr(eh, "columns") else None
        if not eh.empty:
            try:
                # First 3 rows give us a peek at structure
                head = eh.head(3).reset_index().to_dict("records")
                out["head"] = head
                # Last row date if index is timestamp
                if hasattr(eh.index, "min") and hasattr(eh.index, "max"):
                    out["date_min"] = str(eh.index.min())
                    out["date_max"] = str(eh.index.max())
                out["row_count"] = len(eh)
            except Exception as e:
                out["head_error"] = str(e)

    # Also probe earnings_dates for forward-looking calendar (used elsewhere)
    try:
        ed = t.earnings_dates
        out["earnings_dates_type"] = type(ed).__name__
        if hasattr(ed, "shape") and not ed.empty:
            out["earnings_dates_shape"] = list(ed.shape)
            out["earnings_dates_columns"] = list(ed.columns) if hasattr(ed, "columns") else None
    except Exception as e:
        out["earnings_dates_error"] = f"{type(e).__name__}: {e}"

    return out


def main() -> int:
    print("# yfinance earnings_history probe — 2026-05-07")
    print()
    print(f"yfinance version: {yf.__version__}")
    print(f"Probing {len(PROBE_TICKERS)} tickers...\n")

    results = []
    for t in PROBE_TICKERS:
        try:
            r = probe(t)
        except Exception:
            r = {"ticker": t, "fatal": traceback.format_exc()[:500]}
        results.append(r)

    print("## Per-ticker results\n")
    for r in results:
        print(f"### {r['ticker']}")
        for k, v in r.items():
            if k == "ticker":
                continue
            if isinstance(v, str) and len(v) > 250:
                print(f"  - {k}: {v[:250]}...")
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                # Pretty print first record only
                print(f"  - {k}: (showing first row of {len(v)})")
                for kk, vv in v[0].items():
                    print(f"      {kk}: {vv}")
            else:
                print(f"  - {k}: {v}")
        print()

    # Summary
    print("## Aggregate stats\n")
    n = len(results)
    n_err = sum(1 for r in results if "error" in r or "fatal" in r)
    n_dataframe = sum(1 for r in results if r.get("type") == "DataFrame")
    n_with_data = sum(
        1 for r in results if r.get("row_count") is not None and r.get("row_count", 0) > 0
    )
    n_with_eps = sum(
        1
        for r in results
        if r.get("columns")
        and any("eps" in c.lower() or "surprise" in c.lower() for c in r["columns"])
    )

    latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
    avg_ms = sum(latencies) / len(latencies) if latencies else 0
    max_ms = max(latencies) if latencies else 0

    print(f"- Total probed: {n}")
    print(f"- Errored: {n_err}")
    print(f"- Returned DataFrame: {n_dataframe}")
    print(f"- Has rows of data: {n_with_data}")
    print(f"- Has EPS/surprise columns: {n_with_eps}")
    print(f"- Mean latency (success): {avg_ms:.0f}ms")
    print(f"- Max latency (success): {max_ms:.0f}ms")

    return 0


if __name__ == "__main__":
    sys.exit(main())
