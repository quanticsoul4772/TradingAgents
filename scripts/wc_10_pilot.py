"""WC-10 Continuous Scalar Rating v1 pilot harness.

Per specs/108-wc-10-continuous-scalar-rating/tasks.md T015 + spec.md SC-005.

Test grid: 10 dates × 2 tickers × 2 modes (wc_10 + 5tier_baseline) = 40
propagates × ~$0.40 = ~$16 LLM. Constitution III T2 (≤$30).

Resume-on-crash: appends to existing CSV; skips (ticker, date, mode)
triples already present. Mirror pattern from scripts/backtest.py.

Usage:
    uv run --no-sync python scripts/wc_10_pilot.py [--tickers NVDA,AAPL] [--out experiments/<dir>/results.csv]

Output schema (per data-model.md):
    ticker, date, mode, rating, binned_tier, error, run_seconds
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
from tradingagents.graph.signal_processing import (  # noqa: E402
    extract_scalar_rating,
)
from tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: E402
from tradingagents.wc_10 import bin_scalar_to_tier  # noqa: E402

DEFAULT_DATES = [
    "2026-04-01",
    "2026-04-02",
    "2026-04-08",
    "2026-04-09",
    "2026-04-15",
    "2026-04-16",
    "2026-04-22",
    "2026-04-23",
    "2026-04-29",
    "2026-04-30",
]

CSV_HEADER = ["ticker", "date", "mode", "rating", "binned_tier", "error", "run_seconds"]


def _build_config(mode: str, out_dir: Path) -> dict:
    """Build TradingAgentsConfig with mode-specific WC-10 overrides."""
    config = DEFAULT_CONFIG.copy()
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
    # Memory log isolation (per Constitution I): segregate from operator's real memory
    config["memory_log_path"] = str(out_dir / "wc10_pilot_memory.md")
    if mode == "wc_10":
        config["wc_10_enabled"] = True
        config["wc_10_filter_mode"] = "bypass"
        config["wc_10_bin_thresholds"] = (-0.6, -0.2, 0.2, 0.6)
    else:
        config["wc_10_enabled"] = False
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
    """Run one propagate; return CSV row."""
    config = _build_config(mode, out_dir)
    start = time.perf_counter()
    try:
        ta = TradingAgentsGraph(debug=False, config=config)
        final_state, decision = ta.propagate(ticker, date)
        elapsed = time.perf_counter() - start

        # propagate() returns (final_state, signal_processor_output) where the
        # second element is the 5-tier tier extracted via process_signal().
        # For WC-10 mode we need the FULL markdown (final_state['final_trade_decision'])
        # to extract the scalar; the already-extracted `decision` is the 5-tier
        # fallback ("Hold" when no 5-tier match found in scalar markdown).
        markdown = final_state.get("final_trade_decision", "") or ""

        if mode == "wc_10":
            rating_scalar = extract_scalar_rating(markdown)
            if rating_scalar is None:
                return {
                    "ticker": ticker,
                    "date": date,
                    "mode": mode,
                    "rating": "",
                    "binned_tier": "",
                    "error": "scalar_extraction_failed",
                    "run_seconds": f"{elapsed:.1f}",
                }
            binned = bin_scalar_to_tier(rating_scalar)
            return {
                "ticker": ticker,
                "date": date,
                "mode": mode,
                "rating": f"{rating_scalar:+.4f}",
                "binned_tier": binned,
                "error": "",
                "run_seconds": f"{elapsed:.1f}",
            }
        else:
            # 5-tier baseline: `decision` is already the 5-tier string from
            # SignalProcessor.process_signal() — use directly.
            return {
                "ticker": ticker,
                "date": date,
                "mode": mode,
                "rating": decision,
                "binned_tier": decision,  # already a tier
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
            "binned_tier": "",
            "error": f"{type(exc).__name__}: {exc}",
            "run_seconds": f"{elapsed:.1f}",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", default="NVDA,AAPL")
    parser.add_argument("--dates", default=",".join(DEFAULT_DATES))
    parser.add_argument(
        "--out",
        default="experiments/2026-05-08-001-wc-10-pilot/results.csv",
    )
    parser.add_argument(
        "--modes",
        default="wc_10,5tier_baseline",
        help="Comma-separated modes to run (default: both)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip cost-confirmation prompt",
    )
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
            print(f"rating={row['rating']} ({row['binned_tier']}) — {row['run_seconds']}s")
        time.sleep(1)  # rate-limit cushion

    elapsed_total = time.perf_counter() - start_total
    print(f"\nCompleted {len(remaining)} propagates in {elapsed_total:.1f}s")


if __name__ == "__main__":
    main()
