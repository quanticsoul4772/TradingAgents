# Phase 0: Research — Sector-Momentum Filter

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

Resolves the technical-context decisions surfaced during planning. All NEEDS CLARIFICATION items from `plan.md` resolved here. Each entry: Decision / Rationale / Alternatives Considered.

---

## R-1: Sector lookup integration

**Decision**: Use `tradingagents/paper/sectors.py::get_sector(ticker, cache_path)` — the same yfinance-cached sector lookup spec 003.5 uses. Cache path defaults to `<paper_state_dir>/sectors.json` per Spec 002 convention; the filter reads `paper_state_dir` from config (already a `TradingAgentsConfig` key after Spec 002).

**Rationale**:
- Single source of truth for sector membership across spec 003.5 + this spec.
- `get_sector` already handles `"Unknown"` fallback gracefully + yfinance failures.
- No new dependency.

**Alternatives considered**:
- **Build a parallel sector cache** — risks divergence with spec 003.5; rejected.
- **Hardcoded sector mappings** — won't scale; new tickers fall through.

---

## R-2: ETF price-data fetch path + caching

**Decision**: Use yfinance directly (`yf.Ticker(ETF).history(start=..., end=...)`) with an in-process LRU cache keyed by `(etf_symbol, start, end)`. Reuses the same pattern as `tradingagents.paper.pricing._cached_history` (Spec 002 precedent). The price frames feed directly into `tradingagents.dataflows.returns.returns_from_frames` for the prior-30-trading-day return computation per FR-005.

**Rationale**:
- Per-process LRU is cheap (`functools.lru_cache(maxsize=64)`). 11 ETFs × typical day's lookups → handful of cache entries.
- yfinance is already the canonical price source for the framework.
- Reusing `returns_from_frames` keeps forward-α math unified per FR-005 and the pattern from commit `118199a`.

**Alternatives considered**:
- **Persistent disk cache** — invalidation pain; ETF prices get adjusted retroactively for splits/dividends. Skip.
- **Use `tradingagents.paper.pricing.next_trading_day_close`** — close to what we need but oriented toward next-day execution rather than 30-day-back computation. The lower-level frame fetch + `returns_from_frames` is more direct.
- **Store ETF returns per date in the signal cache** — overkill; the data is freely fetchable on demand.

---

## R-3: Threshold semantics + boundary handling

**Decision**: Strictly less than (`return < threshold` ⇒ fire). Equality does NOT fire. Threshold values must be ≤ 0; positive values are rejected at config-load time with a logged warning + filter disabled (returns `mode_skipped` annotation reason `"invalid_threshold"`).

**Rationale**:
- Strict less-than matches A3's behavior (`tradingagents/agents/utils/momentum_filter.py::trailing_momentum_pct < threshold`).
- Boundary equality is rare in practice (random-walk sector ETF returns rarely hit a configured threshold to 4 decimal places); strict-less-than removes ambiguity in tests.
- Positive thresholds invert the intent (would fire on UP-trending sectors). Rejecting at config-load surfaces the error early.

**Alternatives considered**:
- **`<=` (inclusive)** — surfaces boundary edge cases in tests; rejected for consistency with A3.
- **Reject negative threshold validation** — too strict; rejected (a `None` threshold IS the off switch per FR-013).

---

## R-4: Filter ordering in PM hook chain

**Decision**: Order in `portfolio_manager.py`:
1. **A3** — bear suppression (UW/Sell → Hold)
2. **Spec 003 / 003.5 contrarian gate** — bull suppression via prose-density / sector-baseline
3. **Spec 004 sector-momentum filter** — bull suppression via sector ETF momentum

Each filter only sees the rating left by the prior filters. If a prior filter has already turned the rating to Hold, this filter no-ops (per FR-002: filter only acts on Buy/Overweight).

**Rationale**:
- A3 first because it acts on a DIFFERENT rating set (bear suppression) — never conflicts with the bull-suppression filters.
- Spec 003/003.5 next because its mechanism (within-ticker prose-density) is more specific (higher-confidence per finding #4 validation); should fire FIRST when applicable.
- This filter LAST as the safety net for sector-rotation losses the contrarian gate misses (today's empirical motivation).

**Alternatives considered**:
- **Spec 004 before spec 003** — would suppress potentially-good commits (sector down but ticker idiosyncratically strong). Order chosen routes prose-density-confirmed cases through spec 003 first.
- **Run all three in parallel and combine results** — overcomplicated; sequential gives clearer audit trails (operator can see which filter fired).

---

## R-5: Annotation persistence path

**Decision**: Add `"sector_momentum"` to the `_log_state` whitelist in `tradingagents/graph/trading_graph.py:425-453`. One-line extension matching the precedent set by commit `4c14d0f` (which added `contrarian_gate` after the SC-003 Financials investigation revealed the persistence bug).

**Rationale**:
- The state-log writer is a strict whitelist (deliberate per the original architecture); silently dropping the new field would replicate the spec 003 bug.
- Adding the entry is mechanical + minimal-risk.
- The `_log_state` test pattern (regression-guard tests added in commit `4c14d0f`) extends naturally — add a parallel `test_state_log_persists_sector_momentum_field` test.

**Alternatives considered**:
- **Refactor `_log_state` to dump everything** — broader change with unintended persistence-of-internal-state risks; rejected.
- **Skip persistence; rely on event-log alone** — there's no event log for filters today; persistence via state log is the only audit path.

---

## R-6: Retrospective script methodology (SC-008)

**Decision**: Build `scripts/sector_momentum_retrospective.py` that:
1. Walks `experiments/*/results.csv` for all bullish (Buy/OW) commits across the corpus.
2. For each commit, reads the state log to extract `(ticker, trade_date)`.
3. Looks up the ticker's sector via `tradingagents/paper/sectors.py`.
4. Maps to ETF via `SECTOR_ETF_MAP`.
5. Fetches the ETF's prior-30-trading-day return via `returns_from_frames`.
6. Reports: at each candidate threshold (-3, -5, -7.5, -10%), how many commits would have fired, what their realized α was, what the survivors' realized α was, and the net Δα contribution.
7. Includes a per-sector breakdown.

The SC-008 gate: at threshold = -5%, ≥3 of 5 SC-003 Financials Overweight commits should fire (XLF empirically down >5% in the 30 trading days before 2026-04-03 — VERIFY at implementation time; if false, the spec's motivating premise needs revisiting before commit).

**Rationale**:
- Mirrors `scripts/uw_suppression_filter.py` (A3) and `scripts/contrarian_gate_retrospective.py` (spec 003) — same offline-replay-against-existing-corpus methodology, $0 LLM cost.
- The candidate-threshold sweep gives the operator data to argue for or against a specific threshold when (eventually) flipping the default to active.
- Per-sector breakdown helps the operator understand where the filter would help (Financials) vs hurt (e.g., Tech in a Tech-rally regime — the filter would fire on a still-down Tech ETF and suppress what later turn out to be good entries).

**Alternatives considered**:
- **Live retrospective (re-run propagates with the filter on)** — costs LLM tokens; overkill when the filter's decision is purely deterministic given (ticker, date, threshold).
- **Don't write a retrospective; just unit tests** — wouldn't satisfy SC-008's "validate against SC-003 Financials" gate.

---

## R-7: SC-008 empirical-validation approach

**Decision**: SC-008 is verified by a SPECIFIC test in the new retrospective script:

```python
def test_sc003_financials_suppression_at_5pct_threshold():
    # Hard-coded SC-003 Financials cohort
    targets = [("JPM", "2026-04-03"), ("BAC", "2026-04-03"),
               ("WFC", "2026-04-03"), ("GS", "2026-04-03"), ("MA", "2026-04-03")]
    fired = simulate_filter(targets, threshold=-5.0, lookback=30)
    assert len(fired) >= 3, (
        f"Expected ≥3 of 5 to fire at -5% threshold; got {len(fired)}. "
        f"Verify XLF was down >5% in 30d before 2026-04-03."
    )
```

This test is `@pytest.mark.integration` (live yfinance dependency) and skipped in unit-only CI runs. It's run manually as part of the spec-004 implementation validation.

**If the test fails on live yfinance data**: the spec's motivating premise ("Financials losses came from sector-rotation; XLF was down") doesn't hold for the SC-003 date. Two possibilities:
1. **The Financials drawdown was stock-specific, not sector-wide** — adjust the spec's narrative; the filter still has theoretical merit but doesn't validate against THIS specific cohort. Document and proceed.
2. **The drawdown happened intra-window after 2026-04-03** — the filter wouldn't have known at signal-generation time; this is the limit of any look-back filter. Document.

Either way, surfacing the empirical truth is more valuable than assuming. The test makes the assumption falsifiable.

**Rationale**:
- Concrete test ties the spec's motivating empirical claim to executable verification.
- `@pytest.mark.integration` keeps it out of pre-commit unit-test runs (yfinance is slow + flaky for CI).
- Hard-coding the SC-003 cohort makes the test self-documenting.

**Alternatives considered**:
- **Soft assertion (just print, don't fail)** — loses the SC-008 gate's integrity.
- **No SC-008 test at all** — leaves the spec's motivating claim unverified; rejected.

---

## R-8: Module placement (extension vs new module)

**Decision**: New module `tradingagents/agents/utils/sector_momentum_filter.py`. Mirrors A3's `momentum_filter.py` placement.

**Rationale**:
- A3 + this spec share filter shape but operate on different inputs (per-ticker price vs sector ETF price) + emit different annotations. Co-located but separate keeps each module readable.
- Tests already follow the per-module pattern (`tests/test_momentum_filter.py` for A3; `tests/test_sector_momentum_filter.py` for this).
- Extending `momentum_filter.py` to handle both would conflate "bear suppression on per-ticker momentum" and "bull suppression on sector momentum" — two different mechanisms in one file.

**Alternatives considered**:
- **Inline in `portfolio_manager.py`** — too much logic in the PM module; rejected for testability.
- **Extend `momentum_filter.py`** — see above; rejected for clarity.
- **Put in `tradingagents/signals/`** — `signals/` is for featurizers + the contrarian gate; agent-stage filters belong in `agents/utils/` per existing convention.

---

## R-9: ETF history lookback boundary handling

**Decision**: When the trade date doesn't have ≥30 trading days of prior ETF history available (e.g., for very early dates, edge cases at IPO of an ETF), the filter MUST emit `skipped="missing_etf_data"` and pass the rating through unchanged.

**Rationale**:
- All 11 SPDR sector ETFs have decades of history (XLK launched 1998); in practice this only matters for synthetic test fixtures or dates before 1998-12-22 (XLK launch).
- Resilience pattern matches A3's "no data available → no fire" + the broader "filter never breaks PM pipeline" rule (FR-010).

**Alternatives considered**:
- **Use whatever shorter history is available** — would produce inconsistent thresholds. Rejected; clarity wins.

---

## R-10: GICS sector name normalization

**Decision**: yfinance reports sectors using its own naming convention (e.g., `"Financial Services"` not `"Financials"`; `"Consumer Cyclical"` not `"Consumer Discretionary"`). The `SECTOR_ETF_MAP` accepts BOTH common variants per FR-004 (e.g., maps both `"Financial Services"` and `"Financials"` to `"XLF"`). Sectors not in the map cause `skipped="no_etf_mapping"`.

**Rationale**:
- Empirically yfinance returns `"Financial Services"` for JPM/BAC/etc. (verified in spec 003.5's validation script).
- Operators may also encounter analyst tools using the GICS canonical naming (`"Financials"`) when ablating; supporting both reduces friction.
- Sectors yfinance might report outside the SPDR universe (e.g., "Crypto" or weird ADR classifications) gracefully degrade.

**Alternatives considered**:
- **Strict GICS only** — fails on yfinance's actual outputs.
- **Strict yfinance only** — fails when operators use GICS naming.

---

## Summary of resolved unknowns

All technical-context items resolved:
- Sector lookup → R-1
- ETF data fetch + caching → R-2
- Threshold semantics → R-3
- Filter ordering → R-4
- Annotation persistence → R-5
- Retrospective script methodology → R-6
- SC-008 empirical-validation approach → R-7
- Module placement → R-8
- ETF history boundary → R-9
- Sector name normalization → R-10

No outstanding NEEDS CLARIFICATION. Proceed to Phase 1 (data-model + contracts + quickstart).
