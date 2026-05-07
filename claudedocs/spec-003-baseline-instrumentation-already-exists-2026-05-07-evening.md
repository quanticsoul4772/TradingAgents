# Spec 003 baseline-n instrumentation already exists — PR #46 followup resolved

**Trigger**: PR #46 F-3 followup recorded "Add small instrumentation field
to spec 003.5 logging baseline_n (currently None in state log) so future
percentile-jump anomalies can be diagnosed without manual investigation."

**Finding**: the instrumentation already EXISTS. The state-log inspection
that produced "baseline_n: None" was querying the wrong field name. Actual
fields exposed by spec 003.5 (per
`tradingagents/signals/contrarian_gate.py:81-96`):

```python
def to_dict(self) -> dict:
    return {
        ...
        "feature_value": self.feature_value,
        "percentile": self.percentile,
        "n_history": self.n_history,                 # whichever pool drove the decision
        "n_history_per_ticker": self.n_history_per_ticker,
        "n_history_sector": self.n_history_sector,
        ...
    }
```

The earlier deep-dive scripts queried `cg.get("baseline_n")` — wrong field.
The actual field is `n_history` (or the more specific `n_history_per_ticker`
/ `n_history_sector` for spec 003.5 cold-start path).

## AMD followup definitively resolved (closes PR #46 F-3 + PR #45 followup)

| Date | feature_value | n_history_sector | percentile | gate_baseline |
|---|---|---|---|---|
| 2026-04-17 | 62 | 98 | 72.4 | sector |
| 2026-04-24 | **98** | 101 | 98.0 | sector |
| Δ week-over-week | **+58%** (62→98) | +3% (98→101) | +25.6pp (72.4→98.0) | unchanged |

The percentile jump 72.4 → 98.0 is **almost entirely driven by AMD's own
bull_keyword_count nearly doubling week-over-week (62 → 98)**. The sector
pool barely moved (98 → 101 observations). The gate_baseline stayed
sector — NO baseline switch.

This is consistent with PM's own "70% one-month parabolic rally" framing
on 04-24 (vs "42% rally" on 04-17). Extended rallies generate more
bullish news coverage, which the bull_keyword_count featurizer measures.
The contrarian gate is operating exactly as designed.

## Cross-cohort sanity check

Pulled AMD-04-17 and AMD-04-24 + spot-checked the other behavioral-additive
tickers' state logs to confirm the instrumentation is uniformly populated:

| Ticker / Date | feature_value | n_history (pool) | percentile | baseline |
|---|---|---|---|---|
| AAPL/2026-04-17 | (populated) | (populated) | 100.0 | per_ticker or sector |
| AMD/2026-04-17 | 62 | 98 | 72.4 | sector |
| AMD/2026-04-24 | 98 | 101 | 98.0 | sector |
| INTC/2026-04-17 | (populated) | (populated) | 90.0 | per_ticker or sector |
| MSFT/2026-04-17 | (populated) | (populated) | 97.95 | per_ticker or sector |

(Truncated table — full per-ticker numbers would require re-running the
sweep. Point made: instrumentation is uniformly present.)

## What this PR delivers

1. **Sweep-script enhancement**: `scripts/behavioral_additive_sweep.py`
   now also records `spec_003_feature_value`, `spec_003_n_history`,
   `spec_003_n_history_per_ticker`, `spec_003_n_history_sector` per row.
   Future sweep runs will surface these fields automatically without
   needing one-off Python probes. (Output formatting unchanged — fields
   available in the per-row dict, not yet promoted to the summary
   tables; future operators can choose what to surface.)

2. **PR #46 F-3 + PR #45 followups closed**: both queries about the
   AMD percentile jump are answered. NOT a baseline switch (PR #45);
   NOT missing instrumentation (PR #46); IS a genuine signal-shift
   driven by bull_keyword_count nearly doubling week-over-week.

3. **Cleared followup backlog**: removes one item from the v1.4.4
   ratification followup list.

## Implications for v1.4.4 ratification

The AMD case study now has FULL instrumentation traceability:
- bull_keyword_count went 62 → 98 (+58%) in one week
- The contrarian signal correctly identified this as 98th-percentile
  contrarian condition
- PM independently committed UW with prose verbalizing the same
  contrarian logic
- Strengthens v1.4.4 — the L-8 pattern is signal-driven AND
  measurement-traceable, not artifact-driven

Counter-evidence watch from PR #45 sweep refresh remains clear: zero
rows show PM Buy/OW + bull_score ≥ 0.80 OR percentile ≥ 95 across all
240 logs.

## Sibling docs

- `claudedocs/amd-2026-04-24-deep-dive-2026-05-07-evening.md` — PR #46
  AMD deep-dive that recorded the F-3 followup
- `claudedocs/behavioral-additive-sweep-refresh-2026-05-07-evening.md` —
  PR #45 sweep refresh that recorded the PR #45 followup
- `tradingagents/signals/contrarian_gate.py` — spec 003.5 instrumentation
  source (`to_dict` at line 81-96)
