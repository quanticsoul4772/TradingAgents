# Hypothesis: single-call-baseline-aapl

**Experiment ID**: `2026-05-03-004-single-call-baseline-aapl`
**Created**: 2026-05-03
**Source idea**: Recommended next step from `experiments/2026-05-03-003-single-call-baseline-nvda/ANALYSIS.md` "Decision" section — critical replication of the NVDA result on the bear-correct AAPL ticker.
**Cost estimate**: ~$1 (10 single Claude calls × ~$0.10 each, ~5 min wall-clock)

## What we're testing

Direct replication of the NVDA single-call baseline result on AAPL. The NVDA result was striking but n=10 single-ticker. This experiment tests whether the result generalizes:

> **NVDA finding**: single-call baseline broke Hold mode collapse entirely (0 Holds, 6 OW + 4 UW), but produced 30% directionally-correct calls — worse than coin flip — with both buckets pointing the wrong direction on average.
>
> **Reframe**: the framework's Hold mode collapse is calibrated humility, not a defect. Single-call manufactures wrong-direction conviction without the synthesis dampening.

If AAPL replicates this pattern (broken Hold collapse + below-coin-flip calibration), the "honest abstention" thesis is robust. If AAPL shows different behavior (e.g. Hold collapse persists, or calibration is materially better), the NVDA result was ticker-specific noise.

## Predicted findings

**Scenario A (NVDA result replicates — ~60%)**
- Distribution: heavily committed, ≤2 Holds out of 10
- Bucket-α: both buckets directionally wrong on average, ≤40% directional hit rate
- Implication: "honest abstention" thesis is robust across tickers. Write project-level FINDINGS.md and wind down.

**Scenario B (AAPL shows Hold collapse OR materially better calibration — ~25%)**
- E.g. single-call AAPL produces 5+ Holds, OR strong calls are ≥60% directionally correct
- Implication: NVDA result was ticker-specific. Maybe AAPL's bear-correctness in this period (per WC-12 cross-AAPL: UW α=−1.79% across vendors) is something single-call can read while it can't for NVDA's mixed signal.
- Decision: more nuanced reframe needed; the LLM has signal on some tickers but not others.

**Scenario C (AAPL shows DIRECTIONAL calibration win) — ~15%)**
- Bear-correct ticker → single-call commits to bear → bear calls directionally right
- Implication: when the underlying signal is unambiguous (AAPL Q1 2026 was structurally bearish per multiple vendors), single-call CAN extract it. The framework's Hold-collapse is throwing away signal that's there.
- Decision: framework's hedging is too aggressive on directionally-clear tickers; needs calibration-by-confidence, not blanket Hold-when-balanced.

## Why this replication matters

Per the NVDA ANALYSIS.md "Decision" section:
> If AAPL single-call also shows wrong-direction strong calls, the "single-call manufactures noise" thesis is robust enough to write a project-level FINDINGS.md and wind down active experimentation.

NVDA had a complex, mixed underlying signal in this period (some bullish dates, some bearish, framework consistently wrong-bullish). AAPL had a more directionally-consistent bear lean (per WC-12 cross-AAPL: 7/10 dates negative SPY-relative). If single-call can read the AAPL bear signal correctly, the conclusion changes.

This is the cheapest, fastest single experiment that can swing the architectural conclusion.

## Success criterion

- [ ] 10 single-call ratings produced for AAPL × 10 dates (resumability + same script as NVDA)
- [ ] Distribution comparison vs 4 prior AAPL experiments (pilot, WC-12, brave, exa)
- [ ] EH-2 gate output recorded
- [ ] Forward-α per bucket computed
- [ ] Per-date breakdown vs realized α (compute directional hit rate)
- [ ] Decision: write FINDINGS.md / pursue model-swap / pivot architecture

## Notes

- **State logs source**: most-recent AAPL × 10 dates are from exa-news-smoke-aapl (002), per state log mtime. So the analyst reports were produced with Exa's time-honest news.
- **Same script**: `scripts/single_call_baseline.py` — no changes from NVDA run. Same model, same prompt, same temperature (0.0), same Pydantic schema.
- **Underlying AAPL signal**: per the per-date α from exa-news-smoke-aapl ANALYSIS, AAPL × 10 dates included both very-bear (2026-02-06 α=−6.66%) and very-bull (2026-01-30 α=+7.38%) days. Net lean was modest bear (4 of 10 negative).

## Related experiments

- All 4 prior AAPL experiments use the same 10 dates: pilot (yfinance), WC-12 cross-aapl (005, PM-blind), brave-news-smoke-aapl (001), exa-news-smoke-aapl (002).
- **single-call-baseline-nvda** (003, this batch) — produced 6 OW + 4 UW + 0 Hold, 30% directionally correct.
- **AAPL pilot**: 0/0/3/7/0 — Hold collapse with bear lean. (Whatever Pilot's UW α was — recompute if needed.)
- **AAPL WC-12** (005): 0/0/7/2/1 — bear-side UW α=−1.79%, Sell α=+0.95%
- **AAPL Brave** (001): 0/0/7/3/0 — UW α=−1.46% (directionally correct)
- **AAPL Exa** (002): 0/0/6/4/0 — UW α=−1.79% (directionally correct)

## Decision tree on result

| Result | Action |
|---|---|
| Replicates NVDA (Scenario A) | Write FINDINGS.md. Architecturally close the project at this milestone. |
| Different pattern (Scenario B) | Reframe more carefully. Perhaps run a 3rd ticker for tiebreaking ($1, ~5 min). |
| Calibration win (Scenario C) | Single-call beats framework on directionally-clear tickers. Pivot framework toward "single-call core + selective hedging" architecture. |
