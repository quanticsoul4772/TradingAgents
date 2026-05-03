"""Unit tests for the A3 mean-reversion UW/Sell suppression filter."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tradingagents.agents.utils.momentum_filter import maybe_suppress_bear_rating


SAMPLE_UW_MARKDOWN = """**Rating**: Underweight

**Executive Summary**: Reduce position to 60% weight given memory chip cost
pressure and stretched valuation. Hard stop at $250.

**Investment Thesis**: Bull case overstated relative to forward margin risk."""

SAMPLE_BUY_MARKDOWN = """**Rating**: Buy

**Executive Summary**: Initiate full position on earnings strength."""


@pytest.mark.unit
def test_non_bear_rating_passes_through_unchanged():
    """Buy / Overweight / Hold ratings are never touched by the filter."""
    out, suppressed = maybe_suppress_bear_rating(
        SAMPLE_BUY_MARKDOWN, "AAPL", "2026-02-06", threshold_pct=-5.0
    )
    assert out == SAMPLE_BUY_MARKDOWN
    assert suppressed is False


@pytest.mark.unit
def test_bear_rating_with_neutral_momentum_unchanged():
    """UW commit on a flat ticker (momentum above threshold) passes through."""
    with patch(
        "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
        return_value=2.0,  # +2% — above -5% threshold
    ):
        out, suppressed = maybe_suppress_bear_rating(
            SAMPLE_UW_MARKDOWN, "AAPL", "2026-02-06", threshold_pct=-5.0
        )
    assert out == SAMPLE_UW_MARKDOWN
    assert suppressed is False


@pytest.mark.unit
def test_bear_rating_in_drawdown_suppressed_to_hold():
    """UW commit on a deeply-down ticker (-10%, below -5% threshold) is overridden."""
    with patch(
        "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
        return_value=-10.0,
    ):
        out, suppressed = maybe_suppress_bear_rating(
            SAMPLE_UW_MARKDOWN, "AAPL", "2026-02-06", threshold_pct=-5.0
        )
    assert suppressed is True
    assert "**Rating**: Hold" in out
    assert "Underweight" in out  # Original rating mentioned in the note
    assert "[A3 momentum filter]" in out
    assert "-10.00%" in out  # Momentum value in the note


@pytest.mark.unit
def test_missing_momentum_data_does_not_suppress():
    """If yfinance returns None, leave the decision intact rather than fabricate."""
    with patch(
        "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
        return_value=None,
    ):
        out, suppressed = maybe_suppress_bear_rating(
            SAMPLE_UW_MARKDOWN, "AAPL", "2026-02-06", threshold_pct=-5.0
        )
    assert out == SAMPLE_UW_MARKDOWN
    assert suppressed is False


@pytest.mark.unit
def test_sell_rating_also_suppressed():
    """Sell (the most extreme bear rating) is suppressed by the same rule."""
    sell_md = SAMPLE_UW_MARKDOWN.replace("Underweight", "Sell")
    with patch(
        "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
        return_value=-12.0,
    ):
        out, suppressed = maybe_suppress_bear_rating(
            sell_md, "AAPL", "2026-02-06", threshold_pct=-5.0
        )
    assert suppressed is True
    assert "**Rating**: Hold" in out
    assert "Sell" in out  # Original rating preserved in note


@pytest.mark.unit
def test_threshold_at_boundary_suppresses_when_strictly_below():
    """Momentum exactly at threshold should NOT suppress (strict < comparison)."""
    with patch(
        "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
        return_value=-5.0,  # exactly at threshold
    ):
        out, suppressed = maybe_suppress_bear_rating(
            SAMPLE_UW_MARKDOWN, "AAPL", "2026-02-06", threshold_pct=-5.0
        )
    assert suppressed is False
    assert out == SAMPLE_UW_MARKDOWN
