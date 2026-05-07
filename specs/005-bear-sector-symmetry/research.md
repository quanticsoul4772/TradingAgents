# Phase 0: Research — Bear-Sector-Symmetry Filter (Spec 006)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

Resolves the technical-context decisions surfaced during planning. All NEEDS CLARIFICATION items from `plan.md` resolved here. Each entry: Decision / Rationale / Alternatives Considered.

---

## R-1: Sector lookup integration

**Decision**: Use `tradingagents/paper/sectors.py::get_sector(ticker, cache_path)` — the same yfinance-cached sector lookup spec 003.5 + spec 004 use. Cache path defaults to `<paper_state_dir>/sectors.json` per Spec 002 convention; the filter reads `paper_state_dir` from config (already a `TradingAgentsConfig` key after Spec 002).

**Rationale**:
- Single source of truth for sector membership across spec 003.5 + spec 004 + this spec.
- `get_sector` already handles `"Unknown"` fallback gracefully + yfinance failures.
- No new dependency.

**Alternatives considered**:
- **Build a parallel sector cache** — risks divergence with spec 003.5 + spec 004; rejected.
- **Hardcoded sector mappings** — won't scale; new tickers fall through.

---

## R-2: ETF + ticker price-data fetch path + caching

**Decision**: Reuse `_etf_history` LRU-cached fetcher from spec 004's `tradingagents/agents/utils/sector_momentum_filter.py` for the sector ETF side. Add a parallel `_ticker_history` LRU-cached fetcher (`@lru_cache(maxsize=128)`) in this spec's new module for the ticker side. Both feed into `tradingagents.dataflows.returns.returns_from_frames` for prior-30-trading-day return computation per FR-005. The relative-strength delta is computed in this module's helper (`_compute_relative_strength_pct`).

**Rationale**:
- ETF cache reuse: spec 004 already paid the LRU-cache design cost; importing it ensures both filters benefit from cache hits when run in the same propagate (spec 004 fetches XLK; spec 006 fetches XLK — second fetch is a cache hit).
- Ticker cache: parallel pattern; `maxsize=128` covers typical multi-ticker workflows. Same pattern as spec 002's `_cached_history` for paper-trading prices.
- Reusing `returns_from_frames` keeps forward-α math unified per FR-005 and the pattern from commit `118199a`.

**Alternatives considered**:
- **Don't cache ticker fetches** — yfinance round-trips dominate latency; rejected for performance.
- **Build ticker cache in spec 004's module** — orthogonal to spec 004's bull-side mechanism; cleaner to keep ticker cache local to spec 006.
- **Persistent disk cache** — invalidation pain; ticker prices get adjusted retroactively for splits/dividends. Skip.
- **Use `tradingagents.paper.pricing.next_trading_day_close`** — close to what we need but oriented toward next-day execution rather than 30-day-back computation. The lower-level frame fetch + `returns_from_frames` is more direct.

---

## R-3: Threshold semantics + boundary handling

**Decision**: Strictly greater than (`relative_strength_pct > threshold` ⇒ fire). Equality does NOT fire. Threshold values must be ≥ 0; negative values are rejected at config-load time with a logged warning + filter disabled (returns `skipped="invalid_threshold"` annotation reason).

**Rationale**:
- Strict greater-than is the symmetric inverse of A3 + spec 004's strictly-less-than. The mechanism is "ticker outperformed sector by MORE than threshold"; equality should not fire.
- Boundary equality is rare in practice (ticker-vs-sector relative-strength rarely hits a configured threshold to 4 decimal places); strict-greater-than removes ambiguity in tests and matches A3's symmetric semantics.
- Negative thresholds invert the intent (would fire when ticker UNDERPERFORMED its sector, which is a different mechanism — that's where mean-reversion BUYERS would want a contrarian signal, not where bear-call suppression makes sense). Rejecting at config-load surfaces the error early.

**Alternatives considered**:
- **`>=` (inclusive)** — surfaces boundary edge cases in tests; rejected for consistency with A3 + spec 004 which both use strict comparison.
- **Reject `None` threshold validation** — too strict; rejected (a `None` threshold IS the off switch per FR-013).

---

## R-4: Filter ordering in PM hook chain

**Decision**: Order in `portfolio_manager.py`:
1. **A3** — bear suppression (UW/Sell → Hold) on per-ticker DOWN-absolute condition
2. **Bear-sector-symmetry (this spec)** — bear suppression (UW/Sell → Hold) on ticker-UP-relative-to-sector condition
3. **Spec 003 / 003.5 contrarian gate** — bull suppression via prose-density / sector-baseline
4. **Spec 004 sector-momentum filter** — bull suppression via sector ETF momentum

The two bear filters (A3 + spec 006) operate on near-disjoint price-condition cohorts: A3 fires when ticker is DOWN ≥5% absolute; spec 006 fires when ticker is UP relative to sector (which usually means UP absolute too). The relative ordering between A3 and spec 006 is documented for determinism but doesn't affect outcomes in practice — at most one of them can fire on any given commit, and if A3 fires first the rating becomes Hold, which causes spec 006 to no-op (per FR-002: filter only acts on UW/Sell). Bull/bear filters never see each other's input ratings, so the cross-side ordering between {A3, spec 006} and {spec 003, spec 003.5, spec 004} is commutative.

**Rationale**:
- A3 first because it's the older, established bear-suppression filter; spec 006 is the newer addition layered on top.
- Cross-side commutativity confirmed by inspection: bull filters check `pre_rating in {Buy, Overweight}`; bear filters check `pre_rating in {Underweight, Sell}`. Disjoint sets.
- Within-side ordering between two bear filters is deterministic-but-irrelevant due to the disjoint-conditions property.

**Alternatives considered**:
- **Spec 006 before A3** — symmetric outcome; chosen ordering preserves "older filter first" convention.
- **Run both bear filters in parallel and combine results** — overcomplicated; sequential gives clearer audit trails (operator can see which filter fired via the annotation `fired` field).
- **Conditional dispatch (only run spec 006 if A3 didn't fire)** — micro-optimization; rejected for code clarity. The no-op-on-Hold path in spec 006's FR-002 is sufficient.

---

## R-5: Annotation persistence path

**Decision**: Add `"bear_sector_symmetry"` to the `_log_state` whitelist in `tradingagents/graph/trading_graph.py`. One-line extension matching the precedent set by:
- Commit `4c14d0f` (which added `contrarian_gate` after the SC-003 Financials investigation revealed the persistence bug)
- Spec 004 (which added `sector_momentum`)

Additionally, add `bear_sector_symmetry: NotRequired[dict | None]` to the `AgentState` TypedDict in `tradingagents/agents/utils/agent_states.py`. Spec 003 originally hit and worked around the LangGraph `StateGraph` silent-drop bug for undeclared keys; spec 003 fixed it by declaring the key in the TypedDict. Spec 004 followed the same pattern. This spec follows the same pattern for the third time.

**Rationale**:
- The state-log writer is a strict whitelist (deliberate per the original architecture); silently dropping the new field would replicate the spec 003 bug.
- The AgentState TypedDict declaration prevents the LangGraph silent-drop on graph state merges.
- Adding both entries is mechanical + minimal-risk.
- Test pattern (regression-guard tests added in commit `4c14d0f` and reproduced in spec 004) extends naturally — add a parallel `test_state_log_persists_bear_sector_symmetry_field` test.

**Alternatives considered**:
- **Refactor `_log_state` to dump everything** — broader change with unintended persistence-of-internal-state risks; rejected.
- **Skip persistence; rely on event-log alone** — there's no event log for filters today; persistence via state log is the only audit path.
- **Use a generic `filters` dict instead of one key per filter** — would conflate audit trails across filters; harder to query downstream. Per-filter key (already 2 deep: `contrarian_gate` + `sector_momentum`; this adds the 3rd) is clearer.

---

## R-6: Retrospective script methodology (SC-008)

**Decision**: Build `scripts/bear_sector_symmetry_retrospective.py` that:
1. Walks `experiments/*/results.csv` for all bearish (Underweight/Sell) commits across the corpus.
2. For each commit, extracts `(ticker, trade_date)` directly from the CSV (no state-log read needed for the filter's inputs).
3. Looks up the ticker's sector via `tradingagents/paper/sectors.py`.
4. Maps to ETF via `SECTOR_ETF_MAP` (imported from spec 004).
5. Fetches ticker prior-30-trading-day return + ETF prior-30-trading-day return via `returns_from_frames`.
6. Computes the relative-strength delta = ticker_return − etf_return.
7. Reports: at each candidate threshold (+3%, +5%, +7.5%, +10%), how many commits would have fired, what their realized α was (vs SPY at 21d window), what the survivors' realized α was, and the net Δα contribution.
8. Includes a per-sector breakdown.
9. Includes a cross-tab against the cells from `claudedocs/sector-alpha-attribution-2026-05-06.md` (would the filter fire on the n=18 `ticker_strong`-bearish commits identified there? On the n=13 `ticker_weak`-bearish commits — where the bear call worked and the filter SHOULDN'T fire?).

The SC-008 gate: at threshold = +5%, ≥8 of 18 `ticker_strong`-bearish commits should fire (the cohort the spec exists to suppress; ≥44% suppression rate). Net Δα at +5% threshold MUST be positive (sign criterion only; magnitude TBD by retrospective).

**Rationale**:
- Mirrors `scripts/uw_suppression_filter.py` (A3 retrospective), `scripts/contrarian_gate_retrospective.py` (spec 003), `scripts/contrarian_gate_threshold_sweep.py` (spec 003 default-on validation), and `scripts/sector_momentum_retrospective.py` (spec 004) — same offline-replay-against-existing-corpus methodology, $0 LLM cost.
- The candidate-threshold sweep gives the operator data to argue for or against a specific threshold when (eventually) flipping the default to active.
- Per-sector breakdown helps the operator understand where the filter would help (Tech-rally regimes) vs hurt (low-vol periods where ticker-vs-sector divergence is small).
- Cross-tabbing against the ticker_strong / ticker_weak cells from today's sector-α attribution gives a direct interpretability link to the spec's empirical motivation document.

**Alternatives considered**:
- **Live retrospective (re-run propagates with the filter on)** — costs LLM tokens; overkill when the filter's decision is purely deterministic given (ticker, date, threshold).
- **Don't write a retrospective; just unit tests** — wouldn't satisfy SC-008's "validate against today's bear cohort" gate.
- **Reuse `sector_alpha_attribution.py`'s output CSV directly** — viable shortcut but loses the threshold sweep + per-sector + cross-tab structure that operators need for the default-on flip decision.

---

## R-7: SC-008 empirical-validation approach

**Decision**: SC-008 is verified by a SPECIFIC test in the new retrospective script:

```python
def test_today_ticker_strong_bear_cohort_suppression_at_5pct():
    # The 18 ticker_strong-bearish commits identified in
    # claudedocs/sector-alpha-attribution-2026-05-06.md (loaded from the
    # sister CSV at claudedocs/sector-alpha-attribution-2026-05-06.csv).
    cohort = load_ticker_strong_bear_cohort()
    fired = simulate_filter(cohort, threshold=+5.0, lookback=30)
    assert len(fired) >= 8, (
        f"Expected ≥8 of 18 to fire at +5% threshold; got {len(fired)}. "
        f"Verify ticker-vs-sector relative-strength was empirically >5% "
        f"in 30d before each cohort date."
    )
```

This test is `@pytest.mark.integration` (live yfinance dependency) and skipped in unit-only CI runs. It's run manually as part of the spec-006 implementation validation.

**If the test fails on live yfinance data**: the spec's motivating premise ("ticker_strong-bear cohort had ticker-vs-sector relative-strength >5%") doesn't hold for ≥10 of the 18 cohort dates. Two possibilities:
1. **The `ticker_strong` outcome was driven by intra-window news, not pre-trade-date relative-strength** — the filter wouldn't have known at signal-generation time; this is the limit of any look-back filter. Document and either (a) tighten the threshold to a value where ≥8 fire OR (b) accept the filter as default-off operator-opt-in.
2. **The 30d lookback is too short to capture the relative-strength buildup** — try 60d or 90d in the retrospective sweep; flip default lookback if a longer window better separates the cohort.

Either way, surfacing the empirical truth is more valuable than assuming. The test makes the assumption falsifiable.

**Rationale**:
- Concrete test ties the spec's motivating empirical claim to executable verification.
- `@pytest.mark.integration` keeps it out of pre-commit unit-test runs (yfinance is slow + flaky for CI).
- Loading the cohort from the CSV (rather than hardcoding ticker/date pairs) keeps the test forward-compatible if the analyzer is re-run with a larger corpus.

**Alternatives considered**:
- **Soft assertion (just print, don't fail)** — loses the SC-008 gate's integrity.
- **No SC-008 test at all** — leaves the spec's motivating claim unverified; rejected (the +28% mean α is the entire empirical case for spec 006).
- **Hardcode the 18 cohort entries** — rejected for the forward-compatibility reason.

---

## R-8: Module placement (extension vs new module)

**Decision**: New module `tradingagents/agents/utils/bear_sector_symmetry_filter.py`. Mirrors A3's `momentum_filter.py` + spec 004's `sector_momentum_filter.py` placement.

**Rationale**:
- A3 + spec 004 + this spec share the broad shape ("price-condition mean-reversion suppression in PM hook chain") but operate on different inputs (per-ticker absolute / sector-ETF absolute / ticker-vs-sector relative) and emit different annotations. Co-located but separate keeps each module readable.
- Tests already follow the per-module pattern (`tests/test_momentum_filter.py` for A3; `tests/test_sector_momentum_filter.py` for spec 004; `tests/test_bear_sector_symmetry_filter.py` for this).
- Extending `sector_momentum_filter.py` to handle both bull and bear sides would conflate the spec 004 (bull-side ETF-momentum) and spec 006 (bear-side relative-strength) mechanisms in one file — different ratings, different threshold semantics (≤0 vs ≥0), different annotation schemas.
- The new module IMPORTS `SECTOR_ETF_MAP` + `_etf_history` + `clear_etf_cache` from spec 004's module per FR-004. Single source of truth for the sector ETF mapping is preserved.

**Alternatives considered**:
- **Inline in `portfolio_manager.py`** — too much logic in the PM module; rejected for testability.
- **Extend `sector_momentum_filter.py`** — see above; rejected for clarity.
- **Put in `tradingagents/signals/`** — `signals/` is for featurizers + the contrarian gate; agent-stage filters belong in `agents/utils/` per existing convention.

---

## R-9: Lookback boundary handling for ticker + ETF

**Decision**: When EITHER the ticker OR the sector ETF doesn't have ≥30 trading days of prior history available (e.g., for very early dates, edge cases at IPO of an ETF, recently IPO'd tickers), the filter MUST emit the appropriate skip annotation:
- ETF unavailable: `skipped="missing_etf_data"` (matches spec 004's pattern)
- Ticker unavailable: `skipped="missing_ticker_data"` (new reason specific to this spec)

In either case, the rating passes through unchanged.

**Rationale**:
- All 11 SPDR sector ETFs have decades of history (XLK launched 1998); ETF unavailability is rare for any post-1998 trade date.
- Recently IPO'd tickers may not have 30 trading days of prior history (especially in the first few weeks of trading); the filter cannot compute a 30d return for those and degrades cleanly.
- Resilience pattern matches A3's "no data available → no fire" + spec 004's pattern + the broader "filter never breaks PM pipeline" rule (FR-010).

**Alternatives considered**:
- **Use whatever shorter history is available** — would produce inconsistent threshold semantics. Rejected; clarity wins.
- **Conflate both reasons into `"missing_data"`** — loses diagnostic signal; rejected.

---

## R-10: GICS sector name normalization

**Decision**: yfinance reports sectors using its own naming convention (e.g., `"Financial Services"` not `"Financials"`; `"Consumer Cyclical"` not `"Consumer Discretionary"`). The `SECTOR_ETF_MAP` reused from spec 004 already accepts BOTH common variants — no changes to the mapping. Sectors not in the map cause `skipped="no_etf_mapping"`.

**Rationale**:
- Spec 004 already established the dual-key mapping (verified empirically in spec 003.5's validation script). This spec inherits that work unchanged.
- Operators may also encounter analyst tools using the GICS canonical naming when ablating; the dual-key support reduces friction.
- Sectors yfinance might report outside the SPDR universe (e.g., "Crypto" or weird ADR classifications) gracefully degrade.

**Alternatives considered**:
- **Strict GICS only** — fails on yfinance's actual outputs.
- **Strict yfinance only** — fails when operators use GICS naming.
- **Re-define the mapping in this spec's module** — rejected; FR-004 explicitly mandates reuse to prevent drift.

---

## R-11: Disjoint-conditions guard with A3 (SC-009)

**Decision**: SC-009 requires that when A3 has already suppressed a UW/Sell to Hold, this filter no-ops. The implementation already satisfies this via FR-002 (filter only acts on UW/Sell; if rating is already Hold, no-op). No additional code beyond FR-002's standard rating check is needed.

The SC-009 unit test: construct a synthetic scenario where ticker is BOTH down 8% absolute (triggering A3) AND down 3% relative to sector (NOT triggering spec 006). Run both filters in sequence. Verify A3 fired (annotation `fired=True`, post_rating=Hold), spec 006 no-opped (annotation `skipped="rating_not_bearish"` because pre-spec-006 rating is Hold).

**Rationale**:
- Disjoint-conditions guard is structural (rating-set check) not condition-based; the test exercises the structural guarantee.
- The test name + assertion document the expected interaction for future readers.

**Alternatives considered**:
- **Add explicit "skip if A3 already fired" code in spec 006** — redundant with the existing rating-set check; rejected for code minimalism.

---

## R-12: Naming convention (Spec 005 directory vs Spec 006 user-facing)

**Decision**: The spec-kit branch directory is `005-bear-sector-symmetry` (auto-numbered by `create-new-feature.ps1` based on the count of existing `specs/` directories). The user-facing name in CLAUDE.md, RESEARCH_FINDINGS.md, ROADMAP.md, commit messages, and this document is "Spec 006". The two refer to the same feature.

**Rationale**:
- The spec-kit script doesn't know about the user-facing offset (which exists because the project's filter portfolio names start at A3 momentum and span A3 / Spec 003 / Spec 003.5 / Spec 004 / Spec 006 — there's no Spec 005 in the user-facing naming due to a prior planning decision to skip that number).
- The naming offset is a one-time documentation artifact; future specs can either continue the offset or align both numberings, at the operator's discretion when invoking `/speckit.specify`.
- Both names are documented in the spec preamble + CLAUDE.md so readers know they refer to the same thing.

**Alternatives considered**:
- **Rename the directory to `006-bear-sector-symmetry`** — would require manually fighting the spec-kit script + risks confusing future spec-kit invocations. Rejected.
- **Use only "Spec 005" in user-facing docs** — would break the established filter-portfolio numbering convention from CLAUDE.md and today's other docs.

---

## Summary of resolved unknowns

All technical-context items resolved:
- Sector lookup → R-1
- ETF + ticker fetch + caching → R-2
- Threshold semantics → R-3
- Filter ordering → R-4
- Annotation persistence (state-log + AgentState TypedDict) → R-5
- Retrospective script methodology → R-6
- SC-008 empirical-validation approach → R-7
- Module placement → R-8
- Lookback boundary handling → R-9
- Sector name normalization → R-10
- Disjoint-conditions guard with A3 → R-11
- Naming convention (Spec 005 dir vs Spec 006 user-facing) → R-12

No outstanding NEEDS CLARIFICATION. Proceed to Phase 1 (data-model + contracts + quickstart).
