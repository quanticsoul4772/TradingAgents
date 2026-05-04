# Hypothesis: phase-0-cache-smoke

**Experiment ID**: `2026-05-04-006-phase-0-cache-smoke`
**Created**: 2026-05-04
**Source idea**: Spec 002 Phase 0 end-to-end validation — single propagation to verify cache populates from real route_to_vendor calls
**Cost estimate**: ~$2.00
**Cost tier**: T1 (free exploration, $0 – $5)

## What we're testing

End-to-end validation of the spec 002 Phase 0 changes shipped in commit `73a4484`:
1. **`propagate_context` correctly wraps execution** — when `propagate(ticker, date)` runs, the context is set
2. **`route_to_vendor` writes to cache during real tool calls** — every analyst tool call inside the propagate produces a cache row
3. **`bootstrap_initial_signals` runs and registers the 17 production signals** — registry.jsonl contains all expected entries
4. **No production behavior change** — the propagate completes normally, returns a rating, and existing memory log + state log writes are unaffected

NVDA on 2026-01-30 (matches the Phase C smoke test from 005 for direct comparison). Single propagation, default config (no second_opinion overhead).

## Why we expect a clean smoke

Pre-conditions are favorable:
- Phase 0 logic was unit-tested with mocked dispatch (31 tests passing); the integration risk is in the wiring, not the logic
- Cache writes are explicitly designed to fail-and-swallow (per FR-014); even a worst-case cache failure leaves the propagate intact
- Bootstrap is idempotent; no behavior change if registry already populated

## Predicted findings

**Scenario A (clean smoke)** — ~80%
- Propagate completes 1/1 with 0 errors
- Cache (`~/.tradingagents/signals/cache.db`) has ≥10 rows after the run (signal_id × NVDA × 2026-01-30)
- Registry (`~/.tradingagents/signals/registry.jsonl`) contains 17 entries with state=production
- Existing state log + memory log writes still work

**Scenario B (cache writes some but not all signals)** — ~10%
- Propagate completes; some signals show in cache but not all 17
- Means the LLM didn't choose to call every wired tool (which is expected — analysts pick subsets)
- Still validates the wiring; documents what the LLM actually called on this ticker/date

**Scenario C (cache empty despite propagate running)** — ~5%
- propagate_context not actually entered, OR route_to_vendor's hook is broken in production
- Need to debug the wiring

**Scenario D (propagate breaks because of Phase 0 changes)** — ~5%
- Bootstrap or propagate_context throws and breaks the existing flow
- The fail-and-swallow guards should prevent this, but worth verifying

## Success criterion

- [ ] 1 propagation completes with 0 errors
- [ ] `~/.tradingagents/signals/cache.db` exists and has ≥1 row for (signal_id, "NVDA", "2026-01-30")
- [ ] `~/.tradingagents/signals/registry.jsonl` exists and contains all 17 signal_ids
- [ ] Existing state log under `~/.tradingagents/logs/NVDA/` is created as before
- [ ] PM rating extracted normally from the run
- [ ] Total cost ≤ $3

## Notes

- **T1 tier** ($2 estimated, well within ≤$5 ceiling)
- **Single date single ticker** (NVDA 2026-01-30) — minimum viable smoke
- **Default config** — no second_opinion, no A3 filter override (keep the test focused on Phase 0 only)
- **Memory log fresh** if needed; state log is per-date so won't conflict with prior runs
- Comparable to 005 (Phase C smoke) — this is the Phase 0 equivalent

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (clean smoke) | Phase 0 confirmed end-to-end. RESEARCH_FINDINGS gets a "Phase 0 validated" note. Phase 1 (evaluation harness) ready to build with confidence the cache works. |
| Scenario B (partial cache population) | Validate the wiring as correct; document which tools the LLM actually called. Phase 1 still ready to build. |
| Scenario C (cache empty) | Debug the wiring. Most likely culprit: propagate_context not entered, or import-time issue with the cache hook. Fix and re-smoke. |
| Scenario D (propagate breaks) | Revert the Phase 0 wiring changes, keep just the standalone signals/ package. Re-design integration. |

## Related experiments

- **Commit `73a4484`**: Phase 0 shipped — `tradingagents/signals/` + 31 unit tests + PM-pipeline wiring
- **2026-05-04-005-phase-c-smoke-test**: structurally identical smoke pattern for Phase C
- **Spec 002 SC-001**: this smoke test is a direct check on "All 18 currently-wired signals registered with state=production. After 5 backtest propagates, the cache contains values for ≥18×5=90 (signal, ticker, date) tuples." We're checking 1 propagate, not 5; partial validation.
