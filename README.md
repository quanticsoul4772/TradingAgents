# TradingAgents-lab

Personal experimental fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4 — a research playground for studying multi-agent LLM debate dynamics. **Equity decision-making is the substrate (cheap objective ground truth via 5/10/21-day forward returns vs SPY), not the goal.**

Upstream docs in [`README.upstream.md`](README.upstream.md). Upstream release history in [`CHANGELOG.upstream.md`](CHANGELOG.upstream.md). Local changes in [`CHANGELOG.md`](CHANGELOG.md).

## Headline finding

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls are no better than coin flip.** At 21-day windows, the framework's bullish commits (Buy + Overweight) produce **+1.23% mean alpha across n=71 commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE.** Three-period NVDA cross-validation (Q1 2026 / Q4 2025 / Q3 2025): two of three periods positive; Q4 2025 is the negative outlier.

**WC-10 research arc CLOSED (v1 + v2 + v3 + Spec 009 Branch C, $54.40 LLM total)**: mode collapse to Hold is **MULTI-MECHANISM** (4 distinct structural sources documented per Constitution VII v1.5.0/v1.5.1/v1.5.2). v1 (n=20) confirmed SC-007 ALT-A at 3.6× commit ratio. **v2 (n=100, 8 tickers) verdict: SC-005(b) NULL** (Pearson r +0.0918, Spearman ρ +0.0410; both below ±0.197 critical) — scalar magnitude carries no signal beyond what the bin captures. **SC-007 ALT-A PARTIAL** (5/8 tickers ≥80% commit; JNJ 10% + GOOG 60% + JPM 70% retain Hold-default → fall back into VII original sub-population). **Bullish-amplification REPLICATES at expanded n** (Buy n=20 combined α +2.93% / 80% hit; OW n=32 α +2.10% / 53% hit). v3 (Q4 2025 NVDA) PARTIAL ALT-A within ±100bps NULL region. **Spec 009 Branch C activated**: bin-then-output ergonomic-only mode (5-tier external preserved; continuous internal for audit). See [`experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md`](experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md). Sister pilots: WC-11 analyst-order randomization PARTIAL ALT-A + ALT-B (Constitution v1.5.2); BR-3 Squeak market-analyst PARTIAL ALT-B (Phase E NOT unblocked).

Bearish commits are regime-asymmetric (UW on bear-correct tickers ARE directionally appropriate; UW on bull-regime tickers drive the aggregate anti-calibration).

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

## WC-10 mode (research arc CLOSED; Spec 009 Branch C active)

WC-10 replaces the 5-tier categorical PortfolioRating enum (Buy / Overweight / Hold / Underweight / Sell) with a continuous scalar in `[-1.0, +1.0]` (signed conviction magnitude). Per Constitution VII v1.5.0/v1.5.1/v1.5.2, the 5-tier scale is now characterized as MULTI-MECHANISM (4 distinct structural sources of mode collapse to Hold).

**Status (as of 2026-05-09)**: WC-10 research arc CLOSED. v1 (n=20): SC-007 ALT-A confirmed (3.6× commit ratio). v2 (n=80, 8 tickers): SC-005(b) **NULL** (combined v1+v2 Pearson r +0.0918 < ±0.197 critical at n=100); SC-007 ALT-A **PARTIAL** (5/8 tickers ≥80% commit). v3 (Q4 2025 NVDA): PARTIAL ALT-A within ±100bps NULL region. **Spec 009 Branch C selected** — bin-then-output ergonomic-only mode (5-tier external; continuous internal). Operator activation: `wc_10_enabled=True` + `wc_10_filter_mode="bypass"` + `wc_10_internal_only=True` in PARAMS.json. **Branch A** (`daily_signals.py --wc-10-enabled` flag) **NOT activated** per v2 NULL verdict; production-facing signals remain 5-tier. Full guide at [`docs/SIGNALS.md`](docs/SIGNALS.md) WC-10 section.

```bash
# Research mode — opt in via PARAMS.json today (Spec 108):
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

When Branch A activates post-v2:

```bash
# Operator-facing daily workflow (Branch A only)
python scripts/daily_signals.py --tickers tickers.txt --wc-10-enabled \
    --emit-csv ~/.tradingagents/paper/today-wc10.csv

# paper_trade.py consumes scalar for position-sizing
python scripts/paper_trade.py step --signals-csv ~/.tradingagents/paper/today-wc10.csv
```

**Caveats** (mandatory reading; per Constitution v1.5.1 Bear-regime validation paragraph):
1. Bullish-side amplification well-calibrated on bull-regime tickers; bearish-side anti-calibrated on rising tickers (v1 AAPL UW pattern + v3 NVDA Buy-on-falling pattern)
2. Magnitude bound: `|α delta vs 5-tier| < 1.0pp` per v3 cohort empirical evidence
3. Runtime monitoring (`wc_10_underperformance_monitor.py`) is the production enforcement of the caveat — wire it into nightly cron when Branch A activates

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

8 principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md) (**v1.5.2**): Save Everything · One Experiment Per Change · Stay Cheap (T0/T1/T2/T3 cost ladder) · No Production Claims · Steal Liberally · Spec Before Structural Change · **Calibrated Abstention is a Valid Output** · **Retrospective Before Spec for Backward-Looking Price Filters** (extended through v1.5.2 with forward-catalyst-class gate, magnitude fungibility, additive-to-existing-filter gate, behavioral-additive 4th interpretation, **Schema-induced abstention is NOT calibrated abstention** carve-out per WC-10 v1, **Bear-regime validation** paragraph per WC-10 v3, **Analyst-order scope** paragraph per WC-11).

Quality Gate #6 (v1.4.5): operators MUST cross-check memory log entry header data against reflection prose before citing prior entries as evidence. Tooling: `scripts/memory_log_integrity_check.py`.

WC-10 production-deployment monitoring (v1.5.0 caveat enforcement): `scripts/wc_10_underperformance_monitor.py` — flag cohorts where WC-10 mode produces worse realized α than 5-tier baseline. Cron-friendly exit code (0 = no alerts, 1 = alert).

## Tests

**1153 unit + 2 integration tests** (80.5% coverage). Production filter modules all at >80% coverage. Mypy clean baseline at 0 errors as of 2026-05-08 sweep (PRs #117-#129 cleared 124 errors / 17 files).

```bash
pytest                # full suite
pytest -m unit -q     # fast subset
```

Test count history + per-spec breakdown in [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). Coverage analysis in [`claudedocs/test-coverage-gap-analysis-2026-05-08.md`](claudedocs/test-coverage-gap-analysis-2026-05-08.md).

## License

MIT, inherited from upstream. See [`LICENSE`](LICENSE).
