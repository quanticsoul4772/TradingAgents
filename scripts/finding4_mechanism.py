"""Mechanism investigation for finding #4.

Finding #4 (claudedocs/within-ticker-artifact-check-2026-05-05.md):
market_report bull_keyword_count anti-predicts within-ticker α at 90d
(within-ticker median IC -0.4890, 9/9 unanimous negative direction).

Three mechanism candidates per the artifact-check verdict:
  (a) Mean-reversion: high-bull-keyword moments are local price tops
  (b) Confirmation bias / recency: bullish prose follows recent gains
  (c) Selection: analyst gets bullish on recently-strong tickers

This script tests (a)+(b)+(c) by computing PRIOR 30d/60d/90d alpha for
each cached market_report row, then correlating bull_keyword_count
with prior alpha. If high bull_keyword_count correlates with high
prior alpha, the recency/selection mechanism is supported. If
uncorrelated, the mechanism is something else (the prose density isn't
explained by recent price action).

Reports both within-ticker (the load-bearing question) and aggregate
ICs, so we can compare to the artifact-check methodology.

Writes claudedocs/finding4-mechanism-2026-05-05.md.
Zero LLM cost. Uses yfinance for historical prices.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

from tradingagents.signals.cache import query_all
from tradingagents.signals.evaluation import _spearman_ic, _within_ticker_ic_summary
from tradingagents.signals.featurization import bull_keyword_count

PRIOR_HORIZONS = [30, 60, 90]
MIN_N_PER_TICKER = 5
OUT_PATH = Path("claudedocs/finding4-mechanism-2026-05-05.md")


def fetch_prior_alpha(ticker: str, trade_date: str, prior_days: int) -> float | None:
    """Compute SPY-relative return ending the trading day BEFORE trade_date,
    over the last `prior_days` trading days.

    Returns None if data unavailable (too early in history, delisted, network).
    """
    try:
        end = datetime.strptime(trade_date, "%Y-%m-%d")
        # Fetch enough history to capture prior_days trading days
        # plus a buffer for the trade_date itself.
        start = end - timedelta(days=int(prior_days * 1.5) + 14)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")  # exclusive in yfinance

        stock = yf.Ticker(ticker).history(start=start_str, end=end_str)
        spy = yf.Ticker("SPY").history(start=start_str, end=end_str)

        if len(stock) < prior_days + 1 or len(spy) < prior_days + 1:
            return None

        # Use the LAST row of each as the "day before trade_date" close
        # (yfinance end is exclusive, so the last bar is the most recent
        # close strictly before trade_date).
        stock_end = float(stock["Close"].iloc[-1])
        stock_start = float(stock["Close"].iloc[-(prior_days + 1)])
        spy_end = float(spy["Close"].iloc[-1])
        spy_start = float(spy["Close"].iloc[-(prior_days + 1)])

        raw = (stock_end - stock_start) / stock_start
        spy_ret = (spy_end - spy_start) / spy_start
        return raw - spy_ret
    except Exception:  # noqa: BLE001 — return None for any data failure
        return None


def main() -> int:
    print("[load] reading market_report rows from cache...")
    rows = query_all(signal_id="market_report")
    print(f"[load] {len(rows)} cached rows")

    # Build (bull_count, prior_alpha) pairs per (ticker, horizon)
    # plus aggregate (cross-ticker) pairs per horizon
    by_ticker_horizon: dict[tuple[str, int], list[tuple[float, float]]] = defaultdict(list)
    aggregate_per_horizon: dict[int, list[tuple[float, float]]] = defaultdict(list)

    for r in rows:
        prose = r.get("value")
        if not prose or not isinstance(prose, str):
            continue
        ticker = r["ticker"]
        date = r["date"]
        bull_count = bull_keyword_count(prose)
        for h in PRIOR_HORIZONS:
            prior_alpha = fetch_prior_alpha(ticker, date, h)
            if prior_alpha is None:
                continue
            by_ticker_horizon[(ticker, h)].append((bull_count, prior_alpha))
            aggregate_per_horizon[h].append((bull_count, prior_alpha))

    # Aggregate IC per horizon
    aggregate_ic: dict[int, float | None] = {}
    for h, pairs in aggregate_per_horizon.items():
        aggregate_ic[h] = _spearman_ic(pairs)
        print(
            f"[agg] horizon={h}d  n={len(pairs)}  IC={aggregate_ic[h]:+.4f}"
            if aggregate_ic[h] is not None
            else f"[agg] horizon={h}d  n={len(pairs)}  IC=None"
        )

    # Within-ticker IC per horizon
    within_summary: dict[int, dict | None] = {}
    per_ticker_per_horizon: dict[int, list[dict]] = defaultdict(list)
    for h in PRIOR_HORIZONS:
        # Group pairs by ticker for this horizon
        pairs_by_ticker: dict[str, list[tuple[float, float]]] = {}
        for (ticker, hh), pairs in by_ticker_horizon.items():
            if hh != h:
                continue
            pairs_by_ticker[ticker] = pairs
        within_summary[h] = _within_ticker_ic_summary(pairs_by_ticker, min_n=MIN_N_PER_TICKER)

        # Build per-ticker breakdown for the report
        for ticker, pairs in sorted(pairs_by_ticker.items()):
            if len(pairs) < MIN_N_PER_TICKER:
                per_ticker_per_horizon[h].append({"ticker": ticker, "n": len(pairs), "ic": None})
                continue
            per_ticker_per_horizon[h].append(
                {"ticker": ticker, "n": len(pairs), "ic": _spearman_ic(pairs)}
            )

    # Render report
    lines: list[str] = []
    lines.append("# Finding #4 mechanism investigation — 2026-05-05\n")
    lines.append(
        "## Question\n\n"
        "Finding #4 established that `market_report bull_keyword_count` anti-predicts "
        "within-ticker α at 90d (within-ticker median IC -0.4890, 9/9 unanimous negative). "
        "Three mechanism candidates were enumerated:\n"
        "1. **Mean-reversion**: high-bull-keyword moments are local price tops\n"
        "2. **Confirmation bias / recency**: bullish prose follows recent gains\n"
        "3. **Selection**: analyst gets bullish on recently-strong tickers\n\n"
        "All three predict the same observation pattern: **high bull_keyword_count "
        "should correlate with HIGH prior 30d/60d/90d α**. If that correlation is "
        "present and within-ticker (not just between-ticker), one of (a)/(b)/(c) is "
        "operating. If absent, the mechanism is something else (e.g., prose density "
        "is independent of recent price action).\n"
    )
    lines.append("## Method\n")
    lines.append(
        "- For each cached `market_report` row, compute `bull_keyword_count` via the existing featurizer\n"
        "- For each, fetch prior 30d/60d/90d **trading-day** α (ticker − SPY) ending the trading day BEFORE the trade_date\n"
        "- Compute aggregate IC (across all rows) AND within-ticker median IC (per the artifact-check methodology) at each prior horizon\n"
        "- Per-ticker breakdown: which tickers show within-ticker correlation, which don't\n"
    )
    lines.append("## Headline\n")
    lines.append(
        "| Prior horizon | Aggregate IC (n) | Within-ticker median IC | Within-ticker n_pos / n_neg |"
    )
    lines.append("|---|---:|---:|---|")
    for h in PRIOR_HORIZONS:
        agg_n = len(aggregate_per_horizon[h])
        agg_str = f"{aggregate_ic[h]:+.4f} (n={agg_n})" if aggregate_ic[h] is not None else "—"
        if within_summary[h] is not None:
            w = within_summary[h]
            within_str = f"{w['median_ic']:+.4f}"
            sign_str = f"{w['n_positive']}+ / {w['n_negative']}−"
        else:
            within_str = "—"
            sign_str = "—"
        lines.append(f"| Prior {h}d | {agg_str} | {within_str} | {sign_str} |")
    lines.append("")
    lines.append("## Per-ticker IC by prior horizon\n")
    # Combine into one wide table
    tickers = sorted({r["ticker"] for h in PRIOR_HORIZONS for r in per_ticker_per_horizon[h]})
    lines.append("| Ticker | n_30d | IC_30d | n_60d | IC_60d | n_90d | IC_90d |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for tk in tickers:
        cells = [tk]
        for h in PRIOR_HORIZONS:
            row = next((r for r in per_ticker_per_horizon[h] if r["ticker"] == tk), None)
            if row is None:
                cells.extend(["—", "—"])
                continue
            cells.append(str(row["n"]))
            if row["ic"] is None:
                cells.append("—")
            else:
                cells.append(f"{row['ic']:+.3f}")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Verdict\n")
    lines.append("(Verdict written by hand after reviewing tables.)\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    print("\n" + "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
