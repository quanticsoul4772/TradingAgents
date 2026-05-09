# Changelog (personal fork)

All notable changes to this **personal experimental fork** of TradingAgents are documented here. Upstream history lives in [`CHANGELOG.upstream.md`](CHANGELOG.upstream.md).

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added (2026-05-09 — Triple-pilot landing arc COMPLETE + WC-10 research arc CLOSED + Constitution v1.5.1 → v1.5.2 + Spec 009 Branch C activated)

**Triple-pilot landing arc** (8 PRs merged: #179-#186) lands all 3 in-flight pilots (WC-10 v2 + WC-11 + BR-3) plus consolidated docs + Spec 009 Branch C MVP + day-end synthesis + monitor smoke test. $48 LLM (3 pilots; pre-spent in prior session). Wall-clock ~2.5h. Demonstrates rank-driven shipping + pre-scaffolding ROI (~3-6× per-PR vs cold-draft baseline). Canonical day-end synthesis at `claudedocs/research-burst-2026-05-09.md`.

**WC-10 v2 (n=80, 8 tickers × 10 Q1 2026 dates) → SC-005(b) NULL + Branch C selected** (PR #181, $32 LLM):
- Combined v1+v2 (n=100): Pearson r **+0.0918**, Spearman ρ **+0.0410** (both BELOW ±0.197 critical at p=0.05). Scalar magnitude carries no detectable signal beyond what the binned tier captures.
- SC-007 ALT-A generalization: PARTIAL — 5/8 tickers ≥80% commit (NVDA 100%, AMZN 100%, MSFT 90%, AAPL 80%, XOM 80%); 3/8 retain Hold-default (JPM 70%, GOOG 60%, **JNJ 10%**) → fall back into Constitution VII original "genuine ambiguity" sub-population.
- SC-005(c) bullish-amplification REPLICATES: Buy n=20 combined α +2.93% / 80% hit; OW n=32 α +2.10% / 53% hit. Bearish-side anti-calibration also replicates EXCEPT XOM (UW n=8 -1.45%, calibrated bear-correct).
- Notable counter-finding: **NVDA degenerate-attractor** — all 10 NVDA propagates emitted exactly +0.6200 (continuous-scalar mode does NOT prevent intra-ticker mode collapse to a single value). JPM strongly NEGATIVE within-ticker IC (-0.6656).

**WC-11 analyst-order randomization → PARTIAL ALT-A + ALT-B + Constitution v1.5.2** (PRs #177 + #179, $8 LLM): NVDA × 5 dates × 4 permutations (n=20). Per-permutation commit rate range **0% → 40%** (±20pp from pooled mean). Both ALT-A (news-first) and ALT-B (market-last) triggers fire on the same `news_fundamentals_market` permutation — cannot disambiguate at n=20. **DEFAULT order is Hold-biased**. Constitution VII v1.5.1 → v1.5.2 PATCH: new "Analyst-order scope" paragraph in Replicability sub-section. Future ablations targeting commit-rate metrics MUST randomize order or document as confounder.

**BR-3 Squeak market-analyst structured-output → PARTIAL ALT-B** (PR #178, $8 LLM): NVDA + AAPL × 5 dates × 2 modes (n=20). Structured mode produced +20pp commit shift vs prose (commit-shift trigger MET) but α delta +0.24pp below ALT-B magnitude threshold. NVDA unanimous-Hold across all 10 propagates; AAPL is the only divergence ticker (sister to WC-10 bear-side amplification observation). **Phase E architectural variant NOT unblocked at this evidence level.** No Constitution amendment required. L4 cross-pollination status preserved at "pilot-eligible".

**Spec 009 Branch C MVP shipped** (PR #184, $0): bin-then-output ergonomic-only mode. New PARAMS key `wc_10_internal_only: bool` (default False). When True AND `wc_10_enabled=True`, the LLM emits a continuous scalar internally but the rendered Rating header is binned to 5-tier via `bin_scalar_to_tier()` before downstream consumers see it. 3 new unit tests (15/15 WC-10 tests pass). `daily_signals.py` does NOT expose WC-10 flags — production-facing signals remain 5-tier per the v2 NULL verdict. Implementation: ~30 min wall-clock (vs plan estimate 1.5h; pre-scaffolded design surface 5/7 saved time).

**Joint multi-mechanism reframe** (PR #180): WC-10 + WC-11 + BR-3 collectively identify **at least 4 structural sources of mode-collapse-to-Hold**: (1) genuine ambiguity (Constitution VII original); (2) schema-induced collapse (v1.5.0); (3) analyst-order-biased pooling (v1.5.2); (4) weak analyst-format signal (BR-3 PARTIAL ALT-B). Mode collapse is a multi-mechanism phenomenon, not a single-cause artifact.

**WC-10 underperformance monitor compatibility audit** (PR #186, $0): smoke test PASSES on v1 paired CSV (cohort cumulative Δα +22.42pp; 2 per-pair alerts on AAPL bear-side anti-calibration). No monitor modification needed for Spec 009 Branch C. v2 cross-corpus extension deferred until corpus n≥200.

**WC-10 research arc total**: $54.40 LLM (v1 $16 + v2 $32 + v3 $6.40) across 4 ratified Constitution sub-sections (v1.5.0 + v1.5.1 + v1.5.2 Analyst-order; plus pre-existing v1.4.0/v1.4.3 framing). 1 production-deployment branch selected (Branch C). Open Questions table (RESEARCH_FINDINGS.md) reflects 5 WC-10 rows resolved + 2 new rows (WC-11 + BR-3) added.

**Test count**: 1146 → **1171 unit tests** passing (+25 net across the multi-day arc). mypy floor 0; ruff floor 0; both preserved.

### Added (2026-05-08 — WC-10 v1 ALT-A confirmed + Constitution v1.4.6 → v1.5.0 + mypy 126 → 0)

**WC-10 v1 pilot ships the first non-filter / non-prompt-tweak intervention to produce a decisive falsification verdict in the corpus** (40 propagates / 10 dates × 2 tickers × 2 modes / $16 / `experiments/2026-05-08-001-wc-10-pilot/`). SC-007 ALT-A confirmed at distribution level: continuous-scalar mode emitted `|rating| > 0.2` on 18/20 (90%) vs 5-tier mode's 5/20 (25%) — **3.6× commit ratio**. 75% of paired decisions differ. NVDA case study: continuous-scalar emitted bullish reads on every date (+0.38 to +0.72) while 5-tier emitted Hold on 8 of 10 dates with realized 21d α from +2.83% to +8.53% — the schema was suppressing 8 commits the framework would have made under continuous output.

**Constitution VII v1.4.3 → v1.5.0** (MINOR amendment) — added "Schema-induced abstention is NOT calibrated abstention" sub-section to Principle VII (Calibrated Abstention is a Valid Output). VII still applies to commits whose evidence is GENUINELY BALANCED (the original framing); v1.5.0 carves out cases where (a) evidence is one-directional but moderate-magnitude, (b) schema lacks a partial-confidence tier, (c) empirical evidence shows the framework would commit if the schema permitted it. Where these conditions hold, the fix is the scale, not the inference. New HYPOTHESIS.md operational test: structural changes that "reduce Hold rate" must justify which sub-population they target — genuine ambiguity (NOT VII-eligible) or schema-induced collapse (VII-eligible per WC-10 precedent).

**Mode-collapse reframe** — RESEARCH_FINDINGS.md updated: mode collapse to Hold is now characterized as TWO-MECHANISM (genuine ambiguity + schema artifact), not unitary calibrated abstention. Prior "Hold-regime starves filters" pattern (memory `reference_pm_hold_regime_starves_filters.md`) is now decomposable into the two sub-populations.

**Spec 011 (`specs/011-behavioral-additive-procedure/`)** — methodology spec codifying the operational procedure for invoking the Constitution v1.4.6 behavioral-additive escape clause. 6 FRs (required retrospective fields / sample-size minimum / regime-shift trigger specificity / mechanism-class novelty check / canonical re-runnable harness / 6-PR spec-kit bundle pattern). Future filter specs invoking v1.4.6 will cite Spec 011 in their retrospectives.

**Spec 009 (`specs/009-wc-10-production-deployment/`)** — conditional draft scaffolds 4 verdict-conditional branches (A: STRONG → operator-opt-in via `daily_signals.py`; B: MODERATE → research-only; C: NULL → bin-then-output ergonomic-only; D: NULL+ALT-A → no deployment). Branch selection deterministic when v2 + v3 verdicts land.

**WC-10 v2 + v3 in flight** (kicked off 2026-05-08 evening):
- **v2 (n=100 ticker expansion)** — 8 tickers × 10 weekly-Friday Q1 2026 dates × WC-10 only = 80 propagates × $0.40 = $32. Resolves SC-005(b) signed-rating × 21d-α correlation at n=100. `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/`.
- **v3 (Q4 2025 NVDA bear-regime)** — 8 dates × 1 ticker × 2 modes = 16 propagates × $0.40 = $6.40. Tests v1's WC-10 caveat directly. `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/`.

**WC-10 production-deployment monitoring**: `scripts/wc_10_underperformance_monitor.py` (sister to `scripts/memory_log_integrity_check.py`) — flag cohorts where WC-10 mode produces worse realized α than 5-tier baseline. 3 alert criteria (single-pair / streak / cohort cumulative). Cron-friendly exit code. v1 pilot smoke test: cohort cumulative Δα +22.42pp; 2 per-pair alerts (AAPL UW commits during +3-6% rally) — empirically validates v1.5.0 asymmetric-calibration caveat.

**Pre-scaffolding pattern codified** (~5 PRs collectively cut v3 landing series from ~120 min to ~43 min): pre-scaffolded ANALYSIS templates with `<TBD>` placeholders + 4 verdict-conditional Constitution v1.5.1 patches + 3-PR landing series workflow template. New project-level reusable templates: `.specify/templates/spec-template-conditional.md` + `scripts/new_experiment.py --with-analysis-template` flag.

**Mypy 126 → 0** via 12 cleanup PRs (#117-#129) — implicit-Optional widening, helper signature alignment, dict-invariance annotations on the LLM-client `llm_kwargs` (the 4-line PR #128 cleared 85 errors that CLAUDE.md previously characterized as "complex / deferred / needs upstream stubs"; correction: actually trivial dict invariance), TypedDict receiver widening for `TradingAgentsConfig`, and `types-requests` stub addition. Memory `reference_llm_client_kwargs_dict_invariance.md` codifies the "verify deferred classifications by trying the simple fix first" methodology lesson. CLAUDE.md baseline updated. 1146 → 1153 unit tests (+7 from PR #150 ANALYSIS template tests).

### Added (2026-05-07 — Spec X-1 deployed — C-4 institutional rotation filter (FIRST quantitative-flow bear-side filter))

**Spec X-1 (`specs/091-c4-institutional-rotation/`)** ships the framework's FIRST quantitative-flow bear-side filter via 4 PRs (#88 spec → #89 plan + design → #90 tasks → #91 PR-A MVP implementation → #92 PR-B remaining tests → this PR-C polish).

**Mechanism**: At PM stage, AFTER all existing filters (A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007), apply the C-4 check. Fetch top 10 institutional holders for the ticker via `yfinance.Ticker(t).institutional_holders` (LRU-cached maxsize=128 per process). Sum the `pctChange` column across top 10 holders → `net_rotation`. If `net_rotation < -outflow_threshold` AND `pre_rating ∈ {Underweight, Sell}` → suppress to Hold. Bear-side ONLY at v1 (bull-side disabled by default — n=1 evidence too thin).

**Module**: new `tradingagents/agents/utils/institutional_rotation_filter.py` (~190 LOC). Exports `_fetch_institutional_rotation` (LRU-cached fetcher), `should_suppress_bear` (pure function with strict less-than per FR-005 / SC-002), `evaluate_institutional_rotation` (main filter). Internal helpers `_parse_pre_rating` + `_downgrade_to_hold` mirror Spec 007 patterns. Mirrors `scripts/forward_catalyst_class4_retrospective.py` for fetch semantics (single source of truth).

**State annotation** extends `state["forward_catalyst"]["institutional_rotation"]` with 8 fields (`net_rotation_pct`, `outflow_threshold`, `bear_mode`, `bull_mode`, `would_fire_bear`, `fired_bear`, `pre_rating`, `post_rating`). When both modes are off, the sub-dict is NOT added (FR-011 backward-compat with Spec 007 baseline state log shape). Persisted via existing `_log_state` whitelist (no AgentState schema changes — `forward_catalyst` already declared).

**4 new TradingAgentsConfig keys**: `institutional_rotation_bear_mode` (Literal[off/shadow/active], default "shadow"), `institutional_rotation_bull_mode` (Literal[off/shadow/active], default "off"), `institutional_rotation_outflow_threshold` (float, default 0.05), `institutional_rotation_inflow_threshold` (float, default 0.05; reserved for future bull-side activation).

**Defaults rationale**: bear-side default-shadow per Constitution VIII v1.4.0 small-sample-caution sub-clause (n=12 cohort). Bull-side default-off (n=1 evidence too thin). Filter ordering LAST in chain per sample-size discipline (smallest evidence base goes last).

**Empirical evidence** (PR #75 + #77, both pre-cleared the Constitution VIII gates BEFORE spec invocation per VIII v1.4.1 retrospective-FIRST pattern):

| Gate | Result |
|---|---|
| Standalone (VIII v1.4.0) | PASS at n=12 — discrim +10.29pp / hit 75.0% / net Δα +5.41pp at T_outflow=0.05 |
| Additive (VIII v1.4.3) | PASS on 2 of 3 criteria — net Δα improvement +8.06pp / hit improvement +69.23pp / FP improvement +0.00pp (≥1 sufficient) |
| Mechanism class | LITERALLY different from Spec 007 bear (LLM-extracted vs quantitative 13F flow); C-4 catches 11 bearish commits Spec 007 entirely misses (mean α +6.16% on `c4_only` cohort, 81.8% hit) |

**Test coverage**: 18 tests total (15 unit + 3 integration). All PASS via uv venv (matches pre-commit env). 0 regressions in 1134-test unit suite.

**Cost gate**: Zero LLM cost (Constitution III T0 free-tier). yfinance fetch ~50-200ms latency on cache miss.

**Deferred follow-up gates**:
- SC-009 (~2026-05-15): re-run `scripts/forward_catalyst_class4_retrospective.py` + `scripts/forward_catalyst_class4_vs_spec007_overlap.py` with Q1 2026 13F panel; ablate to "off" if either gate drops below v1.4.0 / v1.4.3 thresholds.
- SC-010 (live-mode flip eligibility): n≥30 propagates A/B ablation (active vs shadow on same propagates) before flipping bear_mode default to "active".

**No new constitution amendment needed** — Spec X-1 is governed by existing Principle VIII v1.4.0 + v1.4.3 gates; cleared before spec invocation.

**Sibling docs**: full spec/plan/research/data-model/contracts/quickstart bundle at `specs/091-c4-institutional-rotation/` + 4 retrospective markdowns (`claudedocs/forward-catalyst-class4-{retrospective,vs-spec007-overlap}-2026-05-07.md` + `claudedocs/spec-x-1-c4-institutional-rotation-feature-description-2026-05-07.md`).

### Added (2026-05-07 — Constitution v1.4.6 ratified — Behavioral-additive 4th interpretation; PM-as-multi-mechanism-validator reframe)

**Constitution v1.4.5 → v1.4.6** (PATCH; content originally drafted as v1.4.4 but ratified as v1.4.6 to preserve monotone numbering after v1.4.5 was ratified first per reasoning_decision rank ordering): appends a **"Behavioral-additive sub-case (4th interpretation)"** sub-section to Principle VIII v1.4.3 Additive-to-existing-filter gate.

**Mechanism**: codifies the case where a new filter F's operational fire-decisions appear redundant with existing portfolio fires BUT both correlate with the same PM commit decisions. The PM has internalized F's contrarian logic via Constitution VII's Calibrated Abstention training, so F is **REDUNDANT-ON-EXECUTION but COMPLEMENTARY-ON-DESIGN**. Reframes PM operational role from analyst+debate aggregator to **multi-mechanism-validator**: PM's Calibrated Abstention operationally validates consensus across the analyst+debate ensemble — when multiple mechanism classes flag the same contrarian condition, PM commits Hold or stricter even though no filter operationally fires.

**Three pre-existing additive sub-cases** (per the existing v1.4.3 gate): cohort-additive (different cohort losers), mechanism-additive (different mechanism class), underlying-additive (hybrid filter modulating an underlying). The new 4th — behavioral-additive — fills the gap where standard fire-overlap analysis would SKIP a mechanistically-valuable filter as redundant when it's actually capturing a regime-drift robustness margin.

**Operational test** (when applying the v1.4.3 additive gate):

1. Run the standard intersection / new-only / existing-only / neither matrix on **actual** fire decisions (existing v1.4.3 procedure).
2. **ALSO** run a counterfactual matrix on **would-fire-if-PM-committed** decisions — parse state-log score fields without gating on actual pre_rating. Reusable harness: `scripts/behavioral_additive_sweep.py`.
3. Decision tree: Operational PASS → SHIP per v1.4.3. Operational FAIL but Mechanistic PASS → behavioral-additive case, SHIP with documented expectation that production fires will be sparse until PM regime shifts. Operational FAIL and Mechanistic FAIL → SKIP.

**Empirical basis** (cross-cohort behavioral-additive sweep, `claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md`, PR #41 + AMD-04-17 deep-dive PR #43):

| Mechanism class | Behavioral-additive cases | Per-instrumented-log rate |
|---|---|---|
| Spec 003 (prose-density) | 7 | 70% |
| Spec 007 bull (LLM-extracted) | 7 → 8 (post-AMD) | 47-50% |
| Spec 007 bear (LLM-extracted) | 3 | 20% |
| Spec 008 (calendar-boosted) | 6 | 40% |

**ALL 4 mechanism classes show evidence**, distributed across 7 tickers (AAPL, AMD, COP, INTC, MSFT, NVDA, WFC). MSFT shows the pattern in all 4 classes; AAPL+INTC in 3 each. AMD-04-17 (`claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md`) is the textbook case where PM verbalizes the bull-priced-in mechanism in plain English ("42% rally" + "99th-percentile technical exhaustion" + "earnings repricing risk" with bull_score=0.85 — highest in SC-009).

**Three sub-patterns identified**: (1) PM Hold + bull-priced-in scores high — original framing. (2) PM **stricter-than-Hold** (Underweight) + bull-priced-in scores high — extends original. (3) PM Hold + bear-priced-in scores high — BEAR-SIDE behavioral-additive (empirical kernel for Hybrid D candidate).

**Risk acknowledged + mitigation**: behavioral-additive is a permissive case. Risk: shipping multiple specs whose fires never materialize in production. Mitigation: behavioral-additive specs MUST also document a regime-shift trigger (what PM behavior would cause F's fires to start materializing) in the retrospective. If no plausible regime-shift exists, SKIP.

**Trigger criteria + acceptable exception**: applies when filter F PASSES v1.4.3 standalone gate but FAILS v1.4.3 actual-fire overlap, F's mechanism class is different from at least one existing default-active filter, AND counterfactual sweep shows F's would-fire correlates with PM's commits at ≥60% rate. Same-mechanism-class filters fall back to standard v1.4.3 (no behavioral-additive escape). Shakeout filters (operator-opt-in, default-off, marked `shakeout_filter: true`) skip ALL gates as before.

**Sibling docs**: `scripts/behavioral_additive_sweep.py` (re-runnable harness), `claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md` (textbook mechanistic-validation case), `memory/reference_behavioral_additive_4th_interpretation.md` (operator memory; PM-as-multi-mechanism-validator framing).

### Added (2026-05-07 — Constitution v1.4.5 ratified — Memory-log data-vs-prose discipline gate)

**Constitution v1.4.3 → v1.4.5** (PATCH; v1.4.4 remains drafted but not yet ratified — explicit gap-skip documented in the version footer): adds **Quality Gate #6 — Memory-log data-vs-prose discipline** to the Quality Gates section. Operators MUST cross-check memory log entries' reflection prose against the entry's header data (raw_return, alpha, holding_days). Reflection prose can be hallucinated when the data contradicts the prior call's expected direction.

**Empirical basis**: PR #54 single-case AMD-04-17 (reflection prose "captured the inflection correctly" while header recorded +24.9% raw return showing the Underweight call demonstrably failed at the 21d horizon) + PR #55 systematic sweep finding the pattern at **20% incidence rate** (3 of 15 entries: COP @ 2026-04-17, INTC @ 2026-04-17, AMD @ 2026-04-17 — ALL Underweight calls that went UP, ALL with explicit self-validating phrases despite the data refuting them). PM-04-24 demonstrably trusted AMD-04-17's hallucinated reflection ("the prior AMD lesson itself validates the trim discipline") over the +24.9% raw return data — cascade-failure-mode documented.

**Mechanism explanation** (in the gate text): when `_resolve_pending_entries` writes a reflection, the LLM faces "self-justification pressure" — easier to write narrative coherent with the prior thesis than to admit the call was wrong. Framework has NO data-vs-prose consistency check on the write path.

**Operational rule** (4 steps): read entry header FIRST → check sign consistency → if sign-mismatched, reflection is SUSPECT (do NOT cite without verification) → in claudedocs/analysis, distinguish "entry header says X" from "reflection narrates Y."

**Symmetry with Constitution VII** (filters parse rating, not prose): VII applies to filter design; Quality Gate #6 extends the discipline to operator memory-log reading ("operators parse data, not prose"). Hold-rating entries are exempt (no directional expectation).

**Tooling**: `scripts/memory_log_integrity_check.py` (PR #55, 12 unit tests, CI-friendly exit code 0=clean, 1=suspects). Run periodically or before any analysis citing memory log evidence.

**Trigger criteria** (when this gate applies): operator analysis citing prior memory entries, spec retrospectives extracting historical lessons. NOT during PM propagates themselves — framework lacks the consistency check; this gate exists to protect operators against PM-side hallucinated reflections.

Version footer notes that v1.4.4 (behavioral-additive 4th interpretation appended to Principle VIII v1.4.3 additive-to-existing-filter gate; draft at `claudedocs/constitution-v1.4.4-draft-2026-05-07.md`) remains in draft state. The version skip from v1.4.3 → v1.4.5 is intentional per the user's reasoning_decision rank ordering (v1.4.5 ranked #1 ahead of v1.4.4 due to stronger empirical evidence base — n=3 hallucination threshold met).

### Added (2026-05-07 late session — bear-side survey CONCLUDES; C-4 ADDITIVE PASS; tooling + memory polish)

8 PRs merged extending the prior 2026-05-07 entry (PRs #71-#78). Total day count: 40+ PRs. Cost: $0 LLM (all retrospective + tooling work).

**Bear-side mechanism class survey CONCLUDES (PRs #74, #75, #76, #77, #78)**: 6/6 mechanism classes evaluated; **C-4 (institutional ownership delta) is the SOLE spec-eligible bear-side mechanism class**.

| Class | Standalone Gate | Additive Gate | Spec-eligible? | Source |
|---|---|---|---|---|
| C-1 (insider transactions) | SKIP | n/a | NO | PR #23 |
| C-2 (short-interest delta) | SKIP (mechanism INVERTED) | n/a | NO | PR #76 |
| C-3 (analyst PT delta) | NOT FEASIBLE | n/a | NO | PR #40 |
| **C-4 (institutional ownership)** | **PASS (n=12, +5.41pp)** | **PASS (+8.06pp / +69pp; PR #77)** | **YES (shadow-mode-first)** | PR #75 + PR #77 |
| C-5 EPS-surprise | PASS standalone, FAIL additive | n/a | NO | 2026-05-06 |
| C-5 PRICE-REACTION | SKIP (mechanism INVERTED) | n/a | NO | PR #74 |
| C-6 (bear-news density) | SKIP (structural redundant) | n/a | NO | PR #67 |

C-4 ADDITIVE PASS finding (PR #77): C-4 catches 11 bearish commits Spec 007 ENTIRELY MISSES (`c4_only` cohort: n=11, mean α +6.16%, hit 81.8%). LITERALLY different signal sources (LLM semantic vs quantitative 13F flow). Cross-mechanism-class additive case — exactly what v1.4.3 gate is designed to identify.

Two C-classes show INVERTED bear-side mechanism (C-5 price-reaction + C-2 short-covering): both originally hypothesized as mean-reversion; both empirically show momentum/continuation. Bear cohort on SC-009-era data has strong continuation bias. Three SKIP-types now codified (empirical, data-availability, structural).

**Spec 003 historical-recompute + cache-collision fix (PRs #71, #72)**: `scripts/spec_003_historical_recompute.py` walks 254 state logs and backfills bull_keyword_count cache via `record_value`. Cache state went from sparse to 435 rows / 54 tickers. **9 tickers now clear FR-004 N≥20 per-ticker floor** (NVDA, AAPL, INTC, XLE, MSFT, GOOGL, JPM, XLF, XLK). JPM + GOOGL crossed from `baseline=sector` to `baseline=per_ticker`. Sub-pattern 2 cold-start tickers (AMZN, COP, CVX, LLY, HON) still cold; no source data available for backfill. PR #72 found the cache PK (signal_id, ticker, date, fetcher_version) silently overwrites when --feature differs; added cache-collision guard + new `--write-to` flag for non-default features. Bear-side cache populated under separate signal_id `market_report__bear_keyword_count` (254 rows; preserves bull cache).

**Path C analyst PT snapshot wiring (PR #73)**: new `tradingagents/agents/utils/analyst_pt_snapshot.py` (~80 LOC) captures `yfinance.analyst_price_targets` + `recommendations` distribution at propagate time when `analyst_pt_snapshot_enabled=True` (default OFF). Adds `state["forward_catalyst"]["analyst_pt_snapshot"]` field. Future C-3-class retrospectives can backfill historical contrarian signals from accumulated snapshots in state logs (yfinance has no historical PT panels per PR #40 — snapshots forward are the only path). LRU-cached, graceful fallback, ETFs return None.

**PR #22 design doc updated (PR #78)**: bear-side-mechanism-exploration design doc gets a "SURVEY COMPLETE" section at the top with the full empirical scorecard. Original design exploration preserved below for traceability of how candidate classes were ranked + selected.

**Spec X-1 (C-4 institutional rotation filter) is now spec-invocable** per Constitution VIII v1.4.0 + v1.4.3 gates. Recommend SHADOW-MODE-FIRST launch per the v1.4.0 sample-size caution pattern (n=12 is small; Q1 2026 13F refresh ~2026-05-15 will refresh the data; cohort expansion would tighten variance bands).

**Cross-session memories**: 19 → 21 (+2 new): `reference_signals_cache_pk_collision.md` (PR #72 footgun), `feedback_precommit_ruff_silent_rejection.md` (PR #77 chain-output footgun).

**New scripts**: `scripts/spec_003_historical_recompute.py` (PR #71) + `scripts/forward_catalyst_class5_reaction_retrospective.py` (PR #74) + `scripts/forward_catalyst_class4_retrospective.py` (PR #75) + `scripts/forward_catalyst_class2_retrospective.py` (PR #76) + `scripts/forward_catalyst_class4_vs_spec007_overlap.py` (PR #77).

**Test count**: 1162 → 1170 → 1179 (+17 net from PRs #71, #72, #73). Full unit suite passes.

### Added (2026-05-07 — SC-009 backtest, bear-side mechanism survey, v1.4.4+v1.4.5 drafts)

A multi-session day combining a long-running SC-009 backtest with extensive parallel-safe documentation, diagnostic, and tooling work. 32 PRs merged. ~$18 LLM (background backtest); foreground all $0. See `claudedocs/research-burst-2026-05-07.md` for the canonical narrative.

**SC-009 ablation experiment (PRs #17, #57, #58, #61)**: Spec 008 Hybrid C live A/B ablation completed 36/36 rows. `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/`. Final acceptance gates (PRELIMINARY — canonical 21d windows close ~2026-05-22+):
- Gate 1 (alt suppressed-α in [-10%, +2%]): PASS at +0.43%
- Gate 2 (n_fired_boost_on ≥ 8): PASS at 13 (61% margin above threshold)
- Gate 3 (boost engaged ≥ 1): PASS at 18
- Verdict line auto-emits "PASS — recommend Spec 008 v2 default-on flip" but refined per PR #56 to **PRELIMINARY PASS-by-non-counterexample**: 0 decisions changed by boost across all 36 rows; recommend SHADOW-MODE-FIRST per Constitution VIII v1.4.0, NOT direct default-on flip.

**Bear-side mechanism class survey COMPLETE — 6 of 6 evaluated (PRs #23, #40, #64, #65, #66, #67)**:

| Class | Verdict | Mechanism | Source |
|---|---|---|---|
| C-1 (insider transactions) | SKIP (empirical) | Anti-predictive on cohort | PR #23 |
| C-2 (short-interest delta) | PARTIAL <30d | yfinance returns current + prior month only | PR #65 |
| C-3 (analyst PT delta) | NOT FEASIBLE | yfinance has no historical PT panels | PR #40 |
| C-4 (institutional ownership) | PARTIAL within 13F window | Quarterly 13F + 45d lag → time-bounded until ~2026-05-15 | PR #66 |
| C-5 (earnings price reaction) | FEASIBLE | 4-25 quarters of historical data accessible | PR #64 |
| C-6 (bear-news density) | SKIP (structural) | Strict subset of Spec 003's bear_keyword_count | PR #67 |

Three SKIP-type taxonomy codified: empirical (gate FAIL), data-availability (no historical), structural (redundant with existing). Three retrospectives drafting-eligible (C-2, C-4, C-5).

**Constitution amendment drafts (PRs #44, #61)**: Two amendments drafted (separate `claudedocs/` files; constitution.md NOT yet edited per defensive two-stage pattern):

- **v1.4.4 — Behavioral-additive sub-case (4th interpretation)**: extends v1.4.3 additive-to-existing-filter gate with "PM-as-multi-mechanism-validator" framing. When a new filter F's operational fires appear redundant with existing portfolio fires BUT both correlate with PM commit decisions (PM has internalized F's contrarian logic via Constitution VII), F is REDUNDANT-ON-EXECUTION but COMPLEMENTARY-ON-DESIGN. Empirical basis: cross-cohort sweep finding 23 → 37 cases across all 4 mechanism classes in 10 tickers (PRs #41, #45, #53). Counter-evidence watch (PR #49) found 0 refuting rows across 247 logs.

- **v1.4.5 — Quality Gate #6 Memory-log data-vs-prose discipline**: requires operators to cross-check memory log entry reflection prose against entry header data. Empirical basis: PR #54 single-case (AMD-04-17 reflection claims "captured the inflection correctly" while header records +24.9% raw return showing trim FAILED) + PR #55 sweep finding the pattern is SYSTEMATIC at 20% incidence rate. Symmetry with Constitution VII ("filters parse rating, not prose") extended to memory-log reading.

Both amendments ratification-eligible; ratification not yet committed.

**Tooling additions (PRs #38, #49, #55, #69)**:
- `scripts/analyze_sc009_ab.py`: extracted `evaluate_gate_1` helper with 5-path test coverage (PR #38). Added PRELIMINARY status guard preventing analyzer from overwriting hand-edits (PR #52). Added Spec 003 baseline-coverage diagnostic surfacing cold-start gap (PR #69).
- `scripts/v1_4_4_counter_evidence_watch.py` + 12 unit tests (PR #49): scans state logs for refuting rows. Exit 0 clean / 1 BLOCKED. CI-friendly.
- `scripts/memory_log_integrity_check.py` + 12 unit tests (PR #55): walks any memory log file flagging rating-direction-vs-realized-return-sign mismatches. Found 3 of 15 entries (20%) hallucinated on SC-009 backtest_memory.md.
- `scripts/behavioral_additive_sweep.py` (PR #41, refreshed in PR #45 + PR #53 + enhanced in PR #47): walks all state logs counting behavioral-additive cases per mechanism class.
- `scripts/probe_*` (PRs #40, #64, #65, #66): yfinance probe family for bear-side mechanism class feasibility. 30min probes that determine whether 3h retrospectives are worth running.

**Test count**: 1123 → **1162 PASS** (+39 net from PRs #38, #49, #55, #69).

**Methodology findings**:
- L-8 codification THRESHOLD MET (4-of-4 mechanism classes show behavioral-additive evidence)
- Reflection-prose hallucination DISCOVERED systematic at 20% rate (cascade failure mode documented)
- PASS-by-non-counterexample distinction (PR #56): SC-009 doesn't disprove spec 008 boost — the cohort's bull_score distribution doesn't exercise the borderline regime
- Spec 003 cold-start coverage gap (PR #68): 22 of 36 rows (61%) had `gate_baseline=none` → Spec 003 couldn't engage on majority of cohort
- Spec 007 calendar-INDEPENDENCE empirically validated (PRs #56, #62): 6 Financials bull-pre fires (BAC×2 + GS×2 + JPM×2) all firing at 81-88 days from earnings on bull_score alone

**Cross-session memories preserved**: 14 → **19** (+5 new + 1 updated).

### Added (2026-05-06 late-evening — Constitution v1.4.2 + meta-retrospective)

**Constitution v1.4.2** (`.specify/memory/constitution.md`): added "Magnitude fungibility for hybrid filters" sub-section to Principle VIII (forward-catalyst-class gate). Empirical basis: Spec 008 Hybrid C bull retrofit + Spec 009-candidate bear-inverted retrofit BOTH produced identical fire patterns across magnitude={0.5, 1.0, 2.0} within fixed window. Operational test: sweep window first; sweep magnitude only if smallest doesn't cross threshold; pick smallest as production default if fungible. Saves 60-66% of retrospective sweep time. v1.4.1 → v1.4.2 (PATCH per clarification rule). Fourth constitution amendment of the day.

**Spec 009 candidate (bear-inverted Hybrid C) — SKIP** (`claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.md`): tested inverted boost direction for bear cohort (`effective_bear = max(0, base × (1 - magnitude × boost))` — boost DECREASES bear score near earnings on hypothesis that earnings often rally → priced-in bear cases fade). Result: +0.00pp Δα at every (window × magnitude) config across {7,14,21}d × {0.5,1.0,2.0}. n_fired identical to baseline at all 9 configs — the inverted boost has no measurable effect because the bear cohort's days-to-earnings distribution doesn't intersect with the boost window enough to flip any fire decisions. Spec 008's bull-only configuration remains the recommended Hybrid C stance.

**Meta-retrospective** (`claudedocs/research-burst-2026-05-06.md`): canonical entry point documenting today's 14-work-unit research-burst day. 9 ship-quality units shipped: 2 specs implemented + 6 retrospectives (2 PASS + 4 SKIP) + 1 candidate SKIP + 4 constitution amendments + 3 cross-session memories. Total cost ~$5.05 LLM, ~17h wall-clock. ROI on retrospective methodology: ~10-13× wall-clock leverage on the spec invocations that DID launch. Documents 4 methodology lessons (L-1..L-4) cross-referenced to the constitution amendments that codified them.

### Added (2026-05-06 evening — Spec 008 Hybrid C calendar boost + v0.8.0 tag)

**Spec 008 Hybrid C calendar boost** (`specs/007-calendar-boost-filter/`, branch `007-calendar-boost-filter` merged via PR #6, tagged `v0.8.0-spec-008`): FIRST hybrid filter combining the validated Spec 007 Class 3 LLM-extracted scores (`bull_case_priced_in`) with Class 6 calendar features (days-to-next-earnings via yfinance.earnings_dates) — calendar-aware enhancement of the bull-side branch of the spec 007 forward-catalyst-aware contrarian gate. New helper module `tradingagents/agents/utils/calendar_boost.py` (~80 LOC, 4 functions + LRU cache).

Mechanism: `effective_bull_score = min(1.0, bull_case_priced_in × (1 + magnitude × boost))` where `boost = max(0, 1 - days_to_next_earnings / window)`. Substituted for `bull_case_priced_in` in the Spec 007 fire-decision comparison when enabled. Bull-only (FR-004); bear-side unchanged.

Defaults: **default OFF** (FR-007 — operator opts in). When enabled: window=14d + magnitude=0.5x per the empirically-grounded retrospective best config. Three new TradingAgentsConfig keys: `hybrid_c_calendar_boost_enabled`, `hybrid_c_calendar_boost_window_days`, `hybrid_c_calendar_boost_magnitude`.

Empirical motivation: Hybrid C retrofit + production-config retrospectives (`claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`) DECISIVELY PASSED Constitution VIII v1.4.0 forward-catalyst-class gate at best config window=14d / magnitude=0.5x: bull-side net Δα +5.58pp at boosted threshold (+3.35pp Δα improvement vs Class 3 alone, +3.7pp cohort hit rate improvement to 92.6%, +11.30pp discrimination, n=37 fires).

Cost: **$0 LLM** (Constitution III T0). Pure post-processing of Spec 007's already-paid LLM call output + free yfinance fetch (LRU-cached per ticker per process).

Filter chain unchanged (FR-014); Hybrid C is structurally INSIDE Spec 007's score computation, not parallel. AgentState TypedDict unchanged (state["forward_catalyst"] already declared as Annotated[dict, ...] per spec 007). State annotation gains 4 new keys (`days_to_earnings`, `calendar_boost`, `effective_bull_score`, `effective_bear_score`) ONLY when boost is enabled — backward-compat preserved per FR-011 + SC-005.

Tests: 27 unit tests (boost formula edge cases + monotonicity + LRU cache + yfinance failure paths) + 7 integration tests (default-off backward-compat, enabled-gains-4-keys, borderline-fire-via-boost, far-earnings-no-fire, yfinance-failure-fallthrough, ETF empty-calendar) = 34 net-new tests. Suite at 1121/1121 PASS with -p no:randomly. Live smoke validated end-to-end at boost > 0 (days_to_earnings=7, calendar_boost=0.5, effective=1.0 clamped per I-4) at $0.05 cost.

SC-008 retrospective regression check: PASS — bull-side +3.35pp net Δα at window=14d magnitude=0.5x reproduces exactly (within ±0.5pp tolerance).

### Added (2026-05-06 evening — Constitution v1.4.1: spec ships its retrospective + verdict)

**Constitution v1.4.1** (`.specify/memory/constitution.md`): appended a "Spec ships its retrospective + verdict" sub-section to Principle VI (Spec Before Structural Change). Codifies the pattern that today's 22-work-unit research-burst day demonstrated 5 times: spec invocation requires an accompanying retrospective markdown in `claudedocs/` documenting:
1. The empirical retrospective that motivated the spec (or PASSED Constitution VIII gate)
2. The verdict block — explicit pass/fail per gate criteria with magnitudes
3. The decision tree — what happens if defaults are flipped, ablated, or revisited

Empirical basis (5 retrospectives shipped today):
- `claudedocs/sector-momentum-retrospective-2026-05-06.md` (spec 004, default-off)
- `claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md` (spec 006, default-off)
- `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md` (spec 005 candidate, SKIP)
- `claudedocs/forward-catalyst-class3-retrospective-2026-05-06.md` (Class 3 Haiku, BORDERLINE)
- `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` (Class 3 Opus, DECISIVE PASS → spec 007)

Cost asymmetry (retrospective $0-2 / 1h vs spec+impl ~6-8h) makes "retrospective FIRST, spec SECOND" the dominant strategy for any new filter mechanism class. The pattern is load-bearing for the project's research economy.

v1.4.0 → v1.4.1 (PATCH per clarification rule). Third constitution amendment of the day after v1.3.0 (Principle VIII added) + v1.4.0 (Principle VIII extended with forward-catalyst-class gate).

### Added (2026-05-06 evening — Spec 007 + Constitution v1.4.0)

**Spec 007 forward-catalyst-aware contrarian gate** (`specs/006-forward-catalyst-gate/`, branch `006-forward-catalyst-gate` merged via TBD): FIRST forward-catalyst-aware filter in the framework. New module `tradingagents/agents/utils/forward_catalyst_filter.py` invokes an LLM (Opus default; configurable to Haiku) per propagate to score how widely the bull/bear case is already absorbed by the market via the existing analyst reports + bull/bear debate.

Empirical motivation: Class 3 Opus retrospective (2026-05-06) DECISIVELY PASSED the bull-side gate (discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp on n=33 fires at T=0.60). Bear-side passed criteria 1+2 with shadow-mode-first condition (discrim +23.10pp / hit rate 72.2% / net Δα +0.30pp just below +0.5pp gate).

Defaults per the empirical evidence:
- `forward_catalyst_bull_mode = "active"`, `bull_threshold = 0.60`
- `forward_catalyst_bear_mode = "shadow"`, `bear_threshold = 0.50`
- `forward_catalyst_model = "claude-opus-4-7"`
- Operator can disable via setting BOTH modes to `"off"` (zero LLM cost)

Per-propagate Opus cost ~$0.025 (~$0.25/day for typical 10-ticker workflow); Haiku alternative is ~10× cheaper with documented score-distribution degradation.

Filter ordering (FR-012 amended): A3 → spec 006 → spec 003/003.5 → spec 004 → **spec 007 LAST** (consumes the same analyst reports as inputs to the prior filters).

State annotation: new `state["forward_catalyst"]` field with 16 fields (model / bull+bear scores / rationale / both thresholds / both modes / would_fire+fired per side / pre+post rating / skipped / error). Persisted via `_log_state` whitelist + AgentState TypedDict extensions (precedent: spec 003 + spec 004 + spec 006).

Tests: 29 unit tests (mocked LLM via injection point) + 7 PM-integration tests (mocks the factory + the structured-output call) + 2 state-log persistence regression tests + 1 SC-008 integration test + 1 default-config regression test. Total +40 tests; suite at ~1024.

**Constitution v1.4.0** (`.specify/memory/constitution.md`): Principle VIII extended with a "Forward-catalyst-class validation gate" sub-section codifying the discrim ≥ +5pp (PRIMARY) + cohort hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first criteria for forward-catalyst-aware filters. Empirical basis: Class 3 Opus retrospective DECISIVE PASS unblocked spec 007. v1.3.0 → v1.4.0 (MINOR per amended-principle rule). Future forward-catalyst filters follow this gate; backward-price filters continue to follow the original v1.3.0 gate.

### Added (2026-05-06 research-burst day — 14 work units)

**Filter portfolio expanded 1 → 5; Constitution v1.3.0; pre-spec retrospective methodology validated 4× across mechanism classes.**

#### Specs landed

- **Spec 003.5 sector-baseline fallback** (`specs/003-sector-baseline-gate/`, PR #3 merged): when per-ticker `bull_keyword_count` history is below FR-004 N≥20 floor, gate aggregates across same-sector tickers from the yfinance cache. Default-on. Closes the cold-start universe gap structurally. Module: `tradingagents/signals/sector_baseline.py`. 10+15 unit tests.

- **Spec 004 sector-momentum filter** (`specs/004-sector-momentum-filter/`, PR #4 merged): suppresses Buy/OW when sector ETF is in mean-reversion zone (down >threshold% in prior 30d). New module `tradingagents/agents/utils/sector_momentum_filter.py` with 11-entry SECTOR_ETF_MAP (XLK/XLF/XLV/XLE/XLY/XLP/XLI/XLC/XLU/XLRE/XLB) covering both yfinance-canonical + GICS-canonical sector names. ~29 tests. Default-off after retrospective verdict (see below).

- **Spec 006 bear-sector-symmetry filter** (`specs/005-bear-sector-symmetry/`, branch merged via `4d0401d` --no-ff; user-facing name "Spec 006" — directory auto-numbered to `005-bear-sector-symmetry`): suppresses UW/Sell when ticker has outperformed its sector ETF by >threshold% in prior 30d (counter-trend bear suppression). New module `tradingagents/agents/utils/bear_sector_symmetry_filter.py`. Reuses `SECTOR_ETF_MAP` + `_etf_history` from spec 004 (FR-004; single source of truth); new `_ticker_history` LRU cache. 27 unit + 5 PM-integration + 2 state-log regression tests. Default-off after SC-008 FAIL (see below).

#### Retrospective verdicts (Constitution VIII basis)

- **Spec 004 retrospective** (`claudedocs/sector-momentum-retrospective-2026-05-06.md`): -0.45pp net Δα across 73 commits at -5% threshold (anti-predictive). SC-008 also FALSIFIED (`claudedocs/spec-004-sc008-validation-2026-05-06.md`): XLF was -4.54% (above -5% threshold), filter would suppress 0/5 of SC-003 Financials (not ≥3/5). **Default-off; ships as operator-opt-in.**

- **Spec 003 contrarian gate threshold sweep** (`claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md`): walks 228 propagate state logs, sweeps 75/80/85/90/95th percentile thresholds. 11 of 82 bullish commits eligible (above N≥20 floor + α available). At default 80%: net Δα = +0.65pp. **Verdict: KEEP default-on at 80%** — tightening doesn't help (gate never fires at 85+); loosening to 75% gives +1.36pp but more incorrect-suppression risk. Validates the 2026-05-06 morning default-on flip.

- **Spec 006 retrospective** (`claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md`): SC-008 FAILED at +5% (5 of 18 ticker_strong-bearish cohort fire; target was ≥8) AND -0.71pp net Δα anti-predictive across 36 commits. Mirrors spec 004's outcome. **Default-off; ships as operator-opt-in.**

- **Spec 005 candidate retrospective** (`scripts/ticker_sector_alpha_retrospective.py`, `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`): pre-spec validation of the per-ticker-vs-sector BULL filter hypothesis. Max +0.31pp net Δα across 79 commits, well below Constitution VIII +1pp gate. Cohort hit rate 48% at +3% but cohort-loser suppression washed by winner suppression at indistinguishable rel-strength values. **Verdict: SKIP spec entirely** — saved ~6-8h of empty-spec implementation.

- **Class 3 forward-catalyst retrospective (Haiku)** (`scripts/forward_catalyst_class3_retrospective.py`, `claudedocs/forward-catalyst-class3-retrospective-2026-05-06.md`): pre-spec validation of LLM-extracted "bull/bear case priced in" feature on 94 commits via Haiku at ~$0.19. **Verdict: BORDERLINE** — discrimination passes strongly (+10-37pp) but per-class means show only weak separation (cohort_a vs control_bull_winner +5pp; cohort_b vs control_bear_winner essentially zero) and Haiku score distribution too tight (mean 0.72, std 0.07 for bull). Recommend Opus rerun before any spec invocation.

#### Empirical findings

- **Sector-α attribution analyzer** (`scripts/sector_alpha_attribution.py`, `claudedocs/sector-alpha-attribution-2026-05-06.md`): walks 194 corpus commits, computes (raw_return, α-vs-SPY, α-vs-sector-ETF) at 21d, cross-tabs sign(α-vs-SPY) × sign(α-vs-sector) into 4 cells.

  - **5th failure mode discovered**: 27 of 79 bullish commits (34.2%) land in `ticker_weak` (α<0 vs both) with mean realized α-vs-SPY = -5.34%; **88.9% Tech-concentrated** (24/27 are Technology). 81.8% of LOSING bullish commits are 5th-failure-mode — vast majority of bullish-commit losses are stock-specific, NOT sector-rotation.

  - **Bearish anti-calibration shock**: 18 of 37 bearish commits (48.6%) landed in `ticker_strong` (α>0 vs both) with mean α-vs-SPY = **+28.02%** — largest single-metric anti-calibration finding in the corpus. A3 misses entirely; spec 006 was built to catch but failed empirically.

- **INTC +103% on Hold investigation** (`claudedocs/sc003-intc-hold-investigation-2026-05-06.md`): INTC went +103.14% in 21 trading days from 2026-04-03 (driven by April 23 earnings catalyst). Framework rated Hold; calibrated abstention per Constitution VII validated. Surfaced spec 003 default-on as a hypothetical counter-example: if PM had committed Buy/OW, the spec 003 contrarian gate would have suppressed back to Hold. Closes the SC-003 follow-up arc.

#### Forward-catalyst design exploration

- **Forward-catalyst mechanism design doc** (`claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md`): 6 candidate signal classes evaluated (news-density / options-IV / LLM-extracted "case priced in" feature / cross-asset / fundamentals delta / calendar features). Class 3 (LLM-extracted) recommended as starting point for cheapest highest-ceiling test. Proposes validation methodology that extends Principle VIII for forward-catalyst class (discrimination ≥ +5pp + cohort hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first). Decision tree for $0.10-5 + ~12-20h to definitively answer "is forward-catalyst tractable on this corpus?"

#### Constitution v1.3.0 — Principle VIII

- **Constitution v1.3.0** (`.specify/memory/constitution.md`):
  - **Principle VIII added** (Retrospective Before Spec for Backward-Looking Price Filters): any filter whose mechanism is exclusively backward-looking + price-derived MUST pass a corpus retrospective showing net Δα ≥ +1pp at the proposed default threshold + cohort hit rate ≥ 40% (when a target cohort is named) BEFORE the spec is written. Empirical basis: three same-day retrospective failures on 2026-05-06 — spec 004 sector-momentum (-0.45pp/n=73), spec 006 bear-sector-symmetry (-0.71pp/n=36), spec 005-candidate bull sector-relative (max +0.31pp/n=79). Backward-looking price filters cannot DISCRIMINATE cohort losers from similar-pattern winners; cohort-loser suppression is roughly cancelled by winner suppression. The cost asymmetry ($0/1h retrospective vs ~6-8h spec+impl+tests) makes pre-spec validation a Pareto improvement.
  - Operational test: build retrospective in the shape of `scripts/sector_momentum_retrospective.py` / `scripts/bear_sector_symmetry_retrospective.py` / `scripts/ticker_sector_alpha_retrospective.py`; sweep thresholds; cross-tab against any motivating cohort; commit retrospective markdown BEFORE invoking `/speckit.specify`.
  - Acceptable exception: explicit "shakeout" filters scoped to operator-opt-in (default-off, no SC-008-style empirical-validation gate, marked `shakeout_filter: true` in PARAMS.json).
  - Constitution-VIII follow-up: spec 004 + spec 006 spec.md preambles + quickstart.md "What's new" sections + SC-008 measurable-outcome entries cross-referenced against Principle VIII; future readers immediately see (a) default-off status, (b) empirical verdict with numbers, (c) Principle VIII pointer, (d) grandfathered status.

#### Filter portfolio status (post-day)

| Filter | Default | Empirical support |
|---|---|---|
| A3 momentum (bear/per-ticker absolute) | ON @-5% | +0.70pp/n=43 (in-sample, validated 2026-05-06 default flip) |
| Spec 003 contrarian gate (bull/per-ticker prose) | ON @80% | +0.65pp/n=11 (threshold sweep validates default flip) |
| Spec 003.5 sector-baseline fallback (bull/sector prose) | ON | Closes cold-start universe gap structurally |
| Spec 004 sector-momentum (bull/sector ETF absolute) | OFF | -0.45pp/n=73 anti-predictive (Constitution VIII grandfathered) |
| Spec 006 bear-sector-symmetry (bear/ticker-vs-sector) | OFF | -0.71pp/n=36 anti-predictive; SC-008 failed (Constitution VIII grandfathered) |

3 of 5 default-on; only A3 has > 30 supporting data points.

#### Documentation refreshes

- `RESEARCH_FINDINGS.md`: header updated; new sections added for "Filter portfolio status" + "5th failure mode discovered" + "Bearish anti-calibration shock" + "Constitution Principle VIII added".
- `ROADMAP.md`: header date 2026-05-05 → 2026-05-06; Current state bumped (test count 825 → 984, all 5 filters listed); Active branch section replaced with full numbered list of 14 work units in commit order; 3 new open data questions added (forward-catalyst-aware mechanism, multi-window SC-003 replication, Spec 005 percentile-variant at expanded corpus).
- `CLAUDE.md`: Empirical filters section gained spec 004 + spec 006 entries; principles count 7 → 8 in constitution reading guide.
- `CHANGELOG.md`: this entry.

#### Test count

- 825 → **984 tests passing** — added Spec 003.5 (10+15 tests) + Spec 004 (~29 tests) + Spec 006 (27 unit + 5 PM integration + 2 state-log regression tests). All filters' state-log persistence tests follow the `4c14d0f` precedent.

#### Cost summary

- **3 LLM-cost work units**: Class 3 Haiku retrospective (~$0.19) + Opus rerun pending (~$2 budgeted).
- **All other work units**: $0 LLM cost (offline retrospectives + design docs + spec writing).
- **Spec-writing cost AVOIDED via Principle VIII**: ~12-16h that would have gone into spec 005 + a default-on flip for spec 004 + spec 006 if the retrospective gate didn't exist.

### Added (research milestone — 14 experiments + n=50 OW signal)
- Constitution **v1.2.1** (`.specify/memory/constitution.md`):
  - **Principle III restructured** from single $30 ceiling to 4-tier ladder (T1 ≤$5 / T2 $5-30 / T3 $30-100 / T4 >$100). Higher tiers require progressively more deliberation in HYPOTHESIS.md.
  - **Principle VII added** (Calibrated Abstention is a Valid Output) after the 11-experiment chain converged on the architectural reframe.
  - **Principle VII Replicability scope appended** (v1.2.1) after the 005-vs-007 NVDA non-replication finding: claims must distinguish bucket-level (replicable) from date-level (single observation) evidence.
- Cost-tier scaffolding in `tradingagents/experiments/templates.py` + `scripts/new_experiment.py`:
  - `infer_tier(cost)` derives tier from a USD cost estimate (None → T2 default).
  - `--tier T1/T2/T3/T4` flag on `new_experiment.py`; T3/T4 inject required Cost-Justification scaffold (T4 adds multi-day deliberation, fallback, alternatives, kill criteria).
  - HYPOTHESIS template grew a `**Cost tier**` line. First end-to-end exercise: experiment 008.
- Signals expansion (`tradingagents/dataflows/y_finance.py`, `tradingagents/dataflows/macro.py`):
  - 10 yfinance fields (`get_recommendations`, `get_earnings_calendar`, `get_options_summary`, `get_short_interest`, `get_institutional_holders`, `get_corporate_actions`, plus existing 4 statements).
  - 5 P1 macro/regime additions: `get_vix`, `get_sector_etf_strength` (SPDR Select Sector ETFs).
  - 18 tools total wired into analyst layer (was 8).
  - +25 unit tests for fetchers and tool dispatchers.
- `tradingagents/agents/utils/momentum_filter.py` (A3 production augmentation):
  - Mean-reversion suppression filter for UW/Sell commits, gated by `config["uw_momentum_filter_threshold"]`. Default disabled.
  - Wired in `tradingagents/agents/managers/portfolio_manager.py`.
  - **Validated post-007** by `claudedocs/a3-filter-forensics-007.md`: filter correctly stays inert on regime-mismatch failures (INTC was UP +11-33% at 4 of 6 UW dates, never in suppression zone).
- New analysis scripts: `bear_side_per_ticker.py`, `diagnose_uw_quality.py`, `uw_suppression_filter.py`, `single_call_baseline.py`, `horizon_sweep.py`, `identify_hold_extremes.py` — all $0-cost, operate on existing CSVs.
- Two formal specs (unimplemented): `.specify/specs/001-bots-architecture/` (battlecode-style refactor), `.specify/specs/002-signal-lifecycle/` (discover/evaluate/promote/retire/learn pipeline).
- Spec-kit + ruff + mypy + pre-commit scaffolding installed (per `docs/SCAFFOLDING_PLAN.md`).
- `RESEARCH_FINDINGS.md` — project-level synthesis with 5 open questions + reasoning-tool-derived priors and empirical answers.
- `ROADMAP.md` — sequenced phases (B validate / C operationalize / D substrate-extend / E architectural variants) + cross-pollination table from sibling projects.
- 13 completed experiments + 1 in flight (008 cross-period validation). Latest committed: 007 Opus 30-pair mixed basket NVDA + AAPL + INTC at 21d horizon.

### Changed
- News vendor: removed `yfinance_news.py` and `brave_news.py` entirely. **Exa** is the only first-party news vendor; `alpha_vantage` retained as alternative for users with that subscription.
- `get_insider_transactions` moved from `news_data` → `fundamental_data` category (2026-05-03 evening) to fix routing-mismatch where `route_to_vendor` would try alpha_vantage before yfinance when the news_data vendor (exa) had no impl. Discovered when experiment 008 v1 errored on 22/22 runs.
- Test count: 92 → 466 → 501 (added regression guard `test_every_categorized_tool_has_impl_for_default_vendor` to catch the 008 class of bug at unit-test time).

### Fixed
- Routing-mismatch bug in `tradingagents/dataflows/interface.py` (commit `b00a203`): structural fix moves `get_insider_transactions` to the right category; supersedes the dict-order workaround from `505d2b1`.
- Two pre-existing E731 lambda-assignment lints in `tests/test_interface_routing.py` (cosmetic).

### Headline finding (post-007)
**At 5-day windows the framework is at the LLM single-call calibration ceiling. At 21-day windows, bullish commits (Buy + Overweight) produce +1.99% mean alpha across n=50 commits (65% hit rate)**. Single-experiment OW hit-rate climbs 56→67→75% across 5d/10d/21d on the latest 30-pair Opus run. Bearish commits are regime-asymmetric (not uniformly anti-calibrated): UW on bear-correct tickers directionally appropriate; UW on bull-regime tickers drives the aggregate anti-calibration. Bucket-level claims replicate; date-level claims do not (005 NVDA 10/10 OW vs 007 NVDA 6/10 OW on the same dates).

### Added (experiments scaffolding — spec 001)
- `tradingagents/experiments/` module — ID generation/validation (`ids.py`), config-override parsing (`overrides.py`), template renderers (`templates.py`).
- `scripts/new_experiment.py` — scaffold a new `experiments/<id>/` directory with templated `HYPOTHESIS.md`, `PARAMS.json`, `run.sh`, `run.ps1`. `--source-idea` and `--cost` pre-fills supported.
- `scripts/backtest.py` extensions — `--experiment-id <id>` flag stamps every CSV row; `--config-override KEY=VALUE` (repeatable) overlays runtime config with type coercion (int → float → bool → null → str); `experiment_id` column appended to CSV at end (backward-compatible); PARAMS.json auto-sync of override values (refuses to overwrite manual annotations).
- `scripts/findings_aggregate.py` — walk `experiments/*/ANALYSIS.md`, write `findings.md` at repo root with newest-first ordering and atomic write.
- `experiments/.gitkeep` placeholder; `findings.md` initialized with empty placeholder.
- 53 new tests across 6 files. All pass.
- Spec artifacts at `specs/001-experiments-scaffolding/`: spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md, 4 contracts, 1 checklist.
- CLAUDE.md updated with new commands section.

### Added
- `docs/EXPERIMENT.md` — living brainstorm doc defining the project as a personal research playground for multi-agent LLM debate dynamics (~50 ideas tagged by source project, Tier 1/2/3 cost filter).
- `docs/MULTI_AGENT_DEBATE_RESEARCH.md` — strategic-decision doc evaluating three integration paths (standalone harness / merge into agent-harness-v2 / build new). Recorded for reference; superseded by EXPERIMENT.md's "stay separate, iterate freely" framing.
- `claudedocs/SETUP.md` — personal setup guide (state paths, provider switching, cost ranges, "what not to touch" list).
- `scripts/backtest.py` — typer CLI looping `propagate(ticker, date)` over a grid; resumable via append-as-we-go CSV; segregated memory log; first 65-run pilot completed (NVDA/AAPL/MSFT/GOOGL/JPM × Jan-Apr 2026).
- `scripts/analyze_backtest.py` — alpha-vs-SPY analyzer with per-ticker yfinance cache, rich-table reports for rating-bucket distribution, spread, calibration.
- `tickers.txt` — personal 10-name universe spanning sectors (NVDA / AAPL / MSFT / GOOGL / JPM / BRK.B / UNH / WMT / XOM / CAT). Picked up by `backtest.py` when `--tickers` not given.
- Personalized `README.md` (upstream README preserved at `README.upstream.md`).
- `tradingagents/graph/trading_graph.py` — `_fetch_returns` lifted to module-level `fetch_returns()` so the analyzer can import it without instantiating the full graph (thin wrapper preserved on the class for backward compatibility).

### Changed
- `pyproject.toml` distribution name → `tradingagents-lab` (import name `tradingagents` unchanged); version → `0.3.0-dev`; description, authors, keywords, classifiers, project URLs added.
- `CHANGELOG.md` split — upstream history moved to `CHANGELOG.upstream.md`; this file tracks personal-fork changes only.
- `main.py` — Anthropic provider, Sonnet 4.6 deep / Haiku 4.5 quick, 1/1 debate rounds, checkpoint enabled (default ticker `NVDA`, default date current).

### Removed
- `requirements.txt` — 3-byte stub containing only `.`, redundant with `pyproject.toml`.
- `test.py` (root) — ad-hoc yfinance smoke script; not pytest, misleading filename.
- `backtrader>=1.9.78.123` from `pyproject.toml` dependencies — confirmed unused (zero `import backtrader` references in source).

### Fixed
- `main.py` — removed `anthropic_effort = "medium"` default that produced 400 errors on Sonnet/Haiku (extended-thinking effort is Opus-only). Documented as a gotcha in `claudedocs/SETUP.md`.

### Pilot findings (recorded for posterity)
65-run pilot, ~$32 spend, 0 errors, ~14h wall-clock. Headline findings (read as debate-dynamics phenomena, not stock-picking outcomes):
- **Mode collapse to 3 of 5 rating tiers** — 0 Buys, 0 Sells across 65 runs. Framework's declared 5-tier scale is a vocabulary, not a behavior.
- **Anti-signal in the bullish bucket** — Overweight bucket: -0.35% mean alpha vs SPY, 41% hit rate. When the framework converges on Overweight, the stock underperforms more often than not.
- **Inverted hit-rate ordering** — Hold (57%) > Underweight (58%) > Overweight (41%).
- **Magnitudes inside noise** — σ per bucket 2.5–4%; mean differences ~1.5%. Cannot reject "all means equal" with n=29 max per bucket.

Full analysis in `docs/MULTI_AGENT_DEBATE_RESEARCH.md` and `docs/EXPERIMENT.md`.

### Test coverage at fork point
**31% overall (92 passing tests).** Plumbing well-covered (schemas, memory, signal processing, checkpoint). Core debate logic ≤ 20%: analysts (0–13%), `graph/setup.py` (12% — the actual LangGraph topology), `conditional_logic.py` (21%), all LLM clients (0–22%), `dataflows/` (7–29%, external API wrappers). No test asserts the 5-tier rating scale is honored across runs — direct cause of why upstream's mode collapse went undetected.

---

Personal fork started from upstream `7c37249 chore: release v0.2.4` (2026-04 release).
