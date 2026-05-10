"""Pinned schemas for engine outputs (specs/250-dashboard-ui/spec.md FR-020 to FR-023).

Schemas are part of the contract between engine (writer) and dashboard (reader).
Schema changes require a spec amendment.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AgentStage(str, Enum):
    """The 12 LangGraph agent nodes (FR-022)."""

    MARKET_ANALYST = "market_analyst"
    NEWS_ANALYST = "news_analyst"
    SOCIAL_ANALYST = "social_analyst"
    FUNDAMENTALS_ANALYST = "fundamentals_analyst"
    BULL_RESEARCHER = "bull_researcher"
    BEAR_RESEARCHER = "bear_researcher"
    RESEARCH_MANAGER = "research_manager"
    TRADER = "trader"
    AGGRESSIVE_RISK = "aggressive_risk"
    CONSERVATIVE_RISK = "conservative_risk"
    NEUTRAL_RISK = "neutral_risk"
    PORTFOLIO_MANAGER = "portfolio_manager"


class EventType(str, Enum):
    """events.jsonl event types (FR-023)."""

    RUN_STARTED = "run_started"
    TICKER_STARTED = "ticker_started"
    AGENT_STARTED = "agent_started"
    AGENT_FINISHED = "agent_finished"
    TICKER_FINISHED = "ticker_finished"
    TICKER_FAILED = "ticker_failed"
    COST_DELTA = "cost_delta"
    ERROR = "error"
    RUN_FINISHED = "run_finished"


class CompletedTicker(BaseModel):
    ticker: str
    rating: str
    completed_at: str  # ISO 8601 UTC


class FailedTicker(BaseModel):
    ticker: str
    error: str
    failed_at: str  # ISO 8601 UTC


class ProgressFile(BaseModel):
    """progress.json schema (FR-020).

    Written atomically via temp + os.replace. Heartbeat refreshed every 10 sec
    (FR-006); if older than 90 sec without a terminal event, dashboard renders
    the run as STALE (FR-027).
    """

    run_id: str  # <ISO date>T<HHMMSS>Z UTC; FR-024
    started_at: str  # ISO 8601 UTC
    trade_date: str  # ISO date in America/New_York; FR-025
    watchlist: list[str]
    current_ticker: str | None = None
    current_ticker_started_at: str | None = None
    current_agent_stage: AgentStage | None = None
    completed_tickers: list[CompletedTicker] = Field(default_factory=list)
    failed_tickers: list[FailedTicker] = Field(default_factory=list)
    cost_so_far_usd: float = 0.0
    heartbeat_at: str  # ISO 8601 UTC; FR-006


class Event(BaseModel):
    """events.jsonl line schema (FR-021)."""

    ts: str  # ISO 8601 UTC
    run_id: str
    ticker: str | None = None
    agent_stage: AgentStage | None = None
    event_type: EventType
    payload: dict = Field(default_factory=dict)
