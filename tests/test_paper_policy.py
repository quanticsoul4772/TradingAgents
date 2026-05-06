"""Unit tests for tradingagents/paper/policy.py DefaultPolicy logic.

Sizing edges (cap saturation, cash buffer, whole-share rounding); entry filter;
exit decisions including the Principle VII guard (Hold rating mid-window does
NOT trigger exit, only Sell/Underweight do).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from tradingagents.paper.policy import DefaultPolicy, PolicySnapshot
from tradingagents.paper.portfolio import Portfolio, Position


def _portfolio(cash="100000", starting="100000", positions=None) -> Portfolio:
    snap = PolicySnapshot()
    p = Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 1, 1),
        cash=Decimal(cash),
        starting_equity=Decimal(starting),
        policy_snapshot=snap,
    )
    if positions:
        for pos in positions:
            p.positions[pos.ticker] = pos
    return p


def _position(ticker="NVDA", qty=10, sector="Technology", entry_price="100") -> Position:
    return Position(
        ticker=ticker,
        qty=qty,
        entry_date=date(2026, 1, 5),
        entry_price=Decimal(entry_price),
        entry_rating="Overweight",
        intended_close_date=date(2026, 2, 5),
        sector=sector,
    )


@pytest.mark.unit
def test_size_position_accepts_first_entry_at_target_pct():
    p = _portfolio()
    pol = DefaultPolicy(p.policy_snapshot)
    decision = pol.size_position(p, "NVDA", "Technology", Decimal("500"), {})
    assert decision.accept
    # 10% of 100000 = 10000 / 500 = 20 shares
    assert decision.target_qty == 20
    assert decision.target_dollar_size == Decimal("10000")


@pytest.mark.unit
def test_size_position_rejected_when_n_max_positions_reached():
    snap = PolicySnapshot(n_max_positions=2)
    p = Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 1, 1),
        cash=Decimal("80000"),
        starting_equity=Decimal("100000"),
        policy_snapshot=snap,
    )
    p.positions["A"] = _position(ticker="A")
    p.positions["B"] = _position(ticker="B")
    pol = DefaultPolicy(snap)
    decision = pol.size_position(
        p, "C", "Technology", Decimal("100"), {"A": Decimal("100"), "B": Decimal("100")}
    )
    assert not decision.accept
    assert decision.reason == "n_max_positions"


@pytest.mark.unit
def test_size_position_clamps_to_per_position_cap():
    """Per-position cap (15% default) clamps the target_dollar_size."""
    snap = PolicySnapshot(target_per_position_pct=Decimal("25"), per_position_cap_pct=Decimal("15"))
    p = Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 1, 1),
        cash=Decimal("100000"),
        starting_equity=Decimal("100000"),
        policy_snapshot=snap,
    )
    pol = DefaultPolicy(snap)
    decision = pol.size_position(p, "NVDA", "Technology", Decimal("100"), {})
    # 25% target capped at 15% of starting_equity = 15000 → 150 shares
    assert decision.accept
    assert decision.target_dollar_size == Decimal("15000")
    assert decision.target_qty == 150


@pytest.mark.unit
def test_size_position_per_sector_cap_blocks_entry():
    """Sector-cap saturation rejects further entries in that sector."""
    snap = PolicySnapshot(per_sector_cap_pct=Decimal("20"))  # 20% cap
    p = Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 1, 1),
        cash=Decimal("85000"),
        starting_equity=Decimal("100000"),
        policy_snapshot=snap,
    )
    # Already 15k in Tech (15% of 100k); attempting another 10% would breach 20%
    p.positions["MSFT"] = _position(ticker="MSFT", qty=150, entry_price="100")
    marks = {"MSFT": Decimal("100")}  # mark = entry, so exposure = 15000
    pol = DefaultPolicy(snap)
    decision = pol.size_position(p, "NVDA", "Technology", Decimal("100"), marks)
    assert not decision.accept
    assert decision.reason == "per_sector"


@pytest.mark.unit
def test_size_position_cash_buffer_floor_blocks_entry():
    """When cash - buffer < target_dollar, entry is downsized or rejected."""
    snap = PolicySnapshot(cash_buffer_pct=Decimal("90"))  # absurd 90% buffer
    p = Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 1, 1),
        cash=Decimal("91000"),
        starting_equity=Decimal("100000"),
        policy_snapshot=snap,
    )
    # buffer floor = 90000; cash_available = 1000; target_pct (10% of 91000) = 9100
    # → downsized to 1000 / 100 = 10 shares
    pol = DefaultPolicy(snap)
    decision = pol.size_position(p, "NVDA", "Technology", Decimal("100"), {})
    assert decision.accept
    assert decision.target_qty == 10  # 1000 / 100


@pytest.mark.unit
def test_size_position_rounds_to_zero_shares_rejected():
    """Sub-1-share targets are rejected with reason=cash."""
    p = _portfolio(cash="1000")
    pol = DefaultPolicy(p.policy_snapshot)
    decision = pol.size_position(p, "BRK.A", "Financials", Decimal("500000"), {})
    # target_dollar = 100, entry_price = 500000 → 0 shares
    assert not decision.accept
    assert decision.reason == "cash"


@pytest.mark.unit
def test_size_position_uses_floor_rounding_not_round():
    p = _portfolio()
    pol = DefaultPolicy(p.policy_snapshot)
    decision = pol.size_position(p, "X", "Tech", Decimal("499.99"), {})
    # 10000 / 499.99 = 20.000... → 20 shares (floor)
    assert decision.accept
    assert decision.target_qty == 20


# -- Exit decisions ----------------------------------------------------------


@pytest.mark.unit
def test_evaluate_exit_window_elapsed():
    snap = PolicySnapshot()
    pol = DefaultPolicy(snap)
    pos = _position()
    pos.intended_close_date = date(2026, 2, 5)
    decision = pol.evaluate_exit(pos, date(2026, 2, 5), None)
    assert decision.exit
    assert decision.reason == "window_elapsed"


@pytest.mark.unit
def test_evaluate_exit_mid_window_sell_signal():
    snap = PolicySnapshot()
    pol = DefaultPolicy(snap)
    pos = _position()
    pos.intended_close_date = date(2026, 2, 5)
    decision = pol.evaluate_exit(pos, date(2026, 1, 15), "Sell")
    assert decision.exit
    assert decision.reason == "mid_window_signal"


@pytest.mark.unit
def test_evaluate_exit_mid_window_underweight_signal():
    snap = PolicySnapshot()
    pol = DefaultPolicy(snap)
    pos = _position()
    pos.intended_close_date = date(2026, 2, 5)
    decision = pol.evaluate_exit(pos, date(2026, 1, 15), "Underweight")
    assert decision.exit
    assert decision.reason == "mid_window_signal"


@pytest.mark.unit
def test_evaluate_exit_mid_window_hold_does_NOT_close():
    """Principle VII guard: Hold rating mid-window does NOT trigger exit.

    Hold = calibrated abstention applies to fresh entries; existing positions
    ride out the validated 21d window.
    """
    snap = PolicySnapshot()
    pol = DefaultPolicy(snap)
    pos = _position()
    pos.intended_close_date = date(2026, 2, 5)
    decision = pol.evaluate_exit(pos, date(2026, 1, 15), "Hold")
    assert not decision.exit


@pytest.mark.unit
def test_evaluate_exit_no_signal_keeps_position():
    snap = PolicySnapshot()
    pol = DefaultPolicy(snap)
    pos = _position()
    pos.intended_close_date = date(2026, 2, 5)
    decision = pol.evaluate_exit(pos, date(2026, 1, 15), None)
    assert not decision.exit


@pytest.mark.unit
def test_evaluate_exit_mid_window_bear_disabled_via_snapshot():
    snap = PolicySnapshot(mid_window_exit_on_bear_signal=False)
    pol = DefaultPolicy(snap)
    pos = _position()
    pos.intended_close_date = date(2026, 2, 5)
    decision = pol.evaluate_exit(pos, date(2026, 1, 15), "Sell")
    assert not decision.exit


@pytest.mark.unit
def test_evaluate_exit_bullish_signal_on_held_keeps_position():
    """Bullish signal on a held ticker does not trigger early exit."""
    snap = PolicySnapshot()
    pol = DefaultPolicy(snap)
    pos = _position()
    pos.intended_close_date = date(2026, 2, 5)
    decision = pol.evaluate_exit(pos, date(2026, 1, 15), "Buy")
    assert not decision.exit
