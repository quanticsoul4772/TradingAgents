"""De-risk probe for short-interest data — does yfinance support a
Class C-2 (short-interest delta) retrospective?

What C-2 would need (per Constitution VIII v1.4.0 forward-catalyst-class
gate methodology):

1. Per-ticker current short interest (shares short, % of float)
2. Per-ticker HISTORICAL short interest panels (need a time series for
   delta computation across our backtest cohort dates)
3. Coverage breadth across our usual cohort
4. Historical depth ≥ 6 months for retrospective backfill

This script is read-only / network-only. Mirrors PRs #40 + #64 probe
patterns.

C-2 mechanism hypothesis (per PR #22 bear-side design doc): when short
interest in a ticker has SPIKED recently, the bear thesis is being
established by sophisticated short-side participants. Subsequent bullish
commits may be contrarian-priced-out (informed-bear-flow signals
absorbed information).

Inverse hypothesis: when short interest has been COVERED (DOWN), the
bear thesis is unwinding; bearish commits become contrarian.
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
    """Probe one ticker for short-interest fields."""
    out: dict[str, Any] = {"ticker": ticker}

    t0 = time.perf_counter()
    try:
        t = yf.Ticker(ticker)
        # yfinance exposes short interest via .info dict (no dedicated method)
        info = t.info
        out["latency_ms"] = (time.perf_counter() - t0) * 1000
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out

    if not info:
        out["info_empty"] = True
        return out

    # Relevant short-interest fields (varies by yfinance version; capture all
    # that look short-related)
    short_fields = [
        "sharesShort",
        "sharesShortPriorMonth",
        "sharesShortPreviousMonthDate",
        "dateShortInterest",
        "shortRatio",
        "shortPercentOfFloat",
        "floatShares",
        "sharesPercentSharesOut",
    ]
    out["short_fields"] = {}
    for field in short_fields:
        if field in info:
            out["short_fields"][field] = info[field]

    out["has_any_short_data"] = bool(out["short_fields"])

    return out


def main() -> int:
    print("# yfinance short-interest probe — 2026-05-07")
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
            if k == "short_fields" and isinstance(v, dict):
                print(f"  - short_fields ({len(v)} found):")
                for fk, fv in v.items():
                    print(f"      {fk}: {fv}")
            elif isinstance(v, str) and len(v) > 250:
                print(f"  - {k}: {v[:250]}...")
            else:
                print(f"  - {k}: {v}")
        print()

    # Summary
    print("## Aggregate stats\n")
    n = len(results)
    n_err = sum(1 for r in results if "error" in r or "fatal" in r)
    n_with_short = sum(1 for r in results if r.get("has_any_short_data"))
    n_with_prior = sum(
        1 for r in results if "sharesShortPriorMonth" in (r.get("short_fields") or {})
    )

    latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
    avg_ms = sum(latencies) / len(latencies) if latencies else 0
    max_ms = max(latencies) if latencies else 0

    print(f"- Total probed: {n}")
    print(f"- Errored: {n_err}")
    print(f"- Has any short-interest field: {n_with_short}")
    print(f"- Has sharesShort + sharesShortPriorMonth (delta-computable): {n_with_prior}")
    print(f"- Mean latency (success): {avg_ms:.0f}ms")
    print(f"- Max latency (success): {max_ms:.0f}ms")

    return 0


if __name__ == "__main__":
    sys.exit(main())
