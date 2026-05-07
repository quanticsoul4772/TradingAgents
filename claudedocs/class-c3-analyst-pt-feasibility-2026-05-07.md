# Class C-3 (analyst PT delta) feasibility probe — 2026-05-07

**Goal**: De-risk the eventual ~3h Class C-3 (analyst price-target delta)
forward-catalyst-class retrospective by verifying yfinance API supports
the data shape we'd need.

**Probe script**: `scripts/probe_analyst_price_targets.py` (15 single
stocks across Tech/Financials/Energy/Healthcare + 2 ETFs)

**yfinance version**: 1.3.0

## Core finding: API works, but only returns CURRENT snapshot

`yf.Ticker(t).analyst_price_targets` returns a dict with 5 keys:
`{current, high, low, mean, median}`. Example NVDA: `{current: 211.525,
high: 380.0, low: 140.0, mean: 269.165, median: 265.0}`.

15/15 single-stock tickers return populated dicts. Mean latency 73ms,
max 313ms — fully LRU-cacheable per ticker (analogous to spec 008
calendar boost yfinance fetch pattern).

**HARD LIMITATION**: there's no historical-PT-panel API. We can read TODAY's
PT, but yfinance doesn't expose what the PT was on 2026-04-17 or 2026-04-24
or any prior backtest date. This kills the original C-3 design (compute
"PT delta over prior 14d" as the catalyst signal for retrospective
backtest replay).

## ETF behavior: graceful degradation

SPY and XLF both return `{}` (empty dict) and 0×0 DataFrame for
recommendations. No exception. Mirrors spec 008 calendar-boost behavior
on tickers without earnings calendars — degrades cleanly. Means a future
C-3-style filter could safely run on universes including ETFs without
special-casing.

## `recommendations` DataFrame: alternative angle

Each ticker also exposes a `recommendations` DataFrame with shape (4, 6)
and columns `[period, strongBuy, buy, hold, sell, strongSell]`. The
periods are `0m, -1m, -2m, -3m` — current month plus 3 prior months of
analyst rating COUNTS.

Example NVDA:
| period | strongBuy | buy | hold | sell | strongSell |
|---|---|---|---|---|---|
| 0m | 9 | 48 | 2 | 1 | 0 |
| -1m | 9 | 48 | 2 | 1 | 0 |
| -2m | 9 | 48 | 2 | 1 | 0 |
| -3m | (similar) | | | | |

This is **NOT historical PT panels** — it's analyst-rating-distribution
counts over a rolling 4-month window. So we COULD compute month-over-month
rating-shift as a catalyst signal:
- `Δ_strongBuy = strongBuy[0m] - strongBuy[-1m]`
- `Δ_total_bullish = (strongBuy + buy)[0m] - (strongBuy + buy)[-1m]`
- `Δ_consensus_score = weighted_avg([0m]) - weighted_avg([-1m])`

But this also has a CRITICAL LIMITATION: the `0m / -1m / -2m / -3m`
labels are RELATIVE TO TODAY, not absolute calendar dates. We can read
"current vs 1 month ago" today, but on 2026-04-17 the same query would
have returned different data. **Without snapshotting, we can't backfill
historical retrospectives**. Only forward-going observations work.

## C-3 viability verdict

**Original C-3 design (PT delta retrospective)**: NOT FEASIBLE on $0 budget.

Three rescue paths in increasing cost order:

### Path A: Forward-going observation only (T0 / $0)
- Add a `analyst_pt_snapshot.py` script that fetches `analyst_price_targets`
  + `recommendations` for our watchlist daily and persists to JSON
- After ~30 days of accumulation we'd have enough history to compute
  PT-delta and rating-shift signals on FORWARD propagates
- Doesn't unlock retrospective on existing 1000+ row corpus
- **Cost**: $0 LLM, ~10 minutes to build, ~1ms/day to run

### Path B: Use `recommendations` rating-shift as approximate retrospective signal (T0 / $0)
- Acknowledge the relative-period labels mean we can't time-align PERFECTLY
  to historical backtest dates
- For each historical row, fetch `recommendations` TODAY (which gives us
  the most recent 4-month rolling window), then apply rating-shift signals
  ONLY to backtest dates in the 0-3 month range from today
- Tighter sample: 2026-02-07 to 2026-05-07 = ~3 months of replayable backtest
  rows where the relative labels still meaningfully line up
- **Cost**: $0 LLM, ~30 min to script, but **methodologically dubious**

### Path C: Snapshot the recommendations DataFrame from each backtest run going forward (T0 / $0)
- Modify the spec 007 `forward_catalyst_filter` to also persist
  `analyst_pt_snapshot` + `recommendations_snapshot` to `state["forward_catalyst"]`
- This makes future backtest runs C-3-replay-capable AT THE TIME OF THE PROPAGATE
- Doesn't help us this week — we'd need to run a fresh backtest with the
  snapshot wiring active, then wait for the realized-α window to close
- **Cost**: $0 LLM, ~1h to wire + retest, but ~$15 + 21d wait to validate

### Path D: Paid historical PT panels (NOT pursued)
- FactSet, Bloomberg, Refinitiv, etc. all sell historical analyst PT panels
- Out of constitution III T0 cost gate ($0 / free); rejected by default

## Recommended next move

**Skip the original C-3 retrospective**. The $0-budget gate (constitution
III) effectively rules it out for retrospective application. If the
analyst-PT mechanism class is interesting enough, the right investment is
**Path C** (snapshot wiring) — it costs ~1h to add to spec 007 state log,
piggybacks on existing LLM spend, and unlocks future retrospectives
without any new $$. Defer Path C until a future spec has empirical
motivation (e.g., a finding from cross-cohort sweep that identifies
analyst-PT-delta as a candidate mechanism for an unmet cohort).

**Constitution VIII v1.4.0 verdict on C-3**: cannot run the gate
retrospective methodology because data isn't replayable. Pre-spec
retrospective gate is structurally inapplicable here. Future spec attempt
would need to use shadow-mode-first launch (criteria 1+2 only, criterion
3 deferred to forward-validation) OR collect 30+ days of forward
snapshots before running any spec.

## Sibling docs

- `claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.md`
  — earlier C-1 (insider transactions) SKIP
- `claudedocs/sc-009-bear-side-mid-flight-diagnostic-2026-05-07.md` —
  shows spec 007 score behavior on COP+INTC bear commits
- `tradingagents/agents/utils/forward_catalyst_filter.py` — would gain
  `state["forward_catalyst"]["analyst_pt_snapshot"]` field under Path C
- `specs/006-forward-catalyst-gate/spec.md` — spec 007 implementation
  reference
