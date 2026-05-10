# TradingAgents-lab

Personal experimental fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4 — a research playground for studying multi-agent LLM debate dynamics. **Equity decision-making is the substrate (cheap objective ground truth via 5/10/21-day forward returns vs SPY), not the goal.**

Upstream docs in [`README.upstream.md`](README.upstream.md). Upstream release history in [`CHANGELOG.upstream.md`](CHANGELOG.upstream.md). Local changes in [`CHANGELOG.md`](CHANGELOG.md).

## Live signals product (paper-trading)

```bash
python scripts/run_daily.py    # daily flow: signals → paper-trade step → status
```

One-command daily orchestrator wrapping the framework's `propagate(ticker, today)` over a curated 25-name tech-weighted watchlist into actionable bullish 21d-horizon recommendations + a persistent paper portfolio. Operator runbook + product definition + opinionated defaults rationale in [`docs/LIVE_SIGNALS_PRODUCT.md`](docs/LIVE_SIGNALS_PRODUCT.md). ~$10/day LLM at the default watchlist; paper-only per Constitution Principle IV.

## Headline finding

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls are no better than coin flip.** At 21-day windows, the framework's bullish commits (Buy + Overweight) produce **+1.23% mean alpha across n=71 commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE.** Three-period NVDA cross-validation (Q1 2026 / Q4 2025 / Q3 2025): two of three periods positive; Q4 2025 is the negative outlier.

Mode collapse to Hold is **MULTI-MECHANISM** — 4 distinct structural sources documented per Constitution VII v1.5.0 → v1.5.1 → v1.5.2 → v1.5.3. Three research arcs landed in 2026-05 quantify the mechanisms:

- **WC-10 research arc CLOSED** ($54.40 LLM): output-schema bottleneck. v1 SC-007 ALT-A confirmed at 3.6× commit ratio; v2 (n=100, 8 tickers) SC-005(b) **NULL** (Pearson r +0.0918 < ±0.197 critical); SC-007 ALT-A PARTIAL (5/8 tickers); bullish-amplification REPLICATES (Buy n=20 α +2.93% / 80% hit); v3 (Q4 2025 NVDA) PARTIAL ALT-A within ±100bps NULL. **Spec 009 Branch C activated** (bin-then-output ergonomic-only; 5-tier external preserved). Branch A NOT activated per v2 NULL. See [`## WC-10 mode`](#wc-10-mode-research-arc-closed-spec-009-branch-c-active) section below.

- **WC-11 research arc OPEN at PARTIAL** ($32 LLM = v1 $8 + v2 $24): analyst-order bottleneck. v1 (n=20) PARTIAL ALT-A + ALT-B at per-permutation commit rate 0% → 40%; cannot disambiguate first-vs-last-speaker bias at this n. v2 (n=60, 3 tickers) PARTIAL **ticker-conditional**: NVDA reproduces v1 news-first elevation EXACTLY (40%); AAPL elevates news-LAST (60%); MSFT elevates fundamentals-EARLY. **No single analyst-position rule explains all 3 tickers.** Constitution v1.5.2 Analyst-order scope + v1.5.3 Ticker-conditional clarification both per WC-11. See [`## WC-11 analyst-order randomization`](#wc-11-analyst-order-randomization-research-arc-open-partial-ticker-conditional) section below.

- **BR-3 research arc OPEN at DIFFERENTIAL** ($24 LLM = v1 $8 + v2 $16): analyst-stage structured-output bottleneck. v1 (market analyst, n=20) PARTIAL ALT-B at +20pp commit shift / α delta below ±1pp threshold. v2 (n=40) **DIFFERENTIAL**: sub-A `news_analyst` NULL-leaning (0pp); sub-B `fundamentals_analyst` PARTIAL ALT-B at **+40pp** (2× v1 magnitude). **2 of 3 analyst stages carry the bottleneck** (market + fundamentals); narrative analyst doesn't. Tools-rich analysts carry it. **Phase E (structured-output throughout) STILL NOT unblocked** at this evidence level. No Constitution amendment. See [`## BR-3 analyst-stage structured-output`](#br-3-analyst-stage-structured-output-research-arc-open-differential--phase-e-not-unblocked) section below.

- **Spec 012 Class 4 macro-environment filter DEPLOYED** (2026-05-09): FIRST cross-asset/macro bear-side filter. Default-shadow @ VIX < 18; n=8 retrospective fires; net Δα +24.07pp; cohort hit 75%. Mechanism-disjoint vs A3 (catches 6 of 22 ticker_strong bear cohort A3 misses entirely). Bear-side mechanism class survey now at **7-evaluated / 2-PASS** (C-4 institutional rotation = Spec X-1 + Class 4 macro = Spec 012); survey re-opened to OPEN-ENDED. See [`## Spec 012 Class 4 macro filter`](#spec-012-class-4-macro-environment-filter-first-cross-assetmacro) section below.

Bearish commits are regime-asymmetric (UW on bear-correct tickers ARE directionally appropriate; UW on bull-regime tickers drive the aggregate anti-calibration).

Full synthesis + cross-period evidence + per-failure-mode analysis in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Forward roadmap in [`ROADMAP.md`](ROADMAP.md). Per-experiment summaries in [`findings.md`](findings.md).

## Filter portfolio (10 production filters)

| Filter | Mechanism | Default | Empirical support |
|---|---|---|---|
| [A3 momentum](tradingagents/agents/utils/momentum_filter.py) | backward-price (per-ticker) | ON @ -5%/30d | +0.70pp/n=43 |
| [Spec 003 contrarian gate](tradingagents/signals/contrarian_gate.py) | prose-density (per-ticker IC) | ON @ 80th pct | +0.65pp/n=11 |
| [Spec 003.5 sector-baseline fallback](specs/003-sector-baseline-gate/) | prose-density (sector pool) | ON | Cold-start gap closure |
| [Spec 004 sector-momentum](specs/004-sector-momentum-filter/) | backward-price (sector ETF) | OFF | -0.45pp/n=73 anti-pred |
| [Spec 006 bear-sector-symmetry](specs/005-bear-sector-symmetry/) | backward-price (ticker vs sector) | OFF | -0.71pp/n=36; SC-008 FAILED |
| [Spec 007 forward-catalyst (bull)](specs/006-forward-catalyst-gate/) | LLM-extracted | ACTIVE @ T=0.60 | +14.43pp discrim / 88.9% hit / +2.24pp Δα |
| [Spec 007 forward-catalyst (bear)](specs/006-forward-catalyst-gate/) | LLM-extracted | SHADOW @ T=0.50 | +23.10pp discrim / 72.2% hit |
| [Spec 008 Hybrid C calendar boost](specs/007-calendar-boost-filter/) | hybrid (Class 3 × calendar) | OFF | +3.35pp Δα improvement; SC-009 PRELIMINARY PASS-by-non-counterexample |
| [Spec X-1 C-4 institutional rotation](specs/091-c4-institutional-rotation/) | quantitative 13F flow | SHADOW bear / OFF bull | +5.41pp standalone / +8.06pp additive vs Spec 007 |
| [Spec 012 Class 4 macro-environment](specs/012-class-4-macro-filter/) | cross-asset macro (VIX-snapshot) | SHADOW bear @ VIX<18 / OFF bull | +24.07pp net Δα / 75% hit on n=8 retrospective; mechanism-disjoint vs A3 |

10 candidates retrospectively SKIPPED/DEFERRED before any spec was written (Spec 005, Spec 009-cand, 5 of 7 evaluated bear-side mechanism classes — original 6 from PR #22 plus Class 4 macro added 2026-05-09 → bear-side survey now at **7-evaluated / 2-PASS** with C-4 institutional rotation + Class 4 macro both shipped, Spec 010 Class 5 BULL fundamentals-delta, **Class 4 BULL SKIP** + **local-high BULL DEFER** added 2026-05-09). Pre-spec validation per Constitution Principle VIII saved ~30-40h of empty-spec implementation. Bear-side mechanism class survey is now **OPEN-ENDED** post-Class 4 (new mechanism class hypotheses can surface). See [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) for module paths + spec directories.

## Quick start

```bash
# Install (uv-managed venv)
pip install -e .

# Required env vars (in .env)
# ANTHROPIC_API_KEY=...
# EXA_API_KEY=...    # required for news vendor

# Single-run analysis
python main.py

# Interactive CLI with resume-on-crash
tradingagents analyze --checkpoint
```

## WC-10 mode (research arc CLOSED; Spec 009 Branch C active)

WC-10 replaces the 5-tier categorical PortfolioRating enum (Buy / Overweight / Hold / Underweight / Sell) with a continuous scalar in `[-1.0, +1.0]` (signed conviction magnitude). Per Constitution VII v1.5.0/v1.5.1/v1.5.2/v1.5.3, the 5-tier scale is now characterized as MULTI-MECHANISM (4 distinct structural sources of mode collapse to Hold).

**Status (as of 2026-05-09)**: WC-10 research arc CLOSED. v1 (n=20): SC-007 ALT-A confirmed (3.6× commit ratio). v2 (n=80, 8 tickers): SC-005(b) **NULL** (combined v1+v2 Pearson r +0.0918 < ±0.197 critical at n=100); SC-007 ALT-A **PARTIAL** (5/8 tickers ≥80% commit). v3 (Q4 2025 NVDA): PARTIAL ALT-A within ±100bps NULL region. **Spec 009 Branch C selected** — bin-then-output ergonomic-only mode (5-tier external; continuous internal). Operator activation: `wc_10_enabled=True` + `wc_10_filter_mode="bypass"` + `wc_10_internal_only=True` in PARAMS.json. **Branch A** (`daily_signals.py --wc-10-enabled` flag) **NOT activated** per v2 NULL verdict; production-facing signals remain 5-tier. Full guide at [`docs/SIGNALS.md`](docs/SIGNALS.md) WC-10 section.

```bash
# Research mode — opt in via PARAMS.json today (Spec 009):
# {
#   "config_overrides": {
#     "wc_10_enabled": true,
#     "wc_10_filter_mode": "bypass"
#   }
# }
python scripts/backtest.py --experiment-id <id> --out experiments/<id>/results.csv

# Dry-run digest from saved data (PR #141; $0 LLM):
python scripts/wc_10_dryrun_digest.py --date 2026-04-15

# Production-tier monitoring (PR #146; cron-friendly):
python scripts/wc_10_underperformance_monitor.py --csv <paired-mode-csv>
```

**Branch A NOT activated** per v2 SC-005(b) NULL verdict — `daily_signals.py` and `paper_trade.py` consume the 5-tier external interface only. The v1 NVDA bullish-amplification ergonomic gain is captured by Branch C's bin-then-output pattern internally; no scalar exposure to operator workflows. Future re-evaluation triggers: SC-005(b) re-test at corpus n≥200 OR new mechanism evidence for scalar-magnitude predictiveness.

**Caveats** (mandatory reading; per Constitution v1.5.1 Bear-regime validation paragraph):
1. Bullish-side amplification well-calibrated on bull-regime tickers; bearish-side anti-calibrated on rising tickers (v1 AAPL UW pattern + v3 NVDA Buy-on-falling pattern)
2. Magnitude bound: `|α delta vs 5-tier| < 1.0pp` per v3 cohort empirical evidence
3. Runtime monitoring (`wc_10_underperformance_monitor.py`) is the production enforcement of the caveat — wire it into nightly cron when Branch A activates

## WC-11 analyst-order randomization (research arc OPEN, PARTIAL ticker-conditional)

WC-11 tests whether the framework's commit-rate metrics are stable under randomization of the analyst-execution order (`market`, `news`, `fundamentals` in different sequences). The DEFAULT order is `[market, news, fundamentals]`; v1 found the DEFAULT is empirically Hold-biased.

**v1** (NVDA × 5 dates × 4 permutations, n=20, $8 LLM, [`experiments/2026-05-08-004-wc11-order-randomization/`](experiments/2026-05-08-004-wc11-order-randomization/)): per-permutation commit rate ranged **0% → 40%** (±20pp from pooled mean). Both ALT-A (news-first elevates) and ALT-B (market-last drops) triggers fired on the SAME `news_fundamentals_market` permutation — **cannot disambiguate first-speaker vs last-speaker bias at this n**. Constitution VII v1.5.1 → **v1.5.2** PATCH: new "Analyst-order scope" paragraph mandating future commit-rate ablations randomize order or document as confounder.

**v2** (NVDA + AAPL + MSFT × 5 dates × 4 permutations, n=60, $24 LLM, [`experiments/2026-05-09-002-wc11-v2-disambiguation/`](experiments/2026-05-09-002-wc11-v2-disambiguation/)): cross-ticker generalization test. Per-permutation × per-ticker commit-rate matrix:

| Permutation | NVDA | AAPL | MSFT |
|---|---:|---:|---:|
| `market_news_fundamentals` (DEFAULT) | 0% | 20% | 20% |
| `news_fundamentals_market` | **40%** | 20% | **40%** |
| `fundamentals_market_news` | 0% | **60%** | **40%** |
| `market_fundamentals_news` | 0% | **60%** | 0% |

NVDA reproduces v1 news-first elevation EXACTLY (40% in both v1 + v2). AAPL elevates with NEWS-LAST orderings (60% on the 2 perms where news appears last). MSFT elevates when fundamentals appears EARLY. **No single analyst-position rule explains all 3 tickers simultaneously.** The v1 ALT-A vs ALT-B ambiguity is now joined by a TICKER-ASYMMETRY finding. Constitution VII v1.5.2 → **v1.5.3** PATCH: new "Ticker-conditional clarification" paragraph documenting that the analyst-order effect is ticker-conditional, not framework-general.

**Operational implications**:
1. Continue to randomize analyst order OR document as confounder per v1.5.2
2. Do NOT assume news-first is uniformly preferable — only NVDA-like tickers benefit; AAPL-like tickers benefit from news-LAST
3. Per-ticker analysis is necessary; pooled analyses across heterogeneous ticker sets average out the order-effect

**Open question**: WC-11 v3-class extension (broader ticker basket, ≥5 tickers × 5 dates × 4 perms; ~$40 T3) would test whether the ticker-conditional pattern generalizes beyond the v2 NVDA/AAPL/MSFT mix. Tracked in [`ROADMAP.md`](ROADMAP.md) Open Questions.

## BR-3 analyst-stage structured-output (research arc OPEN, DIFFERENTIAL — Phase E NOT unblocked)

BR-3 (codename **Squeak**, ported from `battlecode2026 ratbot6`) replaces an analyst's prose output with a Pydantic-structured `{bullish, bearish, key_risks}` emission. Tests whether the prose-to-structured representation change at the analyst stage shifts downstream PM commit-rate or α calibration.

**v1** (market analyst only, NVDA + AAPL × 5 dates × 2 modes, n=20, $8 LLM, [`experiments/2026-05-09-001-br3-squeak-market-analyst/`](experiments/2026-05-09-001-br3-squeak-market-analyst/)): commit shift +20pp triggered (ALT-B trigger MET) but α delta +0.24pp BELOW the ±1pp ALT-B magnitude threshold. **PARTIAL ALT-B**. NVDA unanimous-Hold across all 10 propagates; AAPL is the only divergence ticker.

**v2** (news + fundamentals analysts, NVDA + AAPL × 5 dates × 4 modes, n=40, $16 LLM, [`experiments/2026-05-09-003-br3-v2-news-fundamentals/`](experiments/2026-05-09-003-br3-v2-news-fundamentals/)): cross-stage generalization test. **DIFFERENTIAL VERDICT**:

| Sub-experiment | Verdict | Commit shift | α delta |
|---|---|---:|---:|
| sub-A `news_analyst` | **NULL-leaning** | 0pp | +1.60pp* |
| sub-B `fundamentals_analyst` | **PARTIAL ALT-B** | **+40pp** | +0.11pp |

*α delta on sub-A is single-row noise (1 NVDA structured Buy at +20% realized α dominates n=10).

**Joint synthesis across all 3 analyst stages** (BR-3 v1 + v2):

| Stage | Verdict | Commit shift |
|---|---|---:|
| Market analyst (v1) | PARTIAL ALT-B | +20pp |
| News analyst (v2 sub-A) | **NULL** | 0pp |
| Fundamentals analyst (v2 sub-B) | PARTIAL ALT-B | **+40pp** |

**2 of 3 analyst stages carry the structured-output commit-shift bottleneck** (market + fundamentals); 1 of 3 does NOT (news). **Asymmetric mechanism interpretation**: tools-rich analysts (market = technical indicators / fundamentals = financial metrics) carry the bottleneck; prose-heavy analyst (news = narrative) does NOT. When analyst output is fundamentally NUMERIC, prose serialization loses information that structured emission preserves.

**Phase E architectural variant ("structured-output throughout") still NOT unblocked** at this evidence level: PARTIAL ALT-B α magnitudes BELOW ±1pp threshold can't validate calibration. Phase E remains conditional on a v3 cohort with n=30+ commits per analyst stage. Cross-pollination L4 status NARROWED from "pilot-eligible" to **"pilot-eligible (focus on fundamentals analyst stage)"**.

**Open question**: BR-3 v3-class extension (combined market + fundamentals structured modes, ~$8-16 T2) would test whether stacking the 2 confirmed-bottleneck stages pushes α delta above ±1pp ALT-B calibration threshold. Tracked in [`ROADMAP.md`](ROADMAP.md) Open Questions.

## Spec 012 Class 4 macro-environment filter (FIRST cross-asset/macro)

Spec 012 ships the framework's FIRST cross-asset/macro filter: bear-side suppression of UW/Sell commits to Hold when VIX is below threshold. Mechanism-disjoint from all 9 prior filters (A3 / Spec 003 / Spec 003.5 / Spec 004 / Spec 006 / Spec 007 / Spec 008 / Spec X-1 — none consume cross-asset macro state).

**Deployed default**: bear-side `class_4_macro_bear_mode = "shadow"` @ `class_4_macro_vix_threshold = 18.0`; bull-side OFF (asymmetric — bull retrospective SKIP'd at every threshold). 5-PR bundle deployment (#194 spec → #197 plan → #198 module → #199 tests → #200 polish + retrospective).

**Empirical evidence** ([`claudedocs/class4-macro-filter-retrospective-2026-05-09.md`](claudedocs/class4-macro-filter-retrospective-2026-05-09.md)):

| Gate | Result |
|---|---|
| Standalone (Constitution VIII v1.4.0) | **PASS** at n=8 fires; net Δα +24.07pp; cohort hit 75% (6 of 22 ticker_strong cohort caught) |
| Additive (Constitution VIII v1.4.3) vs A3 | **PASS** mechanism-disjoint — A3 catches 0 of 22 ticker_strong cohort by definition; Class 4 catches 6 |
| Discriminator | VIX 30d Δ% (ticker_strong cohort committed bear when VIX rising +10.50%/30d vs other-bear-cells +22.96%; -12.46pp Δ) |

**Filter ordering** (FR-012): A3 → Spec 003/003.5 → Spec 004 → Spec 006 → Spec 007 → Spec X-1 → **Class 4 (LAST per smallest-sample-last rule)**. Zero LLM cost (Constitution III T0); ~250ms p99 latency cache-cold.

**Bear-side mechanism class survey re-opened to 7-evaluated / 2-PASS** post-Class 4 (joins C-4 institutional rotation = Spec X-1). Survey is now **OPEN-ENDED** — Class 4 itself was NEW post-2026-05-07 conclusion, demonstrating new mechanism class hypotheses can surface beyond the original PR #22 6-class taxonomy.

**Audit script**: `scripts/class4_macro_shadow_audit.py` for SC-010 default-on flip readiness (deferred until 30+ live shadow-mode fires accumulate).

## Backtest

```bash
python scripts/backtest.py \
    --start 2026-01-02 --end 2026-04-25 \
    --frequency W \
    --out backtest_results.csv
python scripts/analyze_backtest.py backtest_results.csv --holding-days 21
```

Resumable. `--news-vendor exa|alpha_vantage` switches the news adapter (default `exa`). `--experiment-id` tags rows + auto-syncs override config to `experiments/<id>/PARAMS.json`. `--yes` skips cost confirmation.

## Cross-experiment analysis ($0; reuses existing CSVs)

```bash
python scripts/horizon_sweep.py            # 5/10/21/90-day forward α per bucket per experiment
python scripts/identify_hold_extremes.py   # top-N Hold dates by |α|
python scripts/bear_side_per_ticker.py     # per-ticker UW α breakdown
python scripts/uw_suppression_filter.py    # A3 retrospective
```

## Where things live

| Doc | Purpose |
|---|---|
| [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) | Directory tour: filters / specs / tooling / data vendors / cache + state |
| [`claudedocs/SETUP.md`](claudedocs/SETUP.md) | Operator guide: install, run, filter opt-in, troubleshooting, what NOT to touch |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code project context (read first when re-entering) |
| [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md) | Original brainstorm + Tier 1/2/3 candidate idea filter |

## Constitution

8 principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (**v1.5.3**): Save Everything · One Experiment Per Change · Stay Cheap (T0/T1/T2/T3 cost ladder) · No Production Claims · Steal Liberally · Spec Before Structural Change · **Calibrated Abstention is a Valid Output** · **Retrospective Before Spec for Backward-Looking Price Filters** (extended through v1.5.3 with forward-catalyst-class gate, magnitude fungibility, additive-to-existing-filter gate, behavioral-additive 4th interpretation, **Schema-induced abstention is NOT calibrated abstention** carve-out per WC-10 v1, **Bear-regime validation** paragraph per WC-10 v3, **Analyst-order scope** paragraph per WC-11, **Ticker-conditional clarification** paragraph per WC-11 v2).

Quality Gate #6 (v1.4.5): operators MUST cross-check memory log entry header data against reflection prose before citing prior entries as evidence. Tooling: `scripts/memory_log_integrity_check.py`.

WC-10 production-deployment monitoring (v1.5.0 caveat enforcement): `scripts/wc_10_underperformance_monitor.py` — flag cohorts where WC-10 mode produces worse realized α than 5-tier baseline. Cron-friendly exit code (0 = no alerts, 1 = alert).

## Tests

**1193 unit + 2 integration tests** (81%+ coverage; verified 2026-05-09 PR #233 via `pytest -m unit -q`). Production filter modules all at >80% coverage. Mypy clean baseline at 0 errors maintained since 2026-05-08 sweep (PRs #117-#129 cleared 124 errors / 17 files; ruff also at 0 errors).

```bash
pytest                # full suite
pytest -m unit -q     # fast subset
```

Test count history + per-spec breakdown in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Coverage analysis in [`claudedocs/test-coverage-gap-analysis-2026-05-08.md`](claudedocs/test-coverage-gap-analysis-2026-05-08.md).

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
