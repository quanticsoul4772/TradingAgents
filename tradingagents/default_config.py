import os

_TRADINGAGENTS_HOME = os.path.join(os.path.expanduser("~"), ".tradingagents")

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv(
        "TRADINGAGENTS_RESULTS_DIR", os.path.join(_TRADINGAGENTS_HOME, "logs")
    ),
    "data_cache_dir": os.getenv(
        "TRADINGAGENTS_CACHE_DIR", os.path.join(_TRADINGAGENTS_HOME, "cache")
    ),
    "memory_log_path": os.getenv(
        "TRADINGAGENTS_MEMORY_LOG_PATH",
        os.path.join(_TRADINGAGENTS_HOME, "memory", "trading_memory.md"),
    ),
    # Optional cap on the number of resolved memory log entries. When set,
    # the oldest resolved entries are pruned once this limit is exceeded.
    # Pending entries are never pruned. None disables rotation entirely.
    "memory_log_max_entries": None,
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.4",
    "quick_think_llm": "gpt-5.4-mini",
    # When None, each provider's client falls back to its own default endpoint
    # (api.openai.com for OpenAI, generativelanguage.googleapis.com for Gemini, ...).
    # The CLI overrides this per provider when the user picks one. Keeping a
    # provider-specific URL here would leak (e.g. OpenAI's /v1 was previously
    # being forwarded to Gemini, producing malformed request URLs).
    "backend_url": None,
    # Provider-specific thinking configuration
    "google_thinking_level": None,  # "high", "minimal", etc.
    "openai_reasoning_effort": None,  # "medium", "high", "low"
    "anthropic_effort": None,  # "high", "medium", "low"
    # Checkpoint/resume: when True, LangGraph saves state after each node
    # so a crashed run can resume from the last successful step.
    "checkpoint_enabled": False,
    # Output language for analyst reports and final decision
    # Internal agent debate stays in English for reasoning quality
    "output_language": "English",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Experimental: when False, the Portfolio Manager does NOT see the
    # Research Manager's investment_plan (the bull/bear synthesis). Used by
    # experiments/2026-05-02-002-wc12-pm-blind/ to test whether the synthesis
    # is the dilution step in the framework's mode collapse to moderate
    # ratings. Default True = current behavior; flip via --config-override.
    "pm_sees_synthesis": True,
    # MR-3: Research Manager synthesis prompt + schema variant. "default"
    # / "v1" = original; "v2" = MR-3 fix that decouples "two-sided debate"
    # from "Hold-leaning rating" per docs/EXPERIMENT.md MR-2 finding.
    # Drives experiments/2026-05-02-004-mr3-synthesis-v2/.
    "research_manager_prompt_variant": "default",
    # A3: mean-reversion suppression filter for Underweight / Sell commits.
    # When set (e.g. -5.0 = "down >5% in 30d"), the PM overrides bear ratings
    # to Hold on tickers in mean-reversion zone. Default None = disabled.
    # See claudedocs/uw-suppression-filter.md for in-sample evidence.
    "uw_momentum_filter_threshold": None,
    "uw_momentum_filter_lookback_days": 30,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",  # Options: alpha_vantage, yfinance
        "technical_indicators": "yfinance",  # Options: alpha_vantage, yfinance
        "fundamental_data": "yfinance",  # Options: alpha_vantage, yfinance
        "news_data": "exa",  # Options: exa (default), alpha_vantage. Requires EXA_API_KEY.
        "macro_data": "yfinance",  # VIX, sector ETF strength — yfinance only
        "options_data": "yfinance",  # IV / put-call / max pain — yfinance only
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
}
