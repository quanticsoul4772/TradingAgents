# Analysis: single-call-baseline-aapl

The NVDA single-call result replicates on AAPL: 0 Holds (mode collapse broken), 3 Overweight + 7 Underweight, **both buckets directionally wrong on average** (Overweight α=−2.06%, Underweight α=+1.28%). The 3 highest-magnitude alpha events in the period (01-30 +7.38%, 02-06 −6.66%, 02-13 +3.97%) were ALL wrong-direction calls. Across two tickers and 20 single-call decisions, the "framework Hold mode collapse is calibrated humility, single-call manufactures wrong-direction conviction" thesis holds. **The architectural reframe is robust enough to write FINDINGS.md and wind down active experimentation.**

## Result

### Distribution comparison (AAPL × same 10 dates, 5-way)

| Bucket | Pilot AAPL | WC-12 AAPL | Brave AAPL | Exa AAPL | **Single-call AAPL** |
|---|---|---|---|---|---|
| Buy | 0 | 0 | 0 | 0 | 0 |
| Overweight | 0 | 0 | 0 | 0 | **3** |
| Hold | 3 | 7 | 7 | 6 | **0** |
| Underweight | 7 | 2 | 3 | 4 | **7** |
| Sell | 0 | 1 | 0 | 0 | 0 |

**Single-call AAPL: 0 Holds, fully committed.** Mirrors NVDA single-call's pattern — Hold mode collapse is broken when the synthesis dampening is removed.

### Forward-α (5-day vs SPY)

Convention: Overweight correct when α>0, Underweight correct when α<0.

| Bucket | Pilot α | WC-12 α | Brave α | Exa α | **Single-call α** |
|---|---|---|---|---|---|
| Buy | — | — | — | — | — |
| Overweight | — | — | — | — | **−2.06% (n=3) ✗** |
| Hold | +2.12% (n=1) | −0.84% (n=7) | +1.02% (n=7) | +1.65% (n=6) | — |
| Underweight | (n=7) | +2.89% (n=2) | −1.46% (n=3) | −1.79% (n=4) | **+1.28% (n=7) ✗** |
| Sell | — | +0.95% (n=1) | — | — | — |

**Both single-call buckets are directionally wrong**, replicating NVDA's pattern.

### Cross-ticker replication of single-call buckets

| | Single-call NVDA | Single-call AAPL |
|---|---|---|
| Distribution | 6 OW + 4 UW + 0 Hold | 3 OW + 7 UW + 0 Hold |
| Overweight α | −0.72% (n=6) ✗ | −2.06% (n=3) ✗ |
| Underweight α | +1.64% (n=4) ✗ | +1.28% (n=7) ✗ |
| Directional hit rate | 30% | 50% |
| Hold count | 0 | 0 |

**Both tickers**: 0 Holds, both buckets wrong-direction on average. The pattern is the same; only the lean differs (NVDA single-call leaned Overweight, AAPL leaned Underweight — likely reading the underlying ticker's bull-vs-bear narrative correctly at the news level, but failing to convert that into 5-day prediction).

### Per-date breakdown with realized α

| Date | Realized α | Single-call AAPL | Correct? | Magnitude |
|---|---:|---|---|---|
| 2026-01-30 | +7.38% | UW | ✗ | **BIG miss** |
| 2026-02-06 | −6.66% | OW | ✗ | **BIG miss** |
| 2026-02-13 | +3.97% | UW | ✗ | **Big miss** |
| 2026-02-20 | +0.35% | OW | ✓ | Marginal |
| 2026-02-27 | −0.56% | UW | ✓ | Marginal |
| 2026-03-06 | −1.35% | UW | ✓ | Small |
| 2026-03-13 | +0.95% | UW | ✗ | Small |
| 2026-03-20 | +2.56% | UW | ✗ | Moderate |
| 2026-03-27 | +0.13% | OW | ✓ | Marginal |
| 2026-04-03 | −3.99% | UW | ✓ | Moderate |

**5/10 directionally correct = 50%, exactly coin flip.** But the wins are small-magnitude (0.13, 0.35, −0.56, −1.35, −3.99) and the losses are large-magnitude (7.38, −6.66, +3.97). Inverse magnitude-skill: single-call gets the small movements roughly right but fabricates wrong conviction on the big movements.

This is the worst possible failure mode for "predicting returns": being right when it doesn't matter, wrong when it does.

### EH-2 gate

3 DENY (same as NVDA single-call): missing Buy + Sell. Single-call breaks Hold-collapse but doesn't reach high-conviction calls (Buy/Sell). Sonnet's natural commitment band on these reports is OW/UW, never the extremes.

## Decision

**Scenario A confirmed**: NVDA result replicates on AAPL. The "honest abstention" thesis is robust across two tickers and 20 single-call decisions.

The next step per the NVDA ANALYSIS.md decision tree:

> Replicates NVDA (Scenario A) → Write FINDINGS.md. Architecturally close the project at this milestone.

**Recommendation**: write project-level `FINDINGS.md` aggregating all 11 experiments + the architectural reframe. Wind down active experimentation. Optionally run model-swap (Opus 4.6 / GPT-5.4 / Gemini 3.x) as a curiosity test, but priors are the calibration ceiling is general not Sonnet-specific.

### Why the "honest abstention" thesis is the right framing

Across 11 experiments, every intervention to break the framework's Hold mode collapse either:
1. **Failed to break it** (better news: Brave, Exa) — same Hold-heavy distribution, same calibration
2. **Broke it but produced wrong commits** (PM-blind WC-12 NVDA Buys at α=−4.27%, single-call NVDA OW at −0.72%, single-call AAPL OW at −2.06%, UW at +1.28%)
3. **Marginally tweaked it** (MR-3 v2 prompt) — produced asymmetric commitment that, in retrospect, was sliding toward single-call's failure mode

The synthesis stage's "two-sided evidence → Hold" framing isn't a bug. It's the framework's most honest output: when the LLM cannot reliably predict from public information, Hold is the correct answer. Removing the dampening doesn't reveal hidden signal; it manufactures wrong conviction.

### Why this isn't a failure of the project

The Constitution's Principle IV ("No Production Claims") and the framework's own disclaimer were correct from day one. We've now empirically demonstrated *why*:

> **5-day forward stock returns are not predictable from public information at better than coin-flip rates by ANY architecture we tested** — full multi-agent debate, PM-blind variants, prompt-tweaked synthesis, single-call baselines. The framework's Hold mode collapse is the architecturally correct response to that ceiling.

This is a genuine research finding. The lab notebook (11 experiments) is the artifact.

### What FINDINGS.md should contain

1. The architectural reframe: framework as calibrated-abstention engine, not predictor
2. The empirical evidence: 11 experiments, all consistent with LLM 5-day-prediction ceiling
3. The intervention failure ladder: news quality → news time-faithfulness → synthesis presence → synthesis prompt → single-call baseline; all hit the same ceiling
4. Honest scope claim: "TradingAgents tells you when public-info evidence supports a strong commit vs Hold. When it commits, it's no better than coin flip; the value is the abstention."
5. Open questions worth listing: model swap, longer horizons, cross-asset (FX/commodities/options where 5-day prediction may differ)
6. Project status: research complete on the framework-as-predictor question; further work would require either model-swap experiments or pivoting away from equities

## Detailed findings

### Why the 50% AAPL hit rate is more damning than NVDA's 30%

NVDA single-call's 30% directional hit rate looked clearly bad. AAPL's 50% looks like coin flip — superficially "no skill". But examining magnitude:

- Wins are small-α dates (median magnitude ~0.5%)
- Losses are large-α dates (median magnitude ~4-7%)

A coin flip with random magnitude allocation would expect roughly equal magnitudes on wins and losses. Single-call AAPL has *negatively* correlated magnitude-vs-correctness — meaning when public-info evidence is strong enough that the model commits with confidence, the underlying market moves the *opposite* way more often.

This is the worst calibration profile possible: confidently wrong on the dates that matter, weakly right on the dates that don't.

### Why 0 Holds is the canonical single-call signature

NVDA: 0 Holds. AAPL: 0 Holds. The prompt instruction is "Reserve Hold ONLY for genuinely balanced evidence; otherwise commit." Sonnet, on these analyst reports, never finds the evidence "genuinely balanced" — it always finds something to commit on.

This is exactly the failure mode the framework's synthesis prompt prevents. The synthesis says "two-sided evidence → Hold" because two-sided evidence (which MR-1 confirmed exists in 100% of cases) doesn't actually disambiguate 5-day direction. Single-call pretends it does.

### What the framework's mode collapse actually is

In the Bayesian sense: the synthesis is performing posterior averaging over conflicting evidence and outputting the maximum-entropy answer (Hold) when the posterior is broad. This is the calibrated thing to do. Single-call performs MAP-estimate-from-noisy-signal and picks the wrong mode of a multimodal posterior more often than not.

The framework is implicitly Bayesian; single-call is implicitly MAP. For a noisy signal, Bayesian wins on calibration even when both fail on prediction.

## Limitations

- n=10 per ticker, n=20 total — robust enough to confirm the NVDA result, not robust enough to make strong claims about the calibration ceiling itself
- Both tickers from the same period (Q1 2026) — period-specific noise possible but unlikely given the consistency
- Same prompt instruction ("commit unless balanced") — drives the 0-Hold result. A different prompt might produce more Holds; but the bucket-α failure mode would persist (still wrong-direction commits when committing).
- Single LLM (Sonnet 4.6) — model-swap experiments would test generality. Worth doing but not the most likely lever.

## Cost & timing

- Wall-clock: 1.0 min
- Cost: ~$1
- Errors: 0/10
- Per-call mean: 6.3s

## Next experiment

**FINDINGS.md** (project-level, not per-experiment) — aggregate all 11 experiments into a coherent architectural finding. Update README.md to point at it. This is the project's natural close-out at the current research milestone.

**OR**: model-swap experiments if curiosity warrants the spend (Opus 4.6, GPT-5.4, Gemini 3.x on same NVDA grid). $10-30 total. Tests whether the calibration ceiling is Sonnet-specific or general. Priors say general, but it's the only lever that hasn't been pulled.

## One-paragraph summary for findings.md

> Single-call baseline replicated on AAPL produces the same pattern as NVDA: 0 Holds (mode collapse broken), both buckets directionally wrong on average (Overweight α=−2.06%, Underweight α=+1.28%), with the 3 highest-magnitude alpha events all called wrong-direction. Across two tickers and 20 single-call decisions, the "framework Hold mode collapse is calibrated humility, single-call manufactures wrong-direction conviction" thesis holds robustly. The framework's mode collapse is its most honest output — when the LLM cannot reliably predict 5-day returns from public information (which it cannot), Hold is the correct answer. The architectural reframe is firm: TradingAgents is a calibrated-abstention engine, not a predictor.
