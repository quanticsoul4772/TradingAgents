# Changelog (personal fork)

All notable changes to this **personal experimental fork** of TradingAgents are documented here. Upstream history lives in [`CHANGELOG.upstream.md`](CHANGELOG.upstream.md).

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
