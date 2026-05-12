# Amendment: SC-007 — drop ±5%-vs-Anthropic-billing requirement

**Spec**: 250-dashboard-ui
**Gap closed**: G-6 (per `plan.md`)
**Date**: 2026-05-11
**Status**: Operator-directed amendment.

## Original SC-007 wording

> **SC-007**: End-to-end smoke — dry-run mode (engine emits fake events without LLM calls per FR-008) validates dashboard renders correctly before live $10 run; live run produces ratings + portfolio updates + cost meter accuracy within ±5% of actual Anthropic billing.

## New SC-007 wording

> **SC-007** *(amended 2026-05-11 per `amendments/sc-007-drop-billing-comparison.md`)*: End-to-end smoke — dry-run mode (engine emits fake events without LLM calls per FR-008) validates dashboard renders correctly before any live run; the first live run produces ratings + portfolio updates + a non-zero cost-meter figure. The dashboard's `TokenCostCallback` is the operational ground truth for cost; an external Anthropic-billing comparison is out of scope (no API exists for that data; the per-call token-counts-times-published-pricing computation is internally consistent).

## Why amend, not validate

- **No API access**: Anthropic does not expose a per-account billing endpoint to API keys. Fetching the ±5% reference number requires manual operator action in the web console.
- **Operator does not want to do the manual step**: explicit direction on 2026-05-11.
- **Internal consistency is sufficient for single-operator use**: `TokenCostCallback` sums per-LLM-call token usage from `on_llm_end` events and multiplies by the `ANTHROPIC_PRICING_USD_PER_M` table in `tradingagents/engine/callbacks.py`. As long as the pricing table matches Anthropic's published rates (verified during PR #263 for Opus 4.7 + Haiku 4.5), the meter is accurate by construction. A drift would only arise if Anthropic silently changed pricing without the table being updated.
- **Pricing-table maintenance**: an out-of-spec follow-up should refresh `ANTHROPIC_PRICING_USD_PER_M` whenever Anthropic ships new model SKUs or price changes. That's an ongoing maintenance commitment, not a per-run validation gate.

## Live-run result (2026-05-11) for the record

| Field | Value |
|---|---|
| Run started | 2026-05-11 17:03 ET |
| Run finished | 2026-05-11 20:49 ET |
| Wall-clock | 3 hours 47 minutes |
| Tickers completed | 25 / 25 |
| Tickers failed | 0 |
| Dashboard cost meter | **$38.30** |
| Ratings | 0 Buy / 5 OW / 17 Hold / 3 UW / 0 Sell (32% commit rate) |
| Paper portfolio updated | per FR-007 (auto-spawned `paper_trade.py step` post-run) |

The $38.30 figure is the operational truth going forward. The original spec's "~$10/day" estimate is materially low and should be updated in a follow-up `spec.md` Assumptions section refresh (not in scope of this PR).

## Plan.md update

G-6 row: PENDING operator entry → CLOSED via amendment.
