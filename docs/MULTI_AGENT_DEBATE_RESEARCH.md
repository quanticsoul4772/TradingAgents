# Multi-agent debate research — direction and integration plan

**Status**: research direction proposal, not committed
**Date written**: 2026-05-01
**Author context**: post-pilot of TradingAgents (65 runs, anti-signal in bullish bucket, 0 Buys/Sells), informed by survey of agent-harness-v2, ladybird (security fork), battlecode2026 (ratbot6), and bruno-swarm.

---

## 0. The actual research question

Not "can TradingAgents pick stocks." We already answered that — no. The real question this document plans against:

> **What structural conditions cause role-based multi-agent LLM debate to collapse to moderate ratings, and what enforcement mechanisms (or alternative architectures) would prevent that collapse?**

This is an *agent-systems research* question, not a finance question. The 65 saved JSON state logs are the seed corpus.

---

## 1. What the pilot actually proved

A pilot was run against TradingAgents v0.2.4 with `claude-sonnet-4-6` (deep) + `claude-haiku-4-5` (quick), 1/1 debate rounds, 3 analysts (market/news/fundamentals), 5+5 tickers (NVDA/AAPL/MSFT/GOOGL/JPM ran fully; BRK.B started; UNH/WMT/XOM/CAT untouched), 65 successful propagations over 14h wall-clock. Cost ~$32.

Key findings — read as **debate-dynamics phenomena**, not stock-picking outcomes:

| Phenomenon | Measurement | Interpretation |
|---|---|---|
| Mode collapse | 0 Buys, 0 Sells across 65 runs | The 5-tier rating scale is a vocabulary, not a behavior. Bull/bear/risk debate apparatus does not produce strong conviction. |
| Bullish anti-signal | Overweight bucket: -0.35% mean α, 41% hit rate | When debate converges on Overweight, stock underperforms more often than not. |
| Inverted hit-rate ordering | Hold (57%) > Underweight (58%) > Overweight (41%) | Neutral synthesis outperforms active recommendations. |
| Magnitudes inside noise | σ per bucket 2.5–4%; mean differences ~1.5% | Cannot reject "all means equal" with n=29 max per bucket; if signal exists, it's weak. |

The framework's own README disclaims financial use ("research purposes... not investment advice"). The pilot validates that disclaimer literally.

---

## 2. The portfolio context

The user's GitHub portfolio reveals a coherent thesis being built across multiple substrates. Four projects matter for this decision:

### 2.1 `agent-harness-v2` — the meta-substrate

61,669 LOC Python runtime. Event-sourced SQLite (hash-chained, ~100 event types, projections rebuildable from event log), 42 hooks, REQUIRED_GATES manifest, fail-closed runner, 25 active MCP tools, knowledge digestion pipeline (DEDUPE → CANDIDATE → REVIEW → COMMIT), goal evaluator, alignment gate, Goodhart detector, memory with antibodies + staleness/trauma gates + Voyage AI + sqlite-vec, self-improvement spine (gate effectiveness, calibration, phase advancer EVIDENCE→SYNTHESIS→DRAFT_SPEC→BUILD→CUTOVER→OPERATE), 3 verifiers with checkpoint capture and auto-rewind, counterfactual replay. Three-process architecture (Python runtime + Rust sidecar + Svelte 5 dashboard) deployed on Hetzner CPX31 via podman quadlet.

**Crucial existence proof**: `runtime/src/agent_harness/openclaw_worker.py` is a 1147-line domain-specific worker for poker against the OpenClaw Agent League. It loads strategy parameters from a memory document, plays sessions, then queues a recap prompt so the agent can analyze results and update params. **The worker pattern for bounded-feedback domains already exists.** Trading is a structurally identical case.

Layer 0 commitments that govern: **enforcement is structural** (gates run in harness code, never as model directives); **the event log IS the telemetry** (no additive observability); **tool calls, not text, are engagement**; **context is a finite budget**.

### 2.2 `ladybird` (security fork) — the structural-enforcement pattern at OS scale

14,615 files diverged from upstream LadybirdBrowser/ladybird. Not a feature fork — a re-architecting. Sentinel daemon (separate process, not a renderer hook): YARA + TFLite ML detection, nsjail sandbox, AES-256 quarantine, 27 API hooks for fingerprinting detection with aggressiveness scoring, behavioral net analysis (C2 beaconing, DGA, DNS tunneling), per-process network isolation via iptables/nftables. Tor per-tab circuit isolation, IPFS CID verification, ENS, DoT + DNSSEC. Rust mixed into the C++ codebase. Auto-generated weekly fork-divergence reports.

**Pattern transfer**: same shape as agent-harness-v2 — separate enforcement plane that runs whether the underlying system cooperates or not. Browser does it via daemon; agent runtime does it via event bus. **Both are structural-enforcement systems applied to different substrates.**

### 2.3 `battlecode2026` (ratbot6) — the architectural counter-thesis to TradingAgents

Java competitive bot for MIT Battlecode 2026. Successive iterations (ratbot → ratbot4 → ratbot5 → ratbot6, ~1700 lines for ratbot6).

The stated philosophy is the most important sentence in this entire portfolio for our purposes:

> **"Intelligence in the algorithm, not in roles. Every rat uses a unified value function to decide what to do. 'Roles' emerge from game state, not from assignment."**

This is the **direct architectural opposite** of TradingAgents (which assigns rigid Bull / Bear / Aggressive / Conservative / Neutral roles and orchestrates a debate between them). Ratbot6 puts the intelligence in `scoreAllTargets()` and lets behavioral specialization fall out of state. Wins on DefaultSmall, DefaultMedium, DefaultLarge.

**Implication**: the pilot's mode-collapse finding may not be a TradingAgents-specific bug — it may be a **structural failure mode of role-based multi-agent designs in general**. Ratbot6 is empirical evidence that an agent-system architect prefers value-function-with-emergent-roles over role-assigned debate. The collapse we observed is consistent with that preference being correct.

### 2.4 `bruno-swarm` — the comparison case for role-based multi-agent

7-agent CrewAI dev swarm: 14B Qwen2.5-Coder-abliterated orchestrator + 6 × 3B specialists (Frontend / Backend / Test / Security / Docs / DevOps). Hierarchical mode (orchestrator delegates) or flat (peers sequence). Uses local Ollama, `bruno` (neural behavior engineering) for role-specific abliteration, Modelfiles per role. Pre-built Docker image on DockerHub; deployable on RunPod / Vast.ai / Modal.

This is a **role-based multi-agent system the user already built**. So they have direct experience with this architecture's failure modes (the README mentions: 3B models can be repetitive, 14B orchestrator sends batch delegations, CrewAI needs minimum context windows).

**The cross-domain comparison falls out for free**: TradingAgents and bruno-swarm are both role-based multi-agent. battlecode2026 is value-function-emergent. agent-harness-v2 is the structural-enforcement substrate that any of them can run inside. The four projects already form a 2×2 design matrix.

---

## 3. The architectural dichotomy this exposes

|  | **Rigid roles** | **Emergent roles (value function)** |
|---|---|---|
| **Prompt-only enforcement** | TradingAgents (Bull/Bear/Risk debate, 5-tier scale specified in prompt only) | Hypothetical |
| **Structural enforcement** | bruno-swarm (CrewAI hierarchy is structural; abliteration is structural via model weights) | battlecode2026 (`scoreAllTargets()` IS the structure; roles emerge) — and what agent-harness-v2 enables for any inner architecture |

The pilot's mode collapse sits in the top-left cell. Three exit paths:

1. **Move down** (add structural enforcement to the existing role-based design): agent-harness-v2's gates wrapping TradingAgents' debate. Easiest delta. Tests whether structural gates can rescue a role-based system.
2. **Move right** (replace role-based debate with a unified value function): port the ratbot6 philosophy to financial decisions — one model, one scoring function, decisions emerge. Most ambitious. Tests whether the pilot's failure is endemic to roles.
3. **Move both** (build the bottom-right cell from scratch): structural-enforcement substrate hosting an emergent-role inner architecture. Maximal investment.

---

## 4. The decision

### Three options considered

| Option | Description | Score (mcp-reasoning weighted) |
|---|---|---|
| **A** | Standalone trading-agent harness — port enforcement patterns from agent-harness-v2, trading-only scope | 0.655 |
| **B** | Add trading domain to agent-harness-v2 — new worker module + event types + gates + projections, mirroring `openclaw_worker.py` | **0.825** ✓ |
| **C** | Build new from scratch — multi-agent debate + structural enforcement as primitives in a green-field system | 0.520 |

### Recommendation: **Option B** with an architectural sub-question to resolve

`mcp-reasoning_decision` (weighted criteria over: leverage existing infrastructure investment, minimize duplication, maintain clean abstractions, speed to first research result, fit with existing deployment + dashboard, ability to apply mcp-reasoning to debate transcripts, extensibility to other multi-agent debate domains) recommends Option B decisively. The 61k LOC of agent-harness-v2 is a sunk investment that compounds; `openclaw_worker.py` proves the worker pattern hosts bounded-feedback domains; the existing dashboard, hooks, and self-improvement spine all become free for trading.

But Option B leaves **one architectural sub-question** open that the battlecode2026 lens makes visible:

> Inside the trading worker, do we keep TradingAgents' role-based debate (Bull/Bear/Risk) and *gate* its outputs structurally? Or do we replace the debate with a ratbot6-style unified value function that emits the rating directly, with structural enforcement of the 5-tier distribution?

This is the **research bet**. Both are testable inside agent-harness-v2 as parallel worker variants:
- **`trading_worker_debate.py`** — wraps `TradingAgentsGraph.propagate()` as-is, adds gates.
- **`trading_worker_value.py`** — single-model with a scoring function over the same analyst inputs, emergent rating.

Running both against the same (ticker, date) grid and comparing rating distributions + alpha calibration is the cleanest experiment our pilot data already enables. **This is the actual research contribution** — not "did TradingAgents pick stocks" but "do role-based debates collapse when value-function alternatives don't, and does structural enforcement reach into the gap?"

---

## 5. Cross-project integration map

```
┌─────────────────────────────────────────────────────────────────────┐
│                       agent-harness-v2 (substrate)                   │
│  EventBus · 42 hooks · REQUIRED_GATES · Goodhart · Goal · Memory   │
│  Knowledge digestion · Verifiers · Counterfactual replay · Dashboard│
└──────────┬──────────────────┬────────────────────┬──────────────────┘
           │                  │                    │
   ┌───────▼──────┐   ┌──────▼───────┐   ┌───────▼───────────┐
   │ openclaw     │   │ trading      │   │ external_repo     │
   │ _worker      │   │ _worker(s)   │   │ _agents           │
   │ (poker)      │   │  · debate     │   │ (hygiene, etc.)   │
   │              │   │  · value      │   │                   │
   └──────────────┘   └──────┬───────┘   └───────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
        ┌───────▼─┐  ┌──────▼────┐  ┌────▼──────┐
        │ Trading │  │ mcp-reasoning │ │ ladybird   │
        │ Agents  │  │ (contradiction│ │ (Sentinel  │
        │ pipeline│  │  /divergent/  │ │  pattern   │
        │ (LangGraph)│  decision)    │ │  reference)│
        └─────────┘  └───────────────┘ └────────────┘

bruno-swarm and battlecode2026 inform the architectural choice INSIDE
the trading worker (role-based vs value-function) but are not directly
integrated. They are the empirical reference cases.
```

Each project's role:

| Project | Role in this plan |
|---|---|
| **agent-harness-v2** | Hosts the trading worker(s); provides event bus, gates, projections, dashboard, self-improvement loop. **Where the work lands.** |
| **TradingAgents** | The substrate consumed by `trading_worker_debate.py`. Its `propagate()` call is the unit of work. The 65 saved JSON state logs are the seed corpus for the event log. |
| **mcp-reasoning** | Powers the `trading_debate_contradiction_gate` and the cross-trial debate analysis. Already in agent-harness-v2's MCP server set. |
| **ladybird** | **Reference architecture for the gate design**. Sentinel = separate enforcement plane peer to the renderer. The trading gates should follow the same shape: peers to the worker, not callbacks inside it. |
| **battlecode2026** (ratbot6) | **Reference architecture for the value-function alternative**. `scoreAllTargets()` philosophy informs `trading_worker_value.py`. |
| **bruno-swarm** | **Comparison case** for role-based multi-agent failure modes. Once trading worker is running, run analogous cross-domain comparisons: do dev-task delegations in bruno-swarm exhibit similar collapse? |

---

## 6. Concrete shape of Option B

### 6.1 New worker module

`runtime/src/agent_harness/trading_worker.py` — modeled after `openclaw_worker.py` (1147 lines, 20 functions). Two variants:

- **`trading_worker_debate.py`**: imports `TradingAgentsGraph.propagate()` in-process. No REST like poker needed.
- **`trading_worker_value.py`**: ratbot6-style — single Sonnet call with the analyst reports as inputs and a scoring function that emits rating + confidence directly.

Both load strategy params from memory documents (`trading-strategy-params-debate`, `trading-strategy-params-value`). Both emit the same event types so the analysis layer treats them uniformly.

### 6.2 New event types (in `events/types.py`)

```
trading.propagation.started   ticker, date, params_hash, worker_variant
trading.debate.bull_bear      ticker, date, bull_text, bear_text, debate_rounds   (debate variant only)
trading.debate.risk_3way      ticker, date, aggressive, conservative, neutral     (debate variant only)
trading.value.scored          ticker, date, score_breakdown                       (value variant only)
trading.rating.produced       ticker, date, rating, rationale_excerpt
trading.outcome.resolved      ticker, date, raw_return, alpha_return, holding_days
trading.recap.generated       batch_id, distribution, alpha_by_bucket, by_variant
```

Hash-chained alongside everything else. Each event type needs ≥1 consumer (CLAUDE.md ghost-data audit invariant).

### 6.3 New gates (in `enforcement/`, registered in `EXPECTED_HOOKS`, fail-closed)

Each gate's deny message follows the `reason / purpose / fix` triple (commitment #9):

| Gate | Fires when | Why it exists |
|---|---|---|
| `trading_rating_distribution_gate` | N consecutive runs produce 0 Buy + 0 Sell | Detect declared-vs-behavior drift on the 5-tier scale. Direct response to the pilot's mode-collapse finding. |
| `trading_debate_contradiction_gate` | `mcp-reasoning_contradiction` on bull/bear text returns "parallel monologue" / no substantive disagreement | Test whether adversarial debate is real adversarial structure or theater. Only relevant for `_debate` variant. |
| `trading_calibration_gate` | Realized-α sign systematically disagrees with rating direction over rolling window | The "Hold beats Overweight" finding made structural. |
| `trading_variant_parity_gate` | `_debate` and `_value` variants produce ratings that disagree on N% of (ticker, date) pairs without explanation | Forces investigation when two architectures diverge — useful research signal. |

### 6.4 New projections (in `events/projections.py`)

`trading_runs`, `trading_debates`, `trading_outcomes`, `trading_distributions` — derived tables, rebuildable from events (CLAUDE.md invariant #1).

### 6.5 Dashboard pane

Reuses existing Svelte dashboard. New tile: rating distribution over time (per worker variant), α-by-bucket, gate fire counts, contradiction rate.

### 6.6 Memory documents

`trading-strategy-params-debate`, `trading-strategy-params-value`, `trading-recap-history`, `trading-research-log`. Plug into existing memory + antibody + staleness-gate plumbing.

### 6.7 Specs

Per CLAUDE.md spec hygiene rules, `specs/trading-domain-spec.md` lands alongside, mirroring `specs/external-repo-agent-mode.md`. Layer 0 commitments restated; trading-specific contracts; gate contracts; event-type contracts.

---

## 7. Three-step ramp (gated commits)

Each step produces a concrete artifact. Commit to the next only after the prior produces clean signal.

### Step 1 — One-shot backfill script (~1 hour, no agent-harness-v2 changes yet)

Read the 65 JSON state logs from `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/` and produce a draft event stream (file, not committed to live event bus). Validates the proposed event schema against real data. **Either schema fits or needs adjustment — find out cheap.**

### Step 2 — Contradiction analysis on existing 65 bull/bear pairs (~2 hours, no agent-harness-v2 changes yet)

Apply `mcp-reasoning_contradiction` to all 65 pairs from the pilot. Produces the **first novel research finding** regardless of what we build next:

> "Of 65 bull/bear debates in TradingAgents, X% exhibit substantive contradiction; Y% are parallel monologue."

This finding alone is publishable, sharpens the contradiction-gate design, and is *more interesting* than the stock-picking result. If contradiction rate is low (say <30%), the structural failure mode is identified at the debate-architecture level, not just the rating-output level.

### Step 3 — Decision gate

After steps 1 and 2, three forks open:

**Fork 3a — Commit to full Option B.** Land specs + worker + event types + gates + projections + dashboard pane in agent-harness-v2. Run both worker variants on a fresh 50-run grid (different time window than pilot to avoid overfit). Compare results.

**Fork 3b — Treat trading as research probe only.** Apply the same contradiction analysis to bruno-swarm dev-task delegations and openclaw poker recap pairs. Produce the cross-domain comparison paper: "structural collapse in role-based multi-agent LLM systems across three domains." No agent-harness-v2 commit.

**Fork 3c — Defer.** Steps 1+2 produced enough material for now. Park the integration; revisit when other agent-harness-v2 priorities clear.

---

## 8. Honest tradeoffs and risks

### 8.1 Abstraction widening

agent-harness-v2 is currently positioned as "long-lived autonomous agent on a repo." Adding poker (already done) and trading (proposed) widens the brief to "long-lived autonomous agent across bounded-feedback domains." This is a real abstraction shift. Worth naming explicitly in the spec so it doesn't drift into accidental scope creep over many incremental PRs.

### 8.2 Spec hygiene cost

CLAUDE.md invariant #8 requires PRs touching `specs/001-v3-baseline/spec.md` to also touch `tasks.md`, `data-model.md`, or `plan.md`. A trading-domain addition is non-trivial — expect 2-3 spec files of authoring before Step 3a code can land.

### 8.3 The value-variant might not actually be ratbot6-shaped

ratbot6's value function operates over a small, discrete state space (map tiles, bytecode-bounded). Financial state is high-dimensional and continuous. A naive port may not capture the philosophy faithfully. If `trading_worker_value.py` mode-collapses in the same way as the debate variant, the pilot's failure is endemic to LLMs reasoning over equity decisions, not to role-based architecture specifically. **That negative result would also be valuable** — it would invalidate the "use a value function" thesis as a remedy in this domain.

### 8.4 Backfill data quality

The 65 JSON state logs were produced under one prompt set, one model pair (Sonnet/Haiku), one debate-rounds setting. Treating them as a homogeneous corpus is fine for "did this produce signal" questions but limited for parameter-space questions. Future runs should vary one parameter at a time so the event log accumulates a real ablation matrix.

### 8.5 The user's research interest may evolve

This plan is grounded in the stated interest "understanding LLM debate dynamics." If that interest shifts (e.g., toward operator-dashboard UX, or toward agent-harness-v2's calibration loop, or toward ladybird's network behavioral analysis), the trading-worker investment may not be the highest-leverage place to spend cycles. Re-validate research direction before Step 3a commit.

---

## 9. Open questions for explicit decision

1. **Worker variant scope**: do we ship both `_debate` and `_value` variants in the first cut, or start with `_debate` (lower risk, mirrors existing TradingAgents) and add `_value` after Step 3a?
2. **Ticker universe**: pilot used 5 tech-heavy + 5 not-yet-run names. Is the 10-name `tickers.txt` the canonical set, or should we curate a different universe for sector breadth / volatility regime coverage?
3. **Date-range strategy**: pilot was a single 3-month window (Jan–Apr 2026). Should subsequent runs sample from multiple regimes (e.g., 2024 H2 inflation peak, 2025 H1 rate cuts, 2026 YTD) to test regime-dependence of the collapse?
4. **Cross-domain comparison priority**: does the bruno-swarm + openclaw cross-domain analysis (Fork 3b) get done before, after, or in place of the agent-harness-v2 integration (Fork 3a)?
5. **Disposition of the existing TradingAgents repo**: keep as a vendored dependency consumed by `trading_worker_debate.py`, or fork it under quanticsoul4772 and pin to a specific SHA?

---

## 10. Files referenced

| Path | Why it matters |
|---|---|
| `C:/Development/Projects/TradingAgents/pilot_results.csv` | The 65-run pilot output; seed data for Steps 1-2 |
| `C:/Development/Projects/TradingAgents/scripts/backtest.py` | The harness used to produce pilot |
| `C:/Development/Projects/TradingAgents/scripts/analyze_backtest.py` | The analyzer used to produce the rating-bucket report |
| `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<date>.json` | Full debate transcripts for all 65 runs — the corpus |
| `C:/Development/Projects/agent-harness-v2/runtime/src/agent_harness/openclaw_worker.py` | The blueprint for `trading_worker.py` |
| `C:/Development/Projects/agent-harness-v2/runtime/src/agent_harness/external_repo_agents.py` | Pattern for adding new sub-agent definitions |
| `C:/Development/Projects/agent-harness-v2/runtime/src/agent_harness/events/types.py` | Where new event types land |
| `C:/Development/Projects/agent-harness-v2/runtime/src/agent_harness/enforcement/` | Where new gates land |
| `C:/Development/Projects/agent-harness-v2/specs/agent-harness-v2-spec.md` | Layer 0 commitments to honor |
| `C:/Development/Projects/agent-harness-v2/CLAUDE.md` | Architecture, invariants, conventions |

---

## Bottom line

The pilot didn't fail — it produced a clean failure-mode dataset that aligns directly with the structural-enforcement thesis already running across the user's portfolio. The right move is to fold trading into agent-harness-v2 as a second bounded-feedback domain (joining poker), use the existing event-bus + gates + dashboard infrastructure, and use the architectural dichotomy revealed by battlecode2026 vs bruno-swarm to set up a *real* experiment: does structural enforcement rescue role-based debate, or does the value-function alternative obviate the need for it?

Two cheap probe steps (backfill + contradiction analysis) gate the bigger commitment. Either is worth doing tomorrow.
