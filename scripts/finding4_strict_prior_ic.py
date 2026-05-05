"""Finding #4 strict-prior IC test — discriminates the look-ahead-bias explanation.

The contrarian retrospective (claudedocs/contrarian-gate-retrospective-2026-05-05.md)
surfaced a gap between finding #4's within-ticker IC = -0.489 and the gate's
prospective Δα at strict-prior history. Three explanations:
  1. Strict-prior history at N=5-19 is too noisy for percentile estimation
  2. Early-history fires happen on regimes where mechanism is weaker
  3. Finding #4's IC has look-ahead bias

This script directly tests #3 by computing within-ticker IC TWO ways for the
same ticker × date pairs:

  Original:    spearman(bull_keyword_count, future_90d_α) — uses absolute
               bull_count value, equivalent to ranking against the FULL ticker
               history (all dates simultaneously)

  Strict-prior: spearman(strict_prior_percentile, future_90d_α) — for each
               (ticker, date_i), the percentile of bull_count_i vs bull_counts
               at positions 1..i-1 of same ticker. Noisy early in series.

If both ICs are similar → look-ahead ruled out (#3 rejected) → explanation #1
or #2 is the live candidate.

If strict-prior IC drops materially → look-ahead confirmed (#3) → finding #4's
actionable predictive power is overstated.

Methodology mirrors the within_ticker_artifact_check, except:
  - Sample = market_report (the validated within-ticker predictor signal),
    not fundamentals_report (which was the original eval-report row that
    happened to have the strongest aggregate IC; finding #4 is on
    market_report bull_keyword_count specifically per
    claudedocs/within-ticker-artifact-check-2026-05-05.md).
  - Two parallel IC computations per ticker × position-floor combination.

Writes claudedocs/finding4-strict-prior-ic-2026-05-05.md.
Zero LLM cost.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.signals.cache import query_all
from tradingagents.signals.contrarian_gate import _percentile_of_value
from tradingagents.signals.evaluation import _spearman_ic
from tradingagents.signals.featurization import bull_keyword_count

HORIZON_DAYS = 90
HISTORY_FLOORS = (5, 20)
MIN_TICKER_N = 5  # for the within-ticker IC computation, need ≥ MIN_TICKER_N pairs
OUT_PATH = Path("claudedocs/finding4-strict-prior-ic-2026-05-05.md")


def _load_per_ticker_pairs() -> dict[str, list[dict]]:
    """Pull all market_report rows from cache, grouped by ticker, sorted by date."""
    rows = query_all(signal_id="market_report")
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        prose = r.get("value")
        if not prose or not isinstance(prose, str):
            continue
        ticker = r["ticker"]
        date = r["date"]
        bull_count = bull_keyword_count(prose)
        by_ticker[ticker].append(
            {
                "ticker": ticker,
                "date": date,
                "bull_count": bull_count,
            }
        )
    for ticker in by_ticker:
        by_ticker[ticker].sort(key=lambda r: r["date"])
    return by_ticker


def _enrich_with_alpha_and_strict_prior(
    by_ticker: dict[str, list[dict]],
) -> None:
    """For each (ticker, date_i), add:
    - alpha (90d future return)
    - strict_prior_percentile (vs positions 1..i-1 of same ticker)
    - n_prior (size of strict-prior history)
    """
    for ticker, ticker_rows in by_ticker.items():
        for i, r in enumerate(ticker_rows):
            history_counts = [h["bull_count"] for h in ticker_rows[:i]]
            r["n_prior"] = len(history_counts)
            r["strict_prior_percentile"] = (
                _percentile_of_value(history_counts, r["bull_count"]) if history_counts else None
            )
            _, alpha, _ = fetch_returns(ticker, r["date"], holding_days=HORIZON_DAYS)
            r["alpha"] = alpha


def _per_ticker_ics(by_ticker: dict[str, list[dict]], n_prior_floor: int) -> dict[str, dict]:
    """For each ticker, compute IC two ways:
      - original: spearman(bull_count, alpha) over rows where alpha is not None
        AND row's n_prior >= n_prior_floor (so we're comparing apples-to-apples
        with the strict-prior subset)
      - strict_prior: spearman(strict_prior_percentile, alpha) over the same subset
    Returns {ticker: {n, ic_original, ic_strict_prior}}.
    """
    out: dict[str, dict] = {}
    for ticker, ticker_rows in by_ticker.items():
        eligible = [
            r
            for r in ticker_rows
            if r["alpha"] is not None
            and r["n_prior"] >= n_prior_floor
            and r["strict_prior_percentile"] is not None
        ]
        if len(eligible) < MIN_TICKER_N:
            out[ticker] = {
                "n": len(eligible),
                "ic_original": None,
                "ic_strict_prior": None,
            }
            continue
        original_pairs = [(r["bull_count"], r["alpha"]) for r in eligible]
        strict_prior_pairs = [(r["strict_prior_percentile"], r["alpha"]) for r in eligible]
        out[ticker] = {
            "n": len(eligible),
            "ic_original": _spearman_ic(original_pairs),
            "ic_strict_prior": _spearman_ic(strict_prior_pairs),
        }
    return out


def _summary_for_floor(by_ticker, n_prior_floor: int) -> tuple[list[dict], dict]:
    per_ticker = _per_ticker_ics(by_ticker, n_prior_floor)
    rows = []
    ics_orig: list[float] = []
    ics_strict: list[float] = []
    for ticker, stats in sorted(per_ticker.items()):
        rows.append({"ticker": ticker, **stats})
        if stats["ic_original"] is not None:
            ics_orig.append(stats["ic_original"])
        if stats["ic_strict_prior"] is not None:
            ics_strict.append(stats["ic_strict_prior"])
    summary = {
        "n_tickers_evaluated": len(ics_orig),
        "median_ic_original": statistics.median(ics_orig) if ics_orig else None,
        "median_ic_strict_prior": statistics.median(ics_strict) if ics_strict else None,
        "n_pos_original": sum(1 for ic in ics_orig if ic > 0),
        "n_neg_original": sum(1 for ic in ics_orig if ic < 0),
        "n_pos_strict": sum(1 for ic in ics_strict if ic > 0),
        "n_neg_strict": sum(1 for ic in ics_strict if ic < 0),
    }
    return rows, summary


def main() -> int:
    print("[load] reading market_report rows from cache...")
    by_ticker = _load_per_ticker_pairs()
    print(f"[load] {sum(len(v) for v in by_ticker.values())} rows across {len(by_ticker)} tickers")

    print("[fetch] computing 90d alpha + strict-prior percentiles...")
    _enrich_with_alpha_and_strict_prior(by_ticker)

    results = {}
    for floor in HISTORY_FLOORS:
        rows, summary = _summary_for_floor(by_ticker, floor)
        results[floor] = {"rows": rows, "summary": summary}
        print(
            f"[floor N>={floor}] tickers eligible: {summary['n_tickers_evaluated']}, "
            f"median IC original: {summary['median_ic_original']}, "
            f"median IC strict-prior: {summary['median_ic_strict_prior']}"
        )

    # Render report
    lines: list[str] = []
    lines.append(f"# Finding #4 strict-prior IC test — {datetime.utcnow().date().isoformat()}\n")
    lines.append(
        "## Question\n\n"
        "The spec 003 retrospective surfaced 3 explanations for the gap between finding "
        "#4's within-ticker IC = -0.489 and the gate's prospective Δα. This script "
        "directly tests **explanation #3 (look-ahead bias)** by computing within-ticker "
        "IC two ways:\n\n"
        "1. **Original**: `spearman(bull_keyword_count, future_90d_α)` — uses absolute bull_count\n"
        "2. **Strict-prior**: `spearman(strict_prior_percentile, future_90d_α)` — uses the "
        "percentile that would have been computable PROSPECTIVELY at each (ticker, date)\n\n"
        "Both ICs computed over the SAME row subset (rows where `n_prior >= floor` AND "
        "`alpha is not None`). The only thing that changes is whether the X variable is "
        "the absolute bull_count or the strict-prior percentile.\n\n"
        "**Key insight**: if both ICs are similar → look-ahead bias is NOT the issue → "
        "explanations #1 (history-too-noisy) or #2 (regime-mismatch) are live. If "
        "strict-prior IC drops materially → look-ahead bias confirmed → finding #4's "
        "actionable prospective predictive power is overstated.\n"
    )
    lines.append("## Method\n")
    lines.append(
        "1. For each cached `market_report` row, compute `bull_keyword_count`\n"
        "2. Per ticker, sort by date ascending. For each row at position i:\n"
        "   - `n_prior` = i (number of strictly-prior dates of same ticker)\n"
        "   - `strict_prior_percentile` = percentile of current bull_count vs positions 0..i-1\n"
        f"   - `alpha` = `fetch_returns(holding_days={HORIZON_DAYS})` realized α\n"
        f"3. For each history floor in {HISTORY_FLOORS}, restrict to rows with "
        f"`n_prior >= floor` AND `alpha is not None`\n"
        "4. Per ticker (n_eligible >= 5), compute Spearman IC for both metrics\n"
        "5. Take median across tickers; compare\n"
    )
    for floor in HISTORY_FLOORS:
        s = results[floor]["summary"]
        med_o = s["median_ic_original"]
        med_s = s["median_ic_strict_prior"]
        med_o_str = f"{med_o:+.4f}" if med_o is not None else "—"
        med_s_str = f"{med_s:+.4f}" if med_s is not None else "—"
        lines.append(f"## History floor: N≥{floor}\n")
        lines.append(
            f"- Tickers evaluated: **{s['n_tickers_evaluated']}**\n"
            f"- **Median IC (original, look-ahead-included): {med_o_str}**\n"
            f"  - direction agreement: {s['n_pos_original']}+ / {s['n_neg_original']}−\n"
            f"- **Median IC (strict-prior, no look-ahead): {med_s_str}**\n"
            f"  - direction agreement: {s['n_pos_strict']}+ / {s['n_neg_strict']}−\n"
        )
        lines.append("### Per-ticker breakdown\n")
        lines.append("| Ticker | n | IC original | IC strict-prior | Δ (strict − orig) |")
        lines.append("|---|---:|---:|---:|---:|")
        for r in results[floor]["rows"]:
            ic_o = r["ic_original"]
            ic_s = r["ic_strict_prior"]
            if ic_o is None:
                lines.append(f"| {r['ticker']} | {r['n']} | — | — | — |")
                continue
            diff = ic_s - ic_o if (ic_o is not None and ic_s is not None) else None
            ic_o_str = f"{ic_o:+.4f}"
            ic_s_str = f"{ic_s:+.4f}" if ic_s is not None else "—"
            diff_str = f"{diff:+.4f}" if diff is not None else "—"
            lines.append(f"| {r['ticker']} | {r['n']} | {ic_o_str} | {ic_s_str} | {diff_str} |")
        lines.append("")

    lines.append("## Verdict\n")
    lines.append("(Verdict written by hand after reviewing tables.)\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
