# WC-10 Continuous Scalar Rating — feature description DRAFT for operator review

**Status**: DRAFT for operator review BEFORE invoking `/speckit.specify` or running the experiment.
**Cost gate**: ~$20 LLM (T2 per Constitution III; requires explicit operator authorization).
**Date**: 2026-05-08

**Purpose of this doc**: per Constitution VI (Spec Before Structural Change) + the PR #87 precedent (Spec X-1 feature description draft for operator review BEFORE `/speckit.specify`), this file drafts the equivalent for WC-10. Operator reviews / edits / approves; the approved text becomes the literal input to `/speckit.specify` IF the operator decides to advance.

**Per PR #97 EXPERIMENT.md Tier 2/3 status survey recommendation**: WC-10 (continuous scalar rating) is the highest-information-value untouched experimental candidate. Tests the categorical-bottleneck hypothesis directly: does the 5-tier rating scale itself drive the framework's mode collapse to Hold?

---

## What WC-10 tests

**Hypothesis**: The framework's well-documented mode collapse to Hold (Constitution VII Calibrated Abstention) is partially driven by the **5-tier categorical rating scale** forcing discrete commitment. If the rating output were a **continuous scalar** in `[-1, +1]` (signed magnitude of conviction), the model could express partial confidence without being forced into a Hold abstention.

**Falsifiable prediction**:
- **NULL hypothesis**: continuous scalar does not change behavior; framework outputs cluster near 0 (=Hold) at the same rate as the 5-tier collapse to Hold.
- **ALT hypothesis A (categorical-bottleneck-confirmed)**: continuous scalar produces a less-collapsed distribution; the bull/bear signal that the 5-tier scale was throwing away surfaces in the scalar magnitude.
- **ALT hypothesis B (signal-equivalent)**: continuous scalar bins ex-post (via thresholds) to match the 5-tier distribution; calibrated abstention is mode-collapsed regardless of output type.

The crucial empirical question is whether the **information thrown away by 5-tier discretization is systematically signal or noise**. If signal, the framework's mode collapse is partially an artifact of the output schema; if noise, the categorical scale is an honest expression of the model's calibrated uncertainty.

## Cross-experiment alignment

WC-10 complements 3 prior experiments:

- **WC-12 PM-blind (PR experiments/2026-05-02-002 + cross-aapl + cross-msft)**: stripped debate from PM input. Result: at 5d, broke mode collapse (5 NVDA Buys at α=-0.22%); at 21d, those Buys would have been directionally correct.
- **MR-3 v2 synthesis prompt (experiments/2026-05-02-004)**: replaced free-text synthesis with structured prompt. Result: 6 OW + 3 Hold at NVDA; "no calibration win" at 5d, but 6 OW commits would have been correct at 21d.
- **single_call_baseline (experiments/2026-05-03-003 + 004)**: tested single LLM call vs full multi-agent framework. Result: similar ratings (corpus IC -0.489); the framework's architectural premise is not adding signal beyond a single calibrated call.

WC-10 is **architecturally orthogonal** to all 3: it doesn't touch debate / synthesis / single-vs-multi; it ONLY changes the output schema from 5-tier categorical to continuous scalar.

## Mechanism

### Schema change

`tradingagents/agents/schemas.py`:

```python
class PortfolioDecision(BaseModel):
    rating: float = Field(
        ge=-1.0, le=+1.0,
        description=(
            "Signed conviction. -1 = max bearish (Sell-magnitude); "
            "0 = balanced/no commit (Hold-equivalent); +1 = max bullish "
            "(Buy-magnitude). Values between integer thresholds express "
            "partial confidence."
        ),
    )
    executive_summary: str = ...
    investment_thesis: str = ...
```

### Bin-to-5-tier compatibility layer (FR-007)

For backward compatibility with the 9-filter portfolio (all gates operate on 5-tier `pre_rating ∈ {Buy, Overweight, Hold, Underweight, Sell}`), provide a bin function:

```python
def bin_scalar_to_tier(rating: float) -> str:
    """Bin continuous scalar rating to 5-tier categorical for filter compatibility."""
    if rating <= -0.6: return "Sell"
    if rating <= -0.2: return "Underweight"
    if rating <= +0.2: return "Hold"
    if rating <= +0.6: return "Overweight"
    return "Buy"
```

Bin thresholds are tunable; default `[-0.6, -0.2, +0.2, +0.6]` produces equal-width bins. Operator can sweep alternative bin schemes ex-post via the analysis script.

### Filter portfolio compatibility

All 9 production filters operate on 5-tier `pre_rating`. WC-10 has 2 modes:

- **Filter-passthrough mode**: continuous rating bins to 5-tier via `bin_scalar_to_tier()` BEFORE filters run; filters operate as today; post-filter rating remains 5-tier.
- **Filter-bypass mode**: continuous rating is the final output; filters DO NOT run. Pure WC-10 effect.

**Recommended for WC-10 v1**: filter-bypass mode. Reason: clean ablation. WC-10 vs 5-tier baseline is a single-intervention test. Filter-passthrough bin-then-filter introduces TWO interventions in one experiment.

## Defaults + config

New `TradingAgentsConfig` keys (3):
- `wc_10_enabled` (bool, default `False`) — operator opt-in via PARAMS.json
- `wc_10_filter_mode` (`Literal["bypass", "passthrough"]`, default `"bypass"`) — see modes above
- `wc_10_bin_thresholds` (`tuple[float, float, float, float]`, default `(-0.6, -0.2, +0.2, +0.6)`) — bin boundaries when filter_mode="passthrough"

When `wc_10_enabled = False`, the framework's existing 5-tier `PortfolioRating` enum behavior is unchanged. WC-10 is fully opt-in.

## Test grid + cost

**Grid**: 10 dates × 2 tickers (NVDA + AAPL — both with rich existing baseline corpora) = 20 propagates.

**Per-propagate cost**: ~$0.40 (Sonnet deep + Haiku quick) → **~$8 total**.

If WC-10 v1 surfaces interesting results, follow-up grid expansion to 5-ticker × 10-date = 50 propagates ~$20 (cumulative).

**Constitution III classification**: T1 (≤$5) initial pilot OR T2 ($5-30) full v1. Operator authorizes per gate.

## Validation gates

- **SC-001 (Schema correctness)**: when `wc_10_enabled=True`, `final_state["final_trade_decision"]` contains a numeric rating in [-1, +1]; signal_processor extracts the scalar via regex match. Verified by 3 unit tests covering boundary values + interior values.
- **SC-002 (Bin function deterministic)**: `bin_scalar_to_tier()` is a pure function with deterministic bin assignment. Verified by parametrized test over the 4 boundary thresholds.
- **SC-003 (Default-off integrity)**: when `wc_10_enabled=False`, framework behavior is identical to current 5-tier baseline. Verified by integration test comparing state log shapes.
- **SC-004 (Filter-bypass mode integrity)**: when `wc_10_filter_mode="bypass"`, no filter from the chain (A3 / spec 003 / 003.5 / 004 / 006 / 007 / 008 / X-1) runs. Verified by integration test.
- **SC-005 (Empirical pilot run on 20-propagate grid)**: 10 dates × 2 tickers; rating distribution is captured + analyzed. Headline metrics: (a) fraction of |rating| > 0.2 (= committed); (b) signed-rating × forward-α correlation; (c) bin-ex-post-to-5-tier and compare bucket means to existing baseline.
- **SC-006 (Comparison to 5-tier baseline)**: same (date, ticker) pairs run with WC-10 disabled (5-tier) for direct comparison. ~$8 additional cost; total experiment ~$16.
- **SC-007 (Falsification check)**: at least ONE of the 3 hypothesis predictions (NULL / ALT-A / ALT-B) must be empirically distinguishable post-run. If results are ambiguous across all 3, the experiment is INCONCLUSIVE and the cost was sunk noise.

## Dependencies + scope boundaries

**Dependencies**:
- `tradingagents.agents.schemas.PortfolioDecision` — schema change scope
- `tradingagents.graph.signal_processing.SignalProcessor` — needs scalar-aware extractor when `wc_10_enabled=True`
- `tradingagents.agents.managers.portfolio_manager` — minor branch on `wc_10_filter_mode`

**Out of scope**:
- 3-tier Trader rating (Trader still uses Buy/Hold/Sell — natural ternary)
- Memory log entry rating (still 5-tier; backward-compat with the existing 24-entry corpus)
- Bin threshold tuning study (defer to follow-up if v1 surfaces interesting results)
- Active mode that DOES bin-then-filter (defer; v1 is bypass-only)

## Constitution adherence

- **Principle II (One Experiment Per Change)**: SINGLE intervention — output schema changes from 5-tier categorical to continuous scalar. Filter ablation is intentional consequence, NOT a separate intervention.
- **Principle III (Stay Cheap)**: T2 ≤$30 well within budget; default-off prevents accidental cost.
- **Principle VI (Spec Before Structural Change)**: this draft + subsequent `/speckit.specify` invocation provide the spec-first discipline.
- **Principle VII (Calibrated Abstention)**: WC-10 directly tests whether the abstention is genuinely calibrated (signal-equivalent) vs categorical-bottleneck-induced (artifact). Either result is valid evidence.

## Pre-spec-invocation checklist

| Check | Status |
|---|---|
| EXPERIMENT.md Tier 2/3 survey identifies WC-10 as untouched | ✅ PR #97 |
| WC-10 test cost is operator-affordable | ✅ ~$8 v1 pilot, ~$16 full v1 |
| Schema change scope is bounded | ✅ 1 Pydantic model + 1 SignalProcessor branch |
| Filter portfolio compatibility resolved | ✅ bypass mode for v1 |
| Falsification criteria pre-stated | ✅ SC-007 + 3 hypothesis predictions |
| Backwards-compat with existing memory + state log shape | ✅ default-off; opt-in via PARAMS.json |
| `/speckit.specify` ready to invoke | ⚠️ requires operator authorization |

## What `/speckit.specify` will produce IF operator approves

Following the Spec X-1 precedent (PR #88 → #93 spec-kit 6-PR-bundle):
- New feature branch (e.g., `106-wc-10-continuous-scalar-rating`)
- `specs/<auto-numbered>-wc-10-continuous-scalar-rating/spec.md` with user stories, FRs (FR-001 through ~FR-008), success criteria (SC-001 through SC-007), edge cases, dependencies
- Subsequent spec-kit phases (`/speckit.plan` → `/speckit.tasks` → `/speckit.implement`) build on this

**Estimated total scope** (specify + plan + tasks + implementation + 20-propagate empirical pilot): 4-6h end-to-end + ~$16 LLM. Initial `/speckit.specify` invocation alone is ~1 PR worth (just spec.md).

## Reviewer notes

Operator may want to revise:

- **Bin thresholds** (currently `[-0.6, -0.2, +0.2, +0.6]`). Equal-width default; could use percentile-based defaults from the existing 65-run corpus instead.
- **Test grid size** (currently 10 dates × 2 tickers). Could expand to 5 tickers from start; or shrink to 5 dates × 2 tickers for cheaper pilot.
- **Comparison to 5-tier baseline** (currently SC-006). Could skip if existing 65-run corpus provides sufficient implicit baseline.
- **Filter-bypass vs filter-passthrough as v1 mode**. PR #97 recommended bypass for cleanness; passthrough has the operational advantage of preserving filter-portfolio behavior.

## What this draft is NOT

- NOT a commit to launching WC-10
- NOT a spec.md
- NOT a recommendation that operator MUST act
- The planning artifact that lets operator decide whether to advance Tier 2 work or stay in deferred-gate-only mode

## Sibling docs

- `claudedocs/experiment-md-tier-2-3-status-2026-05-08.md` — PR #97 survey identifying WC-10 as the recommended next experimental arc
- `claudedocs/spec-x-1-c4-institutional-rotation-feature-description-2026-05-07.md` — PR #87 precedent for this draft pattern
- `docs/EXPERIMENT.md` — original brainstorm (Tier 2 description)
- `RESEARCH_FINDINGS.md` — Constitution VII Calibrated Abstention thread
- `experiments/2026-05-03-003-single-call-baseline-nvda/` — closest existing experiment (architecturally adjacent)
