"""Unit tests for Spec 012 Class 4 Macro-Environment Filter.

Covers tasks T010 from specs/012-class-4-macro-filter/tasks.md.
≥10 unit tests covering helper module + threshold edge cases + LRU cache
+ yfinance failure modes per SC-001 / SC-007 / SC-009 / SC-011.

Pattern follows tests/test_institutional_rotation_filter.py
(Spec X-1 PR #91 precedent).
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.agents.utils.macro_environment_filter import (
    _parse_pre_rating,
    _vix_snapshot,
    evaluate_macro_environment,
    should_suppress_bear,
)

pytestmark = pytest.mark.unit


# ---- _vix_snapshot helper -----------------------------------------------


@pytest.fixture(autouse=True)
def _clear_vix_cache():
    """Clear LRU cache between tests to avoid cross-test pollution."""
    _vix_snapshot.cache_clear()
    yield
    _vix_snapshot.cache_clear()


def _mock_vix_history(close_value: float, has_index: bool = True):
    """Build a yfinance-like DataFrame with one Close row."""
    if not has_index:
        return pd.DataFrame()
    idx = pd.DatetimeIndex([pd.Timestamp("2026-04-30")])
    return pd.DataFrame({"Close": [close_value]}, index=idx)


def test_vix_snapshot_returns_close_value():
    """T010: _vix_snapshot returns the latest Close value on or before trade_date."""
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.history.return_value = _mock_vix_history(15.42)
        result = _vix_snapshot("2026-04-30")
    assert result == pytest.approx(15.42)


def test_vix_snapshot_lru_caches_per_date():
    """T010: same trade_date → 1 yfinance call (LRU cache per FR-006)."""
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.history.return_value = _mock_vix_history(20.0)
        _vix_snapshot("2026-04-30")
        _vix_snapshot("2026-04-30")
        _vix_snapshot("2026-04-30")
    # yfinance.Ticker called once; .history called once
    assert mock_ticker.return_value.history.call_count == 1


def test_vix_snapshot_graceful_failure_on_exception():
    """T010 / SC-007: yfinance raises → returns None (no propagation)."""
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.history.side_effect = RuntimeError("network down")
        result = _vix_snapshot("2026-04-30")
    assert result is None


def test_vix_snapshot_graceful_failure_on_empty():
    """T010 / SC-007: yfinance returns empty DataFrame → returns None."""
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.history.return_value = pd.DataFrame()
        result = _vix_snapshot("2026-04-30")
    assert result is None


# ---- should_suppress_bear pure threshold logic --------------------------


def test_should_suppress_bear_below_threshold():
    """T010 / SC-006: VIX < threshold → True (fire)."""
    assert should_suppress_bear(15.0, 18.0) is True


def test_should_suppress_bear_at_threshold_strict_less_than():
    """T010 / SC-006: VIX == threshold → False (strict less-than per FR-002)."""
    assert should_suppress_bear(18.0, 18.0) is False


def test_should_suppress_bear_above_threshold():
    """T010: VIX > threshold → False (no fire)."""
    assert should_suppress_bear(20.5, 18.0) is False


def test_should_suppress_bear_none_input():
    """T010 / SC-007: vix is None → False (no fire even if would technically be below)."""
    assert should_suppress_bear(None, 18.0) is False


# ---- _parse_pre_rating ----------------------------------------------------


def test_parse_pre_rating_extracts_underweight():
    """T010: parses Underweight from PM markdown."""
    md = "**Rating**: Underweight\n\nSome thesis here..."
    assert _parse_pre_rating(md) == "Underweight"


def test_parse_pre_rating_defaults_hold_when_unparseable():
    """T010: empty / missing rating → defaults to Hold."""
    assert _parse_pre_rating("") == "Hold"
    assert _parse_pre_rating("no rating header here") == "Hold"


# ---- evaluate_macro_environment public API -----------------------------


def test_evaluate_off_mode_returns_none_annotation():
    """T010 / SC-002: bear_mode='off' → no annotation, no fetch."""
    md = "**Rating**: Underweight\n"
    state = {"trade_date": "2026-04-30"}
    with patch("tradingagents.agents.utils.macro_environment_filter._vix_snapshot") as mock_fetch:
        result_md, annotation = evaluate_macro_environment(
            md, state, bear_mode="off", vix_threshold=18.0
        )
    assert annotation is None
    assert result_md == md
    # Critical: no yfinance fetch when off
    mock_fetch.assert_not_called()


def test_evaluate_shadow_mode_no_modification():
    """T010 / SC-005: shadow + would_fire=True → annotation present, post_rating == pre_rating."""
    md = "**Rating**: Underweight\n"
    state = {"trade_date": "2026-04-30"}
    with patch(
        "tradingagents.agents.utils.macro_environment_filter._vix_snapshot",
        return_value=15.0,  # below 18 threshold → would_fire
    ):
        result_md, annotation = evaluate_macro_environment(
            md, state, bear_mode="shadow", vix_threshold=18.0
        )
    assert annotation is not None
    assert annotation["would_fire_bear"] is True
    assert annotation["fired_bear"] is False  # shadow does NOT fire
    assert annotation["pre_rating"] == "Underweight"
    assert annotation["post_rating"] == "Underweight"  # unchanged
    # Markdown unchanged
    assert result_md == md


def test_evaluate_active_mode_suppresses_to_hold():
    """T010 / SC-006: active + would_fire=True + Underweight pre → post=Hold + markdown rewritten."""
    md = "**Rating**: Underweight\n\n## Investment thesis\n"
    state = {"trade_date": "2026-04-30"}
    with patch(
        "tradingagents.agents.utils.macro_environment_filter._vix_snapshot",
        return_value=15.0,
    ):
        result_md, annotation = evaluate_macro_environment(
            md, state, bear_mode="active", vix_threshold=18.0
        )
    assert annotation["would_fire_bear"] is True
    assert annotation["fired_bear"] is True
    assert annotation["pre_rating"] == "Underweight"
    assert annotation["post_rating"] == "Hold"
    assert "**Rating**: Hold" in result_md
    assert "[Class 4 Macro-Environment filter]" in result_md


def test_evaluate_annotation_has_7_fields():
    """T010 / SC-004: annotation dict has exactly the 7 documented fields."""
    md = "**Rating**: Hold\n"
    state = {"trade_date": "2026-04-30"}
    with patch(
        "tradingagents.agents.utils.macro_environment_filter._vix_snapshot",
        return_value=20.0,
    ):
        _, annotation = evaluate_macro_environment(
            md, state, bear_mode="shadow", vix_threshold=18.0
        )
    expected_keys = {
        "vix_snapshot",
        "vix_threshold",
        "bear_mode",
        "would_fire_bear",
        "fired_bear",
        "pre_rating",
        "post_rating",
    }
    assert set(annotation.keys()) == expected_keys
