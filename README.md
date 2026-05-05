# TradingAgents-lab — personal experimental fork

Personal copy of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4, repurposed as a research playground for studying multi-agent LLM debate dynamics. Equity decision-making is the substrate (cheap objective ground truth via 5/10/21-day forward returns vs SPY), not the goal. Upstream documentation in [`README.upstream.md`](README.upstream.md); upstream release history in [`CHANGELOG.md`](CHANGELOG.md).

## Headline finding

After 24 experiments + cross-experiment horizon sweep + per-ticker breakdown + Opus 4.7 model swap (NVDA + AAPL) + Opus 30-pair mixed basket (Q1 2026) + 3-period NVDA cross-validation (Q1 2026 + Q4 2025 + Q3 2025) + Phase D substrate exploration (XLK + multi-sector + XLE) + A3 filter forensics + Spec 002 signal-lifecycle pipeline + Spec 001 bots-architecture (Phases 1-5) + Spec 003 analyst-stage contrarian gate (Phases 1+2 implemented + SC-001 + SC-002 validated):

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) produce +1.23% mean alpha across n=71 commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE.** Three-period NVDA cross-validation: Q3 2025 +0.80% (n=10, 60% hit), Q4 2025 -0.47% (n=9, 22% hit), Q1 2026 ~+3.5% blended (n=15, ~80% hit). Two of three periods positive — **Q4 2025 is the negative outlier, not Q1 2026 as 008 alone suggested**. **Reasoning_evidence Bayesian posterior on "stable cross-period signal" trajectory: 0.64 → 0.52 → 0.63** (recovered after Q3 evidence). Bearish commits are **regime-asymmetric, not uniformly anti-calibrated**: UW on bear-correct tickers are directionally appropriate; UW on bull-regime tickers drive the aggregate anti-calibration. Hold ≈ 0% median at every horizon. **Mode-collapse direction is a function of (model × ticker × regime × prompt)**: Sonnet over-abstains on bull tickers + over-commits-bearish on bear tickers; Opus discriminates per-ticker. **Bucket-level claims replicate; date-level and realized-α claims do not.** Phase D substrate test: framework went 30pp more Hold-heavy on XLK vs same-date NVDA — **decision architecture is portable across substrates; commit calibration is substrate-specific (single-stock-prompt-tuned)**.

Full synthesis in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Forward roadmap in [`ROADMAP.md`](ROADMAP.md). Per-experiment summaries auto-aggregated in [`findings.md`](findings.md). A3 filter forensics in [`claudedocs/a3-filter-forensics-007.md`](claudedocs/a3-filter-forensics-007.md). Cross-period validation in [`experiments/2026-05-03-008-opus47-cross-period/ANALYSIS.md`](experiments/2026-05-03-008-opus47-cross-period/ANALYSIS.md) and [`experiments/2026-05-04-001-nvda-q3-2025-micro/ANALYSIS.md`](experiments/2026-05-04-001-nvda-q3-2025-micro/ANALYSIS.md).

## What's local

**Research substrate**
- `experiments/<YYYY-MM-DD>-NNN-<slug>/` — 24 experiments with HYPOTHESIS / ANALYSIS / PARAMS.json / run.sh (latest: 2026-05-05-002 Spec 003 SC-002 — 25 propagates × 5 tickers, borderline-validated mechanism reproduction)
- `tradingagents/signals/` — Spec 002 signal-lifecycle pipeline (registry + cache + featurization + drift + counterfactual + multi-horizon evaluation + within-ticker IC) + Spec 001 bots-architecture (Signal schema, deterministic aggregator, shadow mode, weight tuning, convergence shortcut, per-bot LLM routing) + Spec 003 contrarian gate (analyst-stage bullish-suppression filter). All shipped 2026-05-04 / 2026-05-05.
- `findings.md` — auto-generated per-experiment one-paragraph summaries
- `RESEARCH_FINDINGS.md` — project-level synthesis across all experiments
- `ROADMAP.md` — sequenced phases of exploration + cross-pollination ideas
- `claudedocs/horizon-sweep.md` + `claudedocs/horizon-sweep-007.md` — bucket alpha across 5/10/21-day windows
- `claudedocs/bear-side-per-ticker.md` — per-ticker UW analysis (bull-regime vs bear-correct)
- `claudedocs/uw-debate-diagnostic.md` — debate-quality features for correct vs wrong UW commits
- `claudedocs/uw-suppression-filter.md` — A3 mean-reversion filter retrospective
- `claudedocs/a3-filter-forensics-007.md` — A3 filter validated as correctly inert on regime-mismatch (post-007)
- `.specify/memory/constitution.md` — seven principles governing research approach (v1.2.2)
- `.specify/specs/001-bots-architecture/` + `.specify/specs/002-signal-lifecycle/` — formal specs for two unimplemented refactors

**Tooling**
- `scripts/backtest.py` — typer CLI looping `propagate(ticker, date)` over a grid; resumable; `--news-vendor` flag
- `scripts/analyze_backtest.py` — alpha-vs-SPY analyzer
- `scripts/check_rating_distribution.py` — EH-2 rating distribution gate (DENY/WARN with reason/purpose/fix)
- `scripts/single_call_baseline.py` — single Claude call on saved analyst reports (architectural-premise test)
- `scripts/horizon_sweep.py` — cross-experiment longer-horizon analysis on existing CSVs ($0)
- `scripts/identify_hold_extremes.py` — top-N Hold dates by |α| with state-log evidence summaries
- `scripts/bear_side_per_ticker.py` — per-ticker UW α breakdown (Q4 diagnostic)
- `scripts/diagnose_uw_quality.py` — debate features (bull/bear length, hedge words, keywords) per UW commit
- `scripts/uw_suppression_filter.py` — A3 retrospective on momentum-based suppression
- `scripts/new_experiment.py` + `scripts/findings_aggregate.py` — experiments scaffolding (with `--tier T1/T2/T3/T4` for the cost-tier ladder; T3/T4 inject required Cost-Justification scaffold per Constitution III)

**Data vendors**
- News: `tradingagents/dataflows/exa_news.py` — Exa Search API (true historical date filter via startPublishedDate/endPublishedDate). Requires `EXA_API_KEY`.
- Stock prices / technicals / fundamentals: `tradingagents/dataflows/y_finance.py` (default) or `alpha_vantage*` modules

**Production augmentation (opt-in)**
- `tradingagents/agents/utils/momentum_filter.py` — A3 mean-reversion suppression filter for Underweight/Sell commits. Disabled by default; enable via `config["uw_momentum_filter_threshold"] = -5.0`.

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

Seven principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (v1.2.2): Save Everything, One Experiment Per Change, Stay Cheap (4-tier ladder T1 ≤$5 / T2 $5-30 / T3 $30-100 / T4 >$100, replaces single $30 ceiling), No Production Claims, Steal Liberally, Spec Before Structural Change, **Calibrated Abstention is a Valid Output** (with 2026-05-03 Replicability-scope + Cross-period-scope clarifications: claims must distinguish bucket-level / replicable from date-level / single-observation evidence; realized-α claims are period-conditional unless validated across multiple calendar periods). The principles are constraints, not aspirations.

## Tests

825 tests, 81%+ coverage as of 2026-05-05. Spec 002 signal-lifecycle (registry + cache + featurization + drift + counterfactual + multi-horizon eval + within-ticker IC) + Spec 001 bots-architecture (Phases 1-5, Phase 4 BotLLMFactory live-validated) + Spec 003 contrarian gate (Phases 1+2, SC-001 + SC-002 validated).

```bash
pytest                # full suite
pytest -m unit -q     # fast subset
```

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
