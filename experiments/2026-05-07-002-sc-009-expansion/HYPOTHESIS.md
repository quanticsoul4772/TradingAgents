# Hypothesis: sc-009-expansion

**Experiment ID**: `2026-05-07-002-sc-009-expansion`
**Created**: 2026-05-07
**Source idea**: Spec 008 SC-009 expansion contingency (`claudedocs/sc-009-expansion-contingency-design-2026-05-07.md`) — risk mitigation against the all-Hold pattern observed in the original 2026-05-07-001 backtest
**Cost estimate**: ~\$13 LLM (~26 propagates × \$0.50 avg)
**Cost tier**: T2 (standard, \$5–\$30)
**Trigger gate**: kick off ONLY IF the original backtest 2026-05-07-001 confirms the gate-2 risk: ≥30/36 rows return Hold AND `n_fired_boost_on < 4`. Otherwise SKIP (don't run; original cohort is sufficient).

## What we're testing

Whether the SC-009 verdict from the original 2026-05-07-001 backtest's PASS/FAIL on gate 2 (`n_fired_boost_on ≥ 8`) is robust to a less-Hold-prone cohort selection.

The original backtest used 18 large-cap tickers (NVDA, MSFT, AAPL, WFC, MA, COP, INTC, GOOGL, AMD, AMZN, AVGO, BAC, CSCO, GS, JPM, LLY, CVX, HON) × 2 dates (2026-04-17, 2026-04-24). Mid-flight diagnostic showed the PM was rating Hold on most of these (calibrated abstention per Constitution VII), starving the spec 007/008 fire decisions.

This expansion adds tickers more likely to elicit bull/bear PM commits to confirm the SC-009 verdict isn't an artifact of cohort selection.

**Knob varied**: ticker selection (cohort).
**Baseline**: same `hybrid_c_calendar_boost_enabled=True` config as 2026-05-07-001; combined SC-009 evaluation = original cohort + this expansion cohort.

## Cohort selection

13 tickers chosen for higher commit-elicitation probability:

**Bear-correct candidates** (5; recent fundamental weakness or downtrend):
- TSLA (mega-cap with cycle weakness)
- BA (industrial with execution risk)
- PARA (media with secular decline)
- NIO (China EV with capital concerns)
- F (legacy auto with EV transition)

**Volatile / earnings-active** (5; high option volume + frequent quarterly catalysts):
- NFLX (post-earnings volatile)
- META (advertising sensitivity)
- COIN (crypto-correlation)
- PYPL (payments turnaround)
- SNAP (advertising-leveraged)

**Earnings-proximate from original cohort** (3; force boost engagement):
- LLY (per cohort: earnings 2026-04-30 — within 14d of 2026-04-17)
- INTC (per cohort: earnings 2026-04-24 — within 7d of 2026-04-17)
- COP (energy with Q1 earnings cycle)

Total: 13 tickers × 2 fresh Fridays = 26 propagates.

## Trade dates

- 2026-04-10 (Friday before original cohort window)
- 2026-04-24 (re-use of original Friday but with new tickers)

Both have NOT had realized α computed yet (forward windows still open as of 2026-05-07; close ~2026-05-08 for 2026-04-10 and ~2026-05-22 for 2026-04-24).

## Why this expansion strengthens the SC-009 verdict

If COMBINED data (original 36 + expansion 26 = 62 propagates):
- **n_fired_boost_on ≥ 8**: more likely to satisfy because cohort selection is biased toward commit-eliciting names
- **Gate 1 (Δα improvement [+2.35pp, +4.35pp])**: more reliable variance bands at n=62 vs n=36
- **Gate 3 (boost engagement)**: 3 earnings-proximate tickers guarantee at least 6 boost-engaged rows

## Success criterion

- [ ] **Combined SC-009 gate**: bull-side net Δα improvement (boost-ON kept α minus boost-OFF kept α) is in [+2.35pp, +4.35pp] across BOTH cohorts
- [ ] **Adequate combined fire count**: n_fired-bull under boost-ON ≥ 8 across BOTH cohorts
- [ ] **Boost engaged ≥ 1 row**: at least one propagate has `state.forward_catalyst.calendar_boost > 0` (already PASSED on original cohort with n=4)

If all three combined-cohort PASS: recommend Spec 008 v2 default-on flip (per original SC-009 design).
If gate fails on combined cohort: SKIP default-on flip; document the period-conditional / regime-specific limitation; consider a 21d-later 2026-05-28 expansion.
If still INCONCLUSIVE: structural finding documentation — spec 008 mechanism is empirically untestable on this universe + window.

## Notes

- **Trigger criteria for kicking off**: this experiment is NOT to be run unconditionally. Kick off ONLY IF original 2026-05-07-001 backtest completes with: (≥30/36 rows return Hold) AND (n_fired_boost_on < 4). Run `python scripts/analyze_sc009_ab.py --allow-partial` after original completes to verify.
- **Cost ceiling check**: combined original + expansion ≈ \$31 (T2 upper). Constitution III T2 deliberation requirement satisfied by SC-009 gate floor + expansion necessity per `claudedocs/sc-009-expansion-contingency-design-2026-05-07.md`.
- **Wall-clock**: ~26 × 9 min = ~3.9h compute. ANALYSIS.md timeline ~2026-05-22 (concurrent with original).
- **Risk**: 13 tickers selected to be more commit-eliciting, but no guarantee. If THIS cohort also returns mostly Hold, the SC-009 verdict is structurally INCONCLUSIVE — document and move on. Don't expand a third time.

## Related experiments

- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/` — original SC-009 backtest (in progress)
- `claudedocs/sc-009-expansion-contingency-design-2026-05-07.md` — original contingency design
- `claudedocs/sc-009-mid-backtest-commit-pattern-2026-05-07.md` — mid-flight diagnostic
- `claudedocs/sc-009-hold-rate-root-cause-2026-05-07.md` — root cause analysis (PM Hold-regime, not filter malfunction)
- `specs/007-calendar-boost-filter/spec.md` SC-009 — the spec gate this experiment is testing
