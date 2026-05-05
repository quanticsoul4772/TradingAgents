"""Spec 003 retrospective: simulate the contrarian gate offline against
the historical state-log corpus.

For each historical (ticker, date) propagate in ~/.tradingagents/logs/states/,
re-compute what the contrarian gate would have decided:
  - Pull the propagate's market_report prose + final_trade_decision rating
  - Compute the bull_keyword_count for THIS date
  - Build a per-ticker history of bull_keyword_counts using ONLY dates
    strictly EARLIER than this date (no look-ahead)
  - Compute the percentile of THIS date's count vs that strict-prior history
  - would_fire = (percentile >= threshold) AND (rating in {Buy, Overweight})
  - Compute realized forward α at 21d and 90d
  - Stratify: gate-fired vs gate-not-fired buckets

Output: claudedocs/contrarian-gate-retrospective-2026-05-05.md.

Same measurement as spec 003 SC-002 ("would the gate fire on the right
commits and improve mean α?") but performed offline against the corpus
that already exists. No new LLM cost.

Caveats:
- Offline simulation can use fewer historical points than a live N=20 floor
  would; we report fire rates with both N>=5 and N>=20 floors so the result
  is interpretable at both thresholds.
- Earliest dates per ticker have very little prior history → percentile is
  undefined or noisy. We flag those rows separately.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tradingagents.agents.utils.rating import parse_rating
from tradingagents.graph.trading_graph import fetch_returns
from tradingagents.signals.contrarian_gate import _percentile_of_value
from tradingagents.signals.featurization import bull_keyword_count

LOGS_ROOT = Path.home() / ".tradingagents" / "logs"
OUT_PATH = Path("claudedocs/contrarian-gate-retrospective-2026-05-05.md")
THRESHOLD = 80
HISTORY_FLOORS = (5, 20)
HORIZONS = (21, 90)
BULLISH_RATINGS = {"Buy", "Overweight"}


def _load_all_state_logs() -> list[dict]:
    """Load every full_states_log_*.json under LOGS_ROOT.

    Returns list of {ticker, date, market_report, rating, raw_path}.
    """
    out = []
    for path in sorted(LOGS_ROOT.rglob("full_states_log_*.json")):
        try:
            with path.open(encoding="utf-8") as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        ticker = state.get("company_of_interest") or path.parent.parent.name
        date = state.get("trade_date")
        market_report = state.get("market_report") or ""
        ftd = state.get("final_trade_decision") or ""
        if not date or not market_report or not ftd:
            continue
        rating = parse_rating(ftd)
        out.append(
            {
                "ticker": ticker,
                "date": str(date)[:10],
                "market_report": market_report,
                "rating": rating,
                "raw_path": str(path),
            }
        )
    return out


def _simulate_gate(rows: list[dict], history_floor: int, threshold: int) -> list[dict]:
    """For each (ticker, date) row, compute would_fire using only strict-prior
    history of the same ticker. Returns enriched rows with gate fields."""
    # Group by ticker, sort by date asc
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_ticker[r["ticker"]].append(r)
    for ticker in by_ticker:
        by_ticker[ticker].sort(key=lambda r: r["date"])

    enriched = []
    for ticker_rows in by_ticker.values():
        # Pre-compute bull_keyword_counts for this ticker
        for r in ticker_rows:
            r["bull_count"] = bull_keyword_count(r["market_report"])
        # For each row, history = previous rows
        for i, r in enumerate(ticker_rows):
            history = ticker_rows[:i]  # strict prior, no look-ahead
            n_history = len(history)
            if n_history < history_floor:
                gate_skipped = "insufficient_history"
                percentile = None
                would_fire = None
            else:
                history_counts = [h["bull_count"] for h in history[-history_floor:]]
                # Mirror live gate: take most-recent N (not all available)
                history_counts = [h["bull_count"] for h in history[-20:]]
                percentile = _percentile_of_value(history_counts, r["bull_count"])
                threshold_crossed = percentile >= threshold
                would_fire = threshold_crossed and (r["rating"] in BULLISH_RATINGS)
                gate_skipped = None
            enriched.append(
                {
                    **r,
                    "n_history": n_history,
                    "percentile": percentile,
                    "would_fire": would_fire,
                    "gate_skipped": gate_skipped,
                }
            )
    return enriched


def _enrich_with_alpha(rows: list[dict]) -> None:
    for r in rows:
        for h in HORIZONS:
            _, alpha, actual = fetch_returns(r["ticker"], r["date"], holding_days=h)
            r[f"alpha_{h}d"] = alpha
            r[f"actual_days_{h}d"] = actual


def _summary_table_lines(rows: list[dict], horizon: int, history_floor: int) -> list[str]:
    """Build the bucketed-α summary lines."""
    eligible = [
        r for r in rows if r["gate_skipped"] is None and r.get(f"alpha_{horizon}d") is not None
    ]
    fired = [r for r in eligible if r["would_fire"] is True]
    nofire_bullish = [
        r for r in eligible if r["would_fire"] is False and r["rating"] in BULLISH_RATINGS
    ]
    other = [r for r in eligible if r["rating"] not in BULLISH_RATINGS]

    lines = [
        f"### α @ {horizon}d (history floor N>={history_floor})\n",
        "| Bucket | n | Mean α | Median α | Hit rate (α>0) |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, bucket in [
        ("Gate would fire (Buy/OW + percentile>=80)", fired),
        ("Buy/OW where gate would NOT fire", nofire_bullish),
        ("Hold/UW/Sell (not in gate scope)", other),
    ]:
        if not bucket:
            lines.append(f"| {label} | 0 | — | — | — |")
            continue
        alphas = [r[f"alpha_{horizon}d"] for r in bucket]
        mean_a = statistics.mean(alphas)
        median_a = statistics.median(alphas)
        hit = sum(1 for a in alphas if a > 0) / len(alphas)
        lines.append(
            f"| {label} | {len(bucket)} | {mean_a * 100:+.2f}% | "
            f"{median_a * 100:+.2f}% | {hit:.1%} |"
        )
    lines.append("")

    # Active-mode delta projection: if gate had been ON, fired rows would
    # have been Hold (contribution 0). Compute total Δα.
    # Direction: Buy/OW = +1; α contribution = direction × α; Hold = 0.
    # Pre-gate contribution: +1 × α. Post-gate: 0. Δ = -α.
    # Cumulative Δα across all fired rows = -sum(α_fired).
    if fired:
        total_alpha_fired = sum(r[f"alpha_{horizon}d"] for r in fired)
        cumulative_delta = -total_alpha_fired
        lines.append(
            f"**If active mode had been ON**: gate would have fired on {len(fired)} bullish "
            f"commits, downgrading them to Hold. Cumulative Δα contribution = "
            f"{cumulative_delta * 100:+.2f}% (positive = gate would have helped; negative = "
            f"gate would have hurt by suppressing winning bullish commits).\n"
        )
    return lines


def _per_ticker_fire_rate_table(rows: list[dict], history_floor: int) -> list[str]:
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["gate_skipped"] is not None:
            continue
        by_ticker[r["ticker"]].append(r)
    lines = [
        f"### Per-ticker gate-fire rate (history floor N>={history_floor})\n",
        "| Ticker | n eligible | n bullish (Buy/OW) | n would_fire | fire rate over bullish |",
        "|---|---:|---:|---:|---:|",
    ]
    for ticker in sorted(by_ticker):
        bucket = by_ticker[ticker]
        n_total = len(bucket)
        bullish = [r for r in bucket if r["rating"] in BULLISH_RATINGS]
        fired = [r for r in bullish if r["would_fire"]]
        rate = (len(fired) / len(bullish) * 100) if bullish else 0
        lines.append(f"| {ticker} | {n_total} | {len(bullish)} | {len(fired)} | {rate:.1f}% |")
    lines.append("")
    return lines


def main() -> int:
    print(f"[load] {LOGS_ROOT}")
    rows = _load_all_state_logs()
    print(f"[load] {len(rows)} state logs across {len({r['ticker'] for r in rows})} tickers")
    if not rows:
        print("[error] no state logs found")
        return 1

    # Compute alpha once (reused across both history-floor variants)
    print("[fetch] computing 21d + 90d alpha for each propagate...")
    _enrich_with_alpha(rows)
    n_resolved_21 = sum(1 for r in rows if r.get("alpha_21d") is not None)
    n_resolved_90 = sum(1 for r in rows if r.get("alpha_90d") is not None)
    print(f"[fetch] resolved: 21d={n_resolved_21}/{len(rows)}, 90d={n_resolved_90}/{len(rows)}")

    # Run simulation at both history floors
    sim_results: dict[int, list[dict]] = {}
    for floor in HISTORY_FLOORS:
        sim_results[floor] = _simulate_gate(rows, history_floor=floor, threshold=THRESHOLD)
        n_eligible = sum(1 for r in sim_results[floor] if r["gate_skipped"] is None)
        n_fired = sum(1 for r in sim_results[floor] if r.get("would_fire") is True)
        print(f"[sim] floor=N>={floor}: {n_eligible}/{len(rows)} eligible, {n_fired} would_fire")

    # Render report
    lines: list[str] = []
    lines.append(f"# Contrarian gate retrospective — {datetime.utcnow().date().isoformat()}\n")
    lines.append(
        "## Question\n\n"
        "Spec 003 SC-002 asks: across N>=30 propagates, does the contrarian gate "
        "reproduce finding #4's within-ticker pattern in fresh data + improve mean α "
        "by suppressing bullish commits at high bull_keyword_count percentiles?\n\n"
        "This script answers the same question OFFLINE against the existing 156 historical "
        "propagates in ~/.tradingagents/logs/states/. No new LLM cost.\n\n"
        "**Key methodological constraint**: strict no-look-ahead. For propagate at (ticker, "
        "date), the percentile baseline uses ONLY prior dates of the same ticker, never "
        "data from after this date. Otherwise the gate would have unfair foresight that "
        "wouldn't exist in production.\n"
    )
    lines.append("## Method\n")
    lines.append(
        f"1. Load all {len(rows)} state logs from `~/.tradingagents/logs/states/`\n"
        "2. For each, compute `bull_keyword_count(market_report)` and parse the rating\n"
        "3. Per ticker, sort by date ascending\n"
        "4. For each (ticker, date) row at position i: history = first i rows of that "
        "ticker (strict prior). Take most-recent 20 of those as the percentile baseline.\n"
        "5. Compute percentile of current bull_count vs baseline; would_fire = "
        "(percentile >= 80) AND (rating in {Buy, Overweight})\n"
        f"6. Fetch realized 21d + 90d α (post-buffer-fix `fetch_returns`)\n"
        "7. Stratify α by would_fire bucket; project active-mode Δα\n"
        f"8. Run at two history floors (N>={HISTORY_FLOORS[0]} permissive, "
        f"N>={HISTORY_FLOORS[1]} matches live gate FR-004)\n"
    )

    for floor in HISTORY_FLOORS:
        lines.append(f"## History floor: N>={floor}\n")
        lines.extend(_per_ticker_fire_rate_table(sim_results[floor], floor))
        for horizon in HORIZONS:
            lines.extend(_summary_table_lines(sim_results[floor], horizon, floor))

    lines.append("## Verdict\n")
    lines.append("(Verdict written by hand after reviewing tables.)\n")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[out] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
