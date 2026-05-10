# RESEARCH_FINDINGS — TradingAgents-lab milestone

_Aggregated 2026-05-04 across 22 experiments + cross-experiment horizon sweep + counterfactual analysis + A3 forensics + 3 reasoning_evidence Bayesian updates + Phase D substrate exploration + Spec 002 signal-lifecycle Phases 0-2.5 + Spec 001 bots-architecture Phases 1-5 (including Phase 4 live-validated). For per-experiment summaries see `findings.md`. Latest experiments: `experiments/2026-05-04-001-nvda-q3-2025-micro/` (NVDA Q3 2025 cross-period micro-pilot — Scenario A, posterior recovers), `experiments/2026-05-04-002-xlk-q1-2026-substrate/` (Phase D sector-ETF substrate test — Scenario B), and `experiments/2026-05-04-007-phase4-bot-models-smoke/` (Spec 001 Phase 4 live propagate validation — Scenario A)._

_**Updated 2026-05-06 with 11-work-unit research-burst summary**: Spec 003 default-on flip @80% threshold (validated by `claudedocs/contrarian-gate-threshold-sweep-2026-05-06.md`); Spec 003.5 sector-baseline fallback (`specs/003-sector-baseline-gate/`); Spec 004 sector-momentum filter (`specs/004-sector-momentum-filter/`, default-off after retrospective showed -0.45pp); Spec 006 bear-sector-symmetry filter (`specs/005-bear-sector-symmetry/`, default-off after SC-008 FAILED at +5%); Spec 005 candidate retrospective-then-SKIPPED (`claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`); Sector-α attribution analyzer (`claudedocs/sector-alpha-attribution-2026-05-06.md`) surfaced **5th failure mode** + **bearish anti-calibration shock** (+28.02% mean α-vs-SPY on n=18 ticker_strong-bearish cohort); INTC +103%-on-Hold investigation closed SC-003 follow-up arc as calibrated abstention. **Constitution v1.3.0 with new Principle VIII** (Retrospective Before Spec for Backward-Looking Price Filters) codifies the day's load-bearing methodology lesson. Test count 984 (was 825). Filter portfolio expanded from 1 to 5; see new "Filter portfolio status" section below._

_**Updated 2026-05-07 (94+ PR day; bear-side survey CONCLUDES + Spec X-1 DEPLOYED + 2 constitution amendments RATIFIED)**: Spec 007 forward-catalyst gate (bull-active, bear-shadow) + Spec 008 Hybrid C calendar boost shipped 2026-05-06; **SC-009 live A/B ablation 2026-05-07: 36/36 rows COMPLETE; PRELIMINARY PASS-by-non-counterexample** — 0 decisions changed by boost across full sample; recommend SHADOW-MODE-FIRST for v2 default-on flip, NOT direct flip (PRs #57, #58, #61). Final canonical 21d-window verdict pending ~2026-05-22+. **Bear-side mechanism class survey from PR #22 CONCLUDES (6/6 evaluated)**: only **C-4 (institutional ownership delta)** cleared both Constitution VIII v1.4.0 standalone gate (n=12, mean α +5.41%, hit 75%, discrim +10.29pp; PR #75) AND v1.4.3 additive overlap vs Spec 007 (+8.06pp Δα improvement / +69pp hit improvement; C-4 catches 11 bearish commits Spec 007 entirely misses; PR #77). **Spec X-1 (C-4 institutional rotation filter) DEPLOYED end-to-end via 6-PR bundle (#88 spec → #89 plan → #90 tasks → #91 MVP → #92 tests → #93 polish)** at default-shadow bear-side / default-off bull-side; 18 tests + 4 config keys + ~190 LOC helper module. **Spec 010 (Hybrid D bear-side calendar-boosted) closed via PR #86 SKIP retrospective** on structural-incompatibility argument (3-converging-retrospective methodological closure of bear-side calendar-boost mechanism class). Two C-classes show INVERTED bear-side mechanism (C-2 short-covering + C-5 price-reaction): both originally hypothesized as mean-reversion; bear cohort empirically continuation. Three SKIP-types codified (empirical / data-availability / structural). **Constitution v1.4.3 → v1.4.5 → v1.4.6** — Quality Gate #6 (Memory-log data-vs-prose discipline; PR #83) + Behavioral-additive 4th interpretation (PR #84) both ratified; v1.4.4 draft content was ratified as v1.4.6 to preserve monotone numbering after v1.4.5 was ratified first per reasoning_decision rank ordering. Path C analyst PT snapshot wiring (`tradingagents/agents/utils/analyst_pt_snapshot.py`) shipped default-OFF unlocking future C-3-class retrospectives. Spec 003 historical-recompute backfilled 254 cache rows; 9 tickers now clear FR-004 N≥20 floor (NVDA / AAPL / INTC / XLE / MSFT / GOOGL / JPM / XLF / XLK). Test count: **1134 unit + 2 integration** post-Spec X-1 deployment. Cross-session memories 14 → **23**. Filter portfolio: **9 production filters** (Spec X-1 promoted from candidate to deployed)._

## Headline (revised after 3-period NVDA cross-validation + Phase D substrate test + WC-10 schema-bottleneck pilot)

**At 5-day windows the framework is at the LLM single-call calibration ceiling — strong calls (Buy/OW/UW/Sell) are no better than coin flip. At 21-day windows, the framework's bullish commits (Buy + Overweight) produce +1.23% mean alpha across n=71 cross-experiment commits (~61% hit rate) — POSITIVE AT MODERATE CONFIDENCE.** Three-period NVDA cross-validation: Q3 2025 +0.80% (n=10, 60% hit), Q4 2025 -0.47% (n=9, 22% hit), Q1 2026 ~+3.5% blended (n=15, ~80% hit). **Two of three periods positive — Q4 2025 is the negative outlier, not Q1 2026 as 008 alone suggested.** Reasoning_evidence Bayesian posterior on "stable cross-period signal" trajectory: 0.64 (pre-008, single-period n=50) → 0.52 (post-008, 2-period split) → **0.63 (post-NVDA-Q3, 3-period 2/3 positive)**. The signal exists at modest magnitude; cross-period stability has 3-period evidence supporting it.

**Architectural addition (2026-05-08, WC-10 pilot)**: the framework's mode collapse to Hold is a TWO-MECHANISM phenomenon, not a unitary "calibrated abstention." Mechanism A (genuine ambiguity → Hold, per original Constitution VII) coexists with Mechanism B (one-directional moderate-magnitude evidence collapses to Hold because the 5-tier categorical schema lacks a partial-confidence tier). WC-10 pilot (n=20 paired): continuous-scalar mode emitted `|rating|>0.2` on 18/20 (90%) vs 5-tier mode's 5/20 (25%) non-Hold rate — 3.6× ratio, falsification verdict ALT-A confirmed. Constitution VII amended v1.4.3 → **v1.5.0** to carve out the schema-artifact case. The schema fix is bullish-side-validated (NVDA Buy n=6 mean +4.67% α 21d) but bear-side-anti-calibrated on this cohort (AAPL UW n=6 mean +3.56% α — UW called bearish but ticker rose).

**WC-10 v3 bear-regime validation (2026-05-08 evening)**: WC-10 v3 (Q4 2025 NVDA, n=8 paired) produced **PARTIAL ALT-A** — direction matches ALT-A (WC-10 emitted 8/8 dates as Buy/OW vs 5-tier's 0 OW + 1 UW + 7 Hold) but magnitude < 1.0pp (α delta -0.22pp). Constitution VII v1.5.0 → **v1.5.1** (Patch D applied per PR #154) — caveat language preserved at v1.5.0 scope; empirical magnitude bound documented. **Spec 009 Branch A activation does NOT require regime-aware gating as a hard requirement**; runtime monitoring via `scripts/wc_10_underperformance_monitor.py` (PR #146) provides operational enforcement of the v1.5.0 caveat. v2 (n=100 ticker expansion) still in flight to resolve generalization across 8 tickers.

Phase D substrate test (XLK Q1 2026 vs NVDA Q1 2026 same dates): framework went 30pp more Hold-heavy on the sector ETF substrate (70% Hold vs NVDA's 40% Hold). All XLK buckets had positive realized α; framework over-abstained. **Decision architecture is portable across substrates; commit calibration is substrate-specific (single-stock-prompt-tuned).**

Bearish commits remain regime-asymmetric, not uniformly anti-calibrated: UW commits on bear-correct tickers (AAPL, INTC excl. tail events) ARE directionally appropriate; UW commits on bull-regime tickers (NVDA, MSFT) drive the aggregate anti-calibration. Hold ≈ 0% median at every horizon. The framework's mode collapse to Hold is calibrated abstention; its bullish commits are a moderately-confident 3-period-validated signal at 21d; its bearish commits are an asymmetric signal that works on bear-correct tickers and fails on bull-regime tickers.

## Portfolio synthesis — where the project stands at 22 experiments + 2 specs (added 2026-05-04 late-evening)

**Verdict: useful research yield achieved. The corpus answers the primary question at moderate confidence and documents four publishable secondary findings (one added 2026-05-05 after the within-ticker IC methodology fix surfaced a validated within-ticker predictor). Continued spend should be justified against specific open questions, not exploratory drift.**

### What got built

- **22 experiments** (`experiments/2026-05-02-001-*` through `experiments/2026-05-04-007-*`) covering: 8 prompt/structure interventions (MR-1 through WC-12 variants, EH-2, brave/exa news), 4 single-call architectural baselines, 4 Opus-vs-Sonnet model swaps, 3 cross-period validations (Q1 2026 / Q4 2025 / Q3 2025), 3 Phase D substrate tests (XLK / multi-sector / XLE), 1 Phase C reasoning_evidence smoke, 1 Spec 002 cache smoke, 1 Spec 001 Phase 4 live-validation. Total LLM spend across the corpus ≈ $250-300.
- **Two complete specs implemented**: Spec 002 signal-lifecycle (Phases 0-2.5: registry + cache + 14 featurizers + drift + counterfactual + multi-horizon eval) and Spec 001 bots-architecture (Phases 1-5: Signal schema + deterministic aggregator + shadow mode + bots-mode + convergence shortcut + bot budgets + weight tuning + per-bot LLM routing live-validated).
- **One opt-in production augmentation**: A3 mean-reversion suppression filter (`tradingagents/agents/utils/momentum_filter.py`), validated as correctly inert on regime-mismatch failures.
- **One advisory hook**: Phase C reasoning_evidence second-opinion (`tradingagents/agents/utils/second_opinion.py`), default disabled, asymmetric design per Q5.
- **785 unit + integration tests** (was 501 at scaffolding install), 81%+ coverage, pre-commit gates passing.
- **Constitution v1.2.2** with seven principles including the load-bearing **Principle VII (Calibrated Abstention)** added 2026-05-03 and re-amended after experiment 006 + cross-period clarification.

### What the corpus actually shows (primary research question)

The primary question was: *what structural conditions cause role-based multi-agent LLM debate to collapse to moderate ratings, and what enforcement mechanisms (or alternative architectures) would prevent that collapse?*

**Answer (moderate confidence)**: mode-collapse direction is a function of **(model × ticker × regime × prompt)**, not a uniform property of multi-agent debate. Sonnet over-abstains on bull tickers AND over-commits-bearish on bear tickers. Opus discriminates per-ticker. The same architecture on the same prompt produces different commit distributions across calendar periods (Q4 2025 outlier vs Q1 2026 + Q3 2025 stable) and across substrates (single stocks vs sector ETFs — XLK 70% Hold vs NVDA 40% Hold same dates).

**The "collapse" framing was wrong**. Hold ≈ 0% median forward α at every horizon — Hold isn't a mode-collapse failure; it's calibrated abstention. The framework correctly does nothing when evidence is weak. The interesting question shifted from "why does it collapse to Hold?" to "when it does commit, what's the realized α?" — and the answer there is: **+1.23% at 21d for bullish commits (n=71, 61% hit rate, 2 of 3 periods positive, Bayesian posterior 0.63 on stable cross-period signal)**.

**Enforcement mechanisms tested**:
- **Replace LLM PM with deterministic aggregator over featurized prose signals (Spec 001 Phases 1+5)**: FAILS. Shadow aggregator 42.3% direction match (vs 80% target). Weight tuning overfits (train +0.079 → test -0.062). The featurized-prose Signals don't carry sufficient signal to support a deterministic replacement.
- **Convergence shortcut to skip debate when analysts agree (Spec 001 Phase 3)**: 0% fires at spec defaults on the historical corpus. Featurization-derived magnitudes top out around 0.5; the >0.7 threshold is unreachable from prose alone. Would require LLM-emitted Signals to fire.
- **A3 mean-reversion suppression filter for UW commits**: works as designed but inert on the failure mode that actually matters (regime-mismatch UW commits don't enter the suppression zone). Per-row forensics in `claudedocs/a3-filter-forensics-007.md`.
- **Phase C reasoning_evidence second-opinion**: wired with asymmetric handling per Q5 reasoning_divergent analysis. Default disabled. Empirical effect on rating distribution untested at n>1.

### Four publishable secondary findings

1. **Calibrated abstention as the load-bearing skill, not commits**. Five-tier rating frameworks evaluated naively look like mode-collapse failures (because Hold ≈ 50-70% of decisions). Evaluated against forward returns, Hold is the *calibrated* output — the framework is correctly abstaining. The interesting evaluation metric is conditional-on-commit α, not commit rate. This reframe is encoded in Constitution Principle VII and was the trigger for the 2026-05-03 cross-period reframe.

2. **Replicability scope: bucket-level claims replicate, date-level and realized-α claims do not**. Same Opus model on the same 10 NVDA dates produces 10/10 OW one run and 6/10 OW + 4 Hold the next; per-ticker bucket *ratios* hold (NVDA 90% vs 60% OW, both >50%) but specific commit dates and realized α do not. This means evaluation methodology matters: aggregate hit-rate / mean-α claims are valid; individual-decision causal attributions ("the framework correctly called X on date Y") are noise.

3. **Decision architecture portable, commit calibration substrate-specific**. Phase D XLK Q1 2026 same-date test: framework went 30pp more Hold-heavy on the sector ETF than on the constituent NVDA. All XLK buckets had positive realized α; framework over-abstained on the substrate. Implies the framework's prompt is single-stock-tuned; portability of the *architecture* (analysts → debate → PM) is separate from portability of the *calibration*.

4. **Market analyst bull-keyword density anti-predicts within-ticker α at 90d** (added 2026-05-05; **mechanism established 2026-05-05 evening**). `market_report bull_keyword_count` shows aggregate IC near zero (-0.011) but within-ticker median IC = -0.489 with **9 of 9 tickers negative** — the only feature in the corpus where every ticker shows direction agreement. Within-ticker permutation test: p<2e-4 (passes Bonferroni for 280 tests); unanimous-direction permutation: p=0.0058. Period-stable across Q4 2025 + Q1 2026 (4/4 and 9/9 negative). Per-ticker bootstrap CIs exclude zero for 6 of 9 tickers individually. **First validated within-ticker predictor in the corpus.** **Mechanism (claudedocs/finding4-mechanism-2026-05-05.md): recency + mean-reversion combined.** `bull_keyword_count` correlates strongly POSITIVE with prior 30d/60d/90d α (aggregate +0.47/+0.46/+0.35; within-ticker median +0.31/+0.26/+0.29; 8 of 9 tickers positive at 30d). The market analyst's bullish prose tracks recent strength; recent strength mean-reverts. Same direction of association in the data, both ends. 7 of 9 tickers show the recency-then-reversion pattern clearly; XLF is the one ticker where finding #4's anti-signal does NOT operate through recency. **XLF investigated separately (`claudedocs/xlf-mechanism-2026-05-05.md`)**: not a different mechanism but a sample-window degeneracy — all 10 XLF cached dates have negative-or-zero prior 30d α (XLF underperformed SPY across the entire backtest window), bull_keyword_count is uniformly high (30-76), and future_90d data is mostly truncated for these recent dates. Within-ticker correlation is mathematically near-degenerate when prior α has tiny variance. Implication for spec 003: bump FR-004 percentile-baseline N floor from 5 to 20, exclude XLF from validation grid until prior-α range spans both positive and negative observations.

**Degenerate-window sanity check across all 9 tickers** (`claudedocs/degenerate-window-check-2026-05-05.md`): XLK is ALSO in a degenerate window (prior 30d α range 9.6pp, just under the 10pp threshold; n=10 cached rows). The original "9/9 unanimous negative direction" headline was numerically valid but mechanically over-counted: XLF + XLK were both in degenerate prior-α windows where the within-ticker correlation is uninterpretable. **Restated headline: 8/8 non-degenerate tickers (AAPL, GOOGL, INTC, JPM, MSFT, NVDA, XLE — single stocks plus the one surviving sector ETF) show within-ticker IC negative on bull_keyword_count vs future 90d α.** The empirical signal is unchanged in strength — the 8 tickers carrying the discriminating evidence still produce the headline anti-prediction pattern. XLE is the one sector ETF that survives (range 27pp, 17+/3-) — sector-ETF-ness isn't causal for degeneracy, low-n + low-prior-α-variance is. The framework's market analyst is most bullish at locally-bullish moments that mean-revert over 90d. Full validation in `claudedocs/within-ticker-artifact-check-2026-05-05.md`; mechanism in `claudedocs/finding4-mechanism-2026-05-05.md`. This finding was invisible before the within-ticker IC methodology fix (commit 3c2d0c2) — the column surfaced it; the artifact check confirmed it; the mechanism investigation explained it. **Important caveat (added 2026-05-05 night, `claudedocs/contrarian-gate-retrospective-2026-05-05.md`)**: an offline retrospective of 156 historical propagates simulating the spec 003 gate at strict-prior N≥5 history shows the gate would have HURT cumulative α (-28.69% at 21d across 15 fires), contradicting finding #4's mechanism prediction. The N≥20 production-floor retrospective is consistent with the prediction but only 2 commits qualified (n anecdotal). Three explanations were initially under consideration: (1) low-N percentile is too noisy to identify high-density moments; (2) early-history fires happen on tickers/regimes where the recency mechanism is weaker; (3) finding #4's corpus-aggregate IC has look-ahead bias and overstates actionable predictive power.

**Look-ahead bias RULED OUT (2026-05-05 night, `claudedocs/finding4-strict-prior-ic-2026-05-05.md`)**: re-computed within-ticker IC using strict-prior percentile (vs prior dates of same ticker only, no look-ahead) on the same row subsets. Result: median IC is essentially identical to the original at both floors — N≥5: -0.4534 (original) vs -0.4441 (strict-prior), Δ +0.0093; N≥20 (NVDA only): -0.7473 vs -0.7428, Δ +0.0045. Finding #4's headline statistic is robust, NOT a look-ahead artifact. **Explanation #3 rejected.**

**Within-bullish-subset transfer CONFIRMED (2026-05-05 night, `claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md`)**: re-computed within-ticker IC restricted to ONLY Buy/Overweight commits per ticker (the gate's actual scope). Result: median IC across tickers is -0.4199, essentially equivalent to the all-dates IC of -0.3909. 3 of 4 tickers with sufficient bullish n are negative (GOOGL -0.45, MSFT -0.72, NVDA -0.39); only AAPL is +0.10 with n=5. NVDA at n=27 bullish commits (the gate's actual production-floor target ticker) reproduces finding #4's mechanism cleanly. **Explanation #2 rejected.** Mechanism transfers to the bullish subset; the gate is operating on the right population.

**Gate is mechanically validated through three lines of evidence**: (a) original within-ticker IC, (b) strict-prior IC (no look-ahead), (c) within-bullish-subset IC (the gate's actual scope). All three converge: -0.49, -0.49, -0.42 respectively. The retrospective gap at N≥5 floor is now FULLY attributed to **explanation #1: low-N (5-19) percentile estimation noise**. Spec 003 FR-004's N≥20 floor is the empirically validated defense.

**SC-002 borderline-validated (2026-05-05, `experiments/2026-05-05-002-spec003-sc002/`)**: 25 fresh propagates (5 tickers × 5 mid-week dates) at T2 ~$10. Result: 0 gate fires across 25 propagates (gate is selective by design — AAPL bullish percentiles 30-55 stayed below threshold; INTC's high-percentile commits were all Underweight; GOOGL/JPM/MSFT under N≥20 floor as expected). After backfilling the 25 new propagates into cache (181 total rows), within-bullish-subset median IC = **-0.301**, meeting the SC-002 success criterion at exactly the threshold (≤ -0.30 target). 4 of 5 tickers with bullish n≥5 show negative direction (NVDA -0.40, GOOGL -0.77, JPM -0.30, MSFT -0.20; AAPL +0.16 is the persistent outlier across 3 measurements). Combined fire rate from retrospective + this experiment: 2 fires across 26 N≥20-eligible propagates (~7.7%). The gate is genuinely selective; mechanism reproduces in fresh data; SC-003 matched-grid experiment still needed to test active-mode behavior with non-zero fires.

**Spec 003** (`.specify/specs/003-analyst-contrarian-gate/spec.md`, commit e5dcd46) operationalizes this finding into a Portfolio-Manager-stage contrarian gate. Phase 1 + Phase 2 implementation shipped commit `f238f3a` (823 tests including 30 unit tests for the gate). **SC-001 end-to-end validated** by `experiments/2026-05-05-001-spec003-sc001-shadow-smoke/` — single shadow propagate on NVDA 2026-01-30 produced a clean Scenario A: gate annotation present in state log with all fields populated, mode=shadow, gate_skipped=None, gate_fired=False, pre_rating==post_rating==Overweight, no markdown annotation. Substantively notable: `would_fire = True` (NVDA 2026-01-30 bull_keyword_count = 81 at 85th percentile, above threshold 80) — if active mode had been on, OW would have been downgraded to Hold. This is exactly the case finding #4's mechanism predicts the gate should catch.

### Negative result added 2026-05-05 — most fundamentals-report features are between-ticker artifacts (refined 2026-05-05 evening — see candidate-4 above)

Artifact-checked the top 4 ICs from the eval report (`bear_bigram_count` +0.457, `conviction_density` -0.407, `hedge_density` +0.305, `bull_keyword_count` -0.306, all on `fundamentals_report`). All 4 aggregate ICs are statistically real (permutation p < 0.002, bootstrap CI excludes zero) but **all 4 are between-ticker artifacts**. Within-ticker IC is weak, noisy, and direction-inconsistent for every feature. `hedge_density` is the most striking — aggregate +0.305 but **within-ticker IC negative on 4 of 6 tickers** (Simpson's paradox).

**Important nuance (added 2026-05-05 evening)**: this negative result generalizes to "most featurizers don't carry within-ticker signal", NOT "no featurizer does." The within-ticker IC methodology fix surfaced `market_report bull_keyword_count` as a validated within-ticker predictor (publishable secondary finding #4 above). The negative result holds for the four `fundamentals_report` features tested; it does not hold for at least one `market_report` feature. A targeted aggregator on validated within-ticker features (the new candidate-4 plus possibly `investment_plan bull_keyword_count`, marginal at p=0.008) could outperform the fundamentals-based aggregator that Phase 1 + 5 tested.

**Full-corpus follow-up (2026-05-05 night, `claudedocs/within-ticker-full-artifact-check-2026-05-05.md`)**: artifact-checked all 8 remaining flagged Simpson's-paradox + inverse-pattern candidates from the eval report. Result: **only `market_report bull_keyword_count` is a real within-ticker predictor** in the entire corpus. Of the 8 new candidates, 5 are noise (p > 0.3 — `fundamentals_report` × {sentiment_score, negation_aware_sentiment_score, bull_bear_keyword_ratio, bear_keyword_count, percent_mention_count} + `market_report question_density`); 3 are marginal (pass α=0.05, fail Bonferroni — `news_report bull_bigram_count`, `investment_plan bear_bigram_count`, plus `investment_plan bull_keyword_count` from the prior round). The 3 marginals all share the same direction (negative within-ticker IC ~-0.27), consistent with finding #4's mechanism extending across analyst stages but without independent strong support — could be either correlated regime detection across analysts or genuinely weaker independent signals; SC-002 fresh-data evidence would discriminate. **Implication for spec 003**: choice of `market_report bull_keyword_count` as default gate signal is empirically optimal; pluggable-source User Story 4 has no immediate alternative to swap in.

**Bug fix follow-up (2026-05-05)**: the artifact-check uncovered a `fetch_returns` buffer bug — the "90d horizon" measurements were actually computed over ~50 trading days because the calendar buffer (`holding_days + 7`) was too tight. Fixed by widening to `int(holding_days * 1.5) + 7`. Re-ran the eval pipeline at true 90 trading days; **the artifact-check verdict is robust to the fix** — top-4 IC magnitudes shifted by <0.03 in absolute value, signs unchanged, between-vs-within-ticker pattern preserved. See `claudedocs/buffer-fix-comparison-2026-05-05.md` for the delta. Side effect: the 21d IC for `final_trade_decision` shifted from -0.172 to -0.103 (sub-horizon-shift effect from SPY edge cases at the old narrower buffer); the headline OW α claim could shift by ~0.07pp on rerun, but the moderate-confidence verdict stands.

**Methodology fix follow-up (2026-05-05)**: the within-ticker IC computation that the artifact-check scripts ran ad-hoc is now **wired into `tradingagents/signals/evaluation.py` and surfaced in every future eval report** as a `Within-IC@<longest>d` column with auto-flagged Simpson's-paradox indicator (⚠️ when aggregate sign disagrees with within-ticker median sign). The fresh report at `claudedocs/signal-evaluation-2026-05-05-within-ticker.md` reveals two patterns:

1. **Confirmed Simpson's-paradox artifacts** (auto-flagged): `fundamentals_report sentiment_score` (-0.279 aggregate, +0.166 within), `fundamentals_report negation_aware_sentiment_score` (-0.278 vs +0.167), `fundamentals_report conviction_density` (-0.404 vs +0.017), `fundamentals_report hedge_density` (+0.318 vs -0.010), `fundamentals_report bear_keyword_count` (+0.282 vs -0.014), `news_report bull_bigram_count` (+0.051 vs -0.269), `investment_plan bear_bigram_count` (+0.046 vs -0.262). These were all "between-ticker artifact" candidates the artifact-check would have caught one-by-one; the new report flags them automatically.

2. **Inverse pattern — within-ticker IC STRONGER than aggregate** (no flag, but the aggregate column was *under-stating* the signal). Most striking: `market_report bull_keyword_count` aggregate -0.011 but within-ticker -0.489 with **9 of 9 tickers negative**. Also `investment_plan bull_keyword_count` aggregate -0.199 vs within -0.295 (8 of 9 negative), and `investment_plan hedge_density` aggregate -0.145 vs within -0.189 (7 of 9 negative). These are **candidates for real within-ticker predictors** that the aggregate IC view obscured by averaging across ticker classes with different baseline α. Worth follow-up artifact checks: are these stable across periods? Across re-runs? The candidate list is now visible without one-off scripts.

The Within-IC column changes the eval report from "what features correlate with α across the corpus" (which is essentially ticker identification) to "what features correlate with α within each ticker, on average" (which is closer to a date-level prediction question). Both views are useful; surfacing both prevents future artifact-check rounds.

This **fully mechanically explains** Spec 001 Phase 1 failure (42.3% direction match) and Phase 5 failure (weight tuning overfits): the featurized prose carries between-ticker information ("which ticker has more bear language") but not within-ticker information ("which date for THIS ticker is a stronger commit"). The aggregator was trying to extract signal that wasn't there. See `claudedocs/featurizer-artifact-check-2026-05-04.md` for full per-ticker tables.

This is a useful prior for anyone considering "replace LLM PM with deterministic aggregator over featurized prose" approaches: the corpus-composition effect (ticker-class identification) will produce significant aggregate ICs regardless, and they won't transfer to per-(ticker, date) prediction.

### What got ruled out (negative findings as positive evidence)

- **Single-call architectural baseline (experiments 003, 004)**: replacing the 12-bot debate with one Claude call on the 3 analyst reports produced similar rating quality. Multi-agent debate doesn't dominate the single-call baseline on this substrate. The bull/bear stage adds prose volume, not predictive signal.
- **Featurization can't replace LLM synthesis (Spec 001 Phase 1)**: 42.3% direction match → the prose signals carry information the LLM PM uses but the heuristic featurizers can't extract. **Mechanism now characterized (2026-05-05)**: featurizers carry between-ticker information, not within-ticker; aggregator can't extract signal that isn't there.
- **Weight tuning overfits (Spec 001 Phase 5)**: 100% weight on `investment_plan` (the bridge synthesis) won train but test IC stayed -0.062. The corpus is too small / the signal-to-noise too low for grid-search weight tuning to generalize. **Mechanism now characterized (2026-05-05)**: same as above — between-ticker information doesn't generalize across train/test folds when both folds contain the same tickers.
- **Convergence shortcut needs different inputs (Spec 001 Phase 3)**: 0% fires at spec defaults — the featurization-derived magnitudes don't reach the >0.7 threshold.
- **All 4 strongest featurizer ICs are between-ticker artifacts (2026-05-05)**: bear_bigram, conviction_density, hedge_density, bull_keyword_count. Within-ticker IC near zero or sign-inconsistent across tickers.
- **Mode collapse to Hold is NOT unitary calibrated abstention (2026-05-08, WC-10 pilot)**: previously framed as a single "calibrated abstention" mechanism per Constitution VII v1.4.3. WC-10 ALT-A confirmation shows it's two-mechanism: (a) genuine ambiguity (the original framing) AND (b) schema-induced collapse (one-directional moderate-magnitude evidence trapped by the 5-tier categorical scale). Constitution amended to v1.5.0 to carve out the schema-artifact case. The original VII framing remains correct for sub-population (a); WC-10 is the empirical case for sub-population (b).

### What's still open (and what each would resolve)

> **Status note (refreshed 2026-05-09)**: WC-10 v2 + v3 BOTH RESOLVED (rows below); the WC-10 research arc is now complete at the question-resolution level. Question #5 (`bear_bigram_count` artifact check) RESOLVED 2026-05-04 (between-ticker artifact, not genuine 90d predictor — see "What got ruled out" section + `claudedocs/featurizer-artifact-check-2026-05-04.md`). The 4 remaining non-WC-10 questions retain their original priorities; cross-references added to the partial-answer evidence each has accumulated.

| Open question | What it'd resolve | Cost |
|---|---|---|
| Same-date rerun-variance: how much of date-level non-replication is stochastic LLM variance? | Whether Replicability-scope clarification is fundamental or fixable with more reps. If most variance is stochastic, the bucket-level signal is the load-bearing claim and date-level analysis should be retired. **Partial evidence**: 005-vs-007 NVDA case (10/10 OW → 6/10 OW + 4 Hold on same dates with same model) documented in Constitution VII Replicability-scope sub-section; suggests run-to-run variance is real but unquantified at the date level. **Refined 2026-05-09 (post-WC-11)**: WC-11 bounds the order-mechanism contribution to ±20pp on commit rate. The 005-vs-007 within-DEFAULT-order variance now sets a lower bound on stochastic-only variance. | $15 (T2) |
| Model-swap matrix (GPT-5.4 / Gemini 3.x vs Anthropic on same grid): is period-conditional realized α a model property? | Would tell us whether the Q1 2026 / Q4 2025 sign flip is Anthropic-specific or general. **Partial evidence**: Sonnet 4.6 + Opus 4.7 cross-period both show the Q1+ / Q4- pattern (3-period validation); GPT-5.4 + Gemini are open. Spec 001 Phase 4 per-bot routing enables mix-and-match without rebuild. | $40 (T3) |
| Bear-correct ticker generalization (XOM, PFE): does the bear-side regime-asymmetry hold beyond AAPL + INTC? | n=2 ticker base for the bear-asymmetry claim is thin. XOM + PFE adds 20 commit points in true bear regimes. **Note**: WC-10 v3 (Q4 2025 NVDA) tests bear-regime under continuous-scalar mode but uses NVDA which is a bull-regime ticker that fell — different mechanism from XOM/PFE which are bear-correct tickers in their own regime. The two tests are complementary, not substitutable. | $15 (T2) |
| Phase 4 cost-tier validation (n≥10 with bot_models override): do per-bot model swaps shift rating distribution beyond mode-collapse? | Empirical validation of the Haiku-for-quick + Opus-for-deep cost-savings story. **Status**: Phase 4 wired + live-validated at n=1 in `experiments/2026-05-04-006-phase-4-bot-llm-routing/`; the operator-facing claim needs distribution evidence at n≥10. | $10 (T2) |
| ~~`bear_bigram_count` IC = +0.457 at 90d artifact check~~ — **RESOLVED 2026-05-04**, see `claudedocs/featurizer-artifact-check-2026-05-04.md` + the "What got ruled out" entry above ("All 4 strongest featurizer ICs are between-ticker artifacts"). Pooled IC passes Bonferroni @ 0.05/280 (p<0.0001), but per-ticker IC is near-zero / sign-inconsistent across all 6 tickers. **Verdict: between-ticker artifact, not genuine 90d predictor.** No further investigation warranted. | (resolved) | $0 |
| ~~WC-10 v2 expansion to n≥100 paired propagates: does signed-rating × 21d-α correlation become statistically detectable?~~ — **RESOLVED 2026-05-09**, verdict **NULL on SC-005(b)** per `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md` (Landing PR #181). Combined v1+v2 (n=100) Pearson r = **+0.0918**, Spearman ρ = **+0.0410** — both BELOW ±0.197 critical at p=0.05. Scalar magnitude carries no detectable signal beyond what the binned-tier captures. SC-007 ALT-A generalization: **PARTIAL** — 5 of 8 tickers met ≥80% commit threshold; JNJ + GOOG + JPM fall back into VII original sub-population. SC-005(c) bullish-amplification REPLICATES (Buy n=20 α +2.93% / 80% hit). Branch C selected: bin-then-output pattern (5-tier external interface preserved; continuous internal). | (resolved) | $32 |
| ~~WC-10 bear-regime test (Q4 2025 NVDA cohort under continuous-scalar mode)~~ — **RESOLVED 2026-05-08**, verdict **PARTIAL ALT-A** per `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS.md` (Landing PR #153). v3 emitted 8/8 dates as Buy/OW (binned) where 5-tier emitted 0 OW + 1 UW + 7 Hold; α delta -0.22pp (within ±100bps NULL region; direction matches ALT-A). Constitution VII v1.5.0 → v1.5.1 (Patch D) per Landing PR #154 — caveat language preserved at v1.5.0 scope; empirical magnitude bound documented. Operational: Spec 009 Branch A activation does NOT require regime-aware gating as a hard requirement; runtime monitoring via `scripts/wc_10_underperformance_monitor.py` suffices. | (resolved) | $6.40 |

### Research yield assessment

**The project IS** (per CLAUDE.md): "a personal experimental fork repurposed as a research playground for studying multi-agent LLM debate dynamics. Equity-decision-making is the substrate (cheap objective ground truth), not the goal."

Against this stated purpose:
- ✅ **Primary question answered at moderate confidence** with 3-period evidence and explicit Bayesian posterior trajectory
- ✅ **Three secondary findings** that are non-obvious and publish-worthy (calibrated abstention reframe; replicability scope; substrate-specific calibration)
- ✅ **Negative findings on Spec 001 Phases 1/3/5** documenting the ceiling of "replace LLM with deterministic aggregator" approach — useful prior for anyone considering this direction
- ✅ **Infrastructure self-contained**: any of the open questions above can be answered with the current scaffolding; no new tooling required
- ⚠️ **Diminishing returns from here**: the 5 open questions above are tactical refinements; none would change the headline answer materially
- ⚠️ **Not "shipped product" yield**: framework is at LLM-single-call calibration ceiling; the trading-strategy use case is not viable. The trading substrate served its purpose (cheap evaluation), not the goal

**Verdict**: useful research yield is achieved. The corpus would publish as "an honest 22-experiment study of multi-agent LLM debate dynamics in a high-noise decision domain, with implementation lessons from two attempted refactors." Continued spend should pick from the open-questions table above with explicit hypotheses on what the new evidence would buy, rather than exploratory drift through new experiments hoping for a stronger headline.

The infrastructure-complete moment is the natural pause point. Whether to continue depends on whether the user has a specific question they want answered, not on whether more experiments are *possible*.

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

## Filter portfolio status (added 2026-05-06; expanded 1 → 5 → 7 → 8 → 9 → **10 sides** as of 2026-05-09 late-evening)

The framework now ships with 9 distinct rating-suppression filter MODULES across **10 filter sides** in the PM hook chain (Spec 007 has independent bull + bear branches counted separately; Spec 008 is a hybrid layer inside Spec 007 bull). 7 sides default-on or default-shadow, 3 sides default-off. As of post-2026-05-09 late-evening state: A3 has >30 supporting data points; spec 007 bull is empirically validated by Class 3 Opus retrospective DECISIVE PASS; spec 008 bull-only Hybrid C adds +3.35pp Δα beyond Class 3 alone but ships default-OFF pending live-mode ablation per SC-009; Spec X-1 institutional rotation ships default-shadow at small-sample n=12; **Spec 012 Class 4 macro DEPLOYED end-to-end via 5-PR bundle (#194 + #197 + #198 + #199 + #200) at default-SHADOW** per small-sample-caution (n=8 fires at retrospective; +24.07pp net Δα; mechanism-disjoint with A3).

| Filter | Mechanism class | Default | Threshold | Empirical support | Outcome |
|---|---|---|---|---|---|
| **A3 momentum** (`tradingagents/agents/utils/momentum_filter.py`) | backward-price (per-ticker) | ON | -5% / 30d | +0.70pp Δα over 43 UW commits (in-sample) | OK; correctly inert on regime-mismatch (007 INTC forensics) |
| **Spec 003 contrarian gate** (`tradingagents/signals/contrarian_gate.py`) | prose-density (per-ticker IC) | ON | 80th pct / N≥20 | +6.46% cumulative Δα at 21d (n=2); +0.65pp Δα across 11 eligible | OK; tiny sample. Re-run sweep after corpus +30. |
| **Spec 003.5 sector-baseline fallback** (same module, FR-004 amendment) | prose-density (sector-pool fallback) | ON | 80th pct / sector pool ≥ 20 | Closes cold-start universe gap | OK; doesn't help SC-003 Financials cohort (sector-rotation, not prose mean-reversion). |
| **Spec 004 sector-momentum filter** (`tradingagents/agents/utils/sector_momentum_filter.py`) | backward-price (sector ETF) | OFF | -5% / 30d | -0.45pp net Δα/n=73 (anti-predictive); SC-008 falsified | KEEP default-off; Constitution VIII grandfathered. |
| **Spec 006 bear-sector-symmetry** (`tradingagents/agents/utils/bear_sector_symmetry_filter.py`) | backward-price (ticker vs sector) | OFF | +5% / 30d | -0.71pp net Δα/n=36 (anti-predictive); SC-008 FAILED (5/18 cohort fires) | KEEP default-off; Constitution VIII grandfathered. |
| **Spec 007 forward-catalyst BULL** (`tradingagents/agents/utils/forward_catalyst_filter.py`; v0.7.0) | LLM-extracted feature (Opus default) | **ON @T=0.60** | 0.60 (score) | +14.43pp discrim / 88.9% hit / +2.24pp net Δα on n=33 (DECISIVE PASS) | Default-on; first forward-catalyst filter; SC-008 PASSES at 24/27. |
| **Spec 007 forward-catalyst BEAR** (same module; bear branch) | LLM-extracted feature (Opus default) | **SHADOW @T=0.50** | 0.50 (score) | +23.10pp discrim / 72.2% hit / +0.30pp net Δα | Shadow-mode-first per Constitution VIII; SC-008 PASSES at 13/18. |
| **Spec 008 Hybrid C calendar boost** (`tradingagents/agents/utils/calendar_boost.py`; v0.8.0) | hybrid (Class 3 LLM × Class 6 calendar) | **OFF** (operator opt-in) | window=14d / magnitude=0.5x | **+3.35pp Δα improvement vs Class 3 alone at window=14d** (n=37 fires @ 92.6% cohort hit, +11.30pp discrim PASS) | Default-off pending live-mode ablation per SC-009; bull-only (bear-side neutral at 14d / harmful at 21d). |
| **Spec X-1 C-4 institutional rotation BEAR** (`tradingagents/agents/utils/institutional_rotation_filter.py`) | quantitative-flow (13F ownership delta) | **SHADOW @T_outflow=0.05** | -5% institutional rotation / 30d | +10.29pp discrim / 75.0% hit / +5.41pp net Δα on n=12 (PR #75 retrospective) | Default-shadow per small-sample-caution; v1.4.3 additive PASS on 2 of 3 criteria vs Spec 007 bear union; first quantitative-flow filter. SC-009 + SC-010 follow-up gates deferred. |
| **Spec 012 Class 4 macro BEAR** (`tradingagents/agents/utils/macro_environment_filter.py`; PRs #194 + #197 + #198 + #199 + #200) | cross-asset/macro (VIX-snapshot threshold) | **SHADOW** | VIX < 18 | **+24.07pp net Δα / 75% cohort hit on n=8 retrospective fires** (PR #193) — PASS at v1.4.0 + v1.4.3 (mechanism-disjoint vs A3; +24.07pp incremental) | DEPLOYED at default-shadow (per Constitution VIII v1.4.0 small-sample-caution; n=8 at recommended threshold). First macro-environment-aware filter. SC-010 default-on flip requires 30+ live fires (audit via `scripts/class4_macro_shadow_audit.py`). |

**Two retrospectively SKIPPED spec candidates** (validation per Constitution VIII saved ~12-16h of empty-spec implementation):
- **Spec 005 candidate** (per-ticker-vs-sector BULL filter) — max +0.31pp net Δα across 79 commits, well below Constitution VIII's +1pp backward-price gate. See `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`.
- **Spec 009 candidate** (bear-inverted Hybrid C) — +0.00pp at every (window × magnitude) config; bear cohort's days-to-earnings distribution doesn't intersect with boost window enough to flip any fire decisions. See `claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.md`.

## 5th failure mode discovered (added 2026-05-06)

The sector-α attribution analyzer (`scripts/sector_alpha_attribution.py`, `claudedocs/sector-alpha-attribution-2026-05-06.md`) decomposes per-commit α into sign(α-vs-SPY) × sign(α-vs-sector-ETF) cells. **27 of 79 bullish commits (34.2%) land in `ticker_weak` (α<0 vs both)** with mean realized α-vs-SPY = -5.34%. The cohort is **88.9% Tech-concentrated** (24 of 27 are Technology); AAPL/MSFT/NVDA dominate the worst-10 list (10/10 entries). This is the **5th distinct failure mode** in the framework's failure-mode taxonomy:

| # | Failure mode | Caught by |
|---|---|---|
| 1 | Bear commits on mean-reversion-bound tickers | A3 (per-ticker absolute) |
| 2 | Bullish commits with within-ticker bull-prose density spike | Spec 003 (per-ticker prose) |
| 3 | Bullish commits with within-sector bull-prose spike (cold-start) | Spec 003.5 (sector-pool prose) |
| 4 | Bullish commits when sector ETF is in mean-reversion zone | Spec 004 (sector-ETF absolute, default-off) |
| **5** | **Bullish commits underperforming a rising sector — stock-specific α-vs-sector miss** | **None — backward-price-only signals fail (Spec 005 candidate retrospective; Constitution VIII)** |

**81.8% of LOSING bullish commits are 5th-failure-mode** (27/33 of α<0-vs-SPY bullish commits). Vast majority of bullish-commit losses are stock-specific, NOT sector-rotation. The SC-003 Financials cohort that originally motivated spec 003.5 + spec 004 is a SMALL subset of this much broader pattern. See `claudedocs/sector-alpha-attribution-2026-05-06.md` for per-sector concentration + worst-outlier listing.

## Bearish anti-calibration shock (added 2026-05-06)

Same sector-α attribution analysis: **18 of 37 bearish commits (48.6%) landed in `ticker_strong`** (α>0 vs both SPY AND sector) with **mean α-vs-SPY = +28.02%**. This is the largest single-metric anti-calibration finding in the corpus to date. A3 misses this entire cohort — A3 only fires when ticker is DOWN absolute; spec 006 was built to catch the inverse condition (ticker UP relative to sector) but failed empirically (only 5 of 18 cohort fires at +5% threshold; -0.71pp net Δα anti-predictive). The +28% cohort exists but is uncatchable via backward-looking price signals — the realized rally comes from forward catalysts (earnings, news) the filter cannot see at signal-generation time.

This finding reinforces the **bear-side regime-asymmetry** claim from Key Claim #3 — bear commits aren't uniformly anti-calibrated, but the failure mode is severe when it does occur (+28% mean is roughly 30× the typical rating-bucket effect size). Possible signal classes that might catch the cohort: news-density, options-implied-volatility, LLM-extracted "the bull case is already priced in" feature. None tested yet. Captured as deferred exploration in ROADMAP.

## Constitution Principle VIII added (2026-05-06; v1.3.0)

After three same-day retrospective failures (spec 004 -0.45pp, spec 006 -0.71pp, spec 005-candidate +0.31pp max), Constitution amended to add:

> **Principle VIII — Retrospective Before Spec for Backward-Looking Price Filters**: any filter whose mechanism is exclusively backward-looking + price-derived MUST pass a corpus retrospective showing **net Δα ≥ +1pp at the proposed default threshold AND cohort hit rate ≥ 40%** (when a target cohort is named) BEFORE the spec is written.

Cost asymmetry: $0/1h retrospective vs ~6-8h spec+impl+tests. Three failures in one day codified the lesson. Spec 004 + spec 006 grandfathered as pre-principle implementations; ship as operator-opt-in. A3 grandfathered (pre-dates principle). Future filters of this class follow the new gate. See `.specify/memory/constitution.md` Principle VIII for the full text.

## Constitution v1.4.3 — additive-to-existing-filter gate (added 2026-05-06 late-evening)

After Class 5 fundamentals-delta retrospective PASSED standalone (discrim +11.92pp / hit 96.3% / net Δα +4.37pp at T=0.02) but the post-hoc overlap analysis showed 89% of bull-cohort losers were ALREADY caught by Spec 007 + Class 5's incremental fires were 8 false-positive winners + 2 incremental losers (union HURT net Δα by -4.09pp), Constitution amended:

> **Principle VIII v1.4.3 — Additive-to-existing-filter gate**: any new filter retrospective that PASSES the standalone Constitution VIII gate MUST ALSO show net Δα improvement ≥ +0.5pp OR cohort hit improvement ≥ +5pp OR FP-rate improvement ≥ -10pp vs the union/intersection with the best-performing existing default-active filter in the same direction. Otherwise SKIP the spec entirely.

Without this gate, Spec 010 (Class 5 standalone) would have shipped — wasting ~6-8h on a redundant filter. Spec 008 (Hybrid C) is exempted by the hybrid-filter exception (spec ships its own "improves over underlying" criterion); Spec 007 is exempted by the cross-mechanism-class structural argument (FIRST forward-catalyst-class filter).

5 amendments to Constitution Principle VIII in one day (2026-05-06): v1.3.0 (backward-price gate) → v1.4.0 (forward-catalyst-class gate) → v1.4.1 (Principle VI sub: spec ships its retrospective) → v1.4.2 (Principle VIII sub: magnitude fungibility for hybrid filters) → v1.4.3 (Principle VIII sub: additive-to-existing-filter gate).

## 2026-05-07 morning extension findings

### Hold-rate is a load-bearing precondition for filter ablations (NEW)

SC-009 backtest mid-flight diagnostic (`claudedocs/sc-009-hold-rate-root-cause-2026-05-07.md`): in the first 7/36 propagates of `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/`, 6 returned Hold (86% rate). Root cause is the PM's calibrated Hold-rating behavior on extended-rally large-cap Tech (NVDA, MSFT, AAPL); all 4 PM-stage filters (Spec 003, Spec 004, Spec 006, Spec 007) work correctly but have NOTHING to fire on when PM commits to Hold.

**Mechanism**: Spec 003/007/008 gate on `pre_rating in {Buy, OW, UW, Sell}`. When PM picks Hold from start (per Constitution VII Calibrated Abstention), the filter chain has zero commits to suppress. SC-009 gate 2 (n_fired ≥ 8) becomes structurally constrained by PM commit rate, not filter calibration.

**Operational implication**: ablation experiments for PM-stage filters MUST select cohorts with high commit-elicitation probability (bear-correct + volatile + earnings-active mix). The original 18-large-cap-Tech cohort starves the ablation. Captured as `claudedocs/sc-009-expansion-contingency-design-2026-05-07.md` + scaffolded as `experiments/2026-05-07-002-sc-009-expansion/` (CONDITIONAL kick-off).

### PM Hold-rating + bullish prose can both be calibrated (NEW)

State-log inspection of NVDA 2026-04-17 (rated Hold) showed executive_summary text "Initiate NVDA at Overweight with disciplined tranched entry strategy targeting 4-6% portfolio position, built gradually over 4-8 weeks." Same pattern for MSFT 2026-04-24. The PM's structured rating field and prose recommendation can intentionally diverge per Constitution VII — Hold means "no commit on this propagate"; prose can still recommend "build to OW over weeks."

Downstream filters parse the rating not the prose. Future ANALYSIS.md framings must distinguish:
- "PM didn't commit" (Hold-regime starvation; filter has nothing to act on)
- "Filter fired but missed cohort" (filter calibration issue)
- "Filter fired and caught cohort" (filter working as designed)

Captured as memory `reference_pm_hold_with_bullish_prose.md` + `reference_pm_hold_regime_starves_filters.md`.

### Class C-1 (insider transactions) retrospective SKIP (NEW)

Bear-side mechanism exploration design doc (`claudedocs/bear-side-mechanism-exploration-2026-05-07.md`) enumerated 6 candidate mechanism classes for the +28pp `ticker_strong`-bear cohort. Class C-1 (insider transactions, prior-30d net buying) was the highest-prior candidate. Empirical retrospective (`claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.md`):

| Metric | Value |
|---|---|
| Tickers with ANY insider purchases | 7/18 (only INTC has 1 actual purchase event) |
| Cohort_b_bear_target rows with insider buys in prior 30d | 1/18 (5.6% < 60% gate) |
| Bear-side fire at T≥1 | n=5, net Δα = -2.23pp (anti-pred) |

**Verdict**: SKIP. Insider purchases at large-cap tech are extremely rare (officers exercise + sell options; rarely open wallet to buy). Per design doc decision tree: pivot to Class C-3 (analyst PT consensus delta).

### Spec 007 + Spec 008 v1.4.3 retroactive audits (NEW)

Both Spec 007 and Spec 008 EXEMPTED from Constitution v1.4.3 retroactive application:
- **Spec 008 Hybrid C** (`claudedocs/spec-008-v1.4.3-exemption-audit-2026-05-07.md`): hybrid-filter exception applies cleanly. Spec 008 is structurally INSIDE Spec 007; the v1.4.3 trigger criteria's 5th bullet explicitly names Spec 008 Hybrid C as the canonical exemption case.
- **Spec 007 forward-catalyst** (`claudedocs/spec-007-v1.4.3-overlap-audit-2026-05-07.md`): cross-mechanism-class structural argument. Spec 007 is the FIRST forward-catalyst-class filter; existing default-active filters at invocation time were prose-density (Spec 003 + Spec 003.5) and backward-price (A3) — different mechanism classes per v1.4.0's separate gate tracks.

Both audits would PASS the v1.4.3 numerical criteria if applied retroactively (Spec 008: +3.34pp net Δα improvement vs Spec 007 alone; Spec 007: +1.59pp vs Spec 003 alone). The exemption is consistent with the empirical reality.

## WC-10 v1 pilot — categorical bottleneck confirmed (added 2026-05-08)

**Source**: `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` + `specs/108-wc-10-continuous-scalar-rating/`. Cost: $16 (Constitution III T2). 40/40 propagates resolved without error.

**Design**: 10 dates × 2 tickers (NVDA + AAPL) × 2 modes (continuous-scalar `[-1,+1]` vs 5-tier categorical) on the same (ticker, date) grid. Filter-bypass mode (all 9 filters skipped) to isolate the schema effect from filter behavior.

**SC-007 falsification verdict**: ALT-A (categorical-bottleneck-confirmed) at distribution level. NULL + ALT-B both rejected.

| Metric | Result | Interpretation |
|---|---|---|
| WC-10 commit rate (`\|rating\|>0.2`) | 18/20 (90%) | NULL ("clusters near 0") rejected |
| 5-tier baseline non-Hold rate | 5/20 (25%) | Same dates, dramatically different |
| Commit ratio | **3.6×** | ALT-A predicted "substantially higher" — confirmed |
| Paired decisions differing | 15/20 (75%) | The schema change moves decisions, not just labels |
| WC-10 Buy n=6 mean 21d α | **+4.67%** | Bullish-side amplification well-calibrated |
| WC-10 Underweight n=6 mean 21d α | **+3.56%** | Bearish-side amplification anti-calibrated (all AAPL UW during +3-6% rally) |
| Signed-rating × 21d-α Pearson r | +0.065 (n=20) | SC-005(b) inconclusive at this n; needs n≥100 |

**NVDA case study**: continuous-scalar emitted bullish reads on every date (+0.38 to +0.72) while 5-tier emitted Hold on 8 of 10 dates. The 5-tier scale was suppressing 8 commits the framework would have made under continuous output. Realized 21d α on those 8 dates ranged +2.83% to +8.53% — the suppressed commits would have been profitable. The collapse-to-Hold on NVDA was a SCHEMA artifact, not calibrated abstention.

**AAPL case study**: continuous-scalar emitted 6 bearish reads (-0.22 to -0.38) where 5-tier emitted 3 UW + 7 Hold. The 5-tier scale's Hold-default partially CAUGHT the AAPL anti-calibration that continuous-scalar amplified. WC-10 doubled the bad-direction commit count on AAPL.

**Net signal value depends on the bull/bear regime mix.** Bullish-amplified commits (NVDA cohort) are well-calibrated; bearish-amplified commits (AAPL cohort) are anti-calibrated on this period. Generalization to bearish regimes is unverified.

**Constitution amendment** (PR #131, v1.4.3 → v1.5.0): Principle VII gets a "Schema-induced abstention is NOT calibrated abstention" sub-section. VII still applies to commits whose evidence is GENUINELY BALANCED (the original framing). VII does NOT apply where (a) evidence is one-directional but moderate-magnitude, (b) schema lacks a partial-confidence tier between commit and abstain, (c) empirical evidence shows the framework would commit if the schema permitted it. Where these three conditions hold, the fix is the scale, not the inference. New HYPOTHESIS.md operational test: structural changes that "reduce Hold rate" must justify which mode they target — genuine ambiguity (not VII-eligible) or schema-induced collapse (VII-eligible per WC-10 precedent).

**Empirical reframe of mode collapse**: prior corpus framings of "Hold rate is a load-bearing precondition for filter ablations" (`reference_pm_hold_regime_starves_filters.md`) and "Hold ≈ 0% median at every horizon" remain CORRECT but are now incomplete. The Hold rate is composed of two sub-populations:

- **Genuinely balanced cases** → calibrated abstention → schema-fix would NOT improve outcomes (per Constitution VII original framing)
- **One-directional moderate-magnitude cases** → schema-induced collapse → schema-fix WOULD surface signal (per WC-10 ALT-A)

Future ANALYSIS.md framings should attempt to attribute Hold commits to one sub-population or the other where possible. The continuous-scalar replay is the operational test: re-run a Hold cohort under WC-10 mode; the dates that emit `|rating|>0.2` are the schema-induced sub-population.

## WC-11 analyst-order randomization — first-speaker bias confirmed (added 2026-05-09)

**Source**: `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md` (Landing PR #177). Cost: $8 (Constitution III T2). 20/20 propagates resolved without error.

**Design**: 5 dates × NVDA × 4 analyst-order permutations (DEFAULT `[market, news, fundamentals]` + 3 alternatives) on the same date grid. Tests whether the framework's bucket-level commit rate is invariant under analyst ordering — i.e., whether prior corpus claims are robust to the implicit analyst-order choice.

**Verdict**: PARTIAL — both ALT-A (first-speaker bias) and ALT-B (last-speaker bias) triggers fire on the SAME permutation (`news_fundamentals_market`). NULL clearly REJECTED; cannot disambiguate ALT-A vs ALT-B at n=20 because the permutation is consistent with either mechanism.

| Metric | Result | Threshold | Trigger |
|---|---|---|---|
| Per-permutation commit rate range | **0% → 40%** | ±20pp from pooled mean | ALT-A AND ALT-B both met |
| News-first commit rate vs pooled | **+20pp** | ≥+20pp | ALT-A trigger met |
| Market-last commit rate vs pooled | **+20pp** | ≥+20pp | ALT-B trigger met |
| Dates with divergent ratings across permutations | **2 of 5** | — | substantively non-trivial |
| Pooled commit rate | 20% (4 of 20) | — | baseline |

**Operational implication**: the project's DEFAULT analyst order `[market, news, fundamentals]` is empirically biased TOWARD Hold relative to alternative orderings. Prior corpus bucket-level claims under DEFAULT order systematically UNDER-COUNT commits the framework would have emitted under news-first orderings. The 005-vs-007 NVDA finding (10/10 OW → 6/10 OW + 4 Hold) — both runs under DEFAULT order — is unaffected by the order-mechanism but sets the within-order stochastic-variance baseline against which order-specific variance is now bounded.

**Constitution amendment** (PR #179, v1.5.1 → v1.5.2): Principle VII gets an "Analyst-order scope" paragraph in its Replicability-scope sub-section. Future ablations targeting commit-rate metrics MUST either randomize analyst order within the cohort OR explicitly fix the order AND document analyst-order as a confounder + restrict claims to within-order-cohort comparisons.

**Sister to WC-10**: WC-10 found schema (5-tier categorical) was a structural Hold-amplifier; WC-11 finds analyst-order is a SEPARATE structural Hold-modulator. The two mechanisms are orthogonal — both apply within the same propagate. Suggests the framework's mode-collapse-to-Hold has at least THREE structural sources: (1) genuine ambiguity (Constitution VII original), (2) schema-induced collapse (Constitution VII v1.5.0 sub-section), (3) analyst-order-biased pooling (Constitution VII v1.5.2 sub-section).

## BR-3 Squeak market-analyst structured output — analyst-stage analog (added 2026-05-09)

**Source**: `experiments/2026-05-09-001-br3-squeak-market-analyst/ANALYSIS.md` (Landing PR #178). Cost: $8 (Constitution III T2). 20/20 propagates resolved without error.

**Design**: 5 dates × 2 tickers (NVDA + AAPL) × 2 modes (prose vs Pydantic-structured market analyst output) on the same (ticker, date) grid. Sister hypothesis to WC-10: WC-10 tests structured-vs-categorical at the PM stage; BR-3 tests prose-vs-structured at the analyst (market) stage.

**Verdict**: PARTIAL ALT-B — direction matches ALT-B (structured surfaces commits prose suppresses) but α magnitude is too small to validate calibration at this n.

| Metric | Result | Threshold | Trigger |
|---|---|---|---|
| Prose-mode commit rate | 0/10 (0%) | — | baseline |
| Structured-mode commit rate | 2/10 (20%) | — | +20pp shift |
| Commit shift (structured − prose) | **+20pp** | ALT-B requires ≥+20pp | TRIGGERED |
| α delta (structured − prose) | +0.24pp | ALT-B requires ≥+1.0pp | NOT met (PARTIAL) |
| Direction-correct commits | 1 of 2 | — | uninterpretable at n=2 |

**NVDA observation**: unanimous Hold across all 10 propagates (5 prose + 5 structured) despite NVDA realized 21d α ranging -4.11% to +15.01% across dates. The structured-mode mechanism only differentiates from prose on AAPL in this cohort — consistent with WC-10 finding that AAPL was the bear-side-amplified ticker (under WC-10, scalar mode emitted UW commits 5-tier kept as Hold).

**Constitution implication**: NO amendment required. PARTIAL ALT-B at n=20 doesn't meet ALT-B magnitude threshold. The Phase E architectural variant (structured-output-throughout) is NOT unblocked at this evidence level.

**Sister-experiment recommendation**: BR-3 v2 (extend to news + fundamentals analysts; ~$8 each) would clarify whether the analyst-stage effect is market-analyst-specific or generalizes across the 3 analyst stages. Cross-pollination L4 status (Squeak structured signaling) preserved at "pilot-eligible" rather than "ship-eligible."

**Joint WC-10 + WC-11 + BR-3 implication**: three separate structural choices (PM schema, analyst order, analyst output format) each independently move the framework's commit rate. The Hold-rate has at least 4 distinct structural sources now (Constitution VII original + v1.5.0 schema + v1.5.2 analyst-order + BR-3 weak analyst-format signal). Mode collapse is a multi-mechanism phenomenon, not a single-cause artifact.

## WC-10 v2 ticker expansion — Branch C selected, partial ALT-A generalization (added 2026-05-09)

**Source**: `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md` (Landing PR #181). Cost: $32 (Constitution III T2-boundary). 80/80 propagates resolved without error. Combined v1+v2 cohort: n=100.

**Design**: 8 tickers (NVDA, AAPL, MSFT, GOOG, AMZN, JPM, JNJ, XOM) × 10 dates (Q1 2026 window) under continuous-scalar mode. Filter-bypass mode (matches v1). Predecessor: v1 (n=20 NVDA + AAPL paired); sister: v3 (Q4 2025 NVDA bear-regime, PARTIAL ALT-A).

**SC-005(b) primary verdict: NULL** — combined v1+v2 (n=100) Pearson r = **+0.0918**, Spearman ρ = **+0.0410**. Both BELOW ±0.197 critical at p=0.05. The signed-scalar magnitude carries NO information beyond what the binned-tier captures.

**SC-007 ALT-A generalization: PARTIAL**

| Ticker bucket | Commit rate | Pattern |
|---|---:|---|
| NVDA, AMZN | 100% | ALT-A confirmed; full schema-induced |
| MSFT, AAPL, XOM | 80-90% | ALT-A confirmed |
| JPM, GOOG | 60-70% | ALT-A partial; intermediate band |
| **JNJ** | **10%** | **ALT-A REJECTED**; defensive-sector retains genuine Hold-default under continuous-scalar mode |

5 of 8 tickers cross the ≥80% threshold; JNJ + GOOG + JPM fall back into Constitution VII's ORIGINAL "genuine ambiguity" sub-population. The v1.5.0 carve-out is empirically validated as a sub-population, not a wholesale replacement of VII.

**SC-005(c) per-bucket replication** (combined v1+v2):

| Bucket | n | Mean α | Hit |
|---|---:|---:|---:|
| Buy | 20 | **+2.93%** | **80%** |
| Overweight | 32 | +2.10% | 53% |
| Hold | 23 | +0.16% | — |
| Underweight | 25 | +1.30% (wrong) | 32% |
| Sell | 0 | — | — |

Bullish-side amplification GENERALIZES at expanded n (Buy +2.93% / 80% hit is the strongest bullish signal in the WC-10 corpus); bearish-side anti-calibration also GENERALIZES except XOM (UW n=8 mean -1.45%, calibrated when ticker is in bear regime — matches the broader bear-side regime-asymmetry finding).

**Notable counter-findings**:
- **NVDA degenerate-attractor**: all 10 NVDA propagates emitted exactly +0.6200. Continuous-scalar mode does NOT prevent intra-ticker mode collapse to a single value when the LLM debate synthesis converges deterministically.
- **JPM strongly NEGATIVE within-ticker IC (-0.6656)** — anti-signal at within-ticker resolution. AAPL + MSFT + AMZN also show negative within-ticker correlation. Only XOM (+0.2659) and GOOG (+0.0857) show positive within-ticker ICs.
- **XOM bear-correct case** with UW α calibrated at -1.45% confirms bear-side regime-asymmetry holds under continuous-scalar mode.

**Branch C operational implication** (per pre-scaffolded landing playbook PR #161): WC-10 continuous-scalar mode SHOULD NOT ship as the operator-facing output schema. The bullish-amplification ergonomic gain is captured equally well by binning-then-emitting 5-tier. **Spec 009 Branch C activation** (PR #4 of v2 landing series) implements the bin-then-output pattern: continuous internal representation for richer audit trail; 5-tier external interface preserved.

**Constitution implication**: NO new amendment required. v1.5.0 + v1.5.1 framing is consistent with v2's findings — schema-induced collapse is real but bounded, sub-population carve-out generalizes to majority of ticker base, JNJ-style defensive tickers retain genuine ambiguity sub-population.

**WC-10 research arc complete**: v1 (categorical bottleneck confirmed at PM stage on 2 tickers) + v2 (PARTIAL generalization + Branch C verdict on 8 tickers, n=100) + v3 (PARTIAL ALT-A on Q4 2025 NVDA bear-regime) + Constitution v1.5.0 + v1.5.1 amendments. The arc spent **$54.40 LLM total** (v1 $16 + v2 $32 + v3 $6.40) and produced 4 ratified Constitution sub-sections + 1 selected production-deployment branch.

## BR-3 v2 (news + fundamentals analyst structured-output) — DIFFERENTIAL verdict (added 2026-05-09 evening)

**Source**: `experiments/2026-05-09-003-br3-v2-news-fundamentals/ANALYSIS.md` (Landing PR #225). Cost: $16 (Constitution III T2; user-authorized via PR #214). 40/40 propagates resolved.

**Design**: 2 sub-experiments × 5 dates × 2 tickers (NVDA + AAPL) × 2 modes. Sub-A: news_analyst_format prose vs structured. Sub-B: fundamentals_analyst_format prose vs structured. Sister to BR-3 v1 (market analyst) at PR #178.

**Verdict: DIFFERENTIAL**:

| Sub-experiment | Verdict | Commit shift | α delta | Per-ticker pattern |
|---|---|---:|---:|---|
| A (news_analyst) | **NULL-leaning** | 0pp | +1.60pp* | mixed (NVDA +1; AAPL -1) |
| B (fundamentals_analyst) | **PARTIAL ALT-B** | **+40pp** | +0.11pp | consistent (BOTH +2) |

*α delta on sub-A is single-row noise (1 NVDA structured Buy at +20% realized α dominates n=10 cohort); not a mechanism finding.

**Joint synthesis across all 3 analyst stages** (BR-3 v1 + v2):

| Stage | Verdict | Commit shift | Source |
|---|---|---:|---|
| Market analyst (BR-3 v1) | PARTIAL ALT-B | +20pp | PR #178 |
| News analyst (BR-3 v2 sub-A) | **NULL** | 0pp | PR #225 |
| Fundamentals analyst (BR-3 v2 sub-B) | PARTIAL ALT-B | **+40pp** | PR #225 |

**2 of 3 analyst stages carry the structured-output commit-shift bottleneck** (market + fundamentals); 1 of 3 does NOT (news).

**Asymmetric mechanism interpretation**: tools-rich analysts (market = technical indicators / fundamentals = financial metrics) carry the bottleneck; prose-heavy analyst (news = narrative) does NOT. When analyst output is fundamentally NUMERIC, prose serialization loses information that structured emission preserves. When NARRATIVE, prose IS the natural medium and structured-output forces compression that doesn't add value.

**Phase E architectural variant ("structured-output throughout") still NOT unblocked** at this evidence level: PARTIAL ALT-B α magnitudes BELOW ±1pp threshold can't validate calibration. Phase E remains conditional on a v3 cohort with n=30+ commits per analyst stage.

**Constitution implication**: NO amendment required. The pattern strengthens BR-3 v1 PARTIAL ALT-B framing rather than overturning it.

**Cross-pollination L4 status update**: Squeak structured signaling pattern preserved at "pilot-eligible (focus on fundamentals analyst stage)" — narrowed scope per BR-3 v2 strongest evidence on fundamentals.

## WC-11 v2 disambiguation — PARTIAL verdict + ticker-asymmetry (added 2026-05-09 evening)

**Source**: `experiments/2026-05-09-002-wc11-v2-disambiguation/ANALYSIS.md` (Landing PR #228). Cost: $24 (Constitution III T2; user-authorized via PR #214). 60/60 propagates resolved.

**Design**: 3 tickers (NVDA repeat from v1 + AAPL + MSFT NEW) × 5 dates × 4 analyst-order permutations.

**Verdict: PARTIAL** — NVDA reproduces v1 news_fundamentals_market elevation EXACTLY (40% in both v1 and v2); AAPL + MSFT show DIFFERENT per-permutation patterns:

| Permutation | NVDA | AAPL | MSFT | Pooled |
|---|---:|---:|---:|---:|
| market_news_fundamentals (DEFAULT) | 0% | 20% | 20% | 13% |
| news_fundamentals_market | **40%** | 20% | **40%** | **33%** |
| fundamentals_market_news | 0% | **60%** | **40%** | 33% |
| market_fundamentals_news | 0% | **60%** | 0% | 20% |

**Per-ticker pattern asymmetry**:
- NVDA: news_fundamentals_market is the elevated permutation (40%); reproduces v1 first-speaker effect
- AAPL: news-LAST orderings elevated (60% each); OPPOSITE of NVDA pattern
- MSFT: fundamentals-early pattern; doesn't fit pure first or last speaker hypothesis

**No single analyst-position rule explains all 3 tickers**. Whatever first-/last-speaker effect exists is conditional on (model × ticker × regime × prompt) per CLAUDE.md headline. The v1 ALT-A vs ALT-B ambiguity is now joined by a TICKER-ASYMMETRY finding.

**Cross-rerun-variance check (NVDA v1 vs v2)**: 2 of 4 NVDA permutations REPLICATE exactly between v1 and v2 (news_fundamentals_market 40% in both; market_fundamentals_news 0% in both); 2 vary by ±20pp (DEFAULT 20% → 0%; fundamentals_market_news 20% → 0%). Stochastic NVDA variance is approximately ±20pp at n=5 dates per permutation. The news_fundamentals_market elevation IS REAL on NVDA (replicated 40% exactly).

**Constitution implication**: Apply **Patch D from PR #215 conditional drafts** (CLARIFY; v1.5.2 → v1.5.3 PATCH; ticker-conditional clarification paragraph added to Analyst-order scope sub-section). Pre-scaffolded patch shipped via PR #215; deterministic application per the conditional-branch pattern.

**Operational implication**:
1. Continue to randomize analyst order OR document as confounder per v1.5.2
2. NOT assume news-first is uniformly preferable — empirically only NVDA-like tickers benefit
3. Per-ticker analysis is necessary; pooled analyses across heterogeneous ticker sets average out the order-effect

**v1 + v2 cumulative cost**: $32 LLM ($8 v1 + $24 v2). Disambiguation didn't yield clean ALT-A vs ALT-B answer; yielded ticker-asymmetry observation that EXTENDS the original v1 finding rather than disambiguating it.

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

**Status (2026-05-04 evening): SHIPPED + END-TO-END VALIDATED.** Phase C module `tradingagents/agents/utils/second_opinion.py` shipped in commit `5d68d33` with 29 unit tests + PM wiring + 3 config flags (default disabled). Smoke test in experiment `2026-05-04-005-phase-c-smoke-test` validated end-to-end against Anthropic Opus: NVDA 2026-01-30 produced Overweight commit + NEUTRAL annotation (PM bullish + second-opinion bullish at posterior 0.55, below 0.6 agreement threshold). All 4 success criteria from HYPOTHESIS met. Asymmetric handling works as designed. Phase C ready to enable per-experiment via `config["second_opinion_enabled"] = True`. Original divergent-reasoning recommendation below stays as historical record.



`reasoning_divergent` produced 3 substantive perspectives and a synthesis:

- **Risk Management Advocate**: integration transforms framework from point-estimate to uncertainty-aware — high disagreement signals conservative sizing, consensus enables aggressive allocation, frames decisions as risk-adjusted recommendations with quantified bounds.
- **Behavioral Finance Skeptic**: dangerous illusion of enhanced rationality — both systems trained on same historical patterns, will reproduce rather than correct for market biases. Disagreement creates analysis paralysis or false confidence in consensus.
- **Systems Reliability Engineer**: introduces single points of failure, latency bottleneck, chaotic behavior risk where small evidence-interpretation changes produce wildly different uncertainty signals.

**Synthesis**: build asymmetric handling — agreement boosts confidence/sizing, disagreement triggers human review (NOT algorithmic resolution). Build escape valves — system must degrade gracefully when reasoning_evidence fails. Implement time-boxed decision windows to prevent overthinking. **Verdict**: integration is worth building IF designed asymmetrically (agreement → augment, disagreement → flag for review), NOT as a calibration auto-correct.

## Spec 001 Phase 4 — Per-bot LLM model routing wired (added 2026-05-04 late-evening)

Phase 4 ships `tradingagents/signals/role_models.py::BotLLMFactory` per spec User Story 4 / FR-007. Maps `config["bot_models"]: dict[bot_id → model_name]` to per-bot LLM clients, falling back to the framework default `quick_thinking_llm` / `deep_thinking_llm` for any bot not in the dict. Clients cached by `(provider, model)` so two bots sharing a model share one instance. Provider-specific kwargs (`anthropic_effort`, `openai_reasoning_effort`, `google_thinking_level`, `backend_url`) forwarded automatically.

`GraphSetup` modified to accept an optional `bot_llm_factory`; when wired, every analyst/researcher/manager LLM lookup routes through `_llm_for(bot_id, role)`. When `bot_models = {}` (default), the factory transparently returns the framework defaults — **byte-identical behavior to pre-Phase-4 production** (FR-007 backwards-compat).

`TradingAgentsGraph` always constructs a factory and passes it down; behavior change is opt-in via config:

```python
config["bot_models"] = {
    "market": "claude-haiku-4-5",       # quick analyst → cheap model
    "fundamentals": "claude-opus-4-7",  # heavy analyst → premium model
    "research_manager": "claude-opus-4-7",  # synthesizer → premium
    "portfolio_manager": "claude-opus-4-7", # final decision → premium
}
```

18 unit tests + 3 live-construction integration tests (no mocks; real `create_llm_client` for anthropic + openai with placeholder API keys) cover: default-fallback (empty/missing/None bot_models), per-bot override builds new client, cache hits across bots on same model, separate clients for different models, fallback to default for unconfigured bot, provider-kwarg forwarding (anthropic/openai/google/backend_url), kwargs omitted when unset, `model_for_bot` reporting, end-to-end `GraphSetup` integration with both factory-wired and factory-None paths, and **factory returns the unwrapped LangChain LLM** (the result of `BaseLLMClient.get_llm()`, not the wrapper itself).

**Bug found by integration test** (caught before any propagate spent money): the original implementation stored the `BaseLLMClient` wrapper in the cache instead of calling `.get_llm()` to unwrap to the LangChain `ChatAnthropic` / `ChatOpenAI` instance. The wrapper has no `.bind_tools(...)` method, so analyst factories would have crashed at `chain = prompt | llm.bind_tools(tools)` on the very first per-bot routed call. Unit tests with mocked `create_llm_client` returning `MagicMock()` couldn't catch this — `hasattr(MagicMock(), "bind_tools")` is `True` because MagicMock fabricates any attribute. Fixed `_get_or_create_client` to call `.get_llm()` and added `hasattr(llm, "bind_tools")` integration tests that exercise real client construction.

**Status**: ✅ **end-to-end validated** by experiment `2026-05-04-007-phase4-bot-models-smoke`. NVDA 2026-01-30 propagated cleanly with `bot_models = {"market": "claude-sonnet-4-6"}` — the BotLLMFactory log line confirmed the override path was taken, the factory cache contained the Sonnet client, the propagate completed in 512s with rating Overweight (matching the Haiku-on-market baseline runs from 005 + 007). Without the wrapper-vs-LLM bug fix (commit `2a55c01`), this propagate would have crashed at `llm.bind_tools(tools)` in the market analyst.

**Documented constraint**: `anthropic_effort` config key forwards to ALL anthropic clients the factory builds, but Sonnet/Haiku reject the `effort` kwarg. Only safe to set `anthropic_effort` when every bot in `bot_models` (and the default deep+quick) is an Opus model. The experiment omitted `anthropic_effort` to avoid this constraint; production users should follow the same rule until per-model effort filtering is added.

**Operator use case unlocked**:
```python
config["bot_models"] = {
    "fundamentals": "claude-opus-4-7",     # heavy analyst → premium
    "research_manager": "claude-opus-4-7", # synthesizer (already deep by default)
}
```

The Haiku-for-quick + Opus-for-deep cost-tier story (4 quick analysts at Haiku ≈ 70% cheaper than at Opus, with no expected quality drop on tool-using ReAct loops) is the obvious near-term application. A larger n=10+ experiment with matched baselines is needed to measure whether per-bot model swaps shift the rating distribution beyond the framework's known mode-collapse behavior.

## Spec 001 Phase 3 — convergence shortcut doesn't fire on featurization-derived Signals (added 2026-05-04 late-evening)

Phase 3 ships two deterministic decision modules:
- `tradingagents/signals/shortcut.py` — `should_skip_debate(signals)` boolean per spec FR-006 (skip when 3+ Signals share a direction with magnitude > 0.7)
- `tradingagents/signals/budget.py` — `BotBudget` class with reservation + record + remaining + summary helpers per spec FR-005

Plus `scripts/forecast_shortcut_savings.py` to project token savings before wiring into production.

**KEY EMPIRICAL RESULT**: across the historical 156-propagate corpus, **0% of propagates would trigger the shortcut at the spec's defaults** (3+ bots, magnitude > 0.7). At loose thresholds (2+ bots, magnitude > 0.2): 17.3% skip rate → 5.2% projected savings — still below SC-004's ≥15% target.

**Why it doesn't fire**: the featurization-based `derive_signal_from_prose` produces magnitudes typically in [0.1, 0.5] (heuristic blend of evidence density + conviction density - hedging penalty, with conservative caps). Crossing >0.7 is essentially unreachable from prose alone. The same shape as Phase 1 SC-001: the featurization-based aggregator is less decisive than the actual PM.

**Implication**: Phase 3 production-pipeline wiring (skip-debate routing in `conditional_logic.py` + per-bot LLM-call budget instrumentation) is **moot on this corpus until Signals come from a different source**. Two paths forward:
1. LLM-emitted Signals (each analyst's `with_structured_output(Signal)` call replaces or augments the prose) — would have proper magnitude calibration from the LLM itself
2. Re-tune `derive_signal_from_prose` to produce higher magnitudes — but Phase 5 weight tuning showed featurization has a low IC ceiling, so cranking magnitude won't add real signal

The deterministic shortcut + budget modules ship clean (25 unit tests + corpus forecast script) but don't change production behavior. They're pre-positioned for the future where Signals are LLM-emitted.

**Phase 3.5 (production wiring) deferred**. The Phase 3 forecast result removes the urgency — there's no token savings to capture until the Signal-quality bottleneck is fixed. **Phase 4 (per-bot LLM model routing) shipped separately as wired-but-not-default infrastructure** (see next section) — it doesn't depend on Signal quality, just on whether the operator wants to mix Haiku/Opus per bot for cost/quality tradeoffs.

## Spec 001 Phase 5 + Phase 2 — weight tuning overfits; bots-mode wired as opt-in (added 2026-05-04 late-evening)

**Phase 5 (weight tuning, analytical)**: grid search over WEIGHTS to maximize aggregator IC vs realized α. Train/test date-ordered 70/30 split (n=109/47).

| Metric | Default (train) | Default (test) | Tuned (train) | Tuned (test) |
|---|---:|---:|---:|---:|
| IC vs α | -0.172 | -0.191 | **+0.079** | **-0.062** |
| Direction agreement | 46.8% | 31.9% | 57.8% | 38.3% |
| Within ±1 tier | 95.4% | 91.5% | 95.4% | 95.7% |

Tuned weights: 100% on `investment_plan`, 0% on all 4 analyst-prose bots. Train IC flips +0.079 but test IC stays -0.062 — **overfits, doesn't generalize**. SC-006 fails (test ±0.3pp of train would require IC drift ≤0.003; observed 0.141).

**Honest interpretation**: the analyst-prose featurizers carry minimal generalizable predictive signal in this corpus. Only `investment_plan` (the bridge synthesis) shows weak in-sample predictive value, but it doesn't replicate out-of-sample. The whole featurization-based-aggregator approach has a low ceiling on this data.

**Phase 2 (opt-in bots mode)**: shipped via `config["framework_mode"] = "bots"` flag. When set, the deterministic aggregator's output replaces the LLM-PM's `final_trade_decision` in `_run_graph`. Phase 1 shadow logging always runs regardless (the state log gets `signals: [...]` and `shadow_aggregate_decision: {...}` fields whether the flag is set or not). Default `framework_mode = "prose"` preserves existing behavior (FR-004 backwards-compat).

The `render_aggregated_decision_markdown` helper produces output parseable by `parse_rating` so memory log + signal processor consume bots-mode output identically to PM output.

Phase 2 is wired but UNTESTED end-to-end against a live propagate. Validation would require launching a propagate with `framework_mode=bots` set; deferred since the Phase 5 result suggests the aggregator's own quality is the limiting factor, not the wiring.

## Spec 001 Phase 1 — Shadow Aggregator: 42.3% direction match (FAILS SC-001 ≥80% target) (added 2026-05-04 late-evening)

Spec 001 Phase 1 (Shadow Aggregator) shipped via "Approach A" — derive Signals from analyst prose using the Phase 1.5+ featurizers (no new LLM cost). Aggregator: weighted sum of (direction × magnitude) → 5-tier rating with `DEFAULT_WEIGHTS` (market 0.25, news 0.20, fundamentals 0.30, sentiment 0.10, investment_plan 0.15).

Run against 156 historical state logs:

| Metric | Value | SC-001 target |
|---|---|---|
| Exact rating match | 66 (42.3%) | — |
| Within ±1 tier | 147 (**94.2%**) | — |
| Direction match | 66 (42.3%) | ≥80% — **FAIL** |

**SC-001 fails. Within-±1-tier passes at 94.2%.**

Confusion matrix observation:
- When actual=Hold (n=78), shadow goes OW (19), UW (18), or Hold (40), or even Buy (1) — shadow is more committed than the PM.
- When actual=Overweight (n=52), shadow says Hold 30 of 52 times — shadow is less committed than the PM.
- When actual=Underweight (n=25), shadow says Hold (14) or OW (5) instead of UW (6) — shadow disagrees on bear-side direction.

**Interpretation**: the multi-agent debate + synthesis + risk-debate + PM stages do NOT collapse to a weighted aggregate of analyst-prose featurization. The PM is committing on OW signals that featurization reads as Hold-able, AND committing on Hold signals that featurization reads as committable. Direction-disagreement on bear-side suggests the prose-anti-prediction findings (Phase 1.5+) are being partially MITIGATED by the synthesis stages — the actual PM's UW commits don't simply mirror the bearish prose.

This is consistent with the prior architectural finding: the framework's value is in the structured reasoning stages BEYOND the analyst prose. The prose carries some directional signal but the PM's eventual commit is shaped by debate dynamics, risk-debate moderation, and memory log context.

**Phase 1 closes spec 001 → spec 002 loop**: the bots-architecture aggregator now has measurable agreement statistics against the PM, computed for free from the existing cache. Phase 2 (opt-in `framework_mode = "bots"`) would route actual decisions through the aggregator and let us A/B test it against the prose path on identical inputs. Phase 5 (weight tuning) would optimize WEIGHTS against the corpus to maximize agreement (or alpha).

The 42.3% result motivates Phase 5 weight tuning more strongly than SC-001 anticipated — there's substantial room to bring the aggregator into closer alignment with the PM, OR to deliberately diverge it in ways that improve realized α.

## Phase 1.5+ structural featurizers — bear bigrams hit +0.457 IC at 90d (added 2026-05-04 late-evening; **artifact-checked 2026-05-05, restated**)

7 new structural featurizers added to FEATURIZERS (Phase 1.5+):
- `bull_bigram_count` / `bear_bigram_count` — curated 2-word phrase counts
- `negation_aware_sentiment_score` — flips sentiment when preceded by "not" / "no" / "n't"
- `question_density` — ?-marks per 1000 chars (uncertainty marker)
- `percent_mention_count` / `dollar_mention_count` — split numeric mentions
- `bull_bear_keyword_ratio` — [0, 1] probability-style scaling

**Initial finding**: `fundamentals_report bear_bigram_count` at 90d showed IC = **+0.457** (n=113), the strongest single IC in the corpus.

**Artifact check** (`claudedocs/bear-bigram-artifact-check-2026-05-04.md`, run 2026-05-05): the IC is **statistically real** (permutation p<2e-4 over 5000 shuffles, bootstrap 95% CI [+0.30, +0.60] excludes zero, passes Bonferroni at α=0.05/280) but **mechanistically misleading and not a publishable predictor**:

1. **The "90d horizon" label is wrong** — `fetch_returns(holding_days=90)` uses a `+7 calendar day` buffer, fitting only ~50 trading days into the window (median actual = 50, max = 67). The IC is over ~50 trading days, not 90. Bug in `fetch_returns`, not in the featurizer or eval.
2. **Per-ticker IC is near zero or negative** (AAPL +0.07, GOOGL +0.09, INTC -0.00, JPM -0.28, MSFT +0.34, NVDA -0.16). The aggregated +0.457 is driven by *between-ticker* variance, not within-ticker prediction. Knowing the bear_bigram_count tells you almost nothing about a single ticker's date-level α.
3. **Top-count rows are INTC bear prose in Q4 2025 / Q1 2026 with α between +31% and +85%** — the fundamentals analyst correctly identified bearish factors and was directionally wrong because INTC was in a bull regime. This is the same regime-asymmetry as the main UW-on-bull-regime-tickers finding, expressed at the prose-feature level.

Plus: the dominant bigram `("market", "share")` (115/315 occurrences = 36% of all fired bigrams) is semantically ambiguous — "expanding market share" is bullish, "losing market share" is bearish. The featurizer isn't measuring what its name implies.

**Restated finding**: the bigram featurizer's headline IC is **a third line of evidence for the regime-asymmetric bearish-commit story** (already documented at the rating + per-ticker levels), not an independent predictive signal. The "language-level anti-prediction is bidirectional" framing in the original write-up was wrong — it's the same anti-prediction, propagated from rating to prose because the bear-rated tickers in this corpus happened to be the bull-regime tickers that ripped.

| Featurizer family | Best IC at "90d" (~50 trading days actual) | Status after artifact check |
|---|---|---|
| Bigram (Phase 1.5+) | +0.457 `bear_bigram_count` fundamentals | **between-ticker artifact** — same anti-calibration as rating-level UW-on-bull-regime; not within-ticker predictive |
| Conviction density (Phase 1.5) | -0.407 `conviction_density` fundamentals | not yet artifact-checked; per-ticker breakdown likely shows similar pattern |
| Hedge density (Phase 1.5) | +0.305 `hedge_density` fundamentals | not yet artifact-checked |
| Bull unigram count (Phase 1.5) | -0.306 `bull_keyword_count` fundamentals | not yet artifact-checked |
| Sentiment score (Phase 1.5) | -0.266 `sentiment_score` fundamentals | not yet artifact-checked |
| Negation-aware sentiment | -0.266 (same as plain sentiment_score) | negation patterns rare in corpus |

**Implication for the synthesis essay**: the "three publishable secondary findings" enumerated in the synthesis (calibrated abstention, replicability scope, substrate-specific calibration) stand. The bigram IC is NOT a fourth — it's a re-statement of the bearish-asymmetry finding through a different lens.

**Followup completed (2026-05-05, `claudedocs/featurizer-artifact-check-2026-05-04.md`)**: artifact-checked the next 3 strongest ICs (`conviction_density` -0.407, `hedge_density` +0.305, `bull_keyword_count` -0.306). **All 4 features show the same between-ticker-artifact pattern**. None are within-ticker predictive:

| Feature | Within-ticker sign agreement | Within-ticker median IC |
|---|---|---|
| `bear_bigram_count` | 3+, 3- | +0.03 |
| `conviction_density` | 3+, 3- | +0.09 |
| `hedge_density` | **4-, 2+** (aggregate +0.305 — Simpson's paradox) | **-0.16** |
| `bull_keyword_count` | 2+, 4- | -0.05 |

`hedge_density` is the most striking: aggregate IC is **+0.305** but within-ticker IC is **negative on 4 of 6 tickers**. The "more hedging language → higher α" relationship reverses inside every individual ticker. Pure between-ticker artifact.

**Generalized claim**: featurization-based-aggregators on prose signals will not work on this corpus until either (a) the prose itself starts carrying within-ticker information that distinguishes good-commit dates from bad-commit dates within the same ticker — not currently happening at signal-detectable magnitude — or (b) the aggregator architecture learns ticker-specific means and only predicts deviations (mixed-effects / per-ticker fixed effects on top of the featurizer; would need its own validation).

This **fully mechanically explains** Spec 001 Phase 1 (shadow aggregator 42.3% direction match) and Phase 5 (weight tuning overfits, train +0.079 → test -0.062). The featurizers carry between-ticker information; the aggregator was trying to use them to make per-(ticker, date) predictions; the information just isn't there.

**Methodology fix needed**: `scripts/evaluate_signals.py` should compute within-ticker IC alongside aggregate IC. The difference between the two columns is the artifact magnitude. A future signal-evaluation report can then flag any feature where aggregate-vs-within sign-flips (Simpson's paradox) or magnitudes diverge (between-ticker dominates).

`bull_bear_keyword_ratio` mirrors `sentiment_score` exactly (mathematically equivalent up to scaling). Documented but redundant.

## Phase 2 drift detector + counterfactual — prose anti-prediction is time-localized (added 2026-05-04 late-evening)

Spec 002 Phase 2 shipped: `tradingagents/signals/drift.py` (rolling-IC degradation + KS-distribution drift) + `tradingagents/signals/counterfactual.py` (alpha-delta against alternative-rating rules) + matching CLI scripts. 19 new unit tests.

### Drift findings (n_recent=30, ic_threshold=0.05, ks_threshold=0.2)

**Multiple prose-feature ICs FLIP SIGN between baseline (older 126 rows) and recent (last 30 rows)**:
- `fundamentals_report sentiment_score`: baseline **-0.215** → recent **+0.129** (flipped to positive)
- `news_report sentiment_score`: baseline -0.092 → recent **+0.138** (flipped)
- `investment_plan numeric_mention_count`: baseline -0.164 → recent +0.012 (flipped to near-zero)
- `investment_plan value_length`: baseline -0.027 → recent +0.227 (flipped to strong positive)

Many KS-statistic alerts (>0.20) — recent value distributions differ from baseline. KS values: market_report sentiment 0.305, news_report sentiment 0.467, fundamentals sentiment 0.300, etc.

**Interpretation**: the prose-anti-prediction pattern from Phase 1.5 is **time-localized**, not stable across the whole corpus. Earlier dates showed strong anti-correlation (most of corpus = Q1 2026 bull-tailwind period); recent dates show neutral or positive correlation. Consistent with: Q1 2026 was bullish-then-mean-reverting; the prose-anti-prediction pattern reflects "early Q1 bullish prose was wrong because mean-reversion came later" rather than a stable framework property.

### Counterfactual findings (`hold-all-uw` rule)

Of 156 cached PM commits, 25 were UW. Flipping all 25 to Hold produces:
- Mean alpha delta: **+0.015% per commit** (across all 153 resolved pairs)
- Total alpha delta: +2.232% over 25 changed commits = **~+0.09% per changed commit**

Modest gain. Does NOT strongly support "stop all UW commits" as a portfolio rule. The bear-side anti-calibration loss is real but the absolute magnitude per commit is small enough that a wholesale UW→Hold override doesn't dramatically improve the corpus alpha.

This counterfactual provides a concrete dollar-equivalent: the framework's bear-side anti-calibration costs roughly 0.09% per UW commit. Across 25 commits ≈ 2.2% total alpha. Useful for sizing the "is this worth fixing?" question.

## Multi-horizon evaluation — horizon-dependent IC structure (added 2026-05-04 late-evening)

After multi-horizon was added to the evaluation harness (5d / 10d / 21d / 90d in parallel), per-feature IC reveals dramatic horizon-dependent patterns. **Strongest IC in the project**: `fundamentals_report conviction_density` at 90d = **-0.407**.

Horizon trajectories for top features:

| (Signal, Feature) | 5d IC | 10d IC | 21d IC | 90d IC | Pattern |
|---|---|---|---|---|---|
| fundamentals_report conviction_density | -0.024 | -0.041 | -0.162 | **-0.407** | monotonic strengthening |
| fundamentals_report bull_keyword_count | -0.081 | -0.117 | -0.132 | **-0.306** | monotonic strengthening |
| fundamentals_report hedge_density | +0.157 | +0.113 | +0.154 | **+0.305** | strengthening (positive direction) |
| fundamentals_report bear_keyword_count | +0.067 | +0.074 | +0.112 | +0.276 | monotonic strengthening |
| final_trade_decision rating | -0.0X | -0.112 | -0.172 | **-0.238** | monotonic strengthening |
| market_report sentiment_score | -0.036 | -0.165 | **-0.185** | -0.052 | peaks at 21d, fades at 90d |
| investment_plan sentiment_score | -0.143 | **-0.213** | -0.079 | -0.129 | peaks at 10d, fades at 21d, returns at 90d |

**Two distinct horizon-dependent patterns**:
1. **Monotonic strengthening** (fundamentals_report features, final_trade_decision rating) — anti-correlation grows with horizon. Suggests the framework's bullish prose at the fundamentals + decision level is most-anti-predictive over multi-quarter periods.
2. **Peaks-then-fades** (market_report, investment_plan, news_report sentiment) — anti-correlation peaks at 10-21d then weakens. Suggests medium-term reversal effect specific to the analyst-synthesis level.

The monotonic-strengthening pattern in fundamentals_report is the strongest evidence yet for the **language-level anti-prediction hypothesis** from the previous Phase 1.5 finding. It also fits the corpus-known pattern: most state logs are Q1 2026 (bull-tailwind period), and the 90d horizon for those dates extends well into the Q1 2026 → Q2 2026 mean-reversion window where bullish framework calls underperformed.

## Phase 1.5 prose-signal featurization — language-level anti-prediction (added 2026-05-04 late-evening)

After Phase 1.5 shipped, the evaluation harness produces IC for prose signals via 7 cheap featurizers (sentiment_score, bull/bear keyword counts, hedge density, conviction density, numeric mentions, value length). 5 prose signals × 7 features = 35 (signal, feature) IC values.

**MAJOR FINDING**: bullish prose features are systematically anti-correlated with realized 21d alpha across the corpus. Top |IC| pairs:
- `market_report sentiment_score`: **-0.185** (n=153) — most bullish-sentiment market reports → most NEGATIVE forward α
- `fundamentals_report conviction_density`: **-0.162** (n=113)
- `investment_plan hedge_density`: -0.162 (n=153)
- `fundamentals_report hedge_density`: **+0.154** (n=113)
- `market_report bull_keyword_count`: -0.149 (n=153)
- `market_report bear_keyword_count`: +0.144 (n=153)
- `fundamentals_report bull_keyword_count`: -0.132 (n=113)

**Pattern**: across market_report, fundamentals_report, investment_plan — bullish word choice is anti-predictive, bearish word choice is mildly predictive of better forward α. This is consistent with the `final_trade_decision` IC = -0.172 but goes deeper: the anti-calibration is at the **language level**, not just the rating level.

**Two interpretations**:
1. **Q1-2026 period artifact**: most of the 156-log corpus is the Q1 2026 bull-tailwind period, which we already know inverted on cross-period validation (008 NVDA Q4 2025). The language-level anti-correlation may reflect "Q1 2026 was a period where bullish commitment didn't predict alpha because mega-cap tech mean-reverted."
2. **Genuine framework prose-language anti-prediction**: the analysts' prose word choice is systematically inverse to forward returns at 21d.

This is the most empirically testable finding to date. Phase 2 (drift detector) + cross-period featurization could disambiguate (1) vs (2).

See `claudedocs/signal-evaluation-2026-05-04.md` for the full 35-row table.

## Phase 1 evaluation harness — first IC measurement (added 2026-05-04 evening)

Spec 002 Phase 1 (evaluation harness MVP) shipped after Phase 0 backfill from 156 historical state logs across 10 tickers. First Spearman IC measurement on the framework:

**`final_trade_decision` IC = -0.172 at 21d horizon** (n=153 cached pairs, hit rate 70.6%).

Negative IC means: the framework's PM rating score (Buy=+2, OW=+1, Hold=0, UW=-1, Sell=-2) is **mildly anti-correlated with realized 21d alpha across the cross-experiment, cross-ticker corpus**. This is consistent with — and a clean numerical summary of — the bear-side anti-calibration finding: UW commits on bull-regime tickers had high positive realized α (wrong direction), pulling the rank correlation negative even though OW alone had +1.52% positive α.

The 70.6% hit rate looks high but is dominated by Hold (the majority commit) being recorded as a "hit" when |α| < 0.5%. The IC is the more honest population summary.

**Phase 1 MVP scope**: only `final_trade_decision` is currently IC-evaluated (parsed 5-tier rating → numeric score). Five other synthesis-level signals (market_report, news_report, fundamentals_report, investment_plan, sentiment_report) are cached as prose and report coverage stats only. Featurization of prose signals is deferred to Phase 1.5+. See `claudedocs/signal-evaluation-2026-05-04.md` for the full report.

This is the first **single-number summary** of the framework's PM behavior across the corpus. It does not refute the bull-side α claim (still +1.52% n=73, 62% hit on OW alone) — it captures the bear-side anti-calibration as a population-level rank correlation.

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

## SC-003: 50-ticker signal-at-scale validation (added 2026-05-06)

**Experiment**: `experiments/2026-05-05-003-signal-at-scale/` — 50 diversified tickers spanning 8 sectors at single date 2026-04-03 with shadow gates. 50/50 propagated, 0 errors. Cost ~$20.

**Headline result — Scenario B (tech-specific signal)**:

| Bucket | n | Mean α (21d) | Hit rate |
|---|---|---|---|
| Overweight | 15 | **+5.96%** | 53% |
| Hold | 33 | -3.87% | 21% |
| Underweight | 2 | -15.60% | 0% (correct) |

The aggregate +5.96% bullish-bucket result is nearly 5× the 9-ticker corpus headline of +1.23% — but the per-sector breakdown reveals the signal is **dominated by Tech** (n=7, **+17.80%** mean) with Healthcare contributing modestly (n=2, +8.16%) and Financials actually NEGATIVE on its bullish picks (n=5, -7.07%). The 21d window 2026-04-03 → 2026-05-04 was a Tech-rally regime; the framework correctly went heavily-Hold across down sectors and bullish on Tech, but can't disambiguate "framework picks Tech bullish correctly" from "framework picked Tech bullish at a moment when Tech was about to rally."

**Counterfactuals confirm directional commits carry information**: invert-all -2.41% Δα, hold-all-ow -0.89% Δα, hold-all-uw -0.31% Δα. The framework's commits add value vs the all-Hold counterfactual.

**Implications**:
- The 9-ticker headline (+1.23%) is **confirmed in aggregate at 50-ticker scale**. The signal generalizes to a broader universe.
- Signal is **structurally tech-concentrated** at this single-date observation. Multi-window replication needed to disambiguate genuine cross-sector signal from Tech-rally-window-luck.
- Product surface implication: tech-weighted universes (or per-sector calibrated surfaces) get the strong signal; broad sweeps dilute it.
- 2 Underweight commits both correct (CVX -13%, HON -18%) — small n, but bear-side is on-direction at this date.
- Hold bucket mean α = -3.87% is anti-calibrated (Holds underperformed SPY by ~4%) — first time in the corpus where Hold isn't ≈ 0%; suggests this date's Hold population had a downward bias. Worth follow-up.

**Decision**: product-build path proceeds. Per HYPOTHESIS decision tree this is Scenario B → narrow product universe with empirical observation that universe selection matters. See `experiments/2026-05-05-003-signal-at-scale/ANALYSIS.md` for full sector breakdown, surprises, and follow-up questions.
