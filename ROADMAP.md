# ROADMAP — TradingAgents-lab

_Forward-looking exploration map. **2026-05-06**: 17-ship-quality-unit research-burst day; v0.7.0-spec-007 + v0.8.0-spec-008 + v0.8.1-spec-008.5 tags; Constitution v1.3.0 → v1.4.3 (5 amendments). **2026-05-07**: 50+ PRs (all merged) — SC-009 backtest COMPLETE; bear-side mechanism class survey from PR #22 CONCLUDES (6/6 evaluated; **C-4 institutional ownership delta is SOLE spec-eligible**); **Constitution v1.4.5 + v1.4.6 BOTH RATIFIED**; **Spec X-1 (C-4 institutional rotation filter) DEPLOYED end-to-end via 6-PR bundle (#88-#93)**. **2026-05-08**: 57 PRs (#117-#173) — **mypy floor 126 → 0** via 12 cleanup PRs (PR #128 4-line fix cleared 85 errors); **WC-10 v1 pilot SHIP** (3.6× commit ratio, ALT-A confirmed, $16); **Constitution v1.4.3 → v1.5.0** ("Schema-induced abstention is NOT calibrated abstention"); **RESEARCH_FINDINGS reframe** of mode collapse as TWO-MECHANISM; **Spec 011 behavioral-additive procedure SHIP**. **2026-05-09 — triple-pilot landing arc COMPLETE**: WC-10 v2 expansion (n=100, $32) RESOLVED with **SC-005(b) NULL** + **SC-007 ALT-A PARTIAL (5/8 tickers)** + **Branch C selected** (bin-then-output pattern; PR #181 ANALYSIS); WC-10 v3 bear-regime ($6.40) RESOLVED with **PARTIAL ALT-A** + **Constitution v1.5.0 → v1.5.1**; WC-11 analyst-order randomization ($8) RESOLVED with **PARTIAL ALT-A + ALT-B** (cannot disambiguate at n=20) + **Constitution v1.5.1 → v1.5.2** (Analyst-order scope; PR #179); BR-3 Squeak market-analyst structured-output ($8) RESOLVED with **PARTIAL ALT-B** (commit shift +20pp, α delta below threshold; PR #178); RESEARCH_FINDINGS joint update (PR #180) + WC-10 v2 section (PR #182). Canonical meta-retrospectives at `claudedocs/research-burst-2026-05-07.md` + `claudedocs/research-burst-2026-05-08.md` + (forthcoming) `claudedocs/research-burst-2026-05-09.md`._

This is a research playground, not a product. The roadmap is directions for exploration, not delivery milestones. Per Constitution Principle V ("Steal Liberally"), cross-pollination from sibling projects in the portfolio is a primary driver — many ideas listed here originate elsewhere.

For findings to date see [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). For per-experiment summaries see [`findings.md`](findings.md). For the original idea backlog see [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md).

---

## Current state (2026-05-06)

- **24 completed experiments** + cross-experiment horizon sweep + 3-period NVDA cross-validation + per-ticker breakdown + A1/A3 diagnostics + A3 forensics + Phase D substrate exploration + Phase C reasoning_evidence wiring + Spec 002 signal-lifecycle (Phases 0-2.5) + Spec 001 bots-architecture (Phases 1-5) + **Spec 003 contrarian gate (Phases 1+2 + SC-001 + SC-002 + SC-003 50-ticker validated; default-on flipped @80% threshold 2026-05-06)** + **Spec 003.5 sector-baseline fallback (default-on)** + **Spec 004 sector-momentum filter (default-off after retrospective)** + **Spec 006 bear-sector-symmetry filter (default-off after SC-008 FAIL)**
- A3 mean-reversion suppression filter productionized + default-on @-5%/30d (2026-05-06 flip); validated as correctly inert on regime-mismatch failures (007 INTC half)
- **Spec 003 contrarian gate productionized** (`tradingagents/signals/contrarian_gate.py`); **default flipped to active @80th-percentile + N≥20 floor on 2026-05-06** after `claudedocs/contrarian-gate-retrospective-2026-05-05.md` showed +6.46% cumulative Δα at 21d at production-default floor. **Threshold sweep follow-up validated default at 80%** (`claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md`): +0.65pp net Δα across 11 eligible commits; tightening to 85+ doesn't fire; loosening to 75 gives +1.36pp but more incorrect-suppression risk.
- **Spec 003.5 sector-baseline fallback** (`tradingagents/signals/sector_baseline.py`, `specs/003-sector-baseline-gate/`): when per-ticker history is below FR-004 N≥20 floor, gate aggregates across same-sector tickers. Default-on. Closes the cold-start universe gap structurally; doesn't help SC-003 Financials cohort (different mechanism — see Spec 004 finding).
- **Spec 004 sector-momentum filter** (`tradingagents/agents/utils/sector_momentum_filter.py`, `specs/004-sector-momentum-filter/`): suppresses Buy/OW when sector ETF is down >threshold% in prior 30d. Default-off after corpus retrospective (`claudedocs/sector-momentum-retrospective-2026-05-06.md`) showed -0.45pp net Δα across 73 commits at -5% threshold. SC-008 falsified (XLF was -4.54%, suppress 0/5). Ships as operator-opt-in.
- **Spec 006 bear-sector-symmetry filter** (`tradingagents/agents/utils/bear_sector_symmetry_filter.py`, `specs/005-bear-sector-symmetry/`): suppresses UW/Sell when ticker has outperformed sector ETF by >threshold% in prior 30d (counter-trend bear suppression). Default-off after SC-008 FAILED at +5% (5/18 cohort fires; target ≥8) AND -0.71pp net Δα anti-predictive. Ships as operator-opt-in.
- **Spec 005 candidate (per-ticker-vs-sector BULL filter)**: retrospectively SKIPPED before any spec was written (`claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`). Max +0.31pp net Δα across 79 commits, well below Constitution VIII's +1pp gate. Saved 6-8h of empty-spec work.
- Constitution **v1.3.0** with **Principle VIII** (Retrospective Before Spec for Backward-Looking Price Filters) added 2026-05-06 after three same-day retrospective failures. Plus Principles VII (Calibrated Abstention) + Replicability-scope + Cross-period-scope clarifications.
- Cost-tier ladder shipped; end-to-end exercised on 008
- **1022 tests passing** (was 825 → 984 → **1022** across the 2026-05-06 research-burst day; +197 net) — added Spec 003.5 (10+15 tests) + Spec 004 (~29 tests) + Spec 006 (27 unit + 5 PM integration + 2 state-log regression tests) + **Spec 007 (29 unit + 7 PM integration + 2 state-log + 1 default-config + 1 SC-008 integration)**. All 7 filter sides' state-log persistence tests follow the `4c14d0f` precedent. Suite tagged at v0.7.0-spec-007.
- **Load-bearing claim still stands post-NVDA-Q3 + SC-003 50-ticker validation**: framework's Buy/OW commits at 21d show **+1.23% α (n=71, ~61% hit)** in the legacy 9-ticker cohort + **+5.96% mean α (n=15, 53% hit) on the SC-003 50-ticker bullish bucket** (single-date 2026-04-03 — bullish bucket nearly 5× the 9-ticker headline magnitude, but per-sector breakdown shows the signal is structurally Tech-concentrated: Tech n=7 +17.80% mean; Financials n=5 -7.07% on bullish picks). Scenario B per HYPOTHESIS decision tree.
- **5th failure mode discovered (2026-05-06)** — bullish commits underperforming a rising sector (stock-specific α-vs-sector miss). Affects 27 of 79 bullish commits; 88.9% Tech-concentrated. Backward-price-only signals (Spec 005 candidate) cannot catch it; gap remains for forward-catalyst-aware mechanism. See `RESEARCH_FINDINGS.md` "5th failure mode" section.
- **Bearish anti-calibration shock (2026-05-06)** — 18 of 37 bearish commits at +28.02% mean α-vs-SPY in `ticker_strong` cell. A3 misses; spec 006 was built to catch but failed empirically. Largest single-metric anti-calibration finding in the corpus.
- UW failure mode is **regime-asymmetric, not uniformly anti-calibrated** (unchanged; reinforced by today's bearish anti-calibration finding)
- **Phase D substrate finding**: decision architecture portable across substrates; commit calibration single-stock-prompt-tuned
- **Finding #4 four-line-evidence convergence**: market_report bull_keyword_count anti-predicts within-ticker α at 90d. **First validated within-ticker predictor in the corpus.** Operationalized as Spec 003 contrarian gate; default-on @80% threshold validated by 2026-05-06 sweep.
- **No experiments running** — most recent: experiment `2026-05-05-003-signal-at-scale` (50-ticker SC-003 single-date validation). All 2026-05-06 work was retrospective + spec-development; no new propagates.

---

## Active branch — 2026-05-07 SC-009 ablation kick-off (PRs #17-#24)

Initial 8 PRs (5 merged + 3 open) focused on the Spec 008 SC-009 live A/B ablation kick-off + bear-side mechanism exploration:

1. **SC-009 ablation kick-off** (PR #17, merged): `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/` scaffolded with HYPOTHESIS + PARAMS + run scripts. Backtest running ~5h ETA against 18 tickers × 2 fresh Fridays (2026-04-17, 2026-04-24) = 36 propagates. Per-row pace ~9 min; ETA ~11:30 PDT for results.csv completion. ANALYSIS.md timeline ~2026-05-22 once 21d forward windows close.
2. **Class 5 surprise outlier investigation** (PR #18, merged): identified INTC (not LLY) as the source of the surprisePercent=31.21 outlier; 3 quarters with epsEstimate near $0.01 blowing up the ratio. Documented mitigations for any future Class 5 revival.
3. **Spec 008 Constitution v1.4.3 exemption audit** (PR #19, merged): confirmed Spec 008 is correctly exempted from the v1.4.3 additive-overlap gate (hybrid-filter exception). Sanity-check shows it WOULD pass at +3.34pp vs Spec 007 baseline if applied retroactively.
4. **Test flake fix** (PR #20, merged): added global autouse fixture in `tests/conftest.py` patching `create_llm_client` to raise. Fixes the `test_pm_returns_rendered_markdown_with_rating` ordering flake that surfaced during yesterday's Spec 008 work. Suite at 1123/1123 PASS.
5. **SC-009 analysis plan** (PR #21, merged): 6-phase analysis methodology committed in advance to avoid p-hacking when ANALYSIS.md is written ~2026-05-22.
6. **Bear-side mechanism design doc** (PR #22, merged): enumerates 6 candidate mechanism classes (insider transactions, short-interest delta, analyst PT delta, institutional ownership, earnings price reaction, bear-news density) for the uncatchable +28pp `ticker_strong`-bear cohort. Recommends Class C-1 (insider transactions) as the next retrospective.
7. **Class C-1 (insider transactions) retrospective** (PR #23, merged): SKIP verdict — only 1/18 cohort_b_bear_target rows have insider buys in prior 30d; bear-side fire at T≥1 is anti-predictive (-2.23pp). Insider purchases at large-cap tech are too rare to discriminate. Per design doc decision tree: pivot to Class C-3 (analyst PT delta) as the next bear-side candidate.
8. **SC-009 analyzer prep script** (PR #24, OPEN): `scripts/analyze_sc009_ab.py` ready to run once realized α window closes (~2026-05-22). Mechanism: post-hoc compute boost-OFF would-fire from state-log `bull_case_priced_in` to enable single-run A/B (saved ~$15 vs naive two-branch design). 3 SC-009 acceptance gates evaluated explicitly.

Plus 2 cross-session memories added today: `reference_sc009_ablation_pattern.md` + `feedback_global_conftest_autouse_for_real_llm.md`.

**Open work entering 2026-05-07 mid-day**:
- **SC-009 backtest in progress**: ~5h compute ETA, ANALYSIS.md ~2026-05-22 (after 21d forward window closes)
- **Class C-3 (analyst PT delta) retrospective**: ~3h, $0 — next candidate per bear-side design doc decision tree
- **Class C-5 (earnings price reaction) retrospective**: ~3h, $0 — alternative to C-3 with cleaner data structure
- **Forward-catalyst overlap audit on Spec 007 retroactively**: ~30min, $0 — Spec 007 isn't a hybrid filter so v1.4.3 trigger criteria DO apply; verify it PASSES the additive gate against A3 + spec 003 + spec 003.5

## 2026-05-07 PRs #38-#41 — analyzer tests + AMD deep-dive + sweep

After PR #37 (standalone meta-retrospective), 4 more ship-quality units:

35. **SC-009 analyzer unit tests** (PR #38, merged): 15 unit tests for the new `evaluate_gate_1` helper covering all 5 paths (standard PASS at midpoint/lower-bound/upper-bound, standard FAIL at multiple boundaries, alt PASS, alt FAIL, INCONCLUSIVE). Refactor + tests in one PR. 1138/1138 PASS (was 1123, +15).
36. **Bear-side mid-flight diagnostic on COP+INTC UW commits** (PR #39, merged): 5 findings; F-3 = SECOND behavioral-additive case in a NEW mechanism class (Spec 007 LLM-extracted, complementing morning's Spec 003 prose-density). Evidence base for v1.4.4 codification grows.
37. **Class C-3 (analyst PT delta) feasibility probe** (PR #40, merged): SKIP/NOT-FEASIBLE verdict. yfinance.analyst_price_targets returns ONLY current snapshot; `recommendations` DataFrame uses RELATIVE periods (0m/-1m/-2m/-3m) not absolute dates → can't backfill historical retrospectives. 30-minute probe saved 3h sunk cost. Path forward (deferred): Path C snapshot wiring would unlock future C-3 retrospectives at zero LLM cost.
38. **Cross-cohort behavioral-additive sweep** (PR #41, merged): walks all 236 state logs, finds 23 behavioral-additive cases across 6 tickers in ALL 4 mechanism classes (Spec 003 + Spec 007 bull + Spec 007 bear + Spec 008). Reframes L-8 from "PM-as-implicit-Spec-003" to **PM-as-multi-mechanism-validator**. v1.4.4 codification threshold MET.

**Open work entering 2026-05-08**:
- **SC-009 backtest** ~3h remaining; expansion contingency `experiments/2026-05-07-002-sc-009-expansion/` ready to kick off if `n_fired_boost_on < 4` after final row
- **v1.4.4 amendment draft (L-8 only)**: drafting eligible per PR #41 evidence; ratification deferred 1+ session (Constitution VI risk-management)
- **Hybrid D feasibility design doc**: ~5 candidate both-sides-priced-in cases identified by PR #41 (NVDA-04-24, MSFT-04-24, WFC-04-17, COP-04-24, COP-04-17). Cohort too small for retrospective today
- **C-5 (earnings price reaction) feasibility probe**: same de-risking pattern as C-1 SKIP + C-3 NOT-FEASIBLE. ~30min, $0
- **Path C snapshot wiring PoC**: defer until next backtest design (piggyback on existing LLM spend)
- **Memory polish to PM-as-multi-mechanism-validator framing**: ~15min, $0
- **Spec 003 historical-recompute script** still deferred (~2h)
- **CHANGELOG.md update for PRs #29-#41+** still deferred (~30min)

## 2026-05-07 PRs #57-#79+ — bear-side survey CONCLUDES; C-4 spec-eligible

Major arc: SC-009 backtest completion + bear-side mechanism class survey conclusion + Constitution amendment drafts + tooling.

**SC-009 backtest COMPLETED** (PRs #57, #58, #61): 36/36 rows. Final acceptance gates (PRELIMINARY — canonical 21d windows close ~2026-05-22+):
- Gate 1 (alt suppressed-α): PASS at +0.43% (monotone refinement: -4.44 → +1.75 → +1.12 → +0.43 across 13/23/27/36-row marks)
- Gate 2 (n_fired_boost_on ≥ 8): PASS at 13 (61% margin)
- Gate 3 (boost engaged ≥ 1): PASS at 18
- Verdict refined per PR #56: **PRELIMINARY PASS-by-non-counterexample** — 0 decisions changed by boost; recommend SHADOW-MODE-FIRST per Constitution VIII v1.4.0, NOT direct default-on flip

**Bear-side mechanism class survey CONCLUDES** (PRs #67, #74, #75, #76, #77, #78). 6/6 evaluated; **C-4 (institutional ownership delta) is the SOLE spec-eligible mechanism class**:

| Class | Standalone | Additive | Spec-eligible? |
|---|---|---|---|
| C-1 (insider transactions) | SKIP empirical | n/a | NO |
| C-2 (short-interest delta) | SKIP MECHANISM INVERTED | n/a | NO |
| C-3 (analyst PT delta) | NOT FEASIBLE | n/a | NO |
| **C-4 (institutional ownership)** | **PASS (n=12, +5.41pp)** | **PASS (+8.06pp Δα; PR #77)** | **YES (shadow-mode-first)** |
| C-5 EPS-surprise (2026-05-06) | PASS standalone, FAIL additive | n/a | NO |
| C-5 PRICE-REACTION (PR #74) | SKIP MECHANISM INVERTED | n/a | NO |
| C-6 (bear-news density) | SKIP structural | n/a | NO |

Two C-classes show INVERTED bear-side mechanism (C-2 short-covering, C-5 price-reaction): both originally hypothesized as mean-reversion; bear cohort empirically shows continuation. C-4 catches 11 bearish commits Spec 007 ENTIRELY MISSES — different signal sources (LLM semantic vs quantitative 13F flow). Three SKIP-types codified (empirical, data-availability, structural).

**Constitution amendment drafts** (PRs #44, #61, NOT YET RATIFIED):
- v1.4.4 (behavioral-additive 4th interpretation under Principle VIII v1.4.3) — drafted in PR #44 with 4-mechanism-class evidence base; counter-evidence watch (PR #49) confirms 0 refuting rows across 247+ logs; draft text-only per defensive two-stage pattern
- v1.4.5 (memory-log data-vs-prose discipline as new Quality Gate #6) — drafted in PR #61 with 20% systematic hallucination finding (3 of 15 entries in SC-009 backtest_memory.md)

**Tooling shipped**:
- `scripts/v1_4_4_counter_evidence_watch.py` (PR #49) — scans state logs for v1.4.4-refuting rows; CI-friendly exit code
- `scripts/memory_log_integrity_check.py` (PR #55) — flags reflection-prose hallucinations (rating-direction-vs-realized-return-sign mismatches)
- `scripts/spec_003_historical_recompute.py` (PR #71) — backfilled 254 cache rows; 9 tickers now clear FR-004 floor (NVDA, AAPL, INTC, XLE, MSFT, GOOGL, JPM, XLF, XLK)
- `scripts/forward_catalyst_class[2,4,4_vs_spec007,5_reaction]*.py` (PRs #74, #75, #76, #77) — bear-side retrospective harness family
- `tradingagents/agents/utils/analyst_pt_snapshot.py` (PR #73) — Path C wiring for future C-3 retrospectives (default OFF; ZERO LLM cost; ~50-200ms latency when enabled)

**Cross-session memories**: 14 → 22 (+8 new). Major additions: PM-as-multi-mechanism-validator reframe, memory-log reflection hallucination, PASS-by-non-counterexample, spec 003 cold-start coverage, pre_rating temporal-learning, no-day-rollover narratives, signals cache PK collision, pre-commit ruff silent rejection, bear-side survey complete.

**Test count**: 1123 → **1179** (+56 net across the day from PRs #38, #49, #55, #69, #71, #72, #73).

**Open work entering future sessions**:
- **Spec X-1 (C-4 institutional rotation filter)** — SHIPPED end-to-end via 6-PR bundle (#88-#93). Currently deployed at default-shadow bear-side / default-off bull-side. **Operator action**: monitor `state["forward_catalyst"]["institutional_rotation"]["would_fire_bear"]` rows in state logs; after ~30 shadow-mode observations, decide whether to flip `institutional_rotation_bear_mode` to `"active"` per SC-010 live-mode flip eligibility (n≥30 propagates A/B ablation requirement).
- **Constitution v1.4.5 (Quality Gate #6 Memory-log discipline) + v1.4.6 (Behavioral-additive 4th interpretation)** — BOTH RATIFIED 2026-05-07 (PRs #83 + #84). v1.4.4 draft content was ratified as v1.4.6 to preserve monotone numbering after v1.4.5 was ratified first per reasoning_decision rank ordering.
- **Spec 010 (Hybrid D bear-side calendar-boosted)** — CLOSED via PR #86 SKIP retrospective (structural argument; calendar-boost mechanism cannot operate on n=5 behavioral-additive bear cohort due to pre_rating gating). Bear-side calendar-boost mechanism class is methodologically closed (3 converging retrospectives).
- **Re-run C-4 overlap analysis after 2026-05-15** to verify single-quarter robustness — codified as Spec X-1 SC-009. If either gate drops below v1.4.0 / v1.4.3 thresholds on Q1 2026 13F panel, ablate `institutional_rotation_bear_mode` to `"off"` default pending investigation.
- **Final SC-009 ANALYSIS.md** writable ~2026-05-22+ when canonical 21d windows close (currently PRELIMINARY hand-edit preserved by analyzer guard)
- **Bear-side mechanism class survey COMPLETE** — no more 6-class probes needed; future bear-side hypotheses must propose new mechanism class outside the 6 OR justify re-testing a SKIP'd class with new data

## 2026-05-08 PRs #117-#136 — mypy sweep + WC-10 research arc + Constitution v1.5.0

20+ PRs across two distinct work tracks: tech-debt cleanup + WC-10 research arc.

**Track A — mypy floor sweep (PRs #117-#129, 12 PRs, all merged)**: cleared 124 errors / 17 files in 13 incremental zero-behavior-risk typing PRs. Headline finding: the CLAUDE.md baseline note characterized the LLM-client mypy cluster (~85 errors) as "complex / deferred / needs upstream stubs"; investigation revealed it was a trivial dict-invariance issue fixable with one `dict[str, Any]` annotation per file (PR #128, 4 lines, -85 errors). CLAUDE.md baseline note corrected in PR #129. Memory `reference_llm_client_kwargs_dict_invariance.md` codifies the "verify deferred/complex baseline classifications by trying the simple fix first" methodology lesson for future sweeps.

Per-PR breakdown:

| PR | Δ floor | Surface |
|---|---:|---|
| #117 | n/a | claudedocs cleanup |
| #118 | n/a | gitignore broaden |
| #119 | -7 | implicit-Optional widening (6 files, 14 sites) |
| #120 | -7 | helper signature cascade fix from #119 |
| #121 | -4 | `_make_api_request` return type tighten |
| #122 | -4 | paper/state.py + signals/evaluation.py narrowing |
| #123 | -3 | exa_news.py + macro.py None-narrowing |
| #124 | -2 | trading_graph.py log_states_dict + tuple guard |
| #125 | -3 | VENDOR_METHODS dispatch table annotation |
| #126 | -4 | TypedDict receiver widening (4 files) |
| #127 | -2 | research_manager renderer + checkpointer RunnableConfig |
| #128 | **-85** | LLM client llm_kwargs annotation (4 files, 4 lines) |
| #129 | -2 | types-requests stub + CLAUDE.md baseline correction |
| | **-124** | mypy 126 → 0 |

**Track B — WC-10 research arc (PRs #107-#114 from earlier session + PRs #130-#136 from this session arc)**:

The full WC-10 arc shipped 14 PRs across the spec deployment + pilot + analysis + amendment + expansion + procedure codification:

- Earlier session (PRs #107-#114): spec-kit 6-PR bundle (#107 spec → #108 plan → #109 tasks → #111 pilot harness → #112 tests) + 2 hotfix PRs (#113 prompt + #114 harness extract bug)
- This session (PRs #130-#136):
  - **#130** — v1 pilot ANALYSIS.md (40 propagates, $16, **SC-007 ALT-A confirmed at 3.6× commit ratio**, 75% paired decisions differ, NVDA Buy n=6 mean +4.67% α 21d, AAPL UW n=6 mean +3.56% α anti-calibrated)
  - **#131** — Constitution v1.4.3 → **v1.5.0** amendment ("Schema-induced abstention is NOT calibrated abstention" sub-section to Principle VII)
  - **#132** — RESEARCH_FINDINGS.md reframe of mode collapse as TWO-MECHANISM (genuine ambiguity + schema artifact)
  - **#133** — v2 expansion scaffold (8 tickers × 10 dates × WC-10 mode = 80 propagates, $32, ~12h wall-clock; KICKED OFF in background)
  - **#134** — v3 bear-regime test scaffold (Q4 2025 NVDA, 16 propagates, $6.40, ~2.5h wall-clock; KICKED OFF in background)
  - **#135** — pre-scaffolded ANALYSIS_TEMPLATE.md for v2 + v3 (when data lands, plug in numbers)
  - **#136** — Spec 011 behavioral-additive operational procedure (codifies Constitution v1.4.6 invocation pattern with 6 FRs)

**WC-10 IS the first non-filter / non-prompt-tweak intervention to produce a decisive falsification verdict** in the corpus. Prior interventions (MR-1 through MR-3, EH-2, prompt variants, single-call baselines) either produced no signal or NULL verdicts. WC-10 produced ALT-A at p < 0.001 effect size (3.6× commit ratio with 75% decisions differing). The mode-collapse-to-Hold reframe converts Constitution VII from a unitary principle into a two-mechanism principle with empirical heuristics for distinguishing the two sub-populations.

**In-flight work entering future sessions**:

- ~~WC-10 v2~~ → **RESOLVED 2026-05-09** (PR #181). Combined v1+v2 (n=100): Pearson r +0.0918, Spearman ρ +0.0410 — SC-005(b) **NULL** (below ±0.197 critical). SC-007 ALT-A: PARTIAL (5/8 tickers ≥80% commit; JNJ + GOOG + JPM retained Hold-default). Bullish-amplification REPLICATES (Buy n=20 α +2.93% / 80% hit). **Branch C selected** (bin-then-output pattern). NVDA degenerate-attractor (all 10 dates +0.6200) is the most surprising negative finding.
- ~~WC-10 v3~~ → **RESOLVED 2026-05-08 evening** (PR #153). Q4 2025 NVDA cohort: PARTIAL ALT-A (8/8 dates Buy/OW vs 5-tier 0 OW + 1 UW + 7 Hold; α delta -0.22pp within ±100bps NULL region). Constitution VII v1.5.0 → v1.5.1 ("Bear-regime validation" paragraph; PR #154).
- ~~WC-11 analyst-order randomization~~ → **RESOLVED 2026-05-09** (PR #177). NVDA × 5 dates × 4 perms (n=20, $8). Per-permutation commit rate 0% → 40%; ALT-A + ALT-B both trigger on `news_fundamentals_market` (cannot disambiguate at n=20). DEFAULT order is Hold-biased. Constitution v1.5.1 → v1.5.2 (Analyst-order scope; PR #179).
- ~~BR-3 Squeak market-analyst structured-output~~ → **RESOLVED 2026-05-09** (PR #178). NVDA + AAPL × 5 dates × 2 modes (n=20, $8). PARTIAL ALT-B (commit shift +20pp; α delta +0.24pp below threshold). Phase E architectural variant NOT unblocked at this evidence level. No Constitution amendment.
- **Spec 009 Branch C MVP** — PR #4 of v2 4-PR landing series; activates bin-then-output pattern (continuous internal representation; 5-tier external interface preserved). Pre-scaffolded design surface 5/7 already shipped (spec.md + plan.md + contracts + research.md + quickstart.md). Tasks.md + MVP code + tests + polish remain.
- **Spec 011 first invocation deferred** — methodology spec is shipped; first filter spec to invoke v1.4.6 will cite Spec 011 in its retrospective. No specific candidate identified yet (bear-side survey is COMPLETE; bull-side may produce a candidate from continued state-log accumulation).
- **WC-10 production deployment** — Branch C selected per v2 NULL verdict. Bin-then-output pattern via Spec 009 MVP captures the bullish-amplification ergonomic gain without false-precision scalar claim. SC-005(b) MODERATE/STRONG branches (Branch A/B) are NOT activated.

**Test count**: 1146 → 1146 (no test additions in the cleanup arc; mypy fixes are typing-only). WC-10 unit tests landed in earlier session (10 unit + 2 integration tests for `bin_scalar_to_tier` + PM integration).

## Prior research-burst day — 14-work-unit (2026-05-06; tagged v0.8.0-spec-008)

The day expanded through evening + late-evening sessions, ultimately shipping **12 ship-quality units** across **14 distinct work activities**. The post-Spec 007 work units (in commit order on the late-evening session):

20. Spec 007 merge to main + tag `v0.7.0-spec-007` (earlier evening)
21. Forward-catalyst mechanism design doc + pivot (Class 2 options-IV data-blocked → Hybrid C as substitute, commits `ada8ebb` + `25adb67`)
22. Hybrid C retrofit retrospective (`91135eb`) — DECISIVE PASS bull-side at window=14d/magnitude=0.5x; +3.35pp Δα improvement vs Class 3 alone
23. Hybrid C production-config retrospective confirms (`6cc7be9`) — identical numbers (DEFAULT_CONFIG matched retrofit)
24. Constitution v1.4.0 → v1.4.1 (`b470383`) — Principle VI sub: spec ships its retrospective + verdict
25. Spec 008 design bundle (1850+ LOC: spec.md + plan.md + research.md + data-model.md + contracts/ + quickstart.md + tasks.md, branch `007-calendar-boost-filter`)
26. Spec 008 implementation (`1f1ef27`) — calendar_boost.py helper + spec 007 integration + 34 net-new tests
27. Spec 008 live smoke (`d2680d8`) — real Opus + real yfinance, boost > 0 path verified end-to-end ($0.05)
28. Spec 008 merge to main via PR #6 (`6d7e417`) + tag `v0.8.0-spec-008`
29. Spec 009 candidate (bear-inverted Hybrid C) retrospective — SKIP verdict (+0.00pp at every config; PR #7 open)
30. Constitution v1.4.1 → v1.4.2 (PR #8 open) — Principle VIII sub: magnitude fungibility for hybrid filters
31. Meta-retrospective `claudedocs/research-burst-2026-05-06.md` (PR #9 open) — canonical day-end narrative
32. Doc refresh — README + RESEARCH_FINDINGS + CHANGELOG (PR #10 open)
33. Spec 008.5 latency-benchmark amendment (PR #11 open) — closes the 1 coverage gap from /speckit.analyze
34. (this) ROADMAP + claudedocs/SETUP refresh

Full arc captured in `claudedocs/research-burst-2026-05-06.md`. Filter portfolio at `v0.8.0-spec-008`: **8 sides total** (5 default-active, 3 default-off operator-opt-in — see CLAUDE.md "Empirical filters" section + RESEARCH_FINDINGS.md "Filter portfolio status" section).

**Methodology validation**: Constitution v1.4.1 retrospective-first pattern shipped 6 retrospectives today (2 PASS + 4 SKIP) + 1 candidate SKIP. Empirical ROI: ~10-13× wall-clock leverage on the spec invocations that DID launch (5 SKIP outcomes × 6-8h avoided spec cycles = 30-40h saved). Cost asymmetry validated by direct measurement.

## Original active branch — 11-work-unit research-burst day (2026-05-06; pre-Spec 007)

Today's arc (in commit order on main):

1. **Spec 003.5 sector-baseline fallback** (`specs/003-sector-baseline-gate/`, PR #3 merged): when per-ticker history < N=20 floor, gate aggregates across same-sector tickers from the yfinance cache. Closes the cold-start universe gap. 10+15 unit tests. Default-on.

2. **Spec 004 sector-momentum filter** (`specs/004-sector-momentum-filter/`, PR #4 merged): suppresses Buy/OW when sector ETF is in mean-reversion zone. ~29 tests + new SECTOR_ETF_MAP constant covering 11 GICS sectors. SC-008 validation (`claudedocs/spec-004-sc008-validation-2026-05-06.md`) FALSIFIED the motivating premise: XLF was -4.54% (above -5% threshold), filter would suppress 0/5 of SC-003 Financials (not ≥3/5). Corpus retrospective (`claudedocs/sector-momentum-retrospective-2026-05-06.md`) showed -0.45pp net Δα across 73 commits. Default-off; ships as operator-opt-in.

3. **INTC +103%-on-Hold investigation** (`claudedocs/sc003-intc-hold-investigation-2026-05-06.md`): INTC went +103.14% in 21 trading days from 2026-04-03 (driven by April 23 earnings catalyst). Framework rated Hold; calibrated abstention per Constitution VII validated. Surfaced spec 003 default-on as a counter-example: if PM had committed Buy/OW, the spec 003 contrarian gate would have suppressed back to Hold (NVDA + AAPL retrospective evidence is n=2; 1 large counter-example would dwarf cumulative gain).

4. **Spec 003 contrarian gate threshold sweep** (`scripts/contrarian_gate_threshold_sweep.py`, `claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md`): walks 228 propagate state logs in `~/.tradingagents/logs/`, computes per-ticker strict-prior `bull_keyword_count` history, sweeps thresholds 75/80/85/90/95th percentile. 11 of 82 bullish commits eligible (above N≥20 floor + α available). At default 80% threshold: net Δα = +0.65pp. Verdict: **KEEP default-on at 80%** — tightening doesn't help (gate never fires at 85+); loosening to 75% gives +1.36pp but more incorrect-suppression risk.

5. **Sector-α attribution analyzer** (`scripts/sector_alpha_attribution.py`, `claudedocs/sector-alpha-attribution-2026-05-06.md`): walks all 194 commits in the corpus, computes (raw_return, α-vs-SPY, α-vs-sector-ETF) at 21d, cross-tabs sign(α-vs-SPY) × sign(α-vs-sector) into 4 cells. **Surfaced 5th failure mode** (27/79 bullish commits in ticker_weak with -5.34% mean α; 88.9% Tech-concentrated) AND **bearish anti-calibration shock** (18/37 bearish commits in ticker_strong with +28.02% mean α-vs-SPY). Both findings are RESEARCH_FINDINGS-grade; documented in their own sections there.

6. **Spec 006 design bundle** (`specs/005-bear-sector-symmetry/`, full speckit Phase 0+1+2): 1664 LOC across spec.md + plan.md + research.md + data-model.md + 2 contracts + quickstart.md + 31-task tasks.md. Mechanism: when ticker has outperformed sector ETF by >threshold% in prior 30d, suppress UW/Sell to Hold (counter-trend bear suppression).

7. **Spec 006 implementation + retrospective**: ~190 LOC implementation (reuses spec 004's `SECTOR_ETF_MAP` + `_etf_history` LRU cache per FR-004; new `_ticker_history` LRU). Retrospective (`claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md`) ran on 36 valid bearish commits. **SC-008 FAILED at +5%**: 5 of 18 cohort commits fire (target was ≥8). Net Δα at +5% = **-0.71pp anti-predictive**. Default-off; ships as operator-opt-in. Mirrors spec 004's outcome.

8. **Spec 006 merge into main** (commit `4d0401d` --no-ff): closes the spec 006 work unit; feature branch deleted local + remote.

9. **Spec 005 retrospective FIRST** (`scripts/ticker_sector_alpha_retrospective.py`, `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`): pre-spec validation of the per-ticker-vs-sector BULL filter hypothesis. Both criteria: (a) max +0.31pp net Δα across 79 commits — FAIL +1pp gate; (b) 48% cohort hit rate at +3% — PASS 40% gate. **Verdict: SKIP spec entirely** — cohort-loser suppression washed by winner suppression at indistinguishable rel-strength values. The pre-spec retrospective saved 6-8h of empty-spec implementation.

10. **Constitution v1.3.0 with Principle VIII** (`.specify/memory/constitution.md`): codifies "backward-looking price filters require pre-spec corpus retrospective showing net Δα ≥ +1pp at proposed default threshold + cohort hit rate ≥ 40% (when target cohort named) BEFORE any spec is written." Three same-day retrospective failures validated the case.

11. **Constitution-VIII follow-up**: cross-reference Principle VIII in spec 004 + spec 006 spec.md preambles + quickstart.md "What's new" sections + SC-008 measurable-outcome entries. Future readers of either spec immediately see (a) default-off status, (b) empirical verdict with numbers, (c) Principle VIII pointer, (d) grandfathered status (spec was authored BEFORE Principle VIII).

**No experiment currently selected.** Today was a research-burst day; tomorrow's options are tracked in the open data questions table below.

---

## Sequenced phases of exploration (post-Opus)

### Phase B — out-of-sample validation (priorities reordered post-Q3-recovery)

After NVDA Q3 2025 the load-bearing claim recovers (2 of 3 periods positive; posterior 0.52 → 0.63). Phase B priorities now:

- **B-priority 1 — A3 filter forensics**: **DONE** (`claudedocs/a3-filter-forensics-007.md`). Filter validated as correctly inert on the regime-mismatch failure mode; no tuning needed from 007 evidence.
- **B-priority 2 — cross-period validation**: **DONE as experiment 008**. Result: Scenario C (signal collapses on shifted period). Bayesian posterior 0.64 → 0.52. Reframe applied to RESEARCH_FINDINGS + Constitution v1.2.2.
- **B-priority 2b — third cross-period (Q3 2025) at T2 ~$10**: **DONE as experiment `2026-05-04-001-nvda-q3-2025-micro`**. Result: Scenario A — posterior climbs back to 0.63. Q4 2025 confirmed as the outlier; Q1 2026 is consistent with Q3 2025.
- **B-priority 3 — bear-correct ticker pilot (XOM, PFE)**: lower priority. Adds fresh bear-side data points but doesn't directly address the load-bearing period-conditional question. ($15, ~12h, T2)
- **B-priority 4 — same-date rerun-variance quantification**: 005-vs-007 NVDA non-replication suggests rerun variance is non-trivial. n=3 reps on the same 10 NVDA dates with current config would quantify the bucket-ratio variance bands. ($15, ~12h, T2 — would be the formal evidence backing Constitution VII Replicability-scope clarification)
- **B-priority 5 — model-swap matrix**: Sonnet vs Opus vs GPT-5.4 vs Gemini 3.x on the same grid. Tests whether the period-conditional realized α is a model property or a substrate property (does Sonnet show the same Q1-vs-Q4 sign flip?). Now also enabled by Spec 001 Phase 4 per-bot routing — could mix models within a single grid. ($20-40, T2/T3)
- **B-priority 6 (new) — Phase 4 cost-tier validation**: matched-baseline n=10+ run with `bot_models` set to bump `fundamentals` (heaviest analyst) → Opus while keeping the rest on Haiku. Tests whether per-bot model swaps shift rating distribution beyond known mode-collapse behavior. Phase 4 is wired and live-validated at n=1; the cost-savings story needs n≥10 to characterize. ($5-10, T2)

### Phase C — operational integration

The framework currently outputs ratings. With the A3 filter wired in, it could output more:

- **`reasoning_evidence` second-opinion in PortfolioManager** with asymmetric handling per Q5 (agreement → augment confidence, disagreement → flag for review). **DONE as `tradingagents/agents/utils/second_opinion.py`** + 29 unit tests + Phase C smoke test (`experiments/2026-05-04-005-phase-c-smoke-test/`). Default disabled; opt-in via `config["second_opinion_enabled"] = True`. ~$0.10/run forward when enabled.
- **Bias auditor** running `reasoning_detect` over saved bull/bear debates — produces a per-experiment bias profile (confirmation, anchoring, recency, overconfidence). Validates A1's hedge-words finding programmatically. (2-4h)
- **Counterfactual analyzer** running `reasoning_counterfactual` on Hold-α extreme dates as part of every analysis pass — auto-builds the "what if framework had committed?" narrative for FINDINGS. **PARTIAL** — `tradingagents/signals/counterfactual.py` (Spec 002 Phase 2) ships `run_counterfactual` + `hold_all_uw` / `hold_all_ow` / `invert_all_commits` but is not yet wired into per-experiment auto-analysis. (1-2h to wire)

### Phase D — substrate exploration (different problems, same framework)

Equities are the chosen substrate because they're cheap to evaluate. The framework's findings (calibrated abstention + 21d directional skill) might generalize to other domains:

- **Crypto pairs** — different volatility regime, different news ecosystem
- **FX pairs** — macro-driven, different debate texture
- **Sector ETFs** — debate over whole-sector trends instead of single stocks
- **Options-implied volatility** — debate over IV regime instead of price direction
- **Sports betting / prediction markets** — same ground-truth structure (forward outcome, benchmark to compare against), totally different evidence base. Genuinely tests generalization.

### Phase E — architectural variants

The current framework is one specific choice (4 analysts → bull/bear debate → research manager → trader → 3-persona risk debate → portfolio manager). Other architectures worth testing:

- **No-debate baseline** — analysts → portfolio manager directly, no bull/bear stage. Variant of single-call baseline but using full framework infrastructure
- **Inverted-role debate** — analysts argue against their own report's lean (forces evidence steel-manning)
- **N-perspective generation via `reasoning_divergent`** — replace bull/bear with N divergent perspectives, then synthesize
- **Tree-search exploration** — `reasoning_tree` generates branches of investment theses, scored, pruned, finalized. Replaces linear debate with branching
- **Graph-of-thoughts pipeline** — `reasoning_graph` structures the analyst → debate → synthesis chain as a DAG with intermediate aggregation nodes

---

## Cross-pollination opportunities (Principle V — Steal Liberally)

Patterns from sibling projects worth porting. **Relevance re-ranked 2026-05-08 post-WC-10**, see `claudedocs/cross-pollination-review-2026-05-08.md` for full deep-dive. Tier legend: L5=ship-eligible / L4=pilot-eligible / L3=worth-testing-in-design / L2=speculative / L1=superseded-or-deprioritized.

| Tier | From | Pattern | Where it'd go in TradingAgents-lab |
|---|---|---|---|
| **L4 (pilot landed 2026-05-09)** | **battlecode2026 ratbot6** | **Squeak (structured signaling) — BR-3 v1** | Analysts emit `{bullish, bearish, key_risks}` instead of prose. **Pilot result PARTIAL ALT-B** ($8, n=20, PR #178): commit shift +20pp triggered but α delta +0.24pp below threshold. Phase E NOT unblocked; L4 status preserved at "pilot-eligible" (not promoted). Sister extensions BR-3 v2 (news + fundamentals analysts; ~$8 each) would clarify generalization. |
| **L4 (NEW post-WC-10)** | **agent-harness-v2** | **Knowledge digestion + antibodies** | Auto-tag historical Hold commits as genuine-ambiguity vs schema-induced collapse via WC-10 replay. $0 LLM (saved data only). |
| **L4 (NEW post-WC-10)** | **mcp-reasoning** | **Self-improvement system** | Extend `scripts/memory_log_integrity_check.py` to flag WC-10 commits that underperform 5-tier baseline. Closes Constitution v1.5.0 monitoring loop. $0. |
| L5 (already pollinated) | mcp-reasoning | 15+ reasoning modes (linear/tree/divergent/reflection/decision/evidence/mcts/graph/counterfactual/…) | Reasoning_decision drove 8+ of 2026-05-08 PRs; pollination operationally complete |
| L5 (already pollinated) | branch-thinking / logic-thinking | Structured reasoning tools | Already exercised via mcp-reasoning |
| L3 | agent-harness-v2 | Event sourcing | Spec 002 partially shipped via signals/cache.py; unified event log for memory + checkpoint + paper-trade is Phase E |
| L3 | agent-harness-v2 | Structural enforcement / gates | New post-WC-10: enforce SCHEMA-AWARENESS in spec-writing — every new filter spec MUST declare which v1.5.0 sub-population its mechanism targets |
| L3 | battlecode2026 ratbot6 | Unified value function architecture | Sister to Squeak; together = "structured-output-throughout" Phase E variant |
| L3 | battlecode2026 ratbot6 | Self-removal after idle threshold | Skip analyst if report below content threshold — analyst-stage equivalent of Constitution VII Hold |
| L2 | ladybird | Sentinel pattern (out-of-process enforcement) | Operational complexity high; current in-process filter chain works |
| L2 | battlecode2026 ratbot6 | Value function over assigned roles | Sister to Squeak; standalone harder to apply |
| L2 | battlecode2026 ratbot6 | Bytecode budget tracking + Profiler | Useful tool, not strategic |
| L2 | battlecode2026 ratbot6 | Explicit state machine | Engineering hygiene; not strategic |
| **L1 (deprioritized 2026-05-08)** | battlecode2026 ratbot6 | Pre-computed decision-rule shortcuts | WC-10 finding: schema is already too constraining; pre-computed rules constrain it MORE. Deprioritize. |
| **L1 (deprioritized 2026-05-08)** | bruno-swarm | abliteration for specialization | Squeak is cheaper + tests adjacent hypothesis; abliteration's infrastructure burden disproportionate |

**New patterns surfaced 2026-05-08** (extractable as project tooling):

| Tier | From | Pattern | Application |
|---|---|---|---|
| L4 | this project (today) | **Conditional-branch spec drafting** | Pre-write spec.md with N verdict-conditional branches (Spec 009 pattern). Could ship as `.specify/templates/spec-template-conditional.md` |
| L4 | this project (today) | **Pre-scaffolded ANALYSIS templates** | Write ANALYSIS_TEMPLATE.md alongside HYPOTHESIS.md (PR #135 pattern). Could ship as `scripts/new_experiment.py --with-analysis-template` flag |

---

## Deferred lines worth picking up later

### From the in-session code-improvement list

| # | Item | Effort | Note |
|---|---|---|---|
| 4 | Test coverage on framework innards: `anthropic_client.py` (0%), `openai_client.py` (0%), `graph/setup.py` (12%), `graph/conditional_logic.py` (21%) | hours | These are the load-bearing modules with the lowest coverage. Smoke tests with mocks would catch regressions before they hit propagate() |
| 5 | `PriceCache` helper class to standardize per-ticker yfinance fetch + date-padding boilerplate across analysis scripts | 1h | Eliminates ~15 lines of identical setup per script; centralizes the date-padding logic that currently varies subtly |
| 6 | Constitution Principle V enforcement — commits should cite which sibling-project technique they came from | philosophical | Either drop the principle or actually do it |
| - | Drop the 215 → ~30 ruff baseline by sweeping with `__all__` protections in place | ~1h | Most are stylistic modernizations (Optional → X \| None, etc.). Cosmetic but improves signal-to-noise on linter output |

### From docs/EXPERIMENT.md (~50 ideas)

- Most Tier 1/2 ideas not yet attempted (the 11 completed experiments cover only MR-1, WC-12 variants, MR-2, MR-3, EH-2, brave/exa news swaps, single-call baseline)
- Worth a re-read after Opus lands to mark which are obviated by current findings vs which still discriminate

---

## Open data questions (post-007)

These need new experiments to answer; no amount of analysis on existing CSVs will resolve them.

| Question | Proposed experiment | Cost | Status |
|---|---|---|---|
| Does the 21d bull lift hold at n=100+? | Q3 2025 third cross-period (T2 $10) → if positive, posterior recovers | $30 | **partial-resolved — n=71 cross-period evidence; +1.23% mean α; 2-of-3 periods positive; posterior 0.63** |
| Is the lift period-specific or persistent across calendar windows? | 008 + Q3 micro done: Q1 2026 + Q3 2025 positive, Q4 2025 negative outlier. | $10 + $5 | **resolved (3-period)** — moderately period-stable; Q4 2025 is the outlier |
| Is the lift ticker-class specific (mega-cap tech vs others)? | Sector-stratified pilot — Phase D XLK + multi-sector + XLE done | $20 | **partial** — Phase D shows decision architecture portable, calibration substrate-specific |
| Does the A3 filter generalize off-sample? | Already validated by 007 forensics for regime-mismatch case; off-sample mean-reversion test still open | $10 | **partial** |
| Does Opus / GPT-5.4 / Gemini 3.x show the same 21d shape? | Model-swap matrix — now enabled by Spec 001 Phase 4 per-bot routing | $20-40 | partial — Sonnet + Opus done, others open |
| Is the bear-correct-ticker UW signal robust beyond AAPL + INTC? | XOM or PFE 10-date pilot | $15 | open (B-priority 3) |
| Does the framework predict longer horizons (60/90d) where 5d failed and 21d worked? | Re-aggregate current data + extend window with future price data (60-day wait) | $0 + time | **partial** — Spec 002 Phase 1.5+ multi-horizon eval (5d/10d/21d/90d) shipped; bear_bigram_count IC = +0.457 at 90d |
| Does same-prompt rerun-variance dominate the signal at the date level? | n=3 reps on the existing 10 NVDA dates with current config — formalizes the 005-vs-007 finding | $15 | open (B-priority 4) |
| Does spec 002 (signal-lifecycle) IC measurement reveal which signals are noise? | Build signal-lifecycle pipeline + run on saved state logs | $0 build + $0 run | **resolved** — Spec 002 Phases 0-2.5 shipped; first IC measurement: final_trade_decision IC = -0.172 at 21d, n=153; strongest IC: bear_bigram_count = +0.457 at 90d |
| Does per-bot LLM model routing (Spec 001 Phase 4) shift rating distribution beyond mode-collapse? | n=10+ matched-baseline run with `bot_models = {"fundamentals": "claude-opus-4-7"}` | $5-10 | open (B-priority 6, new) |
| Can a forward-catalyst-aware mechanism catch the 27-row 5th-failure-mode cohort + the 18-row +28%-mean-α ticker_strong-bear cohort? | Design-doc-only exploration of news-density signals / options-IV / LLM-extracted "bull case priced in" feature. Different mechanism class than backward-price-only (Principle VIII grandfathering). | $0 design + $20-40 to implement + retrospect | **partial-resolved (post-spec-007 + spec-008)** — Spec 007 Class 3 LLM feature catches a meaningful slice of the 5th-failure-mode cohort (88.9% bull cohort hit, +14.43pp discrim, +2.24pp net Δα). Spec 008 Hybrid C adds +3.35pp Δα on top. Bear-side ticker_strong cohort still uncaught — bear-inverted Hybrid C SKIP'd, suggests bear-side may need a different mechanism class entirely (Class 4 macro / Class 5 fundamentals deferred). |
| Does a Class 4 (cross-asset/macro) filter catch the bear-side ticker_strong cohort? | VIX + 10y yield + USD index + sector ETF correlation features. Build cohort + retrofit script per Spec 008 design doc Class 4 entry. | $2-10 LLM + ~3h | **open (NEW post-spec-008)** — bear-side cohort still uncaught after all 8 filter sides |
| Does a Class 5 (fundamentals-delta) filter add discrimination beyond Class 3? | Recent earnings surprise + analyst revisions as features. Same retrofit shape; different mechanism. | $1-5 LLM + ~3h | **open (NEW post-spec-008)** — orthogonal to Class 3's prose synthesis |
| Does the Spec 008 Hybrid C bull-only retrofit hold under live-mode A/B ablation? | Run daily_signals.py with boost enabled vs disabled on n≥30 same propagates; verify +3.35pp at 21d. | $5-10 LLM | **open (Spec 008 SC-009 condition for default-on flip)** |
| Does multi-window SC-003 replication strengthen all retrospectives? | Re-run SC-003 50-ticker on 3-5 additional dates; would expand corpus from 234 to 290+ commits + spec 003 eligible from 11 to 30+ + spec 006 ticker_strong cohort from 18 to 40+. | $40 (T3) | **open (NEW post-spec-006)** — biggest empirical-strengthening lever |
| At what corpus size does Spec 005 percentile-based variant become viable? | Extend per-ticker history to 30+ obs per ticker; re-run `scripts/ticker_sector_alpha_retrospective.py` with `--percentile-history-floor 30`. May surface signal that washed at the absolute-threshold variant. | $0 retrospective; needs corpus-expansion first | **open (NEW post-spec-005-skip)** |
| ~~Does scalar magnitude predict α magnitude beyond binary commit/abstain at n=100?~~ | WC-10 v2 expansion (PR #181). | $32 | **RESOLVED 2026-05-09 — NULL** (Pearson +0.0918 / Spearman +0.0410 < 0.197 critical). Branch C selected. |
| ~~Does WC-10 schema fix make bear-regime calibration WORSE, NEUTRAL, or BETTER on Q4 2025 NVDA cohort?~~ | WC-10 v3 (PR #153). | $6.40 | **RESOLVED 2026-05-08 — PARTIAL ALT-A** (direction matches; α delta -0.22pp within ±100bps NULL region). Constitution v1.5.0 → v1.5.1. |
| ~~Does ALT-A categorical-bottleneck pattern generalize across tickers beyond NVDA + AAPL?~~ | WC-10 v2 secondary (PR #181). | $0 | **RESOLVED 2026-05-09 — PARTIAL** (5/8 tickers ≥80% commit; JNJ + GOOG + JPM retained Hold-default). v1.5.0 carve-out validated as sub-population not wholesale. |
| ~~Does the v1 NVDA Buy bullish-amplification generalize beyond NVDA?~~ | WC-10 v2 tertiary (PR #181). | $0 | **RESOLVED 2026-05-09 — REPLICATES** (Buy combined n=20 α +2.93% / 80% hit; OW n=32 α +2.10% / 53% hit). |
| ~~Should `daily_signals.py` integrate WC-10 as an opt-in mode for operator workflows?~~ | Spec 009 Branch C MVP (PR #4 of v2 landing series). | $0 spec design + Branch C MVP impl | **Branch C selected** — bin-then-output pattern; 5-tier external preserved; continuous internal for richer audit trail. Branch A/B (operator-opt-in scalar exposure) NOT activated per NULL verdict. |
| Does analyst-order randomization meaningfully shift bucket-level claims? | WC-11 (PR #177). | $8 | **RESOLVED 2026-05-09 — PARTIAL ALT-A + ALT-B** (per-perm commit rate 0% → 40%; cannot disambiguate at n=20). DEFAULT order Hold-biased. Constitution v1.5.2 mandates randomize-or-document. |
| Does analyst-stage structured-output unblock Phase E (structured-throughout)? | BR-3 Squeak market-analyst (PR #178). | $8 | **RESOLVED 2026-05-09 — PARTIAL ALT-B** (commit shift +20pp; α delta +0.24pp below threshold). Phase E NOT unblocked at this evidence level. BR-3 v2 (news + fundamentals analysts; ~$16 total) would clarify generalization. |
| Can the behavioral-additive escape clause (Constitution v1.4.6 + Spec 011) ever be invoked, or is bear-side mechanism survey COMPLETE making it dormant? | Future state-log accumulation may reveal new bull-side filter candidates that fail v1.4.3 actual-fires gate but pass v1.4.6 counterfactual gate. Bear-side survey is closed (6/6 evaluated, only C-4 spec-eligible). | $0 (passive — depends on accumulated state logs) | **deferred (Spec 011 first invocation)** |

---

## How to use this doc

When a phase fires (e.g. Opus result lands), update the **Active branch** section with the chosen sub-branch and what experiments / builds it triggered. Move completed phase items to RESEARCH_FINDINGS or `findings.md` as their results are written up. Add new exploration ideas to the appropriate phase as they surface — particularly the cross-pollination table when a sibling project ships something new worth porting.

This doc lives at the root with FINDINGS / RESEARCH_FINDINGS / README so anyone (including future you) can scan the directional state of the project from the top-level tree.
