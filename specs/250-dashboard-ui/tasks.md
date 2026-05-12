---
description: "Task list for spec 250-dashboard-ui — closes G-1 through G-12 from plan.md"
---

# Tasks: TradingAgents Dashboard UI

**Input**: Design documents from `specs/250-dashboard-ui/`
**Prerequisites**: `plan.md` (gap list G-1..G-12), `spec.md` (user stories US1..US5)
**Tests**: Included — the project has a 1273+ unit-test culture and a `pytest-fast` pre-commit gate; new code without tests breaks both.

## Format: `[ID] [Story?] Description`

- **[Story]**: Story label (US1..US5) for story-phase tasks only; omitted for Setup / Foundational / Polish
- Every task includes the exact file path(s) it touches
- The `[P]` parallel marker is omitted in this task list — see "Parallel Execution" below for which tasks can run in parallel within a PR

## Path Conventions

- Single project layout: `tradingagents/`, `tests/`, `scripts/`, `deploy/`, `specs/250-dashboard-ui/` at repo root.
- All paths absolute from repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Status**: COMPLETE — project initialized; `pyproject.toml`, pre-commit, ruff, pytest all in place. No tasks needed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Status**: COMPLETE — engine subprocess, dashboard backend, deploy artifacts, smoke gate all shipped via PRs #249, #252-#266. No tasks needed.

**Checkpoint**: Foundation ready — user-story tasks below begin from a green-test, deployed baseline.

---

## Phase 3: User Story 1 — View today's run on phone (Priority: P1) 🎯 MVP

**Goal**: Operator opens `https://rawcell.duckdns.org/trading/` on phone, sees within ≤5s: ratings table + paper portfolio open positions + cost spent today.

**Independent Test**: Load `/` on a fresh browser session. Verify the homepage renders all three blocks (ratings if any, portfolio panel always, cost meter always) without requiring navigation to `/portfolio` or any other route.

**Closes gaps**: G-1, G-2, G-5.

### Tests for User Story 1

- [ ] T001 [US1] Add `test_home_renders_paper_portfolio_inline` in `tests/test_dashboard_app.py` — fixture writes `paper/live.json`, GET `/` asserts cash + open positions render in the response body (G-1)
- [ ] T002 [US1] Add `test_home_shows_cost_today_when_no_run` in `tests/test_dashboard_app.py` — no progress.json present; GET `/` asserts `$0.00` cost block visible (G-2)
- [ ] T003 [US1] Add `test_cost_meter_in_persistent_header` in `tests/test_dashboard_app.py` — verify cost badge present in the `<header>` of every route (`/`, `/live`, `/portfolio`, `/tickers/<date>`, `/ticker/.../...`) per FR-019 (G-5)
- [ ] T004 [US1] Update existing `test_home_empty_state_when_no_runs` in `tests/test_dashboard_app.py` to assert the new portfolio + cost blocks render alongside the empty-state copy (does NOT assert trigger form — that's US4)

### Implementation for User Story 1

- [ ] T005 [US1] Update `home()` in `tradingagents/dashboard/app.py` to call `sr.read_portfolio("live")` and pass `portfolio` to template context (G-1)
- [ ] T006 [US1] Edit `tradingagents/dashboard/templates/home.html` — add two new sections in this order: (a) paper portfolio panel inline with link to full `/portfolio` (b) cost-spent-today block in the no-run header. **Do NOT add the trigger form here — that is owned by T012 in US4.** (G-1 + G-2)
- [ ] T007 [US1] Edit `tradingagents/dashboard/templates/base.html` — add a small persistent `<span>` cost badge in the `<header>` nav row, right-aligned, fed from a `cost_today` context variable (G-5)
- [ ] T008 [US1] Update all 6 HTMLResponse routes in `tradingagents/dashboard/app.py` (`home`, `live`, `live_partial`, `tickers_for_date`, `ticker_detail`, `portfolio`) to inject `cost_today=summarize_progress(read_progress())["cost_so_far_usd"]` into the template context (G-5)

**Checkpoint**: User Story 1 complete. Phone-cold-tap-to-rendered shows ratings + portfolio + cost in one view per US1 acceptance scenario 1. SC-008 (≤10s, target ≤5s) becomes measurable. **Independent of US4 — ships standalone.**

---

## Phase 4: User Story 2 — Watch debate live (Priority: P2)

**Goal**: Operator navigates to `/live` during a run, sees per-agent-stage transitions update via polling within ≤5s of engine writes (SC-009).

**Independent Test**: Trigger an ad-hoc run; navigate to `/live`; verify HTMX polling updates the visible agent-stage marker within 5 seconds of each `agent_started` / `agent_finished` event written to `events.jsonl`.

**Closes gaps**: G-8.

**Status**: Live page + HTMX polling already shipped (PRs #256 + #264). The remaining gap is FR-005 spec deviation (engine uses `BaseCallbackHandler` on `graph.invoke()` rather than `graph.astream()` per spec). This is a decision task — no behavioral change to the user-visible live page either way.

### Implementation for User Story 2

- [ ] T009 [US2] **Decision task — G-8 (FR-005)**: write `specs/250-dashboard-ui/amendments/fr-005-callback-handler.md` (creating the `amendments/` dir if it does not exist — first task to write there owns the dir creation). Documents the BaseCallbackHandler approach (PR #253 commit `50a8bdc` rationale: "smallest diff to trading_graph.py"). Operator decides amend vs refactor.
  - **If amend**: commit doc + redline FR-005 wording in `spec.md` to permit `BaseCallbackHandler`-style instrumentation.
  - **If refactor**: refactor `tradingagents/engine/runner.py::_real_run_ticker()` + `tradingagents/engine/callbacks.py::EngineEventCallback` to consume `graph.astream()` events; update `tests/test_engine_runner.py` + `tests/test_engine_callbacks.py` accordingly; verify all 53 engine tests still pass.

**Checkpoint**: FR-005 reconciled (either amended or refactored). Live page behavior unchanged for end users.

---

## Phase 5: User Story 3 — Read full debate per ticker per date (Priority: P2)

**Goal**: Operator opens `/ticker/{ticker}/{date}` and reads all 4 analyst reports + bull/bear debate + risk debate + trader + portfolio manager rationale.

**Independent Test**: Already validated — `tests/test_dashboard_app.py::test_ticker_detail_renders_debate` confirms full prose renders from a fixture state log.

**Status**: COMPLETE — no gaps from `plan.md` map to US3. Existing implementation at `app.py::ticker_detail` + `templates/ticker.html` satisfies acceptance scenarios 1 + 2.

---

## Phase 6: User Story 4 — Trigger an ad-hoc single-ticker run (Priority: P3)

**Goal**: Operator types a ticker into a small input field on the dashboard, hits "Run", engine spawns within 5 seconds, redirects to `/live`.

**Independent Test**: With engine idle, type `NVDA` in homepage input + click Run. Verify within 5 seconds: dashboard redirects to `/live`, `/live` shows `current_ticker=NVDA` with a starting agent stage. Verify invalid ticker (`FAKE123`) returns 400 client-side (HTML5 pattern) AND server-side (FR-011 regex/watchlist check). Verify concurrent trigger while engine busy returns 409 (FR-013).

**Closes gaps**: G-3, G-9, G-11.

### Tests for User Story 4

- [ ] T010 [US4] Add `test_home_includes_trigger_form` in `tests/test_dashboard_app.py` — GET `/` asserts presence of `id="trigger-form"`, `name="ticker"`, the FR-011 regex pattern, and the JS handler that POSTs to `/trading/trigger/{ticker}` (G-3)
- [ ] T011 [US4] Add `test_trigger_rejects_non_localhost_origin` in `tests/test_dashboard_app.py` — POST `/trigger/NVDA` with `client=("203.0.113.1", 12345)` returns 403; AND assert `client=("127.0.0.1", X)` AND default TestClient (`client.host = "testclient"`) BOTH still pass to the regex/watchlist check (FR-011 boundary preserved). (G-9)

### Implementation for User Story 4

- [ ] T012 [US4] Edit `tradingagents/dashboard/templates/home.html` — add the trigger form section (depends on T006 having landed first; same file). Text input with `pattern="^[A-Z]{1,5}(\.[A-Z]{1,2})?$"` + Run button + small `<script>` block that `fetch()`-POSTs to `/trading/trigger/{ticker}` and `window.location.href = '/trading/live'` on success, displays `body.detail` on error (G-3)
- [ ] T013 [US4] Edit `tradingagents/dashboard/app.py::trigger_ticker` — add app-level source-IP guard: inject FastAPI `Request`, return 403 if `request.client.host not in ("127.0.0.1", "::1", "testclient")`. The `"testclient"` entry preserves the existing 23 dashboard route tests that use FastAPI `TestClient` (which sets `client.host = "testclient"`); without it every existing trigger test breaks. Defense-in-depth alongside Quadlet `PublishPort=127.0.0.1:8000` + Caddy not proxying `/trigger/*` (G-9)
- [ ] T014 [US4] **Decision task — G-11 (FR-012)**: write `specs/250-dashboard-ui/amendments/fr-012-templated-unit.md` (or join the existing `amendments/` dir from T009). Documents the current `systemctl start tradingagents-engine-adhoc@{ticker}.service` approach. Operator decides amend vs refactor.
  - **If amend**: commit doc + redline FR-012 wording in `spec.md` to permit templated-unit pattern.
  - **If refactor**: change `tradingagents/dashboard/app.py::trigger_ticker` lines 220-235 to spawn via `systemd-run --user --unit=adhoc-{ticker}-{run_id}`. Generate `run_id` at trigger time (mirror `tradingagents/engine/runner.py::_generate_run_id`). Pass run_id into engine via `--setenv RUN_ID=...`. Add `test_trigger_unit_naming_per_fr012` in `tests/test_dashboard_app.py` asserting the spawn cmd matches `systemd-run --user --unit=adhoc-NVDA-<run_id>`.

**Checkpoint**: Operator can fully trigger an ad-hoc run from the homepage UI. Defense-in-depth source-IP guard active and TestClient-compatible. FR-012 unit-naming reconciled.

---

## Phase 7: User Story 5 — Inspect paper portfolio over time (Priority: P3)

**Goal**: Operator navigates to `/portfolio` and sees cash + open positions + recent events.

**Status**: COMPLETE — existing `app.py::portfolio` + `templates/portfolio.html` satisfies acceptance scenarios. US1 (Phase 3) adds an inline summary on `/`; the full view at `/portfolio` is unchanged.

**No tasks.**

---

## Phase 8: Polish & Cross-Cutting Concerns

**Closes gaps**: G-4, G-6, G-7, G-12.

### Constitution & Spec amendments

- [ ] T015 **Decision task — G-4 (FR-018 / Constitution IV)**: write `specs/250-dashboard-ui/amendments/fr-018-banner.md` (use existing `amendments/` dir if T009 or T014 created it). Documents the PR #257 banner removal. Operator decides:
  - **(a) Restore**: re-add "Simulation only — not financial advice" banner block in `tradingagents/dashboard/templates/base.html` matching the original FR-018 mandate; update `tests/test_dashboard_app.py::test_home_empty_state_when_no_runs` (and any other test that previously asserted banner absence) to require banner presence.
  - **(b) Amend**: PATCH-bump constitution v1.5.3 → v1.5.4 via `/speckit.constitution`; redline FR-018 in `specs/250-dashboard-ui/spec.md` to remove the banner mandate; flip Constitution Check row IV in `plan.md` from `❌` to `✅`.
- [ ] T016 **Decision task — G-7 (SC-006)**: write `specs/250-dashboard-ui/amendments/sc-006-mobile-wording.md`. PR #266 changed `phase-5-validation.md` from "real iOS Safari" to "any operator-used mobile browser" without spec amendment. Operator decides amend vs revert. Either way, execute the actual mobile validation per `phase-5-validation.md` Step 2 and record the result at `specs/250-dashboard-ui/sc-006-validation-result.md` (no LLM cost).

### Operational deployment hardening

- [ ] T017 Add systemd version-check precondition for FR-033: edit `deploy/README.md` install steps to include `systemctl --version | head -1 | awk '{print $2}'` ≥ 240 verification (recommended approach). Reference one-liner: `systemctl --version | head -1 | awk '{exit ($2 < 240)}'` exits non-zero on older systemd. Document the consequence (older systemd silently treats `OnCalendar=...America/New_York` as UTC — tasks would fire at 17:00 UTC = 13:00 ET in summer, 12:00 ET in winter, instead of 17:00 ET). (G-12)

### Validation gates (operator-executed)

- [ ] T018 **Operator validation gate — G-6 (SC-007)**: execute live $10 run on VPS — `sudo systemctl start tradingagents-engine-daily.service`, monitor `journalctl -u tradingagents-engine-daily.service -f` plus the live dashboard. Acceptance: cost meter ±5% of Anthropic console-reported spend; all 25 tickers either completed or failed; paper portfolio updates with new Buy/OW signals. Record actual cost + delta in `specs/250-dashboard-ui/sc-007-validation-result.md`.

---

## Dependencies

- **Phase 3 (US1)** is independent of Phase 4-7 — ships as standalone MVP PR with no dependency on US4 (T006 no longer carries a US4 placeholder)
- **Phase 4 (US2)** decision task (T009) is independent of all other phases
- **Phase 6 (US4)**:
  - T010, T011 (tests) independent of any Phase 3 task
  - T012 (trigger form in `home.html`) edits the same file as T006 (US1) — must rebase on US1 PR if US1 PR is open
  - T013, T014 independent of Phase 3
- **Phase 8** all four tasks independent of each other and of Phase 3-7 (T018 requires the entire dashboard deployed — already true on `main`)

## Parallel Execution

Within a single PR (different files = parallel-safe):

```text
T001 (test) || T005 (route)  || T007 (template base.html)            # US1 — three files
T010 (test) || T013 (route)  || T012 (template home.html)            # US4 — three files
T015 (amendment doc) || T016 (amendment doc) || T017 (deploy/README) # Phase 8 — three files
```

Within a same-file group (must serialize):

```text
T001 → T002 → T003 → T004 → T010 → T011  (all edit tests/test_dashboard_app.py)
T005 → T008 → T013                       (all edit tradingagents/dashboard/app.py)
T006 → T012                              (both edit tradingagents/dashboard/templates/home.html)
```

## Implementation Strategy

**MVP scope**: Phase 3 (US1) only — gives the operator a useful homepage today: ratings + portfolio + cost. 8 tasks (4 tests + 4 impl).

**Incremental delivery sequence**:

1. **PR-A (US1)**: T001-T008 — homepage shows ratings + portfolio + cost meter. Closes G-1, G-2, G-5. Operator can use the dashboard for daily review immediately.
2. **PR-B (US4 UI + IP guard)**: T010, T011, T012, T013 — trigger form + source-IP guard with `testclient` allowed for tests. Closes G-3, G-9.
3. **PR-C (G-11 decision)**: T014 — FR-012 amendment doc OR refactor. Closes G-11.
4. **PR-D (G-8 decision)**: T009 — FR-005 amendment doc OR refactor. Closes G-8.
5. **PR-E (Polish)**: T015, T016, T017 — Constitution IV decision + SC-006 wording + systemd version check. Closes G-4, G-7, G-12.
6. **PR-F (Validation)**: T018 — operator-executed live run, $10 spend authorized. Closes G-6.

Each PR ships independently. No self-merge — operator reviews and merges every PR (closes G-10 process commitment from `plan.md`).

## Format Validation

Confirmed: all 18 tasks follow `- [ ] T### [Story?] Description with file path` format. Story labels present on Phase 3-6 tasks. File paths included on every implementation task. Decision tasks (T009, T014, T015, T016) name the amendment doc location explicitly + name the redline target + name the refactor scope. Operator-gated tasks (T018) name the verification artifact location.

## Summary

- **Total tasks**: 18
- **Per story**: US1 = 8, US2 = 1, US3 = 0, US4 = 5, US5 = 0, Polish = 4
- **MVP**: Phase 3 (US1) — 8 tasks, 1 PR, gives operator a useful daily dashboard
- **Decision tasks (4)**: T009, T014, T015, T016 — each requires operator amend-or-refactor choice
- **Operator-gated (1)**: T018 — $10 LLM spend
- **Closes gaps**: G-1, G-2, G-3, G-4, G-5, G-6, G-7, G-8, G-9, G-11, G-12 (G-10 is process, no task)
