# SC-009 — all 13 bull-pre rows enumerated (closes PR #57 followup #1)

**Trigger**: PR #57 followup #1 — "Identify 4 unaccounted bull commits
between 23-row and 36-row marks." Resolved using state-log enumeration
across the full 36-row cohort.

## Full bull-pre roster (n=13)

| # | Ticker | Date | pre | post | bull_score | days_to_E | boost | effective_bull |
|---|---|---|---|---|---|---|---|---|
| 1 | NVDA | 2026-04-24 | Overweight | Hold | 0.82 | 26 | 0.000 | 0.820 |
| 2 | MA | 2026-04-17 | Overweight | Hold | 0.70 | 13 | 0.071 | 0.725 |
| 3 | MA | 2026-04-24 | Overweight | Hold | 0.72 | 6 | 0.571 | 0.926 |
| 4 | GOOGL | 2026-04-17 | Buy | Hold | 0.70 | 12 | 0.143 | 0.750 |
| 5 | GOOGL | 2026-04-24 | Overweight | Hold | 0.78 | 5 | 0.643 | 1.000 (clamp) |
| 6 | AMZN | 2026-04-17 | Overweight | Hold | 0.78 | 12 | 0.143 | 0.836 |
| 7 | BAC | 2026-04-17 | Overweight | Hold | 0.65 | 88 | 0.000 | 0.650 |
| 8 | BAC | 2026-04-24 | Overweight | Hold | 0.70 | 81 | 0.000 | 0.700 |
| 9 | GS | 2026-04-17 | Overweight | Hold | 0.65 | 88 | 0.000 | 0.650 |
| 10 | **GS** | **2026-04-24** | Overweight | Hold | 0.62 | 81 | 0.000 | 0.620 |
| 11 | **JPM** | **2026-04-17** | Overweight | Hold | 0.70 | 88 | 0.000 | 0.700 |
| 12 | **JPM** | **2026-04-24** | Overweight | Hold | 0.70 | 81 | 0.000 | 0.700 |
| 13 | **LLY** | **2026-04-17** | Overweight | Hold | 0.70 | 13 | 0.071 | 0.725 |

All 13 fired_bull = True. ALL 13 base bull_scores exceed T_bull = 0.60.

## The 4 new rows (PR #57 followup answered)

PR #57 enumerated 9 bull-pre rows from the 23-row mark. The 4 added in
the final 13 rows:

- **GS @ 2026-04-24** — second GS bull commit; same Financials pattern
  (81d to earnings, no boost)
- **JPM @ 2026-04-17** + **JPM @ 2026-04-24** — JPM joins BAC + GS as
  the third Financials bull-pre ticker
- **LLY @ 2026-04-17** — Healthcare megacap; 13d to earnings (boost
  engaged at 0.071)

## Strengthens PR #56 spec-007-calendar-independence finding

PR #56 documented 3 Financials cases (BAC×2 + GS-04-17) firing at 81-88d
to earnings with calendar_boost = 0. The 4 new rows expand this to **6
Financials cases**: BAC×2 + GS×2 + JPM×2.

All 6 Financials bull-pre fires:
- Days to earnings: 81-88 (well outside the spec 008 14d boost window)
- calendar_boost = 0.000 on all 6
- bull_score range: [0.62, 0.70] — modestly above T_bull = 0.60
- effective_bull = base bull_score on all 6

The 6-case Financials pattern is now a robust empirical demonstration
that **spec 007 fires independently of calendar proximity**. The 3-case
PR #56 finding was on the early Financials sample; the 6-case full-cohort
finding is twice as strong.

## Sector breakdown (final 13 bull-pre fires)

| Sector | Tickers | Count | Notes |
|---|---|---|---|
| Tech megacap | NVDA, GOOGL×2, AMZN | 4 | mixed boost engagement |
| Payments | MA×2 | 2 | both within 14d window; boost engaged |
| Financials | BAC×2, GS×2, JPM×2 | **6** | ALL at 81-88d (no boost) |
| Healthcare | LLY | 1 | within 14d window; small boost |

**The Financials sector is the structural exception** to the
boost-engagement-at-earnings pattern. Two reasons it's interesting:
- Financials have less concentrated earnings catalysts than Tech (no
  hyperscaler-driven AI guide-up dynamics)
- Bull_score 0.62-0.70 cluster suggests the LLM-extracted bull-priced-in
  signal triggers on Financials at moderate-strength evidence rather
  than the 0.78-0.88 intensity seen on Tech megacaps

## Implications for the SC-009 verdict (still PRELIMINARY)

The 13-fire / 100% fire rate / 0 decisions changed by boost finding from
PR #57 + #58 + #60 holds at this enumeration. PR #56 PASS-by-non-
counterexample framing remains the right verdict-refinement.

Adding 6 Financials cases (vs 3 in PR #56) makes the cohort-distribution-
mismatch argument even stronger: the SC-009 cohort's bull_score distribution
clusters in the [0.62, 0.85] range, while spec 008 boost was designed
for the borderline [0.55, 0.65] range. The boost mechanism is structurally
unexercised by this cohort regardless of whether you slice by sector or
date.

## Sibling docs

- `claudedocs/spec-007-calendar-independence-bac-gs-2026-05-07-late.md` — PR #56 (3 Financials cases)
- `claudedocs/sc-009-backtest-complete-final-state-2026-05-07-night.md` — PR #57 (followup #1 source)
- `claudedocs/sc-009-27-row-mark-and-sweep-refresh-2026-05-07-late.md` — PR #53 (9-row enumeration)
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/ANALYSIS.md` — current PRELIMINARY hand-edit
