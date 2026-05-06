# Feature Specification: Paper-Trading Harness

**Feature Branch**: `002-paper-trading-harness`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "Paper-trading harness on top of daily_signals.py — simulation layer that consumes signal CSVs, opens/closes virtual positions per a position policy, marks to market, persists portfolio state across days, and emits daily P&L digests. First signals-consumer; new persistent state convention under ~/.tradingagents/paper/. Principle IV (No Production Claims): simulation only, no broker integration. Principle VI: structurally new state + policy interface, hence speced."

## Why this exists

SC-003 (50-ticker validation, 2026-04-03 single date) confirmed Scenario B: the framework's bullish bucket carries +5.96% mean α at 21d (n=15, 53% hit rate), with the signal structurally tech-concentrated (Tech n=7 +17.80%; Financials n=5 -7.07%). Per the HYPOTHESIS decision tree, this greenlights the product-build path. The next product step is a layer that *uses* the daily_signals output to maintain a simulated portfolio across days — closing the loop between "signal exists" and "signal produces realized P&L when sized and timed by deterministic rules." Without this layer, the framework's empirical α numbers are bucket-statistics on individual decisions, not portfolio-level outcomes; users can't answer "what would my account look like if I'd followed the signals?"

The harness is also the validation gate for any future strategic policy work (sector tilts, conviction-weighted sizing, holding-window adjustments). It runs in two modes: **replay** (deterministic backtest over historical signals — must reproduce SC-003's bullish-bucket numbers within tolerance before live use) and **step** (one-trading-day, idempotent, cron-able for live-forward use).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate harness logic against SC-003 (Priority: P1)

The operator wants to confirm the harness's position-sizing and P&L math is correct before relying on it. They run replay mode over the SC-003 date with the SC-003 watchlist and signals CSV; the harness opens simulated positions on the 15 bullish commits, holds for 21 trading days, closes at close-to-close prices, and reports realized portfolio α vs SPY. The reported number should land within ±100 basis points of SC-003's +5.96% bullish-bucket mean α (allowing for sector cap, position cap, and slippage effects).

**Why this priority**: Without this validation, the harness is a black box producing numbers we can't verify. Reproducing a known result is the gate before using the harness for any forward decision.

**Independent Test**: Run `paper_trade replay --start 2026-04-03 --end 2026-05-04 --signals-csv experiments/2026-05-05-003-signal-at-scale/results.csv --watchlist <sc003-watchlist>` and inspect the realized-α figure in the output digest. Pass if within ±100 bps of +5.96%.

**Acceptance Scenarios**:

1. **Given** the SC-003 signals CSV and watchlist, **When** the operator runs replay over 2026-04-03 → 2026-05-04, **Then** the harness opens ≤ N_max_positions bullish entries at the next-trading-day close, applies the per-position and per-sector caps, and 21 trading days later closes each at the close price, reporting realized portfolio α in a markdown digest.
2. **Given** the same inputs, **When** the digest is rendered, **Then** the per-position realized α figures reconcile with the framework's analyzer output for those same (ticker, date) pairs to within slippage tolerance.
3. **Given** a replay over a date with no bullish commits, **When** the harness runs, **Then** no positions are opened, the digest reports zero trades and the portfolio remains 100% cash, and the run completes without error.

---

### User Story 2 - Run a daily step (cron-able live-forward use) (Priority: P1)

The operator runs `daily_signals.py --emit-csv today.csv` (separately) to generate today's signals, then runs `paper_trade step --signals-csv today.csv` to update the portfolio. The step command is idempotent — running it twice for the same date is a no-op on the second run. The harness opens entries on fresh bullish commits (subject to caps), exits any positions whose 21-day holding window has elapsed (or which received a fresh Sell/UW signal), marks the remaining positions to market against today's close, appends events to the event log, updates the JSON state file, and writes today's digest.

**Why this priority**: This is the actual live-forward use case. Without it, the harness is replay-only and doesn't deliver the "what if I followed the signals" loop the project pivoted toward.

**Independent Test**: With a synthetic 5-day signal CSV (hand-crafted), run `step` for each of the 5 days in sequence. Inspect the JSON state file after each day to verify positions, cash, and equity track correctly. Re-running step for any prior day must produce no change.

**Acceptance Scenarios**:

1. **Given** an empty portfolio with $100,000 cash and a signals CSV containing 3 bullish commits for today, **When** the operator runs `step` for today, **Then** the harness opens 3 positions at next-trading-day close prices (subject to per-position cap), updates cash by the entry cost + slippage, and writes today's digest.
2. **Given** a portfolio with one open position whose entry was 21 trading days ago, **When** the operator runs `step` for today, **Then** the harness exits the position at today's close, records realized α in the closed-positions log, and returns the proceeds to cash (less exit slippage).
3. **Given** a portfolio with one open position and today's signal CSV contains a fresh `Sell` rating for that ticker, **When** the operator runs `step` for today, **Then** the harness exits the position at next-trading-day close (mid-window override), regardless of whether the 21-day window has elapsed.
4. **Given** that `step` was run for date D yesterday, **When** the operator re-runs `step` for date D today, **Then** the harness detects the date is already recorded in state and exits without modifying state or writing a new digest.

---

### User Story 3 - Inspect portfolio state at any time (Priority: P2)

The operator wants to see "what does my simulated portfolio look like right now?" without running a full step. A `paper_trade status` subcommand reads the JSON state file, marks open positions to the most recent available close, and renders a summary digest: equity, cash, MTD/ITD P&L vs SPY, open positions table, recent closes, policy snapshot.

**Why this priority**: Operational ergonomic — the operator will check the portfolio state more often than they update it. Not strictly required for the validation gate (US1) or the daily flow (US2) but high-value for routine use.

**Independent Test**: After running step for a sequence of synthetic days, run `paper_trade status` and verify the digest matches the expected state from manual calculation.

**Acceptance Scenarios**:

1. **Given** a portfolio with 3 open positions and 2 closed positions, **When** the operator runs `status`, **Then** the harness renders a digest showing cash, equity, unrealized P&L per open position, realized P&L per closed position, and aggregate vs-benchmark numbers.
2. **Given** a portfolio whose state file does not exist, **When** the operator runs `status`, **Then** the harness reports an empty-portfolio state without error.

---

### Edge Cases

- What happens when a held ticker is delisted mid-window? The harness detects missing price data, records the position as "closed-stale" with whatever last-known price it has, and surfaces the event in the digest as a data anomaly rather than crashing.
- What happens when a watchlist ticker has no signal in the day's CSV? The harness ignores it (no position change). Watchlist is the universe of *eligible* tickers; signals are the *trigger*.
- What happens when cash is insufficient to honor a fresh bullish commit at the configured per-position size? The harness skips the entry, records the skip event (with the cash-shortfall reason) in the event log, and continues to the next entry candidate.
- What happens when the per-sector cap would be breached by a fresh entry? The harness skips the entry, records the cap-breach skip event, and continues.
- What happens when a position's intended-close trading day is a market holiday? The harness exits at the next available trading day's close.
- What happens on the first run after a long gap (operator missed step calls for several trading days)? The harness does NOT back-fill — it only operates on the date passed in. The operator can manually run replay to back-fill if desired, OR run step once for "today" with the implicit acceptance that any positions whose intended-close was during the gap will close late.
- What happens when the same ticker appears with conflicting ratings on the same day in the input CSV? The harness uses the most recent (later-timestamped) row, or if no timestamp column, the last row in input order.
- What happens when SPY benchmark price is unavailable for a P&L mark? The unrealized α figure is reported as "N/A" for that mark; the position itself still updates correctly (raw P&L doesn't depend on benchmark availability).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness MUST support two operational modes: **replay** (deterministic, processes a date range from a fixed signals CSV) and **step** (single-trading-day, idempotent, designed for cron use).
- **FR-002**: The harness MUST consume signals as a CSV file. The CSV format MUST match the schema produced by `daily_signals.py --emit-csv` (a new flag added under this spec). Required columns: `ticker`, `analysis_date`, `rating`. Optional columns are permitted and ignored.
- **FR-003**: The harness MUST persist portfolio state as a JSON file at a configurable path (default `~/.tradingagents/paper/<portfolio_id>.json`), and MUST persist an append-only event log at `<same-dir>/<portfolio_id>.events.jsonl`. The portfolio_id MUST be configurable via CLI argument, defaulting to `default`.
- **FR-004**: The harness MUST honor the `TRADINGAGENTS_CACHE_DIR` environment variable for the persistence root, matching the convention used by the framework's other state systems (memory log, checkpoint DBs, signal cache).
- **FR-005**: On any fresh bullish commit (`Buy` or `Overweight` rating) for a ticker not currently held, the harness MUST attempt to open a new position at the **next trading day's close price** plus a configurable slippage haircut, subject to all configured caps (per-position, per-sector, cash buffer, max-positions).
- **FR-006**: The harness MUST close any open position when **either** of these conditions is first met: (a) the configured holding window (default 21 trading days) has elapsed since entry, or (b) a fresh `Sell` or `Underweight` rating appears for that ticker in a daily signal CSV. Exit is at the next trading day's close minus slippage.
- **FR-007**: The harness MUST NOT short-sell. `Underweight` and `Sell` ratings only trigger exits of existing long positions; they never open short positions.
- **FR-008**: The harness MUST record every state-changing event (entry, exit, skip-due-to-cap, skip-due-to-cash, mark-to-market) as a single JSON line in the event log, with timestamp, event type, and full payload sufficient to reconstruct state.
- **FR-009**: The harness MUST emit a daily markdown digest including: equity, cash, MTD/ITD P&L (raw $ and % vs SPY benchmark), today's trades (entries + exits with rationale excerpts from rating CSV), open positions table, closed positions summary (rolling 30 days), policy snapshot, and a Constitution Principle IV simulation disclaimer.
- **FR-010**: The harness MUST be idempotent on `step` invocations: running `step` for a date already recorded in state MUST produce no state change, no event log appends, and no new digest output (other than a one-line "already processed" notice on stdout).
- **FR-011**: The harness MUST NOT generate signals itself. It is strictly a signal *consumer*. The signal-generation step (running propagate over a watchlist) remains the responsibility of `daily_signals.py` and incurs LLM cost separately.
- **FR-012**: The harness MUST compute realized P&L (raw return, alpha vs benchmark, actual_holding_days) using the existing consolidated `tradingagents.dataflows.returns.returns_from_frames` primitive. No new forward-α math is permitted in the harness.
- **FR-013**: The position policy (sizing, sector caps, holding-window length, slippage rates, max positions, cash buffer) MUST be expressed as a versioned, immutable policy snapshot embedded in each portfolio's JSON state and in every event-log entry. Changing a policy mid-portfolio MUST require explicit operator intervention (cannot drift silently).
- **FR-014**: The harness MUST include a Constitution Principle IV ("No Production Claims") disclaimer prominently in the daily digest, the operator-facing docs, and any future README content. The disclaimer must state: this is simulation, not financial advice, and no real capital is involved.
- **FR-015**: The harness MUST provide a `status` subcommand that reads current state and renders a digest without modifying state.
- **FR-016**: The harness MUST gracefully handle missing price data (delisted, weekend, network failure): record the data anomaly in the event log, skip the affected operation, and continue with the rest of the day's processing rather than crashing.

### Key Entities *(include if feature involves data)*

- **Portfolio**: The top-level state object. Holds: `portfolio_id`, `inception_date`, current `cash` balance (decimal), `starting_equity`, list of `Position` (open), list of `ClosedPosition` (history), `equity_curve` (date-indexed mark-to-market history vs benchmark), and an immutable `policy_snapshot` recording which sizing/exit/slippage policy produced this portfolio's history.
- **Position** (open): `ticker`, `qty` (whole shares), `entry_date`, `entry_price`, `entry_rating` (Buy or Overweight), `intended_close_date` (entry + holding-window trading days), `sector` (cached from yfinance metadata at entry).
- **ClosedPosition**: All fields of Position plus `exit_date`, `exit_price`, `exit_reason` (`window_elapsed` | `mid_window_signal` | `data_anomaly`), `raw_return` (decimal), `alpha_return` (decimal vs benchmark), `actual_holding_days`.
- **Event**: A single JSON line in the event log. Common fields: `timestamp` (ISO 8601), `event_type` (`entry` | `exit` | `skip_cap` | `skip_cash` | `skip_sector` | `mark` | `data_anomaly` | `step_skipped_already_processed`), `portfolio_id`, `policy_snapshot_hash`, `payload` (event-specific dict).
- **PolicySnapshot**: Immutable record of: `holding_window_trading_days`, `target_per_position_pct`, `n_max_positions`, `cash_buffer_pct`, `per_sector_cap_pct`, `per_position_cap_pct`, `entry_slippage_bps`, `exit_slippage_bps`, `benchmark` (default `SPY`), `policy_version` (semver).
- **SignalCSVRow**: A single row consumed from the input signals CSV. Required columns: `ticker`, `analysis_date` (ISO date), `rating` (one of `Buy` / `Overweight` / `Hold` / `Underweight` / `Sell`). Optional columns ignored.
- **DailyDigest**: A markdown document for one trading day, written to a configurable output path (default `claudedocs/paper-<portfolio_id>-<date>.md`). Contains: header with Principle IV disclaimer, P&L summary, today's trade table, open positions table, recent closes, policy snapshot footer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Validation gate)**: When run in replay mode over the SC-003 date range (2026-04-03 → 2026-05-04) with the SC-003 watchlist and signals CSV, the harness's reported portfolio realized α vs SPY MUST be within **±100 basis points** of the SC-003 bullish-bucket mean α of +5.96%.
- **SC-002 (Idempotency)**: Running `step` twice for the same date MUST produce zero state changes on the second invocation, verified by byte-identical state file before and after.
- **SC-003 (Cap enforcement)**: In any portfolio history with N ≥ 10 entries, **zero** positions exceed the per-position cap; **zero** sector totals exceed the per-sector cap at the moment of entry; cash buffer is honored at all times.
- **SC-004 (P&L reconciliation)**: For every closed position, the harness's reported realized α MUST match the framework's analyzer output (`scripts/analyze_backtest.py`) for the same (ticker, entry_date, exit_date) tuple within **±5 basis points** (slippage tolerance).
- **SC-005 (Disclaimer presence)**: The Constitution Principle IV disclaimer appears in 100% of generated digests and in the operator-facing docs.
- **SC-006 (Live-forward operability)**: An operator can run `paper_trade step` daily for 5 consecutive trading days using a hand-crafted signals CSV without manual intervention beyond providing the CSV path; portfolio state correctly reflects the cumulative effect at the end.
- **SC-007 (Test coverage)**: New code in `tradingagents/paper/` and `scripts/paper_trade.py` reaches at least **90% line coverage** (project standard for new modules). The SC-003 reproduction is encoded as an `integration`-marked pytest case.
- **SC-008 (No LLM cost in harness)**: The harness's `replay`, `step`, and `status` commands MUST complete with zero LLM API calls. Verified by running with all provider API keys unset and observing no failures attributable to missing keys.

## Assumptions

- **Operator profile**: A technical user comfortable with command-line tools, CSV files, and reading markdown reports. The harness is not a consumer product.
- **Watchlist source**: Operator provides a watchlist file (one ticker per line). A default watchlist (`data/watchlists/tech_weighted.txt`, ~25 tickers, ~60% Tech / 15% Healthcare / 10% Financials / 15% other) ships with the harness for the demo path. Operator may override with `--watchlist`.
- **Default starting equity**: $100,000 notional. Configurable via CLI. Affects only the absolute-$ figures in digests; all percentages/α figures are starting-equity-independent.
- **Default position policy** (resolvable after operator review of the open design questions in `plan.md`):
  - Holding window: **21 trading days, fixed**
  - `target_per_position_pct`: **10%**
  - `n_max_positions`: **8**
  - `cash_buffer_pct`: **10%** (always maintained)
  - `per_sector_cap_pct`: **50%** (no sector exceeds half the equity at moment of entry)
  - `per_position_cap_pct`: **15%** (hard ceiling on any single position)
  - `entry_slippage_bps`: **5**
  - `exit_slippage_bps`: **5**
  - `benchmark`: **SPY**
  - Re-entry cooldown: **0 days** (same-day re-entry permitted on closed-then-fresh-bullish)
- **Mid-window Hold rating**: Held positions are NOT closed on a fresh `Hold` for the same ticker. Hold = calibrated abstention (Constitution Principle VII); the position rides out the empirically-validated 21d window. Only `Sell` and `Underweight` trigger mid-window exits.
- **Sector lookup**: Sector metadata is fetched once per ticker via `yfinance.Ticker(t).info["sector"]` at first entry, cached at `~/.tradingagents/paper/sectors.json`. Tickers without sector data default to `"Unknown"` and are treated as their own sector for cap purposes.
- **Trading calendar**: Market holidays are detected via the standard yfinance calendar (no separate holiday source). A position's intended-close-date that falls on a non-trading day rolls forward to the next available trading day.
- **Signal generation cost is operator's responsibility**: This spec does NOT alter `daily_signals.py`'s cost profile. Adding the `--emit-csv` flag is mechanical; it does not change the LLM calls underlying signal generation. Operator's daily LLM cost remains whatever `daily_signals.py` would have charged on its own.
- **No back-fill on missed days**: If the operator does not run `step` on day D, the harness will not retroactively process D on day D+1. Back-fill is an explicit operator-initiated action via replay mode.
- **Persistence backup**: The operator is responsible for backing up `~/.tradingagents/paper/`. The harness does not implement automatic backups in v1.
- **Single portfolio per portfolio_id**: Concurrent step invocations against the same portfolio_id are not supported. The operator is responsible for preventing concurrent runs (e.g., via cron staggering or a wrapper lock).
- **Fractional shares**: Disabled in v1. Position sizing rounds down to whole shares. Affects sub-1% of equity at typical $100k+ notionals.
- **Tax treatment**: None. The harness reports gross realized α; tax-lot accounting is out of scope.
- **The default tech-weighted watchlist is empirically motivated** by SC-003's per-sector breakdown (Tech +17.80%, Financials -7.07%, etc.) and by the per-sector cap (50%) which prevents the harness from going pure-Tech even when the watchlist is heavily weighted that way.
