# ROADMAP — TradingAgents-lab

_Forward-looking exploration map. Updated 2026-05-06 late-evening (post-**14-work-unit research-burst day; 12 ship-quality units** culminating in spec 008 Hybrid C calendar-boost filter + Constitution v1.4.2 + tag `v0.8.0-spec-008`). Day's arc captured in `claudedocs/research-burst-2026-05-06.md` (canonical meta-retrospective) + CHANGELOG.md [Unreleased] section + RESEARCH_FINDINGS.md "Filter portfolio" section. Late-evening additions: spec 008 Hybrid C bull-only enhancement of spec 007 + spec 009 candidate (bear-inverted Hybrid C) retrospectively SKIPPED + Constitution v1.4.0 → v1.4.1 (spec ships its retrospective) → v1.4.2 (magnitude fungibility for hybrid filters) + meta-retrospective + spec 008.5 latency benchmark closing /speckit.analyze coverage gap._

This is a research playground, not a product. The roadmap is directions for exploration, not delivery milestones. Per Constitution Principle V ("Steal Liberally"), cross-pollination from sibling projects in the portfolio is a primary driver — many ideas listed here originate elsewhere.

For findings to date see [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). For per-experiment summaries see [`findings.md`](findings.md). For the original idea backlog see [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md).

---

## Current state (2026-05-06)

- **24 completed experiments** + cross-experiment horizon sweep + 3-period NVDA cross-validation + per-ticker breakdown + A1/A3 diagnostics + A3 forensics + Phase D substrate exploration + Phase C reasoning_evidence wiring + Spec 002 signal-lifecycle (Phases 0-2.5) + Spec 001 bots-architecture (Phases 1-5) + **Spec 003 contrarian gate (Phases 1+2 + SC-001 + SC-002 + SC-003 50-ticker validated; default-on flipped @80% threshold 2026-05-06)** + **Spec 003.5 sector-baseline fallback (default-on)** + **Spec 004 sector-momentum filter (default-off after retrospective)** + **Spec 006 bear-sector-symmetry filter (default-off after SC-008 FAIL)**
- A3 mean-reversion suppression filter productionized + default-on @-5%/30d (2026-05-06 flip); validated as correctly inert on regime-mismatch failures (007 INTC half)
- **Spec 003 contrarian gate productionized** (`tradingagents/signals/contrarian_gate.py`); **default flipped to active @80th-percentile + N≥20 floor on 2026-05-06** after `claudedocs/contrarian-gate-retrospective-2026-05-05.md` showed +6.46% cumulative Δα at 21d at production-default floor. **Threshold sweep follow-up validated default at 80%** (`claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md`): +0.65pp net Δα across 11 eligible commits; tightening to 85+ doesn't fire; loosening to 75 gives +1.36pp but more incorrect-suppression risk.
- **Spec 003.5 sector-baseline fallback** (`tradingagents/signals/sector_baseline.py`, `specs/003-sector-baseline-gate/`): when per-ticker history is below FR-004 N≥20 floor, gate aggregates across same-sector tickers. Default-on. Closes the cold-start universe gap structurally; doesn't help SC-003 Financials cohort (different mechanism — see Spec 004 finding).
- **Spec 004 sector-momentum filter** (`tradingagents/agents/utils/sector_momentum_filter.py`, `specs/004-sector-momentum-filter/`): suppresses Buy/OW when sector ETF is down >threshold% in prior 30d. Default-off after corpus retrospective (`claudedocs/sector-momentum-retrospective-2026-05-06.md`) showed -0.45pp net Δα across 73 commits at -5% threshold. SC-008 falsified (XLF was -4.54%, suppress 0/5). Ships as operator-opt-in.
- **Spec 006 bear-sector-symmetry filter** (`tradingagents/agents/utils/bear_sector_symmetry_filter.py`, `specs/005-bear-sector-symmetry/`): suppresses UW/Sell when ticker has outperformed sector ETF by >threshold% in prior 30d (counter-trend bear suppression). Default-off after SC-008 FAILED at +5% (5/18 cohort fires; target ≥8) AND -0.71pp net Δα anti-predictive. Ships as operator-opt-in.
- **Spec 005 candidate (per-ticker-vs-sector BULL filter)**: retrospectively SKIPPED before any spec was written (`claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`). Max +0.31pp net Δα across 79 commits, well below Constitution VIII's +1pp gate. Saved 6-8h of empty-spec work.
- Constitution **v1.3.0** with **Principle VIII** (Retrospective Before Spec for Backward-Looking Price Filters) added 2026-05-06 after three same-day retrospective failures. Plus Principles VII (Calibrated Abstention) + Replicability-scope + Cross-period-scope clarifications.
- Cost-tier ladder shipped; end-to-end exercised on 008
- **1022 tests passing** (was 825 → 984 → **1022** across the 2026-05-06 research-burst day; +197 net) — added Spec 003.5 (10+15 tests) + Spec 004 (~29 tests) + Spec 006 (27 unit + 5 PM integration + 2 state-log regression tests) + **Spec 007 (29 unit + 7 PM integration + 2 state-log + 1 default-config + 1 SC-008 integration)**. All 7 filter sides' state-log persistence tests follow the `4c14d0f` precedent. Suite tagged at v0.7.0-spec-007.
- **Load-bearing claim still stands post-NVDA-Q3 + SC-003 50-ticker validation**: framework's Buy/OW commits at 21d show **+1.23% α (n=71, ~61% hit)** in the legacy 9-ticker cohort + **+5.96% mean α (n=15, 53% hit) on the SC-003 50-ticker bullish bucket** (single-date 2026-04-03 — bullish bucket nearly 5× the 9-ticker headline magnitude, but per-sector breakdown shows the signal is structurally Tech-concentrated: Tech n=7 +17.80% mean; Financials n=5 -7.07% on bullish picks). Scenario B per HYPOTHESIS decision tree.
- **5th failure mode discovered (2026-05-06)** — bullish commits underperforming a rising sector (stock-specific α-vs-sector miss). Affects 27 of 79 bullish commits; 88.9% Tech-concentrated. Backward-price-only signals (Spec 005 candidate) cannot catch it; gap remains for forward-catalyst-aware mechanism. See `RESEARCH_FINDINGS.md` "5th failure mode" section.
- **Bearish anti-calibration shock (2026-05-06)** — 18 of 37 bearish commits at +28.02% mean α-vs-SPY in `ticker_strong` cell. A3 misses; spec 006 was built to catch but failed empirically. Largest single-metric anti-calibration finding in the corpus.
- UW failure mode is **regime-asymmetric, not uniformly anti-calibrated** (unchanged; reinforced by today's bearish anti-calibration finding)
- **Phase D substrate finding**: decision architecture portable across substrates; commit calibration single-stock-prompt-tuned
- **Finding #4 four-line-evidence convergence**: market_report bull_keyword_count anti-predicts within-ticker α at 90d. **First validated within-ticker predictor in the corpus.** Operationalized as Spec 003 contrarian gate; default-on @80% threshold validated by 2026-05-06 sweep.
- **No experiments running** — most recent: experiment `2026-05-05-003-signal-at-scale` (50-ticker SC-003 single-date validation). All 2026-05-06 work was retrospective + spec-development; no new propagates.

---

## Active branch — 14-work-unit research-burst day (2026-05-06; tagged v0.8.0-spec-008)

The day expanded through evening + late-evening sessions, ultimately shipping **12 ship-quality units** across **14 distinct work activities**. The post-Spec 007 work units (in commit order on the late-evening session):

20. Spec 007 merge to main + tag `v0.7.0-spec-007` (earlier evening)
21. Forward-catalyst mechanism design doc + pivot (Class 2 options-IV data-blocked → Hybrid C as substitute, commits `ada8ebb` + `25adb67`)
22. Hybrid C retrofit retrospective (`91135eb`) — DECISIVE PASS bull-side at window=14d/magnitude=0.5x; +3.35pp Δα improvement vs Class 3 alone
23. Hybrid C production-config retrospective confirms (`6cc7be9`) — identical numbers (DEFAULT_CONFIG matched retrofit)
24. Constitution v1.4.0 → v1.4.1 (`b470383`) — Principle VI sub: spec ships its retrospective + verdict
25. Spec 008 design bundle (1850+ LOC: spec.md + plan.md + research.md + data-model.md + contracts/ + quickstart.md + tasks.md, branch `007-calendar-boost-filter`)
26. Spec 008 implementation (`1f1ef27`) — calendar_boost.py helper + spec 007 integration + 34 net-new tests
27. Spec 008 live smoke (`d2680d8`) — real Opus + real yfinance, boost > 0 path verified end-to-end ($0.05)
28. Spec 008 merge to main via PR #6 (`6d7e417`) + tag `v0.8.0-spec-008`
29. Spec 009 candidate (bear-inverted Hybrid C) retrospective — SKIP verdict (+0.00pp at every config; PR #7 open)
30. Constitution v1.4.1 → v1.4.2 (PR #8 open) — Principle VIII sub: magnitude fungibility for hybrid filters
31. Meta-retrospective `claudedocs/research-burst-2026-05-06.md` (PR #9 open) — canonical day-end narrative
32. Doc refresh — README + RESEARCH_FINDINGS + CHANGELOG (PR #10 open)
33. Spec 008.5 latency-benchmark amendment (PR #11 open) — closes the 1 coverage gap from /speckit.analyze
34. (this) ROADMAP + claudedocs/SETUP refresh

Full arc captured in `claudedocs/research-burst-2026-05-06.md`. Filter portfolio at `v0.8.0-spec-008`: **8 sides total** (5 default-active, 3 default-off operator-opt-in — see CLAUDE.md "Empirical filters" section + RESEARCH_FINDINGS.md "Filter portfolio status" section).

**Methodology validation**: Constitution v1.4.1 retrospective-first pattern shipped 6 retrospectives today (2 PASS + 4 SKIP) + 1 candidate SKIP. Empirical ROI: ~10-13× wall-clock leverage on the spec invocations that DID launch (5 SKIP outcomes × 6-8h avoided spec cycles = 30-40h saved). Cost asymmetry validated by direct measurement.

## Original active branch — 11-work-unit research-burst day (2026-05-06; pre-Spec 007)

Today's arc (in commit order on main):

1. **Spec 003.5 sector-baseline fallback** (`specs/003-sector-baseline-gate/`, PR #3 merged): when per-ticker history < N=20 floor, gate aggregates across same-sector tickers from the yfinance cache. Closes the cold-start universe gap. 10+15 unit tests. Default-on.

2. **Spec 004 sector-momentum filter** (`specs/004-sector-momentum-filter/`, PR #4 merged): suppresses Buy/OW when sector ETF is in mean-reversion zone. ~29 tests + new SECTOR_ETF_MAP constant covering 11 GICS sectors. SC-008 validation (`claudedocs/spec-004-sc008-validation-2026-05-06.md`) FALSIFIED the motivating premise: XLF was -4.54% (above -5% threshold), filter would suppress 0/5 of SC-003 Financials (not ≥3/5). Corpus retrospective (`claudedocs/sector-momentum-retrospective-2026-05-06.md`) showed -0.45pp net Δα across 73 commits. Default-off; ships as operator-opt-in.

3. **INTC +103%-on-Hold investigation** (`claudedocs/sc003-intc-hold-investigation-2026-05-06.md`): INTC went +103.14% in 21 trading days from 2026-04-03 (driven by April 23 earnings catalyst). Framework rated Hold; calibrated abstention per Constitution VII validated. Surfaced spec 003 default-on as a counter-example: if PM had committed Buy/OW, the spec 003 contrarian gate would have suppressed back to Hold (NVDA + AAPL retrospective evidence is n=2; 1 large counter-example would dwarf cumulative gain).

4. **Spec 003 contrarian gate threshold sweep** (`scripts/contrarian_gate_threshold_sweep.py`, `claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md`): walks 228 propagate state logs in `~/.tradingagents/logs/`, computes per-ticker strict-prior `bull_keyword_count` history, sweeps thresholds 75/80/85/90/95th percentile. 11 of 82 bullish commits eligible (above N≥20 floor + α available). At default 80% threshold: net Δα = +0.65pp. Verdict: **KEEP default-on at 80%** — tightening doesn't help (gate never fires at 85+); loosening to 75% gives +1.36pp but more incorrect-suppression risk.

5. **Sector-α attribution analyzer** (`scripts/sector_alpha_attribution.py`, `claudedocs/sector-alpha-attribution-2026-05-06.md`): walks all 194 commits in the corpus, computes (raw_return, α-vs-SPY, α-vs-sector-ETF) at 21d, cross-tabs sign(α-vs-SPY) × sign(α-vs-sector) into 4 cells. **Surfaced 5th failure mode** (27/79 bullish commits in ticker_weak with -5.34% mean α; 88.9% Tech-concentrated) AND **bearish anti-calibration shock** (18/37 bearish commits in ticker_strong with +28.02% mean α-vs-SPY). Both findings are RESEARCH_FINDINGS-grade; documented in their own sections there.

6. **Spec 006 design bundle** (`specs/005-bear-sector-symmetry/`, full speckit Phase 0+1+2): 1664 LOC across spec.md + plan.md + research.md + data-model.md + 2 contracts + quickstart.md + 31-task tasks.md. Mechanism: when ticker has outperformed sector ETF by >threshold% in prior 30d, suppress UW/Sell to Hold (counter-trend bear suppression).

7. **Spec 006 implementation + retrospective**: ~190 LOC implementation (reuses spec 004's `SECTOR_ETF_MAP` + `_etf_history` LRU cache per FR-004; new `_ticker_history` LRU). Retrospective (`claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md`) ran on 36 valid bearish commits. **SC-008 FAILED at +5%**: 5 of 18 cohort commits fire (target was ≥8). Net Δα at +5% = **-0.71pp anti-predictive**. Default-off; ships as operator-opt-in. Mirrors spec 004's outcome.

8. **Spec 006 merge into main** (commit `4d0401d` --no-ff): closes the spec 006 work unit; feature branch deleted local + remote.

9. **Spec 005 retrospective FIRST** (`scripts/ticker_sector_alpha_retrospective.py`, `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`): pre-spec validation of the per-ticker-vs-sector BULL filter hypothesis. Both criteria: (a) max +0.31pp net Δα across 79 commits — FAIL +1pp gate; (b) 48% cohort hit rate at +3% — PASS 40% gate. **Verdict: SKIP spec entirely** — cohort-loser suppression washed by winner suppression at indistinguishable rel-strength values. The pre-spec retrospective saved 6-8h of empty-spec implementation.

10. **Constitution v1.3.0 with Principle VIII** (`.specify/memory/constitution.md`): codifies "backward-looking price filters require pre-spec corpus retrospective showing net Δα ≥ +1pp at proposed default threshold + cohort hit rate ≥ 40% (when target cohort named) BEFORE any spec is written." Three same-day retrospective failures validated the case.

11. **Constitution-VIII follow-up**: cross-reference Principle VIII in spec 004 + spec 006 spec.md preambles + quickstart.md "What's new" sections + SC-008 measurable-outcome entries. Future readers of either spec immediately see (a) default-off status, (b) empirical verdict with numbers, (c) Principle VIII pointer, (d) grandfathered status (spec was authored BEFORE Principle VIII).

**No experiment currently selected.** Today was a research-burst day; tomorrow's options are tracked in the open data questions table below.

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
| Can a forward-catalyst-aware mechanism catch the 27-row 5th-failure-mode cohort + the 18-row +28%-mean-α ticker_strong-bear cohort? | Design-doc-only exploration of news-density signals / options-IV / LLM-extracted "bull case priced in" feature. Different mechanism class than backward-price-only (Principle VIII grandfathering). | $0 design + $20-40 to implement + retrospect | **partial-resolved (post-spec-007 + spec-008)** — Spec 007 Class 3 LLM feature catches a meaningful slice of the 5th-failure-mode cohort (88.9% bull cohort hit, +14.43pp discrim, +2.24pp net Δα). Spec 008 Hybrid C adds +3.35pp Δα on top. Bear-side ticker_strong cohort still uncaught — bear-inverted Hybrid C SKIP'd, suggests bear-side may need a different mechanism class entirely (Class 4 macro / Class 5 fundamentals deferred). |
| Does a Class 4 (cross-asset/macro) filter catch the bear-side ticker_strong cohort? | VIX + 10y yield + USD index + sector ETF correlation features. Build cohort + retrofit script per Spec 008 design doc Class 4 entry. | $2-10 LLM + ~3h | **open (NEW post-spec-008)** — bear-side cohort still uncaught after all 8 filter sides |
| Does a Class 5 (fundamentals-delta) filter add discrimination beyond Class 3? | Recent earnings surprise + analyst revisions as features. Same retrofit shape; different mechanism. | $1-5 LLM + ~3h | **open (NEW post-spec-008)** — orthogonal to Class 3's prose synthesis |
| Does the Spec 008 Hybrid C bull-only retrofit hold under live-mode A/B ablation? | Run daily_signals.py with boost enabled vs disabled on n≥30 same propagates; verify +3.35pp at 21d. | $5-10 LLM | **open (Spec 008 SC-009 condition for default-on flip)** |
| Does multi-window SC-003 replication strengthen all retrospectives? | Re-run SC-003 50-ticker on 3-5 additional dates; would expand corpus from 234 to 290+ commits + spec 003 eligible from 11 to 30+ + spec 006 ticker_strong cohort from 18 to 40+. | $40 (T3) | **open (NEW post-spec-006)** — biggest empirical-strengthening lever |
| At what corpus size does Spec 005 percentile-based variant become viable? | Extend per-ticker history to 30+ obs per ticker; re-run `scripts/ticker_sector_alpha_retrospective.py` with `--percentile-history-floor 30`. May surface signal that washed at the absolute-threshold variant. | $0 retrospective; needs corpus-expansion first | **open (NEW post-spec-005-skip)** |

---

## How to use this doc

When a phase fires (e.g. Opus result lands), update the **Active branch** section with the chosen sub-branch and what experiments / builds it triggered. Move completed phase items to RESEARCH_FINDINGS or `findings.md` as their results are written up. Add new exploration ideas to the appropriate phase as they surface — particularly the cross-pollination table when a sibling project ships something new worth porting.

This doc lives at the root with FINDINGS / RESEARCH_FINDINGS / README so anyone (including future you) can scan the directional state of the project from the top-level tree.
