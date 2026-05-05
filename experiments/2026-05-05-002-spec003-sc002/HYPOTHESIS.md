# Hypothesis: spec 003 SC-002 fresh-data validation

**Experiment ID**: `2026-05-05-002-spec003-sc002`
**Created**: 2026-05-05
**Source idea**: Spec 003 SC-002 — populate AAPL/INTC/JPM/MSFT/GOOGL with fresh propagates so the contrarian gate's mechanism can be tested at scale across multiple tickers
**Cost estimate**: ~$10 (25 propagates at Opus + Haiku + 3 analysts + 1 debate round)
**Cost tier**: T2 (standard, $5-30)

## What we're testing

Three lines of evidence have already mechanically validated the gate (original IC -0.49, strict-prior IC -0.49, within-bullish-subset IC -0.42). The only remaining empirical question is whether **the gate's prospective Δα reproduces in fresh data on tickers OTHER than NVDA**.

Currently:
- NVDA has 33 cached dates → 13 N≥20-eligible → 2 gate fires in the retrospective (both negative α as predicted ✓)
- AAPL has 23, INTC has 20 (both at floor); GOOGL/JPM/MSFT have 12-13 (below floor)

This experiment adds 5 fresh mid-week propagates per ticker × 5 tickers = 25 new propagates. Each new propagate:
- Captures a fresh `market_report` and `final_trade_decision` for the (ticker, date)
- Populates the cache (closer to N≥20 floor for the under-floor tickers)
- Is annotated by the contrarian gate in shadow mode (`contrarian_gate_mode = "shadow"`)
- Will be used to compute the within-ticker IC over the now-larger corpus

Specifically tests the SC-002 success criterion: across N≥30 shadow propagates, within-ticker median IC reproduces finding #4's pattern.

## Date selection (5 mid-week Wednesdays, Q1 2026)

Picked to avoid overlap with existing weekly-Friday cache + to have full 21d forward alpha:
- 2026-03-04 (Wed)
- 2026-03-11 (Wed)
- 2026-03-18 (Wed)
- 2026-03-25 (Wed)
- 2026-04-01 (Wed)

All have 21d forward α as of 2026-05-05. Some have partial 90d data (truncated by recent dates); 21d is the primary horizon for the rating-bucket analysis.

## Per-ticker N≥20-eligibility at experiment dates

| Ticker | Existing cache n | N≥20-eligible new dates (gate can fire) |
|---|---:|---:|
| AAPL | 23 | ~3-5 of 5 (most new dates have ≥20 prior) |
| INTC | 20 | ~3-5 of 5 |
| GOOGL | 12 | 0 (still under floor; cache grows toward future) |
| JPM | 12 | 0 (still under floor) |
| MSFT | 13 | 0 (still under floor) |

Practical: ~6-10 new N≥20-eligible propagates from AAPL+INTC, plus 15 cache-growth propagates for the lower-floor tickers. Combined with NVDA's existing 13, gives ~20-25 N≥20-eligible total — close to but possibly below the SC-002 N≥30 target.

## Why we expect

**Scenario A (mechanism reproduces)** — ~60%
- Within-ticker IC on the now-larger corpus is similar to the original -0.49
- Per-ticker IC for AAPL + INTC remains negative
- Gate fires on a few AAPL/INTC bullish commits with negative α
- SC-002 is supported

**Scenario B (mechanism weakens on AAPL/INTC)** — ~25%
- Within-ticker IC is weaker than -0.30 on the new data
- Suggests NVDA-specificity of finding #4 (mechanism may be idiosyncratic)
- Spec 003 default-on-market_report would need narrower scoping

**Scenario C (gate doesn't fire on new dates)** — ~10%
- AAPL/INTC's new dates' bull_keyword_count percentiles all below threshold
- N≥20 fires count is too small to evaluate
- Need more dates per ticker (next experiment scaling up)

**Scenario D (something breaks)** — ~5%
- Run errors, incomplete data, integration issue
- Investigate, fix, re-run

## Success criterion

- [ ] 25 propagations complete with ≤2 errors (8% error tolerance, matches prior smoke runs)
- [ ] All 25 have `contrarian_gate` annotations in state log
- [ ] AAPL + INTC gate fires (would_fire=True for at least one bullish commit per ticker)
- [ ] Within-ticker IC across the now-enlarged corpus reproduces finding #4 (median ≤ -0.30)
- [ ] Total cost ≤ $15

## Notes

- **T2 tier** ($10 estimated)
- **Mid-week dates** (not Fridays) to avoid existing-cache overlap
- **Config**: `contrarian_gate_mode = "shadow"` override + standard 005/007 config
- **Memory log routed to experiment dir** — clean separation from main memory
- **Wall-clock estimate**: 25 propagates × ~8min ≈ 3.3 hours

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (mechanism reproduces) | Spec 003 SC-002 ✓ validated. Promote to active mode consideration after SC-003. |
| Scenario B (mechanism weakens) | Finding #4 is NVDA-specific. Spec 003's default scope needs narrowing. |
| Scenario C (no gate fires) | Need larger experiment. Don't promote spec 003 active. |
| Scenario D (errors) | Fix bugs; re-run subset. |

## Related work

- **Finding #4**: claudedocs/within-ticker-artifact-check-2026-05-05.md
- **Mechanism**: claudedocs/finding4-mechanism-2026-05-05.md
- **Strict-prior IC**: claudedocs/finding4-strict-prior-ic-2026-05-05.md
- **Within-bullish-subset IC**: claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md
- **Retrospective**: claudedocs/contrarian-gate-retrospective-2026-05-05.md
- **SC-001 smoke**: experiments/2026-05-05-001-spec003-sc001-shadow-smoke/
- **Spec 003**: .specify/specs/003-analyst-contrarian-gate/spec.md
