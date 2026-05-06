# Phase 0: Research — Paper-Trading Harness

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

This document resolves the technical-context decisions surfaced during planning. All NEEDS CLARIFICATION items from `plan.md` are resolved here. Each entry follows the standard format: Decision / Rationale / Alternatives Considered.

---

## R-1: Price-data caching strategy

**Decision**: Per-replay/per-step in-process LRU cache keyed by `(ticker, start_date, end_date)`. The harness fetches each ticker's full history span ONCE per command invocation and slices it in memory for both close-price marking and `returns_from_frames` calls. No persistent cross-invocation cache — the `step` command is short-lived and `replay` runs to completion in one process.

**Rationale**:
- yfinance fetches dominate command latency; in-process LRU is the cheapest mitigation.
- Persistent caching introduces invalidation complexity (today's close vs end-of-day vs corrected after-hours) — the existing `tradingagents.dataflows.price_cache.PriceCache` already handles this for the analysis layer; the harness shouldn't compete.
- For `step`, the daily run touches ≤25 tickers (watchlist) + ≤8 held positions + SPY → ≤34 tickers, ≤10 sec total. Acceptable at the operator's daily cadence.
- For `replay`, one fetch per ticker spanning the full date range → linear in ticker count, sublinear in date count.

**Alternatives considered**:
- **Reuse `PriceCache`** — couples the harness to an analysis-layer abstraction designed for batch backtest with multiple `holding_days_horizon` lookups. Overkill; the harness needs single-frame access, not the cache's multi-horizon-α precomputation.
- **Persistent SQLite cache** — invalidation pain (yfinance close prices get adjusted retroactively for splits/dividends; cache would lie). The framework's `checkpointer.py` uses SQLite for graph state, not price data, for this reason.
- **No cache** — re-fetching SPY for every position mark in a 30-day replay multiplies network hits 30× per ticker. LRU prevents this trivially.

---

## R-2: Persistence format (JSON vs alternatives)

**Decision**: Plain JSON for the materialized portfolio state file; JSONL (one JSON object per line, append-only) for the event log. Both human-readable, both `pathlib.Path.write_text(encoding='utf-8')`-friendly, both diff-able when committed for inspection.

**Rationale**:
- Matches the project's existing persistence preferences (`memory.py` uses markdown; `signals/cache.py` uses JSON; `experiments/*/PARAMS.json` is JSON). No SQLite, no pickle, no protobuf in the codebase outside the LangGraph checkpointer.
- JSON state file is small (<100 KB/year per the spec scale) — no performance reason to escalate to a binary format.
- JSONL event log appends are O(1) per event, atomic at the line level (a half-written line on crash is detectable and recoverable).
- Human-readability supports debugging and the Constitution I "save everything" principle in a transparent way.

**Alternatives considered**:
- **SQLite**: overkill for a single-process write pattern; requires schema-migration discipline we don't need at this scale.
- **Pickle / protobuf**: opaque to operator inspection; violates the spirit of `experiments/*/ANALYSIS.md` being human-readable corpora.
- **Single JSON file with embedded events**: rewrites the whole file on every event → quadratic in event count over the portfolio lifetime. Append-only JSONL is the right separation.

---

## R-3: Sector metadata source

**Decision**: `yfinance.Ticker(ticker).info["sector"]` lookup, cached at `~/.tradingagents/paper/sectors.json` keyed by ticker. Fetched lazily on first entry, never invalidated (sector classifications are stable).

**Rationale**:
- yfinance is already the framework's only equity-data dependency; no new third-party API required.
- `Ticker.info["sector"]` is reliable for US equities (the harness's scope).
- Lazy fetch + persistent cache = zero network cost on subsequent runs.
- Tickers that yfinance can't classify default to `"Unknown"` per the spec's Assumption — treated as their own sector for cap purposes (graceful degradation, no crash).

**Alternatives considered**:
- **Hardcoded sector lookup table**: requires manual maintenance; new tickers (IPOs, additions to default watchlist) silently default to Unknown.
- **GICS API / paid data feed**: violates the no-new-deps constraint.
- **alpha_vantage `OVERVIEW` endpoint**: works but requires a separate API key the harness shouldn't need (the harness has zero LLM cost; adding a non-LLM API key dependency would muddy the operator setup story).

---

## R-4: Sizing-rounding strategy

**Decision**: Whole-share sizing only. `qty = floor(target_dollar_size / entry_price)`. Cash residual stays in the cash buffer (counted toward the 10% cash buffer floor for the next entry decision). No fractional shares in v1.

**Rationale**:
- Whole-share simulation matches realistic broker semantics for non-fractional accounts.
- Sub-1% sizing error at typical $100k notional + 8 positions × 10% = $1,250 per slot; rounding error <$1 per slot at typical share prices ($20-$500). Rounds-to-zero edge cases (e.g., $1,250 / $5,000 = 0.25 shares → 0 → no entry) are caught by the cash-shortfall skip event (per spec edge-case handling).
- Spec Assumption explicitly disables fractional shares for v1; this implementation matches.

**Alternatives considered**:
- **Fractional shares (4 decimal places)**: Empirically more α-precise but: (a) operator's eventual broker may not support fractional, (b) reconciliation complexity for splits/dividends. Defer to v2.
- **Dollar-cost-average across multiple entries**: out of scope; spec is single-entry-per-bullish-commit.

---

## R-5: Idempotency detection mechanism

**Decision**: The Portfolio's `equity_curve` field stores `(date, mark_to_market_equity, benchmark_equity)` tuples. Before `step` does anything else, it checks `if any(e.date == target_date for e in portfolio.equity_curve): return EarlyExit(reason="already_processed")`. The check is O(N) in equity_curve length but N grows linearly in trading days (~252/year) and the lookup is dwarfed by the yfinance fetch latency anyway.

**Rationale**:
- Single source of truth — `equity_curve` is updated atomically when a `step` succeeds. If the date is in there, the day was processed.
- No separate "processed dates" set to keep in sync (which would be its own correctness liability).
- An `EarlyExit` event STILL gets logged to JSONL (`event_type: step_skipped_already_processed`) so operator can audit why a day was skipped. SC-002 requires byte-identical state file before/after; the JSONL append is to a separate file and doesn't violate that.

**Alternatives considered**:
- **Last-processed-date sentinel field**: works but loses information (re-runs of older days vs same-day re-run distinction is muddied).
- **State-file mtime check**: race-prone; doesn't survive restoring from backup.
- **Hash-based fingerprint of (state, signals)**: overengineered for the use case.

---

## R-6: Trading-calendar source

**Decision**: Derive trading days from `yfinance` price-frame index. The `pricing.py` module's `next_trading_day_close(ticker, date)` helper queries yfinance for `date` through `date + 7 calendar days`, takes the second row's index as the next trading day. No separate `pandas_market_calendars` dependency.

**Rationale**:
- yfinance is already the source of truth for prices; deriving trading days from price availability is consistent.
- Zero new dependency.
- The 7-calendar-day buffer covers any 3-day weekend or single holiday; multi-day market closures (rare; e.g. extended NYSE outage) would surface as a `data_anomaly` event — acceptable graceful degradation.

**Alternatives considered**:
- **`pandas_market_calendars`**: more accurate (knows holidays in advance) but adds a dependency for a small benefit. yfinance-derived is sufficient at the harness's scale.
- **Hardcoded NYSE holiday list**: requires annual maintenance; goes stale.
- **`exchange_calendars`**: same dependency tradeoff as `pandas_market_calendars`.

---

## R-7: Holding-window measurement (trading days vs calendar days)

**Decision**: Trading days. The default holding window is `21 trading days`; the `intended_close_date` field is computed by counting forward 21 actual trading days (yfinance index hops) from the entry date. Matches the framework's existing forward-α convention (`fetch_returns(holding_days=21)` interprets `21` as trading days per the docstring updated in commit `118199a`).

**Rationale**:
- Consistent with `returns_from_frames` and the SC-003 validation gate (which measured 21 trading days). If the harness used calendar days, SC-001 reproduction would fail by ~6 days of price drift.
- Trading-day arithmetic naturally skips holidays and weekends without per-event special-casing.

**Alternatives considered**:
- **Calendar days**: simpler arithmetic but breaks SC-001 reproduction.
- **Mixed (trading-day for entry, calendar-day for exit)**: complexity with no benefit.

---

## R-8: Slippage modeling depth

**Decision**: Fixed-bps haircut on entry close (multiply by `1 + entry_slippage_bps/10000`) and exit close (multiply by `1 - exit_slippage_bps/10000`). Default 5 bps each side. Configurable via PolicySnapshot. No volume-aware, no spread-aware, no impact-aware modeling.

**Rationale**:
- Honest to the simulation level: the harness is not a market-impact model.
- Fixed-bps default is a conservative average for liquid US equities at typical $1,000-$15,000 per-position size.
- 0-bps default available for operators who want to reconcile exactly with the framework's analyzer numbers (which assume zero slippage). Non-zero default is more honest for "what would my account actually do" framing.

**Alternatives considered**:
- **Bid-ask spread modeling**: requires intraday quote data the framework doesn't fetch.
- **Volume-impact modeling (e.g., square-root rule)**: requires per-name volume data + calibration; out of scope.
- **Time-of-day slippage**: requires intraday data; out of scope.

---

## R-9: CSV-vs-stdin signals input

**Decision**: CSV file via `--signals-csv <path>` argument. No stdin pipe support in v1 (operator can `--signals-csv -` and we'd need to handle it specially; defer).

**Rationale**:
- File-based input matches the existing project pattern (`scripts/analyze_backtest.py` takes a CSV path).
- Files are inspectable post-hoc; stdin is not.
- Simplifies idempotency: re-running `step` with the same CSV file is naturally re-runnable.

**Alternatives considered**:
- **Stdin only**: makes scripted testing harder; loses the "look at the input later" property.
- **JSON input**: CSV is what `daily_signals.py --emit-csv` produces; using JSON would require a translation layer.

---

## R-10: `daily_signals.py --emit-csv` schema design

**Decision**: The new `--emit-csv <path>` option writes a CSV with the following columns in this order:
- `ticker` (str)
- `analysis_date` (ISO date YYYY-MM-DD)
- `rating` (str — one of `Buy` / `Overweight` / `Hold` / `Underweight` / `Sell`)
- `gate_threshold` (int — the percentile threshold used)
- `a3_threshold` (float — the A3 momentum threshold used)
- `model_deep` (str)
- `model_quick` (str)
- `run_seconds` (float)
- `error` (str — empty if successful)

This is a strict superset of what the harness needs (`ticker`, `analysis_date`, `rating`); extra columns are documented as "ignored by paper_trade.py" but useful for downstream analysis.

**Rationale**:
- Mirrors the schema that `scripts/backtest.py` already produces (the experiment results.csv pattern), so existing tooling (`scripts/analyze_backtest.py`) can read both interchangeably.
- Strict superset means the harness's CSV-parsing code only depends on the 3 required columns; new optional columns can be added to `daily_signals.py` later without breaking the harness.

**Alternatives considered**:
- **Minimum-required columns only**: would diverge from the existing experiment CSV convention; `scripts/analyze_backtest.py` couldn't consume `daily_signals.py --emit-csv` output without translation.
- **JSON output**: doesn't compose with existing CSV-consuming tools.

---

## R-11: Default watchlist composition

**Decision**: `data/watchlists/tech_weighted.txt` ships with these ~25 tickers, sector-balanced per SC-003 empirical findings:

```
# Tech (~60% weight; SC-003 showed +17.80% mean α on bullish picks here)
AAPL
MSFT
NVDA
GOOGL
AMZN
META
AVGO
ORCL
ADBE
CRM
NFLX
CSCO
AMD
QCOM
TSLA

# Healthcare (~15%; SC-003 showed +8.16% on n=2 — small but positive)
UNH
LLY
ABBV

# Financials (~10%; SC-003 showed -7.07% on bullish — included for sector diversification, but expect cap to limit damage)
JPM
GS

# Other (~15%)
INTC
ABT
HD
MCD
XOM
```

**Rationale**:
- Empirically grounded in SC-003's per-sector breakdown.
- 25 tickers fits inside the per-sector cap math: even if all 25 went bullish on the same day, the sector cap (50%) + per-position cap (15%) + max-positions cap (8) would limit exposure responsibly.
- Comments document sector intent so the operator can see why each ticker is on the list.

**Alternatives considered**:
- **S&P 500 default**: too large for a "demo path"; daily LLM cost would balloon at the signal-generation layer.
- **NASDAQ-100**: tech-pure; SC-003 said sector diversification matters, even if Tech is overweighted.
- **Operator-must-provide**: friction for the demo path; spec assumption was to ship one.

---

## R-12: Disclaimer wording (Principle IV)

**Decision**: The exact disclaimer text appearing at the top of every digest:

> ⚠️ **Simulation only — not financial advice.** This portfolio is paper-traded for research purposes. No real capital is involved. Past performance of simulated trades does not predict future results. Generated by `tradingagents-lab/scripts/paper_trade.py` (Constitution Principle IV).

Asserted by SC-005 via a `tests/test_paper_digest.py::test_principle_iv_disclaimer_present` unit test that greps the digest output for the verbatim substring `"Simulation only — not financial advice"`.

**Rationale**:
- Verbatim substring + greppable test = unambiguous SC-005 verification.
- Reuses the project's existing emoji+bold convention for warnings (matches `claudedocs/SETUP.md` style).
- Mentions the script path so a printed/screenshotted digest carries provenance.

**Alternatives considered**:
- **Generic legalese paragraph**: harder to test for; less skimmable.
- **Trail in footer only**: spec requires "prominent" — header position is more prominent.

---

## R-13: Test fixture strategy for SC-001 reproduction

**Decision**: The integration test `tests/test_paper_sc003_reproduction.py::test_replay_sc003_reproduces_bullish_bucket` is marked `@pytest.mark.integration` (skipped by default in pre-commit's `pytest -m unit`). It:
1. Reads `experiments/2026-05-05-003-signal-at-scale/results.csv` directly (the file is gitignored but present on the dev machine; the test skips with a clear message if the file is missing — operator must run SC-003 first or have the corpus checked out).
2. Constructs a watchlist from the unique tickers in the CSV.
3. Runs `replay` over the SC-003 date range.
4. Asserts the closed-position mean α is within ±100 bps of +5.96% (per SC-001).

**Rationale**:
- Integration test against real yfinance data is the only way to verify the validation gate.
- Marking it `integration` keeps the unit-test pre-commit hook fast (the project standard).
- Skipping gracefully when the corpus file is missing keeps CI green for fresh checkouts that don't have the full experiments corpus.

**Alternatives considered**:
- **Pure unit test with synthetic prices**: doesn't validate the SC-001 reproduction; defeats the purpose.
- **Hardcoded expected α**: brittle to upstream yfinance data corrections.

---

## Summary of resolved unknowns

All technical-context items in `plan.md` resolved:
- Caching → R-1
- Persistence → R-2
- Sector data → R-3
- Sizing rounding → R-4
- Idempotency → R-5
- Calendar → R-6
- Holding-window units → R-7
- Slippage → R-8
- CSV input → R-9
- `--emit-csv` schema → R-10
- Default watchlist → R-11
- Disclaimer wording → R-12
- SC-001 test fixture → R-13

No outstanding NEEDS CLARIFICATION. Proceed to Phase 1 (data-model + contracts + quickstart).
