# HYPOTHESIS — BR-3 v2 (news + fundamentals analyst structured-output)

**Experiment ID**: `2026-05-09-003-br3-v2-news-fundamentals`
**Created**: 2026-05-09
**Source idea**: BR-3 v2 (sister extensions to BR-3 v1; per `experiments/2026-05-09-001-br3-squeak-market-analyst/ANALYSIS.md` PR #178 + ROADMAP).
**Cost**: $16 LLM (40 propagates × ~$0.40; Constitution III T2).
**Authorization**: explicit user authorization 2026-05-09 evening.

## Why this experiment

BR-3 v1 (n=20; market analyst prose vs structured) found PARTIAL ALT-B — structured mode produced +20pp commit shift vs prose (commit-shift trigger met) but α delta +0.24pp below the ALT-B magnitude threshold. NVDA was unanimous-Hold across all 10 propagates; AAPL was the only divergence ticker. Phase E architectural variant NOT unblocked at v1 evidence level.

BR-3 v2 extends to **news + fundamentals analysts** (the other 2 of 3 production analyst stages):

1. **Sub-experiment A** (news_analyst_format prose vs structured): tests whether the analyst-stage prose-to-structured effect is market-analyst-specific OR generalizes to news
2. **Sub-experiment B** (fundamentals_analyst_format prose vs structured): same test for fundamentals analyst

If BOTH A + B reproduce the v1 +20pp commit-shift pattern → the analyst-stage structured-output pattern is GENERAL (Phase E unblocked at "all 3 analysts" scope).

If ONLY ONE reproduces → the effect is analyst-specific (which analyst stage carries the structured-output bottleneck).

If NEITHER reproduces → BR-3 v1's +20pp commit-shift is market-analyst-specific (probably driven by the technical-indicators tools the market analyst uses; news + fundamentals tools don't have the same prose-vs-structured contrast).

## Mechanism

2 new structured-output analyst modules (clones of `market_analyst_structured.py`):
- `tradingagents/agents/analysts/news_analyst_structured.py`
- `tradingagents/agents/analysts/fundamentals_analyst_structured.py`

Both reuse `MarketAnalystSquared` schema (analyst-agnostic — bullish_score / confidence / drivers / risks / citations); render via new `render_analyst_squared(squared, analyst_name)` helper.

2 new config keys: `news_analyst_format` + `fundamentals_analyst_format` (Literal[prose, structured], default prose). Factory routing in `tradingagents/graph/setup.py`.

## Test grid

| Sub-experiment | Mode | n | Cost |
|---|---|---:|---:|
| A_news | news_prose (control) | 10 | ~$4 |
| A_news | news_structured (intervention) | 10 | ~$4 |
| B_fund | fund_prose (control) | 10 | ~$4 |
| B_fund | fund_structured (intervention) | 10 | ~$4 |
| **Total** | — | **40** | **~$16** |

Tickers: NVDA + AAPL (same as v1 for direct comparability)
Dates: 2026-01-30, 02-13, 02-27, 03-13, 03-27 (same as v1)

## Falsification framework

Per Constitution VIII v1.4.0 + BR-3 v1 ANALYSIS:

| Verdict | Trigger | Implication |
|---|---|---|
| **NULL** (both A + B) | both sub-experiments show \|commit_shift\| < 10pp AND \|α delta\| < 1pp | Analyst-stage structured-output is market-analyst-specific; news + fundamentals don't carry the bottleneck |
| **ALT-A confirmed** (per sub-exp) | structured mode shows ≥+20pp Hold shift in either A or B (analyst-stage absorbs commits) | Analyst prose carries signal that structured loses; do NOT structurize the affected analyst |
| **ALT-B confirmed** (per sub-exp) | structured mode shows ≥+20pp commit shift AND \|α delta\| ≥ +1pp in either A or B (structured surfaces signal AND it's calibrated) | Phase E architectural variant unblocked for that analyst; ship structured as default |
| **PARTIAL ALT-B** (per sub-exp) | commit shift ≥+20pp triggered but α delta below threshold | Same as v1; analyst-stage effect REAL but n insufficient for calibration validation |
| **DIFFERENTIAL** | A and B show different verdicts (one ALT-B, one NULL) | Analyst-specific: only one stage carries the structured-output bottleneck |

## Pre-scaffolding

ANALYSIS_TEMPLATE.md will accompany this HYPOTHESIS with all 5 verdict-conditional branches per `reference_conditional_branch_spec_pattern.md`. Sister cohort WC-11 v2 (60 propagates × $24) launching in parallel; dual-pilot landing playbook captures coordination.

## Constitution adherence

- ✅ I (Save Everything): isolated experiment dir
- ✅ II (One Experiment Per Change): 2 sub-experiments × single intervention each (news_analyst_format vs fundamentals_analyst_format swap)
- ✅ III (Stay Cheap): T2 ($16 within $5-30); explicit operator authorization
- ✅ IV (No Production Claims): NULL verdict valid
- ✅ VI (Spec Before Structural Change): 2 new analyst modules + 2 config keys is structural change; this HYPOTHESIS + module-level testing serves the spec-first discipline
- ✅ VII (Calibrated Abstention): orthogonal — operates at analyst stage upstream of PM

## Success criterion

- [ ] 40/40 propagates resolved; per-sub-experiment commit-shift + α delta computed; verdict selected per the 5-branch framework above; per-spec retrospective written.

## Notes

Dual-pilot launch with WC-11 v2 (`experiments/2026-05-09-002-wc11-v2-disambiguation/`). Both pilots run in background simultaneously (~12h each); landing playbook coordinates the post-data analysis.

## Related experiments

- BR-3 v1: `experiments/2026-05-09-001-br3-squeak-market-analyst/`
- WC-11 v2 (sister cohort): `experiments/2026-05-09-002-wc11-v2-disambiguation/`
- WC-10 v1 (sister at PM-stage; v1 + v2 + v3): `experiments/2026-05-08-001-wc-10-pilot/` + sisters
- Pilot harness: `scripts/br3_v2_pilot.py` (NEW)
