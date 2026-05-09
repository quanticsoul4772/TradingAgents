# WC-10 underperformance monitor — v3 cohort smoke test

**Trigger**: reasoning_decision rank #1 (0.74 score). Demonstrates the production-tier monitor (`scripts/wc_10_underperformance_monitor.py`, PR #146) on the v3 bear-regime cohort that landed earlier today (PR #153 PARTIAL ALT-A verdict).

**Sister doc**: PR #146's v1 pilot smoke test (cohort cumulative Δα +22.42pp; 2 per-pair alerts on AAPL UW commits) — this is the v3 counterpart.

## Command run

```bash
python scripts/wc_10_underperformance_monitor.py \
    --csv experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv
```

## Output (verbatim)

```
# WC-10 underperformance monitor

Source: experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv
Paired rows: 8
Decisions differ: 8 of 8
Cohort cumulative Δα (WC-10 minus 5-tier): -1.76pp

## Per-pair details
ticker date         wc_bin       5tier              α%  days      Δpp
NVDA   2025-11-07   Buy          Underweight    -3.48%    21   -6.97pp *
NVDA   2025-11-14   Overweight   Hold           -7.57%    21   -7.57pp *
NVDA   2025-11-21   Buy          Hold           +1.08%    21   +1.08pp *
NVDA   2025-11-28   Overweight   Hold           +5.13%    21   +5.13pp *
NVDA   2025-12-05   Overweight   Hold           +2.81%    21   +2.81pp *
NVDA   2025-12-12   Overweight   Hold           +3.08%    21   +3.08pp *
NVDA   2025-12-19   Overweight   Hold           +0.89%    21   +0.89pp *
NVDA   2025-12-26   Buy          Hold           -0.22%    21   -0.22pp *

## Alert summary
Per-pair alerts (delta < threshold): 2
Streak detected (≥5 consecutive negative): False
Cohort alert (n≥10 + cumulative < threshold): False

**⚠ ALERT: WC-10 production deployment caveat may be active.**
See Constitution v1.5.0 Principle VII sub-section + Spec 009 FR-006 for remediation guidance.
```

Exit code: **1** (alert triggered per single-pair criterion).

## Interpretation

### Headline numbers

| Metric | v3 (this) | v1 (PR #146 smoke test) |
|---|---:|---:|
| Paired rows | 8 | 20 |
| Decisions differ | **8 of 8 (100%)** | 15 of 20 (75%) |
| Cohort cumulative Δα | **-1.76pp** | +22.42pp |
| Per-pair alerts (Δ < -5pp) | **2** | 2 |
| Streak detected | False | False |
| Cohort alert triggered | False (n < 10 floor) | False |

### V3 cohort empirical validation

The v3 cohort is **the canonical PARTIAL ALT-A test case** for the v1.5.1 caveat. The monitor's output empirically validates the v3 ANALYSIS verdict:

- **Cohort Δα -1.76pp** = 8 × -0.22pp avg per pair = matches v3 ANALYSIS aggregate exactly
- **100% decisions differ** matches the per-date table in v3 ANALYSIS
- **2 per-pair alerts** on the 2 worst dates (2025-11-07 -6.97pp + 2025-11-14 -7.57pp) — both schema-induced commits where WC-10 amplified bullish reads on the falling Q4 2025 NVDA cohort

### Comparison to v1 (PR #146)

The v1 cohort showed **+22.42pp cohort Δα** (WC-10 net BEATS 5-tier baseline) with 2 per-pair alerts on AAPL UW commits during +3-6% rally. The v3 cohort shows **-1.76pp cohort Δα** (WC-10 marginally worse) with 2 per-pair alerts on NVDA Buy/OW commits during -3.5/-7.5% drops.

The asymmetric-calibration caveat is empirically visible in BOTH cohorts:
- **v1**: bullish-side amplification well-calibrated (NVDA Buy mean +4.67% α); bearish-side amplified anti-calibrated (AAPL UW)
- **v3**: bullish-side amplification anti-calibrated on a falling cohort (NVDA Buy on Q4 2025); single 5-tier UW (2025-11-07) was directionally correct → WC-10 lost it

The monitor's per-pair alerts identify the SPECIFIC dates where the asymmetric calibration produced the worst outcomes. Operators wiring this into nightly cron would receive alerts when production WC-10 mode hits similar conditions.

### Constitution v1.5.1 caveat in operational form

This smoke test is the production-tier enforcement of the v1.5.1 "Bear-regime validation" paragraph (Constitution VII sub-section, applied via PR #154 Patch D). The caveat reads (paraphrased):

> The v1.5.0 caveat language ("WC-10 amplifies whatever signal the framework was already generating") is correct as-written. The magnitude is small enough that the caveat does NOT require regime-aware gating as a hard requirement; runtime monitoring via `scripts/wc_10_underperformance_monitor.py` provides operational enforcement.

The monitor's exit code 1 + 2 per-pair alerts on this v3 cohort demonstrate: in a production deployment, the operator would receive alerts when these dates passed through the system. Operator could then:

1. Acknowledge the alert (cohort cumulative is -1.76pp on n=8, which is BELOW the -5pp cohort threshold — alert is single-pair-driven)
2. Investigate the specific dates (per-pair table identifies them)
3. Decide whether to switch to `--wc-10-disabled` for similar regimes going forward

### Cohort alert NOT triggered (correct behavior)

The cohort cumulative threshold (n ≥ 10 AND cumulative < -5pp) does NOT fire on v3:
- n = 8 (below the n≥10 floor)
- Cumulative Δα = -1.76pp (above the -5pp threshold even if n were sufficient)

This is the CORRECT behavior. The cohort threshold is designed to flag persistent systematic underperformance, not single-cohort variance. Per-pair alerts are the early-warning tier; cohort alerts are the persistent-pattern tier.

If v3 had been ALT-A (α delta ≤ -1.0pp; e.g., -2pp on this cohort would have produced cohort Δα -16pp on n=8), the per-pair alerts would have been more numerous AND the cohort threshold would likely fire (after combining with other cohorts to reach n≥10).

## Recommendation for production deployment (Spec 009 Branch A)

Per Spec 009 quickstart.md (PR #159) section "Mandatory runtime monitoring":

```bash
# Add to crontab (nightly at 22:00)
0 22 * * * cd /path/to/TradingAgents && python scripts/wc_10_underperformance_monitor.py \
    --csv ~/.tradingagents/paper/today-wc10.csv \
    --alert-threshold-pp -5.0 \
    > ~/.tradingagents/monitor-$(date +\%Y-\%m-\%d).log 2>&1
```

Exit code 1 (alert triggered) should email the operator via the cron mailer. Persistent alerts → Spec 009 Branch revision PR.

## Cost

$0. Monitor consumes saved CSV data + yfinance for realized α; ~50ms per ticker.

## Cross-references

- **PR #146** — `scripts/wc_10_underperformance_monitor.py` (the monitor itself + v1 cohort smoke test)
- **PR #153** — v3 ANALYSIS.md (PARTIAL ALT-A verdict that this smoke test validates)
- **PR #154** — Constitution v1.5.0 → v1.5.1 (Patch D, Bear-regime validation paragraph)
- **PR #159** — Spec 009 quickstart.md (cron-wiring guide for production deployment)
- WC-10 v1 ANALYSIS.md (PR #130) — original Mechanism A vs B precedent
