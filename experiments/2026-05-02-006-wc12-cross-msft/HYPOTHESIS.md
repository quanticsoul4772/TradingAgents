# Hypothesis: wc12-cross-msft

**Experiment ID**: `2026-05-02-006-wc12-cross-msft`
**Created**: 2026-05-02
**Source idea**: WC-12 (cross-ticker validation)
**Cost estimate**: ~$5 (10 MSFT propagations × ~$0.50, ~70 min)

## What we're testing

Companion to `wc12-cross-aapl`. Tests whether WC-12's synthesis-blind finding (5/10 Buy on NVDA) generalizes to MSFT — a different mega-cap tech ticker with somewhat different debate dynamics (MSFT pilot ratings showed mixed Hold/Overweight; AAPL was mostly Overweight; NVDA was 12/13 Overweight).

## Predicted finding

Same as wc12-cross-aapl: if WC-12 generalizes, MSFT should also produce ≥2 Buys when the synthesis is withheld. If NVDA-specific, MSFT should remain near its baseline distribution.

## Success criterion

- [ ] 10 MSFT propagations complete with `pm_sees_synthesis=false`
- [ ] Matched comparison vs MSFT pilot baseline (same 10 dates)
- [ ] EH-2 gate output recorded
- [ ] Forward-alpha computed
- [ ] Decision recorded as part of the joint AAPL+MSFT cross-ticker analysis

## Notes

- Same 10 dates as WC-12 NVDA + WC-12 AAPL.
- MSFT pilot: 5 REAL_CONTRADICTION / 7 PARTIAL_OVERLAP per MR-1 — closest to a 50/50 split among the tickers.

## Related experiments

- **WC-12 NVDA** — original finding being validated.
- **WC-12-cross-AAPL** (2026-05-02-005) — companion experiment.
