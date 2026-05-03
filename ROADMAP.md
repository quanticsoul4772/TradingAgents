# ROADMAP — TradingAgents-lab

_Forward-looking exploration map. Updated 2026-05-03._

This is a research playground, not a product. The roadmap is directions for exploration, not delivery milestones. Per Constitution Principle V ("Steal Liberally"), cross-pollination from sibling projects in the portfolio is a primary driver — many ideas listed here originate elsewhere.

For findings to date see [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md). For per-experiment summaries see [`findings.md`](findings.md). For the original idea backlog see [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md).

---

## Current state (2026-05-03)

- 11 completed experiments + cross-experiment horizon sweep + Q4 per-ticker breakdown + A1 debate-quality diagnostic + A3 retrospective filter
- A3 mean-reversion suppression filter productionized (`tradingagents/agents/utils/momentum_filter.py`, gated by `config["uw_momentum_filter_threshold"]`)
- Constitution v1.1.0 with Principle VII (Calibrated Abstention is a Valid Output)
- Two load-bearing claims: (a) framework's Buy/OW commits at 21d show ~+1.6% α (n=37, framework-specific vs single-call), (b) UW failure mode is mean-reversion on tickers in -10%+ drawdowns
- Active: Opus 4.7 swap on NVDA × 10 (experiment 005, 7/10 complete at last check, all Overweight so far)

---

## Active branch — Opus pre-flight pair landed (2026-05-03)

**Both Opus results in**:
- 005 NVDA: 10/10 OW, 21d OW α = +2.85% (n=9, 78% hit) — strong bull commit + correct
- 006 AAPL: 8 Hold + 2 OW, 21d OW α = -0.07% (n=2, 50% hit) — discriminates, doesn't auto-commit

Combined finding: **Opus discriminates by ticker**. The 005 OW-collapse was bull-regime-specific (NVDA up +26% over the window); on mixed-evidence AAPL, Opus mostly holds. This is calibrated commitment — better than Sonnet's behavior on either ticker (Sonnet over-abstained on NVDA AND over-committed-bearish on AAPL).

Cross-experiment OW 21d α: +1.79% (n=41, 63% hit). Still the load-bearing claim; anchored heavily by NVDA bull-regime data.

**Next experiment selected**: 30-pair Opus re-pilot at 21d horizon with **mixed ticker basket** to test per-ticker discrimination at scale. ~$30, ~3.5h, fits Principle III ceiling. Use A3 momentum filter enabled.

Suggested basket composition (10 dates each):
- 1 bull-regime ticker (NVDA → expect mostly OW per 005 pattern)
- 1 mixed-regime ticker (AAPL → expect mostly Hold per 006 pattern)
- 1 bear-leaning ticker (XOM, INTC, or BBY → untested with Opus; expect mostly Hold or some UW)

This tests whether: (a) Opus's bull-side α holds on a fresh bull-regime ticker (n=9 → n=20+ NVDA-like commits), (b) the per-ticker discrimination produces a clean cross-regime distribution, (c) the A3 filter doesn't suppress too many Opus UW commits (in case bear-leaning ticker generates them).

---

## Sequenced phases of exploration (post-Opus)

### Phase B — out-of-sample validation of the existing claims

Current findings rest on n=37 21d-bull commits and n=16 UW commits, all in-sample. Out-of-sample validation could cover:

- **Q1 65-pair re-pilot at 21d** with the A3 filter enabled — tests both the bull-side signal at scale AND whether the filter generalizes off the in-sample 16 commits ($30, ~14h)
- **Smaller filter A/B** on a fresh 10-pair grid (filter on vs off, same dates) — cheaper validation of just the filter ($10, ~2h)
- **Bear-correct ticker pilot** — run the framework on a basket of tickers known to have bear pressure (XOM, PFE, INTC, BBY) at 10 dates each, see if UW commits there look different than NVDA/MSFT. Tests the "UW works on bear-correct tickers" claim ($15, ~12h)

### Phase C — operational integration

The framework currently outputs ratings. With the A3 filter wired in, it could output more:

- **`reasoning_evidence` second-opinion in PortfolioManager** with asymmetric handling per Q5 (agreement → augment confidence, disagreement → flag for review). Per the divergent analysis, must be designed to fail gracefully when the reasoning service is down. (4-6h, $0.10/run forward)
- **Bias auditor** running `reasoning_detect` over saved bull/bear debates — produces a per-experiment bias profile (confirmation, anchoring, recency, overconfidence). Validates A1's hedge-words finding programmatically. (2-4h)
- **Counterfactual analyzer** running `reasoning_counterfactual` on Hold-α extreme dates as part of every analysis pass — auto-builds the "what if framework had committed?" narrative for FINDINGS. (1-2h)

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

## Open data questions

These need new experiments to answer; no amount of analysis on existing CSVs will resolve them.

| Question | Proposed experiment | Cost |
|---|---|---|
| Does the 21d bull lift hold at n=100+? | Q1 65-pair re-pilot at 21d (same as Phase B Q1) | $30 |
| Is the lift ticker-class specific (mega-cap tech vs others)? | Sector-stratified pilot | $20 |
| Does the A3 filter generalize off-sample? | Filter A/B on fresh dates | $10 |
| Does Opus / GPT-5.4 / Gemini 3.x show the same 21d shape? | Model-swap matrix | $20-40 |
| Is the bear-correct-ticker UW signal robust beyond AAPL? | Bear-leaning ticker pilot | $15 |
| Does the framework predict longer horizons (60/90d) where 5d failed and 21d worked? | Re-aggregate current data + extend window with future price data (60-day wait) | $0 + time |
| Does same-prompt rerun-variance dominate the signal? | n=3 reps on the existing 10 NVDA dates with current config | $15 |

---

## How to use this doc

When a phase fires (e.g. Opus result lands), update the **Active branch** section with the chosen sub-branch and what experiments / builds it triggered. Move completed phase items to RESEARCH_FINDINGS or `findings.md` as their results are written up. Add new exploration ideas to the appropriate phase as they surface — particularly the cross-pollination table when a sibling project ships something new worth porting.

This doc lives at the root with FINDINGS / RESEARCH_FINDINGS / README so anyone (including future you) can scan the directional state of the project from the top-level tree.
