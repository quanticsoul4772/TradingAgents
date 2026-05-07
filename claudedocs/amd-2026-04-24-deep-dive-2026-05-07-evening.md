# AMD 2026-04-24 deep-dive — TRIPLE behavioral-additive + PM doubling-down despite +25% in 1 week

**Date**: 2026-05-07 evening (mid-backtest, 20/36 rows)
**Backtest**: `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/`
**Context**: 5th bear-side commit; pairs with PR #43 AMD-04-17 deep-dive
to give 2-week temporal robustness picture for AMD.

## Side-by-side comparison with AMD-04-17

| Field | AMD-04-17 | AMD-04-24 | Δ |
|---|---|---|---|
| Stock price (open) | ~$278 | ~$347.81 | **+25.1%** |
| pm_rating | Underweight | Underweight | same |
| bull_case_priced_in | 0.85 | 0.85 | same |
| bear_case_priced_in | 0.40 | 0.40 | same |
| Spec 003 percentile | 72.4 | **98.02** | **+25.6pp** |
| Spec 003 gate_baseline | sector | sector | **same (NOT a baseline switch)** |
| days_to_earnings | 18 | 11 | -7 |
| calendar_boost | 0.0 (outside window) | 0.214 | engaged |
| effective_bull | 0.85 | **0.94** | +0.09 |
| Behavioral-additive (operational fires) | Spec 007 bull only (1 class) | **Spec 003 + Spec 007 bull + Spec 008 (3 classes)** | +2 |

**Critical**: AMD ROSE +25% in 5 trading days following the AMD-04-17 UW call.
PM's UW thesis was OPERATIONALLY WRONG over the 5-day window — yet PM
DOUBLED DOWN with an even more aggressive UW framing on 04-24.

## State-log highlights

### Forward catalyst (Spec 007/008)

```
bull_case_priced_in:  0.85           (highest in SC-009; tied AMD-04-17)
bear_case_priced_in:  0.40           (well below T_bear=0.50)
days_to_earnings:     11             (INSIDE window=14 → boost engaged)
calendar_boost:       0.214          (= 1 - 11/14)
effective_bull:       0.941          (= 0.85 × (1 + 0.5 × 0.214))
effective_bear:       0.40           (no boost on bear-side)
pre_rating:           Underweight
fired_bull:           False          (pre is UW, not Buy/OW)
fired_bear:           False          (bear_score 0.40 < T_bear)
```

### Spec 003 contrarian gate

```
percentile:           98.02          (well above 80 threshold)
gate_baseline:        sector         (still sector, NOT per-ticker)
threshold:            80
fired:                None           (pre is UW, not Buy/OW)
```

The 98th-percentile reading means AMD's bull_keyword_count is in the top 2%
of the sector aggregation pool for THIS week. AMD-04-17 was at the 72nd
percentile. **The pool composition didn't change — AMD's bull_keyword_count
itself spiked massively in the week's news flow** (consistent with PM's
"70% parabolic rally" framing — rallies generate more bullish coverage).

## PM final_trade_decision excerpts

> "Reduce AMD to 50–60% of current allocation immediately, prioritizing
> execution before the May 5 Q1 2026 earnings print."

> "The risk/reward at ~$347.81 is negatively asymmetric: RSI at 88.94,
> a 70% one-month parabolic rally, $70.6M in insider selling at peak
> prices, and a 43–50x forward P/E on conservative $8–9 2026 EPS leaves
> virtually no margin for guidance error."

> "Establish downside protection via $310/$280 put spreads expiring late May;
> begin rebuilding a full position in tranches at $300–310, $275–285, and
> $255–265, targeting a 12–18 month price [target]."

> **"The prior AMD lesson itself validates the trim discipline: the
> underweight call at $278 captured the inflection correctly, and the
> same setup is present again at a higher absolute price with even more
> stretched technicals."**

> "Price Target: 310.0"

## Findings

### F-1: PM's "captured the inflection correctly" claim is OPERATIONALLY WRONG

PM explicitly self-validates: "the underweight call at $278 captured
the inflection correctly." But AMD went $278 → $347.81 = **+25.1%** in
the 5-trading-day window between the AMD-04-17 call and AMD-04-24
propagation. That is the OPPOSITE of the inflection PM thinks it caught.

Three possible explanations:
1. **Memory log staleness**: AMD-04-17's pending entry hasn't resolved
   yet (memory log resolves on the NEXT same-ticker run, but the
   resolution computes alpha vs SPY at 5d holding window — which is the
   exact window that just elapsed). PM may be working from a HALLUCINATED
   "successful prior call" prior, OR
2. **Different prior AMD memory entry**: PM may be referencing an
   AMD memory entry from outside the SC-009 cohort (memory log persists
   across all runs), OR
3. **PM hallucination on prior outcome**: PM may be conflating "we
   correctly identified bull-priced-in conditions" (mechanistically true
   per state log) with "the trade was profitable" (operationally false).

This is a notable finding for v1.4.4 ratification: **PM's textual
validation of contrarian logic does NOT depend on PM being operationally
correct about realized α**. The multi-mechanism-validator framing is
about WHAT PM commits, not WHETHER PM is right post-hoc. AMD-04-24
shows PM DOUBLING DOWN on UW even though the prior week's UW was
operationally wrong (over the 5-day window — the 21-day window is still
open and may yet vindicate the call).

### F-2: TRIPLE behavioral-additive case — strongest in the corpus

AMD-04-24 hits THREE mechanism classes' would-fire-if-bullish-pre
conditions simultaneously:

| Mechanism | Score | Threshold | Would-fire-if-pre-Buy/OW? |
|---|---|---|---|
| Spec 003 contrarian | 98.02 percentile | 80 | YES (well above) |
| Spec 007 bull | 0.85 | 0.60 | YES (well above) |
| Spec 008 calendar-boosted | 0.941 effective | 0.60 | YES (well above) |

All three would suppress Buy/Overweight to Hold. None operationally fire
because pre_rating=Underweight (filters fire on Buy/OW pre-rating only).
PM independently picked Underweight — STRICTER than what any of the three
filters would have suppressed to.

This is the **strongest behavioral-additive case in the corpus to date**:
3 of 4 mechanism classes simultaneously aligned, with PM committing in
the SAME direction (and farther). MSFT-04-24 has the only 4-mechanism
hit in the sweep, but on a Hold rating not stricter-than-Hold.

### F-3: PR #45 followup partly resolved — NOT a baseline switch

PR #45 sweep refresh observed AMD's spec_003_percentile jumping
72.4 → 98.0 in one week and recorded as followup: "most likely
per-ticker baseline crossed FR-004 N≥20 floor (sector → per-ticker
switch)." **REFUTED**: both AMD-04-17 and AMD-04-24 show
`gate_baseline: sector`. The 25.6pp percentile jump is genuine
movement against the SAME baseline pool, not a baseline-switch
artifact.

The most likely explanation now is **AMD's bull_keyword_count itself
spiked** in the week's news flow (consistent with PM's "70% parabolic
rally" framing — extended rallies generate more bullish coverage and
thus more bull_keyword_count). The sector pool's distribution stayed
roughly stable; AMD pushed deep into its right tail.

This refutation matters for v1.4.4 ratification: the "AMD anomaly" from
PR #45 is NOT a measurement artifact — it's a real signal-strength
movement that PM also independently validated via prose. Strengthens,
not weakens, the v1.4.4 evidence base.

### F-4: Calendar boost engaged this week (was inert at AMD-04-17)

AMD-04-17 had days_to_earnings=18 (outside boost window), so calendar
boost was 0 and effective_bull = base_bull. AMD-04-24 has
days_to_earnings=11 (inside window), so boost=0.214 and
effective_bull = 0.85 × 1.107 = 0.941.

This shows spec 008 boost engaging consistently as the cohort approaches
earnings. PM explicitly says "execute before May 5 Q1 2026 earnings
print" — calendar awareness is in the PM regardless, and the spec 008
boost mechanism is now operationally adding scoring magnitude on top.

If pre_rating had been Buy or Overweight, spec 008 would have fired with
+0.341 margin above T_bull (0.941 vs 0.60). Spec 007 alone at
bull=0.85 would have fired with +0.25 margin. The calendar boost adds
+0.09 incremental signal — operationally inert here (UW pre-rating
pre-empts), but well-tuned.

### F-5: PM "rebuild target" + "12-18 month rebuild" framing

> "begin rebuilding a full position in tranches at $300–310, $275–285,
> and $255–265, targeting a 12–18 month price target $380–$420"

PM's prose distinguishes:
- Immediate UW (trim now, "Time Horizon: 1-3 months for trim execution")
- Forward bull thesis at re-entry levels ("12-18 month rebuild target")

This is the same Constitution VII Calibrated Abstention pattern from
`memory/reference_pm_hold_with_bullish_prose.md` — rating field is
"today's commit" (UW), prose can recommend multi-month framework
(rebuild target). Filters parse rating, not prose. AMD-04-24 is
EXPLICITLY a trim-then-rebuild thesis, not a permanent-bear thesis.

## Implications for v1.4.4 ratification

1. **AMD-04-24 strengthens the evidence base**: 3-mechanism-class
   alignment with PM commit is the strongest behavioral-additive case
   in the corpus. AMD now has 5 behavioral-additive cases across 4
   mechanism classes (1 Spec 003 + 2 Spec 007 bull + 1 Spec 008 + 1
   triple-hit on AMD-04-24).
2. **F-1 nuance for ratification**: PM's textual self-validation can
   be operationally wrong (PM said "captured inflection" while AMD
   went +25%). The v1.4.4 framing should be precise — multi-mechanism-
   validator describes PM's COMMIT-DECISION CORRELATION with contrarian
   signals, NOT PM's REALIZED-α CORRECTNESS. The realized-α verdict
   for AMD requires the 21-day window to close (~2026-05-15).
3. **PR #45 followup refuted**: NOT a baseline switch. The percentile
   movement is genuine signal-shift against constant baseline. Strengthens
   v1.4.4 — the L-8 pattern is signal-driven, not artifact-driven.
4. **Counter-evidence watch confirmed clear so far**: AMD-04-24 with
   bull_score=0.85 + percentile=98 + effective_bull=0.94 had pre=UW
   and pm=UW (NOT Buy/OW). Counter-evidence pattern (PM Buy/OW + score
   ≥ 0.80) still has zero observations across 240 logs.

## Followups (added to backlog)

1. **AMD memory log audit**: check `~/.tradingagents/memory/trading_memory.md`
   for AMD entries to investigate F-1's hallucination question. Did PM
   reference real prior memory or hallucinate? ~10min, $0.
2. **Sector-baseline pool composition tracking**: add a small instrumentation
   field to spec 003.5 logging `baseline_n` (currently `None` in state log)
   so future percentile-jump anomalies can be diagnosed without manual
   investigation. Defer; not v1.4.4-blocking.
3. **AMD-04-17 vs AMD-04-24 21d-α comparison**: when the 2026-05-15 window
   closes, compare realized α for both AMD UW commits. If both negative →
   PM was operationally correct over the 21d horizon despite being wrong
   over 5d. If both positive → PM's UW thesis was wrong at 21d too,
   adding "behavioral-additive doesn't predict realized α" to the v1.4.4
   caveats.

## Sibling docs

- `claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md` — PR #43 paired
  AMD-04-17 deep-dive
- `claudedocs/behavioral-additive-sweep-refresh-2026-05-07-evening.md` —
  PR #45 sweep refresh; this doc resolves the AMD followup
- `claudedocs/constitution-v1.4.4-draft-2026-05-07.md` — PR #44 draft;
  this doc adds F-1/F-2 nuance for ratification
- `memory/reference_pm_hold_with_bullish_prose.md` — Constitution VII
  rating-vs-prose pattern; F-5 is another instance
- `memory/reference_behavioral_additive_4th_interpretation.md` — L-8
  memory; AMD-04-24 is the strongest behavioral-additive case to date
