# Dual-pilot launch playbook — WC-11 v2 + BR-3 v2 (2026-05-09)

**Date**: 2026-05-09 (evening launch; results land ~2026-05-10)
**Authorization**: explicit user authorization for $40 LLM total ($24 WC-11 v2 + $16 BR-3 v2)
**Status**: launches IN FLIGHT (background); landing playbook applies post-completion.

## In-flight pilots

| Pilot | Cost | Cohort | Background ID | Estimated wall-clock |
|---|---:|---|---|---|
| **WC-11 v2** disambiguation | $24 | 3 tickers (NVDA + AAPL + MSFT) × 5 dates × 4 perms = 60 propagates | `bwzris458` | ~12h |
| **BR-3 v2** news + fundamentals | $16 | 2 tickers × 5 dates × 4 modes (news_prose + news_structured + fund_prose + fund_structured) = 40 propagates | `bkpnb5www` | ~8h |
| **TOTAL** | **$40** | **100 propagates** | — | **~12h max** |

## Landing coordination (per triple-pilot playbook PR #172 precedent)

When BOTH pilots complete, execute landing in 3 phases:

### Phase 1: ANALYSIS for each pilot (parallel; ~30-45 min total)

Run computation snippets from ANALYSIS_TEMPLATE.md in each experiment dir:

```bash
# WC-11 v2 ANALYSIS
cd experiments/2026-05-09-002-wc11-v2-disambiguation
python -c "$(grep -A 50 'Computation snippet' ANALYSIS_TEMPLATE.md | tail -50)"
# Pick verdict from {NULL revised, ALT-A confirmed, ALT-B confirmed, PARTIAL, INCONCLUSIVE}
# Plug in numbers; rename ANALYSIS_TEMPLATE.md → ANALYSIS.md

# BR-3 v2 ANALYSIS
cd ../2026-05-09-003-br3-v2-news-fundamentals
python -c "$(grep -A 50 'Computation snippet' ANALYSIS_TEMPLATE.md | tail -50)"
# Pick verdict per sub-experiment from {NULL, ALT-A, ALT-B, PARTIAL ALT-B}; or DIFFERENTIAL
# Plug in numbers; rename to ANALYSIS.md
```

### Phase 2: Constitution amendment evaluation (~15 min)

| Pilot verdict | Constitution implication |
|---|---|
| WC-11 v2 NULL | REVERT v1.5.2 → v1.5.1 (analyst-order is NOT a confounder; v1 was stochastic) |
| WC-11 v2 ALT-A | Strengthen v1.5.2 (require news-first OR document operator opt-in) |
| WC-11 v2 ALT-B | Strengthen v1.5.2 (last-position confounder) |
| WC-11 v2 PARTIAL | v1.5.2 stays AS-IS (ticker-conditional finding) |
| WC-11 v2 INCONCLUSIVE | v1.5.2 stays; flag for n=200+ re-eval |
| BR-3 v2 ALT-B (either sub-exp) | Phase E architectural variant unblocked for that analyst — possible v1.6.0 amendment for Structured-output-throughout |
| BR-3 v2 NULL/PARTIAL | NO amendment |
| BR-3 v2 DIFFERENTIAL | document analyst-specific bottleneck; no broad amendment |

Constitution amendment ordering rule (per VI v1.4.1): WC-11 amendment lands FIRST if it requires REVERT or strengthen (most foundational; affects corpus interpretation).

### Phase 3: Landing PRs (~1.5h total)

Per triple-pilot landing playbook PR #172 disjoint-sections coordination:

1. **Constitution amendment** (if any) — single PR; cite both verdicts where relevant
2. **Joint RESEARCH_FINDINGS update** — both verdicts in disjoint sections (analogous to PR #180)
3. **WC-11 v2 ANALYSIS PR** — standalone
4. **BR-3 v2 ANALYSIS PR** — standalone (sub-experiment A + B together)
5. **Consolidated ROADMAP update** — both verdicts integrated
6. **Memory entries** — global-memory writes per cross-session record (1-2 entries)
7. **Final synthesis refresh** — `claudedocs/research-burst-2026-05-10.md` (next-day if applicable)

Estimated wall-clock from data-landing → all PRs merged: ~1.5-2h (per pre-scaffolded design surfaces).

## Pre-scaffolded artifacts (already shipped; reduce landing wall-clock)

- `experiments/2026-05-09-002-wc11-v2-disambiguation/HYPOTHESIS.md` + `PARAMS.json` + `ANALYSIS_TEMPLATE.md` (5 verdict-conditional branches)
- `experiments/2026-05-09-003-br3-v2-news-fundamentals/HYPOTHESIS.md` + `PARAMS.json` + `ANALYSIS_TEMPLATE.md` (5 verdict-conditional branches)
- `tradingagents/agents/analysts/news_analyst_structured.py` (NEW)
- `tradingagents/agents/analysts/fundamentals_analyst_structured.py` (NEW)
- `tradingagents/agents/schemas.py` — `render_analyst_squared(squared, analyst_name)` generic helper
- 2 new `TradingAgentsConfig` keys: `news_analyst_format` + `fundamentals_analyst_format`
- `tradingagents/graph/setup.py` — factory routing for news + fundamentals structured variants
- `scripts/br3_v2_pilot.py` (NEW)
- This playbook (PR #X — TBD)

## What COULD go wrong

| Failure mode | Mitigation |
|---|---|
| WC-11 v2 background crashes mid-run | Resume-on-crash via `_load_completed` in `wc11_order_pilot.py`; just re-launch with same `--out` |
| BR-3 v2 background crashes | Same resume-on-crash pattern in `br3_v2_pilot.py` |
| Anthropic rate limits | Pilot scripts already have 1s sleep between rows; if 429s persist, re-launch with manual back-off |
| `news_analyst_structured` ReAct loop never terminates | Same fallback as v1 — defensive prose fallback in module |
| Cost overrun beyond $40 | Pilot scripts respect `--yes` flag for cost confirmation; re-launching honors completed rows |
| Sister cohort completes much earlier | Land its ANALYSIS solo; the second cohort's landing PR can stack on top |

## Cost-discipline framing

$40 LLM is at Constitution III T2-boundary ($30-50). User explicit authorization documented in HYPOTHESIS.md for both pilots. Per cost-per-ship-quality-unit metric (PR #211), this batch contributes ~$40 to the project's cumulative spend (cumulative ~$93 across all of 2026-05-09 work).

Estimated ship-quality units from this dual-pilot batch:
- 2 ANALYSIS PRs
- 0-1 Constitution amendment PR
- 1 RESEARCH_FINDINGS update PR
- 1 ROADMAP update PR
- 1-2 memory entries
- 1 day-end synthesis refresh

= **6-7 ship-quality units**. Cost-per-unit: ~$5-7 (higher than today's overall ~$1.61 because the $40 is net-new spend, not amortized over pre-spent pilot data).

## Cross-references

- WC-11 v1: `experiments/2026-05-08-004-wc11-order-randomization/`
- BR-3 v1: `experiments/2026-05-09-001-br3-squeak-market-analyst/`
- Triple-pilot precedent playbook: `claudedocs/triple-pilot-landing-playbook-2026-05-09.md` (PR #172)
- Memory: `reference_speckit_5pr_vs_6pr_pattern.md` (bundle pattern for any spec drafting that follows)
- Memory: `reference_conditional_branch_spec_pattern.md` (verdict-conditional pre-scaffolding)
- Constitution VI v1.4.1 (spec ships its retrospective)
- Constitution VII v1.5.2 (the WC-11 mandate this pilot stress-tests)
