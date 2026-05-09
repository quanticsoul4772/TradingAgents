# Implementation Plan: WC-10 Production Deployment (Spec 009) — Conditional Plan

**Spec**: `specs/009-wc-10-production-deployment/spec.md` (PR #140)
**Created**: 2026-05-08
**Status**: **CONDITIONAL PLAN** — covers Branch A + B implementation paths (the most likely v2 outcomes given v1 + v3 evidence). Final branch selection BLOCKED ON v2 verdict (~9h remaining as of plan-write time).

## Pre-implementation gate

This plan is the second PR in the standard 6-PR spec-kit bundle (per `reference_speckit_6pr_workflow_pattern.md` + Spec 011 FR-006). Bundle progression:

1. ✅ **PR #140** — spec.md (4 verdict-conditional branches A/B/C/D)
2. **THIS PR** — plan.md (Branch A + B implementation; conditional)
3. **PENDING v2** — tasks.md (per selected branch)
4. **PENDING v2 + PR #3** — MVP implementation
5. **PENDING v2 + PR #4** — tests
6. **PENDING v2 + PR #5** — polish + retrospective markdown

The plan can be drafted NOW because:
- v1 confirmed SC-007 ALT-A (PR #130, 3.6× commit ratio)
- v3 confirmed PARTIAL ALT-A on bear regime (PR #153; Constitution v1.5.1 Patch D applied per PR #154)
- Branch A or B activation is the most likely outcome given v1 + v3 evidence (Branch A if v2 STRONG; Branch B if v2 MODERATE)
- Branch C activation requires v2 NULL (low probability per v1 + v3 directional evidence — but still possible)
- Branch D activation requires v2 NULL + v3 ALT-A (REJECTED — v3 verdict was PARTIAL ALT-A, not ALT-A)

**Branch D is now PRE-RULED-OUT** per v3 verdict (Patch D preserved v1.5.0 caveat at scope; did NOT strengthen to require regime-aware gating). The remaining branch selection is between A / B / C per v2 verdict.

## Architectural overview

WC-10 production deployment is fundamentally a **rendering + plumbing change**, not a new mechanism. The schema work (Pydantic + filter-bypass mode) shipped via Spec 108 PRs #107-#114. This deployment ships:

- **Operator-facing surface** in `daily_signals.py` (Branch A only — `--wc-10-enabled` flag; rendering + signal CSV emit)
- **Position-sizing integration** in `paper_trade.py` (Branch A only — consumes scalar for slot-size scaling)
- **Documentation** in `docs/SIGNALS.md` (all branches — caveat block per Spec 009 FR-006)
- **Filter-chain compatibility** verification (all branches — bin-then-filter ordering per Spec 009 FR-003)

No NEW mechanism class is introduced. WC-10's scalar reads pass through `bin_scalar_to_tier()` (already shipped) before any filter sees them, preserving the 9-filter portfolio as-is.

## Branch A implementation (assumes v2 STRONG → Branch A activation)

**Trigger**: v2 SC-005(b) Pearson r ≥ 0.30 OR v2 ALT-A generalization across ≥6 of 8 tickers per FR-005.

### Phase 1 — daily_signals.py operator-facing flag (P1 user story A.1)

**Module**: `scripts/daily_signals.py`

**Changes**:
- New typer flag `--wc-10-enabled` (default False; `--wc-10-disabled` for explicit no)
- When set: build config with `wc_10_enabled=True` + `wc_10_filter_mode="bypass"`
- Markdown digest: render scalar rating to 4 decimals + binned tier (per `bin_scalar_to_tier`)
- "WC-10 confidence note" line in digest header explaining scalar interpretation when flag set
- `--emit-csv` adds `rating_scalar` column when WC-10 mode active

**Tests** (new in `tests/test_daily_signals_wc_10.py`):
- Flag default off → no scalar in output
- Flag on → scalar in markdown + CSV
- 5-tier downstream consumers see binned tier (not scalar) for backward compat

### Phase 2 — paper_trade.py position-sizing integration (P1 user story A.2)

**Module**: `scripts/paper_trade.py`

**Changes**:
- `replay` + `step` commands read `rating_scalar` column if present in signals CSV
- Position-sizing function: `slot_size = base_slot × min(1.0, abs(rating_scalar) / 0.6)` (linear ramp from 0 at threshold to 1 at +0.6)
- Falls back to `rating` (5-tier) if `rating_scalar` absent — preserves backward compat
- Replay invariant: applying events in order produces identical state regardless of mode

**Tests** (extend `tests/test_paper_trade.py`):
- Scalar absent → 5-tier fallback path
- Scalar present at ±0.4 → 75% of normal slot size
- Scalar present at ±0.7 → 100% slot size (clamped)
- Replay equivalence across modes

### Phase 3 — docs/SIGNALS.md caveat block (FR-006)

**Module**: `docs/SIGNALS.md` (existing operator-facing doc)

**Changes**:
- New "WC-10 mode" section
- v3 verdict summary (PARTIAL ALT-A; α delta -0.22pp on Q4 2025 NVDA)
- Cohorts where WC-10 is empirically validated (NVDA + AAPL + v2 tickers passing FR-005)
- Cohorts where WC-10 is NOT empirically validated (operators apply at own risk)
- Reference to `scripts/wc_10_underperformance_monitor.py` (PR #146) for runtime monitoring

### Phase 4 — Polish + retrospective

**New file**: `claudedocs/spec-009-branch-a-retrospective-2026-05-XX.md`

Documents the v1 + v2 + v3 empirical chain that triggered Branch A activation. Per Constitution VI v1.4.1 spec-ships-its-retrospective discipline.

## Branch B implementation (assumes v2 MODERATE → Branch B activation)

**Trigger**: v2 SC-005(b) `0.197 < |r| < 0.30` OR ALT-A generalizes on 3-5 of 8 tickers (insufficient for Branch A but more than D).

**Deployment**: Research-only mode. PARAMS.json access only; NO `daily_signals.py` exposure.

### Phase 1 — Documentation in docs/SIGNALS.md (FR-006)

**Module**: `docs/SIGNALS.md`

**Changes**:
- New "WC-10 (research mode)" section
- Documents `wc_10_enabled: true` + `wc_10_filter_mode: "bypass"` PARAMS.json keys
- Explicitly notes: "NOT exposed in `daily_signals.py` at the current evidence basis"
- Same v3 verdict + monitoring reference as Branch A's doc, but flagged research-only

### Phase 2 — Polish + retrospective

**New file**: `claudedocs/spec-009-branch-b-retrospective-2026-05-XX.md`

Notes the v2 MODERATE outcome that downgraded from Branch A to Branch B.

**No code changes**. Branch B leverages existing infrastructure (PARAMS.json schema is already operator-accessible per Spec 108).

## Branch C implementation (assumes v2 NULL → Branch C activation)

**Trigger**: v2 SC-005(b) `|r| < 0.197`. Scalar carries no information beyond the binary commit/abstain decision the bin already captures.

**Deployment**: bin-then-output ergonomic-only. WC-10 stays internal as a partial-confidence intermediate; external output reverts to 5-tier categorical.

### Phase 1 — New PARAMS.json key `wc_10_internal_only: true`

**Module**: `tradingagents/default_config.py`

**Changes**:
- Add `wc_10_internal_only: bool` to TradingAgentsConfig (default False)
- When True: emits 5-tier externally regardless of `wc_10_enabled`
- `bin_scalar_to_tier` is the canonical bin function (already shipped per Spec 108)

### Phase 2 — Documentation in docs/SIGNALS.md

Notes the v2 NULL outcome + ergonomic-only mode design.

### Phase 3 — Polish + retrospective + spec-close

**New file**: `claudedocs/spec-009-branch-c-retrospective-2026-05-XX.md`

Documents Branch C as an interim mode pending future evidence. Spec 009 stays open with Branch C as the active deployment.

## Implementation effort estimates

| Branch | New code | Tests | Docs | Estimated wall-clock |
|---|---|---|---|---|
| A | ~80 LOC across 2 scripts | ~10 unit + 2 integration | ~1 page | 4-6 hours |
| B | 0 LOC | 0 (existing tests cover PARAMS path) | ~1 page | 30 min |
| C | ~5 LOC config + 5 LOC bin-then-output branch | ~3 unit | ~1 page | 1.5 hours |

**Cost**: $0 LLM (pure plumbing + docs; existing daily_signals.py + paper_trade.py infrastructure handles propagate/consume).

If Branch A activation includes a smoke-test propagate to verify the operator UX, +$0.40 LLM (one propagate). Smoke test is recommended but not strictly required (PR #141 dry-run digest renderer already covers UX validation against saved data).

## Constitution adherence (per branch)

All branches:
- ✅ I (Save Everything): retrospective markdown per branch shipped per Constitution VI v1.4.1
- ✅ II (One Experiment Per Change): N/A (deployment, not experiment)
- ✅ III (Stay Cheap): $0 LLM (or +$0.40 for optional Branch A smoke)
- ✅ IV (No Production Claims): docs/SIGNALS.md caveat block per FR-006
- ✅ VI (Spec Before Structural Change): this plan + spec.md
- ✅ VII v1.5.1 (Calibrated Abstention): cohort-aware deployment per FR-004
- ✅ VIII: N/A (deployment doesn't add a new filter mechanism)

## Pre-implementation checks

Before invoking the next PR (tasks.md), verify:

- [ ] v2 has landed with verdict + ANALYSIS
- [ ] v2 verdict matches one of A/B/C (D is pre-ruled-out per v3 verdict)
- [ ] FR-005 cohort threshold computed from v2 ANALYSIS (≥6 tickers @ ≥80% commit rate for A)
- [ ] Constitution v1.5.1 + Patch D applied (✅ done per PR #154)
- [ ] Spec 009 FR-006 caveat content drafted from v3 ANALYSIS (✅ source data ready per PR #153)

## Cross-references

- `specs/009-wc-10-production-deployment/spec.md` (PR #140 — 4 verdict-conditional branches)
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1 — SC-007 ALT-A confirmed)
- `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS.md` (v3 — PARTIAL ALT-A; PR #153)
- `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/` (v2 IN FLIGHT — branch selection blocker)
- Constitution v1.5.1 Principle VII sub-section + Bear-regime validation paragraph (PR #154)
- Spec 011 6-PR bundle pattern (PR #136)
- `claudedocs/v3-landing-pr-series-bundle-template-2026-05-08.md` (PR #149 — landing playbook for v2 follows the same shape)
- Memory `reference_conditional_branch_spec_pattern.md` (PR #151 — codifies the conditional-branch pattern)
