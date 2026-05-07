# Class C-2 (short-interest delta) feasibility probe — VERDICT: PARTIAL

**Goal**: De-risk eventual ~3h Class C-2 (short-interest delta)
forward-catalyst-class retrospective by verifying yfinance can return
the data needed.

**Probe script**: `scripts/probe_short_interest.py` (18 tickers)
**yfinance version**: 1.3.0

## Verdict — PARTIAL FEASIBILITY

C-2 is **partially feasible** — different from both C-3 (NOT-FEASIBLE)
and C-5 (FEASIBLE):

- **Feasible for SC-009 retrospective specifically** (cohort dates within
  ~30 days of probe time): yfinance returns 2 datapoints (current
  snapshot + 1 prior month) covering the cohort window
- **NOT feasible for older retrospective backfill** (SC-003 dates from
  several months ago, or any cohort > 30 days old): no historical
  panels available
- **Feasible for FORWARD use**: snapshot at each propagate, accumulate
  history (Path C pattern)

## Per-ticker results

16 of 16 single-stock tickers return short-interest data via
`Ticker(t).info` dict. ETFs (SPY, XLF) return empty — graceful
degradation matches C-3 + C-5 patterns.

Available fields per ticker (8 found on each of 16):

| Field | Example (NVDA) | Notes |
|---|---|---|
| sharesShort | 283,335,701 | Most recent FINRA report |
| sharesShortPriorMonth | 229,241,850 | One report prior |
| sharesShortPreviousMonthDate | 1,773,360,000 | Unix timestamp (~2026-03-11) |
| dateShortInterest | 1,776,211,200 | Unix timestamp (~2026-04-13) |
| shortRatio | 1.68 | Days-to-cover |
| shortPercentOfFloat | 0.0122 | 1.22% of float |
| floatShares | 23,321,682,000 | Total float |
| sharesPercentSharesOut | 0.0117 | 1.17% of shares outstanding |

The `dateShortInterest` + `sharesShortPriorMonth` pair gives us a
2-point time series (current + prior month) ALL referenced to the most
recent FINRA short-interest reporting cycle.

## What C-2 retrospective needs vs available

| Need | SC-009 only | Older cohorts |
|---|---|---|
| Per-ticker current short interest | YES (sharesShort) | YES |
| Per-ticker delta (current vs ~30d ago) | YES (computable) | NO (snapshot is FROZEN at probe time) |
| Time-aligned to backtest cohort dates | YES if cohort is within 30 days | NO |
| Coverage breadth | YES (16/16 single stocks) | YES |
| Historical depth ≥ 6 months | NO (only 2 data points per query) | NO |

## Why C-2 differs from C-3 and C-5

| Class | yfinance returns | Retrospective viability |
|---|---|---|
| C-3 (analyst PT delta) | CURRENT snapshot only | NOT FEASIBLE for any backfill |
| **C-2 (short-interest delta)** | **CURRENT + 1 prior month** | **FEASIBLE for cohorts within 30 days** |
| C-5 (earnings price reaction) | 4-25 quarters of historical data | FEASIBLE for any backfill |

C-2 sits in the middle — better than C-3 (we get a delta!) but worse
than C-5 (no deeper history). The 1-prior-month coverage is exactly
what's needed for SC-009 (cohort dates 2026-04-17 / 04-24, within the
30-day window from any probe taken in the next ~2 weeks).

## C-2 retrospective design (now drafting-eligible for SC-009)

If we run a C-2 retrospective on SC-009 specifically:

**Mechanism class hypothesis**: when a ticker's short interest has
SPIKED recently (delta > +X%), sophisticated short-side participants
are establishing a bear thesis. Subsequent BULLISH commits may be
contrarian-priced-out.

Inverse: when short interest has been COVERED (delta < -X%), bear
thesis is unwinding; subsequent BEARISH commits become contrarian.

**Retrospective approach**:
1. For each SC-009 cohort row, fetch current sharesShort + sharesShortPriorMonth
2. Compute `short_interest_delta_pct = (sharesShort - sharesShortPriorMonth) / sharesShortPriorMonth × 100`
3. Apply candidate filter: suppress bullish commits when delta > +T_short_spike,
   or suppress bearish commits when delta < -T_short_cover
4. Score against discrim ≥ +5pp / hit rate ≥ 60% / net Δα ≥ +0.5pp
5. Run additive overlap analysis vs Spec 007 + Spec 008

**Caveat**: results would be valid for SC-009 specifically; generalization
to other cohorts requires snapshot accumulation (Path C pattern, deferred).

## Bear-side mechanism class verdicts updated

| Class | Verdict | Source |
|---|---|---|
| C-1 (insider transactions) | SKIP | PR #23 |
| **C-2 (short-interest delta)** | **PARTIAL — feasible for SC-009** | **this PR** |
| C-3 (analyst PT delta) | NOT FEASIBLE | PR #40 |
| C-4 (institutional ownership) | DEFERRED | not yet probed |
| C-5 (earnings price reaction) | FEASIBLE | PR #64 |
| C-6 (bear-news density) | DEFERRED | not yet probed |

3 of 6 mechanism classes now probed. 1 SKIP / 1 NOT FEASIBLE / 1 PARTIAL
/ 1 FEASIBLE.

## Followups

1. **C-2 retrospective on SC-009 specifically** (~2-3h, $0): use the
   PARTIAL feasibility window to test the short-interest delta mechanism
   on the SC-009 cohort. Could produce a bear-side filter candidate.
2. **Probe C-4 (institutional ownership)** (~30min, $0): same de-risking
   pattern; complete the 4-of-6 probes.
3. **Probe C-6 (bear-news density)** (~30min, $0): would also need to
   identify the data source first (Exa for news? Brave?).
4. **Path C snapshot wiring** (deferred): would unlock C-2 (and C-3)
   forward-going retrospectives at zero LLM cost. Same followup as PR
   #40 noted.

## Sibling docs

- `claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.md`
  — C-1 SKIP
- `claudedocs/class-c3-analyst-pt-feasibility-2026-05-07.md` — C-3 NOT FEASIBLE
- `claudedocs/class-c5-earnings-feasibility-2026-05-07.md` — C-5 FEASIBLE (PR #64)
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md` — bear-side
  design doc (PR #22) enumerating 6 candidate classes
