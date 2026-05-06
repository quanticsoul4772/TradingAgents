# Quickstart: Sector-Baseline Fallback for Contrarian Gate

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data model**: [data-model.md](./data-model.md)

Operator-facing walkthrough: enabling/disabling the fallback, inspecting the new `gate_baseline` annotation, running the spec-003-vs-spec-003+sector ablation comparison.

---

## What's new

After this feature lands, the contrarian gate (Spec 003) gets a sector-level fallback. When a ticker has < 20 prior state logs (FR-004 floor), the gate now consults the pooled `bull_keyword_count` history of all same-sector tickers in your `~/.tradingagents/logs/` directory. If that pool has ≥ 20 observations, the gate fires (or annotates in shadow mode) using sector-level percentile.

Default-on. To revert to the spec 003 per-ticker-only behavior:

```python
from tradingagents.default_config import DEFAULT_CONFIG
config = DEFAULT_CONFIG.copy()
config["contrarian_gate_sector_fallback_enabled"] = False
```

Or set in PARAMS.json for an experiment:

```json
{
  "config_overrides": {
    "contrarian_gate_sector_fallback_enabled": false
  }
}
```

---

## Walkthrough 1 — inspect a fired annotation

After running `daily_signals.py` (or any propagate that goes through the gate), inspect the per-ticker state log:

```bash
jq '.contrarian_gate' ~/.tradingagents/logs/NVDA/TradingAgentsStrategy_logs/full_states_log_2026-05-08.json
```

Expected output (sector-fallback example):

```json
{
  "mode": "active",
  "feature_value": 75.0,
  "percentile": 92.0,
  "n_history": 80,
  "would_fire": true,
  "gate_fired": true,
  "pm_rating_pre_gate": "Overweight",
  "pm_rating_post_gate": "Hold",
  "skipped": null,
  "gate_baseline": "sector",
  "n_history_per_ticker": 13,
  "n_history_sector": 80
}
```

Read it as: NVDA had only 13 prior runs (below the 20-floor), so the gate consulted the Technology-sector pool (80 observations across all Tech tickers in your logs). NVDA's current `bull_keyword_count` (75) was at the 92nd percentile of that pool, above the 80% threshold, so the gate fired and downgraded Overweight → Hold.

For a per-ticker firing (thick-history ticker), `gate_baseline` would be `"per_ticker"`, and `n_history_per_ticker` would be ≥ 20.

---

## Walkthrough 2 — run the SC-003 Financials ablation comparison

The motivating empirical case for this feature was the SC-003 Financials investigation (5 losing Overweight commits, 4 with zero per-ticker history). To verify this feature actually improves coverage on that exact case, re-run the diagnostic with both flag values:

```bash
# Spec 003 baseline (no sector fallback)
python scripts/sc003_financials_gate_check.py --no-sector-fallback > /tmp/sc003-spec003-only.txt

# This spec (sector fallback enabled)
python scripts/sc003_financials_gate_check.py --sector-fallback > /tmp/sc003-with-sector.txt

# Compare
diff /tmp/sc003-spec003-only.txt /tmp/sc003-with-sector.txt
```

Expected behavior change: the 4 zero-history Financials tickers (BAC, WFC, GS, MA) that previously couldn't fire now consult the Financials-sector pool. If the pool has ≥ 20 observations across other Financials tickers in your logs (typically: JPM, MS — depends on your accumulated corpus), the fallback either fires or annotates as would-fire. If the pool has < 20 observations, falls through to `gate_baseline = "none"`.

(Note: as of the time this spec is written, `sc003_financials_gate_check.py` doesn't yet have `--no-sector-fallback` / `--sector-fallback` flags. They'll be added during implementation per the contract — see `tasks.md` once `/speckit.tasks` runs.)

---

## Walkthrough 3 — corpus-level audit by baseline source

Once the fallback has been live for some time, you can audit per-baseline α attribution:

```bash
python -c "
import json, glob
from pathlib import Path

per_ticker_fired = []
sector_fired = []
none_skipped = []

for p in glob.glob(str(Path.home() / '.tradingagents/logs/*/TradingAgentsStrategy_logs/full_states_log_*.json')):
    state = json.loads(Path(p).read_text(encoding='utf-8'))
    cg = state.get('contrarian_gate')
    if cg is None or cg.get('gate_baseline') is None:
        continue
    record = (state['company_of_interest'], state['trade_date'], cg.get('gate_fired'))
    if cg['gate_baseline'] == 'per_ticker':
        per_ticker_fired.append(record)
    elif cg['gate_baseline'] == 'sector':
        sector_fired.append(record)
    elif cg['gate_baseline'] == 'none':
        none_skipped.append(record)

print(f'per_ticker: {len(per_ticker_fired)} entries; {sum(1 for r in per_ticker_fired if r[2])} fired')
print(f'sector:     {len(sector_fired)} entries; {sum(1 for r in sector_fired if r[2])} fired')
print(f'none:       {len(none_skipped)} entries; 0 fired')
"
```

Then compute realized α per baseline source (the `sc003_financials_gate_check.py` script can be extended for this).

---

## Walkthrough 4 — set up an ablation experiment

Per Constitution Principle II (One Experiment Per Change), to test whether the sector fallback genuinely improves α attribution vs adds noise, run one experiment with `contrarian_gate_sector_fallback_enabled=True` (default) and one identical-otherwise experiment with `False`. Compare bullish-bucket realized α between the two:

```bash
# Experiment A: spec 003 only
python scripts/new_experiment.py spec003-only --source-idea "Sector-fallback ablation control"
# edit experiments/<id>/PARAMS.json: "contrarian_gate_sector_fallback_enabled": false
bash experiments/<id>/run.sh

# Experiment B: spec 003 + sector fallback (default)
python scripts/new_experiment.py spec003-plus-sector --source-idea "Sector-fallback ablation treatment"
bash experiments/<id>/run.sh

# Compare bullish-bucket α
python scripts/analyze_backtest.py experiments/<id-A>/results.csv --holding-days 21
python scripts/analyze_backtest.py experiments/<id-B>/results.csv --holding-days 21
```

The treatment (B) should show fewer bullish commits (sector fallback fires more often) but per-commit α should be cleaner. Net effect on bucket α: empirical question this experiment answers.

---

## Troubleshooting

### The gate annotation is missing entirely from a state log

- Check that `contrarian_gate_mode` is not `"off"` — `"off"` mode emits no annotation per Spec 003.
- Check that the state log was written AFTER commit `4c14d0f` (2026-05-06) — earlier state logs lost the annotation due to a persistence bug.

### `gate_baseline` is `"none"` for every ticker

- Check `~/.tradingagents/paper/sectors.json` exists. If missing or empty, every ticker is treated as `"Unknown"` sector. Run `python scripts/paper_trade.py status` (Spec 002) to populate the cache via yfinance.
- Check that you have ≥ 20 same-sector state logs across your tickers. Cold-start universes (≤ 5 tickers, ≤ 5 logs each) won't reach the floor.

### Setting `contrarian_gate_sector_fallback_enabled=False` doesn't seem to do anything

- Verify the flag is being read from the same config the gate sees. The gate calls `get_config()` per the existing PM hook in `tradingagents/agents/managers/portfolio_manager.py`.
- For ablation experiments, set the flag in `PARAMS.json::config_overrides` so `scripts/backtest.py` injects it correctly.

### Sector pool aggregation is slow

- Per R-3, expected per-evaluation cost is ≤ 200ms for typical scale. If you see > 1s, you may have very large state-log directories (thousands of files per ticker). Future spec can add caching.

---

## What this feature does NOT do

- **Override per-ticker semantics** — when per-ticker history is ≥ 20, spec 003's original behavior runs unchanged (SC-002).
- **Mix per-ticker + sector** — fallback ladder is strict; no weighting, no blending.
- **Require sector-pool diversity** — v1 accepts pools dominated by a single ticker (R-7).
- **Add LLM cost** — pure offline state-log scan (SC-006).
- **Persist a sector-pool cache** — recomputed per evaluation (R-3).
- **Touch the spec 003 firing decision logic** — same threshold, same target, same modes; only the BASELINE consulted changes.

---

## Reading list

- `specs/003-sector-baseline-gate/spec.md` — full feature spec
- `specs/003-sector-baseline-gate/data-model.md` — entity definitions + state transitions
- `specs/003-sector-baseline-gate/contracts/gate_annotation_extended.md` — annotation schema delta
- `specs/003-sector-baseline-gate/contracts/sector_pool_function.md` — aggregator function contract
- `specs/003-sector-baseline-gate/research.md` — design decisions (R-1..R-10)
- `specs/003-analyst-contrarian-gate/spec.md` — original Spec 003 (predecessor)
- `claudedocs/sc003-financials-gate-check-2026-05-06.md` — empirical motivation (the SC-003 Financials investigation that surfaced the cold-start gap)
