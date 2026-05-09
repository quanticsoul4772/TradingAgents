# Memory cleanup audit post-Constitution v1.5.2 + WC-10 research arc CLOSED — 2026-05-09

**Trigger**: reasoning_decision rank #1E (0.805 score). Reviews ~33 memory entries (`~/.claude/projects/C--Development-Projects-TradingAgents/memory/*.md`) for stale references after today's closing of the WC-10 research arc + Spec 009 Branch C activation + Constitution v1.5.1 → v1.5.2 amendment.

**Predecessor**: `claudedocs/memory-cleanup-audit-post-v1.5.1-2026-05-09.md` (PR #142; ran post-v1.5.1, produced 2 surgical edits).

## Audit methodology

Each entry classified as one of:

- **HISTORICAL**: describes what was true at a moment in time. Fine as-is; future readers understand the snapshot context.
- **ACTIVE-ONGOING (current)**: describes a pattern operators consult AS GUIDANCE. Must reflect current state. May need surgical edits.
- **STALE**: contains references to in-flight work that has now landed. Surgical edits applied.
- **ALREADY-CURRENT**: prior cleanup pass (PR #142) or sister memory shipping already brought it up-to-date.

## Entries scanned

Total: 33 entries (28 prior + 2 added 2026-05-09 via WC-11 + BR-3 sister memories + 3 added across 2026-05-08 record day session). MEMORY.md index up-to-date with all entries.

### Updated this pass (3 entries)

| File | Change |
|---|---|
| `project_2026-05-08_record_day.md` (frontmatter) | Name field: "TRIPLE-PILOT IN FLIGHT" → "triple-pilot launched (v2/BR-3/WC-11 — landed 2026-05-09 per #179-#187)". Description field: "v2 + BR-3 + WC-11 in flight" → "triple-pilot launched ... landed 2026-05-09 per PRs #179-#187 + project_2026-05-09 record entry". Body unchanged (correctly snapshots 2026-05-08 end-of-session state). |
| `reference_pm_hold_regime_starves_filters.md` (body) | Added "Update 2026-05-09 (post-WC-10 v2 + Spec 009 Branch C)" paragraph documenting the 5/8 + 3/8 sub-population split + JNJ-class as defensive-sector retention case + Spec 009 Branch C as operational tool for sub-population (b). Added a second "Update 2026-05-09 (post-WC-11 + Constitution v1.5.2)" paragraph noting analyst-order as 3rd-axis design variable. |
| `MEMORY.md` (index line) | 2026-05-08 record day index line: condensed body + replaced "Three pilots in flight at end-of-session" with "triple-pilot launched (v2/BR-3/WC-11) at end of session — landed 2026-05-09 per PRs #179-#187". Reduces stale-impression risk for future readers of the index. |

### Already-current — no edits needed (5 entries from today's session)

| File | Status |
|---|---|
| `reference_wc11_analyst_order_first_speaker_bias.md` | Shipped today (PR #180-aux). Current. |
| `reference_br3_analyst_stage_structured_partial.md` | Shipped today (PR #180-aux). Current. |
| `reference_pm_hold_with_bullish_prose.md` | Has 2026-05-08 v1.5.0 update note. v1.5.2 + v2 update is marginal — the core mechanism (PM rating-vs-prose split) is unchanged by today's findings. Leave as-is. |
| `reference_behavioral_additive_4th_interpretation.md` | Updated in PR #142 cleanup pass to reference v1.4.6 ratification. v1.5.2 doesn't affect this entry's content. |
| `reference_pre_rating_temporal_learning.md` | Updated in PR #142 cleanup pass. v1.5.2 doesn't affect this entry. |

### Reviewed and KEPT as-is — historical snapshots (rest)

- `feedback_*` entries (12): operator preference patterns; no Constitution-version dependency
- `project_2026-05-06_research_burst.md` + `project_2026-05-07_record_day.md`: HISTORICAL day-arc records; correctly snapshot the state at their respective dates
- `project_2026-05-08_queue_exhaustion_pattern.md`: HISTORICAL morning-session pattern record
- `reference_bear_side_mechanism_survey_complete.md`: 6/6 evaluation snapshot is HISTORICAL; survey concluded 2026-05-07
- `reference_conditional_branch_spec_pattern.md`: shipped 2026-05-08; current
- `reference_llm_client_kwargs_dict_invariance.md`: shipped 2026-05-08; current
- `reference_memory_log_reflection_hallucination.md`: refreshed in PR #142 with 4/18 = 22% sweep
- `reference_pass_by_non_counterexample.md`: HISTORICAL PR #56 finding
- `reference_pytest_cov_collection_error_undercounts_coverage.md`: HISTORICAL PR #116 lesson; methodology unchanged
- `reference_sc009_ablation_pattern.md`: HISTORICAL ablation pattern from 2026-05-07
- `reference_schema_mutation_needs_prompt_and_consumer_review.md`: WC-10 PR #110-#114 lesson; current
- `reference_signals_cache_pk_collision.md`: PR #72 footgun documentation; current
- `reference_spec_003_cold_start_coverage.md`: PR #68 coverage gap documentation; current
- `reference_speckit_6pr_workflow_pattern.md`: Spec X-1 deployment lessons; current
- `reference_speckit_numbering.md`: numbering convention; current

## Observations

1. **Cleanup remains LOW-CHURN per pass**: PR #142 cleanup made 2 edits; today's pass makes 3 edits. The memory system is structurally stable — most entries are correctly historical snapshots that don't need ongoing maintenance.

2. **Stale-impression risk concentrated in day-arc records**: the 2026-05-08 record entry's "TRIPLE-PILOT IN FLIGHT" framing was the highest stale-impression risk for future readers (could mislead on whether pilots are still running). Surgical fix preserves historical accuracy of the body while updating the frontmatter + index line to flag the resolution.

3. **WC-10 sub-population split now empirically anchored**: the `reference_pm_hold_regime_starves_filters.md` 2-paragraph update connects v2's per-ticker findings (5/8 ALT-A + 3/8 retain Hold-default) to operational ablation design. The defensive-sector vs Tech distinction is now memory-anchored as a design heuristic.

4. **Index line condensation**: the 2026-05-08 index line was 1098 chars (well over the ~150-char guideline). Condensed to ~565 chars while preserving the structural information operators consult.

5. **Open: 2026-05-09 day-arc record entry not yet shipped** — option M from today's reasoning_decision queue (rank-7 tied at 0.735). If shipped, the 2026-05-08 entry's index can be tightened further to defer to the 05-09 entry for the post-arc state.

## Future cleanup triggers

Memory cleanup pass should be triggered by:

- Constitution amendment that REPLACES (not refines) a prior principle — e.g., a v2.0.0 release would warrant full review
- Closing of a multi-PR research arc — today's WC-10 arc closure triggered this pass
- Day-arc record entry shipping (the new entry's content may obsolete or extend prior entries)
- Methodology shift that contradicts a feedback pattern — e.g., if "pre-scaffolding" stops winning consistently

The current cleanup pass cleared the WC-10-arc-closure-related stale references. **Memory hygiene remains stable post-v1.5.2 + Spec 009 Branch C.**

## Cost

$0 codification.

## Cross-references

- PR #142 — earlier post-v1.5.1 cleanup pass
- WC-11 + BR-3 sister memories (PR #180-aux 2026-05-09)
- Today's day-end synthesis: `claudedocs/research-burst-2026-05-09.md` (PR #185)
- Bundled doc refresh: README + CHANGELOG + CLAUDE.md (PR #187)
- Memory entries with WC-10 + WC-11 cross-references: `reference_wc11_analyst_order_first_speaker_bias.md` + `reference_br3_analyst_stage_structured_partial.md` + `reference_pm_hold_regime_starves_filters.md` (post-update) + `reference_pm_hold_with_bullish_prose.md`
