# SIGNAL_LIFECYCLE — discover, evaluate, promote, retire, learn

_Forward design for a systematic signal-development pipeline._
_Created 2026-05-03. Pre-spec; promote to `.specify/specs/` if pursued._

This doc complements two existing docs:
- `SIGNALS.md` — current inventory of signals (the *what*)
- `BOTS_DESIGN.md` — how signals are consumed by the deterministic aggregator (the *how downstream*)

This doc is about the **upstream lifecycle**: how new signals enter the system, how their predictive value is measured, how they get promoted to production, when they're retired, and how the framework learns from every experiment.

---

## Why this matters

Current state: signals are added by hand based on intuition (or because they exist in yfinance). No systematic measurement of which signals actually predict; no promotion / demotion policy; no detection of signals whose predictive value has decayed.

Risk: accumulating dead weight (signals that look useful but don't predict), missing live signals (patterns hiding in data we already collect), and not noticing when a previously-useful signal stops working.

Goal: every signal has a measured score; the framework continuously tries new signals, retires dead ones, and reweights as evidence accumulates. The signal layer becomes *self-improving* rather than *static*.

---

## Signal lifecycle states

Each signal is in exactly one state at any time:

| State | Meaning | Promotion criteria |
|---|---|---|
| **Candidate** | Idea or auto-mined feature not yet evaluated | Pass evaluation harness once (any IC) → Experimental |
| **Experimental** | Measured, but evidence base too small | IC ≥ +0.05 on n ≥ 30 commits AND independence ≥ 0.3 (low correlation with existing) → Production |
| **Production** | Wired into analyst tool list, weighted in aggregator | IC < +0.02 for 3 consecutive measurement windows → Deprecated. IC < 0 for any window → urgent demote. |
| **Deprecated** | Still computed, no longer in active aggregator weighting | After 3 windows in deprecated with no recovery → Archived |
| **Archived** | Removed from active code, definition kept in registry for re-revival | (No automatic transitions — manual revival only) |

Status transitions are recorded as events in a registry (see "Registry" below).

---

## Metrics

For every (signal, horizon, ticker-set) tuple, track:

### Predictive metrics

- **Information coefficient (IC)**: Spearman rank correlation between signal value and realized alpha at the horizon. Range [-1, +1]. >+0.05 = useful, >+0.10 = strong, <0 = anti-signal.
- **Hit rate**: % of times signal-direction agrees with realized direction.
- **Mean alpha by signal quintile**: bucket signal values into quintiles, compare realized alpha. A monotonic gradient = signal is real.
- **Information ratio**: mean(alpha attributable to signal) / std(alpha). Adjusts IC for noise.

### Cost metrics

- **Compute cost**: time per call (median + p99)
- **$ cost**: API tokens / external API spend per call
- **Coverage**: % of (ticker, date) pairs where signal is available (e.g., insider-transactions is null for ETFs)

### Stability metrics

- **Rolling IC**: 30-day rolling IC. Flat-or-declining trend = degradation warning.
- **Distribution drift**: KS-statistic comparing current month's signal-value distribution to historical. >0.2 = regime shift suspected.

### Independence metrics

- **Pairwise correlation**: |corr(this signal, every other signal)|. Max value > 0.85 = redundant with existing signal.
- **Marginal IC**: IC of this signal AFTER controlling for top-3 already-production signals. <0.02 = adds nothing new.

---

## Components

### 1. Signal Registry (`tradingagents/signals/registry.py`)

Append-only event log + computed view:

```python
@dataclass
class SignalDefinition:
    signal_id: str               # "vix_30d_change"
    name: str                    # "VIX 30-day change"
    fetcher: str                 # dotted path to function: "tradingagents.dataflows.macro:vix_30d_change"
    inputs: list[str]            # what this signal depends on, for invalidation
    output_type: Literal["numeric", "categorical", "vector"]
    horizon_days: int            # what horizon this signal is intended for
    introduced: datetime
    state: Literal["candidate", "experimental", "production", "deprecated", "archived"]
    state_history: list[StateTransition]
    metrics: SignalMetrics       # latest IC, hit rate, cost, etc.
    weight: float                # in current aggregator
```

Persists to `~/.tradingagents/signals/registry.jsonl` (append-only, like memory log) + computed view at `~/.tradingagents/signals/current.json`.

### 2. Signal Computation Cache (`tradingagents/signals/cache.py`)

Per-(signal_id, ticker, date) cached value. Lets the evaluation harness re-score historical signals without re-paying compute. Sqlite-backed.

Schema:
```
signal_values(signal_id TEXT, ticker TEXT, date TEXT, value REAL,
              raw_json TEXT, computed_at TIMESTAMP, fetcher_version TEXT,
              PRIMARY KEY (signal_id, ticker, date, fetcher_version))
```

Versioning lets us re-compute when fetcher logic changes; old values stay accessible.

### 3. Evaluation Harness (`scripts/evaluate_signals.py`)

Cron-able / on-demand:

1. For each signal in {candidate, experimental, production}:
2. Pull all (ticker, date) pairs from signal cache
3. Fetch realized alpha at signal's target horizon
4. Compute IC, hit rate, quintile gradient, rolling IC, distribution drift
5. Pull the existing-signals correlation matrix
6. Compute marginal IC vs top-3 production signals
7. Apply transition rules; emit StateTransition events
8. Update `~/.tradingagents/signals/current.json`

Output: `claudedocs/signal-evaluation-<date>.md` with rankings, transitions, alerts.

### 4. Discovery Pipeline (`scripts/discover_signals.py`)

Three discovery channels:

**4a. Combinatorial**: cross-products of existing signals.
- `signal_A × signal_B` (e.g., RSI × short_interest)
- `lag_N(signal)` (yesterday's vs today's)
- `delta(signal, N)` (change over N days)
- Auto-promotes products that show high IC after evaluation.

**4b. Statistical mining**: extract candidate features from existing prose state logs.
- Regex-extract numbers from analyst reports (P/E ratios, percentages, etc.)
- Cluster news article topics; emit "topic_X_intensity" features
- Sentiment polarity from news text via lightweight classifier

**4c. LLM-driven hypothesis generation**: periodically ask Claude:
- "Given these 30 state logs and their realized 21d outcomes, what feature do you wish you had access to that would have helped distinguish the right calls from the wrong ones?"
- Claude responds with structured proposals: `{name, fetcher_logic_pseudocode, expected_IC, expected_cost}`
- Implementer (could be Claude itself) writes the fetcher; harness evaluates; auto-promotes if it passes thresholds.

### 5. Drift Detector (`scripts/detect_signal_drift.py`)

Runs over the rolling-IC history per signal:

- If 30-day rolling IC has declined ≥0.05 over the last 60 days → soft alert ("signal degrading")
- If 30-day rolling IC < 0 in latest window AND was > +0.05 in prior window → urgent alert ("sign flip")
- If KS-statistic on signal-value distribution > 0.2 vs historical → regime-shift warning
- Alerts written to `claudedocs/signal-drift-<date>.md` and surfaced in the evaluation report

### 6. Aggregator Reweighting (extension to BOTS_DESIGN aggregator)

When evaluation produces new IC values, the aggregator weights are updated:

```python
def reweight_from_metrics(registry: dict[str, SignalDefinition]) -> dict[str, float]:
    """Convert evaluated IC + cost into normalized weights."""
    raw = {}
    for sid, sig in registry.items():
        if sig.state != "production":
            continue
        ic = max(sig.metrics.ic, 0)            # never weight an anti-signal positively
        cost_penalty = sig.metrics.cost_per_call / 0.1  # normalize: $0.10 baseline
        raw[sid] = ic / (1 + cost_penalty)
    total = sum(raw.values())
    return {sid: w / total for sid, w in raw.items()} if total else {}
```

Weights become a function of measured value, not hand-tuned.

### 7. Counterfactual Tester (`scripts/counterfactual_signal.py`)

For an arbitrary signal proposal, simulate adding/removing it without running new propagations:

- Add: pull signal value for all historical (ticker, date) pairs in cache, recompute aggregator output, compare to actual outcome.
- Remove: zero out signal weight in aggregator, recompute outputs, measure decision quality delta.

Uses cached signal values + cached realized outcomes — $0 cost per counterfactual experiment.

---

## Meta-learning

Beyond per-signal metrics, learn meta-patterns about which signal types work when:

### Regime-conditional weights

Group signals into types: technical, fundamental, sentiment, macro, ownership, options.
For each type, compute IC stratified by regime (high-VIX / low-VIX / bull-trend / bear-trend / mixed).

Output: a mapping from regime → weighting policy. Example:
```
regime: "high_vix_bull_trend" (n=40 commits)
  technical:    0.10  (low — TA gets noisy in volatile bull regimes)
  fundamental:  0.45  (highest — fundamentals matter when markets are jumpy)
  macro:        0.20
  ownership:    0.15
  sentiment:    0.05
  options:      0.05
```

This becomes a second-level value function: aggregator picks weights from a lookup table indexed by current regime.

### Per-ticker signal preferences

Some tickers respond more to some signals. NVDA may respond to options flow more than AAPL does. Track per-(signal, ticker) IC; if a signal materially outperforms its global IC on a specific ticker, give it ticker-specific bonus weight.

### Time-of-cycle awareness

Pre-earnings vs post-earnings vs mid-cycle behave differently. Stratify IC by `days_to_earnings` from the earnings calendar; weight signals accordingly within the 21d window.

---

## Phased rollout

**Phase 0 — Registry + Cache** (3-4 days)
- Build `tradingagents/signals/registry.py` + `cache.py`
- Migrate existing 18 wired signals into the registry as `production` state with placeholder metrics
- Hook all analyst tool calls to write computed values into the cache
- No behavior change

**Phase 1 — Evaluation Harness** (3-4 days)
- Build `scripts/evaluate_signals.py`
- Run against current `experiments/*/results.csv` corpus + state logs
- Produce first `signal-evaluation-2026-05-XX.md` with IC/hit-rate per signal
- This is the first time we'll empirically know which signals predict 21d alpha

**Phase 2 — Drift Detector + Counterfactual Tester** (3-4 days)
- Build `scripts/detect_signal_drift.py` + `scripts/counterfactual_signal.py`
- Run drift check weekly; counterfactuals on demand
- Catches degraded signals; enables cheap "what if" testing

**Phase 3 — Reweight from Metrics** (2-3 days)
- Replace BOTS_DESIGN aggregator's hand-tuned WEIGHTS with `reweight_from_metrics(registry)`
- A/B against fixed weights on the same evaluation grid
- Validates the data-driven weighting

**Phase 4 — Combinatorial Discovery** (1 week)
- `scripts/discover_signals.py` — Phase 4a: cross-products + lags + deltas
- Auto-evaluate; auto-promote candidates passing thresholds
- Expect dozens of new candidate signals, most rejected, a handful surviving

**Phase 5 — LLM-driven Discovery** (1 week)
- Phase 4c — Claude proposes new features by reading state logs + outcomes
- Human-in-the-loop initially: Claude proposes, human approves before implementing
- After confidence builds, auto-implement low-risk proposals

**Phase 6 — Meta-learning (regime-conditional weights)** (1-2 weeks)
- Stratify IC by regime + ticker + cycle phase
- Build the second-level lookup table
- A/B against flat weighting

**Phase 7 — Continuous Loop** (ongoing)
- After every experiment: write signal values to cache, run evaluation, update registry, reweight
- Drift detector runs weekly; alerts in `claudedocs/`
- Discovery pipeline runs monthly; new candidates evaluated and promoted/rejected
- Project becomes a self-tuning signal pipeline

---

## Acceptance criteria (per phase)

| Phase | Success criterion |
|---|---|
| 0 | Registry has all 18 current signals; cache populates on every backtest run; no perf regression |
| 1 | Evaluation harness produces IC for every signal; ≥3 signals score IC > +0.05 (otherwise our current signal set has no measurable value) |
| 2 | Drift detector successfully flags ≥1 signal whose IC has dropped over the corpus history |
| 3 | Data-driven reweighting matches or beats hand-tuned weights on holdout (within ±1pp at 21d OW α) |
| 4 | At least 5 combinatorial signals promoted to experimental state; ≥1 reaches production |
| 5 | Claude proposes ≥10 candidates; ≥2 reach experimental; ≥1 reaches production |
| 6 | Regime-conditional weights show ≥0.5pp lift over flat weights on holdout |
| 7 | Quarterly review: signal turnover (promotions + demotions + retirements) > 0; project demonstrates ongoing learning |

---

## Risks

| Risk | Mitigation |
|---|---|
| Overfitting — signals look great in-sample but don't generalize | Always test on out-of-sample data; require ≥2 distinct experiments before promotion |
| Signal explosion — combinatorial discovery generates thousands of candidates | Pre-filter via cheap statistics (variance, coverage) before full evaluation; cap registry size at e.g. 200 |
| Metric gaming — signals optimized for IC but useless in practice | Track multiple metrics (IC, hit rate, info ratio, quintile gradient); promote only when 3+ agree |
| Drift detector noise — false alarms desensitize | Tune thresholds based on historical false-positive rate; require 2 consecutive windows before urgent alert |
| LLM-proposed signals are tautologies (e.g., "stock went up → bullish next day") | Require non-trivial transformation; reject pure restatement of inputs; auto-validate via causality test (signal at t must predict at t+horizon, not measured at t+horizon) |
| Cache size — millions of signal values | LRU eviction; archive old values to compressed parquet; only keep N=500 most-recent (signal, date) pairs in hot cache |
| Coupling to BOTS_DESIGN — both specs change in lockstep | Implement registry/cache standalone first (Phase 0-2 don't need bots-mode); aggregator reweighting (Phase 3+) requires BOTS_DESIGN done; sequence carefully |

---

## Connection to existing artifacts

- `SIGNALS.md` — inventory; will be auto-generated from registry once Phase 0 lands
- `BOTS_DESIGN.md` — Signal class consumer; aggregator weighting in this doc plugs into BOTS_DESIGN aggregator
- `ROADMAP.md` cross-pollination table — this doc IS the formalization of the "Steal Liberally" pattern from agent-harness-v2's "knowledge digestion + antibodies" entry
- `RESEARCH_FINDINGS.md` — IC measurement on existing 14 experiments will validate or invalidate our current architectural reframe (Constitution VII calibrated abstention claim depends on signals not being predictive at 5d but being predictive at 21d — that's a testable claim per this lifecycle)
- `.specify/specs/001-bots-architecture/spec.md` — must be implemented through Phase 2 before Phase 3 (reweight) here
- Constitution Principle VI (Spec Before Structural Change) — this doc would need promotion to `.specify/specs/<id>-signal-lifecycle/spec.md` before code

---

## Estimated total effort

| Phase | Effort | Cumulative |
|---|---|---|
| 0 | 3-4 days | 3-4 days |
| 1 | 3-4 days | 1-2 weeks |
| 2 | 3-4 days | 2-3 weeks |
| 3 | 2-3 days | 3-4 weeks |
| 4 | 1 week | 4-5 weeks |
| 5 | 1 week | 5-6 weeks |
| 6 | 1-2 weeks | 7-8 weeks |
| 7 | ongoing | — |

**Total to Phase 6 (full system)**: ~6-8 weeks of focused work.
**Cost**: mostly free (registry/cache/evaluation/drift/counterfactual all $0 — operate on existing data). Phase 5 LLM discovery: ~$5/proposal × 50 proposals = ~$250 across the project lifetime.

Per Constitution Principle III: the only LLM-spend phase (5) needs explicit budget deliberation. Other phases are dev time only.

---

## Sequencing per ROADMAP

This work fits in ROADMAP **Phase C (operationalize)** alongside the bots architecture. Recommended order:

1. **First**: BOTS_DESIGN Phase 1 (Shadow aggregator) — needed so signal values flow through Signal schema
2. **Then**: this doc Phase 0-2 (registry, cache, evaluation, drift) — measures everything
3. **Then**: BOTS_DESIGN Phase 2-3 (opt-in bots mode + cost shortcuts)
4. **Then**: this doc Phase 3 (data-driven reweighting) — replaces hand-tuned weights with measured ones
5. **Then**: this doc Phase 4-6 (discovery + meta-learning) — the project becomes self-improving

This sequence ensures every claim is measured before being acted on.

---

## Decision points before pursuing

- Promote to spec via `/speckit.specify <signal-lifecycle>`? Yes — structural change per Constitution Principle VI
- Allocate effort weeks 1-8 or sequence with other ROADMAP phases?
- Acceptable initial cost for cache + registry storage? (~10MB for current corpus; grows linearly with experiments)
- Rule for "production" promotion threshold (current proposal: IC ≥ +0.05, n ≥ 30, independence ≥ 0.3) — adjust before implementing?
- Privacy / data retention for cached signal values — same as state logs (kept indefinitely on disk)?
