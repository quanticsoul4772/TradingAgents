# TradingAgents-lab

Personal experimental fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4 — a research playground for studying multi-agent LLM debate dynamics. **Equity decision-making is the substrate (cheap objective ground truth via 5/10/21-day forward returns vs SPY), not the goal.**

Upstream docs in [`README.upstream.md`](README.upstream.md). Upstream release history in [`CHANGELOG.upstream.md`](CHANGELOG.upstream.md). Local changes in [`CHANGELOG.md`](CHANGELOG.md).

## Headline finding

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls are no better than coin flip.** At 21-day windows, the framework's bullish commits (Buy + Overweight) produce **+1.23% mean alpha across n=71 commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE.** Three-period NVDA cross-validation (Q1 2026 / Q4 2025 / Q3 2025): two of three periods positive; Q4 2025 is the negative outlier.

Hold ≈ 0% median at every horizon — the framework's mode collapse to Hold is **calibrated abstention**, not a defect (Constitution Principle VII). Bearish commits are regime-asymmetric (UW on bear-correct tickers ARE directionally appropriate; UW on bull-regime tickers drive the aggregate anti-calibration).

Full synthesis + cross-period evidence + per-failure-mode analysis in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Forward roadmap in [`ROADMAP.md`](ROADMAP.md). Per-experiment summaries in [`findings.md`](findings.md).

## Filter portfolio (9 production filters)

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

8 candidates retrospectively SKIPPED before any spec was written (Spec 005, Spec 009, 5 of 6 PR #22 bear-side mechanism classes, Spec 010). Pre-spec validation per Constitution Principle VIII saved ~30-40h of empty-spec implementation. See [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) for module paths + spec directories.

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

8 principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (v1.4.6): Save Everything · One Experiment Per Change · Stay Cheap (T0/T1/T2/T3 cost ladder) · No Production Claims · Steal Liberally · Spec Before Structural Change · **Calibrated Abstention is a Valid Output** · **Retrospective Before Spec for Backward-Looking Price Filters** (extended through v1.4.6 with forward-catalyst-class gate, magnitude fungibility, additive-to-existing-filter gate, behavioral-additive 4th interpretation).

Quality Gate #6 (v1.4.5): operators MUST cross-check memory log entry header data against reflection prose before citing prior entries as evidence. Tooling: `scripts/memory_log_integrity_check.py`.

## Tests

**1146 unit + 2 integration tests** (80.5% coverage). Production filter modules all at >80% coverage.

```bash
pytest                # full suite
pytest -m unit -q     # fast subset
```

Test count history + per-spec breakdown in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Coverage analysis in [`claudedocs/test-coverage-gap-analysis-2026-05-08.md`](claudedocs/test-coverage-gap-analysis-2026-05-08.md).

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
