"""XLF-specific mechanism investigation.

XLF is the one ticker (of 9) where finding #4's anti-signal does NOT fit
the recency mechanism documented in claudedocs/finding4-mechanism-2026-05-05.md:

  Ticker | Prior 30d IC | Future 90d IC | Mechanism active?
  ----------------------------------------------------------------
  XLF    | -0.27        | -0.58         | ❌ no recency signal

For 8 of 9 tickers, bull_keyword_count tracks prior strength (positive
prior IC) and that strength mean-reverts (negative future IC). XLF still
shows the future anti-signal but its bull_keyword_count is NEGATIVELY
correlated with prior strength — so something else is driving the
bullish prose density on this ticker.

Hypotheses:
  H1. Macro-driven: market analyst gets bullish on XLF when macro factors
      (yield curve, rates, financial-sector tailwinds) look favorable —
      independent of recent XLF price action. Mean-reversion still operates
      but on a different setup mechanism.
  H2. Bigram pollution: the bull_keyword set isn't well-calibrated for
      financial-sector prose. "strong" + "earnings" might appear in XLF
      prose for sector-specific reasons that don't correspond to recent
      strength.
  H3. Small n + bigger noise: XLF has only n=10 cached rows; the per-
      ticker IC could be noisier than the others.
  H4. Sample-window artifact: XLF's 10 dates might cluster in a single
      regime where the prose pattern is structurally different.

This script:
  1. Dumps every XLF market_report row's (bull_keyword_count, prior 30d α,
     future 90d α) so we can eyeball the relationship
  2. For each high-count XLF row, lists which bull keywords actually fire
  3. Compares the same view for AAPL (a strong-mechanism ticker) for contrast
  4. Pulls the cached macro signal (VIX) at each XLF date if available
  5. Notes whether dates cluster in time

Writes claudedocs/xlf-mechanism-2026-05-05.md.
Zero LLM cost.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

from tradingagents.signals.cache import query_all
from tradingagents.signals.featurization import _BULL_KEYWORDS, _word_iter, bull_keyword_count

OUT_PATH = Path("claudedocs/xlf-mechanism-2026-05-05.md")


def fetch_prior_alpha(ticker: str, trade_date: str, prior_days: int) -> float | None:
    try:
        end = datetime.strptime(trade_date, "%Y-%m-%d")
        start = end - timedelta(days=int(prior_days * 1.5) + 14)
        stock = yf.Ticker(ticker).history(
            start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d")
        )
        spy = yf.Ticker("SPY").history(
            start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d")
        )
        if len(stock) < prior_days + 1 or len(spy) < prior_days + 1:
            return None
        stock_end = float(stock["Close"].iloc[-1])
        stock_start = float(stock["Close"].iloc[-(prior_days + 1)])
        spy_end = float(spy["Close"].iloc[-1])
        spy_start = float(spy["Close"].iloc[-(prior_days + 1)])
        return (stock_end - stock_start) / stock_start - (spy_end - spy_start) / spy_start
    except Exception:  # noqa: BLE001
        return None


def fetch_future_alpha(ticker: str, trade_date: str, days: int = 90) -> float | None:
    try:
        start = datetime.strptime(trade_date, "%Y-%m-%d")
        end = start + timedelta(days=int(days * 1.5) + 7)
        stock = yf.Ticker(ticker).history(start=trade_date, end=end.strftime("%Y-%m-%d"))
        spy = yf.Ticker("SPY").history(start=trade_date, end=end.strftime("%Y-%m-%d"))
        if len(stock) < days + 1 or len(spy) < days + 1:
            return None
        return (float(stock["Close"].iloc[days]) - float(stock["Close"].iloc[0])) / float(
            stock["Close"].iloc[0]
        ) - (float(spy["Close"].iloc[days]) - float(spy["Close"].iloc[0])) / float(
            spy["Close"].iloc[0]
        )
    except Exception:  # noqa: BLE001
        return None


def which_bull_keywords_fire(text: str) -> Counter:
    """Return Counter of which bull keywords appear in text."""
    fired: Counter = Counter()
    for word in _word_iter(text or ""):
        if word in _BULL_KEYWORDS:
            fired[word] += 1
    return fired


def collect_ticker_rows(ticker: str) -> list[dict]:
    """Pull XLF (or any ticker) market_report rows + compute everything per row."""
    all_rows = query_all(signal_id="market_report", ticker=ticker)
    out = []
    for r in all_rows:
        prose = r.get("value") or ""
        if not prose:
            continue
        date = r["date"]
        bull_count = bull_keyword_count(prose)
        prior_30 = fetch_prior_alpha(ticker, date, 30)
        prior_60 = fetch_prior_alpha(ticker, date, 60)
        prior_90 = fetch_prior_alpha(ticker, date, 90)
        future_90 = fetch_future_alpha(ticker, date, 90)
        keywords_fired = which_bull_keywords_fire(prose)
        out.append(
            {
                "date": date,
                "bull_count": bull_count,
                "prior_30d_alpha": prior_30,
                "prior_60d_alpha": prior_60,
                "prior_90d_alpha": prior_90,
                "future_90d_alpha": future_90,
                "keywords_fired": dict(keywords_fired),
                "prose_len": len(prose),
            }
        )
    return sorted(out, key=lambda r: r["date"])


def render_ticker_section(ticker: str, rows: list[dict]) -> list[str]:
    lines = [f"## {ticker} ({len(rows)} cached market_report rows)\n"]
    if not rows:
        lines.append("(no cached rows)\n")
        return lines

    # Date range
    dates = [r["date"] for r in rows]
    lines.append(f"Date range: {min(dates)} → {max(dates)}\n")

    # Per-row table
    lines.append("### Per-row data\n")
    lines.append(
        "| Date | bull_count | prior_30d α | prior_60d α | prior_90d α | future_90d α | keywords fired |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    for r in rows:

        def _fmt_alpha(a):
            return f"{a * 100:+.2f}%" if a is not None else "—"

        kw_str = (
            ", ".join(
                f"`{k}`×{v}"
                for k, v in sorted(r["keywords_fired"].items(), key=lambda x: -x[1])[:6]
            )
            or "(none)"
        )
        lines.append(
            f"| {r['date']} | {r['bull_count']:.0f} | {_fmt_alpha(r['prior_30d_alpha'])} | "
            f"{_fmt_alpha(r['prior_60d_alpha'])} | {_fmt_alpha(r['prior_90d_alpha'])} | "
            f"{_fmt_alpha(r['future_90d_alpha'])} | {kw_str} |"
        )
    lines.append("")

    # Aggregate keyword counts across all rows
    overall: Counter = Counter()
    for r in rows:
        for k, v in r["keywords_fired"].items():
            overall[k] += v
    lines.append("### Aggregate bull_keyword usage across all rows\n")
    lines.append("| Keyword | Total occurrences |")
    lines.append("|---|---:|")
    for kw, cnt in overall.most_common():
        lines.append(f"| `{kw}` | {cnt} |")
    lines.append("")

    return lines


def main() -> int:
    print("[load] XLF rows...")
    xlf_rows = collect_ticker_rows("XLF")
    print(f"[load] XLF: {len(xlf_rows)} rows")
    print("[load] AAPL rows for contrast (strong-mechanism ticker)...")
    aapl_rows = collect_ticker_rows("AAPL")
    print(f"[load] AAPL: {len(aapl_rows)} rows")

    lines = []
    lines.append("# XLF mechanism investigation — 2026-05-05\n")
    lines.append(
        "## Question\n\n"
        "XLF is the one ticker (of 9) where finding #4's bull_keyword_count anti-signal "
        "(future 90d IC -0.58) does NOT fit the recency mechanism documented in "
        "`claudedocs/finding4-mechanism-2026-05-05.md`. While 8 of 9 tickers show a positive "
        "prior 30d IC (analyst's bull keywords track recent strength), XLF shows -0.27 — "
        "**the bullish prose density on XLF is NEGATIVELY correlated with recent strength**.\n\n"
        "What's different about XLF? Four hypotheses:\n"
        "- **H1 macro-driven**: bullish XLF prose follows macro / sector catalysts (yield curve, "
        "rate cycle, financial-sector tailwinds), not recent price action\n"
        "- **H2 bigram pollution**: the bull_keyword set isn't well-calibrated for financial-sector "
        "prose (e.g., 'strong' + 'earnings' fire for sector-specific reasons unrelated to recent strength)\n"
        "- **H3 noise**: XLF has only n=10 cached rows; per-ticker IC noisier than the others\n"
        "- **H4 sample-window artifact**: XLF's 10 dates cluster in a single regime with "
        "structurally different prose patterns\n"
    )
    lines.append("## Method\n")
    lines.append(
        "1. Dump every XLF market_report row's (bull_keyword_count, prior 30d/60d/90d α, future 90d α)\n"
        "2. For each XLF row, list which specific bull keywords fired and how many times\n"
        "3. Same view for AAPL (a strong-mechanism ticker, prior 30d IC +0.33) for direct contrast\n"
        "4. Aggregate keyword usage across rows to spot pattern differences\n"
    )
    lines.extend(render_ticker_section("XLF", xlf_rows))
    lines.extend(render_ticker_section("AAPL", aapl_rows))
    lines.append("## Verdict\n")
    lines.append("(Verdict written by hand after reviewing the per-row tables.)\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
