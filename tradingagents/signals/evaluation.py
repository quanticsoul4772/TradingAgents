"""Spec 002 Phase 1 evaluation primitives.

Math + per-signal pipeline for ``scripts/evaluate_signals.py``. Lives in the
package (rather than the script) so unit tests can import it without
bundling scripts/ into sys.path.

MVP scope:
- Coverage stats per signal (n cached, unique tickers, unique dates, mean
  value length).
- Spearman IC + directional hit-rate, computed only for signals whose
  values can be coerced to a number. Phase 1 MVP supports only
  ``final_trade_decision`` (parsed 5-tier rating); prose signals
  (market_report, news_report, etc.) report coverage stats only.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone

from tradingagents.agents.utils.rating import parse_rating
from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.signals.registry import load_registry

# Map 5-tier rating to a signed score so we can compute IC.
_RATING_SCORE = {
    "Buy": 2,
    "Overweight": 1,
    "Hold": 0,
    "Underweight": -1,
    "Sell": -2,
}


def _compute_alpha(ticker: str, date: str, holding_days: int) -> float | None:
    """Return realized alpha (ticker - SPY) over `holding_days`. None if data missing."""
    _, alpha, _ = fetch_returns(ticker, date, holding_days=holding_days)
    return alpha


def _spearman_ic(pairs: list[tuple[float, float]]) -> float | None:
    """Spearman rank correlation. Returns None if n < 3 or no variance."""
    if len(pairs) < 3:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None

    def _ranks(values: list[float]) -> list[float]:
        sorted_idx = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(values):
            j = i
            while j + 1 < len(values) and values[sorted_idx[j + 1]] == values[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[sorted_idx[k]] = avg_rank
            i = j + 1
        return ranks

    rx = _ranks(xs)
    ry = _ranks(ys)
    mean_rx = statistics.fmean(rx)
    mean_ry = statistics.fmean(ry)
    num = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry, strict=True))
    den_x = sum((a - mean_rx) ** 2 for a in rx) ** 0.5
    den_y = sum((b - mean_ry) ** 2 for b in ry) ** 0.5
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def _hit_rate(pairs: list[tuple[int, float]]) -> float | None:
    """Fraction of (signed_signal, alpha) pairs where direction agrees.

    Signal score and alpha must have the same sign (both positive or both
    negative). Hold (signal == 0) only counts as hit when |alpha| < 0.5%.
    """
    if not pairs:
        return None
    hits = 0
    for sig, alpha in pairs:
        if sig > 0 and alpha > 0:
            hits += 1
        elif sig < 0 and alpha < 0:
            hits += 1
        elif sig == 0 and abs(alpha) < 0.5:
            hits += 1
    return hits / len(pairs)


def _coverage_stats(rows: list[dict]) -> dict:
    """Coverage diagnostic for any signal."""
    if not rows:
        return {"n": 0, "tickers": 0, "dates": 0, "mean_len": 0}
    tickers = {r["ticker"] for r in rows}
    dates = {r["date"] for r in rows}
    lengths = [len(r["value"] or "") for r in rows]
    return {
        "n": len(rows),
        "tickers": len(tickers),
        "dates": len(dates),
        "mean_len": int(statistics.fmean(lengths)) if lengths else 0,
    }


def _evaluate_signal(
    signal_id: str,
    rows: list[dict],
    horizon_days: int,
) -> dict:
    """Per-signal evaluation: coverage + (where computable) IC + hit rate."""
    cov = _coverage_stats(rows)
    result = {"signal_id": signal_id, **cov, "ic": None, "hit_rate": None, "n_eval": 0}

    # IC + hit rate only computable for signals we can map to a number.
    # MVP: final_trade_decision (5-tier rating) is the only such signal.
    if signal_id != "final_trade_decision":
        return result

    pairs_ic: list[tuple[float, float]] = []
    pairs_hit: list[tuple[int, float]] = []
    for r in rows:
        rating = parse_rating(r["value"] or "")
        score = _RATING_SCORE.get(rating)
        if score is None:
            continue
        alpha = _compute_alpha(r["ticker"], r["date"], holding_days=horizon_days)
        if alpha is None:
            continue
        pairs_ic.append((float(score), float(alpha)))
        pairs_hit.append((score, alpha))

    result["n_eval"] = len(pairs_ic)
    result["ic"] = _spearman_ic(pairs_ic)
    result["hit_rate"] = _hit_rate(pairs_hit)
    return result


def render_report(
    rows_by_signal: dict[str, list[dict]],
    evaluations: list[dict],
    horizon_days: int,
) -> str:
    """Generate the Phase 1 markdown evaluation report."""
    lines: list[str] = []
    lines.append("# Signal Evaluation Report (spec 002 Phase 1)")
    lines.append("")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}._")
    lines.append("")
    lines.append(
        f"Horizon: **{horizon_days} days**. "
        f"Total cached rows analyzed: **{sum(len(rs) for rs in rows_by_signal.values())}**. "
        f"Signals evaluated: **{len(evaluations)}**."
    )
    lines.append("")
    lines.append("## Coverage + IC + Hit Rate per signal")
    lines.append("")
    lines.append(
        "| Signal | n cached | Tickers | Dates | Mean value length | n eval | IC | Hit rate |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for ev in sorted(evaluations, key=lambda x: x["n"], reverse=True):
        ic_str = f"{ev['ic']:+.3f}" if ev["ic"] is not None else "—"
        hit_str = f"{ev['hit_rate']:.1%}" if ev["hit_rate"] is not None else "—"
        lines.append(
            f"| `{ev['signal_id']}` | {ev['n']} | {ev['tickers']} | {ev['dates']} | "
            f"{ev['mean_len']} | {ev['n_eval']} | {ic_str} | {hit_str} |"
        )
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- **n eval** is the count of (ticker, date) pairs where both a numeric "
        "signal value AND a realized forward alpha are available. Smaller than "
        "n cached when the trade date is too recent for forward-return data."
    )
    lines.append(
        "- **IC** = Spearman rank correlation between signal numeric value and "
        f"realized {horizon_days}-day alpha. Only computable for signals whose "
        "values can be coerced to numbers. Phase 1 MVP supports only "
        "`final_trade_decision` (parsed 5-tier rating); prose signals report "
        "coverage stats only."
    )
    lines.append(
        "- **Hit rate** = fraction of pairs where signal direction (bullish / "
        "neutral / bearish) matches realized alpha sign. Hold counts as hit "
        "when |α| < 0.5%."
    )
    lines.append("")
    lines.append("## What this report does NOT include (deferred to Phase 1.5+)")
    lines.append("")
    lines.append(
        "- Featurization of prose signals (would unlock IC for market_report, "
        "news_report, fundamentals_report, investment_plan, sentiment_report)\n"
        "- Quintile gradient (top vs bottom quintile alpha spread)\n"
        "- Info ratio (IC / std)\n"
        "- Per-horizon comparison (5d / 10d / 21d)\n"
        "- Cross-signal correlation matrix\n"
        "- Auto-promote / auto-demote state transitions"
    )
    lines.append("")
    lines.append("## Source data")
    lines.append("")
    lines.append(
        f"- Cache: `~/.tradingagents/signals/cache.db` "
        f"({sum(len(rs) for rs in rows_by_signal.values())} rows)\n"
        f"- Registry: `~/.tradingagents/signals/registry.jsonl` "
        f"({len(load_registry())} signals)"
    )
    lines.append("")

    return "\n".join(lines)
