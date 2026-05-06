"""Portfolio state persistence — JSON load/save + JSONL event-log append.

Spec: ``contracts/state_json.md`` + ``contracts/events_jsonl.md``. Atomic writes
via temp-file-rename pattern. Decimals serialize as JSON strings to preserve
precision.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from tradingagents.paper.errors import PortfolioStateError
from tradingagents.paper.events import Event
from tradingagents.paper.policy import PolicySnapshot
from tradingagents.paper.portfolio import (
    ClosedPosition,
    EquityPoint,
    Portfolio,
    Position,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


def _decimal_to_str(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _portfolio_to_dict(portfolio: Portfolio) -> dict[str, Any]:
    return {
        "portfolio_id": portfolio.portfolio_id,
        "schema_version": SCHEMA_VERSION,
        "inception_date": portfolio.inception_date.isoformat(),
        "starting_equity": str(portfolio.starting_equity),
        "cash": str(portfolio.cash),
        "positions": {
            ticker: {
                **{
                    k: (
                        str(v)
                        if isinstance(v, Decimal)
                        else v.isoformat()
                        if isinstance(v, date)
                        else v
                    )
                    for k, v in asdict(pos).items()
                }
            }
            for ticker, pos in portfolio.positions.items()
        },
        "closed": [
            {
                k: (
                    str(v)
                    if isinstance(v, Decimal)
                    else v.isoformat()
                    if isinstance(v, date)
                    else v
                )
                for k, v in asdict(cp).items()
            }
            for cp in portfolio.closed
        ],
        "equity_curve": [
            {
                "date": ep.date.isoformat(),
                "equity": str(ep.equity),
                "benchmark_equity": str(ep.benchmark_equity),
            }
            for ep in portfolio.equity_curve
        ],
        "policy_snapshot": {
            k: (str(v) if isinstance(v, Decimal) else v)
            for k, v in asdict(portfolio.policy_snapshot).items()
        },
    }


def _portfolio_from_dict(data: dict[str, Any], path: Path) -> Portfolio:
    try:
        snap_raw = data["policy_snapshot"]
        # Convert Decimal-typed fields back from str
        decimal_fields = {
            "target_per_position_pct",
            "cash_buffer_pct",
            "per_sector_cap_pct",
            "per_position_cap_pct",
            "entry_slippage_bps",
            "exit_slippage_bps",
        }
        snap_kwargs = {k: (Decimal(v) if k in decimal_fields else v) for k, v in snap_raw.items()}
        snapshot = PolicySnapshot(**snap_kwargs)

        positions: dict[str, Position] = {}
        for ticker, p in data.get("positions", {}).items():
            positions[ticker] = Position(
                ticker=p["ticker"],
                qty=int(p["qty"]),
                entry_date=date.fromisoformat(p["entry_date"]),
                entry_price=Decimal(p["entry_price"]),
                entry_rating=p["entry_rating"],
                intended_close_date=date.fromisoformat(p["intended_close_date"]),
                sector=p["sector"],
            )

        closed: list[ClosedPosition] = []
        for c in data.get("closed", []):
            closed.append(
                ClosedPosition(
                    ticker=c["ticker"],
                    qty=int(c["qty"]),
                    entry_date=date.fromisoformat(c["entry_date"]),
                    entry_price=Decimal(c["entry_price"]),
                    entry_rating=c["entry_rating"],
                    intended_close_date=date.fromisoformat(c["intended_close_date"]),
                    sector=c["sector"],
                    exit_date=date.fromisoformat(c["exit_date"]),
                    exit_price=Decimal(c["exit_price"]),
                    exit_reason=c["exit_reason"],
                    raw_return=Decimal(c["raw_return"]),
                    alpha_return=Decimal(c["alpha_return"]),
                    actual_holding_days=int(c["actual_holding_days"]),
                )
            )

        equity_curve: list[EquityPoint] = [
            EquityPoint(
                date=date.fromisoformat(ep["date"]),
                equity=Decimal(ep["equity"]),
                benchmark_equity=Decimal(ep["benchmark_equity"]),
            )
            for ep in data.get("equity_curve", [])
        ]

        portfolio = Portfolio(
            portfolio_id=data["portfolio_id"],
            inception_date=date.fromisoformat(data["inception_date"]),
            cash=Decimal(data["cash"]),
            starting_equity=Decimal(data["starting_equity"]),
            policy_snapshot=snapshot,
            positions=positions,
            closed=closed,
            equity_curve=equity_curve,
        )
    except (KeyError, ValueError, TypeError) as e:
        raise PortfolioStateError(
            f"Failed to parse portfolio JSON: {e}",
            path=str(path),
            failing_invariant="json_schema",
        ) from e

    portfolio.validate()
    return portfolio


def load_portfolio(path: Path) -> Portfolio:
    """Load and validate a portfolio from a JSON state file.

    Raises ``PortfolioStateError`` on parse failure or validation failure.
    """
    if not path.exists():
        raise PortfolioStateError(
            f"State file not found at {path}",
            path=str(path),
            failing_invariant="file_exists",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PortfolioStateError(
            f"Corrupt state file: {e}",
            path=str(path),
            failing_invariant="json_parse",
        ) from e
    return _portfolio_from_dict(data, path)


def save_portfolio(portfolio: Portfolio, path: Path) -> None:
    """Atomic write of portfolio state to JSON. Temp file + rename pattern.

    Per ``contracts/state_json.md`` — atomic on POSIX, near-atomic on Windows.
    """
    portfolio.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = _portfolio_to_dict(portfolio)
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    tmp.replace(path)


def append_event(event: Event, path: Path) -> None:
    """Append a single event as one JSON line. Single-writer; readers can be
    concurrent (POSIX append is atomic per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event.to_dict(), default=_decimal_to_str)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def state_path_for(state_dir: Path, portfolio_id: str) -> Path:
    """Path of the JSON state file for ``portfolio_id``."""
    return state_dir / f"{portfolio_id}.json"


def events_path_for(state_dir: Path, portfolio_id: str) -> Path:
    """Path of the JSONL event log for ``portfolio_id``."""
    return state_dir / f"{portfolio_id}.events.jsonl"
