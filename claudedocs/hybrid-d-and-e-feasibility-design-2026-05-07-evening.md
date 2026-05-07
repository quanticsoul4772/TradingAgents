# Hybrid D + Hybrid E feasibility + design sketch — 2026-05-07 evening

**Goal**: Design + feasibility analysis for two candidate forward-catalyst-class
filter extensions surfaced by today's sweep + deep-dives:

- **Hybrid D — both-sides-priced-in suppressor** (motivated by PR #41
  sub-pattern 3 + PR #43/F-2 cross-reference)
- **Hybrid E — asymmetric-setup amplifier** (motivated by PR #43
  sub-pattern 4 / AMD-04-17 finding)

Both would extend Spec 007's bull/bear architecture by combining the two
priced-in scores in different ways. Neither is being implemented today —
this is design work + retrospective sketch only, gated on Constitution
VIII v1.4.1 retrospective-first methodology.

## Hybrid D: both-sides-priced-in suppressor

### Mechanism class

When BOTH `bull_case_priced_in` AND `bear_case_priced_in` are above their
respective thresholds, the LLM is reading the analyst+debate ensemble as
"both sides have already digested the news; no fresh edge to either
direction." In this regime, ANY commit (Buy/OW or UW/Sell) is likely to
chase already-absorbed information — the consensus is exhaustion, not
opportunity.

Hybrid D would suppress ALL commits (Buy, OW, UW, Sell) to Hold when
the both-sides-priced-in condition is met. Operationally this is a
mode-collapse-toward-Hold filter, but mechanistically distinct from the
existing PM Hold-regime — Hybrid D is rule-based and predictable; PM
Hold is emergent behavior from the analyst+debate synthesis.

### Candidate empirical cohort (5-7 cases identified)

From PR #41 sweep + PR #46 deep-dive cross-references:

| Ticker / Date | bull_score | bear_score | sum | PM rating | Notes |
|---|---|---|---|---|---|
| MSFT/2026-04-24 | 0.55 | 0.65 | 1.20 | Hold | Sub-pattern 3 case |
| NVDA/2026-04-24 | 0.82 | 0.55 | 1.37 | Hold | Sub-pattern 3 case (pre=OW; spec 007 bull actually FIRED here) |
| WFC/2026-04-17 | 0.45 | 0.70 | 1.15 | Hold | Sub-pattern 3 case |
| COP/2026-04-17 | 0.55 | 0.50 | 1.05 | Underweight | Boundary case |
| COP/2026-04-24 | 0.65 | 0.50 | 1.15 | Hold | Boundary case |

Spec 007's score architecture allows sums > 1 (the two scores are
independent per PR #41 sub-pattern 4 finding). The above 5 rows have
`sum ≥ 1.05` AND `min(bull, bear) ≥ 0.45` — a reasonable definition of
"both sides priced in."

### Hybrid D candidate threshold

Two configurable shapes:
- **Sum-based**: `bull_score + bear_score > T_sum` (default candidate
  T_sum=1.10)
- **Min-based**: `min(bull_score, bear_score) > T_min` (default
  candidate T_min=0.50)

Sum-based fires more aggressively (catches asymmetric mid-mid pairs);
min-based requires both individually high.

Of the 5 candidates above, sum-based at T=1.10 fires on 4 of 5; min-based
at T=0.50 fires on 4 of 5 (different overlap). Both would suppress
commits to Hold.

### Constitution VIII v1.4.0 retrospective gate (REQUIRED before spec)

Before invoking `/speckit.specify` for Hybrid D, the retrospective gate
needs:
1. **Discrim ≥ +5pp** (cohort hit-rate vs FP cohort hit-rate)
2. **Cohort hit rate ≥ 60%** (% of suppressed commits where realized α
   would have been negative for the suppressed direction)
3. **Net Δα ≥ +0.5pp** (suppressed cohort's realized α magnitude)

OR shadow-mode-first launch if criteria 1+2 pass without 3.

**Cohort size constraint**: only 5 candidates today. Constitution VIII
typically targets n≥30 for forward-catalyst-class retrospectives. Hybrid
D retrospective is **NOT YET RUNNABLE** — defer until cohort grows to
n≥15-20 via more SC-009-class backtests OR via 50-ticker SC-003-class
runs.

**Path forward**: when SC-009 finishes, count how many additional Hybrid
D candidate cases land. If finishing rows add ≥5 more candidates → bring
cohort to n≥10 → run preliminary retrospective (smaller-than-ideal sample
warning) → decide on shadow-mode launch.

### Constitution VIII v1.4.3 additive-gate (would also apply)

Hybrid D's mechanism (rule-based both-sides-priced-in suppression) is
DISTINCT from existing default-active filters:
- A3: backward-price (ticker DOWN >5%)
- Spec 003: prose-density percentile
- Spec 007 bull/bear: LLM-extracted single-direction priced-in
- Spec 008: calendar-boosted Spec 007 bull

Hybrid D operates on the JOINT (bull, bear) score pair, not any single
score or backward-price feature. Mechanism-additive per the v1.4.0
forward-catalyst-class gate.

But the v1.4.3 standard "operational fires" overlap question still
applies: do Hybrid D fires correlate with existing filter fires? The
cohort is too small to compute meaningful overlap statistics today —
deferred to the eventual retrospective.

### Implementation sketch

```python
# tradingagents/agents/utils/joint_priced_in_filter.py (new module, ~80 LOC)

def evaluate_joint_priced_in(
    bull_score: float,
    bear_score: float,
    pre_rating: str,
    config: dict,
) -> dict:
    """Return state annotation for Hybrid D joint priced-in suppression.

    Reads config:
      hybrid_d_mode: off | shadow | active (default off)
      hybrid_d_sum_threshold: float (default 1.10)
      hybrid_d_min_threshold: float (default 0.50)
      hybrid_d_aggregate: 'sum' | 'min' (default 'sum')
    """
    ...
    return {
        "mode": ...,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "joint_metric": ...,  # sum or min
        "threshold": ...,
        "would_fire": ...,
        "fired": ...,
        "pre_rating": pre_rating,
        "post_rating": ...,
    }
```

Ordering (FR-012 chain extension): A3 → spec 006 → spec 003/003.5 →
spec 004 → spec 007 → spec 008 (inside 007) → **Hybrid D (LAST)**.
Hybrid D is the most aggressive filter — it suppresses across both
directions — so it must run last to avoid pre-empting other filters'
fires.

State annotation: new `state["joint_priced_in"]` field, same persistence
pattern as `forward_catalyst`.

### v1.4.4 behavioral-additive consideration

Hybrid D's would-fire condition can ALSO trigger behavioral-additive
analysis: does the PM (without Hybrid D) commit Hold on rows where
`bull + bear > 1.10`? Per the candidate cohort table above, 4 of 5 (MSFT,
NVDA, WFC, COP-04-24) have `pm_rating = Hold` — high behavioral-additive
correlation. So Hybrid D is BOTH cohort-additive AND behavioral-additive
per v1.4.4 (when it ratifies).

## Hybrid E: asymmetric-setup amplifier

### Mechanism class

OPPOSITE direction from Hybrid D. Sub-pattern 4 from PR #43 (AMD-04-17)
identifies **asymmetric** setups: bull case fully priced in (score high),
bear case still has runway (score low) → favors bear-direction commit.
Or symmetrically, bear fully priced in + bull case fresh → favors
bull-direction commit.

Hybrid E would AMPLIFY the side with fresh edge:
- If `bull_score - bear_score ≥ T_asymmetric AND bear_thesis_fresh`:
  amplify bear-side commit (suppress UW→Sell, or boost bear-side fire
  threshold sensitivity)
- If `bear_score - bull_score ≥ T_asymmetric AND bull_thesis_fresh`:
  amplify bull-side commit (boost bull-side fire threshold sensitivity)

This is fundamentally different from Hybrid D (suppression) — Hybrid E
is a confirmation-amplifier for high-conviction asymmetric setups.

### Candidate empirical cohort (n=1)

Only AMD-04-17 (PR #43 sub-pattern 4):
- bull_score = 0.85 (very high)
- bear_score = 0.40 (well below T_bear=0.50)
- diff = 0.45 (asymmetric)
- PM committed UW (correctly aligned with bear-side fresh edge)

AMD-04-24 also fits but with calendar boost engaged (effective_bull=0.94)
and even more asymmetric (effective diff = 0.54). Strongest single-ticker
case.

### Hybrid E feasibility verdict: **TOO EARLY**

Cohort is critically thin (n=1 base + n=1 boosted = 2 rows total). No
retrospective gate possible. **No spec invocation justified per
Constitution VIII v1.4.0.** Record as future-work candidate — when
cohort grows to n≥10 via expanded backtests, re-evaluate.

The conceptual framing is interesting (consensus-vs-fresh-edge dichotomy
generalizes the contrarian-vs-momentum spectrum), but the empirical
foundation is one ticker × two dates today.

## Combined assessment

| Filter | Mechanism class | Candidate cohort | Retrospective runnable? | Spec-invocation status |
|---|---|---|---|---|
| Hybrid D (suppressor) | Joint LLM-extracted | 5 candidates | NO (n<10) | DEFER — gather more cohort |
| Hybrid E (amplifier) | Joint asymmetry | 1 candidate | NO (n<10) | DEFER — gather much more cohort |

**Recommendation**: defer both specs until SC-009 completes and the
SC-009-expansion experiment kicks off (if triggered) to grow the candidate
pool. Re-run this design doc after the next backtest's state logs are
available.

## Implementation sequence (when ratified)

If Hybrid D retrospective eventually passes (criteria 1+2 minimum, with
shadow-mode-first per Constitution VIII v1.4.0):

1. **Spec 010**: `/speckit.specify hybrid-d-joint-priced-in-suppressor`
2. Helper module: `tradingagents/agents/utils/joint_priced_in_filter.py`
3. Integration in PM hook chain after spec 008
4. State annotation: `state["joint_priced_in"]`
5. New TradingAgentsConfig keys: `hybrid_d_mode`, `hybrid_d_sum_threshold`,
   `hybrid_d_min_threshold`, `hybrid_d_aggregate`
6. Default mode: shadow (per Constitution VIII v1.4.0 shadow-mode-first
   for hybrid filters until live-validated)
7. Tests: ~10 unit tests (joint metric computation + boundary semantics +
   firing logic) + 4 integration tests (PM hook + state-log persistence
   + default-off integrity + ordering-correctness)
8. Live smoke: 1 propagate at $0.05; verify state log
9. Empirical retrospective re-validation script: re-run on extended
   cohort

Hybrid E remains backlog until cohort grows.

## Followups (deferred)

1. **Re-run this design doc after SC-009 completes** to update candidate
   cohort counts. ~5min, $0.
2. **Create `experiments/2026-05-07-002-sc-009-expansion/` if D-1 trigger
   met** to grow Hybrid D candidate pool to n≥10. ~5h compute, ~$15.
3. **Consider `daily_signals.py` instrumentation enhancement** to track
   Hybrid D + E candidate cohorts in operational use, surfacing future
   candidates without explicit backtest runs. ~30min, $0. Defer.

## Sibling docs

- `claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md` —
  PR #41 sweep that surfaced sub-pattern 3 (Hybrid D kernel)
- `claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md` — PR #43 that
  surfaced sub-pattern 4 (Hybrid E kernel)
- `claudedocs/amd-2026-04-24-deep-dive-2026-05-07-evening.md` — PR #46
  that strengthened sub-pattern 4 with AMD-04-24 calendar-boost case
- `claudedocs/research-burst-2026-05-08.md` — tomorrow's scaffold;
  D-1 expansion-trigger criteria reference Hybrid D candidate growth
- `.specify/memory/constitution.md` — Constitution VIII v1.4.0 (forward-
  catalyst-class retrospective gate) + v1.4.3 (additive-to-existing-filter
  gate)
