"""Spec 003 SC-001 shadow-smoke validation driver.

Runs ONE NVDA propagate(2026-01-30) with contrarian_gate_mode="shadow" and
verifies:
1. State log carries the contrarian_gate block
2. Gate is NOT skipped (NVDA cache has 33 rows, above the N=20 floor)
3. feature_value, percentile, n_history, would_fire all populated
4. gate_fired == False (shadow mode, no override)
5. pm_rating_pre_gate == pm_rating_post_gate
6. Final decision text contains no [Spec 003 contrarian gate] annotation

Writes a one-row results.csv summarizing the validation.
"""

from __future__ import annotations

import csv
import sys
import time
from copy import deepcopy
from pathlib import Path

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

EXPERIMENT_ID = "2026-05-05-001-spec003-sc001-shadow-smoke"
TICKER = "NVDA"
ANALYSIS_DATE = "2026-01-30"
EXPERIMENT_DIR = Path(__file__).resolve().parent


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
    # Spec 003: enable shadow mode
    config["contrarian_gate_mode"] = "shadow"
    return config


def main() -> int:
    config = build_config()
    print(f"[experiment] {EXPERIMENT_ID}")
    print(f"[config] contrarian_gate_mode = {config['contrarian_gate_mode']}")
    print("[graph] building TradingAgentsGraph...")
    ta = TradingAgentsGraph(
        selected_analysts=["market", "news", "fundamentals"],
        debug=False,
        config=config,
    )

    print(f"[propagate] {TICKER} {ANALYSIS_DATE}...")
    t0 = time.perf_counter()
    rating = ""
    error = ""
    final_state = None
    try:
        final_state, rating_value = ta.propagate(TICKER, ANALYSIS_DATE)
        rating = str(rating_value).strip()
    except Exception as e:  # noqa: BLE001
        error = f"{type(e).__name__}: {e}"
    elapsed = round(time.perf_counter() - t0, 2)
    print(f"[result] rating={rating!r}  error={error!r}  seconds={elapsed}")

    # SC-001 validation
    gate_block = (final_state or {}).get("contrarian_gate")
    decision_md = (final_state or {}).get("final_trade_decision", "")

    checks: dict[str, bool | str | None] = {
        "completed_no_error": not error,
        "gate_block_present": gate_block is not None,
        "gate_block_is_dict": isinstance(gate_block, dict),
    }
    if isinstance(gate_block, dict):
        checks["mode_is_shadow"] = gate_block.get("mode") == "shadow"
        checks["gate_skipped_is_none"] = gate_block.get("gate_skipped") is None
        checks["feature_value_populated"] = isinstance(
            gate_block.get("feature_value"), (int, float)
        )
        pct = gate_block.get("percentile")
        checks["percentile_in_range"] = (
            isinstance(pct, (int, float)) and 0.0 <= pct <= 100.0
        )
        n_hist = gate_block.get("n_history")
        checks["n_history_at_floor"] = isinstance(n_hist, int) and n_hist >= 20
        checks["gate_fired_is_false"] = gate_block.get("gate_fired") is False
        pre = gate_block.get("pm_rating_pre_gate")
        post = gate_block.get("pm_rating_post_gate")
        checks["pre_post_rating_match"] = pre == post
    checks["no_active_annotation_in_decision"] = (
        "[Spec 003 contrarian gate]" not in decision_md
    )

    print("\n[validation]")
    for name, result in checks.items():
        marker = "✓" if result is True else ("✗" if result is False else "?")
        print(f"  {marker} {name}: {result}")

    print("\n[gate_block]")
    if isinstance(gate_block, dict):
        for k, v in gate_block.items():
            print(f"  {k}: {v}")
    else:
        print(f"  (not a dict: {gate_block!r})")

    # Write results.csv
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
        "validation_all_pass",
    ]
    g = gate_block if isinstance(gate_block, dict) else {}
    all_pass = all(v is True for v in checks.values())
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "ticker": TICKER,
            "analysis_date": ANALYSIS_DATE,
            "rating": rating,
            "error": error,
            "run_seconds": elapsed,
            "deep_model": "claude-opus-4-7",
            "quick_model": "claude-haiku-4-5",
            "debate_rounds": 1,
            "analysts": "market,news,fundamentals",
            "experiment_id": EXPERIMENT_ID,
            "gate_mode": g.get("mode", ""),
            "gate_skipped": g.get("gate_skipped", "") or "",
            "feature_value": g.get("feature_value", ""),
            "percentile": g.get("percentile", ""),
            "n_history": g.get("n_history", ""),
            "would_fire": g.get("would_fire", ""),
            "gate_fired": g.get("gate_fired", ""),
            "pre_rating": g.get("pm_rating_pre_gate", ""),
            "post_rating": g.get("pm_rating_post_gate", ""),
            "validation_all_pass": all_pass,
        })
    print(f"\n[csv] {out_csv}")
    print(f"[verdict] all_pass = {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
