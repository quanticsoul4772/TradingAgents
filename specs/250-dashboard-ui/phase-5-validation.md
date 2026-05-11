# Phase 5 Validation Runbook (spec 250-dashboard-ui SC-006 + SC-007)

> Closing the spec. End-to-end gate before Monday's first scheduled live run.

## Pre-conditions

- Phases 0a, 0b, 1, 1b, 1c, 2, 3, 4 all merged + deployed (per CHANGELOG entries through PR #264).
- Dashboard container `tradingagents-dashboard.service` active on the VPS.
- `tradingagents-engine-daily.timer` enabled + scheduled.
- Engine `.venv` installed at `/home/agent/tradingagents/.venv`.

## Step 1 — Automated smoke (`scripts/dashboard_smoke.sh`)

Runs the engine in `--dry-run` mode (zero LLM cost) then probes every dashboard route. Exit 0 = pass. Run on the VPS:

```bash
ssh agent@rawcell.duckdns.org
cd /home/agent/tradingagents
ENGINE_PYTHON=/home/agent/tradingagents/.venv/bin/python ./scripts/dashboard_smoke.sh
```

Expected output:

```
==> Phase 5 smoke validation (spec 250-dashboard-ui SC-007)
✓ /health: ... → 200
✓ engine dry-run completed for NVDA
✓ /api/poll: ... → 200
✓ /api/poll has progress
✓ / shows ticker
✓ /live has HTMX hx-get
✓ /live has 3-sec trigger
✓ trigger /badticker → 400 (regex/watchlist rejection)
✓ ALL CHECKS PASSED
```

Validates:
- SC-001: schema contract (progress.json + events.jsonl readable)
- SC-003: trigger endpoint safety (invalid ticker → 400)
- SC-004: empty-state path (404 on missing ticker debate)
- FR-008: dry-run mode emits events without LLM cost
- FR-016: HTMX polling wired on /live

## Step 2 — SC-006 mobile responsive on real iOS Safari

**Required**: real iOS device, not Chrome devtools mobile preset. iOS Safari handles `<details>` elements + HTMX differently than Chromium emulation.

1. Open `https://rawcell.duckdns.org/trading/` on iPhone Safari
2. Authenticate with `rawcell` basic_auth credential
3. Verify each:
   - [ ] Homepage renders the rating table; ticker links are tappable
   - [ ] Tap a ticker → ticker page renders
   - [ ] On the ticker page, tap "▶ BULL VS BEAR DEBATE" → details element expands; full prose visible
   - [ ] Tap the back/Today button → returns to homepage
   - [ ] Navigate to /live → page renders; check after ~5 sec the "last poll HH:MM:SS UTC" footer increments (HTMX is polling)
   - [ ] Pull-to-refresh works
4. Verify on cellular (turn off WiFi):
   - [ ] /live polling continues
   - [ ] HTMX recovers from brief connectivity drops

If any item fails: file specific bug + investigate.

## Step 3 — Live $10 run validation (SC-007)

**Cost: ~$10 LLM (Anthropic Opus + Haiku across 25-ticker watchlist).**

```bash
sudo systemctl start tradingagents-engine-daily.service
journalctl -u tradingagents-engine-daily.service -f
```

While running, on phone:
- [ ] /trading/live shows current ticker + agent stage updating every ~3 sec
- [ ] /trading/ ticker count increments as completions roll in
- [ ] Cost meter ticks up; matches order of magnitude expected per propagate (~$0.40 each)

After completion (~3-4 hours):
- [ ] Final cost on dashboard within ±5% of Anthropic console-reported spend (SC-007 acceptance)
- [ ] All 25 tickers either in completed or failed bucket
- [ ] Paper portfolio updated (open positions reflect new Buy/OW signals)

## Step 4 — Pass-fail decision

| Outcome | Verdict | Action |
|---|---|---|
| Steps 1+2+3 all green | **PASS** — spec 250 closed | Update spec status: Draft → Ratified |
| Step 1 fails | **BLOCK** — investigate + fix before live spend | |
| Step 2 fails | **PARTIAL** — desktop OK, mobile bug | File bug + ship fix |
| Step 3 cost meter outside ±5% | **PARTIAL** — re-tune Anthropic pricing table | PR with corrected rates |
| Step 3 dashboard breaks during live run | **FAIL** — full investigation | |

## Cost summary

- Step 1: $0 (dry-run only)
- Step 2: $0 (no engine activity, just navigation)
- Step 3: ~$10 (one full 25-ticker live run)

## Cross-references

- Spec: [`specs/250-dashboard-ui/spec.md`](spec.md)
- Smoke script: [`scripts/dashboard_smoke.sh`](../../scripts/dashboard_smoke.sh)
- Deploy README: [`deploy/README.md`](../../deploy/README.md)
