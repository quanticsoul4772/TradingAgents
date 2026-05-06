"""Unit tests for tradingagents/paper/state.py — JSON round-trip + JSONL append.

Covers: load_portfolio + save_portfolio round-trip preserves all fields and
Decimal precision; atomic-write produces no .tmp residue on success; malformed
JSON raises PortfolioStateError; events JSONL append is atomic per-line and
re-readable.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from tradingagents.paper.errors import PortfolioStateError
from tradingagents.paper.events import Event, EventType
from tradingagents.paper.policy import PolicySnapshot, policy_snapshot_hash
from tradingagents.paper.portfolio import (
    ClosedPosition,
    EquityPoint,
    Portfolio,
    Position,
)
from tradingagents.paper.state import (
    append_event,
    events_path_for,
    load_portfolio,
    save_portfolio,
    state_path_for,
)


def _build_portfolio() -> Portfolio:
    snap = PolicySnapshot()
    p = Portfolio(
        portfolio_id="rt-test",
        inception_date=date(2026, 4, 3),
        cash=Decimal("87543.21"),
        starting_equity=Decimal("100000.00"),
        policy_snapshot=snap,
    )
    p.positions["NVDA"] = Position(
        ticker="NVDA",
        qty=25,
        entry_date=date(2026, 4, 7),
        entry_price=Decimal("475.18"),
        entry_rating="Overweight",
        intended_close_date=date(2026, 5, 7),
        sector="Technology",
    )
    p.closed.append(
        ClosedPosition(
            ticker="AAPL",
            qty=50,
            entry_date=date(2026, 4, 4),
            entry_price=Decimal("180.55"),
            entry_rating="Overweight",
            intended_close_date=date(2026, 5, 5),
            sector="Technology",
            exit_date=date(2026, 5, 5),
            exit_price=Decimal("175.21"),
            exit_reason="window_elapsed",
            raw_return=Decimal("-0.0296"),
            alpha_return=Decimal("-0.0423"),
            actual_holding_days=21,
        )
    )
    p.equity_curve.extend(
        [
            EquityPoint(
                date=date(2026, 4, 3),
                equity=Decimal("100000.00"),
                benchmark_equity=Decimal("100000.00"),
            ),
            EquityPoint(
                date=date(2026, 4, 4),
                equity=Decimal("99875.50"),
                benchmark_equity=Decimal("100120.00"),
            ),
        ]
    )
    return p


@pytest.mark.unit
def test_round_trip_preserves_all_fields(tmp_path):
    original = _build_portfolio()
    path = state_path_for(tmp_path, original.portfolio_id)
    save_portfolio(original, path)
    loaded = load_portfolio(path)

    assert loaded.portfolio_id == original.portfolio_id
    assert loaded.inception_date == original.inception_date
    assert loaded.cash == original.cash
    assert loaded.starting_equity == original.starting_equity
    assert set(loaded.positions) == set(original.positions)
    p = loaded.positions["NVDA"]
    o = original.positions["NVDA"]
    assert (p.qty, p.entry_date, p.entry_price, p.sector) == (
        o.qty,
        o.entry_date,
        o.entry_price,
        o.sector,
    )
    assert len(loaded.closed) == 1
    assert loaded.closed[0].alpha_return == original.closed[0].alpha_return
    assert len(loaded.equity_curve) == 2
    assert loaded.equity_curve[0].date == date(2026, 4, 3)
    assert loaded.policy_snapshot == original.policy_snapshot


@pytest.mark.unit
def test_save_is_atomic_no_tmp_residue(tmp_path):
    p = _build_portfolio()
    path = state_path_for(tmp_path, p.portfolio_id)
    save_portfolio(p, path)
    assert path.exists()
    # No leftover .tmp file
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.unit
def test_load_missing_file_raises():
    with pytest.raises(PortfolioStateError, match="not found"):
        load_portfolio(Path("/nonexistent/path/nope.json"))


@pytest.mark.unit
def test_load_corrupt_json_raises(tmp_path):
    bad = tmp_path / "broken.json"
    bad.write_text("{{not valid json", encoding="utf-8")
    with pytest.raises(PortfolioStateError, match="Corrupt state file"):
        load_portfolio(bad)


@pytest.mark.unit
def test_save_then_load_byte_identity_for_idempotent_save(tmp_path):
    """SC-002 supporting test: re-saving an unchanged portfolio produces
    byte-identical output (after the round-trip)."""
    p = _build_portfolio()
    path = state_path_for(tmp_path, p.portfolio_id)
    save_portfolio(p, path)
    bytes_first = path.read_bytes()
    loaded = load_portfolio(path)
    save_portfolio(loaded, path)
    bytes_second = path.read_bytes()
    assert bytes_first == bytes_second


@pytest.mark.unit
def test_event_log_append_one_line_per_event(tmp_path):
    snap = PolicySnapshot()
    h = policy_snapshot_hash(snap)
    path = events_path_for(tmp_path, "test")
    e1 = Event(EventType.MARK, "test", h, {"date": "2026-04-03", "equity": "100000"})
    e2 = Event(EventType.ENTRY, "test", h, {"ticker": "NVDA", "qty": 25})
    append_event(e1, path)
    append_event(e2, path)

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    parsed1 = json.loads(lines[0])
    parsed2 = json.loads(lines[1])
    assert parsed1["event_type"] == "mark"
    assert parsed2["event_type"] == "entry"
    assert parsed2["payload"]["ticker"] == "NVDA"


@pytest.mark.unit
def test_event_log_handles_decimal_in_payload(tmp_path):
    """Decimals in payload must serialize without crashing."""
    snap = PolicySnapshot()
    h = policy_snapshot_hash(snap)
    path = events_path_for(tmp_path, "dec-test")
    e = Event(EventType.ENTRY, "dec-test", h, {"price": Decimal("475.18")})
    append_event(e, path)
    parsed = json.loads(path.read_text(encoding="utf-8").strip())
    assert parsed["payload"]["price"] == "475.18"


@pytest.mark.unit
def test_state_path_helper_naming(tmp_path):
    assert state_path_for(tmp_path, "foo").name == "foo.json"
    assert events_path_for(tmp_path, "foo").name == "foo.events.jsonl"
