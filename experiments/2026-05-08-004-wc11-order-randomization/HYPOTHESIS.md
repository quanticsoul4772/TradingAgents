# WC-11 Order Randomization HYPOTHESIS

**Experiment ID**: `2026-05-08-004-wc11-order-randomization`
**Source idea**: WC-11 (per `docs/EXPERIMENT.md` Tier 1 — last unrun Tier 1 candidate per `claudedocs/experiment-md-tier-2-3-review-2026-05-08.md` PR #145)
**Date**: 2026-05-08 (scaffold; launch deferred pending operator decision)

> **STATUS**: SCAFFOLD ONLY — HYPOTHESIS + PARAMS drafted; experiment NOT yet launched. Operator decides whether to invoke. Cost when launched: ~$8 (T1, ≤$10).

## Question

Does the order in which analysts run (market / news / fundamentals / social) affect the framework's rating distribution? If yes, the "first speaker" effect is a hidden bias that confounds every prior corpus claim. If no, analyst order is genuinely independent and we can stop worrying about it.

EXPERIMENT.md original framing (2026-05-01): "randomize analyst order, debate order, see if 'first speaker' effects exist. Probably do."

This scaffold focuses on **analyst order only** for v1 (debate order = bull/bear is structurally fixed by LangGraph topology and would require broader changes; analyst order is a config-level shuffle). Debate order randomization deferred to v2 if v1 surfaces a first-speaker effect.

## Three predictions

| Prediction | What it means | Empirical signature |
|---|---|---|
| **NULL** (no order effect) | Rating distribution + realized α stable across analyst-order permutations on the same dates. The framework's synthesis is robust to input order. | Per-permutation rating distribution within ±10pp of pooled mean; signed-permutation × α correlation < ±0.2 |
| **ALT-A (first-speaker bias)** | First analyst's rating influences the PM's commit. Permutations starting with `market` produce different distributions than permutations starting with `news` or `fundamentals`. | Per-first-analyst rating distribution differs by ≥20pp from pooled mean for at least one analyst; statistically detectable at n=20 |
| **ALT-B (last-speaker bias)** | Last analyst's rating influences the PM's commit (recency effect). Permutations ending with each analyst tested. | Same as ALT-A but per-LAST-analyst |

ALT-A + ALT-B are mutually exclusive (in expectation; reality may show partial both).

## Test grid

5 dates × 1 ticker (NVDA) × 4 permutations = **20 propagates**.

- **Ticker**: NVDA only (matches v1 + WC-10 cohort for cross-experiment comparison)
- **Dates** (5, weekly Fridays from Q1 2026): 2026-01-30, 2026-02-13, 2026-02-27, 2026-03-13, 2026-03-27 (5 evenly-spaced dates so no calendar-clustering)
- **Permutations** (4 of 24 possible orderings, chosen to maximize first-and-last analyst variation):
  - `[market, news, fundamentals]` — DEFAULT (current production order)
  - `[news, fundamentals, market]` — news-first / market-last
  - `[fundamentals, market, news]` — fundamentals-first / news-last
  - `[market, fundamentals, news]` — market-first / news-last (pivot of default)

Note: drops `social` analyst per CLAUDE.md "yfinance social data is just yfinance news again" + matches v1 + v2 + v3 design (3 analysts).

## Cost estimate

20 propagates × ~$0.40 = **~$8 LLM**. Constitution III T1 (≤$10).

## Headline metrics

1. **(Primary) Per-permutation rating distribution** — count of {Buy/OW/Hold/UW/Sell} per permutation. Test for distribution shifts ≥20pp.
2. **(Secondary) Per-first-analyst rating attribution** — group by first analyst (market / news / fundamentals); compute commit rate, mean rating tier, mean α.
3. **(Tertiary) Realized 21d α per permutation** — does any permutation outperform the default `[market, news, fundamentals]`?

## Falsification verdict (per the 3-prediction framework)

Determined post-run; documented in `ANALYSIS.md`. Possible verdicts:

- **NULL** — rating distribution is order-independent. Default order is fine; no need to randomize.
- **ALT-A confirmed** — first-speaker effect detected. The corpus's prior claims were confounded by the fixed `[market, news, fundamentals]` order; future ablations should randomize.
- **ALT-B confirmed** — last-speaker effect detected. Same implication as ALT-A for confounding.
- **MIXED / INCONCLUSIVE at n=20** — observed effects are within noise floor. Recommend re-run at n=40 if any directional pattern.

## Implementation approach (operator notes when launching)

The framework currently hardcodes analyst order in `tradingagents/graph/setup.py`. Two implementation options:

### Option A: New config key `analyst_order_seed: int | None`

Add a config key that, when set, shuffles `selected_analysts` deterministically before passing to `setup_graph()`. Add ~5 lines in `trading_graph.py` __init__:

```python
if self.config.get("analyst_order_seed") is not None:
    import random
    rng = random.Random(self.config["analyst_order_seed"])
    selected_analysts = list(selected_analysts)
    rng.shuffle(selected_analysts)
```

Pros: minimal change; default behavior unchanged.
Cons: requires structural change to trading_graph.py.

### Option B: Direct `--analysts` flag in pilot harness

Reuse `scripts/wc_10_pilot.py`'s `--tickers` / `--dates` pattern but add `--analysts <comma-list>` flag that overrides DEFAULT analysts via config. The harness already supports per-mode config overrides (mode list could be the 4 permutations).

```bash
python scripts/wc11_order_pilot.py \
  --tickers NVDA \
  --dates 2026-01-30,2026-02-13,2026-02-27,2026-03-13,2026-03-27 \
  --modes "market_news_fundamentals,news_fundamentals_market,fundamentals_market_news,market_fundamentals_news" \
  --out experiments/2026-05-08-004-wc11-order-randomization/results.csv \
  --yes
```

Pros: zero structural code change; uses existing harness pattern.
Cons: needs new pilot harness (~80 LOC, similar to wc_10_pilot.py).

**Recommendation**: Option B (new pilot harness following wc_10_pilot.py pattern). Avoids structural code change per Constitution VI; matches the existing pilot pattern that's been validated (v1 + v2 + v3).

## Constitution adherence

- ✅ I (Save Everything): per-propagate state log + this HYPOTHESIS + PARAMS + (when launched) results.csv + ANALYSIS.md
- ✅ II (One Experiment Per Change): single intervention (analyst order). Debate order randomization deferred to v2.
- ✅ III (Stay Cheap): T1 (≤$10) at $8
- ✅ IV (No Production Claims): NULL is a valid finding; would retire WC-11 as a concern
- ✅ VI (Spec Before Structural Change): Implementation Option B avoids structural change (new pilot harness only); no spec needed
- ✅ VII (Calibrated Abstention): orthogonal — order randomization tests synthesis robustness, not Hold-rate

## Cross-references

- `docs/EXPERIMENT.md` WC-11 (Tier 1 still-open as of 2026-05-08)
- `claudedocs/experiment-md-tier-2-3-review-2026-05-08.md` — flagged WC-11 as Tier 1 last-remaining
- Constitution VII Replicability-scope sub-section — "bucket-level claims replicate, date-level don't" finding might be partly explained by order effects
- Memory `reference_pre_rating_temporal_learning.md` — week-over-week PM rating drift; analogous question to "input-order PM rating drift"

## Operational note

This is a SCAFFOLD. Launching requires:

1. Operator authorization (~$8 cost is sub-T2 but still requires explicit decision)
2. Either Option A (3-line trading_graph.py change) or Option B (new ~80 LOC pilot harness)
3. Background task launch + monitor armed (mirror v2/v3 pattern)
4. ANALYSIS.md write-up post-data (use the 3-prediction verdict framework above)

Estimated wall-clock: 20 propagates × ~9 min = ~3 hours.
