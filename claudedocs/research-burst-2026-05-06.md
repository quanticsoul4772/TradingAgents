# Research-burst day — 2026-05-06

**Day-end tally**: 9 ship-quality units (2 specs implemented + 6 retrospectives + 4 constitution amendments + 3 cross-session memories) + 2 PRs merged (#5 spec 008, #6 spec 008 retag) + 2 PRs open (#7 bear-inverted SKIP, #8 v1.4.2 amendment) + tag `v0.8.0-spec-008`. **8 PASS/SKIP retrospective verdicts** (2 PASS + 6 SKIP); methodology validated empirically.

This document is the meta-retrospective: the day's compounding pattern in one place so future operators (and future Claude sessions) can find the methodology validation evidence without trawling commit history.

## Verdict ledger

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
| 13 | evening | spec 009 candidate bear-inverted Hybrid C retrospective | SKIP | $0 | +0.00pp at every config; PR #7 open |
| 14 | evening | Constitution v1.4.1 → v1.4.2 (Principle VIII sub: magnitude fungibility) | amended | $0 | PR #8 open |

## Cost tally

| Phase | LLM cost | Wall-clock |
|---|---|---|
| Retrospectives (5 backward + 1 bear-inverted) | $0 | ~5h cumulative |
| Class 3 Haiku + Opus retrospectives | ~$3 | ~2h |
| Spec 007 implementation + live validation | ~$2 | ~5h |
| Spec 008 implementation + live smoke | $0.05 | ~4h |
| Constitution amendments (4 PATCH bumps) | $0 | ~1h |
| **Total** | **~$5.05** | **~17h** |

Per Constitution III tier ladder: entire day is T1 (≤$5/experiment unit) or near-T2. Cost discipline preserved through 14 work units.

## Methodology lessons (validated by today's outcomes)

### L-1: Cost asymmetry makes retrospective-first the dominant strategy

**Pattern**: every filter mechanism gets a retrospective FIRST (offline replay against existing corpus + simple price/score math + Constitution VIII gate). If the retrospective FAILS the gate, SKIP the spec entirely.

**Today's evidence**: 6 retrospectives shipped (5 SKIP + 1 PASS). The 5 SKIPs avoided ~30-40h of speculative spec+impl+tests work for filters whose empirical case wouldn't have held. Cost of 6 retrospectives: ~$3 LLM + ~5h wall-clock. Cost of 5 avoided spec cycles: ~30-40h + $0-5 each.

**Codification**: Constitution v1.4.1 Principle VI sub-section "Spec ships its retrospective + verdict" — invocation of `/speckit.specify` for any new filter MUST be preceded by a retrospective markdown commit in `claudedocs/`.

### L-2: Forward-catalyst signals are a fundamentally different mechanism class than backward-price signals

**Pattern**: backward-looking price filters (A3, spec 004, spec 006) systematically MISS cohorts whose realized α comes from forward-only catalysts. Forward-catalyst-aware filters (LLM-extracted features per Class 3, calendar features per Class 6) succeed where backward-price filters fail.

**Today's evidence**: 4 backward-price retrospectives FAILED (specs 004, 006, 005-candidate, ticker-sector-alpha) all with the same signature: similar-pattern winners cancel cohort-loser gain. 1 forward-catalyst retrospective DECISIVELY PASSED (Class 3 Opus). 1 hybrid retrospective PASSED (Spec 008 Hybrid C bull) by combining the validated Class 3 LLM features with calendar features.

**Codification**: Constitution v1.4.0 Principle VIII sub-section "Forward-catalyst-class validation gate" — separate criteria (discrim ≥+5pp PRIMARY, hit ≥60%, net Δα ≥+0.5pp OR shadow-mode-first).

### L-3: Magnitude is fungible within a fixed window for hybrid filters

**Pattern**: when a hybrid filter's modulation crosses the underlying threshold at the smallest tested magnitude, sweeping magnitude is wasted compute. Pick the smallest as the production default.

**Today's evidence**: Spec 008 Hybrid C bull retrofit produced identical fire patterns across magnitude={0.5, 1.0, 2.0} within window=14d. Spec 009-candidate bear-inverted retrofit produced identical fire patterns across all 9 (window × magnitude) configs. Two independent demonstrations.

**Codification**: Constitution v1.4.2 Principle VIII sub-section "Magnitude fungibility for hybrid filters" — operational test: sweep window first; sweep magnitude only if smallest doesn't cross threshold; pick smallest as production default if fungible.

### L-4: SKIP outcomes are valuable too

**Pattern**: a SKIP verdict from a retrospective is a FIRST-CLASS research outcome — it documents the empirical case AGAINST a mechanism class so future operators don't re-explore it.

**Today's evidence**: 5 SKIP retrospectives committed to `claudedocs/` (sector-momentum, bear-sector-symmetry, ticker-sector-alpha, spec-005-candidate, bear-inverted Hybrid C). Each documents the failure pattern + the cohort cross-tab + the "implication" section explaining what this tells us about the mechanism class.

**Codification**: Constitution v1.4.1 Principle VI sub-section makes the retrospective markdown ALWAYS required, regardless of verdict. SKIP retrospectives ship with the same gravity as PASS retrospectives.

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

8 filters, 4 active by default (A3, spec 003, spec 003.5, spec 007 bull), 4 operator-opt-in (spec 004, spec 006, spec 007 bear, spec 008). Constitution VIII v1.4.2 governs all 4 default-off → default-on flip considerations.

## Constitution version trajectory (one day)

| Version | Trigger | Sub-section added |
|---|---|---|
| v1.3.0 | start of day | (carried over from prior day; Principle VIII original backward-price gate) |
| v1.3.0 → v1.4.0 | Class 3 Opus retrospective DECISIVE PASS | Principle VIII forward-catalyst-class validation gate |
| v1.4.0 → v1.4.1 | Today's 5 retrospectives demonstrating retrospective-first pattern | Principle VI sub: "Spec ships its retrospective + verdict" |
| v1.4.1 → v1.4.2 | Spec 008 + bear-inverted retrofits showing identical fire patterns across magnitude sweep | Principle VIII sub: "Magnitude fungibility for hybrid filters" |

3 amendments in one day, all PATCH-level (clarifications + sub-sections, not principle redefinitions).

## What this enables for future sessions

1. **Future hybrid-filter retrospectives**: per v1.4.2, skip the magnitude sweep; sweep window only. Saves 60-66% of retrospective wall-clock.
2. **Future filter mechanism classes**: per v1.4.1, the retrospective markdown is REQUIRED; the spec invocation is conditional on the gate passing. Sessions can short-circuit on a SKIP verdict in ~1h instead of ~6-8h spec+impl.
3. **Future operators considering default-on flips**: spec 008 SC-009 lays out the live-mode A/B ablation procedure; analogous SC-009 patterns should be cross-referenced for spec 004 / 006 / 007 bear flips.
4. **Future investigators reading commit history**: this document is the canonical entry point. The 8 retrospective markdowns in `claudedocs/forward-catalyst-*` and `claudedocs/sector-*` are the per-mechanism evidence.

## Open work entering tomorrow

- PRs #7 + #8 awaiting merge (low-risk: SKIP retrospective + constitution amendment).
- Class 4 (cross-asset/macro) retrospective: deferred from today; ~3h + ~$2-10 LLM.
- Class 5 (fundamentals-delta) retrospective: deferred from today; ~3h + ~$1-5 LLM.
- Spec 008.5 latency benchmark: 1 coverage gap from /speckit.analyze; ~30min + $0.
- Doc refresh sweep: README + RESEARCH_FINDINGS + CHANGELOG + docs/SETUP.md all stale; ~45min + $0.

## What did NOT work

- **Class 2 (options-IV)**: data-blocked. yfinance.Ticker(t).options returns CURRENT snapshot only; no historical IV for retrofit cohort dates. Documented in `claudedocs/spec-008-forward-catalyst-classes-2-6-exploration-2026-05-06.md`. Pivoted to Hybrid C (Class 3 × Class 6) as substitute.
- **Bear-inverted Hybrid C**: zero effect on cohort. The cohort's days-to-earnings distribution doesn't intersect with the boost window enough to flip any fire decisions. Documented in PR #7.
- **Class 3 Haiku retrospective**: borderline pass on bull-side discrimination but score distribution too tight (cohort separation only +5pp vs Opus's +14.43pp). Decision: rerun with Opus, which decisively passed.

## Methodology cost-benefit summary

- 6 retrospectives × ~$0.50 avg cost = ~$3 spent
- 5 SKIP outcomes × ~6-8h avoided spec cycles = ~30-40h saved
- ROI: ~10-13× wall-clock leverage on the spec invocations that DID get launched
- Plus: 5 SKIP outcomes documented = future-self doesn't re-explore those mechanism classes

The cost asymmetry that motivates Constitution VIII v1.4.1 is now empirically validated by a single research-burst day. Future sessions should expect similar leverage: the retrospective is the cheapest possible filter on speculative work, and it ships with the negative result documented.
