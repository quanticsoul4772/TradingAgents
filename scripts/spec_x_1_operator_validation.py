"""Spec X-1 operator validation — runs 1 propagate + verifies state-log annotation.

Per claudedocs/SETUP.md section 10.2, the deployed Spec X-1 (C-4
institutional rotation filter) at default-shadow bear-side should
populate state["forward_catalyst"]["institutional_rotation"] with 8
fields after every propagate. This script runs a single propagate on
NVDA at a recent date and verifies the annotation appears with the
expected schema.

Cost: ~$0.40 (Sonnet deep + Haiku quick; 1 propagate).

Usage:
    python scripts/spec_x_1_operator_validation.py [--ticker NVDA] [--date 2026-05-01]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: E402

EXPECTED_FIELDS = {
    "net_rotation_pct",
    "outflow_threshold",
    "bear_mode",
    "bull_mode",
    "would_fire_bear",
    "fired_bear",
    "pre_rating",
    "post_rating",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="NVDA")
    parser.add_argument("--date", default="2026-05-01")
    args = parser.parse_args()

    load_dotenv()

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

    print(f"[validation] Propagating {args.ticker} @ {args.date}...")
    ta = TradingAgentsGraph(debug=False, config=config)
    final_state, decision = ta.propagate(args.ticker, args.date)

    print(f"[validation] PM decision: {decision}")
    print()

    fc = final_state.get("forward_catalyst") or {}
    ir = fc.get("institutional_rotation")

    if ir is None:
        print("[validation] FAIL — state['forward_catalyst']['institutional_rotation'] is None")
        print("[validation] Forward-catalyst keys present:", list(fc.keys()))
        sys.exit(1)

    print("[validation] state['forward_catalyst']['institutional_rotation']:")
    print(json.dumps(ir, indent=2, default=str))
    print()

    # Schema check
    actual_fields = set(ir.keys())
    missing = EXPECTED_FIELDS - actual_fields
    extra = actual_fields - EXPECTED_FIELDS

    if missing:
        print(f"[validation] FAIL — missing fields: {missing}")
        sys.exit(1)
    if extra:
        print(f"[validation] WARN — unexpected extra fields: {extra}")

    # Field type/value checks
    checks = []
    checks.append(("bear_mode is shadow (default)", ir["bear_mode"] == "shadow"))
    checks.append(("bull_mode is off (default)", ir["bull_mode"] == "off"))
    checks.append(("outflow_threshold is 0.05 (default)", ir["outflow_threshold"] == 0.05))
    checks.append(
        (
            "net_rotation_pct is float or None",
            isinstance(ir["net_rotation_pct"], float) or ir["net_rotation_pct"] is None,
        )
    )
    checks.append(("would_fire_bear is bool", isinstance(ir["would_fire_bear"], bool)))
    checks.append(("fired_bear is False (shadow mode)", ir["fired_bear"] is False))
    checks.append(
        (
            "pre_rating == post_rating (shadow mode preserves rating)",
            ir["pre_rating"] == ir["post_rating"],
        )
    )

    print("[validation] schema + value checks:")
    all_pass = True
    for label, ok in checks:
        marker = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{marker}] {label}")
    print()

    if all_pass:
        print("[validation] OVERALL PASS — Spec X-1 annotation appears correctly")
        sys.exit(0)
    else:
        print("[validation] OVERALL FAIL — see check failures above")
        sys.exit(1)


if __name__ == "__main__":
    main()
