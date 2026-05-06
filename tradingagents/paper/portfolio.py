"""Paper-trading portfolio dataclasses.

Spec: ``specs/002-paper-trading-harness/data-model.md``.

The ``Portfolio`` is the mutable root state holder; ``Position`` and
``ClosedPosition`` are intentionally mutable for the in-place close transition
in the engine. ``EquityPoint`` is a simple value type. All money-sensitive
fields are ``decimal.Decimal`` to avoid float-rounding drift across
cumulative ops; conversion to/from JSON happens at the persistence boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal

from tradingagents.paper.errors import PortfolioStateError
from tradingagents.paper.policy import PolicySnapshot

ZERO = Decimal("0")


@dataclass
class Position:
    """An open long-only equity position."""

    ticker: str
    qty: int
    entry_date: date
    entry_price: Decimal
    entry_rating: Literal["Buy", "Overweight"]
    intended_close_date: date
    sector: str

    def market_value(self, mark_price: Decimal) -> Decimal:
        return Decimal(self.qty) * mark_price


@dataclass
class ClosedPosition:
    """A position that has been exited; recorded for P&L history."""

    ticker: str
    qty: int
    entry_date: date
    entry_price: Decimal
    entry_rating: Literal["Buy", "Overweight"]
    intended_close_date: date
    sector: str
    exit_date: date
    exit_price: Decimal
    exit_reason: Literal["window_elapsed", "mid_window_signal", "data_anomaly"]
    raw_return: Decimal
    alpha_return: Decimal
    actual_holding_days: int


@dataclass
class EquityPoint:
    """A single mark-to-market snapshot for one trading day."""

    date: date
    equity: Decimal
    benchmark_equity: Decimal


@dataclass
class Portfolio:
    """The materialized state of a paper-trading account."""

    portfolio_id: str
    inception_date: date
    cash: Decimal
    starting_equity: Decimal
    policy_snapshot: PolicySnapshot
    positions: dict[str, Position] = field(default_factory=dict)
    closed: list[ClosedPosition] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)

    def is_held(self, ticker: str) -> bool:
        return ticker in self.positions

    def has_processed_date(self, target: date) -> bool:
        """True iff ``target`` has an equity_curve entry (idempotency check, R-5)."""
        return any(point.date == target for point in self.equity_curve)

    def sector_exposure(self, mark_prices: dict[str, Decimal]) -> dict[str, Decimal]:
        """Sum of `qty * mark_price` per sector across open positions."""
        out: dict[str, Decimal] = {}
        for pos in self.positions.values():
            mark = mark_prices.get(pos.ticker)
            if mark is None:
                continue
            out[pos.sector] = out.get(pos.sector, ZERO) + pos.market_value(mark)
        return out

    def market_value(self, mark_prices: dict[str, Decimal]) -> Decimal:
        """Total mark-to-market value of open positions."""
        return sum(
            (
                pos.market_value(mark_prices[pos.ticker])
                for pos in self.positions.values()
                if pos.ticker in mark_prices
            ),
            start=ZERO,
        )

    def equity(self, mark_prices: dict[str, Decimal]) -> Decimal:
        """cash + market value of open positions."""
        return self.cash + self.market_value(mark_prices)

    def validate(self, *, mark_prices: dict[str, Decimal] | None = None) -> None:
        """Run cross-entity invariants per ``data-model.md``. Raises
        ``PortfolioStateError`` on failure with the failing invariant name."""
        if not self.portfolio_id:
            raise PortfolioStateError(
                "portfolio_id is empty", failing_invariant="portfolio_id_nonempty"
            )
        if self.cash < ZERO:
            raise PortfolioStateError(
                f"cash is negative: {self.cash}", failing_invariant="cash_nonneg"
            )
        if self.starting_equity <= ZERO:
            raise PortfolioStateError(
                f"starting_equity must be > 0: {self.starting_equity}",
                failing_invariant="starting_equity_positive",
            )
        if len({p.ticker for p in self.positions.values()}) != len(self.positions):
            raise PortfolioStateError(
                "duplicate tickers in positions dict",
                failing_invariant="positions_unique_tickers",
            )
        for ticker, pos in self.positions.items():
            if ticker != pos.ticker:
                raise PortfolioStateError(
                    f"positions key {ticker!r} != Position.ticker {pos.ticker!r}",
                    failing_invariant="positions_key_matches_ticker",
                )
            if pos.qty < 1:
                raise PortfolioStateError(
                    f"position {ticker} qty < 1: {pos.qty}",
                    failing_invariant="position_qty_positive",
                )
            if pos.entry_price <= ZERO:
                raise PortfolioStateError(
                    f"position {ticker} entry_price must be > 0: {pos.entry_price}",
                    failing_invariant="position_entry_price_positive",
                )
            if pos.intended_close_date <= pos.entry_date:
                raise PortfolioStateError(
                    f"position {ticker} intended_close_date {pos.intended_close_date} "
                    f"<= entry_date {pos.entry_date}",
                    failing_invariant="position_close_after_entry",
                )
        # equity_curve dates strictly ascending
        prior: date | None = None
        for ep in self.equity_curve:
            if prior is not None and ep.date <= prior:
                raise PortfolioStateError(
                    f"equity_curve dates not strictly ascending: {prior} -> {ep.date}",
                    failing_invariant="equity_curve_ascending",
                )
            prior = ep.date
        # Cash buffer floor (only enforced when mark prices are supplied)
        if mark_prices is not None:
            equity = self.equity(mark_prices)
            buffer_floor = (
                self.starting_equity * self.policy_snapshot.cash_buffer_pct / Decimal("100")
            )
            # Allow small rounding tolerance
            if self.cash < buffer_floor - Decimal("0.01"):
                raise PortfolioStateError(
                    f"cash {self.cash} below cash_buffer floor {buffer_floor} "
                    f"(equity={equity}, buffer_pct={self.policy_snapshot.cash_buffer_pct})",
                    failing_invariant="cash_buffer_floor",
                )
