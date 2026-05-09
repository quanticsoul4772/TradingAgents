# ANALYSIS template — WC-11 v2 disambiguation

> **STATUS**: TEMPLATE awaiting data. When `results.csv` reaches 60 rows,
> replace `<TBD>` placeholders, pick matching verdict block (KEEP one,
> DELETE other 4), rename to `ANALYSIS.md`.

**Experiment ID**: `2026-05-09-002-wc11-v2-disambiguation`
**Created**: 2026-05-09
**Predecessor**: v1 ANALYSIS at `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md` (PR #177)

## Headline verdict (TBD post-data)

`<TBD>` — selected from {NULL revised, ALT-A confirmed, ALT-B confirmed, PARTIAL (v1 reproduces), INCONCLUSIVE} per HYPOTHESIS framework.

## Per-permutation × per-ticker commit rate matrix

| Permutation | NVDA | AAPL | MSFT | Pooled |
|---|---:|---:|---:|---:|
| market_news_fundamentals (DEFAULT) | <TBD>% | <TBD>% | <TBD>% | <TBD>% |
| news_fundamentals_market | <TBD>% | <TBD>% | <TBD>% | <TBD>% |
| fundamentals_market_news | <TBD>% | <TBD>% | <TBD>% | <TBD>% |
| market_fundamentals_news | <TBD>% | <TBD>% | <TBD>% | <TBD>% |

## Cross-rerun-variance check (NVDA only)

v1 (n=20) per-permutation commit rate vs v2 NVDA (n=20):

| Permutation | v1 commit % | v2 NVDA commit % | Δ |
|---|---:|---:|---:|
| market_news_fundamentals | 20% | <TBD>% | <TBD> |
| news_fundamentals_market | 40% | <TBD>% | <TBD> |
| fundamentals_market_news | 20% | <TBD>% | <TBD> |
| market_fundamentals_news | 0% | <TBD>% | <TBD> |

## Computation snippet

```python
import csv
from collections import defaultdict

ROWS = []
with open("experiments/2026-05-09-002-wc11-v2-disambiguation/results.csv") as f:
    for r in csv.DictReader(f):
        if not r["error"]:
            ROWS.append(r)

per_perm_per_ticker = defaultdict(lambda: defaultdict(list))
for r in ROWS:
    per_perm_per_ticker[r["mode"]][r["ticker"]].append(r["rating"])

print(f"{'Perm':<30} {'NVDA':>8} {'AAPL':>8} {'MSFT':>8} {'Pooled':>8}")
COMMITS = {"Buy", "Overweight", "Underweight", "Sell"}
for perm in ["market_news_fundamentals", "news_fundamentals_market",
             "fundamentals_market_news", "market_fundamentals_news"]:
    pooled = []
    rates = {}
    for t in ("NVDA", "AAPL", "MSFT"):
        ratings = per_perm_per_ticker[perm][t]
        n = len(ratings)
        commits = sum(1 for r in ratings if r in COMMITS)
        pct = 100 * commits / max(1, n)
        rates[t] = pct
        pooled.extend(ratings)
    pool_n = len(pooled)
    pool_commits = sum(1 for r in pooled if r in COMMITS)
    pool_pct = 100 * pool_commits / max(1, pool_n)
    print(f"{perm:<30} {rates['NVDA']:>7.0f}% {rates['AAPL']:>7.0f}% {rates['MSFT']:>7.0f}% {pool_pct:>7.0f}%")
```

## Verdict-conditional next-steps blocks

### If verdict NULL (v1 was stochastic noise)

1. **Constitution implication**: REVERT the v1.5.2 "Analyst-order scope" mandate; restore v1.5.1
2. **Memory entry**: update `reference_wc11_analyst_order_first_speaker_bias.md` with NULL refutation
3. **RESEARCH_FINDINGS update**: WC-11 section refresh — ALT-A + ALT-B disambiguated as STOCHASTIC; analyst-order is NOT a confounder
4. **Spec implication**: NONE — WC-11 line closes

### If verdict ALT-A confirmed (news-first bias)

1. **Constitution implication**: Strengthen v1.5.2 — REQUIRE news-first analyst order as default OR document operator opt-in via `selected_analysts = ["news", "market", "fundamentals"]`
2. **Spec amendment**: ship a config-default-flip PR analogous to Spec 008 default-on flip (cite ALT-A evidence)
3. **Memory entry**: extend `reference_wc11_analyst_order_first_speaker_bias.md` with ALT-A confirmation at scale
4. **RESEARCH_FINDINGS update**: bullet finding #N (analyst-order has first-speaker effect; news-first elevates commits by ±15pp)

### If verdict ALT-B confirmed (last-speaker recency bias)

1. **Constitution implication**: Strengthen v1.5.2 — REQUIRE the analyst-position rotation OR document last-position as confounder
2. **Spec amendment**: similar to ALT-A but reversing the recommendation direction
3. **Memory entry**: ALT-B confirmation; v1 ambiguity disambiguated as recency bias
4. **RESEARCH_FINDINGS update**: bullet finding (last-speaker effect dominates)

### If verdict PARTIAL (v1 reproduces only on NVDA)

1. **Implication**: ticker-specific interaction — analyst-order effect is conditional on (model × ticker × regime)
2. **Constitution implication**: v1.5.2 mandate stays AS-IS (randomize-or-document); not strengthened
3. **Memory entry**: update with ticker-specific finding; conditional effect documented
4. **RESEARCH_FINDINGS update**: WC-11 section refresh — analyst-order effect is ticker-conditional, not framework-general

### If verdict INCONCLUSIVE (v2 fails to reproduce v1 NVDA pattern)

1. **Implication**: stochastic LLM variance dominates at n=60; even larger n needed
2. **Constitution implication**: v1.5.2 mandate STAYS but flag for re-examination at n=200+
3. **Memory entry**: cross-rerun-variance is HIGHER than expected; v1 result was noise
4. **Spec implication**: NONE — defer further investigation; document as stochastic-variance-dominated finding

## Constitution adherence checklist

- [ ] I (Save Everything): isolated experiment dir
- [ ] II (One Experiment Per Change): single intervention
- [ ] III (Stay Cheap): T2 ($24)
- [ ] IV (No Production Claims): NULL/INCONCLUSIVE valid
- [ ] VI: N/A
- [ ] VII v1.5.2: cross-references the v1.5.2 mandate this experiment stress-tests

## Cross-references

- v1 ANALYSIS: `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md`
- Sister BR-3 v2 cohort: `experiments/2026-05-09-003-br3-v2-news-fundamentals/`
- Dual-pilot landing playbook: `claudedocs/dual-pilot-launch-playbook-2026-05-09.md`
