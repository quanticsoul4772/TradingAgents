"""SC-003 Financials bullish-miss diagnostic — would the spec 003 contrarian
gate have fired on the 5 losing Overweight commits?

SC-003 ANALYSIS.md flagged the Financials sector (n=5 OW, mean α -7.07%) as
the dominant bullish-side miss. The harness's PARAMS.json had
``contrarian_gate_mode = "shadow"``, but the state-log writer didn't persist
the contrarian_gate field (bug noted separately). This script re-derives the
gate annotations offline from the persisted ``market_report`` text using the
same logic the live gate would have applied.

Usage:
    python scripts/sc003_financials_gate_check.py
"""

from __future__ import annotations

import json
from pathlib import Path

from tradingagents.signals.featurization import bull_keyword_count

LOGS_BASE = Path.home() / ".tradingagents" / "logs"
SC003_DATE = "2026-04-03"

# Per SC-003 ANALYSIS.md per-sector breakdown (Financials bullish picks)
FINANCIALS_OW = {
    "JPM": -5.12,
    "BAC": -3.73,
    "WFC": -12.23,
    "GS": -3.74,
    "MA": -10.55,
}


def _load_state(ticker: str, date: str) -> dict | None:
    p = LOGS_BASE / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{date}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _per_ticker_bull_keyword_history(ticker: str, before_date: str) -> list[float]:
    """Return bull_keyword_count values for ALL prior state logs of this ticker
    in chronological order (strict no-look-ahead).
    """
    log_dir = LOGS_BASE / ticker / "TradingAgentsStrategy_logs"
    if not log_dir.exists():
        return []
    out: list[tuple[str, float]] = []
    for p in log_dir.glob("full_states_log_*.json"):
        date = p.stem.removeprefix("full_states_log_")
        if date >= before_date:
            continue
        try:
            state = json.loads(p.read_text(encoding="utf-8"))
            mr = state.get("market_report", "") or ""
            value = float(bull_keyword_count(mr))
            out.append((date, value))
        except (json.JSONDecodeError, OSError, KeyError):
            continue
    out.sort()
    return [v for _, v in out]


def _percentile(history: list[float], current: float) -> float:
    if not history:
        return 0.0
    n_at_or_below = sum(1 for x in history if x <= current)
    return n_at_or_below / len(history) * 100.0


def main():
    print("# SC-003 Financials bullish-miss gate diagnostic")
    print()
    print(f"Date: {SC003_DATE}, gate mode (configured): shadow, threshold: 80th percentile")
    print("History floor (FR-004): N>=20")
    print()
    print(
        "| Ticker | OW α (21d) | bull_keyword_count | history N | percentile | "
        "would_fire (N>=20) | would_fire (N>=5) |"
    )
    print("|---|---|---|---|---|---|---|")

    summary: list[dict] = []
    for ticker, alpha_pct in FINANCIALS_OW.items():
        state = _load_state(ticker, SC003_DATE)
        if state is None:
            print(f"| {ticker} | {alpha_pct:+.2f}% | _no state log_ | — | — | — | — |")
            continue
        market_report = state.get("market_report", "")
        current_value = float(bull_keyword_count(market_report))
        history = _per_ticker_bull_keyword_history(ticker, SC003_DATE)
        n_history = len(history)
        # Use most-recent 20 for percentile baseline (matches live gate semantics)
        baseline = history[-20:] if n_history > 0 else []
        pct = _percentile(baseline, current_value) if baseline else float("nan")
        fire_n20 = (n_history >= 20) and (pct >= 80.0)
        fire_n5 = (n_history >= 5) and (pct >= 80.0)
        print(
            f"| {ticker} | {alpha_pct:+.2f}% | {current_value:.0f} | {n_history} | "
            f"{pct:.0f}% | {'**YES**' if fire_n20 else 'no'} | {'**YES**' if fire_n5 else 'no'} |"
        )
        summary.append(
            {
                "ticker": ticker,
                "alpha_pct": alpha_pct,
                "bull_kw": current_value,
                "n_history": n_history,
                "percentile": pct if pct == pct else None,  # NaN-check
                "fire_n20": fire_n20,
                "fire_n5": fire_n5,
            }
        )

    print()
    print("## Verdict")
    print()
    n_ow = len(summary)
    bullish_alpha_sum_pct = sum(r["alpha_pct"] for r in summary)
    bullish_mean_alpha = bullish_alpha_sum_pct / n_ow if n_ow else 0
    print(f"- Original Financials OW bucket: n={n_ow}, mean α = {bullish_mean_alpha:+.2f}%")

    for floor_name, key in [("N>=20 (production)", "fire_n20"), ("N>=5 (permissive)", "fire_n5")]:
        fired = [r for r in summary if r[key]]
        survived = [r for r in summary if not r[key]]
        n_fired = len(fired)
        if survived:
            survived_mean = sum(r["alpha_pct"] for r in survived) / len(survived)
        else:
            survived_mean = float("nan")
        # Δα contribution if active mode had been on:
        # fired commits → Hold (assume 0% α contribution)
        # survived → unchanged
        delta_pp = (survived_mean - bullish_mean_alpha) if survived else 0
        print(
            f"- At floor {floor_name}: gate would have fired on **{n_fired}/{n_ow}** commits; "
            f"survivors mean α = {survived_mean:+.2f}%; "
            f"Δα improvement = **{delta_pp:+.2f}pp**"
        )
    print()
    print(
        "Note: Δα improvement above is per-commit-mean. The retrospective's "
        "earlier corpus-level +6.46% Δα at 21d (claudedocs/contrarian-gate-"
        "retrospective-2026-05-05.md) used cumulative-position-weighted α, "
        "different denominator. The two numbers are not directly comparable."
    )


if __name__ == "__main__":
    main()
