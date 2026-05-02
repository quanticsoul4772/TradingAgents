# Hypothesis: wc12-cross-aapl

**Experiment ID**: `2026-05-02-005-wc12-cross-aapl`
**Created**: 2026-05-02
**Source idea**: WC-12 (cross-ticker validation)
**Cost estimate**: ~$5 (10 AAPL propagations × ~$0.50, ~70 min)

## What we're testing

WC-12 (NVDA, 10 dates) showed `pm_sees_synthesis=false` produces 5/10 Buy ratings vs 0/65 in the baseline pilot — confirming the synthesis is the dilution step. **But the result was on a single ticker (NVDA) which had a strongly bullish pilot bias** (12/13 Overweight in the original pilot). The WC-12 finding might be NVDA-specific.

This experiment runs the same WC-12 intervention on AAPL × 10 dates (same date set as WC-12 NVDA) to test generalization.

## Predicted finding

If the WC-12 finding generalizes:
- AAPL synthesis-blind distribution should also break the pilot's mode collapse, with **at least 2 Buy ratings out of 10** (compared to AAPL's pilot baseline of 1 Hold + most Overweight).

If the WC-12 finding is NVDA-specific:
- AAPL synthesis-blind distribution should remain heavily Overweight/Hold, similar to the baseline.

## Success criterion

- [ ] 10 AAPL propagations complete with `pm_sees_synthesis=false`
- [ ] PARAMS.json auto-synced
- [ ] Rating distribution computed; matched comparison vs AAPL pilot baseline (same 10 dates)
- [ ] EH-2 gate run on the result
- [ ] Forward-alpha computed
- [ ] Decision: WC-12 generalizes / NVDA-specific / mixed

## Notes

- Same 10 dates as WC-12 NVDA (2026-01-30 → 2026-04-03 weekly).
- AAPL pilot showed 9 PARTIAL_OVERLAP / 4 REAL_CONTRADICTION in MR-1 — moderate engagement, similar to NVDA's debate quality.

## Related experiments

- **WC-12 NVDA** — original finding being validated.
- **WC-12-cross-MSFT** (2026-05-02-006) — companion experiment.
