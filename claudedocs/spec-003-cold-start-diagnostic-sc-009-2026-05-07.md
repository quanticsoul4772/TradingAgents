# Spec 003.5 cold-start diagnostic — Spec 003 inert on 61% of SC-009 cohort

**Trigger**: PR #50 F-5 + PR #56 F-5 + PR #65 followup recurring
finding — multiple SC-009 cohort tickers (AMZN, BAC, GS) had Spec 003
`baseline=none`. The pattern looked recurring; this script-driven
diagnostic enumerates the full cohort and surfaces the structural cause.

## Headline finding

**22 of 36 SC-009 rows (61%) had `gate_baseline=none`** — the Spec 003
contrarian gate could not fire on the majority of the cohort due to
insufficient history pools.

Distribution:
- `per_ticker` baseline: 6 rows (16.7%)
- `sector` baseline: 8 rows (22.2%)
- **none baseline: 22 rows (61.1%)**

For comparison, the analyzer reported 13 bull-pre fires (all from Spec
007; Spec 003 contributed structurally zero to operational fires on
this cohort).

## Two distinct cold-start sub-patterns

Walking the 22 `baseline=none` rows, two sub-patterns emerge:

### Sub-pattern 1: Sector pool present but below FR-004 N≥20 floor

| Ticker | Sector (likely) | n_sector at 04-17 | n_sector at 04-24 |
|---|---|---|---|
| WFC | Financials | 15 | 16 |
| BAC | Financials | 15 | 16 |
| GS | Financials | 15 | 16 |
| JPM | Financials | 15 | 16 |
| MA | Payments | 15 | 16 |
| GOOGL | Tech megacap | 15 | 16 |

These tickers have n_sector = 15-17 (close to but below the FR-004 N≥20
floor). The gate is **by-design inert** here per the FR-004 amendment
documented in CLAUDE.md ("FR-004 amended after XLF investigation"). A
small additional propagate cohort (3-5 more sector tickers per sector)
would push these over the floor.

### Sub-pattern 2: Sector pool empty (truly cold-start)

| Ticker | Sector (likely) | n_sector |
|---|---|---|
| AMZN | Consumer Cyclical | 0 |
| COP | Energy | 0 |
| CVX | Energy | 0 |
| LLY | Healthcare | 0 |
| HON | Industrials | 0 |

These 5 tickers represent 5 distinct sectors with ZERO sector pool
history. The framework hasn't seen enough propagates in these sectors
to populate the sector aggregator at all.

## Per-ticker cold-start status across full SC-009 cohort

| Status | Tickers | Count | Notes |
|---|---|---|---|
| `per_ticker` baseline | AAPL, AMD, INTC, MSFT, NVDA, AVGO (probably) | 6 rows × 1-2 dates = 6 | Tech megacaps with most prior runs |
| `sector` baseline | CSCO, AVGO, etc. | 8 rows | Tech-mid where per-ticker is thin but sector is populated |
| `none` baseline (sub-pattern 1: sector 15-17) | WFC×2, BAC×2, GS×2, JPM×2, MA×2, GOOGL×2 | 12 rows | Below FR-004 floor; close to crossing |
| `none` baseline (sub-pattern 2: sector 0) | AMZN×2, COP×2, CVX×2, LLY×2, HON×2 | 10 rows | Truly cold-start |

Total verifies: 6 + 8 + 12 + 10 = 36 rows ✓

## Operational implications

### Implication 1: Spec 003 effective coverage on SC-009 = 39% (14 of 36)

Spec 003 could only fire on rows with active baseline (per_ticker OR
sector). 14 of 36 rows = 38.9% effective coverage. The gate provided
zero filter contribution on 61% of the cohort.

This is consistent with the SC-009 analyzer's "0 decisions changed by
boost" finding — but now it's also "0 decisions changed by Spec 003"
on 22 of 36 rows. Spec 003 simply couldn't engage.

### Implication 2: SC-009 verdict refinement (mid-grade — informational)

The PR #56 PASS-by-non-counterexample framing for spec 008 boost can
be extended: Spec 003 ALSO didn't engage on 61% of the cohort. Both
filters' empirical absence of effect on this cohort is at least partly
explained by structural inability to engage, not by genuine no-effect
mechanism.

For the eventual default-flip framing: SC-009 doesn't disprove either
Spec 003 OR Spec 008 — it just doesn't exercise them on the
representative regime.

### Implication 3: Cold-start universe is operationally addressable

Two paths forward (not actioned in this diagnostic):

1. **Sector-pool warmup** (~30min, $0): run a small "warmup" backtest
   on 3-5 representative tickers from each underrepresented sector
   (Energy, Healthcare, Industrials, Consumer Cyclical) BEFORE the
   next cohort backtest. Would push sub-pattern 1 over FR-004 floor
   AND establish sub-pattern 2 sectors.
2. **FR-004 floor lowering** (NOT recommended): floor was deliberately
   raised to N≥20 per XLF investigation. Lowering to e.g. N≥10 would
   fire on more rows but with statistically thinner baselines.
   Constitution VIII v1.4.x discipline argues against.

### Implication 4: Baseline=none is invisible in default analyzer output

The current analyzer (`scripts/analyze_sc009_ab.py`) doesn't surface
this 61% cold-start rate. Adding a "baseline=none coverage diagnostic"
would help operators interpret future SC-009-class verdicts. This is
an analyzer-enhancement followup; deferred.

## Followups

1. **Sector-pool warmup design** — small backtest on 3-5 tickers per
   underrepresented sector (Energy, Healthcare, Industrials, Consumer
   Cyclical, more Financials, more Tech-mid) to populate baselines.
   ~$15 LLM, ~5h compute. Would unblock proper Spec 003 coverage on
   future cohorts.
2. **Analyzer enhancement** — add baseline-coverage report to
   `analyze_sc009_ab.py` output. ~20min, $0.
3. **Spec 003 historical-recompute** (separate followup; ~2h, $0):
   could backfill baselines for current cold-start tickers from
   existing experiment state logs without rerunning propagates. Listed
   in deferred backlog.

## Sibling docs

- `claudedocs/amzn-2026-04-17-04-24-deep-dive-2026-05-07-evening.md`
  — PR #50 F-5 first noted AMZN baseline=none
- `claudedocs/spec-007-calendar-independence-bac-gs-2026-05-07-late.md`
  — PR #56 F-5 noted BAC + GS baseline=none
- `claudedocs/class-c2-short-interest-feasibility-2026-05-07.md`
  — PR #65 followup mentioned recurring baseline=none pattern
- `tradingagents/signals/contrarian_gate.py` — DEFAULT_HISTORY_FLOOR=20
  (FR-004 amended floor)
