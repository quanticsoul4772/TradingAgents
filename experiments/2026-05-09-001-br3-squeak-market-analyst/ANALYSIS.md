# ANALYSIS — BR-3 Squeak market-analyst structured-output pilot

**Experiment ID**: `2026-05-09-001-br3-squeak-market-analyst`
**Run date**: 2026-05-09 (kicked off late 2026-05-08; completed early 2026-05-09)
**Total LLM cost**: ~$8 (20 propagates × ~$0.40, T2)
**Predecessors**:
- HYPOTHESIS scaffold (PR #157)
- Implementation + pilot launch (PR #169)
- ANALYSIS_TEMPLATE (PR #157 auto-scaffolded; PR #176 extended with verdict-conditional blocks)
- Triple-pilot landing playbook (PR #172)

## Headline verdict

**SC-007 v1 falsification: PARTIAL ALT-B (structured surfaces commits prose suppresses; calibration mixed at n=2 commits).**

Direction matches ALT-B (commit shift +20pp toward ALT-B trigger) but α delta of +0.24pp falls within the ±1pp NULL region. At n=10 paired propagates with only 2 commits emerging in structured mode (vs 0 in prose), calibration of those commits cannot be validated.

n=20 propagates / 5 dates × 2 tickers (NVDA + AAPL) × 2 modes (prose + structured) / $8.

## Per-date paired results

| Date | Ticker | prose | structured | 21d α | Differ? |
|---|---|---|---|---:|---|
| 2026-01-30 | NVDA | Hold | Hold | -4.11% | no |
| 2026-02-13 | NVDA | Hold | Hold | +1.13% | no |
| 2026-02-27 | NVDA | Hold | Hold | +0.84% | no |
| 2026-03-13 | NVDA | Hold | Hold | +3.88% | no |
| 2026-03-27 | NVDA | Hold | Hold | +15.01% | no |
| 2026-01-30 | AAPL | Hold | **Overweight** | +3.42% | **DIFFER** |
| 2026-02-13 | AAPL | Hold | Hold | +1.00% | no |
| 2026-02-27 | AAPL | Hold | **Underweight** | +0.98% | **DIFFER** |
| 2026-03-13 | AAPL | Hold | Hold | -1.66% | no |
| 2026-03-27 | AAPL | Hold | Hold | -3.43% | no |

**2 of 10 paired propagates differ (20%).** Both differences are AAPL; NVDA was unanimous Hold across all 5 dates.

## Aggregate metrics

| Mode | n | Buy/OW | Hold | UW/Sell | Mean rating-attributed α |
|---|---:|---:|---:|---:|---:|
| **prose** | 10 | 0 | 10 | 0 | +0.00% |
| **structured** | 10 | 1 | 8 | 1 | +0.24% |

| Metric | Value | Threshold | Verdict |
|---|---:|---|---|
| α delta (structured − prose) | +0.24pp | ALT-B requires ≥+1.0pp | NOT triggered |
| Hold shift (structured − prose) | -20pp | ALT-A requires ≥+20pp | NOT triggered (opposite direction) |
| Commit shift (structured − prose) | **+20pp** | ALT-B requires ≥+20pp | **TRIGGERED** |

**Verdict per HYPOTHESIS framework**: PARTIAL ALT-B — direction matches ALT-B (structured produces +20pp more commits than prose) but α magnitude (+0.24pp) is below the ±1pp threshold for full ALT-B confirmation.

## Per-commit calibration check

The 2 structured-mode commits:

| Date | Ticker | Structured rating | 21d α | Direction-correct? |
|---|---|---|---:|---|
| 2026-01-30 | AAPL | Overweight | +3.42% | **YES** (OW + α=+3.42% → +3.42pp attributed) |
| 2026-02-27 | AAPL | Underweight | +0.98% | NO (UW + α=+0.98% → -0.98pp attributed) |

**1 of 2 commits direction-correct.** At n=2 this is statistically uninterpretable — could be 50% calibration (genuine signal) or noise from a small sample.

Net: structured mode's 2 commits contributed +3.42pp − 0.98pp = +2.44pp total attribution across 10 propagates → +0.24pp average per propagate. Prose mode contributed +0.00pp (all Hold).

## NVDA observation: total agreement (10/10 Hold)

NVDA produced Hold across ALL 10 propagates (5 prose + 5 structured). The structured-mode mechanism only differentiates from prose on AAPL in this cohort. This is consistent with WC-10 v1 finding that AAPL was the bear-side-amplified ticker — under WC-10, scalar mode emitted UW commits that 5-tier mode kept as Hold. BR-3 structured mode echoes this pattern at the analyst stage: AAPL is the ticker where structured analyst output diverges from prose.

NVDA's unanimous Hold across both modes is itself notable: the dates 2026-01-30 to 2026-03-27 had NVDA realized 21d α from -4.11% to +15.01% (wide range), but neither prose nor structured market analyst pushed PM toward a commit. This is consistent with Constitution VII v1.5.0 Mechanism A (genuine ambiguity) — the analyst data didn't support a directional read in either format.

## Falsification framework verdict

| Verdict | Strict trigger | Observed | Match? |
|---|---|---|---|
| NULL | `\|delta\| < 1pp` AND `\|hold_shift\| < 10pp` AND `\|commit_shift\| < 10pp` | delta=+0.24pp ✓; hold_shift=-20pp ✗; commit_shift=+20pp ✗ | NO |
| ALT-A | delta ≤ -1pp AND hold_shift ≥ +20pp | delta=+0.24pp (wrong sign + magnitude) | NO |
| ALT-B | delta ≥ +1pp AND commit_shift ≥ +20pp | delta=+0.24pp (below magnitude) ✗; commit_shift=+20pp ✓ | PARTIAL |
| **PARTIAL ALT-B** (this) | direction matches ALT-B but magnitude below threshold | YES | **MATCH** |

## Implications

### Constitution implication

**No amendment required.** BR-3 PARTIAL ALT-B at n=20 doesn't meet the magnitude threshold for ALT-B (which would have triggered v1.5.1 → v1.6.0 MAJOR for new "Structured-output-throughout" Principle). The PARTIAL verdict is a "weak signal exists at the analyst stage but n is too small" finding — exactly what the HYPOTHESIS warned about with the "MIXED / INCONCLUSIVE at n=20" caveat.

### Architectural implication

The Phase E architectural variant (structured-output-throughout) is **NOT unblocked** at this evidence level. The structured-mode analyst produced 2 commits where prose produced 0, but at n=2 commits we cannot determine if structured surfaces well-calibrated signal or noise.

### Sister-experiment recommendation

BR-3 v2 (extend to news + fundamentals analysts) would clarify whether the analyst-stage structured-vs-prose effect is:
- (a) Specific to the market analyst (only diverged on AAPL)
- (b) Generalizes to other analyst stages

Cost: ~$8 each ($16 total for both extensions). Worth doing if operator wants to definitively rule in/out the analyst-stage structured-output pattern.

### Cross-pollination implication

The cross-pollination L4 candidate "Squeak structured signaling" (PR #143) is now **PARTIALLY VALIDATED at n=20** but not strongly enough to commit to as architectural direction. The L4 status remains "pilot-eligible" rather than promoting to "ship-eligible".

### Research findings update

RESEARCH_FINDINGS.md should add a sub-section under WC-10 noting the BR-3 PARTIAL ALT-B finding as the analyst-stage analog. The TWO-MECHANISM mode-collapse framing extends modestly: prose-mode market analyst contributes to PM Hold-collapse on AAPL even when structured-mode would have produced commit data the PM could act on.

## Constitution adherence checklist

- ✅ I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / br3_pilot_memory.md isolated to this dir
- ✅ II (One Experiment Per Change): single intervention (market analyst output format)
- ✅ III (Stay Cheap): T2 ($8 within $5-$30)
- ✅ IV (No Production Claims): PARTIAL ALT-B documented as inconclusive at this n; no production deployment changes
- ✅ VI (Spec Before Structural Change): small module addition (PR #169) didn't require spec-kit invocation
- ✅ VII (Calibrated Abstention v1.5.1): orthogonal — operates upstream of PM
- ✅ VIII: N/A — not a filter

## Next steps (per triple-landing playbook PR #172)

1. **RESEARCH_FINDINGS.md** sister-hypothesis paragraph (Landing PR #2 of BR-3 series; combined with WC-11 + v2 RESEARCH_FINDINGS updates per disjoint-sections coordination)
2. **No Constitution amendment** required (PARTIAL ALT-B doesn't meet magnitude threshold for new Principle)
3. **Sister experiments deferred**: BR-3 v2 (news + fundamentals) is the natural follow-up if operator wants to definitively rule in/out the analyst-stage hypothesis. ~$16 total. Currently sits as scaffold-eligible per cross-pollination review (PR #143 L4 status preserved).

## Cross-references

- HYPOTHESIS.md (this dir) — 3-prediction framework + PR #176 extended verdict-conditional blocks
- Implementation: `tradingagents/agents/analysts/market_analyst_structured.py` (PR #169)
- Pilot harness: `scripts/br3_squeak_pilot.py` (PR #169)
- Sister hypothesis: WC-10 v1 ANALYSIS.md (PM-stage; PR #130) — analogous mechanism at PM stage with strong ALT-A confirmation
- WC-10 v3 ANALYSIS.md (bear-regime; PR #153) — PARTIAL ALT-A precedent for "direction-matches-magnitude-doesn't" interpretation
- Triple-pilot landing playbook (PR #172)
- Cross-pollination L4 progress check (PR #167) — Squeak L4 status preserved at pilot-eligible (not promoted)

## Cost

$8 LLM (Constitution III T2).
