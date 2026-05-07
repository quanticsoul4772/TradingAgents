# Changelog (personal fork)

All notable changes to this **personal experimental fork** of TradingAgents are documented here. Upstream history lives in [`CHANGELOG.upstream.md`](CHANGELOG.upstream.md).

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added (constitution v1.3.0 — Principle VIII)
- **Constitution v1.3.0** (`.specify/memory/constitution.md`):
  - **Principle VIII added** (Retrospective Before Spec for Backward-Looking Price Filters): any filter whose mechanism is exclusively backward-looking + price-derived MUST pass a corpus retrospective showing net Δα ≥ +1pp at the proposed default threshold + cohort hit rate ≥ 40% (when a target cohort is named) BEFORE the spec is written. Empirical basis: three same-day retrospective failures on 2026-05-06 — spec 004 sector-momentum (-0.45pp/n=73), spec 006 bear-sector-symmetry (-0.71pp/n=36), spec 005-candidate bull sector-relative (max +0.31pp/n=79). Backward-looking price filters cannot DISCRIMINATE cohort losers from similar-pattern winners; cohort-loser suppression is roughly cancelled by winner suppression. The cost asymmetry ($0/1h retrospective vs ~6-8h spec+impl+tests) makes pre-spec validation a Pareto improvement.
  - Operational test: build retrospective in the shape of `scripts/sector_momentum_retrospective.py` / `scripts/bear_sector_symmetry_retrospective.py` / `scripts/ticker_sector_alpha_retrospective.py`; sweep thresholds; cross-tab against any motivating cohort; commit retrospective markdown BEFORE invoking `/speckit.specify`.
  - Acceptable exception: explicit "shakeout" filters scoped to operator-opt-in (default-off, no SC-008-style empirical-validation gate, marked `shakeout_filter: true` in PARAMS.json).

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
