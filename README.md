# TradingAgents-lab — personal experimental fork

Personal copy of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4, repurposed as a research playground for studying multi-agent LLM debate dynamics. Equity decision-making is the substrate (cheap objective ground truth via 5-day forward returns vs SPY), not the goal. Upstream documentation in [`README.upstream.md`](README.upstream.md); upstream release history in [`CHANGELOG.md`](CHANGELOG.md).

## Headline finding

After 11 experiments + cross-experiment horizon sweep:

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) are directionally correct and produce ~+1.6% mean alpha across n=37 commits.** Bearish commits remain anti-calibrated at every horizon. Hold ≈ 0% at every horizon (consistent with "tracks SPY"). The framework is a **calibrated-abstention engine with asymmetric directional skill at 21-day** — not a 5-day predictor as the upstream documentation implies.

Full synthesis in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Per-experiment summaries auto-aggregated in [`findings.md`](findings.md).

## What's local

**Research substrate**
- `experiments/<YYYY-MM-DD>-NNN-<slug>/` — 11 experiments with HYPOTHESIS / ANALYSIS / PARAMS.json / run.sh
- `findings.md` — auto-generated per-experiment one-paragraph summaries
- `RESEARCH_FINDINGS.md` — project-level synthesis across all experiments
- `claudedocs/horizon-sweep.md` — bucket alpha across 5/10/21-day windows
- `.specify/memory/constitution.md` — six principles governing research approach

**Tooling**
- `scripts/backtest.py` — typer CLI looping `propagate(ticker, date)` over a grid; resumable; `--news-vendor` flag
- `scripts/analyze_backtest.py` — alpha-vs-SPY analyzer
- `scripts/check_rating_distribution.py` — EH-2 rating distribution gate (DENY/WARN with reason/purpose/fix)
- `scripts/single_call_baseline.py` — single Claude call on saved analyst reports (architectural-premise test)
- `scripts/horizon_sweep.py` — cross-experiment longer-horizon analysis on existing CSVs ($0)
- `scripts/identify_hold_extremes.py` — top-N Hold dates by |α| with state-log evidence summaries
- `scripts/new_experiment.py` + `scripts/findings_aggregate.py` — experiments scaffolding

**Data vendors**
- `tradingagents/dataflows/yfinance_news.py` — default, free, low quality
- `tradingagents/dataflows/brave_news.py` — high quality, time-leaky (currently-popular ranking bias)
- `tradingagents/dataflows/exa_news.py` — high quality, true historical date filter

**Personalization**
- `main.py` — Anthropic Sonnet 4.6 deep / Haiku 4.5 quick, 1/1 debate rounds, checkpoint enabled
- `tickers.txt` — personal ticker universe (10 names)
- `claudedocs/SETUP.md` — operator guide (state paths, provider switching, what not to touch)
- `CLAUDE.md` — Claude Code project context

## Quick start

```bash
.venv\Scripts\activate                    # Windows
source .venv/bin/activate                 # macOS/Linux
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

Resumable. `--news-vendor yfinance|brave|exa` switches the news adapter. `--experiment-id` tags rows + auto-syncs override config to `experiments/<id>/PARAMS.json`. `--yes` skips cost confirmation.

## Reproduce the cross-experiment horizon analysis

```bash
python scripts/horizon_sweep.py
python scripts/identify_hold_extremes.py --top-n 8 --horizon 21
```

Operates on existing `experiments/*/results.csv` files; zero new LLM cost.

## Constitution

Six principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md): Save Everything, One Experiment Per Change, Stay Cheap (≤$30 per session), No Production Claims, Steal Liberally, Spec Before Structural Change. The principles are constraints, not aspirations.

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
