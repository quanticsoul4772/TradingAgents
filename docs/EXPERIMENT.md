# TradingAgents as an experimental research playground

**Status**: living doc, brainstorm-mode
**Started**: 2026-05-01
**Companion**: `docs/MULTI_AGENT_DEBATE_RESEARCH.md` (the strategic-decision doc) — superseded for direction; kept for record.

---

## Part 1 — What this project is now

### Definition

TradingAgents is now a **personal experimental sandbox for studying and improving multi-agent LLM debate dynamics**, using equity-decision-making as the substrate because it has cheap, objective ground truth (forward returns vs benchmark) — not because we care about the trading.

It is explicitly **not**:
- A stock-picker (the disclaimer is correct).
- A merge target with agent-harness-v2 (kept separate so it can break things without contaminating production infra).
- A finished system (it's a place to try things).

It explicitly **is**:
- A fork-of-spirit if not of repo: heavy modification of upstream TradingAgents v0.2.4 with no obligation to remain compatible.
- A place to combine and test ideas drawn from other projects in the portfolio (`agent-harness-v2`, `ladybird/Sentinel`, `battlecode2026/ratbot6`, `bruno-swarm`, `mcp-reasoning`, `branch-thinking`, `logic-thinking`).
- A producer of saved corpora — every run dumps a JSON state log; over time, the corpus IS the research output.
- A test bed for the architectural question: **why does role-based multi-agent debate collapse, and what fixes it?**

### Operating constraints (chosen, not imposed)

- **Stay cheap**: keep individual experiment runs ≤ $30. No 6-hour overnight $200 runs without explicit decision.
- **Save everything**: every run's full state log is preserved. The corpus compounds.
- **One experiment per change**: vary one parameter at a time so the corpus is interpretable as ablation data, not noise.
- **No committed roadmap**: ideas land here, they get tried or shelved, the doc is the journal. Don't optimize for completeness.
- **Steal liberally**: any pattern from the other projects that fits is fair game. No need to maintain abstraction purity.

### Success criteria for this sandbox

Not "the framework picks stocks." Instead:
1. **Produces transferable findings** about multi-agent LLM behavior (mode collapse conditions, debate-vs-monologue, role-based vs value-function, structural enforcement effects).
2. **Generates patterns** that could later land in agent-harness-v2 or another production system.
3. **Sustains your interest** — if it stops being fun to tinker with, that's a signal to switch focus.

---

## Part 2 — What made TradingAgents sound promising

These are surface answers. Reality may differ (and the pilot showed it does).

### What the project advertised

| Advertised feature | Why it sounded promising |
|---|---|
| Multi-agent debate (Bull vs Bear, 3-way risk) | Mirrors how humans actually argue about stocks; promises nuance over single-model output |
| 5-tier rating scale (Buy / Overweight / Hold / Underweight / Sell) | Implies calibration — not just direction but conviction |
| Persistent memory log — "PM learns from past calls" | Implies improvement-over-time, the holy grail for agent systems |
| Multi-provider (10+ LLM backends) | Looks production-ready, comparable across providers |
| LangGraph state machine | A respected, popular framework. Implies real engineering, not prompt spaghetti |
| Structured output (Pydantic) at decision points | Implies type safety, parseable output, real software discipline |
| Saved JSON state logs per run | Implies auditability, replay |
| ArXiv paper (2412.20138) | Academic legitimacy |
| Disclaimer "for research purposes" | Credible disclosure of limitations |
| ~30 minute setup, runs locally | Low barrier to try |

### What made it popular (community signal)

| Signal | What it suggests |
|---|---|
| Multiple translated READMEs, Discord, WeChat, X presence | Active community + marketing investment |
| ~10k+ GitHub stars (estimated from star-history banner in README) | Real audience |
| Frequent releases (v0.2.0 → v0.2.4 in ~3 months per CHANGELOG) | Active maintenance |
| Multiple LLM providers actively supported | Provider-agnostic ambition |
| Tracked contributor list per release | Real contributors, not just one author |

### What people expected (community-side, broader market)

These are the implicit promises of "AI agent" in late 2024-2026:

- **Autonomy**: agents that can take many actions without per-step human approval.
- **Self-improvement**: agents that get better at their task as they accumulate experience.
- **Persistent memory**: state that survives session boundaries and informs future decisions.
- **Tool use**: agents that call APIs, run code, fetch data — not just chatbots.
- **Multi-step reasoning**: chain-of-thought that holds up over many steps.
- **Calibration**: confidence levels that match accuracy.
- **Auditability**: you can inspect what the agent did and why.
- **Transferable competence**: an agent good at task A can adapt to similar task B.

TradingAgents *gestures* at all of these. The pilot showed it delivers on tool use, multi-step reasoning, and auditability cleanly; the rest are aspirational rather than realized.

---

## Part 3 — What we know we get from an agent in agent-harness-v2

Sharper picture from actually reading the runtime + specs. These are *delivered* not advertised:

### Infrastructure delivered

| Capability | What it actually does |
|---|---|
| **Hash-chained event log** | Every state mutation is an immutable, ordered, sha256-chained event. Real auditability, not marketing. |
| **Projection rebuild parity** | Replaying the entire event log produces byte-identical derived state. Tested in CI. |
| **42 hooks, REQUIRED_GATES, fail-closed runner** | Gates run as code, not prompts. Timeout = deny. Exception = deny. |
| **Knowledge digestion (DEDUPE → CANDIDATE → REVIEW → COMMIT)** | Memory writes go through a pipeline, not directly into a context window. |
| **Memory antibodies + staleness/trauma gates** | Memory has a half-life and active immune system, not just a growing pile. |
| **Self-improvement spine** | EVIDENCE → SYNTHESIS → DRAFT_SPEC → BUILD → CUTOVER → OPERATE per version. The agent's improvement of itself is itself a lifecycle. |
| **Goodhart detector** | Watches for metric-gaming behavior in real time. |
| **Goal evaluator + alignment gate + idle detection** | Goals as first-class objects with measurable criteria, not vibes. |
| **3 verifiers + checkpoint capture + auto-rewind** | When the agent breaks something, a separate process can roll back. |
| **Counterfactual replay** | "What would have happened if the agent had taken path B at step 17?" — answerable. |
| **Operator dashboard** | Live SSE stream of what the agent is doing, with intervention surface. |
| **Calibration loop with prediction-feedback** | The agent makes predictions about its own work, gets scored, the score informs future predictions. |
| **Phase advancer per version** | The agent's own self-modification follows a structured release lifecycle, not impulse. |
| **Pluggable model registry with A/B routing** | New models can be promoted through validation → ab_testing → primary based on measured outcomes. |
| **Daily-spend auto-pause at $50** | Hard budget gate. Agent cannot spend itself into bankruptcy. |

### What this means in agent terms

An agent inside agent-harness-v2 has:
- **Real memory** that decays, gets reviewed, gets contradicted (antibodies), and is auditable.
- **Real goals** that are measured by SQL predicates against the event log.
- **Real accountability** — every action is logged, ordered, hash-chained.
- **Real self-improvement** that operates on a release cycle, not vibes.
- **Real budgets** that are enforced structurally.
- **Real introspection** — you can ask "show me everything that happened" and get a complete answer.

This is what "agent" should mean. TradingAgents claims most of these and delivers on roughly two (tool use, structured output).

---

## Part 4 — The gap

What was promised vs what's delivered:

| Promised by TradingAgents | Delivered by TradingAgents | Delivered by agent-harness-v2 |
|---|---|---|
| Self-improving via memory log | Append-only markdown; PM only consults memory if entries exist; no review/decay/contradict | Knowledge digestion pipeline + antibodies + staleness gate + half-life scorer |
| Calibrated 5-tier ratings | Mode collapse to 3 tiers (0 Buy, 0 Sell across 65 runs) | Calibration loop with prediction-feedback; A/B model routing on measured calibration |
| Bull vs Bear *adversarial* debate | Likely parallel monologue (TBD via contradiction analysis) | (Doesn't claim debate, but provides structural-enforcement primitives that would catch debate failures) |
| Auditability via JSON logs | One JSON file per run, no chaining, no projection, no replay | Hash-chained event log with rebuildable projections + counterfactual replay |
| Multi-provider robustness | Anthropic worked; one bug found (`anthropic_effort` default); other paths unverified | Pluggable model registry with promotion lifecycle |
| "Research framework" — improves over time | Static prompts, static topology, no self-improvement loop | Phase advancer + improvement proposals + outcome attribution |

**The gap is the project.** Closing parts of it is the experimental playground's purpose.

---

## Part 5 — Brainstorm: ideas to try

Organized by source of inspiration. None of these are committed; many are bad. The point is to have them on paper.

### From `agent-harness-v2` (structural enforcement + event sourcing)

- **EH-1**: Replace the JSON-per-run log with a hash-chained SQLite event log. Every analyst tool call, every debate utterance, every PM rating becomes a hashed event. Get replay + projection rebuild for free. **Companion**: once the event log exists, point Grafana directly at it via the SQLite datasource plugin (no Prometheus — our access pattern is post-hoc cross-run comparison, not live scrapes; and your `grafana-mcp` repo already exists, so Grafana plugs into your toolchain naturally). Six initial panels: rating distribution over time, α-by-bucket trend, tokens-per-run by agent, gate fire counts, contradiction rate (bull vs bear), experiment leaderboard. Optional zero-config interim: `datasette` over the same SQLite for ad-hoc SQL via browser before committing to Grafana panel design.
- **EH-2**: Add `gates/` directory. First gate: `rating_distribution_gate` that fires when N consecutive runs miss Buy or Sell. Make it deny the run with `reason / purpose / fix`.
- **EH-3**: `goodhart_gate` for our backtest harness — watch for the harness rewarding moderate ratings and the model learning to always pick them.
- **EH-4**: Knowledge digestion pipeline for analyst reports — DEDUPE (same news in two reports), CANDIDATE (worth keeping), REVIEW (does it contradict prior), COMMIT.
- **EH-5**: Memory antibodies — when a past PM call was wrong by >X%, the entry becomes an antibody that *suppresses* similar reasoning in future calls instead of just being a "lesson."
- **EH-6**: Counterfactual replay — "rerun this date but force the bull to make argument X." Useful for ablations.
- **EH-7**: Phase advancer for prompt evolution — the prompts themselves go through DRAFT → AB_TEST → PRIMARY based on measured calibration.
- **EH-8**: Per-agent budgets enforced as gates (token/cost ceilings per role per run).

### From `ladybird/Sentinel` (separate enforcement plane)

- **LS-1**: Run a separate "Sentinel" process *peer to* the LangGraph state machine, not as a callback. It watches the event stream and intervenes structurally.
- **LS-2**: 27-API-hook style for analyst tool use — every tool call goes through a hook that can score, log, or block.
- **LS-3**: "Aggressiveness scoring" for analyst tool use: 0.0–1.0 score for how much an analyst is hitting tools vs synthesizing. Cross-correlate with rating quality.
- **LS-4**: Quarantine for incoherent runs — if PM rating contradicts the bull/bear arguments by some metric, the run is quarantined for review instead of being committed to memory.
- **LS-5**: "Behavioral net analysis" applied to analyst output — detect patterns that look like hallucination signatures (e.g., sudden specific number citations not in the tool output).
- **LS-6**: Per-process network isolation analog for LLM calls — each agent runs against a sandboxed view of available tools instead of the full set.

### From `battlecode2026/ratbot6` (value function over roles)

- **BR-1**: **The big one.** Replace Bull/Bear/Risk debate with a single `scoreAllRatings()` call: one model gets all analyst inputs and emits `{Buy: 0.1, Overweight: 0.3, Hold: 0.4, Underweight: 0.15, Sell: 0.05}`. The "rating" is whichever the score function picks. **No roles**; behavior emerges from the scoring.
- **BR-2**: Bytecode-style budgets per agent — each agent has a hard token budget. Force compression. (`gpt-5.4-mini` with `max_tokens=500` for analysts, `max_tokens=2000` for PM.)
- **BR-3**: Squeak-style structured signaling — replace bull/bear natural-language debate with structured signals (`bull.confidence=0.7, bull.thesis_id=12, bear.contradiction=[3, 7]`). Agents communicate via shared array, not prose.
- **BR-4**: Charge mode — when an analyst returns a strong signal (>X SD from baseline), short-circuit the debate and emit a strong rating directly. Test whether ignoring the "balanced debate" produces *better* calibration.
- **BR-5**: Vision cone management — each analyst can only see a specific data slice (market = price/volume only, news = headlines only, fundamentals = filings only). Force genuine specialization, not "everyone reads everything."
- **BR-6**: Iterate ratbot1 → ratbot2 → ratbot6 style — version each architecture cleanly, run them against each other (same date, both architectures, compare).

### From `bruno-swarm` (multi-agent dev coordination)

- **BS-1**: Hierarchical vs flat mode toggle — TradingAgents is hierarchical (analysts → debate → PM). Test a flat mode where 7 specialist analysts vote with no debate or PM synthesis.
- **BS-2**: Local Ollama for high-volume agents — analysts via local Qwen2.5-Coder-7b, PM via Sonnet. Cuts cost ~80%, tests whether local models can do the high-volume reasoning.
- **BS-3**: Abliterated specialist agents — a model abliterated to *only* be an aggressive risk analyst, never balanced. Test whether structural specialization (via weights) outperforms prompt-specified roles.
- **BS-4**: Orchestrator-led mode — a 14B-class model plans the debate (which analysts to consult, what order, when to stop) instead of using a fixed LangGraph topology.
- **BS-5**: Specialist swarm voting — each of N specialist agents independently produces a rating; PM aggregates with weighted vote based on past accuracy.

### From `mcp-reasoning` + `branch-thinking` + `logic-thinking` (your reasoning toolchain)

- **MR-1**: `reasoning_contradiction` applied to bull/bear pairs at runtime, not just post-hoc. Bull and bear are required to identify ≥1 substantive contradiction with the other; PM only sees pairs that pass.
- **MR-2**: `reasoning_divergent` applied to PM rating decisions — produce 5 alternative ratings with rationales, then pick. Surfaces when the model is committed to one answer vs uncertain.
- **MR-3**: `reasoning_decision` weighted-criteria scoring instead of free-text PM synthesis. Forces explicit criteria.
- **MR-4**: `reasoning_tree` over rating decisions — explore the rating-justification tree, prune weak branches.
- **MR-5**: `logic-thinking` proof construction — every PM rating must come with a structured deductive argument from analyst inputs to conclusion. Surface when arguments are non-deductive.
- **MR-6**: `branch-thinking` semantic analysis on analyst reports — detect which analyst's claims survive cross-referencing against others.

### Wild cards (no specific source)

- **WC-1**: **Adversarial reward** — Bull and Bear get scored on whether they identify flaws in the other's argument. Train this incentive into the prompts. Does it shake debate out of parallel monologue?
- **WC-2**: **Multi-temporal debate** — same analysts debate the same date with different lookbacks (5d / 30d / 90d / 1yr). Aggregate. Tests whether the time horizon assumption is the hidden bias.
- **WC-3**: **Stochastic ensemble** — run TradingAgents N times per (ticker, date) at different temperatures. Vote. Compare noise floor to single-run noise.
- **WC-4**: **Different debate topologies** — round-robin, all-vs-all, hierarchical, swarm, single-model-with-self-debate. Run all 5 on the same grid. Which topology produces the most calibrated output?
- **WC-5**: **Human-in-the-loop step** — the PM proposes, a human (you) approves/overrides. Compare to auto-PM. Builds a human-rated corpus for later RLHF-style training.
- **WC-6**: **Continuous prompt mutation** — memory log feeds into prompt mutation; prompts evolve based on outcome attribution.
- **WC-7**: **Tool-call quality scoring** — separately score how well each analyst USED its tools (relevant calls, redundant calls, ignored returns). Does tool-use quality predict rating quality?
- **WC-8**: **Hallucination detection** — cross-check every numeric claim in an analyst report against the tool outputs that were actually returned. Quarantine reports with unsourced numbers.
- **WC-9**: **Self-play / dual TradingAgents** — run two instances on the same date with different params, have them debate each other's PM ratings. The PMs become the new bull/bear.
- **WC-10**: **Replace 5-tier with continuous scalar** — rating is a float [-1, +1], not a category. Test whether the categorical bottleneck causes the mode collapse.
- **WC-11**: **Order randomization** — randomize analyst order, debate order, see if "first speaker" effects exist. Probably do.
- **WC-12**: **PM blind to debate** — strip the debate from the PM's input; PM only sees raw analyst reports. Does the "synthesis" actually add value, or is it cargo cult?
- **WC-13**: **Debate over actions, not labels** — instead of "Buy/Sell/etc", debate concrete actions ("buy 100 shares at limit X", "wait until earnings"). See if action-grounded debate has different dynamics than label-grounded.
- **WC-14**: **Self-distillation loop** — collect the 65+ runs as training data, fine-tune a single small model to mimic the full pipeline. Compare cost/quality.
- **WC-15**: **Adversarial market regime** — run the harness during a known volatile period (March 2020, Aug 2022) and compare collapse rate to calm periods. Does the model collapse *more* when markets are uncertain?

### Meta / process ideas

- **MP-1**: Every experiment commits a `experiments/<date>-<idea-id>/` directory with: hypothesis, params, results, conclusion. The corpus IS the lab notebook.
- **MP-2**: One-line summary at the top of each experiment dir: "tested X, result Y, decision Z" so the directory listing is scannable.
- **MP-3**: A `findings.md` at the repo root that aggregates one-liners from all experiment directories. Living changelog of *findings*, not commits.
- **MP-4**: `make experiment NAME=foo` scaffold — generates the directory, copies the harness with the param to vary, prepares the analyzer.
- **MP-5**: Adopt agent-harness-v2's CLAUDE.md spec-first discipline — every non-trivial idea above gets a one-page spec before code.

---

## Part 6 — Quick filter (what's worth trying first)

Filtering the brainstorm against: (a) costs <$10 to test, (b) produces a clear yes/no signal, (c) leverages the existing 65-run corpus or only needs a few new runs.

**Status refresh (2026-05-09)**: ~7 of the 12 original Tier 1/2/3 ideas are now DONE. Tier numbering preserved for historical traceability; status badges added inline.

**Tier 1 — would do tomorrow, low cost, high information**:
- ~~**MR-1** (contradiction analysis on existing 65 bull/bear pairs)~~ — **DONE 2026-05-02**: confirmed two-sided evidence in 100% of debates. Two-sidedness is real; framework's Hold response is correct.
- ~~**WC-12** (PM blind to debate)~~ — **DONE 2026-05-02**: broke 5d mode collapse; 5 NVDA Buys at α=-0.22%. At 21d, those Buys would have been directionally correct.
- ~~**EH-2** (rating distribution gate)~~ — **DONE**: DENY findings on every experiment. Gate enforces 5-tier surface; framework legitimately mostly uses 3 tiers.
- ~~**WC-11** (order randomization)~~ — **DONE 2026-05-09 (v1) + v2 IN FLIGHT**: v1 PARTIAL ALT-A + ALT-B (cannot disambiguate at n=20); v2 disambiguation cohort (3 tickers × 5 dates × 4 perms = 60 propagates; ETA 2026-05-10). Constitution v1.5.2 "Analyst-order scope" amendment.

**Tier 2 — medium investment, medium signal**:
- ~~**BR-1** (value-function alternative — single model, no debate)~~ — **DONE 2026-05-03**: single-call baselines on NVDA + AAPL; broke Hold collapse but produced wrong commits at 5d AND 21d. Framework's structural value IS the 21-day lift that single-call lacks.
- ~~**WC-10** (continuous scalar rating)~~ — **DONE 2026-05-08/09 + arc CLOSED**: full v1+v2+v3 + Spec 009 Branch C. v1 SC-007 ALT-A confirmed (3.6× commit ratio); v2 SC-005(b) NULL (Pearson r +0.0918 at n=100); v3 PARTIAL ALT-A. Branch C activated (bin-then-output ergonomic-only). Constitution v1.5.0 + v1.5.1 amendments. Total: $54.40 LLM.
- **WC-2** (multi-temporal — 5d/30d/90d/1yr debates) — STILL DEFERRED. ~$30.
- ~~**MR-3** (`reasoning_decision` weighted scoring instead of free-text PM)~~ — **DONE 2026-05-02 (v1) + 2026-05-03 (v2)**: synthesis prompt fix produced 6 OW + 3 Hold at NVDA; "no calibration win" at 5d. At 21d, 6 OW commits would have been correct.

**Tier 3 — bigger investment, bigger swing**:
- **EH-1** (hash-chained event log replacing JSON-per-run) — STILL DEFERRED (Spec 002 partially shipped via `tradingagents/signals/cache.py`; full unified event log for memory + checkpoint + paper-trade is Phase E per ROADMAP).
- ~~**BR-3** (structured signaling instead of natural-language debate)~~ — **DONE 2026-05-09 (v1) + v2 IN FLIGHT**: v1 PARTIAL ALT-B (commit shift +20pp; α delta below threshold); v2 sister extensions to news + fundamentals analysts (40 propagates; ETA 2026-05-10). Phase E architectural variant NOT unblocked at v1 evidence level.
- **WC-4** (5 debate topologies in parallel) — STILL DEFERRED. ~$50.
- **BS-2** (local Ollama for analysts) — STILL DEFERRED.

**Backlog — interesting but defer**:
- Everything else from Part 5 brainstorm above (most never ranked into Tier 1/2/3).

**NEW ideas surfaced 2026-05-06 → 2026-05-09 (NOT in original Part 5 brainstorm)**:
- ~~**Class 4 macro filter**~~ — **DONE 2026-05-09 (BEAR PASSED → Spec 012 deployed; BULL SKIP per PR #203)**. FIRST cross-asset/macro filter in the framework.
- ~~**Class 5 fundamentals-delta filter**~~ — **DONE 2026-05-06 (BULL SKIP per v1.4.3 additive gate; 89% Spec 007 overlap)**.
- ~~**Spec 008 Hybrid C calendar boost**~~ — **DONE 2026-05-06 (default-off pending live SC-009 ablation)**.
- ~~**C-4 institutional rotation (bear-side)**~~ — **DONE 2026-05-07 (Spec X-1 deployed at default-shadow)**.
- ~~**Local-high BULL filter**~~ — **DONE 2026-05-09 (DEFER per PR #205; n=2 below Spec 012 sample-size floor)**.
- **EH-4** Knowledge digestion pipeline — partially DONE per `claudedocs/historical-hold-attribution-2026-05-08.md` (Hold-attribution analysis); full pipeline per the original brainstorm not yet implemented.

**Tier 1/2/3 completion summary** (2026-05-09 EOD):
- Tier 1: 4 of 4 DONE (100%)
- Tier 2: 3 of 4 DONE (75%; WC-2 multi-temporal deferred)
- Tier 3: 1 of 4 DONE (25%; EH-1 + WC-4 + BS-2 deferred)
- Total Tier 1+2+3: **8 of 12 DONE (67%)**
- Plus 5 NEW ideas DONE (Class 4 + Class 5 + Spec 008 + C-4 + local-high) — exceeded original backlog

The original "Tier 1 = would do tomorrow" framing aged well (all 4 DONE within 7 days of writing). Tier 3 items are by-construction higher-effort + lower-priority; their 25% completion rate is consistent with their Tier 3 ranking.

---

## Part 7 — Working notes

### 2026-05-01 — initial draft

Doc started after the strategic Option-B decision in `MULTI_AGENT_DEBATE_RESEARCH.md` was set aside in favor of "let TradingAgents stay its own playground." Brainstorm above is uncurated. First filter pass landed Tier 1/2/3 above.

Open thread: should we adopt `experiments/<date>-<id>/` directory convention before the next run, so the structure exists from idea #1?

### 2026-05-01 — observability decision

Picked **Grafana over Grafana+Prometheus**. Reason: backtest harness exits between runs, Prometheus is pull-based and built for live targets, would need a pushgateway to glue. Grafana directly over the SQLite event log (EH-1) gives us cross-run dashboards without the extra ops surface. `grafana-mcp` already exists in the portfolio so Grafana plugs into the existing toolchain. Recorded as a companion to EH-1 above.

### 2026-05-01 — baseline metrics before cleanup

Captured for "where we started" reference:
- **Test coverage: 31% overall (92 passing tests).** Plumbing well-covered (schemas, memory, signal processing, checkpoint). Core debate logic ≤ 20%: analysts (0–13%), `graph/setup.py` (12% — the actual LangGraph topology), `conditional_logic.py` (21%), all LLM clients (0–22%), `dataflows/` (7–29%, external API wrappers).
- **No test asserts the 5-tier rating scale is honored across runs.** Direct cause of why mode collapse to 3 tiers went undetected upstream. EH-2 gate would catch this.
- **Dead dependency**: `backtrader>=1.9.78.123` in `pyproject.toml`, zero references in any `.py` file. Survived from the project's original "we'll add a real backtest layer someday" intent.
- **3 vestigial files at root**: `requirements.txt` (3-byte stub `.`), `test.py` (ad-hoc yfinance smoke, not pytest), `tradingagents.egg-info/` (generated by editable install, gitignored but present locally).

### 2026-05-02 — experiments scaffolding implemented (spec 001)

Per `specs/001-experiments-scaffolding/`. Full spec-kit workflow exercised:
`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

Implemented:
- `tradingagents/experiments/` module: `ids.py` (Experiment ID generation/validation/parsing), `overrides.py` (--config-override KEY=VALUE parsing with R-003 type coercion ladder), `templates.py` (HYPOTHESIS / PARAMS / run.sh / run.ps1 renderers).
- `scripts/new_experiment.py` — typer CLI to scaffold a new `experiments/<id>/` dir with templated files. Refuses to overwrite existing dirs.
- `scripts/backtest.py` extensions: `--experiment-id <id>` flag (validated), `--config-override KEY=VALUE` repeatable flag (with type coercion + warning on conflicts with named flags per FR-010), `experiment_id` column appended to CSV at end (R-004; backward-compat with pre-cleanup CSVs), PARAMS.json auto-sync per R-007 (refuses to overwrite manual annotations).
- `scripts/findings_aggregate.py` — walks `experiments/*/ANALYSIS.md`, extracts first-line-after-H1 summary (R-001), writes `findings.md` at repo root with atomic write, newest-first ordering (R-002).
- `experiments/.gitkeep` placeholder so the directory exists in fresh clones.
- `findings.md` at repo root (currently shows "No experiments yet"; lights up as experiments land).
- 53 new tests across `tests/test_experiments_{ids,overrides,templates}.py`, `tests/test_new_experiment.py`, `tests/test_backtest_extensions.py`, `tests/test_findings_aggregate.py`. All pass.

What this enables: the Tier 1 ideas now have a clean experiment-creation workflow. WC-12 (PM-blind) becomes one command line: `python scripts/new_experiment.py pm-blind --source-idea WC-12 --cost 10` → edit run.sh → bash it. WC-11 (order randomization), MR-1 (contradiction analysis on existing 65 pairs), EH-2 (rating distribution gate) all share the same scaffold.

Verdict on the spec-kit workflow for *this* feature: worth it. Forced 7 explicit design decisions (research.md R-001..R-007), separated CLI surface from internal logic (4 contracts), surfaced cross-entity invariants (data-model.md). Cost: ~1 hour of design writing + ~1 hour of implementation = ~2 hours total for ~600 LOC + 128 tests (220 → 92 baseline). Roughly 3:1 design-to-code ratio at this scale; appropriate for foundational scaffolding.

Manual smoke verification (T028 from tasks.md): scaffolded `experiments/2026-05-02-001-smoke-test/` via `new_experiment.py`, populated a fake ANALYSIS.md, ran `findings_aggregate.py` — confirmed both pending and completed paths render correctly. Smoke artifact deleted (operational verification, not real research per Constitution Principle II).

### 2026-05-01 — scaffolding installed (per docs/SCAFFOLDING_PLAN.md)

All 6 steps executed:
- **Step 1**: `[project.optional-dependencies] dev` group added to `pyproject.toml` with pytest≥8, pytest-cov≥6, pytest-asyncio≥0.24, ruff≥0.8, mypy≥1.13, pre-commit≥4. Installed via `uv pip install -e ".[dev]"`. Versions installed: ruff 0.15.12, mypy 1.20.2, pre-commit 4.6.0, pytest 9.0.3.
- **Step 2**: `[tool.ruff]` (line-length 100, py310 target, broad lint rules including E/W/F/I/B/UP) and `[tool.mypy]` (gradual typing, ignore-missing-imports, py310 target, per-module overrides for yfinance/stockstats/parsel/questionary/langgraph/langchain) added.
- **Linter baseline**: ruff = **305 errors** (212 auto-fixable, mostly mechanical: 49 unused imports, 44 unsorted imports, 37 non-PEP585 annotations, 37 blank-line-with-whitespace, 34 module-import-not-at-top — concentrated in upstream code). mypy = **167 errors in 18 files**. New code goes through pre-commit; existing baseline grandfathered.
- **Step 3**: spec-kit installed. `uvx --from specify-cli specify init --here --ai claude --script ps` failed because GitHub releases v0.5.0+ ship with empty asset lists (only v0.4.4 has templates). Worked around by downloading `spec-kit-template-claude-ps-v0.4.4.zip` directly from GitHub releases and extracting in-place. Got `.specify/scripts/powershell/`, `.specify/templates/` (6 templates: spec, plan, checklist, tasks, constitution, agent-file), `.claude/commands/speckit.*.md` (9 slash commands). Wrote `.specify/memory/constitution.md` with our 6 commitments (not template placeholders): Save Everything, One Experiment Per Change, Stay Cheap, No Production Claims, Steal Liberally, Spec Before Structural Change.
- **Step 4**: `.pre-commit-config.yaml` created with ruff (lint+format), standard hygiene hooks (trailing whitespace, EOF, large files, merge conflicts, private keys), and a local `pytest-fast` hook running `pytest -m unit -q`. Installed via `pre-commit install`. Hook lives at `.git/hooks/pre-commit`.
- **Step 5**: CLAUDE.md updated with "What this project is" section + "Read the constitution first" pointing at `.specify/memory/constitution.md` + spec-kit slash command list + quality-gate description.
- **Step 6**: this entry; final pytest run pending.

What this enables: spec-driven workflow for the Tier 1 ideas. First spec to write: the common scaffolding for `experiments/` (per the cleanup-skill's "scaffolding recommendations" section).

---

## Appendix — links

- Strategic-decision doc (now superseded for direction): `docs/MULTI_AGENT_DEBATE_RESEARCH.md`
- Pilot setup guide: `claudedocs/SETUP.md`
- Pilot results: `pilot_results.csv`
- Backtest harness: `scripts/backtest.py`, `scripts/analyze_backtest.py`
- agent-harness-v2 reference: `C:/Development/Projects/agent-harness-v2/CLAUDE.md`
- Layer 0 commitments to optionally honor: `C:/Development/Projects/agent-harness-v2/specs/agent-harness-v2-spec.md`
