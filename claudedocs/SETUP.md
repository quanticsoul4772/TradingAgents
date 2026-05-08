# TradingAgents — Personal Setup Guide

Your local config, distilled. This reflects what's actually on disk, not generic docs.

## 1. What's installed

- **Repo:** `C:/Development/Projects/TradingAgents` (branch `main`, v0.2.4)
- **venv:** `.venv/` (Python 3.12.8, created with `uv venv`)
- **Provider:** Anthropic (key in `.env`, gitignored)
- **Models:** `claude-sonnet-4-6` (deep) + `claude-haiku-4-5` (quick) for default runs; `claude-opus-4-7` for the strongest deep model
- **Data:**
  - News: **Exa** (`EXA_API_KEY` required; in `.env`) — yfinance/brave news vendors were removed 2026-05-03
  - Stock prices / technicals / fundamentals: yfinance (no key needed); insider transactions also yfinance (moved out of news_data category 2026-05-03 evening to fix routing-mismatch)
  - 18 tools wired into analyst layer (was 8 before SIGNALS expansion): full inventory in `docs/SIGNALS.md`
- **Checkpoint resume:** enabled in `main.py` (opt-in for the CLI)
- **Filter portfolio (8 sides as of 2026-05-06; tagged v0.8.0-spec-008):**
  - **A3 momentum filter** (default ON @ -5%/30d): suppresses UW/Sell commits on tickers in mean-reversion zone. Validated by `claudedocs/a3-filter-forensics-007.md`.
  - **Spec 003 contrarian gate** (default ON @ 80th percentile, N≥20): bull-side per-ticker `bull_keyword_count` percentile suppression.
  - **Spec 003.5 sector-baseline fallback** (default ON): when per-ticker history below N=20, falls back to sector-pool percentile.
  - **Spec 004 sector-momentum** (default OFF): operator opts in via `config["sector_momentum_filter_threshold_pct"] = -5.0`. Empirically anti-predictive (-0.45pp); ships as opt-in only.
  - **Spec 006 bear-sector-symmetry** (default OFF): operator opts in via `config["bear_sector_symmetry_filter_threshold_pct"] = 5.0`. Empirically anti-predictive (-0.71pp); ships as opt-in only.
  - **Spec 007 forward-catalyst BULL** (default ACTIVE @ T=0.60): LLM-extracted (`bull_case_priced_in`) score; suppresses Buy/OW when bull case is consensus-priced-in. Adds ~$0.025/propagate Opus cost. Disable both bull+bear modes to skip the LLM call entirely.
  - **Spec 007 forward-catalyst BEAR** (default SHADOW @ T=0.50): observed-only by default. Flip to "active" via `config["forward_catalyst_bear_mode"] = "active"` after live n≥20 observation period.
  - **Spec 008 Hybrid C calendar boost** (default OFF): operator opts in via `config["hybrid_c_calendar_boost_enabled"] = True`. When enabled: window=14d + magnitude=0.5x are the empirically-grounded defaults. Bull-only enhancement of Spec 007; ZERO LLM cost (post-processing of Spec 007's already-paid call). See `specs/007-calendar-boost-filter/quickstart.md` for operator instructions.
- **Cost-tier ladder** (Constitution v1.2.0 → v1.2.2): per-experiment LLM spend governed by T0 $0 (free post-processing — Hybrid C example) / T1 ≤$5 (free exploration; spec 007 ships here at ~$0.025/run) / T2 $5-30 (standard) / T3 $30-100 (scaled) / T4 >$100 (capital). Use `python scripts/new_experiment.py <slug> --tier T2 --cost 15` when scaffolding.
- **Constitution v1.4.2** governs all default-on flip considerations. Three sub-sections under Principle VIII codify (a) backward-price filter retrospective gate (v1.3.0), (b) forward-catalyst-class filter retrospective gate (v1.4.0), (c) magnitude fungibility for hybrid filters (v1.4.2). Plus Principle VI sub: spec ships its retrospective + verdict (v1.4.1). See `.specify/memory/constitution.md`.

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

## 10. Filter portfolio + opt-in modes

The framework runs **6 PM-stage filters** in this order (FR-012 chain):

```
A3 (momentum) → spec 006 (bear-sector-symmetry) → spec 003/003.5 (contrarian gate) →
spec 004 (sector momentum) → spec 007 (forward-catalyst) → spec X-1 (institutional rotation)
```

Most filters default to **shadow mode** (record `would_fire` decisions but don't mutate ratings) when the empirical evidence base is thin. Once you accumulate ≥30 propagates worth of shadow-mode observations and the would-fire pattern matches your expectations, you flip to **active mode** to start suppressing commits.

### 10.1 Defaults summary (after 2026-05-07)

| Filter | Default mode | Default threshold | When it fires (active) |
|---|---|---|---|
| A3 momentum | active | -5% (30d) | Suppress UW/Sell when ticker down >5% in prior 30d |
| Spec 006 bear-sector-symmetry | off | None | Suppress UW/Sell when ticker outperformed sector >+5% |
| Spec 003 contrarian gate | active | 80th percentile | Suppress Buy/OW when bull_keyword_count percentile high |
| Spec 003.5 sector fallback | enabled | N≥20 floor | Falls back to sector pool when per-ticker history thin |
| Spec 004 sector momentum | off | None | Suppress Buy/OW when sector ETF down >threshold% |
| Spec 007 bull (forward catalyst) | active | 0.60 | Suppress Buy/OW when LLM-extracted bull_priced_in score high |
| Spec 007 bear (forward catalyst) | shadow | 0.50 | Suppress UW/Sell when LLM-extracted bear_priced_in score high |
| Spec 008 Hybrid C calendar boost | off | window=14 / mag=0.5 | Multiplies Spec 007 bull score near earnings |
| **Spec X-1 C-4 institutional rotation** | **shadow** | **-0.05** | **Suppress UW/Sell when top 10 institutional holders' net pctChange < -5%** |

### 10.2 Spec X-1 shadow-mode workflow (newest filter)

After PR #93 (2026-05-07), Spec X-1 ships at **default-shadow bear-side**. State logs at `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json` will contain:

```json
{
  "forward_catalyst": {
    "...": "...other Spec 007 fields...",
    "institutional_rotation": {
      "net_rotation_pct": -0.0823,
      "outflow_threshold": 0.05,
      "bear_mode": "shadow",
      "bull_mode": "off",
      "would_fire_bear": true,
      "fired_bear": false,
      "pre_rating": "Underweight",
      "post_rating": "Underweight"
    }
  }
}
```

**Watch for**: rows where `would_fire_bear=true` AND `fired_bear=false` (shadow-mode observation). After ~30 such rows accumulate, review whether the would-fire pattern matches your judgment — if yes, flip to active mode.

### 10.3 Flipping Spec X-1 to active mode

Edit your experiment's `PARAMS.json` (or pass via CLI `--config-override`):

```json
{
  "institutional_rotation_bear_mode": "active",
  "institutional_rotation_outflow_threshold": 0.05
}
```

Or via Python:

```python
config["institutional_rotation_bear_mode"] = "active"
```

After flipping, `fired_bear=true` rows will appear in state logs AND the rendered Portfolio Manager output will show "Hold" instead of the original UW/Sell + a `[C-4 Institutional Rotation filter]` note explaining the suppression.

### 10.4 Disabling a filter entirely (zero overhead)

To fully turn off Spec X-1 (no yfinance fetch, no state annotation):

```json
{
  "institutional_rotation_bear_mode": "off",
  "institutional_rotation_bull_mode": "off"
}
```

The same pattern works for any filter — set its `_mode` config keys to `"off"`. A3 uses `uw_momentum_filter_threshold = None` instead.

### 10.5 Re-validation cadence (Spec X-1 specific)

Spec X-1's empirical evidence base used Q4 2025 13F data (cohort cutoff 2026-02-14). Q1 2026 13Fs land **~2026-05-15**. After that date, re-run:

```bash
python scripts/forward_catalyst_class4_retrospective.py --cohort-cutoff 2026-05-15
python scripts/forward_catalyst_class4_vs_spec007_overlap.py
```

If either gate drops below the v1.4.0 / v1.4.3 thresholds (discrim ≥+5pp / hit ≥60% / Δα ≥+0.5pp standalone; ≥1 of 3 v1.4.3 criteria for additive), ablate the filter to `"off"` default mode pending investigation. Spec X-1 SC-009 codifies this requirement.

### 10.6 Auditing all filter fires across propagates

To survey which filters fired across your entire log corpus (useful for behavioral-additive analysis per Constitution VIII v1.4.6):

```bash
python scripts/behavioral_additive_sweep.py
```

Outputs per-mechanism + per-ticker counts of would-fire decisions. Use to identify operator-relevant patterns (e.g., "Spec X-1 would-fire on 8 of my 30 propagates this month — time to flip to active?").

## 11. Troubleshooting

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
pytest                                  # full suite (placeholder API keys auto-injected) — currently 825 passing
pytest -m unit                          # fast subset
pytest tests/test_checkpoint_resume.py  # one file
```

**Vendor routing safety**: `tests/test_interface_routing.py::test_every_categorized_tool_has_impl_for_default_vendor` asserts every (TOOLS_CATEGORIES tool, default vendor) pair has an impl. Added 2026-05-03 evening after experiment 008 v1 errored on 22/22 runs because `get_insider_transactions` was in `news_data` category but had no `exa` impl. Run this test before adding any new tool to a category, or you'll hit the same class of bug at runtime.

**Smoke-test just the structured-output decision agents** (cheap — no full propagate):
```bash
python scripts/smoke_structured_output.py anthropic
```

## 12. What NOT to touch

- `<!-- ENTRY_END -->` separator in `memory.py` — load-bearing.
- `backend_url` default of `None` — was the cause of the cross-provider URL leak bug.
- `create_msg_delete()` placeholder `HumanMessage("Continue")` — Anthropic requires a non-empty message after `RemoveMessage`s.
- File I/O without `encoding="utf-8"` — Windows will break.

## 13. Files you'll edit most

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
