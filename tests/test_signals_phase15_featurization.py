"""Tests for spec 002 Phase 1.5 — feature extraction for prose signals."""

from __future__ import annotations

import pytest

from tradingagents.signals.featurization import (
    FEATURIZERS,
    PROSE_SIGNAL_IDS,
    bear_keyword_count,
    bull_keyword_count,
    conviction_density,
    hedge_density,
    numeric_mention_count,
    sentiment_score,
    value_length,
)

pytestmark = pytest.mark.unit


# ---- value_length ----------------------------------------------------------


def test_value_length_counts_chars():
    assert value_length("hello") == 5.0
    assert value_length("") == 0.0
    assert value_length(None) == 0.0  # type: ignore[arg-type]


# ---- bull / bear keyword counting ------------------------------------------


def test_bull_keyword_count_basic():
    text = "The stock is bullish with strong momentum and an upgrade outlook."
    # bullish, strong, momentum, upgrade = 4
    assert bull_keyword_count(text) == 4.0


def test_bear_keyword_count_basic():
    text = "Bearish concerns: weak guidance, downgrade risk, and declining margins."
    # bearish, concerns, weak, downgrade, risk, declining = 6
    assert bear_keyword_count(text) == 6.0


def test_keyword_counts_are_case_insensitive():
    assert bull_keyword_count("STRONG buy momentum") == bull_keyword_count("strong buy momentum")


def test_keyword_counts_use_word_boundaries():
    """'risk' should match 'risk' but not 'whisker'."""
    # whisker contains "isk" but not "risk" as a word — should not match
    assert bear_keyword_count("whisker something else") == 0.0
    assert bear_keyword_count("risk profile") == 1.0


def test_keyword_counts_handle_empty_text():
    assert bull_keyword_count("") == 0.0
    assert bear_keyword_count("") == 0.0


# ---- sentiment_score -------------------------------------------------------


def test_sentiment_score_all_bullish():
    text = "bullish bullish strong momentum upgrade"
    assert sentiment_score(text) == pytest.approx(1.0)


def test_sentiment_score_all_bearish():
    text = "bearish bearish weak downgrade decline"
    assert sentiment_score(text) == pytest.approx(-1.0)


def test_sentiment_score_balanced():
    text = "bullish bearish"
    assert sentiment_score(text) == pytest.approx(0.0)


def test_sentiment_score_mixed_more_bull():
    # 3 bull, 1 bear → (3-1)/(3+1) = 0.5
    text = "bullish strong upgrade weak"
    assert sentiment_score(text) == pytest.approx(0.5)


def test_sentiment_score_no_sentiment_words():
    """Returns 0.0 when no bull/bear keywords appear (avoid div by zero)."""
    text = "The quarterly report was published today."
    assert sentiment_score(text) == 0.0


def test_sentiment_score_handles_empty():
    assert sentiment_score("") == 0.0


# ---- hedge_density / conviction_density ------------------------------------


def test_hedge_density_per_1000_chars():
    # Build a text with 1 hedge word in 100 chars — density = 10/1000-chars
    base = "x" * 95  # 95 chars
    text = base + " might"  # 95 + 6 = 101 chars, 1 hedge word
    density = hedge_density(text)
    assert density == pytest.approx(1000.0 / 101.0)


def test_hedge_density_zero_for_empty():
    assert hedge_density("") == 0.0


def test_hedge_density_zero_when_no_hedges():
    text = "The price is rising and momentum is strong"
    assert hedge_density(text) == 0.0


def test_conviction_density_basic():
    text = "The signal is strong and clear, definitively bullish."
    # strong, clear, definitively = 3 conviction words
    assert conviction_density(text) > 0
    expected = 3 * 1000.0 / len(text)
    assert conviction_density(text) == pytest.approx(expected)


# ---- numeric_mention_count -------------------------------------------------


def test_numeric_mention_count_dollar_amounts():
    text = "Revenue was $2.5B, up from $1.8B prior, with 25% growth"
    # Matches: $2.5B, $1.8B, 25% = 3
    assert numeric_mention_count(text) == 3.0


def test_numeric_mention_count_percentages():
    text = "Up 5% today and 10% YTD"
    assert numeric_mention_count(text) == 2.0


def test_numeric_mention_count_decimals():
    text = "Multiple is 23.5 and PEG is 0.63"
    assert numeric_mention_count(text) == 2.0


def test_numeric_mention_count_zero_for_no_numbers():
    text = "This text has no numbers in any quantitative form."
    assert numeric_mention_count(text) == 0.0


def test_numeric_mention_count_handles_empty():
    assert numeric_mention_count("") == 0.0


# ---- FEATURIZERS registry --------------------------------------------------


def test_featurizers_registry_is_non_empty():
    assert len(FEATURIZERS) >= 5


def test_featurizers_all_callable_with_string():
    """Every featurizer in the registry must accept a string and return a number."""
    for name, fn in FEATURIZERS:
        out = fn("test text")
        assert isinstance(out, (int, float)), f"{name} returned non-numeric"


def test_featurizers_all_handle_empty_string():
    for name, fn in FEATURIZERS:
        out = fn("")
        assert isinstance(out, (int, float)), f"{name} broke on empty string"


def test_featurizer_names_are_unique():
    names = [name for name, _ in FEATURIZERS]
    assert len(names) == len(set(names))


# ---- PROSE_SIGNAL_IDS constant ---------------------------------------------


def test_prose_signal_ids_includes_all_synthesis_prose():
    assert "market_report" in PROSE_SIGNAL_IDS
    assert "news_report" in PROSE_SIGNAL_IDS
    assert "fundamentals_report" in PROSE_SIGNAL_IDS
    assert "investment_plan" in PROSE_SIGNAL_IDS
    assert "sentiment_report" in PROSE_SIGNAL_IDS


def test_prose_signal_ids_excludes_final_trade_decision():
    """final_trade_decision uses parse_rating in Phase 1, not featurization."""
    assert "final_trade_decision" not in PROSE_SIGNAL_IDS


# ---- _evaluate_signal_features integration ---------------------------------


def test_evaluate_signal_features_returns_one_per_featurizer(monkeypatch):
    from tradingagents.signals.evaluation import _evaluate_signal_features

    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": "bullish strong upgrade momentum"},
        {"ticker": "AAPL", "date": "2026-01-30", "value": "weak bearish downgrade"},
        {"ticker": "INTC", "date": "2026-01-30", "value": "uncertain mixed concerns"},
    ]
    monkeypatch.setattr(
        "tradingagents.signals.evaluation.fetch_returns",
        lambda *a, **kw: (None, 1.0, None),
    )

    out = _evaluate_signal_features("market_report", rows, horizon_days=21)
    # One row per featurizer
    assert len(out) == len(FEATURIZERS)
    for ev in out:
        assert ev["signal_id"] == "market_report"
        assert ev["feature"] in {f[0] for f in FEATURIZERS}


def test_evaluate_signal_features_skips_non_prose():
    from tradingagents.signals.evaluation import _evaluate_signal_features

    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Buy**"}]
    out = _evaluate_signal_features("final_trade_decision", rows, horizon_days=21)
    assert out == []


def test_evaluate_signal_features_alpha_cache_dedupes(monkeypatch):
    """The shared alpha_cache should prevent fetch_returns from being called
    multiple times for the same (ticker, date)."""
    from tradingagents.signals.evaluation import _evaluate_signal_features

    call_count = 0

    def fake_fetch(ticker, date, holding_days):
        nonlocal call_count
        call_count += 1
        return (None, 1.0, None)

    monkeypatch.setattr("tradingagents.signals.evaluation.fetch_returns", fake_fetch)

    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "bullish"}]
    cache: dict = {}
    _evaluate_signal_features("market_report", rows, horizon_days=21, alpha_cache=cache)
    # 1 row × N featurizers but only 1 unique (ticker, date) pair → 1 fetch call total
    assert call_count == 1


def test_evaluate_signal_features_skips_pairs_with_no_alpha(monkeypatch):
    from tradingagents.signals.evaluation import _evaluate_signal_features

    monkeypatch.setattr(
        "tradingagents.signals.evaluation.fetch_returns",
        lambda *a, **kw: (None, None, None),
    )
    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "bullish"}]
    out = _evaluate_signal_features("market_report", rows, horizon_days=21)
    # Each feature row will have n_eval=0 and ic=None
    for ev in out:
        assert ev["n_eval"] == 0
        assert ev["ic"] is None
