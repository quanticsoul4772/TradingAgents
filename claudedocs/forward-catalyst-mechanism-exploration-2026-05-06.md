# Forward-catalyst-aware mechanism — design exploration (not yet a spec)

**Date**: 2026-05-06
**Status**: Pre-spec design exploration (Principle VIII permits — different filter class)
**Outcome**: identify candidate signals, propose validation methodology, recommend most tractable starting point, capture deferred work for the future spec invocation.

This document is the "thinking BEFORE `/speckit.specify`" stage for a forward-catalyst-aware filter mechanism. Three same-day retrospective failures (`spec 004`, `spec 006`, `spec 005-candidate`) established that backward-price-only filters cannot catch the cohorts whose realized α comes from forward catalysts. **Constitution Principle VIII grandfathered the three implementations as default-off operator-opt-in but explicitly preserved the gap.** This design doc explores how to fill it.

---

## 1. The cohorts a forward-catalyst filter would need to catch

Two cohorts surfaced by today's sector-α attribution analysis (`claudedocs/sector-alpha-attribution-2026-05-06.md`):

### Cohort A — bullish `ticker_weak` (5th failure mode)

| Metric | Value |
|---|---|
| Size | 27 of 79 bullish commits (34.2%) |
| Realized α-vs-SPY | mean = -5.34% over 21 trading days |
| Realized α-vs-sector | mean = -5.80% (also lost vs own sector) |
| Sector concentration | 88.9% Technology (24/27); 22.2% Financials (2/9 cohort entries from XLF universe) |
| Worst outliers | AAPL 2026-03-27 (-3.43% vs SPY, -12.69% vs sector); MSFT 2026-03-11 (-9.14% vs SPY, -10.09% vs sector); NVDA 2025-08-22 (-2.81% vs SPY, -6.67% vs sector) |
| Mechanism (hypothesized) | Stock-specific weakness against a flat/rising sector — forward catalyst (earnings, guidance, news) drove the underperformance, not pre-trade-date sector rotation |

### Cohort B — bearish `ticker_strong` (bearish anti-calibration shock)

| Metric | Value |
|---|---|
| Size | 18 of 37 bearish commits (48.6%) |
| Realized α-vs-SPY | **mean = +28.02%** over 21 trading days |
| Realized α-vs-sector | mean = +25.33% (also rallied vs own sector) |
| Sector concentration | Likely Tech-dominated (full breakdown not yet generated; would mirror Cohort A) |
| Magnitude vs typical effect sizes | ~30× the typical rating-bucket effect size (~+1% for OW-vs-baseline). Largest single anti-calibration finding in the corpus. |
| Mechanism (hypothesized) | Counter-trend bear call on a ticker about to rally on positive catalyst (earnings beat, guidance raise, sector rotation INTO the ticker, etc.) |

### Combined cohort

- **45 commits total** (27 bullish ticker_weak + 18 bearish ticker_strong)
- **Mean |α-vs-SPY|** ≈ 14.9% (weighted: 27×5.34 + 18×28.02 / 45 ≈ 14.4)
- **Both cohorts share a common pattern**: realized α is dominated by post-trade-date catalysts the framework cannot see at signal-generation time
- **Both cohorts are uncatchable via the 5 current filters** (A3 / spec 003 / spec 003.5 / spec 004 / spec 006)

---

## 2. Why backward-looking price-only filters fail (validated 2026-05-06)

Today's three retrospective failures all exhibit the same signature:

1. **Mechanism is intuitive** — "ticker is at sector-relative high → mean-revert is incoming" (spec 005), or "sector ETF is in mean-reversion zone → sector-rotation losses" (spec 004), etc.
2. **Implementation is mechanical** — lookback fetch, threshold comparison, override
3. **Empirical retrospective fails** — either anti-predictive (spec 004 -0.45pp, spec 006 -0.71pp) or too noisy to support default-on (spec 005-candidate +0.31pp max)

**The deeper failure**: backward-looking price patterns cannot DISCRIMINATE cohort losers from similar-pattern winners. Spec 005 candidate retrospective demonstrated the math directly:

> At +3% threshold on the bullish corpus, the spec 005 candidate filter would fire on 22 commits. 13 are ticker_weak cohort losers (mean α = -5.33%, total = -69pp). The OTHER 9 fired commits are ticker_strong / sector_tide_up / sector_drag winners (mean α ≈ +9.9%, total ≈ +89pp). Filter cannot distinguish which subset to suppress; gains wash out.

**The forward catalyst is the discriminator.** A ticker at +12% relative-strength entering an earnings beat will continue rallying; a ticker at +12% relative-strength entering a guidance miss will reverse. Backward price alone cannot separate these.

---

## 3. Candidate forward-catalyst signal classes

Six mechanism classes worth considering, ranked by tractability + cost + likely discrimination power.

### Class 1 — News-density signals (Exa retrofit)

**Mechanism**: At signal-generation time, query Exa for recent news on the ticker. Featurize:
- Snippet count (volume of attention)
- Bull/bear keyword density in headlines + summaries
- Days-since-most-recent-news
- Time-to-known-upcoming-event (earnings, fed days, OpEx) via cached calendar

**Pros**:
- Exa is already wired (current default news vendor). No new vendor integration.
- The signal CHANGES per trade date in a way price doesn't — a ticker may have stable rel-strength but a sudden news spike.
- Zero LLM cost (just structured Exa query parsing).

**Cons**:
- Bull/bear keyword counts on news are likely to suffer the same Simpson's-paradox between-ticker artifact issue as `fundamentals_report bull_keyword_count` (per finding #4 mechanism investigation).
- Snippet count is a confounder — high-news tickers are not the same as high-news-event tickers.
- Time-to-earnings is the single cleanest sub-signal but is itself a known feature in equity research.

**Estimated retrofit cost**: ~$5 (already-cached Exa queries on the 45-commit cohort + ~50 control commits) + ~3h to wire featurizers into `tradingagents/signals/featurization.py`.

**Discrimination power (priored)**: 30-50%. Some news-density signal is likely real but weakened by the same artifact pattern as existing prose features.

### Class 2 — Options-implied-volatility signals

**Mechanism**: At signal-generation time, fetch options chain via yfinance:
- IV percentile (current 30-day-IV vs trailing 1-year-IV distribution)
- IV term structure (front-month vs back-month)
- IV skew (put-IV vs call-IV)
- Put/call ratio
- Days to next IV crush (earnings-IV-collapse pattern)

**Pros**:
- Options markets are forward-looking by construction. IV reflects the market's volatility EXPECTATION — high IV often precedes catalyst-driven moves.
- yfinance has options data (already used in `dataflows/y_finance.py`).
- Genuine new signal class — no existing filter touches options data.
- Likely high discrimination on Cohort B (the +28% rally cohort) — options markets often pre-price expected upside even when the bear analyst doesn't see it.

**Cons**:
- Options data is lower-quality on yfinance for less-liquid tickers (data gaps; stale prices).
- Historical options snapshots are not always available via yfinance — may have data-availability issues for the 45-commit retrospective corpus.
- More plumbing than news-density (need to fetch chains, compute features deterministically).
- IV percentile interpretation is non-trivial — high IV can mean "imminent catalyst" OR "just-finished catalyst" (post-earnings IV collapse).

**Estimated retrofit cost**: ~$0 if data is cached + ~5h to wire featurizers + handle missing-data fallback. Possibly $0-5 for any yfinance API calls.

**Discrimination power (priored)**: 50-70% specifically on Cohort B. Lower (30-50%) on Cohort A because Cohort A's losses are slower-bleed forward catalysts (guidance, share-loss) that options markets don't always pre-price as cleanly as they pre-price binary catalysts.

### Class 3 — LLM-extracted "bull case priced in" feature

**Mechanism**: Add a new analyst-stage call: an LLM (Haiku, ~$0.001/call) reads the existing 4 analyst reports + bull/bear debate + current price level, then emits a structured 0-1 score: **"how widely is the bull case already accepted by the market?"** Operationalized as 1 - "how much room does the bull thesis have to surprise."

**Pros**:
- Most novel — no existing filter or feature is structured this way.
- Genuinely synthesizes prose + price into a single discriminating feature.
- Can pick up consensus-vs-contrarian framing that price + options + news features miss individually.
- Cheap (Haiku per-call cost; ~$0.001 × 45 cohort + 50 control = $0.10 retrofit).
- Could ALSO catch Cohort B (bearish anti-calibration) by symmetry — "how widely is the bear case priced in?"

**Cons**:
- Adds an LLM call to the propagate pipeline (small cost but breaks the "filter is zero LLM cost" precedent of A3 / spec 003 / spec 004 / spec 006).
- LLM-extracted features have validation challenges (stochastic; how do we know the feature is calibrated?).
- The feature itself may suffer from the same anti-prediction Simpson's paradox as `bull_keyword_count` if not carefully prompted.
- Requires a new analyst-stage hook and corresponding state field.

**Estimated retrofit cost**: ~$0.10 LLM cost on the cohort + ~6h to wire (new analyst-stage hook + featurizer + state field + tests).

**Discrimination power (priored)**: 50-70% on BOTH cohorts. Has the highest ceiling because LLM can synthesize across all available evidence; has uncertainty because feature calibration is unproven.

### Class 4 — Cross-asset signals

**Mechanism**: At signal-generation time, fetch:
- 10-year treasury yield (`^TNX`)
- Dollar index (DXY)
- VIX (already cached via `tradingagents/dataflows/macro.py::get_vix`)
- Sector rotation strength (already in `get_sector_etf_strength`)

Featurize: rate-of-change, percentile vs trailing window, sign of recent move.

**Pros**:
- Captures macro regime shifts that single-stock + single-sector filters miss.
- All data already wired (`tradingagents/dataflows/macro.py`).
- Zero LLM cost.

**Cons**:
- Low discrimination on per-ticker basis — macro signals are by construction shared across all tickers in the same propagate batch.
- Cohort A (5th failure mode) is 88.9% Tech-concentrated but happens during periods that probably don't show distinctive macro features (otherwise the framework's existing analysts would see it).
- Cohort B (+28% rally) might show pre-rally yield-down / dollar-down patterns but n=18 is too small to robustly measure.

**Estimated retrofit cost**: ~$0 + ~3h to wire featurizers.

**Discrimination power (priored)**: 20-40%. Real signal exists at macro level but per-ticker discrimination is weak.

### Class 5 — Fundamentals delta (recent guidance revisions, EPS surprise history)

**Mechanism**: At signal-generation time:
- Recent earnings surprise (last 4 quarters, beat/miss magnitude)
- Recent guidance revision (analyst estimate revisions in past 30 days)
- Days to next earnings (single most predictive event-based feature)
- Recent insider transactions (already wired in `get_insider_transactions`)

**Pros**:
- These are EXPECTATIONS the market has already absorbed; deviations from them drive forward catalysts.
- yfinance + alpha_vantage have most of these.
- Days-to-earnings is the cleanest single feature in this class.

**Cons**:
- Many are LAGGING (last quarter's surprise doesn't predict next quarter's; analyst revisions can be stale).
- Days-to-earnings interacts with options-IV (Class 2) — should be combined, not treated independently.
- Insider transactions are noisy (many false signals from automated planned sells).

**Estimated retrofit cost**: ~$5 for any alpha_vantage queries on the cohort + ~4h to wire featurizers.

**Discrimination power (priored)**: 40-60% on Cohort B specifically (where forward earnings catalysts are concentrated); lower on Cohort A.

### Class 6 — Calendar features (proximity to known catalysts)

**Mechanism**: At signal-generation time:
- Days to next earnings (this ticker)
- Days to next earnings (close peers — sector co-movers)
- Days to next Fed meeting (or other macro event)
- Days to next OpEx (option expiration)
- Quarter-end / month-end proximity

**Pros**:
- Trivially computable from cached calendar data.
- Genuine forward-looking signal (which catalysts are imminent).
- Could be combined as a multiplier on other signal classes.

**Cons**:
- By itself, very weak discrimination — every commit is some-distance-from-some-catalyst.
- Probably best as a feature COMBINATION input rather than standalone signal.

**Estimated retrofit cost**: ~$0 + ~2h to wire featurizers.

**Discrimination power (priored)**: 20-40% standalone; 50-70% as a combinatorial input.

---

## 4. Recommended starting point

**Class 3 (LLM-extracted "bull case priced in" feature)** for the first pre-spec retrospective. Rationale:

1. **Highest ceiling on discrimination power** — LLM can synthesize across all the other classes' inputs in a single feature.
2. **Cheapest to retrofit** ($0.10 + ~6h vs $5+ + 5+h for the data-fetching alternatives).
3. **Most novel** — no existing literature or filter exists in this shape; would be a genuine project contribution if it works.
4. **Symmetric on bull + bear cohorts** — the same feature shape catches both Cohort A (bull case priced in → suppress Buy/OW) and Cohort B (bear case priced in → suppress UW/Sell), which means a single retrospective validates two cohorts.

If Class 3 succeeds (passes the validation methodology in §5 below), follow up with:
- **Class 2 (options-IV)** as the second retrospective — likely catches Cohort B specifically and would augment Class 3 on the bull side via earnings-IV-crush patterns.
- **Class 1 (news-density)** as the third — easiest to add but lowest-novelty.

If Class 3 fails (signal-to-noise too weak even for the LLM-extracted feature), the implication is severe: **the forward-catalyst-aware-mechanism class as a whole may not be tractable on the existing corpus**, and the 45-commit cohorts should be treated as Constitution VII calibrated-abstention candidates (i.e., the framework is correctly Hold-leaning on cohort dates and the cohort losses + gains are forward-only catalysts the framework rightly cannot see).

---

## 5. Validation methodology (proposed; would amend Principle VIII)

Constitution Principle VIII codified the gate for backward-price-only filters: **net Δα ≥ +1pp at proposed default + cohort hit rate ≥ 40%**. The same gate is too strict for forward-catalyst signals because:

- The 45-commit cohort is small for measuring α reliably with retrospective fires
- Forward-catalyst data may have availability gaps (options chains, news snippets) that limit retrospective corpus size
- LLM-extracted features have stochastic calibration — a single retrospective may not characterize the signal

**Proposed forward-catalyst gate** (extends Principle VIII):

1. **Discrimination criterion (PRIMARY for forward-catalyst)**: among the suppressed cohort, the suppressed-cohort α magnitude must exceed the suppressed-non-cohort α magnitude by ≥ 5pp. This is the gate spec 005 candidate FAILED on (suppressed-cohort -5.33% vs suppressed-non-cohort +9.9% → discrimination magnitude is -15pp WRONG SIGN). For forward-catalyst signals: the filter must catch genuine cohort losers and NOT catch genuine non-cohort winners. Discrimination ≥ 5pp in the right direction.

2. **Cohort hit rate ≥ 60%** (tightened from VIII's 40%). Forward-catalyst signals should be MORE specific than backward-price signals because they have more information.

3. **Net Δα ≥ +0.5pp** (loosened from VIII's +1pp). Smaller corpus + smaller discrimination is acceptable when the discrimination criterion (1) is strong.

**If a forward-catalyst retrospective passes 1 + 2 + 3** → spec is permitted. If only 1 + 2 pass (small-sample corpus where (3) is unmeasurable) → spec is permitted with a "shadow-mode for n=20+ propagates before active-mode flip" condition added to the spec.

If 1 fails → SKIP spec entirely (mirrors backward-price-only gate failure).

---

## 6. Implications for Constitution Principle VIII

If a forward-catalyst Class 3 retrospective passes the proposed gate (§5), Principle VIII should be amended to:

> **VIII (extended). Backward-looking price-derived filters require corpus retrospective showing net Δα ≥ +1pp + cohort hit rate ≥ 40%. Forward-catalyst-aware filters (signal class includes options-IV, news-density, LLM-extracted features, fundamentals delta, cross-asset) require: (1) discrimination magnitude ≥ 5pp in correct direction, (2) cohort hit rate ≥ 60%, (3) net Δα ≥ +0.5pp OR shadow-mode validation for n≥20 propagates. Both classes' retrospectives must commit BEFORE invoking `/speckit.specify`.**

This would be Constitution v1.4.0 (MINOR bump for amended principle).

If the Class 3 retrospective FAILS, the implication is broader: **Principle VIII grandfathering (spec 004 + spec 006 + A3) was correct BUT the gap remains structurally unfillable on the current corpus** — forward catalysts dominate the cohorts the framework cannot catch. Constitution VII (Calibrated Abstention) becomes the primary defense; the cohorts are accepted as honest research-substrate noise and the framework remains at the LLM single-call calibration ceiling for those failure modes.

---

## 7. Cost summary + decision tree

| Step | Cost | Outcome |
|---|---|---|
| Class 3 retrofit (LLM-extracted feature on 45-commit cohort + ~50 controls) | ~$0.10 + ~6h | Discrimination magnitude + cohort hit rate measured |
| Class 3 retrospective writeup | ~30 min | `claudedocs/forward-catalyst-class3-retrospective-<DATE>.md` |
| **If passes proposed gate** → invoke `/speckit.specify` for forward-catalyst spec | ~6-8h | Full spec → plan → tasks → impl cycle |
| **If fails proposed gate** → document the negative finding | ~30 min | Class 3 ruled out; consider Class 2 (options-IV, ~$0 + ~5h) as fallback retrospective |
| **If both Class 3 + Class 2 fail** → accept the gap | ~0 | Constitution VII acceptance; cohorts treated as calibrated-abstention candidates |

Total cost to definitively answer the "is forward-catalyst tractable on this corpus?" question: **$0.10-5 + ~12-20h work** across one or two retrospectives. Comparable to today's three backward-price retrospectives but with much higher ceiling on positive outcome.

---

## 8. Constitution VIII alignment

This design exploration is itself an instance of the discipline Principle VIII codifies: **think + retrospect BEFORE writing specs**. The exploration has identified:

- Six candidate signal classes with priored discrimination power + cost estimates
- One recommended starting point (Class 3) with explicit rationale
- A proposed validation methodology that extends Principle VIII for the new mechanism class
- A decision tree with explicit cost-bound stopping criteria

**Outcome**: this doc replaces the "spec 007 forward-catalyst gate" placeholder that would otherwise sit on the open-questions list as a ~6-8h cold start. Future invocation of `/speckit.specify` for any forward-catalyst filter has a clear "before you write the spec, run the Class 3 retrospective per §5" precondition.

The exploration cost was ~2h of design work + this doc; the work avoided was potentially 6-8h of spec writing followed by another retrospective failure. Same Pareto improvement as Principle VIII delivers for backward-price filters, applied at the design-doc layer instead of the spec layer.

---

## 9. Reading list

- `claudedocs/sector-alpha-attribution-2026-05-06.md` — the cohort-discovery analysis
- `claudedocs/sector-momentum-retrospective-2026-05-06.md` — spec 004 retrospective failure (same mechanism class)
- `claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md` — spec 006 retrospective failure
- `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md` — spec 005 candidate retrospective skip + discrimination-failure math
- `.specify/memory/constitution.md` Principle VIII — the codified lesson this design extends
- `RESEARCH_FINDINGS.md` "Filter portfolio status" + "5th failure mode" + "Bearish anti-calibration shock" sections — the empirical context this design responds to
- `tradingagents/dataflows/macro.py` — existing cross-asset + sector-ETF data hooks (Class 4)
- `tradingagents/dataflows/y_finance.py::get_options_summary` — existing options-IV hook (Class 2)
- `tradingagents/signals/featurization.py` — where new featurizers would land (all classes)

---

## Status: design-doc complete; next step deferred

This document captures the design exploration. **No code changes; no spec invoked.** Future work to convert this into an actual spec follows the proposed validation methodology (§5):

1. Build retrofit script for Class 3 (LLM-extracted feature) on the 45-commit cohort
2. Run + commit `claudedocs/forward-catalyst-class3-retrospective-<DATE>.md`
3. If passes proposed gate → invoke `/speckit.specify` with this design doc as input
4. If fails → document negative finding + consider Class 2 as alternative

Captured for future invocation; not blocking any current work.
