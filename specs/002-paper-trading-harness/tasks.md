---

description: "Task list for Paper-Trading Harness implementation"
---

# Tasks: Paper-Trading Harness

**Input**: Design documents from `specs/002-paper-trading-harness/`
**Prerequisites**: spec.md ✓, plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Included throughout. The spec explicitly requires ≥90% line coverage on new code (SC-007) and an integration-marked SC-003 reproduction test (SC-001). Tests are written alongside implementation rather than strict TDD-first to keep iteration rapid; pre-commit's `pytest -m unit` gate enforces that all unit tests pass before any commit lands.

**Organization**: Tasks are grouped by user story (US1, US2, US3 from spec.md) so each story can be implemented, tested, and validated independently. Within each story, [P] marks tasks that can run in parallel (different files, no dependencies on incomplete tasks in the same phase).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a single-project Python package + CLI per `plan.md` Structure Decision:
- Source: `tradingagents/paper/` package + `scripts/paper_trade.py` CLI
- Tests: `tests/` (flat, matches existing convention)
- Data: `data/watchlists/`
- Docs: `docs/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton and add config-schema entries for paper-harness defaults.

- [ ] T001 Create `tradingagents/paper/` package directory with empty `tradingagents/paper/__init__.py` (sets up importable package; will receive public exports in Phase 2/3)
- [ ] T002 [P] Create `data/watchlists/` directory with placeholder `data/watchlists/.gitkeep` (so the empty directory is tracked; populated by T030)
- [ ] T003 [P] Add `paper_state_dir` and `paper_digest_dir` keys to `TradingAgentsConfig` TypedDict in `tradingagents/default_config.py` (default values: `~/.tradingagents/paper/` and `claudedocs/`; honors `TRADINGAGENTS_CACHE_DIR` for state path)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: All three user stories load and save portfolio state. The entity dataclasses, state I/O, sectors cache, and pricing layer are blocking prerequisites for US1, US2, and US3.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Create `tradingagents/paper/errors.py` with `PortfolioStateError` exception class (inherits `Exception`; carries `path` + `failing_invariant` attributes for one-line operator error messages per `contracts/cli.md`)
- [ ] T005 [P] Create `tradingagents/paper/portfolio.py` with `Portfolio`, `Position`, `ClosedPosition`, `EquityPoint` dataclasses + `Portfolio.validate()` method per `data-model.md` (frozen=False on Portfolio since it's the mutable state holder; `Position` and `ClosedPosition` are mutable for in-place close transitions; all money fields use `decimal.Decimal`)
- [ ] T006 [P] Create `tradingagents/paper/policy.py` with `PolicySnapshot` frozen dataclass + default values + `policy_snapshot_hash()` helper that returns hex SHA-256 of canonical JSON serialization (defaults match `data-model.md` table; Sizing/Entry/Exit policy logic deferred to T019)
- [ ] T007 [P] Create `tradingagents/paper/events.py` with `EventType` enum + `Event` dataclass per `data-model.md` (event_type values: entry, exit, skip_cap, skip_cash, mark, data_anomaly, step_skipped_already_processed; payload is `dict[str, Any]`)
- [ ] T008 [P] Create `tradingagents/paper/sectors.py` with `get_sector(ticker, cache_path) -> str` helper (lazy yfinance fetch; persistent JSON cache at `~/.tradingagents/paper/sectors.json`; defaults `"Unknown"` on lookup failure per Assumption)
- [ ] T009 Create `tradingagents/paper/state.py` with `load_portfolio(path) -> Portfolio`, `save_portfolio(portfolio, path) -> None` (atomic temp-file-rename per `contracts/state_json.md`), `append_event(event, path) -> None` (single-line JSONL append per `contracts/events_jsonl.md`); depends on T004, T005, T006, T007
- [ ] T010 [P] Create `tradingagents/paper/pricing.py` with `next_trading_day_close(ticker, date, slippage_bps) -> Decimal` (yfinance frame-fetch with 7-day calendar buffer per R-6) + `compute_realized_alpha(ticker, entry_date, exit_date, benchmark) -> tuple[Decimal, Decimal, int]` (delegates to `tradingagents.dataflows.returns.returns_from_frames` per FR-012); depends on T004
- [ ] T011 [P] Create `tests/test_paper_portfolio.py` with unit tests for Portfolio/Position/ClosedPosition/EquityPoint dataclasses + `Portfolio.validate()` invariants (cash + market value = equity; no duplicate tickers; cash buffer floor; sector cap at entry); covers T005
- [ ] T012 [P] Create `tests/test_paper_state.py` with unit tests for state JSON round-trip + atomic write + JSONL append idempotency + replay-from-events invariant per `contracts/events_jsonl.md` ("Replay invariant" section); covers T009
- [ ] T013 [P] Create `tests/test_paper_pricing.py` with unit tests for slippage math + `next_trading_day_close` mocked yfinance frames + `compute_realized_alpha` reconciliation against `returns_from_frames` directly; covers T010
- [ ] T014 [P] Create `tests/test_paper_sectors.py` with unit tests for sector cache hit/miss + `"Unknown"` fallback on yfinance failure (mocked); covers T008
- [ ] T015 [P] Create `tests/test_paper_policy_snapshot.py` with unit tests for PolicySnapshot defaults + frozen-immutability + `policy_snapshot_hash()` determinism; covers T006

**Checkpoint**: Foundation ready. All entities, state I/O, pricing, and sectors are available for the engine. User story implementation can begin.

---

## Phase 3: User Story 1 - Validate harness logic against SC-003 (Priority: P1) 🎯 MVP

**Goal**: Operator can run `paper_trade replay` over the SC-003 date range and have the harness reproduce the +5.96% bullish-bucket mean α within ±100 bps. This is the validation gate — without it, no live use.

**Independent Test**: Run `python scripts/paper_trade.py replay --signals-csv experiments/2026-05-05-003-signal-at-scale/results.csv --watchlist <sc003-tickers> --start 2026-04-03 --end 2026-05-04 --portfolio-id sc003-validation --yes`. Inspect the digest's ITD α vs SPY line; pass if within ±100 bps of +5.96% per SC-001.

### Tests for User Story 1

- [ ] T016 [P] [US1] Create `tests/test_paper_policy.py` with unit tests for `DefaultPolicy` sizing (target_per_position_pct, n_max_positions, cap saturation), entry filter (per-position cap, per-sector cap, cash-buffer respect), exit logic (window_elapsed at 21 trading days, mid_window_signal on Sell/Underweight, NOT mid_window_hold per Principle VII guard), per `data-model.md` ExitReason enum
- [ ] T017 [P] [US1] Create `tests/test_paper_engine.py` with unit tests for `PaperTradingEngine.step` orchestration: empty portfolio + 3-bullish-signals → 3 entries; existing position + intended_close_date today → exit; data anomaly handling (yfinance returns empty frame → exit_reason=data_anomaly; engine continues with rest of signals); ordering (exits before entries within a step so freed cash counts toward entry budget)
- [ ] T018 [P] [US1] Create `tests/test_paper_digest.py` with unit tests for digest renderer: empty portfolio digest renders without error; full-portfolio digest contains all required sections from `contracts/digest_md.md`; **Principle IV disclaimer assertion** (`test_principle_iv_disclaimer_present`) greps for verbatim substring `"Simulation only — not financial advice"` per R-12 + SC-005

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement `DefaultPolicy.size_position(portfolio, ticker, sector) -> int | None` and `DefaultPolicy.should_enter(portfolio, ticker, sector, rating) -> EntryDecision` and `DefaultPolicy.should_exit(position, today, todays_signals) -> ExitDecision` in `tradingagents/paper/policy.py` (extends T006 dataclass with the policy LOGIC; whole-share rounding per R-4; sector cap math per `data-model.md` invariant 4)
- [ ] T020 [P] [US1] Implement digest renderer `render_digest(portfolio, today, todays_step_result) -> str` in `tradingagents/paper/digest.py` per `contracts/digest_md.md` document structure (markdown tables; equity sparkline using Unicode `▁..█`; verbatim Principle IV disclaimer at top; rendering helpers for Decimal currency + percent formatting)
- [ ] T021 [US1] Implement `PaperTradingEngine.step(portfolio, today, signals_dict, policy) -> StepResult` in `tradingagents/paper/engine.py` (idempotency check via R-5 → early-exit `step_skipped_already_processed` event; exits processed before entries; mark-to-market last; emits all Event objects per `contracts/events_jsonl.md`); depends on T019, T010 (pricing), T009 (state I/O)
- [ ] T022 [US1] Implement `replay` subcommand in `scripts/paper_trade.py` (typer subcommand per `contracts/cli.md`; loads or initializes Portfolio; iterates trading days from --start to --end via R-6 calendar derivation; calls `engine.step` per day; writes digest per day to --digest-dir; cost-confirmation prompt prints "0 LLM API calls expected"; `--yes` flag bypasses); depends on T021, T020
- [ ] T023 [US1] Update `tradingagents/paper/__init__.py` to export `Portfolio`, `Position`, `ClosedPosition`, `PolicySnapshot`, `PaperTradingEngine`, `render_digest`, `PortfolioStateError` for downstream callers; depends on T021
- [ ] T024 [US1] Create `tests/test_paper_sc003_reproduction.py` with the integration-marked test `test_replay_sc003_reproduces_bullish_bucket` per R-13: loads `experiments/2026-05-05-003-signal-at-scale/results.csv` (skip with clear message if file missing); constructs watchlist from unique tickers; runs replay over 2026-04-03 → 2026-05-04 in temp dirs; asserts closed-position mean α within ±100 bps of +5.96%; marked `@pytest.mark.integration` so pre-commit's `-m unit` skips it

**Checkpoint**: At this point, US1 is fully functional. Operator can run replay over SC-003 dates and the harness reproduces the +5.96% bullish-bucket α within tolerance. **MVP delivered.**

---

## Phase 4: User Story 2 - Run a daily step (cron-able live-forward use) (Priority: P1)

**Goal**: Operator can run `paper_trade step` daily after generating signals via `daily_signals.py --emit-csv`. Re-running step for the same date is a byte-identical no-op (idempotency per SC-002). Mid-window Sell/Underweight signals exit positions early; mid-window Hold ratings are ignored (Principle VII honored).

**Independent Test**: Construct a synthetic 5-day signals CSV. Run `step` for each day in sequence. Inspect the JSON state file after each day to verify positions, cash, and equity track correctly. Re-running step for any prior day produces zero state changes (verified by byte-identical state file via SC-002 test).

### Tests for User Story 2

- [ ] T025 [P] [US2] Add tests to `tests/test_daily_signals.py` for the new `--emit-csv` flag: round-trips with all required + optional columns per `contracts/signals_csv.md`; atomic-write protection (temp file + rename); overwrites existing file
- [ ] T026 [P] [US2] Create `tests/test_paper_cli.py` with unit tests for `step` subcommand: empty portfolio + 3-bullish-CSV → 3 entries persisted; held position + 21-day-elapsed → exit + cash returned; held position + mid-window Sell signal → exit at next-trading-day close per FR-006; **idempotency test** (`test_step_idempotent_on_same_date_byte_identical_state`) writes the state file, re-runs step for the same date, asserts byte-equal hash per SC-002
- [ ] T027 [P] [US2] Add tests to `tests/test_paper_engine.py` (extends T017) for: mid-window Hold rating on held ticker → position NOT closed (Principle VII guard); mid-window Sell/Underweight on held ticker → position closed with `exit_reason=mid_window_signal`; conflicting signals on same ticker same date → uses last row in input order per `contracts/signals_csv.md` row-rule 1

### Implementation for User Story 2

- [ ] T028 [US2] Add `--emit-csv <path>` option to `scripts/daily_signals.py` (typer Option; after the existing markdown digest write, also writes a CSV with the schema from `contracts/signals_csv.md` R-10; atomic temp-file-rename); depends on existing daily_signals.py structure
- [ ] T029 [US2] Implement `step` subcommand in `scripts/paper_trade.py` per `contracts/cli.md` (loads existing state if present; idempotency check via portfolio.equity_curve dates; calls `engine.step` for the single date; persists state + appends events; writes digest; one-line summary to stdout); depends on T021, T022 (extends same file)
- [ ] T030 [P] [US2] Create default watchlist file `data/watchlists/tech_weighted.txt` per R-11 spec (~25 tickers with sector comments: ~60% Tech, 15% Healthcare, 10% Financials, 15% Other); replaces the placeholder from T002

**Checkpoint**: US1 + US2 both functional. Daily live-forward flow works end-to-end with the operator running daily_signals.py + paper_trade step in sequence. Idempotency verified.

---

## Phase 5: User Story 3 - Inspect portfolio state at any time (Priority: P2)

**Goal**: Operator can run `paper_trade status` to see current portfolio state without modifying anything (no event log writes, no state file writes). Supports inspection of any portfolio_id.

**Independent Test**: After running step over a synthetic sequence, run `paper_trade status`. Verify the rendered digest matches expected state from manual calculation. Re-running status produces identical output (no state mutation).

### Tests for User Story 3

- [ ] T031 [P] [US3] Add tests to `tests/test_paper_cli.py` (extends T026) for `status` subcommand: portfolio with 3 open + 2 closed positions → digest renders all sections; missing state file → "No portfolio found" exit 0 (not exit code error); status invocation does NOT modify state file mtime or events.jsonl size (asserts both before/after)

### Implementation for User Story 3

- [ ] T032 [US3] Implement `status` subcommand in `scripts/paper_trade.py` per `contracts/cli.md` (loads state read-only; fetches latest closes via `pricing.next_trading_day_close` for unrealized marks; renders digest to stdout; **no state file writes, no event log appends**); depends on T021, T022, T029 (extends same file)

**Checkpoint**: All three user stories functional and independently tested. Harness is feature-complete per spec.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Operator documentation, project documentation updates, final validation.

- [ ] T033 [P] Create `docs/PAPER_TRADING.md` operator guide (~150 LOC; copy from `specs/002-paper-trading-harness/quickstart.md` content + Principle IV disclaimer prominent at top; covers: prerequisites, walkthrough 1-4, state file inspection, backup, troubleshooting, scope boundaries)
- [ ] T034 [P] Update `CLAUDE.md` with two new sections: under "Commands" add a paragraph about `paper_trade.py replay/step/status` + the `daily_signals.py --emit-csv` modification; under "Architecture/Persistence" add a third bullet alongside the existing decision-log + checkpoint-resume bullets describing the paper-trading state convention (`~/.tradingagents/paper/<id>.json` + `<id>.events.jsonl`); include cross-link to `specs/002-paper-trading-harness/`
- [ ] T035 Run full `pytest -q` suite. Must pass with all 854 baseline tests + new paper-harness tests (target ~895 total); zero existing-test regressions allowed
- [ ] T036 Run `ruff check .` + `ruff format --check .`; zero new violations (project baseline is 0 errors per CLAUDE.md commit `a0ec447`); manually run `mypy tradingagents` and verify the count has not increased (current floor 126 per commit `1611e51` after AIMessage-narrowing)
- [ ] T037 Run `quickstart.md` Walkthrough 1 end-to-end as a manual smoke test (replay over SC-003 with the SC-003 watchlist; inspect digest manually; confirm ITD α value matches expectations); record actual α value in commit message for the closing commit

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. **BLOCKS** all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Independent of US2/US3.
- **User Story 2 (Phase 4)**: Depends on Foundational completion. Reuses Phase 3's `engine.py` + `policy.py` + `digest.py` (already done after US1) but introduces no NEW shared-file modifications beyond extending `scripts/paper_trade.py`.
- **User Story 3 (Phase 5)**: Depends on Foundational completion. Reuses Phase 3's pricing + digest. Extends `scripts/paper_trade.py` (cannot run in parallel with US2's CLI extension).
- **Polish (Phase 6)**: Depends on at least US1 complete (for the SC-001 reproduction smoke); can run after US1 even if US2/US3 still pending.

### User Story Dependencies

- **US1 (P1, MVP)**: Can start after Phase 2. No dependencies on other stories. **MVP-deliverable on its own.**
- **US2 (P1)**: Can start after Phase 2 + Phase 3 (since the `step` CLI command is added to the same `scripts/paper_trade.py` file extended in T022; sequential file extension required).
- **US3 (P2)**: Can start after Phase 2 + Phase 3. Cannot run in parallel with US2 because both extend `scripts/paper_trade.py`.

### Within Each User Story

- Tests + implementation can be written in either order but tests MUST pass before the story phase is considered checkpoint-complete.
- Models / dataclasses already in Phase 2; story phases focus on behavior implementation + CLI surface.
- Story complete = all SC-### success criteria for that story pass.

### Parallel Opportunities

**Within Phase 1**: T002, T003 are [P] — different files (data dir vs default_config.py).

**Within Phase 2**: T004, T005, T006, T007, T008, T010 are all [P] — different files. T009 depends on T004-T007 (must wait). T011-T015 are all [P] — different test files, each can be written alongside its corresponding source file.

**Within Phase 3 (US1)**: T016, T017, T018 (all tests) are [P]. T019, T020 are [P] (different files: policy.py extension vs digest.py creation). T021 (engine) sequenced after T019. T022 (CLI replay) sequenced after T021. T023 (init exports) sequenced after T021. T024 (integration test) is independent — can run any time after T021.

**Within Phase 4 (US2)**: T025, T026, T027 (all tests) are [P]. T028 (`daily_signals.py --emit-csv`) and T030 (default watchlist file) are [P] — different files. T029 (`step` subcommand) extends `scripts/paper_trade.py` — sequenced after T022 from US1.

**Within Phase 5 (US3)**: T031 (tests) and T032 (status subcommand) — T032 must come after T029 from US2 (same file).

**Within Phase 6**: T033, T034, T036 are [P]. T035 sequenced after all phases. T037 last (manual smoke).

---

## Parallel Example: Phase 2 Foundational

After Phase 1 setup completes, fire these in parallel (different files, no inter-dependencies):

```bash
# Six implementation files in parallel:
Task: "Create tradingagents/paper/errors.py"               # T004
Task: "Create tradingagents/paper/portfolio.py"            # T005
Task: "Create tradingagents/paper/policy.py (dataclass)"   # T006
Task: "Create tradingagents/paper/events.py"               # T007
Task: "Create tradingagents/paper/sectors.py"              # T008
Task: "Create tradingagents/paper/pricing.py"              # T010

# Then T009 (state.py) sequentially after T004-T007 complete
# Then five test files in parallel:
Task: "tests/test_paper_portfolio.py"                      # T011
Task: "tests/test_paper_state.py"                          # T012
Task: "tests/test_paper_pricing.py"                        # T013
Task: "tests/test_paper_sectors.py"                        # T014
Task: "tests/test_paper_policy_snapshot.py"                # T015
```

## Parallel Example: Phase 3 US1

After Phase 2 completes:

```bash
# Three test files in parallel (write tests):
Task: "tests/test_paper_policy.py (DefaultPolicy)"         # T016
Task: "tests/test_paper_engine.py"                         # T017
Task: "tests/test_paper_digest.py + Principle IV assert"   # T018

# Two implementation files in parallel:
Task: "DefaultPolicy LOGIC in tradingagents/paper/policy.py" # T019
Task: "render_digest in tradingagents/paper/digest.py"     # T020

# Then sequentially (engine depends on policy):
Task: "PaperTradingEngine.step in engine.py"               # T021
Task: "replay subcommand in scripts/paper_trade.py"        # T022
Task: "Update tradingagents/paper/__init__.py exports"     # T023

# Independent integration test, any time after T021:
Task: "test_paper_sc003_reproduction.py (SC-001 gate)"     # T024
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001-T003) — ~15 min
2. Complete Phase 2: Foundational (T004-T015) — ~3-4 hours
3. Complete Phase 3: User Story 1 (T016-T024) — ~3-4 hours including the SC-003 integration test
4. **STOP and VALIDATE**: Run T024 (SC-003 reproduction). If +5.96% within ±100 bps, MVP complete.
5. Operator demo: replay any historical signal CSV; inspect digests.

### Incremental Delivery

1. Setup + Foundational + US1 → Foundation + MVP (validation gate passes) → demo
2. Add US2 (T025-T030) → Daily step works idempotently → demo with cron
3. Add US3 (T031-T032) → Status inspection → demo
4. Polish (T033-T037) → Docs + CLAUDE.md updates + green test/ruff/mypy gate → ready to commit + push the branch

### Single-developer Strategy

Since this is a personal project with one developer, "parallel" tasks in practice run sequentially in fast succession; the [P] markers indicate which tasks could be batched in a single multi-tool-call message OR delegated to subagents. Most useful at the test-writing batches in Phase 2 (T011-T015 in one batch) and Phase 3 (T016-T018 in one batch).

---

## Notes

- **[P] tasks** = different files, no dependencies — safe to batch in a single multi-tool-call message
- **[Story] label** maps each task to its user story for traceability against spec.md acceptance scenarios
- **Each user story is independently completable**: US1 alone delivers the MVP (validation gate); US2 adds operator-daily flow; US3 adds inspection ergonomics
- **Pre-commit gate**: pytest unit tests must pass on every commit. T035 (full suite) is the polish-phase gate; intermediate commits within phases must keep the unit-test suite green.
- **Cost discipline (Principle III)**: this entire implementation has T1 cost (≤$5; actually $0 since the harness has no LLM cost per FR-011/SC-008 and the SC-001 reproduction reuses existing CSV signals). No HYPOTHESIS.md cost-justification needed beyond what the spec already documents.
- **Avoid**: cross-story dependencies that break independence (e.g., do NOT make US3's status subcommand depend on US2's step subcommand running first; both should work against any valid state file). Avoid: vague tasks ("improve digest") — every task above names exact files + precise behavior.
- **After completion**: invoke `/speckit.analyze` for post-mortem if anything is worth recording structurally; otherwise the spec dir + commit history is the record.
