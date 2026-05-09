# Feature Specification: WC-10 Production Deployment (Spec 009)

**Feature Branch**: `009-wc-10-production-deployment`
**Created**: 2026-05-08
**Status**: **CONDITIONAL DRAFT** — final activation conditional on WC-10 v2 + v3 verdicts (in flight). Three deployment branches scaffolded below; the v2 SC-005(b) verdict + v3 bear-regime verdict together select which branch ships.
**Predecessors**:
- `specs/108-wc-10-continuous-scalar-rating/` (v1 spec; pilot framework + bin function + filter-bypass mode)
- `experiments/2026-05-08-001-wc-10-pilot/` (v1 pilot ANALYSIS.md — SC-007 ALT-A confirmed)
- `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/` (v2 in flight — n=100 SC-005(b) primary)
- `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/` (v3 in flight — bear-regime caveat test)
- `.specify/memory/constitution.md` v1.5.0 (Principle VII "Schema-induced abstention is NOT calibrated abstention" sub-section)

## Why this spec exists in conditional draft form

WC-10 v1 confirmed the categorical-bottleneck hypothesis (SC-007 ALT-A at 3.6× commit ratio, n=20 paired). The two follow-up pilots (v2 + v3) resolve the load-bearing prerequisites for any production deployment decision:

- **v2 SC-005(b)**: does scalar magnitude predict α magnitude beyond binary commit/abstain at n=100? (STRONG / MODERATE / NULL)
- **v3 bear-regime**: does WC-10 amplification make bear-regime outcomes WORSE / NEUTRAL / BETTER on Q4 2025 NVDA? (NULL / ALT-A / ALT-B / PARTIAL ALT-A)

This spec scaffolds the deployment surface NOW so when the verdicts land in ~2-12h, the appropriate branch is selected and shipped via the standard 6-PR spec-kit bundle without re-arguing the mechanism from scratch.

Pre-scaffolding eliminates ~30-45 min of framing churn per deployment branch + ensures the deployment design is consistent with v1 + v2 + v3 evidence as it accumulates.

## Verdict-conditional deployment branches

### Branch A — STRONG (v2 SC-005b `|r| > 0.30`) + non-anti-calibrated v3

**Trigger**: v2 produces a meaningful signed-rating × α correlation (`|r| > 0.30`, p < 0.05 at n=100) AND v3 produces NULL or ALT-B (i.e., bear-regime amplification is NOT actively wrong).

**Deployment**: WC-10 ships as **operator-opt-in** in `tradingagents/daily_signals.py` workflow.

#### User Story A.1 — Operator runs daily signals with WC-10 enabled (Priority: P1)

**As an** operator
**I want to** run `daily_signals.py --wc-10-enabled` over my watchlist and receive scalar ratings in the markdown digest
**So that** I get partial-confidence signal that the 5-tier scale was suppressing

**Acceptance criteria**:
- New CLI flag `--wc-10-enabled` (default off; `--wc-10-disabled` is the inverse for explicit overrides)
- Markdown digest renders scalar rating to 4 decimal places (e.g., `+0.6200`) alongside binned tier (per `bin_scalar_to_tier`)
- Markdown digest includes a "WC-10 confidence note" line explaining the scalar interpretation when the flag is set
- `--emit-csv` output includes `rating_scalar` column when WC-10 mode is active
- Hold suppression continues per Constitution VII v1.5.0 (genuine ambiguity → suppress; schema-induced collapse → emit binned commit)

#### User Story A.2 — Paper-trading harness consumes WC-10 ratings (Priority: P1)

**As the** paper-trading harness operator
**I want to** consume the `rating_scalar` column from `daily_signals.py --emit-csv --wc-10-enabled` output
**So that** position sizing scales with conviction magnitude (e.g., scalar ±0.4 → 75% of normal slot size; scalar ±0.7 → 100%)

**Acceptance criteria**:
- `scripts/paper_trade.py` reads `rating_scalar` if present; falls back to `rating` (5-tier) if absent
- Position sizing uses `min(1.0, abs(rating_scalar) / 0.6)` as the size scalar (linear ramp from 0 at threshold to 1 at +0.6)
- Replay invariant preserved: applying events in order produces identical state regardless of which mode the original signals were generated in

### Branch B — MODERATE (`0.197 < |r| < 0.30`) OR mixed v3

**Trigger**: v2 produces a statistically detectable but small-effect correlation, OR v3 produces PARTIAL ALT-A (regime-asymmetric calibration as v1 caveat predicted).

**Deployment**: WC-10 ships as **research-only mode** — accessible via PARAMS.json overrides for backtest / replay workflows but NOT exposed in `daily_signals.py`.

#### User Story B.1 — Researcher invokes WC-10 in backtest configs (Priority: P1)

**As a** researcher running backtest experiments
**I want to** enable WC-10 via `PARAMS.json` config overrides in my experiment dir
**So that** I can compare scalar-mode outputs against 5-tier baselines without committing to operator-facing deployment

**Acceptance criteria**:
- Existing PARAMS.json `wc_10_enabled: true` + `wc_10_filter_mode: "bypass"` (per spec 108) continues to work unchanged
- `scripts/backtest.py` + `scripts/wc_10_pilot.py` continue to support the WC-10 mode (already done in spec 108 / pilot harness)
- `daily_signals.py` does NOT expose the `--wc-10-enabled` flag in this branch (branch A only)
- Documentation note in `docs/SIGNALS.md` explains why WC-10 is research-only at the current evidence basis

### Branch C — NULL (v2 `|r| < 0.197`)

**Trigger**: v2 produces no detectable correlation at n=100. Critical r at n=100/p=0.05 is ~0.197; if observed `|r|` is below that, the scalar magnitude carries no information beyond the binary commit/abstain decision the bin already captures.

**Deployment**: **bin-then-output ergonomic-only** — WC-10 stays internal as a partial-confidence intermediate representation, but external output reverts to 5-tier categorical. The schema fix gives operators no false-precision claim, but the internal continuous representation may still help PM-stage reasoning quality.

#### User Story C.1 — Internal continuous representation, external 5-tier (Priority: P1)

**As the** PM agent producing a rating
**I want to** internally compute a scalar in [-1, +1] then bin to 5-tier for emission
**So that** the framework retains any reasoning-quality benefit from continuous internal reasoning while NOT making false-precision claims to operators

**Acceptance criteria**:
- New PARAMS.json key `wc_10_internal_only: true` (default false) — emits 5-tier externally regardless of `wc_10_enabled` flag
- `daily_signals.py` does NOT expose this flag; it's a `PARAMS.json`-only research mode for testing whether continuous-internal helps reasoning quality
- The `bin_scalar_to_tier` function from spec 108 is the canonical bin function; no new bin function needed

### Branch D — Both v2 NULL + v3 ALT-A

**Trigger**: v2 produces `|r| < 0.197` AND v3 produces ALT-A (bear-regime amplification is actively wrong).

**Deployment**: **WC-10 stays research-only; v1 pilot remains the canonical ANALYSIS reference; no production surface added.** The v1.5.0 Constitution amendment caveat is strengthened to "WC-10 is regime-conditional AND magnitude-uninformative; the schema fix is real but not load-bearing for production workflows." Spec 009 closes via SKIP retrospective.

## Functional Requirements (apply to whichever branch ships)

### FR-001 — Default off

WC-10 production deployment is opt-in. Operators must explicitly invoke `--wc-10-enabled` (Branch A) or set `wc_10_enabled: true` in PARAMS.json (Branch B/C). Branch D ships zero new operator surface.

### FR-002 — 5-tier fallback for downstream consumers

All branches MUST preserve 5-tier output as the default external representation. Existing downstream consumers (memory log, paper trade harness sizing, signal CSV consumers) MUST continue to work without modification.

### FR-003 — Filter chain compatibility

The filter chain (A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → spec X-1) operates on 5-tier `pre_rating`. WC-10 modes that emit scalar externally MUST bin to 5-tier BEFORE filter evaluation — filters are NOT scalar-aware.

Branch A's daily_signals.py integration MUST run filters on the binned 5-tier rating, then emit BOTH the scalar and the binned-and-filtered tier in the digest. Branch C's internal-only mode is implicitly compatible (filters see binned tier as today).

### FR-004 — Constitution VII v1.5.0 alignment

Per v1.5.0, the "Schema-induced abstention is NOT calibrated abstention" carve-out applies WHERE schema-induced collapse can be demonstrated empirically. The v1 + v2 ticker cohorts establish the bullish-amplification case (NVDA Buy n=6 mean +4.67% α 21d → confirmed across ≥3 of 8 v2 tickers required for branch A activation). Tickers OUTSIDE that empirical scope fall back to original VII (genuine balance → Hold preserved).

### FR-005 — Sample-size cohort requirement

Branch A activation requires n ≥ 6 of 8 v2 tickers exhibiting ≥80% commit rate (per v2 ANALYSIS_TEMPLATE secondary metric). If only 3-5 tickers exhibit the pattern, downgrade to Branch B (research-only). If 0-2 tickers, downgrade to Branch D.

### FR-006 — Bear-regime documentation

Branch A deployment MUST include a `docs/SIGNALS.md` warning section noting:
1. v3 verdict (NULL/ALT-A/ALT-B/PARTIAL) and what it implies for bear-regime tickers
2. The cohorts where WC-10 is empirically validated (NVDA + AAPL + the v2 tickers that hit the FR-005 threshold)
3. The cohorts where WC-10 is NOT empirically validated (operators apply WC-10 to those tickers at their own risk)

If v3 produces ALT-A, Branch A deployment ALSO requires a regime-aware gating: WC-10 mode disabled when `bear_regime_detected = True` per a new operator-tunable signal (TBD; could reuse existing macro VIX > X heuristic).

## Out of scope (v1)

- **Auto-detection of bear regime** for FR-006 gating: deferred until v3 verdict + a separate ablation determines what regime signal is operator-tunable
- **Per-ticker WC-10 enable/disable**: cohort-level enable per FR-005; finer granularity deferred
- **Continuous → 3-tier compatibility for Trader stage**: Trader stays Buy/Hold/Sell; WC-10 only operates at PM stage
- **Memory log scalar storage**: memory log retains 5-tier rating per spec 108 OOS item; scalar lives only in state log + emit_csv if enabled

## Operational characteristics

- **Branch A cost**: $0 LLM (consumes existing daily_signals.py output; the WC-10 schema doesn't add propagate cost)
- **Branch B cost**: $0 (research-only; backtest costs are tracked per experiment)
- **Branch C cost**: $0 (internal-only)
- **Branch D cost**: $0 (no deployment)

## Spec-kit bundle plan (assuming Branch A or B activation)

Per `reference_speckit_6pr_workflow_pattern.md` + Spec 011 FR-006:

1. **PR #X+0** — spec.md (this PR — already drafted as conditional)
2. **PR #X+1** — plan.md (3-day estimate after v2 + v3 verdicts land)
3. **PR #X+2** — tasks.md
4. **PR #X+3** — MVP implementation
5. **PR #X+4** — Tests
6. **PR #X+5** — Polish + retrospective markdown citing v1 + v2 + v3 ANALYSIS

Estimated wall-clock from v2 verdict landing → Branch A merge: ~1 day.

## Test plan (for the spec itself, not code)

- [x] All 4 verdict-conditional branches scaffolded with concrete trigger criteria
- [x] FR-001 through FR-006 cover all branches consistently
- [x] Constitution v1.5.0 alignment explicit (FR-004)
- [x] Spec 011 6-PR bundle pattern referenced (PR plan section)
- [x] FR-005 cohort threshold (≥6 of 8 tickers @ ≥80% commit rate) cross-references v2 ANALYSIS_TEMPLATE secondary metric
- [ ] First branch activation triggered by v2 + v3 verdicts (deferred — verdicts in flight)

## Cross-references

- `specs/108-wc-10-continuous-scalar-rating/spec.md` (v1 spec)
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1 verdict)
- `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS_TEMPLATE.md` (v2 template; activates FR-005)
- `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS_TEMPLATE.md` (v3 template; activates FR-006)
- Constitution v1.5.0 Principle VII sub-section "Schema-induced abstention is NOT calibrated abstention"
- Spec 011 (`specs/011-behavioral-additive-procedure/spec.md`) — orthogonal; both Specs 011 + 009 are methodology/conditional specs landing while pilots run
