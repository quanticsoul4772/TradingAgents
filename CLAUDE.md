# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`tradingagents-lab` is a personal experimental fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) v0.2.4, repurposed as a research playground for studying multi-agent LLM debate dynamics. Equity-decision-making is the *substrate* (cheap objective ground truth), not the goal.

**Primary research question**: what structural conditions cause role-based multi-agent LLM debate to collapse to moderate ratings, and what enforcement mechanisms (or alternative architectures) would prevent that collapse?

## Read the headline finding first

After 24 experiments + cross-experiment horizon sweep + per-ticker breakdown + Opus 4.7 model swap (NVDA + AAPL) + Opus 30-pair mixed basket + 3-period NVDA cross-validation (Q1 2026, Q4 2025, Q3 2025) + Phase D substrate exploration (XLK + multi-sector + XLE) + Phase C reasoning_evidence wiring + Spec 002 signal-lifecycle pipeline + Spec 001 bots-architecture (Phases 1-5) + Spec 003 analyst-stage contrarian gate (default-on @80%) + Spec 003.5 sector-baseline fallback + Spec 007 forward-catalyst gate (bull-active, bear-shadow) + Spec 008 Hybrid C calendar boost + **SC-003 50-ticker signal-at-scale validation (2026-05-06, Scenario B)** + **Spec 008 SC-009 live A/B ablation 2026-05-07 (36/36 rows COMPLETE; PRELIMINARY PASS-by-non-counterexample; recommend SHADOW-MODE-FIRST for v2 default-on flip)** + **bear-side mechanism class survey from PR #22 CONCLUDES (6/6 evaluated; C-4 institutional ownership delta is SOLE spec-eligible — standalone gate @ n=12 + v1.4.3 additive overlap @ +8.06pp Δα vs Spec 007)**, the architectural conclusion is captured in **`RESEARCH_FINDINGS.md`**. Forward roadmap in **`ROADMAP.md`**.

> At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls (Buy/OW/UW/Sell) are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) produce **+1.23% mean alpha across n=71 cross-experiment commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE**. Three-period NVDA cross-validation: Q3 2025 +0.80% (n=10, 60% hit), Q4 2025 -0.47% (n=9, 22% hit), Q1 2026 ~+3.5% blended (n=15, ~80% hit). Two of three periods positive — **Q4 2025 is the negative outlier, not Q1 2026 as 008 alone suggested**. Reasoning_evidence Bayesian posterior on stable-cross-period-signal: 0.64 → 0.52 → **0.63** (recovered after Q3 evidence). **SC-003 50-ticker validation (2026-04-03 single date, full sector coverage): bullish bucket +5.96% mean α at 21d (n=15, hit rate 53%) — confirms the signal generalizes to a broader universe at aggregate magnitude nearly 5× the 9-ticker headline, but per-sector breakdown shows the signal is structurally tech-concentrated (Tech n=7 +17.80% mean; Financials n=5 -7.07% on bullish picks). Scenario B per HYPOTHESIS decision tree.** Bearish commits are regime-asymmetric, not uniformly anti-calibrated. Hold ≈ 0% median at every horizon (with one SC-003 exception: 50-ticker Hold mean -3.87% — possibly 21d-window-specific). **Mode-collapse direction is a function of (model × ticker × regime × prompt)**: Sonnet over-abstains on bull tickers AND over-commits-bearish on bear tickers; Opus discriminates per-ticker. **Bucket-level claims replicate; date-level and realized-α claims do not** — 005's NVDA 10/10 OW becomes 6/10 OW + 4 Hold on the same dates in 007; per-ticker bucket ratios hold across reruns and across periods, but realized α is period-conditional. The A3 momentum filter is correctly inert on regime-mismatch failures (validated by `claudedocs/a3-filter-forensics-007.md`). Phase D substrate test: framework went 30pp more Hold-heavy on XLK vs same-date NVDA — **decision architecture is portable across substrates; commit calibration is substrate-specific (single-stock-prompt-tuned)**.

This is encoded in **Constitution Principle VII (Calibrated Abstention is a Valid Output)** added 2026-05-03 then re-amended after 006. Any new structural change that reduces Hold rate must justify in HYPOTHESIS.md why the additional commits would be calibrated rather than noise, at what horizon, and with what directional asymmetry expectation.

## Read the constitution first

The design is governed by `.specify/memory/constitution.md`. Before non-trivial changes, read:

1. `.specify/memory/constitution.md` — **eight** core principles (Save Everything, One Experiment Per Change, Stay Cheap, No Production Claims, Steal Liberally, Spec Before Structural Change, **Calibrated Abstention is a Valid Output**, **Retrospective Before Spec for Backward-Looking Price Filters** — added 2026-05-06 v1.3.0; **extended in v1.4.0 (2026-05-06 later) with a Forward-catalyst-class validation gate** after Class 3 Opus retrospective DECISIVE PASS unblocked spec 007; **v1.4.1 (2026-05-06 evening) appended "Spec ships its retrospective + verdict" sub-section to Principle VI** codifying the pattern today's 5 retrospectives demonstrated). The principles are constraints, not aspirations.
2. `RESEARCH_FINDINGS.md` — project-level synthesis across all 24 experiments + the 5 open questions with their reasoning-tool-derived priors and empirical answers, plus Spec 001 (bots architecture) Phases 1-5 + Spec 002 (signal lifecycle) Phases 0-2.5 + Spec 003 (analyst contrarian gate) Phases 1+2 results, including the 4 validated lines of evidence behind finding #4 (corpus IC + strict-prior + within-bullish-subset + SC-002 fresh-data reproduction).
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

**Baseline** (post-2026-05-08 mypy sweep): ruff = **0 errors** (down from 305 at scaffolding install — see commit `a0ec447`); mypy = **0 errors** (down from 175 → 126 → 0 across three sweeps). The 2026-05-08 sweep (PRs #117–#129) cleared 124 errors in 13 PRs: implicit-Optional widening, helper signature alignment, dict-invariance annotations on the LLM-client `llm_kwargs` dicts (which CLAUDE.md previously characterized as "complex / deferred / needs upstream stubs" — actually fixed by one `dict[str, Any]` annotation per file, see PR #128), TypedDict receiver widening for `TradingAgentsConfig`, and `types-requests` stub addition (PR #129). Net-new code must keep both ruff AND mypy at zero and should use the typed `get_config()` return for config access.

**Test coverage** (as of 2026-05-06 spec 007 merge / `v0.7.0-spec-007` tag): **1022 tests passing** (was 852 → 984 → 1022 across the 2026-05-06 research-burst day; +170 net), 81%+ project coverage. Anthropic + OpenAI clients ~95%, all 4 analyst factories + 5 debate-agent factories 100%, graph/setup.py 100%, conditional_logic.py 100%, trading_graph.py 88%, dataflows/interface.py 98%. New since 2026-05-04: Spec 003 contrarian gate (30 unit tests for `tradingagents/signals/contrarian_gate.py`); Spec 002 within-ticker IC integration (8 tests for the methodology fix that surfaces Simpson's-paradox features automatically); analyzer counterfactual-integration contract (2 tests). Spec 002 signal-lifecycle (Phases 0-2.5) at ~95%, Spec 001 bots-architecture (Phases 1-5) including Phase 4 BotLLMFactory live-validated, Spec 003 contrarian gate (Phases 1+2) live-validated end-to-end (SC-001 + SC-002). Routing-mismatch regression test (`tests/test_interface_routing.py::test_every_categorized_tool_has_impl_for_default_vendor`) added 2026-05-03 after experiment 008 caught the `get_insider_transactions × news_data × exa` mismatch.

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

python scripts/analyze_backtest.py <csv> --holding-days 21 \
    --counterfactual-md <out.md>
# → Standard analyzer + counterfactual auto-analysis (spec 002 Phase 2
#   wired into ANALYSIS.md generation). Adds 3 standard counterfactuals
#   (hold-all-uw, hold-all-ow, invert-all) showing alpha delta vs
#   actual. Reuses the alpha cache the analyzer already populated;
#   no extra yfinance fetches. The --counterfactual-md flag writes
#   per-rule changed-pairs tables for paste-into-ANALYSIS.md use.
#   Disable with --skip-counterfactual.

python scripts/daily_signals.py --tickers tickers.txt
# → Operator-facing daily signals product (2026-05-05 onwards).
#   Runs propagate(ticker, today) over the watchlist with all empirical
#   filters ACTIVE by default (A3 momentum filter ON, Spec 003
#   contrarian gate active mode), writes a markdown digest filtered to
#   actionable 21d-horizon bullish recommendations. Hold suppressed by
#   default (calibrated abstention per Constitution VII); pass
#   --include-all to show Hold/UW/Sell. Pass --shadow-gates to run
#   gates in observation-only mode. Estimated cost ~$0.40 per ticker
#   (Opus + Haiku); 5-10 ticker watchlist ≈ $2-4/day.
#   Add --emit-csv <path> to also write a paper_trade.py-consumable
#   signals CSV (Spec 002).

python scripts/paper_trade.py replay \
    --signals-csv experiments/<id>/results.csv \
    --watchlist <txt> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --yes
python scripts/paper_trade.py step --signals-csv ~/.tradingagents/paper/today.csv
python scripts/paper_trade.py status
# → Spec 002 paper-trading harness. Zero LLM cost (pure signal consumer).
#   replay = deterministic backtest; step = single-day, idempotent
#   (cron-able); status = read-only inspection. State at
#   ~/.tradingagents/paper/<id>.json + <id>.events.jsonl. Default
#   policy: 21d window, 8 max positions, 10% per slot, 50% sector cap,
#   5 bps slippage, SPY benchmark. See docs/PAPER_TRADING.md.
```

**News vendor** (per `--news-vendor`):
- `exa` (default; requires `EXA_API_KEY`) — true historical date filter via startPublishedDate/endPublishedDate
- `alpha_vantage` — alternative for users with that subscription

`yfinance` and `brave` news vendors were removed 2026-05-03; `yfinance` the package is still used for stock prices, technical indicators, and fundamental data.

**Empirical filters (default ON as of 2026-05-06)**:

- **A3 momentum filter** — `config["uw_momentum_filter_threshold"]` defaults to `-5.0`. Suppresses UW/Sell commits to Hold when the ticker is already down >5% over the prior 30 trading days (mean-reversion zone). Wired in `tradingagents/agents/managers/portfolio_manager.py` via `tradingagents/agents/utils/momentum_filter.py`. Forensics (`claudedocs/a3-filter-forensics-007.md`) confirm the filter correctly stays inert on regime-mismatch UW commits (e.g. INTC was UP +11-33% at 4 of 6 UW dates). Corpus retrospective (`scripts/uw_suppression_filter.py`) showed +0.70pp Δα at this threshold across the 43-UW-commit corpus, positive at every threshold tested in the -5 to -10% range. Set to `None` in PARAMS.json to ablate.

- **Spec 003 contrarian gate** — `config["contrarian_gate_mode"]` defaults to `"active"` at 80th-percentile threshold + N≥20 history floor (FR-004). Downgrades Buy/Overweight to Hold when the propagate's `bull_keyword_count` exceeds the 80th percentile of the most recent 20 cached values for that ticker. Corpus retrospective (`scripts/contrarian_gate_retrospective.py`) showed +6.46% cumulative Δα at 21d at the production-default floor; the FR-004 amendment to N≥20 is load-bearing — at the permissive N≥5 floor the gate would HURT alpha by -24.87%. Set to `"off"` (or `"shadow"` for measurement-only) in PARAMS.json to ablate.

- **Spec 003.5 sector-baseline fallback** (`specs/003-sector-baseline-gate/`, 2026-05-06) — when per-ticker history is below the FR-004 N≥20 floor, the gate now falls back to a pool aggregated across all same-sector tickers (sector membership from `tradingagents/paper/sectors.py` yfinance cache). Same threshold + target + modes preserved. New annotation field `gate_baseline` ∈ {`"per_ticker"`, `"sector"`, `"none"`} tells operators which baseline fired. Default-on; ablation via `contrarian_gate_sector_fallback_enabled = False`. Empirical motivation (`claudedocs/sc003-financials-gate-check-2026-05-06.md`): SC-003 Financials investigation showed 4 of 5 losing OW commits had zero per-ticker history → spec 003 gate could not fire by construction. The fallback closes that cold-start-universe gap. **Validation finding** (`claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md`): the fallback also doesn't help on the SC-003 Financials cohort itself, because the Financials losers had MODERATE bull_keyword_counts (sector-rotation mechanism, not within-ticker prose mean-reversion). Spec 004 was created to address that gap.

- **Spec 004 sector-momentum filter** (`specs/004-sector-momentum-filter/`, 2026-05-06) — new module `tradingagents/agents/utils/sector_momentum_filter.py`. Suppresses Buy/Overweight commits to Hold when the ticker's sector ETF (XLK/XLF/XLV/XLE/XLY/XLP/XLI/XLC/XLU/XLRE/XLB per the `SECTOR_ETF_MAP` constant) is in mean-reversion zone (down >threshold% in prior 30 trading days). Analogous to A3 but operating at sector level. Default OFF (`sector_momentum_filter_threshold_pct = None`); operator opts in via PARAMS.json or config override. Filter ordering in PM hook chain (FR-012): A3 → spec 003/003.5 → spec 004. New `state["sector_momentum"]` annotation field with `gate_baseline`-style audit info; persisted via the `_log_state` whitelist. Empirical motivation: spec 003.5 validation identified sector-rotation as the SC-003 Financials failure mechanism. Per Constitution II discipline, default-on flip waits on a corpus retrospective (`scripts/sector_momentum_retrospective.py`, deferred from spec polish phase) showing positive net Δα at the chosen threshold.

- **Spec 006 bear-sector-symmetry filter** (`specs/005-bear-sector-symmetry/`, 2026-05-06; user-facing name "Spec 006" — directory auto-numbered to `005-bear-sector-symmetry`) — new module `tradingagents/agents/utils/bear_sector_symmetry_filter.py`. Suppresses Underweight/Sell commits to Hold when the ticker has outperformed its sector ETF by more than threshold% (default +5%) over the prior 30 trading days (counter-trend bear suppression — sector-relative inverse of A3's per-ticker absolute mean-reversion). Reuses `SECTOR_ETF_MAP` + `_etf_history` from spec 004 (FR-004 — single source of truth). New `_ticker_history` LRU cache (maxsize=128) for the ticker side. Default OFF (`bear_sector_symmetry_filter_threshold_pct = None`); operator opts in via PARAMS.json or config override. Filter ordering (FR-012): A3 → **spec 006** → spec 003/003.5 → spec 004. The two bear filters operate on near-disjoint price-condition cohorts (A3 fires on ticker DOWN absolute; spec 006 fires on ticker UP relative to sector). New `state["bear_sector_symmetry"]` annotation field with 13 fields including `ticker_30d_return_pct`, `etf_30d_return_pct`, `relative_strength_pct`, `would_fire`, `fired`, `pre_rating`, `post_rating`, `skipped`. Persisted via the `_log_state` whitelist. AgentState TypedDict extended (precedent: spec 003 silent-drop bug). Empirical motivation: today's sector-α attribution analysis (`claudedocs/sector-alpha-attribution-2026-05-06.md`) found 18 of 37 bearish commits (48.6%) landed in `ticker_strong` with mean realized α-vs-SPY = +28.02% — a cohort A3 misses entirely. **Corpus retrospective verdict** (`claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md`): SC-008 FAILED at +5% — only 5 of 18 cohort commits fire (target was ≥8) AND net Δα at +5% = -0.71pp (anti-predictive). Filter stays default-off; only +10% threshold is marginally net-positive (+1.30pp on n=7 fires) but still fails the cohort gate. Mirrors spec 004's outcome — backward-looking price filters miss cohorts whose realized α comes from forward catalysts. Constitution II discipline validated again.

- **Spec 007 forward-catalyst-aware contrarian gate** (`specs/006-forward-catalyst-gate/`, 2026-05-06; user-facing name "Spec 007" — directory auto-numbered to `006-forward-catalyst-gate`) — new module `tradingagents/agents/utils/forward_catalyst_filter.py`. **FIRST forward-catalyst-aware filter** in the framework — fundamentally different mechanism class from the 5 backward-price filters above. Invokes an LLM (Opus default) per propagate to score how widely the bull/bear case is already absorbed by the market via the existing analyst reports + bull/bear debate. Bull-side **default-on at T=0.60** (Class 3 Opus retrospective DECISIVELY PASSED Constitution VIII gate: discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp on n=33 fires). Bear-side **default-shadow at T=0.50** per Constitution VIII shadow-mode-first condition (passed criteria 1+2 only; criterion 3 net Δα +0.30pp just below the +0.5pp gate). Filter ordering (FR-012): A3 → spec 006 → spec 003/003.5 → spec 004 → **spec 007 (LAST in chain)**; spec 007 consumes the SAME analyst reports as the prior filters' inputs. Six new `TradingAgentsConfig` keys: `forward_catalyst_bull_mode` / `bear_mode` (Literal[off/shadow/active], defaults active/shadow), `forward_catalyst_bull_threshold` / `bear_threshold` (float, defaults 0.60/0.50), `forward_catalyst_model` (str, default `claude-opus-4-7`), `forward_catalyst_max_rationale_chars` (int, default 2000). Operator opts to Haiku via `forward_catalyst_model = "claude-haiku-4-5"` for cost-sensitive workflows (~10× cheaper but tighter score distribution; documented degradation in spec quickstart). New `state["forward_catalyst"]` annotation field with 16 fields (including `model`, both scores, `rationale`, both thresholds, both modes, would_fire/fired per side, pre/post_rating, skipped, error). Persisted via the `_log_state` whitelist. AgentState TypedDict extended. Adds ~$0.025/propagate Opus cost (~$0.25/day for typical 10-ticker workflow); set BOTH modes to "off" to disable + zero cost (FR-013 escape hatch). **Constitution v1.4.0 amended in same commit** (per FR-015): Principle VIII gets a "Forward-catalyst-class validation gate" sub-section codifying the discrim ≥ +5pp + hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first criteria. Future forward-catalyst filters use this gate.

- **Spec X-1 C-4 institutional rotation filter** (`specs/091-c4-institutional-rotation/`, 2026-05-07; user-facing name "Spec X-1" — directory auto-numbered to `091-c4-institutional-rotation`) — new module `tradingagents/agents/utils/institutional_rotation_filter.py`. **FIRST quantitative-flow bear-side filter** in the framework — fundamentally different mechanism class from the 5 prose-density / LLM-extracted / backward-price / calendar-boost filters above. Suppresses Underweight/Sell commits to Hold when top 10 institutional holders' net pctChange rotation (sum across the 10-row × 6-col DataFrame from `yfinance.Ticker(t).institutional_holders`, LRU-cached maxsize=128) falls below `-outflow_threshold` (default 0.05 fractional = -5%). Bear-side **default-shadow at T_outflow=0.05** per Constitution VIII v1.4.0 small-sample-caution sub-clause (n=12 cohort from PR #75 retrospective: discrim +10.29pp / hit 75.0% / net Δα +5.41pp). Bull-side **default-OFF** (n=1 evidence too thin). Filter ordering (FR-012): A3 → spec 006 → spec 003/003.5 → spec 004 → spec 007 → **spec X-1 (LAST in chain)**; runs LAST per sample-size discipline (smallest evidence base). Four new `TradingAgentsConfig` keys: `institutional_rotation_bear_mode` / `bull_mode` (Literal[off/shadow/active], defaults shadow/off), `institutional_rotation_outflow_threshold` / `inflow_threshold` (float, defaults 0.05/0.05; inflow reserved for future bull-side activation). State annotation extends `state["forward_catalyst"]["institutional_rotation"]` per spec 003/004/006/007/008 precedent (NEW dict NOT created at top level) — 8 fields (`net_rotation_pct`, `outflow_threshold`, `bear_mode`, `bull_mode`, `would_fire_bear`, `fired_bear`, `pre_rating`, `post_rating`); when both modes are off, the sub-dict is NOT added (FR-011 backward-compat). Persisted via existing `_log_state` whitelist (no schema changes to AgentState — `forward_catalyst` already declared). Zero LLM cost (Constitution III T0); ~50-200ms latency on yfinance cache miss. **Constitution VIII v1.4.0 + v1.4.3 gates pre-cleared by PR #75 + PR #77 retrospectives**: standalone PASS at n=12, additive PASS on 2 of 3 v1.4.3 criteria (+8.06pp Δα + +69.23pp hit improvement vs Spec 007 bear union; FP rate +0.00pp FAIL but ≥1-of-3 sufficient). Mechanism class distinction: Spec 007 bear is LLM-extracted semantic reasoning; C-4 is institutional ownership rotation (quantitative 13F flow) — LITERALLY different signal sources. C-4 catches 11 bearish commits Spec 007 entirely misses (mean α +6.16% on `c4_only` cohort, 81.8% hit). SC-009 + SC-010 follow-up gates deferred (Q1 2026 13F refresh ~2026-05-15 + n≥30 live-mode A/B ablation respectively).

**Corpus interpretation note**: experiments dated **before 2026-05-06** were run with both filters OFF unless their `PARAMS.json` explicitly set them on. Experiments dated **on/after 2026-05-06** include both filters by default unless explicitly disabled. When comparing pre- and post-flip experiment results, check each experiment's PARAMS.json to know which baseline applies.

**Paper-trading harness** (Spec 002, 2026-05-06): `scripts/paper_trade.py` provides `replay`, `step`, and `status` subcommands consuming signal CSVs emitted by `daily_signals.py --emit-csv`. State persists at `~/.tradingagents/paper/<portfolio_id>.json` + `<portfolio_id>.events.jsonl` (atomic JSON + append-only JSONL). Default policy: 21-day holding window, 8 max positions, 10% per slot, 50% per-sector cap, 5 bps each-side slippage, SPY benchmark. Zero LLM cost (FR-011/SC-008 — pure signal consumer). SC-001 validation gate: replay over SC-003 reproduces the bullish-bucket mean α within ±150 bps. See `docs/PAPER_TRADING.md` for operator usage; `specs/002-paper-trading-harness/` for the full spec/plan/contracts/tasks bundle.

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

Three independent systems, all rooted under `~/.tradingagents/` (override base with `TRADINGAGENTS_CACHE_DIR` / `TRADINGAGENTS_RESULTS_DIR`):

- **Decision log** (`agents/utils/memory.py`, `TradingMemoryLog`) — append-only markdown at `~/.tradingagents/memory/trading_memory.md` (override with `TRADINGAGENTS_MEMORY_LOG_PATH`). `propagate()` writes a `pending` entry at the end of every run; on the next same-ticker run, `_resolve_pending_entries()` fetches realized return + alpha vs SPY via `yfinance`, generates a one-paragraph reflection, and updates the entry. Only the Portfolio Manager reads memory, and only when entries exist (so empty memory cannot fabricate "past lessons"). `memory_log_max_entries` caps **resolved** entries; pending entries are never pruned. The `<!-- ENTRY_END -->` HTML comment is the hard separator — don't change it (LLM prose can't emit HTML comments).
- **Checkpoint resume** (`graph/checkpointer.py`) — opt-in via `config["checkpoint_enabled"]` / `--checkpoint`. Per-ticker SQLite DBs at `~/.tradingagents/cache/checkpoints/<TICKER>.db` so concurrent tickers don't contend. Thread ID is `sha256("<TICKER>:<date>")[:16]` so same ticker+date resumes, different date starts fresh. Checkpoints are cleared on successful completion. The graph is recompiled with the SqliteSaver only inside `propagate()` and torn back down in `finally`.
- **Paper-trading state** (`tradingagents/paper/state.py`, Spec 002) — JSON state file `~/.tradingagents/paper/<portfolio_id>.json` + append-only JSONL event log `<portfolio_id>.events.jsonl`. State is the materialized portfolio (cash, open positions, closed positions, equity_curve, immutable policy snapshot); event log is the source-of-truth audit trail (entries, exits, skips, marks, data anomalies, idempotency-skip events). Atomic writes via temp-file-rename. Replay invariant: applying events in order to an empty Portfolio reproduces the JSON state byte-identically. The harness has zero LLM cost — it only consumes pre-generated signals from `daily_signals.py --emit-csv` (signal generation cost is operator-incurred separately).

## Conventions

- **Always pass `encoding="utf-8"` to `open()` / `read_text()` / `write_text()`.** Windows defaults to cp1252; this has caused multiple bugs (#543, #550, #576).
- **Don't add try/except to silently swallow errors.** The error-protocol rule from global RULES.md applies: read the message, fix the actual broken thing, don't add fallbacks/graceful degradation that hide failures. Existing fallbacks (e.g., structured-output → free-text) are deliberate and logged.
- **Internal debate agents stay in English** even when `output_language` is set (reasoning quality). Only user-facing agents (analysts, portfolio manager) localize via `get_language_instruction()` in `agents/utils/agent_utils.py`.
- **Preserve exchange-qualified tickers** end-to-end (`.TO`, `.L`, `.HK`, `.T`). `build_instrument_context()` enforces this in agent prompts.
- The CLI's `MessageBuffer` (`cli/main.py`) tracks agent status via `REPORT_SECTIONS`. When adding a new analyst or report field, update both `ANALYST_MAPPING` and `REPORT_SECTIONS` or the progress display will desync.
- Tests must not require real API keys: `tests/conftest.py` autouses placeholder values for every provider env var. New tests that hit live providers belong behind the `integration` marker.
- **When adding new state-level data from a graph node's return dict, declare the key in `AgentState`** (`tradingagents/agents/utils/agent_states.py`). LangGraph's `StateGraph` silently drops undeclared keys from state merges. Spec 001 worked around this by mutating `final_state` post-`graph.invoke()`; spec 003 hit the same issue and fixed it by declaring `contrarian_gate` in the TypedDict. If your node returns `{key: value}` and you don't see `key` in `final_state`, check the schema first.
