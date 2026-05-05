# ROADMAP — TradingAgents-lab

_Forward-looking exploration map. Updated 2026-05-04 late-evening (post-Spec 001 Phase 4 live-validation, post-3-period NVDA cross-validation, post-Phase D substrate exploration)._

This is a research playground, not a product. The roadmap is directions for exploration, not delivery milestones. Per Constitution Principle V ("Steal Liberally"), cross-pollination from sibling projects in the portfolio is a primary driver — many ideas listed here originate elsewhere.

For findings to date see [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). For per-experiment summaries see [`findings.md`](findings.md). For the original idea backlog see [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md).

---

## Current state (2026-05-04 late-evening)

- **22 completed experiments** + cross-experiment horizon sweep + 3-period NVDA cross-validation + per-ticker breakdown + A1/A3 diagnostics + A3 forensics + Phase D substrate exploration + Phase C reasoning_evidence wiring + Spec 002 signal-lifecycle (Phases 0-2.5) + Spec 001 bots-architecture (Phases 1-5)
- A3 mean-reversion suppression filter productionized (`tradingagents/agents/utils/momentum_filter.py`, gated by `config["uw_momentum_filter_threshold"]`); validated as correctly inert on regime-mismatch failures (007 INTC half)
- Constitution **v1.2.2** with Principle VII (Calibrated Abstention is a Valid Output) + Replicability-scope (bucket vs date) + Cross-period-scope (realized α is period-conditional unless multi-period validated) clarifications
- Cost-tier ladder shipped (T1 ≤$5 / T2 $5-30 / T3 $30-100 / T4 >$100); end-to-end exercised on 008
- **785 tests passing** (was 501) — Spec 002 signal-lifecycle + Spec 001 Phases 1-5 added; routing-mismatch regression test still in place
- **Load-bearing claim recovered post-NVDA-Q3**: framework's Buy/OW commits at 21d show **+1.23% α (n=71, ~61% hit)** — POSITIVE AT MODERATE CONFIDENCE. Three-period NVDA: Q3 2025 +0.80% (60% hit), Q4 2025 -0.47% (22% hit), Q1 2026 ~+3.5% (~80% hit). 2 of 3 periods positive. Reasoning_evidence Bayesian posterior trajectory: 0.64 → 0.52 → **0.63** (recovered)
- UW failure mode is **regime-asymmetric, not uniformly anti-calibrated** — UW on bear-correct tickers directionally appropriate; UW on bull-regime tickers drives aggregate anti-calibration
- **Phase D substrate finding**: framework went 30pp more Hold-heavy on XLK vs same-date NVDA — decision architecture portable across substrates; commit calibration single-stock-prompt-tuned
- **Spec 001 Phase 4 live-validated**: `bot_models = {bot_id: model_name}` per-bot LLM routing works end-to-end against real Anthropic; wrapper-vs-LLM bug caught by integration tests before live propagate spent money
- **No experiments running** — most recent: experiment 007 Phase 4 smoke (Scenario A clean)

---

## Active branch — Spec 001 Phase 4 landed, infrastructure complete (2026-05-04 late-evening)

**Most recent shipping work**:
- **Spec 001 Phase 4 (per-bot LLM model routing)**: `BotLLMFactory` shipped + wrapper-vs-LLM bug caught by integration tests + live-validated by experiment `2026-05-04-007-phase4-bot-models-smoke` (NVDA Q1 2026, market analyst on Sonnet, all other bots on defaults; clean Scenario A). Operator can now mix models per bot via `config["bot_models"]`.
- **Spec 001 Phases 1, 2, 3, 5**: Shadow aggregator (42.3% direction match — fails SC-001), weight tuning (overfits, train +0.079 → test -0.062), convergence shortcut (0% fires at spec defaults), opt-in bots-mode wired. Honest "this approach has limited ceiling" findings logged.
- **Spec 002 Phases 0-2.5**: signal registry + SQLite cache + 14 featurizers (sentiment, bull/bear keywords + bigrams, hedge density, conviction, numeric mentions, percent/dollar mentions, etc.) + drift detection + counterfactual analysis + multi-horizon evaluation (5d/10d/21d/90d). 740 backfilled cache rows from existing state logs.
- **Phase D substrate exploration**: XLK Q1 2026 (Scenario B — substrate-different commit behavior), multi-sector Phase D, XLE Q4 2025 micro. Decision architecture portable; commit calibration substrate-specific.
- **Phase C reasoning_evidence wiring**: `tradingagents/agents/utils/second_opinion.py` ships with asymmetric handling per Q5 (agreement → augment, disagreement → flag for review). Default disabled; ~$0.10/run forward when enabled.
- **NVDA Q3 2025 cross-period micro** (experiment 001): Scenario A — posterior recovers from 0.52 to 0.63 after 2-of-3 periods positive.

**No experiment currently selected**. Possible next directions per the open questions table below.

---

## Sequenced phases of exploration (post-Opus)

### Phase B — out-of-sample validation (priorities reordered post-Q3-recovery)

After NVDA Q3 2025 the load-bearing claim recovers (2 of 3 periods positive; posterior 0.52 → 0.63). Phase B priorities now:

- **B-priority 1 — A3 filter forensics**: **DONE** (`claudedocs/a3-filter-forensics-007.md`). Filter validated as correctly inert on the regime-mismatch failure mode; no tuning needed from 007 evidence.
- **B-priority 2 — cross-period validation**: **DONE as experiment 008**. Result: Scenario C (signal collapses on shifted period). Bayesian posterior 0.64 → 0.52. Reframe applied to RESEARCH_FINDINGS + Constitution v1.2.2.
- **B-priority 2b — third cross-period (Q3 2025) at T2 ~$10**: **DONE as experiment `2026-05-04-001-nvda-q3-2025-micro`**. Result: Scenario A — posterior climbs back to 0.63. Q4 2025 confirmed as the outlier; Q1 2026 is consistent with Q3 2025.
- **B-priority 3 — bear-correct ticker pilot (XOM, PFE)**: lower priority. Adds fresh bear-side data points but doesn't directly address the load-bearing period-conditional question. ($15, ~12h, T2)
- **B-priority 4 — same-date rerun-variance quantification**: 005-vs-007 NVDA non-replication suggests rerun variance is non-trivial. n=3 reps on the same 10 NVDA dates with current config would quantify the bucket-ratio variance bands. ($15, ~12h, T2 — would be the formal evidence backing Constitution VII Replicability-scope clarification)
- **B-priority 5 — model-swap matrix**: Sonnet vs Opus vs GPT-5.4 vs Gemini 3.x on the same grid. Tests whether the period-conditional realized α is a model property or a substrate property (does Sonnet show the same Q1-vs-Q4 sign flip?). Now also enabled by Spec 001 Phase 4 per-bot routing — could mix models within a single grid. ($20-40, T2/T3)
- **B-priority 6 (new) — Phase 4 cost-tier validation**: matched-baseline n=10+ run with `bot_models` set to bump `fundamentals` (heaviest analyst) → Opus while keeping the rest on Haiku. Tests whether per-bot model swaps shift rating distribution beyond known mode-collapse behavior. Phase 4 is wired and live-validated at n=1; the cost-savings story needs n≥10 to characterize. ($5-10, T2)

### Phase C — operational integration

The framework currently outputs ratings. With the A3 filter wired in, it could output more:

- **`reasoning_evidence` second-opinion in PortfolioManager** with asymmetric handling per Q5 (agreement → augment confidence, disagreement → flag for review). **DONE as `tradingagents/agents/utils/second_opinion.py`** + 29 unit tests + Phase C smoke test (`experiments/2026-05-04-005-phase-c-smoke-test/`). Default disabled; opt-in via `config["second_opinion_enabled"] = True`. ~$0.10/run forward when enabled.
- **Bias auditor** running `reasoning_detect` over saved bull/bear debates — produces a per-experiment bias profile (confirmation, anchoring, recency, overconfidence). Validates A1's hedge-words finding programmatically. (2-4h)
- **Counterfactual analyzer** running `reasoning_counterfactual` on Hold-α extreme dates as part of every analysis pass — auto-builds the "what if framework had committed?" narrative for FINDINGS. **PARTIAL** — `tradingagents/signals/counterfactual.py` (Spec 002 Phase 2) ships `run_counterfactual` + `hold_all_uw` / `hold_all_ow` / `invert_all_commits` but is not yet wired into per-experiment auto-analysis. (1-2h to wire)

### Phase D — substrate exploration (different problems, same framework)

Equities are the chosen substrate because they're cheap to evaluate. The framework's findings (calibrated abstention + 21d directional skill) might generalize to other domains:

- **Crypto pairs** — different volatility regime, different news ecosystem
- **FX pairs** — macro-driven, different debate texture
- **Sector ETFs** — debate over whole-sector trends instead of single stocks
- **Options-implied volatility** — debate over IV regime instead of price direction
- **Sports betting / prediction markets** — same ground-truth structure (forward outcome, benchmark to compare against), totally different evidence base. Genuinely tests generalization.

### Phase E — architectural variants

The current framework is one specific choice (4 analysts → bull/bear debate → research manager → trader → 3-persona risk debate → portfolio manager). Other architectures worth testing:

- **No-debate baseline** — analysts → portfolio manager directly, no bull/bear stage. Variant of single-call baseline but using full framework infrastructure
- **Inverted-role debate** — analysts argue against their own report's lean (forces evidence steel-manning)
- **N-perspective generation via `reasoning_divergent`** — replace bull/bear with N divergent perspectives, then synthesize
- **Tree-search exploration** — `reasoning_tree` generates branches of investment theses, scored, pruned, finalized. Replaces linear debate with branching
- **Graph-of-thoughts pipeline** — `reasoning_graph` structures the analyst → debate → synthesis chain as a DAG with intermediate aggregation nodes

---

## Cross-pollination opportunities (Principle V — Steal Liberally)

Patterns from sibling projects worth porting:

| From | Pattern | Where it'd go in TradingAgents-lab |
|---|---|---|
| **agent-harness-v2** | Event sourcing — every agent action emits a structured event; analysis queries the event log | Replace per-experiment CSV + state-log JSON with a single event log; enables fine-grained pattern detection across runs |
| **agent-harness-v2** | Structural enforcement / gates with DENY/WARN findings | Already partially done (EH-2 rating distribution gate). Could extend: a `pre_pm` gate that checks bull/bear evidence balance before allowing PM to commit |
| **agent-harness-v2** | Knowledge digestion + antibodies | Periodic synthesis of "what we know about UW failure modes" auto-generated from accumulated state logs |
| **ladybird** | Sentinel pattern — separate-process enforcement plane | The momentum filter is currently in-process; a Sentinel could run regime checks asynchronously and override decisions externally |
| **battlecode2026 ratbot6** | Value function over assigned roles, structured signaling | Each analyst has an explicit value function for what counts as "good evidence" in their domain; signaling lets analysts coordinate without full debate |
| **battlecode2026 ratbot6** | Unified value function architecture | Replace prose-output analysts with numeric feature emitters; aggregation via weighted sum, not LLM synthesis. Cheaper, interpretable, gradient-descent-tunable |
| **battlecode2026 ratbot6** | Squeak (structured signaling between bots, compressed broadcasts) | Analysts emit `{bullish: 0.7, key_risks: ["memory_chip"], confidence: 0.6}` instead of 10K-token prose. Synthesis aggregates structured fields. Major token savings |
| **battlecode2026 ratbot6** | Bytecode budget tracking + Profiler | Per-analyst token-spend tracker; warn when analyst exceeds budget. Enforces cost discipline without manual inspection |
| **battlecode2026 ratbot6** | Explicit state machine (BabyRatStateMachineTest) | Make `state.debate_phase` explicit instead of regex-detecting "current_response.startswith('Bull')". Easier to test, easier to add new debate variants |
| **battlecode2026 ratbot6** | Self-removal after idle threshold (attackers suicide after 100 rounds) | If an analyst's report is below a content threshold, skip it — don't pay for downstream debate on empty input. Aligns with Constitution VII |
| **battlecode2026 ratbot6** | Pre-computed pathfinding routes (Pathfinding caches) | Decision-rule shortcuts for common patterns ("earnings beat + uptrend → default OW unless explicit bear evidence"). Avoids LLM call when rule fires |
| **bruno-swarm** | Multi-agent coordination patterns, abliteration for specialization | Specialize each analyst via abliteration on their report style; test if specialization improves signal vs the current general-purpose Sonnet calls |
| **mcp-reasoning** | 15+ reasoning modes (linear, tree, divergent, reflection, decision, evidence, mcts, graph, counterfactual, …) | Phase C operationalization items above are direct applications |
| **mcp-reasoning** | Self-improvement system (4-phase: monitor → diagnose → execute → learn) | Auto-detect when calibration drifts (e.g. a new ticker added to the universe) and trigger re-analysis |
| **branch-thinking / logic-thinking** | Structured reasoning tools | Alternative substrates for the synthesis stage |

---

## Deferred lines worth picking up later

### From the in-session code-improvement list

| # | Item | Effort | Note |
|---|---|---|---|
| 4 | Test coverage on framework innards: `anthropic_client.py` (0%), `openai_client.py` (0%), `graph/setup.py` (12%), `graph/conditional_logic.py` (21%) | hours | These are the load-bearing modules with the lowest coverage. Smoke tests with mocks would catch regressions before they hit propagate() |
| 5 | `PriceCache` helper class to standardize per-ticker yfinance fetch + date-padding boilerplate across analysis scripts | 1h | Eliminates ~15 lines of identical setup per script; centralizes the date-padding logic that currently varies subtly |
| 6 | Constitution Principle V enforcement — commits should cite which sibling-project technique they came from | philosophical | Either drop the principle or actually do it |
| - | Drop the 215 → ~30 ruff baseline by sweeping with `__all__` protections in place | ~1h | Most are stylistic modernizations (Optional → X \| None, etc.). Cosmetic but improves signal-to-noise on linter output |

### From docs/EXPERIMENT.md (~50 ideas)

- Most Tier 1/2 ideas not yet attempted (the 11 completed experiments cover only MR-1, WC-12 variants, MR-2, MR-3, EH-2, brave/exa news swaps, single-call baseline)
- Worth a re-read after Opus lands to mark which are obviated by current findings vs which still discriminate

---

## Open data questions (post-007)

These need new experiments to answer; no amount of analysis on existing CSVs will resolve them.

| Question | Proposed experiment | Cost | Status |
|---|---|---|---|
| Does the 21d bull lift hold at n=100+? | Q3 2025 third cross-period (T2 $10) → if positive, posterior recovers | $30 | **partial-resolved — n=71 cross-period evidence; +1.23% mean α; 2-of-3 periods positive; posterior 0.63** |
| Is the lift period-specific or persistent across calendar windows? | 008 + Q3 micro done: Q1 2026 + Q3 2025 positive, Q4 2025 negative outlier. | $10 + $5 | **resolved (3-period)** — moderately period-stable; Q4 2025 is the outlier |
| Is the lift ticker-class specific (mega-cap tech vs others)? | Sector-stratified pilot — Phase D XLK + multi-sector + XLE done | $20 | **partial** — Phase D shows decision architecture portable, calibration substrate-specific |
| Does the A3 filter generalize off-sample? | Already validated by 007 forensics for regime-mismatch case; off-sample mean-reversion test still open | $10 | **partial** |
| Does Opus / GPT-5.4 / Gemini 3.x show the same 21d shape? | Model-swap matrix — now enabled by Spec 001 Phase 4 per-bot routing | $20-40 | partial — Sonnet + Opus done, others open |
| Is the bear-correct-ticker UW signal robust beyond AAPL + INTC? | XOM or PFE 10-date pilot | $15 | open (B-priority 3) |
| Does the framework predict longer horizons (60/90d) where 5d failed and 21d worked? | Re-aggregate current data + extend window with future price data (60-day wait) | $0 + time | **partial** — Spec 002 Phase 1.5+ multi-horizon eval (5d/10d/21d/90d) shipped; bear_bigram_count IC = +0.457 at 90d |
| Does same-prompt rerun-variance dominate the signal at the date level? | n=3 reps on the existing 10 NVDA dates with current config — formalizes the 005-vs-007 finding | $15 | open (B-priority 4) |
| Does spec 002 (signal-lifecycle) IC measurement reveal which signals are noise? | Build signal-lifecycle pipeline + run on saved state logs | $0 build + $0 run | **resolved** — Spec 002 Phases 0-2.5 shipped; first IC measurement: final_trade_decision IC = -0.172 at 21d, n=153; strongest IC: bear_bigram_count = +0.457 at 90d |
| Does per-bot LLM model routing (Spec 001 Phase 4) shift rating distribution beyond mode-collapse? | n=10+ matched-baseline run with `bot_models = {"fundamentals": "claude-opus-4-7"}` | $5-10 | open (B-priority 6, new) |

---

## How to use this doc

When a phase fires (e.g. Opus result lands), update the **Active branch** section with the chosen sub-branch and what experiments / builds it triggered. Move completed phase items to RESEARCH_FINDINGS or `findings.md` as their results are written up. Add new exploration ideas to the appropriate phase as they surface — particularly the cross-pollination table when a sibling project ships something new worth porting.

This doc lives at the root with FINDINGS / RESEARCH_FINDINGS / README so anyone (including future you) can scan the directional state of the project from the top-level tree.
