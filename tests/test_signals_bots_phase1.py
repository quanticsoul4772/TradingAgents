"""Tests for spec 001 Phase 1 — Shadow Aggregator (tradingagents/signals/bots.py)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tradingagents.signals.bots import (
    DEFAULT_WEIGHTS,
    AggregatedDecision,
    Signal,
    _direction_to_rating,
    aggregate,
    derive_signal_from_prose,
    shadow_aggregate_from_state_log,
)

pytestmark = pytest.mark.unit


# ---- Signal schema --------------------------------------------------------


def test_signal_schema_accepts_valid():
    s = Signal(
        bot_id="market",
        direction=0.5,
        magnitude=0.8,
        horizon_days=21,
        key_facts=["MA crossover", "RSI 60"],
        risks=["overbought near term"],
    )
    assert s.bot_id == "market"
    assert s.direction == 0.5
    assert s.abstain is False


def test_signal_schema_rejects_direction_out_of_range():
    with pytest.raises(ValidationError):
        Signal(bot_id="x", direction=1.5, magnitude=0.5)
    with pytest.raises(ValidationError):
        Signal(bot_id="x", direction=-1.5, magnitude=0.5)


def test_signal_schema_rejects_magnitude_out_of_range():
    with pytest.raises(ValidationError):
        Signal(bot_id="x", direction=0.0, magnitude=1.5)
    with pytest.raises(ValidationError):
        Signal(bot_id="x", direction=0.0, magnitude=-0.1)


def test_signal_schema_default_horizon_21():
    s = Signal(bot_id="x", direction=0.0, magnitude=0.5)
    assert s.horizon_days == 21


def test_signal_schema_default_abstain_false():
    s = Signal(bot_id="x", direction=0.0, magnitude=0.5)
    assert s.abstain is False


# ---- _direction_to_rating -------------------------------------------------


@pytest.mark.parametrize(
    "score,expected",
    [
        (0.9, "Buy"),
        (0.65, "Buy"),
        (0.6, "Overweight"),  # boundary: > 0.6 is Buy
        (0.5, "Overweight"),
        (0.21, "Overweight"),
        (0.2, "Hold"),  # boundary: > 0.2 is Overweight
        (0.0, "Hold"),
        (-0.2, "Hold"),  # boundary: < -0.2 is Underweight
        (-0.21, "Underweight"),
        (-0.5, "Underweight"),
        (-0.6, "Underweight"),  # boundary: < -0.6 is Sell
        (-0.65, "Sell"),
        (-0.9, "Sell"),
    ],
)
def test_direction_to_rating_boundaries(score, expected):
    assert _direction_to_rating(score) == expected


# ---- aggregate ------------------------------------------------------------


def test_aggregate_all_abstain_returns_hold_zero_confidence():
    signals = [
        Signal(bot_id="market_report", direction=0.0, magnitude=0.0, abstain=True),
        Signal(bot_id="news_report", direction=0.0, magnitude=0.0, abstain=True),
    ]
    out = aggregate(signals)
    assert out.rating == "Hold"
    assert out.confidence == 0.0
    assert out.direction_score == 0.0
    assert out.bots_used == []
    assert "market_report" in out.abstained
    assert "news_report" in out.abstained


def test_aggregate_unanimous_bullish_strong_returns_buy():
    signals = [
        Signal(bot_id="market_report", direction=1.0, magnitude=0.9),
        Signal(bot_id="news_report", direction=1.0, magnitude=0.9),
        Signal(bot_id="fundamentals_report", direction=1.0, magnitude=0.9),
    ]
    out = aggregate(signals)
    assert out.rating == "Buy"
    assert out.direction_score > 0.6
    assert out.confidence > 0.0


def test_aggregate_unanimous_bearish_strong_returns_sell():
    signals = [
        Signal(bot_id="market_report", direction=-1.0, magnitude=0.9),
        Signal(bot_id="news_report", direction=-1.0, magnitude=0.9),
        Signal(bot_id="fundamentals_report", direction=-1.0, magnitude=0.9),
    ]
    out = aggregate(signals)
    assert out.rating == "Sell"
    assert out.direction_score < -0.6


def test_aggregate_balanced_signals_return_hold():
    signals = [
        Signal(bot_id="market_report", direction=0.5, magnitude=0.8),
        Signal(bot_id="fundamentals_report", direction=-0.5, magnitude=0.8),
    ]
    out = aggregate(signals)
    # Direction roughly cancels → Hold
    assert out.rating == "Hold"
    assert abs(out.direction_score) < 0.2


def test_aggregate_weighted_by_default_weights():
    """fundamentals (0.30) outweighs market (0.25) when they disagree."""
    signals = [
        Signal(bot_id="market_report", direction=+1.0, magnitude=1.0),
        Signal(bot_id="fundamentals_report", direction=-1.0, magnitude=1.0),
    ]
    out = aggregate(signals)
    # fundamentals is more weighted → bearish-leaning
    assert out.direction_score < 0.0


def test_aggregate_abstain_excluded_from_score():
    signals = [
        Signal(bot_id="market_report", direction=+1.0, magnitude=0.8),
        Signal(bot_id="news_report", direction=-1.0, magnitude=0.0, abstain=True),
    ]
    out = aggregate(signals)
    # Only market_report counts → bullish
    assert out.direction_score > 0
    assert "news_report" in out.abstained


def test_aggregate_unknown_bot_id_gets_zero_weight():
    """Signals from unrecognized bots contribute nothing."""
    signals = [
        Signal(bot_id="unknown_bot", direction=+1.0, magnitude=1.0),
        Signal(bot_id="market_report", direction=-1.0, magnitude=1.0),
    ]
    out = aggregate(signals)
    # unknown_bot has weight 0 → only market_report counts → bearish
    assert out.direction_score < 0


def test_aggregate_is_deterministic():
    """Same inputs always yield same output (FR-010)."""
    signals = [
        Signal(bot_id="market_report", direction=+0.5, magnitude=0.7),
        Signal(bot_id="news_report", direction=-0.3, magnitude=0.6),
    ]
    out_a = aggregate(signals)
    out_b = aggregate(signals)
    assert out_a.rating == out_b.rating
    assert out_a.direction_score == out_b.direction_score
    assert out_a.confidence == out_b.confidence


def test_aggregate_custom_weights_overrides_default():
    signals = [
        Signal(bot_id="market_report", direction=+1.0, magnitude=1.0),
    ]
    custom = {"market_report": 1.0}
    out = aggregate(signals, weights=custom)
    assert out.direction_score == pytest.approx(1.0)


def test_default_weights_sum_close_to_one():
    """Sanity check on the default weights — should approximately sum to 1.0."""
    total = sum(DEFAULT_WEIGHTS.values())
    # Allow small tolerance; spec uses placeholders to be tuned in Phase 5
    assert 0.9 <= total <= 1.1


# ---- derive_signal_from_prose ---------------------------------------------


def test_derive_signal_from_empty_prose_abstains():
    s = derive_signal_from_prose("market", "")
    assert s.abstain is True
    assert s.magnitude == 0.0
    assert s.direction == 0.0


def test_derive_signal_from_short_prose_abstains():
    """Below 50 chars → abstain."""
    s = derive_signal_from_prose("market", "very short")
    assert s.abstain is True


def test_derive_signal_from_bullish_prose_is_positive():
    prose = (
        "Market analysis shows strong bullish momentum with multiple "
        "catalysts. Strong buy with high conviction across the technical "
        "indicators. Price above key moving averages, accelerating growth "
        "trajectory, and clear upside potential going into the next quarter. "
        "Relative strength is robust."
    )
    s = derive_signal_from_prose("market_report", prose)
    assert s.direction > 0.5
    assert s.magnitude > 0.1


def test_derive_signal_from_bearish_prose_is_negative():
    prose = (
        "Bearish thesis: missed estimates, downside risk, declining margins, "
        "regulatory risks, and competitive pressure. Downgrade to Underweight "
        "with high conviction. Guidance lowered, weak momentum across the "
        "key metrics, and clear deceleration in core business."
    )
    s = derive_signal_from_prose("market_report", prose)
    assert s.direction < -0.5
    assert s.magnitude > 0.1


def test_derive_signal_from_neutral_prose_is_near_zero():
    """Pure neutral prose with no sentiment words → near-zero direction."""
    prose = (
        "The quarterly report was published today with the standard "
        "format. Numbers are in line with prior reporting periods. "
        "Standard summary follows the typical structure."
    )
    s = derive_signal_from_prose("market_report", prose)
    # No sentiment words → abstain or near-zero
    assert s.abstain is True or abs(s.direction) < 0.3


def test_derive_signal_bot_id_passes_through():
    prose = "bullish strong upgrade momentum" * 5
    s = derive_signal_from_prose("custom_bot", prose)
    assert s.bot_id == "custom_bot"


def test_derive_signal_horizon_days_passes_through():
    prose = "bullish strong upgrade momentum" * 5
    s = derive_signal_from_prose("market", prose, horizon_days=10)
    assert s.horizon_days == 10


# ---- shadow_aggregate_from_state_log -------------------------------------


def test_shadow_aggregate_extracts_all_known_fields():
    state = {
        "market_report": "bullish strong momentum and high conviction" * 10,
        "news_report": "positive catalyst and beat estimates" * 10,
        "fundamentals_report": "strong growth and expanding margins" * 10,
        "investment_plan": "Bull case dominant; Overweight target" * 10,
        # sentiment_report intentionally missing
    }
    signals, decision = shadow_aggregate_from_state_log(state)
    bot_ids = {s.bot_id for s in signals}
    assert "market_report" in bot_ids
    assert "news_report" in bot_ids
    assert "fundamentals_report" in bot_ids
    assert "investment_plan" in bot_ids
    assert "sentiment_report" not in bot_ids
    # All-bullish prose → positive direction
    assert decision.direction_score > 0


def test_shadow_aggregate_handles_empty_state():
    signals, decision = shadow_aggregate_from_state_log({})
    assert signals == []
    assert decision.rating == "Hold"
    assert decision.confidence == 0.0


def test_shadow_aggregate_skips_non_string_fields():
    """investment_debate_state is a nested dict and should be ignored
    (only flat string fields are extracted)."""
    state = {
        "market_report": "bullish strong momentum" * 10,
        "investment_debate_state": {"history": "..."},
    }
    signals, _ = shadow_aggregate_from_state_log(state)
    bot_ids = {s.bot_id for s in signals}
    assert "investment_debate_state" not in bot_ids
    assert "market_report" in bot_ids


def test_shadow_aggregate_returns_aggregated_decision():
    state = {
        "market_report": "bullish strong" * 20,
        "fundamentals_report": "strong growth" * 20,
    }
    _, decision = shadow_aggregate_from_state_log(state)
    assert isinstance(decision, AggregatedDecision)
    assert decision.rating in {"Buy", "Overweight", "Hold", "Underweight", "Sell"}
    assert 0.0 <= decision.confidence <= 1.0
    assert -1.0 <= decision.direction_score <= 1.0


def test_shadow_aggregate_custom_horizon_propagates_to_signals():
    state = {"market_report": "bullish strong upgrade momentum" * 10}
    signals, _ = shadow_aggregate_from_state_log(state, horizon_days=5)
    assert all(s.horizon_days == 5 for s in signals)


# ---- Phase 2: render_aggregated_decision_markdown -------------------------


def test_render_aggregated_decision_markdown_includes_rating():
    """The Rating: line is the load-bearing parseable token."""
    from tradingagents.signals.bots import render_aggregated_decision_markdown

    decision = AggregatedDecision(
        rating="Overweight",
        confidence=0.7,
        direction_score=0.45,
        bots_used=["market_report", "fundamentals_report"],
        abstained=["sentiment_report"],
    )
    sig = Signal(bot_id="market_report", direction=0.5, magnitude=0.7)
    md = render_aggregated_decision_markdown(decision, [sig], "NVDA", "2026-01-30")
    assert "Rating: Overweight" in md or "Rating**: Overweight" in md
    assert "NVDA" in md
    assert "2026-01-30" in md


def test_render_aggregated_decision_parseable_by_parse_rating():
    """Output must be parseable by tradingagents.agents.utils.rating.parse_rating
    so memory log + signal processor still work in bots mode."""
    from tradingagents.agents.utils.rating import parse_rating
    from tradingagents.signals.bots import render_aggregated_decision_markdown

    for rating in ("Buy", "Overweight", "Hold", "Underweight", "Sell"):
        decision = AggregatedDecision(
            rating=rating,
            confidence=0.5,
            direction_score=0.0,
            bots_used=[],
            abstained=[],
        )
        md = render_aggregated_decision_markdown(decision, [], "X", "2026-01-01")
        assert parse_rating(md) == rating, f"parse_rating failed for {rating}: {md[:200]}"


def test_render_includes_signals_audit_trail():
    from tradingagents.signals.bots import render_aggregated_decision_markdown

    decision = AggregatedDecision(
        rating="Hold",
        confidence=0.0,
        direction_score=0.0,
        bots_used=[],
        abstained=["market_report"],
    )
    sig = Signal(bot_id="market_report", direction=0.0, magnitude=0.0, abstain=True)
    md = render_aggregated_decision_markdown(decision, [sig], "X", "2026-01-01")
    assert "market_report" in md
    assert "abstain" in md.lower()


def test_render_includes_decision_source_disclaimer():
    """The output should make it clear the decision came from the aggregator,
    not the LLM PortfolioManager."""
    from tradingagents.signals.bots import render_aggregated_decision_markdown

    decision = AggregatedDecision(
        rating="Buy",
        confidence=0.8,
        direction_score=0.7,
        bots_used=["market_report"],
        abstained=[],
    )
    md = render_aggregated_decision_markdown(decision, [], "X", "2026-01-01")
    assert "aggregator" in md.lower()
    assert "spec 001" in md.lower() or "phase 2" in md.lower() or "bots mode" in md.lower()
