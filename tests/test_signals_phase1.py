"""Tests for spec 002 Phase 1 (evaluation harness) + the backfill script.

Phase 1 ships ``scripts/evaluate_signals.py`` with the math primitives:
- _spearman_ic — rank correlation
- _hit_rate — directional agreement
- _coverage_stats — n / unique tickers / unique dates / mean value length
- _evaluate_signal — per-signal pipeline (coverage + IC + hit rate)

Tests cover the math primitives in isolation. The backfill script is
covered by smoke + dry-run tests.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.unit


# ---- evaluate_signals math primitives --------------------------------------


def test_spearman_ic_perfect_positive():
    from tradingagents.signals.evaluation import _spearman_ic

    # x = [1, 2, 3, 4, 5], y = [10, 20, 30, 40, 50] — perfect rank correlation
    pairs = [(1.0, 10.0), (2.0, 20.0), (3.0, 30.0), (4.0, 40.0), (5.0, 50.0)]
    ic = _spearman_ic(pairs)
    assert ic == pytest.approx(1.0, abs=1e-6)


def test_spearman_ic_perfect_negative():
    from tradingagents.signals.evaluation import _spearman_ic

    pairs = [(1.0, 50.0), (2.0, 40.0), (3.0, 30.0), (4.0, 20.0), (5.0, 10.0)]
    ic = _spearman_ic(pairs)
    assert ic == pytest.approx(-1.0, abs=1e-6)


def test_spearman_ic_no_correlation():
    from tradingagents.signals.evaluation import _spearman_ic

    # Constructed to have near-zero rank correlation
    pairs = [(1.0, 30.0), (2.0, 10.0), (3.0, 50.0), (4.0, 20.0), (5.0, 40.0)]
    ic = _spearman_ic(pairs)
    assert ic is not None
    assert abs(ic) < 0.5


def test_spearman_ic_handles_ties():
    from tradingagents.signals.evaluation import _spearman_ic

    # Ties in x — average ranks per the implementation
    pairs = [(1.0, 10.0), (1.0, 20.0), (2.0, 30.0), (2.0, 40.0)]
    ic = _spearman_ic(pairs)
    assert ic is not None
    assert -1.0 <= ic <= 1.0


def test_spearman_ic_returns_none_for_small_n():
    from tradingagents.signals.evaluation import _spearman_ic

    assert _spearman_ic([(1.0, 2.0), (3.0, 4.0)]) is None
    assert _spearman_ic([]) is None


def test_spearman_ic_returns_none_for_no_variance():
    from tradingagents.signals.evaluation import _spearman_ic

    pairs = [(5.0, 10.0), (5.0, 20.0), (5.0, 30.0)]  # x has no variance
    assert _spearman_ic(pairs) is None
    pairs = [(1.0, 5.0), (2.0, 5.0), (3.0, 5.0)]  # y has no variance
    assert _spearman_ic(pairs) is None


# ---- hit_rate --------------------------------------------------------------


def test_hit_rate_bullish_agreement():
    from tradingagents.signals.evaluation import _hit_rate

    # All positive signals + positive alphas = 100% hit
    pairs = [(2, 1.5), (1, 0.8), (1, 2.0)]
    assert _hit_rate(pairs) == pytest.approx(1.0)


def test_hit_rate_bearish_agreement():
    from tradingagents.signals.evaluation import _hit_rate

    # All negative signals + negative alphas = 100% hit
    pairs = [(-2, -1.5), (-1, -0.8), (-1, -2.0)]
    assert _hit_rate(pairs) == pytest.approx(1.0)


def test_hit_rate_hold_with_small_alpha_counts_as_hit():
    from tradingagents.signals.evaluation import _hit_rate

    # Hold (sig=0) with |alpha| < 0.5 counts as hit per the implementation
    pairs = [(0, 0.2), (0, -0.4), (0, 0.0)]
    assert _hit_rate(pairs) == pytest.approx(1.0)


def test_hit_rate_hold_with_large_alpha_misses():
    from tradingagents.signals.evaluation import _hit_rate

    pairs = [(0, 5.0), (0, -3.0)]
    assert _hit_rate(pairs) == pytest.approx(0.0)


def test_hit_rate_mixed():
    from tradingagents.signals.evaluation import _hit_rate

    pairs = [(2, 1.0), (1, -0.5), (-1, -2.0), (0, 0.1)]
    # hits: (2, 1.0) ✓, (1, -0.5) ✗, (-1, -2.0) ✓, (0, 0.1) ✓ = 3/4
    assert _hit_rate(pairs) == pytest.approx(0.75)


def test_hit_rate_empty_returns_none():
    from tradingagents.signals.evaluation import _hit_rate

    assert _hit_rate([]) is None


# ---- coverage_stats --------------------------------------------------------


def test_coverage_stats_basic():
    from tradingagents.signals.evaluation import _coverage_stats

    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": "abc"},
        {"ticker": "NVDA", "date": "2026-02-06", "value": "abcdef"},
        {"ticker": "AAPL", "date": "2026-01-30", "value": "abcdefghij"},
    ]
    cov = _coverage_stats(rows)
    assert cov["n"] == 3
    assert cov["tickers"] == 2
    assert cov["dates"] == 2
    assert cov["mean_len"] == int((3 + 6 + 10) / 3)


def test_coverage_stats_empty():
    from tradingagents.signals.evaluation import _coverage_stats

    cov = _coverage_stats([])
    assert cov == {"n": 0, "tickers": 0, "dates": 0, "mean_len": 0}


def test_coverage_stats_handles_none_value():
    from tradingagents.signals.evaluation import _coverage_stats

    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": None},
        {"ticker": "NVDA", "date": "2026-02-06", "value": "abc"},
    ]
    cov = _coverage_stats(rows)
    assert cov["n"] == 2
    assert cov["mean_len"] == int((0 + 3) / 2)


# ---- evaluate_signal: end-to-end with mocked alpha -------------------------


def test_evaluate_signal_final_trade_decision_extracts_rating(monkeypatch):
    """For final_trade_decision, parse_rating extracts the 5-tier rating
    and converts to numeric score for IC computation."""
    from tradingagents.signals.evaluation import _evaluate_signal

    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Buy**\nbody"},
        {"ticker": "AAPL", "date": "2026-01-30", "value": "**Rating: Hold**\nbody"},
        {"ticker": "INTC", "date": "2026-01-30", "value": "**Rating: Sell**\nbody"},
    ]

    # Mock fetch_returns to return predictable alphas
    fake_alphas = {
        ("NVDA", "2026-01-30"): 2.5,
        ("AAPL", "2026-01-30"): 0.1,
        ("INTC", "2026-01-30"): -3.0,
    }

    def fake_fetch(ticker, date, holding_days):
        return (None, fake_alphas.get((ticker, date)), None)

    monkeypatch.setattr("tradingagents.signals.evaluation.fetch_returns", fake_fetch)

    ev = _evaluate_signal("final_trade_decision", rows, horizon_days=21)
    assert ev["signal_id"] == "final_trade_decision"
    assert ev["n"] == 3
    assert ev["n_eval"] == 3
    # Buy=+2 → +2.5α, Hold=0 → 0.1α, Sell=-2 → -3.0α: perfect positive correlation
    assert ev["ic"] == pytest.approx(1.0, abs=1e-6)


def test_evaluate_signal_prose_signal_skips_ic(monkeypatch):
    """Non-final_trade_decision signals report coverage only, not IC."""
    from tradingagents.signals.evaluation import _evaluate_signal

    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": "# Market analysis prose..."},
    ]

    # Even with mocked alpha, prose signals shouldn't try to compute IC
    monkeypatch.setattr(
        "tradingagents.signals.evaluation.fetch_returns", lambda *a, **kw: (None, 1.0, None)
    )

    ev = _evaluate_signal("market_report", rows, horizon_days=21)
    assert ev["n"] == 1
    assert ev["ic"] is None
    assert ev["hit_rate"] is None
    assert ev["n_eval"] == 0


def test_evaluate_signal_skips_pairs_with_missing_alpha(monkeypatch):
    from tradingagents.signals.evaluation import _evaluate_signal

    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Buy**"},
        {"ticker": "AAPL", "date": "2026-01-30", "value": "**Rating: Hold**"},
        {"ticker": "INTC", "date": "2026-01-30", "value": "**Rating: Sell**"},
    ]

    # AAPL alpha is None (e.g., date too recent)
    def fake_fetch(ticker, date, holding_days):
        if ticker == "AAPL":
            return (None, None, None)
        return (None, 1.0 if ticker == "NVDA" else -1.0, None)

    monkeypatch.setattr("tradingagents.signals.evaluation.fetch_returns", fake_fetch)

    ev = _evaluate_signal("final_trade_decision", rows, horizon_days=21)
    assert ev["n"] == 3  # all rows cached
    assert ev["n_eval"] == 2  # only NVDA + INTC have alpha


# ---- backfill script: synthesis-signal extraction --------------------------


def test_backfill_one_extracts_synthesis_signals(tmp_path, monkeypatch):
    """backfill_one reads a state log JSON and writes one cache row per
    synthesis signal that has a non-empty string value."""
    from tradingagents.signals.backfill import backfill_one

    state = {
        "company_of_interest": "NVDA",
        "trade_date": "2026-01-30",
        "market_report": "Market analysis prose...",
        "news_report": "News prose...",
        "fundamentals_report": "Fundamentals prose...",
        "sentiment_report": "",  # empty — should be skipped
        "investment_plan": "Bull/bear synthesis...",
        "final_trade_decision": "**Rating: Overweight**\nbody",
        # investment_debate_state is a dict, not a string — should be skipped
        "investment_debate_state": {"history": "..."},
    }
    log_path = tmp_path / "full_states_log_2026-01-30.json"
    log_path.write_text(json.dumps(state), encoding="utf-8")

    written: list[dict] = []

    def fake_record(**kwargs):
        written.append(kwargs)

    monkeypatch.setattr("tradingagents.signals.backfill.record_value", fake_record)

    counts = backfill_one("NVDA", log_path, dry_run=False)
    # 5 non-empty string fields written (market, news, fundamentals,
    # investment_plan, final_trade_decision); sentiment is empty, debate is dict
    assert counts["market_report"] == 1
    assert counts["news_report"] == 1
    assert counts["fundamentals_report"] == 1
    assert counts["sentiment_report"] == 0
    assert counts["investment_plan"] == 1
    assert counts["final_trade_decision"] == 1
    assert len(written) == 5
    # Verify ticker normalization + date passthrough
    for w in written:
        assert w["ticker"] == "NVDA"
        assert w["date"] == "2026-01-30"
        assert w["fetcher_version"] == "synthesis_v1"


def test_backfill_one_dry_run_does_not_write(tmp_path, monkeypatch):
    from tradingagents.signals.backfill import backfill_one

    state = {
        "company_of_interest": "AAPL",
        "trade_date": "2026-02-06",
        "market_report": "prose",
        "final_trade_decision": "**Rating: Hold**",
    }
    log_path = tmp_path / "full_states_log_2026-02-06.json"
    log_path.write_text(json.dumps(state), encoding="utf-8")

    written: list[dict] = []
    monkeypatch.setattr(
        "tradingagents.signals.backfill.record_value",
        lambda **kw: written.append(kw),
    )

    counts = backfill_one("AAPL", log_path, dry_run=True)
    # Counts are still tracked, but record_value is NOT called
    assert counts["market_report"] == 1
    assert counts["final_trade_decision"] == 1
    assert len(written) == 0  # dry-run skipped real writes


def test_backfill_one_skips_log_without_trade_date(tmp_path, monkeypatch):
    from tradingagents.signals.backfill import backfill_one

    state = {"company_of_interest": "NVDA"}  # missing trade_date
    log_path = tmp_path / "full_states_log_bad.json"
    log_path.write_text(json.dumps(state), encoding="utf-8")

    monkeypatch.setattr("tradingagents.signals.backfill.record_value", lambda **kw: None)
    counts = backfill_one("NVDA", log_path, dry_run=False)
    assert counts["__skipped__"] == 1
    assert counts["market_report"] == 0


def test_backfill_one_skips_malformed_json(tmp_path, monkeypatch):
    from tradingagents.signals.backfill import backfill_one

    log_path = tmp_path / "full_states_log_bad.json"
    log_path.write_text("not valid json {{{", encoding="utf-8")

    monkeypatch.setattr("tradingagents.signals.backfill.record_value", lambda **kw: None)
    counts = backfill_one("NVDA", log_path, dry_run=False)
    assert counts["__skipped__"] == 1
