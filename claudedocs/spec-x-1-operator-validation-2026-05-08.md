# Spec X-1 operator validation — 2026-05-08

**Date**: 2026-05-08
**Cost**: ~$0.40 (1 propagate: NVDA @ 2026-05-01 with Sonnet 4.6 deep + Haiku 4.5 quick)
**Verdict**: **OVERALL PASS** — Spec X-1 deployed annotation appears correctly in production state logs

## Trigger

PR #93 (2026-05-07) shipped Spec X-1 (C-4 institutional rotation filter) at default-shadow bear-side / default-off bull-side. Per Constitution VI (Spec Before Structural Change) + the user-authorized validation pattern, this doc captures the first end-to-end production verification that the deployed filter behaves per spec.

Sister artifact: SC-001 reproduction gate (`tests/test_paper_sc003_reproduction.py`) PASSED in 64s — paper-trading harness still reproduces the SC-003 bullish-bucket mean α within ±150 bps. Spec X-1 deployment did not regress the paper-trading replay invariant.

## Validation harness

`scripts/spec_x_1_operator_validation.py` (~110 LOC). Single-shot validation:

1. Build a TradingAgentsConfig with production defaults (Anthropic Sonnet/Haiku; default Spec X-1 shadow/off modes; default 0.05 outflow threshold)
2. Run `propagate(ticker, date)` end-to-end through the full pipeline (analysts → debate → trader → risk debate → PM with all 9 filters in chain)
3. Read `final_state["forward_catalyst"]["institutional_rotation"]`
4. Assert 8-field schema + 7 value/type checks
5. Exit 0 on PASS, 1 on FAIL

CI-friendly. Re-runnable on operator opt-in (e.g., before flipping bear_mode to "active" per SC-010 live-mode flip eligibility gate).

## Run results

```
[validation] Propagating NVDA @ 2026-05-01...
[validation] PM decision: Hold

[validation] state['forward_catalyst']['institutional_rotation']:
{
  "net_rotation_pct": -0.5508999966000001,
  "outflow_threshold": 0.05,
  "bear_mode": "shadow",
  "bull_mode": "off",
  "would_fire_bear": false,
  "fired_bear": false,
  "pre_rating": "Hold",
  "post_rating": "Hold"
}

[validation] schema + value checks:
  [PASS] bear_mode is shadow (default)
  [PASS] bull_mode is off (default)
  [PASS] outflow_threshold is 0.05 (default)
  [PASS] net_rotation_pct is float or None
  [PASS] would_fire_bear is bool
  [PASS] fired_bear is False (shadow mode)
  [PASS] pre_rating == post_rating (shadow mode preserves rating)

[validation] OVERALL PASS — Spec X-1 annotation appears correctly
```

## Empirical observations

**1. NVDA institutional rotation is dramatically negative**: `net_rotation_pct = -0.5509` (= -55.09% net outflow across top 10 institutional holders). This is **11× the -5% T_outflow threshold**. The data quality is consistent with the PR #75 retrospective basis (Q4 2025 13F era; institutions have been net-selling NVDA aggressively).

**2. Filter did NOT fire because pre_rating = Hold, not bearish**. This is the textbook `reference_pm_hold_regime_starves_filters.md` pattern: when PM picks Hold from start (Constitution VII Calibrated Abstention), filters gating on bearish pre_ratings have nothing to suppress. The filter implementation is correct — it would fire if pre_rating were Underweight or Sell.

**3. Annotation persistence works**. The 8-field annotation appeared in `final_state["forward_catalyst"]["institutional_rotation"]` exactly as specified in the spec. No schema drift, no missing fields, no unexpected extras.

**4. Cost-per-propagate observed**: ~$0.40 (matches CLAUDE.md estimate). Single-ticker cost is operator-affordable as a routine validation.

## Constitution VIII v1.4.0 small-sample-caution adherence

The shadow mode is doing its job: the filter is observing without mutating ratings. To exit shadow mode per SC-010 live-mode flip eligibility, operator needs n≥30 propagates AND verify SC-009 retrospective metrics still hold (~2026-05-15 Q1 2026 13F refresh).

This propagate (NVDA-2026-05-01) counts as **n=1** toward the SC-010 ablation cohort. 29 more shadow-mode propagates needed before the operator can responsibly flip bear_mode to "active".

## SC-001 reproduction gate (sister verification)

Run as part of this validation session:

```
$ uv run --no-sync pytest tests/test_paper_sc003_reproduction.py -v -m integration
========================== 1 passed in 63.94s (0:01:03) ==========================
```

Paper-trading harness (Spec 002) replay over the SC-003 corpus reproduces the bullish-bucket mean α within ±150 bps tolerance. Spec X-1 deployment did NOT introduce paper-trading regressions.

## What this validation does NOT prove

- **Does NOT prove Spec X-1 alpha-generates in production**. That requires SC-010 live ablation (n≥30 propagates A/B) + comparing kept-vs-suppressed alpha. This validation only proves the annotation appears + the filter doesn't crash.
- **Does NOT prove the empirical evidence base holds on Q1 2026 13F panel**. That requires SC-009 (re-run `forward_catalyst_class4_retrospective.py` after ~2026-05-15 13F refresh).
- **Does NOT prove the filter would have fired correctly on the n=12 cohort**. That's already validated by PR #75 retrospective; this is forward-going production verification, not retrospective re-validation.

## Re-runnable harness

To re-run anytime:

```bash
uv run --no-sync python scripts/spec_x_1_operator_validation.py
# Default: NVDA @ 2026-05-01

# Different ticker / date:
uv run --no-sync python scripts/spec_x_1_operator_validation.py --ticker MSFT --date 2026-05-01
```

## Sibling docs

- `specs/091-c4-institutional-rotation/spec.md` — Spec X-1 specification (PR #88)
- `specs/091-c4-institutional-rotation/contracts/institutional_rotation_filter.md` — module API contract (PR #89)
- `claudedocs/SETUP.md` section 10 — operator usage guide (PR #94)
- `claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` — PR #75 standalone gate
- `claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md` — PR #77 additive overlap
- `tradingagents/agents/utils/institutional_rotation_filter.py` — production module
- `memory/reference_pm_hold_regime_starves_filters.md` — explains why the filter didn't fire on this propagate
