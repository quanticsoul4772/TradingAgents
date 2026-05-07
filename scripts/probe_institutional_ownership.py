"""De-risk probe for institutional-ownership data — does yfinance support
a Class C-4 (institutional ownership delta) retrospective?

What C-4 would need (per Constitution VIII v1.4.0 forward-catalyst-class
gate methodology):

1. Per-ticker current institutional-ownership panel (top holders +
   pct-held + share counts)
2. Per-ticker HISTORICAL panels (need a time series for delta computation)
3. Coverage breadth across our usual cohort
4. Historical depth ≥ 6 months for retrospective backfill

This script is read-only / network-only. Mirrors PRs #40, #64, #65
probe patterns.

C-4 mechanism hypothesis (per PR #22 bear-side design doc): when
institutional ownership has been ROTATING into a ticker (smart-money
accumulation), bullish commits become post-hoc-priced-in. Rotation OUT
suggests bear thesis being established.

Inverse: stable ownership = no fresh edge in either direction.
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
    "XLF",  # ETFs
]


def probe(ticker: str) -> dict[str, Any]:
    """Probe one ticker for institutional-holders + .info ownership fields."""
    out: dict[str, Any] = {"ticker": ticker}

    t0 = time.perf_counter()
    try:
        t = yf.Ticker(ticker)
        # Multiple ownership-related accessors
        ih = t.institutional_holders
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out

    out["institutional_holders_type"] = type(ih).__name__
    if ih is None:
        out["institutional_holders"] = None
    elif hasattr(ih, "shape"):
        out["institutional_holders_shape"] = list(ih.shape)
        out["institutional_holders_columns"] = list(ih.columns) if hasattr(ih, "columns") else None
        if not ih.empty:
            try:
                out["institutional_holders_head"] = ih.head(2).to_dict("records")
            except Exception as e:
                out["institutional_holders_head_error"] = str(e)

    # Also probe .info dict for ownership-summary fields
    try:
        info = t.info
        ownership_fields = [
            "heldPercentInsiders",
            "heldPercentInstitutions",
            "institutionsCount",
            "majorHolders",
        ]
        out["info_ownership_fields"] = {f: info.get(f) for f in ownership_fields if f in info}
    except Exception as e:
        out["info_error"] = f"{type(e).__name__}: {e}"

    # Also probe major_holders + mutualfund_holders (sometimes available)
    try:
        mh = t.major_holders
        out["major_holders_type"] = type(mh).__name__
        if hasattr(mh, "shape") and not mh.empty:
            out["major_holders_shape"] = list(mh.shape)
    except Exception as e:
        out["major_holders_error"] = f"{type(e).__name__}: {e}"

    return out


def main() -> int:
    print("# yfinance institutional-ownership probe — 2026-05-07")
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
            if k == "info_ownership_fields" and isinstance(v, dict):
                print(f"  - info_ownership_fields ({len(v)} found):")
                for fk, fv in v.items():
                    print(f"      {fk}: {fv}")
            elif k == "institutional_holders_head" and isinstance(v, list):
                print(f"  - institutional_holders_head (showing {len(v)}):")
                for row in v:
                    cols = " | ".join(f"{kk}={vv}" for kk, vv in row.items())
                    print(f"      {cols}")
            elif isinstance(v, str) and len(v) > 250:
                print(f"  - {k}: {v[:250]}...")
            else:
                print(f"  - {k}: {v}")
        print()

    # Summary
    print("## Aggregate stats\n")
    n = len(results)
    n_err = sum(1 for r in results if "error" in r or "fatal" in r)
    n_with_ih = sum(
        1
        for r in results
        if r.get("institutional_holders_shape") and r["institutional_holders_shape"][0] > 0
    )
    n_with_info_summary = sum(1 for r in results if r.get("info_ownership_fields"))

    latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
    avg_ms = sum(latencies) / len(latencies) if latencies else 0
    max_ms = max(latencies) if latencies else 0

    print(f"- Total probed: {n}")
    print(f"- Errored: {n_err}")
    print(f"- Has institutional_holders DataFrame with rows: {n_with_ih}")
    print(f"- Has info ownership-summary fields: {n_with_info_summary}")
    print(f"- Mean latency (success): {avg_ms:.0f}ms")
    print(f"- Max latency (success): {max_ms:.0f}ms")

    return 0


if __name__ == "__main__":
    sys.exit(main())
