# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
