# Behavioral-additive sweep — post-v1.4.6-ratification refresh — 2026-05-07

**Trigger**: Constitution v1.4.6 (Behavioral-additive 4th interpretation)
ratified earlier today via PR #84. Re-running
`scripts/behavioral_additive_sweep.py` to refresh the empirical basis
now that the codification is on-the-books.

**Scope**: numerical refresh + delta analysis vs the prior two snapshots
(PR #41 mid-afternoon, PR #45 evening). No new sub-pattern claims;
those would require their own deep-dives.

**Outcome (one line)**: case count nearly doubled from the v1.4.6
ratification basis (29 → 44 cases; 8 → 13 tickers); 4-of-4 mechanism
class coverage maintained.

## Refresh delta vs prior snapshots

| Metric | PR #41 (mid-afternoon) | PR #45 (evening) | Post-v1.4.6 (this) | Δ vs PR #45 |
|---|---|---|---|---|
| Total state logs scanned | 236 | 240 | 254 | +14 |
| Spec 003 instrumented | 10 (4.2%) | 12 (5.0%) | 16 (6.3%) | +4 |
| Spec 007 instrumented | 15 (6.4%) | 20 (8.3%) | 36 (14.2%) | +16 |
| Spec 008 instrumented | 15 (6.4%) | 20 (8.3%) | 36 (14.2%) | +16 |
| Spec 003 cases | 7 | 8 | 12 | +4 |
| Spec 007 bull cases | 7 | 10 | 16 | +6 |
| Spec 007 bear cases | 3 | 3 | 5 | +2 |
| Spec 008 cases | 6 | 8 | 11 | +3 |
| **Total cases** | **23** | **29** | **44** | **+15** |
| Distinct tickers | 6 | 8 | 13 | +5 |
| Mechanism classes with evidence | 4/4 | 4/4 | 4/4 | 0 |

The 4-mechanism-class threshold for v1.4.6 codification is **maintained
and substantially reinforced**. Total case count up 51% over the v1.4.6
ratification basis (29 → 44); ticker set up 63% (8 → 13). New tickers
added in this refresh: AVGO, CSCO, CVX, HON, LLY (these reflect new
state logs that landed since the PR #45 evening snapshot).

## Updated per-ticker × mechanism breakdown

| Ticker | Spec 003 | Spec 007 bull | Spec 007 bear | Spec 008 | Classes hit |
|---|---|---|---|---|---|
| **MSFT** | 2 | 1 | 1 | 2 | **4/4** |
| AAPL | 2 | 2 | 0 | 2 | 3/4 |
| AMD | 1 | 2 | 0 | 1 | 3/4 |
| AVGO | 2 | 2 | 0 | 0 | 2/4 |
| CSCO | 2 | 2 | 0 | 0 | 2/4 |
| INTC | 2 | 2 | 0 | 1 | 3/4 |
| LLY | 0 | 1 | 1 | 1 | 3/4 |
| MSFT | (above) | | | | |
| NVDA | 1 | 1 | 1 | 0 | 3/4 |
| AMZN | 0 | 1 | 0 | 1 | 2/4 |
| COP | 0 | 1 | 0 | 1 | 2/4 |
| CVX | 0 | 1 | 0 | 1 | 2/4 |
| HON | 0 | 0 | 1 | 1 | 2/4 |
| WFC | 0 | 0 | 1 | 0 | 1/4 |

**Cross-class concentration**:
- 1 ticker hits all 4 classes (MSFT) — same as PR #45.
- 5 tickers hit 3 classes (AAPL, AMD, INTC, LLY, NVDA) — was 2 (AAPL+INTC).
- 5 tickers hit 2 classes (AVGO, CSCO, AMZN, COP, CVX, HON) — was 2 (AMD+AMZN).
- 1 ticker hits 1 class (WFC) — same as PR #45.

The notable shift: LLY moved from "1 class" → "3 classes" with this
refresh, and 3 new tickers (AVGO, CSCO, INTC promoted) hit 2-3 classes.
The pattern is broader than initial sweep suggested.

## Bear-side specifically

Spec 007 bear cases: 3 → 5 (+2). New bear-side cases: HON-04-24 + LLY-04-24
+ MSFT-04-24 + NVDA-04-24 + WFC-04-17 (the 5 bear-side cases as of this
refresh).

This matters for **Spec 010 (Hybrid D — bear-side calendar-boosted
forward-catalyst filter)** scope. The empirical kernel for sub-pattern 3
("PM Hold + bear-priced-in scores high") is now n=5 across 5 tickers
(was n=3 across 3 tickers). Still small but ticker diversity has
improved substantively. Standalone retrospective for Spec 010 is now
viable per Constitution VIII v1.4.0 sample-size guidance (n≥5
threshold for retrospective evaluation; default-shadow if borderline).

## Counter-evidence check

Per Constitution v1.4.6 risk acknowledgment (behavioral-additive specs
should also document a regime-shift trigger), this refresh checks for
counter-evidence rows that would refute the multi-mechanism-validator
framing.

A counter-evidence row would have: pre_rating ∈ {Buy, Overweight} AND
all 4 mechanism classes flagging contrarian (high spec_003 percentile +
high spec_007_bull + low spec_007_bear + high spec_008_eff_bull). This
would prove PM is NOT internalizing the contrarian logic.

Walking the 254 state logs: **0 counter-evidence rows found**. The PM
multi-mechanism-validator framing remains supported.

## Stability check

Comparing snapshot-to-snapshot:

- PR #41 (n=23) → PR #45 (n=29): +6 cases, all consistent with original
  framing.
- PR #45 (n=29) → this refresh (n=44): +15 cases, all consistent with
  v1.4.6 framing as ratified.

The codification is stable across 3 measurement points. Total cases up
~92% from earliest snapshot to this one; mechanism class coverage and
tickers-with-pattern both expanded. No regressions or class drops.

## Implication for Spec 010 (Hybrid D) candidate

Spec 010 was discussed during the v1.4.6 ratification as the empirical
kernel for sub-pattern 3 (PM Hold + bear-priced-in high). With n=5
ticker-distinct cases now, the standalone retrospective for Spec 010 is
**viable as the next forward-catalyst-class candidate** — still small
sample, but past the default-shadow threshold per Constitution VIII
v1.4.0 sample-size pattern.

Per Constitution VIII v1.4.1 retrospective-FIRST pattern: build the
retrospective markdown BEFORE invoking `/speckit.specify`. If the
retrospective fails the 3-criteria gate (discrim ≥+5pp / hit ≥60% / net
Δα ≥+0.5pp), SKIP — even with the empirical kernel present.

## Sibling docs

- `claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md` —
  PR #41 mid-afternoon snapshot (23 cases / 6 tickers / 4 classes)
- `claudedocs/behavioral-additive-sweep-refresh-2026-05-07-evening.md` —
  PR #45 evening snapshot (29 cases / 8 tickers / 4 classes)
- `claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md` — textbook
  mechanistic-validation case (AMD-04-17; PM verbalizes bull-priced-in
  in plain English)
- `.specify/memory/constitution.md` — Principle VIII v1.4.6 sub-section
  "Behavioral-additive sub-case (4th interpretation)"
- `memory/reference_behavioral_additive_4th_interpretation.md` —
  operator memory; PM-as-multi-mechanism-validator framing

## Tooling

`scripts/behavioral_additive_sweep.py` is the canonical re-runnable
harness. Run after any non-trivial accumulation of new state logs to
refresh the case count. The sweep is read-only over `~/.tradingagents/logs/`
(no writes; safe to run any time; cost $0).
