# Pilot landing PR series template

> **STATUS**: REUSABLE TEMPLATE. When a pilot experiment is in flight + about to land, copy this template + customize per the pilot's specifics. Sister to `.specify/templates/spec-template-conditional.md` (PR #151) which extracts the conditional-branch spec pattern.

**Pattern source**: PR #149 (v3 landing playbook) + PR #161 (v2 landing playbook). Both validated 60-67% wall-clock reduction vs draft-from-scratch. This template generalizes the pattern for any future N-pilot experiment landing.

---

## When to use this template

Use this template when ALL of the following hold:

1. A pilot experiment (with HYPOTHESIS + PARAMS scaffolded) is in flight or expected to land soon
2. The verdict will trigger a sequence of follow-up PRs (typically: ANALYSIS → Constitution amendment → spec scaffolding → docs update)
3. Wall-clock cost of post-verdict draft is large enough (~1+ hour) to justify pre-scaffolding investment

When NOT to use:
- Pilot is small enough that landing is < 30 min from scratch (don't pre-scaffold, just execute)
- Pilot's verdict has only one possible follow-up (no branch selection needed)
- Pilot is too speculative; structure of follow-ups is genuinely unknown

---

## Template structure (customize for each pilot)

### Section header

```markdown
# <Pilot Name> landing PR series bundle template — <YYYY-MM-DD>

> **STATUS**: PRE-LANDING TEMPLATE. <Pilot> data lands soon (~<ETA> ETA from <pre-scaffolding draft time>). When it does, follow the workflow below — all landing PRs land in ~<projected total> total (vs ~<from-scratch baseline> from scratch).

**Trigger**: <reasoning_decision rank or operator directive>. Bundles the pre-scaffolded artifacts (PRs #X #Y #Z) into a single landing playbook.
```

### Section 1: Why this pilot's landing is N PRs

Document why the pilot's landing series is the size it is. Common shapes:
- **2-PR series**: simple verdict → ANALYSIS + RESEARCH_FINDINGS update
- **3-PR series** (v3 pattern, PR #149): ANALYSIS + Constitution amendment + RESEARCH_FINDINGS
- **4-PR series** (v2 pattern, PR #161): ANALYSIS + spec tasks + RESEARCH_FINDINGS + ROADMAP/day-end synthesis
- **5+-PR series**: rare; usually decomposes into multiple smaller landing series

### Section 2: The N-PR landing series table

```markdown
| PR | Type | Estimated time | Pre-scaffolded by |
|---|---|---|---|
| Landing PR #1 — <pilot> ANALYSIS.md | research | ~X min | PR #<analysis-template-PR> |
| Landing PR #2 — <Constitution amendment | spec tasks.md | ...> | <type> | ~X min | PR #<patch-drafts-PR> |
| Landing PR #3 — RESEARCH_FINDINGS.md update | synthesis | ~X min | template (this doc) |
| ...add rows as needed... |
```

Total: **~Y min wall-clock** vs ~Z hours from scratch.

### Section 3: Workflow (copy-paste ready)

For each step, include:
- **Step heading** (verify completion / open Landing PR #N)
- **`bash` block** with branch creation + commands
- **Numbered substeps**: 1. copy template, 2. populate placeholders, 3. compute metrics, 4. commit, 5. push, 6. open PR

Example (from v3 playbook):

```markdown
### Step 2: Open Landing PR #1 — <pilot> ANALYSIS.md (X min)

bash:
git checkout main && git pull origin main
git checkout -b <NNN>-<pilot>-analysis-landing

Then:

1. Copy `experiments/<pilot-dir>/ANALYSIS_TEMPLATE.md` → `ANALYSIS.md`
2. Run computation snippet from Section A; populate <TBD> placeholders
3. Pick verdict per the verdict matrix (Section B); fill verdict prose
4. Run monitoring smoke-test (if applicable); paste output as Section C addendum
5. Update Constitution adherence checklist + Next-steps section
6. git add + commit + gh pr create
```

### Section A: Ready-to-run computation snippet

Pre-write the exact Python snippet operators run after `results.csv` is complete. Output should:
- Load the pilot data
- Compute the headline metrics (correlation / hit rate / α delta / etc.)
- Print the verdict line (which selects the matching verdict block)
- Cite the matching Constitution patch / spec branch / etc.

### Section B: Verdict-conditional analysis blocks

Pre-write N prose blocks, one per possible verdict. Each block:
- Has a trigger criterion (computed from Section A snippet output)
- Has placeholder `<FILL: X>` markers for computed values
- References the matching Constitution patch (per PR #144 pattern) + Spec branch (per PR #156 plan.md pattern)
- States operational implication (what production-deployment changes per this verdict)

When the verdict lands, the operator KEEPS the matching block + DELETES the others.

### Section C: Monitoring loop integration (if applicable)

If the pilot has a runtime monitor (e.g., `wc_10_underperformance_monitor.py` per PR #146), document:
- Smoke-test command for the pilot's data
- Expected output structure
- Alert criteria interpretation
- Cron-wiring guidance for production

### Section D: RESEARCH_FINDINGS.md update template

Pre-written verdict-conditional sentences for the project synthesis doc:
- Headline section paragraph (per verdict)
- Open Questions table row replacements (mark "in flight" rows as "RESOLVED")

### Section E: ROADMAP.md update template

Append-to-active-section block with:
- Landing PR numbers
- Verdict summary
- Next-action cross-references

Optional: day-end synthesis paragraph in `claudedocs/research-burst-<YYYY-MM-DD>.md`.

### Section F: Bundling decision

Document Option A (separate PRs per landing step) vs Option B (single bundled PR):
- **Option A** preferred for amendments / spec changes (Constitution VI v1.4.1 standalone-amendment discipline)
- **Option B** acceptable for trivial single-file ANALYSIS landings

### Section G: Cross-references

List ALL related PRs:
- The pilot's HYPOTHESIS PR
- The ANALYSIS_TEMPLATE.md PR (per PR #135 pattern)
- The Constitution patch drafts PR (if applicable; per PR #144 pattern)
- The monitoring tooling PR (if applicable; per PR #146 pattern)
- The spec scaffolding PRs (if applicable)

### Section H: Estimated total wall-clock

Tabular breakdown:

```markdown
| Phase | Time |
|---|---|
| Step 1: Verify completion + computation snippet | X min |
| Landing PR #1: <name> | X min |
| Landing PR #2: <name> | X min |
| ...add as needed... |
| **Total** | **~Y min** |
```

Plus the from-scratch baseline (so operators see the time-savings).

### Section I: Cost

$0 codification (the pre-scaffolding is documentation; the actual landing PRs are codification + small follow-up work).

---

## Customization checklist (when copying this template)

When adapting this template for a new pilot landing playbook:

- [ ] Replace `<Pilot Name>` with the actual pilot name (e.g., "v2", "v3", "BR-3 Squeak")
- [ ] Replace `<YYYY-MM-DD>` with actual draft date
- [ ] Set ETA + pre-scaffolding draft time
- [ ] Number the PR series (typically 2-4 PRs per landing)
- [ ] Customize Section A computation snippet to the pilot's data shape
- [ ] Pre-write Section B verdict blocks (N blocks per verdict matrix)
- [ ] Cross-reference the pilot's existing pre-scaffolded artifacts in Section G
- [ ] Estimate Section H times honestly (don't over-promise)

## Empirical ROI evidence

| Pilot | From-scratch baseline | Pre-scaffolded actual | Reduction |
|---|---|---|---|
| v3 (PR #149 playbook) | ~120 min | ~40 min | **67%** |
| v2 (PR #161 playbook; projection) | ~180-240 min | ~75 min | ~60% |
| BR-3 (PR #157 ANALYSIS template only) | TBD | TBD | TBD when landed |

Pre-scaffolding cost: ~30-60 min per playbook draft. Pays back on the first landing.

## When NOT to extract a per-pilot playbook

If the pilot's landing series is genuinely 1 PR (just ANALYSIS.md + minor cross-reference updates), no playbook is needed. Just run the post-verdict workflow directly. The pre-scaffolded ANALYSIS_TEMPLATE.md (per PR #135 + the `--with-analysis-template` flag from PR #150) is the minimum scaffolding for any pilot.

## Sister templates + tooling

- `.specify/templates/spec-template-conditional.md` (PR #151) — verdict-conditional spec template
- `scripts/new_experiment.py --with-analysis-template` (PR #150) — auto-scaffolds ANALYSIS_TEMPLATE.md
- `claudedocs/v3-landing-pr-series-bundle-template-2026-05-08.md` (PR #149) — concrete instance for v3 (3-PR series)
- `claudedocs/v2-landing-pr-series-bundle-template-2026-05-08.md` (PR #161) — concrete instance for v2 (4-PR series)
- Memory `reference_conditional_branch_spec_pattern.md` (PR #151) — codifies the conditional-branch pattern

## Cross-references

- Memory `feedback_reasoning_decision_lead_with_list.md` — output discipline when invoking the pattern
- Memory `feedback_no_pick_prompts.md` — execute, don't ask
- Constitution VI v1.4.1 (Spec ships its retrospective + verdict) — sister discipline at the spec level
