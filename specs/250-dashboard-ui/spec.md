# Feature Specification: TradingAgents Dashboard UI

**Feature Branch**: `250-dashboard-ui`
**Created**: 2026-05-10
**Status**: Draft
**Input**: User description: TradingAgents dashboard — mobile-first browser dashboard for the multi-agent debate framework, hosted on existing Hetzner VPS via Caddy + path-routed under existing Duck DNS hostname.

## Overview

The TradingAgents framework runs a 12-agent multi-agent debate per ticker (4 analysts → bull/bear → research manager → trader → 3-way risk debate → portfolio manager) producing ~400 KB of agent prose per propagate. Operators today have no way to read this prose during or after a run except by `cat`-ing JSON state-log files in a terminal. PR #248 attempted to surface this via a CLI orchestrator (`scripts/run_daily.py`) — that PR is being reverted as part of this spec because it hides the actual product (the debate prose) behind a one-line `→ rating: X` terminal output.

This spec defines the operator-facing dashboard that surfaces the agent debate, paper portfolio state, run progress, and cost meter as a mobile-first web UI hosted on the operator's existing Hetzner VPS infrastructure (Caddy reverse proxy + Duck DNS + Podman Quadlet containers, matching the existing agent-harness-v2 deployment pattern).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View today's run on phone (Priority: P1)

The operator wants to pull up their phone in the morning, open `https://rawcell.duckdns.org/trading/`, and immediately see what the framework decided for today: which tickers got Buy / Overweight ratings, which got Hold / Underweight / Sell, what the paper portfolio looks like, and how much LLM was spent.

**Why this priority**: This is the dominant use case. The whole point of the framework is generating actionable signals; if the operator can't see those signals on their phone with one URL load, the framework's research output is invisible to the daily workflow.

**Independent Test**: Open the URL on iOS Safari (real device, not Chrome devtools mobile preset). Without authenticating any further than the basic-auth credential the browser remembers, the homepage renders today's run summary within 2 seconds: ratings table, portfolio panel, cost meter, link to live current-run viewer if a run is in flight.

**Acceptance Scenarios**:

1. **Given** today's run completed at 5pm ET, **When** the operator opens the dashboard URL on phone at 8pm ET, **Then** the homepage shows the 25-ticker rating table sorted with bullish (Buy / Overweight) at top, paper portfolio open positions, and total cost spent today.
2. **Given** today's run is in flight (current ticker = NVDA, agent stage = bull_researcher), **When** the operator opens the dashboard, **Then** the homepage shows progress (X/25 done, current ticker NVDA, current stage Bull Researcher) plus the rating table for tickers already completed.
3. **Given** no runs have ever happened, **When** the operator opens the dashboard, **Then** the homepage shows an empty state ("No runs yet") with instructions for triggering the first run.

---

### User Story 2 - Watch the agent debate happen live (Priority: P2)

The operator wants to navigate to a `/live` page and watch the agent debate unfold in real time as it processes the watchlist — see Bull Researcher start writing for NVDA, finish, see Bear Researcher start, finish, watch the Risk Debate begin, etc. Per-agent-stage transitions visible with timestamps.

**Why this priority**: This is the differentiator from the deprecated CLI product. The CLI hid the debate; this exposes it. Watching the debate live is the operator's main mechanism for trusting (or distrusting) the framework's output.

**Independent Test**: With a run in flight, navigate to `/live`. The page shows the current ticker, current agent stage, and an event log of agent transitions for the in-progress ticker. The page polls and updates without manual refresh; new events appear within 5 seconds of being written by the engine.

**Acceptance Scenarios**:

1. **Given** the engine is processing NVDA and the Bull Researcher has just started, **When** the operator opens `/live` 10 seconds later, **Then** the page shows "NVDA — Bull Researcher started [timestamp]".
2. **Given** the Bull Researcher finishes and Bear Researcher starts, **When** the operator's open `/live` page polls (within 5 sec), **Then** new events appear: "Bull Researcher finished [timestamp] (8m 23s)" + "Bear Researcher started [timestamp]".
3. **Given** the operator is watching `/live` on cellular and the connection drops momentarily, **When** the connection restores, **Then** polling resumes and missed events appear in the next poll cycle.

---

### User Story 3 - Read the full debate for a specific ticker on a specific date (Priority: P2)

The operator wants to drill into a finished propagate — say, "show me everything the agents said about MSFT yesterday" — and read all 4 analyst reports + the bull vs bear debate + the risk debate + the trader's reasoning + the portfolio manager's final rationale.

**Why this priority**: The archive view is what makes the dashboard a reading product, not just a status display. ~400 KB of prose per propagate is wasted if the operator can't navigate it.

**Independent Test**: Navigate to `/ticker/MSFT/2026-05-08`. Page renders the complete debate with collapsible sections per agent stage. Bull case is readable. Bear case is readable. Filter audit trail visible (which filters fired, which downgrades happened).

**Acceptance Scenarios**:

1. **Given** MSFT was propagated yesterday with rating Hold and filter audit showing Spec 003 contrarian gate downgraded OW→Hold, **When** the operator opens `/ticker/MSFT/2026-05-08`, **Then** all sections render with the rating prominently displayed and the contrarian gate annotation visible in the filter audit section.
2. **Given** the operator wants to compare today's MSFT read to yesterday's, **When** they navigate to `/ticker/MSFT/2026-05-09`, **Then** the same view structure loads with that date's content.

---

### User Story 4 - Trigger an ad-hoc single-ticker run (Priority: P3)

The operator wants to type a ticker into a small input field on the dashboard, hit "Run", and have the engine process that one ticker on demand — without waiting for the next scheduled daily run.

**Why this priority**: Useful but secondary. Most operator value comes from reading the daily scheduled run. Ad-hoc triggering is for cases where the operator wants a fresh read on a specific name (e.g., earnings just released).

**Independent Test**: With the engine idle, type "NVDA" + click Run. Engine starts processing NVDA. The `/live` page shows progress. Cost meter ticks up by ~$0.40 when complete. The result appears in the homepage rating table for today's date.

**Acceptance Scenarios**:

1. **Given** the engine is idle, **When** the operator types "NVDA" + clicks Run, **Then** within 5 seconds the engine subprocess spawns and the `/live` page shows "NVDA — Market Analyst started".
2. **Given** the engine is busy processing the daily run, **When** the operator tries to trigger an ad-hoc run, **Then** the system returns an error explaining the engine is busy and shows the in-flight run's status.
3. **Given** the operator types an invalid ticker (e.g., "FAKE123" or "../../etc/passwd"), **When** they click Run, **Then** the system rejects the input with a validation error without spawning anything.

---

### User Story 5 - Inspect paper portfolio over time (Priority: P3)

The operator wants to see the paper portfolio's cumulative performance — open positions, closed positions, equity vs SPY, recent entries/exits.

**Why this priority**: Useful for tracking whether the framework's signals translate to portfolio gains; secondary to seeing the daily run.

**Independent Test**: Navigate to `/portfolio`. Page renders cash + open positions table + equity curve + recent events. Numbers match `~/.tradingagents/paper/<id>.json`.

**Acceptance Scenarios**:

1. **Given** the paper portfolio has 5 open positions and an equity curve with 30 data points, **When** the operator opens `/portfolio`, **Then** all 5 positions render with current marks + Δ% vs entry, equity sparkline displays, recent events list shows last 10.
2. **Given** position NVDA was opened 22 days ago and just hit its 21-day exit, **When** the operator opens `/portfolio`, **Then** NVDA appears in the recent events log as "EXIT NVDA → realized α +X%" and is no longer in the open positions table.

---

### Edge Cases

- **Engine crash mid-run**: heartbeat_at goes stale (>90 sec since last refresh) with no terminal event. Dashboard renders STALE banner on `/live`. Ad-hoc trigger remains usable to start a new run.
- **Empty state day 0**: No runs have ever been done. Homepage renders "No runs yet" with instructions for the first trigger.
- **Concurrent dashboard viewers**: operator on phone + operator on laptop both polling. Each gets the same data; no broadcast needed (read-only views).
- **Cellular connection drop on `/live`**: polling client retries on reconnect; missed events appear in next poll cycle.
- **Mid-write JSON read race**: prevented by Phase 0a PR #249 atomic `_log_state` write.
- **Malicious or malformed ticker in trigger input**: rejected by regex validation + watchlist-membership check before any subprocess spawns.
- **Concurrent triggers (operator clicks Run while engine busy)**: returns 409 Conflict; UI displays "Engine busy: processing <ticker>".
- **Hold rating display**: per Constitution Principle VII (Calibrated Abstention), Hold MUST display as a first-class rating, not as "no recommendation" or empty cell. Hold IS the calibrated output when evidence is balanced.

## Requirements *(mandatory)*

### Functional Requirements

#### Live-viewer fidelity

- **FR-001**: System MUST emit per-agent-stage heartbeat events ONLY (NOT token streaming). Each LangGraph agent NODE emits exactly one `agent_started` event on entry and one `agent_finished` event on exit. 12 `agent_started` + 12 `agent_finished` events per propagate.
- **FR-002**: System MUST NOT modify the existing `graph.invoke()` to support token-by-token streaming. Refactoring to `graph.astream_events()` with token-level callbacks is explicitly out of scope (would risk regressing the 1259-test suite + LangGraph behavior over Anthropic structured-output bind is uncertain).

#### Engine subprocess

- **FR-003**: System MUST run propagates in a separate engine subprocess from the dashboard backend. Engine writes state logs + heartbeat files to disk; dashboard reads. Read-only separation prevents the dashboard endpoint from triggering LLM spend.
- **FR-004**: System MUST acquire a file lock at `~/.tradingagents/engine/lock` before starting any run; concurrent runs MUST be prevented.
- **FR-005**: System MUST iterate the LangGraph via `graph.astream()` (NOT `graph.invoke()`) to receive per-node yields, and emit one `events.jsonl` line per node start + finish.
- **FR-006**: System MUST refresh the `progress.json` `heartbeat_at` field every 10 seconds during a run.
- **FR-007**: System MUST call `paper_trade.py step` after a daily run completes, applying the produced signals to the paper portfolio.
- **FR-008**: System MUST support a `--dry-run` mode that emits fake events (no LLM calls) for end-to-end dashboard validation without LLM cost.

#### Dashboard backend

- **FR-009**: System MUST expose HTTP routes: `GET /` (today's summary), `GET /live` (current-run viewer), `GET /tickers/{date}` (ratings table for a date), `GET /ticker/{ticker}/{date}` (full debate), `GET /portfolio` (paper portfolio panel), `GET /api/poll` (state polling endpoint for live updates), `POST /trigger/{ticker}` (ad-hoc run trigger).
- **FR-010**: System MUST bind the dashboard backend to `127.0.0.1` only; the reverse proxy MUST proxy `GET /` and `GET /api/*` but MUST NOT proxy `POST /trigger/*` (firewall pattern: trigger reachable only from the VPS itself).
- **FR-011**: `POST /trigger/{ticker}` MUST validate ticker against regex `^[A-Z]{1,5}(\.[A-Z]{1,2})?$` AND verify membership in the current watchlist file before spawning anything. Invalid tickers MUST return 400 without subprocess spawn.
- **FR-012** *(amended 2026-05-11 per `amendments/fr-012-templated-unit.md`)*: `POST /trigger/{ticker}` MUST spawn the engine via systemd (NOT `subprocess.Popen` directly), as either: (a) `systemd-run --user --unit=adhoc-{ticker}-{run_id}` (transient unit per run), OR (b) `systemctl start tradingagents-engine-adhoc@{ticker}.service` (templated-instance unit per ticker). Either pattern MUST decouple engine lifetime from dashboard restarts and MUST NOT inherit the dashboard's file descriptors. The templated-instance pattern (b) additionally provides anti-duplicate safety at the systemd layer (a second trigger of the same ticker is a no-op while the first run is active), complementing the engine-lock 409 from FR-013.
- **FR-013**: `POST /trigger/{ticker}` MUST return 409 Conflict if the engine lock is held by another run.
- **FR-014**: `GET /api/poll` MUST return current `progress.json` + recent `events.jsonl` lines (since a `last_event_id` query param if provided) so the live page can update incrementally without a full reload.

#### Frontend

- **FR-015**: Frontend MUST be mobile-first: phone-portrait layout is the primary design; tablet/desktop are responsive enhancements.
- **FR-016**: Live debate viewer MUST update via polling (NOT Server-Sent Events). Polling interval: 2-3 seconds when run is active; 30-60 seconds when idle. Validated through the same Caddy reverse proxy as agent-harness-v2's existing dashboard.
- **FR-017**: All pages MUST render Hold ratings as first-class output, NOT as empty cells or missing recommendations.
- **FR-018** *(amended 2026-05-11 per `amendments/fr-018-sc-006-banner-and-mobile.md`)*: No banner mandate. The dashboard is a single-operator surface gated by Caddy basic-auth; the "Simulation only — not financial advice" banner serves no protective function for the actual user. Constitution Principle IV remains satisfied by the paper-only architecture (no real-money trading integration; FR-007 paper_trade.py is the only signal consumer).
- **FR-019**: Cost meter MUST display cumulative LLM spend for today's run, visible in the page header on every route.

#### Schemas (pinned in spec)

- **FR-020**: `progress.json` schema is FIXED. Fields:

  | Field | Type | Description |
  |---|---|---|
  | `run_id` | string | `<ISO date>T<HHMMSS>Z` UTC; generated when engine starts |
  | `started_at` | ISO 8601 UTC | When this run began |
  | `trade_date` | ISO date | America/New_York calendar date the run is FOR |
  | `watchlist` | array of tickers | The tickers being processed this run |
  | `current_ticker` | string \| null | Currently propagating ticker; null when between tickers |
  | `current_ticker_started_at` | ISO 8601 UTC \| null | When the current ticker started |
  | `current_agent_stage` | enum \| null | Currently-running agent stage (see FR-022 enum) |
  | `completed_tickers` | array of `{ticker, rating, completed_at}` | Done so far |
  | `failed_tickers` | array of `{ticker, error, failed_at}` | Errored tickers this run |
  | `cost_so_far_usd` | float | Cumulative LLM cost for this run |
  | `heartbeat_at` | ISO 8601 UTC | Refreshed every 10 sec; 60-sec TTL; >90 sec = STALE |

- **FR-021**: `events.jsonl` schema is FIXED. Each line is a JSON object with fields:

  | Field | Type | Description |
  |---|---|---|
  | `ts` | ISO 8601 UTC | Event timestamp |
  | `run_id` | string | Owning run |
  | `ticker` | string \| null | Owning ticker (null for run-level events) |
  | `agent_stage` | enum \| null | (see FR-022) |
  | `event_type` | enum | (see FR-023) |
  | `payload` | object | Event-type-specific data |

- **FR-022**: `agent_stage` enum is FIXED at: `market_analyst`, `news_analyst`, `social_analyst`, `fundamentals_analyst`, `bull_researcher`, `bear_researcher`, `research_manager`, `trader`, `aggressive_risk`, `conservative_risk`, `neutral_risk`, `portfolio_manager`.
- **FR-023**: `event_type` enum is FIXED at: `run_started`, `ticker_started`, `agent_started`, `agent_finished`, `ticker_finished`, `ticker_failed`, `cost_delta`, `error`, `run_finished`.

#### Semantics

- **FR-024**: `run_id` is generated when the engine process starts; format `<ISO date>T<HHMMSS>Z` UTC. Each run gets a unique `run_id`.
- **FR-025**: `trade_date` is the America/New_York calendar date the run is FOR (not when the run was kicked off). The daily-scheduled run at 5pm ET on Mon 2026-05-11 has `trade_date = 2026-05-11`. An ad-hoc trigger fired at 11pm ET on Mon 2026-05-11 ALSO has `trade_date = 2026-05-11` (same business day) but a new `run_id`.
- **FR-026**: Ad-hoc triggers MUST NOT join an in-flight run. Each trigger creates a new run with new `run_id`; concurrent runs are blocked by the engine lock (FR-004).
- **FR-027**: Heartbeat TTL is 60 seconds. If `heartbeat_at` is older than 90 seconds AND no `run_finished`/`ticker_failed` terminal event has been emitted, the dashboard MUST render the run as STALE.

#### Deployment

- **FR-028**: Dashboard MUST be deployed as a Podman Quadlet rootful container under system systemd, matching the existing agent-harness-v2 pattern. Container file at `deploy/tradingagents-dashboard.container`.
- **FR-029**: Reverse proxy configuration MUST extend the existing Caddyfile with a new `handle_path /trading/*` block. This MUST NOT be a fresh Caddyfile — it adds to the existing one that already serves agent-harness-v2.
- **FR-030**: TLS MUST reuse the existing Let's Encrypt certificate Caddy already manages for `rawcell.duckdns.org`. No new certificate provisioning.
- **FR-031**: Auth MUST reuse the existing Caddy basic-auth `rawcell` user/credential pattern. No new auth credential.
- **FR-032**: DNS uses the path `rawcell.duckdns.org/trading/` — no new DNS record. The existing Duck DNS subdomain handles it.
- **FR-033**: Engine MUST be scheduled by a systemd timer with `OnCalendar=Mon..Fri 17:00 America/New_York`. Implementation MUST verify systemd version ≥240 (older versions silently treat the timezone as UTC).

### Key Entities

- **Run**: One execution of the engine over a watchlist (or a single ticker for ad-hoc). Identified by `run_id`. Owns a `progress.json` file + an `events.jsonl` file.
- **Trade Date**: ISO date in America/New_York calendar — the date the run is FOR. Multiple Runs can share the same Trade Date (e.g., scheduled run + ad-hoc trigger same day).
- **Ticker**: A stock symbol (e.g., NVDA, AAPL) being propagated. Validated via regex `^[A-Z]{1,5}(\.[A-Z]{1,2})?$` + watchlist membership.
- **Agent Stage**: One of the 12 LangGraph nodes (analysts, debate, risk, PM). Each stage emits a heartbeat event on start + finish.
- **Event**: A `events.jsonl` line. Owns timestamps, run_id, ticker (nullable), agent_stage (nullable), event_type, payload.
- **Paper Portfolio**: Persistent state at `~/.tradingagents/paper/<id>.json` + `<id>.events.jsonl`, owned by Spec 002 paper-trading harness. Dashboard reads only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Schema contract — engine writes match dashboard expectations. Verified by contract tests in `tests/test_engine_contracts.py` with fixture `progress.json` + `events.jsonl` files. All test cases pass.
- **SC-002**: Atomic state-log writes — dashboard tailer never observes partial JSON. Verified by Phase 0a PR #249 atomic `_log_state` write; dashboard implementation relies on this invariant.
- **SC-003**: Trigger endpoint safety — invalid tickers (regex fail OR not in watchlist) return 400 without spawning subprocess; valid tickers spawn via `systemd-run`; concurrent triggers return 409 if engine lock held.
- **SC-004**: Empty state — `GET /` on day 0 (no runs ever happened) returns "No runs yet" page with trigger instructions; does not error or render blank.
- **SC-005**: Engine crash recovery — if `heartbeat_at` is older than 90 sec AND no terminal event, dashboard renders STALE banner; ad-hoc trigger remains usable to start a new run.
- **SC-006** *(amended 2026-05-11 per `amendments/fr-018-sc-006-banner-and-mobile.md`)*: Mobile responsive — the dashboard renders correctly on the operator's actual mobile browser (any modern phone browser; the operator does not use iOS). Polling works over cellular; layout is usable in phone-portrait orientation. Validation is performed by the operator on their own device once per spec change that touches the mobile layout.
- **SC-007**: End-to-end smoke — dry-run mode (engine emits fake events without LLM calls per FR-008) validates dashboard renders correctly before live $10 run; live run produces ratings + portfolio updates + cost meter accuracy within ±5% of actual Anthropic billing.
- **SC-008**: Operator can pull up phone, view today's ratings + portfolio + cost in under 10 seconds from cold-tap-on-URL to fully-rendered page (target: under 5 seconds; ceiling: under 10).
- **SC-009**: When a run is in flight, the live debate viewer updates with new agent-stage events within 5 seconds of the engine writing them.

## Assumptions

- **Existing infrastructure assumed**: Hetzner CPX31 VPS with Ubuntu 24.04, Caddy ≥2.x installed and running, Podman with Quadlet support enabled, systemd ≥240, existing Duck DNS hostname `rawcell.duckdns.org` resolving to the VPS, existing basic-auth `rawcell` user already configured in Caddyfile for the parent domain.
- **No new DNS, no new certificate, no new auth user**: this spec REUSES every existing pattern from agent-harness-v2.
- **PR #248 will be reverted**: `scripts/run_daily.py` + `docs/LIVE_SIGNALS_PRODUCT.md` + the README "Live signals product" front-section block are removed before or during Phase 1 implementation.
- **Single-user**: only the operator accesses the dashboard. No multi-tenant, no shared accounts, no role-based access.
- **No real-money**: paper-only per Constitution Principle IV. The dashboard MUST display the "Simulation only — not financial advice" banner.
- **Token-streaming refactor is out of scope**: per FR-002, the dashboard works with the existing post-completion `_log_state` writes + per-node `graph.astream()` yields. True token streaming would be a separate spec.
- **Live-viewer fidelity is per-agent-stage heartbeat ONLY**: 12 events per propagate (one start + one finish per agent NODE). Operators see "Bull Researcher started [timestamp]... finished [timestamp] (8m 23s)" — not token-by-token agent prose.
- **Polling not SSE**: agent-harness-v2 already validated polling works through Caddy at this scale. Polling eliminates SSE buffering, reverse-proxy compression, and `Last-Event-ID` reconnect concerns.
- **Cost basis**: ~$10/day LLM at the default 25-ticker watchlist (Opus + Haiku per propagate). Implementation includes Anthropic-client instrumentation for the cost meter (per-call token counts → cumulative $ → emitted as `cost_delta` events).
- **Constitution III T2 classification per phase**: build = T0 (no LLM cost); end-to-end live smoke = T2 (~$10).

## Out of Scope

- Token streaming (per-token agent prose in the live viewer)
- Multi-tenant / shared user accounts
- Real-money trading integration
- Notification delivery (email / Slack / push)
- In-UI watchlist editing (file-based for v1)
- In-UI per-bot model swap (config-file only for v1)
- Background scheduler other than the daily systemd timer
- Mobile native app (iOS / Android — this is a web app accessed via mobile browser)
- Sharing the dashboard URL with other people (single-user, basic-auth gated)
- Dashboard-triggered changes to filter configuration
- Cost-budget caps (operator must monitor cost meter manually)

## Constitution Adherence

- **Principle IV (No Production Claims)**: paper-only — no real-money trading integration anywhere in the system. The previous banner mandate (original FR-018) was dropped 2026-05-11 because a single-operator basic-auth-gated dashboard does not need an audience-facing disclaimer. The protective invariant (paper-only, no real broker integration) is preserved by the architecture itself.
- **Principle VI (Spec Before Structural Change)**: this spec IS the structural-change discipline; new module + new deploy surface + new operator interface.
- **Principle VII (Calibrated Abstention is a Valid Output)**: dashboard MUST display Hold gracefully — Hold IS the calibrated output, not absent recommendation. (FR-017)

## Dependencies

- Existing 12-agent LangGraph framework (`tradingagents/graph/`)
- All 10 production filters (A3 / Spec 003 / 003.5 / 004 / 006 / 007 / 008 / X-1 / 012)
- `paper_trade.py` state model (Spec 002 paper-trading harness)
- Atomic `_log_state` write from PR #249 (Phase 0a) — required for SC-002
- Existing agent-harness-v2 deploy infra: Caddy, Podman Quadlet, Duck DNS, basic-auth user
