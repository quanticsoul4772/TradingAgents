# Spec 007 calendar-independence — BAC + GS 80+ days from earnings fire empirically

**Trigger**: PR #53 followup — "BAC + GS at 80+d fire pattern analysis."
3 Financials bull-pre rows (BAC×2 + GS-04-17) all fire WITHOUT calendar
boost engagement (days_to_earnings outside 14d window). Investigates
spec 007 vs spec 008 mechanism separation empirically.

## Side-by-side state logs

| Ticker | Date | pre | post | bull_score | bear_score | days_to_earnings | calendar_boost | effective_bull | fired_bull | spec_003_percentile |
|---|---|---|---|---|---|---|---|---|---|---|
| BAC | 2026-04-17 | Overweight | Hold | 0.65 | 0.35 | **88** | **0.000** | 0.65 | True | None |
| BAC | 2026-04-24 | Overweight | Hold | 0.70 | 0.35 | **81** | **0.000** | 0.70 | True | None |
| GS | 2026-04-17 | Overweight | Hold | 0.65 | 0.45 | **88** | **0.000** | 0.65 | True | None |

**Common pattern**:
- All 3 are Financials bull-pre commits (Overweight)
- All 3 fired (post = Hold)
- All 3 have base bull_score in 0.65-0.70 range — modestly above T_bull=0.60
- All 3 have bear_score 0.35-0.45 (well below T_bear=0.50; bear correctly inert)
- All 3 are 81-88 days from earnings — FAR outside spec 008's 14d boost window
- All 3 had spec 003 baseline=none (cold-start universe; same as AMZN F-5 from PR #50)

## Finding F-1: Spec 007 fires independently of calendar proximity

The 3 Financials cases empirically demonstrate spec 007's mechanism is
**LLM-extracted bull-priced-in score crossing T_bull = 0.60**, full stop.
The calendar boost (spec 008) is a mechanism-INDEPENDENT enhancement; it
modifies the score before threshold check but doesn't gate firing.

This validates the spec design: spec 007 = "is the bull case priced in
right NOW (per LLM)" → fires when answer is yes. spec 008 = "is the
near-earnings amplification regime engaged" → adds magnitude when yes.
Two separable mechanisms.

Operationally: any bull commit with sufficient bull-priced-in evidence
(per LLM) gets suppressed regardless of when earnings happens. This is
robust calibration, not earnings-event-driven calibration.

## Finding F-2: All 9 bull-pre fires have base bull_score > T_bull

Sweeping across all 9 bull-pre fires in the SC-009 cohort:

| # | Ticker / Date | base bull_score | days_to_E | boost engaged | effective_bull |
|---|---|---|---|---|---|
| 1 | AMZN-04-17 | 0.78 | 12 | YES (0.143) | 0.836 |
| 2 | **BAC-04-17** | **0.65** | **88** | **no** | **0.65** |
| 3 | **BAC-04-24** | **0.70** | **81** | **no** | **0.70** |
| 4 | GOOGL-04-17 | 0.70 | 12 | YES (0.143) | 0.75 |
| 5 | GOOGL-04-24 | 0.78 | 5 | YES (0.643) | 1.00 (clamp) |
| 6 | **GS-04-17** | **0.65** | **88** | **no** | **0.65** |
| 7 | MA-04-17 | 0.70 | 13 | YES (0.071) | 0.725 |
| 8 | MA-04-24 | 0.72 | 6 | YES (0.571) | 0.926 |
| 9 | NVDA-04-24 | 0.82 | 26 | no | 0.82 |

**ALL 9 base bull_scores exceed T_bull=0.60**. NO fire required boost
to cross threshold. The minimum base is 0.65 (BAC-04-17 + GS-04-17),
already 5pp above the threshold floor.

## Finding F-3: Boost-ON vs Boost-OFF would produce IDENTICAL fire decisions

The analyzer's "Decisions changed by boost: 0" output is now
**mechanistically explained**:

- 4 of 9 fires have boost = 0 (irrelevant — would fire either way)
- 5 of 9 fires have boost > 0 but base score already above T_bull
  (incremental enhancement only — not threshold-crossing)
- 0 of 9 fires required the boost to push borderline-below-threshold
  → above-threshold

Net Δα improvement from boost on this cohort: **0** (zero decisions
changed → zero α difference between boost-ON and boost-OFF universes).

## Finding F-4: This refines the SC-009 verdict story

The Hybrid C retrofit (PR #44 v1.4.4 draft empirical basis) showed
+3.35pp net Δα improvement on a backtest with DIFFERENT bull_score
distribution. In that retrofit, the boost was rescuing borderline-
below-threshold scores → above threshold. The SC-009 cohort doesn't
exhibit this: bull_scores cluster in [0.65, 0.85] — comfortably above
threshold without help.

This means SC-009's PRELIMINARY PASS verdict is technically
"PASS-by-non-counterexample" rather than "PASS-by-active-improvement":
- Gates 2 + 3 PASS (count-based, robust)
- Gate 1 (alt suppressed-α direction) PASS by negation (suppressed α
  doesn't go strongly positive); not by demonstrating α improvement
- The boost mechanism never engaged decision-relevant boundaries → no
  α delta to measure

For the eventual default-flip decision, this changes the framing:
- **Best case (boost mechanism is correctly inert here)**: Hybrid C
  is mechanism-correct but cohort-irrelevant on extended-rally Tech +
  Financials at-or-above-threshold cohort. Default-on flip is safe
  because the boost can't cause harm here.
- **Worst case (cohort selection bias)**: SC-009 cohort happens to
  have bull_score distribution that doesn't exercise the borderline
  regime where the retrofit showed value. Default-on flip on this
  evidence is premature.

The right answer is probably: **shadow-mode-first** per Constitution
VIII v1.4.0 — observe Hybrid C in production for n≥30 propagates with
varied bull_score distributions before flipping default-on. Add to
tomorrow's SC-009 ANALYSIS.md framing.

## Finding F-5: Spec 003 cold-start affects Financials too

BAC×2 + GS-04-17 all show `spec_003_baseline = none, percentile = None`.
Same pattern as AMZN-04-17/24 from PR #50 F-5. Spec 003.5 sector-baseline
fallback is unable to engage on these tickers — likely because the
Financials sector pool is empty (only WFC has prior history; not enough
to populate the pool).

Strengthens PR #50 followup: spec 003.5 instrumentation needs better
"why baseline = none" reporting. Multiple tickers (AMZN, BAC, GS) hit
this state.

## Implications

1. **For SC-009 verdict (independent of v1.4.4)**: shadow-mode-first
   recommendation gains weight. Default-on flip should wait for
   bull_score distribution that exercises the borderline regime.

2. **For spec 008 mechanism design validation**: confirms spec 008 is
   correctly mechanism-INDEPENDENT of spec 007 firing. Boost is purely
   additive enhancement, never a fire prerequisite. This validates the
   FR-012 design (spec 008 INSIDE spec 007).

3. **For v1.4.4 ratification**: independent. v1.4.4 is about
   behavioral-additive multi-mechanism-validator framing of the
   Constitution v1.4.3 additive gate, not about boost mechanism
   specifics. v1.4.4 still UNBLOCKED on counter-evidence axis.

4. **For RESEARCH_FINDINGS.md (post-SC-009)**: cross-sector empirical
   validation of spec 007 calendar-independence belongs in the
   findings; it's a distinct empirical claim from the SC-009 ablation
   verdict.

## Followups

1. **SC-009 ANALYSIS.md framing update**: add "shadow-mode-first
   recommendation" framing per F-3/F-4. Defer to tomorrow.
2. **Spec 003.5 cold-start universe diagnostic** (recurring; AMZN +
   BAC + GS all hit it): build a small audit to enumerate which
   ticker × sector cells lack baseline. ~30min, $0. Defer.
3. **Bull_score distribution histogram across full corpus**: how often
   does the borderline regime (bull_score in [0.55, 0.65]) occur?
   Drives the "is shadow-mode-first the right call?" answer. ~15min,
   $0 once SC-009 finishes.

## Sibling docs

- `claudedocs/sc-009-27-row-mark-and-sweep-refresh-2026-05-07-late.md`
  — PR #53 sweep refresh; this doc closes followup
- `claudedocs/constitution-v1.4.4-draft-2026-05-07.md` — PR #44 draft;
  independent of this finding
- `claudedocs/sc-009-23-row-mark-trajectory-pass-2026-05-07-evening.md`
  — PR #51 verdict trajectory analysis
- `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md`
  (yesterday) — original retrofit that showed +3.35pp on different
  cohort distribution
