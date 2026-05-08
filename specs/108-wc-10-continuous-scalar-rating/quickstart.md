# Quickstart: WC-10 Continuous Scalar Rating

**Branch**: `108-wc-10-continuous-scalar-rating` | **Date**: 2026-05-08

## What WC-10 does

Replaces the framework's 5-tier categorical `PortfolioRating` enum with a continuous scalar in `[-1, +1]` for the Portfolio Manager's output. Tests whether the framework's mode collapse to Hold (Constitution VII Calibrated Abstention) is partially driven by the categorical bottleneck.

**Default-OFF**. Operator opts in via PARAMS.json. No production behavior change unless explicitly enabled.

## Empirical question (3 falsifiable predictions)

| Prediction | What it means |
|---|---|
| **NULL** | Continuous scalar doesn't change behavior; framework outputs cluster near 0 (=Hold). Calibrated Abstention is genuine. |
| **ALT-A** | Distribution less collapsed; bull/bear signal that 5-tier scale was throwing away surfaces in scalar magnitude. Categorical bottleneck confirmed. |
| **ALT-B** | Continuous scalar bins ex-post to match 5-tier distribution. Calibrated abstention is mode-collapsed regardless of output type. |

Per Constitution Principle IV, NULL or INCONCLUSIVE results are valid deliverables.

## Default configuration

After WC-10 implementation lands:

```python
# tradingagents/default_config.py
DEFAULT_CONFIG = {
    # ... existing entries ...
    "wc_10_enabled": False,                  # default-OFF
    "wc_10_filter_mode": "bypass",           # active when enabled
    "wc_10_bin_thresholds": (-0.6, -0.2, 0.2, 0.6),  # equal-width default
}
```

## Operator opt-in to WC-10

Edit experiment's `PARAMS.json` (or pass via CLI override):

```json
{
  "wc_10_enabled": true,
  "wc_10_filter_mode": "bypass"
}
```

Or via Python:

```python
config["wc_10_enabled"] = True
config["wc_10_filter_mode"] = "bypass"
```

When enabled, the Portfolio Manager emits a continuous scalar rating in `[-1, +1]` instead of a 5-tier categorical string. The 9-filter chain (A3 / spec 003 / 003.5 / 004 / 006 / 007 / 008 / X-1) is SKIPPED in bypass mode (clean single-intervention test).

## Running the v1 pilot

```bash
# 10 dates × 2 tickers × 2 modes (wc_10 + 5tier_baseline) = 40 propagates × ~$0.40 = ~$16
uv run --no-sync python scripts/wc_10_pilot.py --tickers NVDA,AAPL

# Resume on crash:
uv run --no-sync python scripts/wc_10_pilot.py --tickers NVDA,AAPL  # appends to existing CSV
```

Output:
- `experiments/2026-05-08-001-wc-10-pilot/results.csv` — 40 rows
- `experiments/2026-05-08-001-wc-10-pilot/HYPOTHESIS.md` — pre-stated falsification predictions (per Principle I)
- `experiments/2026-05-08-001-wc-10-pilot/PARAMS.json` — config snapshot

## Analyzing the pilot

```bash
uv run --no-sync python scripts/analyze_backtest.py \
    experiments/2026-05-08-001-wc-10-pilot/results.csv \
    --holding-days 21
```

Headline metrics (per SC-005):
1. Fraction of `|rating| > 0.2` in WC-10 mode (= committed cases vs Hold-equivalent)
2. Signed-rating × 21d-forward-α correlation
3. Bin-ex-post-to-5-tier and compare bucket means to existing 5-tier baseline corpus

Falsification verdict (per SC-007): determine which of NULL / ALT-A / ALT-B is empirically distinguishable.

## Auditing WC-10 fires

When `wc_10_enabled=True`, state logs at `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json` will contain:

```json
{
  "final_trade_decision": "**Rating**: 0.45\n\nBody...",
  "wc_10": {
    "rating_scalar": 0.45,
    "filter_mode": "bypass",
    "bin_thresholds_snapshot": [-0.6, -0.2, 0.2, 0.6]
  }
}
```

When `wc_10_enabled=False`, the `wc_10` top-level state field is ABSENT (FR-006 backward-compat).

## Disabling WC-10 (return to 5-tier baseline)

```json
{
  "wc_10_enabled": false
}
```

OR delete the keys from PARAMS.json — the framework's defaults take over.

## Bin function for ex-post analysis

```python
from tradingagents.wc_10 import bin_scalar_to_tier

bin_scalar_to_tier(0.45)  # → "Overweight"
bin_scalar_to_tier(-0.6)  # → "Sell" (boundary; ≤ claims lower bin)
bin_scalar_to_tier(0.0)   # → "Hold"

# Custom thresholds:
bin_scalar_to_tier(0.45, thresholds=(-0.7, -0.3, 0.3, 0.7))  # → "Hold"
```

Pure function. No side effects.

## Cost gate

| Cost component | Estimate |
|---|---|
| Pilot run (WC-10 mode, 20 propagates) | ~$8 |
| 5-tier baseline comparison run (20 propagates) | ~$8 |
| **Total v1** | **~$16** |
| Constitution III T2 budget | ≤$30 |
| Buffer | ~$14 |

## Filter chain ordering (FR-012)

When `wc_10_enabled=True` AND `wc_10_filter_mode="bypass"`:

```
PM LLM call → emit scalar rating
  → state["wc_10"] annotation
  → state["final_trade_decision"] (rendered with float rating)
  → [9-filter chain SKIPPED]
  → return state
```

When `wc_10_enabled=False` (default):

```
PM LLM call → emit 5-tier rating
  → A3 (momentum_filter)
  → spec 006 (bear_sector_symmetry_filter)
  → spec 003/003.5 (contrarian_gate)
  → spec 004 (sector_momentum_filter)
  → spec 007 (forward_catalyst_filter)
  → spec X-1 (institutional_rotation_filter)  ← LAST in chain
  → return state
```

WC-10 bypass mode is the cleanest possible single-intervention test of the categorical-bottleneck hypothesis.

## Implementation files (after `/speckit.tasks` + `/speckit.implement`)

```text
tradingagents/wc_10/__init__.py                           # NEW
tradingagents/wc_10/bin.py                                # NEW (~80 LOC)
tradingagents/agents/schemas.py                           # MODIFIED (PortfolioDecision Union)
tradingagents/agents/utils/agent_states.py                # MODIFIED (wc_10 field)
tradingagents/agents/managers/portfolio_manager.py        # MODIFIED (~5 LOC bypass branch)
tradingagents/graph/signal_processing.py                  # MODIFIED (scalar-aware extractor)
tradingagents/graph/trading_graph.py                      # MODIFIED (_log_state whitelist)
tradingagents/default_config.py                           # MODIFIED (3 new keys)

tests/test_wc_10_bin.py                                   # NEW (~6 unit tests)
tests/test_wc_10_pm_integration.py                        # NEW (2 integration tests)

experiments/2026-05-08-001-wc-10-pilot/                   # NEW (created by pilot harness)
scripts/wc_10_pilot.py                                    # NEW (~120 LOC harness)
```

## Sibling docs

- [spec.md](spec.md) — feature specification
- [plan.md](plan.md) — implementation plan
- [research.md](research.md) — Phase 0 research (8 documented decisions)
- [data-model.md](data-model.md) — Phase 1 data model
- [contracts/wc_10_module.md](contracts/wc_10_module.md) — module API contract
- `claudedocs/wc-10-continuous-scalar-rating-feature-description-2026-05-08.md` — PR #104 feature description draft
- `claudedocs/experiment-md-tier-2-3-status-2026-05-08.md` — PR #97 Tier 2/3 survey
- `docs/EXPERIMENT.md` — original WC-10 brainstorm
