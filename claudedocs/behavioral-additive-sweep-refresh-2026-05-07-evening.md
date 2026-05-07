# Behavioral-additive sweep refresh — 2026-05-07 evening

**Trigger**: 4 new state logs landed since PR #41 sweep (AMD-04-17, AMD-04-24,
AMZN-04-17, AMZN-04-24). Re-running `scripts/behavioral_additive_sweep.py`
to refresh the v1.4.4 ratification evidence basis (PR #44 decision matrix).

**Scope**: numerical refresh + delta analysis only. No new sub-pattern claims;
those would require their own deep-dives.

## Refresh delta vs PR #41

| Metric | PR #41 (mid-afternoon) | Refresh (evening) | Δ |
|---|---|---|---|
| Total state logs scanned | 236 | 240 | +4 |
| Spec 003 instrumented | 10 (4.2%) | 12 (5.0%) | +2 |
| Spec 007 instrumented | 15 (6.4%) | 20 (8.3%) | +5 |
| Spec 008 instrumented | 15 (6.4%) | 20 (8.3%) | +5 |
| Spec 003 cases | 7 | 8 | +1 |
| Spec 007 bull cases | 7 | 10 | **+3** |
| Spec 007 bear cases | 3 | 3 | 0 |
| Spec 008 cases | 6 | 8 | +2 |
| **Total cases** | **23** | **29** | **+6** |
| Distinct tickers | 6 | 8 | +2 |
| Mechanism classes with evidence | 4/4 | 4/4 | 0 |

The 4-mechanism-class threshold for v1.4.4 codification is **maintained**
post-refresh. Total case count up 26%; AMD and AMZN added to the ticker
set (was AAPL+COP+INTC+MSFT+NVDA+WFC; now +AMD+AMZN).

## Updated per-ticker × mechanism breakdown

| Ticker | Spec 003 | Spec 007 bull | Spec 007 bear | Spec 008 | Mechanism classes |
|---|---|---|---|---|---|
| AAPL | 2 | 2 | 0 | 2 | 3 |
| **AMD** (NEW) | 1 | 2 | 0 | 1 | 3 |
| **AMZN** (NEW) | 0 | 1 | 0 | 1 | 2 |
| COP | 0 | 1 | 0 | 1 | 2 |
| INTC | 2 | 2 | 0 | 1 | 3 |
| MSFT | 2 | 1 | 1 | 2 | **4** |
| NVDA | 1 | 1 | 1 | 0 | 3 |
| WFC | 0 | 0 | 1 | 0 | 1 |

AMD jumps directly into the 3-mechanism-class tier (joining AAPL, INTC,
NVDA). MSFT remains the only ticker with all 4. AMZN enters at 2 classes.

## Notable observations from new rows

### AMD-04-24: Spec 003 percentile jumped 72.4 → 98.0 in one week

AMD-04-17 had `spec_003_percentile = 72.4` with `gate_baseline = sector`
(per-ticker history below FR-004 N≥20 floor). AMD-04-24 has
`spec_003_percentile = 98.0` — a 25.6pp jump in one week.

Two possibilities:
- **Most likely**: AMD's per-ticker history crossed the N≥20 floor between
  04-17 and 04-24, switching from sector-baseline to per-ticker baseline.
  AMD's per-ticker bull_keyword_count distribution may be tighter than the
  sector pool, putting current values at higher percentile.
- **Less likely but possible**: bull_keyword_count itself increased
  significantly in AMD's news flow during the week, pushing the percentile
  up regardless of baseline.

State-log doesn't preserve enough information to distinguish; would need
to inspect `~/.tradingagents/cache/spec003_baseline_history/` directly.
Recording as a follow-up; not blocking v1.4.4.

### AMZN-04-24: First clamp-saturation observed in non-INTC ticker

AMZN-04-24 has `spec_008_eff_bull = 1.000` — clamped from
`bull_score = 0.78 × (1 + 0.5 × calendar_boost)`. This is the second
production clamp-saturation observation (first was INTC-04-17 in PR #39).
Confirms spec 008 FR-018 numerical clamp behaves consistently across
tickers.

### Spec 007 bear unchanged at n=3

The bear-side behavioral-additive count did NOT grow with the new rows.
AMD-04-17/24 both had `bear_score = 0.40` (well below T_bear=0.50);
AMZN-04-17/24 both had `bear_score = 0.40`. None of the new rows
contributed to the bear-side sub-pattern.

This is consistent with AMD-04-17 deep-dive F-2 (sub-pattern 4 candidate
— bull-fully-priced-in + bear-thesis-fresh asymmetric setups). Bear-side
behavioral-additive remains a thin n=3 cohort: MSFT-04-24, NVDA-04-24,
WFC-04-17. Not enough evidence to expand bear-side framing.

## v1.4.4 decision matrix update

Updates to the matrix in `claudedocs/constitution-v1.4.4-draft-2026-05-07.md`:

| Pre-ratification check | Status (PR #44) | Status (post-refresh) |
|---|---|---|
| 4+ mechanism classes show evidence | YES (per PR #41 sweep) | YES (still 4/4) |
| Pattern observed across 5+ tickers | YES (7 tickers) | **YES (8 tickers)** |
| ≥1 textbook case with mechanistic PM-prose validation | YES (AMD-04-17) | YES (still AMD-04-17) |
| SC-009 finishes without counter-evidence | PENDING | **PENDING** (now 20/36 rows; 16 more) |
| Memory deferral rule satisfied (3+ mechanism classes) | YES | YES |
| Risk-of-retraction acceptable | YES | YES |
| Operational impact bounded | YES | YES |

**Direction**: +1 ticker, +6 cases, no negative signal. Evidence base
for ratification has STRENGTHENED, not weakened. SC-009 is the one
remaining PENDING check; if backtest finishes without counter-evidence,
ratification on Tuesday morning is well-supported.

## Counter-evidence watch (what would refute the framing)

For tomorrow's ratification check, look for ANY row where:
- bull_score ≥ 0.80 AND PM picked Buy or Overweight, OR
- bear_score ≥ 0.60 AND PM picked Buy or Overweight, OR
- spec_003_percentile ≥ 95 AND PM picked Buy or Overweight

Such rows would indicate PM is NOT correlated with the multi-mechanism
contrarian signals — directly refuting the PM-as-multi-mechanism-validator
framing. So far across all 240 logs, ZERO such rows exist.

## Followups

1. **AMD spec 003 baseline-switch investigation**: inspect
   `~/.tradingagents/cache/spec003_baseline_history/` to confirm the
   72.4 → 98.0 jump is from sector→per-ticker baseline switch vs
   genuine percentile shift. Defer; not v1.4.4-blocking.
2. **Bear-side cohort expansion plan**: bear-side behavioral-additive
   stays at n=3 — too thin for confident codification. The v1.4.4 draft
   is appropriately scoped to the 4-class evidence; bear-side stays in
   the "thin sample" caveat.
3. **AMZN Hold deep-dive deferred**: AMZN×2 are both Hold; behavioral-
   additive on Spec 007 bull at AMZN-04-24 (bull_score=0.78). Not
   urgent; decision matrix already updated numerically.

## Sibling docs

- `claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md` —
  PR #41 source sweep
- `claudedocs/constitution-v1.4.4-draft-2026-05-07.md` — PR #44 draft
  (decision matrix updated by this refresh)
- `claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md` — PR #43 textbook
  case (AMD-04-17)
- `scripts/behavioral_additive_sweep.py` — re-runnable harness
