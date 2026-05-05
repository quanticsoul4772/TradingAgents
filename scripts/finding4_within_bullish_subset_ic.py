"""Finding #4 within-bullish-subset IC test — discriminates explanation #2.

The strict-prior IC test ruled out look-ahead bias as the explanation for the
gap between finding #4's IC = -0.489 and the gate's prospective Δα. Two
remaining explanations:

  1. Low-N (5-19) percentile estimation noise dominates (LEADING)
  2. The IC measures across-all-dates rank correlation; the gate measures
     within-bullish-commit-subset Δα — these are different statistics

Explanation #2 says: even with perfect history, the gate's predictive power
on the bullish-rated subset (which is what it actually fires on) is weaker
than the all-dates correlation suggests. This script directly tests it by
restricting the IC computation to ONLY Buy + Overweight commits per ticker.

If within-bullish-subset IC ≈ all-dates IC (~-0.49) → mechanism transfers to
bullish subset → explanation #2 REJECTED → low-N noise (explanation #1) is
the residual cause.

If within-bullish-subset IC ≈ 0 or positive → mechanism doesn't transfer →
explanation #2 CONFIRMED → the gate's premise is broken at the bullish-bucket
level even with infinite history.

Methodology:
  - Pull market_report (for bull_count) AND final_trade_decision (for rating)
    from cache, joined by (ticker, date)
  - For each ticker, sort by date; compute strict-prior percentile of bull_count
  - Filter to rows where rating ∈ {Buy, Overweight}
  - Compute Spearman IC per ticker over the bullish subset
  - Compare to the all-dates IC from the strict-prior IC test

Writes claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md.
Zero LLM cost.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tradingagents.agents.utils.rating import parse_rating
from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.signals.cache import query_all
from tradingagents.signals.contrarian_gate import _percentile_of_value
from tradingagents.signals.evaluation import _spearman_ic
from tradingagents.signals.featurization import bull_keyword_count

HORIZON_DAYS = 90
MIN_TICKER_N = 5
BULLISH_RATINGS = {"Buy", "Overweight"}
OUT_PATH = Path("claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md")


def _join_market_report_and_rating() -> dict[str, list[dict]]:
    """Load market_report + final_trade_decision from cache, join by (ticker, date),
    group by ticker, sort by date asc."""
    mr_rows = query_all(signal_id="market_report")
    ftd_rows = query_all(signal_id="final_trade_decision")

    # Build {(ticker.upper(), date): rating} map
    rating_map: dict[tuple[str, str], str] = {}
    for r in ftd_rows:
        v = r.get("value")
        if not v or not isinstance(v, str):
            continue
        rating_map[(r["ticker"].upper(), r["date"])] = parse_rating(v)

    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for r in mr_rows:
        prose = r.get("value")
        if not prose or not isinstance(prose, str):
            continue
        ticker = r["ticker"]
        date = r["date"]
        rating = rating_map.get((ticker.upper(), date))
        if rating is None:
            continue
        by_ticker[ticker].append(
            {
                "ticker": ticker,
                "date": date,
                "bull_count": bull_keyword_count(prose),
                "rating": rating,
            }
        )
    for ticker in by_ticker:
        by_ticker[ticker].sort(key=lambda r: r["date"])
    return by_ticker


def _enrich(by_ticker: dict[str, list[dict]]) -> None:
    for ticker_rows in by_ticker.values():
        for i, r in enumerate(ticker_rows):
            history_counts = [h["bull_count"] for h in ticker_rows[:i]]
            r["n_prior"] = len(history_counts)
            r["strict_prior_percentile"] = (
                _percentile_of_value(history_counts, r["bull_count"]) if history_counts else None
            )
            _, alpha, _ = fetch_returns(r["ticker"], r["date"], holding_days=HORIZON_DAYS)
            r["alpha"] = alpha


def _ic_for_subset(rows: list[dict]) -> tuple[float | None, int]:
    """Compute Spearman IC of (strict_prior_percentile, alpha) over a subset.
    Returns (ic, n_eligible). IC is None if n < MIN_TICKER_N or no variance."""
    eligible = [
        r for r in rows if r["alpha"] is not None and r["strict_prior_percentile"] is not None
    ]
    if len(eligible) < MIN_TICKER_N:
        return None, len(eligible)
    pairs = [(r["strict_prior_percentile"], r["alpha"]) for r in eligible]
    return _spearman_ic(pairs), len(eligible)


def main() -> int:
    print("[load] joining market_report + final_trade_decision from cache...")
    by_ticker = _join_market_report_and_rating()
    print(
        f"[load] {sum(len(v) for v in by_ticker.values())} joined rows "
        f"across {len(by_ticker)} tickers"
    )

    print("[fetch] computing 90d alpha + strict-prior percentiles...")
    _enrich(by_ticker)

    # Per-ticker: compute IC over (a) all-dates, (b) bullish-only subset, (c) non-bullish
    per_ticker_results: list[dict] = []
    for ticker, rows in sorted(by_ticker.items()):
        all_ic, all_n = _ic_for_subset(rows)
        bullish_rows = [r for r in rows if r["rating"] in BULLISH_RATINGS]
        bullish_ic, bullish_n = _ic_for_subset(bullish_rows)
        nonbullish_rows = [r for r in rows if r["rating"] not in BULLISH_RATINGS]
        nonbull_ic, nonbull_n = _ic_for_subset(nonbullish_rows)
        per_ticker_results.append(
            {
                "ticker": ticker,
                "all_n": all_n,
                "all_ic": all_ic,
                "bullish_n": bullish_n,
                "bullish_ic": bullish_ic,
                "nonbull_n": nonbull_n,
                "nonbull_ic": nonbull_ic,
            }
        )
        print(
            f"  {ticker}: all_n={all_n} all_IC={all_ic} | "
            f"bullish_n={bullish_n} bullish_IC={bullish_ic}"
        )

    # Aggregate medians
    all_ics = [r["all_ic"] for r in per_ticker_results if r["all_ic"] is not None]
    bullish_ics = [r["bullish_ic"] for r in per_ticker_results if r["bullish_ic"] is not None]
    nonbull_ics = [r["nonbull_ic"] for r in per_ticker_results if r["nonbull_ic"] is not None]

    median_all = statistics.median(all_ics) if all_ics else None
    median_bullish = statistics.median(bullish_ics) if bullish_ics else None
    median_nonbull = statistics.median(nonbull_ics) if nonbull_ics else None

    print(f"\n[median] all-dates: {median_all}")
    print(f"[median] bullish-subset: {median_bullish}")
    print(f"[median] non-bullish-subset: {median_nonbull}")

    # Render report
    lines: list[str] = []
    lines.append(
        f"# Finding #4 within-bullish-subset IC test — {datetime.now().date().isoformat()}\n"
    )
    lines.append(
        "## Question\n\n"
        "The strict-prior IC test ruled out look-ahead bias as the explanation for "
        "the gap between finding #4's IC = -0.489 and the gate's prospective Δα. "
        "This script tests **explanation #2 (within-bullish-subset Δα is a different "
        "statistic than all-dates rank IC)** by computing the within-ticker IC over "
        "ONLY Buy + Overweight commits per ticker.\n\n"
        "**If within-bullish-subset IC ≈ all-dates IC (~-0.49)**: mechanism transfers "
        "to bullish subset → explanation #2 REJECTED → low-N noise (explanation #1) is "
        "the residual cause.\n\n"
        "**If within-bullish-subset IC ≈ 0 or positive**: mechanism doesn't transfer → "
        "explanation #2 CONFIRMED → the gate's premise is broken at the bullish-bucket "
        "level even with infinite history.\n"
    )
    lines.append("## Method\n")
    lines.append(
        "1. Load `market_report` + `final_trade_decision` from cache; join by (ticker, date)\n"
        "2. Per ticker, sort by date asc; compute strict-prior percentile of bull_count + "
        f"realized {HORIZON_DAYS}d α via `fetch_returns`\n"
        f"3. Per ticker, compute Spearman IC of (strict_prior_percentile, α) for "
        f"three subsets (require n ≥ {MIN_TICKER_N}):\n"
        "   - All dates (matches the prior strict-prior IC test)\n"
        "   - Bullish subset (rating ∈ {Buy, Overweight}) — the gate's actual scope\n"
        "   - Non-bullish subset (rating ∈ {Hold, Underweight, Sell}) — control\n"
        "4. Take median across tickers; compare\n"
    )
    lines.append("## Headline\n")
    lines.append("| Subset | Median IC across tickers | n tickers eligible | Direction |")
    lines.append("|---|---:|---:|---|")
    for label, med, ics in [
        ("All dates", median_all, all_ics),
        ("**Bullish subset (Buy/OW)**", median_bullish, bullish_ics),
        ("Non-bullish subset", median_nonbull, nonbull_ics),
    ]:
        if med is None:
            lines.append(f"| {label} | — | 0 | — |")
            continue
        n_pos = sum(1 for ic in ics if ic > 0)
        n_neg = sum(1 for ic in ics if ic < 0)
        lines.append(f"| {label} | **{med:+.4f}** | {len(ics)} | {n_pos}+ / {n_neg}− |")
    lines.append("")
    lines.append("## Per-ticker breakdown\n")
    lines.append("| Ticker | All n | All IC | Bullish n | Bullish IC | Non-bull n | Non-bull IC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in per_ticker_results:

        def _fmt(ic, n, name):
            if n < MIN_TICKER_N:
                return f"({n}, n<5)"
            if ic is None:
                return "—"
            return f"{ic:+.3f}"

        lines.append(
            f"| {r['ticker']} | {r['all_n']} | {_fmt(r['all_ic'], r['all_n'], 'all')} | "
            f"{r['bullish_n']} | {_fmt(r['bullish_ic'], r['bullish_n'], 'bull')} | "
            f"{r['nonbull_n']} | {_fmt(r['nonbull_ic'], r['nonbull_n'], 'non')} |"
        )
    lines.append("")
    lines.append("## Verdict\n")
    lines.append("(Verdict written by hand after reviewing tables.)\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
