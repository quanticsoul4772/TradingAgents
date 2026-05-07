# AVGO temporal-jump investigation — bull_keyword_count spike + mechanism disagreement

**Trigger**: PR #53 sweep-refresh followup — "AVGO percentile jumped
89.8 → 98.0 in one week (same pattern as AMD). Worth investigation."
PR #47 closed the analogous AMD followup with a "feature_value spike
against constant sector pool" finding. This investigates whether AVGO
matches.

## State-log delta

| Field | AVGO-04-17 | AVGO-04-24 | Δ WoW |
|---|---|---|---|
| spec 003 feature_value (bull_keyword_count) | 79 | 97 | **+22.8%** |
| spec 003 n_history_sector (pool size) | 98 | 101 | +3.1% |
| spec 003 percentile | 89.8 | 98.0 | **+8.2pp** |
| spec 003 gate_baseline | sector | sector | unchanged |
| spec 007 bull_case_priced_in | 0.85 | **0.82** | **-0.03 (down)** |
| spec 007 bear_case_priced_in | 0.45 | 0.45 | unchanged |
| pre_rating | Hold | Hold | unchanged |

## Finding F-1: Same mechanism as AMD — bull_keyword_count spike against constant pool

Just like AMD-04-17 → 04-24 (+58% feature_value → 25.6pp percentile jump
per PR #47), AVGO's percentile jump is almost entirely driven by its own
bull_keyword_count spiking week-over-week. Pool size barely changed
(+3.1%), so the percentile movement is genuine signal-shift against a
near-stable baseline.

**Comparison**:

| Ticker | feature Δ | pool Δ | percentile Δ |
|---|---|---|---|
| AMD-04-17 → 04-24 | +58.1% (62→98) | -2.0% (98→101) | +25.6pp (72.4→98.0) |
| AVGO-04-17 → 04-24 | +22.8% (79→97) | +3.1% (98→101) | +8.2pp (89.8→98.0) |

AMD had a much larger feature-value spike (likely tracking the "70%
parabolic rally" coverage explosion per PR #46). AVGO's was milder but
the same MECHANISM: extended-rally generates more bullish news coverage,
which the bull_keyword_count featurizer measures, which pushes percentile
up against a stable sector baseline.

The 2-ticker pattern (now both AMD and AVGO show this) tentatively
supports the PR #47 hypothesis that bull_keyword_count is a valid
**leading indicator of contrarian condition intensification** in
extended-rally Tech tickers.

## Finding F-2: Spec 003 and Spec 007 DISAGREED on WoW direction

Notable wrinkle: AVGO's two contrarian signals moved in OPPOSITE
directions week-over-week:

- **Spec 003 percentile**: 89.8 → 98.0 (UP +8.2pp; more contrarian)
- **Spec 007 bull_case_priced_in**: 0.85 → 0.82 (DOWN -0.03; less contrarian)

Both stayed above their respective thresholds (Spec 003 > 80; Spec 007
> 0.60), so both still signaled "contrarian-priced-in" in the binary
sense. But the direction of WoW change diverged.

Possible explanations:
1. **Different time-horizon sensitivity**: Spec 003 (prose-density
   percentile) may track recency more aggressively than Spec 007
   (LLM-extracted holistic synthesis). The 04-24 LLM debate may have
   weighted other context (earnings volatility, sector rotation)
   slightly more bearishly even as bull-keyword-density rose.
2. **Different signal sources**: Spec 003 measures bull_keyword_count
   from `market_report` only. Spec 007 reads ALL analyst reports +
   debate prose. The two have different input scopes; divergence is
   mechanistically possible.
3. **Score-saturation effect**: Spec 003 percentile was already at 89.8
   (plenty of room to move up). Spec 007 was at 0.85 (close to its
   ceiling of 1.0). Both can rise but Spec 007 has less ceiling room.

## Finding F-3: Refines v1.4.4 multi-mechanism-validator framing

PR #41 sweep introduced PM-as-multi-mechanism-validator: PM internalizes
contrarian logic across multiple mechanism classes. AVGO shows the
mechanisms can DISAGREE on direction-of-change while still BOTH being
above their thresholds.

PM picked Hold both weeks for AVGO — consistent with both signals being
above threshold. But PM didn't seem to track the directional disagreement.

This nuances the v1.4.4 framing:
- **What PM tracks**: threshold-crossing in each mechanism class (binary
  "is this contrarian-priced-in?")
- **What PM may NOT track**: direction-of-change (was this MORE or LESS
  contrarian than last week?)

This is consistent with v1.4.4 ratification scope — the amendment
codifies the threshold-correlation behavior, not the direction-of-change
behavior. No revision to the v1.4.4 draft (PR #44) needed; AVGO is
within the framing.

## Implications

1. **AMD followup pattern generalizes**: spec 003.5 sector-baseline +
   bull_keyword_count featurizer shows consistent "rally → news coverage
   → percentile spike" mechanism across at least 2 Tech tickers (AMD,
   AVGO). PR #45 sweep already counted both of these as behavioral-
   additive cases; this just adds mechanism-traceability.

2. **Mechanism disagreement is not a refutation**: Spec 003 and Spec 007
   are independent; they can disagree on direction without invalidating
   either or the v1.4.4 framing.

3. **Cohort enumeration**: 2 of 10 tickers in the v1.4.4 evidence base
   (AMD + AVGO) show the temporal-intensification pattern. Cohort is
   thin; not codifying this as a separate finding — leaving it as a
   subordinate observation under v1.4.4.

## Followups

1. **3rd ticker confirmation** (deferred): if a future cohort surfaces
   another ticker with feature_value spike + percentile jump WoW pattern,
   the bull_keyword_count temporal-intensification mechanism graduates to
   a stand-alone observation.
2. **Spec 003 vs Spec 007 directional-divergence sweep**: across the
   v1.4.4 evidence base (10 tickers), how often do the two mechanisms
   disagree on direction-of-WoW-change? Could surface a new pattern.
   Defer; not v1.4.4-blocking.

## Sibling docs

- `claudedocs/spec-003-baseline-instrumentation-already-exists-2026-05-07-evening.md`
  — PR #47 (AMD case; 62 → 98 feature spike)
- `claudedocs/amd-2026-04-24-deep-dive-2026-05-07-evening.md` — PR #46 (AMD-04-24 deep-dive)
- `claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md` — PR #41
- `claudedocs/sc-009-27-row-mark-and-sweep-refresh-2026-05-07-late.md` — PR #53 (raised AVGO followup)
