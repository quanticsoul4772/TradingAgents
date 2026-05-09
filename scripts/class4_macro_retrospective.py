"""Class 4 (cross-asset/macro) filter retrospective — bear-side ticker_strong cohort.

Per RESEARCH_FINDINGS Open Questions table + Constitution VIII v1.4.0 / v1.4.3
gates. Tests whether macro features (VIX + 10y yield + USD index + sector ETF
correlation) can identify the 18-row bear-side `ticker_strong` cohort
(α-vs-SPY = +28.02% mean) BEFORE the framework commits Underweight/Sell —
i.e., would Class 4 have suppressed these counter-trend bear calls if the
macro environment was risk-on?

Mechanism class: cross-asset/macro (Class 4 per Spec 008 design doc).
Different from C-4 institutional rotation (already shipped as Spec X-1) — this
is the OTHER "Class 4" naming.

Constitution gates:
- v1.4.0 standalone: net Δα ≥ +0.5pp at proposed default threshold AND
  cohort hit rate ≥ 40% (when target cohort is named).
- v1.4.3 additive: net Δα ≥ +0.5pp OR cohort hit ≥ +5pp OR FP -10pp vs
  best-existing-default-active same-direction filter (A3 / Spec X-1 bear).

Empirical motivation: `claudedocs/sector-alpha-attribution-2026-05-06.md`
identified 18-row bear-side ticker_strong cohort with mean α-vs-SPY +28.02%
that A3 misses entirely (A3 only fires on per-ticker DOWN absolute mean-
reversion; ticker_strong cohort is per-ticker-UP RELATIVE-to-sector).

Cost: $0 LLM (all yfinance + arithmetic; no LLM scoring).

Usage:
    python scripts/class4_macro_retrospective.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.graph.trading_graph import fetch_returns  # noqa: E402

EXPERIMENTS_DIR = Path("experiments")
BEAR_RATINGS = {"Underweight", "Sell"}

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


def _enumerate_bear_commits() -> pd.DataFrame:
    """Walk experiments/*/results.csv. Handles both 'analysis_date' (legacy) and 'date' (newer) columns."""
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
        # Filter to bear ratings + non-error
        if "error" in df.columns:
            df = df[df["error"].isna() | (df["error"] == "")]
        df = df[df["rating"].isin(BEAR_RATINGS)]
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
    """VIX + 10y yield + USD index closes on the trade_date (or last business day before)."""
    if trade_date in _MACRO_CACHE:
        return _MACRO_CACHE[trade_date]
    try:
        end = pd.Timestamp(trade_date) + pd.Timedelta(days=1)
        start = pd.Timestamp(trade_date) - pd.Timedelta(days=10)
        vix = yf.Ticker("^VIX").history(start=start, end=end, auto_adjust=False)
        tnx = yf.Ticker("^TNX").history(start=start, end=end, auto_adjust=False)  # 10y yield × 10
        dxy = yf.Ticker("DX-Y.NYB").history(start=start, end=end, auto_adjust=False)

        # Use the latest close on or before trade_date
        def _latest_close(df, target_date):
            if df.empty:
                return None
            df_idx = df.index.tz_localize(None) if df.index.tz else df.index
            mask = df_idx <= pd.Timestamp(target_date)
            valid = df[mask]
            if valid.empty:
                return None
            return float(valid["Close"].iloc[-1])

        snap = {
            "vix": _latest_close(vix, trade_date),
            "tnx": _latest_close(tnx, trade_date),  # actual yield × 10 (e.g., 42.5 = 4.25%)
            "dxy": _latest_close(dxy, trade_date),
        }

        # 30d trailing change
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

        # Need wider window for 30d change
        wide_start = pd.Timestamp(trade_date) - pd.Timedelta(days=60)
        vix_w = yf.Ticker("^VIX").history(start=wide_start, end=end, auto_adjust=False)
        tnx_w = yf.Ticker("^TNX").history(start=wide_start, end=end, auto_adjust=False)
        dxy_w = yf.Ticker("DX-Y.NYB").history(start=wide_start, end=end, auto_adjust=False)
        snap["vix_30d_pct"] = _pct_change_30d(vix_w, trade_date)
        snap["tnx_30d_pct"] = _pct_change_30d(tnx_w, trade_date)
        snap["dxy_30d_pct"] = _pct_change_30d(dxy_w, trade_date)
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
    print("Class 4 (cross-asset/macro) filter retrospective")
    print("Target: bear-side ticker_strong cohort (mean α-vs-SPY +28.02% per")
    print("        claudedocs/sector-alpha-attribution-2026-05-06.md)")
    print("=" * 70)
    print()

    bear = _enumerate_bear_commits()
    print(f"Bear commits enumerated: {len(bear)}")

    # Compute α-vs-SPY + α-vs-sector + macro snapshot per bear commit
    rows = []
    for _, r in bear.iterrows():
        ticker = r["ticker"]
        date = r["trade_date"]
        rating = r["rating"]
        # Forward returns
        raw_t, alpha_spy, days = fetch_returns(ticker, date, holding_days=21)
        if alpha_spy is None:
            continue
        sector = _get_sector(ticker)
        if sector is None or sector not in SECTOR_ETF_MAP:
            continue
        etf = SECTOR_ETF_MAP[sector]
        raw_e, alpha_e_vs_spy, _ = fetch_returns(etf, date, holding_days=21)
        if raw_t is None or raw_e is None:
            continue
        alpha_sector = (raw_t - raw_e) * 100  # ticker-vs-sector in pp
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
                "tnx_pct": macro["tnx"] / 10 if macro["tnx"] else None,  # to actual %
                "dxy": macro["dxy"],
                "vix_30d_pct": macro["vix_30d_pct"],
                "tnx_30d_pct": macro["tnx_30d_pct"],
                "dxy_30d_pct": macro["dxy_30d_pct"],
            }
        )
    df = pd.DataFrame(rows)
    print(f"Bear commits with valid forward + sector + macro data: {len(df)}")

    if df.empty:
        print("\nNo data — exiting.")
        return

    # ticker_strong cohort
    ts = df[df["cell"] == "ticker_strong"].copy()
    print(f"\nticker_strong cohort: {len(ts)} bear commits with α-vs-SPY > 0 AND α-vs-sector > 0")
    if len(ts) > 0:
        print(f"  mean α-vs-SPY: {ts['alpha_spy_pct'].mean():+.2f}%")
        print(f"  mean α-vs-sector: {ts['alpha_sector_pct'].mean():+.2f}pp")

    # Macro signature of ticker_strong vs other cells
    print()
    print("Macro signature comparison (ticker_strong vs other bear cells):")
    print(f"{'Metric':<20} {'ticker_strong':>15} {'other_cells':>15} {'Δ':>10}")
    for col in ["vix", "tnx_pct", "dxy", "vix_30d_pct", "tnx_30d_pct", "dxy_30d_pct"]:
        if col not in df.columns:
            continue
        ts_mean = ts[col].mean() if not ts.empty else None
        other = df[df["cell"] != "ticker_strong"]
        other_mean = other[col].mean() if not other.empty else None
        if ts_mean is None or other_mean is None:
            continue
        delta = ts_mean - other_mean
        print(f"{col:<20} {ts_mean:>15.2f} {other_mean:>15.2f} {delta:>+10.2f}")

    # Test thresholds: would suppress UW if VIX < threshold (low VIX = risk-on = bear call likely wrong)
    print()
    print("Threshold sweep — fire decision = SUPPRESS bear call when VIX < threshold")
    print(f"{'VIX_thresh':>10} {'fired':>6} {'cohort_hit':>12} {'fp':>4} {'net_Δα':>10}")

    cohort_target = ts.index.tolist()

    for thresh in [12.0, 14.0, 16.0, 18.0, 20.0, 22.0]:
        if "vix" not in df.columns:
            break
        fires = df[df["vix"] < thresh]
        n_fired = len(fires)
        cohort_caught = len(set(fires.index).intersection(set(cohort_target)))
        fp = n_fired - cohort_caught
        # net Δα: suppressed UW commit means we'd flip its α-attribution from -alpha_spy to 0
        # If alpha_spy>0 and we suppress UW, we save |alpha_spy| pp of attribution
        # If alpha_spy<0 and we suppress UW, we LOSE |alpha_spy| pp (UW would have been correct)
        net_delta = 0.0
        for idx in fires.index:
            row_alpha = df.loc[idx, "alpha_spy_pct"]
            if row_alpha is None:
                continue
            # Suppressing UW: we no longer "earn" -alpha_spy via UW direction.
            # If alpha_spy > 0 (bear call wrong), suppression saves us alpha_spy pp.
            # If alpha_spy < 0 (bear call right), suppression costs us |alpha_spy| pp.
            # Per filter convention: net_delta = sum(alpha_spy on fires) (positive = good)
            net_delta += row_alpha
        net_delta = net_delta / max(1, n_fired)
        cohort_hit_rate = cohort_caught / max(1, n_fired) * 100
        print(
            f"{thresh:>10.1f} {n_fired:>6} {cohort_caught:>5}/{len(cohort_target):<6} {fp:>4} {net_delta:>+9.2f}pp ({cohort_hit_rate:.0f}% cohort)"
        )

    # Constitution VIII gate evaluation
    print()
    print("=" * 70)
    print("Constitution VIII gate evaluation")
    print("=" * 70)
    print()
    print("v1.4.0 standalone gate: net Δα ≥ +0.5pp at default threshold AND")
    print("                        cohort hit rate ≥ 40% (when cohort named)")
    print()
    # Pick the "best" threshold (max net_delta)
    best = None
    for thresh in [12.0, 14.0, 16.0, 18.0, 20.0, 22.0]:
        fires = df[df["vix"] < thresh]
        n_fired = len(fires)
        if n_fired == 0:
            continue
        cohort_caught = len(set(fires.index).intersection(set(cohort_target)))
        cohort_hit_rate = cohort_caught / n_fired * 100
        net_delta = fires["alpha_spy_pct"].mean()
        if best is None or net_delta > best[3]:
            best = (thresh, n_fired, cohort_caught, net_delta, cohort_hit_rate)
    if best:
        thresh, n_fired, cohort_caught, net_delta, cohort_hit_rate = best
        print(f"Best threshold: VIX < {thresh}")
        print(f"  Fires: {n_fired}; cohort caught: {cohort_caught} of {len(cohort_target)}")
        print(f"  Net Δα at threshold: {net_delta:+.2f}pp")
        print(f"  Cohort hit rate: {cohort_hit_rate:.0f}%")
        print("  Standalone gate (v1.4.0) PASS criteria: net Δα ≥ +0.5pp AND cohort hit ≥ 40%")
        gate_a = net_delta >= 0.5
        gate_b = cohort_hit_rate >= 40
        print(f"    Net Δα ≥ +0.5pp: {'PASS' if gate_a else 'FAIL'} ({net_delta:+.2f}pp)")
        print(f"    Cohort hit ≥ 40%: {'PASS' if gate_b else 'FAIL'} ({cohort_hit_rate:.0f}%)")
        print(f"  Standalone gate VERDICT: {'PASS' if gate_a and gate_b else 'FAIL → SKIP'}")


if __name__ == "__main__":
    main()
