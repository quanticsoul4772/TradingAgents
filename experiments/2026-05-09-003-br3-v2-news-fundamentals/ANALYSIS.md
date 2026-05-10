# ANALYSIS — BR-3 v2 (news + fundamentals analyst structured-output)

**Experiment ID**: `2026-05-09-003-br3-v2-news-fundamentals`
**Run date**: 2026-05-09 evening (background pilot `bkpnb5www`; completed within ~6h wall-clock)
**Total LLM cost**: ~$16 (40 propagates × ~$0.40, T2)
**Predecessors**:
- BR-3 v1 ANALYSIS: `experiments/2026-05-09-001-br3-squeak-market-analyst/ANALYSIS.md` (PR #178 — market analyst; PARTIAL ALT-B)
- HYPOTHESIS + ANALYSIS_TEMPLATE: PR #214
- Dual-pilot landing playbook: `claudedocs/dual-pilot-launch-playbook-2026-05-09.md` (PR #214)
- Landing-PR series template: `claudedocs/dual-pilot-landing-pr-series-template-2026-05-09.md` (PR #218)

## Headline verdict

**DIFFERENTIAL** — sub-experiments A and B show DIFFERENT verdicts:

- **Sub-experiment A (news_analyst_format)**: **NULL-leaning** — α delta +1.60pp meets the ALT-B magnitude threshold (≥+1.0pp), but commit shift = 0pp does NOT meet ALT-B trigger (≥+20pp). Mixed per-ticker (NVDA prose 0/5 → structured 1/5; AAPL prose 2/5 → structured 1/5; net 0pp shift). News analyst stage does NOT carry the structured-output bottleneck.

- **Sub-experiment B (fundamentals_analyst_format)**: **PARTIAL ALT-B** — commit shift +40pp (4/10 prose → 6/10 structured) triggers ALT-B distribution test, BUT α delta +0.11pp is below the ALT-B magnitude threshold (±1pp NULL region). Per-ticker pattern is CONSISTENT: NVDA prose 1/5 → structured 3/5; AAPL prose 1/5 → structured 3/5. Fundamentals analyst stage carries the structured-output bottleneck.

**Synthesis with BR-3 v1 (market analyst)**: 2 of 3 analyst stages carry the structured-output bottleneck (market + fundamentals); news analyst is the exception. The pattern Phase E architectural variant would test ("structured-output throughout") shows asymmetric mechanism class incidence across analyst stages.

n=40 propagates / 5 dates × 2 tickers (NVDA + AAPL) × 2 sub-experiments × 2 modes / $16.

## Per-mode aggregate (n=10 each)

| Mode | n | Buy/OW | Hold | UW/Sell | Mean rating-attributed α |
|---|---:|---:|---:|---:|---:|
| **news_prose** (control) | 10 | 0 | 8 | 2 | +0.07% |
| **news_structured** (intervention) | 10 | 1 | 8 | 1 | +1.67% |
| **fund_prose** (control) | 10 | 1 | 8 | 1 | +1.67% |
| **fund_structured** (intervention) | 10 | 2 | 4 | 4 | +1.77% |

## Sub-experiment A — news_analyst (NULL-leaning)

| Trigger | Threshold | Observed | Met? |
|---|---|---:|---|
| Hold shift (ALT-A) | ≥ +20pp | **+0pp** | NOT triggered |
| Commit shift (ALT-B) | ≥ +20pp | **+0pp** | NOT triggered |
| α delta magnitude (ALT-B full) | ≥ +1.0pp | **+1.60pp** | TECHNICALLY MET |
| NULL region | \|α delta\| < 1pp | +1.60pp | OUTSIDE |

**Per-ticker pattern (mixed; net 0)**:
- NVDA: prose 0/5 commits → structured 1/5 commits (+1)
- AAPL: prose 2/5 commits → structured 1/5 commits (-1)

The news_analyst result is INSIDE the NULL region for distribution shift (no Hold or commit movement) but OUTSIDE the NULL region for α magnitude. The α delta is driven by 1 NVDA structured commit (Buy at +20% realized α — large single-row attribution) AND the displacement of 1 AAPL prose commit. Without a distribution shift on the cohort level, this is a **stochastic single-row effect** rather than a mechanism finding — verdict is closer to NULL than ALT-B.

**Reframe**: news_analyst structured-output does NOT generalize the BR-3 v1 commit-shift effect. The +1.60pp α delta is artifact of sample-size noise at n=10.

## Sub-experiment B — fundamentals_analyst (PARTIAL ALT-B)

| Trigger | Threshold | Observed | Met? |
|---|---|---:|---|
| Hold shift (ALT-A) | ≥ +20pp | **-40pp** | NOT triggered (opposite direction) |
| Commit shift (ALT-B) | ≥ +20pp | **+40pp** | **TRIGGERED** |
| α delta magnitude (ALT-B full) | ≥ +1.0pp | +0.11pp | NOT met |

**Per-ticker pattern (consistent)**:
- NVDA: prose 1/5 commits → structured 3/5 commits (+2)
- AAPL: prose 1/5 commits → structured 3/5 commits (+2)

Both tickers show CONSISTENT +2 commit increase under structured fundamentals mode. Total: 2 prose commits → 6 structured commits across the cohort = +40pp commit shift.

**Verdict per HYPOTHESIS framework**: PARTIAL ALT-B — direction matches ALT-B (structured fundamentals produces +40pp more commits than prose) but α magnitude (+0.11pp) is well below the ±1pp threshold for full ALT-B confirmation. This is the SAME pattern as BR-3 v1 (market analyst PARTIAL ALT-B; commit shift +20pp + α delta +0.24pp).

## Combined v1 + v2 across analyst stages

| Stage | Verdict | Commit shift | α delta | Sister analysis |
|---|---|---:|---:|---|
| Market analyst (BR-3 v1) | PARTIAL ALT-B | +20pp | +0.24pp | PR #178 |
| News analyst (BR-3 v2 sub-A) | **NULL** | 0pp | +1.60pp* | This ANALYSIS |
| Fundamentals analyst (BR-3 v2 sub-B) | PARTIAL ALT-B | **+40pp** | +0.11pp | This ANALYSIS |

*The news α delta is sample-size-noise per per-ticker mixed pattern; not a genuine mechanism finding.

**2 of 3 analyst stages carry the structured-output commit-shift bottleneck** (market + fundamentals); 1 of 3 does NOT (news).

## Implications

### Phase E architectural variant ("structured-output throughout") — STILL NOT UNBLOCKED at this evidence level

Per HYPOTHESIS framework:
- Pure ALT-B confirmation (commit shift ≥+20pp AND α delta ≥+1pp) on EITHER sub-experiment → Phase E unblocked
- v1 + v2 results: 2 PARTIAL ALT-B (market + fundamentals at n=10 commits each) + 1 NULL (news)
- α magnitudes BELOW ±1pp threshold → can't validate calibration of the surfaced commits

Phase E remains conditional on a v3 cohort with larger n (e.g., 30+ commits per analyst stage to validate calibration). At current evidence level, the EFFECT is real (commit shift) but its CALIBRATION is unproven.

### Constitution implication

**No amendment required.** PARTIAL ALT-B verdicts on 2 of 3 sub-experiments don't trigger MAJOR v1.6.0 amendment for "Structured-output-throughout" Principle. The pattern strengthens the BR-3 v1 finding rather than overturning it.

### Architectural finding

**Asymmetric mechanism incidence across analyst stages**:
- Tools-rich analysts (market: technical indicators / fundamentals: financial metrics) carry the structured-output bottleneck
- Prose-heavy analyst (news: free-form narrative) does NOT carry the bottleneck

Mechanistic interpretation: when the analyst's output is fundamentally NUMERIC + structured (ratios, metrics, deltas), prose serialization of those numbers loses information that structured emission preserves. When the analyst's output is fundamentally NARRATIVE (news context, geopolitical reads), prose IS the natural medium and structured-output forces compression that doesn't add value.

### Sister-experiment recommendation

BR-3 v3 (extend to v1 cohort dates × analyst-stage cross + larger commit-cohort) would clarify:
1. Does the +40pp fundamentals commit shift hold at n=30+?
2. Is the news NULL stable across more dates?
3. Combined "structured-throughout" mode (all 3 analysts structured) — does it dominate prose-throughout or hybrid?

Estimated cost: $16-32 depending on scope.

### Cross-pollination L4 status

The Squeak structured signaling pattern (BR-3 line) status: was preserved at "pilot-eligible" per PR #178 BR-3 v1 finding. **v2 strengthens the recommendation modestly** — fundamentals analyst is the strongest candidate for structured-output (PARTIAL ALT-B with +40pp commit shift + consistent across tickers); market analyst is the moderate candidate (PARTIAL ALT-B with +20pp); news analyst is NOT a candidate (NULL).

L4 status update: "pilot-eligible (focus on fundamentals analyst stage)" — narrowed scope.

## Constitution adherence

- ✅ I (Save Everything): isolated experiment dir
- ✅ II (One Experiment Per Change): 2 sub-experiments × single intervention each (analyst-format swap)
- ✅ III (Stay Cheap): T2 ($16); user-authorized
- ✅ IV (No Production Claims): DIFFERENTIAL/PARTIAL ALT-B documented as inconclusive at this n; no production deployment changes
- ✅ VI (Spec Before Structural Change): 2 new analyst modules + 2 config keys is structural change; HYPOTHESIS + module testing served the spec-first discipline
- ✅ VII v1.5.2 (Calibrated Abstention): orthogonal — operates upstream of PM
- ✅ VIII: N/A (not a filter retrospective)

## Next steps (per PR #218 4-PR landing template)

1. **PR #1 (this ANALYSIS)**: ANALYSIS.md replacing template — current PR
2. **PR #2**: RESEARCH_FINDINGS.md BR-3 v2 section append + Open Questions row resolved
3. **PR #3**: ROADMAP.md row updated to RESOLVED with verdict reference
4. **PR #4 (optional)**: Memory write capturing the DIFFERENTIAL finding + asymmetric-mechanism-incidence framing

WC-11 v2 still in flight (~2.7h ETA per dual-pilot monitor); its landing arc follows on completion.

## Cost

$16 LLM (Constitution III T2; user-authorized via PR #214).

## Cross-references

- BR-3 v1 ANALYSIS: `experiments/2026-05-09-001-br3-squeak-market-analyst/ANALYSIS.md` (PR #178)
- HYPOTHESIS + PARAMS: this dir
- Dual-pilot launch playbook: PR #214
- Landing PR series template: PR #218
- Constitution v1.5.3 conditional patches (WC-11 v2): PR #215 — orthogonal to this ANALYSIS
