# Project structure

Internal directory tour for operators + future-self. Links from `README.md` "Where things live" section.

## Research substrate

| Path | Purpose |
|---|---|
| `experiments/<YYYY-MM-DD>-NNN-<slug>/` | Per-experiment dirs with `HYPOTHESIS.md` + `PARAMS.json` + `results.csv` + `ANALYSIS.md` + `run.sh` |
| `findings.md` | Auto-aggregated experiment summaries (regenerate via `scripts/findings_aggregate.py`) |
| `RESEARCH_FINDINGS.md` | Project-level synthesis across all experiments |
| `ROADMAP.md` | Forward-looking exploration map + open work |
| `CHANGELOG.md` | Per-day entries with merged-PR detail |
| `claudedocs/` | Retrospectives + meta-narratives + design docs (~100 files) |
| `claudedocs/research-burst-<YYYY-MM-DD>.md` | Canonical day-narrative docs for major-arc days |
| `docs/EXPERIMENT.md` | Original brainstorm + Tier 1/2/3 candidate idea filter |

## Filter portfolio

9 production filters. See README "Filter portfolio" table for default modes + empirical support. Module paths:

| Filter | Module |
|---|---|
| A3 momentum | `tradingagents/agents/utils/momentum_filter.py` |
| Spec 003 contrarian gate | `tradingagents/signals/contrarian_gate.py` |
| Spec 003.5 sector-baseline fallback | `tradingagents/signals/sector_baseline.py` |
| Spec 004 sector-momentum | `tradingagents/agents/utils/sector_momentum_filter.py` |
| Spec 006 bear-sector-symmetry | `tradingagents/agents/utils/bear_sector_symmetry_filter.py` |
| Spec 007 forward-catalyst (bull/bear) | `tradingagents/agents/utils/forward_catalyst_filter.py` |
| Spec 008 Hybrid C calendar boost | `tradingagents/agents/utils/calendar_boost.py` |
| Spec X-1 C-4 institutional rotation | `tradingagents/agents/utils/institutional_rotation_filter.py` |
| Path C analyst PT snapshot (default-off) | `tradingagents/agents/utils/analyst_pt_snapshot.py` |

## Specs (`specs/` + `.specify/specs/`)

Spec-kit bundles for each structural change:

| Spec | Directory | Status |
|---|---|---|
| Spec 001 bots-architecture | `.specify/specs/001-bots-architecture/` | Phases 1-5 implemented |
| Spec 002 signal-lifecycle | `.specify/specs/002-signal-lifecycle/` | Phases 0-2.5 implemented |
| Spec 003 contrarian gate | `.specify/specs/003-analyst-contrarian-gate/` | Phases 1+2 implemented + default-on |
| Spec 003.5 sector-baseline | `specs/003-sector-baseline-gate/` | Default-on |
| Spec 004 sector-momentum | `specs/004-sector-momentum-filter/` | Default-off (retrospective FAILED) |
| Spec 006 bear-sector-symmetry | `specs/005-bear-sector-symmetry/` | Default-off (SC-008 FAILED) |
| Spec 007 forward-catalyst | `specs/006-forward-catalyst-gate/` | Bull-active, bear-shadow |
| Spec 008 Hybrid C calendar boost | `specs/007-calendar-boost-filter/` | Default-off |
| Spec X-1 C-4 institutional rotation | `specs/091-c4-institutional-rotation/` | Bear-shadow / bull-off |
| WC-10 continuous scalar rating | `specs/108-wc-10-continuous-scalar-rating/` | Default-off (Tier 2 experiment) |

The on-disk directory prefix (e.g., `091-`) often diverges from the user-facing spec name (e.g., "Spec X-1") — cross-check via `spec.md` header.

## Tooling

### Backtest + analysis
- `scripts/backtest.py` — typer CLI looping `propagate(ticker, date)` over a grid; resumable; `--news-vendor` flag
- `scripts/analyze_backtest.py` — alpha-vs-SPY analyzer
- `scripts/analyze_sc009_ab.py` — SC-009 A/B ablation analyzer (post-hoc reconstruction)
- `scripts/single_call_baseline.py` — single Claude call on saved analyst reports
- `scripts/horizon_sweep.py` — cross-experiment longer-horizon analysis ($0)
- `scripts/identify_hold_extremes.py` — top-N Hold dates by |α|
- `scripts/check_rating_distribution.py` — EH-2 rating distribution gate

### Bear-side mechanism class survey + Constitution VIII gate tooling
- `scripts/forward_catalyst_class[1,2,3,4,5,5_reaction]_retrospective.py` — VIII v1.4.0 standalone-gate retrospectives (one per mechanism class)
- `scripts/forward_catalyst_class[5_vs_class3,4_vs_spec007]_overlap.py` — v1.4.3 additive-overlap analysis pairs
- `scripts/probe_[analyst_price_targets,earnings_history,short_interest,institutional_ownership].py` — feasibility probe family

### Behavioral-additive + memory-log integrity
- `scripts/behavioral_additive_sweep.py` — cross-cohort behavioral-additive case counter; canonical v1.4.6 evidence base
- `scripts/v1_4_4_counter_evidence_watch.py` — scans state logs for v1.4.6-refuting rows; CI-friendly
- `scripts/memory_log_integrity_check.py` — flags reflection-prose hallucinations (Quality Gate #6 tooling)

### Spec-X-1 / Spec-003 specific
- `scripts/spec_x_1_operator_validation.py` — single-shot Spec X-1 production validation (~$0.40)
- `scripts/spec_003_historical_recompute.py` — backfills Spec 003 cache from existing state logs ($0)

### WC-10 (Tier 2 experiment)
- `scripts/wc_10_pilot.py` — 40-propagate pilot harness (10 dates × 2 tickers × 2 modes; ~$16 LLM)

### Per-ticker / debate diagnostics
- `scripts/bear_side_per_ticker.py` — per-ticker UW α breakdown
- `scripts/diagnose_uw_quality.py` — debate features per UW commit
- `scripts/uw_suppression_filter.py` — A3 retrospective on momentum-based suppression

### Experiment scaffolding
- `scripts/new_experiment.py` — generates `experiments/<date>-NNN-<slug>/` with `HYPOTHESIS.md` + `PARAMS.json` + `run.sh` stubs (`--tier T1/T2/T3/T4` for Constitution III cost-tier)
- `scripts/findings_aggregate.py` — walks `experiments/*/ANALYSIS.md`, writes `findings.md`

## Data vendors

| Vendor | Module | Notes |
|---|---|---|
| Exa Search (news) | `tradingagents/dataflows/exa_news.py` | Default; requires `EXA_API_KEY`. True historical date filter via startPublishedDate/endPublishedDate. |
| yfinance (prices/technicals/fundamentals) | `tradingagents/dataflows/y_finance.py` | Default; no API key needed |
| Alpha Vantage | `tradingagents/dataflows/alpha_vantage_*.py` | Alternative; requires `ALPHA_VANTAGE_API_KEY` |

## Personalization

| File | Purpose |
|---|---|
| `main.py` | Anthropic Sonnet 4.6 deep / Haiku 4.5 quick, 1/1 debate rounds, checkpoint enabled |
| `tickers.txt` | Personal ticker universe (10 names) |
| `claudedocs/SETUP.md` | Operator guide (state paths, provider switching, filter portfolio + opt-in modes, what NOT to touch) |
| `CLAUDE.md` | Claude Code project context (read first when re-entering project) |
| `.env` | API keys (gitignored) |

## Constitution + spec-kit

| File | Purpose |
|---|---|
| `.specify/memory/constitution.md` | 8 principles + Quality Gates + Principle VIII sub-clauses |
| `.specify/templates/` | Spec-kit templates (spec-template.md, plan-template.md, tasks-template.md) |
| `.specify/scripts/powershell/` | Spec-kit helper scripts (`create-new-feature.ps1`, `setup-plan.ps1`, etc.) |

## Auto-memory

`C:\Users\<user>\.claude\projects\C--Development-Projects-TradingAgents\memory\` — operator-private cross-session memory. 26+ entries covering feedback rules, project status, reusable patterns, footguns. NOT in git; persists via Claude Code auto-memory system.

## Cache + state

`~/.tradingagents/` (override via `TRADINGAGENTS_CACHE_DIR` / `TRADINGAGENTS_RESULTS_DIR` / `TRADINGAGENTS_MEMORY_LOG_PATH`):

| Subdir | Purpose |
|---|---|
| `logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json` | Per-propagate state log (rich annotation; persisted via `_log_state` whitelist) |
| `cache/checkpoints/<TICKER>.db` | Per-ticker SQLite checkpoint (resume-on-crash; opt-in via `checkpoint_enabled=True`) |
| `memory/trading_memory.md` | Append-only trading memory log (Portfolio Manager reads on next same-ticker propagate) |
| `paper/<portfolio_id>.json` + `.events.jsonl` | Paper-trading harness state (Spec 002) |
