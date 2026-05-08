# Quickstart: C-4 Institutional Rotation Filter (Spec X-1)

**Branch**: `091-c4-institutional-rotation` | **Date**: 2026-05-07

## What this filter does

Suppresses Underweight/Sell commits to Hold when top 10 institutional
holders' net pctChange rotation falls below a configurable outflow
threshold (default -5%). Detects the "post-hoc bear chase" pattern
where institutions have already sold and the bear thesis is
post-priced-in.

**Empirical justification**:

- PR #75 standalone retrospective: bear-side n=12, +5.41pp net Δα,
  +10.29pp discrim, 75.0% hit rate at T_outflow=0.05
- PR #77 additive overlap: union vs Spec 007 bear shadow improves
  net Δα by +8.06pp + hit rate by +69.23pp; C-4 catches 11 bearish
  commits Spec 007 entirely misses

**Mechanism class distinction**: Spec 007 bear is LLM-extracted
semantic reasoning over analyst+debate text; C-4 is institutional
ownership rotation (quantitative 13F flow). LITERALLY different
signal sources.

## Default configuration

After this spec is implemented, the framework's defaults will be:

```python
# tradingagents/default_config.py
DEFAULT_CONFIG = {
    # ... existing entries ...
    "institutional_rotation_bear_mode": "shadow",  # default-shadow per VIII v1.4.0
    "institutional_rotation_bull_mode": "off",  # n=1 evidence too thin
    "institutional_rotation_outflow_threshold": 0.05,
    "institutional_rotation_inflow_threshold": 0.05,  # reserved for future bull-side
}
```

In shadow mode, the filter measures `would_fire_bear` decisions but
does NOT mutate ratings. Operators observe the filter's behavior in
their workflow before flipping to active mode (per SC-010 live-mode
ablation requirement).

## Operator opt-in to active mode

Edit your experiment's `PARAMS.json` (or pass via CLI override):

```json
{
  "institutional_rotation_bear_mode": "active",
  "institutional_rotation_outflow_threshold": 0.05
}
```

Operators MAY also tune the threshold (e.g., `0.03` for tighter
suppression or `0.08` for looser); recommended to keep at `0.05`
to match the empirical evidence base.

## Operator opt-out

To fully disable C-4 (zero overhead, no yfinance fetches):

```json
{
  "institutional_rotation_bear_mode": "off",
  "institutional_rotation_bull_mode": "off"
}
```

When both modes are off, the helper module is not invoked, no yfinance
calls are made, and no annotation fields appear in state logs (FR-011
backward-compatibility guarantee).

## Auditing fire decisions

State logs at `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json`
will contain (when mode != off):

```json
{
  "forward_catalyst": {
    "...": "...other Spec 007 fields...",
    "institutional_rotation": {
      "net_rotation_pct": -0.0823,
      "outflow_threshold": 0.05,
      "bear_mode": "shadow",
      "bull_mode": "off",
      "would_fire_bear": true,
      "fired_bear": false,
      "pre_rating": "Underweight",
      "post_rating": "Underweight"
    }
  }
}
```

To survey all behavioral-additive fires post-deployment:

```bash
python scripts/behavioral_additive_sweep.py
```

(Per the post-v1.4.6-ratification refresh in PR #85, this script will
naturally pick up C-4 behavioral-additive cases once Spec X-1 is
deployed and accumulates state logs with the new annotation field.)

## Re-validating the empirical evidence

After Q1 2026 13Fs land (~2026-05-15), re-run the retrospectives to
verify both Constitution VIII gates still pass on refreshed data:

```bash
# Standalone gate
python scripts/forward_catalyst_class4_retrospective.py --cohort-cutoff 2026-05-15

# Additive overlap gate
python scripts/forward_catalyst_class4_vs_spec007_overlap.py
```

Per SC-009: if either gate drops below the v1.4.0 / v1.4.3 thresholds
on refreshed data, ablate `institutional_rotation_bear_mode` to "off"
default pending further investigation.

## Live-mode flip eligibility (SC-010)

Before flipping `institutional_rotation_bear_mode` default from
"shadow" to "active":

1. Operator runs a live-mode A/B ablation (active vs shadow on the
   same propagates) for n≥30 propagates.
2. Verifies the SC-009 retrospective metrics hold within ±1pp at
   live-validated horizons.
3. Per Constitution VIII v1.4.0 shadow-mode-first-then-flip pattern.

This is a future spec amendment; the current spec defaults to shadow
mode pending this validation.

## Cost gate

ZERO LLM cost addition (Constitution III T0 free-tier classification).

yfinance institutional_holders fetch adds ~50-200ms latency on cache
miss; LRU-cached to one fetch per ticker per process.

## Implementation files (after `/speckit.tasks` + `/speckit.implement`)

```text
tradingagents/agents/utils/institutional_rotation_filter.py  # NEW (~120 LOC)
tradingagents/agents/managers/portfolio_manager.py           # MODIFIED (~3 LOC)
tradingagents/default_config.py                              # MODIFIED (4 new keys)

tests/test_institutional_rotation_filter.py                  # NEW (~14 unit tests)
tests/test_institutional_rotation_pm_integration.py          # NEW (4 integration tests)
```

## Filter chain ordering (FR-012)

After Spec X-1 is deployed, the PM-stage filter chain is:

```
A3 (momentum_filter)
  → spec 006 (bear_sector_symmetry_filter)
  → spec 003/003.5 (contrarian_gate)
  → spec 004 (sector_momentum_filter)
  → spec 007 (forward_catalyst_filter)
  → spec X-1 (institutional_rotation_filter)  ← NEW, LAST in chain
```

Sample-size discipline puts smallest-evidence filter last; C-4 (n=12)
runs after Spec 007 (n=33+ for bull-side).

## Sibling docs

- [spec.md](spec.md) — feature specification
- [plan.md](plan.md) — implementation plan
- [research.md](research.md) — Phase 0 research (technical decisions)
- [data-model.md](data-model.md) — Phase 1 data model
- [contracts/institutional_rotation_filter.md](contracts/institutional_rotation_filter.md) — module API contract
- `claudedocs/forward-catalyst-class4-retrospective-2026-05-07.md` —
  PR #75 standalone retrospective evidence
- `claudedocs/forward-catalyst-class4-vs-spec007-overlap-2026-05-07.md` —
  PR #77 additive overlap evidence
- `claudedocs/spec-x-1-c4-institutional-rotation-feature-description-2026-05-07.md` —
  PR #87 feature description draft
