# Quickstart: Forward-Catalyst-Aware Contrarian Gate (Spec 007)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data model**: [data-model.md](./data-model.md)

Operator-facing walkthrough: enable the filter, inspect annotations, run the SC-008 retrospective, prerequisites for bear-side default-on flip, cost-tier considerations for Haiku vs Opus.

> **Constitution VIII status**: this is the **FIRST forward-catalyst-aware filter** to clear the validation gate per Principle VIII (v1.4.0 amended as part of this spec). Bull-side ships **default-on at T=0.60** (Class 3 Opus retrospective DECISIVELY PASSED all 3 gate criteria). Bear-side ships **default-shadow at T=0.50** (passes criteria 1+2 only; shadow-mode-first observation period required before active-mode flip). See `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` + `.specify/memory/constitution.md` Principle VIII for the empirical evidence + codified gate.

> **Cost note**: this filter adds an LLM call per propagate (default Opus, ~$0.025/call). For typical operator workflow (`daily_signals.py` on 5-10 ticker watchlist daily): ~$0.25/day cost addition. For backtest workflows running 100+ propagates: ~$2.50 cost addition. Operators can disable via setting BOTH modes to `"off"` (FR-013 escape hatch) for cost-sensitive runs.

---

## What's new

After this feature lands, the framework gets the FIRST forward-catalyst-aware rating-suppression filter (after A3 + spec 003 + spec 003.5 + spec 004 + spec 006 — all backward-price-derived):

- **A3 momentum filter** suppresses bearish commits on tickers DOWN ≥5% absolute over the prior 30 trading days
- **Spec 003 / 003.5 contrarian gate** suppresses bullish commits when the analyst's prose has high `bull_keyword_count` percentile
- **Spec 004 sector-momentum filter** (default-off) suppresses bullish commits when the ticker's sector ETF is in absolute mean-reversion zone
- **Spec 006 bear-sector-symmetry filter** (default-off) suppresses bearish commits when the ticker has outperformed its sector ETF
- **Spec 007 forward-catalyst filter** (this one) suppresses commits when the LLM-extracted "case-priced-in" score (per side) exceeds threshold — both bull and bear sides

The mechanism class is fundamentally different from the prior 5 filters: an LLM (Opus default) reads the same analyst evidence the PM saw and scores how widely the bull/bear case is ALREADY ACCEPTED by the market. When the thesis is consensus-priced-in, the framework's commit in that direction is unlikely to add value beyond the consensus → suppress to Hold.

Bull-side default-on; bear-side default-shadow per the empirical retrospective evidence.

---

## Walkthrough 1 — verify default behavior on a fresh propagate

```bash
python main.py  # or `tradingagents analyze` for the interactive CLI
```

After a propagate completes, inspect the state log:

```bash
jq '.forward_catalyst' ~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json
```

Expected output (typical case where bull-side fires):

```json
{
  "model": "claude-opus-4-7",
  "bull_case_priced_in": 0.78,
  "bear_case_priced_in": 0.45,
  "rationale": "The bull case (iPhone 17 supercycle + services growth) is widely covered...",
  "bull_threshold": 0.60,
  "bear_threshold": 0.50,
  "bull_mode": "active",
  "bear_mode": "shadow",
  "would_fire_bull": true,
  "would_fire_bear": false,
  "fired_bull": true,
  "fired_bear": false,
  "pre_rating": "Overweight",
  "post_rating": "Hold",
  "skipped": null,
  "error": null
}
```

Read it as: the LLM scored the bull case as 0.78 priced-in (above the +0.60 default threshold); pre-rating was Overweight; bull-side fired and downgraded to Hold; bear-side observed `would_fire_bear=false` (score 0.45 below +0.50 threshold).

---

## Walkthrough 2 — disable for a cost-sensitive workflow

```python
from tradingagents.default_config import DEFAULT_CONFIG
config = DEFAULT_CONFIG.copy()
config["forward_catalyst_bull_mode"] = "off"
config["forward_catalyst_bear_mode"] = "off"
```

Or in `PARAMS.json` for an experiment:

```json
{
  "config_overrides": {
    "forward_catalyst_bull_mode": "off",
    "forward_catalyst_bear_mode": "off"
  }
}
```

With both modes off, the filter skips the LLM call entirely (zero cost per FR-009 / SC-006). PM ratings byte-identical to the no-filter baseline.

---

## Walkthrough 3 — opt down to Haiku for cheaper backtest runs

```python
config["forward_catalyst_model"] = "claude-haiku-4-5"
```

**Documented degradation**: Haiku produces a tighter score distribution (std 0.071 vs Opus 0.090) and smaller bull-side cohort separation (5pp vs Opus 10pp). The bull-side default-on flip is empirically justified ONLY at Opus (per `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` + `claudedocs/forward-catalyst-class3-retrospective-2026-05-06.md` Haiku vs Opus comparison table). Haiku ablation experiments are valid for cost-sensitive backtests but should NOT be treated as production-equivalent.

Cost trade-off: Haiku is ~$0.0025/call (10× cheaper than Opus). For 100-propagate backtest: $0.25 (Haiku) vs $2.50 (Opus).

---

## Walkthrough 4 — enable bear-side active mode (shadow-mode → active flip)

Per Constitution VIII shadow-mode-first condition + design doc §5: bear-side default-active flip requires observing n≥20 fresh propagates in shadow mode BEFORE flipping. After 20+ propagates, run the SC-008 retrospective + review:

1. Inspect bear-side `would_fire_bear` annotations across the 20+ propagates
2. Compute the observed bear-side fire rate
3. Cross-tab against realized 21d α to estimate net Δα at active-mode default

If the observed fire rate + net Δα are consistent with the Opus retrospective evidence (cohort hit rate ~72%, net Δα ~+0.30pp), the flip can proceed:

```python
config["forward_catalyst_bear_mode"] = "active"
```

Or via `PARAMS.json` config_overrides for experiments. Document the flip in HYPOTHESIS.md per Constitution II ablation discipline + the new Principle VIII v1.4.0 forward-catalyst-class shadow-mode-first condition.

---

## Walkthrough 5 — run the SC-008 empirical-validation retrospective

```bash
python scripts/forward_catalyst_retrospective.py
```

The script extends `scripts/forward_catalyst_class3_retrospective.py` (the existing retrofit) by:
1. Loading config from `tradingagents.default_config.DEFAULT_CONFIG` (production thresholds + modes)
2. Walking the same 45-commit cohort + ~50 controls from `claudedocs/sector-alpha-attribution-2026-05-06.csv`
3. Re-applying the production filter logic at default thresholds
4. Reporting per-side fire rates + cohort hit rates + verifying SC-008 acceptance

Expected results at default thresholds (bull=0.60, bear=0.50):
- Bull-side fires on ≥24 of 27 ticker_weak commits (88.9% hit rate per Opus retrospective evidence)
- Bear-side fires (in shadow mode) on ≥10 of 18 ticker_strong commits (per design doc §5; empirically validated at 13/18 in Opus retrospective)

If either gate fails, the spec's motivating premise needs revisiting before any further default-on flips.

The retrospective is `~$2 LLM cost` (one Opus call per cohort + control commit; reuses cached state logs from `~/.tradingagents/logs/`).

---

## Walkthrough 6 — corpus-wide ablation experiment (Constitution II discipline)

Per Constitution Principle II + the spec 004 / spec 006 precedent, to test whether the default-on bull-side filter genuinely improves bullish-bucket α vs adds noise, run two experiments differing only in `forward_catalyst_bull_mode`:

```bash
# Experiment A: filter off (control)
python scripts/new_experiment.py spec007-control --source-idea "Forward-catalyst ablation control"
# edit experiments/<id>/PARAMS.json:
#   "forward_catalyst_bull_mode": "off",
#   "forward_catalyst_bear_mode": "off"
bash experiments/<id>/run.sh

# Experiment B: filter on (treatment)
python scripts/new_experiment.py spec007-treatment --source-idea "Forward-catalyst ablation treatment"
# edit experiments/<id>/PARAMS.json:
#   "forward_catalyst_bull_mode": "active",
#   "forward_catalyst_bear_mode": "shadow",
#   "forward_catalyst_bull_threshold": 0.60,
#   "forward_catalyst_bear_threshold": 0.50,
#   "forward_catalyst_model": "claude-opus-4-7"
bash experiments/<id>/run.sh

# Compare bullish-bucket realized alpha
python scripts/analyze_backtest.py experiments/<id-A>/results.csv --holding-days 21
python scripts/analyze_backtest.py experiments/<id-B>/results.csv --holding-days 21
```

Treatment (B) should show fewer bullish commits (filter suppresses some) but a cleaner bullish bucket if the filter mechanism captures real signal. The retrospective evidence predicts +2.24pp net Δα improvement on the bullish bucket at default T=0.60. Document the cost addition in HYPOTHESIS.md per Constitution III (treatment B incurs ~$0.025/propagate).

---

## Walkthrough 7 — what the filter does and doesn't catch

| Failure pattern | Backward filters (A3 / 003 / 003.5 / 004 / 006) | Spec 007 forward-catalyst |
|---|---|---|
| Bear commits on already-down tickers | A3 | — |
| Bull commits with high prose-density (within-ticker mean reversion) | Spec 003 | — |
| Bull commits with high prose-density on cold-start tickers | Spec 003.5 | — |
| Bull commits when sector ETF is in mean-reversion zone | Spec 004 (default-off; -0.45pp/n=73) | — |
| Bear commits on tickers rallying vs sector | Spec 006 (default-off; -0.71pp/n=36) | — |
| Bull commits where the bull case is already widely accepted | — | **Spec 007 bull-side (default-on)** |
| Bear commits where the bear case is already widely accepted | — | **Spec 007 bear-side (default-shadow)** |
| Bull commits underperforming a rising sector (5th failure mode, ticker_weak cohort) | None catches | **Spec 007 bull-side (88.9% cohort hit rate per Opus retrospective)** |
| Bear commits with +28%-mean-α counter-trend rallies (ticker_strong cohort) | None catches | **Spec 007 bear-side (72% cohort hit rate; shadow-mode for now)** |

Spec 007 fills the gap that the 5 backward-price filters couldn't reach because forward catalysts (earnings, guidance, news) are not visible in backward price patterns. The LLM synthesis IS visible to those catalysts via the analyst reports.

---

## Walkthrough 8 — Constitution v1.4.0 amendment

After spec 007 lands, Constitution Principle VIII has TWO sub-sections:

1. **Backward-price-filter validation gate** (original v1.3.0): net Δα ≥ +1pp + cohort hit rate ≥ 40%
2. **Forward-catalyst-class validation gate** (v1.4.0 added): discrim ≥ +5pp (PRIMARY) + cohort hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first

Future filters of either class follow their respective gate. Mixed-class filters (e.g., a hybrid LLM + price feature) follow whichever gate is stricter.

The amendment is committed AS PART OF spec 007 implementation (FR-015 + SC-009), not separately. CHANGELOG.md entry references the amendment + spec 007 as the trigger.

---

## Prerequisites for bear-side default-on flip

Per Constitution VIII v1.4.0 shadow-mode-first condition:

1. **Shadow-mode observation period (n≥20 fresh propagates)**: operator runs the framework with `bear_mode="shadow"` (the default) for at least 20 propagates that produce bearish pre-ratings. Each `state["forward_catalyst"]["would_fire_bear"]` annotation is captured.
2. **Net Δα measurement on shadow-mode data**: compute realized 21d α for each `would_fire_bear=True` propagate. If the observed mean α is positive (i.e., the bear call would have been wrong), the filter would have correctly suppressed.
3. **Decision criterion**: if observed bear-side net Δα ≥ +0.5pp on the n≥20 fresh propagates, flip `bear_mode = "active"` in a separate commit. Document the flip in HYPOTHESIS.md per Constitution II + III.
4. **Re-run SC-008 retrospective** at the new active-mode default to confirm the flip is empirically justified at the production-config (not just the retrospective-config).

If the observed net Δα is < +0.5pp, the bear-side stays default-shadow as an operator-opt-in tool. Mirrors the spec 004 / spec 006 default-off outcome.

---

## Troubleshooting

### `state["forward_catalyst"]` is missing entirely

- BOTH `forward_catalyst_bull_mode` AND `forward_catalyst_bear_mode` are `"off"`. Set at least one to `"shadow"` or `"active"`.

### Annotation shows `skipped="llm_failed"`

- LLM call raised an exception. Check `error` field for the exception summary. Common causes: API key not set, network error, rate limit. The filter degrades cleanly per FR-010; rating is unchanged. Re-run the propagate to retry.

### Annotation shows `skipped="invalid_threshold"`

- One or both thresholds are outside [0, 1]. Check `forward_catalyst_bull_threshold` + `forward_catalyst_bear_threshold` config; reset to defaults (0.60 / 0.50) or values within [0, 1].

### Filter never fires even though scores are clearly above threshold

- Check `bull_mode` / `bear_mode`: `"shadow"` annotates without firing; `"active"` fires.
- Bear-side default is `"shadow"` (NOT active) — bear commits will NOT be suppressed unless operator explicitly flips `bear_mode = "active"`.
- Inspect a specific propagate's annotation: `jq '.forward_catalyst.bull_case_priced_in, .forward_catalyst.bull_threshold, .forward_catalyst.fired_bull' <state-log>`. If `bull_case_priced_in <= bull_threshold` OR `fired_bull == false`, the filter (correctly) didn't fire.

### Cost is higher than expected

- Verify `forward_catalyst_model` setting. Opus default is ~$0.025/call; Haiku alternative is ~$0.0025/call (10× cheaper).
- Per-propagate cost ≈ `(forward_catalyst_bull_mode != "off" OR forward_catalyst_bear_mode != "off") × $0.025`. Setting BOTH modes to `"off"` zeroes the cost (FR-009 + SC-006).
- Verify the per-propagate cost via `pytest tests/test_forward_catalyst_filter.py::test_per_call_cost_ceiling -v` (mocks the cost-tracker).

### Spec 007 fires on a propagate where prior filters already overrode to Hold

- Per FR-002 + the data-model state-transition diagram: the filter still calls the LLM (annotation captured for audit) but both bull-side and bear-side branches no-op when pre-rating is Hold (Hold is neither bullish nor bearish). The annotation will show `would_fire_bull=False AND would_fire_bear=False AND fired_bull=False AND fired_bear=False`. This is expected behavior, not a bug.

---

## What this filter does NOT do

- Override Hold ratings — per FR-002, only acts on Buy/Overweight (bull side) or Underweight/Sell (bear side).
- Upgrade ratings to Buy/OW from Hold — per FR-007, suppression target is always Hold; never flip-to-bullish.
- Cache LLM responses — per-propagate uniqueness; cache would invalidate on re-run anyway.
- Modify the AnthropicClient or the LLM factory — uses `tradingagents.llm_clients.factory.create_llm_client` per R-1.
- Touch the spec 003 / spec 004 / spec 006 firing logic — independent filter; runs LAST in the chain per FR-012.
- Persist anything beyond the `state["forward_catalyst"]` annotation — uses the existing `_log_state` whitelist + AgentState TypedDict pattern.
- Fire when both modes are `"off"` — zero LLM call, zero cost (FR-009 + SC-006).

---

## Reading list

- `specs/006-forward-catalyst-gate/spec.md` — full feature spec
- `specs/006-forward-catalyst-gate/data-model.md` — entity definitions + state transitions + invariants
- `specs/006-forward-catalyst-gate/contracts/annotation_schema.md` — annotation schema + worked examples
- `specs/006-forward-catalyst-gate/contracts/filter_function.md` — filter function contract
- `specs/006-forward-catalyst-gate/research.md` — design decisions (R-1..R-11)
- `claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md` — design exploration that led to this spec
- `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` — empirical-PASS evidence (DECISIVE bull-side; shadow-mode-first bear-side)
- `claudedocs/forward-catalyst-class3-retrospective-2026-05-06.md` — initial Haiku-borderline retrospective (Opus comparison context)
- `.specify/memory/constitution.md` Principle VIII (v1.4.0) — codified validation gate (both backward-price + forward-catalyst classes)
- `tradingagents/agents/utils/momentum_filter.py` — A3 (sibling filter; bear/per-ticker absolute)
- `tradingagents/agents/utils/sector_momentum_filter.py` — Spec 004 (sibling filter; bull/sector ETF absolute, default-off)
- `tradingagents/agents/utils/bear_sector_symmetry_filter.py` — Spec 006 (sibling filter; bear/ticker-vs-sector relative, default-off)
- `tradingagents/signals/contrarian_gate.py` — Spec 003 / 003.5 (sibling filter; bull/prose-density)
- `tradingagents/agents/utils/second_opinion.py` — Phase C precedent for adding LLM calls inside PM hooks (pattern source for spec 007's structured-output handling)
