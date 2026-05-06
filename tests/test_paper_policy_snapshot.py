"""Unit tests for tradingagents/paper/policy.py PolicySnapshot dataclass.

DefaultPolicy logic tests live in tests/test_paper_policy.py (Phase 3 / US1).
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from tradingagents.paper.policy import PolicySnapshot, policy_snapshot_hash


@pytest.mark.unit
def test_default_snapshot_matches_spec_defaults():
    snap = PolicySnapshot()
    assert snap.policy_version == "v1-alpha"
    assert snap.holding_window_trading_days == 21
    assert snap.target_per_position_pct == Decimal("10.0")
    assert snap.n_max_positions == 8
    assert snap.cash_buffer_pct == Decimal("10.0")
    assert snap.per_sector_cap_pct == Decimal("50.0")
    assert snap.per_position_cap_pct == Decimal("15.0")
    assert snap.entry_slippage_bps == Decimal("5.0")
    assert snap.exit_slippage_bps == Decimal("5.0")
    assert snap.benchmark == "SPY"
    assert snap.mid_window_exit_on_bear_signal is True
    assert snap.re_entry_cooldown_trading_days == 0


@pytest.mark.unit
def test_snapshot_is_frozen():
    snap = PolicySnapshot()
    with pytest.raises(dataclasses.FrozenInstanceError):
        snap.holding_window_trading_days = 30  # type: ignore[misc]


@pytest.mark.unit
def test_hash_is_deterministic_for_identical_snapshots():
    snap1 = PolicySnapshot()
    snap2 = PolicySnapshot()
    assert policy_snapshot_hash(snap1) == policy_snapshot_hash(snap2)


@pytest.mark.unit
def test_hash_changes_when_any_field_differs():
    snap1 = PolicySnapshot()
    snap2 = PolicySnapshot(holding_window_trading_days=30)
    assert policy_snapshot_hash(snap1) != policy_snapshot_hash(snap2)


@pytest.mark.unit
def test_hash_is_stable_across_decimal_precision():
    snap1 = PolicySnapshot(target_per_position_pct=Decimal("10.0"))
    snap2 = PolicySnapshot(target_per_position_pct=Decimal("10.0"))
    assert policy_snapshot_hash(snap1) == policy_snapshot_hash(snap2)


@pytest.mark.unit
def test_hash_is_64_hex_chars():
    snap = PolicySnapshot()
    h = policy_snapshot_hash(snap)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
