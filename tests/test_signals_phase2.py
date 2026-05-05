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


# ---- Phase 2.5: apply_drift_actions ---------------------------------------


def _make_report(
    signal_id: str = "test_signal",
    feature: str | None = None,
    ic_decline_alert: bool = True,
    ks_drift_alert: bool = False,
    ic_baseline: float | None = -0.1,
    ic_recent: float | None = -0.3,
    ic_decline: float | None = 0.2,
):
    from tradingagents.signals.drift import DriftReport

    return DriftReport(
        signal_id=signal_id,
        feature=feature,
        horizon_days=21,
        n_total=100,
        n_recent=30,
        n_baseline=70,
        ic_recent=ic_recent,
        ic_baseline=ic_baseline,
        ic_decline=ic_decline,
        ic_decline_alert=ic_decline_alert,
        ks_statistic=0.15,
        ks_drift_alert=ks_drift_alert,
    )


def test_apply_drift_actions_demotes_production_to_deprecated(tmp_path, monkeypatch):
    """A production signal with IC-decline alert is auto-demoted to deprecated."""
    from tradingagents.signals.drift import apply_drift_actions
    from tradingagents.signals.registry import register_signal

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)
    register_signal("s1", "S1", "x.y", ["a"], state="production", registry_path=reg)

    actions = apply_drift_actions([_make_report(signal_id="s1")])
    assert len(actions) == 1
    assert actions[0].signal_id == "s1"
    assert actions[0].from_state == "production"
    assert actions[0].to_state == "deprecated"
    assert actions[0].applied is True
    assert "IC decline" in actions[0].reason

    # Verify registry was actually updated
    from tradingagents.signals.registry import get_signal

    sig = get_signal("s1", registry_path=reg)
    assert sig.state == "deprecated"


def test_apply_drift_actions_demotes_deprecated_to_archived(tmp_path, monkeypatch):
    from tradingagents.signals.drift import apply_drift_actions
    from tradingagents.signals.registry import register_signal

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)
    register_signal("s2", "S2", "x.y", ["a"], state="deprecated", registry_path=reg)

    actions = apply_drift_actions([_make_report(signal_id="s2")])
    assert actions[0].to_state == "archived"
    from tradingagents.signals.registry import get_signal

    assert get_signal("s2", registry_path=reg).state == "archived"


def test_apply_drift_actions_skips_non_alerts(tmp_path, monkeypatch):
    """No alert → no action."""
    from tradingagents.signals.drift import apply_drift_actions

    actions = apply_drift_actions([_make_report(signal_id="s3", ic_decline_alert=False)])
    assert actions == []


def test_apply_drift_actions_skips_ks_only_alerts(tmp_path, monkeypatch):
    """KS-only alerts (no IC decline) don't trigger transitions per spec
    Edge Case ('drift can be benign; flag for human review instead')."""
    from tradingagents.signals.drift import apply_drift_actions

    actions = apply_drift_actions(
        [
            _make_report(
                signal_id="s4",
                ic_decline_alert=False,
                ks_drift_alert=True,
            )
        ]
    )
    assert actions == []


def test_apply_drift_actions_skips_per_feature_reports(tmp_path, monkeypatch):
    """Per-feature drift reports are diagnostic — only signal-level reports
    trigger state transitions."""
    from tradingagents.signals.drift import apply_drift_actions
    from tradingagents.signals.registry import register_signal

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)
    register_signal("market_report", "M", "x.y", ["a"], registry_path=reg)

    actions = apply_drift_actions(
        [
            _make_report(signal_id="market_report", feature="sentiment_score"),
        ]
    )
    assert actions == []  # feature-level → skipped


def test_apply_drift_actions_skips_unregistered_signals(tmp_path, monkeypatch):
    """If a signal isn't in the registry, the action is silently skipped."""
    from tradingagents.signals.drift import apply_drift_actions

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)

    actions = apply_drift_actions([_make_report(signal_id="nonexistent")])
    assert actions == []


def test_apply_drift_actions_skips_archived_signals(tmp_path, monkeypatch):
    """Already-archived signals can't be demoted further."""
    from tradingagents.signals.drift import apply_drift_actions
    from tradingagents.signals.registry import register_signal

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)
    register_signal("s5", "S5", "x.y", ["a"], state="archived", registry_path=reg)

    actions = apply_drift_actions([_make_report(signal_id="s5")])
    assert actions == []


def test_apply_drift_actions_skips_candidate_and_experimental(tmp_path, monkeypatch):
    """Candidate / experimental signals aren't on the production-stability
    ladder; auto-demotion only applies to production -> deprecated -> archived."""
    from tradingagents.signals.drift import apply_drift_actions
    from tradingagents.signals.registry import register_signal

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)
    register_signal("s6", "S6", "x.y", ["a"], state="candidate", registry_path=reg)
    register_signal("s7", "S7", "x.y", ["a"], state="experimental", registry_path=reg)

    actions = apply_drift_actions(
        [
            _make_report(signal_id="s6"),
            _make_report(signal_id="s7"),
        ]
    )
    assert actions == []


def test_apply_drift_actions_dry_run_does_not_mutate_registry(tmp_path, monkeypatch):
    from tradingagents.signals.drift import apply_drift_actions
    from tradingagents.signals.registry import get_signal, register_signal

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)
    register_signal("s8", "S8", "x.y", ["a"], state="production", registry_path=reg)

    actions = apply_drift_actions([_make_report(signal_id="s8")], dry_run=True)
    # The action is reported as a preview...
    assert len(actions) == 1
    assert actions[0].applied is False
    assert actions[0].to_state == "deprecated"
    # ...but the registry is NOT updated
    sig = get_signal("s8", registry_path=reg)
    assert sig.state == "production"


def test_apply_drift_actions_includes_reason_with_ic_values(tmp_path, monkeypatch):
    from tradingagents.signals.drift import apply_drift_actions
    from tradingagents.signals.registry import register_signal

    reg = tmp_path / "registry.jsonl"
    monkeypatch.setattr("tradingagents.signals.registry.get_registry_path", lambda: reg)
    register_signal("s9", "S9", "x.y", ["a"], state="production", registry_path=reg)

    actions = apply_drift_actions(
        [
            _make_report(
                signal_id="s9",
                ic_baseline=-0.05,
                ic_recent=-0.20,
                ic_decline=0.15,
            )
        ]
    )
    reason = actions[0].reason
    # Specific IC values appear in the reason for auditability
    assert "0.150" in reason or "+0.15" in reason
    assert "21d" in reason


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


# ---- analyze_backtest counterfactual integration contract --------------


def test_analyzer_row_shape_contract_round_trips_all_5_ratings():
    """analyze_backtest builds counterfactual rows as `{ticker, date,
    value: "**Rating**: <rating>"}`. Confirm parse_rating extracts each
    of the 5 canonical ratings from this exact format — locks in the
    contract that scripts/analyze_backtest.py depends on."""
    from tradingagents.agents.utils.rating import parse_rating

    for rating in ["Buy", "Overweight", "Hold", "Underweight", "Sell"]:
        synthetic = f"**Rating**: {rating}"
        assert parse_rating(synthetic) == rating, (
            f"analyze_backtest row-shape contract broke: parse_rating({synthetic!r}) != {rating!r}"
        )


def test_analyzer_counterfactual_uses_pre_seeded_alpha_cache(monkeypatch):
    """When analyze_backtest pre-populates the alpha cache from its
    enriched DataFrame, run_counterfactual must not call _compute_alpha
    again (would re-fetch from yfinance, defeats the cache reuse)."""
    from tradingagents.signals.counterfactual import hold_all_ow, run_counterfactual

    fetch_count = {"n": 0}

    def _fail_if_fetched(ticker, date, holding_days):
        fetch_count["n"] += 1
        return None

    monkeypatch.setattr(
        "tradingagents.signals.counterfactual._compute_alpha",
        _fail_if_fetched,
    )

    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating**: Overweight"},
        {"ticker": "AAPL", "date": "2026-02-06", "value": "**Rating**: Buy"},
    ]
    pre_cache: dict[tuple[str, str, int], float | None] = {
        ("NVDA", "2026-01-30", 21): 0.05,
        ("AAPL", "2026-02-06", 21): -0.03,
    }
    report = run_counterfactual(rows, hold_all_ow, horizon_days=21, alpha_cache=pre_cache)
    # No fetches should have happened — both alphas were pre-cached
    assert fetch_count["n"] == 0
    # Both rows changed (Overweight → Hold, Buy → Hold)
    assert report.n_changed == 2
