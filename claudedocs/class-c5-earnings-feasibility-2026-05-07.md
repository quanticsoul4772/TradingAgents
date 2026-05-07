# Class C-5 (earnings price reaction) feasibility probe — VERDICT: FEASIBLE

**Goal**: De-risk eventual ~3h Class C-5 (earnings price reaction)
forward-catalyst-class retrospective by verifying yfinance can return
the data needed.

**Probe script**: `scripts/probe_earnings_history.py` (18 tickers across
4 sectors + 2 ETFs).

**yfinance version**: 1.3.0

## Verdict — UNLIKE C-3, this IS feasible

**C-5 retrospective IS RUNNABLE on $0 budget.** yfinance returns
historical, time-stamped earnings surprise data with sufficient depth
for retrospective backfill across the SC-009 cohort dates.

This is the OPPOSITE of the C-3 (analyst PT delta) verdict from PR #40
where the API returned only current snapshot with no historical panels.

## Per-ticker results

16 of 16 single-stock tickers return populated DataFrames. ETFs (SPY,
XLF) return empty — same graceful degradation pattern as C-3 probe.

**`earnings_history` API** returns DataFrame with shape `(4, 4)`:

| Column | Type | Example (INTC Q2 2025) |
|---|---|---|
| epsActual | float | -0.10 |
| epsEstimate | float | 0.00847 |
| epsDifference | float | -0.11 |
| surprisePercent | float | -12.81% |

Time-indexed by quarter end-date. 4 quarters of recent history per ticker
(2025-06-30 to 2026-03-31 in current data — covers Q3 2025 through
Q1 2026).

**`earnings_dates` API** returns DataFrame with shape `(25, 3)` — even
deeper:

| Column | Type |
|---|---|
| EPS Estimate | float |
| Reported EPS | float |
| Surprise(%) | float |

25 quarterly events ≈ ~6 years of coverage. This is the canonical source
for historical earnings surprise + announcement-date alignment.

## What C-5 retrospective would need vs what's available

| Need | Source | Available? |
|---|---|---|
| Per-ticker earnings dates | `earnings_dates` index | YES |
| Per-earnings EPS surprise | `surprisePercent` (history) or `Surprise(%)` (dates) | YES |
| Stock price reaction (1d / 5d forward) | `Ticker(t).history()` (already used elsewhere) | YES |
| Coverage breadth | 16/16 single stocks; ETFs gracefully empty | YES |
| Historical depth ≥ 6 months | 4-25 quarters available | YES |

**Conclusion**: C-5 retrospective design can proceed. Estimated cost
remains ~3h, $0 (yfinance free). No paid data source needed.

## Latency + cacheability

- Mean: 90ms per probe
- Max: 300ms (network outliers)
- LRU-cacheable per ticker (analogous to spec 008 calendar boost
  earnings_dates fetch — already proven pattern in production)

## Mechanism class for the eventual retrospective

**Class C-5 hypothesis** (per bear-side mechanism design doc PR #22):

When a stock has had a recent EARNINGS PRICE REACTION (1-5 day move
post-announcement) of large magnitude, that reaction itself signals
information already absorbed by the market. Subsequent commits in the
direction of the reaction are post-hoc; commits against it may be
contrarian-priced-in.

Two operationalizations to test in the retrospective:
1. **Reaction-magnitude filter**: at propagate time, look back to the
   most recent earnings event in `earnings_history`. If the
   announcement-day price move was ≥ T_reaction (e.g., ±5%), suppress
   commits in the direction of the reaction.
2. **Reaction-vs-surprise alignment filter**: combine surprise with
   reaction direction. Beat + UP move + bullish commit = post-hoc
   chasing. Miss + DOWN move + bearish commit = post-hoc chasing.

Either operationalization is testable retrospectively now that the data
is confirmed available.

## Comparison to prior bear-side mechanism class verdicts

| Class | Verdict | Reason |
|---|---|---|
| C-1 (insider transactions) | SKIP (PR #23) | Anti-predictive on cohort_b at T≥1; only 1/18 cohort hit |
| C-2 (short-interest delta) | DEFERRED | (not yet probed) |
| C-3 (analyst PT delta) | NOT FEASIBLE (PR #40) | yfinance has no historical PT panels |
| C-4 (institutional ownership) | DEFERRED | (not yet probed) |
| **C-5 (earnings price reaction)** | **FEASIBLE** (this PR) | **Historical earnings surprise + price reaction both accessible** |
| C-6 (bear-news density) | DEFERRED | (not yet probed) |

C-5 becomes the next bear-side mechanism class candidate to actually
run a retrospective on, since the data feasibility is now confirmed.

## Followups

1. **Run C-5 retrospective** — design + implement the actual
   retrospective script. ~3h, $0. Per Constitution VIII v1.4.0 + v1.4.3
   pattern, the retrospective should:
   - Compute earnings surprise + announcement-day price reaction for
     each cohort row's most recent prior earnings event
   - Apply candidate filters (reaction-magnitude, reaction-vs-surprise)
   - Score against discrim ≥ +5pp / hit rate ≥ 60% / net Δα ≥ +0.5pp
   - Run additive overlap analysis vs Spec 007 + Spec 008 (per v1.4.3)
   - Write verdict markdown
2. **Probe C-2 (short-interest delta)** — `Ticker(t).short_position`
   may not exist or may be limited; needs same de-risking probe pattern.
   ~30min, $0.
3. **Probe C-4 (institutional ownership)** — `Ticker(t).institutional_holders`
   exists; needs probe to determine quality + historical depth.
   ~30min, $0.

## Sibling docs

- `claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.md`
  — C-1 SKIP verdict
- `claudedocs/class-c3-analyst-pt-feasibility-2026-05-07.md` — C-3
  NOT-FEASIBLE verdict (PR #40)
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` — bear-side
  mechanism design doc (PR #22) enumerating 6 candidate classes
