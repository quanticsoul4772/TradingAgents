# Changelog (personal fork)

All notable changes to this **personal experimental fork** of TradingAgents are documented here. Upstream history lives in [`CHANGELOG.upstream.md`](CHANGELOG.upstream.md).

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
