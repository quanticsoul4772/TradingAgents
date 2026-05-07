# Research-burst day — 2026-05-08 (scaffold, written 2026-05-07 evening; UPDATED 2026-05-07 night)

**Status as of LATEST UPDATE (2026-05-07 night)**: SC-009 backtest
**COMPLETED** via background process (exit code 0) at 36/36 rows. Final
acceptance gates documented in PR #57 + PR #58. ANALYSIS.md updated to
final-PRELIMINARY state. Tomorrow opens with **Scenario A confirmed**.

**Status as of original scaffold writing (afternoon)**: SC-009 backtest in
progress; ~16/36 rows. Predictions about scenarios are now obsolete —
see "Confirmed opening state" section below.

**Companion docs**:
- `claudedocs/research-burst-2026-05-06.md` — yesterday's 17-unit + 5-amendment day
- `claudedocs/research-burst-2026-05-07.md` — today's parallel-safe-during-backtest day (final tally TBD)
- `claudedocs/sc-009-backtest-complete-final-state-2026-05-07-night.md` — backtest completion summary (PR #57)

## Confirmed opening state (UPDATED 2026-05-07 night)

**Scenario A confirmed**. Backtest finished. 36/36 rows in CSV. Analyzer
already re-run with PR #52 PRELIMINARY guard preserving operator hand-edit.

Final acceptance gates (PRELIMINARY at full sample):
- Gate 1 (alt suppressed-α in [-10%, +2%]): PASS at **+0.43%** (61% margin from upper bound)
- Gate 2 (n_fired_boost_on ≥ 8): PASS at **13** fires (was predicted 4-7; actual 13 — well above threshold)
- Gate 3 (boost engaged ≥ 1): PASS at **18** rows
- Verdict line (auto-generated): PASS — recommend Spec 008 v2 default-on flip proposal
- Refined verdict (per PR #56/#57): **PRELIMINARY PASS-by-non-counterexample** — recommend SHADOW-MODE-FIRST per Constitution VIII v1.4.0, NOT direct default-on flip

**Headline**: 13 bull commits / 13 fires / 100% fire rate / **0 decisions changed by boost** (PR #56 finding empirically confirmed at full sample).

Realized α window status (UNCHANGED — windows still open):
- 2026-04-17 cohort: ~2026-05-18 (~11 days remaining)
- 2026-04-24 cohort: ~2026-05-26 (~19 days remaining)
- Final SC-009 ANALYSIS.md (FINAL status, not PRELIMINARY) writable ~2026-05-22+

## Decisions to make Tuesday morning (UPDATED 2026-05-07 night)

### D-1: SC-009 expansion contingency trigger — **RESOLVED**

Final n_fired_boost_on = 13. Per criterion `n_fired_boost_on ≥ 8`:
**NO EXPANSION needed**. The conditional `experiments/2026-05-07-002-sc-009-expansion/`
scaffold stays inert. Proceed to ANALYSIS.md FINAL writing once
realized α landings start ~2026-05-22+.

Tuesday action: none for D-1; conditional-experiment scaffold remains
available for future borderline-regime cohort if one is needed.

### D-2: v1.4.4 amendment ratification timing — **READY**

Per PR #44 v1.4.4 draft decision matrix, **ALL 7 pre-ratification checks
NOW PASS** (last one — "SC-009 finishes without counter-evidence" —
flipped from PENDING to YES per PR #57). Counter-evidence watch (PR #49)
still 0 refuting rows.

Tuesday action: **ratify v1.4.4** per PR #44 plan. Single commit modifying:
- `.specify/memory/constitution.md` (add behavioral-additive sub-section
  + bump header to v1.4.4)
- `CHANGELOG.md` (add v1.4.4 entry)
- Reference PR #44 draft doc in commit body for traceability.

No code changes; tests unchanged. ~30min, $0.

### D-2.5 (NEW): v1.4.5 amendment ratification candidacy — **DRAFTING-ELIGIBLE**

Per PR #55 systematic finding (3 hallucinated reflections at 20%
incidence rate in SC-009 backtest_memory.md), the n=3 threshold for the
v1.4.5 "reflection-prose-distrustable" amendment is now MET. Per the
"draft-then-ratify across sessions" defensive pattern, v1.4.5 needs to
be DRAFTED before it can be ratified.

Two options for D-2.5:
- **Draft tonight (2026-05-07 night), ratify Tuesday alongside v1.4.4**
  — efficient dual-amendment session.
- **Draft Tuesday, ratify Wednesday-or-later** — safer per same-session-
  ratification rule (mirror of v1.4.4 plan).

Recommend: **decide based on time/energy**. If drafting tonight is
feasible, dual-ratification Tuesday is the ROI-maximizing path. Otherwise
draft Tuesday + ratify Wednesday parallel to v1.4.4's two-stage cadence.

### D-3: C-5 (earnings price reaction) feasibility probe — UNCHANGED

Per the C-1 SKIP + C-3 NOT-FEASIBLE pattern, the de-risking probe (~30min,
$0) saves ~3h sunk cost if the data isn't accessible. `Ticker(t).earnings_history`
is the candidate API.

Recommend: **probe Tuesday morning** (~30min, $0). If feasible → schedule
C-5 retrospective for later in the week.

### D-4: Path C snapshot wiring PoC — UNCHANGED + CONTEXT REFINED

PR #40 verdict on C-3 was: "Path C (snapshot wiring) costs ~1h + 21d wait
for first replayable validation." Tomorrow's session has no immediate next
backtest planned (no expansion needed per D-1). Path C wiring can wait
until a future experiment is designed.

Recommend: **defer until next backtest design**. Wire it into the design
phase, not as a one-off.

### D-5 (NEW): SC-009 ANALYSIS.md — FINAL status timing

Current ANALYSIS.md is PRELIMINARY (preserved by PR #52 guard). The
FINAL version requires:
- Operator removes the `**Status**: PRELIMINARY` line
- Re-runs analyzer (with canonical 21d-closed α data, post 2026-05-22+)
- Writes operator framing on top of the auto-generated content (or
  extends it with the PASS-by-non-counterexample shadow-mode-first
  recommendation per PR #56/#57)

Recommend: **schedule for ~2026-05-22 or later**. Tuesday action: none
for D-5 yet; place a calendar reminder for 2026-05-22 to revisit.

## Standing open work (carryover from 2026-05-07 evening)

In rough priority order:

1. **Constitution v1.4.4 amendment draft (L-8 only)** — text-only.
   ~45min, $0.
2. **Hybrid D feasibility design doc** — empirical kernel from PR #41
   sub-pattern 3 (~5 candidate cases). Design + retrospective sketch only.
   ~30min, $0.
3. **C-5 (earnings price reaction) feasibility probe** — see D-3. ~30min,
   $0.
4. **Memory polish: PM-as-multi-mechanism-validator framing** — update
   `reference_behavioral_additive_4th_interpretation.md` to reflect
   PR #41's reframe + 23-case sweep evidence. ~15min, $0.
5. **CHANGELOG.md update for 2026-05-07 PRs #29-#41+** — operational
   hygiene. ~30min, $0.
6. **Bear-side sample-size diagnostic update** — ~20min, $0.
7. **Spec 003 historical-recompute script** — operational improvement.
   ~2h, $0.
8. **SC-009 final ANALYSIS.md skeleton fill-in** — once realized α
   landings start ~2026-05-15. Defer until then.

## Cross-session memories most relevant to tomorrow

- `reference_behavioral_additive_4th_interpretation.md` — guides the
  v1.4.4 draft framing
- `reference_pm_hold_regime_starves_filters.md` — context for any
  expansion experiment design
- `feedback_additive_filter_gate.md` — Constitution v1.4.3 standard
  for any new filter spec
- `feedback_retrospective_first_pattern.md` — Constitution VIII v1.4.1
  gate; mandatory before any new filter spec
- `feedback_no_stop_recommendation.md` — never close with STOP/pause
  framings
- `feedback_no_pick_prompts.md` — execute the recommendation directly
- `reference_sc009_ablation_pattern.md` — single-run + post-hoc
  reconstruction methodology for any future ablation work
- `feedback_global_conftest_autouse_for_real_llm.md` — when adding new
  default-on lazy-LLM filters, ALWAYS extend conftest

## Cost forecast for tomorrow

Conservative estimate:
- D-1 expansion experiment (if triggered): ~$15 LLM, ~5h compute
- C-5 feasibility probe (if pursued): $0
- v1.4.4 amendment draft + Hybrid D doc + memory polish: $0
- Possible spec-008.5 evolution toward Path C wiring: defer

**Total**: $0-$15 LLM, depending on D-1 trigger. ~3-5h foreground.

## What this scaffold is NOT

- It's NOT a commitment to do all the listed tasks
- It's NOT a substitute for tomorrow's actual reasoning_decision invocations
- It's NOT a frozen plan — D-1 trigger criteria depend on data we don't
  have yet; D-2/D-3/D-4 priorities depend on D-1 outcome
- It IS a context-preservation scaffold so tomorrow's session opens with
  full visibility into today's state-of-play

## Methodology pattern preferences (carry forward)

- **Reasoning_decision rank #1 wins**: today's PR cadence was driven by
  user accepting the rank #1 option each cycle. This minimizes choice
  paralysis and maximizes throughput.
- **Lead with full ranked-options table** when reporting reasoning_decision
  output (per memory).
- **Pre-commit reformat dance is normal**: ruff format may abort the
  first commit; re-stage and retry. Captured as memory.
- **Feasibility probe before retrospective design**: today's PR #40
  saved 3h by probing in 30min. Continue this pattern for any new
  data-source-dependent retrospective.

## Reset checklist for opening tomorrow's session (UPDATED 2026-05-07 night)

- [x] Backtest finished — confirmed 36/36 rows
- [x] Analyzer re-run; ANALYSIS.md updated to PRELIMINARY + 36-row data
- [x] D-1 expansion-trigger logic applied → no expansion needed
- [ ] Tomorrow morning: read `MEMORY.md` (auto-loaded; 16 cross-session memories)
- [ ] Tomorrow morning: ratify v1.4.4 per D-2 (single commit; ~30min)
- [ ] Tomorrow morning: decide D-2.5 v1.4.5 draft timing (tonight vs Tuesday)
- [ ] Tomorrow morning: run `reasoning_decision` for the first task after ratification
- [ ] Calendar reminder for 2026-05-22+ — D-5 final SC-009 ANALYSIS.md

**Memories most directly relevant to tomorrow's ratification work**:
- `reference_behavioral_additive_4th_interpretation.md` — guides v1.4.4 amendment text
- `reference_pass_by_non_counterexample.md` — informs spec 008 default-flip framing
- `reference_memory_log_reflection_hallucination.md` — guides v1.4.5 amendment text
- `feedback_retrospective_first_pattern.md` — Constitution VIII v1.4.1 gate (always applies)
