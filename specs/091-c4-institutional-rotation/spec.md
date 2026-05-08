# Feature Specification: C-4 Institutional Rotation Filter (Spec X-1)

**Feature Branch**: `091-c4-institutional-rotation`
**Created**: 2026-05-07
**Status**: Draft
**Input**: User description (excerpted): "Spec X-1 — C-4 Institutional Rotation Filter. FIRST quantitative-flow bear-side filter — fundamentally different mechanism class from the 5 prose-density / LLM-extracted / backward-price / calendar-boost filters in the existing portfolio. Suppresses Underweight/Sell commits to Hold when top 10 institutional holders' net rotation is below a configurable outflow threshold."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bear-side commit suppression on institutional outflow signal (Priority: P1)

An operator runs `tradingagents analyze` (or programmatic `propagate(ticker, date)`) on a ticker where the framework's pre-filter rating is Underweight or Sell. The C-4 filter checks the top 10 institutional holders' net pctChange rotation. When net rotation is more negative than a configured outflow threshold (e.g., institutions have collectively rotated out by more than 5% of their prior pctHeld), the filter suppresses the bearish commit to Hold. The operator sees the suppression annotation in state logs and can audit the decision via persisted fields.

**Why this priority**: This is the core feature. The empirical evidence (PR #75 standalone n=12, +5.41pp net Δα; PR #77 additive +8.06pp Δα improvement vs Spec 007 bear union) is exclusively about bear-side suppression. Without this user story, the filter is non-functional.

**Independent Test**: Run `propagate("AMD", "2026-04-24")` (or any ticker where the retrospective recorded an institutional outflow) with the filter active. Verify state log contains `state["forward_catalyst"]["institutional_rotation"]` with `fired_bear=True`, `pre_rating="Underweight"` (or Sell), `post_rating="Hold"`, and `net_rotation_pct < -threshold`. Verify the rendered Portfolio Manager output shows Hold instead of the original bearish rating.

**Acceptance Scenarios**:

1. **Given** a ticker whose top 10 institutional holders show net pctChange = -8.0% (below -5% outflow threshold), and the framework's pre-filter rating is Underweight, **When** the operator invokes propagate with active mode, **Then** the post-filter rating is Hold and the state log records `fired_bear=True` with the suppression details.
2. **Given** a ticker whose top 10 institutional holders show net pctChange = -3.0% (above the -5% threshold), and the framework's pre-filter rating is Underweight, **When** the operator invokes propagate with active mode, **Then** the post-filter rating remains Underweight (no suppression) and `fired_bear=False`.
3. **Given** a ticker with bullish pre-filter rating (Buy or Overweight), regardless of institutional rotation, **When** the operator invokes propagate, **Then** the bear-side filter does NOT fire and `fired_bear=False` (bear-side filter only operates on bearish pre-ratings).

---

### User Story 2 - Shadow-mode observation without suppression (Priority: P1)

An operator wants to observe how often the C-4 filter WOULD fire on their workflow without yet committing to active suppression. The shadow mode populates `would_fire_bear=True` in state logs whenever the filter's conditions are met, but never mutates the rating. After accumulating ≥30 propagates, the operator runs an A/B ablation to confirm the empirical Δα improvement holds before flipping to active mode.

**Why this priority**: Constitution VIII v1.4.0 shadow-mode-first pattern requires this for any new mechanism class at small sample size (n=12 cohort triggered the requirement). Without shadow mode, operators cannot incrementally validate the filter's behavior in their own workflow.

**Independent Test**: Set `institutional_rotation_bear_mode="shadow"` in PARAMS.json. Run propagate on a ticker with confirmed institutional outflow + bearish pre-rating. Verify state log shows `would_fire_bear=True` AND `fired_bear=False`, AND that `post_rating == pre_rating` (no mutation). Compare across multiple tickers to confirm the pattern.

**Acceptance Scenarios**:

1. **Given** mode is "shadow" and the suppression conditions are met, **When** propagate runs, **Then** `would_fire_bear=True`, `fired_bear=False`, and the rating is unchanged.
2. **Given** mode is "shadow" and the suppression conditions are NOT met, **When** propagate runs, **Then** both `would_fire_bear` and `fired_bear` are False.
3. **Given** mode is "active" and the suppression conditions are met, **When** propagate runs, **Then** `would_fire_bear=True`, `fired_bear=True`, and the rating becomes Hold.

---

### User Story 3 - Filter degrades cleanly on data unavailability (Priority: P1)

An operator runs the framework on a ticker where yfinance institutional_holders data is unavailable (an ETF, a very small cap, an API outage, or a missing pctChange column). The filter detects this gracefully — no exception escapes — and the filter does not fire. The operator can audit the data unavailability via state log fields (e.g., `net_rotation_pct=None`).

**Why this priority**: Operational reliability is non-negotiable. Without graceful degradation, a single yfinance issue breaks the entire propagate. This is a P1 because it determines whether the filter can be safely deployed.

**Independent Test**: Run propagate on an ETF ticker (e.g., "SPY", "XLK"). Verify state log shows `net_rotation_pct=None`, `fired_bear=False`, `would_fire_bear=False`, and the rating is unchanged from pre-filter. Verify no exception is raised and the propagate completes successfully.

**Acceptance Scenarios**:

1. **Given** yfinance returns None or empty DataFrame for institutional_holders, **When** the filter runs, **Then** `net_rotation_pct=None`, `fired_bear=False`, and propagate completes without error.
2. **Given** yfinance returns a DataFrame missing the pctChange column, **When** the filter runs, **Then** `net_rotation_pct=None`, `fired_bear=False`, and propagate completes without error.
3. **Given** the yfinance call raises an exception, **When** the filter runs, **Then** the exception is caught, `net_rotation_pct=None`, `fired_bear=False`, and propagate completes without error.

---

### User Story 4 - Operator cost-control via mode=off escape hatch (Priority: P2)

An operator who wants zero overhead from the C-4 filter (no yfinance fetches, no state annotations, no helper module invocation) sets `institutional_rotation_bear_mode="off"` AND `institutional_rotation_bull_mode="off"` in PARAMS.json. The filter is fully disabled — state logs match the pre-Spec-X-1 baseline shape, no yfinance API calls are made, no annotation fields appear in state.

**Why this priority**: Constitution III (Stay Cheap) compliance requires an explicit escape hatch even for free-tier features. P2 because the default-shadow mode is already conservative, but operators may want absolute opt-out.

**Independent Test**: Set both modes to "off" in PARAMS.json. Run propagate on a ticker that would otherwise trigger the filter. Verify state log does NOT contain `state["forward_catalyst"]["institutional_rotation"]` field at all. Verify yfinance.Ticker(t).institutional_holders is NOT called (mockable via test).

**Acceptance Scenarios**:

1. **Given** both bear_mode and bull_mode are "off", **When** propagate runs, **Then** state log does not contain the `institutional_rotation` annotation field.
2. **Given** both bear_mode and bull_mode are "off", **When** propagate runs, **Then** the helper module's `_fetch_institutional_rotation` is not invoked (verified by mock-call-count test).

---

### Edge Cases

- **Ticker with exactly threshold rotation**: When `net_rotation_pct == -threshold` exactly, the filter does NOT fire (strict less-than semantics, matching Spec 007 SC-002).
- **Ticker with mixed pctChange across top 10 holders**: Some positive, some negative; sum across top 10 is what matters. Sum is computed via `fillna(0).sum()` to handle missing per-holder pctChange values without corrupting the aggregate.
- **Ticker repeatedly fetched in same process**: LRU cache (maxsize=128) ensures only one yfinance call per ticker per process. Cache lifetime is process-scoped — restarting the process re-fetches.
- **Bullish pre-rating with strong institutional outflow**: Bear-side filter does NOT fire on bullish pre-ratings (only suppresses Underweight/Sell). The case is irrelevant to bear-side suppression.
- **Q1 2026 13F refresh window crossed (~2026-05-15)**: yfinance institutional_holders data shifts to a new quarter's panel after the SEC filing window. Filter behavior remains identical (just operating on fresher data); the empirical Δα claims need re-validation per SC-009.
- **First propagate of the day vs subsequent in same process**: First call hits yfinance (~50-200ms latency); subsequent calls hit LRU cache (microseconds). No correctness difference.
- **Operator manually invalidates LRU cache** (process restart, code change): The cache is rebuilt from the next yfinance call. No persistence across processes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch top 10 institutional holders for a given ticker via yfinance.Ticker(ticker).institutional_holders, accessing the `pctChange` column.
- **FR-002**: System MUST compute net_rotation as the sum of pctChange across the top 10 holders, treating any NaN values as 0.
- **FR-003**: System MUST cache the fetch result via LRU (maxsize=128) per process, ensuring only one yfinance call per ticker per process.
- **FR-004**: System MUST suppress the Portfolio Manager rating from Underweight/Sell to Hold when net_rotation is more negative than the configured outflow threshold, AND the pre-filter rating is in the bearish set {Underweight, Sell}.
- **FR-005**: System MUST use strict less-than semantics for the threshold comparison (boundary case: net_rotation == -threshold MUST NOT fire), matching Spec 007 SC-002 boundary discipline.
- **FR-006**: System MUST support three operational modes per side (bear / bull): "off" (filter disabled), "shadow" (record would-fire decisions without rating mutation), and "active" (full suppression).
- **FR-007**: System MUST default `institutional_rotation_bear_mode` to "shadow" (per Constitution VIII v1.4.0 shadow-mode-first for small-sample evidence at n=12).
- **FR-008**: System MUST default `institutional_rotation_bull_mode` to "off" (per the empirical evidence that bull-side has only n=1 fire — too thin to warrant any default mode beyond off).
- **FR-009**: System MUST default `institutional_rotation_outflow_threshold` to 0.05 (fractional; reproduces the PR #75 best-config).
- **FR-010**: System MUST extend the existing `state["forward_catalyst"]` annotation dict with an `institutional_rotation` sub-dict containing 8 fields: `net_rotation_pct`, `outflow_threshold`, `bear_mode`, `bull_mode`, `would_fire_bear`, `fired_bear`, `pre_rating`, `post_rating`.
- **FR-011**: System MUST NOT add the `institutional_rotation` annotation sub-dict when both bear_mode and bull_mode are "off" (preserves backward compatibility with Spec 007 baseline state log shape).
- **FR-012**: System MUST run the C-4 filter LAST in the PM-stage filter chain (after A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007), reflecting its smaller evidence base relative to upstream filters.
- **FR-013**: System MUST gracefully degrade when yfinance returns None, empty DataFrame, missing pctChange column, or raises an exception — net_rotation MUST be set to None and the filter MUST NOT fire (no suppression, no exception escape).
- **FR-014**: System MUST persist the `institutional_rotation` annotation sub-dict via the existing `_log_state` whitelist (which already includes `forward_catalyst`).

### Key Entities *(include if feature involves data)*

- **Top 10 institutional holders snapshot**: A 10-row × 6-col DataFrame from yfinance.Ticker(ticker).institutional_holders. Each row represents one institutional holder (e.g., Vanguard, BlackRock); the `pctChange` column records the per-holder change in pctHeld from the prior 13F filing to the current snapshot.
- **net_rotation aggregate**: The sum of pctChange across the top 10 holders. Positive = net inflow (institutions accumulating); negative = net outflow (institutions selling).
- **state["forward_catalyst"]["institutional_rotation"] annotation**: An 8-field dict persisted in propagate state logs. Contains the rotation aggregate, threshold, both modes, would-fire/fired flags, and pre/post rating.
- **TradingAgentsConfig keys**: 4 new entries in the `TradingAgentsConfig` TypedDict: `institutional_rotation_bear_mode`, `institutional_rotation_bull_mode`, `institutional_rotation_outflow_threshold`, `institutional_rotation_inflow_threshold` (last is reserved for future bull-side activation; unused at default-off).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Suppression firing logic)**: When net_rotation = -0.06, threshold = 0.05, and pre_rating ∈ {Underweight, Sell}, the filter MUST suppress to Hold. When net_rotation = -0.04 (above threshold), filter MUST NOT suppress. Verified by ~6 unit tests covering boundary edge cases.
- **SC-002 (Boundary semantics)**: When net_rotation == -threshold exactly, filter MUST NOT fire (strict less-than). Verified by boundary unit test.
- **SC-003 (yfinance failure resilience)**: When yfinance returns None / empty DataFrame / missing pctChange / raises an exception, net_rotation MUST be None and filter MUST NOT fire. Verified by 4 mocked tests.
- **SC-004 (LRU cache correctness)**: Same ticker requested twice in a single process MUST hit cache (no second yfinance call). Verified by mock-call-count test.
- **SC-005 (Mode integrity)**: When both modes are "off", helper module MUST NOT be invoked AND state logs MUST NOT contain the new annotation fields. Verified by integration test.
- **SC-006 (Shadow vs active mode distinction)**: When mode = "shadow", `would_fire_bear` MAY be True but `fired_bear` MUST be False (no rating mutation). When mode = "active", both fields track the same decision. Verified by shadow-mode integration test.
- **SC-007 (State annotation completeness)**: When enabled and applied, state log MUST contain the 8 fields. Verified by state-log persistence regression test.
- **SC-008 (Pre/post rating accuracy)**: When `fired_bear=True` and pre_rating ∈ {Underweight, Sell}, post_rating MUST be "Hold". When `fired_bear=False`, post_rating MUST equal pre_rating. Verified by parametrized test.
- **SC-009 (Empirical retrospective re-validation, deferred to ~2026-05-15)**: After Q1 2026 13Fs land, re-run `scripts/forward_catalyst_class4_retrospective.py` with `--cohort-cutoff 2026-05-15` (or later) AND `scripts/forward_catalyst_class4_vs_spec007_overlap.py` to verify both gates STILL pass on the refreshed data panel. If either drops below the v1.4.0 / v1.4.3 thresholds, ablate to "off" default mode pending further investigation.
- **SC-010 (Live-mode flip eligibility, deferred until SC-009 confirms)**: Before flipping `institutional_rotation_bear_mode` default from "shadow" to "active", operators MUST run a live-mode A/B ablation (active vs shadow on the same propagates) for n≥30 propagates AND verify the SC-009 retrospective metrics hold within ±1pp at live-validated horizons.
- **SC-011 (Cost discipline)**: The filter adds zero LLM cost (no LLM calls in the implementation path). Verified by cost-instrumentation test.
- **SC-012 (Latency budget)**: yfinance.institutional_holders fetch on cache miss MUST complete within 200ms p95 over 10 runs (network-dependent; informational rather than gate-blocking).

## Assumptions

- **yfinance institutional_holders availability for major equities**: For US-listed equities with consistent 13F filings, yfinance.Ticker(t).institutional_holders returns a 10-row × 6-col DataFrame with the pctChange column populated. ETFs, foreign ADRs, and very small-cap stocks may return None or empty.
- **13F filing cycle ~45-day lag**: Institutional holders' pctChange data reflects the most-recently-filed 13F panel. The lag is structural and acknowledged in the empirical evidence (PR #75 cohort cutoff 2026-02-14 = ~45 days after 2025-12-31 quarter end).
- **Spec 007 already deployed**: Filter chain integration assumes Spec 007 (`forward_catalyst` annotation dict) is present in state. The C-4 sub-dict extends Spec 007's existing dict per the spec 003/004/006/007/008 precedent.
- **AgentState TypedDict is extension-safe**: The `forward_catalyst` field is already declared in AgentState (per Spec 007). No schema changes to AgentState are needed; sub-dict extension does not require TypedDict modification.
- **PARAMS.json is the operator opt-in mechanism**: Operators set mode + threshold values via PARAMS.json, which experiment runners read to set config keys. No CLI flag required for the spec; consistent with Spec 003/004/006/007/008 precedent.
- **The 13F-data window is time-bounded**: Q4 2025 13F era (cohort 2026-02-14) is the empirical evidence base. Q1 2026 13Fs land ~2026-05-15. After that date, the empirical evidence base needs re-evaluation per SC-009. The filter implementation is independent of this re-evaluation (the filter reads live yfinance data, not the cohort cache); only the default-mode policy may need adjustment if the post-refresh metrics drop below thresholds.
- **Filter ordering reflects evidence-base hierarchy**: C-4 runs LAST in the chain because its evidence base (n=12) is smaller than upstream filters. This is a deliberate sample-size discipline choice; filter could be re-ordered upward in a future spec amendment if the evidence base expands substantially.
- **Bear-side only at v1**: Bull-side mechanism (n=1 evidence base) is too thin to warrant default-on at any mode beyond "off". The bull-side config keys (`institutional_rotation_bull_mode`, `institutional_rotation_inflow_threshold`) are reserved for future expansion when bull-side empirical evidence accumulates.

## Constitution adherence

This spec satisfies the following Constitution principles:

- **Principle II (One Experiment Per Change)**: Spec defines the filter mechanism + defaults; live-mode A/B ablation is deferred to a separate spec amendment per SC-010.
- **Principle III (Stay Cheap)**: T0 (free) classification — no LLM cost addition; yfinance is a free data source.
- **Principle VI (Spec Before Structural Change)**: Structural addition (new helper module + state field extension + 4 config keys + PM-hook chain extension) is governed by this spec.
- **Principle VII (Calibrated Abstention is a Valid Output)**: Spec X-1 fires INCREASE Hold rate. Per VII this is permitted because the additional commits would otherwise be miscalibrated (+5.41pp standalone Δα + +8.06pp additive Δα empirical justification per PR #75 + #77).
- **Principle VIII v1.4.0 (Forward-catalyst-class validation gate)**: Pre-spec retrospective gate cleared at n=12 — discrim +10.29pp ≥ +5pp PASS / cohort hit 75.0% ≥ 60% PASS / net Δα +5.41pp ≥ +0.5pp PASS. Default-shadow per the v1.4.0 small-sample-caution sub-clause.
- **Principle VIII v1.4.1 (Spec ships its retrospective + verdict)**: Satisfied by the two pre-existing retrospective markdowns (`claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` + `claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md`) referenced in this spec.
- **Principle VIII v1.4.3 (Additive-to-existing-filter gate)**: Cleared at PASS on 2 of 3 v1.4.3 criteria (net Δα improvement +8.06pp ≥ +0.5pp PASS / hit rate improvement +69.23pp ≥ +5pp PASS / FP rate improvement +0.00pp FAIL). Per v1.4.3 "at least 1 of 3 criteria PASSING is sufficient" rule, additive gate clears.

## Dependencies

- **Spec 007 (forward-catalyst-aware contrarian gate)** — already deployed. C-4 extends Spec 007's `forward_catalyst` annotation dict; the chain integration appends one step after Spec 007.
- **yfinance** — already in dependencies. C-4 uses `yfinance.Ticker(t).institutional_holders` (existing API surface).
- **No new dependencies introduced**.

## Out of scope

- **Bull-side default-on activation**: n=1 empirical evidence is too thin. Bull-side config keys exist as scaffolding; default mode is "off". A future spec amendment may activate bull-side after evidence accumulates.
- **Multi-quarter trend analysis**: This spec uses single-quarter (most-recent-13F) pctChange. Multi-quarter trend (e.g., 2-quarter cumulative outflow) is a future expansion candidate but not in this spec.
- **Historical 13F data integration**: yfinance only exposes the current snapshot. Historical retrospectives (re-running with different cohort cutoffs) require running the script before the next 13F refresh. This spec's filter operates on live yfinance data; historical analysis is a separate concern handled by `scripts/forward_catalyst_class4_retrospective.py`.
- **Per-holder behavioral filters**: This spec aggregates across top 10 holders. Per-holder filters (e.g., "if Vanguard is selling specifically") are out of scope.
- **CLI flag**: Operator opt-in is via PARAMS.json (consistent with Spec 003/004/006/007/008 precedent). No `--c4-mode` CLI flag in this spec.
- **Multi-asset-class extension**: This spec is equity-only (yfinance institutional_holders is equity-specific). ETF / fixed-income / other asset classes are out of scope.

## Sibling docs

- `claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` — PR #75 standalone retrospective (verdict: PASS at n=12)
- `claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md` — PR #77 additive overlap (verdict: PASS on 2 of 3 v1.4.3 criteria)
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` — PR #78 bear-side mechanism survey (C-4 SOLE spec-eligible)
- `claudedocs/spec-x-1-c4-institutional-rotation-feature-description-2026-05-07.md` — PR #87 feature description draft (canonical input to this spec)
- `scripts/forward_catalyst_class4_retrospective.py` — re-runnable standalone-gate harness
- `scripts/forward_catalyst_class4_vs_spec007_overlap.py` — re-runnable additive-gate harness
- `specs/006-forward-catalyst-gate/spec.md` — Spec 007 precedent for FR + SC structure
- `.specify/memory/constitution.md` Principle VIII v1.4.0 + v1.4.3 — governing forward-catalyst-class gates
