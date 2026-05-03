# TradingAgents-lab — personal experimental fork

Personal copy of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4, repurposed as a research playground for studying multi-agent LLM debate dynamics. Equity decision-making is the substrate (cheap objective ground truth via 5/10/21-day forward returns vs SPY), not the goal. Upstream documentation in [`README.upstream.md`](README.upstream.md); upstream release history in [`CHANGELOG.md`](CHANGELOG.md).

## Headline finding

After 13 experiments + cross-experiment horizon sweep + per-ticker breakdown + Opus 4.7 model swap (NVDA + AAPL):

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) are directionally correct and produce ~+1.79% mean alpha across n=41 commits (63% hit rate).** Bearish commits remain anti-calibrated at every horizon, with the failure mode concentrated on tickers in -10%+ drawdowns (mean-reversion plays the framework misidentifies). Hold ≈ 0% at every horizon. **Mode-collapse direction is a function of (model × ticker × regime × prompt)**: Sonnet over-abstains on bull tickers + over-commits-bearish on bear tickers; Opus discriminates per-ticker (10/10 OW on NVDA bull regime, 8/10 Hold on AAPL mixed regime).

Full synthesis in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Forward roadmap in [`ROADMAP.md`](ROADMAP.md). Per-experiment summaries auto-aggregated in [`findings.md`](findings.md).

## What's local

**Research substrate**
- `experiments/<YYYY-MM-DD>-NNN-<slug>/` — 13 experiments with HYPOTHESIS / ANALYSIS / PARAMS.json / run.sh
- `findings.md` — auto-generated per-experiment one-paragraph summaries
- `RESEARCH_FINDINGS.md` — project-level synthesis across all experiments
- `ROADMAP.md` — sequenced phases of exploration + cross-pollination ideas
- `claudedocs/horizon-sweep.md` — bucket alpha across 5/10/21-day windows
- `claudedocs/bear-side-per-ticker.md` — per-ticker UW analysis (bull-regime vs bear-correct)
- `claudedocs/uw-debate-diagnostic.md` — debate-quality features for correct vs wrong UW commits
- `claudedocs/uw-suppression-filter.md` — A3 mean-reversion filter retrospective
- `.specify/memory/constitution.md` — seven principles governing research approach (v1.1.0)

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
- `scripts/new_experiment.py` + `scripts/findings_aggregate.py` — experiments scaffolding

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

Seven principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md): Save Everything, One Experiment Per Change, Stay Cheap (≤$30 per session), No Production Claims, Steal Liberally, Spec Before Structural Change, **Calibrated Abstention is a Valid Output** (added 2026-05-03 after the 11-experiment chain converged on this reframe). The principles are constraints, not aspirations.

## Tests

466 tests, 81% coverage as of 2026-05-03.

```bash
pytest                # full suite
pytest -m unit -q     # fast subset
```

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
