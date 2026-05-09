# HYPOTHESIS — WC-11 v2 disambiguation (cross-ticker + cross-rerun)

**Experiment ID**: `2026-05-09-002-wc11-v2-disambiguation`
**Created**: 2026-05-09
**Source idea**: WC-11 v2 (per `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md` PR #177 + ROADMAP Open Questions row).
**Cost**: $24 LLM (60 propagates × ~$0.40; Constitution III T2-boundary).
**Authorization**: explicit user authorization 2026-05-09 evening.

## Why this experiment

WC-11 v1 (n=20; NVDA only × 4 permutations) found PARTIAL ALT-A + ALT-B — both triggers fire on the same `news_fundamentals_market` permutation (which has BOTH news-first AND market-last). Cannot disambiguate first-speaker vs last-speaker bias at n=20 single-ticker.

v2 extends to **3 tickers × 5 dates × 4 perms = 60 propagates** to:

1. **Cross-rerun-variance check** for NVDA (does v1 result reproduce when re-run? confirms the v1 pattern wasn't stochastic noise)
2. **Cross-ticker generalization** to AAPL (bear-side amplifier per WC-10 v1) + MSFT (bullish per WC-10 v2)
3. **Disambiguate ALT-A vs ALT-B** by observing the per-permutation pattern across 3 tickers

## Mechanism

Same harness as v1 (`scripts/wc11_order_pilot.py`) — varies `selected_analysts` parameter at TradingAgentsGraph construction. No structural code change to trading_graph.py.

Permutations (same 4 from v1):
- `market_news_fundamentals` (DEFAULT)
- `news_fundamentals_market` (news first AND market last; v1's elevated cohort)
- `fundamentals_market_news`
- `market_fundamentals_news` (v1's lowest-commit cohort)

Tickers:
- NVDA (REPEAT from v1; cross-rerun-variance check)
- AAPL (NEW; bear-side-amplifier per WC-10 v1)
- MSFT (NEW; bullish per WC-10 v2)

## Falsification framework

| Verdict | Trigger | Implication |
|---|---|---|
| **NULL (revised)** | All 4 perms within ±10pp of pooled commit rate across 3 tickers | v1 was stochastic noise; could revert v1.5.2 mandate |
| **ALT-A confirmed** | News-first elevates ≥+15pp vs DEFAULT across ≥2/3 tickers | First-speaker bias ratified at scale |
| **ALT-B confirmed** | Market-last drops ≤-15pp vs DEFAULT across ≥2/3 tickers | Last-speaker (recency) bias confirmed |
| **PARTIAL** | v1 NVDA pattern reproduces but AAPL/MSFT differ | Ticker-specific interaction; conditional effect |
| **INCONCLUSIVE** | v2 fails to reproduce v1 NVDA pattern | n=60 too thin; defer further work |

## Success criterion

- [ ] 60/60 propagates resolved; per-permutation × per-ticker commit rates computed; verdict selected per the 5-branch framework above.

## Notes

Pre-scaffolding: ANALYSIS_TEMPLATE.md will accompany this HYPOTHESIS with all 5 verdict-conditional branches per `reference_conditional_branch_spec_pattern.md`. Landing playbook for the dual BR-3 v2 + WC-11 v2 launch coordination is sister artifact.

## Related experiments

- v1: `experiments/2026-05-08-004-wc11-order-randomization/`
- Sister BR-3 v2 cohort: `experiments/2026-05-09-003-br3-v2-news-fundamentals/` (in same launch authorization batch)
- Pilot harness: `scripts/wc11_order_pilot.py`
