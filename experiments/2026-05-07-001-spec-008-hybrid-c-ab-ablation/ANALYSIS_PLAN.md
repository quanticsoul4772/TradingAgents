# Analysis Plan — Spec 008 SC-009 live A/B ablation

**Status**: Plan only (data not yet collected). When backtest completes + realized α window closes (~2026-05-22), this document becomes the input to the actual ANALYSIS.md.

This plan is committed in advance to (a) lock in analysis methodology BEFORE seeing the data (avoids p-hacking / motivated-reasoning), (b) provide a checklist for the analyst session that returns to write ANALYSIS.md.

## Phase 1 — Wait for backtest completion (~5h ETA from kick-off)

**Trigger**: results.csv has ≥35 rows (allowing for 1 error tolerance), OR error column shows ≥3 rows with errors (which would invalidate the experiment — see "Failure-mode response" below).

**On completion**:
- Verify `wc -l experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv` ≥ 36 (header + 35 rows)
- Spot-check 3-5 rows for sanity (rating in {Buy, Overweight, Hold, Underweight, Sell}, error column empty, run_seconds reasonable)
- Verify state logs were written: `ls ~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json` for ≥30 distinct (ticker, date) combinations
- Confirm boost actually engaged on at least one ticker: `grep -l "calendar_boost" ~/.tradingagents/logs/*/TradingAgentsStrategy_logs/full_states_log_2026-04-{17,24}.json | head -3`

If all checks pass → proceed to Phase 2.

## Phase 2 — Wait for realized α window (~2026-05-22)

**Trigger**: 21 trading days after 2026-04-24 + 1-day yfinance settle buffer = ~2026-05-22.

**Earlier-trigger safeguard**: 2026-04-17's window closes ~2026-05-15. If the analyst returns earlier (between 2026-05-15 and 2026-05-22), partial analysis on the 2026-04-17 cohort alone is acceptable for a preliminary check, but the full SC-009 verdict requires both trade dates' windows closed.

**On window close**:
- Run `python scripts/analyze_backtest.py experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv --holding-days 21` to enrich the CSV with `raw_return` + `alpha_return` columns
- Verify all rows have non-NaN α (any NaN means yfinance data issue — investigate before proceeding)

## Phase 3 — A/B comparison from state logs

**Goal**: extract per-row {pre_rating, fired_bull, calendar_boost, bull_case_priced_in, effective_bull_score} from state logs, then compute boost-ON kept α vs boost-OFF kept α.

**Script to write** (post-completion, ~30min): `scripts/analyze_sc009_ab.py`. Inputs:
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv` (enriched with α)
- State logs in `~/.tradingagents/logs/<TICKER>/TradingAgentsStrategy_logs/full_states_log_<DATE>.json` for each row

For each row:
1. Load state log JSON
2. Extract `state.forward_catalyst.{pre_rating, fired_bull, calendar_boost, bull_case_priced_in, effective_bull_score}`
3. Compute boost-ON fire decision (already in `fired_bull`)
4. Compute boost-OFF fire decision (would_fire_bull_unboosted = `bull_case_priced_in > 0.60 AND pre_rating in {Buy, Overweight}`)
5. Tag each row with both decisions

Aggregate:
- Boost-ON kept set: rows where `fired_bull is False` (boost ON didn't fire OR was below threshold)
- Boost-OFF kept set: rows where `would_fire_bull_unboosted is False`
- For each kept set: mean α
- Net Δα improvement = boost-OFF kept α − boost-ON kept α (positive = boost helps; matches the retrospective's framing)

## Phase 4 — SC-009 acceptance gate evaluation

Per `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/HYPOTHESIS.md` success criterion:

- [ ] **SC-009 gate**: bull-side net Δα improvement in `[+2.35pp, +4.35pp]` (= +3.35pp ± 1pp tolerance)
- [ ] **Adequate fire count**: n_fired-bull under boost-ON ≥ 8
- [ ] **Boost actually engaged**: at least one propagate has `calendar_boost > 0`

Decision tree:
- **All 3 PASS** → write Spec 008 v2 amendment proposal recommending `hybrid_c_calendar_boost_enabled` default flip from `False` → `True`. Cite the SC-009 evidence + the retrofit's +3.35pp consistency.
- **SC-009 gate fails (Δα outside ±1pp tolerance) but n_fired ≥ 8 AND boost engaged** → SKIP default-on flip. Document the period-conditional limitation. Bayesian posterior on "+3.35pp generalizes" updates downward. Future: consider expanded n=60+ follow-up at next research-burst day.
- **n_fired < 8** → INCONCLUSIVE. Expand cohort (e.g., add 2026-05-01 + 2026-05-08 once their windows close ~2026-06-05, doubling n) and rerun. Cost: another ~$18.
- **Boost not engaged** → bug in the code or config; treat as a SC-007 (state annotation completeness) regression and investigate.

## Phase 5 — Decompose the Δα by boost-fire reason

Beyond the headline SC-009 verdict, the analysis should decompose:

- **Boost-positive set** (rows where `calendar_boost > 0`): expected to drive most of the Δα; this is the empirical mechanism
- **Boost-zero set** (rows where `calendar_boost == 0` due to no earnings within window): boost-ON and boost-OFF decisions identical; Δα contribution should be ~0
- Per-ticker breakdown: which tickers' fire decisions changed (boost ON vs boost OFF)?
- Per-date breakdown: any difference between 2026-04-17 vs 2026-04-24?

## Phase 6 — ANALYSIS.md skeleton

```markdown
# ANALYSIS — 2026-05-07-001-spec-008-hybrid-c-ab-ablation

## Headline

[One-line verdict: PASS / SKIP / INCONCLUSIVE per SC-009 gate]

## Setup recap

- 18 tickers × 2 Fridays (2026-04-17, 2026-04-24) = 36 propagates
- Boost ENABLED throughout; boost-OFF comparison post-hoc from state logs
- Cost: $XX.XX (actual)
- Wall-clock: XXh from kick-off to ANALYSIS.md (today + waiting + analysis)

## Phase 4 SC-009 verdict

| Criterion | Threshold | Observed | Status |
|---|---|---|---|
| Bull-side net Δα improvement | [+2.35pp, +4.35pp] | +X.XXpp | PASS/FAIL |
| n_fired-bull (boost-ON) | ≥ 8 | XX | PASS/FAIL |
| Boost engaged on ≥1 row | ≥ 1 | XX | PASS/FAIL |

Decision: [recommend Spec 008 v2 default-on flip / SKIP / INCONCLUSIVE].

## Boost-fire mechanism

- n_fired-bull (boost-ON): XX
- n_fired-bull (boost-OFF, post-hoc): XX
- Incremental fires from boost: XX
- Of the incremental fires, X were cohort-correct (in 2026-04-17/24 cohort_a equivalent) and X were false-positive winners

## Per-ticker / per-date breakdown

| Ticker | 2026-04-17 boost-ON rating | 2026-04-17 boost-OFF would-rating | 2026-04-24 boost-ON | 2026-04-24 boost-OFF |
|---|---|---|---|---|
| (one row per ticker) | | | | |

## Bayesian posterior update

Prior at experiment start: 0.55 on PASS verdict.
Observed evidence: [boost-ON kept α, boost-OFF kept α, n_fired, etc.]
Posterior: [updated value] on PASS verdict per Constitution VIII v1.4.0 forward-catalyst-class gate criteria.

## Implications

- Spec 008 default-on flip: [recommended / not recommended / pending more data]
- Cross-period stability: [holds / period-conditional / TBD]
- Filter portfolio: [no change / Spec 008 v2 amendment to flip default]
- Constitution: [no change / Spec 008 SC-009 procedural section update]

## Reproducibility

```bash
bash experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/run.sh
python scripts/analyze_backtest.py experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv --holding-days 21
python scripts/analyze_sc009_ab.py experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/results.csv
```

## Lessons (if any) for Constitution VIII

[Document any methodology improvements discovered during analysis — e.g., live-mode vs retrofit Δα discrepancies that warrant a Constitution v1.4.4 amendment.]
```

## Failure-mode response

**Backtest crashes mid-run**: results.csv has <30 rows + ≥1 error. Re-run only the failed propagates via `backtest.py` resume mechanism (it skips already-present rows by default). Cost: marginal (~$0.50 × failed-rows).

**State log missing**: `state.forward_catalyst` field absent on some rows → spec 007 disabled for those rows somehow. Investigate config; should not happen with this PARAMS.json.

**All boost calendar_boost = 0**: indicates no earnings within 14 days of either trade date for any ticker. Verify by `python scripts/inspect_class5_surprise_outliers.py` style probe of yfinance.earnings_dates for the cohort. If true, the experiment did not exercise the boost mechanism — INCONCLUSIVE; plan a follow-up with earnings-proximate dates.

**SC-009 gate fails with high statistical confidence (Δα < 0pp i.e. boost actively HURTS)**: this would be a strong negative finding for Spec 008. Document in ANALYSIS.md + propose Spec 008 v2 amendment to MARK the calendar boost as `shakeout_filter: true` (per Constitution VIII v1.4.3 acceptable exception).

## Cross-references

- `specs/007-calendar-boost-filter/spec.md` — SC-009 acceptance gate definition
- `claudedocs/forward-catalyst-hybrid-c-retrospective-2026-05-06.md` — retrofit cohort verdict (+3.35pp)
- `experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/HYPOTHESIS.md` — experiment hypothesis + criteria
- `claudedocs/spec-008-v1.4.3-exemption-audit-2026-05-07.md` — confirms Spec 008 hybrid-filter exemption from Constitution v1.4.3 additive-overlap gate
