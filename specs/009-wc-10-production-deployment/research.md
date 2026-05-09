# Research: WC-10 Production Deployment (Spec 009)

**Spec**: [spec.md](spec.md) (PR #140) | **Plan**: [plan.md](plan.md) (PR #156) | **Contract**: [contracts/daily_signals_wc_10_flag.md](contracts/daily_signals_wc_10_flag.md) (PR #158)

Decisions log for Spec 009. Each entry: decision / rationale / alternatives considered / status.

---

## R-1 — Conditional spec.md with 4 verdict-conditional branches

**Decision**: spec.md (PR #140) drafted as CONDITIONAL DRAFT with 4 branches A/B/C/D, one per v2 × v3 verdict combination. Branch selection deterministic when v2 verdict lands (v3 already resolved per PR #153).

**Rationale**: Pre-writing 4 branches NOW eliminates 30-45 min framing churn per branch when verdict lands. Pattern source: PR #131 + #144 conditional Constitution patches.

**Alternatives considered**: Wait for both v2 + v3 to land, then write a single-branch spec. Rejected — wall-clock cost of post-verdict draft is ~2-3× pre-scaffold cost, and the structure of each branch is knowable in advance.

**Status**: spec.md shipped via PR #140. Branch D pre-RULED-OUT per v3 verdict (PR #153 PARTIAL ALT-A; not full ALT-A). Remaining selection: A vs B vs C per v2 verdict.

## R-2 — Implementation Option A (forked module) vs Option B (config flag in existing file)

**Decision**: Branch A implementation uses Option A — new `tradingagents/agents/analysts/market_analyst_structured.py` module (separate from `market_analyst.py`).

**Rationale**:
- Clean separation; doesn't disturb existing prose analyst path
- Easy to delete if WC-10 mode is later retired
- Matches project precedent: Spec X-1 + Spec 007 added new modules rather than mixing modes in existing files
- Filter chain compatibility (Spec 009 FR-003) works naturally via the existing `bin_scalar_to_tier` function (Spec 108)

**Alternatives considered**: Option B — config flag `market_analyst_format: "prose" | "structured"` switching the existing analyst between modes. Rejected — mixing two paths in one file violates the project's separation-of-modes pattern.

**Status**: Documented in plan.md Phase 1 (PR #156). Implementation in MVP PR #4 of bundle.

## R-3 — paper_trade.py position-sizing scalar interpretation

**Decision**: Linear ramp `slot_size = base_slot × min(1.0, abs(rating_scalar) / 0.6)`. Scalar magnitude 0 → 0% slot; magnitude 0.6 → 100% slot; magnitude > 0.6 clamped to 100%.

**Rationale**:
- 0.6 is the WC-10 bin threshold for Buy / OW (per Spec 108 default thresholds). Below 0.6 → OW or weaker. At 0.6 → full conviction Buy.
- Linear ramp avoids step-function discontinuities at bin boundaries
- Clamp at 100% prevents over-leveraging on extreme scalars (paper_trade.py respects existing per-position cap pct)
- Backward-compat: when `rating_scalar` absent, falls back to existing 5-tier sizing logic

**Alternatives considered**:
- Quadratic ramp (`(rating_scalar / 0.6) ^ 2` for 0→1) — would underweight low-confidence commits. Rejected as adding complexity without empirical justification at v1.
- Piecewise step function matching bin thresholds. Rejected — discards the continuous information that WC-10 exists to surface.

**Status**: Documented in plan.md Phase 2 + contracts/daily_signals_wc_10_flag.md (PR #158). Implementation in MVP PR #4.

## R-4 — V3 caveat note placement (after rationale, not before rating)

**Decision**: The ⚠️ V3-caveat note in markdown digest appears AFTER the per-ticker rationale block, NOT before the rating header.

**Rationale**:
- Operator's primary read is the rating; they shouldn't have to scroll past a warning to see the signal
- Caveat is a magnitude-bound (per v3 ANALYSIS PARTIAL ALT-A verdict + Constitution v1.5.1 Patch D), not a hard gate
- Matches Constitution VII v1.5.0's framing: caveat is documentation, not blocking

**Alternatives considered**: Place ⚠️ block at top of per-ticker section. Rejected — too prominent for a documented-but-bounded caveat.

**Status**: Documented in contracts/daily_signals_wc_10_flag.md (PR #158).

## R-5 — Empirically-validated cohort gating (FR-005)

**Decision**: WC-10 mode applies WITHOUT regime-aware gating, but tickers OUTSIDE the FR-005 empirically-validated cohort receive the ⚠️ V3-caveat note in the digest.

**Rationale**:
- Per v3 PARTIAL ALT-A + Constitution v1.5.1 Patch D, hard regime-aware gating is NOT required (would have been required if v3 had been full ALT-A)
- Operator discretion suffices for the small (`|delta| < 1.0pp`) magnitude bound
- Cohort-level annotation gives operators the empirical context without blocking the signal

**Alternatives considered**:
- Hard regime-detection signal (e.g., VIX > 25 disables WC-10). Rejected per v3 verdict — the magnitude doesn't justify a hard gate.
- No annotation. Rejected — operators deserve cohort-level evidence cues.

**Status**: Documented in spec.md FR-006 + contracts/daily_signals_wc_10_flag.md (PR #158).

## R-6 — Backward-compat for paper_trade.py replay

**Decision**: paper_trade.py replay handles BOTH schemas (with and without `rating_scalar` column) gracefully. CSVs without scalar column use existing 5-tier sizing; CSVs with scalar use linear-ramp sizing per R-3.

**Rationale**:
- Existing paper_trade.py state files may have been generated under 5-tier mode and replayed later
- Mode-mixing across runs should be safe: replay should produce identical state regardless of which mode the original signals were generated under (replay invariant)
- Forward-compat: future modes can add columns without breaking existing replay paths

**Alternatives considered**: Require scalar column always (break backward-compat). Rejected — would invalidate existing state files + require migration.

**Status**: Documented in contracts/daily_signals_wc_10_flag.md edge cases section (PR #158).

## R-7 — Branch C as fallback (bin-then-output)

**Decision**: If v2 returns NULL (signed-rating × α correlation `|r| < 0.197`), Spec 009 ships Branch C — internal continuous reasoning + external 5-tier output via new `wc_10_internal_only: bool` config key.

**Rationale**:
- Even if scalar magnitude carries no information beyond binary commit/abstain, the internal continuous reasoning at PM stage MAY still help reasoning quality
- External 5-tier output avoids false-precision claims to operators
- Cheap to ship (~5 LOC config + ~5 LOC bin-then-output branch)

**Alternatives considered**: SKIP Spec 009 entirely if v2 NULL. Rejected — Branch C captures any reasoning-quality-only benefit at near-zero cost; worth shipping as research mode.

**Status**: Documented in spec.md Branch C + plan.md Phase 1 (Branch C section). Awaits v2 verdict.

## R-8 — Monitoring loop closure

**Decision**: `scripts/wc_10_underperformance_monitor.py` (PR #146) is the production-tier runtime monitor for v1.5.1 caveat enforcement. Operators can wire it into nightly cron.

**Rationale**:
- Per v3 verdict + v1.5.1, hard gating is not required but runtime monitoring IS load-bearing
- Monitor consumes daily_signals.py paired output (when both modes are captured) and flags cohorts where WC-10 underperforms 5-tier
- 3 alert criteria (single-pair severe / streak / cohort cumulative) cover the failure modes documented in v1 + v3
- Cron-friendly exit code (0 = no alerts, 1 = alert triggered)

**Alternatives considered**:
- Inline runtime gate in daily_signals.py that disables WC-10 mode if recent underperformance exceeds threshold. Rejected — couples monitoring to production hot path; out-of-band cron monitor is cleaner.
- No monitoring tool. Rejected — v1.5.1 caveat without monitoring is documentation-only.

**Status**: Shipped as PR #146 + smoke-tested on v1 pilot (cohort cumulative Δα +22.42pp; 2 per-pair alerts on AAPL UW commits — empirically validates v1.5.1 caveat in operational form).

---

## Summary

8 decisions documented. Branch A implementation specified end-to-end pending v2 verdict. Branch B + C + D contingencies covered. Monitoring loop closed via PR #146.

The conditional-branch pattern from PR #151 + the contract pattern from PR #158 + this research log together form a complete pre-implementation surface for Spec 009. Final activation gate is the v2 verdict landing.
