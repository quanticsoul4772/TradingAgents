# Hypothesis: brave-news-smoke-aapl

**Experiment ID**: `2026-05-03-001-brave-news-smoke-aapl`
**Created**: 2026-05-03
**Source idea**: Recommended next step from `experiments/2026-05-02-007-brave-news-smoke/ANALYSIS.md` "Decision" section
**Cost estimate**: ~$5 (10 AAPL propagations × ~$0.50, ~80 min with throttle)

## What we're testing

Companion to `brave-news-smoke` (which ran NVDA × 10 dates with Brave news + synthesis intact). The NVDA result showed:
- Brave news enabled the synthesis to produce 2 Buy ratings (vs pilot's 0)
- Both Buys had **-4.27% α** — confidently wrong
- Conclusion: NVDA's bullish bias was structurally wrong in this period; better news doesn't fix that

This experiment tests the **mirror condition**: AAPL is a bear-correct ticker in this period (per cross-ticker WC-12 finding: AAPL Underweight α=+3.86%, Sell α=+0.95%, Hold α=−0.84%). If Brave news enables the synthesis to commit to MORE Sells/Underweights AND those bear ratings continue to be correct, we have the **first calibration win** of the entire research arc.

## Predicted findings

Two scenarios:

**Scenario A (Brave news improves bear-side calibration on AAPL)**
- Distribution shifts toward MORE Underweight/Sell vs pilot's 7 Underweight + 3 Hold
- Forward-α stays positive on the bear bucket (matching WC-12 cross-AAPL pattern)
- Implication: news quality matters when the underlying signal is correct AND the synthesis is willing to commit
- Justifies scaling to a larger Brave re-pilot focused on bear-correct tickers

**Scenario B (Brave news produces wrong calls on AAPL too)**
- Bear ratings match pilot but have negative α
- OR ratings shift toward Hold like the WC-12 cross-AAPL pattern (which moderated 5 of 10 to Hold)
- OR ratings shift toward Buy/Overweight (against the period's bearish reality)
- Implication: the framework's calibration problem is not localized to bull/bear bias; it's a general inability to predict, no matter the direction
- Closes the door on news-quality interventions

## Success criterion

- [ ] 10 AAPL propagations complete with `--news-vendor brave`
- [ ] Distribution comparison vs 4 baselines: AAPL pilot, AAPL WC-12 (cross-ticker), NVDA pilot, NVDA Brave smoke
- [ ] EH-2 gate output recorded
- [ ] Forward-α computed for each bucket
- [ ] Decision: scale Brave to bear-correct tickers / abandon news-quality intervention

## Notes

- Same 10 dates (2026-01-30 → 2026-04-03 weekly) as all NVDA experiments and WC-12 AAPL → enables clean 4-way comparison.
- Throttle: 1.2s between Brave calls (per-second free tier limit).
- Brave per-month quota: ~1980 of 2000 remaining today. 10 propagations × ~3 news calls ≈ 30 Brave calls.
- This is the SECOND opportunity for a calibration win across the entire research arc. The MR-3 v2 prompt also produced one (1 Underweight at +2.45% α on NVDA), but n=1.

## Related experiments

- **WC-12 AAPL** (cross-ticker, 005) — pilot was bearish-skewed; PM-blind moderated mostly to Hold but produced 1 Sell with positive α. Same 10 dates.
- **brave-news-smoke** (007) — NVDA companion, showed Brave news enables wrong-direction Buys.
- **MR-3** (004) — synthesis prompt v2; produced 1 correct Underweight on NVDA at +2.45% α.
- **Future scaling decision** — depends on this experiment's calibration result.
