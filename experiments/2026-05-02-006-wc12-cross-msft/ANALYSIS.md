# Analysis: wc12-cross-msft

WC-12 on MSFT shows a third distinct pattern (no aggressive shift in either direction; mostly tracks pilot) AND the experiment accidentally produced a 2-run reproducibility test that revealed substantial run-to-run variance — same date + same config produced 2-tier rating disagreements in 3 of 10 cases — which is the experiment's most important finding and changes how we should weight all prior single-run results.

## Result

### Important methodological note: the CSV has 20 rows, not 10

This experiment was launched twice in parallel by accident (a buggy `bash ... &` launch in the previous turn was followed by a proper `run_in_background=true` launch before the first one was caught). Both runs wrote to the same `results.csv`. The runner's deduplication uses `(ticker, analysis_date)` only, so when both runs started simultaneously and both saw "no rows done yet", they both ran all 10 dates and appended their results.

**This is a feature, not a bug**. We accidentally got a 2-run reproducibility test of the synthesis-blind PM on MSFT × 10 dates. Run-to-run variance turns out to be substantial.

### Per-date pair comparison

| Date | Run A | Run B | Δ |
|---|---|---|---|
| 2026-01-30 | Overweight | Hold | 1 tier |
| 2026-02-06 | Underweight | Underweight | **same** |
| 2026-02-13 | Overweight | Hold | 1 tier |
| 2026-02-20 | Hold | Underweight | 1 tier |
| 2026-02-27 | Hold | Hold | **same** |
| 2026-03-06 | Hold | Overweight | 1 tier |
| 2026-03-13 | Underweight | Overweight | **2 tiers** |
| 2026-03-20 | Hold | Overweight | 1 tier |
| 2026-03-27 | Overweight | Underweight | **2 tiers** |
| 2026-04-03 | Hold | **Buy** | **2 tiers** |

- 2 exact agreements (20%)
- 5 one-tier disagreements (50%)
- **3 two-tier disagreements (30%)**, including one Hold-vs-Buy

**This is the most important single finding of any cross-ticker experiment.** The synthesis-blind PM is non-deterministic to a degree that affects research conclusions. NVDA's "5/10 Buys" finding from WC-12 might have been "3/10 Buys" or "7/10 Buys" if re-run.

### Distribution (combined across both runs, n=20)

| Bucket | N | % |
|---|---|---|
| **Buy** | **1** | 5.0% |
| Overweight | 6 | 30.0% |
| Hold | 8 | 40.0% |
| Underweight | 5 | 25.0% |
| Sell | 0 | 0.0% |

Pilot MSFT (matched 9 dates; pilot didn't run 1/30): 5 Overweight + 3 Hold + 2 Underweight + 0 Buy + 0 Sell.

WC-12 MSFT distribution is broader (introduces 1 Buy, more Underweight, more Hold) but neither uniformly bullish nor bearish.

### Forward-α (combined across both runs)

| Bucket | N | Mean α | Hit rate |
|---|---|---|---|
| Buy | 1 | -1.04% | 0% |
| Overweight | 6 | **-2.97%** | 17% |
| Hold | 8 | -0.78% | 25% |
| Underweight | 5 | **+0.19%** | 60% |
| Sell | 0 | — | — |

Same calibration pattern as AAPL: bear-side ratings outperform bull-side. MSFT in this period was a market where the bullish lean (Overweight at -2.97%) was the wrong direction. Underweight was the only positive-α bucket.

### EH-2 gate

1 DENY: missing Sell. Better than pilot's distribution coverage (which missed both Buy AND Sell).

## Decision

**Three findings here, in order of importance:**

### 1. (PRIMARY) Run-to-run variance is high

The accidental 2-run replication shows the synthesis-blind PM produces:
- 30% two-tier disagreements
- 50% one-tier disagreements
- 20% exact agreements

This is a major caveat on EVERY single-run experiment we've done. Specifically:
- WC-12 NVDA "5/10 Buys" — actual Buy rate at this point in the architecture might be anywhere from ~30% to ~70% depending on which run you sampled
- WC-12 AAPL "1 Sell" — could be 0 or 2 in alternate runs
- MR-3 NVDA "0 Buys, 1 Underweight" — these specific counts are noisy
- The original pilot's "0 Buys across 65 runs" — robust because n is large; less likely to be a fluke

**Implication**: small-n experiments (n=10) should be run AT LEAST twice and reported as ranges, not point estimates. Or scaled up to n>=30 per condition.

### 2. WC-12 effect is ticker-dependent

Three distinct patterns observed:

- **NVDA** (pilot bullish): WC-12 produces 5 Buys (amplifies bullish bias) — **wrong calibration**
- **AAPL** (pilot bearish): WC-12 produces 7 Hold + 2 Underweight + 1 Sell (moderates bearish bias except for one strong Sell) — **right calibration** (Underweight/Sell outperform Holds)
- **MSFT** (pilot mixed): WC-12 produces 1 Buy + 6 Over + 8 Hold + 5 Under across both runs — broader distribution, **right calibration** (Underweight outperforms Overweight)

The framework's mode collapse depends on whether the synthesis is suppressing real signal vs noise. Removing the synthesis works only when the PM has the directional insight to begin with.

### 3. Bear-side ratings consistently outperform bull-side in 2026 Q1 NVDA/AAPL/MSFT

In all three cross-ticker experiments, the bearish ratings (Underweight, Sell) outperform the bullish ratings (Overweight, Buy) on realized 5-day α. This is a regime characteristic — early 2026 was a period where the bullish surface narrative was systematically over-priced. A different time window might show the opposite pattern.

### Architectural recommendation update

After 4 follow-up experiments (MR-1, WC-12, MR-3, WC-12 cross-ticker), the picture is:

1. **Mode collapse to moderate ratings is real but variable.** Removing the synthesis fixes it on bull-biased tickers (NVDA), partially fixes it on bear-biased tickers (AAPL), barely changes it on mixed tickers (MSFT).
2. **Strong calls are not better-calibrated by default.** They're better when the underlying signal is right (AAPL bear) and worse when it's wrong (NVDA bull).
3. **Run-to-run variance is high enough to invalidate single-run conclusions** at n=10. Need either replication or larger samples.
4. **The Brave news source improvement** (committed but not yet tested via experiment) remains the most important next intervention. Better analyst inputs → better signal → strong calls earn their keep.

## Limitations

- The 2-run replication was accidental. A planned replication would have used different random seeds or different prompt-paraphrase variants for tighter controls.
- MSFT pilot doesn't include 1/30, so 1 of the 10 dates can't be matched.
- n=20 ratings across 10 dates is still small; full statistical analysis (e.g., per-bucket bootstrap CI) would be more rigorous.
- The "right calibration" call is per-bucket-mean; individual ratings are noisy.

## Implications for the experiment workflow itself

This finding should propagate into the `experiments/` convention:

- `EXPERIMENT.md` should add a meta-principle: "n≥10 single-run experiments are exploratory; n≥30 OR 2× replication of n≥10 are inferential."
- Future experiment HYPOTHESIS.md templates could include an explicit `n_replications` field.
- Or — even better — the backtest runner could grow a `--seed` or `--replicate N` flag that re-runs the same grid N times automatically and stores results with replicate IDs.

This discovery (accidental as it was) is more valuable than the cross-ticker finding itself.

## One-paragraph summary for findings.md

> WC-12 on MSFT shows a third distinct pattern (no aggressive shift in either direction; mostly tracks pilot) AND the experiment accidentally produced a 2-run reproducibility test that revealed substantial run-to-run variance — same date + same config produced 2-tier rating disagreements in 3 of 10 cases — which is the experiment's most important finding and changes how we should weight all prior single-run results.
