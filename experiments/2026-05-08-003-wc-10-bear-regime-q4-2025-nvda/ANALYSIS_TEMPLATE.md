# WC-10 v3 bear-regime test — ANALYSIS template

> **STATUS**: TEMPLATE awaiting data. Background pilot in flight (~2.5h ETA from 2026-05-08 evening kickoff). Replace `<TODO>` placeholders + numerical TBDs with computed values once `results.csv` reaches 16 rows. Then move/rename this file to `ANALYSIS.md`.

**Experiment ID**: `2026-05-08-003-wc-10-bear-regime-q4-2025-nvda`
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/`
**Run date**: 2026-05-08 → <TODO completion timestamp>
**Total LLM cost**: ~$6.40 (16 propagates × ~$0.40)
**Predecessors**:
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1, n=20 paired)
- `experiments/2026-05-03-008-opus47-cross-period/` (5-tier Q4 2025 NVDA reference, Opus 4.7)

## Headline verdict (TBD post-data)

**SC-007 v3 falsification verdict: <NULL | ALT-A | ALT-B | PARTIAL ALT-A>** on the bear-regime cohort.

- **NULL** (regime-neutral): mean_α(WC-10) ≈ mean_α(5-tier) within ±100 bps
- **ALT-A** (bear-regime AMPLIFIES failure): WC-10 commits more bullishly → MORE wrong → mean_α(WC-10) − mean_α(5-tier) ≤ -100 bps
- **ALT-B** (bear-regime CORRECTS direction): WC-10 surfaces bearish reads → mean_α(WC-10) − mean_α(5-tier) ≥ +100 bps
- **PARTIAL ALT-A**: direction matches ALT-A (more bullish commits) but α delta < 100 bps in magnitude

## Per-date paired results

| Date | NVDA WC-10 rating | NVDA WC-10 binned | NVDA 5-tier rating | NVDA 21d raw | 21d α vs SPY |
|---|---|---|---|---:|---:|
| 2025-11-07 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-11-14 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-11-21 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-11-28 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-05 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-12 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-19 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-26 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |

(NVDA 21d raw is the same value across both modes per propagate; only the rating differs.)

## Aggregate metrics (PRIMARY)

| Mode | n | Mean rating | Buy/OW count | UW/Sell count | Hold-bin count | Mean 21d α |
|---|---:|---:|---:|---:|---:|---:|
| WC-10 | 8 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>% |
| 5-tier baseline | 8 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>% |

**α delta (WC-10 − 5-tier)**: <TBD>pp

**Verdict**: <NULL / ALT-A / ALT-B / PARTIAL ALT-A>

## Direction distribution comparison (SECONDARY)

| Bin | WC-10 count | 5-tier count | Pattern |
|---|---:|---:|---|
| Buy | <TBD> | <TBD> | <TBD> |
| Overweight | <TBD> | <TBD> | <TBD> |
| Hold | <TBD> | <TBD> | <TBD> |
| Underweight | <TBD> | <TBD> | <TBD> |
| Sell | <TBD> | <TBD> | <TBD> |

**Pattern interpretation**:

- If WC-10 emits MORE Buy/OW than 5-tier on this falling cohort → ALT-A confirmed
- If WC-10 emits MORE UW/Sell than 5-tier → ALT-B confirmed
- If both modes emit similar distributions → NULL
- If WC-10 amplifies BOTH directions while 5-tier collapses to Hold → PARTIAL ALT-A (the schema fix is direction-aware but not regime-aware)

## Cross-experiment comparison to 008 (TERTIARY)

Experiment 008 (Opus 4.7) ran the same 8 dates and produced **7/8 OW + 1 Hold (5-tier)** with realized 21d α ≈ -0.47% n=9, 22% hit per `RESEARCH_FINDINGS.md`. This experiment uses Sonnet 4.6 (lighter model); cross-experiment comparison is approximate. Within-experiment pairing is the load-bearing measurement.

| Source | Model | Mode | OW count | UW count | Hold count | Mean 21d α |
|---|---|---|---:|---:|---:|---:|
| Exp 008 | Opus 4.7 | 5-tier | 7 | 0 | 1 | -0.47% |
| v3 5-tier | Sonnet 4.6 | 5-tier | <TBD> | <TBD> | <TBD> | <TBD>% |
| v3 WC-10 | Sonnet 4.6 | continuous | <TBD> | <TBD> | <TBD> | <TBD>% |

If v3 5-tier ≈ 008 5-tier in direction (but with Sonnet's likely higher Hold rate per Constitution VII v1.5.0 mechanism A), then v3's WC-10 vs 5-tier delta isolates the schema effect from the model effect.

## Constitution VII v1.5.0 feedback (load-bearing)

| Verdict | What it implies for v1.5.0 caveat |
|---|---|
| ALT-A confirmed | v1.5.0 caveat STRENGTHENED — bear-regime validation IS load-bearing for universalizing schema fix; WC-10 is regime-conditional |
| ALT-B confirmed | v1.5.0 caveat WEAKENED — WC-10 may surface direction-correct signal independent of regime; consider revising caveat language |
| NULL | v1.5.0 caveat MAY BE OVER-CAUTIOUS — schema fix is regime-neutral; consider relaxing caveat to "asymmetric bullish-amplification but neutral overall" |
| PARTIAL ALT-A | v1.5.0 caveat CONFIRMED at predicted scope — regime-asymmetric calibration is real but bounded; caveat language is correct as-written |

## Constitution adherence checklist

- ✅ I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / wc10_pilot_memory.md isolated to v3 dir
- ✅ II (One Experiment Per Change): same intervention as v1 + v2 (continuous-scalar schema). v3 differs only in cohort.
- ✅ III (Stay Cheap): T1 (≤$10) at $6.40
- ✅ IV (No Production Claims): bear-regime result informs the universalize-or-not decision; does not commit
- ✅ VI (Spec Before Structural Change): per spec bundle 108
- <TBD VII>: result feeds back into v1.5.0 caveat per the table above

## Next steps (for operator decision; populate after data lands)

<TBD per verdict — possibilities include:>

1. If ALT-A → memorialize regime-conditionality as a constitutional clarification (v1.5.0 → v1.5.1 PATCH); WC-10 production deployment requires regime-aware gating
2. If ALT-B → schema fix may be universally beneficial; v1.5.0 caveat language could be loosened
3. If NULL → schema fix is regime-neutral; bullish-amplification finding from v1 + v2 is the dominant claim and bear-regime concern was over-cautious
4. If PARTIAL ALT-A → caveat is correctly bounded; document the regime-asymmetry pattern in `RESEARCH_FINDINGS.md` headline
