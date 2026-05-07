# Quickstart: Bear-Sector-Symmetry Filter (Spec 006)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data model**: [data-model.md](./data-model.md)

Operator-facing walkthrough: enable in shadow mode, inspect annotations, run the SC-008 retrospective, set up an ablation experiment, prerequisites for default-on flip.

> **Constitution VIII status**: this filter ships **default-off as operator-opt-in only**. Corpus retrospective (`claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md`) showed (a) SC-008 FAILED at +5% (5 of 18 ticker_strong-bear cohort fires; target was ≥8); (b) net Δα = -0.71pp at +5% (anti-predictive across n=36 commits). Default-on flip is NOT justified by the empirical evidence and is NOT planned. Under Constitution v1.3.0 Principle VIII, future filters of this class (backward-looking + price-derived) require a passing pre-spec retrospective; this filter is grandfathered as a pre-principle artifact.

---

## What's new

After this feature lands, the framework gets a SECOND bear-side rating-suppression filter (after A3):

- **A3 momentum filter** suppresses bearish commits when the ticker is DOWN ≥5% absolute over the prior 30 trading days (mean-reversion zone for buyers).
- **Spec 006 bear-sector-symmetry filter** (this one) suppresses bearish commits when the ticker has OUTPERFORMED its sector ETF by more than a configurable threshold (default +5%) over the prior 30 trading days (counter-trend bear suppression).

The filter targets a different mechanism: **counter-trend bearish commits on rallying tickers**. Today's sector-α attribution analysis (`claudedocs/sector-alpha-attribution-2026-05-06.md`) found 18 of 37 bearish commits in the 194-row corpus (48.6%) landed in `ticker_strong` (ticker rallied vs both SPY AND its own sector despite the bear call) with mean realized α-vs-SPY = +28.02%. A3 misses this entire cohort because A3 only fires when the ticker is already DOWN; spec 006 fires when the ticker is already UP relative to its sector — the inverse condition.

Default-off — must be explicitly enabled.

---

## Walkthrough 1 — enable in shadow mode

```python
from tradingagents.default_config import DEFAULT_CONFIG
config = DEFAULT_CONFIG.copy()
config["bear_sector_symmetry_filter_mode"] = "shadow"
config["bear_sector_symmetry_filter_threshold_pct"] = 5.0
```

Or in `PARAMS.json` for an experiment:

```json
{
  "config_overrides": {
    "bear_sector_symmetry_filter_mode": "shadow",
    "bear_sector_symmetry_filter_threshold_pct": 5.0
  }
}
```

Shadow mode computes the annotation but does NOT modify ratings — useful for measuring would-fire rate before committing to active mode.

---

## Walkthrough 2 — inspect a fired annotation

After running a propagate that crosses the threshold:

```bash
jq '.bear_sector_symmetry' ~/.tradingagents/logs/NVDA/TradingAgentsStrategy_logs/full_states_log_<DATE>.json
```

Expected output (active-mode fire example):

```json
{
  "mode": "active",
  "sector": "Technology",
  "etf": "XLK",
  "ticker_30d_return_pct": 18.32,
  "etf_30d_return_pct": 6.40,
  "relative_strength_pct": 11.92,
  "threshold_pct": 5.0,
  "lookback_days": 30,
  "would_fire": true,
  "fired": true,
  "pre_rating": "Underweight",
  "post_rating": "Hold",
  "skipped": null
}
```

Read it as: the PM rated NVDA Underweight; the filter saw NVDA was up 18.32% over the prior 30 trading days while XLK was up only 6.40% (relative-strength delta = +11.92%, above the configured +5% threshold); since the rating was bearish AND the threshold was crossed, the filter fired and downgraded Underweight → Hold.

For a shadow-mode firing, `fired` would be `false` and `post_rating == pre_rating == "Underweight"`. For a non-firing case (relative-strength delta below threshold), `would_fire` would be `false`.

---

## Walkthrough 3 — run the SC-008 retrospective on today's bear cohort

The motivating empirical case for this spec was today's sector-α attribution finding: 18 of 37 bearish commits in the 194-row corpus landed in `ticker_strong` (mean α-vs-SPY = +28.02%). SC-008 specifies that this filter MUST suppress ≥8 of the 18 at threshold = +5% AND show net Δα positive at the default threshold.

```bash
python scripts/bear_sector_symmetry_retrospective.py \
    --threshold-pct 5.0 \
    --lookback-days 30 \
    --restrict-to-ticker-strong-cohort
```

Expected behavior change (relative to A3 which doesn't catch this cohort):
- If the relative-strength signal was empirically there (ticker outperforming sector by >5% in the prior 30d for ≥8 of the 18 dates) → SC-008 passes
- If fewer fire → spec's motivating premise needs revisiting; tighten the threshold or accept the filter as a conservative niche tool

The retrospective is `$0` LLM cost (purely offline yfinance lookups + sector-cache reads).

---

## Walkthrough 4 — corpus-wide ablation experiment (Constitution II discipline)

Per Constitution Principle II (One Experiment Per Change), to test whether the filter genuinely improves bearish-bucket α vs adds noise, run two experiments differing only in the filter:

```bash
# Experiment A: filter off (control)
python scripts/new_experiment.py spec006-control --source-idea "Bear-sector-symmetry ablation control"
# edit experiments/<id>/PARAMS.json: "bear_sector_symmetry_filter_threshold_pct": null
bash experiments/<id>/run.sh

# Experiment B: filter on (treatment)
python scripts/new_experiment.py spec006-treatment --source-idea "Bear-sector-symmetry ablation treatment"
# edit experiments/<id>/PARAMS.json:
#   "bear_sector_symmetry_filter_threshold_pct": 5.0,
#   "bear_sector_symmetry_filter_mode": "active"
bash experiments/<id>/run.sh

# Compare bearish-bucket realized α
python scripts/analyze_backtest.py experiments/<id-A>/results.csv --holding-days 21
python scripts/analyze_backtest.py experiments/<id-B>/results.csv --holding-days 21
```

Treatment (B) should show fewer bearish commits (filter suppresses some) but a cleaner bearish bucket if the filter mechanism captures real signal. Net effect on bucket α: an empirical question this experiment answers.

---

## Walkthrough 5 — corpus-wide retrospective with threshold sweep

The retrospective script supports a threshold-sweep mode (mirrors `scripts/sector_momentum_retrospective.py` for spec 004):

```bash
python scripts/bear_sector_symmetry_retrospective.py --threshold-sweep
```

Output (table per candidate threshold):

```
| threshold | n_fired | n_kept | fired_α | kept_α | net_Δα |
|---|---|---|---|---|---|
| +3.0%     | XX      | YY     | +ZZ%    | -AA%   | +BBpp  |
| +5.0%     | XX      | YY     | ...     | ...    | ...    |
| +7.5%     | XX      | YY     | ...     | ...    | ...    |
| +10.0%    | XX      | YY     | ...     | ...    | ...    |
```

Use this to choose a threshold that maximizes `net_Δα` before flipping the default to active mode (per Constitution II + the precedent set by A3 + spec 003 + spec 004 default flips).

---

## Walkthrough 6 — what the filter does and doesn't catch

| Failure pattern | A3 | Spec 006 | Both | Neither |
|---|---|---|---|---|
| Bear commit on a ticker already DOWN ≥5% absolute | ✓ | — | — | — |
| Bear commit on a ticker rallying vs its own sector (>+5% relative) | — | ✓ | — | — |
| Bear commit on a ticker DOWN absolute AND outperforming a worse-down sector (rare overlap) | ✓ | — | (A3 fires first; spec 006 no-ops) | — |
| Bear commit on a ticker drifting sideways (no momentum either direction) | — | — | — | ✓ (genuine bearish-call evaluation; no filter intervenes) |
| Bear commit driven by stock-specific news the framework processed correctly | — | — | — | ✓ (this is what the framework SHOULD do; filter doesn't second-guess fundamentals) |

The matrix shows the filter is targeted at one specific failure mode (counter-trend bear calls on relatively strong tickers). Combined with A3 (the absolute-down case) the bear side gets coverage of both "ticker already crushed (mean-revert)" and "ticker still rallying (don't fight the tape)" failure patterns.

---

## Prerequisites for default-on flip

Per Constitution Principle II + the A3/spec 003/spec 004 precedent, the default flip from `"off"` to `"active"` happens in a SEPARATE commit AFTER:

1. SC-008 passes (filter suppresses ≥8 of the 18 today's `ticker_strong`-bearish commits at +5% threshold) — implementation gate
2. A corpus-wide retrospective (`scripts/bear_sector_symmetry_retrospective.py`) shows positive `net_Δα` at the chosen threshold across the existing experiments corpus
3. The `claudedocs/bear-sector-symmetry-retrospective-<DATE>.md` writeup documents per-sector behavior (where the filter helps vs hurts) so the operator can reason about sector-specific risks
4. Verify the spec 003 + spec 004 default-on patterns hold: when spec 006 is layered on top of an active-mode spec 003 + active-mode A3, are interactions still clean? (The filter chain order in FR-012 + the disjoint-conditions guard in SC-009 should ensure yes; the retrospective should empirically confirm.)

Until those gates pass, the filter remains default-off. Operators can opt-in via PARAMS.json or config override.

---

## Troubleshooting

### `state["bear_sector_symmetry"]` is missing entirely
- Mode is `"off"` (default). Set it to `"shadow"` or `"active"`.

### Annotation shows `skipped="unknown_sector"` for every ticker
- `~/.tradingagents/paper/sectors.json` doesn't exist or is empty. Run `python scripts/paper_trade.py status` (Spec 002) to populate it.

### Annotation shows `skipped="no_etf_mapping"`
- The sector yfinance returned isn't in `SECTOR_ETF_MAP`. Check the ticker's `info["sector"]`. Either it's an unusual sector (e.g., a foreign ADR with a non-standard classification), or yfinance changed its naming. Add the variant to `SECTOR_ETF_MAP` (in spec 004's module — single source of truth) if appropriate.

### Annotation shows `skipped="missing_ticker_data"`
- The ticker doesn't have ≥30 trading days of prior history at the trade_date. Likely a recent IPO. The filter degrades cleanly — no firing on that propagate. If the operator wants the filter to fire on shorter-history tickers, lower the `lookback_days` config (but this loosens the threshold's interpretability).

### Filter never fires even though tickers are clearly outperforming their sectors
- Check threshold: negative values are rejected (per FR-006). Use a positive number like `+5.0`.
- Check mode: `"shadow"` annotates without firing; `"active"` fires.
- Check `lookback_days`: default 30. Very short windows (e.g., 5d) will produce noisier relative-strength values.
- Inspect a specific propagate's annotation: `jq '.bear_sector_symmetry.relative_strength_pct, .bear_sector_symmetry.threshold_pct' <state-log>`. If `relative_strength_pct ≤ threshold_pct`, the filter (correctly) didn't fire.

### Setting threshold to +5.0 doesn't seem to do anything
- Verify the config flag is being read from the same config the filter sees. The filter calls `get_config()` per the existing PM hook pattern.
- For ablation experiments, set the flag in `PARAMS.json::config_overrides` so `scripts/backtest.py` injects it correctly.

### Filter and A3 both fired on the same propagate
- Should not happen by construction (disjoint conditions per R-11/SC-009): A3 needs ticker DOWN absolute, spec 006 needs ticker UP relative to sector, which requires ticker ≥ sector return; in practice ticker is also UP absolute. If you observe both firing, the rare overlap case (e.g. ticker -5% absolute AND sector -10%) triggered A3 first → rating became Hold → spec 006 no-opped (`skipped="rating_not_bearish"`). Inspect the annotations to confirm; report as a bug if both `fired=True`.

---

## What this filter does NOT do

- Override A3's bear suppression — A3 runs FIRST in the chain (per FR-012). This filter only sees ratings A3 left as Underweight/Sell.
- Touch bullish ratings — spec 003 / 003.5 / 004 cover the bull side. Bull/bear filters are independent (different rating sets).
- Open long positions on ticker_strong rallying tickers. Like A3, this is purely a downgrade filter (UW/Sell → Hold; never UPGRADE to Buy/OW per FR-007).
- Add LLM cost (per FR-006/SC-005).
- Persist a relative-strength cache beyond the in-process LRU (recomputed per evaluation; LRU only).
- Re-implement the SECTOR_ETF_MAP — imports it from spec 004's module (FR-004; single source of truth preserved).
- Modify spec 004's logic in any way — they're parallel filters that happen to share an ETF-fetch cache.

---

## Reading list

- `specs/005-bear-sector-symmetry/spec.md` — full feature spec
- `specs/005-bear-sector-symmetry/data-model.md` — entity definitions + state transitions
- `specs/005-bear-sector-symmetry/contracts/annotation_schema.md` — annotation schema
- `specs/005-bear-sector-symmetry/contracts/filter_function.md` — filter function contract
- `specs/005-bear-sector-symmetry/research.md` — design decisions (R-1..R-12)
- `claudedocs/sector-alpha-attribution-2026-05-06.md` — empirical motivation (the +28.02% mean-α `ticker_strong` cohort)
- `tradingagents/agents/utils/momentum_filter.py` — A3 (sibling filter; per-ticker absolute bear suppression)
- `tradingagents/agents/utils/sector_momentum_filter.py` — Spec 004 (sibling filter; sector-ETF absolute bull suppression; this spec imports `SECTOR_ETF_MAP` + `_etf_history` from here)
- `tradingagents/signals/contrarian_gate.py` — Spec 003 / 003.5 (sibling filter; bull suppression on prose density)
