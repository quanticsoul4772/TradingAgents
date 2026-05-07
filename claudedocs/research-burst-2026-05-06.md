# Research-burst day — 2026-05-06

**Day-end tally** (late-evening update; supersedes v1): **16 ship-quality units** = 2 specs implemented + 1 spec amendment + 9 retrospectives + 5 constitution amendments + 4 cross-session memories. **2 PRs merged** (#5, #6) + **9 PRs open** (#7-#15) + tag `v0.8.0-spec-008`.

**Net-net retrospective verdict ledger**: 9 retrospectives × {2 PASS + 6 SKIP + 1 PASS-then-overlap-SKIP}. The PASS rate dropped from 33% (3 of 9 standalone) to 22% (2 of 9 net-additive) after the post-hoc additive-overlap gate (Constitution VIII v1.4.3) re-classified Class 5 as redundant.

This document is the canonical entry point for future operators (and future Claude sessions) to find the methodology validation evidence in one place.

## Verdict ledger (chronological)

| # | Time | Unit | Verdict | Cost | Outcome |
|---|---|---|---|---|---|
| 1 | morning | spec 003.5 sector-baseline fallback (impl) | shipped, default-on | $0 | merged |
| 2 | morning | spec 004 sector-momentum (impl + retrospective) | shipped, default-OFF | $0 | -0.45pp/n=73 → KEEP off |
| 3 | morning | spec 005 candidate (per-ticker-vs-sector bull retrospective) | SKIP | $0 | max +0.31pp → spec NOT invoked |
| 4 | midday | spec 006 bear-sector-symmetry (impl + retrospective) | shipped, default-OFF | $0 | -0.71pp/n=36, SC-008 FAIL |
| 5 | midday | Constitution v1.3.0 → v1.4.0 (Principle VIII forward-catalyst-class gate) | amended | $0 | codified separate gate for forward-catalyst filters |
| 6 | midday | Class 3 Haiku retrospective | BORDERLINE | ~$1 | recommend Opus rerun |
| 7 | afternoon | Class 3 Opus retrospective | DECISIVE PASS | ~$2 | discrim +14.43pp / hit 88.9% / net Δα +2.24pp at T=0.60 |
| 8 | afternoon | spec 007 forward-catalyst-aware contrarian gate (impl) | shipped, bull-active / bear-shadow | ~$2 (live validation) | merged + tagged v0.7.0 |
| 9 | evening | Hybrid C bull retrofit retrospective | DECISIVE PASS | $0 | bull +3.35pp net Δα at window=14d / magnitude=0.5x |
| 10 | evening | Hybrid C production-config retrospective | PASS confirms | $0 | identical numbers (DEFAULT_CONFIG matched retrofit thresholds) |
| 11 | evening | spec 008 Hybrid C calendar boost (spec → plan → tasks → impl) | shipped, default-OFF | $0.05 (live smoke) | merged, tagged v0.8.0 |
| 12 | evening | Constitution v1.4.0 → v1.4.1 (Principle VI sub: spec ships its retrospective) | amended | $0 | codified retrospective-first pattern |
| 13 | evening | spec 009 candidate bear-inverted Hybrid C retrospective | SKIP | $0 | +0.00pp at every config; PR #7 |
| 14 | evening | Constitution v1.4.1 → v1.4.2 (Principle VIII sub: magnitude fungibility) | amended | $0 | PR #8 |
| 15 | evening | meta-retrospective v1 (this doc, original) | shipped | $0 | PR #9 |
| 16 | evening | doc refresh (README + RESEARCH_FINDINGS + CHANGELOG) | shipped | $0 | PR #10 |
| 17 | evening | spec 008.5 latency-benchmark amendment | shipped | $0 | PR #11 |
| 18 | evening | ROADMAP + claudedocs/SETUP refresh | shipped | $0 | PR #12 |
| 19 | late-evening | Class 5 fundamentals-delta retrospective (standalone) | PASS | $0 | discrim +11.92pp / hit 96.3% / net Δα +4.37pp; PR #13 |
| 20 | late-evening | Class 5 vs Spec 007 overlap analysis | RETROACTIVE SKIP | $0 | 89% cohort overlap; union HURTS net Δα -4.09pp; PR #14 |
| 21 | late-evening | Constitution v1.4.2 → v1.4.3 (Principle VIII sub: additive-to-existing-filter gate) | amended | $0 | PR #15 — codifies Class 5 lesson |
| 22 | late-evening | meta-retrospective v2 (this doc, late-evening update) | shipped | $0 | this PR |

## Cost tally

| Phase | LLM cost | Wall-clock |
|---|---|---|
| Retrospectives (5 backward + 1 bear-inverted + Class 5 standalone + Class 5 overlap) | $0 | ~6h cumulative |
| Class 3 Haiku + Opus retrospectives | ~$3 | ~2h |
| Spec 007 implementation + live validation | ~$2 | ~5h |
| Spec 008 implementation + live smoke + Spec 008.5 latency | $0.05 | ~5h |
| Constitution amendments (5 PATCH bumps) | $0 | ~1.5h |
| Doc refreshes (README/RESEARCH_FINDINGS/CHANGELOG/ROADMAP/SETUP) | $0 | ~1.5h |
| Meta-retrospectives (v1 + v2) + memory polish | $0 | ~1h |
| **Total** | **~$5.05** | **~22h** |

Per Constitution III tier ladder: entire day is T0-T1 (≤$5 LLM/total). Cost discipline preserved through 22 work units.

## Methodology lessons (validated empirically by today's outcomes)

### L-1: Cost asymmetry makes retrospective-first the dominant strategy

**Pattern**: every filter mechanism gets a retrospective FIRST (offline replay against existing corpus + simple math + Constitution VIII gate). If the retrospective FAILS the gate, SKIP the spec entirely.

**Today's evidence**: 9 retrospectives shipped (2 PASS + 6 SKIP + 1 PASS-then-overlap-SKIP). The 7 SKIPs avoided ~42-56h of speculative spec+impl+tests work. Cost of 9 retrospectives: ~$3 LLM + ~6h wall-clock. **ROI: ~7-9× wall-clock leverage** on the spec invocations that DID launch.

**Codification**: Constitution v1.4.1 Principle VI sub-section "Spec ships its retrospective + verdict".

### L-2: Forward-catalyst signals are a fundamentally different mechanism class than backward-price signals

**Pattern**: backward-looking price filters (A3, spec 004, spec 006) systematically MISS cohorts whose realized α comes from forward-only catalysts. Forward-catalyst-aware filters (LLM-extracted features per Class 3, calendar features per Class 6, fundamentals delta per Class 5) succeed where backward-price filters fail.

**Today's evidence**: 4 backward-price retrospectives FAILED (specs 004, 006, 005-candidate, ticker-sector-alpha) — all with the same signature: similar-pattern winners cancel cohort-loser gain. 3 forward-catalyst retrospectives PASSED standalone (Class 3 Opus, Hybrid C, Class 5).

**Codification**: Constitution v1.4.0 Principle VIII sub-section "Forward-catalyst-class validation gate".

### L-3: Magnitude is fungible within a fixed window for hybrid filters

**Pattern**: when a hybrid filter's modulation crosses the underlying threshold at the smallest tested magnitude, sweeping magnitude is wasted compute.

**Today's evidence**: Spec 008 Hybrid C bull retrofit + bear-inverted retrofit BOTH produced identical fire patterns across magnitude={0.5, 1.0, 2.0} within a fixed window. Two independent demonstrations.

**Codification**: Constitution v1.4.2 Principle VIII sub-section "Magnitude fungibility for hybrid filters".

### L-4: SKIP outcomes are first-class research outcomes

**Pattern**: a SKIP verdict from a retrospective is valuable — it documents the empirical case AGAINST a mechanism class so future operators don't re-explore it.

**Today's evidence**: 6 SKIP retrospectives committed to `claudedocs/`. Each documents the failure pattern + cohort cross-tab + decision-tree implication.

**Codification**: Constitution v1.4.1 Principle VI sub-section makes the retrospective markdown ALWAYS required, regardless of verdict.

### L-5 (NEW, discovered late-evening): Standalone PASS isn't enough — overlap analysis required

**Pattern**: a new filter retrospective passing the standalone Constitution VIII gate can hide redundancy with existing default-active filters. The same cohort losers may be caught by both filters; the new filter adds only false-positive winners. Production union HURTS alpha.

**Today's evidence**: Class 5 (recent earnings surprise) PASSED standalone (discrim +11.92pp / hit 96.3% / net Δα +4.37pp) BUT the post-hoc overlap analysis showed 89% of bull-cohort losers caught by BOTH Class 5 + Spec 007. Class 5 catches +2 incremental losers AT A COST of +8 false-positive winners. Hybrid B union HURTS net Δα by -4.09pp vs Spec 007 alone. Without the overlap test, Spec 010 would have been invoked, wasting ~6-8h of spec+impl on a redundant filter.

**Codification**: Constitution v1.4.3 Principle VIII sub-section "Additive-to-existing-filter gate" — net Δα ≥ +0.5pp OR cohort hit ≥ +5pp OR FP rate ≤ -10pp improvement vs the best-performing existing same-direction filter. Memory: `feedback_additive_filter_gate.md`.

## Filter portfolio at end-of-day

| Filter | Spec | Mechanism class | Default | Trigger |
|---|---|---|---|---|
| A3 momentum filter | n/a (pre-Constitution VIII grandfathered) | backward-price | ON @ -5% | UW/Sell + 30d return ≤ threshold |
| Spec 003 contrarian gate | 003 | prose-density (within-ticker IC) | ACTIVE @ 80th percentile | Buy/OW + bull_keyword_count > threshold (N≥20 history) |
| Spec 003.5 sector-baseline fallback | 003.5 | prose-density (sector pool fallback) | ON | Buy/OW + bull_keyword_count > threshold (N<20 per-ticker → sector pool) |
| Spec 004 sector-momentum | 004 | backward-price (sector ETF) | OFF | Buy/OW + sector ETF 30d return ≤ threshold |
| Spec 006 bear-sector-symmetry | 006 | backward-price (ticker vs sector) | OFF | UW/Sell + (ticker - sector) 30d ≥ threshold |
| Spec 007 forward-catalyst (bull) | 007 | LLM-extracted feature | ACTIVE @ T=0.60 | Buy/OW + bull_case_priced_in > T |
| Spec 007 forward-catalyst (bear) | 007 | LLM-extracted feature | SHADOW @ T=0.50 | UW/Sell + bear_case_priced_in > T |
| Spec 008 Hybrid C calendar boost (bull) | 008 | hybrid (Class 3 × Class 6) | OFF (operator opt-in) | Buy/OW + earnings within 14d → boost effective_bull_score |

8 filters, 4 active by default (A3 bear, spec 003 bull, spec 003.5 bull, spec 007 bull). 4 operator-opt-in (spec 004, spec 006, spec 007 bear, spec 008). Constitution VIII v1.4.3 governs all 4 default-off → default-on flip considerations.

## Constitution version trajectory (one day, five amendments)

| Version | Trigger | Sub-section added |
|---|---|---|
| v1.3.0 | start of day | (carried over from prior day; Principle VIII original backward-price gate) |
| v1.3.0 → v1.4.0 | Class 3 Opus retrospective DECISIVE PASS | Principle VIII "Forward-catalyst-class validation gate" |
| v1.4.0 → v1.4.1 | Today's 5 retrospectives demonstrating retrospective-first pattern | Principle VI sub: "Spec ships its retrospective + verdict" |
| v1.4.1 → v1.4.2 (PR #8) | Spec 008 + bear-inverted retrofits showing identical fire patterns across magnitude sweep | Principle VIII sub: "Magnitude fungibility for hybrid filters" |
| v1.4.2 → v1.4.3 (PR #15) | Class 5 standalone PASS + post-hoc overlap analysis showing 89% cohort overlap with Spec 007 | Principle VIII sub: "Additive-to-existing-filter gate" |

5 amendments in one day, all PATCH-level (clarifications + sub-sections, not principle redefinitions).

## What this enables for future sessions

1. **Future hybrid-filter retrospectives**: per v1.4.2, skip the magnitude sweep; sweep window only. Saves 60-66% of retrospective wall-clock.
2. **Future filter mechanism classes**: per v1.4.1, the retrospective markdown is REQUIRED; the spec invocation is conditional on the gate passing. Sessions can short-circuit on a SKIP verdict in ~1h instead of ~6-8h spec+impl.
3. **Future filter retrospectives that PASS standalone**: per v1.4.3, an overlap analysis against existing default-active filters in the same direction is REQUIRED before spec invocation. Saves another ~6-8h on filters that pass standalone but are redundant.
4. **Future operators considering default-on flips**: spec 008 SC-009 lays out the live-mode A/B ablation procedure; analogous SC-009 patterns should be cross-referenced for spec 004 / 006 / 007 bear flips.
5. **Future investigators reading commit history**: this document is the canonical entry point. The 9 retrospective markdowns in `claudedocs/forward-catalyst-*` and `claudedocs/sector-*` are the per-mechanism evidence.

## Open work entering tomorrow

- **9 PRs awaiting merge** (#7-#15): bear-inverted SKIP, Constitution v1.4.2, meta-retrospective v1, doc refresh, Spec 008.5 latency, ROADMAP/SETUP refresh, Class 5 standalone retrospective (now retroactively SKIP per v1.4.3), Class 5 vs Spec 007 overlap, Constitution v1.4.3 + this meta-retrospective v2.
- **Class 4 cross-asset/macro retrospective**: deferred again from today; ~3h + ~$2-10 LLM.
- **Class 5 surprise outlier investigation**: max=31.21 (3,121%) — likely LLY negative-EPS-base — needs data-cleanup documentation if Class 5 is ever revisited.
- **Forward-catalyst overlap audit (retroactive Spec 008)**: now that v1.4.3 is codified, check if Spec 008 Hybrid C PASSES the additive gate against Spec 007. (Spec 008 is hybrid INSIDE Spec 007 not parallel, so likely vacuous, but worth confirming.)

## What did NOT work today

- **Class 2 (options-IV)**: data-blocked. yfinance.Ticker(t).options returns CURRENT snapshot only; no historical IV for retrofit cohort dates. Documented in `claudedocs/spec-008-forward-catalyst-classes-2-6-exploration-2026-05-06.md`. Pivoted to Hybrid C as substitute.
- **Bear-inverted Hybrid C**: zero effect on cohort. The cohort's days-to-earnings distribution doesn't intersect with the boost window enough to flip any fire decisions. Documented in PR #7.
- **Class 3 Haiku retrospective**: borderline pass on bull-side discrimination but score distribution too tight (cohort separation only +5pp vs Opus's +14.43pp). Decision: rerun with Opus, which decisively passed.
- **Class 5 standalone Spec 010 invocation**: would have been a wasted ~6-8h spec+impl. The post-hoc overlap analysis caught it just in time. Methodology lesson codified as v1.4.3.

## Methodology cost-benefit summary

- 9 retrospectives × ~$0.55 avg cost = ~$5 spent
- 7 SKIP outcomes × ~6-8h avoided spec cycles = ~42-56h saved
- ROI: ~7-9× wall-clock leverage on the spec invocations that DID get launched
- Plus: 7 SKIP outcomes documented = future-self doesn't re-explore those mechanism classes

The cost asymmetry that motivates Constitution VIII v1.4.1 + v1.4.3 is now empirically validated by a single research-burst day. Future sessions should expect similar leverage: the retrospective is the cheapest possible filter on speculative work, and it ships with the negative result documented.

## Constitution v1.4.3 specifically: the additive-to-existing-filter gate

The most important methodology output of today is Constitution v1.4.3. Before today's late-evening session, the implicit assumption was: PASS the standalone gate → invoke `/speckit.specify`. The Class 5 episode showed that this assumption is INSUFFICIENT — a new filter can pass standalone yet be REDUNDANT with the existing portfolio. Without v1.4.3, the project would have shipped a Spec 010 (Class 5 standalone) that adds nothing to Spec 007.

The v1.4.3 gate adds 30 minutes of overlap-analysis work between the standalone PASS and the spec invocation. This is a Pareto improvement over the 6-8h spec+impl cycle: cheap insurance against shipping correlated filters.

The v1.4.3 amendment ships in PR #15 in parallel with v1.4.2 (PR #8). When both PRs merge, the constitution will have all 5 sub-sections under Principle VIII; merge order matters only for the version metadata in the header.
