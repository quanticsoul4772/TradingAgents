# Spec 008+ candidates — design exploration of remaining forward-catalyst signal classes

**Date**: 2026-05-06 (evening, post-`v0.7.0-spec-007` tag)
**Status**: Pre-spec design exploration (Constitution VIII v1.4.0 forward-catalyst-class gate applies)
**Outcome**: enumerate Classes 2 + 4 + 5 + 6 + hybrids with priored discrimination + cost; recommend execution order; capture Spec 008 candidate criteria for future invocation.

This document is the "thinking BEFORE the next forward-catalyst spec" stage. Spec 007 (Class 3 LLM-extracted "case priced in" feature) ships at v0.7.0 with bull-side default-on at T=0.60 and bear-side shadow-mode-first per Constitution VIII v1.4.0. The forward-catalyst-mechanism design exploration (`claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md`) identified 6 candidate signal classes total; only Class 3 has been retrofitted + validated + shipped. **5 classes remain unexplored.** This doc enumerates them with updated priors after spec 007's empirical evidence.

---

## 1. Updated context after spec 007

What spec 007's Class 3 retrospectives validated:
- **Forward-catalyst mechanism class is tractable on this corpus** — discrim +14.43pp bull / +23.10pp bear, well above the +5pp Constitution VIII gate
- **Per-class mean separation matters** — bull cohort_a vs control_bull_winner gap = +0.097 was load-bearing; bear cohort_b vs control_bear_winner gap ≈ 0 was the load-bearing reason for shadow-mode-first
- **LLM choice (model capability) matters** — Haiku saturated the score distribution (std 0.071) and produced borderline verdict; Opus widened it (std 0.090) and unblocked decisive PASS
- **Per-side asymmetry is fundamental** — the forward-catalyst signal favors bull-side suppression more than bear-side (the bear cohort doesn't cluster at high bear_priced_in scores empirically)

What spec 007 did NOT validate:
- **Whether the bull-side cohort hit will hold on FRESH propagates** — the retrospective measures the in-sample Opus call on cached state logs; production Opus calls on new propagates may behave differently. Shadow-mode observation period (n≥20) is the natural validation but bear-side only.
- **Whether other LLM models (Sonnet, GPT-5.4) would produce comparable discrimination** — only Haiku + Opus tested.
- **Whether a hybrid signal (Class 3 + Class 2 options-IV combined) would catch MORE of the cohort** — single-class only tested.
- **Whether the bear-side shadow-mode period reveals it should be flipped to active** — calendar-bound; needs operator-driven activity.

---

## 2. Remaining forward-catalyst classes

### Class 2 — Options-implied volatility (HIGHEST priority candidate; **DATA-BLOCKED 2026-05-06 evening**)

**Mechanism**: At signal-generation time, fetch options chain via yfinance:
- IV percentile (current 30-day-IV vs trailing 1-year-IV distribution)
- IV term structure (front-month vs back-month)
- IV skew (put-IV vs call-IV)
- Put/call ratio
- Days to next IV crush (earnings-IV-collapse pattern)

**Updated prior** (post-spec-007): **HIGHER than the original design doc estimated** because:
- The original design doc gave Class 2 a 50-70% prior on bear-cohort discrimination specifically. Spec 007's bear-side gap = 0 means Class 3 alone CAN'T catch the bear cohort cleanly. Class 2's options-IV signal is the natural complement (options markets often pre-price expected upside even when prose doesn't reflect it).
- Cost was originally estimated at $0-5 retrofit (yfinance options data is free).

**🚫 BLOCKED — yfinance does NOT cache historical options chains** (verified 2026-05-06 evening; commit `ada8ebb`). The `yf.Ticker(...).options` attribute returns ONLY the current snapshot of expirations; `option_chain(expiration)` returns the current option chain for that expiration. There is no historical-by-trade-date lookup for `2026-04-03` or any other historical date in the cohort. The 45-commit cohort spans 2025-08 through 2026-04; none of those dates have cached options chains accessible via yfinance.

**Implications**:
- Class 2 retrofit as originally designed is **infeasible without a paid 3rd-party historical options data provider** (e.g., OptionMetrics, OPRA, Polygon.io). Out of scope per Constitution III T1/T2 cost gating.
- A LIVE Class 2 implementation (production filter that fetches the CURRENT options chain at signal-generation time) is still feasible — but cannot be retrospectively validated against the historical cohort, so Constitution VIII v1.4.0's pre-spec retrospective gate cannot be satisfied. Spec 008 invocation for Class 2 is **NOT permitted** without cohort-validation evidence.
- Possible workaround: **shadow-mode-first** for live Class 2 (collect annotations on n≥20 fresh propagates, evaluate after the holding window closes). This is the slow path; it doesn't unblock spec writing today.

**Spec 008 fit candidate**: ~~VERY STRONG~~ → **DEFERRED until historical options data is available** OR shadow-mode-first observation period yields enough fresh data (~21+ trading days minimum to score realized α on n≥20 fresh propagates).

**Substitute path forward (not Spec 008)**: Hybrid C (Class 3 × Class 6 calendar) is the cheapest retrofit-feasible alternative — both Class 3 + Class 6 data are historically available; Hybrid C combines them into a calendar-aware enhancement of the validated Class 3 filter without requiring options data.

### Class 4 — Cross-asset / regime signals

**Mechanism**: At signal-generation time, fetch:
- 10-year treasury yield (^TNX) + delta vs trailing N days
- Dollar index (DXY) + delta
- VIX + percentile vs trailing year
- Sector rotation strength (already in `tradingagents/dataflows/macro.py::get_sector_etf_strength`)

**Updated prior** (post-spec-007): **LOWER than the original design doc estimated**. Spec 007's bull cohort is 88.9% Tech-concentrated; macro features (yields/dollar/VIX) are by construction shared across all tickers in the same propagate batch + don't discriminate per-ticker. The "macro regime" framing is intuitive but doesn't help with the per-ticker cohort discrimination problem the failure-mode taxonomy actually presents.

**Spec 008 fit candidate**: WEAK. Better as a feature to combine with Class 3 (multiplier on the LLM score) than as a standalone filter.

**Implementation cost**: ~3h to wire featurizers; $0 (data already in `dataflows/macro.py`).

**Pre-spec retrospective gate prediction**: probably FAIL discrim ≥ +5pp criterion because per-ticker discrimination is weak. Skip building the spec; consider only as a Class 3 hybrid input.

### Class 5 — Fundamentals delta

**Mechanism**: At signal-generation time:
- Recent earnings surprise (last 4 quarters, beat/miss magnitude)
- Recent guidance revision (analyst estimate revisions in past 30 days)
- Days to next earnings (single most predictive event-based feature)
- Recent insider transactions (already wired in `get_insider_transactions`)

**Updated prior** (post-spec-007): **MODERATE** — per the original design doc 40-60% on Cohort B. Spec 007 catches +14pp of bull-side; Class 5's days-to-earnings + recent surprise features are orthogonal to Class 3's prose synthesis (Class 3 reads the analyst summaries; Class 5 reads the structured data the analysts referenced).

**Spec 008 fit candidate**: MODERATE. Cleanest single feature is days-to-earnings; could be combined with Class 2 (earnings drives options-IV; combined feature might be stronger than either alone).

**Implementation cost**: ~4h to wire featurizers + handle stale data; $5-10 if alpha_vantage queries needed for some features.

**Pre-spec retrospective gate prediction**: probably PASS criterion 1 (discrim) on the bear cohort (where forward earnings catalysts dominate); possibly fail criterion 2 on the bull cohort. Worth retrofitting if Class 2 retrofit doesn't cover the bear gap fully.

### Class 1 — News-density (Exa retrofit)

**Mechanism**: At signal-generation time, query Exa for recent news on the ticker. Featurize:
- Snippet count (volume of attention)
- Bull/bear keyword density in headlines + summaries
- Days-since-most-recent-news
- Time-to-known-upcoming-event via cached calendar

**Updated prior** (post-spec-007): **LOWER than the original design doc estimated** (was 30-50% for both cohorts). Spec 007's Class 3 already synthesizes the news report into the bull/bear-priced-in scores; Class 1's news-density features are a strict subset of Class 3's input space. Adding Class 1 as a separate filter would likely produce correlated discrimination (catch the same cohort Class 3 catches) without adding meaningful coverage.

**Spec 008 fit candidate**: WEAK as standalone; potential as audit signal. Consider Class 1 features as INPUT to a Class 3 LLM prompt (already implicitly there) rather than as a separate filter.

**Implementation cost**: ~3h to wire featurizers; $0-5 (Exa already wired).

**Pre-spec retrospective gate prediction**: probably PASS criterion 1 on cohort discrimination but with high correlation to Class 3. Spec invocation NOT JUSTIFIED unless Class 3 is somehow disabled for cost reasons + Class 1 serves as a cheap fallback.

### Class 6 — Calendar features (proximity to known catalysts)

**Mechanism**: At signal-generation time:
- Days to next earnings (this ticker)
- Days to next earnings (close peers — sector co-movers)
- Days to next Fed meeting (or other macro event)
- Days to next OpEx (option expiration)
- Quarter-end / month-end proximity

**Updated prior** (post-spec-007): **WEAK as standalone, STRONG as combinatorial input**. Days-to-earnings is the cleanest single feature in this class; could be a SCALE FACTOR on Class 3's score (e.g., bull_case_priced_in × (1 - days_to_earnings_norm) — ticker close to earnings should weight the priced-in score more heavily because the catalyst is imminent).

**Spec 008 fit candidate**: WEAK as standalone filter; STRONG as combinatorial input to a Class 3 + Class 2 hybrid.

**Implementation cost**: ~2h to wire featurizers; $0.

---

## 3. Hybrid combinations

The strongest single-class candidate is **Class 2 (options-IV)**. The strongest pairings:

### Hybrid A — Class 3 (current) + Class 2 (options-IV)

**Rationale**: Class 3 catches bull cohort cleanly; Class 2 should catch bear cohort better (options markets often pre-price expected upside via IV term structure / skew). Combined fire decision: bull side fires when Class 3's bull_priced_in > 0.60 OR Class 2's IV-percentile-implied-priced-in > some threshold; bear side fires when Class 3's bear_priced_in > 0.50 OR Class 2's bear-side options signal fires.

**Cost**: Class 3 baseline (~$0.025/propagate) + Class 2 yfinance fetches (~free; ~1s latency). Total per-propagate cost ≤ $0.025.

**Implementation cost**: ~5h after Class 2 retrofit + ~3h to wire combined fire decision in the production filter.

**Likely outcome**: bull-side coverage stays at 88.9% (Class 3 dominates); bear-side coverage may rise from current 72.2% (shadow-mode) toward 85-95% if Class 2 catches the cohort the LLM doesn't.

### Hybrid B — Class 3 + Class 5 (fundamentals delta)

**Rationale**: Class 5's days-to-earnings is a forward-looking event marker that can SCALE the LLM-extracted score. Tickers close to earnings get a boost on the priced-in score because the catalyst is imminent and consensus is more likely to be wrong.

**Cost**: Class 3 baseline + Class 5 yfinance/alpha_vantage fetches (~$0-5/100 propagates).

**Implementation cost**: ~6h after Class 5 retrofit + ~3h hybrid wiring.

**Likely outcome**: marginal improvement on both cohorts; primary value is in catching the "earnings-week reversal" pattern that Class 3 alone may underweight.

### Hybrid C — Class 3 + Class 6 (calendar) as multiplier

**Rationale**: Days-to-earnings as a scale factor on the priced-in score. Cheapest hybrid; pure metadata.

**Cost**: Class 3 baseline + zero (calendar data is free).

**Implementation cost**: ~2h hybrid wiring.

**Likely outcome**: small but positive — boosts Class 3's discrimination near earnings dates without changing baseline behavior elsewhere.

---

## 4. Recommended execution order

Per Constitution VIII v1.4.0 forward-catalyst-class validation gate + cost-asymmetry discipline:

### Spec 008 candidate (NEXT) — Class 2 retrofit + spec ~~RECOMMENDED~~ → **DATA-BLOCKED; PIVOT TO HYBRID C** (2026-05-06 evening)

~~1. **Build `scripts/forward_catalyst_class2_retrospective.py`** — load 45-commit cohort + 50 controls; fetch options chain via yfinance for each (ticker, trade_date); compute IV percentile / term structure / skew / put-call; sweep thresholds; evaluate against Constitution VIII v1.4.0 gate.~~
~~2. **Cost**: ~$0-5 yfinance fetch (caching may be partial); ~5h script.~~

**Outcome of attempted Class 2 retrofit (2026-05-06 evening)**: yfinance probe confirmed options data is CURRENT-SNAPSHOT-ONLY; no historical lookups for 2025-08 through 2026-04 cohort dates. Retrofit-feasibility blocked. See "Class 2 — DATA-BLOCKED" section above for details.

### Spec 008 candidate (revised) — Hybrid C (Class 3 × Class 6 calendar boost)

The cheapest retrofit-feasible path forward — both Class 3 (LLM-extracted, already validated + shipped) + Class 6 (calendar features: days-to-earnings, days-to-Fed, OpEx) data ARE historically available via yfinance + cached calendar.

1. **Build `scripts/forward_catalyst_hybrid_c_retrospective.py`** — load the 94-commit Class 3 retrospective CSV (forward-catalyst-class3-opus-retrospective-2026-05-06.csv); for each row, compute days-to-next-earnings (from `yf.Ticker(t).earnings_dates`); apply calendar boost: `effective_score = bull_case_priced_in × (1 + boost)` where `boost = max(0, 1 - days_to_earnings / 14)` so tickers within 14 days of earnings get up to 2× weighting; sweep boost-curve params; evaluate against Constitution VIII v1.4.0 gate (delta vs Class 3 alone).
2. **Cost**: ~$0 (reuses cached Class 3 scores + free yfinance earnings calendar); ~3h script.
3. **Decision tree**:
   - If Hybrid C improves bull-side discrimination AND/OR bear-side cohort hit rate vs Class 3 alone → write Spec 008 as the calendar-aware enhancement
   - If Hybrid C is no better than Class 3 alone → SKIP spec; document the negative finding; calendar features are too crude to discriminate
   - If Hybrid C is WORSE than Class 3 (calendar boost over-weights bad commits near earnings) → SKIP + document

**Why this is the right substitute**:
- Tests an empirically-grounded hypothesis (forward catalysts within 14 trading days are more "priced in" than distant catalysts)
- Zero new LLM cost (reuses cached Class 3 scores)
- Zero data-availability risk (earnings_dates IS in yfinance historical)
- Quick decision (~3h not ~5h)

### Spec 009 candidate (FUTURE) — Class 5 (fundamentals delta) standalone OR Hybrid B

### Spec 009 candidate (FUTURE) — Hybrid A (Class 3 + Class 2)

If Spec 008 (Class 2) passes only the bear-side gate, Spec 009 would be Hybrid A: combine Class 3's bull-side cleanness with Class 2's bear-side coverage into a single filter with side-specific signal sources. Lower implementation cost than two separate filters; cleaner operational story (one filter, two signal sources per side).

Per Constitution VIII v1.4.0: Hybrid A's pre-spec retrospective would need to show net Δα improvement over the BETTER of Class 3 alone or Class 2 alone (otherwise the simpler single-class filter dominates).

### Spec 010 candidate (FUTURE) — Class 5 (fundamentals delta) standalone OR Hybrid B

Days-to-earnings + recent earnings surprise. Standalone Class 5 may have weaker discrimination than Class 3 + Class 2; Hybrid B (Class 3 × Class 5 calendar boost) may have stronger coverage at marginal cost.

---

## 5. What's NOT recommended for spec invocation

Per the priored estimates above:

- **Class 4 (cross-asset / regime)** — fails per-ticker discrimination criterion by construction (macro features are batch-level, not ticker-level). Useful as audit context, NOT as a filter.
- **Class 1 (news-density)** — strict subset of Class 3's input space; would catch correlated cohort. Spec invocation not justified unless Class 3 is disabled for cost reasons.
- **Class 6 (calendar) as standalone** — too weak by itself. Useful as multiplier on Class 3's score (Hybrid C); not as a separate filter.

---

## 6. Constitution VIII v1.4.0 application

Each candidate spec follows the Constitution VIII v1.4.0 forward-catalyst-class validation gate:

1. **Discrimination ≥ +5pp in correct direction (PRIMARY)** — among suppressed cohort, suppressed-cohort α magnitude must exceed suppressed-non-cohort α magnitude by ≥ 5pp
2. **Cohort hit rate ≥ 60%** when target cohort named
3. **Net Δα ≥ +0.5pp at proposed default** OR shadow-mode-first if (3) is unmeasurable on small retrospective corpus

The pre-spec retrospective methodology is now battle-tested across 5 mechanism classes (4 backward-price + 1 forward-catalyst); cost asymmetry validated at ~$0-2 + 30min retrospective vs ~6-8h spec+impl+tests per class. Each new spec invocation should follow the same workflow.

---

## 7. Operational outcome

**Spec 008 (Class 2 options-IV retrofit + spec) is the recommended next forward-catalyst work unit.** Estimated cost: ~$0-5 + ~10h total (5h retrospective + 5h spec + impl if it passes the gate). Highest-info-value because it directly addresses the gap Class 3 left (bear-side cohort not separable on prose features).

If Spec 008 retrospective fails both gates, **fall back to Hybrid A or Hybrid C exploration** — combining Class 3 with another signal class may provide marginal coverage improvements at lower implementation cost than another standalone spec.

If multi-window SC-003 replication completes (calendar-bound; T2-T3 cost), the corpus expands from 234 → 290+ commits and spec 005 candidate's per-ticker percentile variant becomes viable. That's a separate work track from forward-catalyst exploration.

---

## 8. Reading list

- `claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md` — original 6-class enumeration + Class 3 recommendation
- `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` — empirical PASS evidence for Class 3 (justifies Spec 007)
- `specs/006-forward-catalyst-gate/` — Spec 007 (Class 3 production implementation)
- `.specify/memory/constitution.md` Principle VIII (v1.4.0) — forward-catalyst-class validation gate
- `claudedocs/sector-alpha-attribution-2026-05-06.md` — cohort source (27 ticker_weak-bull + 18 ticker_strong-bear + 49 controls)
- `tradingagents/dataflows/y_finance.py::get_options_summary` — Class 2 data hook (already wired)
- `tradingagents/dataflows/macro.py` — Class 4 data hooks (already wired)
- `tradingagents/dataflows/y_finance.py::get_earnings_calendar` — Class 5 + Class 6 data hook (already wired)

---

## Status: design-doc complete; Spec 008 candidate identified

This document captures the design exploration of remaining forward-catalyst signal classes. **No code changes; no spec invoked.** Future work to convert this into Spec 008 follows the proposed validation methodology:

1. Build `scripts/forward_catalyst_class2_retrospective.py` (Class 2 options-IV)
2. Run + commit retrospective markdown
3. If passes Constitution VIII v1.4.0 gate → invoke `/speckit.specify` with this design doc + the Class 2 retrospective as input
4. If fails → document negative finding + consider Hybrid A (Class 3 + Class 2 combined)

Captured for future invocation; not blocking any current work.
