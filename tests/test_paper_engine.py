"""Unit tests for tradingagents/paper/engine.py — PaperTradingEngine.step.

Mocks pricing and sectors so tests are fast and deterministic.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from tradingagents.paper.engine import PaperTradingEngine
from tradingagents.paper.policy import PolicySnapshot
from tradingagents.paper.portfolio import (
    EquityPoint,
    Portfolio,
    Position,
)


def _portfolio(cash="100000", starting="100000") -> Portfolio:
    snap = PolicySnapshot()
    return Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 4, 3),
        cash=Decimal(cash),
        starting_equity=Decimal(starting),
        policy_snapshot=snap,
    )


def _engine(portfolio: Portfolio, tmp_path) -> PaperTradingEngine:
    return PaperTradingEngine(portfolio, tmp_path / "sectors.json")


def _patch_pricing(monkeypatch, *, prices: dict[tuple[str, date], Decimal] | None = None):
    """Patch all engine pricing helpers with deterministic stubs."""

    prices = prices or {}

    def fake_close(ticker, target_date, lookback_days=7):
        return prices.get((ticker, target_date), (target_date, Decimal("100"))) and (
            target_date,
            prices.get((ticker, target_date), Decimal("100")),
        )

    def fake_next_close(ticker, after_date, slippage_bps=Decimal("0"), direction="buy"):
        from datetime import timedelta as _td

        next_d = after_date + _td(days=1)
        price = prices.get((ticker, next_d), Decimal("100"))
        # Apply slippage
        mult = Decimal("1") + (slippage_bps / Decimal("10000")) * (
            Decimal("1") if direction == "buy" else Decimal("-1")
        )
        return next_d, price * mult

    def fake_trading_days_after(ticker, anchor, n):
        from datetime import timedelta as _td

        return anchor + _td(days=n)

    def fake_alpha(ticker, entry_date, holding_days, benchmark="SPY"):
        # Deterministic +1% alpha
        return Decimal("0.05"), Decimal("0.01")

    def fake_sector(ticker, cache_path):
        return "Technology"

    monkeypatch.setattr("tradingagents.paper.engine.close_on_or_before", fake_close)
    monkeypatch.setattr("tradingagents.paper.engine.next_trading_day_close", fake_next_close)
    monkeypatch.setattr("tradingagents.paper.engine.trading_days_after", fake_trading_days_after)
    monkeypatch.setattr("tradingagents.paper.engine.compute_realized_alpha", fake_alpha)
    monkeypatch.setattr("tradingagents.paper.engine.get_sector", fake_sector)


@pytest.mark.unit
def test_step_opens_positions_on_bullish_signals(tmp_path, monkeypatch):
    p = _portfolio()
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 3), {"NVDA": "Overweight", "MSFT": "Buy"})
    assert len(result.entries) == 2
    assert {e.ticker for e in result.entries} == {"NVDA", "MSFT"}
    assert not result.was_already_processed


@pytest.mark.unit
def test_step_ignores_hold_for_new_entry(tmp_path, monkeypatch):
    p = _portfolio()
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 3), {"NVDA": "Hold"})
    assert len(result.entries) == 0


@pytest.mark.unit
def test_step_ignores_bearish_for_new_entry_no_short(tmp_path, monkeypatch):
    """FR-007: Sell/Underweight never opens positions."""
    p = _portfolio()
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 3), {"NVDA": "Sell", "MSFT": "Underweight"})
    assert len(result.entries) == 0


@pytest.mark.unit
def test_step_idempotent_when_date_already_processed(tmp_path, monkeypatch):
    p = _portfolio()
    p.equity_curve.append(
        EquityPoint(
            date=date(2026, 4, 3), equity=Decimal("100000"), benchmark_equity=Decimal("100000")
        )
    )
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    cash_before = p.cash
    n_pos_before = len(p.positions)
    n_curve_before = len(p.equity_curve)

    result = engine.step(date(2026, 4, 3), {"NVDA": "Overweight"})
    assert result.was_already_processed
    assert len(result.entries) == 0
    assert p.cash == cash_before
    assert len(p.positions) == n_pos_before
    assert len(p.equity_curve) == n_curve_before


@pytest.mark.unit
def test_step_exits_position_when_window_elapses(tmp_path, monkeypatch):
    p = _portfolio(cash="90000")
    pos = Position(
        ticker="NVDA",
        qty=10,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("100"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 4),
        sector="Technology",
    )
    p.positions["NVDA"] = pos
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 5, 4), {})
    assert len(result.exits) == 1
    assert result.exits[0].exit_reason == "window_elapsed"
    assert "NVDA" not in p.positions


@pytest.mark.unit
def test_step_exits_position_on_mid_window_sell(tmp_path, monkeypatch):
    p = _portfolio(cash="90000")
    pos = Position(
        ticker="NVDA",
        qty=10,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("100"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 4),
        sector="Technology",
    )
    p.positions["NVDA"] = pos
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 10), {"NVDA": "Sell"})
    assert len(result.exits) == 1
    assert result.exits[0].exit_reason == "mid_window_signal"


@pytest.mark.unit
def test_step_does_NOT_exit_on_mid_window_hold(tmp_path, monkeypatch):
    """Principle VII guard: Hold mid-window keeps the position open."""
    p = _portfolio(cash="90000")
    pos = Position(
        ticker="NVDA",
        qty=10,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("100"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 4),
        sector="Technology",
    )
    p.positions["NVDA"] = pos
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 10), {"NVDA": "Hold"})
    assert len(result.exits) == 0
    assert "NVDA" in p.positions


@pytest.mark.unit
def test_step_does_not_re_open_on_held_ticker(tmp_path, monkeypatch):
    p = _portfolio(cash="90000")
    pos = Position(
        ticker="NVDA",
        qty=10,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("100"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 4),
        sector="Technology",
    )
    p.positions["NVDA"] = pos
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 10), {"NVDA": "Overweight"})
    assert len(result.entries) == 0


@pytest.mark.unit
def test_step_emits_mark_event_with_equity(tmp_path, monkeypatch):
    p = _portfolio()
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 3), {})
    mark_events = [e for e in result.events if e.event_type.value == "mark"]
    assert len(mark_events) == 1
    assert "equity" in mark_events[0].payload


@pytest.mark.unit
def test_step_with_unknown_rating_skipped_silently(tmp_path, monkeypatch):
    """Forward-compat: unknown rating values are filtered, no crash."""
    p = _portfolio()
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    result = engine.step(date(2026, 4, 3), {"NVDA": "FutureTier4"})
    assert len(result.entries) == 0


@pytest.mark.unit
def test_step_records_equity_point(tmp_path, monkeypatch):
    p = _portfolio()
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    engine.step(date(2026, 4, 3), {})
    assert len(p.equity_curve) == 1
    assert p.equity_curve[0].date == date(2026, 4, 3)


@pytest.mark.unit
def test_step_processes_exits_before_entries_for_cash_freeing(tmp_path, monkeypatch):
    """Exits should free cash for entries within the same step."""
    snap = PolicySnapshot(n_max_positions=2)
    p = Portfolio(
        portfolio_id="t",
        inception_date=date(2026, 4, 3),
        cash=Decimal("80000"),
        starting_equity=Decimal("100000"),
        policy_snapshot=snap,
    )
    # 2 positions held; window elapsed for one of them
    p.positions["A"] = Position(
        ticker="A",
        qty=100,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("100"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 4, 5),  # elapsed
        sector="Technology",
    )
    p.positions["B"] = Position(
        ticker="B",
        qty=100,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("100"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 5),  # not yet
        sector="Technology",
    )
    _patch_pricing(monkeypatch)
    engine = _engine(p, tmp_path)
    # Try to open C while at n_max=2; A's exit should free a slot
    result = engine.step(date(2026, 4, 5), {"C": "Buy"})
    assert len(result.exits) == 1
    assert result.exits[0].ticker == "A"
    assert len(result.entries) == 1
    assert result.entries[0].ticker == "C"
