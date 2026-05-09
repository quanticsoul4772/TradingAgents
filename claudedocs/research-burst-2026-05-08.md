# Research-burst day — 2026-05-08 (extending into 2026-05-09)

**TALLY (END-OF-SESSION)**: **57 PRs shipped (#117-#173)** + **mypy 0 errors** (down from 126; 12-PR cleanup sweep) + **WC-10 v1 ALT-A confirmed** (3.6× commit ratio, $16) + **Constitution v1.4.6 → v1.5.0 → v1.5.1** (TWO-MECHANISM mode-collapse reframe) + **WC-10 v3 PARTIAL ALT-A** (Q4 2025 NVDA bear-regime, $6.40) + **Spec 009 design surface 5/7** (production deployment, conditional draft) + **Spec 011 procedure** (behavioral-additive operational codification) + **3 reusable templates extracted** (`--with-analysis-template` flag + conditional spec template + pilot landing playbook template) + **THREE PILOTS IN FLIGHT** at end of session (v2 + BR-3 Squeak + WC-11; $48 total committed).

**Pattern**: rank-driven continuous-shipping workflow via `mcp__mcp-reasoning__reasoning_decision`. ~10+ ranking decisions across the session; pre-scaffolding ranked #1 in 5+ runs; codified as project methodology in PR #164. Distinct from prior session patterns (2026-05-06 spec-first / 2026-05-07 6-PR bundle deployment).

**Cost**: $48 LLM committed ($16 v1 + $6.40 v3 + $32 v2 + $8 BR-3 + $8 WC-11). Codification + tooling work was $0. v1 + v3 verdicts merged; v2 + BR-3 + WC-11 verdicts pending.

This document is the canonical entry point for today's session. Companion to:
- `claudedocs/research-burst-2026-05-06.md` — original research-burst day (17 ship-quality units; 5 Constitution amendments)
- `claudedocs/research-burst-2026-05-07.md` — 95+ PR Spec X-1 deployment day

## Six-phase arc

The session naturally decomposed into 6 phases (per PR #164 methodology doc):

| Phase | PRs | Theme | Headline outcome |
|---|---|---|---|
| 1 | #117–#129 (12) | Mypy cleanup sweep | 126→0 errors; PR #128 4-line fix cleared 85 errors that CLAUDE.md baseline previously called "deferred / complex" |
| 2 | #130–#141 (12) | WC-10 v1 ALT-A research arc | 3.6× commit ratio; Constitution v1.5.0 amendment; Spec 009 + Spec 011 conditional scaffolds |
| 3 | #142–#152 (11) | Pre-scaffolding density | Constitution v1.5.1 conditional patches + reusable templates extracted (PR #150 + #151) |
| 4 | #153–#162 (10) | v3 landing + Spec 009 design surface | PARTIAL ALT-A verdict; Constitution v1.5.1 (Patch D); Spec 009 5/7 spec-kit artifacts |
| 5 | #163–#167 (5) | Empirical extension + methodology codification | EH-4 corpus walk (183 Holds = 43% of 427); methodology doc; cross-pollination L4 progress check |
| 6 | #168–#173 (6) | WC-10 aggregate retro + BR-3/WC-11 launches + triple-pilot coordination | Combined n=28 paired Δα +20.66pp; BR-3 + WC-11 launched; triple-landing playbook |

## The TWO-MECHANISM finding (most consequential of the day)

WC-10 v1 demonstrated that the framework's mode collapse to Hold is **not unitary** "calibrated abstention" (per the original Constitution VII framing). It's TWO-MECHANISM:

- **Mechanism A** (genuine ambiguity): bull/bear evidence is GENUINELY BALANCED; Hold is calibrated abstention per the original VII framing
- **Mechanism B** (schema-induced collapse): evidence is one-directional but moderate-magnitude; the 5-tier categorical schema lacks a partial-confidence tier; the framework would commit if the schema permitted

Empirical magnitude:
- WC-10 commit rate: 18/20 (90%) vs 5-tier 5/20 (25%) — **3.6× ratio**
- 75% paired decisions differ
- NVDA case: 8 of 10 5-tier Holds were schema-suppressed bullish reads with realized 21d α from +2.83% to +8.53% (would have been profitable)

This finding changed the corpus's interpretation framework. Constitution v1.4.6 → v1.5.0 (PR #131) carved out the schema-artifact case; v1.5.0 → v1.5.1 (PR #154) added the bear-regime magnitude bound (`|delta| < 1.0pp` per v3 PARTIAL ALT-A).

Bear-side caveat (preserved across both amendments): WC-10 amplifies the framework's existing reads regardless of direction-correctness. On v1's AAPL UW cohort during +3-6% rally, this was anti-calibrated. On v3's Q4 2025 NVDA falling cohort, this was anti-calibrated again (8 of 8 dates Buy/OW vs 5-tier 0 OW + 1 UW + 7 Hold; α delta -0.22pp).

## Verdict ledger (chronological PR order, abbreviated)

Full per-PR breakdown in memory `project_2026-05-08_record_day.md` Tracks A-F. Highlights:

| Phase | Notable PRs | Headline |
|---|---|---|
| 1 | #128 | 4-line `dict[str, Any]` annotation cleared 85 mypy errors that CLAUDE.md called "complex / deferred / needs upstream stubs" — the actual cause was simple dict invariance |
| 2 | #130 | v1 ANALYSIS — SC-007 ALT-A confirmed at p<0.001 effect size |
| 2 | #131 | Constitution VII v1.4.3 → v1.5.0 ("Schema-induced abstention is NOT calibrated abstention" sub-section) |
| 3 | #144 | 4 verdict-conditional Constitution v1.5.1 patches pre-drafted |
| 3 | #150 | `scripts/new_experiment.py --with-analysis-template` flag (extracts PR #135 pattern) |
| 3 | #151 | `.specify/templates/spec-template-conditional.md` (extracts PR #140/#144/#148 pattern) |
| 4 | #153 | v3 ANALYSIS — verdict PARTIAL ALT-A (α delta -0.22pp; 8/8 Buy/OW vs 5-tier 0 OW + 1 UW + 7 Hold) |
| 4 | #154 | Constitution v1.5.0 → v1.5.1 (Patch D applied; Bear-regime validation paragraph) |
| 5 | #163 | EH-4 historical Hold attribution Phase 1 (183 Holds = 43% of corpus) |
| 5 | #164 | Methodology doc — rank-driven continuous-shipping workflow (third meta-workflow in project history) |
| 6 | #168 | WC-10 v1+v3 aggregate retrospective (combined n=28; cohort cumulative Δα +20.66pp) |
| 6 | #169 | BR-3 Squeak implementation + launch ($8 LLM; structured-output market analyst module) |
| 6 | #171 | WC-11 order randomization launch ($8 LLM; last Tier 1 candidate) |
| 6 | #172 | Triple-pilot landing playbook (BR-3 + WC-11 + v2 simultaneous coordination) |

## Pre-scaffolding pattern empirical validation

Pre-scaffolding ranked #1 in 5+ reasoning_decision invocations today. Empirically validated end-to-end:

| Pattern | Evidence | ROI |
|---|---|---|
| v3 landing series | PR #149 playbook (3-PR, ~40 min wall-clock) | **67% reduction** vs ~120 min from scratch |
| v2 landing series (projected) | PR #161 playbook (4-PR, ~75 min projected) | ~60% projected vs ~180-240 min |
| `--with-analysis-template` flag | PR #150 (validated in PR #157 production use) | Saves 30-45 min per ANALYSIS landing |
| Conditional spec template | PR #151 (`.specify/templates/spec-template-conditional.md`) | Reusable for any future verdict-conditional spec |
| Generic landing playbook template | PR #170 (extracts PR #149 + #161 patterns) | Reusable for any future N-pilot experiment |
| Triple-pilot coordination playbook | PR #172 (BR-3 + WC-11 + v2) | Specialized for current 3-pilot scenario; sets precedent |

## Constitution evolution

Three amendments ratified during the session:

| Version | Trigger | Effect |
|---|---|---|
| v1.4.3 → **v1.5.0** | WC-10 v1 ALT-A | "Schema-induced abstention is NOT calibrated abstention" sub-section to Principle VII |
| v1.5.0 → **v1.5.1** | WC-10 v3 PARTIAL ALT-A | "Bear-regime validation" paragraph; magnitude bound `\|delta\| < 1.0pp` documented; runtime monitoring (not hard gating) is production enforcement |

Pending amendments (per triple-landing playbook PR #172, conditional on v2 + BR-3 + WC-11 verdicts):
- v1.5.1 → **v1.5.2?** — possible if v2 STRONG / NULL or WC-11 ALT-A/B (Replicability-scope sub-section amendment)
- v1.5.x → **v1.6.0?** — possible if BR-3 ALT-B (new Principle for structured-output-throughout architecture)

## Spec evolution

| Spec | Status |
|---|---|
| **Spec 011** (Behavioral-additive operational procedure) | SHIPPED single-file methodology spec (PR #136) |
| **Spec 009** (WC-10 production deployment) | 5 of 7 spec-kit artifacts SHIPPED (spec.md PR #140 + plan.md PR #156 + contracts PR #158 + research.md + quickstart.md PR #159); tasks.md + MVP/tests/polish PENDING v2 verdict |

## Filter portfolio + production tooling

Filter portfolio unchanged (9 production filters). Production tooling extended:

- **`scripts/wc_10_dryrun_digest.py`** (PR #141) — operator UX prototype against saved data
- **`scripts/wc_10_underperformance_monitor.py`** (PR #146) — production-tier runtime monitor for v1.5.1 caveat enforcement
- **`scripts/historical_hold_attribution.py`** (PR #163) — EH-4 corpus walk + Mechanism A vs B classification scaffold
- **`scripts/br3_squeak_pilot.py`** (PR #169) — BR-3 pilot harness
- **`scripts/wc11_order_pilot.py`** (PR #171) — WC-11 pilot harness

## Three pilots in flight at end-of-session

| Pilot | Cohort | Cost | ETA | Pre-scaffolded for landing |
|---|---|---|---|---|
| **v2 (n=100 ticker expansion)** | 8 tickers × 10 dates × WC-10 only | $32 | ~5h | PR #135 + #147 + #161 (full playbook) + Spec 009 5/7 |
| **BR-3 Squeak** | NVDA + AAPL × 5 dates × 2 modes | $8 | ~3h | PR #157 (ANALYSIS_TEMPLATE) |
| **WC-11 order randomization** | NVDA × 5 dates × 4 permutations | $8 | ~3h | PR #173 (ANALYSIS_TEMPLATE) |

Triple-landing coordinated via PR #172 playbook (3 coordination mechanisms + 9-branch Constitution implications matrix).

## Methodology lessons codified as memory

| Memory entry | Lesson |
|---|---|
| `reference_llm_client_kwargs_dict_invariance.md` | Verify "deferred / complex" baseline classifications by trying simple fix first (PR #128 lesson) |
| `reference_conditional_branch_spec_pattern.md` | Pre-write N verdict-conditional branches NOW; post-verdict edit becomes deterministic pick (PR #151 codification) |
| `project_2026-05-08_record_day.md` | Day-arc summary updated 2× during session (51-PR snapshot + 57-PR end-of-session refresh) |

Plus the methodology doc itself (PR #164) lives in `claudedocs/methodology-rank-driven-workflow-2026-05-08.md` — could be promoted to memory entry as a future improvement.

## Risk assessment (end-of-session)

**LOW**:
- Quality gates intact: mypy 0 / ruff 0 / 1168 tests PASS across every PR
- Cost discipline preserved: each pilot launch explicitly authorized; v2 over T2 cap deliberated in HYPOTHESIS

**MEDIUM**:
- Operator review capacity: 12+ landing PRs converging in ~2h window when all 3 pilots land
- Constitution amendment sequencing: if multiple amendments fire (WC-11 ALT-A + BR-3 ALT-B + v2 STRONG), sequence per VI v1.4.1
- $48 in-flight LLM (over T2 cap; deliberated)

**HIGH**: none identified.

## Comparison to prior burst days

| Day | PRs | Pattern | Constitution amendments | Specs |
|---|---:|---|---:|---|
| 2026-05-06 | 17 ship-quality units | spec-first invocation | 5 (v1.3.0 → v1.4.3) | Spec 008 deployment |
| 2026-05-07 | 95+ PRs | 6-PR bundle deployment | 2 (v1.4.5 + v1.4.6) | Spec X-1 deployment + Spec 010 SKIP |
| **2026-05-08 (this)** | **57+ PRs (#117-#173+)** | **rank-driven continuous shipping** | **2 (v1.5.0 + v1.5.1; possibly more pending pilots)** | **Spec 011 + Spec 009 5/7 + 3 reusable templates** |

The rank-driven pattern emerged organically as the third identified workflow in the project's history. Each is appropriate for its session character.

## Pending work (entering future sessions)

**In flight** (will land in next ~5h after end-of-session):
- v2 verdict → Spec 009 Branch A/B/C selection + 4-PR landing series per PR #161 playbook
- BR-3 verdict → ANALYSIS + RESEARCH_FINDINGS update; possibly Phase E spec scaffold if ALT-B
- WC-11 verdict → ANALYSIS + RESEARCH_FINDINGS update; possibly Constitution v1.5.2 amendment if ALT-A or ALT-B

**Deferred** (post-verdict; not blocking):
- EH-4 Phase 2 (state-log feature extraction; needs v2 calibration data)
- Spec 009 PRs #4-#7 (tasks → MVP → tests → polish; needs v2 branch selection)
- Memory cleanup pass (~32 entries; some may be stale post-v1.5.1)

**Possible follow-up**: research-burst-2026-05-09.md sister doc capturing the post-landing arc once all 3 pilots complete + their landing series ship.

## Single-line takeaway

The session validated rank-driven continuous-shipping workflow at unprecedented volume (57 PRs / day extending across midnight) while shipping decisive empirical evidence (WC-10 ALT-A → PARTIAL ALT-A → 3 follow-up pilots in flight), a Constitution principle reframe (TWO-MECHANISM mode collapse), the reusable infrastructure (3 templates + 5 production tools + Spec 009 design surface), and the methodology codification (PR #164) needed for the rank-driven pattern to inherit forward.

## Cross-references

- Memory `project_2026-05-08_record_day.md` — day-arc memory (full Track A-F PR breakdowns)
- `claudedocs/methodology-rank-driven-workflow-2026-05-08.md` (PR #164) — workflow pattern codification
- `claudedocs/wc-10-v1-v3-aggregate-retrospective-2026-05-08.md` (PR #168) — WC-10 unified arc
- `claudedocs/triple-pilot-landing-playbook-2026-05-09.md` (PR #172) — triple-landing coordination
- `claudedocs/templates/pilot-landing-pr-series-template.md` (PR #170) — generic landing template
- `claudedocs/cross-pollination-l4-progress-check-2026-05-08.md` (PR #167) — L4 candidate progress
- Constitution v1.5.1 Principle VII sub-section + Bear-regime validation paragraph
- Sister burst docs: `research-burst-2026-05-06.md` + `research-burst-2026-05-07.md`
