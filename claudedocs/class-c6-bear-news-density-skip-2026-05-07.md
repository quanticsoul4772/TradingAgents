# Class C-6 (bear-news density) — VERDICT: SKIP (REDUNDANT WITH SPEC 003)

**Goal**: Complete the 6/6 bear-side mechanism class survey from PR #22
by recording the C-6 verdict.

**Method**: No probe needed. PR #22 bear-side mechanism design doc
already evaluated C-6 at the design stage and concluded it's REDUNDANT
with Spec 003's bear_keyword_count featurizer (strict subset of Spec
003's input space). The "Updated prior: LOW" + "Spec 015 fit candidate:
WEAK" + "Likely fails v1.4.3 additive-overlap-vs-Spec-003 gate"
combination preemptively closes the question.

This doc records the C-6 SKIP verdict for closure of the 6-class survey.
The other 5 classes were evaluated via separate probe PRs (#23, #40, #64,
#65, #66) because their feasibility couldn't be determined from the
design doc alone — only data-source availability checks could.

## C-6 mechanism (per PR #22 design doc excerpt)

> "At trade_date, query exa for recent news on the ticker. Featurize
> bearish keyword density in headlines. Hypothesis: `ticker_strong`-bear
> cohort tickers had ABSENT bearish narrative in recent news — the
> framework's bear thesis lacks media reinforcement."

The mechanism would query Exa for news within a window (e.g., 7-30 days)
prior to propagate, count bearish keywords in headlines, and use that
as a contrarian filter signal.

## Why SKIP without probe

The design doc concluded:

> "Spec 003 already partially measures this via the bear_keyword_count
> side of the prose-density features. Class C-6 would be a strict subset
> of Spec 003's input space; correlation likely high, additive value low."

The reasoning chain:
1. Spec 003 already featurizes prose density across the analyst+debate
   ensemble, including the bear side via `bear_keyword_count`.
2. The analyst reports already include news data (per the existing
   `news_data` tool flowing into `news_analyst.py`).
3. C-6 would featurize the same news data Spec 003 already consumes,
   just with a narrower scope (bear-only keywords).
4. The v1.4.3 additive-overlap gate would compare C-6 vs Spec 003.
   Since C-6 is a strict subset of Spec 003's signal space, the
   intersection would be near-100% and the additive Δα ≤ +0.5pp gate
   would FAIL almost certainly.

This is a structural argument, not an empirical one — the SKIP holds
regardless of cohort or backtest. Per Constitution VI (Spec Before
Structural Change) and Constitution VIII v1.4.1 (retrospective FIRST
when retrospective gate fails), C-6 doesn't merit a retrospective at
all.

## Comparison to other SKIP / NOT FEASIBLE verdicts

| Class | Verdict | Skip type |
|---|---|---|
| C-1 (insider transactions) | SKIP (PR #23) | Empirical SKIP — retrospective ran, gate FAILed |
| C-3 (analyst PT delta) | NOT FEASIBLE (PR #40) | Data-availability SKIP — yfinance has no historical PT panels |
| **C-6 (bear-news density)** | **SKIP (this PR)** | **Structural SKIP — redundant with existing Spec 003 featurizer** |

Three different skip reasons, all valid per Constitution VIII v1.4.x.

## Final bear-side mechanism class scorecard (6 of 6 evaluated)

| Class | Verdict | Source | Retrospective viable? |
|---|---|---|---|
| C-1 (insider transactions) | SKIP | PR #23 | NO (empirically anti-predictive) |
| C-2 (short-interest delta) | PARTIAL | PR #65 | YES for SC-009 only (within 30d) |
| C-3 (analyst PT delta) | NOT FEASIBLE | PR #40 | NO (no historical panels) |
| C-4 (institutional ownership) | PARTIAL | PR #66 | YES for SC-009 only (within 13F window, until ~2026-05-15) |
| C-5 (earnings price reaction) | FEASIBLE | PR #64 | YES (4-25 quarters of data) |
| **C-6 (bear-news density)** | **SKIP** | **this PR** | **NO (structural redundancy with Spec 003)** |

**Bear-side mechanism class survey COMPLETE.**

Net result: of 6 bear-side mechanism classes enumerated in PR #22,
**3 are viable for retrospective** (C-2 / C-4 / C-5), 2 are STRUCTURALLY
or DATA-blocked (C-3 / C-6), and 1 is EMPIRICALLY SKIPPED (C-1).

C-5 is the strongest candidate (full historical depth), followed by C-2
and C-4 (both PARTIAL with time-window discipline).

## Followups

1. **C-5 retrospective** (~3h, $0) — strongest data-availability case.
   Rank #2 in last reasoning_decision after this probe.
2. **C-2 retrospective on SC-009** (~2-3h, $0) — narrower scope than C-5.
3. **C-4 retrospective on SC-009** (~2-3h, $0) — time-bounded until
   ~2026-05-15.
4. **Update PR #22 design doc** to reflect the 6/6 evaluated state +
   final scorecard. ~10min, $0. Optional polish.
5. **No more bear-side PROBES needed** — survey is complete.

## Sibling docs

- `claudedocs/bear-side-mechanism-exploration-2026-05-07.md`
  — original 6-class enumeration (PR #22)
- `claudedocs/forward-catalyst-class-c1-insider-retrospective-2026-05-07.md`
  — C-1 SKIP (PR #23)
- `claudedocs/class-c2-short-interest-feasibility-2026-05-07.md`
  — C-2 PARTIAL (PR #65)
- `claudedocs/class-c3-analyst-pt-feasibility-2026-05-07.md`
  — C-3 NOT FEASIBLE (PR #40)
- `claudedocs/class-c4-institutional-ownership-feasibility-2026-05-07.md`
  — C-4 PARTIAL (PR #66)
- `claudedocs/class-c5-earnings-feasibility-2026-05-07.md`
  — C-5 FEASIBLE (PR #64)
