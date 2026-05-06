# Phase 0: Research — Sector-Baseline Fallback

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

Resolves the technical-context decisions surfaced during planning. All NEEDS CLARIFICATION items from `plan.md` are resolved here. Each entry: Decision / Rationale / Alternatives Considered.

---

## R-1: Sector-pool aggregation algorithm

**Decision**: For each evaluation, scan `~/.tradingagents/logs/<ticker>/TradingAgentsStrategy_logs/full_states_log_*.json` for every ticker whose cached sector matches the current ticker's sector. For each state log, recompute `bull_keyword_count(market_report)` using the same featurizer the live gate uses. Filter by date strictly less than the current evaluation date. Aggregate the resulting list into a single pooled distribution; return the count + the values.

**Rationale**:
- Same data path as `scripts/contrarian_gate_retrospective.py` and `scripts/sc003_financials_gate_check.py` — proven working pattern from the empirical investigation that motivated this spec.
- Recomputing `bull_keyword_count` from `market_report` text (rather than reading a cached value) means the feature is portable across any future signal/feature pluggability changes from spec 003 (FR-004 preserved).
- Filtering on filename-encoded date (state-log filename is `full_states_log_<YYYY-MM-DD>.json`) is O(1) per file; no JSON parse needed for the filter step.

**Alternatives considered**:
- **Pre-compute and cache the sector pool** — adds invalidation complexity (when does the cache stale?). Skipped for v1; the spec's Assumptions section explicitly notes cache as a future-spec concern if performance becomes an issue.
- **Read a featurized signal cache (Spec 002 signal lifecycle Phase 0+)** — would be cleaner but couples this feature to Spec 002's signal-cache schema. The state-log scan path works without that dependency.
- **Aggregate via SQL/database** — overkill at the project's scale (≤50 tickers, ≤50 state logs each).

---

## R-2: Strict-prior cutoff handling within a single step

**Decision**: The strict-prior cutoff is computed per evaluation, not per step. When evaluating ticker T on date D, the sector pool excludes ALL state logs dated D or later, INCLUDING any state log written by another ticker in the same sector earlier in the SAME step (i.e., in the current `daily_signals.py` invocation).

**Rationale**:
- Spec 003 already enforces strict-prior on the per-ticker baseline (FR-004 + retrospective scripts use date < current_date filter).
- Within-step pooling of same-day observations would introduce circular dependency: ticker A's gate decision would depend on ticker B's market report from the same step, and vice versa. Order-dependent and invalid.
- Filtering by filename-date is sufficient: state logs are written at the END of each propagate, after the gate has fired. Same-step state logs all share the same filename date and are excluded by the < cutoff.

**Alternatives considered**:
- **Within-step pooling** — order-dependent, breaks reproducibility (FR-009 / SC-004), violates strict-prior. Rejected.
- **Per-step cutoff that includes some same-day observations** — too clever, not necessary, adds complexity.

---

## R-3: Performance budget for the aggregator

**Decision**: 200ms budget per evaluation. Achieved by:
- O(1) filesystem `glob()` per same-sector ticker (typical: 5-15 tickers per sector at the operator's scale)
- O(N_state_logs) JSON parses + `bull_keyword_count` calls per ticker (typical: 5-50 per ticker)
- Total expected work per evaluation: ~50-750 JSON parses, fitting in well under 200ms on a modern SSD

**Rationale**:
- The contrarian gate runs once per `propagate()` (which itself is ~5-10 minutes of LLM time per ticker). 200ms is invisibly small in that budget.
- No need for caching at v1 scale. If state-log directories grow into the thousands per ticker (years of daily ops), revisit.
- Sector-membership lookups via `tradingagents/paper/sectors.py` are already O(1) cache hits per the Spec 002 design.

**Alternatives considered**:
- **Persistent on-disk cache** — invalidation pain, premature optimization at current scale.
- **Lazy in-process LRU cache keyed by (sector, before_date)** — useful if multiple evaluations in the same process hit the same sector, but daily_signals.py runs one ticker at a time and creates a new gate per call. Defer.

---

## R-4: "Unknown" sector handling

**Decision**: When `tradingagents/paper/sectors.py::get_sector` returns `"Unknown"` for the current ticker, the sector-baseline aggregator returns `(0, [])` — no pool. The fallback ladder then sees count=0 < FR-003 floor and falls through to `gate_baseline = "none"` (gate doesn't fire).

**Rationale**:
- Pooling all `"Unknown"`-sector tickers together would produce a meaningless distribution (no shared sector dynamics).
- Operators get a clear annotation (`gate_baseline = "none"`) rather than a silent miss.
- Matches the spec's edge-case section directly.

**Alternatives considered**:
- **Pool all `"Unknown"`-sector tickers** — Spec 002's sectors.py already has `"Unknown"` as a defensive fallback for delisted/unrecognized tickers; pooling them creates a "junk drawer" baseline. Rejected.
- **Skip the gate entirely for `"Unknown"`-sector tickers** — would lose visibility; the `"none"` annotation is more informative.

---

## R-5: Ablation flag default

**Decision**: `contrarian_gate_sector_fallback_enabled` defaults to `True`. Settable to `False` for ablation experiments per Constitution Principle II.

**Rationale**:
- The empirical motivation (SC-003 Financials investigation) showed cold-start tickers get ZERO gate value under spec 003. Default-on closes that gap immediately for any new operator universe.
- The fallback is strictly additive on the cold-start path; it does NOT change spec 003's per-ticker semantics on thick-history tickers (SC-002 byte-identity). So default-on doesn't risk regressing existing behavior.
- Default-off would be defensive but means cold-start universes see no benefit unless the operator opts in — which they probably don't know to do.
- Future ablation experiments that want to compare spec 003 vs spec 003+sector can flip the flag in `PARAMS.json`.

**Alternatives considered**:
- **Default False (opt-in)** — discoverability problem; cold-start operators don't know to enable.
- **No flag, always on** — violates Constitution II's "vary one knob" pattern; future ablation requires code change.

---

## R-6: Annotation backward compatibility

**Decision**: Add `gate_baseline`, `n_history_per_ticker`, `n_history_sector` fields ADDITIVELY to the existing spec 003 annotation dict. Existing fields (`mode`, `feature_value`, `percentile`, `n_history`, `would_fire`, `gate_fired`, `pm_rating_pre_gate`, `pm_rating_post_gate`) are unchanged. Existing consumers (e.g., `scripts/contrarian_gate_retrospective.py`) remain forward-compatible — they simply ignore the new fields.

**Rationale**:
- Additive schema changes don't break consumers.
- The existing `n_history` field becomes ambiguous (does it mean per-ticker or sector?) — resolve by KEEPING `n_history` as an alias for whichever baseline fired (per-ticker if `gate_baseline=="per_ticker"`, sector if `"sector"`, 0 if `"none"`), and add the explicit `n_history_per_ticker` + `n_history_sector` for unambiguous audit.
- The sector-fallback test corpus (sc003_financials_gate_check.py) provides a regression-checkable comparison against the per-ticker-only spec 003 behavior.

**Alternatives considered**:
- **Replace `n_history` with `n_history_per_ticker` + `n_history_sector`** — breaks existing consumers; rejected.
- **Add a fully-versioned annotation schema** — overkill; additive change is sufficient.

---

## R-7: Sector-pool minimum-diversity requirement

**Decision**: No minimum-diversity requirement in v1. A sector pool with 50 observations all from one ticker counts the same as a pool with 50 observations from 5 tickers. Operators trust that the dominant ticker's history represents sector dynamics; a future variant can add a `≥3 distinct contributors` rule if empirically motivated.

**Rationale**:
- Spec edge-case section explicitly notes this as v1 behavior.
- Single-ticker-dominated pools are MORE common in early-life portfolios (NVDA dominates Tech in the current corpus). Refusing to fire because the pool isn't diverse enough would defeat the cold-start-coverage purpose.
- Future investigation: if SC-001 reproduction shows single-ticker-dominated pools produce systematically wrong fires, add the diversity rule then.

**Alternatives considered**:
- **Require ≥3 distinct ticker contributors** — premature; no empirical motivation yet.
- **Weight pool members by 1/N_per_ticker** to dampen single-ticker dominance — too clever for v1.

---

## R-8: Module placement (extension vs new module)

**Decision**: Create a new `tradingagents/signals/sector_baseline.py` module for the pool aggregator. The existing `contrarian_gate.py` imports from it and uses it in the fallback path.

**Rationale**:
- Separation of concerns: `contrarian_gate.py` stays focused on the gate's evaluation/annotation logic; `sector_baseline.py` owns the pool aggregation.
- Sector-pool aggregation is a reusable concept — future features (e.g., a sector-momentum filter) might want the same pool aggregation primitive.
- Easier to test in isolation (test the pool aggregator with synthetic state logs without instantiating the gate).

**Alternatives considered**:
- **Inline in `contrarian_gate.py`** — fine for ~50 LOC of aggregator logic but couples it to gate state; rejected for testability.
- **Put in `tradingagents/paper/sectors.py`** — the sector cache module shouldn't be growing aggregation logic. Keep that module focused.

---

## R-9: Test corpus for SC-002 regression-guard

**Decision**: SC-002 (byte-identical decisions on thick-history tickers) is verified by an integration test that:
1. Loads the existing spec 003 retrospective output (hand-curated test fixtures or `claudedocs/contrarian-gate-retrospective-2026-05-05.md` data)
2. Runs both the spec 003 gate (with `contrarian_gate_sector_fallback_enabled=False`) and the new gate (with `True`) over the same N≥20 history corpus
3. Asserts byte-identical `gate_fired` decisions between the two runs

**Rationale**:
- The SC-002 invariant is the central regression-guard: this feature must NOT change behavior on tickers where spec 003 already worked.
- The flag-off path is the cleanest way to compare — no need to monkey-patch sector lookups; just disable the fallback and let the existing per-ticker path run.
- Marking as `integration` (not `unit`) is appropriate because it touches real state logs.

**Alternatives considered**:
- **Pure-unit comparison via mocked sector lookups** — would test the same thing but less convincingly. The integration test catches accidental regressions in the actual data path.
- **No regression test** — unacceptable; SC-002 is load-bearing.

---

## R-10: Sector-pool source — paper-trading sectors cache vs computed on-demand

**Decision**: Use `tradingagents/paper/sectors.py::get_sector(ticker, cache_path)` as the canonical sector-membership lookup. The cache lives at `<paper_state_dir>/sectors.json` per Spec 002 (default `~/.tradingagents/paper/sectors.json`).

**Rationale**:
- Spec 002 already established this path for the paper-trading harness; reusing it avoids creating a parallel sector cache.
- `get_sector` already handles the `"Unknown"` fallback and yfinance lookup gracefully.
- If `paper_state_dir` doesn't exist (operator hasn't run paper_trade yet), `get_sector` will create the directory + populate the cache as a side effect — same as Spec 002 behavior. No change needed.

**Alternatives considered**:
- **Build a parallel sector cache** — duplicates work, risks divergence. Rejected.
- **Hardcode sector mappings** — won't scale to new tickers, requires manual maintenance.

---

## Summary of resolved unknowns

All technical-context items in `plan.md` resolved:
- Aggregator algorithm → R-1
- Strict-prior within step → R-2
- Performance budget → R-3
- "Unknown" sector handling → R-4
- Ablation flag default → R-5
- Annotation backward compat → R-6
- Diversity requirement → R-7
- Module placement → R-8
- Regression-guard test approach → R-9
- Sector lookup source → R-10

No outstanding NEEDS CLARIFICATION. Proceed to Phase 1 (data-model + contracts + quickstart).
