# Spec 003 historical-recompute — backfill results

**Trigger**: PR #68 cold-start diagnostic identified that 22 of 36 SC-009
rows (61%) had `gate_baseline=none` because the spec 003 cache lacked
sufficient per-ticker / sector history. PR #68 followup #3 was a
historical-recompute script to backfill the cache from existing state
logs (no new propagates needed; zero LLM cost).

**Script**: `scripts/spec_003_historical_recompute.py` + 7 unit tests.

## Results — 254 state logs backfilled with 0 errors

```
State logs scanned:  254
Written to cache:    254
Skipped (existing):  0
Skipped (no prose):  0
Skipped (errors):    0
```

## Cache state — before vs after

**Before**: cache mostly populated by 2026-05-04+ propagates (since
spec 003 went live 2026-05-04). Pre-spec-003 propagates had market_report
prose in state logs but no cache entries.

**After**: 435 cache rows for `signal_id=market_report` across 54
distinct tickers.

## Tickers now clearing FR-004 N≥20 per-ticker floor

After backfill, **9 tickers** have ≥20 cached values for `market_report`,
sufficient to trigger `gate_baseline=per_ticker`:

| Ticker | Cache rows |
|---|---|
| NVDA | 67 |
| AAPL | 57 |
| INTC | 52 |
| XLE | 40 |
| MSFT | 36 |
| GOOGL | 34 |
| JPM | 34 |
| XLF | 20 |
| XLK | 20 |

**JPM and GOOGL are the most operationally significant additions**: both
had `baseline=sector` (15-17 rows below FR-004 floor) per PR #68
sub-pattern 1; both now cross the floor and would use `per_ticker`
baseline on the next propagate.

The 5 ETFs (XLE, XLF, XLK) clear because they're well-represented in
the prior Phase D substrate experiments. The 4 single stocks
(AAPL, GOOGL, INTC, JPM, MSFT, NVDA) are the most-frequently-propagated
tickers across the corpus.

## Tickers still cold-start after backfill

The PR #68 sub-pattern 2 tickers (5 sectors with empty pools) only
gained 2 entries each from SC-009 — still well below FR-004 floor:

| Ticker | Cache rows after backfill |
|---|---|
| AMZN | 2 |
| COP | 2 |
| CVX | 2 |
| LLY | 2 |
| HON | 2 |
| MA | 2 |
| AMD | (existing per-ticker, less frequently run) |
| BAC | (existing sub-pattern 1, ~2 entries) |
| GS | (existing sub-pattern 1, ~2 entries) |
| WFC | (existing sub-pattern 1, ~3 entries) |

These tickers need **more propagates run on them** (or sector-pool
warmup as separately discussed in PR #68 implication 3) — backfill
alone can't help if the source data wasn't there.

## Sector-pool aggregation effect

Spec 003.5 sector-baseline-fallback aggregates per-ticker history
across tickers in the same sector when per-ticker is below FR-004.
With 9 tickers now clearing per-ticker floor (and many more with 1-5
rows each), the SECTOR pools should also be larger:

- **Tech sector pool**: AAPL+GOOGL+INTC+MSFT+NVDA+AMD+AVGO+CSCO+META+TSLA+AMZN combined → comfortably above FR-004 floor for any Tech ticker requesting sector baseline
- **Financials sector pool**: BAC+GS+JPM+WFC+MS combined → above floor
- **ETF pool**: XLE+XLF+XLK combined (likely small but exists)
- **Other sectors** (Energy, Healthcare, Industrials, Consumer Cyclical):
  still thin; would benefit from sector-pool warmup

## Operational impact summary

For a future SC-009-class backtest run on the same 18 tickers:

| Cohort tickers | Pre-backfill baseline | Post-backfill expected |
|---|---|---|
| AAPL, AMD, INTC, MSFT, NVDA | per_ticker (already) | per_ticker (more rows) |
| GOOGL, JPM | sector (15-17 rows) | **per_ticker (34 each)** |
| AVGO, CSCO | sector | sector or per_ticker depending on per-ticker |
| BAC, GS, WFC, MA | sector (15-17) | sector (more rows; still below per-ticker floor) |
| AMZN, COP, CVX, LLY, HON | none (sector=0) | **sector (now 1-2 entries via backfill)** OR none if floor unmet |

Net effect on the SC-009 cohort: 22-of-36 baseline=none rate would
likely drop to ~10-15 (from sub-pattern 2 tickers still being
single-ticker-only with ~2 entries; sector pool needs more diversity).

## Idempotency + re-runnability

The cache schema uses `INSERT OR REPLACE` keyed on
`(signal_id, ticker, date, fetcher_version)`, so re-running the script
is safe — values get overwritten with same data. `--skip-existing`
flag available for those who want to avoid the writes anyway.

## Followups (recorded)

1. **Sector-pool warmup design**: 3-5 representative tickers per
   underrepresented sector (Energy, Healthcare, Industrials, Consumer
   Cyclical). Would unblock sub-pattern 2 cold-start. ~$15 LLM, ~5h
   compute. Same followup as PR #68 implication I-3.
2. **Run analyzer on next backtest with the enriched cache** to
   measure: did baseline=none rate actually drop?
3. **Bear-side recompute**: re-run this script with
   `--feature bear_keyword_count` to populate the bear-side featurizer
   cache too. Tooling supports it (script accepts `--feature` flag).
   ~5min, $0.

## Sibling docs

- `claudedocs/spec-003-cold-start-diagnostic-sc-009-2026-05-07.md`
  — PR #68 (motivating diagnostic)
- `tradingagents/signals/contrarian_gate.py` — DEFAULT_HISTORY_FLOOR=20
- `tradingagents/signals/cache.py` — sqlite cache schema
- `tradingagents/signals/featurization.py` — FEATURIZERS registry
- `memory/reference_spec_003_cold_start_coverage.md` — operator memory
