"""Tests for momentum_filter internals — trailing_momentum_pct and the
fallback-prepend branch of maybe_suppress_bear_rating.

Existing test_momentum_filter.py covers the public API with mocked
trailing_momentum_pct. This file fills the remaining gaps:
- trailing_momentum_pct: yfinance success path, insufficient-history path,
  exception swallowing.
- maybe_suppress_bear_rating: the fallback path where the rating regex
  doesn't match (note prepended instead of appended).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.utils.momentum_filter import (
    maybe_suppress_bear_rating,
    trailing_momentum_pct,
)


# -- trailing_momentum_pct -------------------------------------------------


def _fake_history(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"Close": closes})


@pytest.mark.unit
def test_trailing_momentum_pct_happy_path():
    """Sufficient history → returns the trailing % return."""
    # 31 prices: enough for lookback_days=30 (need 31 = lookback+1 prices)
    frame = _fake_history([100.0 + i * 1.0 for i in range(31)])
    with patch(
        "tradingagents.agents.utils.momentum_filter.yf.Ticker"
    ) as mock_ticker:
        mock_ticker.return_value.history.return_value = frame
        result = trailing_momentum_pct("NVDA", "2026-02-06", lookback_days=30)
    # 130 vs 100 over 30 days → +30%
    assert result == pytest.approx(30.0)


@pytest.mark.unit
def test_trailing_momentum_pct_insufficient_history_returns_none():
    """Frame too short → None, not an error."""
    frame = _fake_history([100.0, 101.0, 102.0])  # only 3 rows for 30-day lookback
    with patch(
        "tradingagents.agents.utils.momentum_filter.yf.Ticker"
    ) as mock_ticker:
        mock_ticker.return_value.history.return_value = frame
        result = trailing_momentum_pct("NVDA", "2026-02-06", lookback_days=30)
    assert result is None


@pytest.mark.unit
def test_trailing_momentum_pct_swallows_yfinance_exception():
    """yfinance raising (network down, delisted) → None, with log warning."""
    with patch(
        "tradingagents.agents.utils.momentum_filter.yf.Ticker",
        side_effect=RuntimeError("yfinance broken"),
    ):
        result = trailing_momentum_pct("BOGUS", "2026-02-06", lookback_days=30)
    assert result is None


@pytest.mark.unit
def test_trailing_momentum_pct_handles_invalid_date_format():
    """Bad date string → exception caught, returns None."""
    result = trailing_momentum_pct("NVDA", "not-a-real-date", lookback_days=30)
    assert result is None


# -- maybe_suppress_bear_rating fallback path ----------------------------


@pytest.mark.unit
def test_suppress_falls_back_to_prepend_when_rating_line_not_found():
    """If the markdown doesn't contain a parseable 'Rating: X' line that
    matches the parsed rating, the suppression note is prepended (rather
    than the rating being substituted in place).

    Trigger: rare case where parse_rating finds a rating word in the body
    but no '**Rating**: X' label line — substitute pattern fails.
    """
    # Markdown contains "Underweight" but not as a labeled rating line
    md_no_label = "We should go Underweight on this one. The bear case is strong."
    with patch(
        "tradingagents.agents.utils.momentum_filter.trailing_momentum_pct",
        return_value=-15.0,
    ):
        out, suppressed = maybe_suppress_bear_rating(
            md_no_label, "NVDA", "2026-02-06", threshold_pct=-5.0
        )
    assert suppressed is True
    # Prepended note pattern: starts with the [A3 momentum filter] note
    assert out.startswith("\n\n---")
    assert "[A3 momentum filter]" in out
    assert "Underweight" in out  # original rating mentioned
    # Original markdown body still present at the end
    assert "We should go Underweight on this one." in out
