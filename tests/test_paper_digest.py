"""Unit tests for tradingagents/paper/digest.py — markdown rendering.

Most important: the verbatim Principle IV disclaimer is asserted by SC-005.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from tradingagents.paper.digest import DISCLAIMER, digest_filename, render_digest
from tradingagents.paper.engine import StepResult
from tradingagents.paper.policy import PolicySnapshot
from tradingagents.paper.portfolio import (
    ClosedPosition,
    EquityPoint,
    Portfolio,
    Position,
)


def _portfolio() -> Portfolio:
    return Portfolio(
        portfolio_id="default",
        inception_date=date(2026, 4, 3),
        cash=Decimal("100000"),
        starting_equity=Decimal("100000"),
        policy_snapshot=PolicySnapshot(),
    )


@pytest.mark.unit
def test_principle_iv_disclaimer_present():
    """SC-005: every digest contains the verbatim Principle IV disclaimer."""
    p = _portfolio()
    md = render_digest(p, date(2026, 4, 3), None, {})
    assert "Simulation only — not financial advice" in md
    assert "Constitution Principle IV" in md
    # Disclaimer is the first line (most prominent placement)
    assert md.startswith(DISCLAIMER)


@pytest.mark.unit
def test_empty_portfolio_renders_no_trades_today():
    p = _portfolio()
    md = render_digest(p, date(2026, 4, 3), None, {})
    assert "_No trades today._" in md
    assert "_No open positions._" in md


@pytest.mark.unit
def test_full_portfolio_renders_all_sections():
    p = _portfolio()
    p.cash = Decimal("85000")
    p.positions["NVDA"] = Position(
        ticker="NVDA",
        qty=20,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("750"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 5),
        sector="Technology",
    )
    p.closed.append(
        ClosedPosition(
            ticker="AAPL",
            qty=50,
            entry_date=date(2026, 3, 1),
            entry_price=Decimal("180"),
            entry_rating="Overweight",
            intended_close_date=date(2026, 4, 1),
            sector="Technology",
            exit_date=date(2026, 4, 1),
            exit_price=Decimal("175"),
            exit_reason="window_elapsed",
            raw_return=Decimal("-0.0278"),
            alpha_return=Decimal("-0.0413"),
            actual_holding_days=21,
        )
    )
    p.equity_curve.extend(
        EquityPoint(
            date=date(2026, 4, day),
            equity=Decimal(str(99000 + day * 100)),
            benchmark_equity=Decimal(str(100000 + day * 50)),
        )
        for day in range(1, 16)
    )
    md = render_digest(p, date(2026, 4, 15), None, {"NVDA": Decimal("780")})
    assert "## Summary" in md
    assert "## Open positions" in md
    assert "NVDA" in md
    assert "## Recent closes" in md
    assert "AAPL" in md
    assert "## Equity curve" in md
    assert "## Policy snapshot" in md


@pytest.mark.unit
def test_step_result_entries_and_exits_render_in_todays_trades():
    p = _portfolio()
    pos = Position(
        ticker="NVDA",
        qty=20,
        entry_date=date(2026, 4, 3),
        entry_price=Decimal("750"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 5),
        sector="Technology",
    )
    cp = ClosedPosition(
        ticker="AAPL",
        qty=50,
        entry_date=date(2026, 3, 1),
        entry_price=Decimal("180"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 4, 1),
        sector="Technology",
        exit_date=date(2026, 4, 3),
        exit_price=Decimal("175"),
        exit_reason="window_elapsed",
        raw_return=Decimal("-0.0278"),
        alpha_return=Decimal("-0.0413"),
        actual_holding_days=21,
    )
    sr = StepResult(date=date(2026, 4, 3), portfolio=p, entries=[pos], exits=[cp])
    md = render_digest(p, date(2026, 4, 3), sr, {})
    assert "OPEN" in md
    assert "NVDA" in md
    assert "CLOSE" in md
    assert "AAPL" in md


@pytest.mark.unit
def test_digest_filename_pattern():
    assert digest_filename("default", date(2026, 5, 6)) == "paper-default-2026-05-06.md"
    assert digest_filename("tech-only", date(2026, 1, 15)) == "paper-tech-only-2026-01-15.md"


@pytest.mark.unit
def test_digest_includes_policy_version():
    p = _portfolio()
    md = render_digest(p, date(2026, 4, 3), None, {})
    assert "v1-alpha" in md
    assert "21 trading days" in md  # holding_window default
