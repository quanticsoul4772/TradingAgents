"""BR-3 v2 — news + fundamentals analyst structured-output pilot harness.

Per `experiments/2026-05-09-003-br3-v2-news-fundamentals/HYPOTHESIS.md`.

Sister to BR-3 v1 (`scripts/br3_squeak_pilot.py`). Test grid:
2 sub-experiments × 5 dates × 2 tickers × 2 modes = 40 propagates × ~$0.40 = ~$16 LLM (T2).

Sub-experiment A: news_analyst_format prose vs structured (10 + 10 = 20 propagates / ~$8)
Sub-experiment B: fundamentals_analyst_format prose vs structured (10 + 10 = 20 propagates / ~$8)

Mode encoding:
- "news_prose" / "news_structured" — news_analyst_format varies; fundamentals stays prose
- "fund_prose" / "fund_structured" — fundamentals_analyst_format varies; news stays prose

Output schema:
    ticker, date, sub_experiment, mode, rating, error, run_seconds

Usage:
    python scripts/br3_v2_pilot.py [--tickers NVDA,AAPL] [--out experiments/<dir>/results.csv]
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: E402

DEFAULT_DATES = [
    "2026-01-30",
    "2026-02-13",
    "2026-02-27",
    "2026-03-13",
    "2026-03-27",
]

CSV_HEADER = ["ticker", "date", "sub_experiment", "mode", "rating", "error", "run_seconds"]

# Mode → config-overrides map
MODES = {
    "news_prose": {"news_analyst_format": "prose", "fundamentals_analyst_format": "prose"},
    "news_structured": {
        "news_analyst_format": "structured",
        "fundamentals_analyst_format": "prose",
    },
    "fund_prose": {"news_analyst_format": "prose", "fundamentals_analyst_format": "prose"},
    "fund_structured": {
        "news_analyst_format": "prose",
        "fundamentals_analyst_format": "structured",
    },
}

MODE_TO_SUB_EXPERIMENT = {
    "news_prose": "A_news",
    "news_structured": "A_news",
    "fund_prose": "B_fund",
    "fund_structured": "B_fund",
}


def _build_config(mode: str, out_dir: Path) -> dict:
    """Build TradingAgentsConfig with mode-specific analyst-format overrides."""
    config = dict(DEFAULT_CONFIG)
    config["llm_provider"] = "anthropic"
    config["deep_think_llm"] = "claude-sonnet-4-6"
    config["quick_think_llm"] = "claude-haiku-4-5"
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1
    config["checkpoint_enabled"] = False
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }
    config["memory_log_path"] = str(out_dir / "br3_v2_pilot_memory.md")
    overrides = MODES[mode]
    config.update(overrides)
    return config


def _load_completed(out_csv: Path) -> set[tuple[str, str, str]]:
    if not out_csv.exists():
        return set()
    completed: set[tuple[str, str, str]] = set()
    with out_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            completed.add((row["ticker"], row["date"], row["mode"]))
    return completed


def _append_row(out_csv: Path, row: dict) -> None:
    write_header = not out_csv.exists()
    with out_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _run_propagate(ticker: str, date: str, mode: str, out_dir: Path) -> dict:
    config = _build_config(mode, out_dir)
    start = time.perf_counter()
    sub_exp = MODE_TO_SUB_EXPERIMENT[mode]
    try:
        ta = TradingAgentsGraph(debug=False, config=config)
        _final_state, decision = ta.propagate(ticker, date)
        elapsed = time.perf_counter() - start
        return {
            "ticker": ticker,
            "date": date,
            "sub_experiment": sub_exp,
            "mode": mode,
            "rating": decision,
            "error": "",
            "run_seconds": f"{elapsed:.1f}",
        }
    except Exception as exc:  # noqa: BLE001
        elapsed = time.perf_counter() - start
        return {
            "ticker": ticker,
            "date": date,
            "sub_experiment": sub_exp,
            "mode": mode,
            "rating": "",
            "error": f"{type(exc).__name__}: {exc}",
            "run_seconds": f"{elapsed:.1f}",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", default="NVDA,AAPL")
    parser.add_argument("--dates", default=",".join(DEFAULT_DATES))
    parser.add_argument(
        "--out",
        default="experiments/2026-05-09-003-br3-v2-news-fundamentals/results.csv",
    )
    parser.add_argument(
        "--modes",
        default=",".join(MODES.keys()),
        help="Comma-separated modes (default: all 4)",
    )
    parser.add_argument("--yes", action="store_true", help="Skip cost-confirmation prompt")
    args = parser.parse_args()

    load_dotenv()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    dates = [d.strip() for d in args.dates.split(",") if d.strip()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    grid = [(ticker, date, mode) for ticker in tickers for date in dates for mode in modes]
    n_grid = len(grid)
    cost_estimate = n_grid * 0.40

    out_csv = Path(args.out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    completed = _load_completed(out_csv)
    remaining = [g for g in grid if g not in completed]

    print(
        f"BR-3 v2 pilot: {n_grid} total propagates, {len(completed)} already done, "
        f"{len(remaining)} remaining"
    )
    print(
        f"Estimated cost: ${cost_estimate:.2f} (full grid). Cost remaining: ${len(remaining) * 0.40:.2f}"
    )
    if not args.yes:
        resp = input("Proceed? [y/N] ").strip().lower()
        if resp != "y":
            print("Aborted.")
            sys.exit(0)

    for i, (ticker, date, mode) in enumerate(remaining, start=1):
        print(f"[{i}/{len(remaining)}] {ticker} {date} {mode}")
        row = _run_propagate(ticker, date, mode, out_csv.parent)
        _append_row(out_csv, row)
        if row["error"]:
            print(f"  ERROR: {row['error']}")
        else:
            print(f"  rating: {row['rating']} ({row['run_seconds']}s)")
        time.sleep(1)


if __name__ == "__main__":
    main()
