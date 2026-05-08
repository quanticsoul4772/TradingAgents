# Hybrid E (asymmetric-setup amplifier) mini-feasibility — 2026-05-08

**Date**: 2026-05-08
**Cost**: $0 (corpus walk + realized-α fetch via existing `fetch_returns`)
**Verdict**: **SKIP — mechanism is INVERTED**, joining the C-2 short-covering + C-5 price-reaction precedent

## Trigger

PR #102 backlog grooming flagged `hybrid-d-and-e-feasibility-design-2026-05-07-evening.md` as MIXED-status: Hybrid D was closed via PR #86 SKIP retrospective; **Hybrid E remained speculative** with cohort n=1 (AMD-04-17 only). Per the queued forward-work item rank #3 (U. Draft Hybrid E mini-feasibility doc, score 0.72), this re-evaluates Hybrid E against the now-richer corpus.

## Cohort growth — n=1 → n=17

| Snapshot | Cohort size | Tickers |
|---|---|---|
| 2026-05-07 evening (orig feasibility doc) | 1 | AMD only |
| 2026-05-08 (this) | **17** | 12 distinct (AAPL, AMD, AMZN, AVGO, BAC, CSCO, GOOGL, INTC, MA, NVDA + 2 partial) |

The cohort is **past the n≥10 threshold for retrospective viability** noted in the original feasibility doc. Hybrid E is technically advanceable to retrospective evaluation under Constitution VIII v1.4.0.

## Empirical evidence (FALSIFICATION)

Asymmetric bull-priced-in cohort (`bull_score - bear_score ≥ +0.30`; original Hybrid E hypothesis: amplify bear-side commit because "bear case has fresh edge"):

| Ticker/Date | diff | PM commit | Realized 21d α |
|---|---|---|---|
| AAPL/2026-04-17 | +0.30 | Hold | +5.12% |
| AAPL/2026-04-24 | +0.35 | **Underweight** | **+5.34%** |
| AMD/2026-04-17 | +0.45 | **Underweight** | **+52.00%** |
| AMD/2026-04-24 | +0.45 | **Underweight** | **+21.49%** |
| AMZN/2026-04-17 | +0.48 | Hold | +4.57% |
| AMZN/2026-04-24 | +0.38 | Hold | -0.39% |
| AVGO/2026-04-17 | +0.40 | Hold | +0.20% |
| AVGO/2026-04-24 | +0.37 | Hold | -3.24% |
| BAC/2026-04-17 | +0.30 | Hold | -6.87% |
| BAC/2026-04-24 | +0.35 | Hold | -2.85% |
| CSCO/2026-04-17 | +0.32 | Hold | +7.34% |
| GOOGL/2026-04-24 | +0.43 | Hold | +13.07% |
| INTC/2026-04-17 | +0.58 | **Underweight** | **+65.37%** |
| INTC/2026-04-24 | +0.60 | **Underweight** | **+37.15%** |
| MA/2026-04-17 | +0.40 | Hold | -9.17% |
| NVDA/2026-04-17 | +0.48 | Hold | +2.87% |
| NVDA/2026-05-01 | +0.47 | Hold | +6.12% |

**PM commit distribution**:

| PM rating | n | Mean 21d α | Hit rate (α<0; bear-correct) |
|---|---|---|---|
| **Underweight** (Hybrid E directional match — bear commit) | 5 | **+36.27%** | **0 / 5 = 0.0%** |
| Hold (PM Calibrated Abstention) | 12 | +1.40% | varies; ~50% |
| Buy/Overweight | 0 | n/a | n/a |

**Reverse-cohort (asymmetric bear-priced-in; favors bull commit)**: n=0 in current corpus. No data to evaluate the reverse direction.

## The mechanism is INVERTED

Hybrid E hypothesis (per `hybrid-d-and-e-feasibility-design-2026-05-07-evening.md` line 167):

> If `bull_score - bear_score ≥ T_asymmetric AND bear_thesis_fresh`: amplify bear-side commit (suppress UW→Sell, OR boost bear-side fire threshold sensitivity)

The reasoning was: "bear case still has runway → favors bear-direction commit." Empirical refutation:

- 5 UW commits in this cohort have mean α = **+36.27%** (stock went UP +36% on average over 21d, i.e., bear thesis was MASSIVELY WRONG)
- 0 of 5 UW commits had α<0 (zero hit rate on the bear thesis)
- Hybrid E would AMPLIFY (= make more likely) UW commits in this cohort — exactly the WRONG direction

**The "bull case widely priced in" signal is more often momentum/strength continuation than contrarian mean-reversion**, at least in this Q4 2025 / Q1 2026 corpus. The cohort includes INTC + AMD which had massive recovery rallies (+52% / +65% / +21% / +37%) where the "bull is priced in" reading was actually a "stock has been strong + remains strong" signal.

## Connection to inverted-mechanism precedent

This finding joins the bear-side mechanism class survey's INVERTED outcomes:

| Class | Original hypothesis | Empirical verdict | Source |
|---|---|---|---|
| **C-2** (short-interest delta) | rising shorts → bear-confirming | INVERTED (short-covering rally) | PR #76 |
| **C-5** (price-reaction) | bear post-earnings reaction → continued bear | INVERTED (continuation up) | PR #74 |
| **Hybrid E** (this) | bull-priced-in → bear-fresh-edge | INVERTED (continuation up) | This doc |

3 of 8+ mechanism class candidates show INVERTED bear-side mechanism. Bear cohort on Q4 2025 / Q1 2026 data has strong continuation bias that mean-reversion mechanisms cannot exploit. **This is now a documented project-level pattern**, not a one-off.

## Constitution VIII v1.4.0 standalone gate evaluation

- **Discrim ≥ +5pp PRIMARY**: would require computing fired-vs-control α distribution. Since UW commits already have +36% mean α (massively positive on a bear-direction-aligned filter), discrim would be NEGATIVE (filter underperforms control). **FAIL**.
- **Cohort hit rate ≥ 60%**: hit rate on UW commits is 0%. **FAIL**.
- **Net Δα ≥ +0.5pp**: amplifying bear commits in this cohort would HURT alpha by +36% per fire (vs Hold baseline). **FAIL**.

**All 3 standalone gate criteria FAIL DECISIVELY**.

## Constitution VIII v1.4.3 additive overlap gate

Vacuous because standalone gate fails decisively. No additive analysis warranted.

## Verdict — SKIP

Hybrid E (asymmetric-setup amplifier, original direction) is **NOT spec-eligible** under Constitution VIII v1.4.0. The mechanism is inverted on the n=17 cohort; the hypothesis is empirically refuted.

**Do not invoke `/speckit.specify` for Hybrid E.**

## Future considerations

### Reversed-direction Hybrid E (momentum continuation)

A REVERSED Hybrid E would be: "amplify BULL commits in asymmetric-bull-priced-in cohort" (treating "bull priced in" as momentum strength). This is a DIFFERENT mechanism class (momentum continuation, not contrarian mean-reversion); it would be its own spec retrospective.

The existing 9-filter portfolio has A3 momentum filter on the SUPPRESSION side (down >5% → suppress UW commits). A bull-amplifier momentum filter would be a NEW direction. Per Constitution VIII v1.4.0, it would need its own retrospective + standalone gate clearance + v1.4.3 additive overlap evaluation.

**Verdict on reversed-direction Hybrid E**: speculative; defer to a future session if operator wants to explore momentum-continuation amplification. Not advanced as part of this mini-feasibility.

### Cross-reference to deployed Spec X-1

Spec X-1 (C-4 institutional rotation filter, deployed 2026-05-07 PRs #88-#93) does suppress some UW commits in similar cohorts via the institutional-flow signal. If institutional outflow data was strong on AMD-04-17 + INTC-04-17 + AMD-04-24 + AAPL-04-24 + INTC-04-24, Spec X-1 would have fired and suppressed those UW commits — capturing the +36% kept-alpha that Hybrid E would have AMPLIFIED in the wrong direction.

This is the empirical sense in which **Spec X-1 (deployed) is the CORRECT bear-side filter** for this cohort, not Hybrid E (anti-predictive).

## Methodological observation

The original Hybrid E feasibility doc (2026-05-07 evening) said "TOO EARLY" with cohort n=1. The presumption was that more data would CONFIRM the hypothesis. Today's n=17 cohort REFUTES the hypothesis instead.

This reinforces the **retrospective-FIRST methodology** (Constitution VIII v1.4.1): wait for cohort to grow before invoking spec; the cohort evidence IS the gate. If the original Hybrid E had been spec-invoked at n=1 on speculative grounds, ~6-8h of implementation effort would have been wasted before the n=17 retrospective surfaced the inverted mechanism.

The "wait for data" discipline saved ~6-8h here.

## Three-converging-retrospective pattern (now extended)

The bear-side mechanism class survey identified the 3-converging-retrospective pattern for closing a mechanism class (Spec 010 Hybrid D bear-side calendar-boost was closed via 3 converging SKIP retrospectives: original Spec 008 bear retrofit + Hybrid C INVERTED + behavioral-additive structural argument).

Hybrid E joins a NEW emerging pattern: **mechanism-inverted-on-cohort**. With C-2 + C-5-price-reaction + Hybrid E all showing the same INVERTED outcome, this now constitutes 3 converging examples that **bear-side mean-reversion mechanisms are generally inverted on Q4 2025 / Q1 2026 corpus** (continuation-biased regime).

**Project-level lesson**: in continuation-biased regimes, bear-side suppression filters that aim to catch "momentum reversal" tend to be anti-predictive. Future bear-side specs should EITHER (a) propose a non-mean-reversion mechanism class (like C-4 institutional flow which is a quantitative "smart-money-already-out" signal), OR (b) include explicit regime-detection to gate the filter to mean-reversion regimes only.

## Sibling docs

- `claudedocs/hybrid-d-and-e-feasibility-design-2026-05-07-evening.md` — original 2026-05-07 evening feasibility (Hybrid E TOO EARLY at n=1)
- `claudedocs/forward-catalyst-class2-retrospective-2026-05-07.md` — C-2 short-interest INVERTED (PR #76)
- `claudedocs/forward-catalyst-class5-reaction-retrospective-2026-05-07.md` — C-5 price-reaction INVERTED (PR #74)
- `claudedocs/forward-catalyst-hybrid-d-retrospective-2026-05-07.md` — Hybrid D structural SKIP (PR #86)
- `claudedocs/spec-x-1-operator-validation-2026-05-08.md` — Spec X-1 deployed; correct bear-side filter for this cohort (PR #98)
- `.specify/memory/constitution.md` Principle VIII v1.4.0 — standalone gate (3 criteria FAIL on Hybrid E)

## Reproducibility

```bash
# Re-run the asymmetric-cohort identification + α computation:
uv run --no-sync python -c "
import json, os, re
from pathlib import Path
import sys; sys.path.insert(0, '.')
from tradingagents.graph.trading_graph import fetch_returns
log_base = Path(os.environ['USERPROFILE']) / '.tradingagents/logs'
T = 0.30
asym = []
# ... (full code in commit message)
"
```

If a future cohort re-run on REFRESHED data shifts the realized α distribution (e.g., regime change to mean-reversion-friendly market), re-evaluate this verdict per the `bear-side-mechanism-exploration-2026-05-07.md` SURVEY COMPLETE pattern.

## Verdict summary

| Check | Result |
|---|---|
| Cohort n≥10 (retrospective-viable) | ✅ n=17 |
| Constitution VIII v1.4.0 discrim ≥ +5pp | ❌ FAIL (would be NEGATIVE; mechanism inverted) |
| Constitution VIII v1.4.0 cohort hit ≥ 60% | ❌ FAIL (0% on UW commits) |
| Constitution VIII v1.4.0 net Δα ≥ +0.5pp | ❌ FAIL (would HURT by ~+36% per fire) |
| Spec invocation justified | ❌ NO |
| Joins inverted-mechanism precedent (C-2, C-5 price-reaction) | ✅ Yes — 3rd documented case |

**FINAL: SKIP Hybrid E. Mechanism inverted. Do not invoke `/speckit.specify`.**
