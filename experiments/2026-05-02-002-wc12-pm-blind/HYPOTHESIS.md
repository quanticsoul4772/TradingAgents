# Hypothesis: wc12-pm-blind

**Experiment ID**: `2026-05-02-002-wc12-pm-blind`
**Created**: 2026-05-02
**Source idea**: WC-12 (from `docs/EXPERIMENT.md`)
**Cost estimate**: ~$5 (10 NVDA propagations × ~$0.50 each, ~70 min wall-clock)

## What we're testing

After **MR-1** confirmed bull/bear debates produce real adversarial argument (50.8% REAL_CONTRADICTION, 0% PARALLEL_MONOLOGUE across 65 pairs), the locus of TradingAgents' mode collapse must be **downstream of the debate**. The first downstream candidate is the **Research Manager's synthesis** of that debate into the `investment_plan` that the Portfolio Manager consumes.

Looking at the actual PM input chain (`tradingagents/agents/managers/portfolio_manager.py`), the PM receives:
1. `research_plan` — Research Manager's synthesis of bull/bear (the candidate dilution point)
2. `trader_plan` — Trader's transaction proposal
3. `risk_debate_state.history` — 3-way risk debate (Aggressive/Conservative/Neutral)
4. `past_context` — memory log

The PM never sees bull/bear directly. Whatever moderation enters the system on the synthesis step is what the PM consumes.

**Variant chosen for this experiment**: gate `research_plan` behind a config flag `pm_sees_synthesis` (default True = current behavior). Set to False to withhold the synthesis from the PM. Keep trader_plan, risk_debate_state, past_context unchanged. The PM is forced to build its own conclusion from the trader's directional proposal + the 3-way risk debate, without the Research Manager's pre-digested view.

## Why we expect ratings to shift toward stronger calls

If the synthesis is where moderation creeps in, then removing it should:
- **Increase rating extremity** — more Buy / Sell, fewer Hold
- **Match the underlying disagreement** that MR-1 confirmed exists in the bull/bear debate

**Predicted directional shift** vs the matched-date pilot baseline: ≥30% of runs change rating bucket; ≥1 of 10 runs produces a strong call (Buy or Sell) — vs the pilot's 0/65 baseline.

If the prediction holds, the synthesis IS the dilution step. The architectural fix is then targeted: redesign the Research Manager's synthesis prompt/structure rather than touching the PM, the debate, or the rating scale.

If the prediction is **wrong** (no rating distribution shift), the moderation lives somewhere else — likely the PM prompt itself or its memory-log conditioning. That points to **WC-12b** as the next experiment: strict PM-blind variant (strip ALL upstream context except raw analyst reports), a more invasive test.

## Why I'm using Variant B (synthesis-only-blind) not Variant A (strict per brainstorm)

The original brainstorm said *"strip the debate from the PM's input; PM only sees raw analyst reports"*. After MR-1, that's diagnostically blunt: if it works, we don't know whether the synthesis OR the trader plan OR the risk debate was the source. Variant B isolates the synthesis specifically.

If Variant B doesn't shift ratings, **then** Variant A becomes the right next test (it tells us whether the entire downstream apparatus is decorative). Save it for `WC-12b` next iteration.

## Success criterion

- [ ] 10 NVDA propagations run with `pm_sees_synthesis=False`; results CSV produced
- [ ] Matched comparison against the existing pilot data (same 10 NVDA dates if available)
- [ ] Rating distribution table: synthesis-blind vs baseline, side-by-side counts
- [ ] At least 1 distinct rating change documented (with quote from PM rationale showing how the absence of synthesis changed reasoning)
- [ ] Decision recorded: confirms or refutes the synthesis-as-dilution-step hypothesis

## Notes

- **Implementation approach**: add `pm_sees_synthesis: bool = True` to `default_config.py`; gate the `research_plan` line in `portfolio_manager.py` behind that flag. Default behavior unchanged. Use `--config-override pm_sees_synthesis=false` to flip it for this experiment. The new experiments-scaffolding's `--config-override` flag does exactly this — first real use of the auto-sync feature.
- **Why NVDA + matched dates**: NVDA had 13 dates in the pilot, the most data per ticker. We can pick 10 of those same dates to get a matched comparison without spending money on a baseline rerun. Dates: 2026-01-30 + 2026-02-06 through 2026-04-10 (skipping 2026-04-17 and 2026-04-24 to keep at 10).
- **Sample size**: n=10 is small. Won't reach statistical significance on the rating distribution comparison; we're looking for **direction** (more strong calls → confirms hypothesis) not p-values.
- **What this doesn't change**: bull/bear debate, research_manager.py, trader.py, risk debaters. Only the PM's input dict.

## Related experiments

- **MR-1** (`experiments/2026-05-02-001-mr1-contradiction/`) — established that bull/bear debate is real, motivating this experiment.
- **Future WC-12b** — strict-reading PM-blind (strip everything above raw analyst reports). Run if WC-12 doesn't shift ratings.
- **Future MR-2** — Research Manager synthesis instrumentation. Useful regardless of WC-12 outcome.
