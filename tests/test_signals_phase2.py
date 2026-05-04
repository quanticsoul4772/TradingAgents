"""Tests for spec 002 Phase 2 — drift detector + counterfactual tester."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ---- KS-statistic ---------------------------------------------------------


def test_ks_statistic_identical_samples_zero():
    from tradingagents.signals.drift import ks_statistic

    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert ks_statistic(a, b) == pytest.approx(0.0)


def test_ks_statistic_disjoint_samples_one():
    from tradingagents.signals.drift import ks_statistic

    # Completely separated distributions → KS = 1.0
    a = [0.0, 0.1, 0.2]
    b = [10.0, 11.0, 12.0]
    assert ks_statistic(a, b) == pytest.approx(1.0)


def test_ks_statistic_partial_overlap():
    from tradingagents.signals.drift import ks_statistic

    a = [1.0, 2.0, 3.0]
    b = [2.0, 3.0, 4.0]
    ks = ks_statistic(a, b)
    assert ks is not None
    assert 0.0 < ks < 1.0


def test_ks_statistic_handles_empty():
    from tradingagents.signals.drift import ks_statistic

    assert ks_statistic([], [1.0, 2.0]) is None
    assert ks_statistic([1.0, 2.0], []) is None
    assert ks_statistic([], []) is None


# ---- split_by_recency -----------------------------------------------------


def test_split_by_recency_basic():
    from tradingagents.signals.drift import split_by_recency

    rows = [
        {"date": "2026-01-01", "ticker": "A"},
        {"date": "2026-01-02", "ticker": "A"},
        {"date": "2026-01-03", "ticker": "A"},
        {"date": "2026-01-04", "ticker": "A"},
        {"date": "2026-01-05", "ticker": "A"},
    ]
    baseline, recent = split_by_recency(rows, n_recent=2)
    assert len(baseline) == 3
    assert len(recent) == 2
    assert recent[0]["date"] == "2026-01-04"
    assert recent[1]["date"] == "2026-01-05"


def test_split_by_recency_when_n_recent_exceeds_total():
    from tradingagents.signals.drift import split_by_recency

    rows = [{"date": "2026-01-01", "ticker": "A"}, {"date": "2026-01-02", "ticker": "A"}]
    baseline, recent = split_by_recency(rows, n_recent=10)
    # All rows go to recent; baseline empty
    assert baseline == []
    assert len(recent) == 2


def test_split_by_recency_sorts_by_date():
    """Rows out of order are sorted before splitting."""
    from tradingagents.signals.drift import split_by_recency

    rows = [
        {"date": "2026-01-05", "ticker": "A"},
        {"date": "2026-01-01", "ticker": "A"},
        {"date": "2026-01-03", "ticker": "A"},
    ]
    baseline, recent = split_by_recency(rows, n_recent=1)
    assert recent[0]["date"] == "2026-01-05"
    assert baseline[0]["date"] == "2026-01-01"
    assert baseline[1]["date"] == "2026-01-03"


# ---- analyze_drift end-to-end ---------------------------------------------


def test_analyze_drift_no_alert_when_ic_stable(monkeypatch):
    """If recent IC ~= baseline IC, no IC-decline alert."""
    from tradingagents.signals.drift import analyze_drift

    # All rows return the same alpha → IC computation yields a consistent value
    monkeypatch.setattr(
        "tradingagents.signals.drift._compute_alpha",
        lambda ticker, date, holding_days: 1.0,
    )
    rows = [
        {"ticker": "A", "date": f"2026-01-{i:02d}", "value": "**Rating: Buy**"}
        for i in range(1, 11)
    ]
    report = analyze_drift("final_trade_decision", rows, n_recent=5)
    # Both halves all-Buy with constant alpha → IC is None (no variance) → no alert
    assert report.ic_decline_alert is False


def test_analyze_drift_flags_ic_decline(monkeypatch):
    """If recent IC dropped materially below baseline, raise IC-decline alert."""
    from tradingagents.signals.drift import analyze_drift

    # Construct rows where baseline has Buy→positive_alpha, Sell→negative_alpha
    # (IC = +1.0); recent half has Buy→negative_alpha, Sell→positive_alpha
    # (IC = -1.0). Decline = 2.0, well above threshold 0.05.
    alpha_map = {}
    rows = []
    for i in range(1, 7):
        date = f"2026-01-{i:02d}"
        rows.append({"ticker": "A", "date": date, "value": "**Rating: Buy**"})
        alpha_map[("A", date, 21)] = +2.0
        rows.append({"ticker": "B", "date": date, "value": "**Rating: Sell**"})
        alpha_map[("B", date, 21)] = -2.0
    # Now flip the most-recent 4 rows (the "recent" half)
    recent_rows = []
    for i in range(7, 11):
        date = f"2026-01-{i:02d}"
        recent_rows.append({"ticker": "A", "date": date, "value": "**Rating: Buy**"})
        alpha_map[("A", date, 21)] = -2.0  # Buy → negative alpha (anti-cal)
        recent_rows.append({"ticker": "B", "date": date, "value": "**Rating: Sell**"})
        alpha_map[("B", date, 21)] = +2.0  # Sell → positive alpha (anti-cal)
    rows.extend(recent_rows)

    def fake_alpha(ticker, date, holding_days):
        return alpha_map.get((ticker, date, holding_days))

    monkeypatch.setattr("tradingagents.signals.drift._compute_alpha", fake_alpha)

    report = analyze_drift("final_trade_decision", rows, n_recent=8)
    assert report.ic_baseline is not None
    assert report.ic_recent is not None
    assert report.ic_baseline > 0  # baseline was positively correlated
    assert report.ic_recent < 0  # recent flipped to negative
    assert report.ic_decline > 0.05
    assert report.ic_decline_alert is True


def test_analyze_drift_returns_none_decline_when_baseline_too_small():
    from tradingagents.signals.drift import analyze_drift

    # 5 rows total, n_recent=5 → no baseline data
    rows = [
        {"ticker": "A", "date": f"2026-01-{i:02d}", "value": "**Rating: Hold**"}
        for i in range(1, 6)
    ]
    report = analyze_drift("final_trade_decision", rows, n_recent=5)
    assert report.ic_baseline is None
    assert report.ic_decline is None
    assert report.ic_decline_alert is False


def test_analyze_drift_works_with_feature_extractor(monkeypatch):
    """analyze_drift can take a custom feature extractor for prose signals."""
    from tradingagents.signals.drift import analyze_drift
    from tradingagents.signals.featurization import sentiment_score

    monkeypatch.setattr(
        "tradingagents.signals.drift._compute_alpha",
        lambda ticker, date, holding_days: 1.0,
    )
    rows = [
        {"ticker": "A", "date": "2026-01-01", "value": "bullish strong"},
        {"ticker": "B", "date": "2026-01-02", "value": "bearish weak"},
        {"ticker": "A", "date": "2026-01-03", "value": "bullish strong"},
        {"ticker": "B", "date": "2026-01-04", "value": "bearish weak"},
    ]
    report = analyze_drift(
        "market_report",
        rows,
        n_recent=2,
        feature_name="sentiment_score",
        feature_extractor=sentiment_score,
    )
    assert report.feature == "sentiment_score"


# ---- analyze_all_signals integration --------------------------------------


def test_analyze_all_signals_returns_one_per_signal_or_feature(monkeypatch):
    from tradingagents.signals.drift import analyze_all_signals
    from tradingagents.signals.featurization import FEATURIZERS

    monkeypatch.setattr(
        "tradingagents.signals.drift._compute_alpha",
        lambda ticker, date, holding_days: 1.0,
    )
    rows_by_signal = {
        "final_trade_decision": [
            {"ticker": "A", "date": "2026-01-01", "value": "**Rating: Buy**"},
        ],
        "market_report": [
            {"ticker": "A", "date": "2026-01-01", "value": "bullish"},
        ],
        "get_stock_data": [
            {"ticker": "A", "date": "2026-01-01", "value": "csv prose"},
        ],
    }
    reports = analyze_all_signals(rows_by_signal)
    # 1 (final_trade_decision) + len(FEATURIZERS) for market_report + 1 (get_stock_data)
    assert len(reports) == 1 + len(FEATURIZERS) + 1


# ---- counterfactual rules -------------------------------------------------


def test_hold_all_uw_overrides_underweight():
    from tradingagents.signals.counterfactual import hold_all_uw

    assert hold_all_uw("NVDA", "2026-01-30", "Underweight") == "Hold"
    assert hold_all_uw("NVDA", "2026-01-30", "Sell") == "Hold"
    assert hold_all_uw("NVDA", "2026-01-30", "Overweight") == "Overweight"
    assert hold_all_uw("NVDA", "2026-01-30", "Hold") == "Hold"
    assert hold_all_uw("NVDA", "2026-01-30", "Buy") == "Buy"


def test_hold_all_ow_overrides_bullish():
    from tradingagents.signals.counterfactual import hold_all_ow

    assert hold_all_ow("NVDA", "2026-01-30", "Buy") == "Hold"
    assert hold_all_ow("NVDA", "2026-01-30", "Overweight") == "Hold"
    assert hold_all_ow("NVDA", "2026-01-30", "Hold") == "Hold"
    assert hold_all_ow("NVDA", "2026-01-30", "Underweight") == "Underweight"


def test_invert_all_commits_inverts_directionals():
    from tradingagents.signals.counterfactual import invert_all_commits

    assert invert_all_commits("NVDA", "2026-01-30", "Buy") == "Sell"
    assert invert_all_commits("NVDA", "2026-01-30", "Overweight") == "Underweight"
    assert invert_all_commits("NVDA", "2026-01-30", "Hold") == "Hold"
    assert invert_all_commits("NVDA", "2026-01-30", "Underweight") == "Overweight"
    assert invert_all_commits("NVDA", "2026-01-30", "Sell") == "Buy"


# ---- run_counterfactual ---------------------------------------------------


def test_run_counterfactual_computes_alpha_delta(monkeypatch):
    from tradingagents.signals.counterfactual import (
        invert_all_commits,
        run_counterfactual,
    )

    # NVDA Buy → realized α = +5%. Inverted to Sell → contribution flips sign.
    # Actual contribution = +1 × 5 = +5; alternative = -1 × 5 = -5; delta = -10.
    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Buy**"}]
    monkeypatch.setattr(
        "tradingagents.signals.counterfactual._compute_alpha",
        lambda ticker, date, holding_days: 5.0,
    )

    report = run_counterfactual(rows, invert_all_commits)
    assert report.n_total == 1
    assert report.n_resolved == 1
    assert report.n_changed == 1
    p = report.pairs[0]
    assert p.actual_rating == "Buy"
    assert p.alternative_rating == "Sell"
    assert p.actual_alpha_contribution == pytest.approx(5.0)
    assert p.alternative_alpha_contribution == pytest.approx(-5.0)
    assert p.alpha_delta == pytest.approx(-10.0)


def test_run_counterfactual_skips_unresolved_alphas(monkeypatch):
    from tradingagents.signals.counterfactual import hold_all_uw, run_counterfactual

    rows = [{"ticker": "NVDA", "date": "2026-04-01", "value": "**Rating: Underweight**"}]
    # Alpha returns None — date too recent
    monkeypatch.setattr(
        "tradingagents.signals.counterfactual._compute_alpha",
        lambda ticker, date, holding_days: None,
    )

    report = run_counterfactual(rows, hold_all_uw)
    assert report.n_total == 1
    assert report.n_resolved == 0
    assert report.mean_alpha_delta is None  # no resolved deltas


def test_run_counterfactual_handles_no_change(monkeypatch):
    """If alternative_rating == actual_rating, the row is included but
    counts as 0 change and 0 alpha delta."""
    from tradingagents.signals.counterfactual import hold_all_uw, run_counterfactual

    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Hold**"}]
    monkeypatch.setattr(
        "tradingagents.signals.counterfactual._compute_alpha",
        lambda ticker, date, holding_days: 2.0,
    )
    # hold_all_uw on Hold → Hold (no change)
    report = run_counterfactual(rows, hold_all_uw)
    assert report.n_changed == 0
    assert report.pairs[0].alpha_delta == pytest.approx(0.0)


def test_run_counterfactual_aggregate_stats(monkeypatch):
    from tradingagents.signals.counterfactual import hold_all_uw, run_counterfactual

    # Three UW rows; counterfactual flips them to Hold.
    # If realized alphas are +5, -3, +2 → actual contribs (UW = -1) are -5, +3, -2.
    # Alternative (Hold = 0) → 0, 0, 0. Deltas = +5, -3, +2.
    rows = []
    alphas = {}
    for i, alpha in enumerate([5.0, -3.0, 2.0], start=1):
        date = f"2026-01-{i:02d}"
        rows.append({"ticker": "X", "date": date, "value": "**Rating: Underweight**"})
        alphas[("X", date, 21)] = alpha

    monkeypatch.setattr(
        "tradingagents.signals.counterfactual._compute_alpha",
        lambda ticker, date, holding_days: alphas[(ticker, date, holding_days)],
    )

    report = run_counterfactual(rows, hold_all_uw)
    assert report.n_changed == 3
    assert report.total_alpha_delta == pytest.approx(5.0 - 3.0 + 2.0)
    assert report.mean_alpha_delta == pytest.approx((5.0 - 3.0 + 2.0) / 3)
