"""Spec 003 contrarian gate threshold sweep.

Re-evaluates the spec 003 default-on flip (which happened in commit 2c6ebd0,
2026-05-06) by sweeping multiple thresholds (75/80/85/90/95th percentile)
across the historical state-log corpus and reporting per-threshold:

  - n_eligible bullish commits
  - n_fired (would have suppressed at this threshold)
  - kept_alpha (mean realized 21d α of commits left alone)
  - fired_alpha (mean realized 21d α of commits would-have-suppressed)
  - net_dalpha (kept − baseline; positive = filter helps)

Per-sector breakdown shows where the filter fires + helps vs hurts.

Empirical motivation (today, 2026-05-06):
  - Spec 003 retrospective showed +6.46% cumulative Δα at the production
    N>=20 floor — but n=2 fires only.
  - INTC investigation showed bull_kw=98 at 96th percentile; gate would
    have fired if PM had committed bullish, costing a +103% winner.
  - Pattern: the gate's anti-prediction is statistically real (corpus
    IC -0.489) but fires high-confidence-wrong on individual outliers.

The threshold question: does tightening from 80% (default) to 90% / 95%
maintain the gate's expected value while reducing false-fires on outliers
like INTC?

Mirrors the offline-replay methodology of:
  - scripts/contrarian_gate_retrospective.py (spec 003 single-threshold)
  - scripts/sector_momentum_retrospective.py (spec 004 threshold sweep)

Zero LLM cost.

Usage:
    python scripts/contrarian_gate_threshold_sweep.py
    python scripts/contrarian_gate_threshold_sweep.py --thresholds 75,80,85,90,95
    python scripts/contrarian_gate_threshold_sweep.py --history-floor 20
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yfinance as yf  # noqa: E402

from tradingagents.dataflows.returns import returns_from_frames  # noqa: E402
from tradingagents.paper.sectors import get_sector  # noqa: E402
from tradingagents.signals.contrarian_gate import _percentile_of_value  # noqa: E402
from tradingagents.signals.featurization import bull_keyword_count  # noqa: E402

LOGS_BASE = Path.home() / ".tradingagents" / "logs"
SECTORS_CACHE = Path.home() / ".tradingagents" / "paper" / "sectors.json"
BENCHMARK = "SPY"
BULLISH_RATINGS = {"Buy", "Overweight"}
DEFAULT_THRESHOLDS = (75, 80, 85, 90, 95)
DEFAULT_HISTORY_FLOOR = 20


def _all_propagate_rows() -> list[dict]:
    """Walk all state logs; return one row per (ticker, date) propagate.

    Each row: ticker, date, rating, bull_count.
    """
    rows = []
    if not LOGS_BASE.exists():
        return rows
    for ticker_dir in sorted(LOGS_BASE.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        log_dir = ticker_dir / "TradingAgentsStrategy_logs"
        if not log_dir.exists():
            continue
        for p in sorted(log_dir.glob("full_states_log_*.json")):
            date = p.stem.removeprefix("full_states_log_")
            try:
                state = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            mr = state.get("market_report", "") or ""
            ftd = state.get("final_trade_decision", "") or ""
            # Extract rating from the FTD's first line
            rating = "Hold"
            if ftd:
                first_line = ftd.split("\n", 1)[0]
                for r in ["Overweight", "Underweight", "Buy", "Sell", "Hold"]:
                    if r in first_line:
                        rating = r
                        break
            rows.append(
                {
                    "ticker": ticker,
                    "date": date,
                    "rating": rating,
                    "bull_count": float(bull_keyword_count(mr)) if mr else 0.0,
                }
            )
    rows.sort(key=lambda r: (r["ticker"], r["date"]))
    return rows


def _per_ticker_strict_prior(rows: list[dict], ticker: str, before_date: str) -> list[float]:
    """Return ALL bull_count values for `ticker` strictly before `before_date`."""
    return [r["bull_count"] for r in rows if r["ticker"] == ticker and r["date"] < before_date]


def _realized_alpha_pct(ticker: str, trade_date: str, holding_days: int = 21) -> float | None:
    from datetime import date as _date
    from datetime import timedelta as _td

    try:
        anchor = _date.fromisoformat(trade_date)
    except ValueError:
        return None
    end = (anchor + _td(days=int(holding_days * 1.5) + 7)).isoformat()
    try:
        stock = yf.Ticker(ticker).history(start=trade_date, end=end)
        bench = yf.Ticker(BENCHMARK).history(start=trade_date, end=end)
    except Exception:
        return None
    if stock.empty or bench.empty:
        return None
    raw, alpha, _ = returns_from_frames(stock, bench, trade_date, holding_days, as_percent=False)
    if alpha is None:
        return None
    return float(alpha) * 100.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--thresholds",
        default=",".join(str(t) for t in DEFAULT_THRESHOLDS),
        help="Comma-separated percentile thresholds (default: 75,80,85,90,95)",
    )
    parser.add_argument(
        "--history-floor",
        type=int,
        default=DEFAULT_HISTORY_FLOOR,
        help="Minimum per-ticker prior history for the gate to fire (default: 20 / FR-004)",
    )
    parser.add_argument(
        "--holding-days",
        type=int,
        default=21,
        help="Forward holding window for realized α (default: 21 trading days)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md"),
    )
    args = parser.parse_args()

    thresholds = tuple(sorted(int(t) for t in args.thresholds.split(",")))

    print("# Spec 003 contrarian gate threshold sweep")
    print()
    print(f"History floor: N >= {args.history_floor}")
    print(f"Thresholds: {thresholds} (percentile)")
    print(f"Holding window: {args.holding_days} trading days")
    print()

    print("Loading all propagate state logs...")
    all_rows = _all_propagate_rows()
    print(f"  {len(all_rows)} propagates across the corpus")

    bullish = [r for r in all_rows if r["rating"] in BULLISH_RATINGS]
    print(f"  {len(bullish)} bullish (Buy/OW) commits")
    if not bullish:
        print("[fatal] no bullish commits found")
        return

    # For each bullish commit, compute per-ticker prior history + percentile
    print()
    print("Computing percentiles + realized α (this hits yfinance)...")
    enriched = []
    for i, r in enumerate(bullish):
        if i % 10 == 0 and i > 0:
            print(f"  [{i}/{len(bullish)}]")
        history = _per_ticker_strict_prior(all_rows, r["ticker"], r["date"])
        n_history = len(history)
        if n_history >= args.history_floor:
            percentile = _percentile_of_value(history, r["bull_count"])
        else:
            percentile = None
        alpha = _realized_alpha_pct(r["ticker"], r["date"], args.holding_days)
        enriched.append(
            {
                **r,
                "n_history": n_history,
                "percentile": percentile,
                "alpha_pct": alpha,
            }
        )

    # Filter to commits with both percentile (above floor) and realized α
    eligible = [e for e in enriched if e["percentile"] is not None and e["alpha_pct"] is not None]
    print(f"  {len(eligible)} commits eligible (above floor + α available)")
    print(f"  {len(enriched) - len(eligible)} commits dropped (below floor or α unavailable)")

    if not eligible:
        print("[fatal] no eligible commits")
        return

    df = pd.DataFrame(eligible)
    baseline = df["alpha_pct"].mean()

    # Resolve sectors for per-sector breakdown
    sector_cache: dict[str, str] = {}
    for ticker in df["ticker"].unique():
        try:
            sector_cache[ticker] = get_sector(ticker, SECTORS_CACHE)
        except Exception:
            sector_cache[ticker] = "Unknown"
    df["sector"] = df["ticker"].map(sector_cache)

    print()
    print(f"## Baseline (no gate): n={len(df)}, mean α = {baseline:+.2f}%")
    print()

    # Threshold sweep
    print("## Threshold sweep")
    print()
    print(
        "| threshold | n_kept | n_fired | kept α | fired α | "
        "net Δα (kept − baseline) | suppressed-loser α | suppressed-winner α |"
    )
    print("|---|---|---|---|---|---|---|---|")
    sweep_rows = []
    for thr in thresholds:
        fire_mask = df["percentile"] >= thr
        kept = df[~fire_mask]
        fired = df[fire_mask]
        kept_mean = kept["alpha_pct"].mean() if not kept.empty else float("nan")
        fired_mean = fired["alpha_pct"].mean() if not fired.empty else float("nan")
        net_dalpha = kept_mean - baseline if not kept.empty else 0.0

        # Of the suppressed commits: how many were losers (α<0) vs winners (α>0)?
        sup_losers = fired[fired["alpha_pct"] < 0]
        sup_winners = fired[fired["alpha_pct"] > 0]
        sup_loser_mean = sup_losers["alpha_pct"].mean() if not sup_losers.empty else float("nan")
        sup_winner_mean = sup_winners["alpha_pct"].mean() if not sup_winners.empty else float("nan")

        print(
            f"| {thr}% | {len(kept)} | {len(fired)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp | "
            f"{sup_loser_mean:+.2f}% (n={len(sup_losers)}) | "
            f"{sup_winner_mean:+.2f}% (n={len(sup_winners)}) |"
        )
        sweep_rows.append(
            {
                "threshold": thr,
                "n_kept": len(kept),
                "n_fired": len(fired),
                "kept_mean": kept_mean,
                "fired_mean": fired_mean,
                "net_dalpha": net_dalpha,
                "n_sup_losers": len(sup_losers),
                "sup_loser_mean": sup_loser_mean,
                "n_sup_winners": len(sup_winners),
                "sup_winner_mean": sup_winner_mean,
            }
        )

    # Per-sector breakdown at default 80% threshold
    print()
    print("## Per-sector breakdown at threshold 80% (current default)")
    print()
    print("| Sector | n_total | n_fired | kept α | fired α | net Δα |")
    print("|---|---|---|---|---|---|")
    fire_mask_80 = df["percentile"] >= 80
    for sector in sorted(df["sector"].unique()):
        sub = df[df["sector"] == sector]
        sub_fire = sub[fire_mask_80[sub.index]]
        sub_kept = sub.drop(sub_fire.index)
        kept_mean = sub_kept["alpha_pct"].mean() if not sub_kept.empty else float("nan")
        fired_mean = sub_fire["alpha_pct"].mean() if not sub_fire.empty else float("nan")
        sector_baseline = sub["alpha_pct"].mean()
        net_dalpha = kept_mean - sector_baseline if not sub_kept.empty else 0.0
        print(
            f"| {sector} | {len(sub)} | {len(sub_fire)} | "
            f"{kept_mean:+.2f}% | {fired_mean:+.2f}% | {net_dalpha:+.2f}pp |"
        )

    # List the suppressed-winner outliers at 80% threshold (the INTC class)
    print()
    print("## Suppressed-winner outliers at threshold 80% (commits gate would have killed)")
    print()
    print("| Ticker | Date | bull_kw | percentile | n_history | realized α |")
    print("|---|---|---|---|---|---|")
    for _, r in (
        df[(df["percentile"] >= 80) & (df["alpha_pct"] > 0)]
        .sort_values("alpha_pct", ascending=False)
        .iterrows()
    ):
        print(
            f"| {r['ticker']} | {r['date']} | {r['bull_count']:.0f} | "
            f"{r['percentile']:.0f}% | {r['n_history']} | {r['alpha_pct']:+.2f}% |"
        )

    # Build markdown output
    md_lines = [
        f"# Spec 003 contrarian gate threshold sweep — {pd.Timestamp.now().date().isoformat()}",
        "",
        "**Spec**: `.specify/specs/003-analyst-contrarian-gate/spec.md`",
        f"**History floor**: N >= {args.history_floor} (FR-004)",
        f"**Holding window**: {args.holding_days} trading days",
        f"**Corpus**: {len(all_rows)} propagates → {len(bullish)} bullish commits → "
        f"{len(eligible)} eligible (above floor + α available)",
        "",
        "## Empirical motivation",
        "",
        "Today's INTC investigation (`claudedocs/sc003-intc-hold-investigation-2026-05-06.md`)",
        "surfaced that the spec 003 default-on flip (commit `2c6ebd0`, 2026-05-06) rests on",
        "n=2 evidence (NVDA + AAPL retrospective, +6.46% cumulative Δα). INTC at bull_kw=98",
        "/ 96th percentile is a concrete counter-example: gate would have suppressed a +103%",
        "winner if PM had committed bullish.",
        "",
        "This sweep tests whether a threshold change (tighten to 90/95% or revert to off)",
        "is empirically justified.",
        "",
        f"## Baseline (no gate): n={len(df)}, mean α = {baseline:+.2f}%",
        "",
        "## Threshold sweep",
        "",
        "| threshold | n_kept | n_fired | kept α | fired α | net Δα | "
        "suppressed-loser α | suppressed-winner α |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sweep_rows:
        md_lines.append(
            f"| {r['threshold']}% | {r['n_kept']} | {r['n_fired']} | "
            f"{r['kept_mean']:+.2f}% | {r['fired_mean']:+.2f}% | {r['net_dalpha']:+.2f}pp | "
            f"{r['sup_loser_mean']:+.2f}% (n={r['n_sup_losers']}) | "
            f"{r['sup_winner_mean']:+.2f}% (n={r['n_sup_winners']}) |"
        )
    md_lines.extend(
        [
            "",
            "## Verdict (template — fill from data above)",
            "",
            "If `net Δα` is positive at the current 80% default → keep the default-on flip.",
            "If `net Δα` is positive at 90% / 95% but not at 80% → tighten to 90/95%.",
            "If `net Δα` is non-positive at all thresholds → revert default to off.",
            "",
            "## Reproducibility",
            "",
            "```",
            f"python scripts/contrarian_gate_threshold_sweep.py "
            f"--thresholds {args.thresholds} --history-floor {args.history_floor}",
            "```",
            "",
            "Reads from `~/.tradingagents/logs/<ticker>/TradingAgentsStrategy_logs/`",
            "+ spec 002 sectors cache + yfinance for realized α. No LLM cost.",
        ]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md_lines), encoding="utf-8")
    print()
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
