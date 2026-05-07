"""Integration tests for Spec 008 Hybrid C calendar boost layer wired into spec 007.

Verifies SC-005 (default-off integrity), SC-007 (state annotation completeness),
and SC-003 path-through (yfinance failure → spec 007 baseline behavior).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.utils.calendar_boost import _fetch_earnings_dates
from tradingagents.agents.utils.forward_catalyst_filter import (
    CasePricedInScore,
    evaluate_forward_catalyst,
)

pytestmark = pytest.mark.unit


# Spec 007 baseline annotation keys (all 16 fields). Hybrid C adds 4 ONLY when
# enabled. SC-005 asserts the dict-key set is byte-equivalent in default-off mode.
_SPEC_007_KEYS = {
    "model",
    "bull_case_priced_in",
    "bear_case_priced_in",
    "rationale",
    "bull_threshold",
    "bear_threshold",
    "bull_mode",
    "bear_mode",
    "would_fire_bull",
    "would_fire_bear",
    "fired_bull",
    "fired_bear",
    "pre_rating",
    "post_rating",
    "skipped",
    "error",
}
_HYBRID_C_KEYS = {
    "days_to_earnings",
    "calendar_boost",
    "effective_bull_score",
    "effective_bear_score",
}


@pytest.fixture(autouse=True)
def _clear_lru_cache():
    """Clear the calendar_boost LRU cache between tests (R-7)."""
    _fetch_earnings_dates.cache_clear()
    yield
    _fetch_earnings_dates.cache_clear()


def _state(ticker: str = "NVDA", trade_date: str = "2026-05-06") -> dict:
    return {
        "company_of_interest": ticker,
        "trade_date": trade_date,
        "market_report": "m",
        "sentiment_report": "s",
        "news_report": "n",
        "fundamentals_report": "f",
        "investment_plan": "p",
        "investment_debate_state": {"history": "d"},
    }


def _make_llm(bull: float, bear: float, rationale: str = "test"):
    llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = CasePricedInScore(
        bull_case_priced_in=bull, bear_case_priced_in=bear, rationale=rationale
    )
    llm.with_structured_output.return_value = structured
    return llm


def _earnings_df(dates: list[datetime]) -> pd.DataFrame:
    if not dates:
        return pd.DataFrame()
    idx = pd.DatetimeIndex(dates).tz_localize("US/Eastern")
    return pd.DataFrame({"EPS Estimate": [None] * len(dates)}, index=idx)


# ---- SC-005 default-off integrity ----------------------------------------


def test_default_off_state_log_equals_spec_007_baseline():
    """SC-005 + FR-011: when boost disabled (default), annotation dict-keys
    must be byte-equivalent to spec 007 baseline (no Hybrid C keys present).
    """
    llm = _make_llm(bull=0.50, bear=0.30)
    _, ann = evaluate_forward_catalyst(
        "**Rating**: Buy",
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
        # hybrid_c_calendar_boost_enabled defaults to False (FR-007)
    )
    assert set(ann.keys()) == _SPEC_007_KEYS, (
        f"Default-off annotation should not contain Hybrid C keys. "
        f"Extra: {set(ann.keys()) - _SPEC_007_KEYS}"
    )


def test_default_off_explicit_false_state_log_unchanged():
    """SC-005: explicit hybrid_c_calendar_boost_enabled=False → same as default."""
    llm = _make_llm(bull=0.50, bear=0.30)
    _, ann = evaluate_forward_catalyst(
        "**Rating**: Buy",
        _state(),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
        hybrid_c_calendar_boost_enabled=False,
    )
    assert set(ann.keys()) == _SPEC_007_KEYS


# ---- SC-007 state annotation completeness --------------------------------


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_enabled_state_log_gains_four_keys(mock_ticker):
    """SC-007 + FR-012: when boost enabled, annotation gains exactly 4 new keys."""
    mock_ticker.return_value.earnings_dates = _earnings_df([datetime(2026, 5, 13)])  # +7 days
    llm = _make_llm(bull=0.50, bear=0.30)
    _, ann = evaluate_forward_catalyst(
        "**Rating**: Buy",
        _state(ticker="NVDA", trade_date="2026-05-06"),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
        hybrid_c_calendar_boost_enabled=True,
        hybrid_c_calendar_boost_window_days=14,
        hybrid_c_calendar_boost_magnitude=0.5,
    )
    assert set(ann.keys()) == _SPEC_007_KEYS | _HYBRID_C_KEYS
    # Boost values: days=7, boost = 1 - 7/14 = 0.5, effective_bull = 0.5 * (1 + 0.5*0.5) = 0.625
    assert ann["days_to_earnings"] == 7
    assert ann["calendar_boost"] == pytest.approx(0.5)
    assert ann["effective_bull_score"] == pytest.approx(0.625)
    assert ann["effective_bear_score"] == 0.30  # bull-only per FR-004


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_enabled_borderline_score_fires_via_boost(mock_ticker):
    """SC-001 end-to-end: borderline-below-threshold score crosses with boost.

    Setup: bull_case_priced_in=0.50 (below T_bull=0.60); earnings in 7 days.
    Expected: effective_bull = 0.625 > 0.60 → fires; rating downgrades to Hold.
    """
    mock_ticker.return_value.earnings_dates = _earnings_df([datetime(2026, 5, 13)])
    llm = _make_llm(bull=0.50, bear=0.30)
    md, ann = evaluate_forward_catalyst(
        "**Rating**: Buy",
        _state(ticker="NVDA", trade_date="2026-05-06"),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
        hybrid_c_calendar_boost_enabled=True,
    )
    assert ann["fired_bull"] is True
    assert ann["post_rating"] == "Hold"
    assert "Hold" in md
    # Without the boost, bull=0.50 would NOT fire at threshold 0.60
    # With boost: effective=0.625 > 0.60 → fires


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_enabled_far_earnings_no_boost_no_fire(mock_ticker):
    """SC-001 control: same setup but earnings 20 days away → no boost → no fire."""
    mock_ticker.return_value.earnings_dates = _earnings_df([datetime(2026, 5, 26)])  # +20 days
    llm = _make_llm(bull=0.50, bear=0.30)
    md, ann = evaluate_forward_catalyst(
        "**Rating**: Buy",
        _state(ticker="NVDA", trade_date="2026-05-06"),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
        hybrid_c_calendar_boost_enabled=True,
        hybrid_c_calendar_boost_window_days=14,
    )
    assert ann["calendar_boost"] == 0.0
    assert ann["effective_bull_score"] == 0.50
    assert ann["fired_bull"] is False
    assert ann["post_rating"] == "Buy"


# ---- SC-003 yfinance failure path-through --------------------------------


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_enabled_yfinance_failure_falls_through_to_baseline(mock_ticker):
    """SC-003: yfinance.Ticker raises → days=None → boost=0 → effective=base.

    Filter behaves identically to spec 007 baseline (no spurious fire).
    """
    mock_instance = MagicMock()
    type(mock_instance).earnings_dates = property(
        lambda self: (_ for _ in ()).throw(RuntimeError("simulated"))
    )
    mock_ticker.return_value = mock_instance

    llm = _make_llm(bull=0.50, bear=0.30)
    _, ann = evaluate_forward_catalyst(
        "**Rating**: Buy",
        _state(ticker="FAKE", trade_date="2026-05-06"),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
        hybrid_c_calendar_boost_enabled=True,
    )
    assert ann["days_to_earnings"] is None
    assert ann["calendar_boost"] == 0.0
    assert ann["effective_bull_score"] == 0.50
    assert ann["fired_bull"] is False  # baseline behavior — no fire at base=0.50 < T=0.60


@patch("tradingagents.agents.utils.calendar_boost.yf.Ticker")
def test_enabled_etf_empty_calendar_falls_through(mock_ticker):
    """SC-003 / edge case: ETF with no earnings calendar → graceful baseline."""
    mock_ticker.return_value.earnings_dates = _earnings_df([])  # empty DataFrame
    llm = _make_llm(bull=0.55, bear=0.30)
    _, ann = evaluate_forward_catalyst(
        "**Rating**: Overweight",
        _state(ticker="SPY", trade_date="2026-05-06"),
        bull_mode="active",
        bear_mode="shadow",
        bull_threshold=0.60,
        bear_threshold=0.50,
        model="claude-opus-4-7",
        llm=llm,
        hybrid_c_calendar_boost_enabled=True,
    )
    assert ann["days_to_earnings"] is None
    assert ann["calendar_boost"] == 0.0
    assert ann["effective_bull_score"] == 0.55
    assert ann["fired_bull"] is False
