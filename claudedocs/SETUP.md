# TradingAgents — Personal Setup Guide

Your local config, distilled. This reflects what's actually on disk, not generic docs.

## 1. What's installed

- **Repo:** `C:/Development/Projects/TradingAgents` (branch `main`, v0.2.4)
- **venv:** `.venv/` (Python 3.12.8, created with `uv venv`)
- **Provider:** Anthropic (key in `.env`, gitignored)
- **Models:** `claude-sonnet-4-6` (deep) + `claude-haiku-4-5` (quick) for default runs; `claude-opus-4-7` for the strongest deep model
- **Data:**
  - News: **Exa** (`EXA_API_KEY` required; in `.env`) — yfinance/brave news vendors were removed 2026-05-03
  - Stock prices / technicals / fundamentals: yfinance (no key needed)
- **Checkpoint resume:** enabled in `main.py` (opt-in for the CLI)
- **A3 momentum filter:** opt-in via `config["uw_momentum_filter_threshold"] = -5.0` — suppresses UW/Sell commits on tickers in -5%+ trailing-30d drawdown (mean-reversion zone). Default off.

Persistent state lives under `~/.tradingagents/`:
```
~/.tradingagents/
├── logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<date>.json
├── memory/trading_memory.md
└── cache/checkpoints/<TICKER>.db
```

## 2. Activate the env (every new shell)

```bash
source .venv/Scripts/activate         # Git Bash
.venv\Scripts\activate                # cmd / PowerShell
```

Confirm with `which python` → should point inside `.venv/Scripts/`.

## 3. Run an analysis

Three entry points, pick whichever fits the moment:

| Command | When to use |
|---|---|
| `python main.py` | Scripted run with the config baked into `main.py` (currently NVDA, 2026-04-30) |
| `tradingagents analyze` | Interactive — picks ticker, date, depth, provider via menus |
| `tradingagents analyze --checkpoint` | Same, with resume-on-crash |
| `tradingagents analyze --clear-checkpoints` | Wipe all checkpoint DBs first |

The CLI overrides `main.py`'s config with whatever the menus return — so `main.py` is the right place to encode your defaults, the CLI is for one-offs.

## 4. Where output goes

After a run completes:

- **Final decision** — printed to stdout (the last line of `python main.py`).
- **Full transcript** — `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<date>.json`. Contains every analyst report, both debate transcripts (bull/bear and 3-way risk), trader plan, and final PM decision. This is the audit trail.
- **Memory log entry** — appended to `~/.tradingagents/memory/trading_memory.md` as `pending`. Backfilled with realized 5-day return + alpha vs SPY on the **next same-ticker run** (after ~7 calendar days have passed).

## 5. Reading the JSON state log

The fields you'll actually look at:

```
market_report          ← Market Analyst (technicals)
sentiment_report       ← Social Analyst (social media tone)
news_report            ← News Analyst (current events)
fundamentals_report    ← Fundamentals Analyst (company financials)
investment_debate_state.judge_decision   ← Research Manager's pick after Bull/Bear
trader_investment_decision               ← Trader's proposal
risk_debate_state.judge_decision         ← Portfolio Manager's final call
final_trade_decision                     ← duplicate of above; what gets parsed for the rating
```

The 5-tier rating (Buy / Overweight / Hold / Underweight / Sell) is regex-extracted from `final_trade_decision` by `SignalProcessor` — no extra LLM call.

## 6. Changing models or depth

All knobs live in `main.py` (or override per-run in your own script):

```python
config["deep_think_llm"]  = "claude-opus-4-6"   # ~3-5x cost, used 2 times per run
config["quick_think_llm"] = "claude-haiku-4-5"  # cheap, used many times
config["anthropic_effort"] = "high"             # extended-thinking budget — Opus only; Sonnet/Haiku 400
config["max_debate_rounds"] = 2                 # bull↔bear rounds; doubles those calls
config["max_risk_discuss_rounds"] = 2           # 3-way risk debate rounds
config["output_language"] = "Spanish"           # localizes user-facing reports; debates stay English
```

**`anthropic_effort` gotcha**: extended-thinking effort is only supported on Opus 4.x. Setting it on Sonnet 4.6 or Haiku 4.5 returns `BadRequestError 400: This model does not support the effort parameter`. Leave it unset (or empty) unless your `deep_think_llm` is Opus.

**Cost rule of thumb** (NVDA-sized analysis):
- Sonnet-deep + Haiku-quick + 1/1 rounds → **$0.30-$0.80**
- Same with 2/2 rounds → **~$0.80-$1.80**
- Opus-deep + Haiku-quick + 1/1 rounds → **$1.50-$3.50**
- All-Opus → **$5-$15+** (don't unless you have a specific reason)

The deep model only runs at Research Manager and Portfolio Manager — the two reasoning-heavy decision points. Worth paying up for; the quick model handles the high-volume nodes.

## 7. Memory log workflow

Designed for **iterated** analysis — runs of the same ticker over time accumulate context the Portfolio Manager uses.

Lifecycle of an entry:
1. Run 1 for NVDA on 4/30 → entry written as `pending`.
2. ~7 calendar days pass.
3. Run 2 for NVDA on 5/7 → at startup, the system fetches NVDA's actual price + SPY's price between 4/30 and 5/7, computes realized return + alpha, generates a one-paragraph reflection, and updates the entry to `resolved`.
4. The PM prompt for run 2 receives the resolved entry from run 1 plus recent cross-ticker lessons.

What this means for you:
- **First run of any ticker** = no memory context. PM is flying blind.
- **The benefit compounds** — run NVDA monthly for six months and PM gets six pieces of "here's what you said, here's what happened" context.
- **Don't edit `trading_memory.md` by hand** unless you understand the parser (see `tradingagents/agents/utils/memory.py`). The `<!-- ENTRY_END -->` separator is load-bearing.
- **Pending entries never get pruned.** Resolved entries can be capped via `config["memory_log_max_entries"] = N`.

To wipe memory and start fresh: `rm ~/.tradingagents/memory/trading_memory.md`.

## 8. Checkpoint resume

Currently **on** in `main.py`. Off by default in the CLI (use `--checkpoint`).

What it does: after every node in the LangGraph pipeline (analyst, debater, manager, etc.), state is serialized to a per-ticker SQLite DB. If the run crashes — network blip, LLM rate limit, you Ctrl+C — the next `propagate()` call with the **same ticker + same date** picks up at the next unfinished node instead of restarting.

Behavior:
- Same ticker, same date → resumes.
- Same ticker, different date → fresh (different `thread_id`).
- Successful completion → checkpoint cleared automatically.

Wipe everything: `tradingagents analyze --clear-checkpoints` or delete `~/.tradingagents/cache/checkpoints/`.

The cost of leaving it on is one SQLite write per node (~negligible). Recommended on.

## 9. Common changes

**Different ticker / date:**
```python
ta.propagate("AAPL", "2026-04-29")
```

**Run multiple tickers in one script:**
```python
for ticker in ["NVDA", "AAPL", "MSFT"]:
    _, decision = ta.propagate(ticker, "2026-04-30")
    print(f"{ticker}: {decision}")
```
Each gets its own checkpoint DB and its own memory-log entries.

**Switch provider mid-experiment:**
```python
config["llm_provider"] = "deepseek"            # cents per run
config["deep_think_llm"] = "deepseek-chat"
config["quick_think_llm"] = "deepseek-chat"
```
Then add `DEEPSEEK_API_KEY=...` to `.env`. The `backend_url` stays `None` — each provider client falls back to its native endpoint.

**Subset of analysts** (skip the news analyst, e.g.):
```python
ta = TradingAgentsGraph(
    selected_analysts=["market", "social", "fundamentals"],
    debug=True,
    config=config,
)
```
Saves time and tokens. The Trader and PM still run regardless.

**Quiet mode** (no streaming chunk prints):
```python
ta = TradingAgentsGraph(debug=False, config=config)   # was True
```

**Localized reports:**
```python
config["output_language"] = "Spanish"  # or any language
```
Internal Bull/Bear/risk debates stay in English on purpose (reasoning quality).

## 10. Troubleshooting

**`UnicodeEncodeError` on Windows** — shouldn't happen in v0.2.4 (every `open()` was patched to `encoding="utf-8"`). If it does, that's a bug — file an issue, don't add a `try/except`.

**Anthropic 401** — key is wrong or revoked. `.env` is loaded by `load_dotenv()` in `main.py` and `cli/main.py`; confirm with:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(bool(os.environ.get('ANTHROPIC_API_KEY')))"
```

**Exa `EXA_API_KEY not set` RuntimeError** — news vendor needs the key:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(bool(os.environ.get('EXA_API_KEY')))"
```
Get a key from https://dashboard.exa.ai/api-keys. Free tier is ~1000 calls/month, generous for normal experiment cadence.

**Anthropic 429 (rate limit)** — drop `max_debate_rounds` to 1, switch `quick_think_llm` to Haiku if you weren't already, or just retry (checkpoint will resume mid-run if enabled).

**yfinance returns empty / `_fetch_returns` warns "could not resolve outcome"** — normal. Means the trade date is too recent for 5-day forward returns. Entry stays `pending`; it'll resolve on the next same-ticker run after enough trading days pass.

**Run hangs on a particular agent** — `debug=True` (already set) prints each chunk. Whichever agent is taking forever is either looping on tools or waiting on the model. Ctrl+C; with checkpoint on, the next run resumes past the completed nodes.

**Tests** —
```bash
pytest                                  # full suite (placeholder API keys auto-injected)
pytest -m unit                          # fast subset
pytest tests/test_checkpoint_resume.py  # one file
```

**Smoke-test just the structured-output decision agents** (cheap — no full propagate):
```bash
python scripts/smoke_structured_output.py anthropic
```

## 11. What NOT to touch

- `<!-- ENTRY_END -->` separator in `memory.py` — load-bearing.
- `backend_url` default of `None` — was the cause of the cross-provider URL leak bug.
- `create_msg_delete()` placeholder `HumanMessage("Continue")` — Anthropic requires a non-empty message after `RemoveMessage`s.
- File I/O without `encoding="utf-8"` — Windows will break.

## 12. Files you'll edit most

| File | Why |
|---|---|
| `main.py` | Your run config and ticker/date |
| `.env` | API keys |
| `tradingagents/default_config.py` | Defaults if you want a different baseline than the upstream's |
| `tradingagents/agents/managers/portfolio_manager.py` | Tweak the PM prompt — highest-leverage agent |
| `tradingagents/agents/managers/research_manager.py` | Tweak the Bull/Bear synthesis |
| `tradingagents/agents/analysts/*.py` | Tweak individual analyst prompts |
| `tradingagents/agents/schemas.py` | Edit Pydantic schemas if you change structured-output shape |

Don't edit anything in `tradingagents/graph/` unless you intend to change the pipeline topology.
