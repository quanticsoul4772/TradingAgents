# Spec X-1 — C-4 Institutional Rotation Filter — `/speckit.specify` feature description

**Status**: DRAFT for user review BEFORE invoking `/speckit.specify`.
**Author**: Claude (planning artifact).
**Date**: 2026-05-07.

**Purpose of this doc**: per Constitution VI (Spec Before Structural
Change) + the Spec 008 Hybrid C precedent (where the user authored the
full feature description as input to `/speckit.specify`), this file
drafts the equivalent block of text for Spec X-1. User reviews / edits /
approves; the approved text becomes the literal input to
`/speckit.specify`.

If the draft is approved as-is, the next-step PR is "invoke
`/speckit.specify` with this text" → spec-kit generates `specs/<id>-c4-institutional-rotation/spec.md`.

---

## Draft `/speckit.specify` input

```text
Spec X-1 — C-4 Institutional Rotation Filter (operator-facing name "Spec
X-1"; implementation directory will be auto-numbered by spec-kit per
the recurring numbering quirk noted in operator memory). FIRST
quantitative-flow bear-side filter — fundamentally different mechanism
class from the 5 prose-density / LLM-extracted / backward-price /
calendar-boost filters in the existing portfolio. Suppresses Underweight/
Sell commits to Hold when top 10 institutional holders' net rotation
(sum of pctChange across the 10-row × 6-col DataFrame from
yfinance.Ticker(t).institutional_holders) is below a configurable
outflow threshold (T_outflow, default 0.05 fractional = -5% net rotation).

EMPIRICAL MOTIVATION: Two PR-shipped retrospectives DECISIVELY PASS the
Constitution VIII v1.4.0 standalone gate AND the v1.4.3 additive-
overlap-vs-Spec-007 gate:
- PR #75 standalone: bear-side n=12, discrim +10.29pp, hit rate 75.0%,
  net Δα +5.41pp at T_outflow=0.05 (per
  claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md).
  Bull-side n=1 — too thin, deferred.
- PR #77 additive: union (C-4 OR Spec 007 bear) net Δα +8.06pp
  improvement vs Spec 007 bear alone, hit rate +69.23pp improvement
  (per claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md).
  C-4 catches 11 bearish commits Spec 007 ENTIRELY MISSES — clean
  cross-mechanism-class additive case.

Mechanism class distinction: Spec 007 bear is LLM-extracted bear-priced-in
score (semantic reasoning over analyst+debate text); C-4 is institutional
ownership rotation (quantitative flow signal from 13F filings). LITERALLY
different signal sources. The 11 c4_only fires are bear commits where
LLM didn't read the bear thesis as priced-in (bear_score ≤ 0.50) BUT
institutions had been rotating OUT (selling) — PM picked UW chasing the
move; suppressing was correct (mean +6.16% α on the c4_only cell, 81.8%
hit rate).

MECHANISM: At PM stage, AFTER all existing filters (A3 → spec 006 →
spec 003/003.5 → spec 004 → spec 007), apply the C-4 check. Fetch top
10 institutional holders for the ticker via
yfinance.Ticker(t).institutional_holders (LRU-cached per process). Sum
the pctChange column across top 10 holders → net_rotation. If
net_rotation < -T_outflow AND pre_rating ∈ {Underweight, Sell} →
suppress to Hold. Bear-side ONLY (bull-side disabled by config; n=1
empirical evidence too thin to warrant default-on bull-side, per the PR
#75 verdict).

DEFAULTS (per retrospective best config + Constitution VIII v1.4.0
shadow-mode-first for new mechanism classes at small sample size):
`institutional_rotation_bear_mode` defaults to `"shadow"` (NOT default-
on) per VIII v1.4.0 sample-size caution (n=12 is small; the 13F-data
window is time-bounded — Q1 2026 13Fs land ~2026-05-15, after which
this retrospective's evidence base will need refreshing). The bull-side
counterpart `institutional_rotation_bull_mode` defaults to `"off"`
(n=1 evidence base; not eligible per VIII v1.4.0). Operator opt-in to
active mode via PARAMS.json. When active or shadow, the threshold
defaults to `institutional_rotation_outflow_threshold = 0.05`
(fractional; reproduces the PR #75 best-config). The Constitution VIII
v1.4.1 "spec ships its retrospective + verdict" pattern is satisfied
by the two pre-existing retrospective markdowns + this spec's
quickstart referencing them.

MODULE: New helper `tradingagents/agents/utils/institutional_rotation_filter.py`
(~120 LOC). Exposes:
- `_fetch_institutional_rotation(ticker: str) -> float | None` —
  LRU-cached (maxsize=128) per-process yfinance fetch + sum across top
  10 holders. Mirrors the same name + signature in
  `scripts/forward_catalyst_class4_retrospective.py` (single source of
  truth for the data fetch logic — script already references it; new
  module re-implements with same semantics for production).
- `should_suppress_bear(net_rotation: float | None, threshold: float) -> bool` —
  pure function; returns True iff `net_rotation is not None and
  net_rotation < -threshold`. Boundary semantics: strict less-than, by
  symmetry with Spec 007 SC-002.
- `apply_filter(state: AgentState, config: TradingAgentsConfig) -> AgentState` —
  PM-hook integration. Annotates state["forward_catalyst"]["institutional_rotation"]
  dict (extends Spec 007's annotation per the spec 003/004/006/007/008
  precedent — NEW dict NOT created at top level).

INTEGRATION: `tradingagents/agents/managers/portfolio_manager.py` adds
the C-4 check AFTER Spec 007 in the FR-012 chain. Final ordering:
A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → **spec X-1**.
Helper module is ~120 LOC and independently testable.

STATE ANNOTATION (extends `state["forward_catalyst"]["institutional_rotation"]`
per spec 003/004/006/007/008 precedent — NEW dict NOT created at top
level): adds 8 fields {`net_rotation_pct`: float | None, `outflow_threshold`:
float, `bear_mode`: Literal["off","shadow","active"], `bull_mode`:
Literal["off","shadow","active"], `would_fire_bear`: bool, `fired_bear`:
bool, `pre_rating`: str, `post_rating`: str}. When mode is "off" (both
sides), these fields are NOT added to the dict (preserves backward compat
with Spec 007 baseline state logs). Persisted via the existing `_log_state`
whitelist that already includes `forward_catalyst` (no schema changes to
AgentState).

NEW TradingAgentsConfig keys: 4 keys total —
- `institutional_rotation_bear_mode` (Literal["off","shadow","active"],
  default "shadow")
- `institutional_rotation_bull_mode` (Literal["off","shadow","active"],
  default "off")
- `institutional_rotation_outflow_threshold` (float, default 0.05)
- `institutional_rotation_inflow_threshold` (float, default 0.05) —
  reserved for future bull-side activation; unused at default-off.

FILTER ORDERING (extends FR-012 chain by appending one step, NO CHANGE
to existing 5 filters): A3 → spec 006 → spec 003/003.5 → spec 004 →
spec 007 → **spec X-1 (LAST in chain)**. Spec X-1 runs LAST because
it has the smallest evidence base (n=12) and should not gate-out
suppressions decided by the higher-confidence upstream filters.

CONSTITUTION VIII v1.4.0 EVIDENCE: pre-spec retrospective methodology
PASS gate cleared (discrim +10.29pp > +5pp / cohort hit 75.0% > 60% /
net Δα +5.41pp > +0.5pp at n=12). NO NEW CONSTITUTION AMENDMENT NEEDED
— Spec X-1 is governed by the existing Principle VIII v1.4.0 forward-
catalyst-class gate.

CONSTITUTION VIII v1.4.3 ADDITIVE EVIDENCE: PASS on 2 of 3 v1.4.3
criteria (net Δα improvement +8.06pp ≥ +0.5pp PASS; hit rate improvement
+69.23pp ≥ +5pp PASS; FP rate improvement +0.00pp FAIL). Per v1.4.3
"at least 1 of 3 criteria PASSING is sufficient" rule, additive gate
clears.

COST GATE: ZERO LLM cost (Spec X-1 is pure yfinance-data lookup +
arithmetic). yfinance institutional_holders fetch adds ~50-200ms latency
on cache miss; LRU-cached to one fetch per ticker per process.
Constitution III T0 (free) classification.

OPERATIONAL CHARACTERISTICS:
- yfinance.institutional_holders is fetched once per ticker per process
  (LRU maxsize=128; safe for any realistic ticker universe)
- When yfinance returns None, empty DataFrame, or missing pctChange
  column (e.g., for ETFs, very small caps, or yfinance API outages):
  net_rotation = None → filter does NOT fire → degrades cleanly to
  baseline (no suppression)
- The Q4 2025 13F era (cohort cutoff 2026-02-14) is the data source for
  the retrospective evidence. Q1 2026 13Fs land ~2026-05-15; after
  that date, the empirical evidence base needs re-evaluation via re-
  running scripts/forward_catalyst_class4_retrospective.py to confirm
  the +10.29pp / +5.41pp metrics still hold on the refreshed data
  panel. Spec X-1 implementation is independent of this re-evaluation
  (the filter itself reads live yfinance data, not the cohort cache),
  but the default-mode policy may need revising if the post-refresh
  retrospective's metrics drop below the v1.4.0 gate.

VALIDATION GATES:
- SC-001 (Suppression firing logic): Synthetic test with net_rotation=
  -0.06 + threshold=0.05 + pre_rating=Underweight → MUST suppress to
  Hold. Same inputs at net_rotation=-0.04 → MUST NOT suppress (below
  threshold). Verified by ~6 unit tests covering boundary edge cases.
- SC-002 (Boundary semantics): When net_rotation == -threshold exactly,
  filter MUST NOT fire (strict less-than, matching Spec 007 SC-002).
  Verified by boundary unit test.
- SC-003 (yfinance failure resilience): When
  yfinance.Ticker(t).institutional_holders raises an exception OR
  returns None OR returns empty DataFrame OR returns DataFrame missing
  the pctChange column, net_rotation MUST be None and filter MUST NOT
  fire — degrades cleanly to baseline. Verified by 4 mocked tests.
- SC-004 (LRU cache correctness): Same ticker requested twice in a
  single process MUST hit cache (no second yfinance call). Verified by
  mock-call-count test.
- SC-005 (Mode integrity): When `institutional_rotation_bear_mode=
  "off"` (and bull_mode="off"), the helper module MUST NOT be invoked.
  State logs MUST NOT contain the new annotation fields (preserves
  Spec 007 baseline state log shape). Verified by integration test.
- SC-006 (Shadow vs active mode distinction): When mode="shadow",
  `would_fire_bear` MAY be True but `fired_bear` MUST be False (no
  pre_rating mutation). When mode="active", both fields track the same
  decision. Verified by shadow-mode integration test.
- SC-007 (State annotation completeness): When enabled and applied,
  state["forward_catalyst"]["institutional_rotation"] MUST contain the
  8 fields (net_rotation_pct, outflow_threshold, bear_mode, bull_mode,
  would_fire_bear, fired_bear, pre_rating, post_rating). Verified by
  state-log persistence regression test.
- SC-008 (Pre/post rating accuracy): When fired_bear is True and
  pre_rating ∈ {Underweight, Sell}, post_rating MUST be "Hold". When
  fired_bear is False, post_rating MUST equal pre_rating. Verified by
  parametrized test.
- SC-009 (Empirical retrospective re-validation, deferred to ~2026-05-15):
  After Q1 2026 13Fs land, re-run
  scripts/forward_catalyst_class4_retrospective.py with --cohort-cutoff
  2026-05-15 (or later) AND scripts/forward_catalyst_class4_vs_spec007_overlap.py
  to verify both gates STILL pass on the refreshed data panel. If
  either drops below the v1.4.0 / v1.4.3 thresholds, ablate to "off"
  default mode pending further investigation.
- SC-010 (Live-mode flip eligibility, deferred until SC-009 confirms):
  Before flipping `institutional_rotation_bear_mode` default from
  "shadow" to "active", operators MUST run a live-mode A/B ablation
  (active vs shadow on the same propagates) for n≥30 propagates AND
  verify the SC-009 retrospective metrics hold within ±1pp at live-
  validated horizons. Defer per Constitution VIII v1.4.0 shadow-mode-
  first-then-flip pattern.

TEST COUNTS: ~14 unit tests (helper module — fetcher LRU + suppression
function + state annotation builder + edge cases) + 4 integration
tests (PM-hook with mode=off / shadow / active / yfinance failure) +
0 PM-integration tests beyond the existing Spec 007 test suite (filter
ordering already validated by Spec 007's PM-integration tests; new
filter is appended to the chain).

CONSTITUTION VII (Calibrated Abstention): Spec X-1 fires INCREASE Hold
rate (suppresses additional Underweight/Sell commits whose institutional
rotation triggered the chase-the-move pattern). Per Principle VII this
is permitted as long as the additional commits would otherwise be
miscalibrated — the +5.41pp standalone net Δα + +8.06pp additive Δα
improvement IS the empirical justification.

CONSTITUTION VI (Spec Before Structural Change): structural addition of
new helper module + state field extension (within Spec 007's existing
forward_catalyst dict) + 4 new TradingAgentsConfig keys + integration
into PM hook chain (1 new step appended). Spec required.

CONSTITUTION III (Stay Cheap): T0 (free) — no LLM cost addition;
yfinance is a free data source.

CONSTITUTION II (One Experiment Per Change): the spec defines the
filter mechanism + defaults; live-mode ablation is deferred to a
separate spec amendment per Constitution VIII v1.4.0 shadow-mode-first.
```

---

## Pre-spec-invocation checklist (post-overlap)

| Check | Status | Source |
|---|---|---|
| Standalone gate PASS | ✅ bear-side at n=12 | PR #75 |
| Mechanism class distinct from existing | ✅ institutional-flow class | PR #75 |
| v1.4.3 additive overlap vs Spec 007 | ✅ PASS on 2/3 criteria | PR #77 |
| Bear-side mechanism survey closure | ✅ C-4 SOLE spec-eligible | PR #78 |
| Time-window discipline acknowledged | ✅ SC-009 codifies refresh pattern | This draft |
| Sample-size caution acknowledged | ✅ default-shadow per VIII v1.4.0 | This draft |
| Constitution VI Spec Before Structural Change | ⚠️ requires `/speckit.specify` invocation | Next step |

## What `/speckit.specify` will produce

Following the Spec 008 Hybrid C precedent (per CLAUDE.md
specs/006-forward-catalyst-gate/ reference), invoking `/speckit.specify`
with the draft text above will produce:

- New feature branch (e.g., `090-c4-institutional-rotation`)
- `specs/<auto-numbered>-c4-institutional-rotation/spec.md`
- spec.md will be structured per the speckit-template format with
  user stories, FRs (FR-001 through ~FR-014), success criteria
  (SC-001 through SC-010), edge cases, dependencies, etc.

Subsequent spec-kit phases (`/speckit.plan` → `/speckit.tasks` →
`/speckit.implement`) build on this. Estimated total scope (specify +
plan + tasks + implementation): 3-4h end-to-end. Initial `/speckit.specify`
invocation alone is ~1 PR worth (just spec.md generation).

## Reviewer notes

Operator may want to revise:
- **Filter ordering** (currently appended LAST). Could argue for
  inserting BEFORE Spec 007 if institutional-flow signal is considered
  higher-confidence than LLM-extracted-bear. Current placement reflects
  sample-size discipline (smallest evidence base goes last). Revisit
  after Q1 2026 13F retrospective.
- **Default mode** ("shadow" for bear; "off" for bull). Conservative
  per VIII v1.4.0; operator may prefer "active" if confidence in PR #75
  + #77 evidence is higher.
- **Threshold** (0.05 fractional). PR #75 used this as the production
  config; could parametrize differently if operator wants to test
  thresholds during implementation.
- **Module name** — `institutional_rotation_filter.py` matches the
  existing naming pattern (sector_momentum_filter.py /
  bear_sector_symmetry_filter.py / forward_catalyst_filter.py /
  calendar_boost.py). Could prefer a different name; flag in review.
- **State annotation field count** (8 fields). Following the Spec 007
  precedent (16 fields). Could be expanded if operator wants more
  audit information per fire decision.
- **SC-009 + SC-010 timing**. Currently anchored to ~2026-05-15 13F
  refresh. Operator may prefer to reframe these as "after Q1 2026
  13F season" without specific date anchoring (per
  `feedback_no_day_rollover_planning.md` memory pattern — though SC
  numbering inherently anchors timing).

If the draft is approved as-is, the next step is a single PR that
invokes `/speckit.specify` with this text and ships the resulting
spec.md. If the draft needs revision, the operator edits THIS file
(claudedocs/spec-x-1-c4-institutional-rotation-feature-description-2026-05-07.md)
or supplies a fresh feature description, and we proceed from there.

## Sibling docs

- `claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` —
  PR #75 standalone retrospective evidence
- `claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md` —
  PR #77 additive overlap evidence
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` —
  PR #78 bear-side mechanism survey (C-4 SOLE spec-eligible)
- `scripts/forward_catalyst_class4_retrospective.py` — re-runnable
  standalone-gate harness
- `scripts/forward_catalyst_class4_vs_spec007_overlap.py` — re-runnable
  additive-gate harness
- `specs/006-forward-catalyst-gate/spec.md` — Spec 007 precedent for
  feature description structure + SC organization
- `.specify/memory/constitution.md` Principle VIII v1.4.0 + v1.4.3 —
  governing forward-catalyst-class gates
