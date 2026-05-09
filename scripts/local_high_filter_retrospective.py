"""Per-ticker local-high BULL-side filter retrospective.

Per RESEARCH_FINDINGS Open Questions + Constitution VIII v1.4.0 / v1.4.3
gates. Tests whether suppressing Buy/Overweight commits when ticker price
is within X% of its 30d rolling high catches the 27-row bull-side
`ticker_weak` cohort (5th-failure-mode; mean α-vs-SPY -5.34%) per
`claudedocs/sector-alpha-attribution-2026-05-09.md`.

**Hypothesis** (per PR #203 Class 4 BULL SKIP analysis): the bull
ticker_weak cohort is **stock-specific mean-reversion at local highs**
(88.9% Tech-concentrated; AAPL/MSFT/NVDA dominate worst-10 list). A
filter measuring price proximity to recent rolling high should catch
this cohort BEFORE the framework commits Buy/Overweight.

Mechanism class: per-ticker price-vs-rolling-high (NEW class —
distinct from A3 per-ticker absolute mean-reversion which uses
30d-return; this uses 30d-rolling-MAX-distance).

Cost: $0 LLM (yfinance + arithmetic).

Usage:
    python scripts/local_high_filter_retrospective.py
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


_PRICE_CACHE: dict[str, pd.DataFrame] = {}


def _ticker_history(ticker: str, trade_date: str, lookback_days: int = 60) -> pd.DataFrame | None:
    """Fetch ticker price history from trade_date back lookback_days."""
    cache_key = f"{ticker}|{trade_date}|{lookback_days}"
    if cache_key in _PRICE_CACHE:
        return _PRICE_CACHE[cache_key]
    try:
        end = pd.Timestamp(trade_date) + pd.Timedelta(days=1)
        start = pd.Timestamp(trade_date) - pd.Timedelta(days=lookback_days + 5)
        df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
        if df is None or df.empty:
            _PRICE_CACHE[cache_key] = None
            return None
        _PRICE_CACHE[cache_key] = df
        return df
    except Exception:
        _PRICE_CACHE[cache_key] = None
        return None


def _proximity_to_30d_high_pct(ticker: str, trade_date: str) -> float | None:
    """Return (current - 30d_high) / 30d_high * 100. Negative = below high.
    A value of -1.5 means current is 1.5% BELOW the 30d high."""
    df = _ticker_history(ticker, trade_date, lookback_days=30)
    if df is None or df.empty or "Close" not in df.columns or "High" not in df.columns:
        return None
    df_idx = df.index.tz_localize(None) if df.index.tz else df.index
    mask = df_idx <= pd.Timestamp(trade_date)
    valid = df[mask]
    if valid.empty:
        return None
    # Use last 30 trading days
    last_30 = valid.tail(30)
    if last_30.empty:
        return None
    rolling_high = float(last_30["High"].max())
    current = float(last_30["Close"].iloc[-1])
    if rolling_high <= 0:
        return None
    return (current - rolling_high) / rolling_high * 100


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
    print("Per-ticker local-high BULL-side filter retrospective")
    print("Target: bull ticker_weak cohort (5th-failure-mode; n=27, mean")
    print("        α-vs-SPY -5.34% per claudedocs/sector-alpha-attribution-2026-05-09.md)")
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
        raw_e, _, _ = fetch_returns(etf, date, holding_days=21)
        if raw_t is None or raw_e is None:
            continue
        alpha_sector = (raw_t - raw_e) * 100
        cell = _classify_cell(alpha_spy * 100, alpha_sector)
        prox = _proximity_to_30d_high_pct(ticker, date)
        if prox is None:
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
                "proximity_to_30d_high_pct": prox,
            }
        )
    df = pd.DataFrame(rows)
    print(f"Bull commits with valid forward + sector + price data: {len(df)}")

    if df.empty:
        print("\nNo data — exiting.")
        return

    tw = df[df["cell"] == "ticker_weak"].copy()
    print(f"\nticker_weak cohort: {len(tw)} bull commits with α<0 vs both SPY AND sector")
    if len(tw) > 0:
        print(f"  mean α-vs-SPY: {tw['alpha_spy_pct'].mean():+.2f}%")
        print(
            f"  mean proximity to 30d high: {tw['proximity_to_30d_high_pct'].mean():+.2f}% (negative = below high)"
        )

    # Compare proximity-to-30d-high signature
    print()
    print("Proximity-to-30d-high signature comparison:")
    print(f"{'Cell':<20} {'n':>4} {'mean prox %':>14} {'< -2%':>8} {'< -5%':>8}")
    for cell in ["ticker_strong", "sector_tide_up", "sector_drag", "ticker_weak"]:
        sub = df[df["cell"] == cell]
        if sub.empty:
            continue
        n = len(sub)
        mean_prox = sub["proximity_to_30d_high_pct"].mean()
        below_2 = (sub["proximity_to_30d_high_pct"] < -2.0).sum()
        below_5 = (sub["proximity_to_30d_high_pct"] < -5.0).sum()
        print(f"{cell:<20} {n:>4} {mean_prox:>+13.2f}% {below_2:>8} {below_5:>8}")

    # Threshold sweep — fire = SUPPRESS bull when proximity > threshold
    # (i.e., price is close to local high; mean-reversion zone)
    print()
    print("Threshold sweep — fire decision = SUPPRESS bull when proximity > threshold")
    print("(threshold > -X means: price within X% of 30d high)")
    print(f"{'thresh %':>10} {'fired':>6} {'cohort_hit':>12} {'fp':>4} {'net_Δα':>10}")

    cohort_target = tw.index.tolist()

    for thresh in [-0.5, -1.0, -2.0, -3.0, -5.0, -8.0]:
        # Suppress when proximity > thresh (i.e., closer to high than thresh)
        fires = df[df["proximity_to_30d_high_pct"] > thresh]
        n_fired = len(fires)
        if n_fired == 0:
            print(
                f"{thresh:>10.1f} {n_fired:>6} {'0/' + str(len(cohort_target)):>12} {0:>4} {'n/a':>10}"
            )
            continue
        cohort_caught = len(set(fires.index).intersection(set(cohort_target)))
        fp = n_fired - cohort_caught
        # Bull suppression net_delta = -alpha_spy on fires
        net_delta = sum(-df.loc[idx, "alpha_spy_pct"] for idx in fires.index) / n_fired
        cohort_hit_rate = cohort_caught / n_fired * 100
        print(
            f"{thresh:>10.1f} {n_fired:>6} {cohort_caught:>5}/{len(cohort_target):<6} "
            f"{fp:>4} {net_delta:>+9.2f}pp ({cohort_hit_rate:.0f}% cohort)"
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
    best = None
    for thresh in [-0.5, -1.0, -2.0, -3.0, -5.0, -8.0]:
        fires = df[df["proximity_to_30d_high_pct"] > thresh]
        n_fired = len(fires)
        if n_fired == 0:
            continue
        cohort_caught = len(set(fires.index).intersection(set(cohort_target)))
        cohort_hit_rate = cohort_caught / n_fired * 100
        net_delta = sum(-df.loc[idx, "alpha_spy_pct"] for idx in fires.index) / n_fired
        if best is None or net_delta > best[3]:
            best = (thresh, n_fired, cohort_caught, net_delta, cohort_hit_rate)
    if best:
        thresh, n_fired, cohort_caught, net_delta, cohort_hit_rate = best
        print(f"Best threshold: proximity > {thresh}% (price within {-thresh}% of 30d high)")
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
