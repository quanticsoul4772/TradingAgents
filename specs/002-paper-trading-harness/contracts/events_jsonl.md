# Contract: Event log JSONL

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)

Append-only event log for a paper-trading portfolio. One file per `portfolio_id` at `~/.tradingagents/paper/<portfolio_id>.events.jsonl`. Captures every state-changing event with sufficient detail to fully reconstruct portfolio state by replay.

---

## File format

- **Path**: `<state-dir>/<portfolio_id>.events.jsonl`
- **Encoding**: UTF-8
- **Format**: JSON Lines — one JSON object per line, no leading/trailing comma, terminated by newline (`\n`)
- **Append-only**: every event-emitting operation appends one line via `f.write(json.dumps(event) + "\n")`
- **No truncation, no rewrite**: the only file operation other than read is `open(path, "a", encoding="utf-8")`

---

## Per-line schema

```json
{
  "timestamp": "2026-05-06T14:32:11.456789",
  "event_type": "entry",
  "portfolio_id": "default",
  "policy_snapshot_hash": "a8b9c0d1e2f3...",
  "payload": { ... }
}
```

Top-level fields (every event):
- **`timestamp`**: ISO 8601 with microsecond precision; UTC (`datetime.now(timezone.utc).isoformat()`)
- **`event_type`**: one of the enum values below
- **`portfolio_id`**: matches the owning portfolio's id (filter convenience; the file path also encodes it)
- **`policy_snapshot_hash`**: hex SHA-256 of the active PolicySnapshot's canonical JSON; cross-references the policy active at event time
- **`payload`**: event-type-specific dict

---

## Event types and payload schemas

### `entry`

Emitted when a new position is opened.

```json
{
  "event_type": "entry",
  "payload": {
    "ticker": "NVDA",
    "qty": 25,
    "entry_date": "2026-05-07",
    "entry_price": "475.18",
    "entry_rating": "Overweight",
    "sector": "Technology",
    "intended_close_date": "2026-06-09",
    "cash_after": "97624.50"
  }
}
```

### `exit`

Emitted when a position is closed.

```json
{
  "event_type": "exit",
  "payload": {
    "ticker": "AAPL",
    "qty": 50,
    "exit_date": "2026-05-05",
    "exit_price": "175.21",
    "exit_reason": "window_elapsed",
    "raw_return": "-0.02958",
    "alpha_return": "-0.04231",
    "actual_holding_days": 21,
    "cash_after": "108485.50"
  }
}
```

### `skip_cap`

Emitted when an entry is skipped due to a cap breach.

```json
{
  "event_type": "skip_cap",
  "payload": {
    "ticker": "AVGO",
    "reason": "per_sector",
    "current_exposure_pct": "48.2",
    "attempted_size_pct": "10.0",
    "cap_pct": "50.0",
    "sector": "Technology"
  }
}
```

`reason` is one of: `per_position`, `per_sector`, `n_max_positions`.

### `skip_cash`

Emitted when an entry is skipped due to insufficient cash.

```json
{
  "event_type": "skip_cash",
  "payload": {
    "ticker": "AVGO",
    "attempted_size": "10000.00",
    "available_cash": "5430.20",
    "cash_buffer_floor": "10000.00"
  }
}
```

### `mark`

Emitted once per `step` after all entries/exits, capturing the day's mark-to-market.

```json
{
  "event_type": "mark",
  "payload": {
    "date": "2026-05-06",
    "equity": "103247.12",
    "benchmark_equity": "100120.00",
    "n_open_positions": 5
  }
}
```

### `data_anomaly`

Emitted when price data is unavailable or malformed.

```json
{
  "event_type": "data_anomaly",
  "payload": {
    "ticker": "DELISTED.OLD",
    "date": "2026-05-06",
    "anomaly_type": "delisted",
    "message": "yfinance returned empty frame for ticker between 2026-05-01 and 2026-05-08",
    "consequence": "position closed at last-known price; exit_reason=data_anomaly"
  }
}
```

`anomaly_type`: `missing_close`, `delisted`, `network_error`.

### `step_skipped_already_processed`

Emitted when `step` is invoked for a date already in the equity_curve (R-5).

```json
{
  "event_type": "step_skipped_already_processed",
  "payload": {
    "requested_date": "2026-05-06"
  }
}
```

This event IS appended to the JSONL even when the state file is not modified — it provides operator-visible audit of every step invocation, including no-ops.

---

## Replay invariant

A consumer that reads the JSONL from the start and applies events in order, against the same starting `Portfolio` (cash=starting_equity, no positions), MUST produce a `Portfolio` byte-identical (after re-serialization to canonical JSON) to the materialized state file at the time the last event was appended.

This invariant is the operational definition of Constitution Principle I (Save Everything) for this feature: the state file is the materialized view; the event log is the source of truth.

A test asserts this round-trip: `tests/test_paper_state.py::test_replay_from_events_matches_state`.

---

## File-level rules

1. **Order matters**: events are appended in the order they occur within a step. Entries before exits is NOT guaranteed (a step may interleave them depending on engine logic); the order in the file IS the order of state mutation.
2. **Crash safety**: if a `step` crashes mid-event-emission, the file may end with a partial line. The reader detects partial lines (incomplete JSON) and surfaces a one-line error with the byte offset; does not auto-truncate.
3. **No size limit in v1**: typical portfolio at the spec's scale produces ~1 MB/year of event log. If file growth becomes a concern, future spec can introduce rotation by year.
4. **Concurrency**: single-writer; multiple readers OK (a `status` invocation can read concurrently with a `step` write because events are appended atomically per line on POSIX). Concurrent `step` invocations against the same `portfolio_id` are not supported (per spec Assumption).

---

## What the JSONL does NOT contain

- The materialized `Portfolio` snapshot — that's in the JSON state file.
- Daily digests — those are emitted to `claudedocs/`.
- Input signal CSV contents — those are operator-provided files referenced by path; not duplicated here.
- LLM call records — the harness has zero LLM exposure (SC-008).
- Personal/sensitive data — only ticker symbols, prices, and dates.
