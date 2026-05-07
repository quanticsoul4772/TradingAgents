# Hypothesis: spec-008-hybrid-c-ab-ablation

**Experiment ID**: `2026-05-07-001-spec-008-hybrid-c-ab-ablation`
**Created**: 2026-05-07
**Source idea**: Spec 008 SC-009 (live-mode A/B ablation requirement before any future default-on flip of `hybrid_c_calendar_boost_enabled`)
**Cost estimate**: ~$18 LLM (~36 propagates × $0.50 avg)
**Cost tier**: T2 (standard, $5 – $30)

## What we're testing

Whether the +3.35pp bull-side net Δα improvement Hybrid C showed on the retrofit cohort (`claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`) holds on FRESH live propagates.

The retrospective measured the boost mechanism on cached Spec 007 Opus scores from the 18-ticker / 94-commit retrofit cohort spanning 2025-08 through 2026-04. The retrofit doesn't validate that the +3.35pp generalizes to NEW propagates against fresh data — production behavior may differ from in-sample because (a) the cached scores are a frozen snapshot, (b) the LLM calls on fresh inputs may produce different score distributions, (c) the days-to-earnings distribution on a 2026-05-07-onwards live universe differs from the historical cohort.

This experiment runs `scripts/backtest.py` with `hybrid_c_calendar_boost_enabled=True` over the same 18-ticker universe across 2 fresh trade dates (2026-04-17 + 2026-04-24) for n=36 propagates. Because Hybrid C is pure post-processing of Spec 007's already-paid LLM call, a single boost-enabled propagate captures BOTH branches of the ablation in its state log:

- `state["forward_catalyst"]["bull_case_priced_in"]` — the underlying Spec 007 score
- `state["forward_catalyst"]["effective_bull_score"]` — the boosted score
- `state["forward_catalyst"]["fired_bull"]` — actual fire decision under boost-ON
- post-hoc compute: `would_fire_bull_unboosted = bull_case_priced_in > 0.60 AND rating in {Buy, OW}` — the boost-OFF decision

After the 21-trading-day forward window closes (~2026-06-04 for the 2026-05-07 dates; ~2026-05-29 for the 2026-04-30 dates), realized α-vs-SPY at 21d will be measurable for each propagate. The ANALYSIS.md compares boost-ON vs boost-OFF kept-set α and tests the SC-009 gate.

**Knob varied**: `hybrid_c_calendar_boost_enabled` flipped from `False` (Spec 008 default) → `True` for this experiment only.
**Baseline**: Spec 007 production-default behavior (boost OFF; bull_case_priced_in > 0.60 fire decision).
**All other knobs held constant**: same model (Sonnet+Haiku+Opus per main.py), same exa news vendor, same A3 + spec 003 + spec 003.5 filters at default-active, same spec 007 thresholds (T_bull=0.60, T_bear=0.50).

## Why we expect the +3.35pp to hold within ±1pp at 21d

The retrofit-cohort effect is grounded in a structural mechanism (earnings-proximate commits are more likely to have the bull case priced in by the rally into earnings). This mechanism is forward-looking and not specific to the historical cohort; a fresh cohort with similar earnings-proximity distribution should produce similar discrimination.

Counter-considerations:
- **Cohort size risk**: n=36 propagates is small. Expected n_fired under boost ≈ 14 (37/94 baseline rate). Variance bands at n=14 may exceed the ±1pp tolerance band of SC-009.
- **Earnings calendar coverage**: only commits where the ticker has earnings within 14 days of trade_date will see boost > 0. From the retrofit, that was ~50% of bull commits. So expected n_boost-fired ≈ 7.
- **Live LLM variance**: same-prompt rerun-variance is non-trivial (Constitution VII Replicability-scope clarification, 2026-05-03). The bull_case_priced_in score on a fresh call may differ from the cached value.

Bayesian prior at start of experiment: 0.55 on "+3.35pp holds within ±1pp at 21d, n=36". This sample size is intentionally borderline-sufficient; if the result is inconclusive (within ±2pp), a follow-up experiment expanding to n=60+ would be the natural next step.

## Success criterion

- [ ] **SC-009 gate**: bull-side net Δα improvement (boost-ON kept α minus boost-OFF kept α) is in [+2.35pp, +4.35pp] (= +3.35pp ± 1pp tolerance)
- [ ] **Adequate fire count**: n_fired-bull under boost-ON ≥ 8 (binomial confidence band stable)
- [ ] **Boost actually engaged**: at least one propagate has `state.forward_catalyst.calendar_boost > 0` (sanity check that the integration is live)

If all three: PASS, recommend Spec 008 v2 amendment to flip `hybrid_c_calendar_boost_enabled` default to `True`.
If gate fails but n_fired ≥ 8: SKIP default-on flip; document the period-conditional limitation; consider expanded n=60+ follow-up.
If n_fired < 8: INCONCLUSIVE; expand cohort and rerun (additional experiments at the same cost tier).

## Notes

- Live A/B ablation uses backtest.py (not daily_signals.py) for corpus integration per Constitution I (Save Everything). The state-log format is identical; results.csv is tagged with this experiment ID for findings_aggregate.py pickup.
- Realized α requires a 21-trading-day forward window. Wall-clock timeline:
  - 2026-04-17 dates → realized α measurable ~2026-05-15 (21 trading days forward + 1 day yfinance settle)
  - 2026-04-24 dates → realized α measurable ~2026-05-22
  - ANALYSIS.md cannot be written until the later date; this is the SC-009 wall-clock cost (~15 days from today).
- **Date selection rationale**: 2026-04-17 + 2026-04-24 are the two Fridays just AFTER the cohort window ends (cohort spans 2025-08 through 2026-04-03). Picking dates outside the cohort avoids leakage from cached scores while preserving market-regime continuity (same-quarter as cohort end). Both Fridays are >7 calendar days back from today (per backtest.py date filter) and have NOT had realized α computed yet (forward window still open on both). This satisfies the SC-009 "fresh propagates" intent — fresh LLM calls AND fresh dates not seen during retrofit.
- Boost-OFF comparison is post-hoc (computed from `bull_case_priced_in` in the state logs without re-running). This avoids running 60+ propagates; the savings are ~$15.
- Cost tier: T2 ($5-30). At ~$18 LLM, this is the lower-T2 band — well within tier budget. Per Constitution III T2 deliberation requirement, cost is justified by the SC-009 gate that mandates n≥30 fresh propagates.
- Uses the SAME 18 tickers as the validated retrofit cohort (NVDA, MSFT, AAPL, WFC, MA, COP, INTC, GOOGL, AMD, AMZN, AVGO, BAC, CSCO, GS, JPM, LLY, CVX, HON) but on FRESH dates. Variety in days_to_next_earnings is preserved by the ticker selection (mix of earnings-near + earnings-far names).

## Related experiments

- `2026-05-03-007-opus47-30pair-mixed` — first Opus-30-pair single-period ablation
- `2026-05-03-008-opus47-cross-period` — Q4 2025 cross-period validation showing realized-α flip
- `2026-05-04-001-nvda-q3-2025-micro` — Q3 2025 third-period recovery; reasoning_evidence posterior recovered 0.52 → 0.63
- `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md` — retrofit verdict (PASS bull-side at window=14d magnitude=0.5x)
- `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` — Spec 007 Opus retrospective (PASS, the retrofit's underlying score source)
- `specs/007-calendar-boost-filter/` — Spec 008 spec.md (defines SC-009 ablation procedure)
