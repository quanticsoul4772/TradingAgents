> **⚠️ SUPERSEDED by [`sc-009-backtest-complete-final-state-2026-05-07-night.md`](sc-009-backtest-complete-final-state-2026-05-07-night.md)** — SC-009 mid-flight diagnostic at 23/36 rows; backtest later completed at 36/36 rows. Preserved as research record per Constitution Principle I.

---

# SC-009 23-row trajectory mark — analyzer reports PRELIMINARY PASS

**Date**: 2026-05-07 evening
**Backtest**: `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/`
**Trigger**: Re-ran `scripts/analyze_sc009_ab.py` at the 23-row mid-flight
mark (per PR #50 followup). Significant trajectory change vs earlier
13-row diagnostic.

## Headline trajectory shift

| Gate | 13-row mark (earlier) | 23-row mark (now) | Change |
|---|---|---|---|
| Gate 1 (alt suppressed-α in [-10%, +2%]) | PASS at -4.44% | **PASS at +1.82%** | sign flip |
| Gate 2 (n_fired_boost_on ≥ 8) | FAIL/RISK at 3 | **PASS at 8** | +5 fires |
| Gate 3 (boost engaged ≥ 1 row) | PASS at 7 | **PASS at 14** | +7 |
| Verdict | INCONCLUSIVE | **PASS — recommend default-on flip** | upgraded |

## Headline numbers

```
n_bull_commits total:   8       (was 3 at 13 rows)
n_fired_boost_on:       8       (100% fire rate maintained)
n_fired_boost_off:      8       (post-hoc; boost changed 0 decisions)
Bull baseline α:        +1.82%  (was -4.44%; sign flipped)
Boost-ON kept α:        N/A     (no rows kept; 100% fire rate)
Boost-OFF kept α:       N/A     (same)
Decisions changed by boost: 0
Net Δα improvement:     N/A     (standard gate undefined; alt fallback)
```

## CRITICAL CAVEAT: realized α uses PARTIAL data

The analyzer reports "Realized α: 24 measurable, 0 pending" but the
21-day forward windows have NOT actually closed for the SC-009 cohort:

- 2026-04-17 + 21 trading days ≈ **2026-05-18** → window closes in
  ~11 days
- 2026-04-24 + 21 trading days ≈ **2026-05-26** → window closes in
  ~19 days

Today is 2026-05-07. The fetch_returns helper is likely using whatever
forward data is available (partial windows clipped to today), reporting
those as "measurable." **The α values shown are PRELIMINARY**.

**Final SC-009 verdict cannot be issued until 2026-05-22 or later** when
the actual 21-day forward windows close for both date cohorts.

This is consistent with the SC-009 ANALYSIS.md skeleton (`experiments/
2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS.md`) which
explicitly states the realized α timeline as ~2026-05-22.

## What is meaningful vs preliminary at this mark

**Meaningful (count-based, not α-dependent)**:
- Gate 2 (n_fired_boost_on ≥ 8): **PASS at 8** — this is a structural
  count, robust to α data completeness. As more rows land it can only
  grow.
- Gate 3 (boost engaged ≥ 1 row): **PASS at 14** — same robustness.
- 100% fire rate confirmed (8 of 8 bull commits fired) — robust to α
  data completeness.

**Preliminary (α-dependent, will shift as windows close)**:
- Gate 1 (alt suppressed-α direction): currently +1.82% but this WILL
  change as more days of forward data accumulate. The +1.82% is
  computed against PARTIAL forward windows, not the canonical 21d
  measurement.
- The "PASS — recommend default-on flip" verdict line is therefore
  TENTATIVE. Final verdict requires the canonical 21d window
  completion.

## Trajectory analysis

### From 13 rows → 23 rows: what changed

The 13-row mark had 3 bull commits (all NVDA/MSFT/AAPL early). The
23-row mark has 8 — a +5 increase in bull commits over the 10 new
rows. Per the deep-dives:
- AMZN-04-17: pre=Overweight, fired_bull=True (PR #50 F-1) — adds 1
  to the bull commit count
- The other 4 new bull commits aren't yet identified by deep-dive;
  could include NVDA-04-24 (which we saw had pre=Overweight in the
  PR #41 sweep), pre=OW rows on AMZN-04-24, etc.

Worth running the sweep refresh again to identify the 4 unidentified
bull commits — but tomorrow's session can do that with full data.

### Suppressed α sign flip: -4.44% → +1.82%

This is the most consequential preliminary change. Earlier the
suppressed cohort was clearly negative (filter was catching losers).
Now the suppressed cohort is slightly positive (filter is suppressing
slight winners on average).

Two competing interpretations:
1. **Filter over-suppression**: as more bull commits land (8 vs 3),
   the average across the suppressed cohort regresses toward zero or
   slightly positive. The +1.82% within the [-10%, +2%] band still
   PASSES alt gate-1 — just barely.
2. **Partial-window artifact**: the +1.82% reflects PARTIAL forward
   data, NOT the canonical 21d window. The sign could shift back
   negative as the 21d windows close.

Either interpretation is consistent with the data. The final verdict
must wait for canonical windows.

## Implications for SC-009 verdict storyline

1. **Best case (final verdict matches preliminary PASS)**: Spec 008
   v2 default-on flip proposal proceeds. CHANGELOG + production
   default flip + corresponding spec amendment.

2. **Mid case (gates 2+3 PASS but gate 1 marginal at canonical 21d)**:
   shadow-mode-first launch per Constitution VIII v1.4.0. Spec 008
   stays default-off but with active monitoring.

3. **Worst case (gate 1 FAILs at canonical 21d e.g. suppressed α >
   +2%)**: SKIP default-on flip; spec 008 stays operator-opt-in. This
   would be a meaningful negative result: the filter suppresses too
   many winners.

The trajectory direction (gates 2+3 strengthening; gate 1 marginal
but flipping toward over-suppression) suggests the **mid case** is
most likely. We'll know definitively in ~15 days.

## Implications for v1.4.4 ratification (different question)

**v1.4.4 ratification is INDEPENDENT of SC-009 verdict.** The
behavioral-additive evidence (PRs #41, #43, #45, #46, #50) is about
PM-decision correlation with contrarian signals — a STRUCTURAL claim
about LLM-debate-ensemble behavior, not a claim about realized α
performance.

The PR #44 v1.4.4 draft decision matrix lists "SC-009 finishes without
counter-evidence" as a pre-ratification check. The 23-row mark shows:
- Counter-evidence watch (PR #49 script): still 0 refuting rows
- All 4 mechanism classes still showing behavioral-additive evidence
- All previous deep-dive findings still hold

So v1.4.4 ratification is still UNBLOCKED (counter-evidence axis), and
the "SC-009 finishes" check just means SC-009 needs to complete (not
that the SC-009 verdict needs to be PASS or FAIL specifically).

## Followups

1. **Re-run analyzer when SC-009 hits 36 rows** (final), then again
   when canonical 21d windows close (~2026-05-22). Note these as
   key dates for final SC-009 ANALYSIS.md.
2. **Identify the 4 unaccounted bull commits**: re-run sweep refresh
   to locate which 4 new bull-pre rows landed between 13-row and
   23-row marks. ~5min. Defer to tomorrow.
3. **SC-009 ANALYSIS.md update**: amend the skeleton (`experiments/
   2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS.md`) with
   the 23-row preliminary numbers and explicit caveat about partial
   forward windows. ~15min, $0. Defer; not v1.4.4-blocking.

## Sibling docs

- `claudedocs/sc-009-mid-backtest-commit-pattern-2026-05-07.md` — earlier
  13-row mid-flight diagnostic
- `claudedocs/amzn-2026-04-17-04-24-deep-dive-2026-05-07-evening.md` —
  PR #50 (AMZN-04-17 first operational fire event)
- `claudedocs/constitution-v1.4.4-draft-2026-05-07.md` — PR #44 draft
  (independent of SC-009 verdict per discussion above)
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS.md`
  — auto-updated by the analyzer with the 23-row numbers
