# Memory cleanup audit post-Constitution v1.5.1 — 2026-05-09

**Trigger**: reasoning_decision rank #5 (0.42 score). Reviews ~31 memory entries (`~/.claude/projects/C--Development-Projects-TradingAgents/memory/*.md`) for stale references after Constitution v1.4.6 → v1.5.0 → v1.5.1 evolution + WC-10 v1+v3 verdict landings + Spec 011 + Spec 009 5/7 design surface shipping.

## Audit methodology

Each entry classified as one of:

- **HISTORICAL**: describes what was true at a moment in time. Fine as-is. Future readers understand the snapshot context.
- **ACTIVE-ONGOING (current)**: describes a pattern operators consult AS GUIDANCE. Must reflect current state. May need surgical edits.
- **STALE**: contains references to draft versions (e.g., v1.4.4 was renamed to v1.4.6 at ratification). Surgical edits applied.
- **ALREADY-UPDATED**: prior cleanup pass (PR #142) already added v1.5.0 references; v1.5.1 update is marginal.

## Entries scanned

Total: 31 entries (28 reference + feedback + project; excluding MEMORY.md index).

### Updated (2 entries)

| File | Change |
|---|---|
| `reference_behavioral_additive_4th_interpretation.md` | Description field: "v1.4.4 codification threshold MET" → "codification ratified as Constitution v1.4.6 (originally drafted as v1.4.4; renamed to preserve monotone numbering after v1.4.5 ratified first)". Added: "2026-05-08 Spec 011 (PR #136) codifies operational invocation procedure with 6 FRs. Current Constitution v1.5.1 retains v1.4.6 sub-section unchanged." |
| `reference_pre_rating_temporal_learning.md` | All "v1.4.4" → "v1.4.6 (originally drafted as v1.4.4)" via replace_all. Preserves historical context while pointing to ratified version. |

### Already-updated by PR #142 (2 entries; v1.5.0 references present)

| File | Status |
|---|---|
| `reference_pm_hold_regime_starves_filters.md` | Has 2026-05-08 Constitution v1.5.0 update note. Could add v1.5.1 note but marginal — the v1.5.0 update is structurally accurate (TWO-MECHANISM is the load-bearing reframe; v1.5.1 just bounds the bear-regime caveat). |
| `reference_pm_hold_with_bullish_prose.md` | Same. v1.5.0 update note present; v1.5.1 update is marginal. |

### Reviewed and KEPT as-is — historical snapshots (rest of the entries)

- `feedback_*` entries (10): operator preference patterns; no Constitution-version dependency
- `project_2026-05-06_research_burst.md` + `project_2026-05-07_record_day.md`: HISTORICAL day-arc records; correctly snapshot the state at their respective dates
- `project_2026-05-08_record_day.md`: refreshed today; current
- `project_2026-05-08_queue_exhaustion_pattern.md`: HISTORICAL morning-session pattern record
- `reference_bear_side_mechanism_survey_complete.md`: 6/6 evaluation snapshot is HISTORICAL; survey concluded 2026-05-07
- `reference_conditional_branch_spec_pattern.md`: NEW today (PR #151); current
- `reference_llm_client_kwargs_dict_invariance.md`: NEW today (PR #128 lesson); current
- `reference_memory_log_reflection_hallucination.md`: refreshed in PR #142 with 4/18 = 22% sweep
- `reference_pass_by_non_counterexample.md`: HISTORICAL PR #56 finding; v1.4.4 reference is in context of PR #44 historical work, not active guidance
- `reference_pytest_cov_collection_error_undercounts_coverage.md`: HISTORICAL PR #116 lesson; methodology unchanged
- `reference_sc009_ablation_pattern.md`: HISTORICAL ablation pattern from 2026-05-07
- `reference_schema_mutation_needs_prompt_and_consumer_review.md`: WC-10 PR #110-#114 lesson; current
- `reference_signals_cache_pk_collision.md`: PR #72 footgun documentation; current
- `reference_spec_003_cold_start_coverage.md`: PR #68 coverage gap documentation; current
- `reference_speckit_6pr_workflow_pattern.md`: Spec X-1 deployment lessons; current pattern still holds
- `reference_speckit_numbering.md`: numbering convention; current

## Observations

1. **Historical-record entries dominate**: 24 of 31 entries are point-in-time snapshots that correctly preserve the state at their date. Cleanup is mostly inappropriate for these (would erase historical context).

2. **Active-guidance entries with v1.5.0 cross-references already exist**: 2 entries (pm_hold pair) were updated in PR #142's earlier cleanup pass and don't need v1.5.1-specific updates because v1.5.1 is a magnitude-bound to v1.5.0's structural carve-out (the substantive reframe is in v1.5.0).

3. **Stale references in description fields**: 2 entries had stale "v1.4.4" references (v1.4.4 was the draft number; ratified version was v1.4.6). Updated surgically.

4. **No deletions warranted**: every entry tracked something useful; no obvious duplicates or contradictions surfaced.

## Future cleanup triggers

Memory cleanup pass should be triggered by:
- Constitution amendment that REPLACES (not refines) a prior principle (e.g., a v2.0.0 release would warrant full review)
- Spec deprecation that retires a tooling reference cited across multiple memory entries
- Methodology shift that contradicts a feedback pattern (e.g., if "pre-scaffolding" stops winning consistently, the methodology doc + memory references need updating)

The current cleanup pass (this PR) cleared 2 stale draft-version references but found no other cleanup work warranting churn. **Memory hygiene is stable post-v1.5.1.**

## Cost

$0 codification.

## Cross-references

- PR #142 — earlier memory cleanup pass (added v1.5.0 references)
- PR #167 — cross-pollination L4 progress check (notes 28 → 32 entries during today's session)
- PR #173 + PR #167 + PR #163 — recent memory entries that don't need updates (already current)
