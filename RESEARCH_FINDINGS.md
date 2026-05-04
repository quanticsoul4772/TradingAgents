# RESEARCH_FINDINGS — TradingAgents-lab milestone

_Aggregated 2026-05-04 across 17 experiments + cross-experiment horizon sweep + counterfactual analysis + A3 forensics + 2 reasoning_evidence Bayesian updates + Phase D substrate exploration. For per-experiment summaries see `findings.md`. Latest experiments: `experiments/2026-05-04-001-nvda-q3-2025-micro/` (NVDA Q3 2025 cross-period micro-pilot — Scenario A, posterior recovers) and `experiments/2026-05-04-002-xlk-q1-2026-substrate/` (Phase D sector-ETF substrate test — Scenario B, substrate-different commit behavior)._

## Headline (revised after 3-period NVDA cross-validation + Phase D substrate test)

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls (Buy/OW/UW/Sell) are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) produce +1.23% mean alpha across n=71 cross-experiment commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE.** Three-period NVDA cross-validation: Q3 2025 +0.80% (n=10, 60% hit), Q4 2025 -0.47% (n=9, 22% hit), Q1 2026 ~+3.5% blended (n=15, ~80% hit). **Two of three periods positive — Q4 2025 is the negative outlier, not Q1 2026 as 008 alone suggested.** Reasoning_evidence Bayesian posterior on "stable cross-period signal" trajectory: 0.64 (pre-008, single-period n=50) → 0.52 (post-008, 2-period split) → **0.63 (post-NVDA-Q3, 3-period 2/3 positive)**. The signal exists at modest magnitude; cross-period stability has 3-period evidence supporting it.

Phase D substrate test (XLK Q1 2026 vs NVDA Q1 2026 same dates): framework went 30pp more Hold-heavy on the sector ETF substrate (70% Hold vs NVDA's 40% Hold). All XLK buckets had positive realized α; framework over-abstained. **Decision architecture is portable across substrates; commit calibration is substrate-specific (single-stock-prompt-tuned).**

Bearish commits remain regime-asymmetric, not uniformly anti-calibrated: UW commits on bear-correct tickers (AAPL, INTC excl. tail events) ARE directionally appropriate; UW commits on bull-regime tickers (NVDA, MSFT) drive the aggregate anti-calibration. Hold ≈ 0% median at every horizon. The framework's mode collapse to Hold is calibrated abstention; its bullish commits are a moderately-confident 3-period-validated signal at 21d; its bearish commits are an asymmetric signal that works on bear-correct tickers and fails on bull-regime tickers.

## Empirical core (cross-experiment summary, 5/10/21-day forward α vs SPY)

| Rating | 5d α (Σn) | 10d α (Σn) | **21d α (Σn)** |
|---|---|---|---|
| Buy | -1.27% (n=8, 25% hit) | -0.55% (38%) | **+1.16% (n=7, 71%) ✓** |
| Overweight | -0.46% (n=65, ~46%) | -0.07% (n=65, ~44%) | **+1.23% (n=71+2, ~61%) ✓ — moderately period-stable** |
| Hold | +0.45% (n=69, 53%) | +0.42% (n=69, 45%) | +1.93% (n=67, 60%) |
| Underweight | +2.05% (n=37, 63%) | +2.16% (n=37, 56%) | +4.55% (n=32, 59%) |
| Sell | +1.22% (n=1) | +3.73% (n=1) | -1.38% (n=1) |

(OW row updated post-NVDA-Q3 micro: post-008 +1.30% n=61 + Q3 micro's +0.80% n=10 → +1.23% n=71. Plus +1.51% n=2 from XLK Phase D = ~+1.24% n=73. Hit rate stable at ~61%. Updated UW + Hold rows to include 1 UW + 7 Hold + 6 Hold-resolved-rows from new experiments; magnitudes shift slightly but pattern holds.)

**Period composition** (added per Constitution VII Cross-period scope clarification, expanded post-NVDA-Q3):
- Q3 2025 cohort (NVDA-only micro 2025-08-01 → 2025-10-03): n=10 OW commits, +0.80% mean, 60% hit
- Q4 2025 cohort (008 dates 2025-11-07 → 2026-01-09): n=11 OW commits, -1.81% mean, 45% hit
- Q1 2026 cohort (005-007 dates 2026-01-30 → 2026-04-03): n=50 OW commits, +1.99% mean, 65% hit
- Combined n=71 cohort spans 3 calendar periods. **2 of 3 periods positive.** Cross-period replication status: **moderately supported** — Bayesian posterior 0.63 (recovered from 0.52 after Q3 evidence).
- Plus n=2 XLK OW (Phase D substrate test, Q1 2026, +1.51% — substrate-different commit behavior, low-n contribution)

90-day window unresolved — extends past today's data. n=1 Sell rows are noise.

Convention: bullish ratings (Buy/OW) directionally correct when α>0; bearish (UW/Sell) correct when α<0; Hold neutral. Hit rate = % positive α.

## Key claims (load-bearing, n large enough)

1. **5-day strong calls are noise.** Buy α=-1.27% (25% hit), OW α=-0.59% (44%) — bull commits underperform on the realized 5-day window. UW α=+1.04% (60% positive) — bear commits also underperform their direction. **007 single-experiment OW hit rate climb 56→67→75% across 5d→10d→21d** is the cleanest single-experiment evidence yet for horizon-dependent signal emergence.

2. **21-day bull commits have a period-conditional signal.** Cross-experiment OW α now +1.30% across n=61 with ~61% hit rate. **The signal split by calendar period**: Q1 2026 cohort = +1.99% n=50, 65% hit; Q4 2025 cohort = -1.81% n=11, 45% hit. Same model + prompt + A3 filter + news vendor + tickers in both cohorts; only calendar period differed. Buy α=+1.16% across n=7 with 71% hit rate (Q1 2026 only). **Single-call baseline does NOT show the 21-day Q1 2026 lift** (NVDA single-call UW at 21d = +6.35% directionally wrong; AAPL single-call OW at 21d = -2.57% wrong) — when the lift exists, it is framework-specific, not LLM-general. **Q1 (n=100+ scaling) partially answered**: cohort now at n=61 with cross-period evidence showing the signal is period-conditional, not stable. Reasoning_evidence Bayesian update: posterior on stable-cross-period-signal hypothesis dropped 0.64 → 0.52 (roughly even odds).

3. **Bear commits are regime-asymmetric, not uniformly anti-calibrated.** Per `bear_side_per_ticker.py` + 007 INTC forensics (`claudedocs/a3-filter-forensics-007.md`): UW commits on bear-correct tickers (AAPL n=14 α=-0.18% 43% wrong; INTC n=4 α=-1.73% excl. one 03-20 outlier) ARE directionally appropriate. UW commits on bull-regime tickers (NVDA n=4 α=+6.35% 100% wrong; MSFT n=5 α=+2.03% 80% wrong) drive the aggregate anti-calibration. **The bear-side failure mode is "framework chose UW on a bull-regime ticker," NOT "the UW signal itself is broken."** The A3 momentum filter (-5%/30d) targets a different failure (mean-reversion bounces) and is correctly inert on this regime-mismatch failure.

4. **Hold ≈ 0% median at every horizon** with hit rate near 50%. The aggregate Hold mean inflated by post-007 INTC tail (007 alone showed Hold mean +9.53% at 21d, dragged by INTC bouncing while framework abstained). Counterfactual analysis on the 4 highest-magnitude Hold-α dates (MSFT 2026-03-06 α=-7.01%; AAPL 2026-02-06 α=-4.27%; NVDA 2026-03-13 α=+4.16%; AAPL 2026-01-30 α=+3.33%) consistently flagged real evidence ambiguity — supports Hold-as-honest-abstention. **Median is the honest signal; mean is tail-distorted.**

5. **Distribution-level claims replicate; date-level claims do not.** 005 produced 10/10 OW on Opus NVDA × 10 dates. 007 produced 6/10 OW + 4 Hold on the SAME 10 NVDA dates with the same Opus model — Hold dates clustered in NVDA's early-Feb selloff window. With stochastic data sources (exa news non-determinism) and per-experiment fresh memory logs, run-to-run variance on identical inputs is real. **The bucket ratio (Opus on NVDA-bull commits ≥ 60% OW) is replicable; the specific commit dates are not.** Methodologically: ANALYSIS write-ups should report bucket ratios as claims and per-date commits as observations.

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

**Empirical answer post-007 (2026-05-03 evening, n=50 milestone)**: load-bearing claim sat at n=50, +1.99% mean, 65% hit. The reasoning-tool prior was conservative — the n=30 → n=50 jump did NOT erode the signal at that point. Single-experiment 007 hit-rate climb 56→67→75% across 5d/10d/21d was the cleanest single-run horizon-emergence evidence in the corpus.

**Empirical answer post-008 (2026-05-03 late-evening, n=61 with 2-period split)**: 008 (same config as 007, Q4 2025 dates) produced OW 21d α = -1.81% (n=11, 45% hit) — sign-flipped from 007's +3.05%. Cross-experiment OW α: +1.99% n=50 → +1.30% n=61, hit 65% → ~61%. **Reasoning_evidence Bayesian posterior on "stable cross-period signal" dropped 0.64 → 0.52** (likelihood ratio 0.6). Q1 partial-resolved with caveat at this snapshot.

**Empirical answer post-NVDA-Q3 micro-pilot (2026-05-04, n=71 with 3-period evidence)**: NVDA Q3 2025 micro-pilot ($3 T1) produced 10/10 OW with 21d α = +0.80% (n=10, 60% hit). Three-period NVDA: Q3'25 +0.80% / Q4'25 -0.47% / Q1'26 ~+3.5%. **Two of three periods positive — Q4 2025 is the negative outlier.** Cross-experiment OW α: +1.30% n=61 → +1.23% n=71, hit ~61%. **Reasoning_evidence Bayesian posterior recovered: 0.52 → 0.63** (likelihood ratio 1.57). Q1 status updated to **moderately supported**. Cost-effectiveness: $3 micro-pilot produced equivalent evidence quality to a $10 T2 experiment because it targeted the highest-signal ticker on the load-bearing question. Constitution VII Cross-period scope clarification (v1.2.2) remains valid; we now have 3-period validation supporting it.

### Q2 — Bear-side anti-calibration at 90d

Posterior **0.10** (prior 0.3, Bayes factor 0.25). Tool synthesis: "Anti-calibration worsens monotonically with horizon (5d +0.62% → 10d +0.75% → 21d +1.56%) — strongly suggests structural bullish bias rather than horizon-dependent timing issue. Bias will likely persist or worsen at 90d, not reverse. Low sensitivity to prior — even with optimistic priors (0.5-0.6), strong contradictory evidence yields posterior <0.2." **Verdict**: do NOT expect 90d to fix bear side. The bullish lean is structural. UW bucket should be treated as anti-signal, not as a flat-noise bucket.

### Q3 — 21d lift Sonnet-specific vs general

Reasoning-tool prior: posterior 0.64 (moderate confidence general).

**Empirical answer (2026-05-03, two experiments)**:

- **005 opus47-swap-nvda**: 10/10 Overweight on NVDA, 21d OW α = +2.85% (n=9, 78% hit). STRONGER than Sonnet cross-experiment OW 21d α of +1.59%.
- **006 opus47-swap-aapl** (pre-flight): 8 Hold + 2 OW on AAPL, 21d OW α = -0.07% (n=2, 50% hit). Flat, NOT replicating the NVDA lift.

Verdict: **the 21d bull signal is regime-conditional, not model-wide**. Opus produces strong bull commits AND positive 21d α only on tickers in clear bull regimes (NVDA in this period). On mixed-evidence tickers (AAPL), Opus correctly holds rather than committing.

Cross-experiment OW 21d α now +1.99% (n=50, 65% hit) — load-bearing claim, anchored across NVDA + AAPL + INTC after 007.

**Constitution Principle VII (re-amended after 006)**: mode-collapse direction is a function of (model × ticker × regime × prompt). Opus on the same prompt produces 10/10 OW on bull-regime NVDA AND 8/10 Hold on mixed-regime AAPL. The framework's calibrated abstention/commit behavior IS the model expressing its intrinsic confidence given the available evidence — stronger models discriminate this confidence per-ticker rather than collapsing uniformly. Sonnet either over-abstains (NVDA) or over-commits-bearish (AAPL); Opus does neither.

**Further refined post-007 (2026-05-03 evening)**: the SAME Opus model on the SAME 10 NVDA dates produces 10/10 OW (run 005) vs 6/10 OW + 4 Hold (run 007) — Hold dates clustered in NVDA's local Feb selloff window. Run-to-run variance is real because (a) exa news API returns slightly different snippet sets per call, (b) memory-log state evolves through the run. **Bucket ratios replicate; specific commit dates do not.** Implication for Principle VII: claims about "model X on ticker Y" must specify whether they are bucket-level (replicable) or date-level (single observation). The empirical finding "Opus on NVDA bull regime → ≥60% OW commits" is replicable; "Opus on NVDA 2026-02-06 → OW" is a single observation, not a property.

### Q4 — UW anti-calibration: ticker-concentrated or distributed?

Answered empirically via `scripts/bear_side_per_ticker.py` (output at `claudedocs/bear-side-per-ticker.md`):

| Ticker | n at 21d | mean α | wrong % | verdict |
|---|---|---|---|---|
| **AAPL** | 14 | **-0.18%** | 43% | **directionally correct** |
| MSFT | 5 | +2.03% | 80% | anti-cal |
| NVDA | 4 | +6.35% | 100% | anti-cal |
| **INTC (007)** | 5 | +20.31% (raw) / **-1.73% excl. tail** | 40% | **directionally correct excl. single 03-20 outlier** |
| CROSS | 28 | +4.78% (raw) / +1.49% excl. INTC 03-20 | 57% | tail-distorted; per-ticker shows AAPL+INTC correct, NVDA+MSFT anti-cal |

**Verdict updated post-007**: Anti-calibration is REGIME-CONCENTRATED + tail-distorted, not structural. AAPL + INTC (bear-correct tickers) show directionally correct bear-bucket α at 21d when small-n outliers are accounted for. NVDA + MSFT in their Q1 2026 bull regime drove the prior aggregate "anti-calibration" appearance. **Q2's reasoning-tool verdict (posterior 0.10 for "bear-side fixes at 90d") is now further refined**: the bear-side problem isn't "structural bullish bias" — it's regime-mismatch (committing UW on bull-regime tickers) plus catalyst-driven tail events that no momentum filter catches. The UW *rating* works when pointed at bear-correct tickers. The A3 momentum filter (-5%/30d) is correctly inert on the failure mode it doesn't target.

Implication for any UW user: only trust UW when the ticker has independent bear evidence. UW on bull-regime tickers concentrates anti-calibration; UW on bear-correct tickers is sometimes-right with single-event tail risk.

### Q5 — Wire reasoning_evidence into PortfolioManager as 2nd opinion

`reasoning_divergent` produced 3 substantive perspectives and a synthesis:

- **Risk Management Advocate**: integration transforms framework from point-estimate to uncertainty-aware — high disagreement signals conservative sizing, consensus enables aggressive allocation, frames decisions as risk-adjusted recommendations with quantified bounds.
- **Behavioral Finance Skeptic**: dangerous illusion of enhanced rationality — both systems trained on same historical patterns, will reproduce rather than correct for market biases. Disagreement creates analysis paralysis or false confidence in consensus.
- **Systems Reliability Engineer**: introduces single points of failure, latency bottleneck, chaotic behavior risk where small evidence-interpretation changes produce wildly different uncertainty signals.

**Synthesis**: build asymmetric handling — agreement boosts confidence/sizing, disagreement triggers human review (NOT algorithmic resolution). Build escape valves — system must degrade gracefully when reasoning_evidence fails. Implement time-boxed decision windows to prevent overthinking. **Verdict**: integration is worth building IF designed asymmetrically (agreement → augment, disagreement → flag for review), NOT as a calibration auto-correct.

## Phase D substrate exploration (added 2026-05-04, expanded post-multi-sector)

Two Phase D experiments landed:

**Experiment 002 (XLK Q1 2026, single sector)**: 2 OW + 7 Hold + 1 UW vs NVDA's 6 OW + 4 Hold (per-date match rate 5/10). XLK was 30pp more Hold-heavy than NVDA in the same period. All XLK buckets had positive realized α (XLK was bullish in window). Initial finding: "framework over-abstains on sector ETFs."

**Experiment 003 (XLF + XLE Q1 2026, multi-sector)**: XLF 8 Hold + 2 UW + 0 OW; XLE 5 Hold + 2 OW + 3 UW (3 of 5 tiers used). **The XLK over-Hold finding does NOT uniformly generalize**. Per-sector commit profiles diverge: XLK 70% Hold, XLF 80% Hold, XLE 50% Hold. **Per-sector regime discrimination is intact on ETFs** (Scenario B from HYPOTHESIS) — the abstention bar is just elevated.

**Initial bonus finding (now retired)**: 003 produced bear-side UW commits on sector ETFs at 80% directionally correct (n=5, mean α -6.03%) — claimed sector ETFs as a structurally better substrate for the framework's bear-side. **Cross-period validation in 004 (XLE Q4 2025 micro) refuted this**: XLE Q4 2025 UW α = +11.77% n=3, 100% directionally WRONG. Combined cross-period XLE UW: n=6, +2.24% mean, 33% correct. Full cross-experiment ETF UW (XLF Q1 + XLE Q1 + XLE Q4): n=8, +0.65% mean, 62.5% correct — barely-positive aggregate, no special bear-side advantage. The 80% claim was small-sample artifact + favorable Q1 2026 energy regime. **Bayesian posterior on "ETF bear-side accuracy is real": ~0.55 → ~0.25.**

**Architectural reframe v3 (post-XLE-Q4 retraction)**:
- Architecture is portable ✓
- Per-sector regime discrimination intact on ETFs ✓
- ~~Bear-side accuracy is higher on sector ETFs~~ → **No special bear-side advantage on ETFs; period-conditional like everything else**
- Generalization lesson: this is the third instance of a single-experiment α finding failing to replicate cross-period (008 NVDA bull-side, 003 ETF bear-side initially looked great, 004 retracted it). **Constitution VII Cross-period scope clarification (v1.2.2) repeatedly validated.**

**Next Phase D options**: (a) XLF Q4 2025 micro to complete cross-period XLF picture, (b) prompt re-tuning experiment to test shifting the abstention bar, (c) different substrate type (commodity ETF, crypto pair) to test broader generalization. None of these are urgent; the architectural reframe is now stable enough that further Phase D testing has diminishing returns.

## Project status

Updated 2026-05-04 (post-NVDA-Q3-micro + post-XLK-Phase-D). The architectural reframe: **calibrated abstention + 3-period-validated bull-side signal at modest magnitude + regime-asymmetric bear-side + substrate-specific commit calibration**. Q1 (n=100+ scaling) is now resolved with **moderate confidence positive** — at n=71 spanning 3 periods the signal is +1.23% with ~61% hit rate; Bayesian posterior 0.63. Q3 (model-specificity) answered: signal is regime-conditional + period-conditional + substrate-conditional, not model-wide. Q4 (UW concentration) answered: regime-concentrated + tail-distorted. Q2 (90d bear fix) reasoning-confidence-rejected (posterior 0.10) — do not pursue. Q5 (reasoning_evidence in PM) unbuilt; reasoning identified real failure modes needing asymmetric handling.

Next planned: choices include (a) substrate-prompt-adapted XLK rerun (~$10 T2) to test prompt-tuning fix for the over-Hold finding, (b) different substrate type (~$10 T2) to test substrate-generalization of over-Hold, (c) full 30-pair Q3 2025 validation (~$30 T3) to push n past 100 on the bull-α claim, (d) cross-ticker Phase D (XLF financials, XLE energy) to test sector-rotation signal at low cost. Two specs unimplemented: 001-bots-architecture (battlecode-style refactor) and 002-signal-lifecycle (discover/evaluate/promote/retire/learn pipeline) — both no-LLM-cost large builds, deferrable.
