# SC-009 mid-backtest commit-pattern diagnostic — 2026-05-07

**Status**: Mid-flight diagnostic of `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/` (kicked off 06:14 PDT 2026-05-07, ~5h ETA, 6/36 rows complete as of 07:08 PDT).

**Trigger**: First 5 rows all returned Hold; concern raised that all-Hold pattern would FAIL SC-009 gate 2 (n_fired ≥ 8). Documented as `claudedocs/sc-009-expansion-contingency-design-2026-05-07.md`.

**Verdict on the concern**: **PARTIALLY RELAXED.** State-log inspection of the 6 completed rows shows the framework IS committing (1 OW fire by spec 007 + 1 native UW), and the boost IS engaging (4/6 rows have `calendar_boost > 0`). Gate 3 already PASSED at n=4 boost-engaged; gate 2 on track at extrapolated ~12 commits in 36 rows.

## Per-row state-log diagnostic (6 of 36)

| Ticker | Date | pre_rating | post_rating | fired_bull | bull_pi | bear_pi | days_to_earn | calendar_boost |
|---|---|---|---|---|---|---|---|---|
| NVDA | 2026-04-17 | Hold | Hold | no | 0.78 | 0.30 | 33 | 0.000 |
| NVDA | 2026-04-24 | Overweight | **Hold** | **YES** | 0.82 | 0.55 | 26 | 0.000 |
| MSFT | 2026-04-17 | Hold | Hold | no | 0.62 | 0.50 | 12 | **0.143** |
| MSFT | 2026-04-24 | Hold | Hold | no | 0.55 | 0.65 | 5 | **0.643** |
| AAPL | 2026-04-17 | Hold | Hold | no | 0.75 | 0.45 | 13 | **0.071** |
| AAPL | 2026-04-24 | Underweight | Underweight | no | 0.75 | 0.40 | 6 | **0.571** |

## Findings

### 1. Spec 008 boost IS engaging (4/6 = 67%)

`calendar_boost > 0` on MSFT 04-17 (12d to earnings, boost=0.14), MSFT 04-24 (5d, boost=0.64), AAPL 04-17 (13d, boost=0.07), AAPL 04-24 (6d, boost=0.57). NVDA's earnings are far enough out (33d, 26d) to not engage the boost.

**SC-009 gate 3 (boost engaged ≥ 1 row): ALREADY PASSED** at n=4.

### 2. Spec 007 fired once (NVDA 04-24)

NVDA 2026-04-24: pre_rating=Overweight, post_rating=Hold, fired_bull=YES. Spec 007 caught this on `bull_case_priced_in=0.82` (above T=0.60 by margin). Boost wasn't engaged (days=26 > window=14), so this is a Spec 007-attributable fire (not Spec 008-attributable).

**SC-009 gate 2 (n_fired ≥ 8): currently 1/8.** Extrapolation at 6 rows → 36 rows: if commit rate stays at 2/6 (1 OW + 1 UW = 33%), expect ~12 commits, with maybe 6-8 of those firing through Spec 007. Achievable but tight.

### 3. Boost hasn't changed any decision (0/6 boost-attributable fires)

The 4 boost-engaged rows all have base scores either:
- ABOVE T=0.60 already (would fire boost-OFF too): MSFT 04-17 (0.62), AAPL 04-17 (0.75), AAPL 04-24 (0.75)
- BELOW T=0.60 even with boost: MSFT 04-24 (base=0.55, boost=0.64 → effective=0.55×1.32=0.73 > 0.60 — wait, this WOULD push above threshold)

Let me recompute MSFT 2026-04-24:
- base = 0.55
- magnitude = 0.5
- boost = 0.643
- effective = 0.55 × (1 + 0.5 × 0.643) = 0.55 × 1.3215 = 0.7268

`effective = 0.7268 > T=0.60`. This SHOULD have fired bull-side. But the row shows pre_rating=Hold, so spec 007 had no bull commit to suppress regardless of effective score. The boost engaged but had no commit to fire on (PM picked Hold from start).

This is exactly the **PM Hold-regime starves filters** pattern documented in memory `reference_pm_hold_regime_starves_filters.md`. Even when spec 008 boost works mechanically, if PM doesn't commit, the filter has nothing to do.

### 4. The bear-side cohort got a member (AAPL 04-24 UW)

AAPL 2026-04-24: pre=post=Underweight. Spec 007 bear is in SHADOW mode, so even though `bear_case_priced_in=0.40 < T_bear=0.50`, no fire either way. But this row IS a bear commit — meaningful for the SC-009 bear-side analysis when ANALYSIS.md is written.

## Updated risk assessment

The SC-009 expansion contingency (PR #27 — kick off 26 more propagates IF ≥30/36 rows return Hold AND `n_fired_boost_on < 4`) is now **less likely to be triggered**:
- Current Hold rate: 4/6 = 67% (extrapolation: 24 of 36 = 67%)
- Trigger threshold: ≥30/36 (83%)
- Gap: 24 vs 30 → expansion likely NOT triggered

If commit rate stays at 33% across the full 36 rows → ~12 commits → expect 6-8 fires through Spec 007 → gate 2 (n_fired ≥ 8) borderline-achievable.

## Implications for ANALYSIS.md (when realized α lands ~2026-05-22)

The boost-changed-decision count is the key Spec 008 attribution metric, and it's currently 0/6. Even if extrapolated to ~0/36 (most engaged rows have extreme base scores), the SC-009 verdict may be:
- **PASS gate 2 + 3 from spec 007 fires alone** (Spec 007 accounts for the SC-009 numerator)
- **Δα improvement (gate 1) inconclusive on boost-attributable rows** because boost didn't change any decisions
- → Verdict could be "Spec 008 boost is engineered correctly but RARELY changes outcomes on this cohort because the cohort's score distribution already has bull commits well above T"

This would be an interesting finding: Spec 008 isn't broken; it's just structurally narrow on most cohorts. The retrofit cohort's +3.35pp came from a specific subset of borderline scores that this live cohort doesn't replicate.

The PROPER SC-009 verdict will require the 21d realized α + the per-row boost-decision-changed analysis. Current diagnostic is mid-flight; final verdict deferred to ~2026-05-22.

## Next steps

1. **Let backtest run to completion** (~30 more rows × 9 min = ~4.5h)
2. **Re-run analyzer** (`scripts/analyze_sc009_ab.py --allow-partial`) every ~10 rows to track gate 2 trajectory
3. **Decide on expansion** (PR #27 contingency) ONLY after backtest completes + analyzer shows final n_fired_boost_on < 4
4. **Wait for realized α** (~2026-05-22) before writing ANALYSIS.md

## Cost

\$0 (diagnostic only; no LLM calls).

## Cross-references

- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/HYPOTHESIS.md` — original SC-009 design
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS_PLAN.md` — Phase 4 verdict tree
- `claudedocs/sc-009-expansion-contingency-design-2026-05-07.md` — expansion contingency
- `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md` — original +3.35pp retrofit verdict
- Memory: `reference_pm_hold_regime_starves_filters.md` — methodology insight on this exact phenomenon
