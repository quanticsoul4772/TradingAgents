# Hypothesis: spec 003 SC-001 shadow-smoke

**Experiment ID**: `2026-05-05-001-spec003-sc001-shadow-smoke`
**Created**: 2026-05-05
**Source idea**: Spec 003 SC-001 validation — single shadow-mode propagate to confirm the contrarian gate emits annotation + does not modify the rating
**Cost estimate**: ~$0.40 (1 NVDA propagation, Opus + Haiku, 3 analysts, 1 debate round)
**Cost tier**: T1 (free exploration, $0 – $5)

## What we're testing

End-to-end validation of the spec 003 contrarian gate (commit `f238f3a`) in **shadow mode**. The gate has 30 unit tests with mocked cache, but ZERO live-propagate smoke tests.

This experiment is the smoke test: one full propagation with `contrarian_gate_mode = "shadow"` to verify:

1. **Gate annotation appears in `state["contrarian_gate"]`** with all expected keys (mode, signal_id, feature, threshold, target, feature_value, percentile, n_history, would_fire, gate_skipped, gate_fired, pm_rating_pre_gate, pm_rating_post_gate)
2. **Gate is NOT skipped** — NVDA has 33 cached market_report rows (above the N=20 floor); annotation should have non-None feature_value, percentile, n_history, would_fire
3. **Shadow mode does NOT modify the rating** — `pm_rating_pre_gate == pm_rating_post_gate` and `gate_fired == False`
4. **Final decision text is unchanged** — no `[Spec 003 contrarian gate]` annotation block appended (that block is active-mode-only)
5. **Run completes without errors**

NVDA on 2026-01-30 (same date used by experiments 005, 007, 2026-05-04-007 — known-working config).

## Note on byte-identical-vs-baseline (spec SC-001 wording)

Spec SC-001 reads "byte-identical to a no-gate baseline run." Strict cross-run byte-identicality is fragile because Anthropic LLM calls aren't fully deterministic across separate API requests even with the same input. This smoke test instead validates byte-identicality **by-construction**: in shadow mode, `ContrarianGate.maybe_override_decision` returns `(decision_markdown, False)` unchanged when `mode != "active"`. The unit tests already cover this code path; this live test confirms the wiring doesn't somehow modify the markdown elsewhere.

If a strict cross-run comparison is needed in the future, it would require running the same propagate twice (off + shadow) on the same date and accepting that any difference is LLM stochasticity, not gate behavior.

## Why we expect a clean smoke test

- Spec 003 implementation has 30 unit tests passing including:
  - `test_shadow_mode_never_overrides` — explicitly asserts `(modified == decision, fired == False)`
  - `test_per_ticker_baseline_uses_only_target_ticker` — confirms cache is queried by ticker
  - `test_insufficient_history_skipped` — N<20 → skipped
- NVDA cache has 33 rows (well above floor)
- Default config preserves backwards-compat (mode="off"); we explicitly enable shadow

## Predicted findings

**Scenario A (clean smoke, all 5 validations pass)** — ~85%
- Run completes 1/1 with 0 errors
- State log contains `contrarian_gate` block with non-null fields
- pre_rating == post_rating, gate_fired == False
- Final decision text contains no Spec 003 annotation
- would_fire is True or False depending on whether NVDA 2026-01-30's market_report has high bull_keyword_count vs the prior 20 NVDA dates

**Scenario B (gate skipped: insufficient_history)** — ~5%
- Cache might have fewer than 20 market_report rows for NVDA after some cache event (unlikely; verified 33 rows present pre-run)
- Annotation present, but `gate_skipped == "insufficient_history"`, percentile=None
- Validates skip path; not a failure

**Scenario C (gate skipped: missing_source_signal)** — ~3%
- Featurizer threw an exception
- Should not happen; bull_keyword_count is robust

**Scenario D (state log missing contrarian_gate block)** — ~5%
- Wiring in PM didn't propagate the block to state
- Would require investigation: is contrarian_gate getting stripped by LangGraph's state merging?

**Scenario E (unexpected break)** — ~2%
- Some integration issue with the gate's PM hook
- Fix the bug, re-run

## Success criterion

- [ ] 1 propagation completes with 0 errors
- [ ] `final_state["contrarian_gate"]` is present and non-None
- [ ] `contrarian_gate.gate_skipped` is None (gate ran, did not skip)
- [ ] `contrarian_gate.feature_value` is a number (not None)
- [ ] `contrarian_gate.percentile` is in [0, 100]
- [ ] `contrarian_gate.n_history` >= 20
- [ ] `contrarian_gate.gate_fired` == False (shadow mode, no override)
- [ ] `contrarian_gate.pm_rating_pre_gate` == `contrarian_gate.pm_rating_post_gate`
- [ ] Final decision text contains no `[Spec 003 contrarian gate]` annotation
- [ ] Total cost ≤ $1

## Notes

- **T1 tier** ($0.40 estimated, well within ≤$5 ceiling)
- **Single date single ticker** (NVDA 2026-01-30) — minimum viable smoke
- **Config**: `contrarian_gate_mode = "shadow"` override + standard 005/007 config (Opus deep + Haiku quick + Anthropic + exa news + 3 analysts + 1 debate round)
- **No `anthropic_effort`** — explicitly omitted (Sonnet/Haiku reject it; conservative default for the smoke)
- **Memory log routed to experiment dir** — keeps main memory log clean
- **Existing baseline runs of NVDA 2026-01-30** (commits b234f10, the Phase 4 smoke; 2026-05-04-007 results) all produced rating "Overweight" — useful comparison point even if not strict byte-identicality

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (clean smoke) | Spec 003 Phase 1 declared end-to-end-validated. RESEARCH_FINDINGS updated. SC-001 box checked. Spec 003 SC-002 (N≥30 shadow) and SC-003 (active grid) become next candidates. |
| Scenario B (insufficient_history skip) | Validates the skip path. If unexpected (we have 33 NVDA rows), investigate the cache query. |
| Scenario C (featurizer error) | Bug in featurizer; fix and re-run. |
| Scenario D (block missing from state log) | LangGraph state-merging issue; investigate AgentState schema or PM return-dict pattern. Likely needs declaring `contrarian_gate` in AgentState. |
| Scenario E (unexpected break) | Fix the bug; re-run. |

## Related work

- **Spec 003 spec.md**: User Story 1 (Priority P1), SC-001
- **Spec 003 plan.md**: Phase 1 sequencing
- **Commit `f238f3a`**: Spec 003 Phase 1 + 2 implementation
- **Constitution Principle VII**: shadow mode does not change calibration; gate's annotation is observation-only
