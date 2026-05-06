---

description: "Task list for Sector-Momentum Filter implementation"
---

# Tasks: Sector-Momentum Filter

**Input**: Design documents from `specs/004-sector-momentum-filter/`
**Prerequisites**: spec.md ✓, plan.md ✓, research.md ✓, data-model.md ✓, contracts/ (2) ✓, quickstart.md ✓

**Tests**: Included throughout. Spec requires ≥90% line coverage on new code (SC-007). Integration-marked test for SC-008 empirical-validation gate (XLF down >5% before 2026-04-03 → ≥3 of 5 SC-003 Financials commits suppressed).

**Organization**: Tasks grouped by user story (US1, US2 from spec.md). Within each story, [P] marks parallel-safe tasks (different files, no incomplete dependencies in the same phase).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Single-project Python library extension per `plan.md` Structure Decision:
- Source: `tradingagents/agents/utils/` (new module parallel to A3) + `tradingagents/agents/managers/portfolio_manager.py` wiring
- Config: `tradingagents/default_config.py` (extend `TradingAgentsConfig` TypedDict + `DEFAULT_CONFIG`)
- State persistence: `tradingagents/graph/trading_graph.py:_log_state` whitelist extension
- Tests: `tests/` (flat)
- Scripts: `scripts/sector_momentum_retrospective.py` (new)
- Docs: `CLAUDE.md` (existing)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the config keys + scaffold the new module + extend the state-log whitelist so US1's tests have something to import and the persistence path is in place.

- [X] T001 Add `sector_momentum_filter_mode: Literal["off", "shadow", "active"]`, `sector_momentum_filter_threshold_pct: float | None`, `sector_momentum_filter_lookback_days: int` keys to `TradingAgentsConfig` TypedDict in `tradingagents/default_config.py` (placement next to existing momentum_filter / contrarian_gate keys; defaults `"off"`, `None`, `30` per FR-008/FR-013/R-9)
- [X] T002 Add the same three keys to `DEFAULT_CONFIG` in `tradingagents/default_config.py` with default values + a 5-line comment cross-referencing `specs/004-sector-momentum-filter/spec.md` and explaining (a) the filter is disabled by default per Constitution II ablation discipline, (b) the corpus retrospective gate before any default-on flip
- [X] T003 [P] Create `tradingagents/agents/utils/sector_momentum_filter.py` with module docstring referencing the spec; include `SECTOR_ETF_MAP` constant (11 GICS sectors + variant keys per data-model.md); placeholder `maybe_suppress_bull_rating` function stub returning unmodified decision + off annotation, so US1 tests can import without circular-import issues
- [X] T004 [P] Extend `_log_state` whitelist in `tradingagents/graph/trading_graph.py:425-453` to include `"sector_momentum": final_state.get("sector_momentum")` with a 2-line comment cross-referencing the precedent set by commit `4c14d0f` (which added `contrarian_gate`); per R-5 + FR-009

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the filter function + its supporting infrastructure (annotation builder, ETF history fetcher with LRU cache, sector lookup integration). Both user stories depend on `maybe_suppress_bull_rating` existing.

**⚠️ CRITICAL**: Both user stories depend on the filter function being callable.

- [X] T005 [P] Implement the LRU-cached ETF history fetcher in `tradingagents/agents/utils/sector_momentum_filter.py`: `_etf_history(etf, start, end) -> pd.DataFrame` decorated with `@functools.lru_cache(maxsize=64)` per R-2; thin wrapper around `yf.Ticker(etf).history(start=start, end=end)`; returns empty DataFrame on yfinance failure (caught + warning logged); cache cleared between tests via a dedicated `clear_etf_cache()` helper
- [X] T006 [P] Implement `_compute_etf_30d_return_pct(etf, trade_date, lookback_days) -> float | None` helper in `tradingagents/agents/utils/sector_momentum_filter.py` that fetches the ETF history via `_etf_history` for `trade_date - lookback_days * 1.5 - 7 calendar days` to `trade_date`, then computes the return as `(close[lookback_days] - close[0]) / close[0] * 100`; returns None if the frame has fewer than `lookback_days + 1` rows (insufficient history per R-9)
- [X] T007 Implement `maybe_suppress_bull_rating(decision_markdown, ticker, trade_date, *, threshold_pct, lookback_days, mode, sectors_cache_path, etf_history_fetcher=None, sector_lookup=None) -> tuple[str, dict]` in `tradingagents/agents/utils/sector_momentum_filter.py` per `contracts/filter_function.md`; depends on T005 + T006; flow per data-model.md "State transitions" section: off-mode early return → bullish-only check → threshold validation → sector lookup → ETF mapping → ETF return computation → strict-less-than threshold check → active-mode override (Buy/OW → Hold) with markdown annotation matching A3's pattern from `tradingagents/agents/utils/momentum_filter.py:54-78`; emits annotation dict with all fields per `contracts/annotation_schema.md`
- [X] T008 [P] Create `tests/test_sector_momentum_filter.py` covering all 15 fixtures named in `contracts/filter_function.md`: off-mode, rating-not-bullish, threshold-None/positive, unknown-sector, no-etf-mapping, missing-etf-data, threshold-crossed-active, threshold-crossed-shadow, threshold-not-crossed, strict-less-than-boundary, yfinance-fetch-raises, decision-markdown-no-rating, invalid-mode, lru-cache-amortizes; uses synthetic frames + injected `sector_lookup` callable to avoid live yfinance dependency

**Checkpoint**: Foundation ready. The filter function is fully testable in isolation. User story implementation can begin.

---

## Phase 3: User Story 1 - Sector-rotation bullish miss prevented (Priority: P1) 🎯 MVP

**Goal**: When the PM emits Buy/Overweight on a ticker whose sector ETF is in mean-reversion zone (down >threshold% in prior 30 trading days), the filter downgrades the rating to Hold and emits an annotation describing the suppression.

**Independent Test**: Run a propagate against WFC for a date when XLF was down >5% in the prior 30 trading days (verify with the SC-008 retrospective). With `sector_momentum_filter_mode="active"` + `threshold_pct=-5.0`, verify the persisted state shows `final_trade_decision` as Hold (not Overweight) and `state["sector_momentum"]["fired"] == True`.

### Tests for User Story 1

- [X] T009 [P] [US1] Add `test_filter_disabled_by_default_threshold_none` to `tests/test_portfolio_manager_filter_integration.py`: with `threshold_pct=None` (default), running the PM hook chain on an Overweight rating produces unchanged rating + `state["sector_momentum"]["mode"] == "off"` (or None per implementer's choice); SC-006 byte-identity regression-guard
- [X] T010 [P] [US1] Add `test_filter_active_downgrades_overweight_when_etf_below_threshold` to `tests/test_portfolio_manager_filter_integration.py`: mocked sector lookup returns "Financial Services", mocked ETF fetcher returns XLF frame with -8% prior-30d return, `threshold_pct=-5.0`, `mode="active"`; verify `final_trade_decision` rating downgraded to Hold + `state["sector_momentum"]["fired"] == True` + post_rating == "Hold"; covers US1 acceptance scenario 1
- [X] T011 [P] [US1] Add `test_filter_active_keeps_overweight_when_etf_above_threshold` to `tests/test_portfolio_manager_filter_integration.py`: same setup as T010 but ETF return is -2% (above -5% threshold); verify rating remains Overweight + `would_fire == False`; covers US1 acceptance scenario 2
- [X] T012 [P] [US1] Add `test_filter_does_not_act_on_non_bullish_ratings` to `tests/test_portfolio_manager_filter_integration.py`: same setup with ETF down -8%, but PM rating is Underweight or Hold; verify rating unchanged + `skipped == "rating_not_bullish"`; covers US1 acceptance scenarios 3 + 4
- [X] T013 [P] [US1] Add `test_filter_runs_after_spec_003_in_pm_hook_chain` to `tests/test_portfolio_manager_filter_integration.py`: setup where spec 003 contrarian gate has already downgraded Overweight to Hold; verify the sector-momentum filter sees Hold and emits `skipped == "rating_not_bullish"` (no double-suppression, ordering matters per FR-012)
- [X] T014 [P] [US1] Add `test_state_log_persists_sector_momentum_field` to `tests/test_trading_graph.py`: regression-guard mirroring the precedent set by `test_state_log_persists_contrarian_gate_field` from commit `4c14d0f`; constructs final_state with `"sector_momentum"` populated, calls `_log_state`, asserts the field appears in the persisted JSON
- [X] T015 [P] [US1] Add `test_state_log_sector_momentum_is_none_when_field_absent` to `tests/test_trading_graph.py`: when `sector_momentum` key is absent from final_state (e.g., off-mode early return that returned None), persisted log has `"sector_momentum": null`; mirrors the parallel test for `contrarian_gate`

### Implementation for User Story 1

- [X] T016 [US1] Wire `maybe_suppress_bull_rating` into `tradingagents/agents/managers/portfolio_manager.py` AFTER the existing A3 hook (line 95-103) AND AFTER the existing spec 003 contrarian gate hook (line 154-204), per FR-012 ordering. Pass: `decision_markdown=final_trade_decision`, `ticker=state["company_of_interest"]`, `trade_date=state["trade_date"]`, `threshold_pct=config.get("sector_momentum_filter_threshold_pct")`, `lookback_days=config.get("sector_momentum_filter_lookback_days", 30)`, `mode=config.get("sector_momentum_filter_mode", "off")`, `sectors_cache_path=Path(config.get("paper_state_dir", str(Path.home() / ".tradingagents" / "paper"))) / "sectors.json"`. Wrap in try/except that mirrors the existing spec 003 wrap (per FR-010); merge the returned annotation into the result dict at `result["sector_momentum"] = annotation`. Depends on T007.
- [X] T017 [US1] Update `tradingagents/agents/utils/agent_states.py` AgentState TypedDict to declare `sector_momentum: Annotated[dict, "Spec 004 sector-momentum filter annotation; None when mode=='off'"]` (matches existing `contrarian_gate` TypedDict declaration pattern). Without this declaration, LangGraph silently drops the field from state merges per the existing convention noted in CLAUDE.md.

**Checkpoint**: At this point US1 is functional. Operator can enable the filter via PARAMS.json and observe both shadow + active mode behavior. **MVP delivered.** All US1 acceptance scenarios from spec.md pass.

---

## Phase 4: User Story 2 - Operator distinguishes sector-momentum firings in audit (Priority: P2)

**Goal**: Operator inspecting `state["sector_momentum"]` sees populated dict with all fields documented in `contracts/annotation_schema.md` so they can filter the corpus by `fired` / `would_fire` / `sector` / `etf` for per-filter α attribution.

**Independent Test**: After running a small corpus through the harness with the filter in shadow mode, inspect each `state["sector_momentum"]` annotation; verify the fields are populated correctly per the schema (mode, sector, etf, etf_30d_return_pct, threshold_pct, lookback_days, would_fire, fired, pre_rating, post_rating, skipped).

### Tests for User Story 2

- [X] T018 [P] [US2] Add `test_annotation_active_fires_populates_all_fields` to `tests/test_sector_momentum_filter.py`: mode=active + would_fire=True → all fields populated per `contracts/annotation_schema.md` schema (sector, etf, etf_30d_return_pct, threshold_pct, lookback_days, pre_rating, post_rating, would_fire=True, fired=True, skipped=None); covers US2 acceptance scenario 1
- [X] T019 [P] [US2] Add `test_annotation_shadow_records_would_fire_only` to `tests/test_sector_momentum_filter.py`: mode=shadow + threshold-crossed → would_fire=True + fired=False + post_rating == pre_rating; covers US2 acceptance scenario 2
- [X] T020 [P] [US2] Add `test_annotation_off_returns_none_or_off_skipped` to `tests/test_sector_momentum_filter.py`: mode=off → annotation dict OR None per implementer's choice (both forms documented as valid in contract); covers US2 acceptance scenario 3
- [X] T021 [P] [US2] Add `test_annotation_invariants_per_data_model` to `tests/test_sector_momentum_filter.py`: invariant 1-9 from `data-model.md` "Validation invariants" + `contracts/annotation_schema.md` "Field invariants"; one assert per invariant; covers schema-level audit guarantees
- [X] T022 [P] [US2] Add `test_audit_corpus_filter_by_fired` to `tests/test_sector_momentum_filter.py`: build a list of 6 synthetic annotations (2 fired, 2 would-fire-only, 2 not-fire), verify a Python filter `[a for a in annotations if a["fired"]]` returns the correct subset; matches the corpus-audit pattern in `quickstart.md` Walkthrough 2

### Implementation for User Story 2

- [X] T023 [US2] Verify the annotation builder in `maybe_suppress_bull_rating` (T007) populates ALL fields specified in `contracts/annotation_schema.md` regardless of which path is taken (off / skipped / not-fired / fired). Add explicit field-by-field initialization to a default dict at the function entry; mutate fields as the function progresses; assert all 11 fields are present in the returned dict before returning. This task is a verification-and-tightening pass on T007's existing implementation, not a separate function.
- [X] T024 [US2] Verify the persistence path: state["sector_momentum"] flows through `_log_state` per T004 (whitelist extension) + T014 (regression test). Inspect `tradingagents/graph/trading_graph.py` after T004 to confirm no field-level filtering occurs that would drop sub-fields of the annotation dict; if any filtering exists, extend it. The annotation dict is dumped whole, so all fields ride together — same pattern as `contrarian_gate`.

**Checkpoint**: US1 + US2 both functional. Audit annotation fields are persisted, queryable, and distinguish fired vs would-fire vs skipped firings.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: SC-008 empirical-validation gate, retrospective script for the corpus-wide threshold sweep, CLAUDE.md update, final test/ruff/mypy gate, manual smoke.

- [ ] T025 [P] Create `scripts/sector_momentum_retrospective.py` per R-6 + R-7: walks `experiments/*/results.csv` for bullish (Buy/OW) commits; for each, looks up the ticker's sector + maps to ETF + fetches ETF prior-30-trading-day return + reports per-threshold (`-3, -5, -7.5, -10`) what would have fired, fired α, kept α, net Δα contribution; per-sector breakdown; offline (zero LLM cost). Mirror `scripts/uw_suppression_filter.py` (A3) and `scripts/contrarian_gate_retrospective.py` (spec 003) shape.
- [ ] T026 [P] Add `test_sc003_financials_suppression_at_5pct_threshold` to `tests/test_sector_momentum_filter.py` per R-7: hardcoded SC-003 Financials cohort (JPM/BAC/WFC/GS/MA on 2026-04-03); calls the filter against live yfinance data with threshold=-5.0 + lookback=30; asserts `len(fired) >= 3` per SC-008. Marked `@pytest.mark.integration` so pre-commit's `pytest -m unit` skips it. Skip with clear message if `~/.tradingagents/paper/sectors.json` is missing.
- [ ] T027 [P] Update `CLAUDE.md` "Empirical filters" section to add a 4th bullet for spec 004: name the filter, mention its empirical motivation (SC-003 Financials sector-rotation gap), default-off status, threshold/mode config keys, the `state["sector_momentum"]` annotation field, the SC-008 validation gate. Cross-link the spec dir, `claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md`, and the new retrospective script.
- [ ] T028 Run full `pytest -q` suite (unit + integration markers) plus `ruff check .` plus `mypy tradingagents`; gate: 920+ baseline unit tests still pass plus the ~22 added by this spec; ruff 0 errors; mypy ≤ 132 (current floor 129 + at most 3 from new code; flag if higher)
- [ ] T029 Run `quickstart.md` Walkthrough 3 (SC-008 retrospective on the SC-003 Financials cohort) end-to-end as a manual smoke test against your real `~/.tradingagents/logs/` corpus; record the n_fired count + the survivors' realized α in the closing commit message. If `n_fired < 3`, document the empirical finding (XLF wasn't actually down >5%) in `claudedocs/sector-momentum-empirical-validation-<DATE>.md` and note that the spec's motivating premise needs revisiting before any default-on flip.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion (T003 placeholder is filled in by T005-T007). **BLOCKS** both user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Independent of US2.
- **User Story 2 (Phase 4)**: Depends on Foundational completion AND US1 (US2's verification tasks T023-T024 verify properties of the annotation that US1's wiring produces). Cannot run in parallel with US1 because both touch the same files (`portfolio_manager.py`, `sector_momentum_filter.py`).
- **Polish (Phase 5)**: Depends on US1 + US2 complete. Manual smoke (T029) last.

### User Story Dependencies

- **US1 (P1, MVP)**: Can start after Phase 2. **MVP-deliverable on its own** — operator gets sector-momentum suppression coverage even if US2's audit-clarity tasks haven't landed.
- **US2 (P2)**: Strictly depends on US1 (the audit fields it verifies are emitted by US1's wiring). Cannot run in parallel.

### Within Each User Story

- Tests can be batched in parallel within a phase (separate functions in the same test file).
- Implementation tasks within US1 are minimal because the heavy lifting is in Phase 2; T016-T017 are sequential because both touch `portfolio_manager.py` / `agent_states.py`.

### Parallel Opportunities

**Within Phase 1**: T001 + T002 sequential (same file `default_config.py`); T003 + T004 [P] (different files).

**Within Phase 2**: T005 + T006 sequential (same file `sector_momentum_filter.py`; T006 depends on T005); T007 sequential after T006 (same file). T008 [P] with T005-T007 as test-writing batch (separate file, no dependency on impl ordering).

**Within Phase 3 (US1)**: 7 test tasks T009-T015 all in parallel — separate functions in 2 test files (test_portfolio_manager_filter_integration.py + test_trading_graph.py). Implementation T016 sequential after tests; T017 [P] with T016 (different files: agent_states.py).

**Within Phase 4 (US2)**: 5 test tasks T018-T022 in parallel (test_sector_momentum_filter.py separate functions); T023 + T024 sequential (verification passes on existing files).

**Within Phase 5**: T025 + T026 + T027 in parallel (different files); T028 + T029 sequential at end.

---

## Parallel Example: Phase 2 Foundational

After Phase 1 setup completes, the test file can be drafted in parallel with the impl files; then impl tasks run sequentially:

```bash
# Sequential impl (same file `sector_momentum_filter.py`):
Task: "Implement _etf_history with LRU cache"                    # T005
Task: "Implement _compute_etf_30d_return_pct"                    # T006
Task: "Implement maybe_suppress_bull_rating per filter_function.md" # T007

# Parallel test file (independent of impl ordering — write the tests against the planned interface):
Task: "Create tests/test_sector_momentum_filter.py with 15 fixtures" # T008
```

## Parallel Example: Phase 3 US1

After Phase 2 completes:

```bash
# All 7 test functions in parallel (separate functions in 2 test files):
Task: "Add test_filter_disabled_by_default_threshold_none"              # T009
Task: "Add test_filter_active_downgrades_overweight_when_etf_below"     # T010
Task: "Add test_filter_active_keeps_overweight_when_etf_above"          # T011
Task: "Add test_filter_does_not_act_on_non_bullish_ratings"             # T012
Task: "Add test_filter_runs_after_spec_003_in_pm_hook_chain"            # T013
Task: "Add test_state_log_persists_sector_momentum_field"               # T014
Task: "Add test_state_log_sector_momentum_is_none_when_field_absent"    # T015

# Then implementation (T016 sequential first because PM wiring; T017 [P] different file):
Task: "Wire maybe_suppress_bull_rating into portfolio_manager.py"       # T016
Task: "Add sector_momentum field to AgentState TypedDict"               # T017
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001-T004) — ~20 min
2. Complete Phase 2: Foundational (T005-T008) — ~2h (filter logic + 15 unit tests)
3. Complete Phase 3: User Story 1 (T009-T017) — ~1.5h (7 integration tests + 2 wiring tasks)
4. **STOP and VALIDATE**: Run T026 (SC-008 integration test) plus the US1 tests. If all green and SC-008 holds (n_fired ≥ 3 for SC-003 Financials at -5% threshold), MVP complete.
5. Operator demo: enable filter in shadow mode for a 5-day live-forward run; observe annotations.

### Incremental Delivery

1. Setup + Foundational + US1 → MVP (sector-rotation suppression works) → demo
2. Add US2 → audit annotation fields persisted + queryable → operator can attribute α per filter
3. Polish (T025-T029) → retrospective + CLAUDE.md updated + green test/ruff/mypy gate → ready to commit + push the branch

### Single-developer Strategy

Sequential in practice; [P] markers indicate which tasks can be batched in a single multi-tool-call message. Most useful at:
- Phase 2 test-writing batch (T008 alongside T005-T007)
- Phase 3 US1 test-writing batch (T009-T015 in one batch, then implementation)
- Phase 4 US2 test-writing batch (T018-T022)
- Phase 5 polish files in parallel (T025-T027)

---

## Notes

- **[P] tasks** = different files, no dependencies — safe to batch in a single multi-tool-call message.
- **[Story] label** maps each task to its user story for traceability against `spec.md` acceptance scenarios.
- **Each user story is independently completable** within the constraint that US2's verification depends on US1's wiring producing the annotation fields. This matches the spec's intent — US1 is the MVP, US2 is operational ergonomic on top.
- **Pre-commit gate**: pytest unit tests must pass on every commit. T028 (full gate) is the polish-phase final gate; intermediate commits within phases must keep the unit-test suite green.
- **Cost discipline (Principle III)**: this entire implementation has T1 cost (zero LLM API calls per FR-006/SC-005). The validation in `quickstart.md` Walkthrough 4 (ablation experiment) IS T2-T3 cost depending on the experiment scope; HYPOTHESIS.md should justify per the constitution.
- **Avoid**: cross-story dependencies that break independence beyond the documented US2-needs-US1 ordering. Avoid: vague tasks ("improve filter") — every task above names exact files + precise behavior.
- **Default-on flip**: out of scope for this spec. Lands in a separate commit AFTER (a) SC-008 passes, (b) corpus retrospective shows positive net Δα, (c) per-sector behavior documented. Per Constitution II ablation discipline + the precedent set by A3 + spec 003 default flips.
- **After completion**: invoke `/speckit.analyze` for post-mortem if anything is worth recording structurally; otherwise the spec dir + commit history is the record.
