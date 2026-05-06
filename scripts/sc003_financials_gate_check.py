"""SC-003 Financials bullish-miss diagnostic — would the spec 003 contrarian
gate have fired on the 5 losing Overweight commits?

SC-003 ANALYSIS.md flagged the Financials sector (n=5 OW, mean α -7.07%) as
the dominant bullish-side miss. The harness's PARAMS.json had
``contrarian_gate_mode = "shadow"``, but the state-log writer didn't persist
the contrarian_gate field (bug noted separately). This script re-derives the
gate annotations offline from the persisted ``market_report`` text using the
same logic the live gate would have applied.

Spec 003.5 (specs/003-sector-baseline-gate/) added a sector-level fallback
baseline. The ``--sector-fallback`` / ``--no-sector-fallback`` flags simulate
both branches so operators can compare cold-start coverage with vs without
the fallback.

Usage:
    python scripts/sc003_financials_gate_check.py
    python scripts/sc003_financials_gate_check.py --no-sector-fallback
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add repo root to sys.path so the script can import tradingagents/* modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.signals.featurization import bull_keyword_count  # noqa: E402

LOGS_BASE = Path.home() / ".tradingagents" / "logs"
SECTORS_CACHE_PATH = Path.home() / ".tradingagents" / "paper" / "sectors.json"
SC003_DATE = "2026-04-03"

# Per SC-003 ANALYSIS.md per-sector breakdown (Financials bullish picks)
FINANCIALS_OW = {
    "JPM": -5.12,
    "BAC": -3.73,
    "WFC": -12.23,
    "GS": -3.74,
    "MA": -10.55,
}

PER_TICKER_FLOOR_STRICT = 20  # FR-004 production
PER_TICKER_FLOOR_PERMISSIVE = 5  # legacy / pre-FR-004
SECTOR_FLOOR = 20  # spec 003.5 default
PERCENTILE_THRESHOLD = 80


def _load_state(ticker: str, date: str) -> dict | None:
    p = LOGS_BASE / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{date}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _per_ticker_bull_keyword_history(ticker: str, before_date: str) -> list[float]:
    """Return bull_keyword_count values for ALL prior state logs of this ticker
    in chronological order (strict no-look-ahead)."""
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


def _sector_bull_keyword_history(
    target_sector: str,
    before_date: str,
    sector_lookup,
) -> tuple[list[float], dict[str, int]]:
    """Aggregate bull_keyword_count history across same-sector tickers in
    LOGS_BASE strictly before before_date. Mirrors spec 003.5's
    aggregate_sector_pool but using state logs (the data SC-003 actually
    populated) instead of the signal cache."""
    if not LOGS_BASE.exists():
        return [], {}
    if not target_sector or target_sector == "Unknown":
        return [], {}
    pooled: list[float] = []
    contributors: dict[str, int] = {}
    for ticker_dir in sorted(LOGS_BASE.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        try:
            sector = sector_lookup(ticker)
        except Exception:
            continue
        if sector != target_sector:
            continue
        values = _per_ticker_bull_keyword_history(ticker, before_date)
        for v in values:
            pooled.append(v)
        if values:
            contributors[ticker] = len(values)
    return pooled, contributors


def _percentile(history: list[float], current: float) -> float:
    if not history:
        return 0.0
    n_at_or_below = sum(1 for x in history if x <= current)
    return n_at_or_below / len(history) * 100.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sector-fallback",
        dest="sector_fallback",
        action="store_true",
        default=True,
        help="Enable spec 003.5 sector-level fallback when per-ticker history is below floor (default).",
    )
    parser.add_argument(
        "--no-sector-fallback",
        dest="sector_fallback",
        action="store_false",
        help="Disable sector fallback (spec 003 baseline behavior; cold-start tickers cannot fire).",
    )
    args = parser.parse_args()

    # Sector lookup via the spec 002 paper-harness cache. Falls back to a
    # hardcoded mapping if the cache lookup fails (e.g. yfinance unavailable).
    HARDCODED_FINANCIALS = {"JPM", "BAC", "WFC", "GS", "MA", "MS", "V", "AXP"}

    def sector_lookup(ticker: str) -> str:
        try:
            from tradingagents.paper.sectors import get_sector

            return get_sector(ticker, SECTORS_CACHE_PATH)
        except Exception:
            return "Financial Services" if ticker in HARDCODED_FINANCIALS else "Unknown"

    print("# SC-003 Financials bullish-miss gate diagnostic")
    print()
    print(
        f"Date: {SC003_DATE}, threshold: {PERCENTILE_THRESHOLD}th percentile, "
        f"per-ticker floor: {PER_TICKER_FLOOR_STRICT} (FR-004), sector floor: {SECTOR_FLOOR}"
    )
    print(f"Sector fallback (spec 003.5): **{'ENABLED' if args.sector_fallback else 'DISABLED'}**")
    print()

    # Pre-compute the Financials sector pool (same for all 5 tickers; depends only on before_date).
    target_sector = "Financial Services"  # yfinance's canonical name; may also be "Financials"
    sector_pool, sector_contribs = _sector_bull_keyword_history(
        target_sector, SC003_DATE, sector_lookup
    )
    if not sector_pool:
        # Fall back to "Financials" naming
        target_sector = "Financials"
        sector_pool, sector_contribs = _sector_bull_keyword_history(
            target_sector, SC003_DATE, sector_lookup
        )

    print(
        f"Sector pool ({target_sector}): N={len(sector_pool)}, "
        f"contributors={dict(sorted(sector_contribs.items()))}"
    )
    print()
    print(
        "| Ticker | OW α (21d) | bull_kw | per-ticker N | per-ticker pct | "
        "sector N | sector pct | gate_baseline | would_fire |"
    )
    print("|---|---|---|---|---|---|---|---|---|")

    summary: list[dict] = []
    for ticker, alpha_pct in FINANCIALS_OW.items():
        state = _load_state(ticker, SC003_DATE)
        if state is None:
            print(f"| {ticker} | {alpha_pct:+.2f}% | _no state log_ | — | — | — | — | none | no |")
            continue
        market_report = state.get("market_report", "")
        current_value = float(bull_keyword_count(market_report))
        per_ticker_history = _per_ticker_bull_keyword_history(ticker, SC003_DATE)
        n_per_ticker = len(per_ticker_history)

        per_ticker_pct = (
            _percentile(per_ticker_history, current_value) if per_ticker_history else None
        )
        sector_pct = _percentile(sector_pool, current_value) if sector_pool else None

        # Apply fallback ladder per spec 003.5
        gate_baseline = "none"
        decision_pct = None
        if n_per_ticker >= PER_TICKER_FLOOR_STRICT:
            gate_baseline = "per_ticker"
            decision_pct = per_ticker_pct
        elif args.sector_fallback and len(sector_pool) >= SECTOR_FLOOR:
            gate_baseline = "sector"
            decision_pct = sector_pct

        would_fire = decision_pct is not None and decision_pct >= PERCENTILE_THRESHOLD

        per_ticker_pct_str = f"{per_ticker_pct:.0f}%" if per_ticker_pct is not None else "n/a"
        sector_pct_str = f"{sector_pct:.0f}%" if sector_pct is not None else "n/a"
        print(
            f"| {ticker} | {alpha_pct:+.2f}% | {current_value:.0f} | "
            f"{n_per_ticker} | {per_ticker_pct_str} | "
            f"{len(sector_pool)} | {sector_pct_str} | "
            f"{gate_baseline} | {'**YES**' if would_fire else 'no'} |"
        )
        summary.append(
            {
                "ticker": ticker,
                "alpha_pct": alpha_pct,
                "bull_kw": current_value,
                "n_per_ticker": n_per_ticker,
                "n_sector": len(sector_pool),
                "gate_baseline": gate_baseline,
                "would_fire": would_fire,
                "per_ticker_pct": per_ticker_pct,
                "sector_pct": sector_pct,
            }
        )

    # Verdict
    print()
    print("## Verdict")
    print()
    n_ow = len(summary)
    bullish_alpha_sum = sum(r["alpha_pct"] for r in summary)
    bullish_mean = bullish_alpha_sum / n_ow if n_ow else 0
    fired = [r for r in summary if r["would_fire"]]
    survived = [r for r in summary if not r["would_fire"]]
    n_fired = len(fired)
    survived_mean = (
        (sum(r["alpha_pct"] for r in survived) / len(survived)) if survived else float("nan")
    )
    delta_pp = (survived_mean - bullish_mean) if survived else 0

    print(f"- Original Financials OW bucket: n={n_ow}, mean α = {bullish_mean:+.2f}%")
    print(
        f"- Gate would fire on **{n_fired}/{n_ow}** commits "
        f"(sector_fallback={'ON' if args.sector_fallback else 'OFF'})"
    )
    print(f"- Survivors mean α = {survived_mean:+.2f}%; Δα improvement = **{delta_pp:+.2f}pp**")
    print()
    by_baseline = {"per_ticker": 0, "sector": 0, "none": 0}
    for r in summary:
        by_baseline[r["gate_baseline"]] += 1
    print(
        f"- gate_baseline counts: per_ticker={by_baseline['per_ticker']}, "
        f"sector={by_baseline['sector']}, none={by_baseline['none']}"
    )


if __name__ == "__main__":
    main()
