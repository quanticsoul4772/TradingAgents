# BOTS_DESIGN — refactor TradingAgents agents into battlecode-style bots

_Design doc, 2026-05-03. Pre-spec; promote to `.specify/specs/` if pursued._

## Goal

Apply 6 patterns from `battlecode2026` ratbot6 to the TradingAgents multi-agent pipeline. The goals are:

1. **Token cost reduction** — current analysts emit ~10K-token prose per call; battlecode-style structured signaling replaces most of that with compact JSON.
2. **Interpretability** — replace LLM-as-synthesizer with explicit weighted aggregation of structured signals. Decisions become auditable as math, not prose.
3. **Tunability** — once the value function is explicit, weights become hyperparameters that gradient-descent / grid-search can optimize against the experiment corpus.
4. **Cost discipline** — per-bot token budget enforced at runtime, not by manual inspection.
5. **Architectural clarity** — make implicit state machines explicit; make the abstention-when-evidence-weak path part of the design (Constitution VII operationalized).

This is **NOT** about replacing LLMs with rule-based bots. The bots still call LLMs; they just produce structured outputs and respect resource budgets. Per Constitution Principle VI (Spec Before Structural Change), this would be a structural change requiring `/speckit.specify` before implementation.

## Current state

Per `tradingagents/graph/setup.py`:

```
Analysts (4) → Bull/Bear debate → Research Manager → Trader → Risk debate (3) → PM
   prose         prose ↔ prose      prose             prose    prose ↔ prose      prose
```

Every node emits free-form prose. Synthesis (Research Manager + PM) consumes all prior prose and re-reasons over it. Total per-propagate token spend: ~80K-150K tokens.

Mode collapse pattern (per RESEARCH_FINDINGS): synthesis produces Hold when prose evidence is mixed; commits when it leans clearly one way. Calibration is decent at 21d for bull commits, anti-calibrated for bear commits without a momentum filter.

## Proposed: bots emit signals, an aggregator emits decisions

### Architecture

```
                  ┌──────────────────────── Bot Layer ────────────────────────┐
                  │                                                           │
                  │   MarketBot       NewsBot      FundBot     SentimentBot   │
                  │   (LLM call)      (LLM call)   (LLM call)  (LLM call)     │
                  │       │              │            │            │          │
                  │       └──────────────┴────────────┴────────────┘          │
                  │                          │                                │
                  │                  Signal { ... }                           │
                  └──────────────────────────┼────────────────────────────────┘
                                             ▼
                  ┌────────────── Bull/Bear Debate (optional) ───────────────┐
                  │   Bull bot: argues IF aggregate signal lean is non-clear  │
                  │   Bear bot: argues IF aggregate signal lean is non-clear  │
                  │   Skip both if signals already converge (Tier-3 shortcut) │
                  └──────────────────────────┼────────────────────────────────┘
                                             ▼
                  ┌────────────── Aggregator (deterministic) ────────────────┐
                  │   weighted_sum(signals) → confidence + direction          │
                  │   apply_threshold(confidence) → rating                    │
                  │   apply_filters(momentum, regime) → final rating          │
                  └──────────────────────────┼────────────────────────────────┘
                                             ▼
                                   PortfolioDecision
```

### Data model: the `Signal` type

Each analyst-bot emits a `Signal` instead of prose:

```python
class SignalDirection(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"

class Signal(BaseModel):
    """One analyst-bot's contribution to the rating decision.

    Replaces ~10K-token prose with ~200-token structured fields.
    Aggregator combines signals via weighted sum without re-reading prose.
    """

    bot_id: str = Field(description="market | news | fundamentals | sentiment | bull | bear")
    direction: SignalDirection
    magnitude: float = Field(ge=0.0, le=1.0, description="confidence in direction, 0-1")
    horizon_days: int = Field(description="forward window the signal targets")
    key_facts: list[str] = Field(max_items=5, description="quoted evidence, 1-line each")
    risks: list[str] = Field(max_items=3, description="caveats / counterevidence")
    abstain: bool = Field(default=False, description="signal explicitly declines to predict")
    full_report: str | None = Field(default=None, description="fallback prose for debate / audit; not used by aggregator")
```

`abstain=True` means the bot saw insufficient evidence and is opting out. Aggregator gives it zero weight (instead of treating neutral=0.5).

### Aggregator (deterministic, no LLM)

```python
WEIGHTS = {
    "market": 0.25,        # technicals
    "news": 0.20,          # current events
    "fundamentals": 0.30,  # earnings/balance sheet
    "sentiment": 0.10,     # social
    "bull": 0.075,         # debate-derived
    "bear": 0.075,
}

def aggregate(signals: list[Signal]) -> AggregatedDecision:
    direction_score = 0.0   # +1 = bull, -1 = bear
    total_weight = 0.0
    for s in signals:
        if s.abstain:
            continue
        w = WEIGHTS[s.bot_id]
        sign = +1 if s.direction == SignalDirection.BULL else (
               -1 if s.direction == SignalDirection.BEAR else 0)
        direction_score += sign * s.magnitude * w
        total_weight += w

    if total_weight < MIN_WEIGHT_FOR_DECISION:
        return AggregatedDecision(rating="Hold", confidence=0.0)

    normalized = direction_score / total_weight
    return _threshold(normalized)  # ±0.6 → Buy/Sell, ±0.3 → OW/UW, else Hold
```

### Battlecode patterns mapped

| Pattern (battlecode) | Implementation in TradingAgents |
|---|---|
| Unified value function | `aggregate(signals)` is the value function |
| Squeak (structured signaling) | `Signal` schema replaces 10K-token prose |
| Bytecode budget | `BotBudget` tracks tokens per bot per propagate; logs warning + abstains if exceeded |
| Role specialization | `MarketBot` uses small/fast model; `FundBot` uses larger; `NewsBot` could use Exa-tuned |
| Explicit state machine | `DebatePhase` enum: ANALYSIS → DEBATE → SYNTHESIS → RISK → DECISION |
| Self-removal | `Signal.abstain = True` removes bot from aggregator weighting |
| Pre-computed shortcuts | Skip debate when 3+ signals converge with magnitude > 0.7 |

## Component contracts

### `BotBudget` (new)

```python
class BotBudget:
    """Per-bot token-spend ceiling enforced per propagate."""
    def __init__(self, ceilings: dict[str, int]): ...
    def reserve(self, bot_id: str) -> "BudgetReservation": ...

class BudgetReservation:
    def record(self, prompt_tokens: int, completion_tokens: int) -> None: ...
    @property
    def remaining(self) -> int: ...
    @property
    def exceeded(self) -> bool: ...
```

Used by each bot before its LLM call:

```python
def market_bot(state, llm, budget) -> Signal:
    res = budget.reserve("market")
    if res.exceeded:
        return Signal(bot_id="market", abstain=True, ...)
    response = llm.invoke(prompt)
    res.record(prompt.tokens, response.usage.output_tokens)
    return parse_signal(response)
```

### `DebatePhase` enum (new)

Replaces the implicit `current_response.startswith("Bull")` regex routing in `conditional_logic.py`:

```python
class DebatePhase(str, Enum):
    ANALYSIS = "analysis"
    BULL_TURN = "bull_turn"
    BEAR_TURN = "bear_turn"
    SYNTHESIS = "synthesis"
    TRADER = "trader"
    RISK_AGG = "risk_aggressive"
    RISK_CON = "risk_conservative"
    RISK_NEU = "risk_neutral"
    PM = "pm"
    DONE = "done"
```

Conditional edges become `state["phase"] == DebatePhase.X` checks instead of regex on prose.

### Pre-computed shortcuts

Convergence detection BEFORE debate:

```python
def should_skip_debate(signals: list[Signal]) -> bool:
    """Skip the bull/bear debate when analyst signals already converge.

    Saves 2 LLM calls (bull + bear) and ~10K tokens when convergence is clear.
    """
    non_abstain = [s for s in signals if not s.abstain]
    if len(non_abstain) < 3:
        return False  # not enough confidence either way
    bull_count = sum(1 for s in non_abstain if s.direction == SignalDirection.BULL and s.magnitude > 0.7)
    bear_count = sum(1 for s in non_abstain if s.direction == SignalDirection.BEAR and s.magnitude > 0.7)
    return bull_count >= 3 or bear_count >= 3
```

## Phased rollout

**Phase 1 — non-breaking augmentation (1-2 days)**: each existing analyst emits a `Signal` ALONGSIDE its prose report. The current downstream chain still uses prose. The aggregator runs in parallel as a "shadow PM" — its decision is logged for comparison but not used.

Validates the Signal schema works for all 4 analysts. No production behavior change. Cost: same as today + small overhead for the structured-output bind.

**Phase 2 — opt-in bot path (1 week)**: add `config["framework_mode"] = "bots"` flag. When enabled, the graph routes through aggregator (skipping prose synthesis); when disabled, current behavior. A/B comparable on the same dates.

Validates the bot path produces compatible ratings on a controlled experiment. Run as `experiment 008-bots-mode` against 10 NVDA dates.

**Phase 3 — debate-shortcut + budget (1 week)**: enable convergence-based debate skipping when `should_skip_debate()` is true. Wire `BotBudget` with per-bot token ceilings. Measure cost reduction.

Validates the cost-reduction claims empirically. Likely 30-50% token savings per propagate when convergence shortcut fires.

**Phase 4 — role specialization (2 days experiment)**: try lighter quick model for MarketBot, larger model for FundBot. Measure quality vs cost.

**Phase 5 — weight tuning (ongoing)**: with experiment corpus growing, optimize `WEIGHTS` against realized 21d alpha. Gradient descent or grid search over the existing `experiments/*/results.csv`.

## Validation strategy

Per Constitution Principle II (One Experiment Per Change):

- **Phase 1 shadow comparison**: log aggregator decision + actual PM decision per propagate. Compare distributions across 10 dates. Must agree on direction in ≥80% of cases for the bot path to be considered viable.
- **Phase 2 A/B**: run identical 10-date grid in both modes. Compare 21d α per bucket. Ratings need to match within ±1 tier in 80%+ of cases. Bucket alphas should be statistically equivalent.
- **Phase 3 cost measurement**: per-propagate token count with vs without shortcut. Target: ≥30% reduction when shortcut fires; net reduction ≥15% across mixed runs.
- **Phase 4 role-specialization**: measure quality (rating consistency with general-purpose run) and cost (per-propagate $ delta).

Constitution III ($30 per experiment ceiling): Phase 2 A/B at 10 pairs × 2 modes = ~$15. Phase 3 cost measurement = ~$10. Both comfortably under.

## Risks

| Risk | Mitigation |
|---|---|
| Signal schema too restrictive — analysts can't express important nuance | Keep `full_report` field as fallback; if downstream consumer needs nuance, it can read prose |
| Aggregator weights are arbitrary; no principled justification for 0.25/0.20/0.30/0.10 | Phase 5 (weight tuning) addresses; until then, weights are explicit hyperparameters subject to revision |
| Convergence shortcut hides cases where debate would have surfaced critical bear case | A/B in Phase 3 measures this; if shortcut produces materially wrong-direction decisions, raise threshold or remove |
| Bytecode-style budget might force premature abstention in legitimately complex cases | Make ceilings per-bot configurable; start generous, tighten based on observed spend distribution |
| Pydantic strict-output failures (per Opus 4.7 retry pattern in 005/007) | Keep free-text fallback already in `structured.py`; bot path inherits it |
| Bots-mode breaks downstream consumers that expect prose | Phase 1 is non-breaking; Phase 2 is opt-in via config flag — never default-on without explicit promotion |

## Out of scope

- **Replacing LLMs with rule-based bots**: bots still call LLMs. Structured signaling is about the OUTPUT shape, not the reasoning method.
- **Removing the existing prose pipeline**: kept indefinitely as the fallback / audit trail.
- **Cross-bot communication during analysis**: each bot is independent (no chatter mid-analysis). The "debate" is the only inter-bot communication, and it's optional.
- **Online learning / weight updates during a single propagate**: weights are static within a run; only updated between experiments via Phase 5 tuning.

## Decision points before implementation

If the user wants to pursue this:

1. **Promote to spec** (`/speckit.specify` to scaffold `.specify/specs/<id>-bots-architecture/spec.md`) per Constitution Principle VI — required for structural changes.
2. **Sequence relative to ROADMAP** — currently Phase B (Q1 65-pair re-pilot) is the active branch. Bots refactor would be Phase E (architectural variants). Probably fits AFTER 007 result lands and the 21d signal is validated at scale.
3. **Estimate**: Phase 1 (1-2 days) + Phase 2 (1 week) + Phase 3 (1 week) + Phase 4 (2 days) = ~3 weeks of focused work. Phase 5 is ongoing.
4. **Budget**: framework dev costs ~$0 (mocked tests). Validation experiments per phase ~$10-20 each. Total ~$60-80 across all phases — split into 3-4 separate runs each under Principle III ceiling.

## Related artifacts

- `battlecode2026/AGENTS.md` — source patterns
- `ROADMAP.md` cross-pollination table — high-level pointers
- Current implementation: `tradingagents/agents/analysts/`, `tradingagents/agents/managers/`, `tradingagents/graph/setup.py`, `tradingagents/graph/conditional_logic.py`
- Constitution Principles II (one change), III ($30 ceiling), VI (spec before structural change), VII (calibrated abstention) — all directly relevant
