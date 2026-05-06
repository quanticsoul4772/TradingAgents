# Phase 1: Data Model — Paper-Trading Harness

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Date**: 2026-05-06

This document defines the harness's data entities, their fields with types + validation rules, and the state transitions between them. All entities are Python dataclasses (frozen where immutable) under `tradingagents/paper/portfolio.py` and `tradingagents/paper/policy.py`. JSON serialization uses `dataclasses.asdict()` + custom encoders for Decimal and date types.

---

## Entity reference

### `Portfolio` (root state)

The materialized state of a paper-trading account at a given instant.

| Field | Type | Validation | Notes |
|---|---|---|---|
| `portfolio_id` | `str` | non-empty, alphanumeric + dashes/underscores; ≤ 64 chars | filename-safe; default `"default"` |
| `inception_date` | `date` | ≤ today; ≥ 2020-01-01 | first `step` invocation date |
| `cash` | `Decimal` | ≥ 0 | quoted in account currency (USD) |
| `starting_equity` | `Decimal` | > 0 | recorded once at inception; never updated |
| `positions` | `dict[str, Position]` | each value valid Position; ticker key = `Position.ticker` | open positions only; closed positions move to `closed` |
| `closed` | `list[ClosedPosition]` | each entry valid ClosedPosition; ordered by `exit_date` ascending | append-only |
| `equity_curve` | `list[EquityPoint]` | unique `date` values; sorted ascending | one entry per processed trading day |
| `policy_snapshot` | `PolicySnapshot` | valid PolicySnapshot | immutable for the portfolio's lifetime; mid-life policy change requires explicit operator action that resets state |

**State invariants** (asserted in `Portfolio.validate()` after every state-changing op):
1. `cash + sum(p.qty * latest_close[p.ticker] for p in positions.values()) == latest_equity`
2. `len({p.ticker for p in positions.values()}) == len(positions)` (no duplicate tickers)
3. `cash >= starting_equity * policy_snapshot.cash_buffer_pct / 100` after any entry
4. `sum(per-sector exposure) <= starting_equity * policy_snapshot.per_sector_cap_pct / 100` for each sector at moment of entry (not continuously enforced — sector exposure can drift up via mark-to-market without violating)
5. `equity_curve[-1].date >= max(p.entry_date for p in positions.values())` if any positions exist

### `Position` (open)

A long-only equity position currently held.

| Field | Type | Validation | Notes |
|---|---|---|---|
| `ticker` | `str` | uppercase, ≤ 10 chars, optionally `.SUFFIX` for exchange-qualified | matches the framework's existing `build_instrument_context()` validation |
| `qty` | `int` | ≥ 1 | whole shares only (R-4) |
| `entry_date` | `date` | ≤ today | the trading day on whose close the position was opened (= signal date + 1 trading day) |
| `entry_price` | `Decimal` | > 0 | close price × (1 + entry_slippage_bps/10000) |
| `entry_rating` | `Literal["Buy", "Overweight"]` | enum-bound | only bullish ratings open positions per FR-005 + FR-007 |
| `intended_close_date` | `date` | > entry_date | entry_date + holding_window_trading_days (R-7) |
| `sector` | `str` | non-empty; defaults to `"Unknown"` | from yfinance Ticker info; cached (R-3) |

### `ClosedPosition`

A position that has been exited; recorded for P&L history.

Inherits all fields from `Position` plus:

| Field | Type | Validation | Notes |
|---|---|---|---|
| `exit_date` | `date` | ≥ entry_date | the trading day on whose close the position was exited |
| `exit_price` | `Decimal` | > 0 | close price × (1 - exit_slippage_bps/10000) |
| `exit_reason` | `ExitReason` (enum) | one of the enum values | see ExitReason below |
| `raw_return` | `Decimal` | finite | (exit_price - entry_price) / entry_price |
| `alpha_return` | `Decimal` | finite | raw_return - benchmark_return over same window |
| `actual_holding_days` | `int` | ≥ 1 | trading days between entry_date and exit_date |

### `ExitReason` (enum)

| Value | When |
|---|---|
| `window_elapsed` | The `intended_close_date` was reached without a mid-window override |
| `mid_window_signal` | A fresh `Sell` or `Underweight` rating for the held ticker was observed before `intended_close_date` |
| `data_anomaly` | Price data unavailable for the close (delisting, etc.); position closed at last-known price |

**Note on Principle VII**: there is no `mid_window_hold` value. Hold ratings on a held ticker are explicitly ignored mid-window — calibrated abstention applies to fresh entries, not to existing positions.

### `EquityPoint`

A single mark-to-market snapshot.

| Field | Type | Validation | Notes |
|---|---|---|---|
| `date` | `date` | unique within `equity_curve` | the trading day this snapshot represents |
| `equity` | `Decimal` | ≥ 0 | cash + sum(qty × close) for all open positions |
| `benchmark_equity` | `Decimal` | ≥ 0 | hypothetical equity if `starting_equity` had been invested in `benchmark` ticker on `inception_date` |

### `PolicySnapshot` (immutable)

A frozen record of the position policy active for a portfolio.

| Field | Type | Validation | Default |
|---|---|---|---|
| `policy_version` | `str` | semver-ish | `"v1-alpha"` |
| `holding_window_trading_days` | `int` | 1 ≤ x ≤ 90 | `21` |
| `target_per_position_pct` | `Decimal` | 0 < x ≤ 50 | `Decimal("10.0")` |
| `n_max_positions` | `int` | 1 ≤ x ≤ 50 | `8` |
| `cash_buffer_pct` | `Decimal` | 0 ≤ x ≤ 50 | `Decimal("10.0")` |
| `per_sector_cap_pct` | `Decimal` | 1 ≤ x ≤ 100 | `Decimal("50.0")` |
| `per_position_cap_pct` | `Decimal` | 0 < x ≤ 100 | `Decimal("15.0")` |
| `entry_slippage_bps` | `Decimal` | 0 ≤ x ≤ 100 | `Decimal("5.0")` |
| `exit_slippage_bps` | `Decimal` | 0 ≤ x ≤ 100 | `Decimal("5.0")` |
| `benchmark` | `str` | uppercase ticker | `"SPY"` |
| `mid_window_exit_on_bear_signal` | `bool` | — | `True` (closes mid-window on Sell/UW per FR-006) |
| `re_entry_cooldown_trading_days` | `int` | ≥ 0 | `0` |

`PolicySnapshot` is `@dataclass(frozen=True)`; mutation raises `dataclasses.FrozenInstanceError`. Hash via SHA-256 of canonical JSON serialization for embedding in event-log entries.

### `Event` (one JSON line per occurrence)

| Field | Type | Validation | Notes |
|---|---|---|---|
| `timestamp` | `str` (ISO 8601) | parseable as `datetime.fromisoformat` | UTC; nanosecond precision not required |
| `event_type` | `EventType` (enum) | one of the values below | see EventType below |
| `portfolio_id` | `str` | matches Portfolio.portfolio_id | for log filter convenience |
| `policy_snapshot_hash` | `str` | hex SHA-256 of PolicySnapshot canonical JSON | for cross-referencing the policy active at event time |
| `payload` | `dict` | event-type-specific schema (see below) | flexible JSON object |

### `EventType` (enum)

| Value | Payload schema |
|---|---|
| `entry` | `{ticker, qty, entry_date, entry_price, entry_rating, sector}` |
| `exit` | `{ticker, qty, exit_date, exit_price, exit_reason, raw_return, alpha_return, actual_holding_days}` |
| `skip_cap` | `{ticker, reason: "per_position" \| "per_sector" \| "n_max_positions", attempted_size, current_exposure}` |
| `skip_cash` | `{ticker, attempted_size, available_cash}` |
| `mark` | `{date, equity, benchmark_equity, n_open_positions}` |
| `data_anomaly` | `{ticker, date, anomaly_type: "missing_close" \| "delisted" \| "network_error", message}` |
| `step_skipped_already_processed` | `{requested_date}` |

### `SignalCSVRow` (input)

What the harness reads from the input CSV. Required + optional columns per R-10.

| Field | Type | Required? | Notes |
|---|---|---|---|
| `ticker` | `str` | Required | uppercase |
| `analysis_date` | `date` | Required | ISO YYYY-MM-DD |
| `rating` | `Literal["Buy", "Overweight", "Hold", "Underweight", "Sell"]` | Required | exact case |
| All other columns | — | Ignored | per R-10 |

### `StepResult` (return value of `engine.step`)

| Field | Type | Notes |
|---|---|---|
| `date` | `date` | the date that was processed |
| `portfolio` | `Portfolio` | post-step portfolio state |
| `events` | `list[Event]` | all events emitted by this step (also persisted to JSONL) |
| `entries` | `list[Position]` | new positions opened today |
| `exits` | `list[ClosedPosition]` | positions closed today |
| `skips` | `list[Event]` | filtered list of skip_cap / skip_cash / data_anomaly events |
| `was_already_processed` | `bool` | True if the step exited early due to idempotency check (R-5) |

### `DailyDigest` (output)

A markdown document. Schema:

```
⚠️ Simulation only — not financial advice. ...

# Paper-Trading Digest — <portfolio_id> — <date>

## Summary
- Equity: $XXX,XXX (XX.XX% vs starting; XX.XX% vs SPY)
- Cash: $XX,XXX (X% of equity)
- Open positions: N
- ITD trades: N entries, N exits

## Today's trades
| Action | Ticker | Qty | Price | Sector | Rationale |
|---|---|---|---|---|---|
...

## Open positions
| Ticker | Sector | Entry | Days held | Entry $ | Current $ | Unrealized $ | Unrealized % | Intended close |
|---|---|---|---|---|---|---|---|---|
...

## Recent closes (last 30 days)
| Ticker | Entry → Exit | Held | Reason | Raw % | α % |
|---|---|---|---|---|---|
...

## Policy snapshot
- v1-alpha: holding_window=21 trading days, n_max_positions=8, target_per_position=10%, ...
```

---

## State transitions

### Portfolio: empty → first step

```
∅ ──[step(D, signals_with_3_bullish)]──▶ Portfolio{
    cash: starting_equity - sum(entry_costs),
    positions: {ticker_1, ticker_2, ticker_3},
    equity_curve: [(D, equity_after_marks)]
}
```

### Position: open → closed

Three possible transitions, in priority order checked at each step:

1. **mid_window_signal**: a fresh `Sell` or `Underweight` for the ticker arrives before `intended_close_date`
   ```
   Position(ticker=T, intended_close_date=D+21) ──[step(D+5, {T: Sell})]──▶
       ClosedPosition(..., exit_reason=mid_window_signal, exit_date=D+5)
   ```

2. **window_elapsed**: today's date >= `intended_close_date`, no override
   ```
   Position(ticker=T, intended_close_date=D+21) ──[step(D+21, signals)]──▶
       ClosedPosition(..., exit_reason=window_elapsed, exit_date=D+21)
   ```

3. **data_anomaly**: yfinance fails to provide a close price for the ticker
   ```
   Position(ticker=T) ──[step(D, signals) where T price unavailable]──▶
       ClosedPosition(..., exit_reason=data_anomaly, exit_price=last_known_close)
   ```

### Idempotency: same-date step

```
Portfolio{equity_curve_dates: {..., D}} ──[step(D, anything)]──▶
    StepResult{was_already_processed=True, ...}  # state unchanged
    +
    Event{event_type=step_skipped_already_processed, payload={requested_date: D}}  # appended to JSONL
```

### Entry skip (cap or cash)

```
Portfolio{positions: 8 of 8 slots full} ──[step(D, {T: Buy})]──▶
    StepResult{skips: [Event{event_type=skip_cap, reason=n_max_positions, ticker=T, ...}]}
```

### Sector cap saturation

```
Portfolio{Tech exposure 48% of starting_equity} ──[step(D, {AAPL: Buy})]──▶
    # AAPL is Tech; 48% + 10% > 50% cap → entry skipped
    StepResult{skips: [Event{event_type=skip_cap, reason=per_sector, ticker=AAPL, current_exposure=48%, attempted_size=10%}]}
```

---

## Validation summary

All entity-level validation lives in `validate()` methods on each dataclass; `Portfolio.validate()` calls into nested validates and adds the cross-entity invariants. Validation runs:
- After loading from JSON (catches corrupted state files)
- After every state-changing operation in `engine.step` (defense against logic bugs)
- In every test that constructs an entity from raw values (caught by `pytest`)

A failed validation raises `tradingagents.paper.errors.PortfolioStateError` with the failing invariant + the offending field value. The CLI catches and renders these as a single-line operator-readable error rather than a stack trace.

---

## Notes on Decimal vs float

All money-sensitive fields (cash, prices, equity, percentages) are `decimal.Decimal` to avoid float-rounding drift across cumulative ops. Conversion to `float` only at the JSON serialization boundary (`json.dumps` doesn't natively handle Decimal — `default=str` then `Decimal` on read). yfinance returns `numpy.float64`; the pricing layer converts to Decimal at the boundary.

`alpha_return` and `raw_return` are stored as Decimal but typically displayed as percent in digests (× 100) for operator readability. Internal math is decimal-precise; presentation is human-formatted.
