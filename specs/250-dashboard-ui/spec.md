# Feature Specification: TradingAgents Dashboard

**Feature Branch**: `250-dashboard-ui`
**Created**: 2026-05-10
**Cleaned**: 2026-05-12 (stripped unauthorized FRs/SCs that were not in the original ask)
**Status**: Reflects only what was actually requested.

## Overview

A polished web dashboard for the TradingAgents framework, accessible from a phone, hosted on the operator's existing Hetzner VPS. The dashboard surfaces today's run, the live agent debate, and the per-ticker debate archive. Replaces the deprecated CLI orchestrator (`scripts/run_daily.py`).

## What was actually asked for

The original request, in operator's own words: a live signal product with a polished web dashboard accessible from phone, deployed on the existing VPS infrastructure, surfacing the multi-agent debate that the framework already produces.

Everything below is a direct expansion of that request. Engineering details, validation gates, cost-meter scaffolding, banner mandates, browser-specific test requirements, and similar additions that earlier versions of this spec contained have been removed — they were not part of the ask.

## User Scenarios

### User Story 1 — Open the dashboard on phone, see today's results

The operator pulls up `https://rawcell.duckdns.org/trading/` on their phone and sees the framework's output for today: which tickers got which ratings (Buy / Overweight / Hold / Underweight / Sell), with the strongest commits at top.

### User Story 2 — Watch the agent debate live

When a run is in flight, the operator can navigate to a `/live` page and watch agent stages transition in real time as the engine processes each ticker.

### User Story 3 — Read the full debate for a specific ticker

The operator can drill into any past propagate at `/ticker/{TICKER}/{DATE}` and read all four analyst reports plus the bull/bear/risk debate plus the trader and portfolio manager rationale. The full ~400 KB of agent prose per propagate is reachable through the UI.

### User Story 4 — Trigger an ad-hoc single-ticker run from the dashboard

The operator can type a ticker into a small input field on the homepage, hit Run, and have the engine process that one ticker on demand.

### User Story 5 — See the paper portfolio

The operator can navigate to `/portfolio` and see the paper-trading harness state (cash, open positions, recent events).

## Requirements

### Functional

- **FR-1 — Pages**: The dashboard exposes pages for: today's run summary (`/`), live current-run viewer (`/live`), per-date ratings (`/tickers/{date}`), per-ticker debate detail (`/ticker/{ticker}/{date}`), paper portfolio (`/portfolio`), and an ad-hoc trigger (`POST /trigger/{ticker}`).
- **FR-2 — Mobile-first**: Phone-portrait layout is the primary design; tablet/desktop are responsive enhancements.
- **FR-3 — Live updates**: The live viewer updates without manual refresh while a run is in flight.
- **FR-4 — Hold renders as first-class**: Hold ratings render as a normal cell, not as empty or missing — Hold IS the framework's calibrated output when evidence is balanced (Constitution Principle VII).
- **FR-5 — Trigger validation**: The trigger endpoint validates the ticker (regex + watchlist membership) before spawning anything; invalid tickers are rejected without subprocess work.
- **FR-6 — Engine isolation**: Engine runs as a subprocess separate from the dashboard backend. Engine state is on disk; dashboard is read-only against it.
- **FR-7 — Daily run**: A scheduled timer fires the engine on the operator's working schedule (Mon–Fri 17:00 ET).
- **FR-8 — Paper-trade integration**: When a daily run completes, the resulting signals are applied to the paper portfolio (`paper_trade.py step`).

### Deployment

- **FR-9 — Reuse existing infrastructure**: Deploys to the existing VPS using the existing Caddy reverse proxy, existing Podman Quadlet container pattern, existing Duck DNS hostname (`rawcell.duckdns.org`), existing basic-auth user, existing Let's Encrypt cert. No new DNS, no new cert, no new auth user.
- **FR-10 — Path routing**: Lives at `rawcell.duckdns.org/trading/` (same hostname as other operator services, new path).

### State / contract

- **FR-11 — Engine writes; dashboard reads**: Engine writes `progress.json` (current-run snapshot) + `events.jsonl` (per-stage events) to a known location; dashboard reads them. Atomic writes so the dashboard never sees a partial JSON.

## Acceptance

The dashboard is acceptable when:
- The five user-story flows above all work end-to-end on the operator's actual phone.
- A daily run on the production schedule produces ratings that show up on the homepage.
- The paper portfolio reflects the latest run's signals.

## Out of Scope

- Token-by-token streaming of agent prose (per-stage updates are the granularity)
- Multi-tenant access — single operator behind basic-auth
- Real-money trading integration (paper-only, Constitution Principle IV)
- Notification delivery (email, Slack, push)

## Constitution Adherence

- **Principle IV (No Production Claims)**: paper-only — no real-money trading integration anywhere in the system.
- **Principle V (Steal Liberally)**: deployment infrastructure (Caddy / Quadlet / systemd-creds / basic-auth / Duck DNS) is reused from `agent-harness-v2` without rewrite.
- **Principle VII (Calibrated Abstention)**: Hold renders as first-class output, not as empty/missing.

## Dependencies

- Existing 12-agent LangGraph framework
- `paper_trade.py` state model (Spec 002)
- Existing `agent-harness-v2` deployment infrastructure on the VPS
