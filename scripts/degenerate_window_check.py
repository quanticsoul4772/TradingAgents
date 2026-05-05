"""Sanity check: are any of the 8 non-XLF tickers in degenerate-window regimes?

The XLF investigation (claudedocs/xlf-mechanism-2026-05-05.md) showed XLF's
finding-#4 anti-signal is a sample-window artifact: all 10 cached XLF dates
fall in a single regime where (a) prior 30d α has tiny variance and is
near-uniformly negative, (b) bull_keyword_count is uniformly high, making
within-ticker correlation mathematically degenerate.

This script checks the other 8 tickers (AAPL, GOOGL, INTC, JPM, MSFT, NVDA,
XLE, XLK) for the same condition. For each, compute:
  - prior 30d α range (max - min) across all cached market_report dates
  - prior 30d α sign agreement (any prior dates positive? negative? mixed?)
  - bull_keyword_count range
  - degenerate-window flag: range < 10pp OR all-same-sign

If any non-XLF ticker is also degenerate, the headline finding-#4 claim
("9/9 unanimous direction") is overstated and should be re-cast as
"<= 9/9 with some included tickers in degenerate windows".

Writes claudedocs/degenerate-window-check-2026-05-05.md.
Zero LLM cost.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

from tradingagents.signals.cache import query_all
from tradingagents.signals.featurization import bull_keyword_count

TICKERS = ["AAPL", "GOOGL", "INTC", "JPM", "MSFT", "NVDA", "XLE", "XLK", "XLF"]
DEGENERATE_RANGE_PP = 10.0  # prior 30d α range < this in pp = degenerate

OUT_PATH = Path("claudedocs/degenerate-window-check-2026-05-05.md")


def fetch_prior_30d_alpha(ticker: str, trade_date: str) -> float | None:
    try:
        end = datetime.strptime(trade_date, "%Y-%m-%d")
        start = end - timedelta(days=int(30 * 1.5) + 14)
        stock = yf.Ticker(ticker).history(
            start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d")
        )
        spy = yf.Ticker("SPY").history(
            start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d")
        )
        if len(stock) < 31 or len(spy) < 31:
            return None
        s_e = float(stock["Close"].iloc[-1])
        s_s = float(stock["Close"].iloc[-31])
        spy_e = float(spy["Close"].iloc[-1])
        spy_s = float(spy["Close"].iloc[-31])
        return (s_e - s_s) / s_s - (spy_e - spy_s) / spy_s
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    ticker_summaries: list[dict] = []
    for ticker in TICKERS:
        rows = query_all(signal_id="market_report", ticker=ticker)
        priors: list[float] = []
        bulls: list[float] = []
        for r in rows:
            prose = r.get("value") or ""
            if not prose:
                continue
            p = fetch_prior_30d_alpha(ticker, r["date"])
            if p is None:
                continue
            priors.append(p)
            bulls.append(bull_keyword_count(prose))
        if not priors:
            ticker_summaries.append(
                {"ticker": ticker, "n": 0, "degenerate": None, "note": "no prior data"}
            )
            continue
        prior_min = min(priors)
        prior_max = max(priors)
        prior_range_pp = (prior_max - prior_min) * 100
        n_pos = sum(1 for x in priors if x > 0)
        n_neg = sum(1 for x in priors if x < 0)
        bull_min = min(bulls)
        bull_max = max(bulls)
        # degenerate = either range too small OR all same sign
        degenerate = prior_range_pp < DEGENERATE_RANGE_PP or n_pos == 0 or n_neg == 0
        ticker_summaries.append(
            {
                "ticker": ticker,
                "n": len(priors),
                "prior_range_pp": prior_range_pp,
                "prior_min_pct": prior_min * 100,
                "prior_max_pct": prior_max * 100,
                "n_pos": n_pos,
                "n_neg": n_neg,
                "bull_min": bull_min,
                "bull_max": bull_max,
                "degenerate": degenerate,
            }
        )
        flag = "⚠️ DEGENERATE" if degenerate else "OK"
        print(
            f"[{ticker}] n={len(priors)} prior_range={prior_range_pp:.1f}pp "
            f"({prior_min * 100:+.2f}% to {prior_max * 100:+.2f}%) "
            f"pos={n_pos} neg={n_neg} bull=[{bull_min:.0f},{bull_max:.0f}]  {flag}"
        )

    lines: list[str] = []
    lines.append("# Degenerate-window sanity check across all 9 tickers — 2026-05-05\n")
    lines.append(
        "## Question\n\n"
        "The XLF investigation (`claudedocs/xlf-mechanism-2026-05-05.md`) showed XLF's "
        "finding-#4 anti-signal is a sample-window artifact: all 10 XLF cached dates fall in a "
        "single regime where (a) prior 30d α has tiny variance, (b) bull_keyword_count is "
        "uniformly high. This makes the within-ticker correlation mathematically degenerate.\n\n"
        "Do any of the OTHER 8 tickers in the corpus have the same problem? If so, the "
        "headline finding-#4 claim (within-ticker IC -0.489 with 9/9 unanimous direction) is "
        "overstated.\n"
    )
    lines.append("## Method\n")
    lines.append(
        "For each cached market_report row across all 9 tickers, compute prior 30d SPY-relative α. "
        "Flag a ticker as **degenerate** if EITHER:\n"
        f"- Prior 30d α range (max − min) < {DEGENERATE_RANGE_PP}pp, OR\n"
        "- All prior 30d α observations have the same sign (no mix of + and −)\n\n"
        "Either condition means the within-ticker correlation can't separate signal from noise.\n"
    )
    lines.append("## Per-ticker check\n")
    lines.append(
        "| Ticker | n | Prior 30d α range | Prior min | Prior max | n_pos | n_neg | bull_count range | Status |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---|")
    for s in ticker_summaries:
        if s["n"] == 0:
            lines.append(f"| {s['ticker']} | 0 | — | — | — | — | — | — | {s['note']} |")
            continue
        status = "⚠️ DEGENERATE" if s["degenerate"] else "OK"
        lines.append(
            f"| {s['ticker']} | {s['n']} | {s['prior_range_pp']:.1f}pp | "
            f"{s['prior_min_pct']:+.2f}% | {s['prior_max_pct']:+.2f}% | "
            f"{s['n_pos']} | {s['n_neg']} | [{s['bull_min']:.0f}, {s['bull_max']:.0f}] | {status} |"
        )
    lines.append("")

    n_degenerate = sum(1 for s in ticker_summaries if s.get("degenerate"))
    n_ok = sum(1 for s in ticker_summaries if s.get("degenerate") is False)
    lines.append("## Verdict\n")
    if n_degenerate == 1 and ticker_summaries[TICKERS.index("XLF")]["degenerate"]:
        lines.append(
            f"**Only XLF is degenerate. The other {n_ok} tickers all have prior 30d α range "
            f">= {DEGENERATE_RANGE_PP}pp AND mix of positive + negative observations.**\n\n"
            "Finding #4's headline claim (within-ticker IC -0.489, 9/9 unanimous direction) "
            "should be restated as **8/8 unanimous direction on tickers with non-degenerate "
            "windows; the 9th (XLF) is in a degenerate window where the correlation is "
            "mathematically meaningless**. The empirical strength of the finding is unchanged "
            "— if anything, removing the degenerate-window inclusion makes the claim cleaner.\n"
        )
    elif n_degenerate > 1:
        lines.append(
            f"**{n_degenerate} of 9 tickers flagged as degenerate.** Finding #4's headline "
            "9/9 claim needs revision. The `unanimous direction` aggregate is contaminated by "
            "degenerate-window tickers. See per-ticker table for which.\n"
        )
    else:
        lines.append(
            f"**{n_ok} of 9 tickers OK** (prior 30d range >= {DEGENERATE_RANGE_PP}pp + mixed signs). "
            "Finding #4's headline claim is robust to the degenerate-window check.\n"
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
