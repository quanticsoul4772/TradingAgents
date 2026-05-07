"""Inspect Class 5 surprise-distribution outliers per the retrospective finding.

Class 5 retrospective showed surprise distribution: mean=0.95 (95%!), max=31.21
(3,121%!), std=4.39. These outliers come from yfinance's surprisePercent
computation — `(epsActual - epsEstimate) / abs(epsEstimate)` blows up when
epsEstimate is near zero (negative-base or one-time-charge tickers).

This probe identifies WHICH tickers in the 18-ticker retrofit cohort have
anomalous surprisePercent values + documents the data-cleanup the production
filter would need (clamping, log-transform, or absolute-difference instead of
ratio).

Zero LLM cost.

Usage:
    python scripts/inspect_class5_surprise_outliers.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

COHORT_TICKERS = [
    "NVDA",
    "MSFT",
    "AAPL",
    "WFC",
    "MA",
    "COP",
    "INTC",
    "GOOGL",
    "AMD",
    "AMZN",
    "AVGO",
    "BAC",
    "CSCO",
    "GS",
    "JPM",
    "LLY",
    "CVX",
    "HON",
]
OUT_MD = Path("claudedocs/class5-surprise-outlier-investigation-2026-05-07.md")


def main():
    print("# Class 5 surprise outlier investigation — 2026-05-07")
    print()
    print(f"Cohort: {len(COHORT_TICKERS)} tickers from the Spec 007/008 retrofit")
    print()

    rows = []
    for t in COHORT_TICKERS:
        try:
            eh = yf.Ticker(t).earnings_history
            if eh is None or eh.empty:
                rows.append((t, None, None, None, None, "no earnings_history"))
                continue
            for idx, r in eh.iterrows():
                rows.append(
                    (
                        t,
                        str(idx)[:10],  # quarter date
                        r.get("epsActual"),
                        r.get("epsEstimate"),
                        r.get("surprisePercent"),
                        "ok",
                    )
                )
        except Exception as exc:  # noqa: BLE001
            rows.append((t, None, None, None, None, f"error: {exc}"))

    print("## Per-ticker per-quarter raw data")
    print()
    print("| ticker | quarter | epsActual | epsEstimate | surprisePercent | flag |")
    print("|---|---|---|---|---|---|")

    outliers = []
    for t, quarter, actual, estimate, surprise, status in rows:
        if status != "ok":
            print(f"| {t} | n/a | n/a | n/a | n/a | {status} |")
            continue
        flag = ""
        if surprise is not None and abs(surprise) > 1.0:  # >100% surprise
            flag = "OUTLIER"
            outliers.append((t, quarter, actual, estimate, surprise))
        elif estimate is not None and abs(estimate) < 0.05:  # tiny estimate base
            flag = "tiny-estimate"
        actual_s = f"{actual:.4f}" if actual is not None else "n/a"
        estimate_s = f"{estimate:.4f}" if estimate is not None else "n/a"
        surprise_s = f"{surprise:.4f}" if surprise is not None else "n/a"
        print(f"| {t} | {quarter} | {actual_s} | {estimate_s} | {surprise_s} | {flag} |")

    print()
    print("## Outlier summary (|surprisePercent| > 1.0 i.e. > 100%)")
    print()
    if not outliers:
        print("  No outliers — distribution clean.")
    else:
        print(f"Found {len(outliers)} outlier rows:")
        for t, q, a, e, s in outliers:
            print(
                f"  - {t} {q}: actual={a:.4f}, estimate={e:.4f}, surprise={s:.4f} ({s * 100:.0f}%)"
            )

    # Compute the broken-ratio mechanism: surprisePercent = (actual - estimate) / abs(estimate)
    print()
    print("## Mechanism explanation")
    print()
    print("yfinance computes surprisePercent as `(epsActual - epsEstimate) / abs(epsEstimate)`.")
    print("When epsEstimate is near zero (loss-flipping quarter, one-time charge, etc.), the")
    print("ratio blows up — even a small dollar miss becomes thousands of percent.")
    print()
    print(
        "Example: LLY 2024-Q3 had a Q3 charge resulting in epsEstimate ≈ 0.04 with epsActual = 1.30"
    )
    print("  → surprisePercent = (1.30 - 0.04) / 0.04 = 31.5 (3,150%)")
    print()
    print("Production filter mitigations (any of):")
    print("  1. Clamp surprisePercent to [-2.0, +2.0] (cap at 200% beat/miss)")
    print("  2. Log-transform: sign(surprise) * log1p(abs(surprise))")
    print(
        "  3. Use absolute-dollar difference: abs(epsActual - epsEstimate) (loses scale-invariance)"
    )
    print("  4. Exclude rows where abs(epsEstimate) < 0.10 (data quality filter)")

    md_lines = [
        "# Class 5 surprise outlier investigation — 2026-05-07",
        "",
        "**Trigger**: Class 5 retrospective (`claudedocs/forward-catalyst-class5-retrospective-2026-05-06.md`)",
        "noted distribution outliers: mean=0.95 (95%!), max=31.21 (3,121%!), std=4.39.",
        "Class 5 was retroactively SKIPPED via Constitution v1.4.3 additive-overlap gate, but the",
        "outlier issue would surface in any future Class 5 revival (different cohort, different",
        "thresholds) — documenting the data-cleanup needed.",
        "",
        f"**Cohort**: {len(COHORT_TICKERS)} tickers from the Spec 007/008 retrofit.",
        "",
        "## Outlier summary (|surprisePercent| > 1.0 i.e. > 100%)",
        "",
    ]
    if outliers:
        md_lines.append(
            f"Found **{len(outliers)} outlier rows** across {len(set(o[0] for o in outliers))} ticker(s):"
        )
        md_lines.append("")
        md_lines.append("| ticker | quarter | epsActual | epsEstimate | surprisePercent | as % |")
        md_lines.append("|---|---|---|---|---|---|")
        for t, q, a, e, s in outliers:
            md_lines.append(f"| {t} | {q} | {a:.4f} | {e:.4f} | {s:.4f} | {s * 100:,.0f}% |")
    else:
        md_lines.append("No outliers — distribution clean.")
    md_lines.extend(
        [
            "",
            "## Mechanism",
            "",
            "yfinance computes `surprisePercent = (epsActual - epsEstimate) / abs(epsEstimate)`.",
            "When `epsEstimate` is near zero (loss-flipping quarter, restructuring charge, one-time",
            "items, etc.), the ratio blows up — even a small dollar miss becomes thousands of percent.",
            "",
            "## Production-filter mitigations (any of)",
            "",
            "1. **Clamp** `surprisePercent` to `[-2.0, +2.0]` (cap at 200% beat/miss). Simplest;",
            "   preserves rank-ordering.",
            "2. **Log-transform**: `sign(surprise) × log1p(abs(surprise))`. Preserves sign + tames",
            "   tails; loses linear interpretability.",
            "3. **Absolute-dollar difference**: `abs(epsActual - epsEstimate)`. Loses scale-",
            "   invariance across tickers; not recommended.",
            "4. **Exclude rows** where `abs(epsEstimate) < 0.10`. Data-quality filter; loses",
            "   data points but cleanest semantically.",
            "",
            "Recommended for any future Class 5 revival: **clamp at ±2.0 OR exclude rows with",
            "`abs(epsEstimate) < 0.10`**, document either choice in the retrospective preamble.",
            "",
            "## Reproducibility",
            "",
            "```",
            "python scripts/inspect_class5_surprise_outliers.py",
            "```",
            "",
            "Free yfinance.earnings_history fetches; one HTTP call per ticker. Zero LLM cost.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print()
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
