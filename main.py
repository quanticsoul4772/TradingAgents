from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

from dotenv import load_dotenv

load_dotenv()

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "anthropic"
config["deep_think_llm"] = "claude-sonnet-4-6"   # Research Manager + Portfolio Manager
config["quick_think_llm"] = "claude-haiku-4-5"   # analysts, trader, debaters
# NOTE: anthropic_effort (extended thinking) is only supported on Opus models.
# Sonnet/Haiku reject it with a 400. Leave unset unless you switch deep_think_llm to Opus.
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1
config["checkpoint_enabled"] = True              # resume on crash; per-ticker SQLite

config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "yfinance",
}

ta = TradingAgentsGraph(debug=True, config=config)

_, decision = ta.propagate("NVDA", "2026-04-30")
print(decision)
