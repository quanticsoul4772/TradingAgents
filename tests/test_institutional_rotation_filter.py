"""Unit tests for Spec X-1 C-4 Institutional Rotation Filter.

Covers PR-A tasks T004-T010 + PR-B tasks T016, T018-T022, T024-T025, T027
from specs/091-c4-institutional-rotation/tasks.md.

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


# ---- T016 (US2): shadow mode observes only -------------------------------


def test_apply_filter_shadow_mode_observes_only(_mock_yf_ticker):
    """T016 (SC-006): shadow mode + cohort conditions met → would_fire_bear=True,
    fired_bear=False, post_rating == pre_rating, markdown unchanged.
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
        bear_mode="shadow",
        bull_mode="off",
        outflow_threshold=0.05,
    )

    assert annotation is not None
    assert annotation["would_fire_bear"] is True
    assert annotation["fired_bear"] is False
    assert annotation["pre_rating"] == "Underweight"
    assert annotation["post_rating"] == "Underweight"  # unchanged in shadow
    # Markdown unchanged (no rating mutation, no filter note)
    assert modified == pre_decision
    assert "[C-4 Institutional Rotation filter]" not in modified


# ---- T018-T021 (US3): yfinance failure resilience (4 modes) --------------


def test_fetch_returns_none_on_yfinance_none(_mock_yf_ticker):
    """T018 (SC-003): yfinance returns None → _fetch returns None."""
    mock_ticker = MagicMock()
    mock_ticker.institutional_holders = None
    _mock_yf_ticker.Ticker.return_value = mock_ticker

    assert irf._fetch_institutional_rotation("NVDA") is None


def test_fetch_returns_none_on_empty_dataframe(_mock_yf_ticker):
    """T019 (SC-003): yfinance returns empty DataFrame → _fetch returns None."""
    mock_ticker = MagicMock()
    mock_ticker.institutional_holders = pd.DataFrame()
    _mock_yf_ticker.Ticker.return_value = mock_ticker

    assert irf._fetch_institutional_rotation("NVDA") is None


def test_fetch_returns_none_on_missing_pctchange_column(_mock_yf_ticker):
    """T020 (SC-003): DataFrame missing pctChange column → _fetch returns None."""
    df = pd.DataFrame(
        {
            "Holder": ["H1", "H2"],
            "pctHeld": [0.05, 0.04],
            "Shares": [1000, 2000],
            # No pctChange column
        }
    )
    mock_ticker = MagicMock()
    mock_ticker.institutional_holders = df
    _mock_yf_ticker.Ticker.return_value = mock_ticker

    assert irf._fetch_institutional_rotation("NVDA") is None


def test_fetch_returns_none_on_yfinance_exception(_mock_yf_ticker):
    """T021 (SC-003): yfinance raises an exception → _fetch returns None
    (no exception escapes; graceful degradation per FR-013).
    """
    _mock_yf_ticker.Ticker.side_effect = ConnectionError("simulated yfinance outage")

    assert irf._fetch_institutional_rotation("NVDA") is None


# ---- T022 (US3): None input boundary -------------------------------------


def test_should_suppress_bear_none_input_returns_false():
    """T022 (SC-003 boundary): None net_rotation → no fire."""
    assert irf.should_suppress_bear(None, 0.05) is False


# ---- T024-T025 (US4): mode=off escape hatch ------------------------------


def test_apply_filter_both_modes_off_no_annotation(_mock_yf_ticker):
    """T024 (SC-005, FR-011): both modes off → annotation is None,
    state unchanged, no filter signal.
    """
    pre_decision = (
        "**Final Trading Decision**: Underweight\n\n**Rating**: Underweight\n\nBody of decision..."
    )
    state = {"company_of_interest": "NVDA"}

    modified, annotation = irf.evaluate_institutional_rotation(
        pre_decision,
        state,
        bear_mode="off",
        bull_mode="off",
        outflow_threshold=0.05,
    )

    assert annotation is None
    assert modified == pre_decision


def test_apply_filter_both_modes_off_no_yfinance_call(_mock_yf_ticker):
    """T025 (SC-005): both modes off → no yfinance call (zero overhead)."""
    pre_decision = "**Rating**: Underweight\n\nBody."
    state = {"company_of_interest": "NVDA"}

    irf.evaluate_institutional_rotation(
        pre_decision,
        state,
        bear_mode="off",
        bull_mode="off",
        outflow_threshold=0.05,
    )

    # yfinance.Ticker MUST NOT have been called when both modes are off
    _mock_yf_ticker.Ticker.assert_not_called()


# ---- T027: LRU cache correctness (cross-cutting) -------------------------


def test_lru_cache_correctness(_mock_yf_ticker):
    """T027 (SC-004): same ticker fetched twice → only one yfinance call."""
    df = _make_ih_dataframe([0.01] * 10)
    mock_ticker = MagicMock()
    mock_ticker.institutional_holders = df
    _mock_yf_ticker.Ticker.return_value = mock_ticker

    irf._fetch_institutional_rotation("NVDA")
    irf._fetch_institutional_rotation("NVDA")  # second call should hit cache

    # yfinance.Ticker should have been called exactly once
    assert _mock_yf_ticker.Ticker.call_count == 1
