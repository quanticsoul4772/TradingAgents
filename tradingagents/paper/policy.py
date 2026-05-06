"""Paper-trading policy: PolicySnapshot dataclass + DefaultPolicy logic.

Spec: ``specs/002-paper-trading-harness/data-model.md`` (PolicySnapshot table) +
``specs/002-paper-trading-harness/contracts/cli.md`` (entry/exit semantics).

The ``PolicySnapshot`` dataclass is frozen and immutable; each portfolio carries
exactly one snapshot for its lifetime. ``DefaultPolicy`` provides the sizing /
entry-filter / exit-decision logic; the engine calls into it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tradingagents.paper.portfolio import Portfolio, Position

ZERO = Decimal("0")
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class PolicySnapshot:
    """Immutable record of the position policy active for a portfolio."""

    policy_version: str = "v1-alpha"
    holding_window_trading_days: int = 21
    target_per_position_pct: Decimal = Decimal("10.0")
    n_max_positions: int = 8
    cash_buffer_pct: Decimal = Decimal("10.0")
    per_sector_cap_pct: Decimal = Decimal("50.0")
    per_position_cap_pct: Decimal = Decimal("15.0")
    entry_slippage_bps: Decimal = Decimal("5.0")
    exit_slippage_bps: Decimal = Decimal("5.0")
    benchmark: str = "SPY"
    mid_window_exit_on_bear_signal: bool = True
    re_entry_cooldown_trading_days: int = 0


def policy_snapshot_hash(snapshot: PolicySnapshot) -> str:
    """Hex SHA-256 of the canonical JSON serialization. Stable across runs.

    Embedded in every event-log entry (see ``contracts/events_jsonl.md``) so
    operators can later filter events by policy version even if the snapshot
    schema evolves.
    """
    payload = asdict(snapshot)
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# -- DefaultPolicy logic -----------------------------------------------------


@dataclass
class EntryDecision:
    """Result of `DefaultPolicy.evaluate_entry`."""

    accept: bool
    reason: Literal["ok", "n_max_positions", "per_position", "per_sector", "cash"]
    target_qty: int = 0
    target_dollar_size: Decimal = ZERO
    detail: str = ""


@dataclass
class ExitDecision:
    """Result of `DefaultPolicy.evaluate_exit`."""

    exit: bool
    reason: Literal["window_elapsed", "mid_window_signal", ""] = ""


class DefaultPolicy:
    """Default sizing/entry/exit logic per spec defaults.

    Constructor takes a ``PolicySnapshot`` so the same logic works against
    any snapshot — supports the ablation pattern in
    ``quickstart.md#walkthrough-4`` where operators provide a custom snapshot
    via ``--policy <path>``.
    """

    def __init__(self, snapshot: PolicySnapshot):
        self.snapshot = snapshot

    def size_position(
        self,
        portfolio: Portfolio,
        ticker: str,
        sector: str,
        entry_price: Decimal,
        mark_prices: dict[str, Decimal],
    ) -> EntryDecision:
        """Decide whether ``ticker`` qualifies as a new entry and at what size.

        Returns an EntryDecision indicating accept/reject + reason. Whole-share
        rounding (R-4): qty = floor(target_dollar_size / entry_price).
        """
        snap = self.snapshot

        # Check N_max_positions
        if len(portfolio.positions) >= snap.n_max_positions:
            return EntryDecision(
                accept=False,
                reason="n_max_positions",
                detail=f"open positions {len(portfolio.positions)} >= n_max {snap.n_max_positions}",
            )

        # Compute candidate dollar size
        equity = portfolio.equity(mark_prices)
        target_dollar = equity * snap.target_per_position_pct / HUNDRED
        per_position_cap = portfolio.starting_equity * snap.per_position_cap_pct / HUNDRED
        if target_dollar > per_position_cap:
            target_dollar = per_position_cap

        # Per-sector cap check (against starting_equity, evaluated at moment of entry)
        sector_cap = portfolio.starting_equity * snap.per_sector_cap_pct / HUNDRED
        sector_now = portfolio.sector_exposure(mark_prices).get(sector, ZERO)
        if sector_now + target_dollar > sector_cap:
            return EntryDecision(
                accept=False,
                reason="per_sector",
                target_dollar_size=target_dollar,
                detail=(
                    f"sector {sector} exposure {sector_now} + attempted {target_dollar} "
                    f"would exceed cap {sector_cap}"
                ),
            )

        # Cash buffer check
        cash_buffer_floor = portfolio.starting_equity * snap.cash_buffer_pct / HUNDRED
        cash_available = portfolio.cash - cash_buffer_floor
        if cash_available <= ZERO:
            return EntryDecision(
                accept=False,
                reason="cash",
                target_dollar_size=target_dollar,
                detail=f"cash {portfolio.cash} - buffer {cash_buffer_floor} = {cash_available} <= 0",
            )
        if target_dollar > cash_available:
            target_dollar = cash_available

        # Whole-share rounding
        if entry_price <= ZERO:
            return EntryDecision(
                accept=False,
                reason="cash",
                detail=f"entry_price {entry_price} <= 0",
            )
        qty = int((target_dollar / entry_price).to_integral_value(rounding="ROUND_DOWN"))
        if qty < 1:
            return EntryDecision(
                accept=False,
                reason="cash",
                target_dollar_size=target_dollar,
                detail=f"target_dollar {target_dollar} / entry_price {entry_price} rounds to 0 shares",
            )

        actual_dollar = Decimal(qty) * entry_price
        return EntryDecision(
            accept=True,
            reason="ok",
            target_qty=qty,
            target_dollar_size=actual_dollar,
        )

    def evaluate_exit(
        self,
        position: Position,
        today: date,
        todays_signal_for_ticker: str | None,
    ) -> ExitDecision:
        """Decide whether ``position`` should be closed today.

        Per FR-006: exit if (a) ``today >= intended_close_date`` (window_elapsed),
        OR (b) a fresh ``Sell`` or ``Underweight`` rating arrives mid-window
        (mid_window_signal). Mid-window ``Hold`` is explicitly ignored
        (Principle VII guard — Hold is calibrated abstention, not a sell signal).
        """
        snap = self.snapshot
        bear_signals = {"Sell", "Underweight"}
        if (
            snap.mid_window_exit_on_bear_signal
            and todays_signal_for_ticker in bear_signals
            and today < position.intended_close_date
        ):
            return ExitDecision(exit=True, reason="mid_window_signal")
        if today >= position.intended_close_date:
            return ExitDecision(exit=True, reason="window_elapsed")
        return ExitDecision(exit=False)
