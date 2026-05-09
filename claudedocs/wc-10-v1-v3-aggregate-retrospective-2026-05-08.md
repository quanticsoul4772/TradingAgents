# WC-10 aggregate retrospective: v1 + v3 (v2 pending) — 2026-05-08

**Trigger**: reasoning_decision rank #9 (0.535 score) — operator-selected. Bridges the two completed WC-10 pilots into a unified synthesis. v2 (n=100 ticker expansion) still in flight; this doc gets a v2-integration appendix when v2 lands.

**Scope**: 36 propagates total across 2 cohorts on 3 tickers. ~$22.40 LLM spent.

---

## The arc in one sentence

WC-10 confirmed the **categorical bottleneck hypothesis** (PM stage) at distribution level (v1 ALT-A; 3.6× commit ratio) and bounded the **bear-regime amplification caveat** at < 1pp magnitude (v3 PARTIAL ALT-A) — together establishing that the 5-tier categorical PortfolioRating enum is a real but bounded constraint on the framework's commit calibration.

## Verdict chain

| Pilot | Cohort | Verdict | Magnitude | Evidence |
|---|---|---|---|---|
| **v1** | NVDA + AAPL × 10 dates Apr 2026 (paired modes) | **ALT-A** (categorical-bottleneck-confirmed) | 3.6× commit ratio (90% vs 25%); 75% paired decisions differ | Distribution-level; PM Stage |
| **v3** | NVDA × 8 dates Q4 2025 bear regime (paired modes) | **PARTIAL ALT-A** (direction matches, magnitude < 1pp) | α delta -0.22pp; 8/8 dates Buy/OW vs 5-tier 0 OW + 1 UW + 7 Hold | Realized α; bear-regime stress |
| v2 (in flight) | 8 tickers × 10 dates Q1 2026 (WC-10-only mode) | TBD | TBD — primary metric SC-005(b) Pearson r at n=100 | Cross-ticker generalization |

## What v1 established

WC-10 v1 demonstrated the **categorical bottleneck**:

- **3.6× commit ratio** (18/20 vs 5/20 on the same dates) — distribution-level effect
- **75% paired decisions differ** — same date, different mode → different output
- **NVDA case study**: 8 of 10 5-tier Holds were schema-suppressed bullish reads with realized 21d α from +2.83% to +8.53% (would have been profitable). The collapse-to-Hold was a SCHEMA artifact.
- **AAPL case study**: WC-10 amplified bearish reads (6 UW vs 5-tier 3 UW + 7 Hold) on a rising AAPL — bearish-side anti-calibrated on this cohort

**Constitution VII v1.4.3 → v1.5.0** amendment: added "Schema-induced abstention is NOT calibrated abstention" sub-section per the v1 NVDA evidence. Mode collapse to Hold reframed as **TWO-MECHANISM** (Mechanism A = genuine ambiguity; Mechanism B = schema-induced collapse).

**v1 caveat (preserved)**: "WC-10 doesn't fix bear-side calibration; it amplifies whatever signal the framework was already generating." Bear-regime validation flagged as required follow-up.

## What v3 added

WC-10 v3 tested the v1 caveat directly on the corpus's HARDEST regime — Q4 2025 NVDA, where the framework's commits historically failed (-0.47% mean 21d α, 22% hit rate per RESEARCH_FINDINGS headline).

Key v3 numbers:
- WC-10 emitted **8/8 dates as Buy/OW** (binned). Reading bullish on a falling cohort.
- 5-tier emitted **0 OW + 1 UW + 7 Hold** — the single UW (2025-11-07, NVDA fell -3.48%) was DIRECTIONALLY CORRECT
- WC-10 mean rating-attributed 21d α: +0.21%
- 5-tier mean rating-attributed 21d α: +0.44%
- **α delta: -0.22pp** (within ±100bps NULL region; direction matches ALT-A)

**Per-date worst Δpp**: 2025-11-14 (-7.57pp; NVDA fell 7.57% post-OW commit) + 2025-11-07 (-6.97pp; WC-10 lost the only correct UW the 5-tier got).

**Per-date best Δpp**: 2025-11-28 (+5.13pp) + 2025-12-12 (+3.08pp) + 2025-12-05 (+2.81pp) — bullish commits where WC-10 collapsed Hold-to-Buy/OW were validated by realized α.

**Constitution VII v1.5.0 → v1.5.1** amendment: added "Bear-regime validation" paragraph documenting the empirical magnitude bound (`|α delta| < 1.0pp` on this cohort). Caveat language preserved at v1.5.0 scope; magnitude bound formalizes the "asymmetric calibration" finding.

**Operational implication**: Spec 009 Branch A activation does NOT require regime-aware gating as a hard requirement. Runtime monitoring via `scripts/wc_10_underperformance_monitor.py` (PR #146) is the production-tier enforcement. Smoke test on v3 cohort (PR #165) empirically confirmed: cohort cumulative Δα -1.76pp, 2 per-pair alerts on the 2 worst dates.

## Side-by-side cohort comparison

| Metric | v1 | v3 | Combined (n=28 paired) |
|---|---:|---:|---:|
| Tickers | NVDA + AAPL | NVDA only | 2 distinct |
| Dates | 10 (Apr 2026) | 8 (Nov-Dec 2025) | 18 distinct |
| Paired propagates | 20 | 8 | 28 |
| WC-10 commit rate (\|rating\|>0.2) | 90% (18/20) | 100% (8/8) | 93% (26/28) |
| 5-tier non-Hold rate | 25% (5/20) | 12.5% (1/8) | 21% (6/28) |
| Decisions differ | 75% (15/20) | 100% (8/8) | 82% (23/28) |
| WC-10 mean attributed α | not directly comparable to v1 (v1 reports per-bucket) | +0.21% | n/a |
| 5-tier mean attributed α | n/a (v1 reports per-bucket) | +0.44% | n/a |
| Cohort cumulative Δα | +22.42pp (per PR #146 monitor) | -1.76pp (per PR #165 monitor) | +20.66pp (combined) |

The **combined cohort cumulative Δα = +20.66pp** is dominated by v1's bullish-NVDA cohort's wins. The bear-regime cohort's marginal underperformance (-1.76pp) doesn't undo the bull-regime cohort's substantial overperformance (+22.42pp), which is the empirical foundation for Constitution v1.5.1's caveat scope ("magnitude bounded; runtime monitoring sufficient").

## Per-bucket realized α (v1 only — v3 is N/A since no Hold or UW commits)

From PR #130 v1 ANALYSIS:

| Bucket | WC-10 n | WC-10 mean α | 5-tier n | 5-tier mean α |
|---|---:|---:|---:|---:|
| Buy | 6 | **+4.67%** | 1 | +2.41% |
| Overweight | 6 | +2.34% | 1 | +2.93% |
| Hold | 2 | +4.29% | 15 | +3.97% |
| Underweight | 6 | **+3.56%** (anti-cal) | 3 | +2.37% |

The **NVDA Buy n=6 mean +4.67% α** is the load-bearing bullish-amplification finding. v2 (n=100) will test whether this generalizes beyond NVDA + AAPL.

## What v2 will resolve

v2 (in flight; ~5-6h remaining as of this doc) ships 80 propagates × WC-10 mode only (no paired baseline within v2; v1 paired baseline is the comparison).

Three primary metrics:

1. **SC-005(b)**: signed-rating × 21d-α correlation at n=100 (combining v1+v2 WC-10 cohorts). Critical r at p=0.05/n=100 = ±0.197.
   - STRONG (`|r| > 0.30`) → Spec 009 Branch A activation
   - MODERATE (`0.197 < |r| < 0.30`) → Spec 009 Branch B (research-only)
   - NULL (`|r| < 0.197`) → Spec 009 Branch C (bin-then-output ergonomic-only)
2. **FR-005 generalization**: per-ticker commit rate ≥80% on ≥6 of 8 tickers required for Branch A.
3. **NVDA Buy generalization**: does the v1 NVDA Buy mean +4.67% α generalize beyond NVDA on the broader 6-ticker (MSFT/GOOG/AMZN/JPM/JNJ/XOM) base?

When v2 lands, the v2 LANDING PR series (per PR #161 playbook) ships in ~75 min: ANALYSIS.md → Spec 009 tasks.md → RESEARCH_FINDINGS update → ROADMAP refresh.

## Constitution implications

| Amendment | Trigger | Effect |
|---|---|---|
| v1.4.3 → **v1.5.0** | v1 ALT-A | "Schema-induced abstention is NOT calibrated abstention" sub-section added; Hold reframed as TWO-MECHANISM |
| v1.5.0 → **v1.5.1** | v3 PARTIAL ALT-A | "Bear-regime validation" paragraph added; empirical magnitude bound `\|delta\| < 1.0pp` documented; runtime monitoring (not hard gating) is production enforcement |
| v1.5.1 → v1.5.2? | v2 STRONG | Possible: "Cross-ticker generalization" paragraph; cohort coverage extended |
| v1.5.1 → v1.5.2? | v2 NULL | Possible: caveat scope tightened to "schema fix is interpretive convenience only; doesn't surface signal beyond binary commit/abstain" |

## Spec implications

Spec 009 (WC-10 production deployment) design surface 5/7 complete:
- ✅ spec.md (PR #140) — 4 verdict-conditional branches A/B/C/D
- ✅ plan.md (PR #156) — Branch A/B/C implementation paths
- ✅ contracts/daily_signals_wc_10_flag.md (PR #158) — flag CLI surface
- ✅ research.md (PR #159) — 8 decisions log
- ✅ quickstart.md (PR #159) — operator activation guide
- ⏳ tasks.md (pending v2 verdict)
- ⏳ MVP / tests / polish (pending v2 verdict)

When v2 lands, Spec 009 ships its remaining 4-PR bundle to activate the selected branch.

## Sister artifacts

- **Spec 011** (PR #136) — behavioral-additive operational procedure (orthogonal methodology spec)
- **PR #146** + **#165** — `scripts/wc_10_underperformance_monitor.py` + v1 + v3 cohort smoke tests (production monitoring)
- **PR #141** — `scripts/wc_10_dryrun_digest.py` (operator UX prototype against saved data)
- **PR #144** — Constitution v1.5.1 conditional patches (4 verdicts × 1 patch)
- **PR #149** — v3 landing PR series bundle template
- **PR #161** — v2 landing PR series bundle template
- **PR #157** — BR-3 Squeak scaffold (sister hypothesis at analyst stage)
- **PR #163** — EH-4 historical Hold attribution Phase 1 (183 Holds = 43% of corpus)

## Headline takeaways for the project research record

1. **Categorical bottleneck is real** (v1 ALT-A confirmed at p<0.001 effect size). The 5-tier scale was suppressing roughly 65pp of commits the framework would have made under continuous output (90% vs 25%).

2. **Bear-regime amplification is asymmetric but bounded** (v3 PARTIAL ALT-A). The framework's existing reads get amplified regardless of direction-correctness; on bear-regime cohorts where reads are wrong, WC-10 amplifies the wrongness, BUT the magnitude is small (`|delta| < 1pp`).

3. **Mode collapse is TWO-MECHANISM**, not unitary. Constitution VII v1.5.0 carved out the schema-artifact case; v1.5.1 bounded the bear-regime caveat.

4. **Production deployment is conditional on v2** (Spec 009 Branch A/B/C selection per SC-005(b) verdict + FR-005 cohort threshold). Branch D pre-ruled-out per v3.

5. **Runtime monitoring suffices** (per v1.5.1) — `scripts/wc_10_underperformance_monitor.py` is the operational enforcement layer. No regime-aware hard gate required.

6. **Combined cohort cumulative Δα +20.66pp** across n=28 paired propagates — bull-regime wins dominate bear-regime losses by ~13×. This is the empirical foundation for the v1.5.1 "magnitude bounded" framing.

## v2-integration appendix (PENDING)

Will be appended to this doc when v2 lands. Expected sections:
- v2 ANALYSIS verdict + per-ticker breakdown
- Updated combined cohort cumulative Δα at n=100+
- Spec 009 branch selection per the verdict matrix
- Constitution v1.5.2? — pending v2 verdict
- Final WC-10 arc summary (v1 + v2 + v3 unified narrative)

## Cost summary

| Pilot | Cost |
|---|---:|
| v1 | $16 |
| v3 | $6.40 |
| v2 (in flight) | $32 |
| **Total** | **$54.40** |

Plus the 51 PRs of supporting work today (Constitution amendments / Spec 009 design surface / monitoring tooling / scaffolds / docs) — all $0 LLM (codification + infrastructure).

## Cross-references

- v1 ANALYSIS.md (PR #130) — original SC-007 ALT-A verdict
- v3 ANALYSIS.md (PR #153) — PARTIAL ALT-A verdict
- Constitution v1.5.0 sub-section (PR #131) + v1.5.1 paragraph (PR #154)
- RESEARCH_FINDINGS.md WC-10 section (PRs #132 + #138 + #155)
- Spec 009 spec-kit bundle (PRs #140 + #156 + #158 + #159)
- v2 landing playbook (PR #161) + v3 landing playbook (PR #149)
- Monitor + smoke tests (PRs #146 + #165)
- Memory `project_2026-05-08_record_day.md` — full day-arc context
- Memory `reference_conditional_branch_spec_pattern.md` (PR #151) — pattern source for Spec 009 + Constitution v1.5.1 patches
