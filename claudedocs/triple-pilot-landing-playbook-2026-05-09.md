# Triple-pilot landing playbook — 2026-05-09 (BR-3 + WC-11 + v2)

> **STATUS**: PRE-LANDING TEMPLATE for THREE simultaneous in-flight pilots. v2 lands ~5h, BR-3 + WC-11 land ~3h each. Each lands independently; this playbook coordinates the three landing series + handles cross-pilot interactions.

**Trigger**: reasoning_decision rank #1 (0.775 score). Specializes the generic pilot landing template (PR #170) to the unprecedented 3-pilot simultaneous landing scenario.

**Sister playbooks**:
- PR #149 — v3 landing (3-PR series, ~40 min, COMPLETE)
- PR #161 — v2 landing (4-PR series, projected ~75 min)
- PR #170 — generic landing template

---

## Why this playbook is needed

Three simultaneous pilots is unprecedented for the project. Each pilot has its own:
- Cohort (different tickers / dates / mechanism)
- Verdict matrix (different N branches per HYPOTHESIS)
- Downstream artifacts (different Constitution implications + spec changes)

Without coordination, the 3 landings could:
1. Step on each other (e.g., 2 PRs racing to update RESEARCH_FINDINGS.md → merge conflicts)
2. Produce inconsistent narratives (Constitution v1.5.1 caveat scope evolving as each lands)
3. Burn operator review capacity (3 × 4-PR series = 12 PRs landing in a ~2h window)

This playbook prevents those failure modes via:
1. **Landing order recommendation** (BR-3 / WC-11 first; v2 last)
2. **Cross-pilot RESEARCH_FINDINGS / ROADMAP coordination** (single update per landing, not 3)
3. **Day-end synthesis option** (bundle all 3 verdicts into one wrap-up doc)

---

## Pilot status snapshot

| Pilot | Cohort | ETA | Pre-scaffolded | Cost | Monitor |
|---|---|---|---|---|---|
| **BR-3 Squeak** | NVDA + AAPL × 5 dates × 2 modes (prose/structured) | ~3h | ANALYSIS_TEMPLATE only (PR #157) | $8 | `bklbkngsj` |
| **WC-11 order randomization** | NVDA × 5 dates × 4 permutations | ~3h | HYPOTHESIS + PARAMS only (PR #148) | $8 | `bsjh07xep` |
| **v2 expansion** | 8 tickers × 10 dates × WC-10 only | ~5h | Full landing playbook (PR #149/#161/#147 + Spec 009 5/7) | $32 | `b4v66551r` |

## Landing order recommendation

**Order**: BR-3 + WC-11 land roughly simultaneously (~3h); execute their landing PRs in either order (no dependency between them). v2 lands later (~5h); its landing series is the most complex (4 PRs + Spec 009 branch selection).

**Why this order**:
- BR-3 + WC-11 are independent; their verdicts don't interact
- v2 is the highest-leverage landing (drives Spec 009 Branch A/B/C selection); landing it LAST means the v1+v3 (already merged) + BR-3 + WC-11 verdicts are all in main when v2 ANALYSIS is written
- Each landing's RESEARCH_FINDINGS update can reference the prior verdicts already merged

## Per-pilot landing series

### BR-3 Squeak — 2-PR landing (~30 min)

| PR | Type | Time |
|---|---|---|
| Landing PR #1 | BR-3 ANALYSIS.md + verdict block | ~20 min |
| Landing PR #2 | RESEARCH_FINDINGS + ROADMAP cross-ref | ~10 min |

**Possible verdicts**:
- **NULL**: structured = pure cost win; consider extending to other analysts (BR-3 v2 sister scaffold)
- **ALT-A**: prose carries signal; do NOT structurize; close BR-3 line
- **ALT-B**: structured surfaces signal; OPENS Phase E architectural variant — may warrant new spec scaffold

If verdict is ALT-B, add Landing PR #3: "Phase E spec scaffold for structured-output-throughout architecture (analogous to Spec 009 conditional draft pattern)".

### WC-11 order randomization — 2-PR landing (~30 min)

| PR | Type | Time |
|---|---|---|
| Landing PR #1 | WC-11 ANALYSIS.md + verdict block | ~20 min |
| Landing PR #2 | RESEARCH_FINDINGS + ROADMAP cross-ref | ~10 min |

**Possible verdicts**:
- **NULL**: synthesis order-robust; retire WC-11 as a concern; document in CHANGELOG as "ruled out"
- **ALT-A** (first-speaker bias): EVERY prior corpus claim is confounded by the fixed `[market, news, fundamentals]` order; massive methodology implications. Constitution VII Replicability-scope sub-section needs amendment.
- **ALT-B** (last-speaker recency bias): same implication as ALT-A but for last analyst.

If verdict is ALT-A or ALT-B (NON-null), add Landing PR #3: "Constitution VII Replicability-scope amendment + corpus-wide methodology note".

### v2 expansion — 4-PR landing (~75 min)

Per pre-scaffolded PR #161 v2 landing playbook. No changes needed — playbook is ready.

## Cross-pilot coordination

### RESEARCH_FINDINGS.md update strategy

**Problem**: 3 landings each want to update the WC-10 section / Open Questions table. Naive approach = 3 separate PRs racing to update the same sections → merge conflicts.

**Recommended approach**:
1. BR-3 + WC-11 LANDING PR #2 each updates DIFFERENT sections (BR-3 → WC-10 sister-hypothesis paragraph; WC-11 → Open Questions Tier 1 row)
2. v2 LANDING PR #3 (per PR #161 plan) updates the WC-10 v2 paragraph + closes 4 Open Questions rows

If actual merge conflicts occur (uncommon since sections are disjoint), resolve via standard `git merge --no-edit` after the first PR lands.

### ROADMAP.md update strategy

**Problem**: 3 landings each want to add their verdict to the 2026-05-08/09 PRs section.

**Recommended approach**: SINGLE consolidated ROADMAP update PR that lands AFTER all 3 pilot verdicts are in. Format:

```markdown
**Late 2026-05-08 / early 2026-05-09 — Three-pilot landing convergence**:
- BR-3 Squeak verdict <X>; Landing PRs #<N> + #<N+1>
- WC-11 order randomization verdict <X>; Landing PRs #<M> + #<M+1>
- WC-10 v2 expansion verdict <X>; Landing PRs #<P> through #<P+3>
- Spec 009 Branch <A/B/C> activated per v2 verdict
```

Single ROADMAP PR keeps the project's forward-looking doc consistent.

### Constitution implications matrix

| Pilot | Verdict | Constitution change? |
|---|---|---|
| BR-3 NULL | none | No |
| BR-3 ALT-A | none (confirms prose-as-load-bearing) | No |
| BR-3 ALT-B | NEW Principle? "Structured-output-throughout architecture" | Possible v1.6.0 |
| WC-11 NULL | none | No |
| WC-11 ALT-A or ALT-B | Constitution VII Replicability-scope sub-section AMENDMENT | Possible v1.5.2 |
| v2 STRONG | Possible scope-extension paragraph | v1.5.2? |
| v2 MODERATE | Caveat preserved at v1.5.1 | No |
| v2 NULL | Caveat tightened | v1.5.2? |

**If multiple Constitution amendments are triggered**: land them sequentially per Constitution VI v1.4.1 standalone-amendment discipline. Sequence: WC-11 amendment first (most foundational; affects corpus interpretation), then BR-3 amendment, then v2 amendment.

## Day-end synthesis option

Once all 3 pilots land + their landing PRs are merged, OPTIONALLY write `claudedocs/research-burst-2026-05-08-extended-2026-05-09.md` capturing:
- Full session arc (now spanning 2 calendar days)
- 3-pilot triple-landing convergence (unprecedented)
- Constitution evolution v1.4.6 → v1.5.0 → v1.5.1 → (possibly v1.5.2 → v1.6.0)
- Spec 009 Branch activation
- Memory entry refresh

Per memory `feedback_no_day_rollover_planning.md` — don't pre-write the day-end synthesis until all 3 verdicts are in.

## Estimated total wall-clock

| Phase | Time |
|---|---|
| BR-3 landing (~3h after start) | 30 min |
| WC-11 landing (~3h after start) | 30 min |
| Inter-landing coordination (RESEARCH_FINDINGS sections + check for conflicts) | 15 min |
| v2 landing (~5h after start; per PR #161) | 75 min |
| Consolidated ROADMAP update (post-all-3) | 15 min |
| Day-end synthesis (optional) | 60 min |
| **Total** | **~225 min (~3.75h)** of landing work |

vs ~4-6h total if drafting from scratch without pre-scaffolding (40-50% reduction; lower than v3 + v2 individual reductions because v2 already had max pre-scaffolding).

## Risk assessment

**LOW risks:**
- Each pilot's data is independent — no cross-data contamination
- Landing PRs can land asynchronously per the pilot's actual completion time
- Pre-scaffolding for v2 is comprehensive (PR #149 / #161 / #147)

**MEDIUM risks:**
- Operator review capacity: 12+ PRs landing in a ~2h window may exceed operator merge cadence. Mitigation: pace landing PR creation; let operator merge each before opening the next.
- Constitution amendment sequencing: if WC-11 ALT-A + v2 STRONG both fire, two amendments to ship in order; need to be careful about version numbers
- Three-pilot LLM cost: $48 in flight; v2 alone is over T2 cap (deliberated in HYPOTHESIS)

**HIGH risks:**
- (none identified)

## Pre-landing checklist (do BEFORE any landing)

- [ ] WC-11 needs an ANALYSIS_TEMPLATE.md scaffolded (currently only HYPOTHESIS + PARAMS) — if landing happens before this PR lands, just write ANALYSIS.md from scratch (~25 min vs ~10 min with template)
- [ ] BR-3 ANALYSIS_TEMPLATE.md exists (PR #157) but NOT extended with verdict-conditional blocks — extension would save ~15 min if added before landing
- [ ] v2 ANALYSIS_TEMPLATE.md fully extended (PR #147 covered v3 in detail; PR #135 v2 template is base-tier; could extend if time permits before v2 lands)

## Cross-references

- PR #149 — v3 landing playbook (complete, validated 67% time reduction)
- PR #161 — v2 landing playbook (projected ~75 min)
- PR #170 — generic pilot landing template (parent abstraction)
- PR #157 — BR-3 HYPOTHESIS + ANALYSIS_TEMPLATE (scaffold)
- PR #148 — WC-11 HYPOTHESIS + PARAMS (scaffold)
- PR #156 — Spec 009 plan.md (Branch A/B/C implementation paths)
- PR #161 — v2 landing playbook (governs v2 portion of triple-landing)

## Cost

$0 codification.
