# Spec 003 contrarian-gate fire pattern on SC-009 cohort — 2026-05-07

**Trigger**: Per yesterday's `claudedocs/spec-007-v1.4.3-overlap-audit-2026-05-07.md` (PR #26 merged), Spec 007's exemption from Constitution v1.4.3 retroactive application was justified via STRUCTURAL ARGUMENT (Spec 003 + Spec 007 catch different cohorts by construction). Today's SC-009 backtest (in progress, 9/36 rows complete) provides the EMPIRICAL OPPORTUNITY to validate that argument by inspecting the live Spec 003 fire pattern across the same rows where Spec 007 is operating.

**Finding**: **STRUCTURAL ARGUMENT VALIDATED.** Spec 003 + Spec 007 catch different cohorts by construction. PLUS bonus finding: PM's Calibrated Abstention behavior is FUNCTIONALLY EQUIVALENT to Spec 003 firing on extended-rally Tech.

## Per-row Spec 003 contrarian_gate fields

| Ticker | Date | mode | gate_skip | percentile | baseline | per_ticker_n | sector_n |
|---|---|---|---|---|---|---|---|
| NVDA | 2026-04-17 | active | (no skip) | **90.0** | per_ticker | (data) | n/a |
| NVDA | 2026-04-24 | active | (no skip) | 60.0 | per_ticker | (data) | n/a |
| MSFT | 2026-04-17 | active | (no skip) | **97.9** | sector (per-ticker insufficient) | <20 | (data) |
| MSFT | 2026-04-24 | active | (no skip) | **88.1** | sector | <20 | (data) |
| AAPL | 2026-04-17 | active | (no skip) | **100** | per_ticker | (data) | n/a |
| AAPL | 2026-04-24 | active | (no skip) | 75.0 | per_ticker | (data) | n/a |
| WFC | 2026-04-17 | active | insufficient_history | n/a | none | <20 | <20 |
| WFC | 2026-04-24 | active | insufficient_history | n/a | none | <20 | <20 |
| MA | 2026-04-17 | active | insufficient_history | n/a | none | <20 | <20 |

**Bold rows** = percentile ≥ 80 (would fire IF pre_rating bullish). 4 of 9 rows would fire on bull-side suppression IF the PM had committed bull.

## Comparison: Spec 003 vs Spec 007 fire decisions on these rows

| Ticker | Date | PM pre_rating | Spec 003 would-fire-if-bull (pct ≥ 80) | Spec 007 fired_bull |
|---|---|---|---|---|
| NVDA | 2026-04-17 | Hold | YES (pct=90) | no (no bull commit to fire on) |
| NVDA | 2026-04-24 | Overweight | no (pct=60) | **YES** (bull_pi=0.82 > 0.60) |
| MSFT | 2026-04-17 | Hold | YES (pct=97.9) | no |
| MSFT | 2026-04-24 | Hold | YES (pct=88.1) | no |
| AAPL | 2026-04-17 | Hold | YES (pct=100) | no |
| AAPL | 2026-04-24 | Underweight | no (irrelevant — bear commit) | no (no bull commit) |
| WFC | 2026-04-17 | Hold | n/a (skipped) | no |
| WFC | 2026-04-24 | Underweight | n/a (skipped) | no |
| MA | 2026-04-17 | Hold | n/a (skipped) | no |

## Empirical validation of the v1.4.3 audit's structural argument

Yesterday's structural argument: "Spec 003 + Spec 007 catch different cohorts by construction." Today's empirical evidence:

- **Of the 1 bull commit** (NVDA 2026-04-24): Spec 007 fired alone. Spec 003 would NOT have fired (pct=60 < 80). **Disjoint coverage on the only bull commit so far.**
- **Of the 4 would-fire-if-bull-Spec-003 rows** (NVDA 04-17 pct=90, MSFT both, AAPL 04-17): all rated Hold by PM. Spec 003 had no commit to fire on. **Pre-empted by PM's calibrated abstention.**
- **Bonus finding**: the PM is functionally implementing Spec 003's contrarian logic on extended-rally Tech via Constitution VII Calibrated Abstention. Both Spec 003 (would-fire-if-bull) and PM (rates Hold) make the SAME prediction on these rows. Spec 003 is structurally redundant with PM Hold-regime in this cohort.

## What this means for the v1.4.3 retroactive audit

**Spec 007 v1.4.3 exemption is VALIDATED by empirical data**:
- Spec 003 catches: high-prose-density rows (regardless of PM commit)
- Spec 007 catches: high-LLM-priced-in rows WITH bull PM commit
- The two filters' fire sets are **disjoint or near-disjoint** on this cohort
- Spec 007 is additive to Spec 003 (catches NVDA 04-24 OW that Spec 003 misses)
- Spec 003 is additive to Spec 007 in the COUNTERFACTUAL where PM had committed bull on the high-pct rows

**Implication for future v1.4.3 audits**: when a future filter retrospective passes the standalone gate, the empirical overlap analysis should distinguish:
1. **Direct overlap**: both filters fire on the same actual commits
2. **Counterfactual overlap**: would both filters fire on commits THAT THE PM ELECTED TO HOLD? (Constitution VII context)

The second is operationally invisible to the production filter chain (PM Hold means no commit means no fire), but methodologically relevant for understanding filter-mechanism redundancy.

## Methodology note: PM as implicit Spec 003

This finding strengthens the L-2 lesson from `claudedocs/research-burst-2026-05-06.md`: forward-catalyst signals (Spec 007) are a fundamentally different mechanism class than prose-density (Spec 003). On the SC-009 cohort, the PM has internalized Spec 003's contrarian logic via Calibrated Abstention training. The two filters are operationally REDUNDANT-ON-EXECUTION (PM's Hold pre-empts Spec 003's fire) but COMPLEMENTARY-ON-DESIGN (Spec 003 catches what PM might commit; Spec 007 catches what PM already committed).

This is a 4th interpretation of "additive" in the v1.4.3 gate (alongside "different cohort", "different mechanism", and "improves underlying"):
- **Behavioral additive**: filter catches commits the PM would have made HAD it not internalized the gate's logic. Operationally invisible but mechanistically different.

Codify in a future Constitution v1.4.4 amendment if this pattern recurs.

## Cost

\$0 (state-log inspection only).

## Cross-references

- `claudedocs/spec-007-v1.4.3-overlap-audit-2026-05-07.md` — yesterday's structural argument (now empirically validated)
- `claudedocs/sc-009-hold-rate-root-cause-2026-05-07.md` — root cause framing for PM Hold-regime
- `claudedocs/sc-009-mid-backtest-commit-pattern-2026-05-07.md` — Spec 007 fire pattern probe
- `.specify/memory/constitution.md` Principle VIII v1.4.3 — additive-to-existing-filter gate
- Memory: `reference_pm_hold_regime_starves_filters.md` + `reference_pm_hold_with_bullish_prose.md` — operational consequences
