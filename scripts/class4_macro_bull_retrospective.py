"""Class 4 (cross-asset/macro) BULL-side filter retrospective.

Per RESEARCH_FINDINGS Open Questions + Constitution VIII v1.4.0 / v1.4.3
gates. Tests whether macro features (VIX snapshot + 30d Δ%) can identify
the 27-row bull-side `ticker_weak` cohort (mean realized α-vs-SPY = -5.34%
per `claudedocs/sector-alpha-attribution-2026-05-06.md`) BEFORE the
framework commits Buy/Overweight — i.e., would Class 4 BULL have
suppressed these counter-trend bullish calls when the macro environment
was risk-off (high VIX)?

Sister to scripts/class4_macro_retrospective.py (bear-side). Same data
fetch + cell classification logic; mirrored for bull cohort.

Mechanism class: cross-asset/macro (Class 4 per Spec 008 design doc).
Bull-side asymmetric to bear-side:
- Bear-side: low VIX (risk-on) + bear commit → likely wrong (counter-trend)
- Bull-side: high VIX (risk-off) + bull commit → likely wrong (counter-trend)

Cost: $0 LLM (yfinance + arithmetic; no LLM scoring).

Usage:
    python scripts/class4_macro_bull_retrospective.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

EXPERIMENTS_DIR = Path("experiments")
BULL_RATINGS = {"Buy", "Overweight"}

SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Industrials": "XLI",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Basic Materials": "XLB",
}


def _enumerate_bull_commits() -> pd.DataFrame:
    """Walk experiments/*/results.csv. Handles both 'analysis_date' (legacy)
    and 'date' (newer) columns."""
    rows = []
    for p in sorted(EXPERIMENTS_DIR.glob("*/results.csv")):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if "rating" not in df.columns or "ticker" not in df.columns:
            continue
        date_col = (
            "analysis_date"
            if "analysis_date" in df.columns
            else ("date" if "date" in df.columns else None)
        )
        if date_col is None:
            continue
        if "error" in df.columns:
            df = df[df["error"].isna() | (df["error"] == "")]
        df = df[df["rating"].isin(BULL_RATINGS)]
        for _, r in df.iterrows():
            rows.append(
                {
                    "experiment": p.parent.name,
                    "ticker": str(r["ticker"]).upper().strip(),
                    "trade_date": str(r[date_col]).strip(),
                    "rating": str(r["rating"]).strip(),
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.drop_duplicates(subset=["ticker", "trade_date", "rating"]).reset_index(drop=True)
    return out


_SECTOR_CACHE: dict[str, str | None] = {}


def _get_sector(ticker: str) -> str | None:
    if ticker in _SECTOR_CACHE:
        return _SECTOR_CACHE[ticker]
    try:
        info = yf.Ticker(ticker).info
        sector = info.get("sector")
        _SECTOR_CACHE[ticker] = sector
        return sector
    except Exception:
        _SECTOR_CACHE[ticker] = None
        return None


_MACRO_CACHE: dict[str, dict | None] = {}


def _macro_snapshot(trade_date: str) -> dict | None:
    if trade_date in _MACRO_CACHE:
        return _MACRO_CACHE[trade_date]
    try:
        end = pd.Timestamp(trade_date) + pd.Timedelta(days=1)
        wide_start = pd.Timestamp(trade_date) - pd.Timedelta(days=60)
        vix = yf.Ticker("^VIX").history(start=wide_start, end=end, auto_adjust=False)

        def _latest_close(df, target_date):
            if df.empty:
                return None
            df_idx = df.index.tz_localize(None) if df.index.tz else df.index
            mask = df_idx <= pd.Timestamp(target_date)
            valid = df[mask]
            if valid.empty:
                return None
            return float(valid["Close"].iloc[-1])

        def _pct_change_30d(df, target_date):
            close = _latest_close(df, target_date)
            if close is None or df.empty:
                return None
            df_idx = df.index.tz_localize(None) if df.index.tz else df.index
            past_target = pd.Timestamp(target_date) - pd.Timedelta(days=40)
            past_mask = df_idx <= past_target
            past_valid = df[past_mask]
            if past_valid.empty:
                return None
            past_close = float(past_valid["Close"].iloc[-1])
            return (close - past_close) / past_close * 100

        snap = {
            "vix": _latest_close(vix, trade_date),
            "vix_30d_pct": _pct_change_30d(vix, trade_date),
        }
        _MACRO_CACHE[trade_date] = snap
        return snap
    except Exception as exc:
        print(f"  WARN: macro fetch failed for {trade_date}: {exc}", file=sys.stderr)
        _MACRO_CACHE[trade_date] = None
        return None


def _classify_cell(alpha_spy: float | None, alpha_sector: float | None) -> str:
    if alpha_spy is None or alpha_sector is None:
        return "no_data"
    if alpha_spy > 0 and alpha_sector > 0:
        return "ticker_strong"
    if alpha_spy > 0 and alpha_sector <= 0:
        return "sector_tide_up"
    if alpha_spy <= 0 and alpha_sector > 0:
        return "sector_drag"
    return "ticker_weak"


def main():
    print("=" * 70)
    print("Class 4 (cross-asset/macro) BULL-side filter retrospective")
    print("Target: bull-side ticker_weak cohort (5th-failure-mode; mean")
    print("        α-vs-SPY -5.34% per claudedocs/sector-alpha-attribution-2026-05-06.md)")
    print("=" * 70)
    print()

    bull = _enumerate_bull_commits()
    print(f"Bull commits enumerated: {len(bull)}")

    rows = []
    for _, r in bull.iterrows():
        ticker = r["ticker"]
        date = r["trade_date"]
        rating = r["rating"]
        raw_t, alpha_spy, _days = fetch_returns(ticker, date, holding_days=21)
        if alpha_spy is None:
            continue
        sector = _get_sector(ticker)
        if sector is None or sector not in SECTOR_ETF_MAP:
            continue
        etf = SECTOR_ETF_MAP[sector]
        raw_e, _alpha_e, _ = fetch_returns(etf, date, holding_days=21)
        if raw_t is None or raw_e is None:
            continue
        alpha_sector = (raw_t - raw_e) * 100
        cell = _classify_cell(alpha_spy * 100, alpha_sector)
        macro = _macro_snapshot(date)
        if macro is None:
            continue
        rows.append(
            {
                "ticker": ticker,
                "date": date,
                "rating": rating,
                "sector": sector,
                "alpha_spy_pct": alpha_spy * 100,
                "alpha_sector_pct": alpha_sector,
                "cell": cell,
                "vix": macro["vix"],
                "vix_30d_pct": macro["vix_30d_pct"],
            }
        )
    df = pd.DataFrame(rows)
    print(f"Bull commits with valid forward + sector + macro data: {len(df)}")

    if df.empty:
        print("\nNo data — exiting.")
        return

    # ticker_weak cohort (5th failure mode for bullish)
    tw = df[df["cell"] == "ticker_weak"].copy()
    print(f"\nticker_weak cohort: {len(tw)} bull commits with α-vs-SPY < 0 AND α-vs-sector < 0")
    if len(tw) > 0:
        print(f"  mean α-vs-SPY: {tw['alpha_spy_pct'].mean():+.2f}%")
        print(f"  mean α-vs-sector: {tw['alpha_sector_pct'].mean():+.2f}pp")

    # Macro signature
    print()
    print("Macro signature comparison (ticker_weak vs other bull cells):")
    print(f"{'Metric':<20} {'ticker_weak':>15} {'other_cells':>15} {'Δ':>10}")
    for col in ["vix", "vix_30d_pct"]:
        if col not in df.columns:
            continue
        tw_mean = tw[col].mean() if not tw.empty else None
        other = df[df["cell"] != "ticker_weak"]
        other_mean = other[col].mean() if not other.empty else None
        if tw_mean is None or other_mean is None:
            continue
        delta = tw_mean - other_mean
        print(f"{col:<20} {tw_mean:>15.2f} {other_mean:>15.2f} {delta:>+10.2f}")

    # Threshold sweep — fire = SUPPRESS bull when VIX > threshold (risk-off)
    print()
    print("Threshold sweep — fire decision = SUPPRESS bull call when VIX > threshold (risk-off)")
    print(f"{'VIX_thresh':>10} {'fired':>6} {'cohort_hit':>12} {'fp':>4} {'net_Δα':>10}")

    cohort_target = tw.index.tolist()

    for thresh in [16.0, 18.0, 20.0, 22.0, 25.0, 28.0, 30.0]:
        if "vix" not in df.columns:
            break
        # SUPPRESS bull when VIX > threshold (risk-off)
        fires = df[df["vix"] > thresh]
        n_fired = len(fires)
        cohort_caught = len(set(fires.index).intersection(set(cohort_target)))
        fp = n_fired - cohort_caught
        # Net Δα convention: suppressing a bullish commit means we no longer "earn" alpha_spy.
        # If alpha_spy < 0 (bullish call wrong), suppression saves us |alpha_spy| pp (positive).
        # If alpha_spy > 0 (bullish call right), suppression costs us alpha_spy pp (negative).
        # Sign flip from bear: net_delta = sum(-alpha_spy on fires) → positive = good
        net_delta = 0.0
        for idx in fires.index:
            row_alpha = df.loc[idx, "alpha_spy_pct"]
            if row_alpha is None:
                continue
            # For bull suppression: net_delta = -alpha_spy (positive = bull call was wrong)
            net_delta += -row_alpha
        net_delta = net_delta / max(1, n_fired)
        cohort_hit_rate = cohort_caught / max(1, n_fired) * 100
        print(
            f"{thresh:>10.1f} {n_fired:>6} {cohort_caught:>5}/{len(cohort_target):<6} "
            f"{fp:>4} {net_delta:>+9.2f}pp ({cohort_hit_rate:.0f}% cohort)"
        )

    # Constitution VIII gate eval
    print()
    print("=" * 70)
    print("Constitution VIII gate evaluation")
    print("=" * 70)
    print()
    print("v1.4.0 standalone gate: net Δα ≥ +0.5pp at default threshold AND")
    print("                        cohort hit rate ≥ 40% (when cohort named)")
    print()
    best = None
    for thresh in [16.0, 18.0, 20.0, 22.0, 25.0, 28.0, 30.0]:
        fires = df[df["vix"] > thresh]
        n_fired = len(fires)
        if n_fired == 0:
            continue
        cohort_caught = len(set(fires.index).intersection(set(cohort_target)))
        cohort_hit_rate = cohort_caught / n_fired * 100
        # Bull suppression net_delta convention: -alpha_spy
        net_delta = sum(-df.loc[idx, "alpha_spy_pct"] for idx in fires.index) / n_fired
        if best is None or net_delta > best[3]:
            best = (thresh, n_fired, cohort_caught, net_delta, cohort_hit_rate)
    if best:
        thresh, n_fired, cohort_caught, net_delta, cohort_hit_rate = best
        print(f"Best threshold: VIX > {thresh}")
        print(f"  Fires: {n_fired}; cohort caught: {cohort_caught} of {len(cohort_target)}")
        print(f"  Net Δα at threshold: {net_delta:+.2f}pp")
        print(f"  Cohort hit rate: {cohort_hit_rate:.0f}%")
        gate_a = net_delta >= 0.5
        gate_b = cohort_hit_rate >= 40
        print(f"    Net Δα ≥ +0.5pp: {'PASS' if gate_a else 'FAIL'} ({net_delta:+.2f}pp)")
        print(f"    Cohort hit ≥ 40%: {'PASS' if gate_b else 'FAIL'} ({cohort_hit_rate:.0f}%)")
        print(f"  Standalone gate VERDICT: {'PASS' if gate_a and gate_b else 'FAIL → SKIP'}")


if __name__ == "__main__":
    main()
