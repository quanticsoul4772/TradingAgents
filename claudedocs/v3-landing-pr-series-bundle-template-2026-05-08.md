# v3 landing PR series bundle template — 2026-05-08

> **STATUS**: PRE-LANDING TEMPLATE. WC-10 v3 (Q4 2025 NVDA bear-regime) data lands soon (~30 min). When it does, follow the workflow below — all 3 PRs land in ~30 min total (vs ~90+ min from scratch).

**Trigger**: reasoning_decision rank #1 (0.74 score). Bundles the four pre-scaffolded artifacts (PR #135 + PR #144 + PR #146 + PR #147) into a single v3 landing playbook.

## The 3-PR landing series

When v3 results.csv reaches 16 rows, the v3 landing series consists of:

| PR | Type | Estimated time | Pre-scaffolded by |
|---|---|---|---|
| **Landing PR #1** — v3 ANALYSIS.md | research | ~15 min | PR #135 + PR #147 (extended template) |
| **Landing PR #2** — Constitution v1.5.0 → v1.5.1 (Patch A/B/C/D) | constitution amendment | ~15 min | PR #144 (4 conditional patches) |
| **Landing PR #3** — RESEARCH_FINDINGS.md update + ROADMAP cross-ref | synthesis | ~10 min | template below |

Total: **~40 min wall-clock** vs ~120+ min from scratch.

## Workflow (copy-paste ready)

### Step 1: Verify v3 completion + run computation snippet (3 min)

```bash
cd C:/Development/Projects/TradingAgents
wc -l experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv
# Should print 17 (16 data rows + header). If less, wait for completion.

# Run the computation snippet from the v3 ANALYSIS_TEMPLATE.md (PR #147 Section A)
# Outputs verdict line citing the matching Constitution v1.5.1 patch.
```

### Step 2: Open Landing PR #1 — v3 ANALYSIS.md (15 min)

```bash
git checkout main && git pull origin main
git checkout -b 150-v3-analysis-landing
```

Then:

1. Copy `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS_TEMPLATE.md` → `ANALYSIS.md` in the same dir
2. From PR #147 Section A computation snippet output, replace ALL `<TBD>` placeholders with computed values
3. From PR #147 Section B, KEEP the matching verdict block + DELETE the other 3
4. Update the Constitution adherence checklist line `<TBD VII>` → final mark per the verdict block's implication
5. Update Next-steps section to point to the matching Spec 009 branch
6. Run `scripts/wc_10_underperformance_monitor.py --csv experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv` and paste output as a Section C "Monitoring smoke test" addendum
7. `git add` + commit with message: `research(WC-10 v3): ANALYSIS — verdict <X> on Q4 2025 NVDA bear-regime`
8. `gh pr create` with title matching commit + body summarizing all 5 metric verdicts

### Step 3: Open Landing PR #2 — Constitution v1.5.1 patch (15 min)

```bash
git checkout main && git pull origin main
git checkout -b 151-constitution-v1.5.1-patch-<verdict>
```

Then:

1. From PR #144's `claudedocs/constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md`, find the patch matching the v3 verdict (A/B/C/D)
2. Apply the patch text edit to `.specify/memory/constitution.md`:
   - Append the "Bear-regime validation" paragraph to Principle VII sub-section
   - Update the version bump in the header (v1.5.0 → v1.5.1)
3. Replace `<FILL: X>` placeholders in the appended paragraph with v3 ANALYSIS values
4. Replace `2026-05-XX` with `2026-05-08` (or actual date)
5. `git add` + commit with message: `constitution(VII): v1.5.0 → v1.5.1 — bear-regime validation paragraph (verdict <X>)`
6. `gh pr create`

### Step 4: Open Landing PR #3 — RESEARCH_FINDINGS + ROADMAP cross-ref (10 min)

```bash
git checkout main && git pull origin main
git checkout -b 152-research-findings-v3-integration
```

Edits:

1. **`RESEARCH_FINDINGS.md` Headline section** — append a sentence to the WC-10 paragraph:
   > "WC-10 v3 (Q4 2025 NVDA bear-regime, n=8 paired) produced verdict <X>; α delta <FILL: delta>pp. Constitution VII v1.5.0 → v1.5.1 (Patch <X>) per `claudedocs/constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md` PR #144 application."

2. **`RESEARCH_FINDINGS.md` "WC-10 v1 pilot — categorical bottleneck confirmed" section** — add a new sub-section "WC-10 v3 follow-up — bear-regime validation":
   > Brief summary of v3 verdict + α delta + per-pair detail count. Reference to v3 ANALYSIS.md.

3. **`RESEARCH_FINDINGS.md` Open Questions table** — mark "Does WC-10 schema fix make bear-regime calibration WORSE / NEUTRAL / BETTER?" as RESOLVED:
   > ~~In flight (WC-10 v3)~~ — **RESOLVED 2026-05-08**, see v3 ANALYSIS.md (verdict <X>).

4. **`ROADMAP.md` 2026-05-08 PRs section** — append v3-landing PR numbers (Landing PR #1, #2, #3 = #150-152 estimated) + verdict summary

5. `git add` + commit with message: `research: integrate WC-10 v3 verdict <X> into RESEARCH_FINDINGS + ROADMAP`
6. `gh pr create`

## RESEARCH_FINDINGS update — pre-written verdict-conditional sentences

The exact sentences to drop into RESEARCH_FINDINGS depend on the verdict. Pre-written:

### If verdict ALT-A:

> WC-10 v3 (Q4 2025 NVDA bear-regime, n=8 paired) confirmed ALT-A: α delta of <FILL: delta>pp WORSE under WC-10 mode on this falling cohort. Constitution VII v1.5.0 → **v1.5.1** (Patch A) added the "Bear-regime validation" paragraph requiring regime-aware gating for WC-10 production deployment. Spec 009 Branch A activation now requires a regime-detection signal.

### If verdict NULL:

> WC-10 v3 (Q4 2025 NVDA bear-regime, n=8 paired) produced NULL: α delta of <FILL: delta>pp — statistically indistinguishable from baseline. Constitution VII v1.5.0 → **v1.5.1** (Patch B) preserved the asymmetric-calibration caveat for documentation but downgraded it from a hard requirement to a runtime-monitoring trigger via `scripts/wc_10_underperformance_monitor.py`. The v1 AAPL UW finding is reframed as a single-cohort artifact rather than a universal bear-side mechanism. Spec 009 Branch A activation does NOT require regime-aware gating per this evidence.

### If verdict ALT-B:

> WC-10 v3 (Q4 2025 NVDA bear-regime, n=8 paired) produced ALT-B (REVERSED v1 caveat direction): α delta of <FILL: delta>pp BETTER under WC-10 mode on this falling cohort. WC-10 surfaced bearish reads on Q4 2025 NVDA that 5-tier suppressed (<FILL: WC-10 bear count>/8 dates as Underweight). Constitution VII v1.5.0 → **v1.5.1** (Patch C) reframed the v1 AAPL UW finding as a regime-specific counter-case rather than a universal bear-side mechanism. WC-10 mode is universally beneficial across the bull/bear spectrum on this evidence basis. Spec 009 Branch A ships without regime-aware gating.

### If verdict PARTIAL ALT-A:

> WC-10 v3 (Q4 2025 NVDA bear-regime, n=8 paired) produced PARTIAL ALT-A: α delta of <FILL: delta>pp (direction matches ALT-A but magnitude < 1pp). Constitution VII v1.5.0 → **v1.5.1** (Patch D) preserved the v1.5.0 caveat language; documented empirical magnitude bound at < 1pp on this cohort. Spec 009 Branch A activation ships with the v1.5.0 caveat documented in `docs/SIGNALS.md` per Spec 009 FR-006 but does NOT require regime-aware gating as a hard requirement.

## Open-Questions table update

In `RESEARCH_FINDINGS.md` "What's still open" section, find the row:

> | Does WC-10 schema fix make bear-regime calibration WORSE or just NEUTRAL? ... | $8-16 (T2) | **in flight (WC-10 v3)** |

Replace with:

> | ~~Does WC-10 schema fix make bear-regime calibration WORSE or just NEUTRAL?~~ — **RESOLVED 2026-05-08**, verdict <X> per `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS.md` (Landing PR #150). | (resolved) | $6.40 |

## Bundling decision: separate vs single PR

Two options:

### Option A — 3 separate PRs (recommended)

Each landing PR is independently mergeable + reviewable. Sister to today's pattern of small focused PRs (#117-#148 are mostly single-purpose).

Pros:
- Constitution amendment landing alone is the cleanest archival event
- RESEARCH_FINDINGS update can be merged independently of constitutional approval
- Standard workflow today

Cons:
- Three PR creations + reviews = slightly more wall-clock

### Option B — single bundled PR

All 3 changes in one PR. Faster wall-clock; harder review.

Pros:
- Single review event
- Atomic landing of v3 verdict + Constitution + synthesis

Cons:
- Constitution amendment buried in larger PR
- Harder to revert constitutional change if regretted

**Recommendation**: Option A (3 separate PRs in sequence). Constitution amendments deserve standalone PR review per Constitution VI v1.4.1 "Spec ships its retrospective" principle (analogously, "Constitution amendment ships its empirical basis").

## Cross-references

- **PR #135** — original v3 ANALYSIS_TEMPLATE.md (skeleton)
- **PR #144** — Constitution v1.5.1 conditional patch drafts (4 verdicts × 1 patch)
- **PR #146** — `scripts/wc_10_underperformance_monitor.py` (smoke test on v3 data)
- **PR #147** — extended v3 ANALYSIS_TEMPLATE.md (computation snippet + 4 verdict prose blocks + monitoring)
- **PR #148** — WC-11 scaffold (sister deferred experiment; not part of v3 landing)
- v1 ANALYSIS.md (the predecessor verdict)
- Spec 009 (`specs/009-wc-10-production-deployment/spec.md`) — branch selection per v3 verdict
- v2 ANALYSIS_TEMPLATE.md (sister template; v2 verdict feeds Spec 009 selection orthogonally)

## Estimated total wall-clock

| Phase | Time |
|---|---|
| Step 1: Verify completion + run snippet | 3 min |
| Landing PR #1: ANALYSIS.md | 15 min |
| Landing PR #2: Constitution v1.5.1 patch | 15 min |
| Landing PR #3: RESEARCH_FINDINGS + ROADMAP | 10 min |
| **Total** | **~43 min** |

vs ~2 hours if all 3 PRs were drafted from scratch without pre-scaffolding. **~60% time reduction** from the 2026-05-08 pre-scaffolding investment (PRs #135 + #144 + #146 + #147 + this).

## Cost

$0. Codification work only. Constitution III T0.

## v2 LANDING outlook

When v2 lands (~9h after v3), an analogous landing series applies:

- Landing PR for v2 ANALYSIS.md (uses PR #135 v2 template)
- Spec 009 Branch A/B/C/D activation PR (uses PR #140 conditional draft) — selects branch based on v2 SC-005(b) verdict
- RESEARCH_FINDINGS + ROADMAP cross-ref update PR

The v2 landing series is NOT pre-scaffolded to the same density (v2 template at PR #135 is base-tier; no extension PR analogous to #147). Pre-scaffolding investment for v2 deferred to when v2 nears completion (~9h is far enough that re-prioritization is worth doing then).
