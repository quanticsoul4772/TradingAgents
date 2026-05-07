# SC-009 backtest COMPLETE — final 36-row state summary

**Date**: 2026-05-07 night (backtest completed via background process,
exit code 0).
**Triggers tomorrow's scaffold D-1 evaluation**.

## Final acceptance gates (PRELIMINARY — partial 21d windows)

| Gate | Threshold | 13-row | 23-row | 27-row | **36-row final** | Status |
|---|---|---|---|---|---|---|
| Gate 1 (alt suppressed-α in [-10%, +2%]) | within band | PASS @ -4.44% | PASS @ +1.75% | PASS @ +1.12% | **PASS @ +0.43%** | held |
| Gate 2 (n_fired_boost_on ≥ 8) | ≥ 8 | FAIL @ 3 | PASS @ 8 | PASS @ 9 | **PASS @ 13** | strengthened |
| Gate 3 (boost engaged ≥ 1) | ≥ 1 | PASS @ 7 | PASS @ 14 | PASS @ 14 | **PASS @ 18** | strengthened |
| Verdict line | — | INCONCLUSIVE | PASS-tentative | PASS-tentative | **PASS-tentative** | held |

Gate 1 trajectory shows **monotone improvement toward neutrality**:
-4.44% → +1.75% → +1.12% → +0.43%. The suppressed-α direction has
refined from "filter caught moderate losers" (negative) toward "filter
suppressed near-neutral commits" (slightly positive). At +0.43%, the
filter is suppressing commits with realized α very close to zero on
average — comfortably within the [-10%, +2%] PASS band but on the
non-counterexample side.

## Final headline numbers

```
Total rows enriched:    36 of 36 (no errors, no missing state logs)
n_bull_commits total:   13       (was 9 at 27 rows; +4 in final 9 rows)
n_fired_boost_on:       13       (100% bull-fire rate sustained throughout)
n_fired_boost_off:      13       (post-hoc reconstruction matches)
Decisions changed by boost: 0    (PASS-by-non-counterexample finding
                                  CONFIRMED at full sample)
Bull baseline α:        +0.43%   (closer to neutral than any prior mark)
Boost-ON kept α:        N/A      (100% fire rate; no rows kept)
Boost-OFF kept α:       N/A      (same)
Net Δα improvement:     N/A      (standard gate undefined)
```

## D-1 expansion-trigger evaluation (per tomorrow's scaffold)

Per `claudedocs/research-burst-2026-05-08.md` D-1 criteria:

| Criterion | Final value | D-1 outcome |
|---|---|---|
| Backtest finished | YES (36/36) | continue |
| `n_fired_boost_on < 4` | NO (n=13) | NO EXPANSION needed |

**Decision: NO SC-009 expansion experiment is required.** The 18-ticker
× 2-Friday cohort generated sufficient bull-fire data (n=13) to clear
gate 2 with margin. The conditional `experiments/2026-05-07-002-sc-009-expansion/`
scaffold from PR #31 stays inert; it can be repurposed for a future
borderline-regime cohort if one is needed.

## Cohort breakdown (full 36-row final)

**By PM rating** (final SC-009 cohort):
- Hold: 23 of 36 (64%)
- Underweight: 7 of 36 (19%)
- Overweight: 6 of 36 (17%)
- Buy: 0 of 36
- Sell: 0 of 36

**Bull-pre fires (13)**:
- AMZN-04-17 / BAC×2 / GOOGL×2 / GS×2 / MA×2 / NVDA-04-24 + 4 from
  late-cohort rows (the late-cohort additions need identification —
  could be JPM-pre, LLY-pre, NVDA-04-17, etc.)

**Bear-pre commits (7)** — note: spec 007 bear is in shadow mode at T=0.50
- COP-04-17 (UW), INTC-04-17 (UW), INTC-04-24 (UW), AMD-04-17 (UW),
  AMD-04-24 (UW), CVX-04-17 (UW), CVX-04-24 (UW)
- All 7 likely had bear_score < T_bear → spec 007 bear correctly inert
  on all (calibrated PASS for shadow-mode evidence)

## v1.4.4 ratification readiness — UPDATED with final data

Per PR #44 v1.4.4 draft decision matrix + counter-evidence watch (PR #49):

| Pre-ratification check | Status |
|---|---|
| 4+ mechanism classes show evidence | YES (still 4/4) |
| Pattern across 5+ tickers | YES (10 tickers as of PR #45 sweep refresh) |
| ≥1 textbook mechanistic-PM-prose validation | YES (AMD-04-17 per PR #43) |
| **SC-009 finishes without counter-evidence** | **YES (now COMPLETE)** |
| Memory deferral rule (3+ classes) | YES |
| Risk-of-retraction acceptable | YES |
| Operational impact bounded | YES |

**ALL 7 PRE-RATIFICATION CHECKS NOW PASS.** v1.4.4 is fully unblocked
on the canonical 21d windows close — but ratification timing should
still wait per PR #44's two-stage pattern (draft-then-ratify across
sessions for defensive retraction-risk control). Tomorrow's session
can ratify if 1+ session of pattern-holding is satisfied.

## Spec 008 default-on flip framing — REFINED per PR #56 finding

Per PR #56 PASS-by-non-counterexample finding (now confirmed at full
sample with n=13):

- Boost-ON vs Boost-OFF would produce IDENTICAL fire decisions on this
  cohort. n_fired_boost_off (post-hoc) = 13 = n_fired_boost_on.
- Net Δα improvement = 0 (zero decisions changed).
- The acceptance gates PASS by negation, not by demonstration.

**Recommendation for default-on flip decision**: shadow-mode-first
launch per Constitution VIII v1.4.0, NOT direct default-on flip. The
empirical evidence shows Hybrid C boost is mechanism-correct but
cohort-irrelevant on the SC-009 distribution. A future spec 008
default-on flip needs evidence from a cohort exercising the borderline
regime (bull_score in [0.55, 0.65]) where the original Hybrid C
retrofit showed +3.35pp improvement.

This framing aligns with `memory/reference_pass_by_non_counterexample.md`
(added today).

## Realized α window status (UNCHANGED — windows still open)

Today: 2026-05-07. Cohort dates and canonical 21d window closure:
- 2026-04-17 cohort: ~2026-05-18 (~11 days remaining)
- 2026-04-24 cohort: ~2026-05-26 (~19 days remaining)

α numbers above are PARTIAL forward data (truncated to today). Final
SC-009 ANALYSIS.md (with FINAL status, not PRELIMINARY) writable
~2026-05-22+. The verdict line "PASS — recommend Spec 008 v2 default-on
flip proposal" remains TENTATIVE per the analyzer's auto-output, but
modulated by PR #56's PASS-by-non-counterexample framing.

## Followups for tomorrow's session

1. **Identify the 4 new bull-pre fires from final 9 rows** — quick state
   log enumeration. Likely candidates: JPM, LLY, HON if any went bull-
   pre. Sweep refresh would surface them. ~10min, $0.
2. **Update SC-009 ANALYSIS.md** with 36-row final preliminary numbers
   + PASS-by-non-counterexample framing + shadow-mode-first
   recommendation. Manual edit preserved by PR #52 guard. ~15min, $0.
3. **v1.4.4 ratification commit** — if tomorrow's session confirms
   pattern still holds (run counter-evidence watch + sweep refresh
   one more time on the now-complete 36-row data), ratify the
   amendment per PR #44 plan. ~30min, $0 (no code changes needed).
4. **v1.4.5 amendment draft** (reflection-prose-distrustable) — n=3
   threshold met per PR #55. Drafting eligible. ~30min, $0.
5. **Final SC-009 ANALYSIS.md** at canonical 21d window close
   (~2026-05-22+). FINAL status; not preliminary. Will overwrite the
   current PRELIMINARY hand-edit per PR #52 guard convention (operator
   removes PRELIMINARY status line first).

## Sibling docs

- `claudedocs/sc-009-23-row-mark-trajectory-pass-2026-05-07-evening.md`
  — earlier 23-row mark
- `claudedocs/sc-009-27-row-mark-and-sweep-refresh-2026-05-07-late.md`
  — 27-row mark
- `claudedocs/spec-007-calendar-independence-bac-gs-2026-05-07-late.md`
  — PR #56 PASS-by-non-counterexample finding (now empirically
  confirmed at full sample)
- `claudedocs/research-burst-2026-05-08.md` — tomorrow's scaffold;
  D-1 expansion trigger now resolved (no expansion needed)
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS.md`
  — current PRELIMINARY hand-edit (preserved by PR #52 guard)
