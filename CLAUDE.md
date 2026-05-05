# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`tradingagents-lab` is a personal experimental fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4, repurposed as a research playground for studying multi-agent LLM debate dynamics. Equity-decision-making is the *substrate* (cheap objective ground truth), not the goal.

**Primary research question**: what structural conditions cause role-based multi-agent LLM debate to collapse to moderate ratings, and what enforcement mechanisms (or alternative architectures) would prevent that collapse?

## Read the headline finding first

After 22 experiments + cross-experiment horizon sweep + per-ticker breakdown + Opus 4.7 model swap (NVDA + AAPL) + Opus 30-pair mixed basket + 3-period NVDA cross-validation (Q1 2026, Q4 2025, Q3 2025) + Phase D substrate exploration (XLK + multi-sector + XLE) + Phase C reasoning_evidence wiring + Spec 002 signal-lifecycle pipeline + Spec 001 bots-architecture (Phases 1-5) + Phase 4 live-validated bot_models routing, the architectural conclusion is captured in **`RESEARCH_FINDINGS.md`**. Forward roadmap in **`ROADMAP.md`**.

> At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls (Buy/OW/UW/Sell) are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) produce **+1.23% mean alpha across n=71 cross-experiment commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE**. Three-period NVDA cross-validation: Q3 2025 +0.80% (n=10, 60% hit), Q4 2025 -0.47% (n=9, 22% hit), Q1 2026 ~+3.5% blended (n=15, ~80% hit). Two of three periods positive — **Q4 2025 is the negative outlier, not Q1 2026 as 008 alone suggested**. Reasoning_evidence Bayesian posterior on stable-cross-period-signal: 0.64 → 0.52 → **0.63** (recovered after Q3 evidence). Bearish commits are regime-asymmetric, not uniformly anti-calibrated. Hold ≈ 0% median at every horizon. **Mode-collapse direction is a function of (model × ticker × regime × prompt)**: Sonnet over-abstains on bull tickers AND over-commits-bearish on bear tickers; Opus discriminates per-ticker. **Bucket-level claims replicate; date-level and realized-α claims do not** — 005's NVDA 10/10 OW becomes 6/10 OW + 4 Hold on the same dates in 007; per-ticker bucket ratios hold across reruns and across periods, but realized α is period-conditional. The A3 momentum filter is correctly inert on regime-mismatch failures (validated by `claudedocs/a3-filter-forensics-007.md`). Phase D substrate test: framework went 30pp more Hold-heavy on XLK vs same-date NVDA — **decision architecture is portable across substrates; commit calibration is substrate-specific (single-stock-prompt-tuned)**.

This is encoded in **Constitution Principle VII (Calibrated Abstention is a Valid Output)** added 2026-05-03 then re-amended after 006. Any new structural change that reduces Hold rate must justify in HYPOTHESIS.md why the additional commits would be calibrated rather than noise, at what horizon, and with what directional asymmetry expectation.

## Read the constitution first

The design is governed by `.specify/memory/constitution.md`. Before non-trivial changes, read:

1. `.specify/memory/constitution.md` — **seven** core principles (Save Everything, One Experiment Per Change, Stay Cheap, No Production Claims, Steal Liberally, Spec Before Structural Change, **Calibrated Abstention is a Valid Output**). The principles are constraints, not aspirations.
2. `RESEARCH_FINDINGS.md` — project-level synthesis across all 22 experiments + the 5 open questions with their reasoning-tool-derived priors and empirical answers, plus Spec 001 (bots architecture) Phases 1-5 + Spec 002 (signal lifecycle) Phases 0-2.5 results.
3. `ROADMAP.md` — sequenced phases of exploration (Phase B validate / C operationalize / D substrate-extend / E architectural variants) + cross-pollination opportunities from sibling projects.
4. `docs/EXPERIMENT.md` — original brainstorm of ~50 ideas tagged by source project (agent-harness-v2 / ladybird / battlecode2026 / bruno-swarm / mcp-reasoning). Most Tier 1 ideas now superseded by completed experiments; Tier 2/3 still untouched.
5. `docs/MULTI_AGENT_DEBATE_RESEARCH.md` — strategic-context doc evaluating three integration paths against the user's portfolio. Recorded for reference; superseded by ROADMAP framing.
6. `docs/SCAFFOLDING_PLAN.md` — install plan for spec-kit + ruff + mypy + pre-commit. Reflects what's currently scaffolded.
7. `claudedocs/SETUP.md` — operator setup guide (state paths, provider switching, cost ranges, "what not to touch").

The principles in the constitution govern day-to-day code changes:
- **Save Everything (Principle I)** — every experiment writes to `experiments/<date>-<id>-<name>/` with `HYPOTHESIS.md`, `PARAMS.json`, `results.csv`, `ANALYSIS.md`, `run.sh`. Corpus is the research output.
- **One Experiment Per Change (Principle II)** — vary one parameter at a time so the corpus is interpretable as ablation data.
- **Stay Cheap (Principle III)** — runs default to ≤ $30 LLM spend; crossing requires explicit deliberation in `HYPOTHESIS.md`.
- **Spec Before Structural Change (Principle VI)** — changes to the (future) event log, gates, worker structures, or `experiments/` convention itself start with `/speckit.specify`.

## Spec-kit workflow

Spec-kit (GitHub spec-kit v0.4.4 templates) is installed at `.specify/`. Slash commands available in this Claude Code session:

- `/speckit.constitution` — amend constitution
- `/speckit.specify <feature>` — generate `.specify/specs/<id>-<name>/spec.md`
- `/speckit.clarify` — resolve open questions interactively
- `/speckit.plan` — generate implementation plan
- `/speckit.tasks` — generate task list
- `/speckit.implement` — execute (or do by hand)
- `/speckit.analyze` — post-mortem
- `/speckit.checklist`, `/speckit.taskstoissues` — auxiliary

Templates live at `.specify/templates/`. Helper scripts (PowerShell) at `.specify/scripts/powershell/`.

## Quality gates (run by pre-commit)

- **ruff** (`v0.15.12`) — formatter + linter, target Python 3.10, line-length 100. Configured in `pyproject.toml` `[tool.ruff]`.
- **pytest unit tests** — runs on every commit via the `pytest-fast` local hook (`pytest -m unit -q`).
- **Standard hygiene**: trailing whitespace, EOF newlines, large files (>500KB), merge conflicts, private keys.

mypy (`v1.20`) is installed but **not** in pre-commit (too slow). Run manually: `mypy tradingagents`.

**Baseline** (recorded at scaffolding install): ruff = 305 errors, mypy = 167 errors. New code adds zero new violations; the existing baseline is grandfathered for now (we'll be replacing much of it as part of `EXPERIMENT.md` plans).

**Test coverage** (as of 2026-05-04): 785 tests passing, 81%+ project coverage. Anthropic + OpenAI clients ~95%, all 4 analyst factories + 5 debate-agent factories 100%, graph/setup.py 100%, conditional_logic.py 100%, trading_graph.py 88%, dataflows/interface.py 98%. New since 2026-05-03: Spec 002 signal-lifecycle (Phases 0-2.5) at ~95% (registry + cache + featurization + drift + counterfactual + multi-horizon eval); Spec 001 bots-architecture (Phases 1-5) including Phase 4 BotLLMFactory (18 unit + 3 live-construction integration tests, plus end-to-end live-validation in `experiments/2026-05-04-007-phase4-bot-models-smoke/`). Routing-mismatch regression test (`tests/test_interface_routing.py::test_every_categorized_tool_has_impl_for_default_vendor`) added 2026-05-03 after experiment 008 caught the `get_insider_transactions × news_data × exa` mismatch.

## Commands

Install (editable, with dev deps via uv-managed lockfile):
```bash
pip install -e .
```

Run the interactive CLI (entry point installed by `pyproject.toml`):
```bash
tradingagents analyze                       # standard run
tradingagents analyze --checkpoint          # enable resume-on-crash
tradingagents analyze --clear-checkpoints   # wipe per-ticker checkpoint DBs
python -m cli.main                          # equivalent without install
```

Run a Python-API analysis directly:
```bash
python main.py
```

Experiments scaffolding (per `.specify/memory/constitution.md` Principle I):
```bash
python scripts/new_experiment.py mr1-contradiction --source-idea MR-1
# → creates experiments/<YYYY-MM-DD>-NNN-mr1-contradiction/ with HYPOTHESIS.md,
#   PARAMS.json, run.sh, run.ps1 stubs.

python scripts/backtest.py \
    --experiment-id 2026-05-02-001-pm-blind \
    --config-override pm_sees_debate=false \
    --out experiments/2026-05-02-001-pm-blind/results.csv \
    --yes
# → tags every CSV row with the experiment ID; auto-syncs the override
#   into experiments/<id>/PARAMS.json.

python scripts/findings_aggregate.py
# → walks experiments/*/ANALYSIS.md, writes findings.md at repo root
#   (newest first). Lab-notebook view of the project.

python scripts/horizon_sweep.py
# → cross-experiment longer-horizon analysis on existing CSVs
#   (5/10/21/90-day forward alpha per rating bucket per experiment).
#   Zero new LLM cost — reuses saved data.

python scripts/identify_hold_extremes.py --top-n 8 --horizon 21
# → top-N Hold dates by |α| with state-log evidence summaries.
#   Feeds counterfactual analysis ("what if framework had committed?").

python scripts/single_call_baseline.py \
    --ticker NVDA \
    --dates 2026-01-30,2026-02-06,... \
    --experiment-id <id> --out <path> --yes
# → loads existing state logs, feeds 3 analyst reports to ONE Claude call,
#   produces a 5-tier rating. Tests architectural premise of multi-agent
#   structure vs single call on same inputs.

python scripts/bear_side_per_ticker.py
# → per-ticker UW α breakdown (Q4 diagnostic). Tests whether bear-side
#   anti-calibration is uniform or regime-concentrated.

python scripts/diagnose_uw_quality.py
# → debate features (bull/bear length, hedge words, keywords) for each
#   UW commit. Identifies the composite discriminator from A1.

python scripts/uw_suppression_filter.py
# → A3 retrospective: simulates the mean-reversion suppression filter
#   on historical UW commits. Operates on existing CSVs; $0.
```

**News vendor** (per `--news-vendor`):
- `exa` (default; requires `EXA_API_KEY`) — true historical date filter via startPublishedDate/endPublishedDate
- `alpha_vantage` — alternative for users with that subscription

`yfinance` and `brave` news vendors were removed 2026-05-03; `yfinance` the package is still used for stock prices, technical indicators, and fundamental data.

**A3 momentum filter** (opt-in production augmentation): set `config["uw_momentum_filter_threshold"] = -5.0` to enable mean-reversion suppression of UW/Sell commits. Wired in `tradingagents/agents/managers/portfolio_manager.py` via `tradingagents/agents/utils/momentum_filter.py`. Default disabled. **Forensics validation** (post-experiment 007): the filter targets mean-reversion bounces specifically — it correctly stays inert on regime-mismatch UW commits (e.g. INTC was UP +11-33% at 4 of 6 UW dates and never in suppression zone). See `claudedocs/a3-filter-forensics-007.md` for per-row breakdown.

Tests (pytest is configured in `pyproject.toml`, markers: `unit`, `integration`, `smoke`):
```bash
pytest                                      # full suite — conftest injects placeholder API keys
pytest tests/test_structured_agents.py      # single file
pytest -k checkpoint_resume                 # by name
pytest -m unit                              # by marker
```

Smoke-test the structured-output decision agents against a real provider (no `propagate()` cost):
```bash
OPENAI_API_KEY=... python scripts/smoke_structured_output.py openai
ANTHROPIC_API_KEY=... python scripts/smoke_structured_output.py anthropic
```

Docker:
```bash
cp .env.example .env                        # add API keys
docker compose run --rm tradingagents
docker compose --profile ollama run --rm tradingagents-ollama
```

## Architecture

The system is a LangGraph `StateGraph` over `AgentState` (a `MessagesState` subclass in `tradingagents/agents/utils/agent_states.py`). Entry point is `TradingAgentsGraph.propagate(ticker, date)` in `tradingagents/graph/trading_graph.py`. Pipeline order, defined in `graph/setup.py`:

1. **Analysts** (selectable subset of `market`, `social`, `news`, `fundamentals`) — each is a tool-using ReAct loop that writes a typed report into state. Connected in sequence with a `tools_<type>` ToolNode and a `Msg Clear <Type>` node that wipes scratch messages between analysts (via `create_msg_delete()` — Anthropic compatibility requires the placeholder `HumanMessage`).
2. **Bull ↔ Bear debate** — alternates until `max_debate_rounds` then exits to **Research Manager**.
3. **Trader** produces a trade proposal.
4. **Risk debate** — Aggressive ↔ Conservative ↔ Neutral, alternates until `max_risk_discuss_rounds` then exits to **Portfolio Manager** (the only agent that consults the memory log).

Three decision agents (`research_manager`, `trader`, `portfolio_manager`) use `llm.with_structured_output(Schema)` with provider-native modes (json_schema, response_schema, tool-use). The pattern is centralized in `agents/utils/structured.py`: the bind happens at agent creation; if the provider doesn't support structured output the agent falls back to free-text and logs a warning. Pydantic schemas + `render_*` markdown helpers live in `agents/schemas.py` — render output preserves the legacy markdown shape so downstream consumers (memory log, CLI display, JSON state log) keep working.

`SignalProcessor` (`graph/signal_processing.py`) extracts the rating from the Portfolio Manager's rendered markdown via a deterministic regex over the **5-tier scale** (Buy / Overweight / Hold / Underweight / Sell). Trader uses a 3-tier scale (Buy / Hold / Sell) since transaction direction is naturally ternary. Don't introduce a fourth scale.

### LLM provider layer (`tradingagents/llm_clients/`)

`create_llm_client(provider, model, base_url=None, **kwargs)` is a factory with **lazy provider imports** so test collection and the CLI startup don't pull in every SDK. OpenAI-compatible providers (`openai`, `xai`, `deepseek`, `qwen`, `glm`, `ollama`, `openrouter`) all route through `OpenAIClient`. `anthropic`, `google`, and `azure` have dedicated clients. Provider-specific thinking/effort kwargs are mapped in `TradingAgentsGraph._get_provider_kwargs()`.

**`backend_url` defaults to `None` on purpose.** Each provider client falls back to its native default endpoint. The previous OpenAI-URL default leaked into Gemini and produced 404s — don't reintroduce a non-None default at the config layer.

### Data vendor layer (`tradingagents/dataflows/`)

Tools in `agents/utils/{core_stock,technical_indicators,fundamental_data,news_data}_tools.py` are vendor-agnostic. Routing happens in `dataflows/interface.py` based on `config["data_vendors"]` (category-level default) and `config["tool_vendors"]` (per-tool override). Supported vendors: `yfinance` (default, no key) and `alpha_vantage`. When adding a new vendor, register it in both dicts.

### Persistence

Two independent systems, both rooted under `~/.tradingagents/` (override base with `TRADINGAGENTS_CACHE_DIR` / `TRADINGAGENTS_RESULTS_DIR`):

- **Decision log** (`agents/utils/memory.py`, `TradingMemoryLog`) — append-only markdown at `~/.tradingagents/memory/trading_memory.md` (override with `TRADINGAGENTS_MEMORY_LOG_PATH`). `propagate()` writes a `pending` entry at the end of every run; on the next same-ticker run, `_resolve_pending_entries()` fetches realized return + alpha vs SPY via `yfinance`, generates a one-paragraph reflection, and updates the entry. Only the Portfolio Manager reads memory, and only when entries exist (so empty memory cannot fabricate "past lessons"). `memory_log_max_entries` caps **resolved** entries; pending entries are never pruned. The `<!-- ENTRY_END -->` HTML comment is the hard separator — don't change it (LLM prose can't emit HTML comments).
- **Checkpoint resume** (`graph/checkpointer.py`) — opt-in via `config["checkpoint_enabled"]` / `--checkpoint`. Per-ticker SQLite DBs at `~/.tradingagents/cache/checkpoints/<TICKER>.db` so concurrent tickers don't contend. Thread ID is `sha256("<TICKER>:<date>")[:16]` so same ticker+date resumes, different date starts fresh. Checkpoints are cleared on successful completion. The graph is recompiled with the SqliteSaver only inside `propagate()` and torn back down in `finally`.

## Conventions

- **Always pass `encoding="utf-8"` to `open()` / `read_text()` / `write_text()`.** Windows defaults to cp1252; this has caused multiple bugs (#543, #550, #576).
- **Don't add try/except to silently swallow errors.** The error-protocol rule from global RULES.md applies: read the message, fix the actual broken thing, don't add fallbacks/graceful degradation that hide failures. Existing fallbacks (e.g., structured-output → free-text) are deliberate and logged.
- **Internal debate agents stay in English** even when `output_language` is set (reasoning quality). Only user-facing agents (analysts, portfolio manager) localize via `get_language_instruction()` in `agents/utils/agent_utils.py`.
- **Preserve exchange-qualified tickers** end-to-end (`.TO`, `.L`, `.HK`, `.T`). `build_instrument_context()` enforces this in agent prompts.
- The CLI's `MessageBuffer` (`cli/main.py`) tracks agent status via `REPORT_SECTIONS`. When adding a new analyst or report field, update both `ANALYST_MAPPING` and `REPORT_SECTIONS` or the progress display will desync.
- Tests must not require real API keys: `tests/conftest.py` autouses placeholder values for every provider env var. New tests that hit live providers belong behind the `integration` marker.
- **When adding new state-level data from a graph node's return dict, declare the key in `AgentState`** (`tradingagents/agents/utils/agent_states.py`). LangGraph's `StateGraph` silently drops undeclared keys from state merges. Spec 001 worked around this by mutating `final_state` post-`graph.invoke()`; spec 003 hit the same issue and fixed it by declaring `contrarian_gate` in the TypedDict. If your node returns `{key: value}` and you don't see `key` in `final_state`, check the schema first.
