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


# ---- Phase 1.5+ structural featurizers (added 2026-05-04 late) -----------


def test_bull_bigram_count_matches_curated_phrases():
    from tradingagents.signals.featurization import bull_bigram_count

    text = "The thesis: strong buy with high conviction and clear upside potential."
    # bigrams: ('strong', 'buy'), ('high', 'conviction'), ('clear', 'upside') = 3
    assert bull_bigram_count(text) == 3.0


def test_bull_bigram_count_zero_for_no_bullish_phrases():
    from tradingagents.signals.featurization import bull_bigram_count

    assert bull_bigram_count("Random words with no curated bigrams.") == 0.0


def test_bull_bigram_count_handles_empty():
    from tradingagents.signals.featurization import bull_bigram_count

    assert bull_bigram_count("") == 0.0


def test_bear_bigram_count_matches_curated_phrases():
    from tradingagents.signals.featurization import bear_bigram_count

    text = "Downside risk: missed estimates with declining margins on regulatory risks."
    # ('downside', 'risk'), ('missed', 'estimates'), ('declining', 'margins'),
    # ('regulatory', 'risks') = 4
    assert bear_bigram_count(text) == 4.0


def test_bear_bigram_count_zero_for_no_bearish_phrases():
    from tradingagents.signals.featurization import bear_bigram_count

    assert bear_bigram_count("Bullish thesis with strong fundamentals.") == 0.0


def test_negation_aware_sentiment_flips_negated_bullish():
    """'not bullish' should count as bearish (-1), not bullish (+1)."""
    from tradingagents.signals.featurization import negation_aware_sentiment_score

    assert negation_aware_sentiment_score("not bullish") == pytest.approx(-1.0)


def test_negation_aware_sentiment_flips_negated_bearish():
    """'not bearish' should count as bullish (+1), not bearish (-1)."""
    from tradingagents.signals.featurization import negation_aware_sentiment_score

    assert negation_aware_sentiment_score("not bearish") == pytest.approx(1.0)


def test_negation_aware_sentiment_handles_no_words():
    from tradingagents.signals.featurization import negation_aware_sentiment_score

    assert negation_aware_sentiment_score("just plain text") == 0.0


def test_negation_aware_sentiment_handles_mixed():
    """'bullish but not weak' = bullish + (negated weak = bullish?) wait.
    Actually 'weak' is bearish, so 'not weak' should count as bullish.
    bullish=2, bearish=0 → +1.0.
    """
    from tradingagents.signals.featurization import negation_aware_sentiment_score

    assert negation_aware_sentiment_score("bullish but not weak") == pytest.approx(1.0)


def test_negation_aware_sentiment_unaffected_by_distant_negation():
    """Conservative: only the IMMEDIATELY-prior word counts as negation.
    'not just bullish' has 'just' between → negation is NOT applied."""
    from tradingagents.signals.featurization import negation_aware_sentiment_score

    # bullish without an immediate negation → +1.0
    assert negation_aware_sentiment_score("not just bullish") == pytest.approx(1.0)


def test_question_density_basic():
    from tradingagents.signals.featurization import question_density

    text = "Is the rally sustainable? Will earnings beat? Three risks?"
    expected = 3 * 1000.0 / len(text)
    assert question_density(text) == pytest.approx(expected)


def test_question_density_zero_for_no_questions():
    from tradingagents.signals.featurization import question_density

    assert question_density("Statements without questions.") == 0.0


def test_question_density_zero_for_empty():
    from tradingagents.signals.featurization import question_density

    assert question_density("") == 0.0


def test_percent_mention_count_isolates_percentage_tokens():
    from tradingagents.signals.featurization import percent_mention_count

    text = "Up 5%, growth 10.5%, but $25M revenue not counted here"
    # 5%, 10.5% = 2
    assert percent_mention_count(text) == 2.0


def test_dollar_mention_count_isolates_dollar_tokens():
    from tradingagents.signals.featurization import dollar_mention_count

    text = "Revenue $2.5B, EPS $1.2, market cap $300B, but 25% growth excluded"
    # $2.5B, $1.2, $300B = 3
    assert dollar_mention_count(text) == 3.0


def test_bull_bear_keyword_ratio_balanced():
    from tradingagents.signals.featurization import bull_bear_keyword_ratio

    # bull=2 (bullish, strong), bear=2 (bearish, weak) → 0.5
    assert bull_bear_keyword_ratio("bullish strong bearish weak") == pytest.approx(0.5)


def test_bull_bear_keyword_ratio_all_bullish():
    from tradingagents.signals.featurization import bull_bear_keyword_ratio

    assert bull_bear_keyword_ratio("bullish strong upgrade") == pytest.approx(1.0)


def test_bull_bear_keyword_ratio_all_bearish():
    from tradingagents.signals.featurization import bull_bear_keyword_ratio

    assert bull_bear_keyword_ratio("bearish weak downgrade") == pytest.approx(0.0)


def test_bull_bear_keyword_ratio_no_words_returns_neutral():
    from tradingagents.signals.featurization import bull_bear_keyword_ratio

    # No bull or bear words → neutral 0.5 (instead of div-by-zero)
    assert bull_bear_keyword_ratio("plain text without sentiment") == 0.5


def test_featurizers_registry_includes_new_features():
    from tradingagents.signals.featurization import FEATURIZERS

    names = {n for n, _ in FEATURIZERS}
    assert "bull_bigram_count" in names
    assert "bear_bigram_count" in names
    assert "negation_aware_sentiment_score" in names
    assert "question_density" in names
    assert "percent_mention_count" in names
    assert "dollar_mention_count" in names
    assert "bull_bear_keyword_ratio" in names


def test_featurizers_registry_count_grew():
    from tradingagents.signals.featurization import FEATURIZERS

    # Phase 1.5 had 7; Phase 1.5+ adds 7 more → 14
    assert len(FEATURIZERS) == 14


# ---- multi-horizon evaluation ---------------------------------------------


def test_evaluate_multi_horizon_returns_one_row_per_horizon(monkeypatch):
    from tradingagents.signals.evaluation import evaluate_multi_horizon

    monkeypatch.setattr(
        "tradingagents.signals.evaluation.fetch_returns",
        lambda *a, **kw: (None, 1.5, None),
    )
    rows = [
        {"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Buy**"},
        {"ticker": "AAPL", "date": "2026-01-30", "value": "**Rating: Hold**"},
        {"ticker": "INTC", "date": "2026-01-30", "value": "**Rating: Sell**"},
    ]
    out = evaluate_multi_horizon("final_trade_decision", rows, [5, 10, 21, 90])
    assert set(out.keys()) == {5, 10, 21, 90}
    for h, ev in out.items():
        assert ev["horizon"] == h
        assert ev["signal_id"] == "final_trade_decision"
        # 3 rows with non-None alpha => n_eval=3
        assert ev["n_eval"] == 3


def test_evaluate_multi_horizon_alpha_cache_keyed_by_horizon(monkeypatch):
    """Each (ticker, date, horizon) should be fetched once across calls."""
    from tradingagents.signals.evaluation import evaluate_multi_horizon

    call_count = {"n": 0}

    def fake(ticker, date, holding_days):
        call_count["n"] += 1
        return (None, 1.0, None)

    monkeypatch.setattr("tradingagents.signals.evaluation.fetch_returns", fake)

    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Buy**"}]
    cache: dict = {}
    evaluate_multi_horizon("final_trade_decision", rows, [5, 10, 21], cache)
    # 1 row × 3 horizons → 3 unique (ticker, date, horizon) keys → 3 fetches
    assert call_count["n"] == 3
    # Re-running should hit cache, no new fetches
    evaluate_multi_horizon("final_trade_decision", rows, [5, 10, 21], cache)
    assert call_count["n"] == 3


def test_evaluate_multi_horizon_non_numeric_signal_returns_coverage_only(monkeypatch):
    from tradingagents.signals.evaluation import evaluate_multi_horizon

    monkeypatch.setattr(
        "tradingagents.signals.evaluation.fetch_returns",
        lambda *a, **kw: (None, 1.0, None),
    )
    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "prose"}]
    out = evaluate_multi_horizon("market_report", rows, [5, 21])
    assert set(out.keys()) == {5, 21}
    for _h, ev in out.items():
        assert ev["n_eval"] == 0
        assert ev["ic"] is None


def test_evaluate_features_multi_horizon_returns_per_feature_per_horizon(monkeypatch):
    from tradingagents.signals.evaluation import evaluate_features_multi_horizon
    from tradingagents.signals.featurization import FEATURIZERS

    monkeypatch.setattr(
        "tradingagents.signals.evaluation.fetch_returns",
        lambda *a, **kw: (None, 1.0, None),
    )
    rows = [{"ticker": "NVDA", "date": "2026-01-30", "value": "bullish strong upgrade"}]
    horizons = [5, 21, 90]
    out = evaluate_features_multi_horizon("market_report", rows, horizons)
    # Should have len(FEATURIZERS) × len(horizons) rows
    assert len(out) == len(FEATURIZERS) * len(horizons)
    # Each row has feature + horizon set
    for ev in out:
        assert ev["feature"] in {f[0] for f in FEATURIZERS}
        assert ev["horizon"] in horizons


def test_evaluate_features_multi_horizon_skips_non_prose():
    from tradingagents.signals.evaluation import evaluate_features_multi_horizon

    out = evaluate_features_multi_horizon(
        "final_trade_decision",
        [{"ticker": "NVDA", "date": "2026-01-30", "value": "**Rating: Buy**"}],
        [5, 21],
    )
    assert out == []


# ---- within-ticker IC summary (artifact-check methodology) ----------------


def test_within_ticker_ic_summary_returns_none_when_no_ticker_meets_threshold():
    from tradingagents.signals.evaluation import _within_ticker_ic_summary

    pairs_by_ticker = {
        "NVDA": [(1.0, 0.1), (2.0, 0.2)],  # n=2, below default min_n=5
        "AAPL": [(1.0, 0.05)],  # n=1
    }
    assert _within_ticker_ic_summary(pairs_by_ticker) is None


def test_within_ticker_ic_summary_computes_median_and_counts():
    from tradingagents.signals.evaluation import _within_ticker_ic_summary

    # 3 tickers with n>=5; constructed so per-ticker ICs are roughly +1, -1, 0
    pairs_by_ticker = {
        "POS": [(i, i + 0.1) for i in range(5)],  # perfectly positive
        "NEG": [(i, -i + 0.1) for i in range(5)],  # perfectly negative
        "MIX": [(1, 0.5), (2, 0.3), (3, 0.4), (4, 0.2), (5, 0.6)],  # mostly noise
    }
    summary = _within_ticker_ic_summary(pairs_by_ticker)
    assert summary is not None
    assert summary["n_tickers_evaluated"] == 3
    # Median of {+1, -1, ~0} ≈ 0
    assert -0.5 < summary["median_ic"] < 0.5
    assert summary["n_positive"] >= 1
    assert summary["n_negative"] >= 1
    assert summary["max_abs_ic"] == pytest.approx(1.0, abs=0.01)
    assert len(summary["per_ticker"]) == 3


def test_within_ticker_ic_summary_skips_below_threshold_but_includes_others():
    from tradingagents.signals.evaluation import _within_ticker_ic_summary

    pairs_by_ticker = {
        "BIG": [(i, i) for i in range(8)],  # n=8, perfectly correlated
        "SMALL": [(1, 1)],  # n=1, below threshold
    }
    summary = _within_ticker_ic_summary(pairs_by_ticker)
    assert summary is not None
    assert summary["n_tickers_evaluated"] == 1
    assert summary["median_ic"] == pytest.approx(1.0)
    # SMALL still appears in per_ticker but with ic=None
    by_ticker = {row["ticker"]: row for row in summary["per_ticker"]}
    assert by_ticker["SMALL"]["ic"] is None
    assert by_ticker["BIG"]["ic"] == pytest.approx(1.0)


def test_evaluate_multi_horizon_populates_within_ticker_for_final_trade_decision(monkeypatch):
    """Each horizon should carry a within_ticker summary."""
    from tradingagents.signals.evaluation import evaluate_multi_horizon

    # Make alpha depend on (ticker, date) so per-ticker IC is non-degenerate
    def fake_fetch(ticker, date, holding_days):
        # NVDA gets +α aligned with rating; AAPL gets -α (anti-aligned)
        # so the within-ticker breakdown shows mixed signs.
        return (None, 0.05 if ticker.startswith("NV") else -0.05, None)

    monkeypatch.setattr("tradingagents.signals.evaluation.fetch_returns", fake_fetch)

    rows = []
    # 6 dates per ticker × 2 tickers = 12 rows
    for i in range(6):
        rows.append({"ticker": "NVDA", "date": f"2026-01-{i + 1:02d}", "value": "**Rating: Buy**"})
        rows.append({"ticker": "AAPL", "date": f"2026-01-{i + 1:02d}", "value": "**Rating: Sell**"})
    out = evaluate_multi_horizon("final_trade_decision", rows, [21])
    ev = out[21]
    assert "within_ticker" in ev
    # All alphas constant per ticker → within-ticker IC is undefined (no
    # variance) → summary returns None
    assert ev["within_ticker"] is None


def test_evaluate_features_multi_horizon_populates_within_ticker(monkeypatch):
    from tradingagents.signals.evaluation import evaluate_features_multi_horizon

    # Vary alpha per (ticker, date) so within-ticker IC can be computed
    def fake_fetch(ticker, date, holding_days):
        # Decode the date suffix as a small float to give variance
        idx = int(date.split("-")[-1])
        return (None, idx * 0.01 if ticker == "NVDA" else -idx * 0.01, None)

    monkeypatch.setattr("tradingagents.signals.evaluation.fetch_returns", fake_fetch)

    rows = []
    # Vary keyword density per row so featurizer values vary within each ticker
    bull_words = ["bullish growth strong upgrade beat", "growth upgrade", "bullish", "", "", ""]
    bear_words = ["", "", "", "downside risk", "downside risk decline", "decline weak miss"]
    for i in range(6):
        text = f"{bull_words[i]} something neutral {bear_words[i]}"
        rows.append({"ticker": "NVDA", "date": f"2026-01-{i + 1:02d}", "value": text})
        rows.append({"ticker": "AAPL", "date": f"2026-01-{i + 1:02d}", "value": text})

    out = evaluate_features_multi_horizon("market_report", rows, [21])
    # Each (feature, horizon) row should have within_ticker in its keys
    assert all("within_ticker" in ev for ev in out)
    # At least one feature should have a within-ticker summary populated
    summaries = [ev["within_ticker"] for ev in out if ev["within_ticker"] is not None]
    assert summaries, "expected at least one within_ticker summary"
    # Each summary has the expected keys
    for s in summaries:
        assert {"median_ic", "n_tickers_evaluated", "n_positive", "n_negative"} <= s.keys()


def test_format_within_cell_flags_simpsons_paradox():
    """When aggregate IC sign disagrees with within-ticker median sign,
    the cell should include the ⚠️ Simpson's-paradox marker."""
    from tradingagents.signals.evaluation import _format_within_cell

    # Aggregate is positive, within-ticker median is negative → flag
    cell = _format_within_cell(
        +0.30,
        {
            "median_ic": -0.16,
            "n_tickers_evaluated": 6,
            "n_positive": 2,
            "n_negative": 4,
            "max_abs_ic": 0.50,
            "per_ticker": [],
        },
    )
    assert "⚠️" in cell
    assert "-0.160" in cell
    assert "(6t: 2+/4−)" in cell


def test_format_within_cell_no_flag_when_signs_agree():
    from tradingagents.signals.evaluation import _format_within_cell

    cell = _format_within_cell(
        -0.40,
        {
            "median_ic": -0.16,
            "n_tickers_evaluated": 6,
            "n_positive": 2,
            "n_negative": 4,
            "max_abs_ic": 0.50,
            "per_ticker": [],
        },
    )
    assert "⚠️" not in cell
    assert "-0.160" in cell


def test_format_within_cell_handles_none():
    from tradingagents.signals.evaluation import _format_within_cell

    assert _format_within_cell(None, None) == "—"
    assert _format_within_cell(0.5, None) == "—"
