# Quickstart: Sector-Momentum Filter

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data model**: [data-model.md](./data-model.md)

Operator-facing walkthrough: enable in shadow mode, inspect annotations, run the SC-008 retrospective, set up an ablation experiment, prerequisites for default-on flip.

> **Constitution VIII status**: this filter ships **default-off as operator-opt-in only**. Corpus retrospective (`claudedocs/sector-momentum-retrospective-2026-05-06.md`) showed net Δα = -0.45pp at the proposed default -5% threshold (anti-predictive across n=73 commits). Default-on flip is NOT justified by the empirical evidence and is NOT planned. Under Constitution v1.3.0 Principle VIII, future filters of this class (backward-looking + price-derived) require a passing pre-spec retrospective; this filter is grandfathered as a pre-principle artifact.

---

## What's new

After this feature lands, the framework gets a third bullish-suppression filter (after Spec 003 + Spec 003.5):

- **Spec 003 / 003.5 contrarian gate** suppresses bullish commits when the analyst's bull-keyword density is high (within-ticker or sector-baseline).
- **Spec 004 sector-momentum filter** (this one) suppresses bullish commits when the ticker's SECTOR ETF is in a mean-reversion zone (down >threshold% in the prior 30 trading days).

The filter targets a different mechanism: **sector-rotation losses** where the ticker isn't anomalous within itself or its sector, but the entire sector is down. The 5 SC-003 Financials Overweight commits (-7.07% mean α) had moderate `bull_keyword_count` values; neither spec 003 nor spec 003.5 fires on them, but XLF was down ~7% in the 30d before 2026-04-03.

Default-off — must be explicitly enabled.

---

## Walkthrough 1 — enable in shadow mode

```python
from tradingagents.default_config import DEFAULT_CONFIG
config = DEFAULT_CONFIG.copy()
config["sector_momentum_filter_mode"] = "shadow"
config["sector_momentum_filter_threshold_pct"] = -5.0
```

Or in `PARAMS.json` for an experiment:

```json
{
  "config_overrides": {
    "sector_momentum_filter_mode": "shadow",
    "sector_momentum_filter_threshold_pct": -5.0
  }
}
```

Shadow mode computes the annotation but does NOT modify ratings — useful for measuring would-fire rate before committing to active mode.

---

## Walkthrough 2 — inspect a fired annotation

After running a propagate that crosses the threshold:

```bash
jq '.sector_momentum' ~/.tradingagents/logs/WFC/TradingAgentsStrategy_logs/full_states_log_2026-04-03.json
```

Expected output (active-mode fire example):

```json
{
  "mode": "active",
  "sector": "Financial Services",
  "etf": "XLF",
  "etf_30d_return_pct": -7.85,
  "threshold_pct": -5.0,
  "lookback_days": 30,
  "would_fire": true,
  "fired": true,
  "pre_rating": "Overweight",
  "post_rating": "Hold",
  "skipped": null
}
```

Read it as: the PM rated WFC Overweight; the filter saw that XLF was down 7.85% over the prior 30 trading days (below the configured -5% threshold); since the rating was bullish AND the threshold was crossed, the filter fired and downgraded Overweight → Hold.

For a shadow-mode firing, `fired` would be `false` and `post_rating == pre_rating == "Overweight"`. For a non-firing case (sector ETF not in mean-reversion zone), `would_fire` would be `false`.

---

## Walkthrough 3 — run the SC-008 retrospective on the SC-003 Financials cohort

The motivating empirical case for this spec was today's spec 003.5 validation finding (`claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md`): the 5 SC-003 Financials Overweight commits lost -7.07% mean α from sector-rotation, and neither spec 003 nor spec 003.5 catches them. SC-008 specifies that this filter MUST suppress ≥3 of the 5 at threshold = -5%.

```bash
python scripts/sector_momentum_retrospective.py \
    --threshold-pct -5.0 \
    --lookback-days 30 \
    --restrict-to-sc003-financials
```

Expected behavior change (relative to spec 003 / 003.5 which fire 0/5):
- If XLF was empirically down >5% in the 30d before 2026-04-03 → ≥3 of 5 fire → SC-008 passes
- If XLF wasn't down enough → fewer fire; spec's motivating premise needs revisiting

The retrospective is `$0` LLM cost (purely offline yfinance lookups + sector-cache reads).

---

## Walkthrough 4 — corpus-wide ablation experiment (Constitution II discipline)

Per Constitution Principle II (One Experiment Per Change), to test whether the filter genuinely improves bullish-bucket α vs adds noise, run two experiments differing only in the filter:

```bash
# Experiment A: filter off (control)
python scripts/new_experiment.py spec004-control --source-idea "Sector-momentum filter ablation control"
# edit experiments/<id>/PARAMS.json: "sector_momentum_filter_threshold_pct": null
bash experiments/<id>/run.sh

# Experiment B: filter on (treatment)
python scripts/new_experiment.py spec004-treatment --source-idea "Sector-momentum filter ablation treatment"
# edit experiments/<id>/PARAMS.json: "sector_momentum_filter_threshold_pct": -5.0, "sector_momentum_filter_mode": "active"
bash experiments/<id>/run.sh

# Compare bullish-bucket realized α
python scripts/analyze_backtest.py experiments/<id-A>/results.csv --holding-days 21
python scripts/analyze_backtest.py experiments/<id-B>/results.csv --holding-days 21
```

Treatment (B) should show fewer bullish commits (filter suppresses some) but a cleaner bullish bucket if the filter mechanism captures real signal. Net effect on bucket α: an empirical question this experiment answers.

---

## Walkthrough 5 — corpus-wide retrospective with threshold sweep

The retrospective script supports a threshold-sweep mode (mirrors `scripts/uw_suppression_filter.py` for A3):

```bash
python scripts/sector_momentum_retrospective.py --threshold-sweep
```

Output (table per candidate threshold):

```
| threshold | n_fired | n_kept | fired_α | kept_α | net_Δα |
|---|---|---|---|---|---|
| -3.0%     | XX      | YY     | -ZZ%    | +AA%   | +BBpp  |
| -5.0%     | XX      | YY     | ...     | ...    | ...    |
| -7.5%     | XX      | YY     | ...     | ...    | ...    |
| -10.0%    | XX      | YY     | ...     | ...    | ...    |
```

Use this to choose a threshold that maximizes `net_Δα` before flipping the default to active mode (per Constitution II + the precedent set by A3 + spec 003 default flips).

---

## Walkthrough 6 — what the filter does and doesn't catch

| Failure pattern | Spec 003 / 003.5 | Spec 004 | Both | Neither |
|---|---|---|---|---|
| Within-ticker bull-prose density spike (finding #4 mechanism) | ✓ | — | — | — |
| Cold-start ticker in a sector with thick history + bull-prose spike | ✓ (003.5) | — | — | — |
| Sector-rotation: ticker bullish, sector down regime | — | ✓ | — | — |
| Sector-rotation AND prose-density spike | ✓ | ✓ | ✓ | — |
| Cold-start universe (small operator), sector-rotation | — | — | — | ✓ (operator needs more time accumulating per-ticker / per-sector history OR a different mechanism) |
| Pure idiosyncratic ticker miss (no sector or prose signal) | — | — | — | ✓ (this is what calibrated abstention exists for; framework should default to Hold when evidence is weak) |

The matrix shows the filter is one tool in a larger system; combined with the others + Constitution VII calibrated abstention, most catch-able failure modes have coverage.

---

## Prerequisites for default-on flip

Per Constitution Principle II + the A3/spec 003 precedent, the default flip from `"off"` to `"active"` happens in a SEPARATE commit AFTER:

1. SC-008 passes (filter suppresses ≥3 of 5 SC-003 Financials Overweight commits at -5% threshold) — implementation gate
2. A corpus-wide retrospective (`scripts/sector_momentum_retrospective.py`) shows positive `net_Δα` at the chosen threshold across the existing experiments corpus
3. The `claudedocs/sector-momentum-retrospective-<DATE>.md` writeup documents per-sector behavior (where the filter helps vs hurts) so the operator can reason about sector-specific risks

Until those gates pass, the filter remains default-off. Operators can opt-in via PARAMS.json or config override.

---

## Troubleshooting

### `state["sector_momentum"]` is missing entirely
- Mode is `"off"` (default). Set it to `"shadow"` or `"active"`.

### `gate_baseline` shows `unknown_sector` for every ticker
- `~/.tradingagents/paper/sectors.json` doesn't exist or is empty. Run `python scripts/paper_trade.py status` (Spec 002) to populate it.

### `gate_baseline` shows `no_etf_mapping`
- The sector yfinance returned isn't in `SECTOR_ETF_MAP`. Check the ticker's `info["sector"]`. Either it's an unusual sector (e.g., a foreign ADR with a non-standard classification), or yfinance changed its naming. Add the variant to `SECTOR_ETF_MAP` if appropriate.

### Filter never fires even though sector ETFs are clearly down
- Check threshold: positive values are rejected (per FR-006). Use a negative number like `-5.0`.
- Check mode: `"shadow"` annotates without firing; `"active"` fires.
- Check `lookback_days`: default 30. Very short windows (e.g., 5d) will rarely cross typical thresholds.

### Setting threshold to -5.0 doesn't seem to do anything
- Verify the config flag is being read from the same config the gate sees. The filter calls `get_config()` per the existing PM hook pattern.
- For ablation experiments, set the flag in `PARAMS.json::config_overrides` so `scripts/backtest.py` injects it correctly.

---

## What this filter does NOT do

- Override per-ticker semantics from spec 003 / 003.5 — those run FIRST in the chain (per FR-012). This filter only sees ratings the prior filters left as Buy/OW.
- Open short positions. Like A3 + spec 003 / 003.5, this is purely a downgrade filter (Buy/OW → Hold; never to UW per FR-007).
- Add LLM cost (per FR-006/SC-005).
- Persist a sector-pool cache (recomputed per evaluation; LRU only).
- Touch the spec 003 firing decision logic — same threshold + target + modes; only the BASELINE consulted differs.

---

## Reading list

- `specs/004-sector-momentum-filter/spec.md` — full feature spec
- `specs/004-sector-momentum-filter/data-model.md` — entity definitions + state transitions
- `specs/004-sector-momentum-filter/contracts/annotation_schema.md` — annotation schema
- `specs/004-sector-momentum-filter/contracts/filter_function.md` — filter function contract
- `specs/004-sector-momentum-filter/research.md` — design decisions (R-1..R-10)
- `claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md` — empirical motivation
- `tradingagents/agents/utils/momentum_filter.py` — A3 (sibling filter; bear suppression on per-ticker momentum)
- `tradingagents/signals/contrarian_gate.py` — Spec 003 / 003.5 (sibling filter; bull suppression on prose density)
