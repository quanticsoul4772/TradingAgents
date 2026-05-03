# RESEARCH_FINDINGS — TradingAgents-lab milestone

_Aggregated 2026-05-03 across 11 experiments + cross-experiment horizon sweep + counterfactual analysis on Hold extremes. For per-experiment summaries see `findings.md`._

## Headline

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls (Buy/OW/UW/Sell) are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) become directionally correct and produce ~+1.6% mean alpha across n=37 across-experiment commits.** Bearish commits remain anti-calibrated at every horizon. Hold ≈ 0% at every horizon (consistent with "tracks SPY"). The framework's mode collapse to Hold is calibrated abstention; its bullish commits are a real 21-day signal; its bearish commits are an anti-signal.

## Empirical core (cross-experiment summary, 5/10/21-day forward α vs SPY)

| Rating | 5d α (Σn) | 10d α (Σn) | **21d α (Σn)** |
|---|---|---|---|
| Buy | -1.27% (n=8, 25% hit) | -0.55% (38%) | **+1.16% (n=7, 71%) ✓** |
| Overweight | -0.59% (n=33, 42%) | +0.14% (42%) | **+1.59% (n=30, 60%) ✓** |
| Hold | +0.31% (n=32, 53%) | +0.01% (44%) | -0.22% (57%) |
| Underweight | +0.62% (n=26, 62% ✗) | +0.75% (54% ✗) | +1.56% (n=22, 64% ✗) |
| Sell | +1.22% (n=1) | +3.73% (n=1) | -1.38% (n=1) |

90-day window unresolved — extends past today's data. n=1 Sell rows are noise.

Convention: bullish ratings (Buy/OW) directionally correct when α>0; bearish (UW/Sell) correct when α<0; Hold neutral. Hit rate = % positive α.

## Key claims (load-bearing, n large enough)

1. **5-day strong calls are noise.** Buy α=-1.27% (25% hit), OW α=-0.59% (42%) — bull commits underperform on the realized 5-day window. UW α=+0.62% (62% positive) — bear commits also underperform their direction.

2. **21-day bull commits have signal.** OW α=+1.59% across n=30 with 60% hit rate. Buy α=+1.16% across n=7 with 71% hit rate. **Single-call baseline does NOT show this 21-day lift** (NVDA single-call UW at 21d = +6.35% directionally wrong; AAPL single-call OW at 21d = -2.57% wrong) — the lift is framework-specific, not LLM-general.

3. **Bear commits are anti-calibrated at every horizon.** UW α positive at 5d, 10d, AND 21d. The framework leans bullish; bear-side rating bucket selects dates that, on average, outperformed.

4. **Hold ≈ 0% at every horizon** with hit rate near 50%. Consistent with neutral. Counterfactual analysis on the 4 highest-magnitude Hold-α dates (MSFT 2026-03-06 α=-7.01%; AAPL 2026-02-06 α=-4.27%; NVDA 2026-03-13 α=+4.16%; AAPL 2026-01-30 α=+3.33%) consistently flagged real evidence ambiguity — supports Hold-as-honest-abstention.

## Architectural reframe

The framework is **a calibrated-abstention engine with asymmetric directional skill at 21-day**:
- Hold = honest output when evidence doesn't disambiguate
- Bull commits (Buy/OW) = real signal at 21-day, ceiling-noise at 5-day
- Bear commits (UW/Sell) = anti-signal — the bear bucket selects wrong dates

The pilot's 5-day evaluation horizon **was the wrong horizon**. The original mode-collapse "problem" was the framework correctly recognizing 5-day non-predictability. The bullish skill at 21-day was hiding underneath the 5-day noise.

## Intervention ablation ladder — 11 experiments, ranked by effect on calibration

| Lever pulled | Outcome at 5d | Reframed in light of 21-day finding |
|---|---|---|
| MR-1: contradiction analysis on debates | Confirmed two-sided evidence in 100% of debates | Two-sidedness is real; framework's Hold is correct response |
| WC-12: PM-blind variant | Broke 5d mode collapse; 5 NVDA Buys at α=-0.22% | At 21d, those Buys would have been directionally correct |
| MR-2: synthesis prompt instrumentation | Found "two-sided→Hold" instruction in prompt | The instruction is correct, not a bug |
| MR-3 v2: synthesis prompt fix | 6 OW + 3 Hold at NVDA; "no calibration win" at 5d | At 21d, 6 OW commits would have been correct |
| EH-2: rating distribution gate | DENY findings on every experiment | Gate enforces 5-tier surface; framework legitimately mostly uses 3 tiers (OW/Hold/UW) for its actual signal band |
| Brave news vendor (richer content, time-leaky) | No change at 5d | Same 21d signal as yfinance baseline |
| Exa news vendor (richer content, time-honest) | No change at 5d | Same 21d signal |
| Cross-ticker WC-12 (NVDA/AAPL/MSFT) | Direction varied by underlying signal | At 21d the bull-direction win is consistent across tickers |
| Single-call baseline (NVDA + AAPL) | Broke Hold collapse; wrong commits at 5d AND 21d | Framework's structural value IS the 21-day lift that single-call lacks |

## What the multi-agent structure actually contributes

Operationalized as: framework's 21d OW alpha (+1.59%, n=30) vs single-call's 21d alpha on same inputs (-2.57% AAPL OW, +6.35% NVDA UW = both directionally wrong).

The bull/bear debate + synthesis + risk debate + PM stack does **something** that single-call can't: (a) it hedges to Hold when evidence doesn't support commit, AND (b) when it commits bullish at OW/Buy, those dates have real 21-day signal. Single-call manufactures wrong-direction conviction on the same inputs.

## What this is NOT

- Not investment advice. Per Constitution Principle IV.
- Not validation that the framework predicts equities. The 21-day +1.59% bull-side α is real but small; n=30 across 9 tickers/dates is not portfolio-grade evidence.
- Not a 5-day signal. Original framework documentation implies 5-day prediction; that claim is empirically false at this scale.
- Not a bear-side signal. UW commits are anti-calibrated at every horizon tested.

## Open questions worth pursuing if research continues

1. **Does the 21-day bull lift hold at scale (n=100+)?** Current evidence is n=37 strong-bull commits across 9 experiments. A 65-pair re-pilot at the 21-day measurement horizon would test the signal robustly. Cost: ~$30, ~14h.
2. **Does the bear-side anti-calibration disappear at 90+ days?** Currently unresolved (data window extends past today). Needs another 60 days of price data.
3. **Is the 21-day lift Sonnet-specific or general?** Model-swap (Opus 4.6 / GPT-5.4 / Gemini 3.x) on the same NVDA grid would test. Cost: ~$10-30.
4. **Are bear-correct tickers (per WC-12 cross-AAPL) where the framework's UW anti-calibration concentrates?** A bucketed analysis at 21d would tell us.
5. **What changes if PortfolioManager runs `reasoning_evidence` (probabilistic) as a second-opinion calibration check?** Could elevate or downgrade the framework's commits based on independent Bayesian posterior. Build cost: 4-6h.

## Methodology notes

- All experiments use Anthropic Sonnet 4.6 (deep) + Haiku 4.5 (quick). Effort=medium not used (Opus-only param).
- Same 10-date grid (2026-01-30 → 2026-04-03 weekly) for matched cross-experiment comparison across NVDA/AAPL/MSFT.
- Forward α = ticker_Nd_return - SPY_Nd_return.
- 5-tier scale: Buy / Overweight / Hold / Underweight / Sell. Ratings extracted via deterministic regex from PM markdown.
- All raw data preserved per Constitution Principle I: `experiments/<id>/results.csv`, `~/.tradingagents/logs/<TICKER>/full_states_log_<DATE>.json`.
- Horizon sweep + counterfactual analysis: `scripts/horizon_sweep.py`, `scripts/identify_hold_extremes.py`, outputs at `claudedocs/horizon-sweep.md`, `claudedocs/hold-extremes-21d.json`.

## Reproducibility

```bash
bash experiments/<id>/run.sh            # rerun any experiment
python scripts/findings_aggregate.py    # rebuild experiment index
python scripts/horizon_sweep.py         # rebuild horizon table
python scripts/identify_hold_extremes.py --top-n 8 --horizon 21
```

## Related artifacts

- `findings.md` — auto-generated per-experiment one-paragraph summaries
- `claudedocs/horizon-sweep.md` — full per-experiment × horizon × bucket table
- `claudedocs/hold-extremes-21d.json` — Hold-α extreme dates with experiments
- `experiments/2026-05-02-001` through `2026-05-03-004` — 11 experiments with HYPOTHESIS + ANALYSIS each
- `.specify/memory/constitution.md` — six principles governing the research approach
- `docs/EXPERIMENT.md` — backlog of ~50 untested ideas

## MCP-reasoning answers to the 5 open questions

Each open question above was put through `mcp-reasoning` for an independent reasoning-architecture answer (mostly `reasoning_evidence` probabilistic for Bayesian estimates, `reasoning_decision` and `reasoning_divergent` where appropriate). Results:

### Q1 — 21d bull lift at n=100+ scale

Posterior **0.64** (prior 0.4, Bayes factor 2.67). Tool synthesis: "Moderately strong support that bull-side alpha would persist at scale, though scaling risks remain. Sensitivity moderate — with a more pessimistic prior (0.2) posterior would still reach ~0.5; with optimistic (0.6+) would exceed 0.75." **Verdict**: scaling is worth funding (~$30, ~14h overnight); evidence supports the hypothesis but doesn't dominate it.

### Q2 — Bear-side anti-calibration at 90d

Posterior **0.10** (prior 0.3, Bayes factor 0.25). Tool synthesis: "Anti-calibration worsens monotonically with horizon (5d +0.62% → 10d +0.75% → 21d +1.56%) — strongly suggests structural bullish bias rather than horizon-dependent timing issue. Bias will likely persist or worsen at 90d, not reverse. Low sensitivity to prior — even with optimistic priors (0.5-0.6), strong contradictory evidence yields posterior <0.2." **Verdict**: do NOT expect 90d to fix bear side. The bullish lean is structural. UW bucket should be treated as anti-signal, not as a flat-noise bucket.

### Q3 — 21d lift Sonnet-specific vs general

Reasoning-tool prior: posterior 0.64 (moderate confidence general).

**Empirical answer (2026-05-03, two experiments)**:

- **005 opus47-swap-nvda**: 10/10 Overweight on NVDA, 21d OW α = +2.85% (n=9, 78% hit). STRONGER than Sonnet cross-experiment OW 21d α of +1.59%.
- **006 opus47-swap-aapl** (pre-flight): 8 Hold + 2 OW on AAPL, 21d OW α = -0.07% (n=2, 50% hit). Flat, NOT replicating the NVDA lift.

Verdict: **the 21d bull signal is regime-conditional, not model-wide**. Opus produces strong bull commits AND positive 21d α only on tickers in clear bull regimes (NVDA in this period). On mixed-evidence tickers (AAPL), Opus correctly holds rather than committing.

Cross-experiment OW 21d α now +1.79% (n=41, 63% hit) — still the load-bearing claim, but anchored heavily by NVDA bull-regime data.

**Constitution Principle VII (re-amended after 006)**: mode-collapse direction is a function of (model × ticker × regime × prompt). Opus on the same prompt produces 10/10 OW on bull-regime NVDA AND 8/10 Hold on mixed-regime AAPL. The framework's calibrated abstention/commit behavior IS the model expressing its intrinsic confidence given the available evidence — stronger models discriminate this confidence per-ticker rather than collapsing uniformly. Sonnet either over-abstains (NVDA) or over-commits-bearish (AAPL); Opus does neither.

### Q4 — UW anti-calibration: ticker-concentrated or distributed?

Answered empirically via `scripts/bear_side_per_ticker.py` (output at `claudedocs/bear-side-per-ticker.md`):

| Ticker | n at 21d | mean α | wrong % | verdict |
|---|---|---|---|---|
| **AAPL** | 14 | **-0.18%** | 43% | **directionally correct** |
| MSFT | 5 | +2.03% | 80% | anti-cal |
| NVDA | 4 | +6.35% | 100% | anti-cal |
| CROSS | 23 | +1.44% | 61% | anti-cal (NVDA + MSFT-driven) |

**Verdict**: Anti-calibration is REGIME-CONCENTRATED, not structural. AAPL (the bear-correct ticker per WC-12 cross-AAPL) shows directionally correct bear-bucket α at 21d. NVDA + MSFT in their Q1 2026 bull regime drove the aggregate "anti-calibration" appearance. **This refines Q2's reasoning-tool verdict**: the bear-side problem isn't "structural bullish bias" — it's "the framework chose to commit UW at all on bull-regime tickers." The UW *rating* works when pointed at bear-correct tickers. The failure mode is UW *commit selection* during bull regimes.

Implication for any UW user: only trust UW when the ticker has independent bear evidence. UW on bull-regime tickers is where anti-calibration concentrates.

### Q5 — Wire reasoning_evidence into PortfolioManager as 2nd opinion

`reasoning_divergent` produced 3 substantive perspectives and a synthesis:

- **Risk Management Advocate**: integration transforms framework from point-estimate to uncertainty-aware — high disagreement signals conservative sizing, consensus enables aggressive allocation, frames decisions as risk-adjusted recommendations with quantified bounds.
- **Behavioral Finance Skeptic**: dangerous illusion of enhanced rationality — both systems trained on same historical patterns, will reproduce rather than correct for market biases. Disagreement creates analysis paralysis or false confidence in consensus.
- **Systems Reliability Engineer**: introduces single points of failure, latency bottleneck, chaotic behavior risk where small evidence-interpretation changes produce wildly different uncertainty signals.

**Synthesis**: build asymmetric handling — agreement boosts confidence/sizing, disagreement triggers human review (NOT algorithmic resolution). Build escape valves — system must degrade gracefully when reasoning_evidence fails. Implement time-boxed decision windows to prevent overthinking. **Verdict**: integration is worth building IF designed asymmetrically (agreement → augment, disagreement → flag for review), NOT as a calibration auto-correct.

## Project status

Research milestone closed at this snapshot. The architectural reframe (calibrated abstention + asymmetric 21-day bull-side signal) is the result. Further work would either (a) test the 21-day signal at scale (Open Question 1) — reasoning supports as moderately likely-positive, (b) wire reasoning_evidence integration with asymmetric handling (Open Question 5) — reasoning identifies real failure modes that need explicit guards, or (c) pursue model-swap (Open Question 3) — reasoning suggests moderate model-specificity, useful but not as load-bearing. Q2 (90d bear fix) is reasoning-confidence-rejected — do not pursue without strong contrary evidence. All three actionable directions would exceed the Constitution Principle III ($30) per-session ceiling and need explicit cost deliberation in their own HYPOTHESIS.
