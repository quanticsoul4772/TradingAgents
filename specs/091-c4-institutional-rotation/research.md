# Phase 0 Research: C-4 Institutional Rotation Filter (Spec X-1)

**Branch**: `091-c4-institutional-rotation` | **Date**: 2026-05-07
**Source**: spec.md + Technical Context section of plan.md

## Purpose

Resolve any NEEDS CLARIFICATION items from Technical Context, document
decisions for non-trivial technical choices, and reference the empirical
evidence base + reusable patterns.

No NEEDS CLARIFICATION markers remain in spec.md or plan.md (all
required values are concrete: Python 3.10, yfinance, pytest, etc.).
Research below documents key technical decisions for traceability.

## Decision 1: yfinance.institutional_holders as the data source

**Decision**: Use `yfinance.Ticker(ticker).institutional_holders` to
fetch the top 10 institutional holders' DataFrame. Aggregate the
`pctChange` column via `fillna(0).sum()` to produce `net_rotation`.

**Rationale**:

- This is the EXACT data source used by both retrospective scripts
  (`scripts/forward_catalyst_class4_retrospective.py` PR #75 and
  `scripts/forward_catalyst_class4_vs_spec007_overlap.py` PR #77)
  that produced the empirical evidence justifying this spec.
- Single-source-of-truth principle: the production module MUST use
  the same data shape + aggregation as the retrospective scripts to
  ensure the +5.41pp / +8.06pp Δα claims are reproducible in
  production.
- yfinance is already a project dependency (no new packages).
- Free data source — Constitution III T0 classification.

**Alternatives considered**:

- **Direct SEC EDGAR API**: Would offer historical 13F panels (yfinance
  only exposes current snapshot). Rejected for v1 because the
  retrospective evidence base used yfinance; switching data source for
  production would invalidate the empirical justification.
- **Alpha Vantage / Polygon institutional data**: Would require new
  API key + paid subscription. Rejected per Constitution III.

## Decision 2: LRU cache (maxsize=128) at process scope

**Decision**: Use `functools.lru_cache(maxsize=128)` on the
`_fetch_institutional_rotation(ticker)` function. Cache lifetime is
process-scoped (resets on process restart).

**Rationale**:

- yfinance fetches add ~50-200ms latency per call; multiple propagates
  of the same ticker (e.g., `daily_signals.py` over a watchlist) would
  redundantly fetch.
- maxsize=128 covers any realistic ticker universe (typical operator
  watchlist is 5-50 tickers; SC-003 50-ticker validation was the
  largest single-process workload to date).
- Process-scoped lifetime is correct: institutional_holders data is
  daily-stable; per-process caching avoids stale-data risk across
  process boundaries (operator restarts pick up fresh data).
- Mirrors the same LRU pattern used by `_fetch_institutional_rotation`
  in `scripts/forward_catalyst_class4_retrospective.py` (single source
  of truth for fetch semantics).

**Alternatives considered**:

- **Persistent disk cache**: Would survive process restarts but
  introduces stale-data risk + filesystem dependency. Rejected as
  overkill for the use case.
- **No cache (re-fetch every call)**: Would multiply latency by N for
  N propagates of same ticker. Rejected on operator-experience grounds.
- **Cache lifetime TTL**: Would require a more complex cache (cachetools
  TTLCache); the process-scoped lifetime achieves the same correctness
  with simpler code.

## Decision 3: Strict less-than threshold semantics

**Decision**: Filter fires when `net_rotation < -threshold` (strict
less-than; equality boundary does NOT fire).

**Rationale**:

- Symmetry with Spec 007 SC-002 boundary discipline (`bull_score >
  T_bull` is strict greater-than).
- Boundary cases at exactly -threshold are inherently ambiguous; strict
  semantics resolves the ambiguity deterministically.
- FR-005 + SC-002 both codify this rule.

**Alternatives considered**:

- **Inclusive less-than-or-equal**: Would fire on the exact boundary.
  Rejected for asymmetry with Spec 007.

## Decision 4: Filter ordering — appended LAST in FR-012 chain

**Decision**: C-4 filter runs LAST in the PM-stage chain:
A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → **spec X-1**.

**Rationale**:

- Sample-size discipline: C-4 has the smallest evidence base (n=12)
  in the filter portfolio. Running last means upstream filters with
  larger evidence bases (Spec 003 N≥20 floor, Spec 007 n=33 bull
  fires) decide first.
- C-4 fires only when pre_rating ∈ {Underweight, Sell}. If an upstream
  filter already suppressed to Hold, C-4's check is a no-op (the
  `pre_rating ∈ bearish` precondition fails). No interference with
  upstream decisions.
- The reverse ordering (C-4 before Spec 007) was considered but
  rejected because Spec 007 has stronger evidence + may need to fire
  on the same row (unrelated bull-side suppression). Last position
  preserves Spec 007's existing behavior unchanged.

**Alternatives considered**:

- **C-4 before Spec 007**: Rejected per sample-size discipline.
- **C-4 inserted between Spec 003 and Spec 004**: Mixed-evidence
  ordering with no principled justification; rejected.

## Decision 5: Default modes — bear=shadow, bull=off

**Decision**: `institutional_rotation_bear_mode` defaults to `"shadow"`;
`institutional_rotation_bull_mode` defaults to `"off"`.

**Rationale**:

- **Bear=shadow**: Constitution VIII v1.4.0 small-sample-caution
  sub-clause applies (n=12 bear-side cohort is small; default-shadow
  is the conservative position pending live-mode A/B ablation per
  SC-010). The PR #75 bull-side n=1 was too thin to constitute a
  default-active justification.
- **Bull=off**: Even shadow-mode would require some non-trivial
  empirical basis; n=1 is insufficient. Setting to "off" prevents
  yfinance overhead + state annotation noise for an unsupported
  direction.

**Alternatives considered**:

- **Bear=active by default**: Would skip the shadow-mode-first pattern.
  Rejected per VIII v1.4.0 small-sample caution.
- **Bear=off, bull=off (full opt-in)**: Would require operators to
  flip both per filter use. Rejected because the bear-side evidence is
  strong enough for default-shadow per the VIII v1.4.0 + v1.4.3
  combined gate clearance.
- **Bull=shadow with n=1**: Rejected; shadow mode with insufficient
  evidence base would create noise without informational value.

## Decision 6: State annotation as sub-dict of forward_catalyst

**Decision**: New annotation lives at
`state["forward_catalyst"]["institutional_rotation"]` (sub-dict of the
existing Spec 007 annotation).

**Rationale**:

- Per spec 003 / 004 / 006 / 007 / 008 precedent: each filter's
  annotation is a sub-dict of `state["forward_catalyst"]`. C-4
  follows the same pattern.
- The `forward_catalyst` field is already declared in AgentState
  TypedDict (per Spec 007). No schema changes needed.
- Already on the `_log_state` whitelist; no new persistence wiring.
- Sub-dict approach (vs new top-level field) preserves the conceptual
  grouping: forward-catalyst-class filters all live under the
  `forward_catalyst` umbrella.

**Alternatives considered**:

- **New top-level field `state["institutional_rotation"]`**: Would
  require AgentState schema change + `_log_state` whitelist update.
  Rejected as unnecessary schema churn.
- **Inline in `state["forward_catalyst"]`** (no sub-dict): Would
  collide with existing Spec 007 / Spec 008 fields. Rejected.

## Decision 7: 8-field annotation schema

**Decision**: When mode is non-off, the sub-dict contains 8 fields:

| Field | Type | Purpose |
|---|---|---|
| `net_rotation_pct` | float \| None | Aggregate from yfinance fetch |
| `outflow_threshold` | float | Configured threshold value |
| `bear_mode` | Literal["off","shadow","active"] | Active config |
| `bull_mode` | Literal["off","shadow","active"] | Active config |
| `would_fire_bear` | bool | Suppression conditions met (regardless of mode) |
| `fired_bear` | bool | True only in active mode + conditions met |
| `pre_rating` | str | Rating before filter applied |
| `post_rating` | str | Rating after filter applied (= pre_rating in shadow) |

**Rationale**:

- Mirrors Spec 007 annotation field count (16 fields) but smaller because
  C-4 is bear-only at v1 + has fewer mechanism-class parameters.
- Pre/post rating fields enable post-hoc auditing of which suppressions
  the filter actually performed vs would have performed.
- Mode fields capture the operational policy at fire time (operators
  may flip modes between propagates).
- All 8 fields are CSV-friendly types for downstream analyzer scripts.

**Alternatives considered**:

- **Smaller schema (5 fields)**: Drop bull_mode + threshold + post_rating.
  Rejected because the dropped fields are useful for retrospective
  analysis (e.g., "which threshold was active at time of fire").
- **Larger schema (mirror Spec 007's 16)**: Would add bull-side fields
  that are unused in v1. Rejected as scope creep.

## Decision 8: Test count and structure

**Decision**: ~14 unit tests in `tests/test_institutional_rotation_filter.py`
+ 4 integration tests in `tests/test_institutional_rotation_pm_integration.py`.

Unit tests cover (target shape):

1. `_fetch_institutional_rotation` happy path (mocked yfinance)
2. `_fetch_institutional_rotation` returns None on yfinance None
3. `_fetch_institutional_rotation` returns None on yfinance empty DataFrame
4. `_fetch_institutional_rotation` returns None on missing pctChange column
5. `_fetch_institutional_rotation` returns None on yfinance raised exception
6. `_fetch_institutional_rotation` LRU cache hit on second call
7. `_fetch_institutional_rotation` handles NaN pctChange via fillna(0)
8. `should_suppress_bear` returns True when net_rotation < -threshold
9. `should_suppress_bear` returns False when net_rotation == -threshold (boundary)
10. `should_suppress_bear` returns False when net_rotation > -threshold
11. `should_suppress_bear` returns False when net_rotation is None
12. `apply_filter` builds annotation dict correctly in active mode
13. `apply_filter` builds annotation dict correctly in shadow mode
14. `apply_filter` does NOT add annotation when both modes are off

Integration tests cover:

1. PM-hook with bear_mode=off + bull_mode=off → no annotation in state log + no yfinance call
2. PM-hook with bear_mode=shadow + cohort conditions met → would_fire_bear=True + fired_bear=False + post_rating == pre_rating
3. PM-hook with bear_mode=active + cohort conditions met → fired_bear=True + post_rating="Hold"
4. PM-hook with bear_mode=active + yfinance raises exception → graceful degradation, no fire, propagate completes

**Rationale**:

- 14 unit tests covers all 12 SCs at the unit level + the FR-005 boundary semantics + FR-002 NaN handling.
- 4 integration tests cover SC-005 (mode integrity), SC-006 (shadow vs active), SC-008 (pre/post rating), and SC-003 (yfinance failure resilience) at the PM-hook level.
- Mirrors Spec 007 + Spec 008 test ratio (~12 unit + 4 integration).

**Alternatives considered**:

- **Fewer unit tests (8-10)**: Would drop boundary + NaN coverage.
  Rejected as inadequate for SC-001 + SC-002.
- **More PM integration tests**: Would duplicate Spec 007 chain
  ordering tests. Rejected because chain ordering is already validated
  upstream.

## Empirical evidence references

- `claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` —
  PR #75 standalone retrospective (verdict: PASS at n=12)
- `claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md` —
  PR #77 additive overlap (verdict: PASS on 2 of 3 v1.4.3 criteria)
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` —
  PR #78 bear-side mechanism survey (C-4 SOLE spec-eligible)
- `scripts/forward_catalyst_class4_retrospective.py` — re-runnable
  standalone-gate harness (canonical reference for `_fetch_institutional_rotation` semantics)
- `scripts/forward_catalyst_class4_vs_spec007_overlap.py` — re-runnable
  additive-gate harness

## Pattern-reuse references

- `tradingagents/agents/utils/forward_catalyst_filter.py` (Spec 007) —
  precedent for: PM-hook structure, state["forward_catalyst"] annotation
  pattern, Literal["off","shadow","active"] mode field, would_fire/fired
  boolean pair, graceful degradation on data failure
- `tradingagents/agents/utils/calendar_boost.py` (Spec 008) — precedent
  for: small helper module (~80 LOC), LRU cache for free-data-source
  fetches, sub-dict extension of `state["forward_catalyst"]`
- `tradingagents/agents/utils/momentum_filter.py` (Spec A3) — precedent
  for: pre_rating/post_rating annotation pattern
- `specs/006-forward-catalyst-gate/` (Spec 007) — precedent for: spec
  + plan + research + data-model + quickstart bundle structure

No NEEDS CLARIFICATION items remain. Ready for Phase 1.
