# Amendment: FR-012 — Permit templated-unit spawn pattern

**Spec**: 250-dashboard-ui
**Gap**: G-11 (per `plan.md`)
**Task**: T014 (per `tasks.md`)
**Date**: 2026-05-11
**Status**: Proposed — operator decides amend vs refactor by merging or rejecting this PR

## Original FR-012 wording

> **FR-012**: `POST /trigger/{ticker}` MUST spawn the engine via `systemd-run --user --unit=adhoc-{ticker}-{run_id}` (NOT `subprocess.Popen`). This prevents inheriting the dashboard's file descriptors and decouples engine lifetime from dashboard restarts.

## What we actually shipped (PR #256)

`tradingagents/dashboard/app.py::trigger_ticker` (current `lines 220-258`) spawns via:

```python
unit_name = f"tradingagents-engine-adhoc@{ticker}"
cmd = ["systemctl", "start", f"{unit_name}.service"]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
```

The named unit `tradingagents-engine-adhoc@.service` is a templated systemd unit installed at `/etc/systemd/system/tradingagents-engine-adhoc@.service` (per `deploy/systemd/`). The `@<ticker>` instance is created on demand by `systemctl start`.

## Functional comparison

| Property | Spec FR-012 (`systemd-run --user --unit=adhoc-{ticker}-{run_id}`) | Shipped (`systemctl start tradingagents-engine-adhoc@{ticker}.service`) |
|---|---|---|
| Decouples engine lifetime from dashboard restarts | ✓ (separate systemd transient unit) | ✓ (separate systemd templated-instance unit) |
| Doesn't inherit dashboard file descriptors | ✓ (systemd-run forks clean) | ✓ (systemctl start forks clean via systemd) |
| Engine runs as `agent` user | ✓ (`--user`) | ✓ (unit declares `User=agent`) |
| Engine inherits `LoadCredentialEncrypted=` for API keys | ⚠️ requires `--setenv` plumbing | ✓ (declared in the unit file) |
| Per-run unique unit name (run_id in unit) | ✓ | ✗ (one unit per ticker; serially reused across runs) |
| Concurrent runs of the same ticker | ✓ (each gets unique unit) | ✗ (second `systemctl start` is a no-op while first is active) |
| Engine lock at `~/.tradingagents/engine/lock` (FR-004) blocks concurrent runs anyway | n/a — different concern | n/a — different concern |
| Operator can `journalctl -u <unit>` per run | ✓ (per-run unit) | ⚠ (per-ticker unit; runs interleave in journal) |
| Operator can `systemctl status <unit>` per run | ✓ | ⚠ (only the most recent run is queryable by unit name) |
| Anti-duplicate-spend safety | ✗ (concurrent same-ticker runs allowed; only the dashboard 409 from FR-013 prevents) | ✓ (templated unit is a singleton per ticker; second trigger is a no-op until first finishes) |

## Recommendation: AMEND, not refactor

**Three reasons to amend** (accept the templated-unit pattern):

1. **All spec invariants are met.** FR-012's stated guarantees (no FD inheritance + lifetime decoupling) hold for both patterns. The unit-naming pattern was a means; the listed properties were the ends.
2. **Templated-unit pattern adds anti-duplicate safety as a side effect.** A repeated trigger of the same ticker is a no-op while the first run is active — a useful safety property for an LLM-spend-bearing endpoint that the spec didn't explicitly call out. The dashboard's FR-013 409-on-lock-held check is a separate (broader) safeguard at the engine layer; the per-ticker unit is a tighter check at the systemd layer. Defense-in-depth.
3. **API-key credential plumbing is already declarative in the unit file.** The unit ships with `LoadCredentialEncrypted=anthropic-key:/etc/credstore/anthropic-key.encrypted` etc. (per `deploy/systemd/tradingagents-engine-adhoc@.service`). Re-implementing this via `--setenv` on every `systemd-run` invocation is duplicative + bug-prone.

**The single tradeoff**: per-run journalctl/status queries are coarser. Operator must filter by run_id from `events.jsonl` rather than `journalctl -u <unit-with-run-id>`. Acceptable — the engine already emits run_id-tagged events as the source of truth (FR-021).

## Proposed FR-012 redline (in `spec.md`)

```diff
-- **FR-012**: `POST /trigger/{ticker}` MUST spawn the engine via `systemd-run --user --unit=adhoc-{ticker}-{run_id}` (NOT `subprocess.Popen`). This prevents inheriting the dashboard's file descriptors and decouples engine lifetime from dashboard restarts.
++ **FR-012**: `POST /trigger/{ticker}` MUST spawn the engine via systemd (NOT `subprocess.Popen` directly), as either:
++   (a) `systemd-run --user --unit=adhoc-{ticker}-{run_id}` (transient unit per run), OR
++   (b) `systemctl start tradingagents-engine-adhoc@{ticker}.service` (templated-instance unit per ticker).
++ Either pattern MUST decouple engine lifetime from dashboard restarts and MUST NOT inherit the dashboard's file descriptors. The templated-instance pattern (b) additionally provides anti-duplicate safety at the systemd layer (a second trigger of the same ticker is a no-op while the first run is active), complementing the engine-lock 409 from FR-013.
```

## Alternative: refactor path (if amendment is rejected)

If the operator decides to ship the spec-literal `systemd-run --user --unit=adhoc-{ticker}-{run_id}` pattern instead:

1. Edit `tradingagents/dashboard/app.py::trigger_ticker` to:
   - Generate `run_id` at trigger time (mirror `tradingagents/engine/runner.py::_generate_run_id`)
   - Pass run_id into the engine via `--setenv RUN_ID=<run_id>`
   - Spawn `systemd-run --user --unit=adhoc-{ticker}-{run_id} ...` with full credential plumbing via `--load-credential=`
2. Update `EngineRunner` to read `RUN_ID` from env and use it instead of generating one
3. Add `test_trigger_unit_naming_per_fr012` in `tests/test_dashboard_app.py` asserting the spawn cmd matches `systemd-run --user --unit=adhoc-NVDA-<ISO-timestamp>`
4. Decide whether to remove the templated unit file from `deploy/systemd/` (cleanup) or keep it for the daily-timer use case

Estimated effort: ~2 hours of code + tests. No functional advantage over the templated pattern.

## Operator decision

- **Merge this PR** = accept amendment. FR-012 is updated in `spec.md`. Plan.md G-11 row marked closed. Constitution Check unaffected (FR-012 is not a Constitution principle).
- **Reject this PR + reply "refactor"** = pursue alternative path above. This amendment doc gets deleted; new PR ships the systemd-run refactor.
