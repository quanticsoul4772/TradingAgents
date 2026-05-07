---

description: "Task list for Bear-Sector-Symmetry Filter (Spec 006) implementation"
---

# Tasks: Bear-Sector-Symmetry Filter (Spec 006)

**Input**: Design documents from `specs/005-bear-sector-symmetry/`
**Prerequisites**: spec.md ✓, plan.md ✓, research.md ✓, data-model.md ✓, contracts/ (2) ✓, quickstart.md ✓

**Tests**: Included throughout. Spec requires ≥90% line coverage on new code (SC-007). Integration-marked test for SC-008 empirical-validation gate (≥8 of 18 `ticker_strong`-bearish commits suppressed at default +5% threshold) plus SC-009 disjoint-conditions guard with A3.

**Organization**: Tasks grouped by user story (US1, US2, US3 from spec.md). Within each story, [P] marks parallel-safe tasks (different files, no incomplete dependencies in the same phase).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single-project Python library extension per `plan.md` Structure Decision:
- Source: `tradingagents/agents/utils/` (new module parallel to A3 + spec 004) + `tradingagents/agents/managers/portfolio_manager.py` wiring
- Config: `tradingagents/default_config.py` (extend `TradingAgentsConfig` TypedDict + `DEFAULT_CONFIG`)
- State persistence: `tradingagents/graph/trading_graph.py:_log_state` whitelist extension + `tradingagents/agents/utils/agent_states.py` AgentState TypedDict extension
- Tests: `tests/` (flat)
- Scripts: `scripts/bear_sector_symmetry_retrospective.py` (new)
- Docs: `CLAUDE.md` (existing)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the config keys + scaffold the new module + extend the state-log whitelist + AgentState TypedDict so US1's tests have something to import and the persistence path is in place.

- [ ] T001 Add `bear_sector_symmetry_filter_mode: Literal["off", "shadow", "active"]`, `bear_sector_symmetry_filter_threshold_pct: float | None`, `bear_sector_symmetry_filter_lookback_days: int` keys to `TradingAgentsConfig` TypedDict in `tradingagents/default_config.py` (placement next to existing `sector_momentum_filter_*` keys; defaults `"off"`, `None`, `30` per FR-008/FR-013/R-9)
- [ ] T002 Add the same three keys to `DEFAULT_CONFIG` in `tradingagents/default_config.py` with default values + a 5-line comment cross-referencing `specs/005-bear-sector-symmetry/spec.md` and explaining (a) the filter is disabled by default per Constitution II ablation discipline, (b) the corpus retrospective gate before any default-on flip
- [ ] T003 [P] Create `tradingagents/agents/utils/bear_sector_symmetry_filter.py` with module docstring referencing the spec; include imports of `SECTOR_ETF_MAP`, `_etf_history`, `clear_etf_cache` from `tradingagents/agents/utils/sector_momentum_filter.py` per FR-004 (no duplication); placeholder `maybe_suppress_bear_rating` function stub returning unmodified decision + off annotation, so US1 tests can import without circular-import issues
- [ ] T004 [P] Extend `_log_state` whitelist in `tradingagents/graph/trading_graph.py` to include `"bear_sector_symmetry": final_state.get("bear_sector_symmetry")` with a 2-line comment cross-referencing the precedent set by commit `4c14d0f` (which added `contrarian_gate`) and spec 004 (which added `sector_momentum`); per R-5 + FR-009
- [ ] T005 [P] Extend `AgentState` TypedDict in `tradingagents/agents/utils/agent_states.py` to declare `bear_sector_symmetry: NotRequired[dict | None]` (matches existing `contrarian_gate` + `sector_momentum` declarations); without this, LangGraph silently drops the field from state merges per the bug spec 003 originally hit and CLAUDE.md documents

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the filter function + its supporting infrastructure (annotation builder, ticker history fetcher with LRU cache, sector lookup integration, relative-strength computation). All three user stories depend on `maybe_suppress_bear_rating` existing.

**⚠️ CRITICAL**: All user stories depend on the filter function being callable.

- [ ] T006 [P] Implement the LRU-cached ticker history fetcher in `tradingagents/agents/utils/bear_sector_symmetry_filter.py`: `_ticker_history(ticker, start, end) -> pd.DataFrame` decorated with `@functools.lru_cache(maxsize=128)` per R-2; thin wrapper around `yf.Ticker(ticker).history(start=start, end=end)`; returns empty DataFrame on yfinance failure (caught + warning logged); cache cleared between tests via a dedicated `clear_ticker_cache()` helper
- [ ] T007 [P] Implement `_compute_ticker_30d_return_pct(ticker, trade_date, lookback_days) -> float | None` helper in `tradingagents/agents/utils/bear_sector_symmetry_filter.py` that fetches the ticker history via `_ticker_history` for `trade_date - lookback_days * 1.5 - 7 calendar days` to `trade_date`, then computes the return as `(close[lookback_days] - close[0]) / close[0] * 100`; returns None if the frame has fewer than `lookback_days + 1` rows (insufficient history per R-9). Mirrors the spec 004 `_compute_etf_30d_return_pct` shape exactly.
- [ ] T008 Implement `maybe_suppress_bear_rating(decision_markdown, ticker, trade_date, *, threshold_pct, lookback_days, mode, sectors_cache_path, etf_history_fetcher=None, ticker_history_fetcher=None, sector_lookup=None) -> tuple[str, dict]` in `tradingagents/agents/utils/bear_sector_symmetry_filter.py` per `contracts/filter_function.md`; depends on T006 + T007; flow per data-model.md "State transitions" section: off-mode early return → bearish-only check → threshold validation (`< 0` rejected) → sector lookup → ETF mapping (via imported `SECTOR_ETF_MAP`) → ticker return computation → ETF return computation (via imported `_etf_history`) → relative-strength delta computation → strict-greater-than threshold check → active-mode override (UW/Sell → Hold) with markdown annotation matching spec 004's pattern; emits annotation dict with all 13 fields per `contracts/annotation_schema.md`
- [ ] T009 [P] Create `tests/test_bear_sector_symmetry_filter.py` covering all 20 fixtures named in `contracts/filter_function.md` + 12 fixtures from `contracts/annotation_schema.md`: off-mode, rating-not-bearish (Hold/Buy/OW each separate), threshold-None, threshold-negative, unknown-sector, no-etf-mapping, missing-ticker-data, missing-etf-data, threshold-crossed-active-on-underweight, threshold-crossed-active-on-sell, threshold-crossed-shadow, threshold-not-crossed, strict-greater-than-boundary, yfinance-ticker-fetch-raises, yfinance-etf-fetch-raises, decision-markdown-no-rating, invalid-mode, lru-cache-amortizes-ticker-fetches, etf-cache-shared-with-spec-004, relative-strength-arithmetic, all 11 invariants from data-model.md; uses synthetic frames + injected `sector_lookup` + `ticker_history_fetcher` + `etf_history_fetcher` callables to avoid live yfinance dependency

**Checkpoint**: Foundation ready. The filter function is fully testable in isolation. User story implementation can begin.

---

## Phase 3: User Story 1 - Counter-trend bear miss prevented (Priority: P1) 🎯 MVP

**Goal**: When the PM emits Underweight/Sell on a ticker that has outperformed its sector ETF by more than the configured threshold over the prior 30 trading days, the filter downgrades the rating to Hold and emits an annotation describing the suppression.

**Independent Test**: Run a propagate against NVDA for a date when NVDA's prior-30d return exceeded XLK's prior-30d return by >5% (verify with the SC-008 retrospective). With `bear_sector_symmetry_filter_mode="active"` + `threshold_pct=5.0`, verify the persisted state shows `final_trade_decision` as Hold (not Underweight) and `state["bear_sector_symmetry"]["fired"] == True`.

### Tests for User Story 1

- [ ] T010 [P] [US1] Add `test_bear_filter_disabled_by_default_threshold_none` to `tests/test_portfolio_manager_filter_integration.py`: with `threshold_pct=None` (default), running the PM hook chain on an Underweight rating produces unchanged rating + `state["bear_sector_symmetry"]["mode"] == "off"` (or None per implementer's choice); SC-006 byte-identity regression-guard
- [ ] T011 [P] [US1] Add `test_bear_filter_active_downgrades_underweight_when_relative_strength_above_threshold` to `tests/test_portfolio_manager_filter_integration.py`: mocked sector lookup returns "Technology", mocked ticker fetcher returns NVDA frame with +18% prior-30d return, mocked ETF fetcher returns XLK frame with +6% prior-30d return (delta = +12%), `threshold_pct=5.0`, `mode="active"`; verify `final_trade_decision` rating downgraded to Hold + `state["bear_sector_symmetry"]["fired"] == True` + post_rating == "Hold"; covers US1 acceptance scenario 1
- [ ] T012 [P] [US1] Add `test_bear_filter_active_downgrades_sell_when_relative_strength_above_threshold` to `tests/test_portfolio_manager_filter_integration.py`: same setup as T011 but PM rating is Sell; verify rating downgraded to Hold; covers US1 acceptance scenario 2
- [ ] T013 [P] [US1] Add `test_bear_filter_active_keeps_underweight_when_relative_strength_below_threshold` to `tests/test_portfolio_manager_filter_integration.py`: ticker +18%, ETF +14% (delta = +4%, below +5% threshold); verify rating remains Underweight + `would_fire == False`; covers US1 acceptance scenario 3
- [ ] T014 [P] [US1] Add `test_bear_filter_does_not_act_on_non_bearish_ratings` to `tests/test_portfolio_manager_filter_integration.py`: same setup with delta = +12%, but PM rating is Buy / Overweight / Hold (one test parameterized over the three); verify rating unchanged + `skipped == "rating_not_bearish"`; covers US1 acceptance scenarios 4 + 5
- [ ] T015 [P] [US1] Add `test_bear_filter_runs_after_a3_in_pm_hook_chain` to `tests/test_portfolio_manager_filter_integration.py`: setup where A3 has already downgraded Underweight to Hold (ticker -8% absolute); verify the bear-sector-symmetry filter sees Hold and emits `skipped == "rating_not_bearish"` (no double-suppression, ordering matters per FR-012); also covers US1 acceptance scenario 6 + SC-009 disjoint-conditions guard
- [ ] T016 [P] [US1] Add `test_state_log_persists_bear_sector_symmetry_field` to `tests/test_trading_graph.py`: regression-guard mirroring `test_state_log_persists_contrarian_gate_field` (commit `4c14d0f`) and the parallel spec 004 test; constructs final_state with `"bear_sector_symmetry"` populated, calls `_log_state`, asserts the field appears in the persisted JSON
- [ ] T017 [P] [US1] Add `test_state_log_bear_sector_symmetry_is_none_when_field_absent` to `tests/test_trading_graph.py`: when `bear_sector_symmetry` key is absent from final_state (e.g., off-mode early return that returned None), persisted log has `"bear_sector_symmetry": null`; mirrors the parallel test for `contrarian_gate` + `sector_momentum`

### Implementation for User Story 1

- [ ] T018 [US1] Wire `maybe_suppress_bear_rating` into `tradingagents/agents/managers/portfolio_manager.py` AFTER the existing A3 hook (the `maybe_suppress_bear_rating`-style block at lines ~95-109, NOT the spec 003/004 hooks which act on bullish ratings) per FR-012 ordering. Pass: `decision_markdown=final_trade_decision`, `ticker=state["company_of_interest"]`, `trade_date=state["trade_date"]`, `threshold_pct=config.get("bear_sector_symmetry_filter_threshold_pct")`, `lookback_days=config.get("bear_sector_symmetry_filter_lookback_days", 30)`, `mode=config.get("bear_sector_symmetry_filter_mode", "off")`, `sectors_cache_path=Path(config.get("paper_state_dir", str(Path.home() / ".tradingagents" / "paper"))) / "sectors.json"`. Wrap in try/except that mirrors the existing spec 003 + spec 004 wraps (per FR-010); merge the returned annotation into the result dict at `result["bear_sector_symmetry"] = annotation`. Depends on T008.

**Checkpoint**: At this point US1 is functional. Operator can enable the filter via PARAMS.json and observe both shadow + active mode behavior. **MVP delivered.** All 6 US1 acceptance scenarios from spec.md pass.

---

## Phase 4: User Story 2 - Operator distinguishes bear-sector-symmetry firings in audit (Priority: P2)

**Goal**: Operator inspecting `state["bear_sector_symmetry"]` sees a populated dict with all fields documented in `contracts/annotation_schema.md` so they can filter the corpus by `fired` / `would_fire` / `sector` / `etf` / `relative_strength_pct` for per-filter α attribution distinct from A3.

**Independent Test**: After running a small corpus through the harness with the filter in shadow mode, inspect each `state["bear_sector_symmetry"]` annotation; verify the fields are populated correctly per the schema (mode, sector, etf, ticker_30d_return_pct, etf_30d_return_pct, relative_strength_pct, threshold_pct, lookback_days, would_fire, fired, pre_rating, post_rating, skipped).

### Tests for User Story 2

- [ ] T019 [P] [US2] Add `test_annotation_active_fires_populates_all_fields` to `tests/test_bear_sector_symmetry_filter.py`: mode=active + would_fire=True → all 13 fields populated per `contracts/annotation_schema.md` schema (sector, etf, ticker_30d_return_pct, etf_30d_return_pct, relative_strength_pct, threshold_pct, lookback_days, pre_rating, post_rating, would_fire=True, fired=True, mode="active", skipped=None); covers US2 acceptance scenario 1
- [ ] T020 [P] [US2] Add `test_annotation_shadow_records_would_fire_only` to `tests/test_bear_sector_symmetry_filter.py`: mode=shadow + threshold-crossed → would_fire=True + fired=False + post_rating == pre_rating; covers US2 acceptance scenario 2
- [ ] T021 [P] [US2] Add `test_annotation_off_returns_none_or_off_skipped` to `tests/test_bear_sector_symmetry_filter.py`: mode=off → annotation dict OR None per implementer's choice (both forms documented as valid in contract); covers US2 acceptance scenario 3
- [ ] T022 [P] [US2] Add `test_annotation_invariants_per_data_model` to `tests/test_bear_sector_symmetry_filter.py`: invariants 1-11 from `data-model.md` "Validation invariants" + `contracts/annotation_schema.md` "Field invariants"; one assert per invariant; covers schema-level audit guarantees
- [ ] T023 [P] [US2] Add `test_audit_corpus_filter_by_fired_and_relative_strength` to `tests/test_bear_sector_symmetry_filter.py`: build a list of 6 synthetic annotations (2 fired, 2 would-fire-only, 2 not-fire), verify Python filters `[a for a in annotations if a["fired"]]` and `[a for a in annotations if a["relative_strength_pct"] is not None and a["relative_strength_pct"] > 5]` return the correct subsets; matches the corpus-audit pattern in `quickstart.md` Walkthrough 2

### Implementation for User Story 2

- [ ] T024 [US2] Verify the annotation builder in `maybe_suppress_bear_rating` (T008) populates ALL 13 fields specified in `contracts/annotation_schema.md` regardless of which path is taken (off / skipped / not-fired / fired). Add explicit field-by-field initialization to a default dict at the function entry; mutate fields as the function progresses; assert all 13 fields are present in the returned dict before returning. This task is a verification-and-tightening pass on T008's existing implementation, not a separate function.
- [ ] T025 [US2] Verify the persistence path: state["bear_sector_symmetry"] flows through `_log_state` per T004 (whitelist extension) + T016 (regression test). Inspect `tradingagents/graph/trading_graph.py` after T004 to confirm no field-level filtering occurs that would drop sub-fields of the annotation dict; if any filtering exists, extend it. The annotation dict is dumped whole, so all fields ride together — same pattern as `contrarian_gate` + `sector_momentum`.

**Checkpoint**: US1 + US2 both functional. Audit annotation fields are persisted, queryable, and distinguish fired vs would-fire vs skipped firings, distinct from A3's annotation.

---

## Phase 5: User Story 3 - Corpus retrospective gate before default-on flip (Priority: P3)

**Goal**: An offline retrospective script exists that walks the existing experiments corpus, simulates the filter at multiple thresholds, and reports per-threshold + per-sector net Δα contribution. The script gates the default-on flip per Constitution II ablation discipline.

**Independent Test**: Run `scripts/bear_sector_symmetry_retrospective.py` against the existing corpus. Inspect the output markdown; verify it reports baseline mean α (no filter) + per-threshold (kept α, fired α, net Δα) + per-sector breakdown at the default threshold + suppressed-loser/winner cohort listing. SC-008 quantitative gate: at +5% threshold, ≥8 of 18 `ticker_strong`-bearish commits suppressed AND net Δα positive.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create `scripts/bear_sector_symmetry_retrospective.py` per R-6 + R-7: walks `experiments/*/results.csv` for bearish (Underweight/Sell) commits; for each, looks up the ticker's sector + maps to ETF + fetches both ticker prior-30-trading-day return AND ETF prior-30-trading-day return + computes relative-strength delta + reports per-threshold (`+3, +5, +7.5, +10`) what would have fired, fired α, kept α, net Δα contribution; per-sector breakdown; cross-tab against the cells from `claudedocs/sector-alpha-attribution-2026-05-06.md` (loaded via the sister CSV); offline (zero LLM cost). Mirror `scripts/sector_momentum_retrospective.py` (spec 004) shape exactly with bear-side inversions.
- [ ] T027 [P] [US3] Add `test_today_ticker_strong_bear_cohort_suppression_at_5pct` to `tests/test_bear_sector_symmetry_filter.py` per R-7: load the 18 `ticker_strong`-bearish commits from `claudedocs/sector-alpha-attribution-2026-05-06.csv` (filter rows where `cell == "ticker_weak"` for bearish commits — no, wait: for BEARISH commits the success cell is `ticker_weak` and the FAILURE cell is `ticker_strong`; load rows where `rating in ("Underweight", "Sell") AND cell == "ticker_strong"`); calls the filter against live yfinance data with threshold=+5.0 + lookback=30; asserts `len(fired) >= 8` per SC-008. Marked `@pytest.mark.integration` so pre-commit's `pytest -m unit` skips it. Skip with clear message if `~/.tradingagents/paper/sectors.json` is missing OR if the attribution CSV is missing.

**Checkpoint**: US3 complete. Retrospective script + SC-008 integration test both runnable. Default-on flip prerequisites in place per Constitution II.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: CLAUDE.md update, final test/ruff/mypy gate, manual smoke against the corpus.

- [ ] T028 [P] Update `CLAUDE.md` "Empirical filters" section to add a 5th bullet for spec 006: name the filter, mention its empirical motivation (today's sector-α attribution +28.02%-mean-α `ticker_strong`-bear cohort), default-off status, threshold/mode config keys, the `state["bear_sector_symmetry"]` annotation field, the SC-008 validation gate. Cross-link the spec dir, `claudedocs/sector-alpha-attribution-2026-05-06.md`, and the new retrospective script.
- [ ] T029 Run full `pytest -q` suite (unit + integration markers) plus `ruff check .` plus `mypy tradingagents`; gate: existing baseline tests still pass plus the ~26 added by this spec; ruff 0 errors; mypy ≤ 132 (current floor 126 + at most 6 from new code; flag if higher)
- [ ] T030 Run `quickstart.md` Walkthrough 3 (SC-008 retrospective on today's `ticker_strong`-bear cohort) end-to-end as a manual smoke test; record the n_fired count + the kept/fired α values in the closing commit message. If `n_fired < 8`, document the empirical finding in `claudedocs/bear-sector-symmetry-empirical-validation-<DATE>.md` and note that the spec's motivating premise (+5% threshold catches the cohort) needs revisiting before any default-on flip.
- [ ] T031 Run the corpus-wide threshold sweep (`scripts/bear_sector_symmetry_retrospective.py --threshold-sweep`) against the full 194-row corpus; record per-threshold net Δα + per-sector breakdown in `claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md`; this output drives the eventual (out-of-scope) default-on-flip decision

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion (T003 placeholder is filled in by T006-T008). **BLOCKS** all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Independent of US2 and US3.
- **User Story 2 (Phase 4)**: Depends on Foundational completion AND US1 (US2's verification tasks T024-T025 verify properties of the annotation that US1's wiring produces). Cannot run in parallel with US1 because both touch the same files (`portfolio_manager.py`, `bear_sector_symmetry_filter.py`).
- **User Story 3 (Phase 5)**: Depends on Foundational completion. Can run in parallel with US1 + US2 (different files: new script + new test).
- **Polish (Phase 6)**: Depends on US1 + US2 + US3 complete. Manual smoke (T030 + T031) last.

### User Story Dependencies

- **US1 (P1, MVP)**: Can start after Phase 2. **MVP-deliverable on its own** — operator gets bear-sector-symmetry suppression coverage even if US2's audit-clarity tasks + US3's retrospective haven't landed.
- **US2 (P2)**: Strictly depends on US1 (the audit fields it verifies are emitted by US1's wiring). Cannot run in parallel with US1.
- **US3 (P3)**: Independent of US1 + US2 in implementation (separate script + separate test); however, the SC-008 integration test (T027) only validates a working filter, so it logically depends on T008 (foundational impl). The retrospective script (T026) operates on existing corpus CSVs + yfinance, doesn't need the filter wiring at all.

### Within Each User Story

- Tests can be batched in parallel within a phase (separate functions in the same test file).
- Implementation tasks within US1 are minimal because the heavy lifting is in Phase 2; T018 is sequential (touches `portfolio_manager.py` which T024-T025 verify in US2).

### Parallel Opportunities

**Within Phase 1**: T001 + T002 sequential (same file `default_config.py`); T003 + T004 + T005 [P] (3 different files).

**Within Phase 2**: T006 + T007 sequential (same file `bear_sector_symmetry_filter.py`); T008 sequential after T007 (same file). T009 [P] with T006-T008 as test-writing batch (separate file, no dependency on impl ordering).

**Within Phase 3 (US1)**: 8 test tasks T010-T017 all in parallel — separate functions in 2 test files (test_portfolio_manager_filter_integration.py + test_trading_graph.py). Implementation T018 sequential after tests (touches portfolio_manager.py).

**Within Phase 4 (US2)**: 5 test tasks T019-T023 in parallel (test_bear_sector_symmetry_filter.py separate functions); T024 + T025 sequential (verification passes on existing files).

**Within Phase 5 (US3)**: T026 + T027 in parallel (different files: new script + new test).

**Within Phase 6**: T028 alone in parallel; T029 + T030 + T031 sequential at end (T029 is the gate; T030 + T031 are manual smokes that depend on a green gate).

---

## Parallel Example: Phase 2 Foundational

After Phase 1 setup completes, the test file can be drafted in parallel with the impl files; then impl tasks run sequentially:

```bash
# Sequential impl (same file `bear_sector_symmetry_filter.py`):
Task: "Implement _ticker_history with LRU cache"                       # T006
Task: "Implement _compute_ticker_30d_return_pct"                       # T007
Task: "Implement maybe_suppress_bear_rating per filter_function.md"    # T008

# Parallel test file (independent of impl ordering — write the tests against the planned interface):
Task: "Create tests/test_bear_sector_symmetry_filter.py with 20 fixtures"  # T009
```

## Parallel Example: Phase 3 US1

After Phase 2 completes:

```bash
# All 8 test functions in parallel (separate functions in 2 test files):
Task: "Add test_bear_filter_disabled_by_default_threshold_none"                       # T010
Task: "Add test_bear_filter_active_downgrades_underweight_when_relative_strength_above_threshold"  # T011
Task: "Add test_bear_filter_active_downgrades_sell_when_relative_strength_above_threshold"         # T012
Task: "Add test_bear_filter_active_keeps_underweight_when_relative_strength_below_threshold"       # T013
Task: "Add test_bear_filter_does_not_act_on_non_bearish_ratings"                      # T014
Task: "Add test_bear_filter_runs_after_a3_in_pm_hook_chain"                           # T015
Task: "Add test_state_log_persists_bear_sector_symmetry_field"                        # T016
Task: "Add test_state_log_bear_sector_symmetry_is_none_when_field_absent"             # T017

# Then implementation (T018 sequential because PM wiring):
Task: "Wire maybe_suppress_bear_rating into portfolio_manager.py"                     # T018
```

## Parallel Example: Phase 5 US3 (independent of US1+US2)

After Phase 2 completes (does NOT need to wait for US1+US2 to finish):

```bash
# Both tasks in parallel — different files:
Task: "Create scripts/bear_sector_symmetry_retrospective.py"                          # T026
Task: "Add test_today_ticker_strong_bear_cohort_suppression_at_5pct"                  # T027
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001-T005) — ~25 min
2. Complete Phase 2: Foundational (T006-T009) — ~2.5h (filter logic + 20+ unit tests)
3. Complete Phase 3: User Story 1 (T010-T018) — ~1.5h (8 integration tests + 1 wiring task)
4. **STOP and VALIDATE**: Run T027 (SC-008 integration test) plus the US1 tests. If all green and SC-008 holds (n_fired ≥ 8 for today's `ticker_strong`-bear cohort at +5% threshold), MVP complete.
5. Operator demo: enable filter in shadow mode for a 5-day live-forward run; observe annotations.

### Incremental Delivery

1. Setup + Foundational + US1 → MVP (counter-trend bear suppression works) → demo
2. Add US2 → audit annotation fields persisted + queryable → operator can attribute α per filter (distinct from A3's annotation)
3. Add US3 → retrospective + SC-008 integration test → empirical case for/against default-on flip in hand
4. Polish (T028-T031) → CLAUDE.md updated + green test/ruff/mypy gate + manual smoke + corpus retrospective writeup → ready to commit + push the branch

### Single-developer Strategy

Sequential in practice; [P] markers indicate which tasks can be batched in a single multi-tool-call message. Most useful at:
- Phase 1 setup files batch (T003 + T004 + T005 together)
- Phase 2 test-writing batch (T009 alongside T006-T008)
- Phase 3 US1 test-writing batch (T010-T017 in one batch, then implementation)
- Phase 4 US2 test-writing batch (T019-T023)
- Phase 5 US3 batch (T026 + T027 together)
- Phase 6 polish (T028 alongside T029)

### Cross-story parallel opportunity

US3 can run in parallel with US1 + US2 since the retrospective script doesn't touch the PM wiring. A single developer can interleave: write the retrospective script (T026) while waiting for the next batch of US1 tests to run.

---

## Notes

- **[P] tasks** = different files, no dependencies — safe to batch in a single multi-tool-call message.
- **[Story] label** maps each task to its user story for traceability against `spec.md` acceptance scenarios.
- **Each user story is independently completable** within the constraint that US2's verification depends on US1's wiring producing the annotation fields. US3 is genuinely independent (different files entirely).
- **Pre-commit gate**: pytest unit tests must pass on every commit. T029 (full gate) is the polish-phase final gate; intermediate commits within phases must keep the unit-test suite green.
- **Cost discipline (Principle III)**: this entire implementation has T1 cost (zero LLM API calls per FR-005/SC-005). The validation in `quickstart.md` Walkthrough 4 (ablation experiment) IS T2-T3 cost depending on the experiment scope; HYPOTHESIS.md should justify per the constitution.
- **Avoid**: cross-story dependencies that break independence beyond the documented US2-needs-US1 ordering. Avoid: vague tasks ("improve filter") — every task above names exact files + precise behavior.
- **Default-on flip**: out of scope for this spec. Lands in a separate commit AFTER (a) SC-008 passes, (b) corpus retrospective shows positive net Δα at +5%, (c) per-sector behavior documented. Per Constitution II ablation discipline + the precedent set by A3 + spec 003 + spec 004 default flips.
- **Reuse from spec 004**: `SECTOR_ETF_MAP` + `_etf_history` + `clear_etf_cache` imported per FR-004; new module adds NO duplicated mapping table or fetcher. Cache hits when both filters run on the same propagate (always true since both run on every commit).
- **AgentState declaration (T005)**: load-bearing per CLAUDE.md note + the spec 003 + spec 004 precedents. Without it, LangGraph silently drops the field from state merges — the bug spec 003 originally hit + worked around then later fixed.
- **Filter ordering (FR-012)**: A3 → spec 006 (this) → spec 003/003.5 → spec 004. The two bear filters are nearly disjoint by construction; if A3 fires the rating becomes Hold → spec 006 no-ops via the standard rating-set check (SC-009).
- **After completion**: invoke `/speckit.analyze` for post-mortem if anything is worth recording structurally; otherwise the spec dir + commit history is the record.
