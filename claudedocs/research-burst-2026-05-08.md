# Research-burst day — 2026-05-08 (scaffold, written 2026-05-07 evening)

**Status as of scaffold writing**: SC-009 backtest still in progress; ~16/36 rows
complete late-afternoon 2026-05-07. Expected to finish overnight or
tomorrow morning. This doc is a forward-planning scaffold, not yet a
record of work.

**Companion docs**:
- `claudedocs/research-burst-2026-05-06.md` — yesterday's 17-unit + 5-amendment day
- `claudedocs/research-burst-2026-05-07.md` — today's 24+ unit parallel-safe-during-backtest day

## Likely opening state (predicted)

When tomorrow opens, the SC-009 backtest is most likely:

**Scenario A (likely, ~70% probability)**: backtest completed overnight.
36 rows in `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv`.
Re-running the analyzer produces:
- Final n_fired_boost_on count (predicted 4-7 based on 16-row trajectory of 3 fires)
- Final alt gate-1 suppressed-α (still PASS-likely if pattern holds)
- Bull commit count (predicted 6-10 based on 16-row trajectory of 6)

**Scenario B (~25% probability)**: backtest still running at start of session.
Continue in parallel-safe mode like today.

**Scenario C (~5% probability)**: backtest crashed or stalled. Diagnose,
restart from where it left off (resumable per design — checkpointed CSV
appends).

## Decisions to make Tuesday morning

### D-1: SC-009 expansion contingency trigger

If backtest finished AND `n_fired_boost_on < 4`:
- KICK OFF expansion experiment `experiments/2026-05-07-002-sc-009-expansion/`
  (already scaffolded). 13 tickers × 2 dates = 26 propagates targeting
  bear-correct + volatile + earnings-active mix. Cost ~$15.

If backtest finished AND `4 ≤ n_fired_boost_on < 8`:
- DECISION: expansion (boost gate-2 to ≥8) or accept partial-pass and ship
  ANALYSIS.md as-is. Default is expansion — alt gate-1 alone isn't enough
  for clean v0.8.0+ default-flip.

If backtest finished AND `n_fired_boost_on ≥ 8`:
- NO EXPANSION needed. Proceed to ANALYSIS.md skeleton fill-in once
  realized α landings start ~2026-05-15.

### D-2: v1.4.4 amendment draft timing

Per yesterday's PR #41 cross-cohort sweep: L-8 codification threshold MET
(4/4 mechanism classes show evidence). Drafting-eligible from a memory-
deferral perspective. But per Constitution VI, formal amendments should
ship via the standard `/speckit.constitution` workflow with their own
verdict cadence.

Two options for D-2:
- **Draft + ratify in one PR Tuesday**: unblocks future spec ROIs that
  depend on the 4th additive interpretation. Risk: SC-009 final data
  could reveal counter-evidence.
- **Draft Tuesday, ratify in a later session**: safer; builds in 1-2
  more sessions of pattern-holding before flipping.

Recommend: **draft Tuesday, ratify Wednesday-or-later**.

### D-3: C-5 (earnings price reaction) feasibility probe

Per the C-1 SKIP + C-3 NOT-FEASIBLE pattern, the de-risking probe (~30min,
$0) saves ~3h sunk cost if the data isn't accessible.

For C-5 specifically, the question is: does yfinance return historical
post-earnings price-reaction magnitudes (1-day, 5-day) cleanly enough to
backfill across our SC-009 cohort dates? `Ticker(t).earnings_history` is
the candidate API; needs to be probed analogously to PR #40.

Recommend: **probe Tuesday morning** (~30min, $0). If feasible → schedule
C-5 retrospective for later in the week.

### D-4: Path C snapshot wiring PoC

PR #40 verdict on C-3 was: "Path C (snapshot wiring) costs ~1h + 21d wait
for first replayable validation." With backtest finishing soon, a fresh
backtest with Path C snapshot wiring active becomes attractive — it
piggybacks on the next experiment's LLM spend without extra $$$.

Recommend: **defer until next backtest design** (could be SC-009 expansion
or a fresh experiment). Wire it into the design phase, not as a one-off.

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

## Reset checklist for opening tomorrow's session

- [ ] Read `MEMORY.md` (auto-loaded)
- [ ] Check `wc -l experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv`
- [ ] If 36 rows: read latest analyzer output (`python scripts/analyze_sc009_ab.py ...`)
- [ ] Apply D-1 expansion-trigger logic
- [ ] Run `reasoning_decision` for the first task selection
- [ ] Execute rank #1
