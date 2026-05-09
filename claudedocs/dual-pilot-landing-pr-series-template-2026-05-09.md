# Dual-pilot landing PR series template — WC-11 v2 + BR-3 v2 (2026-05-09)

**Status**: PRE-SCAFFOLDED for the dual-pilot landing arc (in flight; ETA ~2026-05-10).

**Pattern source**: `claudedocs/v2-landing-pr-series-bundle-template-2026-05-08.md` (PR #161 — 4-PR landing playbook for WC-10 v2; deployed via PRs #181-#184).

**Sister doc**: `claudedocs/dual-pilot-launch-playbook-2026-05-09.md` (PR #214 — operator-facing coordination + Constitution amendment evaluation per verdict).

This template captures the EXACT PR sequence + commit-message structure + scope-per-PR for the post-data landing arc. When BR-3 v2 lands first (~8h ETA per dual_pilot_monitor) and WC-11 v2 lands second (~12h ETA), each pilot's landing follows this template.

## 4-PR landing sequence (per pilot — applies to BOTH WC-11 v2 + BR-3 v2)

Per the triple-pilot landing precedent (PR #172 + #181-#184), each pilot's landing is a 4-PR series. Total across BOTH pilots: ~8 PRs landing in sequence.

### PR #1 of 4 (per pilot): ANALYSIS

**Branch**: `<NNN>-<pilot>-v2-analysis-<verdict>`
**Title**: `research(<pilot> v2): ANALYSIS — <verdict> verdict`
**Scope**:
- `experiments/<pilot-dir>/ANALYSIS.md` (move from ANALYSIS_TEMPLATE.md; plug in computed numbers + pick verdict block)
- `experiments/<pilot-dir>/ANALYSIS_TEMPLATE.md` (deleted)

**Wall-clock estimate**: ~30-45 min per pilot (computation snippet + plug-in numbers + delete 4 of 5 verdict blocks + commit).

### PR #2 of 4 (per pilot): RESEARCH_FINDINGS append

**Branch**: `<NNN>-research-findings-<pilot>-v2-section-append`
**Title**: `research(<pilot> v2): RESEARCH_FINDINGS section append + Open Questions row resolved`
**Scope**:
- `RESEARCH_FINDINGS.md` (new top-level section after the most-recent prior section; cite verdict + ANALYSIS PR)
- `RESEARCH_FINDINGS.md` Open Questions table row updated to RESOLVED with verdict reference (PR #182 precedent)

**Wall-clock estimate**: ~15-20 min per pilot.

### PR #3 of 4 (per pilot): ROADMAP update

**Branch**: `<NNN>-roadmap-<pilot>-v2-resolved`
**Title**: `roadmap: <pilot> v2 row RESOLVED — <verdict>`
**Scope**:
- `ROADMAP.md` Open Questions row updated from "in flight" → "RESOLVED 2026-05-10 — <verdict>"

**Wall-clock estimate**: ~5-10 min per pilot.

### PR #4 of 4 (per pilot OR joint): Constitution amendment + memory writes

This PR is OPTIONAL per pilot:
- WC-11 v2: Constitution patch from PR #215 conditional-drafts file (1 of 5 patches per verdict)
- BR-3 v2: NO Constitution amendment unless ALT-B confirmed (rare; would unblock Phase E "Structured-output-throughout" Principle as MAJOR v1.6.0)

**Branch**: `<NNN>-constitution-v153-<pilot>-v2-<verdict>` OR `<NNN>-memory-writes-<pilot>-v2`
**Title**: `constitution(VII): v1.5.2 → v1.5.3 — <patch description> per <pilot> v2 <verdict>` OR `memory: <pilot> v2 sister memory entry`
**Scope**:
- `.specify/memory/constitution.md` (apply matching patch from PR #215; bump version + add narrative)
- Global memory: new sister-memory entry per pilot (optional; PR #180-aux precedent)

**Wall-clock estimate**: ~15-20 min per pilot (Constitution patch is deterministic pick + plug-in per PR #215 pre-scaffolding).

## Sequencing rule (per Constitution VI v1.4.1 + PR #172 triple-pilot precedent)

**WC-11 v2 amendment lands FIRST** (most foundational; affects corpus interpretation per Constitution VII v1.5.2 mandate). Per PR #179 precedent, the Constitution amendment for WC-11 lands BEFORE the joint RESEARCH_FINDINGS update.

**BR-3 v2 amendment is conditional** — only fires if ALT-B confirmed (would be Phase E unblock; MAJOR v1.6.0). Otherwise no amendment; PR #4 of BR-3 series collapses to memory-writes-only.

## Scope discipline (per PR #172 disjoint-sections rule)

To prevent merge conflicts on shared files (RESEARCH_FINDINGS.md, ROADMAP.md), each pilot's landing PR targets a DISJOINT section:

- WC-11 v2 RESEARCH_FINDINGS section append: NEW top-level section "## WC-11 v2 disambiguation (added 2026-05-10)" inserted after WC-10 v2 section
- BR-3 v2 RESEARCH_FINDINGS section append: NEW top-level section "## BR-3 v2 (news + fundamentals) (added 2026-05-10)" inserted after WC-11 v2 section
- WC-11 v2 ROADMAP row update: Open Questions row at line ~349
- BR-3 v2 ROADMAP row update: Open Questions row at line ~350 (different row; no conflict)

## Total estimated wall-clock for the full landing arc

- BR-3 v2 lands first (~8h ETA): 4 PRs × ~15-30 min = ~1-1.5h
- WC-11 v2 lands second (~12h ETA): 4 PRs × ~15-30 min = ~1-1.5h
- Joint synthesis refresh (research-burst-2026-05-10.md if applicable): ~15 min
- **Total**: ~2.5-3.5h from first-pilot-data-landing → all PRs merged

This is half the wall-clock of equivalent cold-draft work (~6h estimated without pre-scaffolding).

## Pre-scaffolding ROI summary

| Artifact | Status |
|---|---|
| WC-11 v2 ANALYSIS_TEMPLATE.md (5 verdict-conditional blocks) | ✅ shipped PR #214 |
| BR-3 v2 ANALYSIS_TEMPLATE.md (5 verdict-conditional blocks per sub-experiment) | ✅ shipped PR #214 |
| Constitution v1.5.3 conditional patch drafts (5 verdict-conditional patches) | ✅ shipped PR #215 |
| Dual-pilot launch playbook (operator coordination) | ✅ shipped PR #214 |
| Dual-pilot monitor script | ✅ shipped PR #216 |
| ROADMAP in-flight rows | ✅ shipped PR #217 |
| 4-PR landing series template (this doc) | ✅ shipped PR #X (this) |

**Pre-scaffolding ROI projection** (per memory `reference_conditional_branch_spec_pattern.md` + PR #185 cumulative ~3-6x):
- Without pre-scaffolding: ~6h cold-draft estimate for the landing arc
- With pre-scaffolding: ~2.5-3.5h
- **Savings: ~2.5-3.5h** (40-60% reduction)

## Verdict-conditional landing-PR scope details

### WC-11 v2 verdict-conditional scope per Patch (mapping to PR #215)

| Verdict | PR #4 scope | Net Δ wall-clock |
|---|---|---|
| NULL revised → Patch B (REVERT) | constitution.md REVERT v1.5.2 → v1.5.1 + paragraph removal | +5 min (REVERT is more careful than PATCH) |
| ALT-A confirmed → Patch A (STRENGTHEN) | constitution.md PATCH v1.5.2 → v1.5.3 + new "ALT-A confirmation" paragraph + RESEARCH_FINDINGS adds news-first recommendation note | nominal |
| ALT-B confirmed → Patch C (STRENGTHEN) | constitution.md PATCH v1.5.2 → v1.5.3 + new "ALT-B confirmation" paragraph + ROADMAP adds market-last avoidance recommendation | nominal |
| PARTIAL → Patch D (CLARIFY) | constitution.md PATCH v1.5.2 → v1.5.3 + new "Ticker-conditional clarification" paragraph | nominal |
| INCONCLUSIVE → Patch E (RE-EVAL trigger) | constitution.md PATCH v1.5.2 → v1.5.3 + new "Re-evaluation trigger at n≥200" note | nominal |

### BR-3 v2 verdict-conditional scope per sub-experiment

| Sub-A verdict | Sub-B verdict | PR #4 scope |
|---|---|---|
| NULL | NULL | NO Constitution amendment; memory entry "BR-3 v2 — analyst-stage prose-to-structured is market-analyst-specific" |
| ALT-B (either) | ALT-B (either) | Phase E architectural variant unblocked at "broad analyst-stage" scope; Constitution v1.6.0 MAJOR amendment "Structured-output-throughout architecture" Principle drafting eligible |
| PARTIAL ALT-B (either) | PARTIAL ALT-B (either) | Same as v1; analyst-stage effect REAL but n insufficient |
| DIFFERENTIAL (A NULL, B ALT-B OR vice versa) | — | Memory entry: analyst-specific bottleneck on ONE analyst; document which |

## Operational checklist (when each pilot lands)

```
For each pilot (BR-3 v2 first, WC-11 v2 second):

  [ ] Run computation snippet from ANALYSIS_TEMPLATE.md
  [ ] Pick verdict per HYPOTHESIS framework
  [ ] PR #1: Move ANALYSIS_TEMPLATE.md → ANALYSIS.md; plug numbers; delete non-matching verdict blocks; commit + push + open PR
  [ ] User merge of PR #1
  [ ] PR #2: Append RESEARCH_FINDINGS new section; mark Open Questions row RESOLVED; commit + push + open PR
  [ ] User merge of PR #2
  [ ] PR #3: ROADMAP row RESOLVED with verdict reference; commit + push + open PR
  [ ] User merge of PR #3
  [ ] PR #4 (conditional): Constitution amendment per PR #215 patch (WC-11 v2 only) OR memory write (both pilots, optional)
  [ ] User merge of PR #4

After both pilots fully landed:
  [ ] Day-end synthesis refresh (research-burst-2026-05-09.md OR research-burst-2026-05-10.md if rolled over)
  [ ] Day-arc memory entry refresh (project_2026-05-09_record_day.md OR new project_2026-05-10 entry)
  [ ] MEMORY.md index refresh
```

## Cross-references

- Triple-pilot landing precedent: PR #172 (3-pilot coordination playbook)
- v2 4-PR landing playbook: PR #161 (WC-10 v2 landing series; deployed via #181-#184)
- Dual-pilot launch playbook: PR #214 (operator-facing)
- Constitution v1.5.3 conditional patches: PR #215 (5 verdict-conditional drafts)
- Dual-pilot monitor: PR #216
- ROADMAP in-flight rows: PR #217
- Memory: `reference_conditional_branch_spec_pattern.md` (PR #151)
- Memory: `reference_speckit_5pr_vs_6pr_pattern.md` (post-Spec 012; Spec X-1 6-PR vs Spec 012 5-PR)
