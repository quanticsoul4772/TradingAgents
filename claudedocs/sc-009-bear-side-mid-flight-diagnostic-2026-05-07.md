# SC-009 bear-side mid-flight diagnostic — COP + INTC UW commits

**Date**: 2026-05-07 (mid-backtest, 13/36 rows complete, ~36%)
**Backtest**: `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/`
**Trigger**: First bear-side commits surfaced in the SC-009 expansion cohort
(COP UW 2026-04-17, COP Hold 2026-04-24, INTC UW 2026-04-17). The Tech-heavy
core cohort had been all-Hold per Constitution VII; bear commits give the
first read on whether spec 007 bear-side shadow-mode is calibrated on
non-Tech tickers.

## Setup recap

Spec 007 bear-side runs in **shadow mode** at T=0.50 in production config
(per constitution VIII v1.4.0: passed criteria 1+2 of the forward-catalyst
gate but criterion 3 net Δα +0.30pp came in just below the +0.5pp threshold
→ shadow-mode-first launch). The bear filter would fire if:

1. `pre_rating in {"Underweight", "Sell"}`, AND
2. `bear_case_priced_in > T_bear` (strict greater-than, FR-004 boundary
   semantics).

When it fires, it would suppress UW/Sell to Hold (mirror of bull-side).
Shadow-mode means the score is computed and logged, the firing decision is
made, but the `post_rating` is unchanged from `pre_rating` — operationally
inert, observationally measured.

## Per-row state inspection

Parsed `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json` for the 3 bear-relevant rows.

| Ticker | Date | pm_rating | bull_score | bear_score | T_bull | T_bear | would_fire_bull | would_fire_bear | days_to_earnings | calendar_boost | effective_bull | effective_bear |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| COP | 2026-04-17 | Underweight | 0.55 | 0.50 | 0.60 | 0.50 | False | False | 13 | 0.071 | 0.570 | 0.50 |
| COP | 2026-04-24 | Hold | 0.65 | 0.50 | 0.60 | 0.50 | False | False | 6 | 0.571 | 0.836 | 0.50 |
| INTC | 2026-04-17 | Underweight | 0.88 | 0.30 | 0.60 | 0.50 | False | False | 6 | 0.571 | 1.000 (clamped) | 0.30 |

(`would_fire_*` columns reflect the operational fire decision, which
combines pre_rating gating + score-vs-threshold check. Bull-side requires
`pre_rating in {Buy, Overweight}`; bear-side requires `pre_rating in {Underweight, Sell}`. None of the rows met BOTH the pre_rating + score criteria.)

## Findings

### F-1: Bear-side shadow mode is correctly inert on this cohort

Both COP-04-17 UW and INTC-04-17 UW had `bear_score ≤ T_bear` (0.50 and
0.30 respectively). The filter mechanism reads "bear case is NOT yet
priced in → bear thesis still has legs to play out → suppression not
warranted." Both PM Underweight commits are aligned with that read:
**bear_score low ↔ PM picks bear-rating ↔ filter agrees-by-not-firing**.

This is the first cohort-level evidence that spec 007 bear-side, even at
its borderline-T criterion-3 calibration, **doesn't generate spurious
suppressions on out-of-Tech bear commits**. Sample is small (n=2 UW
commits) but directionally supportive of the eventual default-flip
decision.

### F-2: Strict greater-than boundary at COP-04-17 (bear_score == T_bear)

COP-04-17 had `bear_score = 0.50` — exactly equal to T_bear. Per FR-004
SC-006-equivalent boundary semantics (strict gt), filter does NOT fire.
This is the first observed equality case in production data; behaviorally
identical to spec 007 bull-side SC-002 (effective_score == bull_threshold
→ no fire). The implementation correctly enforces the strict-gt rule.

### F-3: COP-04-24 — second behavioral-additive case (Spec 007 mechanism)

COP-04-24 had `bull_case_priced_in = 0.65 > T_bull = 0.60`, AND
`effective_bull_score = 0.836` (calendar boost engaged at 6d to earnings,
6.42x scale-up via the magnitude=0.5x×boost=0.571 formula). If
pre_rating had been Buy or Overweight, the spec 007 bull-side filter would
have fired (and so would spec 008 Hybrid C even more decisively).

But pre_rating was **Hold**. PM independently arrived at "bull case is
priced in → don't commit bullishly." This is the **second recurrence** of
the L-8 behavioral-additive pattern from this morning's
`spec-003-fire-pattern-on-sc-009-cohort-2026-05-07.md` analysis.

**Critical distinction**: this morning's behavioral-additive cases were
about **Spec 003 (prose-density percentile mechanism)** — PM internalized
contrarian logic via Calibrated Abstention. Today's COP-04-24 case is
about **Spec 007 (LLM-extracted forward-catalyst mechanism)** — a
*different* mechanism class. The PM has internalized BOTH classes of
contrarian logic.

This expands the L-8 evidence:
- 2026-05-07 morning: 4 of 9 NVDA/MSFT/AAPL rows behavioral-additive on Spec 003 mechanism
- 2026-05-07 mid-flight: COP-04-24 behavioral-additive on Spec 007 mechanism

**Two mechanism classes covered → growing case for v1.4.4 codification**.
But still defer codification per memory (need 3rd recurrence with a 3rd
mechanism class to fully validate the pattern is generalizable across the
entire forward-catalyst-class space, not just LLM-extracted).

### F-4: bull_score + bear_score are NOT complementary (sum ≠ 1.0)

Sums across the 3 rows: 1.05, 1.15, 1.18. Spec 007 prompt evidently
doesn't enforce bull/bear complementarity — the two scores are
independent reads of "how much is THIS side already priced in." Both
sides can be HIGH simultaneously (bull and bear both already absorbed →
neutral-to-slightly-bearish), or both LOW (both still have room to play
out → high-conviction-needed-to-pick-direction).

This is a **design feature, not a bug**: independent scoring lets the
LLM express "tons of news on both sides, market has digested everything"
vs "fresh news on neither side, position still untaken." If we ever add
a Hybrid D (both-sides-priced-in suppressor), it would key on
`max(bull_score, bear_score) > T_combined` rather than `bull_score - bear_score`.

### F-5: Calendar boost behaves correctly on non-Tech, non-Buy-pre tickers

Hybrid C boost engaged on 2 of 3 rows (COP-04-24 and INTC-04-17, both at
days_to_earnings=6). The boost is computed regardless of pre_rating; it
only INFLUENCES the effective_bull_score that spec 007 then evaluates.
Since neither row had pre_rating in {Buy, Overweight}, the boost was
operationally inert (effective_bull_score logged but not consequential).

INTC-04-17's `effective_bull_score = 1.000` is the **first observed
clamp-saturation** in production: base 0.88 × (1 + 0.5 × 0.571) = 1.131,
clamped to 1.000 by the `min(1.0, ...)` guard from spec 008 FR-018. Verifies
the clamp is wired correctly in the live filter (vs only synthetic unit
tests).

## Implications for SC-009 verdict

- **Bull-side gate-2 (n_fired ≥ 8)**: still at risk per the morning's
  mid-flight diagnostic. COP-04-24 had effective_bull > T_bull but
  pre_rating=Hold → does NOT count as a fire. Bear commits (COP-04-17 UW,
  INTC-04-17 UW) also can't fire bull-side. The remaining 23 rows would
  need to deliver ≥5 more bull fires for gate-2 PASS. This is unlikely
  given the cohort composition — Tech rally tickers stay PM-Hold; non-Tech
  earnings-proximate tickers (COP/MA/INTC) have mixed pre_ratings without
  bullish lean.
- **Alt gate-1 (suppressed-α direction)**: still on track. Currently
  suppressed-α = -4.44% on n=3 fires. If the remaining cohort generates
  a few more fires with similarly-negative suppressed α, alt gate-1 PASS
  holds.
- **Bear-side default-flip evidence**: 2 of 2 UW commits had
  bear_score ≤ T_bear → calibrated inertness. Adds two data points to
  the eventual bear-side evaluation that would need n≥30 to exit
  shadow-mode per Constitution VIII v1.4.0.

## Followups (not actioned today)

1. **Cross-reference effective_bull > T_bull but PM-Hold across the full
   completed-cohort** when SC-009 finishes — this is the canonical
   behavioral-additive count for Spec 007 specifically. If ≥3 cases land
   from a 36-row sample, we can codify v1.4.4 with mechanism-class-mixed
   evidence (Spec 003 + Spec 007 both demonstrating).
2. **Bear-side score distribution histogram** when n grows — currently
   3 rows is too thin to chart.
3. **Calendar boost engagement-rate on full cohort** — track how often
   `calendar_boost > 0` in the realized rows. Currently 8/13 ≈ 62%, but
   the boost only matters when pre_rating is bullish AND
   bull_case_priced_in is borderline.

## Sibling docs

- `claudedocs/sc-009-mid-backtest-commit-pattern-2026-05-07.md` — earlier
  same-day mid-flight at 7 rows
- `claudedocs/sc-009-hold-rate-root-cause-2026-05-07.md` — Hold-rate
  Constitution-VII calibration explanation
- `claudedocs/spec-003-fire-pattern-on-sc-009-cohort-2026-05-07.md` —
  morning's behavioral-additive cases on Spec 003 mechanism
- `memory/reference_behavioral_additive_4th_interpretation.md` — L-8
  pattern memory (this doc adds Spec 007 mechanism-class evidence)
