"""Spec 003 historical-recompute — backfill bull_keyword_count cache from
existing experiment state logs.

Per `claudedocs/spec-003-cold-start-diagnostic-sc-009-2026-05-07.md`
(PR #68): 22 of 36 SC-009 rows had `gate_baseline=none` because the
spec 003 cache lacked sufficient per-ticker / sector history. The
underlying `market_report` prose is in every state log; the cache just
hasn't been populated for older runs.

This script walks all state logs under `~/.tradingagents/logs/<TICKER>/`,
extracts `market_report` from each, computes the bull_keyword_count
featurizer value, and writes it to the cache via `record_value`. Future
spec 003 propagates will see more per-ticker history immediately.

Zero LLM cost (pure post-processing of saved state). Idempotent —
INSERT OR REPLACE on the cache schema makes re-runs safe.

Usage:
    python scripts/spec_003_historical_recompute.py
    python scripts/spec_003_historical_recompute.py --dry-run
    python scripts/spec_003_historical_recompute.py --tickers NVDA,AAPL
    python scripts/spec_003_historical_recompute.py --feature bear_keyword_count
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.signals.cache import (  # noqa: E402
    init_cache,
    query_value,
    record_value,
)
from tradingagents.signals.featurization import FEATURIZERS  # noqa: E402

LOG_BASE = Path(os.getenv("TRADINGAGENTS_RESULTS_DIR", os.path.expanduser("~/.tradingagents/logs")))


def _resolve_featurizer(feature_name: str):
    for name, fn in FEATURIZERS:
        if name == feature_name:
            return fn
    return None


def _list_state_logs(ticker_filter: set[str] | None) -> list[tuple[str, str, Path]]:
    """Walk LOG_BASE and yield (ticker, date, path) for every state log."""
    out = []
    if not LOG_BASE.exists():
        return out
    for ticker_dir in sorted(LOG_BASE.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        if ticker_filter and ticker.upper() not in ticker_filter:
            continue
        log_dir = ticker_dir / "TradingAgentsStrategy_logs"
        if not log_dir.exists():
            continue
        for log_file in sorted(log_dir.glob("full_states_log_*.json")):
            date = log_file.stem.replace("full_states_log_", "")
            out.append((ticker, date, log_file))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--feature",
        default="bull_keyword_count",
        help="Featurizer name from FEATURIZERS registry (default: bull_keyword_count)",
    )
    parser.add_argument(
        "--signal-id",
        default="market_report",
        help="State-log key to extract prose from (default: market_report)",
    )
    parser.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated ticker filter (default: all tickers under LOG_BASE)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to cache; just print what would be written.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip rows where the cache already has a value (otherwise INSERT OR REPLACE).",
    )
    args = parser.parse_args()

    featurizer = _resolve_featurizer(args.feature)
    if featurizer is None:
        valid_names = [name for name, _ in FEATURIZERS]
        print(
            f"ERROR: featurizer {args.feature!r} not found. Valid: {valid_names}",
            file=sys.stderr,
        )
        return 2

    ticker_filter = {t.strip().upper() for t in args.tickers.split(",")} if args.tickers else None

    print(f"# Spec 003 historical-recompute — feature={args.feature} signal_id={args.signal_id}")
    print()
    print(f"Log base: {LOG_BASE}")
    print(f"Ticker filter: {ticker_filter or '(all)'}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'WRITE'}")
    print(f"Skip existing: {args.skip_existing}")
    print()

    if not args.dry_run:
        init_cache()

    state_logs = _list_state_logs(ticker_filter)
    print(f"Found {len(state_logs)} state logs to process")
    print()

    n_processed = 0
    n_written = 0
    n_skipped_existing = 0
    n_skipped_no_prose = 0
    n_skipped_featurizer_error = 0
    n_skipped_load_error = 0
    by_ticker: dict[str, int] = defaultdict(int)

    for ticker, date, log_path in state_logs:
        n_processed += 1
        try:
            d = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] {ticker}/{date}: failed to load: {exc}")
            n_skipped_load_error += 1
            continue

        prose = d.get(args.signal_id, "") or ""
        if not prose.strip():
            n_skipped_no_prose += 1
            continue

        try:
            value = float(featurizer(prose))
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] {ticker}/{date}: featurizer failed: {exc}")
            n_skipped_featurizer_error += 1
            continue

        if args.skip_existing:
            existing = query_value(args.signal_id, ticker, date)
            if existing is not None:
                n_skipped_existing += 1
                continue

        if args.dry_run:
            print(f"  [DRY] {ticker}/{date}: {args.feature}={value}")
        else:
            record_value(
                signal_id=args.signal_id,
                ticker=ticker,
                date=date,
                value=value,
            )
            n_written += 1
            by_ticker[ticker] += 1

    print()
    print("## Summary")
    print()
    print(f"- State logs scanned: {n_processed}")
    print(f"- Written to cache: {n_written}")
    print(f"- Skipped (existing): {n_skipped_existing}")
    print(f"- Skipped (no prose in {args.signal_id}): {n_skipped_no_prose}")
    print(f"- Skipped (featurizer error): {n_skipped_featurizer_error}")
    print(f"- Skipped (load error): {n_skipped_load_error}")
    print()
    if by_ticker:
        print("## Per-ticker writes")
        print()
        for t in sorted(by_ticker.keys()):
            print(f"- {t}: {by_ticker[t]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
