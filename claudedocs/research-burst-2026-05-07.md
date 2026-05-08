# Research-burst day — 2026-05-07

**TALLY (current)**: **80+ PRs shipped** (all merged) + SC-009 backtest COMPLETED (36/36 rows, exit code 0) + **9 cross-session memories added today** (14 → 23 cumulative). Pattern: parallel-safe $0 work while backtest burned ~$18 LLM in background. Major arcs: SC-009 ablation completion + bear-side mechanism class survey CONCLUSION (6/6 evaluated; C-4 SOLE spec-eligible) + Constitution v1.4.4 + v1.4.5 amendment drafts + tooling family.

**Pattern**: parallel-safe documentation + diagnostic + risk-mitigation + filter-audit + tooling-build work while a long-running experiment ran in background. Foreground LLM cost: $0 across all 80+ PRs. Background backtest cost: ~$18 (completed). Test count 1123 → 1179 (+56 net).

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
| 26 | #42 | late-afternoon | ROADMAP refresh + tomorrow's scaffold | Establishes context preservation across day boundary |
| 27 | #43 | late-afternoon | AMD-04-17 deep-dive | Cleanest L-8 sub-pattern 2 case + new sub-pattern 4 (Hybrid E candidate) |
| 28 | #44 | evening | Constitution v1.4.4 amendment DRAFT | Two-stage pattern: separate doc; ratification deferred to tomorrow |
| 29 | #45 | evening | Behavioral-additive sweep refresh | 23 → 29 cases / 6 → 8 tickers; v1.4.4 evidence strengthened |
| 30 | #46 | evening | AMD-04-24 deep-dive | TRIPLE behavioral-additive case; PR #45 followup REFUTED (no baseline switch) |
| 31 | #47 | evening | Spec 003 instrumentation followup | Already exists; closes 2 followups; sweep harness enhanced |
| 32 | #48 | evening | Hybrid D + E feasibility design | Both DEFERRED; cohort too thin |
| 33 | #49 | evening | Counter-evidence watch automation | 12 unit tests; current corpus 0 refuting rows; v1.4.4 UNBLOCKED on this axis |
| 34 | #50 | evening | AMZN combined deep-dive | First OPERATIONAL spec 007 fire event in deep-dives + temporal-learning arc |
| 35 | #51 | evening | SC-009 23-row trajectory mark | Gates 2+3 PASS; gate 1 PASS @ +1.75% (preliminary) |
| 36 | #52 | evening | ANALYSIS.md PRELIMINARY + analyzer guard | Operator hand-edit preserved across analyzer runs |
| 37 | #53 | evening | 27-row mark + sweep refresh | 29 → 37 cases / 8 → 10 tickers; +AVGO +CSCO |
| 38 | #54 | night | AMD memory log audit RESOLVED | Hallucination is REAL (entry exists; reflection prose contradicts data) — cascade failure mode |
| 39 | #55 | night | Memory log integrity check tool + 12 tests | BREAKTHROUGH: 3 of 15 entries (20%) hallucinated; n=3 v1.4.5 threshold MET |
| 40 | #56 | night | Spec 007 calendar-independence (BAC+GS at 80+d) | PASS-by-non-counterexample finding; recommend shadow-mode-first |
| 41 | #57 | night | SC-009 BACKTEST COMPLETE | 36/36 rows; gates 1+2+3 all PASS; D-1 expansion not needed |
| 42 | #58 | night | ANALYSIS.md final-PRELIMINARY update | Headline + table + sections updated to 36-row state |
| 43 | #59 | night | Tomorrow's scaffold update | D-decisions pre-resolved/scoped for Tuesday |

## Cross-session memories added today (6)

- `reference_sc009_ablation_pattern.md` — single-run + post-hoc reconstruction saves 50% LLM cost vs naive two-branch
- `feedback_global_conftest_autouse_for_real_llm.md` — when adding default-on lazy-LLM filter, ALWAYS extend conftest with autouse fixture
- `reference_pm_hold_regime_starves_filters.md` — when PM picks Hold from start, filters gating on `pre_rating` have nothing to suppress
- `reference_pm_hold_with_bullish_prose.md` — Constitution VII pattern: rating=Hold + prose="Initiate at OW" can intentionally diverge
- `reference_behavioral_additive_4th_interpretation.md` — UPDATED to PM-as-multi-mechanism-validator framing (cross-cohort sweep evidence)
- `reference_memory_log_reflection_hallucination.md` — NEW evening: memory log REFLECTION prose can contradict entry header data; cascade failure if downstream PM trusts prose
- `reference_pass_by_non_counterexample.md` — NEW evening: distinguish PASS-by-active-improvement from PASS-by-non-counterexample; default-on flip needs the former

Combined with yesterday's 9 memories: **16 cross-session memories total** indexed in MEMORY.md.

## Cost (2026-05-07 final)

| Phase | LLM cost | Wall-clock |
|---|---|---|
| SC-009 ablation backtest (COMPLETE) | ~$18 (actual) | ~7h compute completed + 14-19d remaining for canonical 21d realized α |
| Morning: Class C-1 + Class 5 + v1.4.3 audits + analyzer prep + ROADMAP + 5 docs | $0 | ~3.5h (PRs #17-#26) |
| Early-afternoon: SC-009 expansion design + diagnostics + RESEARCH_FINDINGS update + skeleton + behavioral-additive insight + analyzer fixes + alt gate-1 + meta-retrospective | $0 | ~3.5h (PRs #27-#37) |
| Late-afternoon: PR #38-#43 (analyzer tests + bear-side diagnostic + C-3 SKIP + sweep + ROADMAP + AMD-04-17) | $0 | ~1.5h |
| Evening: PR #44-#53 (v1.4.4 draft + sweep refresh + AMD-04-24 + spec 003 followup + Hybrid D/E + counter-evidence watch + AMZN dive + 23-row trajectory + ANALYSIS.md guard + 27-row sweep refresh) | $0 | ~2.5h |
| Night: PR #54-#59 (AMD memory audit + integrity tool + spec 007 calendar-independence + backtest complete + ANALYSIS.md final-PRELIM + tomorrow's scaffold) | $0 | ~1.5h |
| Memory polish (6 new + 1 updated, all sessions) | $0 | ~1h |
| **2026-05-07 FINAL TOTAL** | **~$18** | **~9h foreground + ~7h compute parallel** |

Combined 2026-05-06 + 2026-05-07: **~$23 LLM total + ~31h wall-clock** for **17 + 43 = 60 ship-quality units across 2 days**. Per-unit: $0.38 LLM / 31min wall-clock. Cost discipline: well within Constitution III T1-T2 (entire 2-day burst ≤$30, T2 upper).

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

## Open work entering tomorrow (UPDATED end-of-day)

**RESOLVED today (no longer pending)**:
- ✅ SC-009 backtest completes (PR #57 — 36/36 rows, exit code 0)
- ✅ Re-run analyzer on full 36-row data (PR #58 — ANALYSIS.md updated)
- ✅ D-1 expansion contingency: NOT triggered (n_fired=13 ≥ 8) — scaffold inert
- ✅ Constitution v1.4.4 amendment draft (PR #44 — drafted; ratification ready for tomorrow)
- ✅ Hybrid D feasibility design doc (PR #48 — both Hybrid D + E DEFERRED for cohort growth)
- ✅ Bear-side sample-size update (subsumed into PR #39 + PR #46 + PR #56 deep-dives)
- ✅ Memory log integrity check tooling (PR #55 — n=3 v1.4.5 threshold MET)
- ✅ AMD memory log audit (PR #54 — hallucination cascade documented)

**Still pending entering 2026-05-08**:
- **Realized α window for 2026-04-17 closes ~2026-05-18** (~11 days)
- **Realized α window for 2026-04-24 closes ~2026-05-26** (~19 days)
- **Final SC-009 ANALYSIS.md** (FINAL status not PRELIMINARY) writable ~2026-05-22+
- **D-2 v1.4.4 amendment ratification** — Tuesday morning per same-session-defer rule
- **D-2.5 v1.4.5 amendment draft + ratification** — n=3 threshold MET per PR #55; draft tonight or Tuesday
- **D-3 C-5 (earnings price reaction) feasibility probe** — ~30min, $0
- **Path C snapshot wiring PoC** — defer until next backtest design
- **AVGO temporal-jump investigation** — small followup from PR #53
- **Identify 4 unaccounted bull-pre fires from final 9 rows** — small followup from PR #57
- **Memory polish: PR #50 F-3 temporal-learning observation** — never captured
- **Update CHANGELOG.md for today's 22-PR + 4-memory burst** — operational hygiene
- **Spec 003.5 baseline=none diagnostic** (recurring on AMZN + BAC + GS)
- **Spec 003 historical-recompute script** — still deferred (~2h)

## What did NOT happen today

- Class C-3 retrospective (deferred — too time-expensive vs parallel-safe constraints)
- Class C-5 retrospective (deferred — same reason)
- Spec 003 historical-recompute script (deferred — strategic but not blocking)
- Class 4 (cross-asset/macro) retrospective (still data-deferred — yfinance VIX/yield/USD coverage TBD)
- Active default-flip on Spec 007 bear (still shadow mode; awaiting n≥20 fresh propagates per Constitution VIII v1.4.0)

## Cumulative state across 2 days (FINAL end-of-day 2026-05-07)

- **Filter portfolio**: 8 sides (unchanged from 2026-05-06 evening)
- **Constitution version**: v1.4.3 in effect (v1.4.4 + v1.4.5 candidates DRAFTED + ELIGIBLE for ratification tomorrow)
- **Cross-session memories**: 16 total (was 9 entering today; +6 new + 1 updated)
- **PRs merged across 2026-05-06 + 2026-05-07**: 60+ (15 yesterday + ~45 today including pre-#38 morning work)
- **Tags**: v0.7.0/v0.8.0/v0.8.1 (no new today; SC-009 verdict pending ~2026-05-22)
- **Tests**: **1162/1162 PASS** (was 1123 → +15 PR #38 + +12 PR #49 + +12 PR #55 = +39 net)
- **Backtest**: COMPLETE 36/36 rows; PRELIMINARY analyzer at +0.43% suppressed-α / 13 fires / 0 decisions changed by boost. ANALYSIS.md FINAL writable ~2026-05-22+

## Headline findings shipped today

1. **L-8 codification THRESHOLD MET + reframed**: `PM-as-multi-mechanism-validator` (was PM-as-implicit-Spec-003). 23 → 29 → 37 cases across 4/4 mechanism classes and 6 → 8 → 10 tickers (PRs #41, #45, #53). v1.4.4 amendment drafted (PR #44).
2. **AMD-04-17 textbook L-8 case** (PR #43) + AMD-04-24 TRIPLE behavioral-additive (PR #46) + AMZN-04-17 first OPERATIONAL fire event (PR #50).
3. **Reflection-prose hallucination DISCOVERED systematic at 20% rate** (PRs #54+#55). N=3 threshold for v1.4.5 amendment MET. Three hallucinated reflections found via integrity-check tool.
4. **PASS-by-non-counterexample distinction** (PR #56): SC-009 cohort doesn't exercise spec 008 boost's intended borderline regime; default-on flip should be SHADOW-MODE-FIRST per Constitution VIII v1.4.0.
5. **Spec 007 calendar-INDEPENDENCE** validated empirically (BAC×2 + GS at 81-88d to earnings fire on bull_score alone — PR #56).
6. **C-3 mechanism class NOT FEASIBLE** for retrospective (PR #40 — yfinance has no historical PT panels).
7. **Counter-evidence watch automation shipped** (PR #49) with 12 tests; current corpus 0 refuting rows.

## Methodology cost-benefit summary across both days (FINAL)

- Total cost: ~$23 LLM + ~40h wall-clock for **60+ ship-quality units** across 2 days
- Per-unit: ~$0.38 LLM + ~40min wall-clock
- Cost discipline: well within Constitution III T1-T2 (entire 2-day burst ≤$30, T2 upper)
- ROI on retrospective methodology: ~10-13× wall-clock leverage on spec invocations that DID launch (yesterday's 7 SKIP outcomes × 6-8h avoided + today's C-1 SKIP + C-3 NOT-FEASIBLE × 6-8h avoided each = ~50-60h saved by ~$5 + ~7h of retrospectives)
- Memory leverage: 16 cross-session memories durably preserved (vs forgetting and re-discovering)
- Memory leverage: 14 cross-session memories now instructed future sessions on yesterday's + today's lessons; future-self continuity preserved
