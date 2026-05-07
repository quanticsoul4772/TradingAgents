# Research-burst day — 2026-05-07 (morning + early-afternoon + late-afternoon extension session)

**Day-in-progress tally** (late-afternoon): **24 PRs shipped** (24 merged) + SC-009 backtest running in background (16/36 rows, ~3h ETA remaining) + 5 cross-session memories. Pattern continues: parallel-safe $0 work while backtest burns ~$18 LLM in background.

**Pattern**: parallel-safe documentation + diagnostic + risk-mitigation + filter-audit work while a long-running experiment runs in background. Foreground LLM cost: $0. Background backtest cost: ~$18 (estimated). Wall-clock: ~5.5h foreground + parallel ~5h compute.

This document is the canonical entry point for today's session. Companion to `claudedocs/research-burst-2026-05-06.md` (yesterday's 17-unit + 5-amendment day) which now has a 2026-05-07 appendix referencing this standalone doc.

## Verdict ledger (chronological PR order)

| # | PR | Time | Unit | Verdict |
|---|---|---|---|---|
| 1 | #17 | 06:14 | SC-009 ablation kick-off (HYPOTHESIS + PARAMS + run scripts) | backtest started, ~5h compute ETA |
| 2 | #18 | morning | Class 5 surprise outlier investigation | INTC identified (3 quarters epsEstimate near $0.01); LLY surprises clean |
| 3 | #19 | morning | Spec 008 v1.4.3 exemption audit | EXEMPTED via hybrid-filter exception (canonical case) |
| 4 | #20 | morning | Test flake fix (global conftest autouse) | 1123/1123 PASS; pre-existing test_pm flake fixed |
| 5 | #21 | morning | SC-009 analysis plan committed in advance | 6-phase methodology locked before data collection |
| 6 | #22 | morning | Bear-side mechanism design doc | 6 candidate classes enumerated; C-1 insider-transactions recommended |
| 7 | #23 | morning | Class C-1 retrospective | SKIP — 1/18 cohort hit; -2.23pp anti-pred. Pivot to C-3 |
| 8 | #24 | morning | SC-009 analyzer prep script | analyze_sc009_ab.py ready for ANALYSIS.md when α lands |
| 9 | #25 | morning | ROADMAP refresh | active branch updated for 2026-05-07 morning work |
| 10 | #26 | early-afternoon | Spec 007 v1.4.3 exemption audit | EXEMPTED via cross-mechanism-class structural argument |
| 11 | #27 | early-afternoon | SC-009 expansion contingency design | trigger criteria documented; LIKELY NOT triggered |
| 12 | #28 | early-afternoon | SC-009 mid-backtest commit-pattern diagnostic | boost engaging 4/6; spec 007 fired once at 7 rows |
| 13 | #29 | early-afternoon | Meta-retrospective appendix to 2026-05-06 doc | session continuity preserved |
| 14 | #30 | early-afternoon | Hold-rate root cause investigation | PM Calibrated Abstention; all filters work correctly |
| 15 | #31 | early-afternoon | SC-009 expansion experiment scaffold (CONDITIONAL) | ready to kick off iff trigger criteria met |
| 16 | #32 | early-afternoon | RESEARCH_FINDINGS.md update | Constitution v1.4.3 + 4 new findings documented |
| 17 | #33 | early-afternoon | SC-009 ANALYSIS.md skeleton | 126-line placeholder with most-likely-outcome framing |
| 18 | #34 | early-afternoon | Spec 003 fire pattern probe + behavioral-additive insight | PM-as-implicit-Spec-003 + 4th interpretation captured |
| 19 | #35 | early-afternoon | Analyzer bug fixes (fetch_returns + boost-engagement) | 100% bull-fire rate finding surfaced |
| 20 | #36 | mid-afternoon | Alternative gate-1 evaluator for 100%-fire-rate | suppressed-α direction check; alt gate-1 PASS at -4.29% |
| 21 | #37 | mid-afternoon | Standalone meta-retrospective doc | session continuity restored after compaction |
| 22 | #38 | late-afternoon | Unit tests for `evaluate_gate_1` helper | 15 tests, 5 paths covered; refactor + tests in one PR |
| 23 | #39 | late-afternoon | Bear-side mid-flight diagnostic on COP+INTC UW commits | 5 findings; F-3 = 2nd behavioral-additive class (Spec 007) |
| 24 | #40 | late-afternoon | Class C-3 (analyst PT delta) feasibility probe | NOT FEASIBLE on $0 budget — yfinance has no historical PT panels; pivot recommended |
| 25 | #41 | late-afternoon | Cross-cohort behavioral-additive sweep | ALL 4 mechanism classes show evidence; reframes L-8 to PM-as-multi-mechanism-validator; v1.4.4 codification threshold MET |

## Cross-session memories added today (5)

- `reference_sc009_ablation_pattern.md` — single-run + post-hoc reconstruction saves 50% LLM cost vs naive two-branch
- `feedback_global_conftest_autouse_for_real_llm.md` — when adding default-on lazy-LLM filter, ALWAYS extend conftest with autouse fixture
- `reference_pm_hold_regime_starves_filters.md` — when PM picks Hold from start, filters gating on `pre_rating` have nothing to suppress
- `reference_pm_hold_with_bullish_prose.md` — Constitution VII pattern: rating=Hold + prose="Initiate at OW" can intentionally diverge
- `reference_behavioral_additive_4th_interpretation.md` — PM as implicit Spec 003; behavioral-additive 4th interpretation of Constitution v1.4.3

Combined with yesterday's 9 memories (1 from earlier sessions + 8 from 2026-05-06 work): **14 cross-session memories total** indexed.

## Cost (2026-05-07 extension)

| Phase | LLM cost | Wall-clock |
|---|---|---|
| SC-009 ablation backtest (in progress) | ~$18 (estimated) | ~5h compute (in progress) + 21d wait for realized α |
| Class C-1 insider-transactions retrospective | $0 | ~30min |
| Class 5 outlier probe | $0 | ~15min |
| Spec 008 + Spec 007 v1.4.3 audits | $0 | ~45min |
| SC-009 expansion design + contingency scaffold | $0 | ~45min |
| SC-009 diagnostics (mid-backtest + Hold-root-cause + Spec 003 fire pattern) | $0 | ~1.5h |
| SC-009 analyzer + alt gate-1 + bug fixes | $0 | ~1h |
| Doc updates (RESEARCH_FINDINGS, ROADMAP, CHANGELOG, meta-retrospective appendix, skeleton) | $0 | ~1h |
| Memory polish (5 new) | $0 | ~30min |
| **2026-05-07 extension total** | **~$18** | **~5h foreground + ~5h compute parallel** |

Combined 2026-05-06 + 2026-05-07: **~$23 LLM total + ~31h wall-clock** (37 ship-quality units across 2 days).

## Methodology pattern

**Yesterday's mode** (2026-05-06): dense retrospective + spec invocation work. 17 ship-quality units in ~22h, ~$5 LLM. Each unit was substantive research output (retrospectives + spec implementations + constitution amendments).

**Today's mode** (2026-05-07): parallel-safe documentation + diagnostic + risk-mitigation work while SC-009 backtest runs in background. 20 ship-quality units in ~5.5h foreground, ~$18 LLM (in background). Foreground work all $0.

Both modes valid. Today's mode is appropriate when:
- A long-running experiment is the gating step (can't be accelerated)
- Cheap parallel work fills the wait time
- The parallel work doesn't compete for compute or attention with the gating experiment
- The session is focused on EXTRACTING VALUE FROM existing data + future-proofing infrastructure rather than generating NEW research data

## 5 methodology lessons codified today (NEW)

### L-6 (NEW): PM Hold-regime starves filters

When PM picks Hold from start (per Constitution VII Calibrated Abstention), all 4 PM-stage filters (Spec 003, Spec 004, Spec 006, Spec 007) have NOTHING to fire on. Filter ablations need cohorts with high commit-elicitation probability (bear-correct + volatile + earnings-active mix).

Empirical: SC-009 backtest at 11/36 rows has 73% Hold rate (8 Hold + 3 bear UW; 3 bull commits all fired by Spec 007).

Codified as: `reference_pm_hold_regime_starves_filters.md`

### L-7 (NEW): PM rating-vs-prose can intentionally diverge

Constitution VII pattern: PM rates Hold but prose says "Initiate at Overweight, build over weeks." Rating means "no commit on this propagate"; prose can recommend multi-week framework. Filters parse rating not prose. Future ANALYSIS.md framings must distinguish "PM didn't commit" vs "filter missed cohort" vs "filter caught cohort."

Empirical: NVDA 04-17 + MSFT 04-24 explicit examples in state logs.

Codified as: `reference_pm_hold_with_bullish_prose.md`

### L-8 (NEW): Behavioral-additive 4th interpretation of v1.4.3

When PM has internalized a filter's logic (PM-as-implicit-Spec-003 on extended-rally Tech), the new filter is REDUNDANT-ON-EXECUTION (PM Hold pre-empts its fire) but COMPLEMENTARY-ON-DESIGN (different mechanism class). SHIP behavioral-additive specs anyway for PM regime-drift robustness. Future Constitution v1.4.4 candidate amendment.

Empirical: 4 of 9 SC-009 cohort rows had Spec 003 percentile ≥ 80 (would-fire-if-bull) but PM rated Hold on all 4. Spec 003 functionally redundant with PM Hold-regime on this cohort.

Codified as: `reference_behavioral_additive_4th_interpretation.md`

### L-9 (NEW): When fire rate is 100%, standard gate-1 is structurally undefined

Standard SC-009 gate 1 (boost-ON kept α minus boost-OFF kept α) requires a non-empty kept set. When 100% of bull commits get fired, both kept sets are empty. Need alternative measure: suppressed commits' realized α direction (filter caught losers if α < 0).

Empirical: Spec 007 fires on 3/3 = 100% of bull commits in SC-009 partial data. Suppressed α = -4.29% → alt gate-1 PASS.

Codified as: alternative gate-1 evaluator in `scripts/analyze_sc009_ab.py`. Future Constitution v1.4.4 candidate amendment to standardize.

### L-10 (NEW): Cross-mechanism-class filters are structurally additive

Spec 007 (forward-catalyst LLM-extracted) catches different cohort than Spec 003 (prose-density). Spec 008 (hybrid INSIDE Spec 007) catches different than its underlying Spec 007. The v1.4.3 trigger criteria explicitly exempt cross-mechanism-class filters via the structural argument.

Empirical: Spec 007 + Spec 008 audits (PRs #19, #26) confirm both EXEMPT from v1.4.3 retroactive application. Spec 003 fire pattern probe (PR #34) empirically validates the structural argument.

Captured in `claudedocs/spec-007-v1.4.3-overlap-audit-2026-05-07.md` + `claudedocs/spec-008-v1.4.3-exemption-audit-2026-05-07.md`.

## Filter portfolio at end of 2026-05-07 morning

Unchanged from yesterday: 8 filters, 4 default-active, 4 operator-opt-in. SC-009 ablation will determine if Spec 008 v2 default-on flip is justified (verdict ~2026-05-22 after realized α window closes).

## Constitution version trajectory

**Yesterday (2026-05-06)**: v1.3.0 → v1.4.0 → v1.4.1 → v1.4.2 → v1.4.3 (5 amendments).

**Today (2026-05-07)**: no constitution amendments. 2 candidate v1.4.4 amendments captured for future codification:
- L-8: codify behavioral-additive 4th interpretation of v1.4.3 — **threshold MET** as of PR #41 (4/4 mechanism classes have evidence; 23 cases across 6 tickers). Reframed from "PM-as-implicit-Spec-003" to **PM-as-multi-mechanism-validator**. Drafting eligible; ratification still gated on 1 more session of pattern holding to avoid over-fitting.
- L-9: codify alt gate-1 methodology for 100%-fire-rate filters in SC-009 pattern. Still n=1 (SC-009 only); defer until pattern recurs in another spec.

## Open work entering tomorrow

- **SC-009 backtest completes** (~3h ETA remaining, ~end-of-day PDT)
- **Re-run analyzer on full 36-row data** with the merged `evaluate_gate_1` helper to see final gate trajectory
- **Realized α window for 2026-04-17 closes ~2026-05-15** (8 days from now)
- **Realized α window for 2026-04-24 closes ~2026-05-22** (15 days from now)
- **Final SC-009 ANALYSIS.md** writable ~2026-05-22 onward
- **Expansion contingency**: kick off `experiments/2026-05-07-002-sc-009-expansion/` IF backtest completes with ≥30/36 Hold AND `n_fired_boost_on < 4`
- **Constitution v1.4.4 amendment draft** (L-8 behavioral-additive only — L-9 still defers): threshold MET per PR #41; can draft text-only with no flip yet. Risk: retraction needed if SC-009 finishing rows refute the multi-mechanism-validator framing (modest — framing is descriptive not predictive).
- **Hybrid D feasibility design doc**: ~5 candidate both-sides-priced-in cases identified by PR #41 (NVDA-04-24 + MSFT-04-24 + WFC-04-17 + COP-04-24 + COP-04-17). Cohort too small for retrospective today; design doc + retrospective sketch only.
- **C-5 (earnings price reaction) feasibility probe**: same de-risking pattern that worked for C-1 + C-3. ~30min, $0.
- **Path C snapshot wiring PoC**: add `analyst_pt_snapshot` to `state['forward_catalyst']` persistence; unlocks future C-3 retrospectives at zero LLM cost. ~1h, $0.
- **Bear-side sample-size update**: SC-009 cohort grew INTC-04-24 UW (3rd UW commit); quick mid-flight update. ~20min, $0.
- **Spec 003 historical-recompute script** still deferred (~2h)
- **CHANGELOG.md update for PRs #29-#41 + sweep verdict** still deferred (~30min)

## What did NOT happen today

- Class C-3 retrospective (deferred — too time-expensive vs parallel-safe constraints)
- Class C-5 retrospective (deferred — same reason)
- Spec 003 historical-recompute script (deferred — strategic but not blocking)
- Class 4 (cross-asset/macro) retrospective (still data-deferred — yfinance VIX/yield/USD coverage TBD)
- Active default-flip on Spec 007 bear (still shadow mode; awaiting n≥20 fresh propagates per Constitution VIII v1.4.0)

## Cumulative state across 2 days

- **Filter portfolio**: 8 sides (unchanged from 2026-05-06 evening)
- **Constitution version**: v1.4.3 (5 amendments yesterday; v1.4.4 candidate L-8 drafting-eligible after PR #41 evidence change)
- **Cross-session memories**: 14 total
- **PRs merged across 2026-05-06 + 2026-05-07**: 41+ (15 yesterday + 25+ today)
- **Tags**: v0.7.0/v0.8.0/v0.8.1 (no new today; SC-009 verdict pending ~2026-05-22)
- **Tests**: 1138/1138 PASS (was 1123 → +15 from PR #38 SC-009 analyzer unit tests)
- **Backtest**: 16/36 rows complete + ~20 more pending; ANALYSIS.md ~2026-05-22

## Methodology cost-benefit summary across both days

- Total cost: ~$23 LLM + ~31h wall-clock for 37 ship-quality units
- Per-unit: ~$0.62 LLM + ~50min wall-clock
- Cost discipline: well within Constitution III T1-T2 (entire 2-day burst ≤$30, T2 upper)
- ROI on retrospective methodology: ~10-13× wall-clock leverage on spec invocations that DID launch (yesterday's 7 SKIP outcomes × 6-8h avoided + today's C-1 SKIP × 6-8h avoided = ~50-60h saved by ~$5 + ~7h of retrospectives)
- Memory leverage: 14 cross-session memories now instructed future sessions on yesterday's + today's lessons; future-self continuity preserved
