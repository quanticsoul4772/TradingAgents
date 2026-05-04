"""Tests for spec 001 Phase 3 — convergence shortcut + bot budgets."""

from __future__ import annotations

import pytest

from tradingagents.signals.bots import Signal
from tradingagents.signals.budget import (
    BotBudget,
    BudgetReservation,
)
from tradingagents.signals.shortcut import (
    DEFAULT_MAGNITUDE_THRESHOLD,
    DEFAULT_MIN_CONVERGING_SIGNALS,
    analyze_shortcut_corpus,
    should_skip_debate,
)

pytestmark = pytest.mark.unit


# ---- should_skip_debate ---------------------------------------------------


def test_skip_when_3_bullish_strong():
    """3 bots bullish with magnitude > 0.7 → skip."""
    signals = [
        Signal(bot_id="market", direction=0.8, magnitude=0.8),
        Signal(bot_id="news", direction=0.9, magnitude=0.9),
        Signal(bot_id="fundamentals", direction=0.7, magnitude=0.75),
    ]
    decision = should_skip_debate(signals)
    assert decision.skip is True
    assert decision.n_bullish_strong == 3
    assert decision.n_bearish_strong == 0
    assert "bullish" in decision.reason


def test_skip_when_3_bearish_strong():
    signals = [
        Signal(bot_id="market", direction=-0.8, magnitude=0.8),
        Signal(bot_id="news", direction=-0.9, magnitude=0.9),
        Signal(bot_id="fundamentals", direction=-0.7, magnitude=0.75),
    ]
    decision = should_skip_debate(signals)
    assert decision.skip is True
    assert decision.n_bearish_strong == 3
    assert "bearish" in decision.reason


def test_no_skip_when_only_2_strong():
    """Only 2 bots cross the threshold → don't skip."""
    signals = [
        Signal(bot_id="market", direction=0.8, magnitude=0.8),
        Signal(bot_id="news", direction=0.9, magnitude=0.9),
        Signal(bot_id="fundamentals", direction=0.5, magnitude=0.5),  # below threshold
    ]
    decision = should_skip_debate(signals)
    assert decision.skip is False
    assert decision.n_bullish_strong == 2


def test_no_skip_when_signals_split_direction():
    """3+ strong bots but split between bull and bear → no skip."""
    signals = [
        Signal(bot_id="market", direction=0.9, magnitude=0.8),
        Signal(bot_id="news", direction=-0.9, magnitude=0.8),
        Signal(bot_id="fundamentals", direction=-0.9, magnitude=0.8),
    ]
    decision = should_skip_debate(signals)
    # 1 bullish + 2 bearish → neither side hits min_converging=3
    assert decision.skip is False


def test_skip_threshold_exactly_at_boundary_does_not_fire():
    """Magnitude exactly equal to threshold (0.7) does NOT count as strong
    (strict greater-than per spec wording 'magnitude > 0.7')."""
    signals = [
        Signal(bot_id="m", direction=0.5, magnitude=0.7),
        Signal(bot_id="n", direction=0.5, magnitude=0.7),
        Signal(bot_id="f", direction=0.5, magnitude=0.7),
    ]
    decision = should_skip_debate(signals)
    assert decision.skip is False
    assert decision.n_bullish_strong == 0  # all exactly at threshold


def test_skip_excludes_abstaining_signals():
    """Abstaining signals don't count toward convergence."""
    signals = [
        Signal(bot_id="market", direction=0.9, magnitude=0.9),
        Signal(bot_id="news", direction=0.9, magnitude=0.9),
        Signal(bot_id="fundamentals", direction=0.0, magnitude=0.0, abstain=True),
        Signal(bot_id="sentiment", direction=0.0, magnitude=0.0, abstain=True),
    ]
    decision = should_skip_debate(signals)
    # Only 2 strong-bullish (fundamentals + sentiment abstain) → no skip
    assert decision.skip is False
    assert decision.n_bullish_strong == 2
    assert decision.n_abstaining == 2


def test_skip_with_custom_threshold():
    """Custom min_converging=2 → 2 strong bots is enough to skip."""
    signals = [
        Signal(bot_id="market", direction=0.9, magnitude=0.9),
        Signal(bot_id="news", direction=0.9, magnitude=0.9),
    ]
    decision = should_skip_debate(signals, min_converging=2)
    assert decision.skip is True


def test_default_thresholds_match_spec():
    """Per spec FR-006: 3+ Signals share a direction with magnitude > 0.7."""
    assert DEFAULT_MIN_CONVERGING_SIGNALS == 3
    assert DEFAULT_MAGNITUDE_THRESHOLD == 0.7


def test_no_skip_on_empty_signals():
    decision = should_skip_debate([])
    assert decision.skip is False
    assert decision.n_signals_total == 0


# ---- analyze_shortcut_corpus ---------------------------------------------


def test_corpus_report_counts_correctly():
    bull = [
        Signal(bot_id="m", direction=0.8, magnitude=0.8),
        Signal(bot_id="n", direction=0.8, magnitude=0.8),
        Signal(bot_id="f", direction=0.8, magnitude=0.8),
    ]
    bear = [
        Signal(bot_id="m", direction=-0.8, magnitude=0.8),
        Signal(bot_id="n", direction=-0.8, magnitude=0.8),
        Signal(bot_id="f", direction=-0.8, magnitude=0.8),
    ]
    no_skip = [
        Signal(bot_id="m", direction=0.5, magnitude=0.5),
    ]
    report = analyze_shortcut_corpus([bull, bear, bull, no_skip])
    assert report.n_total == 4
    assert report.n_would_skip == 3
    assert report.n_bullish_skip == 2
    assert report.n_bearish_skip == 1
    assert report.skip_rate == pytest.approx(0.75)


def test_corpus_report_empty_returns_zero():
    report = analyze_shortcut_corpus([])
    assert report.n_total == 0
    assert report.n_would_skip == 0
    assert report.skip_rate == 0.0


# ---- BotBudget ------------------------------------------------------------


def test_budget_can_reserve_when_under_limit():
    budget = BotBudget(limits={"market": 5000})
    assert budget.can_reserve("market") is True


def test_budget_can_reserve_unbudgeted_bot():
    """Bots without a configured limit are unconstrained."""
    budget = BotBudget(limits={"market": 1000})
    assert budget.can_reserve("news") is True  # no limit set


def test_budget_can_reserve_returns_false_when_at_limit():
    budget = BotBudget(limits={"market": 1000})
    res = budget.reserve("market")
    budget.record(res, prompt_tokens=600, completion_tokens=600)
    # Used 1200 > limit 1000
    assert budget.can_reserve("market") is False


def test_budget_reserve_returns_reservation():
    budget = BotBudget(limits={"market": 5000})
    res = budget.reserve("market")
    assert isinstance(res, BudgetReservation)
    assert res.bot_id == "market"
    assert res.reservation_id > 0


def test_budget_reservation_ids_are_unique():
    budget = BotBudget(limits={"market": 100000})
    r1 = budget.reserve("market")
    r2 = budget.reserve("market")
    assert r1.reservation_id != r2.reservation_id


def test_budget_record_accumulates_used():
    budget = BotBudget(limits={"market": 10000})
    r1 = budget.reserve("market")
    budget.record(r1, prompt_tokens=500, completion_tokens=300)
    r2 = budget.reserve("market")
    budget.record(r2, prompt_tokens=200, completion_tokens=400)
    assert budget.used["market"] == 500 + 300 + 200 + 400


def test_budget_record_increments_call_count():
    budget = BotBudget(limits={"market": 10000})
    r1 = budget.reserve("market")
    budget.record(r1, prompt_tokens=100, completion_tokens=100)
    r2 = budget.reserve("market")
    budget.record(r2, prompt_tokens=100, completion_tokens=100)
    assert budget.by_bot_calls["market"] == 2


def test_budget_record_double_close_is_idempotent_warning(caplog):
    budget = BotBudget(limits={"market": 10000})
    r1 = budget.reserve("market")
    budget.record(r1, prompt_tokens=100, completion_tokens=100)
    # Second close on same reservation should warn + skip, not crash
    budget.record(r1, prompt_tokens=100, completion_tokens=100)
    # used count NOT incremented twice
    assert budget.used["market"] == 200


def test_budget_remaining_returns_difference():
    budget = BotBudget(limits={"market": 1000})
    r = budget.reserve("market")
    budget.record(r, prompt_tokens=300, completion_tokens=200)
    assert budget.remaining("market") == 500


def test_budget_remaining_clamps_at_zero_when_over():
    budget = BotBudget(limits={"market": 100})
    r = budget.reserve("market")
    budget.record(r, prompt_tokens=200, completion_tokens=200)
    # Used 400 > limit 100 → remaining is 0, not negative
    assert budget.remaining("market") == 0


def test_budget_remaining_returns_none_for_unlimited():
    budget = BotBudget(limits={"market": 1000})
    assert budget.remaining("news") is None


def test_budget_summary_reports_per_bot():
    budget = BotBudget(limits={"market": 1000, "news": 2000})
    r1 = budget.reserve("market")
    budget.record(r1, prompt_tokens=300, completion_tokens=200)
    summary = budget.summary()
    assert summary["market"]["used"] == 500
    assert summary["market"]["limit"] == 1000
    assert summary["market"]["calls"] == 1
    assert summary["market"]["remaining"] == 500
    assert summary["market"]["exceeded"] is False
    # news not yet used but limit configured
    assert summary["news"]["limit"] == 2000
    assert summary["news"]["used"] == 0


def test_budget_summary_reports_exceeded():
    budget = BotBudget(limits={"market": 100})
    r = budget.reserve("market")
    budget.record(r, prompt_tokens=200, completion_tokens=200)  # 400 > 100
    summary = budget.summary()
    assert summary["market"]["exceeded"] is True


def test_budget_negative_token_counts_treated_as_zero():
    """Defensive: never decrement used by a negative token count."""
    budget = BotBudget(limits={"market": 1000})
    r = budget.reserve("market")
    budget.record(r, prompt_tokens=-100, completion_tokens=200)
    # negative prompt is clamped to 0; only +200 counted
    assert budget.used["market"] == 200
