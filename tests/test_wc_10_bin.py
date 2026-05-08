"""Unit tests for WC-10 bin_scalar_to_tier pure function.

Covers tasks T005 from specs/108-wc-10-continuous-scalar-rating/tasks.md.
Tests the 6 cases from contracts/wc_10_module.md test contract.
"""

from __future__ import annotations

import pytest

from tradingagents.wc_10 import DEFAULT_BIN_THRESHOLDS, bin_scalar_to_tier

pytestmark = pytest.mark.unit


# ---- T005 (6 unit tests covering SC-002 + FR-008 validation) -------------


def test_bin_buy_interior():
    """T005 (SC-002 interior): rating=0.7 with default thresholds → Buy."""
    assert bin_scalar_to_tier(0.7) == "Buy"


def test_bin_overweight_boundary():
    """T005 (SC-002 boundary): rating=0.6 → Overweight (≤ claims lower bin)."""
    assert bin_scalar_to_tier(0.6) == "Overweight"


def test_bin_hold_interior():
    """T005 (SC-002 interior): rating=0.0 → Hold (mode-collapse zone)."""
    assert bin_scalar_to_tier(0.0) == "Hold"


def test_bin_sell_boundary():
    """T005 (SC-002 boundary): rating=-0.6 → Sell (≤ claims lower bin)."""
    assert bin_scalar_to_tier(-0.6) == "Sell"


def test_bin_sell_interior():
    """T005 (SC-002 interior): rating=-0.7 → Sell."""
    assert bin_scalar_to_tier(-0.7) == "Sell"


def test_bin_rejects_invalid_thresholds():
    """T005 (FR-008 validation): out-of-order/duplicate/out-of-range thresholds raise ValueError."""
    # Out of order
    with pytest.raises(ValueError, match="strictly monotonic"):
        bin_scalar_to_tier(0.0, thresholds=(0.6, -0.2, 0.2, -0.6))
    # Duplicate
    with pytest.raises(ValueError, match="strictly monotonic"):
        bin_scalar_to_tier(0.0, thresholds=(-0.6, -0.6, 0.2, 0.6))
    # Out of [-1, +1] range
    with pytest.raises(ValueError, match="out of"):
        bin_scalar_to_tier(0.0, thresholds=(-1.5, -0.2, 0.2, 0.6))
    # Rating out of [-1, +1]
    with pytest.raises(ValueError, match="out of"):
        bin_scalar_to_tier(1.5)


# ---- Bonus: extreme boundary + custom thresholds (FR-004) ---------------


def test_bin_extreme_negative():
    """Extreme value: rating=-1.0 → Sell."""
    assert bin_scalar_to_tier(-1.0) == "Sell"


def test_bin_extreme_positive():
    """Extreme value: rating=1.0 → Buy."""
    assert bin_scalar_to_tier(1.0) == "Buy"


def test_bin_custom_thresholds():
    """FR-004: custom thresholds override default."""
    # Wider bins: rating=0.45 with thresholds (-0.7, -0.3, 0.3, 0.7) → Overweight
    assert bin_scalar_to_tier(0.45, thresholds=(-0.7, -0.3, 0.3, 0.7)) == "Overweight"
    assert bin_scalar_to_tier(0.0, thresholds=(-0.7, -0.3, 0.3, 0.7)) == "Hold"


def test_default_thresholds_constant():
    """Sanity check: DEFAULT_BIN_THRESHOLDS matches the spec.md default."""
    assert DEFAULT_BIN_THRESHOLDS == (-0.6, -0.2, 0.2, 0.6)
