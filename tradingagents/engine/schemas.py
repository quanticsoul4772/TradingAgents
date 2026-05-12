"""Pinned schemas for engine outputs.

Schemas are part of the contract between engine (writer) and dashboard (reader).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AgentStage(str, Enum):
    """The 12 LangGraph agent nodes."""

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
    """events.jsonl event types."""

    RUN_STARTED = "run_started"
    TICKER_STARTED = "ticker_started"
    AGENT_STARTED = "agent_started"
    AGENT_FINISHED = "agent_finished"
    TICKER_FINISHED = "ticker_finished"
    TICKER_FAILED = "ticker_failed"
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
    """progress.json schema.

    Written atomically via temp + os.replace. Heartbeat refreshed every 10 sec;
    if older than 90 sec without a terminal event, dashboard renders the run as
    STALE.
    """

    run_id: str  # <ISO date>T<HHMMSS>Z UTC
    started_at: str  # ISO 8601 UTC
    trade_date: str  # ISO date in America/New_York
    watchlist: list[str]
    current_ticker: str | None = None
    current_ticker_started_at: str | None = None
    current_agent_stage: AgentStage | None = None
    completed_tickers: list[CompletedTicker] = Field(default_factory=list)
    failed_tickers: list[FailedTicker] = Field(default_factory=list)
    heartbeat_at: str  # ISO 8601 UTC


class Event(BaseModel):
    """events.jsonl line schema."""

    ts: str  # ISO 8601 UTC
    run_id: str
    ticker: str | None = None
    agent_stage: AgentStage | None = None
    event_type: EventType
    payload: dict = Field(default_factory=dict)
