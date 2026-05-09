# Feature Specification: Class 4 Macro-Environment Filter (Spec 012)

**Feature Branch**: `012-class-4-macro-filter`
**Created**: 2026-05-09
**Status**: **CONDITIONAL DRAFT** — initial activation conditional on operator deployment cadence; 2 verdict-conditional default-mode branches scaffolded below.
**Predecessors**:
- `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193 — retrospective PASSED at v1.4.0 + v1.4.3 gates)
- `claudedocs/sector-alpha-attribution-2026-05-06.md` (cohort identification: 22-row bear ticker_strong)
- `tradingagents/agents/utils/momentum_filter.py` (A3 — only existing default-active bear filter; mechanism-disjoint with Class 4)
- `.specify/memory/constitution.md` v1.5.2 Principle VIII (v1.4.0 standalone gate + v1.4.3 additive gate; both PASSED in retrospective)

## Naming clarification

This is **Spec 012** (user-facing) = Class 4 from Spec 008 design doc mechanism classification (cross-asset/macro). NOT to be confused with **C-4** institutional rotation from the bear-side mechanism survey numbering, which became Spec X-1 (`specs/091-c4-institutional-rotation/`).

## Why this spec exists

The Class 4 retrospective (PR #193) showed that VIX-based macro features identify a 22-row bear ticker_strong cohort (mean realized α-vs-SPY = +32.64% — anti-calibration shock) that **A3 momentum filter misses by construction** (A3 fires on per-ticker DOWN absolute mean-reversion; ticker_strong cohort has ticker UP relative to sector AND UP vs SPY). Mechanism-disjointness yields v1.4.3 additive PASS at +24.07pp vs A3 alone.

This is the **FIRST macro-environment-aware filter** in the framework, distinct from per-ticker price (A3) / per-sector (Spec 004/006) / prose-density (Spec 003) / LLM-extracted (Spec 007/008) / institutional flow (Spec X-1).

## Verdict-conditional default-mode branches

### Branch A — default-SHADOW (recommended at this evidence level)

**Trigger**: this is the recommended default per Constitution VIII v1.4.0 small-sample-caution sub-clause. Retrospective n=8 fires at recommended threshold (VIX < 18) is at the lower bound of statistical confidence. Shadow-mode-first launch matches the precedent set by Spec 007 bear (PR #76).

**Deployment**: `class_4_macro_bear_mode = "shadow"` default. Filter computes the fire decision + records it in state but does NOT modify the rating. Operators inspect state logs to verify the filter behaves as expected on real propagates.

**Default-on flip path**: after 30+ live shadow-mode fires accumulate (per Constitution VIII v1.4.0 shadow-mode-first sub-clause), a follow-up ablation can validate the default-on flip via PR amendment to this spec.

#### User Story A.1 — Operator runs propagates with Class 4 in shadow (Priority: P1)

**As an** operator running the daily signals workflow
**I want to** see when Class 4 would have suppressed my bear commits without it actually firing
**So that** I can validate the filter empirically before activating it

**Acceptance criteria**:
- New PARAMS.json key `class_4_macro_bear_mode = "shadow"` (default)
- When in shadow mode + a bear commit (UW or Sell pre_rating): filter fetches macro snapshot via yfinance + computes fire decision; records in `state["class_4_macro"]` dict with would_fire boolean + macro feature values
- Filter does NOT modify pre_rating in shadow mode
- State log has 7 fields: `vix_snapshot`, `vix_30d_pct`, `tnx_30d_pct`, `dxy_30d_pct`, `would_fire_bear`, `fired_bear`, `pre_rating`, `post_rating` (where `fired_bear=False` and `post_rating=pre_rating` in shadow mode)

#### User Story A.2 — Researcher reviews shadow-mode fire log (Priority: P2)

**As a** researcher investigating Class 4 effectiveness
**I want to** walk state logs to count shadow-mode would-fire instances + check against realized α
**So that** I can build the n≥30 evidence base needed for default-on flip per Constitution VIII v1.4.0

**Acceptance criteria**:
- New script `scripts/class4_macro_shadow_audit.py` walks state logs + outputs would-fire enumeration + realized α
- After 30+ would-fire instances accumulate, script outputs default-on-flip-readiness report

### Branch B — default-ACTIVE (after live-mode evidence)

**Trigger**: 30+ live shadow-mode fires accumulate AND ablation re-validates the retrospective Δα ≥ +0.5pp at 21-day forward-alpha horizon AND cohort hit ≥ 40%.

**Deployment**: `class_4_macro_bear_mode = "active"` default. Filter actively suppresses bear commits when the macro environment indicates risk-on (VIX < threshold).

**Spec amendment path**: a PR-level amendment to this spec.md flips the default + cites the live-mode ablation evidence (analogous to Spec 003 / Spec 007 bull mode flips that landed via separate PRs after their respective retrospectives + live evidence).

#### User Story B.1 — Operator runs propagates with Class 4 active (Priority: P1)

**As an** operator
**I want to** have bear commits automatically suppressed when macro environment is risk-on
**So that** the framework's bear-side anti-calibration is mitigated without operator intervention

**Acceptance criteria**:
- `class_4_macro_bear_mode = "active"` (after Branch A → B transition)
- When active mode + bear commit + VIX < threshold: filter sets `post_rating = "Hold"` (suppress to Hold)
- State log records `fired_bear=True` + pre/post rating change

## Functional Requirements

### FR-001 — Default off / shadow / active modes

The `class_4_macro_bear_mode` config key MUST be a Literal["off", "shadow", "active"] with default "shadow" per Branch A. Operator can override via PARAMS.json or DEFAULT_CONFIG.

### FR-002 — VIX snapshot threshold

The `class_4_macro_vix_threshold` config key MUST be a float (default 18.0) representing the VIX-snapshot threshold below which a bear commit triggers fire decision. Per the retrospective, VIX < 18 yields n=8 fires + 75% cohort hit + +24.07pp Δα.

### FR-003 — yfinance macro source

The filter MUST source VIX via `yf.Ticker("^VIX").history()` with snapshot = latest close ≤ trade_date. LRU cache by trade_date keyed in-process per FR-006 below.

### FR-004 — Filter ordering in PM hook chain

The filter MUST run AFTER A3 (existing default-active bear filter) and BEFORE Spec X-1 institutional rotation (default-shadow bear). Per CLAUDE.md filter-portfolio section's "smallest-sample last" ordering rule, Class 4 (n=8 cohort) sits between A3 (n=43 cohort) and Spec X-1 (n=12 cohort) in sample-size order.

### FR-005 — Bull-side scope deferred

The filter MUST NOT modify bullish commits (Buy or Overweight pre_rating). Bull-side macro filter is a separate question (would test "bullish commit when VIX rising fast" cohort); not addressed in this spec. `class_4_macro_bull_mode` config key is reserved but defaults "off" + spec leaves bull-side unimplemented.

### FR-006 — In-process LRU caching

The filter MUST cache `yf.Ticker("^VIX").history()` results via in-process LRU keyed by trade_date. Cache scope is process lifetime (no persistence across runs). Same pattern as Spec 008 calendar boost FR-006.

### FR-007 — yfinance failure resilience

When yfinance fetch raises OR returns empty data: filter MUST gracefully degrade (`vix_snapshot = None`, `would_fire_bear = False`, `fired_bear = False`). MUST NOT raise OR log at ERROR level. DEBUG level acceptable.

### FR-008 — State annotation completeness

When the filter is enabled (shadow or active) AND applies to a bear commit, `state["class_4_macro"]` MUST contain exactly 7 fields: `vix_snapshot`, `vix_30d_pct`, `tnx_30d_pct`, `dxy_30d_pct`, `would_fire_bear`, `fired_bear`, `pre_rating`, `post_rating`. Verified by state-log persistence regression test.

### FR-009 — AgentState TypedDict declaration

The new `class_4_macro` state field MUST be declared in `tradingagents/agents/utils/agent_states.py` AgentState TypedDict per the precedent set by Spec 003 (silent-drop bug) + Spec 007 + Spec X-1.

### FR-010 — Config keys default values

| Key | Type | Default | Notes |
|---|---|---|---|
| `class_4_macro_bear_mode` | Literal["off", "shadow", "active"] | "shadow" | Branch A initial |
| `class_4_macro_bull_mode` | Literal["off", "shadow", "active"] | "off" | Bull-side deferred |
| `class_4_macro_vix_threshold` | float | 18.0 | Per retrospective recommended default |

## Success Criteria

- **SC-001 (Module presence)**: `tradingagents/agents/utils/macro_environment_filter.py` ships with `maybe_suppress_bear_macro()` function. Verified by import test.
- **SC-002 (Default mode)**: `class_4_macro_bear_mode` defaults to "shadow" in DEFAULT_CONFIG. Verified by config-snapshot test.
- **SC-003 (PM hook integration)**: `tradingagents/agents/managers/portfolio_manager.py` invokes the filter in the right hook position (between A3 and Spec X-1) when bear_mode is "shadow" or "active". Verified by PM integration test.
- **SC-004 (State annotation persistence)**: state log includes `class_4_macro` dict with 7 fields after a bear-pre commit. Verified by state-log regression test.
- **SC-005 (Shadow mode no-modification)**: `class_4_macro_bear_mode = "shadow"` AND a fire condition met → `post_rating = pre_rating` (no modification). Verified by integration test.
- **SC-006 (Active mode suppression)**: `class_4_macro_bear_mode = "active"` AND a fire condition met → `post_rating = "Hold"` (suppress). Verified by integration test.
- **SC-007 (yfinance failure graceful)**: when yfinance raises, filter does NOT raise + records `would_fire_bear=False` + `vix_snapshot=None`. Verified by mocked failure test.
- **SC-008 (Cost discipline)**: per-propagate LLM cost addition = $0 (filter is pure yfinance + arithmetic). Verified by manual smoke; same pattern as A3 + Spec X-1.
- **SC-009 (Latency budget)**: per-propagate latency p99 ≤ 250 ms cache-cold (single yfinance fetch); ≤ 5 ms cache-warm. Same budget as Spec 008.
- **SC-010 (Default-on flip evidence requirement)**: before any future change flips `class_4_macro_bear_mode` default to `"active"`, operators MUST run a live-mode ablation for n ≥ 30 shadow-mode fires AND verify retrospective +24.07pp Δα holds within ±5pp at the 21-day horizon. Enforced procedurally.
- **SC-011 (Test count expectation)**: spec ships ≥10 unit tests covering helper module + threshold edge cases + yfinance failure + LRU cache; ≥3 PM integration tests (off / shadow / active modes); ≥2 state-log regression tests.

## Out of scope (v1)

- **Bull-side activation**: `class_4_macro_bull_mode` is reserved but defaults "off"; bull-side macro filter is a separate spec.
- **Sector ETF correlation features**: the retrospective discriminator was VIX-30d-Δ% alone; sector correlation features deferred to v2 if needed.
- **10y yield + DXY USD threshold-gating**: retrospective showed these don't discriminate (Δ ≈ 0); deferred.
- **Auto-detection of bear regime via VIX 30d Δ%**: the discriminator in the retrospective; deferred to v2 amendment if VIX-snapshot alone proves insufficient.
- **Persisting LRU cache across runs**: in-process cache sufficient for batch + daily-signals use cases.

## Operational characteristics

- **Cost**: $0 per propagate (yfinance + arithmetic; no LLM call).
- **Latency**: per FR-006 + SC-009 — cache-warm ~5ms, cache-cold ~100-250ms (yfinance HTTP fetch).
- **Failure mode**: yfinance unreachable → graceful degradation (no fire; same as cache-empty).
- **Memory log impact**: none (filter operates pre-PM commit; doesn't write to memory).

## Spec-kit bundle plan (per Spec 011 6-PR pattern)

1. **PR #X+0** — spec.md (this PR)
2. **PR #X+1** — plan.md (this PR also)
3. **PR #X+2** — tasks.md
4. **PR #X+3** — MVP implementation
5. **PR #X+4** — tests
6. **PR #X+5** — polish + per-spec retrospective markdown citing the 2026-05-09 retrospective + integration into RESEARCH_FINDINGS

This PR ships PR #X+0 + PR #X+1 (spec.md + plan.md) per the conditional-branch pattern (PR #151) — PRs #X+2 through #X+5 deferred to a future session per cost-discipline (the retrospective already established the mechanism; spec drafting is the operational completeness step).

## Test plan (for the spec itself, not code)

- [x] Both deployment branches scaffolded with concrete trigger criteria
- [x] FR-001 through FR-010 cover all branches consistently
- [x] Constitution v1.5.2 alignment explicit (PRINCIPLE VIII v1.4.0 + v1.4.3)
- [x] FR-004 hook ordering rationale documented (smallest-sample-last)
- [x] FR-005 bull-side scope explicitly deferred

## Cross-references

- `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193 — retrospective verdict)
- `claudedocs/sector-alpha-attribution-2026-05-06.md` (cohort identification)
- `tradingagents/agents/utils/momentum_filter.py` (A3 — sister bear-side filter; mechanism-disjoint per retrospective)
- `tradingagents/agents/utils/institutional_rotation_filter.py` (Spec X-1 — bear-side default-shadow)
- `specs/007-calendar-boost-filter/spec.md` (Spec 008 — yfinance LRU cache pattern + SC-009 ablation precedent)
- `specs/006-forward-catalyst-gate/spec.md` (Spec 007 — shadow-mode-first launch precedent)
- `specs/091-c4-institutional-rotation/spec.md` (Spec X-1 — small-sample-caution precedent)
- `.specify/memory/constitution.md` v1.5.2 Principle VIII v1.4.0 + v1.4.3
- Memory: `reference_conditional_branch_spec_pattern.md` (PR #151 — pattern this spec follows)
