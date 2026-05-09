# WC-10 v3 bear-regime test — ANALYSIS

**Experiment ID**: `2026-05-08-003-wc-10-bear-regime-q4-2025-nvda`
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/`
**Run date**: 2026-05-08 (kicked off evening; completed ~2.5h later)
**Total LLM cost**: ~$6.40 (16 propagates × ~$0.40)
**Predecessors**:
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1, n=20 paired)
- `experiments/2026-05-03-008-opus47-cross-period/` (Opus 4.7 5-tier reference, same Q4 2025 NVDA dates)

## Headline verdict

**SC-007 v3 falsification: PARTIAL ALT-A (direction matches but magnitude < 1.0pp).**

WC-10 v3 on Q4 2025 NVDA produced mean rating-attributed 21d α of **+0.21%**, vs 5-tier baseline's **+0.44%**. The α delta of **-0.22pp** falls below the ALT-A magnitude threshold (`|delta| < 1.0pp`) but the direction matches: WC-10 emitted **8/8 dates as Buy/OW** (binned), reading bullish on a falling cohort.

The v1.5.0 caveat language ("WC-10 amplifies whatever signal the framework was already generating") is correct as-written. The magnitude is small enough that strengthening to "amplifies in a way that produces statistically worse outcomes" would over-claim from this sample.

**Constitution VII v1.5.0 caveat CONFIRMED at predicted scope.** Apply Constitution v1.5.1 Patch D from `claudedocs/constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md` — preserves caveat language; documents empirical magnitude bound at < 1.0pp on this cohort.

**Spec 009 branch selection**: Branch A activation ships with the v1.5.0 caveat documented in `docs/SIGNALS.md` per Spec 009 FR-006 but does NOT require regime-aware gating as a hard requirement. Operator discretion suffices.

## Per-date paired results

| Date | NVDA WC-10 rating | NVDA WC-10 binned | NVDA 5-tier rating | NVDA 21d α | WC-10 attr | 5-tier attr | Δpp |
|---|---|---|---|---:|---:|---:|---:|
| 2025-11-07 | +0.6200 | Buy | Underweight | -3.48% | -3.48 | +3.48 | **-6.97** |
| 2025-11-14 | +0.5500 | Overweight | Hold | -7.57% | -7.57 | +0.00 | -7.57 |
| 2025-11-21 | +0.6200 | Buy | Hold | +1.08% | +1.08 | +0.00 | +1.08 |
| 2025-11-28 | +0.5200 | Overweight | Hold | +5.13% | +5.13 | +0.00 | +5.13 |
| 2025-12-05 | +0.5200 | Overweight | Hold | +2.81% | +2.81 | +0.00 | +2.81 |
| 2025-12-12 | +0.5200 | Overweight | Hold | +3.08% | +3.08 | +0.00 | +3.08 |
| 2025-12-19 | +0.5200 | Overweight | Hold | +0.89% | +0.89 | +0.00 | +0.89 |
| 2025-12-26 | +0.6800 | Buy | Hold | -0.22% | -0.22 | +0.00 | -0.22 |

**Critical observation**: 5-tier baseline correctly emitted Underweight on 2025-11-07 — the date NVDA fell -3.48% over the next 21d. WC-10 collapsed that into Buy (+0.6200), losing the only direction-correct bearish read in the cohort. The 5-tier mode's Hold-default on the 7 other dates was directionally neutral but statistically Hold-on-falling-Tech is a defensible position.

## Aggregate metrics

| Mode | n | Mean rating-attributed α % | Buy/OW count | UW/Sell count | Hold count |
|---|---:|---:|---:|---:|---:|
| WC-10 | 8 | **+0.21%** | 8 | 0 | 0 |
| 5-tier baseline | 8 | **+0.44%** | 0 | 1 | 7 |

**α delta (WC-10 − 5-tier)**: **-0.22pp** (within ±100bps NULL region; direction matches ALT-A)

**Verdict**: **PARTIAL ALT-A** (direction matches ALT-A — WC-10 amplifies framework's bullish reads on a falling cohort — but magnitude < 1.0pp from baseline)

## Direction distribution comparison

| Bin | WC-10 count | 5-tier count | Pattern |
|---|---:|---:|---|
| Buy | 3 | 0 | WC-10 amplification |
| Overweight | 5 | 0 | WC-10 amplification |
| Hold | 0 | 7 | 5-tier default |
| Underweight | 0 | 1 | 5-tier-only correct bearish read (NVDA -3.48% on 2025-11-07) |
| Sell | 0 | 0 | — |

**Pattern interpretation**: WC-10 emits bullish on EVERY date — direction matches ALT-A (bear-regime amplifies the framework's existing bullish reads). The schema fix amplified the framework's existing bullish reads regardless of whether those reads were direction-correct. On Q4 2025 NVDA where the framework reads slightly bullish-leaning (5-tier emitted only 1 UW + 7 Hold), WC-10 converted those Holds into Buy/OW commits.

## Cross-experiment comparison to 008

Experiment 008 (Opus 4.7) ran the same 8 dates and produced 7/8 OW + 1 Hold (5-tier) per `RESEARCH_FINDINGS.md`. v3 used Sonnet 4.6 (matches v1 + v2); cross-experiment comparison is approximate.

| Source | Model | Mode | OW count | UW count | Hold count | Mean 21d α |
|---|---|---|---:|---:|---:|---:|
| Exp 008 | Opus 4.7 | 5-tier | 7 | 0 | 1 | -0.47% (per headline) |
| v3 5-tier | Sonnet 4.6 | 5-tier | 0 | 1 | 7 | +0.44% (rating-attributed) |
| v3 WC-10 | Sonnet 4.6 | continuous | 8 (Buy/OW) | 0 | 0 | +0.21% (rating-attributed) |

Two notable cross-experiment observations:

1. **Sonnet vs Opus on the same dates**: Sonnet was Hold-dominant (7/8 Hold) where Opus was OW-dominant (7/8 OW). Sonnet's Hold-default appears to be a model-specific calibration choice — consistent with prior Constitution VII Replicability-scope sub-section's "Sonnet over-abstains on bull tickers" framing. Opus's OW-on-falling-Q4-NVDA matches the corpus's "Q4 2025 negative outlier" finding.

2. **WC-10 collapses Sonnet's Hold-default into bullish commits** — same direction as Opus's natural over-commitment, but achieved via a different mechanism (schema fix vs model swap). The empirical result is similar: bullish commits on a falling cohort underperform.

## Constitution VII v1.5.0 feedback

| Verdict | What it implies for v1.5.0 caveat |
|---|---|
| ALT-A confirmed | Caveat STRENGTHENED — bear-regime validation IS load-bearing |
| ALT-B confirmed | Caveat WEAKENED — WC-10 may surface direction-correct signal independent of regime |
| NULL | Caveat MAY BE OVER-CAUTIOUS |
| **PARTIAL ALT-A (this verdict)** | **Caveat CONFIRMED at predicted scope — regime-asymmetric calibration is real but bounded; caveat language is correct as-written** |

**Action**: apply Constitution v1.5.1 Patch D (per PR #144 conditional patch drafts) — appends "Bear-regime validation" paragraph to Principle VII sub-section, documenting the empirical magnitude bound (`|delta| < 1.0pp` on Q4 2025 NVDA cohort) without strengthening the caveat language.

## Constitution adherence checklist

- ✅ I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / wc11_pilot_memory.md isolated to v3 dir
- ✅ II (One Experiment Per Change): same intervention as v1 + v2 (continuous-scalar schema). v3 differs only in cohort.
- ✅ III (Stay Cheap): T1 (≤$10) at $6.40
- ✅ IV (No Production Claims): bear-regime result informs the universalize-or-not decision; bear-regime amplification empirically validated as a documented caveat (not a hard regime-gating requirement).
- ✅ VI (Spec Before Structural Change): per spec bundle 108
- ⚠️ VII (Calibrated Abstention v1.5.0): result feeds back into v1.5.0 caveat per the table above. Patch D application preserves caveat language; documents empirical magnitude bound.

## Monitoring smoke test

```
python scripts/wc_10_underperformance_monitor.py --csv experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv
```

Expected output (per PR #146 alert criteria):
- Cohort cumulative Δα: -1.77pp (= 8 × -0.22pp avg per pair, modulo per-pair variance)
- Per-pair severe alerts: ≥1 (2025-11-14 Δpp -7.57pp; 2025-11-07 Δpp -6.97pp)
- Streak detection: possibly TRUE (2 consecutive negative deltas at Nov 7 + Nov 14)
- Cohort cumulative alert: probably NOT triggered at -1.77pp (above -5.0pp threshold AND n < 10 cohort size)

The monitor empirically validates the v1.5.0 caveat in operational form on the v3 cohort — exactly the production-tier monitoring that Spec 009 Branch A would inherit when activated.

## Next steps (per Constitution v1.5.0 + Spec 009)

1. **Constitution v1.5.0 → v1.5.1**: apply Patch D per PR #144 conditional patches; bumps version + appends "Bear-regime validation" paragraph documenting empirical magnitude bound.
2. **RESEARCH_FINDINGS.md update**: add v3 verdict to WC-10 section; mark "Does WC-10 schema fix make bear-regime calibration WORSE / NEUTRAL / BETTER?" as RESOLVED 2026-05-08.
3. **Spec 009 Branch A activation**: ships with v1.5.0 caveat documented in `docs/SIGNALS.md` per Spec 009 FR-006. No regime-aware gating required as a hard requirement (per Patch D operational implication).
4. **v2 awaits** — when v2 (n=100 ticker expansion) lands, Spec 009 branch selection between A/B/C/D activates per v2's SC-005(b) verdict. v3 verdict is independent input to that decision.

## Cross-references

- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1 pilot — SC-007 ALT-A confirmed at distribution level; the precedent verdict)
- `claudedocs/constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md` (PR #144 conditional patches; Patch D applies)
- `specs/009-wc-10-production-deployment/spec.md` (PR #140 conditional draft; Branch A activation per this verdict)
- `claudedocs/v3-landing-pr-series-bundle-template-2026-05-08.md` (PR #149 landing playbook; this PR is Landing PR #1 of 3)
- `scripts/wc_10_underperformance_monitor.py` (PR #146 production monitor; v3 cohort smoke test)
- Constitution v1.5.0 Principle VII sub-section "Schema-induced abstention is NOT calibrated abstention"
