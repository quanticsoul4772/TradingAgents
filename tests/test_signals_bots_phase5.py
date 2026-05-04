"""Tests for spec 001 Phase 5 — weight tuning."""

from __future__ import annotations

import pytest

from tradingagents.signals.bots import DEFAULT_WEIGHTS, Signal
from tradingagents.signals.weight_tuning import (
    TuningCorpusRow,
    WeightEvaluation,
    build_tuning_corpus,
    evaluate_weights,
    grid_search_weights,
    split_train_test,
)

pytestmark = pytest.mark.unit


def _row(
    ticker: str = "NVDA",
    date: str = "2026-01-30",
    actual_rating: str = "Overweight",
    alpha: float | None = 1.0,
    signals: list | None = None,
) -> TuningCorpusRow:
    return TuningCorpusRow(
        ticker=ticker,
        date=date,
        signals=signals
        or [
            Signal(bot_id="market_report", direction=0.5, magnitude=0.7),
            Signal(bot_id="fundamentals_report", direction=0.6, magnitude=0.8),
        ],
        actual_rating=actual_rating,
        alpha=alpha,
    )


# ---- evaluate_weights -----------------------------------------------------


def test_evaluate_weights_returns_full_metrics():
    # Vary the signal direction across rows so direction_score has variance
    # (otherwise _spearman_ic correctly returns None).
    rows = [
        _row(
            alpha=1.0,
            signals=[Signal(bot_id="market_report", direction=0.8, magnitude=0.9)],
        ),
        _row(
            date="2026-01-31",
            alpha=2.0,
            signals=[Signal(bot_id="market_report", direction=0.3, magnitude=0.7)],
        ),
        _row(
            date="2026-02-06",
            alpha=-1.0,
            signals=[Signal(bot_id="market_report", direction=-0.5, magnitude=0.6)],
        ),
    ]
    ev = evaluate_weights(rows, DEFAULT_WEIGHTS)
    assert isinstance(ev, WeightEvaluation)
    assert ev.n_total == 3
    assert ev.n_resolved == 3
    assert ev.weights == DEFAULT_WEIGHTS
    # IC computed (n>=3 with alpha + variance)
    assert ev.ic is not None
    assert -1.0 <= ev.ic <= 1.0
    # Direction agreement reported as fraction
    assert 0.0 <= ev.direction_agreement <= 1.0


def test_evaluate_weights_handles_unresolved_alpha():
    rows = [_row(alpha=None), _row(date="2026-02-01", alpha=1.0)]
    ev = evaluate_weights(rows, DEFAULT_WEIGHTS)
    assert ev.n_total == 2
    assert ev.n_resolved == 1


def test_evaluate_weights_returns_zero_for_empty_corpus():
    ev = evaluate_weights([], DEFAULT_WEIGHTS)
    assert ev.n_total == 0
    assert ev.ic is None
    assert ev.direction_agreement == 0.0


def test_evaluate_weights_counts_ratings():
    """All-bullish signals + uniform weights → all-bullish ratings."""
    bullish_signals = [
        Signal(bot_id="market_report", direction=1.0, magnitude=1.0),
        Signal(bot_id="fundamentals_report", direction=1.0, magnitude=1.0),
    ]
    rows = [
        _row(actual_rating="Buy", signals=bullish_signals, alpha=1.0),
        _row(date="2026-02-01", actual_rating="Buy", signals=bullish_signals, alpha=1.0),
    ]
    ev = evaluate_weights(rows, DEFAULT_WEIGHTS)
    # Strong-bullish unanimity → mostly Buy
    assert ev.n_buy + ev.n_overweight == 2


def test_evaluate_weights_direction_agreement_reflects_match():
    """Construct rows where actual matches shadow direction → high agreement."""
    bull_signals = [Signal(bot_id="market_report", direction=1.0, magnitude=1.0)]
    rows = [
        _row(actual_rating="Buy", signals=bull_signals, alpha=1.0),
        _row(date="2026-02-01", actual_rating="Overweight", signals=bull_signals, alpha=1.0),
    ]
    ev = evaluate_weights(rows, {"market_report": 1.0})
    # Both rows actual=bull, shadow=bull (single weighted bot=Buy/+1 dir → Buy)
    assert ev.direction_agreement == 1.0


# ---- grid_search_weights --------------------------------------------------


def test_grid_search_returns_weights_and_evaluation():
    bull_signals = [
        Signal(bot_id="market_report", direction=1.0, magnitude=1.0),
        Signal(bot_id="fundamentals_report", direction=-1.0, magnitude=1.0),
    ]
    rows = [
        _row(actual_rating="Buy", signals=bull_signals, alpha=1.0),
        _row(date="2026-02-01", actual_rating="Buy", signals=bull_signals, alpha=2.0),
        _row(date="2026-02-08", actual_rating="Buy", signals=bull_signals, alpha=3.0),
    ]
    # Coarse grid for fast test
    weights, ev = grid_search_weights(
        rows,
        objective="agreement",
        bot_ids=["market_report", "fundamentals_report"],
        grid_values=(0.0, 1.0),
    )
    # Best agreement maximizes match with actual=Buy
    # market_report direction=+1 → wants weight=1.0 here
    assert weights["market_report"] == 1.0
    assert weights["fundamentals_report"] == 0.0  # bearish-direction → exclude
    assert ev.direction_agreement == 1.0


def test_grid_search_skips_all_zero():
    """The all-zero weight vector is degenerate and should be skipped."""
    rows = [_row()]
    weights, _ = grid_search_weights(
        rows,
        objective="agreement",
        bot_ids=["market_report"],
        grid_values=(0.0, 0.5),
    )
    # If all-zero were allowed, sum could be zero; verify it isn't
    assert sum(weights.values()) > 0


def test_grid_search_rejects_unknown_objective():
    rows = [_row()]
    with pytest.raises(ValueError, match="Unknown objective"):
        grid_search_weights(
            rows,
            objective="nonsense",
            bot_ids=["market_report"],
            grid_values=(0.0, 1.0),
        )


# ---- split_train_test -----------------------------------------------------


def test_split_train_test_date_ordered():
    rows = [
        _row(date="2026-03-01"),
        _row(date="2026-01-01"),
        _row(date="2026-02-01"),
        _row(date="2026-04-01"),
    ]
    train, test = split_train_test(rows, train_fraction=0.5)
    assert len(train) == 2
    assert len(test) == 2
    # Train should be the OLDER half
    assert train[0].date == "2026-01-01"
    assert train[1].date == "2026-02-01"
    assert test[0].date == "2026-03-01"
    assert test[1].date == "2026-04-01"


def test_split_train_test_70_30_default():
    rows = [_row(date=f"2026-01-{i:02d}") for i in range(1, 11)]  # 10 rows
    train, test = split_train_test(rows)
    assert len(train) == 7  # 0.7 * 10 = 7
    assert len(test) == 3


def test_split_train_test_handles_small_corpus():
    rows = [_row(date="2026-01-01"), _row(date="2026-01-02")]
    train, test = split_train_test(rows, train_fraction=0.5)
    assert len(train) == 1
    assert len(test) == 1


# ---- build_tuning_corpus --------------------------------------------------


def test_build_tuning_corpus_extracts_signals_and_actual():
    state_logs = [
        (
            "NVDA",
            {
                "trade_date": "2026-01-30",
                "market_report": "bullish strong upgrade momentum" * 10,
                "final_trade_decision": "**Rating: Overweight**\nbody",
            },
            2.5,  # alpha
        )
    ]
    rows = build_tuning_corpus(state_logs)
    assert len(rows) == 1
    assert rows[0].ticker == "NVDA"
    assert rows[0].date == "2026-01-30"
    assert rows[0].actual_rating == "Overweight"
    assert rows[0].alpha == 2.5
    assert len(rows[0].signals) >= 1


def test_build_tuning_corpus_skips_logs_without_trade_date():
    state_logs = [
        ("NVDA", {"market_report": "x"}, 1.0),  # no trade_date → skipped
        ("AAPL", {"trade_date": "2026-01-30", "market_report": "bullish strong upgrade" * 10}, 1.0),
    ]
    rows = build_tuning_corpus(state_logs)
    assert len(rows) == 1
    assert rows[0].ticker == "AAPL"


def test_build_tuning_corpus_handles_missing_alpha():
    state_logs = [
        (
            "NVDA",
            {"trade_date": "2026-04-25", "market_report": "bullish strong" * 20},
            None,
        )
    ]
    rows = build_tuning_corpus(state_logs)
    assert len(rows) == 1
    assert rows[0].alpha is None
