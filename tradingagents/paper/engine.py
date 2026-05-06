"""PaperTradingEngine — orchestrates a single trading day.

Spec: ``contracts/cli.md`` (replay/step semantics) + ``data-model.md``
(state transitions). The engine is signal-agnostic: it consumes a
``signals_dict[ticker] -> rating`` and emits events + a StepResult.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

from tradingagents.paper.events import Event, EventType
from tradingagents.paper.policy import DefaultPolicy, policy_snapshot_hash
from tradingagents.paper.portfolio import (
    ClosedPosition,
    EquityPoint,
    Portfolio,
    Position,
)
from tradingagents.paper.pricing import (
    close_on_or_before,
    compute_realized_alpha,
    next_trading_day_close,
    trading_days_after,
)
from tradingagents.paper.sectors import get_sector

logger = logging.getLogger(__name__)

ZERO = Decimal("0")
RATING_VALUES = {"Buy", "Overweight", "Hold", "Underweight", "Sell"}
BULLISH = {"Buy", "Overweight"}
BEARISH = {"Sell", "Underweight"}


@dataclass
class StepResult:
    """Return value of `PaperTradingEngine.step`."""

    date: date
    portfolio: Portfolio
    events: list[Event] = field(default_factory=list)
    entries: list[Position] = field(default_factory=list)
    exits: list[ClosedPosition] = field(default_factory=list)
    skips: list[Event] = field(default_factory=list)
    was_already_processed: bool = False


class PaperTradingEngine:
    """Stateless orchestrator. State lives in the Portfolio passed in.

    Constructor takes the portfolio + policy + sectors-cache path. The
    pricing layer is module-level (uses LRU cache); injection point is the
    yfinance fetch which can be patched in tests.
    """

    def __init__(self, portfolio: Portfolio, sectors_cache_path: Path):
        self.portfolio = portfolio
        self.policy = DefaultPolicy(portfolio.policy_snapshot)
        self.sectors_cache_path = sectors_cache_path
        self.snap_hash = policy_snapshot_hash(portfolio.policy_snapshot)

    def _emit(
        self,
        result: StepResult,
        event_type: EventType,
        payload: dict,
        is_skip: bool = False,
    ) -> Event:
        ev = Event(event_type, self.portfolio.portfolio_id, self.snap_hash, payload)
        result.events.append(ev)
        if is_skip:
            result.skips.append(ev)
        return ev

    def step(
        self,
        today: date,
        signals: dict[str, str],
    ) -> StepResult:
        """Process one trading day.

        Order of operations:
          1. Idempotency check (R-5) — if today is already in equity_curve,
             emit step_skipped_already_processed and return early.
          2. Mark-to-market all open positions to today's close.
          3. Process exits: window-elapsed + mid-window-bear-signal.
             Free cash returned to buffer.
          4. Process entries: bullish signals on tickers not currently held.
          5. Append today's equity_curve point.
        """
        result = StepResult(date=today, portfolio=self.portfolio)

        # Filter unknown ratings (defensive against future tier additions)
        signals = {t: r for t, r in signals.items() if r in RATING_VALUES}

        # 1. Idempotency
        if self.portfolio.has_processed_date(today):
            self._emit(
                result,
                EventType.STEP_SKIPPED_ALREADY_PROCESSED,
                {"requested_date": today.isoformat()},
            )
            result.was_already_processed = True
            return result

        # 2. Mark-to-market
        mark_prices = self._fetch_marks(today, result)

        # 3. Exits (process before entries so freed cash is available for entries)
        self._process_exits(today, signals, mark_prices, result)

        # Refresh marks for any position that just closed (no-op for survivors)
        # — survivors retain their marks, closed positions removed from .positions

        # 4. Entries
        self._process_entries(today, signals, mark_prices, result)

        # 5. Equity curve point (mark-to-market AFTER all entries/exits)
        # Refresh marks if we just opened new positions on tickers we hadn't
        # marked before
        for ticker in self.portfolio.positions:
            if ticker not in mark_prices:
                mark = close_on_or_before(ticker, today)
                if mark is not None:
                    mark_prices[ticker] = mark[1]

        equity = self.portfolio.equity(mark_prices)
        # Benchmark equity: starting_equity * (1 + benchmark_return_since_inception)
        # Track inception benchmark price for compounding
        bench_equity = self._compute_benchmark_equity(today)
        ep = EquityPoint(date=today, equity=equity, benchmark_equity=bench_equity)
        self.portfolio.equity_curve.append(ep)
        self._emit(
            result,
            EventType.MARK,
            {
                "date": today.isoformat(),
                "equity": str(equity),
                "benchmark_equity": str(bench_equity),
                "n_open_positions": len(self.portfolio.positions),
            },
        )
        return result

    # -- private helpers ----------------------------------------------------

    def _fetch_marks(self, today: date, result: StepResult) -> dict[str, Decimal]:
        """Fetch mark-to-market close prices for all currently-open positions."""
        marks: dict[str, Decimal] = {}
        for ticker in list(self.portfolio.positions):
            mark = close_on_or_before(ticker, today)
            if mark is None:
                self._emit(
                    result,
                    EventType.DATA_ANOMALY,
                    {
                        "ticker": ticker,
                        "date": today.isoformat(),
                        "anomaly_type": "missing_close",
                        "message": f"No close price available on or before {today}",
                        "consequence": "marked at last entry price; mark-to-market degraded",
                    },
                )
                marks[ticker] = self.portfolio.positions[ticker].entry_price
            else:
                marks[ticker] = mark[1]
        return marks

    def _process_exits(
        self,
        today: date,
        signals: dict[str, str],
        mark_prices: dict[str, Decimal],
        result: StepResult,
    ) -> None:
        for ticker in list(self.portfolio.positions):
            pos = self.portfolio.positions[ticker]
            todays_signal = signals.get(ticker)
            decision = self.policy.evaluate_exit(pos, today, todays_signal)
            if not decision.exit:
                continue

            # Compute exit price (with sell slippage)
            exit_quote = next_trading_day_close(
                ticker,
                today,
                slippage_bps=self.portfolio.policy_snapshot.exit_slippage_bps,
                direction="sell",
            )
            if exit_quote is None:
                # Data anomaly — close at last known mark price
                exit_price = mark_prices.get(ticker, pos.entry_price)
                exit_date = today
                exit_reason: Literal["window_elapsed", "mid_window_signal", "data_anomaly"] = (
                    "data_anomaly"
                )
                self._emit(
                    result,
                    EventType.DATA_ANOMALY,
                    {
                        "ticker": ticker,
                        "date": today.isoformat(),
                        "anomaly_type": "missing_close",
                        "message": "No future close available for exit",
                        "consequence": f"closed at last mark {exit_price}; exit_reason=data_anomaly",
                    },
                )
            else:
                exit_date, exit_price = exit_quote
                exit_reason = decision.reason  # type: ignore[assignment]

            # Compute realized alpha
            actual_holding_days = max((exit_date - pos.entry_date).days, 1)
            alpha_pair = compute_realized_alpha(
                pos.ticker,
                pos.entry_date,
                actual_holding_days,
                self.portfolio.policy_snapshot.benchmark,
            )
            if alpha_pair is not None:
                raw_return, alpha_return = alpha_pair
            else:
                # Fallback: raw from entry/exit prices, alpha = raw (no benchmark)
                raw_return = (exit_price - pos.entry_price) / pos.entry_price
                alpha_return = raw_return

            cp = ClosedPosition(
                ticker=pos.ticker,
                qty=pos.qty,
                entry_date=pos.entry_date,
                entry_price=pos.entry_price,
                entry_rating=pos.entry_rating,
                intended_close_date=pos.intended_close_date,
                sector=pos.sector,
                exit_date=exit_date,
                exit_price=exit_price,
                exit_reason=exit_reason,
                raw_return=raw_return,
                alpha_return=alpha_return,
                actual_holding_days=actual_holding_days,
            )
            # Apply cash effect
            proceeds = Decimal(pos.qty) * exit_price
            self.portfolio.cash += proceeds
            del self.portfolio.positions[ticker]
            self.portfolio.closed.append(cp)
            mark_prices.pop(ticker, None)
            result.exits.append(cp)
            self._emit(
                result,
                EventType.EXIT,
                {
                    "ticker": cp.ticker,
                    "qty": cp.qty,
                    "exit_date": cp.exit_date.isoformat(),
                    "exit_price": str(cp.exit_price),
                    "exit_reason": cp.exit_reason,
                    "raw_return": str(cp.raw_return),
                    "alpha_return": str(cp.alpha_return),
                    "actual_holding_days": cp.actual_holding_days,
                    "cash_after": str(self.portfolio.cash),
                },
            )

    def _process_entries(
        self,
        today: date,
        signals: dict[str, str],
        mark_prices: dict[str, Decimal],
        result: StepResult,
    ) -> None:
        # Iterate signals deterministically (alpha-sorted by ticker) so cap-saturation
        # ordering is reproducible across runs
        for ticker in sorted(signals):
            rating = signals[ticker]
            if rating not in BULLISH:
                continue
            if self.portfolio.is_held(ticker):
                continue

            sector = get_sector(ticker, self.sectors_cache_path)

            # Compute entry quote
            entry_quote = next_trading_day_close(
                ticker,
                today,
                slippage_bps=self.portfolio.policy_snapshot.entry_slippage_bps,
                direction="buy",
            )
            if entry_quote is None:
                self._emit(
                    result,
                    EventType.DATA_ANOMALY,
                    {
                        "ticker": ticker,
                        "date": today.isoformat(),
                        "anomaly_type": "missing_close",
                        "message": "No next-trading-day close for entry",
                        "consequence": "entry skipped",
                    },
                    is_skip=True,
                )
                continue
            entry_date, entry_price = entry_quote

            decision = self.policy.size_position(
                self.portfolio, ticker, sector, entry_price, mark_prices
            )
            if not decision.accept:
                event_type = (
                    EventType.SKIP_CASH if decision.reason == "cash" else EventType.SKIP_CAP
                )
                payload = {
                    "ticker": ticker,
                    "reason": decision.reason,
                    "detail": decision.detail,
                    "sector": sector,
                }
                if decision.reason == "per_sector":
                    payload["current_exposure"] = str(
                        self.portfolio.sector_exposure(mark_prices).get(sector, ZERO)
                    )
                self._emit(result, event_type, payload, is_skip=True)
                continue

            # Compute intended close date
            intended_close = trading_days_after(
                ticker, entry_date, self.portfolio.policy_snapshot.holding_window_trading_days
            )
            if intended_close is None:
                intended_close = entry_date  # safety net; validate() will catch

            pos = Position(
                ticker=ticker,
                qty=decision.target_qty,
                entry_date=entry_date,
                entry_price=entry_price,
                entry_rating=rating,  # type: ignore[arg-type]
                intended_close_date=intended_close,
                sector=sector,
            )
            cost = Decimal(pos.qty) * pos.entry_price
            self.portfolio.cash -= cost
            self.portfolio.positions[ticker] = pos
            mark_prices[ticker] = pos.entry_price
            result.entries.append(pos)
            self._emit(
                result,
                EventType.ENTRY,
                {
                    "ticker": pos.ticker,
                    "qty": pos.qty,
                    "entry_date": pos.entry_date.isoformat(),
                    "entry_price": str(pos.entry_price),
                    "entry_rating": pos.entry_rating,
                    "sector": pos.sector,
                    "intended_close_date": pos.intended_close_date.isoformat(),
                    "cash_after": str(self.portfolio.cash),
                },
            )

    def _compute_benchmark_equity(self, today: date) -> Decimal:
        """starting_equity × (today's benchmark close / inception's benchmark close)."""
        benchmark = self.portfolio.policy_snapshot.benchmark
        # First time: cache the inception benchmark close in the equity_curve
        # Use a slightly-loose anchor: latest close on or before inception_date
        inception_quote = close_on_or_before(benchmark, self.portfolio.inception_date)
        today_quote = close_on_or_before(benchmark, today)
        if inception_quote is None or today_quote is None or inception_quote[1] == ZERO:
            return self.portfolio.starting_equity
        ratio = today_quote[1] / inception_quote[1]
        return self.portfolio.starting_equity * ratio
