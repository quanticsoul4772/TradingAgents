"""Schema contract tests for engine writers (specs/250-dashboard-ui/ SC-001).

Verifies that progress.json + events.jsonl conform to the pinned schemas in
FR-020 through FR-023. Without this, the dashboard backend (Phase 2) and the
engine writer (Phase 1) can drift.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from tradingagents.engine.schemas import (
    AgentStage,
    CompletedTicker,
    Event,
    EventType,
    FailedTicker,
    ProgressFile,
)

# ---------------------------------------------------------------------------
# AgentStage enum (FR-022) — fixed 12 values
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_agent_stage_enum_has_exactly_twelve_values():
    """FR-022: agent_stage enum is FIXED at 12 stages."""
    assert len(AgentStage) == 12


@pytest.mark.unit
def test_agent_stage_enum_values_match_spec():
    """FR-022: enum values exactly match the LangGraph node names in the spec."""
    expected = {
        "market_analyst",
        "news_analyst",
        "social_analyst",
        "fundamentals_analyst",
        "bull_researcher",
        "bear_researcher",
        "research_manager",
        "trader",
        "aggressive_risk",
        "conservative_risk",
        "neutral_risk",
        "portfolio_manager",
    }
    assert {s.value for s in AgentStage} == expected


# ---------------------------------------------------------------------------
# EventType enum (FR-023) — fixed 9 values
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_event_type_enum_values_match_spec():
    """event_type enum values."""
    expected = {
        "run_started",
        "ticker_started",
        "agent_started",
        "agent_finished",
        "ticker_finished",
        "ticker_failed",
        "error",
        "run_finished",
    }
    assert {e.value for e in EventType} == expected


# ---------------------------------------------------------------------------
# ProgressFile schema (FR-020)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_progress_file_minimal_construction():
    p = ProgressFile(
        run_id="2026-05-10T120000Z",
        started_at="2026-05-10T12:00:00Z",
        trade_date="2026-05-08",
        watchlist=["NVDA", "AAPL"],
        heartbeat_at="2026-05-10T12:00:00Z",
    )
    assert p.run_id == "2026-05-10T120000Z"
    assert p.completed_tickers == []
    assert p.failed_tickers == []
    assert p.current_ticker is None
    assert p.current_agent_stage is None


@pytest.mark.unit
def test_progress_file_full_construction():
    p = ProgressFile(
        run_id="2026-05-10T120000Z",
        started_at="2026-05-10T12:00:00Z",
        trade_date="2026-05-08",
        watchlist=["NVDA"],
        current_ticker="NVDA",
        current_ticker_started_at="2026-05-10T12:00:05Z",
        current_agent_stage=AgentStage.BULL_RESEARCHER,
        completed_tickers=[
            CompletedTicker(
                ticker="AAPL", rating="Underweight", completed_at="2026-05-10T12:09:00Z"
            )
        ],
        failed_tickers=[
            FailedTicker(
                ticker="ZZZ",
                error="ValueError: bad ticker",
                failed_at="2026-05-10T12:10:00Z",
            )
        ],
        heartbeat_at="2026-05-10T12:00:30Z",
    )
    assert p.current_agent_stage == AgentStage.BULL_RESEARCHER
    assert p.completed_tickers[0].rating == "Underweight"
    assert p.failed_tickers[0].error.startswith("ValueError")


@pytest.mark.unit
def test_progress_file_round_trip_via_json():
    """JSON round-trip must preserve all fields (dashboard reads via JSON)."""
    original = ProgressFile(
        run_id="2026-05-10T120000Z",
        started_at="2026-05-10T12:00:00Z",
        trade_date="2026-05-08",
        watchlist=["NVDA", "AAPL"],
        current_agent_stage=AgentStage.PORTFOLIO_MANAGER,
        heartbeat_at="2026-05-10T12:30:00Z",
    )
    raw = original.model_dump_json()
    parsed = ProgressFile.model_validate_json(raw)
    assert parsed == original


@pytest.mark.unit
def test_progress_file_rejects_invalid_agent_stage():
    """Pydantic enum validation catches drift in current_agent_stage."""
    with pytest.raises(ValidationError):
        ProgressFile(
            run_id="x",
            started_at="x",
            trade_date="x",
            watchlist=[],
            current_agent_stage="not_a_real_stage",  # type: ignore[arg-type]
            heartbeat_at="x",
        )


# ---------------------------------------------------------------------------
# Event schema (FR-021)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_event_minimal_construction():
    e = Event(
        ts="2026-05-10T12:00:00Z",
        run_id="2026-05-10T120000Z",
        event_type=EventType.RUN_STARTED,
    )
    assert e.ticker is None
    assert e.agent_stage is None
    assert e.payload == {}


@pytest.mark.unit
def test_event_with_agent_stage():
    e = Event(
        ts="2026-05-10T12:00:05Z",
        run_id="2026-05-10T120000Z",
        ticker="NVDA",
        agent_stage=AgentStage.BULL_RESEARCHER,
        event_type=EventType.AGENT_STARTED,
        payload={"prompt_tokens": 1234},
    )
    assert e.ticker == "NVDA"
    assert e.agent_stage == AgentStage.BULL_RESEARCHER
    assert e.payload["prompt_tokens"] == 1234


@pytest.mark.unit
def test_event_jsonl_line_round_trip():
    """events.jsonl is one JSON object per line; round-trip must be lossless."""
    e = Event(
        ts="2026-05-10T12:00:00Z",
        run_id="2026-05-10T120000Z",
        ticker="NVDA",
        agent_stage=AgentStage.PORTFOLIO_MANAGER,
        event_type=EventType.AGENT_FINISHED,
        payload={"rating": "Buy", "duration_sec": 8.4},
    )
    line = e.model_dump_json()
    # Verify it's a single line (no embedded newlines).
    assert "\n" not in line
    parsed = Event.model_validate_json(line)
    assert parsed == e


@pytest.mark.unit
def test_event_rejects_invalid_event_type():
    with pytest.raises(ValidationError):
        Event(
            ts="x",
            run_id="x",
            event_type="not_a_real_event_type",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Cross-schema invariants
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_completed_ticker_and_failed_ticker_are_disjoint_concepts():
    """A ticker is either completed (with rating) or failed (with error)."""
    c = CompletedTicker(ticker="X", rating="Hold", completed_at="t")
    f = FailedTicker(ticker="X", error="boom", failed_at="t")
    # Both reference the same ticker, but are distinct types — by construction.
    assert type(c).__name__ != type(f).__name__


@pytest.mark.unit
def test_progress_json_indented_for_human_readability():
    """progress.json is written with indent=2 for operator hand-inspection."""
    p = ProgressFile(
        run_id="r",
        started_at="t",
        trade_date="2026-05-08",
        watchlist=[],
        heartbeat_at="t",
    )
    raw = p.model_dump_json(indent=2)
    assert "\n" in raw
    # Parsing the indented form must still work.
    json.loads(raw)
