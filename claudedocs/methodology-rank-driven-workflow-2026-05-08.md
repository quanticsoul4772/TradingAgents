# Methodology: rank-driven continuous-shipping workflow — 2026-05-08

**Trigger**: reasoning_decision rank #7 (0.575 score). Codifies the workflow pattern that drove today's 47-PR session (#117-#163).

**Sister documents**:
- Memory `project_2026-05-08_record_day.md` — narrative day-arc summary
- Memory `project_2026-05-08_queue_exhaustion_pattern.md` — earlier-session pattern (PRs #97-#103)
- Memory `project_2026-05-07_record_day.md` — prior 95+ PR session
- Memory `feedback_reasoning_decision_lead_with_list.md` — reasoning_decision output discipline
- Memory `feedback_no_pick_prompts.md` — execute, don't ask
- Memory `feedback_no_stop_recommendation.md` — keep forward motion

## The pattern

Continuous shipping cadence driven by `reasoning_decision` ranking + user "merged → next ranked option" signals. Each cycle:

1. Operator merges last PR
2. Operator either gives explicit next directive OR invokes `reasoning_decision`
3. Assistant ranks open candidates by leverage / cost / urgency / time
4. Assistant executes rank #1 (or operator-selected option)
5. Assistant ships PR
6. Repeat

## What ranks consistently win

Across ~10+ reasoning_decision invocations today:

| Pattern | Win frequency | Typical score | Example PRs |
|---|---|---|---|
| **Pre-scaffolding for in-flight work** | 5+ rank-#1 wins | 0.71-0.82 | #135 (templates), #140 (Spec 009 conditional), #144 (Constitution patches), #147 (extended template), #149 (landing playbook), #161 (v2 landing), #156 (plan.md) |
| **Codification of recent findings** | 4 rank-#1 / #2 wins | 0.65-0.84 | #131 (Constitution v1.5.0), #132 (RESEARCH_FINDINGS), #136 (Spec 011), #154 (Constitution v1.5.1) |
| **Reusable-tooling extraction** | 2 rank-#2 wins (tied) | 0.735 | #150 (--with-analysis-template), #151 (conditional spec template) |
| **Doc refresh post-event** | 2 rank-#3 / #4 wins | 0.6-0.73 | #137 (ROADMAP), #160 (CLAUDE.md), #162 (CLAUDE.md again) |
| **Empirical-extension via saved data** | 1 rank-#6 win | 0.34-0.63 | #163 (EH-4 historical Hold attribution) |

## What ranks consistently lose

| Pattern | Typical score | Reason |
|---|---|---|
| Memory file cleanup | 0.36-0.47 | Low leverage; existing entries usually still accurate |
| Methodology / synthesis docs | 0.46-0.575 | Important but not blocking; can wait |
| scripts/ mypy cleanup | 0.30-0.33 | Out of CLAUDE.md scope; ROI unclear |

## Why pre-scaffolding wins so consistently

The downstream choice's STRUCTURE is knowable in advance even when the verdict is not. Drafting under cognitive load (post-verdict, late session) produces lower-quality output than drafting in advance. The post-verdict edit becomes deterministic pick + plug-in numbers vs draft-from-scratch.

**Empirical ROI** (from PR #149 + PR #161):
- v3 landing series: ~40 min wall-clock vs ~120 min from scratch (67% reduction)
- v2 landing series (pre-scaffolded): ~75 min projected vs ~180-240 min from scratch (60% projected)

The pattern is now project-level reusable infrastructure (PR #150 + #151) so future experiments inherit it.

## When to invoke reasoning_decision

GOOD timing:
- Rank queue from prior decision is exhausted
- New empirical evidence has shifted priorities (verdict landed, scope finding, etc.)
- After a major arc (3+ related PRs) ships
- When operator explicitly asks "what next?"

BAD timing:
- Mid-task (would interrupt execution)
- When operator has given explicit next directive (skip the ranking)
- When only 1-2 candidates exist (over-engineering)

## Invocation discipline

Per memory `feedback_reasoning_decision_lead_with_list.md`:
- **ALWAYS** lead with the complete ranked-options table
- Never paragraph-summarize ranks
- Execute rank #1 directly (per `feedback_no_pick_prompts.md`)
- Don't ask "should I do X?" — just execute

## Today's arc by phase

### Phase 1 (morning): mypy cleanup sweep (PRs #117-#129)

- 12 cleanup PRs, mypy floor 126 → 0
- Pattern: incremental zero-behavior-risk typing fixes
- Highlight: PR #128 (4-line fix cleared 85 errors that CLAUDE.md previously characterized as "complex / deferred / needs upstream stubs")

### Phase 2 (mid-day): WC-10 v1 ANALYSIS arc (PRs #130-#141)

- v1 pilot ALT-A confirmation (3.6× commit ratio)
- Constitution v1.4.3 → v1.5.0 amendment
- RESEARCH_FINDINGS reframe (TWO-MECHANISM)
- v2 + v3 scaffolds + landing playbook precursors
- Spec 009 conditional draft + Spec 011 procedure
- Dry-run digest renderer

### Phase 3 (afternoon): pre-scaffolding density (PRs #142-#152)

- v3 ANALYSIS extended template + Constitution v1.5.1 patches + landing playbook + reusable templates extracted as project tooling
- Cross-pollination + EXPERIMENT.md backlog reviews
- README + CHANGELOG refresh

### Phase 4 (evening): v3 landing + Spec 009 design surface (PRs #153-#162)

- v3 ANALYSIS landed (PARTIAL ALT-A)
- Constitution v1.5.0 → v1.5.1 (Patch D)
- RESEARCH_FINDINGS integration
- Spec 009 design surface complete (5/7 spec-kit artifacts)
- BR-3 Squeak scaffold (sister hypothesis)
- v2 landing playbook
- CLAUDE.md refreshes

### Phase 5 (late): empirical extension + methodology codification (PRs #163-#164)

- EH-4 historical Hold attribution (Mechanism A vs B scope)
- This methodology doc

## Cumulative metrics

| Metric | Value |
|---|---:|
| Total PRs shipped today | 47 (#117-#163) + this PR |
| Total LLM cost | ~$22.40 ($16 v1 + $6.40 v3; v2 $32 in flight) |
| Constitution amendments ratified | 2 (v1.4.6 → v1.5.0 → v1.5.1) |
| New specs scaffolded | 2 (Spec 009 5-of-7 + Spec 011 single-file) |
| Reusable templates extracted | 2 (--with-analysis-template flag + conditional spec template) |
| Test count | 1146 → 1153 (+7) |
| Mypy floor | 126 → 0 |
| Memory entries created | 3 (#117-... — record-day + LLM client kwargs + conditional-branch pattern) |

## Sustainability characteristics

The rank-driven workflow scales because:

1. **No cognitive overload** — operator just merges + signals next; assistant handles ranking
2. **Cost discipline preserved** — pre-scaffolding + codification are $0; experiments authorized explicitly
3. **Quality maintained** — pre-commit hooks + tests run on every commit; reformat dance is auto-handled
4. **Reusable patterns extracted** — today's frequent-win patterns (pre-scaffolding) became project-level templates
5. **Methodology compounds** — each session's lessons land as memory entries; future sessions inherit

## Anti-patterns observed (and avoided)

| Anti-pattern | Avoided via |
|---|---|
| Mid-task interruption to re-rank | Only invoke reasoning_decision between PRs |
| Paragraph-summarizing ranked options | Memory `feedback_reasoning_decision_lead_with_list.md` |
| Closing with "Pick A/B/C?" | Memory `feedback_no_pick_prompts.md` |
| "Stopping" or "wait for X" framings | Memory `feedback_no_stop_recommendation.md` |
| Future-session planning narratives | Memory `feedback_no_day_rollover_planning.md` |
| Bypassing pre-commit failures | Memory `feedback_precommit_reformat_dance.md` |

## When to STOP the rank-driven cycle

The cycle naturally pauses when:
1. Background experiments are still in flight + no $0 work remains pre-scaffolded
2. Operator explicitly directs other work
3. All rank candidates score below ~0.4 (signals diminishing returns)

Today did NOT hit a natural stop — every cycle had a high-leverage rank #1 candidate. The v2 pilot in flight provides natural background work + serves as the next pivot point.

## Comparison to prior days

| Day | Total PRs | Pattern |
|---|---:|---|
| 2026-05-06 | 17 ship-quality units | research-burst day; spec invocations + retrospectives |
| 2026-05-07 | 95+ PRs | extended record day; spec X-1 deployment + bear-side survey conclusion |
| **2026-05-08 (this)** | **47+ PRs (#117-#163+)** | continuous reasoning_decision-driven shipping; mypy sweep + WC-10 arc |

The rank-driven pattern emerged organically today. It's distinct from:
- 2026-05-06's "spec-first invocation pattern" (constitution-amendment-driven)
- 2026-05-07's "6-PR bundle deployment" (spec-kit-driven)

This methodology is the THIRD identified workflow pattern in the project's history. Each is appropriate for its session character.

## Recommendations for future sessions

1. **Default to reasoning_decision** when between PRs without explicit operator direction
2. **Pre-scaffolding wins** when experiments are in flight (5+ today's wins)
3. **Codification wins** after major findings (Constitution + RESEARCH_FINDINGS updates)
4. **Doc refreshes win** after spec / version changes (CLAUDE.md + README + CHANGELOG)
5. **Reusable tooling extracts win** after patterns are validated 3+ times (PR #150 + #151 precedents)
6. **Don't fight the queue** — execute ranked options sequentially; don't second-guess

## Cross-references

- Memory `project_2026-05-08_record_day.md` — narrative day arc
- Memory `project_2026-05-08_queue_exhaustion_pattern.md` — earlier-session sister pattern
- Memory `project_2026-05-07_record_day.md` + `project_2026-05-06_research_burst.md` — prior record-day comparisons
- Memory `feedback_reasoning_decision_lead_with_list.md` + `feedback_no_pick_prompts.md` — invocation discipline
- PR #149 + PR #161 — pre-scaffolding pattern artifacts (v3 + v2 landing playbooks)
- PR #150 + PR #151 — reusable-tooling extractions (template flag + conditional spec template)
- PR #128 — methodology lesson on verifying "deferred / complex" baseline classifications
