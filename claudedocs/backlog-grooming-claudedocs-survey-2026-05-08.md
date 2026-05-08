# claudedocs/ backlog grooming — stale-doc survey 2026-05-08

**Date**: 2026-05-08
**Cost**: $0 (corpus directory listing + targeted greps)
**Total docs in claudedocs/**: 99 markdown files
**Purpose**: Identify stale, superseded, or scaffold docs that warrant cleanup or annotation. Does NOT delete anything (Constitution Principle I — Save Everything).

## Cleanup categories

### Category A: Day-rollover scaffolds (1 doc) — DELETE candidate

Per `feedback_no_day_rollover_planning.md` operator memory, no docs should be anchored to future sessions. The scaffold pattern is itself an operator-flagged anti-pattern.

| Doc | Status | Recommendation |
|---|---|---|
| `research-burst-2026-05-08.md` | Written 2026-05-07 evening as a "scaffold for tomorrow." Today (the actual 2026-05-08) shipped 4+ PRs but didn't use this scaffold; the doc references obsolete predictions ("tomorrow opens with Scenario A confirmed") that are now unused. | **DELETE** OR rewrite as a today's-narrative-doc (tracking PRs #97-#101 + ongoing) |

This is the most clear-cut stale doc in the corpus.

### Category B: Mid-flight diagnostics superseded by completion (8 docs) — KEEP-with-banner

These were valuable mid-arc artifacts but the underlying experiments / surveys completed. Each is referenced by a later "completion" doc and the conclusion supersedes the mid-flight observations.

| Doc | Superseded by |
|---|---|
| `sc-009-13-bull-pre-rows-enumerated-2026-05-07.md` | `sc-009-backtest-complete-final-state-2026-05-07-night.md` (PR #57) |
| `sc-009-23-row-mark-trajectory-pass-2026-05-07-evening.md` | Same |
| `sc-009-27-row-mark-and-sweep-refresh-2026-05-07-late.md` | Same |
| `sc-009-mid-backtest-commit-pattern-2026-05-07.md` | Same |
| `sc-009-bear-side-mid-flight-diagnostic-2026-05-07.md` | Same |
| `sc-009-hold-rate-root-cause-2026-05-07.md` | Same |
| `sc-009-expansion-contingency-design-2026-05-07.md` | NOT triggered (PR #57: n_fired=13 ≥ 8 threshold met → no expansion needed) |
| `behavioral-additive-sweep-refresh-2026-05-07-evening.md` | `behavioral-additive-sweep-post-v1.4.6-ratification-2026-05-07.md` (PR #85; 29 → 44 cases extension) |

**Recommendation**: KEEP, but add a one-line banner at the top of each: `> **Superseded by [later-doc.md](other-doc.md)** — preserved as research record.`

These docs have value as snapshots of the mid-arc reasoning + are referenced in commit messages + research-burst narratives.

### Category C: Speculative-design docs closed by post-survey verdicts (1 doc) — KEEP-with-banner

| Doc | Status | Recommendation |
|---|---|---|
| `hybrid-d-and-e-feasibility-design-2026-05-07-evening.md` | Hybrid D was closed via SKIP retrospective (PR #86 `forward-catalyst-hybrid-d-retrospective-2026-05-07.md`). Hybrid E remains speculative; behavioral-additive sweep refresh confirmed sub-pattern 4 (PM stricter-than-Hold + bull-priced-in high) has empirical support but no spec invocation pursued yet. | KEEP with banner: "Hybrid D part: SUPERSEDED by PR #86 SKIP retrospective. Hybrid E part: still speculative; no spec invocation." |

### Category D: Mechanism class feasibility docs (4-5 docs) — KEEP-with-banner

These are the per-class feasibility probes from the bear-side mechanism class survey. Each was decisive in its time + the survey CONCLUDED in PR #78 with the final scorecard. Individual feasibility docs remain valuable as the per-class evidence:

| Doc | Status |
|---|---|
| `class-c2-short-interest-feasibility-2026-05-07.md` | Survey CONCLUDED — C-2 SKIP (mechanism INVERTED) |
| `class-c3-analyst-pt-feasibility-2026-05-07.md` | Survey CONCLUDED — C-3 NOT FEASIBLE |
| `class-c4-institutional-ownership-feasibility-2026-05-07.md` | Survey CONCLUDED — C-4 PASS → DEPLOYED as Spec X-1 |
| `class-c5-earnings-feasibility-2026-05-07.md` | Survey CONCLUDED — C-5 RETROACTIVE SKIP (89% overlap) |
| `class-c6-bear-news-density-skip-2026-05-07.md` | Survey CONCLUDED — C-6 SKIP (structural redundant) |

**Recommendation**: KEEP. The `bear-side-mechanism-exploration-2026-05-07.md` parent doc already cross-references all of these + has the SURVEY COMPLETE banner. No per-doc cleanup needed; the parent's TOC effectively annotates each child as "scorecard-final."

### Category E: Investigation / deep-dive docs (10+) — KEEP unchanged

| Doc | Status |
|---|---|
| `amd-2026-04-17-deep-dive-2026-05-07.md` | Textbook L-8 case; cited in v1.4.6 amendment + memory |
| `amd-2026-04-24-deep-dive-2026-05-07-evening.md` | TRIPLE behavioral-additive case |
| `amd-memory-log-audit-hallucination-resolution-2026-05-07-late.md` | PR #54 — empirical basis for Quality Gate #6 |
| `amzn-2026-04-17-04-24-deep-dive-2026-05-07-evening.md` | First operational Spec 007 fire; temporal-learning evidence |
| `avgo-temporal-jump-investigation-2026-05-07.md` | Followup investigation |
| `spec-007-calendar-independence-bac-gs-2026-05-07-late.md` | PR #56 — calendar-independence empirical evidence |
| `spec-003-fire-pattern-on-sc-009-cohort-2026-05-07.md` | PR #34 — fire-pattern probe |
| `spec-003-cold-start-diagnostic-sc-009-2026-05-07.md` | Spec 003 cold-start gap diagnostic |
| `spec-003-baseline-instrumentation-already-exists-2026-05-07-evening.md` | Followup; closes 2 followups |
| `spec-003-historical-recompute-results-2026-05-07.md` | PR #71 backfill results |
| `memory-log-integrity-systematic-finding-2026-05-07-late.md` | PR #55 — empirical basis for Quality Gate #6 |
| `sector-alpha-attribution-2026-05-06.md` | 5th failure mode discovery |

These are durable research artifacts. KEEP unchanged.

### Category F: Already-banner-annotated SUPERSEDED docs (2) — DONE

| Doc | Status |
|---|---|
| `constitution-v1.4.4-draft-2026-05-07.md` | SUPERSEDED banner added in PR #101 (ratified as v1.4.6) |
| `constitution-v1.4.5-draft-2026-05-07.md` | SUPERSEDED banner added in PR #101 (ratified as v1.4.5 AS-IS) |

No further action needed.

### Category G: Operator-facing docs — KEEP unchanged

| Doc | Status |
|---|---|
| `SETUP.md` | Operator setup guide; refreshed PR #94 |
| `research-burst-2026-05-06.md` | Yesterday's record day; complete |
| `research-burst-2026-05-07.md` | Today's session narrative; refreshed PR #96 |

These are top-of-funnel docs for operator + future-self continuity. KEEP unchanged.

## Cleanup verdict summary

| Category | Doc count | Action |
|---|---|---|
| A — Day-rollover scaffold | 1 | DELETE candidate |
| B — Mid-flight superseded by completion | 8 | Add SUPERSEDED banner |
| C — Speculative-design partially closed | 1 | Add SUPERSEDED banner (Hybrid D part) |
| D — Per-class survey feasibility | 5 | KEEP (parent doc already annotates) |
| E — Investigations / deep-dives | 12+ | KEEP unchanged |
| F — Already-banner-annotated | 2 | DONE |
| G — Operator-facing top-funnel | 3 | KEEP unchanged |
| Other (unsurveyed) | ~67 | Mostly KEEP; spot-check on operator request |

**Total cleanup target**: 1 DELETE + 9 SUPERSEDED-banner additions = 10 of 99 docs (~10%).

## Recommended PR scope

If the operator wants to action this survey:

- **Quick**: 1 PR deleting `research-burst-2026-05-08.md` (~5min, $0)
- **Medium**: 1 PR adding SUPERSEDED banners to 9 mid-flight docs (~15min, $0)
- **Bundled**: 1 PR doing both (~20min, $0)

This survey doc is the planning artifact; cleanup PRs are deferred to operator approval.

## What this survey did NOT cover

- Per-doc accuracy review (claims still true vs drifted) — would require reading each of 99 docs
- Cross-doc contradiction check (do two docs claim conflicting things) — requires whole-corpus comparison
- Backlink validation (which docs are referenced from where) — requires full grep over the codebase
- claudedocs/ directory growth rate analysis — would inform "is this signal-or-noise" question

These are valid follow-up survey passes if the operator wants deeper grooming.

## Sibling docs

- `feedback_no_day_rollover_planning.md` — operator memory; basis for Category A recommendation
- `claudedocs/research-burst-2026-05-06.md` + `claudedocs/research-burst-2026-05-07.md` — canonical narratives that mid-flight docs feed into
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` — parent doc with SURVEY COMPLETE banner (cross-references the 5 per-class feasibility docs)
- PR #101 — established the SUPERSEDED banner pattern for the v1.4.4 + v1.4.5 drafts (template to reuse for Category B + C)
