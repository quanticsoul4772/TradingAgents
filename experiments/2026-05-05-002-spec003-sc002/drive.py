"""Spec 003 SC-002 fresh-data validation driver.

Runs 25 propagates (5 tickers × 5 mid-week dates) with
contrarian_gate_mode='shadow' and writes results.csv with rating +
gate annotation per row.

After completion, the analyzer (scripts/analyze_backtest.py) + the
within-ticker artifact-check scripts can be re-run to compute the
SC-002 success criterion: within-ticker median IC ≤ -0.30 reproduced
in the now-larger corpus.
"""

from __future__ import annotations

import csv
import sys
import time
from copy import deepcopy
from pathlib import Path

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

EXPERIMENT_ID = "2026-05-05-002-spec003-sc002"
TICKERS = ["AAPL", "GOOGL", "INTC", "JPM", "MSFT"]
DATES = ["2026-03-04", "2026-03-11", "2026-03-18", "2026-03-25", "2026-04-01"]
EXPERIMENT_DIR = Path(__file__).resolve().parent
SLEEP_BETWEEN_PROPAGATES_SEC = 1.0


def build_config() -> dict:
    config = deepcopy(DEFAULT_CONFIG)
    config["llm_provider"] = "anthropic"
    config["deep_think_llm"] = "claude-opus-4-7"
    config["quick_think_llm"] = "claude-haiku-4-5"
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1
    config["checkpoint_enabled"] = False
    config["memory_log_path"] = str(EXPERIMENT_DIR / "backtest_memory.md")
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "exa",
    }
    config["contrarian_gate_mode"] = "shadow"
    return config


def main() -> int:
    config = build_config()
    print(f"[experiment] {EXPERIMENT_ID}")
    print(f"[grid] {len(TICKERS)} tickers × {len(DATES)} dates = {len(TICKERS) * len(DATES)} propagates")
    print(f"[config] contrarian_gate_mode = {config['contrarian_gate_mode']}")
    print("[graph] building TradingAgentsGraph...")
    ta = TradingAgentsGraph(
        selected_analysts=["market", "news", "fundamentals"],
        debug=False,
        config=config,
    )

    out_csv = EXPERIMENT_DIR / "results.csv"
    fieldnames = [
        "ticker",
        "analysis_date",
        "rating",
        "error",
        "run_seconds",
        "deep_model",
        "quick_model",
        "debate_rounds",
        "analysts",
        "experiment_id",
        "gate_mode",
        "gate_skipped",
        "feature_value",
        "percentile",
        "n_history",
        "would_fire",
        "gate_fired",
        "pre_rating",
        "post_rating",
    ]

    # Write header
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    n_total = len(TICKERS) * len(DATES)
    n_done = 0
    n_err = 0
    fires = 0
    wall_start = time.perf_counter()

    for ticker in TICKERS:
        for date in DATES:
            n_done += 1
            print(f"\n[propagate {n_done}/{n_total}] {ticker} {date}...")
            t0 = time.perf_counter()
            rating = ""
            error = ""
            final_state = None
            try:
                final_state, rating_value = ta.propagate(ticker, date)
                rating = str(rating_value).strip()
            except Exception as e:  # noqa: BLE001
                error = f"{type(e).__name__}: {e}"
                n_err += 1
            elapsed = round(time.perf_counter() - t0, 2)
            print(f"  → rating={rating!r} error={error!r} seconds={elapsed}")

            gate = (final_state or {}).get("contrarian_gate") or {}
            if gate.get("gate_fired") is True:
                fires += 1
            row = {
                "ticker": ticker,
                "analysis_date": date,
                "rating": rating,
                "error": error,
                "run_seconds": elapsed,
                "deep_model": "claude-opus-4-7",
                "quick_model": "claude-haiku-4-5",
                "debate_rounds": 1,
                "analysts": "market,news,fundamentals",
                "experiment_id": EXPERIMENT_ID,
                "gate_mode": gate.get("mode", ""),
                "gate_skipped": gate.get("gate_skipped", "") or "",
                "feature_value": gate.get("feature_value", ""),
                "percentile": gate.get("percentile", ""),
                "n_history": gate.get("n_history", ""),
                "would_fire": gate.get("would_fire", ""),
                "gate_fired": gate.get("gate_fired", ""),
                "pre_rating": gate.get("pm_rating_pre_gate", ""),
                "post_rating": gate.get("pm_rating_post_gate", ""),
            }
            with out_csv.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)

            if n_done < n_total:
                time.sleep(SLEEP_BETWEEN_PROPAGATES_SEC)

    elapsed_min = (time.perf_counter() - wall_start) / 60.0
    print(
        f"\n[summary] {n_done - n_err}/{n_total} ok, {n_err} errors, "
        f"{fires} active gate fires (shadow mode → no actual override), "
        f"{elapsed_min:.1f} min wall-clock"
    )
    print(f"[csv] {out_csv}")
    return 0 if n_err < 3 else 1


if __name__ == "__main__":
    sys.exit(main())
