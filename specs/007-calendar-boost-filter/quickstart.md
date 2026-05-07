# Quickstart — Spec 008 Hybrid C Calendar-Boosted Forward-Catalyst Filter

**Branch**: `007-calendar-boost-filter` | **Date**: 2026-05-06

## Operator quickstart (after Spec 008 lands)

### Step 1 — Verify Spec 007 is active

Hybrid C is structurally INSIDE Spec 007 (no PM hook chain change per FR-014). Confirm Spec 007 is in `active` mode for at least the bull side:

```python
# In your PARAMS.json or via CLI override:
{
  "forward_catalyst_bull_mode": "active",   # required for Hybrid C bull-side enhancement
  "forward_catalyst_bull_threshold": 0.60   # spec 007 default; Hybrid C tuned for this value
}
```

### Step 2 — Enable Hybrid C with empirically-grounded defaults

Add three keys to your PARAMS.json (or CLI override via `--config-override`):

```json
{
  "hybrid_c_calendar_boost_enabled": true,
  "hybrid_c_calendar_boost_window_days": 14,
  "hybrid_c_calendar_boost_magnitude": 0.5
}
```

The defaults `(window=14, magnitude=0.5)` come from the production-config retrospective best config (`claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`). The retrofit showed magnitude is fungible within window=14d (any of {0.5, 1.0, 2.0} produces identical fire pattern); 0.5 is the most conservative choice.

### Step 3 — Run daily_signals or a backtest

```bash
python scripts/daily_signals.py --tickers tickers.txt
```

Expected behavior:
- **Bull-side commits with earnings within 14 days AND borderline-below-threshold scores (0.40-0.60 range)**: effective score crosses threshold; rating downgrades to Hold (additional ~+3.35pp net Δα catch per the retrospective).
- **Bull-side commits with earnings 14+ days away OR no calendar data (e.g., ETFs)**: boost = 0; effective = base; spec 007 baseline behavior unchanged.
- **Bear-side commits**: unchanged (FR-004 — bull-only).

### Step 4 — Verify the boost annotations in state logs

For any propagate run with the boost enabled, the state log JSON includes (under `state.forward_catalyst`):

```json
{
  "days_to_earnings": 7,
  "calendar_boost": 0.5,
  "effective_bull_score": 0.625,
  "effective_bear_score": 0.32,
  "...": "spec 007 fields (bull_case_priced_in, bear_case_priced_in, mode, etc.)"
}
```

### Step 5 — Verify the regression check (SC-008)

After landing Spec 008, re-run the retrospective and confirm the +3.35pp bull-side improvement reproduces:

```bash
python scripts/forward_catalyst_hybrid_c_retrospective.py
```

Expected verdict: PASS — bull-side at window=14d, magnitude=0.5x produces +3.35pp net Δα improvement vs Class 3-alone baseline (within ±0.5pp tolerance).

## Cost expectation (Constitution III T0)

Hybrid C adds **$0** per propagate (FR-015 + SC-011). Mechanism:
- Spec 007 LLM call: already paid (no second LLM call)
- yfinance.earnings_dates fetch: free, LRU-cached per ticker per process
- Boost arithmetic: pure Python multiplication

A single `daily_signals.py` run over 5 tickers shows the same total LLM cost line ($0.40 × 5 ≈ $2 baseline per spec 007 quickstart) regardless of whether Hybrid C is enabled.

## Latency expectation (SC-012)

- Cache-cold ticker (first call per process): adds ≤250 ms p99 (single yfinance HTTP fetch).
- Cache-warm ticker (subsequent calls in same process): adds ≤5 ms p99 (in-memory dict lookup + arithmetic).

For a 5-ticker daily_signals run, the cold latency hits 5× once (one fetch per ticker on first encounter), then warms for any subsequent same-process calls.

## When NOT to enable Hybrid C

- **Spec 007 is in mode="off"**: Hybrid C does nothing (no spec 007 fire decision to enhance). Set Spec 007 to "active" or "shadow" first.
- **You're running an isolated experiment that should baseline against pre-Hybrid C behavior**: leave `hybrid_c_calendar_boost_enabled=False` (the default) so your `experiments/<id>/` results are comparable to the spec 007 baseline corpus.
- **Your ticker universe is mostly ETFs / new IPOs without earnings calendars**: graceful-degradation path (FR-010) makes the helper a no-op for those tickers, but you're paying ~250 ms per first-call ticker for nothing. Functionally fine, just no benefit.

## Ablation procedure (before considering default-on flip per SC-009)

If you want to validate the +3.35pp improvement in your own use case before any future spec amendment flips the default:

1. Run `daily_signals.py` with `hybrid_c_calendar_boost_enabled=False` over n ≥ 30 propagates. Save state logs.
2. Run `daily_signals.py` with `hybrid_c_calendar_boost_enabled=True` over the SAME n ≥ 30 propagates (same tickers, same dates). Save state logs.
3. Use `analyze_backtest.py` with `--counterfactual-md` to attribute alpha differences specifically to the rows where `state.forward_catalyst.calendar_boost > 0` (i.e., boost actually fired).
4. Verify the +3.35pp bull-side improvement holds within ±1pp at the 21-day forward-alpha horizon. If yes, document evidence in a future Spec 008.5 amendment. If no, leave default-off and document why your operator universe differs from the SC-008 retrospective cohort.

## Rollback procedure

To disable Hybrid C without removing it:

```json
{
  "hybrid_c_calendar_boost_enabled": false
}
```

Spec 007 baseline behavior is restored immediately. State logs revert to spec 007 baseline shape (no Hybrid C annotation keys per FR-011).

## Smoke-test integration scenarios (for QA after Spec 008 lands)

1. **Boost ENABLED + earnings TODAY + borderline score**:
   - Setup: ticker NVDA, trade_date == NVDA earnings day, mocked `bull_case_priced_in=0.50`, defaults
   - Expected: `days_to_earnings=0`, `calendar_boost=1.0`, `effective_bull_score=min(1.0, 0.5*1.5)=0.75`, fires
2. **Boost ENABLED + earnings 14 DAYS AWAY**:
   - Setup: same but mocked `days_to_earnings=14`
   - Expected: `calendar_boost=0`, `effective_bull_score=0.50`, does not fire
3. **Boost ENABLED + yfinance fails**:
   - Setup: monkey-patch `yfinance.Ticker(t).earnings_dates` to raise
   - Expected: `days_to_earnings=None`, `calendar_boost=0`, `effective_bull_score=base`, spec 007 baseline behavior
4. **Boost DISABLED (default)**:
   - Setup: leave `hybrid_c_calendar_boost_enabled=False`
   - Expected: state["forward_catalyst"] dict-key set equals spec 007 baseline; no Hybrid C keys present
5. **Boost ENABLED + ETF (no earnings calendar)**:
   - Setup: ticker SPY, `yfinance.Ticker("SPY").earnings_dates` returns empty
   - Expected: `days_to_earnings=None`, `calendar_boost=0`, effective=base, spec 007 baseline behavior
