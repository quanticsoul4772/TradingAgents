# ANALYSIS template — wc11-order-randomization

> **STATUS**: TEMPLATE awaiting data. When the experiment completes (~3h after kickoff per PR #171), replace `<TBD>` placeholders with computed values, fill the matching verdict block, delete the other 2 verdict blocks, and rename this file to `ANALYSIS.md`.

**Experiment ID**: `2026-05-08-004-wc11-order-randomization`
**Created**: 2026-05-08 (template draft); pilot launched 2026-05-09 per PR #171
**Predecessors**:
- HYPOTHESIS + PARAMS scaffold (PR #148)
- Pilot harness (PR #171, `scripts/wc11_order_pilot.py`)
- Triple-pilot landing playbook (PR #172) for cross-pilot coordination

## Headline verdict (TBD post-data)

**Verdict**: <NULL | ALT-A | ALT-B>

<!-- One-paragraph plain-English summary picked from the matching verdict
block below. -->

## Per-permutation results

| Permutation | n | Buy/OW | Hold | UW/Sell | Mean rating-attributed α | Notes |
|---|---:|---:|---:|---:|---:|---|
| `market_news_fundamentals` (DEFAULT) | 5 | <TBD> | <TBD> | <TBD> | <TBD> | First analyst: market |
| `news_fundamentals_market` | 5 | <TBD> | <TBD> | <TBD> | <TBD> | First: news; Last: market |
| `fundamentals_market_news` | 5 | <TBD> | <TBD> | <TBD> | <TBD> | First: fundamentals; Last: news |
| `market_fundamentals_news` | 5 | <TBD> | <TBD> | <TBD> | <TBD> | First: market; Last: news |

## Per-first-analyst aggregation (SECONDARY)

Group propagates by FIRST analyst across permutations:

| First analyst | n | Buy/OW count | Hold count | UW/Sell count | Distribution shift vs pooled mean |
|---|---:|---:|---:|---:|---:|
| market | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>pp |
| news | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>pp |
| fundamentals | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>pp |

ALT-A trigger: any first-analyst's distribution differs by ≥20pp from the pooled mean across all 4 permutations.

## Per-last-analyst aggregation (TERTIARY)

| Last analyst | n | Buy/OW count | Hold count | UW/Sell count | Distribution shift vs pooled mean |
|---|---:|---:|---:|---:|---:|
| market | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>pp |
| news | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>pp |
| fundamentals | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>pp |

ALT-B trigger: any last-analyst's distribution differs by ≥20pp.

## Verdict-conditional analysis blocks

When the data lands, KEEP the matching block + DELETE the other two.

### Block NULL (apply if no first-analyst OR last-analyst distribution differs by ≥20pp from pooled mean)

> **SC-007 falsification: NULL — synthesis is order-robust.**
>
> WC-11 ran 5 dates × NVDA × 4 permutations (20 propagates / $8). Per-permutation rating distribution stayed within ±10pp of pooled mean across all 4 orderings. Per-first-analyst aggregation: market-first <X>%, news-first <Y>%, fundamentals-first <Z>% — max distribution shift <FILL: max delta>pp (below 20pp ALT-A threshold). Per-last-analyst aggregation similarly within ±10pp.
>
> **Implication**: the framework's analyst synthesis is order-robust at the rating distribution level. Prior corpus claims using the fixed `[market, news, fundamentals]` order are NOT confounded by first-speaker or last-speaker bias.
>
> **Constitution implication**: NONE. WC-11 retired as a corpus-confounder concern.
>
> **CHANGELOG entry**: "WC-11 ruled out — synthesis order-robust at n=20."

### Block ALT-A (apply if any first-analyst distribution differs by ≥20pp from pooled)

> **SC-007 falsification: ALT-A — first-speaker bias detected.**
>
> WC-11 ran 5 dates × NVDA × 4 permutations (20 propagates / $8). Per-first-analyst rating distribution shows <FILL: which analyst's first-position> produces a distribution shift of <FILL: pp magnitude>pp from the pooled mean — exceeds 20pp ALT-A threshold.
>
> **Implication**: EVERY prior corpus claim using the fixed `[market, news, fundamentals]` order is confounded by first-speaker bias toward whatever rating the market analyst's framing tends to produce. Re-interpretation of prior bucket-level claims required.
>
> **Constitution implication**: Constitution VII Replicability-scope sub-section needs amendment to flag analyst-order as a load-bearing methodological variable. Possible v1.5.1 → v1.5.2 PATCH.
>
> **Operational implication**: future ablations should randomize analyst order within the cohort OR explicitly fix the order and document it as a confounder.

### Block ALT-B (apply if any last-analyst distribution differs by ≥20pp from pooled)

> **SC-007 falsification: ALT-B — last-speaker (recency) bias detected.**
>
> WC-11 ran 5 dates × NVDA × 4 permutations (20 propagates / $8). Per-last-analyst rating distribution shows <FILL: which analyst's last-position> produces a distribution shift of <FILL: pp magnitude>pp from the pooled mean — exceeds 20pp ALT-B threshold.
>
> **Implication**: same as ALT-A but for last analyst's framing (recency effect). EVERY prior corpus claim using `[market, news, fundamentals]` order confounded by last-speaker bias toward fundamentals-framed conclusions.
>
> **Constitution implication**: Constitution VII Replicability-scope sub-section amendment (analogous to ALT-A but for last-speaker). Possible v1.5.1 → v1.5.2 PATCH.

## Constitution adherence checklist

- [ ] I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / wc11_pilot_memory.md isolated to this dir
- [ ] II (One Experiment Per Change): single intervention (analyst order); no other variables changed across permutations
- [ ] III (Stay Cheap): T1 ($8 within ≤$10)
- [ ] IV (No Production Claims): NULL / ALT-A / ALT-B all valid findings
- [ ] VI (Spec Before Structural Change): N/A — no structural change (Option B harness avoids it)
- [ ] VII (Calibrated Abstention v1.5.1): orthogonal at outcome — but ALT-A or ALT-B verdict triggers a v1.5.2 PATCH amendment
- [ ] VIII (Retrospective gate): N/A — not a filter

## Next steps (verdict-conditional; populate after data lands)

<TBD per verdict — possibilities include:>

1. **If NULL**: retire WC-11 as a concern; CHANGELOG entry; close Tier 1 candidates queue (last one). RESEARCH_FINDINGS Open Questions update marks the WC-11 row as RESOLVED.
2. **If ALT-A** (first-speaker bias): draft Constitution v1.5.2 amendment to Principle VII Replicability-scope sub-section. Update RESEARCH_FINDINGS to flag prior corpus claims as confounded. Per triple-landing playbook (PR #172), this amendment lands FIRST (most foundational; sequence per Constitution VI v1.4.1).
3. **If ALT-B** (last-speaker bias): same as ALT-A but for last-analyst recency effect. Constitution v1.5.2 PATCH likely with different paragraph framing.

## Cross-references

- **PR #148** — HYPOTHESIS + PARAMS scaffold
- **PR #171** — pilot harness + launch
- **PR #172** — triple-pilot landing playbook (cross-pilot coordination + Constitution amendment sequencing)
- **PR #145** — EXPERIMENT.md backlog review (flagged WC-11 as last Tier 1 candidate)
- Memory `reference_pre_rating_temporal_learning.md` — analogous question to "input-order PM rating drift" but at temporal scale
- Constitution VII Replicability-scope sub-section — bucket-level claims replicate, date-level don't (might be partly explained by order effects under ALT-A or ALT-B)

## Estimated time-to-PR

With this extended pre-scaffolding:

| Step | Time |
|---|---|
| Run computation snippet (group by permutation; aggregate by first/last analyst) | 5 min |
| Pick matching verdict block (KEEP one, DELETE two) | 2 min |
| Plug in `<FILL: X>` numbers + per-permutation/first/last tables | 8 min |
| Update Constitution adherence checklist | 2 min |
| Update Next-steps section | 3 min |
| Open PR | 5 min |
| **Total** | **~25 min** |

vs ~45 min if drafting ANALYSIS from scratch without this template.

## Cost

$0 codification (template). Pilot itself was $8 (PR #171).
