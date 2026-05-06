"""Unit tests for tradingagents/paper/portfolio.py — entity dataclasses + invariants.

Covers: Portfolio.validate() invariants per data-model.md (cash non-neg,
starting_equity positive, no duplicate tickers, position-key matches ticker,
qty positive, entry_price positive, intended_close after entry, equity_curve
strictly ascending, cash buffer floor when mark_prices supplied).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from tradingagents.paper.errors import PortfolioStateError
from tradingagents.paper.policy import PolicySnapshot
from tradingagents.paper.portfolio import (
    ClosedPosition,
    EquityPoint,
    Portfolio,
    Position,
)


def _snap() -> PolicySnapshot:
    return PolicySnapshot()


def _empty_portfolio() -> Portfolio:
    return Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 1, 1),
        cash=Decimal("100000"),
        starting_equity=Decimal("100000"),
        policy_snapshot=_snap(),
    )


def _position(ticker="NVDA", qty=10, sector="Technology") -> Position:
    return Position(
        ticker=ticker,
        qty=qty,
        entry_date=date(2026, 1, 5),
        entry_price=Decimal("475.00"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 2, 5),
        sector=sector,
    )


@pytest.mark.unit
def test_empty_portfolio_validates():
    p = _empty_portfolio()
    p.validate()  # no raise


@pytest.mark.unit
def test_portfolio_with_one_position_validates():
    p = _empty_portfolio()
    pos = _position()
    p.cash = Decimal("95250")  # cash - 10 * 475 = 95250
    p.positions[pos.ticker] = pos
    p.validate()


@pytest.mark.unit
def test_negative_cash_fails():
    p = _empty_portfolio()
    p.cash = Decimal("-1")
    with pytest.raises(PortfolioStateError, match="cash is negative"):
        p.validate()


@pytest.mark.unit
def test_zero_starting_equity_fails():
    p = _empty_portfolio()
    p.starting_equity = Decimal("0")
    with pytest.raises(PortfolioStateError, match="starting_equity must be > 0"):
        p.validate()


@pytest.mark.unit
def test_positions_key_must_match_ticker():
    p = _empty_portfolio()
    pos = _position(ticker="NVDA")
    p.positions["AAPL"] = pos  # key/ticker mismatch
    with pytest.raises(PortfolioStateError, match="positions key"):
        p.validate()


@pytest.mark.unit
def test_position_zero_qty_fails():
    p = _empty_portfolio()
    pos = _position(qty=0)
    p.positions[pos.ticker] = pos
    with pytest.raises(PortfolioStateError, match="qty < 1"):
        p.validate()


@pytest.mark.unit
def test_position_intended_close_must_be_after_entry():
    p = _empty_portfolio()
    bad = Position(
        ticker="NVDA",
        qty=10,
        entry_date=date(2026, 2, 5),
        entry_price=Decimal("100"),
        entry_rating="Buy",
        intended_close_date=date(2026, 1, 5),  # before entry — invalid
        sector="Technology",
    )
    p.positions[bad.ticker] = bad
    with pytest.raises(PortfolioStateError, match="intended_close_date"):
        p.validate()


@pytest.mark.unit
def test_equity_curve_must_be_strictly_ascending():
    p = _empty_portfolio()
    p.equity_curve = [
        EquityPoint(
            date=date(2026, 1, 5), equity=Decimal("100000"), benchmark_equity=Decimal("100000")
        ),
        EquityPoint(
            date=date(2026, 1, 5), equity=Decimal("100100"), benchmark_equity=Decimal("100050")
        ),
    ]
    with pytest.raises(PortfolioStateError, match="strictly ascending"):
        p.validate()


@pytest.mark.unit
def test_has_processed_date_idempotency_helper():
    p = _empty_portfolio()
    assert not p.has_processed_date(date(2026, 1, 5))
    p.equity_curve.append(
        EquityPoint(
            date=date(2026, 1, 5), equity=Decimal("100000"), benchmark_equity=Decimal("100000")
        )
    )
    assert p.has_processed_date(date(2026, 1, 5))
    assert not p.has_processed_date(date(2026, 1, 6))


@pytest.mark.unit
def test_market_value_and_equity_with_marks():
    p = _empty_portfolio()
    pos = _position(qty=10)
    p.cash = Decimal("95250")  # 100000 - 10*475
    p.positions[pos.ticker] = pos
    marks = {"NVDA": Decimal("500.00")}
    assert p.market_value(marks) == Decimal("5000.00")
    assert p.equity(marks) == Decimal("100250.00")


@pytest.mark.unit
def test_sector_exposure_sums_correctly():
    p = _empty_portfolio()
    p.cash = Decimal("80000")
    p.positions["NVDA"] = _position(ticker="NVDA", qty=10, sector="Technology")
    p.positions["MSFT"] = _position(ticker="MSFT", qty=5, sector="Technology")
    p.positions["JPM"] = _position(ticker="JPM", qty=8, sector="Financials")
    marks = {"NVDA": Decimal("500"), "MSFT": Decimal("400"), "JPM": Decimal("200")}
    exp = p.sector_exposure(marks)
    assert exp == {"Technology": Decimal("7000"), "Financials": Decimal("1600")}


@pytest.mark.unit
def test_cash_buffer_floor_enforced_when_marks_given():
    p = _empty_portfolio()
    p.cash = Decimal("9000")  # below 10% of 100000 buffer
    p.positions["NVDA"] = _position(qty=10)
    marks = {"NVDA": Decimal("9100")}  # equity = 9000 + 91000 = 100000
    with pytest.raises(PortfolioStateError, match="cash_buffer floor"):
        p.validate(mark_prices=marks)


@pytest.mark.unit
def test_closed_position_can_be_appended():
    p = _empty_portfolio()
    cp = ClosedPosition(
        ticker="AAPL",
        qty=20,
        entry_date=date(2026, 1, 5),
        entry_price=Decimal("180"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 2, 5),
        sector="Technology",
        exit_date=date(2026, 2, 5),
        exit_price=Decimal("175"),
        exit_reason="window_elapsed",
        raw_return=Decimal("-0.0278"),
        alpha_return=Decimal("-0.0413"),
        actual_holding_days=21,
    )
    p.closed.append(cp)
    p.validate()


@pytest.mark.unit
def test_is_held_helper():
    p = _empty_portfolio()
    p.positions["NVDA"] = _position(ticker="NVDA")
    assert p.is_held("NVDA")
    assert not p.is_held("AAPL")
