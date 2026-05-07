# Class C-4 (institutional ownership) feasibility probe — VERDICT: PARTIAL

**Goal**: De-risk eventual ~3h Class C-4 (institutional ownership delta)
forward-catalyst-class retrospective by verifying yfinance can return
the data needed.

**Probe script**: `scripts/probe_institutional_ownership.py` (18 tickers)
**yfinance version**: 1.3.0

## Verdict — PARTIAL FEASIBILITY (similar to C-2 but for different reason)

C-4 is **partially feasible** in a different way than C-2:

- **Feasible for SC-009 retrospective specifically** (cohort dates after
  the most recent 13F filing was filed but before the next one would
  be due): yfinance returns the same Q4 2025 snapshot that was
  knowable at SC-009 propagate time
- **Time-staleness alignment is critical**: 13F filings happen quarterly
  with 45-day lag. Currently today (2026-05-07) and the SC-009 cohort
  dates (2026-04-17 / 04-24) BOTH have Q4 2025 (ending 2025-12-31) as
  the most recent filed data. Q1 2026 13Fs aren't due until ~2026-05-15
- **NOT feasible for older cohorts** where 13F state at cohort time
  was different from today's snapshot

## Per-ticker results

16 of 16 single-stock tickers return populated `institutional_holders`
DataFrames. ETFs (SPY, XLF) return empty — graceful degradation matches
C-3 + C-5 + C-2 patterns.

`institutional_holders` returns 10-row × 6-column DataFrame:

| Column | Type | Example (NVDA top holder) |
|---|---|---|
| Date Reported | datetime | 2025-12-31 |
| Holder | str | "Vanguard Group Inc" |
| pctHeld | float | 0.0933 (9.33%) |
| Shares | int | 2,266,683,275 |
| Value | float | $479,403,512,662 |
| **pctChange** | **float** | **0.0194 (+1.94% pctHeld delta vs prior quarter)** |

**Critical**: the `pctChange` column gives the per-holder pctHeld delta
from prior 13F → current 13F. This is exactly the "rotation" signal
C-4 mechanism hypothesis needs — already computed by yfinance.

`Ticker.info` also exposes:
- `heldPercentInsiders` (e.g., NVDA 4.21%)
- `heldPercentInstitutions` (e.g., NVDA 68.15%)

`major_holders` returns DataFrame shape (4, 1) — summary breakdown.

## Why C-4 differs from C-2 / C-3 / C-5 — quarterly cadence + 45d lag

| Class | Snapshot cadence | Lag | Backfill viability |
|---|---|---|---|
| C-3 (analyst PT delta) | continuous | none | NOT FEASIBLE (no historical) |
| C-2 (short-interest delta) | bi-monthly FINRA | days | feasible <30d cohort window |
| **C-4 (institutional ownership)** | **quarterly 13F** | **~45 days** | **feasible WITHIN current 13F-filing window** |
| C-5 (earnings price reaction) | quarterly + cumulative | days | feasible for ANY backfill (4-25 quarters) |

C-4's PARTIAL feasibility is a **calendar artifact**, not a data
limitation: as long as today's 13F-filing-state matches the
13F-filing-state at cohort propagate time, the retrospective works.
This is true for SC-009 right now but won't be true ~2026-05-15+ when
Q1 2026 13Fs start landing.

**Critical caveat**: this analysis must run BEFORE Q1 2026 13F filings
land, otherwise today's snapshot will reflect Q1 2026 data while the
cohort propagate state was Q4 2025. C-4 retrospective on SC-009 is
**time-bounded**: feasible until ~2026-05-15.

## What C-4 retrospective needs vs available

| Need | SC-009 (Apr 2026 cohort) | Older cohorts |
|---|---|---|
| Per-ticker top institutional holders | YES (10 per ticker) | YES |
| Per-holder pctChange (rotation signal) | YES (column already in DataFrame) | NO |
| Time-aligned to backtest cohort dates | YES (Q4 2025 13F state matches both) | NO (state has refreshed) |
| Coverage breadth | YES (16/16 single stocks) | YES |
| Historical depth ≥ 6 months | NO (only 1 prior quarter, via pctChange delta) | NO |

## C-4 retrospective design (drafting-eligible for SC-009)

If we run a C-4 retrospective on SC-009 specifically (within the
~2026-05-15 deadline):

**Mechanism class hypothesis**: when top institutional holders are
ROTATING IN to a ticker (sum of positive pctChange across top 10
holders), smart-money accumulation is establishing a bull thesis.
Subsequent BULLISH commits become contrarian-priced-in (the bull case
is already absorbed by sophisticated participants).

Inverse: rotation OUT (sum of negative pctChange) suggests bear thesis;
BEARISH commits become contrarian.

**Retrospective approach**:
1. For each SC-009 cohort row, fetch institutional_holders at cohort
   time (= today's snapshot, since Q1 2026 13Fs not yet filed)
2. Compute `top10_net_rotation_pct = sum of pctChange across top 10
   institutional holders`
3. Apply candidate filter: suppress bullish commits when net rotation
   > +T_inflow, or suppress bearish commits when net rotation < -T_outflow
4. Score against discrim ≥ +5pp / hit rate ≥ 60% / net Δα ≥ +0.5pp
5. Run additive overlap analysis vs Spec 007 + Spec 008

**Time-window discipline**: must run before ~2026-05-15. After that
date, today's snapshot will diverge from cohort-propagate state and
the retrospective becomes non-replayable.

## Bear-side mechanism class verdicts updated

| Class | Verdict | Source |
|---|---|---|
| C-1 (insider transactions) | SKIP | PR #23 |
| C-2 (short-interest delta) | PARTIAL — feasible <30d | PR #65 |
| C-3 (analyst PT delta) | NOT FEASIBLE | PR #40 |
| **C-4 (institutional ownership)** | **PARTIAL — feasible until 2026-05-15** | **this PR** |
| C-5 (earnings price reaction) | FEASIBLE | PR #64 |
| C-6 (bear-news density) | DEFERRED | not yet probed |

**4 of 6 mechanism classes now probed**: 1 SKIP / 1 NOT FEASIBLE / 2
PARTIAL / 1 FEASIBLE / 1 DEFERRED.

## Followups

1. **Probe C-6 (bear-news density)** to complete the 6-of-6 sweep:
   would need to identify the data source first (Exa news? Brave news?
   Spec 007's existing news_data input?). ~30min, $0.
2. **C-4 retrospective on SC-009** within the 2026-05-15 time-window:
   ~2-3h, $0. Could produce a bear-side filter candidate.
3. **Path C snapshot wiring** (deferred; same followup as PR #40 + #65)
   would unlock generalized C-2 + C-4 retrospectives by accumulating
   snapshots forward.

## Sibling docs

- `claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.md`
  — C-1 SKIP
- `claudedocs/class-c2-short-interest-feasibility-2026-05-07.md`
  — C-2 PARTIAL (PR #65)
- `claudedocs/class-c3-analyst-pt-feasibility-2026-05-07.md`
  — C-3 NOT FEASIBLE (PR #40)
- `claudedocs/class-c5-earnings-feasibility-2026-05-07.md`
  — C-5 FEASIBLE (PR #64)
- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md`
  — bear-side design doc (PR #22)
