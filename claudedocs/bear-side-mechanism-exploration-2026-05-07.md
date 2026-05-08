# Bear-side mechanism exploration — the uncatchable +28pp `ticker_strong` cohort

**Date**: 2026-05-07 (UPDATED 2026-05-07 evening — survey complete)
**Status**: ~~Pre-retrospective design exploration~~ — **6/6 mechanism class survey COMPLETE; C-4 is sole spec-eligible**
**Cost**: $0 (design + 7 retrospectives, all yfinance-only)

## SURVEY COMPLETE — empirical results (added 2026-05-07 evening)

The 6 candidate mechanism classes enumerated below were all evaluated.
Final scorecard:

| Class | Standalone Gate | Additive Gate | Spec-eligible? | Source |
|---|---|---|---|---|
| C-1 (insider transactions) | SKIP (anti-pred) | n/a | NO | PR #23 |
| C-2 (short-interest delta) | SKIP (mechanism INVERTED) | n/a | NO | PR #76 |
| C-3 (analyst PT delta) | NOT FEASIBLE (no historical) | n/a | NO | PR #40 |
| **C-4 (institutional ownership)** | **PASS (n=12, +5.41pp)** | **PASS (+8.06pp / +69pp)** | **YES (shadow-mode-first)** | PR #75 + PR #77 |
| C-5 (EPS surprise) | PASS standalone | FAIL additive (89% overlap) | NO | 2026-05-06 |
| C-5 (PRICE-REACTION) | SKIP (mechanism INVERTED) | n/a | NO | PR #74 |
| C-6 (bear-news density) | SKIP (structural redundant) | n/a | NO | PR #67 |

**1 of 6 mechanism classes spec-eligible**: C-4 (institutional ownership delta).

### Major findings from the survey

1. **Two C-classes show INVERTED mechanism on bear-side** (C-2 short-covering + C-5 price-reaction). Both originally hypothesized as mean-reversion signals; both empirically refuted — bear cohort on SC-009-era data has strong continuation bias that mean-reversion mechanisms can't exploit.

2. **C-4 catches 11 bearish commits Spec 007 ENTIRELY MISSES**. Cross-mechanism-class additive case (LLM semantic + quantitative 13F flow). Hit rate 81.8% on c4_only cohort.

3. **3 SKIP-types codified**: empirical (C-1, C-2, C-5 reaction), data-availability (C-3), structural (C-6).

4. **Constitution VIII v1.4.1 retrospective-first methodology validated 6 times in this survey alone**: ~$0 + ~3-30min per retrospective avoided ~6-8h × 5 = 30-40h of spec-and-impl work that would have been wasted.

### Spec-invocation pre-checklist for C-4 — ALL CLEARED + DEPLOYED

| Check | Status | Source |
|---|---|---|
| Standalone gate PASS | ✅ n=12 | PR #75 |
| Mechanism class distinct from existing | ✅ institutional-flow | PR #75 |
| v1.4.3 additive overlap | ✅ +8.06pp Δα / +69pp hit | PR #77 |
| Time-window discipline | ⚠️ valid until ~2026-05-15 (Q1 2026 13F refresh) — codified as Spec X-1 SC-009 | PR #66 + #75 |
| Sample-size confidence | ⚠️ n=12 single-period — codified as Spec X-1 SC-010 (n≥30 live ablation before active flip) | PR #75 |
| `/speckit.specify` | ✅ shipped via PR #88 | PR #88 |
| `/speckit.plan` | ✅ shipped via PR #89 | PR #89 |
| `/speckit.tasks` | ✅ shipped via PR #90 | PR #90 |
| MVP implementation | ✅ shipped via PR #91 (PR-A: T001-T015) | PR #91 |
| Remaining tests | ✅ shipped via PR #92 (PR-B: T016-T027) | PR #92 |
| Polish | ✅ shipped via PR #93 (PR-C: T028-T034) | PR #93 |

**Spec X-1 DEPLOYED end-to-end** at default-shadow bear-side / default-off bull-side. 18 tests + 4 config keys + ~190 LOC helper module + PM-hook chain integration. Constitution VIII v1.4.0 small-sample-caution sub-clause invoked → shadow mode pending SC-010 live ablation (n≥30 propagates). Operator-facing usage guide in `claudedocs/SETUP.md` section 10 (PR #94).

### Original design exploration (preserved below for traceability)

The original 6-class enumeration + decision tree below is preserved as a record of how the candidate classes were ranked + selected. The "recommended next research-burst-day work unit" (C-1) was empirically tested and SKIPPED (PR #23); the survey then proceeded through C-3 / C-5 / C-2 / C-4 / C-6 with empirical findings as documented above.

---

## The problem

From `claudedocs/sector-alpha-attribution-2026-05-06.md`: **18 of 37 bearish commits (48.6%) landed in `ticker_strong`** (α > 0 vs both SPY AND sector) with **mean α-vs-SPY = +28.02%**. This is the largest single-metric anti-calibration finding in the corpus to date.

After a full day of bear-side filter exploration on 2026-05-06:

| Filter / candidate | Mechanism class | Verdict on `ticker_strong` cohort |
|---|---|---|
| A3 momentum (production) | backward-price (per-ticker absolute) | MISSES — A3 only fires on ticker DOWN; cohort is ticker UP |
| Spec 006 bear-sector-symmetry (production OFF) | backward-price (ticker vs sector) | 5/18 cohort fires at +5%; -0.71pp net Δα anti-predictive |
| Spec 007 forward-catalyst BEAR (production SHADOW) | LLM-extracted feature | 13/18 cohort fires (72%); +0.30pp net Δα — passes criteria 1+2, criterion 3 just-under-gate |
| Spec 009-candidate bear-inverted Hybrid C | hybrid (LLM × calendar) | 0/18 cohort flips; +0.00pp Δα — bear cohort's days-to-earnings distribution doesn't intersect window |
| Class 2 (options-IV) bear-side | forward-catalyst (options market) | DATA-BLOCKED — yfinance returns current snapshot only |

**Production state**: Spec 007 bear is the strongest current contender at 72% cohort hit + criteria-1+2 pass. Shadow-mode-first per Constitution VIII v1.4.0 — needs n≥20 fresh propagates before active-mode flip.

**Open question**: what mechanism class might catch the remaining ~28% of cohort + push net Δα over the +0.5pp gate to enable an active-mode flip?

## Candidate mechanism classes (un-tested)

Each candidate has the v1.4.3 additive-overlap-vs-Spec-007-bear gate to clear, NOT just the standalone Constitution VIII forward-catalyst-class gate.

### Class C-1 — Insider transactions (cluster-buying SIGNAL ON BULL DIRECTION; absence-of on bear)

**Mechanism**: at signal-generation time, fetch insider transaction history (already wired in `get_insider_transactions`). For each bear commit, check whether insiders have been net BUYING in the prior 30/60/90 days. Hypothesis: `ticker_strong`-bear cohort tickers had insider buying that signals confidence the LLM didn't price in.

**Updated prior** (post-spec-007 + cohort analysis): **MODERATE-HIGH** — insider transactions are forward-information-bearing (insiders know what the market doesn't yet). The data is structured, free via yfinance, historically available (unlike options chains). Cluster-buying patterns (≥3 insiders buying within a 30-day window) are particularly predictive in equity research literature.

**Cost**: ~$0 retrofit. ~3h script. Zero LLM cost.

**Spec 010 fit candidate (suppress UW/Sell when insider net-buying ≥ X)**: STRONG. Different mechanism class than Class 3 (LLM prose), so v1.4.3 additive gate has good chance of passing.

**Pre-spec retrospective gate prediction** (Constitution VIII v1.4.0):
- Discrim: probably ≥+5pp on cohort_b (insider-buying tickers tend to have positive realized α)
- Cohort hit rate: probably ≥40% on `ticker_strong`-bear (8+ of 18 with insider net-buying in prior 30d)
- Net Δα ≥ +0.5pp: plausible if cohort hit + cleanness
- Additive vs Spec 007 bear: insider data is orthogonal to LLM prose synthesis — Spec 007 reads the analysis reports which MAY mention insider activity but probably without the structured + recent + cluster signals

### Class C-2 — Short-interest delta (rising short interest as bull-confirming, falling as bear-supporting)

**Mechanism**: short interest (% of float shorted) + delta vs prior 30d. Hypothesis: `ticker_strong`-bear cohort tickers had FALLING short interest (covering by sophisticated bears) that signals bear case is already played-out.

**Updated prior**: **MODERATE**. Short interest is reported semi-monthly (lag) but historically available. Falling short interest into a bear PM rating may signal "the bears already took their profit; further bear commits are too late."

**Cost**: ~$0 retrofit (yfinance shortRatio + shortInterest). ~3h script. Zero LLM.

**Spec 011 fit candidate**: MODERATE. Short interest is a coarse signal (semi-monthly granularity); may not discriminate cleanly at per-trade-date level. Worth exploring after Class C-1.

### Class C-3 — Analyst price-target consensus delta (rising PTs as bull-confirming on bear cohort)

**Mechanism**: aggregate analyst consensus PT + delta vs prior 30/60d. Hypothesis: `ticker_strong`-bear cohort tickers had RISING analyst price targets in the run-up — sell-side analysts were upgrading while the framework picked Underweight/Sell.

**Updated prior**: **MODERATE-HIGH**. Sell-side analyst PT deltas are public, structured, and a well-documented bull-side leading indicator. yfinance.Ticker(t).recommendations + .recommendations_summary provide upgrade/downgrade history.

**Cost**: ~$0 retrofit (yfinance free). ~4h script (data structure is gnarly across yfinance versions). Zero LLM.

**Spec 012 fit candidate**: STRONG. Analyst PT data is orthogonal to Class 3 LLM prose synthesis (LLM reads the analysis reports BUT the analysts themselves are external; the framework's own analysts are the LLM's synthesis layer, not the same as Wall Street consensus).

### Class C-4 — Fund-flow / institutional ownership delta

**Mechanism**: net institutional ownership change (13F filings) over prior quarter. Hypothesis: `ticker_strong`-bear cohort had NET INSTITUTIONAL ACCUMULATION in the prior quarter — the smart money was buying into the strength.

**Updated prior**: **LOW-MODERATE**. 13F filings have a 45-day lag from quarter-end, so the signal is stale by ~6-8 weeks at trade time. This may be too laggy to catch the +28pp signal, which is concentrated within the 21-day forward window.

**Cost**: ~$0-2 retrofit (yfinance limited; sec.gov 13F parser may need a one-off script). ~6h script.

**Spec 013 fit candidate**: WEAK due to lag. Skip unless C-1 + C-3 fail.

### Class C-5 — Recent earnings PRICE reaction (vs historical)

**Mechanism**: at trade_date, look back to most recent earnings event. Compute the 1-day price reaction vs the prior 4-quarter average price reaction. Hypothesis: `ticker_strong`-bear cohort tickers had ABOVE-AVERAGE earnings price reactions that signal the market re-rated the company AFTER earnings — the framework's bear thesis is now stale.

**Updated prior**: **MODERATE**. Earnings price reaction is a single-event signal (quarterly), historically available via yfinance.history around earnings_dates. Quick to compute.

**Cost**: ~$0 retrofit. ~3h script. Zero LLM.

**Spec 014 fit candidate**: MODERATE. Single-quarter signal may have noise; multi-quarter average smoothing helps.

### Class C-6 — News-density on the BEAR SIDE specifically (bearish narrative absent)

**Mechanism**: at trade_date, query exa for recent news on the ticker. Featurize bearish keyword density in headlines. Hypothesis: `ticker_strong`-bear cohort tickers had ABSENT bearish narrative in recent news — the framework's bear thesis lacks media reinforcement.

**Updated prior**: **LOW**. Spec 003 already partially measures this via the bear_keyword_count side of the prose-density features. Class C-6 would be a strict subset of Spec 003's input space; correlation likely high, additive value low.

**Cost**: ~$0 retrofit. ~3h script.

**Spec 015 fit candidate**: WEAK. Likely fails v1.4.3 additive-overlap-vs-Spec-003 gate.

## Hybrid combinations to consider (post-individual-class evaluation)

If multiple individual classes PASS standalone but FAIL additive vs Spec 007 bear:

### Hybrid D-1 — Spec 007 bear × Class C-1 insider transactions (intersection)

**Rationale**: Spec 007 bear catches 13/18 cohort at 72% hit but +0.30pp net Δα (just under +0.5pp gate). If C-1 insider-buying catches a complementary ~3-5 cohort members the LLM missed, the union may hit 16-18/18 with sufficient net Δα.

### Hybrid D-2 — Spec 007 bear × Class C-3 analyst PT delta (intersection)

**Rationale**: Spec 007 bear + analyst PT delta — bear case is suppressed only when BOTH (LLM thinks bear case is priced in) AND (analyst PTs are rising). Should reduce false positives without losing true positives.

## Recommended execution order

Per Constitution VIII v1.4.1 retrospective-first + v1.4.3 additive-overlap discipline:

### Spec 010 candidate (NEXT) — Class C-1 (insider transactions) retrospective

1. Build `scripts/forward_catalyst_class_c1_insider_retrospective.py`
2. For each bear commit in cohort + controls, fetch insider transactions in prior 30/60/90 days
3. Featurize: insider net-buy count, insider net-buy dollar, # distinct insiders
4. Sweep thresholds; evaluate Constitution VIII v1.4.0 gate
5. **If standalone PASS**: also run additive-vs-Spec-007-bear overlap analysis per v1.4.3
6. **Decision tree** (per v1.4.3 + standalone gate):
   - Both PASS → invoke Spec 010 (insider transactions standalone)
   - Standalone PASS but additive FAIL → consider Hybrid D-1 (Spec 007 × C-1) retrospective; SKIP standalone
   - Both FAIL → SKIP entirely; document negative result

**Cost**: ~$0 + ~3h. Zero LLM. Constitution III T0.

### Spec 011 candidate (FUTURE) — Class C-3 (analyst PT delta) retrospective

Run after Spec 010 verdict lands. Same workflow.

### Spec 012 candidate (FUTURE) — Class C-5 (earnings price reaction) retrospective

Run after C-1 + C-3 verdicts. Lower priority due to single-event noise.

### NOT RECOMMENDED for spec invocation

- **Class C-2 (short-interest delta)**: signal granularity too coarse (semi-monthly); skip unless C-1, C-3, C-5 all fail
- **Class C-4 (institutional ownership)**: lag too long (45+ days from quarter-end); skip
- **Class C-6 (bear-news-density)**: redundant with Spec 003's bear_keyword_count side; skip

## Constitution VIII application

Each candidate retrospective follows the v1.4.0 forward-catalyst-class gate:
1. Discrim ≥ +5pp in correct direction (PRIMARY)
2. Cohort hit rate ≥ 60% (when target cohort named — here, `ticker_strong`-bear with 18 members)
3. Net Δα ≥ +0.5pp at proposed default OR shadow-mode-first

PLUS the v1.4.3 additive-to-existing gate (NEW since 2026-05-06 late-evening):
- Net Δα improvement ≥ +0.5pp for the union vs best existing default-active bear-side filter (currently A3, since Spec 007 bear is shadow not active)
- OR cohort hit improvement ≥ +5pp for the union
- OR FP rate improvement ≥ -10pp for the intersection

Note: the v1.4.3 gate's "best existing default-active filter" baseline is currently weak on the bear side (only A3, which misses the cohort entirely). So a candidate need only show ANY net Δα improvement to clear the additive gate. This is favorable for new bear-side filters — the bar is lower than for new bull-side filters (which face Spec 003 + spec 003.5 + Spec 007 bull).

## Operational outcome

**Recommended next research-burst-day work unit**: Class C-1 (insider transactions) retrospective. Highest prior, lowest cost, freshest mechanism class.

If C-1 PASSES both gates → Spec 010 candidate justified → invoke `/speckit.specify`.
If C-1 FAILS standalone → SKIP + document; pivot to C-3 analyst PT delta.
If C-1 PASSES standalone but FAILS additive vs Spec 007 bear → consider Hybrid D-1 retrospective (Spec 007 bear × C-1 intersection).

**Wall-clock estimate for full bear-side exploration**: ~3 candidate retrospectives × 3h each = ~9h spread across 1-2 future research-burst days. Cost: ~$0 (no LLM).

## Blocking concern

The +28pp `ticker_strong`-bear cohort has n=18. Statistical power for net Δα discrimination at this cohort size is borderline. A 50-ticker SC-003 cross-window replication would expand the cohort to ~40+, dramatically tightening the variance bands. This is a separate work track (T3 cost ~$40 for the replication propagates) but would strengthen ALL future bear-side retrospectives, including C-1.

If C-1 retrospective produces an INCONCLUSIVE verdict on the n=18 cohort, the next move is the cohort expansion, not pivoting to C-3.

## Cross-references

- `claudedocs/sector-alpha-attribution-2026-05-06.md` — original cohort discovery
- `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` — Spec 007 bear-side numbers (13/18 hit, +0.30pp Δα)
- `claudedocs/forward-catalyst-hybrid-c-bear-retrospective-2026-05-06.md` — bear-inverted Hybrid C SKIP
- `claudedocs/spec-008-forward-catalyst-classes-2-6-exploration-2026-05-06.md` — Class 2 options-IV DATA-BLOCKED finding
- `.specify/memory/constitution.md` — Principle VIII v1.4.0 + v1.4.3 gates
