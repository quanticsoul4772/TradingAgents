import os
from typing import Literal, TypedDict

_TRADINGAGENTS_HOME = os.path.join(os.path.expanduser("~"), ".tradingagents")


class TradingAgentsConfig(TypedDict):
    """Typed schema for the framework's runtime config.

    Defined as a TypedDict (rather than a Pydantic model or dataclass) so that
    `DEFAULT_CONFIG` and the dict that flows through `get_config()` /
    `set_config()` continue to behave as plain dicts at runtime — preserving
    backwards compatibility with the many call sites that use `.get(key)`,
    `.update(...)`, and dict-merge patterns. Mypy uses this schema to type
    each `cfg["key"]` access; runtime behavior is unchanged.

    Added 2026-05-06 to eliminate the dominant source of the historical
    175-error mypy baseline (untyped config dict flooding `conditional_logic.py`,
    LLM clients, and `trading_graph.py` with arg-type / union-attr noise).
    """

    project_dir: str
    results_dir: str
    data_cache_dir: str
    memory_log_path: str
    memory_log_max_entries: int | None
    llm_provider: str
    deep_think_llm: str
    quick_think_llm: str
    backend_url: str | None
    google_thinking_level: str | None
    openai_reasoning_effort: str | None
    anthropic_effort: str | None
    checkpoint_enabled: bool
    output_language: str
    max_debate_rounds: int
    max_risk_discuss_rounds: int
    max_recur_limit: int
    pm_sees_synthesis: bool
    research_manager_prompt_variant: str
    uw_momentum_filter_threshold: float | None
    uw_momentum_filter_lookback_days: int
    second_opinion_enabled: bool
    second_opinion_agree_threshold: float
    second_opinion_disagree_threshold: float
    framework_mode: Literal["prose", "bots"]
    contrarian_gate_mode: Literal["off", "shadow", "active"]
    contrarian_gate_threshold: int
    contrarian_gate_target: Literal["hold", "underweight"]
    contrarian_gate_signal: str
    contrarian_gate_feature: str
    contrarian_gate_sector_fallback_enabled: bool
    contrarian_gate_sector_floor: int
    sector_momentum_filter_mode: Literal["off", "shadow", "active"]
    sector_momentum_filter_threshold_pct: float | None
    sector_momentum_filter_lookback_days: int
    bot_models: dict[str, str]
    data_vendors: dict[str, str]
    tool_vendors: dict[str, str]
    paper_state_dir: str
    paper_digest_dir: str


DEFAULT_CONFIG: TradingAgentsConfig = {
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
    # to Hold on tickers in mean-reversion zone.
    # **Default flipped from None → -5.0 on 2026-05-06** after corpus-wide
    # retrospective (`scripts/uw_suppression_filter.py`) showed +0.70pp Δα
    # improvement at -5% threshold across the 43-UW-commit corpus, positive
    # at every threshold tested in the -5 to -10% range. Set to None in a
    # specific experiment's PARAMS.json to ablate. In-sample caveat applies.
    "uw_momentum_filter_threshold": -5.0,
    "uw_momentum_filter_lookback_days": 30,
    # Phase C: independent second-opinion review of PM decisions. When True,
    # an extra LLM call evaluates the framework's commit against the same
    # evidence and annotates the decision markdown with agreement / neutral /
    # review-flag based on asymmetric thresholds. Never modifies the PM rating.
    # Adds ~$0.10/run forward cost when enabled. Default False = disabled.
    # See tradingagents/agents/utils/second_opinion.py for the asymmetry rules
    # and RESEARCH_FINDINGS Q5 for the reasoning_divergent synthesis that
    # motivated the asymmetric design.
    "second_opinion_enabled": False,
    "second_opinion_agree_threshold": 0.6,
    "second_opinion_disagree_threshold": 0.4,
    # Spec 001 Phase 2: framework mode. "prose" (default) = current LLM-based
    # PM pipeline. "bots" = route the final rating through the deterministic
    # aggregator in tradingagents/signals/bots.py (skips LLM PM call). Phase 1
    # (shadow mode) always logs the aggregator output alongside the actual PM
    # rating regardless of this flag; Phase 2 uses this flag to override the
    # actual final_trade_decision when set to "bots".
    "framework_mode": "prose",
    # Spec 003: analyst-stage contrarian gate. Empirically motivated by
    # RESEARCH_FINDINGS finding #4 (within-ticker IC -0.489 for
    # market_report bull_keyword_count vs 90d α). Gate measures the
    # current propagate's bull_keyword_count percentile against the most
    # recent N=20 cached values for THIS ticker; in active mode, when
    # percentile >= threshold AND PM rating is Buy/Overweight, the rating
    # is downgraded to Hold (or Underweight per target).
    # **Default mode flipped from "off" → "active" on 2026-05-06** after
    # corpus-wide retrospective (`scripts/contrarian_gate_retrospective.py`)
    # showed +6.46% cumulative Δα at 21d at the production-default N>=20
    # history floor (FR-004). The N>=5 permissive floor would HURT alpha
    # by -24.87% — confirming FR-004's amendment to N=20 is load-bearing
    # and cannot be loosened. Set to "off" in a specific experiment's
    # PARAMS.json to ablate. See claudedocs/contrarian-gate-retrospective-2026-05-05.md.
    "contrarian_gate_mode": "active",  # "off" | "shadow" | "active"
    "contrarian_gate_threshold": 80,  # percentile threshold
    "contrarian_gate_target": "hold",  # "hold" | "underweight"
    "contrarian_gate_signal": "market_report",  # pluggable per spec User Story 4
    "contrarian_gate_feature": "bull_keyword_count",  # pluggable per spec User Story 4
    # Spec 003.5 (specs/003-sector-baseline-gate/spec.md): sector-baseline
    # fallback for cold-start tickers. When per-ticker history is below
    # contrarian_gate_threshold's N>=20 floor, the gate falls back to
    # aggregating bull_keyword_count history across same-sector tickers.
    # Set to False for ablation experiments comparing spec-003-only vs
    # spec-003+sector. Empirical motivation: SC-003 Financials investigation
    # showed 4 of 5 losing OW commits had zero per-ticker history.
    "contrarian_gate_sector_fallback_enabled": True,
    "contrarian_gate_sector_floor": 20,
    # Spec 004 (specs/004-sector-momentum-filter/spec.md): suppress Buy/OW
    # commits to Hold when the ticker's sector ETF is in mean-reversion
    # zone (down >threshold% in prior N trading days). Default-off per
    # Constitution II ablation discipline; corpus retrospective gate
    # (scripts/sector_momentum_retrospective.py + SC-008) before any
    # default-on flip. Threshold = None IS the off switch.
    "sector_momentum_filter_mode": "off",
    "sector_momentum_filter_threshold_pct": None,
    "sector_momentum_filter_lookback_days": 30,
    # Spec 001 Phase 4: per-bot LLM model routing. Maps bot_id -> model_name
    # (str). When set, the framework instantiates a per-bot client for that
    # model using the configured llm_provider; bots not in this dict use the
    # role default (quick_think_llm or deep_think_llm). Default empty dict
    # = uniform model behavior, no override (FR-007 backwards-compat).
    # Example: {"market": "claude-haiku-4-5", "fundamentals": "claude-opus-4-7"}.
    # Per spec FR-008, the chosen model is logged per bot for cost analysis.
    "bot_models": {},
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
    # Paper-trading harness state + digest directories. Spec 002.
    # State files (`<id>.json`, `<id>.events.jsonl`) live under paper_state_dir.
    # Daily digests are written to paper_digest_dir as `paper-<id>-<date>.md`.
    # paper_state_dir defaults to the paper subdir of TRADINGAGENTS_CACHE_DIR
    # if set, else `~/.tradingagents/paper/`.
    "paper_state_dir": os.path.join(
        os.getenv("TRADINGAGENTS_CACHE_DIR", _TRADINGAGENTS_HOME), "paper"
    ),
    "paper_digest_dir": "claudedocs",
}
