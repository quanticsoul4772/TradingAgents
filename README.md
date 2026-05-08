# TradingAgents-lab — personal experimental fork

Personal copy of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4, repurposed as a research playground for studying multi-agent LLM debate dynamics. Equity decision-making is the substrate (cheap objective ground truth via 5/10/21-day forward returns vs SPY), not the goal. Upstream documentation in [`README.upstream.md`](README.upstream.md); upstream release history in [`CHANGELOG.md`](CHANGELOG.md).

## Headline finding

After 24 experiments + cross-experiment horizon sweep + per-ticker breakdown + Opus 4.7 model swap (NVDA + AAPL) + Opus 30-pair mixed basket (Q1 2026) + 3-period NVDA cross-validation (Q1 2026 + Q4 2025 + Q3 2025) + Phase D substrate exploration (XLK + multi-sector + XLE) + SC-003 50-ticker validation + A3 filter forensics + Spec 002 signal-lifecycle pipeline + Spec 001 bots-architecture (Phases 1-5) + Spec 003 analyst-stage contrarian gate (Phases 1+2 implemented + SC-001/SC-002/SC-003 validated; default-on flipped 2026-05-06) + Spec 003.5 sector-baseline fallback + Spec 004 sector-momentum filter + Spec 006 bear-sector-symmetry filter + Spec 007 forward-catalyst gate (bull-active, bear-shadow) + Spec 008 Hybrid C calendar boost + sector-α attribution analyzer + Constitution v1.4.3 + **Spec 008 SC-009 live A/B ablation (2026-05-07; 36/36 rows COMPLETE; PRELIMINARY PASS-by-non-counterexample — 0 decisions changed by boost across full sample; recommend SHADOW-MODE-FIRST for v2 default-on flip)** + **bear-side mechanism class survey from PR #22 CONCLUDES (6/6 evaluated; C-4 institutional ownership delta is SOLE spec-eligible — passed standalone gate @ n=12 + v1.4.3 additive overlap @ +8.06pp Δα improvement vs Spec 007)**:

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) produce +1.23% mean alpha across n=71 commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE.** Three-period NVDA cross-validation: Q3 2025 +0.80% (n=10, 60% hit), Q4 2025 -0.47% (n=9, 22% hit), Q1 2026 ~+3.5% blended (n=15, ~80% hit). Two of three periods positive — **Q4 2025 is the negative outlier, not Q1 2026 as 008 alone suggested**. **Reasoning_evidence Bayesian posterior on "stable cross-period signal" trajectory: 0.64 → 0.52 → 0.63** (recovered after Q3 evidence). Bearish commits are **regime-asymmetric, not uniformly anti-calibrated**: UW on bear-correct tickers are directionally appropriate; UW on bull-regime tickers drive the aggregate anti-calibration. **Bearish anti-calibration shock added 2026-05-06**: 18 of 37 bearish commits (48.6%) landed in `ticker_strong` cell with mean realized α-vs-SPY = **+28.02%** — largest single-metric anti-calibration finding in the corpus. Hold ≈ 0% median at every horizon. **Mode-collapse direction is a function of (model × ticker × regime × prompt)**: Sonnet over-abstains on bull tickers + over-commits-bearish on bear tickers; Opus discriminates per-ticker. **Bucket-level claims replicate; date-level and realized-α claims do not.** Phase D substrate test: framework went 30pp more Hold-heavy on XLK vs same-date NVDA — **decision architecture is portable across substrates; commit calibration is substrate-specific (single-stock-prompt-tuned)**.

**5th failure mode discovered 2026-05-06** (sector-α attribution analyzer): 27 of 79 bullish commits (34.2%) underperform BOTH SPY AND their own sector at 21d (mean α-vs-SPY = -5.34%); **88.9% Tech-concentrated** (AAPL/MSFT/NVDA dominate). 81.8% of LOSING bullish commits are this 5th failure mode. **Constitution Principle VIII v1.3.0** codifies retrospective-first methodology; subsequent v1.4.0 (forward-catalyst-class gate) + v1.4.1 (spec ships its retrospective) + v1.4.2 (magnitude fungibility) + v1.4.3 (additive-to-existing-filter gate) extend it.

**Bear-side mechanism class survey CONCLUDES 2026-05-07**: 6/6 candidate mechanism classes from PR #22 design doc evaluated. **C-4 (institutional ownership delta) is the SOLE spec-eligible mechanism class** — passed Constitution VIII v1.4.0 standalone gate (n=12, mean α +5.41% on suppressed bearish, hit 75%, discrim +10.29pp) AND v1.4.3 additive overlap vs Spec 007 (+8.06pp Δα improvement / +69pp hit improvement; C-4 catches 11 bearish commits Spec 007 entirely misses — different signal sources: LLM semantic vs quantitative 13F flow). C-4 is now spec-invocable as Spec X-1 candidate (SHADOW-MODE-FIRST recommended). Two C-classes show INVERTED bear-side mechanism (C-2 short-covering + C-5 price-reaction): both originally hypothesized as mean-reversion; bear cohort empirically continuation. Three SKIP-types codified: empirical (C-1, C-2, C-5 reaction), data-availability (C-3), structural (C-6). v1.4.4 (behavioral-additive 4th interpretation) + v1.4.5 (memory-log data-vs-prose discipline) constitution amendment drafts shipped, ratification deferred.

Full synthesis in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Forward roadmap in [`ROADMAP.md`](ROADMAP.md). Per-experiment summaries auto-aggregated in [`findings.md`](findings.md). Research-burst day summaries in [`claudedocs/research-burst-2026-05-06.md`](claudedocs/research-burst-2026-05-06.md) and [`claudedocs/research-burst-2026-05-07.md`](claudedocs/research-burst-2026-05-07.md); [`CHANGELOG.md`](CHANGELOG.md) [Unreleased] section has the per-day entries. Sector-α attribution in [`claudedocs/sector-alpha-attribution-2026-05-06.md`](claudedocs/sector-alpha-attribution-2026-05-06.md). A3 filter forensics in [`claudedocs/a3-filter-forensics-007.md`](claudedocs/a3-filter-forensics-007.md). Cross-period validation in [`experiments/2026-05-03-008-opus47-cross-period/ANALYSIS.md`](experiments/2026-05-03-008-opus47-cross-period/ANALYSIS.md) and [`experiments/2026-05-04-001-nvda-q3-2025-micro/ANALYSIS.md`](experiments/2026-05-04-001-nvda-q3-2025-micro/ANALYSIS.md). Bear-side mechanism class survey design + final scorecard in [`claudedocs/bear-side-mechanism-exploration-2026-05-07.md`](claudedocs/bear-side-mechanism-exploration-2026-05-07.md).

## Filter portfolio (8 production filters + 1 spec-eligible candidate as of 2026-05-07)

| Filter | Mechanism class | Default | Empirical support |
|---|---|---|---|
| [A3 momentum](tradingagents/agents/utils/momentum_filter.py) | backward-price (per-ticker) | ON @ -5%/30d | +0.70pp/n=43 (in-sample) |
| [Spec 003 contrarian gate](tradingagents/signals/contrarian_gate.py) | prose-density (per-ticker IC) | ON @ 80th pct, N≥20 | +0.65pp/n=11 (threshold-sweep validated 2026-05-06) |
| [Spec 003.5 sector-baseline fallback](specs/003-sector-baseline-gate/) | prose-density (sector-pool fallback) | ON | Closes cold-start universe gap |
| [Spec 004 sector-momentum](specs/004-sector-momentum-filter/) | backward-price (sector ETF) | OFF | -0.45pp/n=73 anti-predictive (Constitution VIII grandfathered) |
| [Spec 006 bear-sector-symmetry](specs/005-bear-sector-symmetry/) | backward-price (ticker vs sector) | OFF | -0.71pp/n=36 anti-predictive; SC-008 FAILED |
| [Spec 007 forward-catalyst (bull)](specs/006-forward-catalyst-gate/) | LLM-extracted feature | ACTIVE @ T=0.60 | +14.43pp discrim / 88.9% hit / +2.24pp net Δα on n=33 fires |
| [Spec 007 forward-catalyst (bear)](specs/006-forward-catalyst-gate/) | LLM-extracted feature | SHADOW @ T=0.50 | +23.10pp discrim / 72.2% hit / +0.30pp net Δα; shadow-mode-first |
| [Spec 008 Hybrid C calendar boost](specs/007-calendar-boost-filter/) | hybrid (Class 3 × Class 6 calendar) | OFF (operator opt-in) | +3.35pp Δα improvement vs Class 3 alone @ window=14d magnitude=0.5x; SC-009 live ablation 2026-05-07 PRELIMINARY PASS-by-non-counterexample (0 decisions changed by boost; recommend SHADOW-MODE-FIRST for v2 default-on) |
| **Spec X-1 candidate (C-4 institutional rotation)** — NOT YET IMPLEMENTED | quantitative 13F flow (NEW class) | n/a | Standalone PASS @ n=12 (PR #75) + v1.4.3 ADDITIVE PASS @ +8.06pp Δα (PR #77); bear-side; SOLE survivor of 6/6 PR #22 mechanism class survey |

4 of 8 production filters default-active (A3, spec 003, spec 003.5, spec 007 bull). 7 candidates retrospectively SKIPPED before any spec written: **Spec 005 candidate** (per-ticker-vs-sector BULL, max +0.31pp), **Spec 009 candidate** (bear-inverted Hybrid C, +0.00pp at every config), and **5 of 6 bear-side mechanism classes** from PR #22 (Class C-1 SKIP empirical / C-2 SKIP mechanism-inverted / C-3 SKIP not-feasible / C-5 SKIP both variants / C-6 SKIP structural). Pre-spec validation per Constitution Principle VIII saved ~30-40h of empty-spec implementation across the 6-class survey. See [`claudedocs/research-burst-2026-05-06.md`](claudedocs/research-burst-2026-05-06.md) and [`claudedocs/research-burst-2026-05-07.md`](claudedocs/research-burst-2026-05-07.md) for meta-retrospectives.

## What's local

**Research substrate**
- `experiments/<YYYY-MM-DD>-NNN-<slug>/` — 24 experiments with results.csv + HYPOTHESIS / ANALYSIS / PARAMS.json / run.sh (28 directories total; 4 are scaffolds-only or non-propagate harnesses). Latest with realized data: 2026-05-07-001 SC-009 ablation (36/36 rows; PRELIMINARY PASS-by-non-counterexample; canonical 21d windows close ~2026-05-22+).
- `tradingagents/signals/` — Spec 002 signal-lifecycle pipeline (registry + cache + featurization + drift + counterfactual + multi-horizon evaluation + within-ticker IC) + Spec 001 bots-architecture (Signal schema, deterministic aggregator, shadow mode, weight tuning, convergence shortcut, per-bot LLM routing) + Spec 003 contrarian gate (analyst-stage bullish-suppression filter, default-on @80th percentile + N≥20 floor as of 2026-05-06) + Spec 003.5 sector-baseline fallback (default-on; cold-start gap closure)
- `tradingagents/agents/utils/` — A3 momentum filter (bear-side per-ticker absolute, default-on @-5%) + Spec 004 sector-momentum filter (bull-side sector-ETF absolute, default-off) + Spec 006 bear-sector-symmetry filter (bear-side ticker-vs-sector relative, default-off) + Spec 007 forward_catalyst_filter.py (bull-active T=0.60, bear-shadow T=0.50) + Spec 008 calendar_boost.py (Hybrid C, default-off) + Path C analyst_pt_snapshot.py (default-off; unlocks future C-3-class retrospectives)
- `findings.md` — auto-generated per-experiment one-paragraph summaries
- `RESEARCH_FINDINGS.md` — project-level synthesis across all experiments + filter portfolio + 5th failure mode + bearish anti-calibration shock + bear-side mechanism class survey + Principle VIII methodology
- `ROADMAP.md` — sequenced phases of exploration + cross-pollination ideas + open data questions table
- `claudedocs/sector-alpha-attribution-2026-05-06.md` + `.csv` — 4-cell α-vs-SPY × α-vs-sector cross-tab analyzer; surfaced 5th failure mode + bearish anti-calibration
- `claudedocs/sector-momentum-retrospective-2026-05-06.md` / `bear-sector-symmetry-retrospective-2026-05-06.md` / `ticker-sector-alpha-retrospective-2026-05-06.md` / `contrarian-gate-threshold-sweep-2026-05-06.md` — pre-spec corpus retrospectives (4 retrospectives validated the methodology across mechanism classes)
- `claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md` — design exploration for forward-catalyst-aware mechanism class (gap remaining after Principle VIII grandfathering)
- `claudedocs/forward-catalyst-class3-retrospective-2026-05-06.md` — Class 3 LLM-extracted "case priced in" feature retrospective (BORDERLINE; Opus rerun pending)
- `claudedocs/horizon-sweep.md` + `claudedocs/horizon-sweep-007.md` — bucket alpha across 5/10/21-day windows
- `claudedocs/bear-side-per-ticker.md` — per-ticker UW analysis (bull-regime vs bear-correct)
- `claudedocs/uw-debate-diagnostic.md` — debate-quality features for correct vs wrong UW commits
- `claudedocs/uw-suppression-filter.md` — A3 mean-reversion filter retrospective
- `claudedocs/a3-filter-forensics-007.md` — A3 filter validated as correctly inert on regime-mismatch (post-007)
- `.specify/memory/constitution.md` — **eight** principles governing research approach (v1.4.3; Principle VIII added 2026-05-06 with v1.3.0 retrospective-first base, then extended same-day v1.4.0 forward-catalyst-class gate / v1.4.1 spec ships its retrospective / v1.4.2 magnitude fungibility for hybrid filters / v1.4.3 additive-to-existing-filter gate). v1.4.4 (behavioral-additive 4th interpretation) + v1.4.5 (memory-log data-vs-prose discipline) drafts shipped in `claudedocs/constitution-v1.4.[4,5]-draft-2026-05-07.md`; ratification deferred per defensive same-session rule.
- `specs/004-sector-momentum-filter/` + `specs/005-bear-sector-symmetry/` — full speckit bundles for the two grandfathered backward-price filters (cross-referenced against Principle VIII)
- `specs/003-sector-baseline-gate/` — Spec 003.5 sector-baseline fallback bundle
- `specs/006-forward-catalyst-gate/` — Spec 007 forward-catalyst gate bundle (bull-active, bear-shadow)
- `specs/007-calendar-boost-filter/` — Spec 008 Hybrid C calendar boost bundle
- `.specify/specs/001-bots-architecture/` + `.specify/specs/002-signal-lifecycle/` + `.specify/specs/003-analyst-contrarian-gate/` — formal specs (001/002 unimplemented refactors; 003 implemented + default-on)

**Tooling**
- `scripts/backtest.py` — typer CLI looping `propagate(ticker, date)` over a grid; resumable; `--news-vendor` flag
- `scripts/analyze_backtest.py` — alpha-vs-SPY analyzer
- `scripts/analyze_sc009_ab.py` — SC-009 A/B ablation analyzer (post-hoc reconstruction of boost-OFF; 5-path evaluate_gate_1 helper; PRELIMINARY-status guard against accidental ANALYSIS.md overwrite; baseline-coverage diagnostic)
- `scripts/check_rating_distribution.py` — EH-2 rating distribution gate (DENY/WARN with reason/purpose/fix)
- `scripts/single_call_baseline.py` — single Claude call on saved analyst reports (architectural-premise test)
- `scripts/horizon_sweep.py` — cross-experiment longer-horizon analysis on existing CSVs ($0)
- `scripts/identify_hold_extremes.py` — top-N Hold dates by |α| with state-log evidence summaries
- `scripts/bear_side_per_ticker.py` — per-ticker UW α breakdown (Q4 diagnostic)
- `scripts/diagnose_uw_quality.py` — debate features per UW commit
- `scripts/uw_suppression_filter.py` — A3 retrospective on momentum-based suppression
- `scripts/new_experiment.py` + `scripts/findings_aggregate.py` — experiments scaffolding (with `--tier T1/T2/T3/T4` for the cost-tier ladder; T3/T4 inject required Cost-Justification scaffold per Constitution III)

**Research / retrospective scripts** (all $0; bear-side mechanism class survey + Constitution VIII gate tooling)
- `scripts/forward_catalyst_class[1,2,3,4,5,5_reaction]_retrospective.py` — Constitution VIII v1.4.0 standalone-gate retrospectives (one per mechanism class)
- `scripts/forward_catalyst_class[5_vs_class3,4_vs_spec007]_overlap.py` — v1.4.3 additive-overlap analysis pairs
- `scripts/probe_[analyst_price_targets,earnings_history,short_interest,institutional_ownership].py` — feasibility probe family (de-risks ~3h retrospectives via 30-min API checks)
- `scripts/behavioral_additive_sweep.py` — cross-cohort behavioral-additive case counter; canonical v1.4.4 evidence base
- `scripts/v1_4_4_counter_evidence_watch.py` — scans state logs for v1.4.4-refuting rows; CI-friendly exit code
- `scripts/memory_log_integrity_check.py` — flags reflection-prose hallucinations (rating-direction-vs-realized-return-sign mismatches); 20% incidence rate finding
- `scripts/spec_003_historical_recompute.py` — backfills spec 003 cache from existing state logs without rerunning propagates; 9 tickers cleared FR-004 floor

**Data vendors**
- News: `tradingagents/dataflows/exa_news.py` — Exa Search API (true historical date filter via startPublishedDate/endPublishedDate). Requires `EXA_API_KEY`.
- Stock prices / technicals / fundamentals: `tradingagents/dataflows/y_finance.py` (default) or `alpha_vantage*` modules

**Empirical filters (8 production + 1 spec-eligible candidate; 4 default-on)**
- `tradingagents/agents/utils/momentum_filter.py` — A3 mean-reversion suppression filter for Underweight/Sell commits. **Default-on** at -5%/30d. Set to None to ablate.
- `tradingagents/signals/contrarian_gate.py` — Spec 003 contrarian gate + Spec 003.5 sector-baseline fallback. **Default-on** at 80th percentile + N≥20 floor (FR-004). Set `contrarian_gate_mode = "off"` to ablate.
- `tradingagents/agents/utils/sector_momentum_filter.py` — Spec 004 sector-momentum filter. **Default-off** (-0.45pp/n=73 retrospective). Set `sector_momentum_filter_threshold_pct = -5.0` + `sector_momentum_filter_mode = "active"` to enable.
- `tradingagents/agents/utils/bear_sector_symmetry_filter.py` — Spec 006 bear-sector-symmetry filter. **Default-off** (-0.71pp/n=36; SC-008 FAILED). Set `bear_sector_symmetry_filter_threshold_pct = 5.0` + `bear_sector_symmetry_filter_mode = "active"` to enable.
- `tradingagents/agents/utils/forward_catalyst_filter.py` — Spec 007 forward-catalyst gate (LLM-extracted bull/bear case-priced-in scores). Bull-side **default-active** at T=0.60; bear-side **default-shadow** at T=0.50. Set `forward_catalyst_bull_mode = "off"` / `forward_catalyst_bear_mode = "off"` to ablate.
- `tradingagents/agents/utils/calendar_boost.py` — Spec 008 Hybrid C calendar boost (modulates Spec 007's bull score by days-to-earnings within 14d window). **Default-off**. Set `hybrid_c_calendar_boost_enabled = True` + `hybrid_c_calendar_boost_window_days = 14` + `hybrid_c_calendar_boost_magnitude = 0.5` to enable. SC-009 live ablation 2026-05-07 PRELIMINARY PASS-by-non-counterexample.
- `tradingagents/agents/utils/analyst_pt_snapshot.py` — Path C analyst PT snapshot (captures `analyst_price_targets` + `recommendations` distribution at propagate time, persists to `state["forward_catalyst"]["analyst_pt_snapshot"]`). **Default-off**. Set `analyst_pt_snapshot_enabled = True` to enable. Unlocks future C-3-class retrospectives.

**Spec-eligible filter candidate** (NOT YET IMPLEMENTED): Spec X-1 C-4 institutional rotation filter. Bear-side. Standalone PASS at n=12 + v1.4.3 ADDITIVE PASS at +8.06pp Δα improvement vs Spec 007. Recommend SHADOW-MODE-FIRST launch per Constitution VIII v1.4.0 sample-size caution. Caveats: time-window valid until ~2026-05-15 (Q1 2026 13F refresh); n=12 single-quarter sample.

**Personalization**
- `main.py` — Anthropic Sonnet 4.6 deep / Haiku 4.5 quick, 1/1 debate rounds, checkpoint enabled
- `tickers.txt` — personal ticker universe (10 names)
- `claudedocs/SETUP.md` — operator guide (state paths, provider switching, what not to touch)
- `CLAUDE.md` — Claude Code project context

## Quick start

```bash
.venv\Scripts\activate                    # Windows
source .venv/bin/activate                 # macOS/Linux

# Required env vars (in .env or shell):
#   ANTHROPIC_API_KEY=...
#   EXA_API_KEY=...    (required for news)

python main.py                            # one run with baked-in config
tradingagents analyze --checkpoint        # interactive menu, resume on crash
```

## Backtest

```bash
python scripts/backtest.py \
    --start 2026-01-02 --end 2026-04-25 \
    --frequency W \
    --out backtest_results.csv
python scripts/analyze_backtest.py backtest_results.csv --holding-days 21
```

Resumable. `--news-vendor exa|alpha_vantage` switches the news adapter (default `exa`). `--experiment-id` tags rows + auto-syncs override config to `experiments/<id>/PARAMS.json`. `--yes` skips cost confirmation.

## Reproduce the cross-experiment analysis

```bash
python scripts/horizon_sweep.py
python scripts/identify_hold_extremes.py --top-n 8 --horizon 21
python scripts/bear_side_per_ticker.py
python scripts/uw_suppression_filter.py
```

All operate on existing `experiments/*/results.csv` files; zero new LLM cost.

## Constitution

**Eight** principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (v1.4.3): Save Everything, One Experiment Per Change, Stay Cheap (4-tier ladder T1 ≤$5 / T2 $5-30 / T3 $30-100 / T4 >$100), No Production Claims, Steal Liberally, Spec Before Structural Change (extended v1.4.1 with "Spec ships its retrospective + verdict"), **Calibrated Abstention is a Valid Output** (with 2026-05-03 Replicability-scope + Cross-period-scope clarifications), **Retrospective Before Spec for Backward-Looking Price Filters** (added v1.3.0 2026-05-06; extended same-day with v1.4.0 forward-catalyst-class gate / v1.4.2 magnitude fungibility for hybrid filters / v1.4.3 additive-to-existing-filter gate). v1.4.4 (behavioral-additive 4th interpretation) + v1.4.5 (memory-log data-vs-prose discipline) drafts shipped 2026-05-07 — ratification deferred per defensive same-session rule. The principles are constraints, not aspirations.

## Tests

**1179 tests** (was 825 → 984 → 1162 → **1179** across 2026-05-06 + 2026-05-07 research-burst days; +354 net), 81%+ coverage. Spec 002 signal-lifecycle (registry + cache + featurization + drift + counterfactual + multi-horizon eval + within-ticker IC) + Spec 001 bots-architecture (Phases 1-5, Phase 4 BotLLMFactory live-validated) + Spec 003 contrarian gate (Phases 1+2, SC-001 + SC-002 + SC-003 validated; default-on) + Spec 003.5 sector-baseline fallback (10+15 tests; default-on) + Spec 004 sector-momentum filter (~29 tests; default-off after retrospective) + Spec 006 bear-sector-symmetry filter (27 unit + 5 PM-integration + 2 state-log regression tests; default-off after SC-008 FAIL) + Spec 007 forward-catalyst gate (29 unit + 7 PM-integration + 4 state-log/config tests) + Spec 008 Hybrid C calendar boost (27 unit + 7 integration tests) + 2026-05-07 tooling tests: SC-009 analyzer (17 unit), counter-evidence watch (12), memory-log integrity check (12), analyst PT snapshot (9), spec 003 historical-recompute (8 incl. cache-collision guard).

```bash
pytest                # full suite
pytest -m unit -q     # fast subset
```

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
