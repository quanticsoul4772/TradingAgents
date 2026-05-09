# WC-10 underperformance monitor smoke test post Spec 009 Branch C activation

**Date**: 2026-05-09
**Trigger**: Spec 009 Branch C MVP landed (PR #184). Verifying `scripts/wc_10_underperformance_monitor.py` (PR #146) still works correctly and is compatible with Branch C's `wc_10_internal_only=True` mode + the `state["wc_10"]["internal_only"]` annotation field added in PR #184.
**Cost**: $0 (smoke test only; no propagates).

## Smoke test PASSED on v1 paired CSV

Command:

```
python scripts/wc_10_underperformance_monitor.py
```

Source: `experiments/2026-05-08-001-wc-10-pilot/results.csv` (v1; 20 paired rows).

Output:
- 20 paired rows loaded (10 NVDA + 10 AAPL × 2 modes each)
- 15 of 20 decisions differ between WC-10 and 5-tier
- Cohort cumulative Δα: **+22.42pp** (WC-10 minus 5-tier; NVDA bullish-amplification dominant)
- 2 per-pair alerts (delta < threshold) — both AAPL (2026-04-16 -6.23pp + 2026-04-30 -5.46pp; consistent with v1 ANALYSIS bear-side anti-calibration finding)
- No streak alert (no 5-consecutive-negative streak)
- No cohort alert (cumulative is positive at +22.42pp; cohort alert requires cumulative < threshold)

**Conclusion**: monitor still runs correctly post-Branch C. The Branch C MVP doesn't break the monitor because:
- Branch C only kicks in when `wc_10_internal_only=True` (default False)
- When Branch C IS active, the monitor still reads `binned_tier` (the same column the script consumes) — Branch C just routes the rendering through the same `bin_scalar_to_tier()` function the monitor implicitly assumes
- The monitor's alpha-attribution logic uses bin labels, not raw scalar magnitudes, so binning-via-Branch-C is transparent to the monitor

## v2 CSV is wc_10-only — monitor cannot operate on it directly

Investigated:

```
v2 modes: {'wc_10': 80}
v1 modes: {'wc_10': 20, '5tier_baseline': 20}
```

The v2 backtest was designed wc_10-only (no 5-tier baseline rows on the same dates+tickers) per its $32 cost-discipline scope per Constitution III. The underperformance monitor expects BOTH modes per (ticker, date) pair to compute Δα; v2's solo wc_10 rows pass through `_load_paired_rows()` filter that drops keys without both modes present.

Monitor behavior on v2 CSV when explicitly pointed at it:

```
python scripts/wc_10_underperformance_monitor.py --csv experiments/2026-05-08-002-wc-10-v2-ticker-expansion/results.csv
```

Expected: "Paired rows: 0" (no rows match both-modes filter). Monitor exits with no alerts (no data to compare).

This is BY DESIGN — the monitor enforces paired-baseline-comparison discipline. Operators wanting to monitor solo wc_10 CSVs need to either:
1. Run a separate 5-tier baseline backtest on the same (ticker, date) grid, OR
2. Cross-reference against the project's existing 5-tier production corpus (overlapping dates from prior experiments)

## v2 CSV cross-corpus extension — future work scope (NOT shipped today)

A monitor extension to support v2 + solo wc_10 CSVs via cross-corpus pairing would:
- Walk the project's existing 5-tier corpus (e.g., `experiments/*/results.csv` with mode-NULL or mode-5tier_baseline)
- Build a per-(ticker, date) lookup
- Inner-join against the wc_10 CSV's (ticker, date) keys
- Compute Δα per inner-joined pair

Empirical scope for v2: dates 2026-01-30 → 2026-04-03 overlap heavily with the project's Q1 2026 cohort (n=50 OW commits per RESEARCH_FINDINGS). Tickers NVDA + AAPL + MSFT have prior 5-tier coverage; AMZN + GOOG + JPM + JNJ + XOM are net-new in v2 and would have no cross-corpus baseline to pair against. So a cross-corpus extension would yield ~30-40 paired rows from v2 (the Tech subset), not all 80.

**Recommendation**: defer this extension until cumulative WC-10 corpus reaches n≥200 per the v4+ expansion question in `RESEARCH_FINDINGS.md` Open Questions. At current n=100, the cross-corpus pairing wouldn't add enough new evidence to justify the script-extension work.

## Branch C compatibility audit

Branch C MVP (PR #184) added one new annotation field: `state["wc_10"]["internal_only"]: bool`.

Reviewed:
- ✅ The monitor does NOT consume `state["wc_10"]` annotations (operates on the CSV columns: `ticker`, `date`, `mode`, `rating`, `binned_tier`, `error`)
- ✅ The new `internal_only` field doesn't appear in any results.csv column (it's only in the per-propagate state log, not the backtest CSV)
- ✅ Branch C's bin-then-output behavior produces identical results.csv rows as research-mode backtest (the binned tier in the CSV is the same in both modes; only the rendered Rating header in the per-propagate state log differs)

**No monitor modification needed for Branch C compatibility.**

## Operational status

- Monitor: ✅ ready for Branch C deployment (compatible)
- Monitor cron-wiring: ⏳ deferred until daily_signals.py exposes WC-10 mode (Branch A activation, currently not selected per v2 NULL verdict)
- Monitor v2/cross-corpus extension: ⏳ deferred until corpus n≥200

## Cross-references

- `scripts/wc_10_underperformance_monitor.py` (PR #146)
- Spec 009 Branch C MVP retrospective: `claudedocs/spec-009-branch-c-retrospective-2026-05-09.md` (PR #184)
- Constitution v1.5.0 Principle VII sub-section ("Schema-induced abstention is NOT calibrated abstention")
- WC-10 v1 ANALYSIS: `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md`
- WC-10 v2 ANALYSIS: `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md`
- RESEARCH_FINDINGS Open Questions table — v4+ corpus expansion entry
