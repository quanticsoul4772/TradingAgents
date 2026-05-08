"""Unit tests for Spec X-1 C-4 Institutional Rotation Filter (PR-A scope).

Covers tasks T004-T010 from specs/091-c4-institutional-rotation/tasks.md.

Test isolation: every test mocks yfinance.Ticker via the autouse fixture
(per contracts/institutional_rotation_filter.md test-isolation
requirement). LRU cache is cleared before each test for determinism.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tradingagents.agents.utils import institutional_rotation_filter as irf

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clear_lru_cache():
    """Clear the LRU cache before each test for deterministic behavior."""
    irf._fetch_institutional_rotation.cache_clear()
    yield
    irf._fetch_institutional_rotation.cache_clear()


@pytest.fixture(autouse=True)
def _mock_yf_ticker():
    """Mock yfinance.Ticker to prevent network calls."""
    with patch.object(irf, "yf") as mock_yf:
        yield mock_yf


def _make_ih_dataframe(pct_changes: list[float | None]) -> pd.DataFrame:
    """Build a minimal institutional_holders DataFrame for testing."""
    return pd.DataFrame(
        {
            "Holder": [f"Holder{i}" for i in range(len(pct_changes))],
            "pctHeld": [0.05] * len(pct_changes),
            "Shares": [1000000] * len(pct_changes),
            "Value": [10000000] * len(pct_changes),
            "Date Reported": ["2026-01-31"] * len(pct_changes),
            "pctChange": pct_changes,
        }
    )


# ---- T005: fetch happy path ----------------------------------------------


def test_fetch_happy_path(_mock_yf_ticker):
    """T005: 10-row DataFrame with valid pctChange → sum returned correctly."""
    df = _make_ih_dataframe([0.01, -0.02, 0.005, -0.015, 0.0, 0.03, -0.04, 0.0, -0.005, 0.01])
    mock_ticker = MagicMock()
    mock_ticker.institutional_holders = df
    _mock_yf_ticker.Ticker.return_value = mock_ticker

    result = irf._fetch_institutional_rotation("NVDA")
    expected = sum([0.01, -0.02, 0.005, -0.015, 0.0, 0.03, -0.04, 0.0, -0.005, 0.01])
    assert result == pytest.approx(expected)


# ---- T006: NaN handling --------------------------------------------------


def test_fetch_handles_nan_pctchange(_mock_yf_ticker):
    """T006: NaN values in pctChange are treated as 0 via fillna(0).sum()."""
    df = _make_ih_dataframe([0.01, None, 0.005, None, 0.0, 0.03, None, 0.0, -0.005, 0.01])
    mock_ticker = MagicMock()
    mock_ticker.institutional_holders = df
    _mock_yf_ticker.Ticker.return_value = mock_ticker

    result = irf._fetch_institutional_rotation("NVDA")
    expected = 0.01 + 0.005 + 0.0 + 0.03 + 0.0 - 0.005 + 0.01
    assert result == pytest.approx(expected)


# ---- T007 / T008 / T009: should_suppress_bear semantics ------------------


def test_should_suppress_bear_below_threshold():
    """T007: net_rotation = -0.06 < -0.05 threshold → fire."""
    assert irf.should_suppress_bear(-0.06, 0.05) is True


def test_should_suppress_bear_above_threshold():
    """T008: net_rotation = -0.04 > -0.05 threshold → no fire."""
    assert irf.should_suppress_bear(-0.04, 0.05) is False


def test_should_suppress_bear_boundary_equals():
    """T009 (FR-005, SC-002): strict less-than, equality boundary does NOT fire."""
    assert irf.should_suppress_bear(-0.05, 0.05) is False


# ---- T010: apply_filter active mode fires (full integration) -------------


def test_apply_filter_active_mode_fires(_mock_yf_ticker):
    """T010 (SC-001 / SC-007 / SC-008): active mode + bearish pre-rating +
    outflow → fired_bear=True, post_rating="Hold", markdown mutated.
    """
    df = _make_ih_dataframe([-0.01] * 10)  # net_rotation = -0.10
    mock_ticker = MagicMock()
    mock_ticker.institutional_holders = df
    _mock_yf_ticker.Ticker.return_value = mock_ticker

    pre_decision = (
        "**Final Trading Decision**: Underweight\n\n**Rating**: Underweight\n\nBody of decision..."
    )
    state = {"company_of_interest": "NVDA"}

    modified, annotation = irf.evaluate_institutional_rotation(
        pre_decision,
        state,
        bear_mode="active",
        bull_mode="off",
        outflow_threshold=0.05,
    )

    assert annotation is not None
    assert annotation["net_rotation_pct"] == pytest.approx(-0.10)
    assert annotation["outflow_threshold"] == pytest.approx(0.05)
    assert annotation["bear_mode"] == "active"
    assert annotation["bull_mode"] == "off"
    assert annotation["would_fire_bear"] is True
    assert annotation["fired_bear"] is True
    assert annotation["pre_rating"] == "Underweight"
    assert annotation["post_rating"] == "Hold"
    # Markdown mutation: rating line now contains Hold (and original Underweight is replaced)
    assert "Rating**: Hold" in modified or "Rating: Hold" in modified
    assert "[C-4 Institutional Rotation filter]" in modified
