"""Phase 4 bot_models live-propagate validation driver.

Runs ONE NVDA propagate(2026-01-30) with config["bot_models"] set so that
the market analyst routes through the per-bot factory while every other
bot uses the framework defaults. Captures the BotLLMFactory log line as
proof the override path was taken; writes a one-row results.csv.
"""

from __future__ import annotations

import csv
import io
import logging
import sys
import time
from copy import deepcopy
from pathlib import Path

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

EXPERIMENT_ID = "2026-05-04-007-phase4-bot-models-smoke"
TICKER = "NVDA"
ANALYSIS_DATE = "2026-01-30"
EXPERIMENT_DIR = Path(__file__).resolve().parent

OVERRIDE_BOT = "market"
OVERRIDE_MODEL = "claude-sonnet-4-6"


def build_config() -> dict:
    """Construct the propagate() config — same shape as scripts/backtest.py
    sets, plus the Phase 4 bot_models override.
    """
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
    # Phase 4: per-bot override
    config["bot_models"] = {OVERRIDE_BOT: OVERRIDE_MODEL}
    return config


def main() -> int:
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
    factory_logger = logging.getLogger("tradingagents.signals.role_models")
    factory_logger.addHandler(handler)
    factory_logger.setLevel(logging.INFO)

    config = build_config()
    print(f"[experiment] {EXPERIMENT_ID}")
    print(f"[config] bot_models = {config['bot_models']}")
    print("[graph] building TradingAgentsGraph...")
    ta = TradingAgentsGraph(
        selected_analysts=["market", "news", "fundamentals"],
        debug=False,
        config=config,
    )

    # Verify the factory was constructed with bot_models
    assert ta.bot_llm_factory is not None, "BotLLMFactory not wired"
    assert ta.bot_llm_factory.config.get("bot_models") == {OVERRIDE_BOT: OVERRIDE_MODEL}, (
        "bot_models not propagated to factory"
    )

    print(f"[propagate] {TICKER} {ANALYSIS_DATE}...")
    t0 = time.perf_counter()
    rating = ""
    error = ""
    try:
        _, rating_value = ta.propagate(TICKER, ANALYSIS_DATE)
        rating = str(rating_value).strip()
    except Exception as e:  # noqa: BLE001
        error = f"{type(e).__name__}: {e}"
    elapsed = round(time.perf_counter() - t0, 2)

    factory_log = log_capture.getvalue()
    instantiation_line = (
        f"BotLLMFactory: instantiated anthropic/{OVERRIDE_MODEL}"
    )
    override_path_taken = instantiation_line in factory_log

    print(f"[result] rating={rating!r}  error={error!r}  seconds={elapsed}")
    print(f"[factory_log]\n{factory_log}")
    print(f"[verification] override path taken: {override_path_taken}")
    print(
        f"[verification] cache populated: "
        f"{('anthropic', OVERRIDE_MODEL) in ta.bot_llm_factory._cache}"
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
        "override_bot",
        "override_model",
        "override_path_taken",
        "cache_populated",
    ]
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
            "override_bot": OVERRIDE_BOT,
            "override_model": OVERRIDE_MODEL,
            "override_path_taken": override_path_taken,
            "cache_populated": ("anthropic", OVERRIDE_MODEL)
            in ta.bot_llm_factory._cache,
        })
    print(f"[csv] {out_csv}")

    success = (
        not error
        and rating
        and override_path_taken
        and ("anthropic", OVERRIDE_MODEL) in ta.bot_llm_factory._cache
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
