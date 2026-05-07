# SC-009 expansion contingency design — 2026-05-07

**Trigger**: SC-009 backtest at `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/` (kicked off 06:14 PDT 2026-05-07) shows an all-Hold pattern in the first 5/36 rows. If this continues, `n_fired_boost_on` will be ~0 and SC-009 gate 2 (n_fired ≥ 8) FAILS → INCONCLUSIVE verdict.

**Status**: DESIGN ONLY — not run yet. Kick off only IF the original backtest confirms all-Hold (≥30 of 36 rows return Hold). Otherwise the original backtest's data suffices.

## Why all-Hold is the failure mode for SC-009

Spec 007 + Spec 008 only fire on commits where `pre_rating in {Buy, Overweight, Underweight, Sell}`. When PM picks Hold from the start (the framework's default abstention per Constitution VII), there's no commit to suppress. The forward-catalyst filter chain has nothing to act on.

For SC-009:
- Gate 1 (Δα improvement): undefined when 0 commits get filtered
- Gate 2 (n_fired_boost_on ≥ 8): FAILS at 0 fires
- Gate 3 (boost engaged ≥ 1 row): MIGHT pass (calendar_boost > 0 rows exist regardless of fire decision)

If gates 1-2 fail because the framework didn't COMMIT in the first place, the test isn't measuring Spec 008's mechanism — it's measuring the framework's Hold-regime tendency. The boost mechanism is irrelevant when the underlying rating is Hold.

## Pre-trigger empirical context

From the running backtest (5/36 rows as of 06:58 PDT):
| Ticker | Date | Rating |
|---|---|---|
| NVDA | 2026-04-17 | Hold |
| NVDA | 2026-04-24 | Hold |
| MSFT | 2026-04-17 | Hold |
| MSFT | 2026-04-24 | Hold |
| AAPL | 2026-04-17 | Hold |

5/5 Hold. Possible explanations (any combination):
1. **Spec 007 is firing**: bull_case_priced_in is high (NVDA showed 0.78 in earlier state log), spec 007 active mode downgrades Buy/OW → Hold. The PM's pre-rating MAY have been Buy/OW; the post-rating is Hold. Need to inspect state logs to distinguish.
2. **PM picks Hold natively**: 2026-04-17/24 dates were post-NVDA-rally + uncertain regime. PM may have chosen Hold from the start. State logs distinguish via `state.forward_catalyst.pre_rating` field.
3. **Tech-cluster bias**: cohort is 18 tickers but the FIRST 9 in the order (NVDA, MSFT, AAPL...) are mostly Tech. Tech tickers had unusual rallies into mid-April. PM may default to Hold on extended-rally Tech.

The state-log inspection (analyze_sc009_ab.py partial run earlier) showed NVDA 2026-04-17 had `pre_rating=Hold, post_rating=Hold` — so explanation 2 is likely. Spec 007 had nothing to suppress because PM didn't commit.

## Trigger criteria for kicking off the expansion

Kick off `experiments/2026-05-07-002-sc-009-expansion/` IF after the original backtest completes:
- ≥30 of 36 rows return Hold (>83% Hold rate); AND
- `n_fired_boost_on` < 4 (less than half the gate-2 threshold of 8)

If only ONE of those conditions fires, the original cohort is borderline and a smaller expansion (10 tickers × 2 dates = 20 propagates ~$10) suffices. If BOTH fire, larger expansion is justified.

## Expansion design

**Cohort selection** (12-15 tickers; varied to maximize bull/bear commit elicitation):
- **Bear-correct names** (recent fundamental weakness, likely PM Underweight/Sell): TSLA, BA, PARA, NIO, F (5 tickers)
- **Volatile / earnings-active**: NFLX, META, COIN, PYPL, SNAP (5 tickers)
- **From original cohort but earnings-proximate** to ensure boost engagement: pick 3 names from original 18 with `days_to_next_earnings ∈ [1, 14]` as of 2026-04-17 or 2026-04-24

**Trade dates** (2 fresh Fridays, similar logic to original):
- 2026-04-10 (Friday before 04-17; cohort doesn't include this date)
- 2026-04-24 (re-use of original-cohort Friday but with new tickers)

**Total**: 13 tickers × 2 dates = 26 propagates. Cost ~$13 LLM (T2 within budget).

**Wall-clock**: ~26 × 9 min = ~3.9h compute + ~15 days for realized α (2026-04-10 forward window closes ~2026-05-08 tomorrow; 2026-04-24 closes ~2026-05-22).

## Acceptance criteria for the expansion

Same SC-009 gate structure (3 conditions). Combined with the original backtest:
- Total propagates: 36 + 26 = 62
- Expected n_fired_boost_on (if expansion succeeds in eliciting commits): 8-15
- Variance bands tighten with combined n; gate 1 evaluation more reliable

If COMBINED data still has n_fired < 8: SC-009 INCONCLUSIVE. Document the framework's all-Hold-regime tendency as a structural finding (relates to Constitution VII Calibrated Abstention) rather than a Spec 008 verdict.

## Cost summary

- Original backtest: ~$18 (already spent; running)
- Expansion (only if triggered): ~$13
- Combined ceiling: ~$31 (T2 upper)
- ANALYSIS.md timeline: original ~2026-05-22; combined ~2026-05-22 (expansion forward windows close concurrently)

## Operational note

If the original backtest produces enough bull commits to satisfy gate 2, this expansion is NOT TRIGGERED — saves $13 + 4h compute. The contingency design exists as risk-mitigation insurance, not a guaranteed next step.

## Cross-references

- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/HYPOTHESIS.md` — original SC-009 experiment design
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS_PLAN.md` — Phase 4 SC-009 verdict tree
- `scripts/analyze_sc009_ab.py` — analyzer that will produce the verdict
- `.specify/memory/constitution.md` Principle VII — Calibrated Abstention (the all-Hold pattern's normative grounding)
- `specs/007-calendar-boost-filter/spec.md` SC-009 — the spec gate this experiment is testing
