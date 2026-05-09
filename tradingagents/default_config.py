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
    bear_sector_symmetry_filter_mode: Literal["off", "shadow", "active"]
    bear_sector_symmetry_filter_threshold_pct: float | None
    bear_sector_symmetry_filter_lookback_days: int
    forward_catalyst_bull_mode: Literal["off", "shadow", "active"]
    forward_catalyst_bear_mode: Literal["off", "shadow", "active"]
    forward_catalyst_bull_threshold: float
    forward_catalyst_bear_threshold: float
    forward_catalyst_model: str
    forward_catalyst_max_rationale_chars: int
    hybrid_c_calendar_boost_enabled: bool
    hybrid_c_calendar_boost_window_days: int
    hybrid_c_calendar_boost_magnitude: float
    analyst_pt_snapshot_enabled: bool
    institutional_rotation_bear_mode: Literal["off", "shadow", "active"]
    institutional_rotation_bull_mode: Literal["off", "shadow", "active"]
    institutional_rotation_outflow_threshold: float
    institutional_rotation_inflow_threshold: float
    class_4_macro_bear_mode: Literal["off", "shadow", "active"]
    class_4_macro_bull_mode: Literal["off", "shadow", "active"]
    class_4_macro_vix_threshold: float
    wc_10_enabled: bool
    wc_10_filter_mode: Literal["bypass", "passthrough"]
    wc_10_bin_thresholds: tuple[float, float, float, float]
    wc_10_internal_only: bool
    # BR-3 Squeak (per experiments/2026-05-09-001-br3-squeak-market-analyst/):
    # When "structured", swap market_analyst.py for market_analyst_structured.py
    # which emits Pydantic MarketAnalystSquared via second LLM call instead of
    # free-form prose. Default "prose" preserves existing behavior.
    market_analyst_format: Literal["prose", "structured"]
    news_analyst_format: Literal["prose", "structured"]
    fundamentals_analyst_format: Literal["prose", "structured"]
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
    # Spec 006 (specs/005-bear-sector-symmetry/spec.md): suppress UW/Sell
    # commits to Hold when the ticker has outperformed its sector ETF by
    # more than threshold% over the prior N trading days (counter-trend bear
    # suppression). Empirical motivation: today's sector-α attribution found
    # 18 of 37 bearish commits (48.6%) landed in ticker_strong with mean
    # α-vs-SPY = +28.02% — a cohort A3 misses entirely (A3 only fires on
    # ticker DOWN absolute; spec 006 fires on ticker UP relative to sector).
    # Default-off per Constitution II ablation discipline; corpus retrospective
    # gate (scripts/bear_sector_symmetry_retrospective.py + SC-008) before any
    # default-on flip. Threshold = None IS the off switch.
    "bear_sector_symmetry_filter_mode": "off",
    "bear_sector_symmetry_filter_threshold_pct": None,
    "bear_sector_symmetry_filter_lookback_days": 30,
    # Spec 007 (specs/006-forward-catalyst-gate/spec.md): forward-catalyst-aware
    # contrarian gate. FIRST forward-catalyst-aware filter — invokes an LLM (Opus
    # default) per propagate to score how widely the bull/bear case is already
    # absorbed by the market. Bull-side default-on @T=0.60 per Class 3 Opus
    # retrospective DECISIVE PASS (claudedocs/forward-catalyst-class3-opus-
    # retrospective-2026-05-06.md). Bear-side default-shadow per Constitution VIII
    # shadow-mode-first condition (n>=20 propagates before active flip). Adds
    # ~$0.025/propagate Opus cost (~$0.25/day for typical 10-ticker workflow).
    # Set BOTH modes to "off" to disable + zero cost (FR-013 escape hatch).
    "forward_catalyst_bull_mode": "active",
    "forward_catalyst_bear_mode": "shadow",
    "forward_catalyst_bull_threshold": 0.60,
    "forward_catalyst_bear_threshold": 0.50,
    "forward_catalyst_model": "claude-opus-4-7",
    "forward_catalyst_max_rationale_chars": 2000,
    # Spec 008: Hybrid C calendar boost — enhances spec 007's bull-side
    # by multiplying bull_case_priced_in by (1 + magnitude * boost) where
    # boost = max(0, 1 - days_to_next_earnings / window). Default OFF
    # (FR-007); operator opts in via PARAMS.json. When enabled,
    # window=14d + magnitude=0.5 are the empirically-grounded defaults
    # from claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md
    # (+3.35pp bull-side net Δα improvement vs Class 3 alone, n=37 fires
    # @ 92.6% cohort hit). Bull-only per FR-004; bear-side unchanged.
    # Zero LLM cost (Constitution III T0). See specs/007-calendar-boost-filter/.
    "hybrid_c_calendar_boost_enabled": False,
    "hybrid_c_calendar_boost_window_days": 14,
    "hybrid_c_calendar_boost_magnitude": 0.5,
    # Path C snapshot wiring (PR #73): when True, capture analyst PT panel +
    # recommendations distribution at propagate time and persist to
    # state["forward_catalyst"]["analyst_pt_snapshot"]. Unlocks future
    # C-3-class retrospectives by accumulating historical snapshots in state
    # logs (yfinance has no historical PT panels per PR #40 — snapshots
    # forward are the only way to build the time series). Default OFF;
    # zero behavior impact when disabled. ~50-200ms latency per propagate
    # when enabled (per PR #40 + PR #66 empirical timings). Zero LLM cost.
    "analyst_pt_snapshot_enabled": False,
    # Spec X-1 (specs/091-c4-institutional-rotation/): C-4 institutional
    # rotation filter. FIRST quantitative-flow bear-side filter — suppresses
    # Underweight/Sell commits to Hold when top 10 institutional holders'
    # net pctChange rotation is below -outflow_threshold. Default-shadow per
    # Constitution VIII v1.4.0 small-sample-caution sub-clause (n=12 cohort
    # from PR #75 retrospective). Bear-side empirical evidence: discrim
    # +10.29pp / hit 75.0% / net Δα +5.41pp at T_outflow=0.05. Additive
    # PASS vs Spec 007 bear (PR #77): +8.06pp Δα improvement / +69.23pp hit
    # improvement on union. Bull-side default-OFF (n=1 evidence too thin).
    # Set BOTH modes to "off" to disable + zero overhead.
    "institutional_rotation_bear_mode": "shadow",
    "institutional_rotation_bull_mode": "off",
    "institutional_rotation_outflow_threshold": 0.05,
    "institutional_rotation_inflow_threshold": 0.05,
    # Spec 012 Class 4 macro-environment filter (per
    # specs/012-class-4-macro-filter/spec.md). FIRST cross-asset/macro
    # filter. Suppresses Underweight/Sell commits to Hold when VIX
    # snapshot < threshold (default 18.0; risk-on environment correlates
    # with bear-side ticker_strong cohort counter-trend failures per
    # claudedocs/class4-macro-filter-retrospective-2026-05-09.md PASS
    # verdict at v1.4.0 + v1.4.3 gates). Bear-side default-shadow per
    # Constitution VIII v1.4.0 small-sample-caution sub-clause (n=8 fires
    # at recommended threshold; 30+ live fires required before default-on
    # flip per SC-010). Bull-side default-off (deferred). Naming: "Class 4"
    # = Spec 008 design doc numbering, NOT C-4 institutional rotation
    # (which became Spec X-1).
    "class_4_macro_bear_mode": "shadow",
    "class_4_macro_bull_mode": "off",
    "class_4_macro_vix_threshold": 18.0,
    # WC-10 (specs/108-wc-10-continuous-scalar-rating/): Tier 2 experiment to
    # test the categorical-bottleneck hypothesis. Replaces the framework's
    # 5-tier categorical PortfolioRating enum with a continuous scalar in
    # [-1, +1] (signed conviction magnitude). Default-OFF (operator opts in
    # via PARAMS.json). When enabled, filter-bypass mode (the v1 default)
    # SKIPS the entire 9-filter PM chain so the experiment is a clean
    # single-intervention test. bin_scalar_to_tier() pure function provides
    # 5-tier compatibility for ex-post analysis. v1 cost ~$16 LLM (40
    # propagates × ~$0.40); Constitution III T2 ≤$30. Per Principle IV,
    # NULL or INCONCLUSIVE results are valid. See spec.md SC-007 for the
    # 3 falsifiable predictions framework.
    "wc_10_enabled": False,
    "wc_10_filter_mode": "bypass",
    "wc_10_bin_thresholds": (-0.6, -0.2, 0.2, 0.6),
    # Spec 009 Branch C (per specs/009-wc-10-production-deployment/spec.md
    # User Story C.1): bin-then-output ergonomic-only mode. When True AND
    # wc_10_enabled=True, the LLM still emits a continuous scalar internally
    # but the rendered Rating header is binned to 5-tier via bin_scalar_to_tier
    # before downstream consumers see it. Default False preserves the v1+v2
    # research mode (raw scalar emission). Activated by Branch C verdict on
    # WC-10 v2 SC-005(b) NULL (Pearson r +0.0918, Spearman ρ +0.0410 at n=100;
    # see experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md).
    "wc_10_internal_only": False,
    # BR-3 Squeak (per experiments/2026-05-09-001-br3-squeak-market-analyst/).
    # When "structured", market analyst emits MarketAnalystSquared Pydantic
    # via second LLM call. "prose" preserves existing behavior (default).
    "market_analyst_format": "prose",
    # BR-3 v2 (per experiments/2026-05-09-003-br3-v2-news-fundamentals/).
    # Sister extensions to BR-3 v1: when "structured", news/fundamentals analysts
    # emit MarketAnalystSquared Pydantic via second LLM call instead of free-form
    # prose. Default "prose" preserves existing behavior. Tests whether the
    # analyst-stage prose-to-structured effect generalizes beyond market analyst.
    "news_analyst_format": "prose",
    "fundamentals_analyst_format": "prose",
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
