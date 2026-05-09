"""WC-11 order randomization pilot harness.

Per `experiments/2026-05-08-004-wc11-order-randomization/HYPOTHESIS.md`.

Test grid: 5 dates × 1 ticker (NVDA) × 4 analyst-order permutations =
20 propagates × ~$0.40 = ~$8 LLM (T1, ≤$10).

Tests whether the framework's fixed [market, news, fundamentals] analyst
order is a confounding "first-speaker bias" affecting prior corpus claims.
NULL = order-independent synthesis; ALT-A = first-speaker bias; ALT-B =
last-speaker (recency) bias.

Mirrors `scripts/wc_10_pilot.py` + `scripts/br3_squeak_pilot.py` shape.
Implementation Option B from HYPOTHESIS: no structural code change to
trading_graph.py — varies `selected_analysts` parameter passed to
TradingAgentsGraph constructor (already supported per setup.py edge
construction).

Output schema:
    ticker, date, mode, rating, error, run_seconds

(`mode` is the permutation key like "market_news_fundamentals" or
"news_fundamentals_market"; `rating` is the standard 5-tier from PM.)

Usage:
    python scripts/wc11_order_pilot.py [--tickers NVDA] [--out experiments/<dir>/results.csv]
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

# Permutations chosen to maximize first-and-last analyst variation per
# HYPOTHESIS section "Permutations". 4 of 24 possible orderings (3! = 6
# unique orderings of 3 analysts; 4 chosen to cover first-vs-last
# variations).
PERMUTATIONS = {
    "market_news_fundamentals": ["market", "news", "fundamentals"],  # DEFAULT
    "news_fundamentals_market": ["news", "fundamentals", "market"],
    "fundamentals_market_news": ["fundamentals", "market", "news"],
    "market_fundamentals_news": ["market", "fundamentals", "news"],
}

CSV_HEADER = ["ticker", "date", "mode", "rating", "error", "run_seconds"]


def _build_config(out_dir: Path) -> dict:
    """Build TradingAgentsConfig (mode-independent for WC-11; order is via
    selected_analysts parameter, not config)."""
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
    config["memory_log_path"] = str(out_dir / "wc11_pilot_memory.md")
    return config


def _load_completed(out_csv: Path) -> set[tuple[str, str, str]]:
    """Resume-on-crash: load (ticker, date, mode) triples already in the CSV."""
    if not out_csv.exists():
        return set()
    completed: set[tuple[str, str, str]] = set()
    with out_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            completed.add((row["ticker"], row["date"], row["mode"]))
    return completed


def _append_row(out_csv: Path, row: dict) -> None:
    """Append-on-each-row: survives Ctrl+C."""
    write_header = not out_csv.exists()
    with out_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _run_propagate(ticker: str, date: str, mode: str, out_dir: Path) -> dict:
    """Run one propagate with the specified analyst order; return CSV row."""
    config = _build_config(out_dir)
    selected_analysts = PERMUTATIONS[mode]
    start = time.perf_counter()
    try:
        ta = TradingAgentsGraph(
            selected_analysts=selected_analysts,
            debug=False,
            config=config,
        )
        _final_state, decision = ta.propagate(ticker, date)
        elapsed = time.perf_counter() - start
        return {
            "ticker": ticker,
            "date": date,
            "mode": mode,
            "rating": decision,  # standard 5-tier from PM
            "error": "",
            "run_seconds": f"{elapsed:.1f}",
        }
    except Exception as exc:  # noqa: BLE001
        elapsed = time.perf_counter() - start
        return {
            "ticker": ticker,
            "date": date,
            "mode": mode,
            "rating": "",
            "error": f"{type(exc).__name__}: {exc}",
            "run_seconds": f"{elapsed:.1f}",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", default="NVDA")
    parser.add_argument("--dates", default=",".join(DEFAULT_DATES))
    parser.add_argument(
        "--out",
        default="experiments/2026-05-08-004-wc11-order-randomization/results.csv",
    )
    parser.add_argument(
        "--modes",
        default=",".join(PERMUTATIONS.keys()),
        help=(
            "Comma-separated permutation keys to run (default: all 4). "
            f"Available: {', '.join(PERMUTATIONS.keys())}"
        ),
    )
    parser.add_argument("--yes", action="store_true", help="Skip cost-confirmation prompt")
    args = parser.parse_args()

    load_dotenv()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    dates = [d.strip() for d in args.dates.split(",") if d.strip()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    out_csv = Path(args.out)
    out_dir = out_csv.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    grid = [(t, d, m) for t in tickers for d in dates for m in modes]
    completed = _load_completed(out_csv)
    remaining = [g for g in grid if g not in completed]

    est_cost = len(remaining) * 0.40
    print(f"Grid: {len(grid)} (ticker × date × mode); already-completed: {len(completed)}")
    print(f"Remaining: {len(remaining)} propagates × ~$0.40 = ~${est_cost:.2f} estimated cost")
    print(f"Output: {out_csv}")
    print()

    if not args.yes and remaining:
        try:
            response = input("Proceed? [y/N]: ").strip().lower()
        except EOFError:
            response = "n"
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    start_total = time.perf_counter()
    for i, (ticker, date, mode) in enumerate(remaining, 1):
        print(f"[{i}/{len(remaining)}] {ticker} {date} {mode}...", end=" ", flush=True)
        row = _run_propagate(ticker, date, mode, out_dir)
        _append_row(out_csv, row)
        if row["error"]:
            print(f"ERROR ({row['error'][:60]}) — {row['run_seconds']}s")
        else:
            print(f"rating={row['rating']} — {row['run_seconds']}s")
        time.sleep(1)

    elapsed_total = time.perf_counter() - start_total
    print(f"\nCompleted {len(remaining)} propagates in {elapsed_total:.1f}s")


if __name__ == "__main__":
    main()
