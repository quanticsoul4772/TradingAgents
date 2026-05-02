# Analysis: brave-news-smoke

Better news data via Brave Search enabled the synthesis pipeline to break NVDA's Buy-side mode collapse (2/10 Buys vs pilot's 0/65), but the resulting Buy calls had -4.27% mean alpha — confidently wrong, same direction as WC-12's NVDA-side finding — meaning yfinance's poor news quality was not the root cause; the framework's bullish bias on NVDA in 2026 Q1 is structurally wrong regardless of news source, and the planned 65-pair scale-up is NOT recommended for NVDA but should pivot to bear-skewed tickers (AAPL) where bear commitments showed positive forward-alpha.

## Result

### Distribution (Brave news, synthesis intact, NVDA × 10 dates)

| Bucket | Brave smoke | Pilot baseline | WC-12 (PM-blind) | MR-3 (v2 prompt) |
|---|---|---|---|---|
| Buy | **2** | 0 | 5 | 0 |
| Overweight | **8** | 9 | 4 | 6 |
| Hold | 0 | 1 | 1 | 3 |
| Underweight | 0 | 0 | 0 | 1 |
| Sell | 0 | 0 | 0 | 0 |

### Forward-α (5-day vs SPY)

| Bucket | Brave N | Brave α | WC-12 α | Pilot α |
|---|---|---|---|---|
| Buy | 2 | **-4.27%** (0% hit) | -0.22% (40%) | — |
| Overweight | 8 | **+1.35%** (62% hit) | +0.25% (50%) | +0.01% (44%) |
| Hold | 0 | — | +2.34% (n=1) | +2.12% (n=1) |
| Underweight | 0 | — | — | — |
| Sell | 0 | — | — | — |

The Brave-news Buy calls are the **most confidently wrong** of the three conditions. Both Buys (2026-02-20 and 2026-03-13) were dates where NVDA underperformed SPY by ~4% over the next 5 days.

### EH-2 gate

1 DENY: missing Hold + Underweight + Sell. The Brave-smoke distribution is **narrower** than even the pilot — only Buy and Overweight, no moderate or bear-side ratings at all.

### Per-date breakdown vs three baselines

| Date | Pilot | WC-12 | MR-3 | **Brave** |
|---|---|---|---|---|
| 2026-01-30 | Over | Over | Over | Over |
| 2026-02-06 | Over | **Buy** | Over | Over |
| 2026-02-13 | Over | **Buy** | Over | Over |
| 2026-02-20 | Over | **Buy** | Over | **Buy** ← differential |
| 2026-02-27 | Over | Hold | Hold | Over |
| 2026-03-06 | Over | **Buy** | Hold | Over |
| 2026-03-13 | Over | **Buy** | Hold | **Buy** ← differential |
| 2026-03-20 | Over | Over | Over | Over |
| 2026-03-27 | Hold | Over | Over | Over |
| 2026-04-03 | Over | Over | Underweight | Over |

Brave's 2 Buys (2/20 and 3/13) overlap with WC-12's Buy days. Both are dates where multiple conditions independently surfaced bullish conviction — and both were wrong directionally.

### News quality verification

Spot-check on the NVDA 2026-02-06 state log (after the run): the news_report is **9.5KB of period-specific synthesis** referencing real Jan 30 - Feb 6 events:
- OpenAI $100B → $20B deal stall and revision (Bloomberg, Feb 3)
- Jensen Huang's "$660 billion AI infrastructure investment is sustainable and justified" quote
- 8.2% intraday surge on Feb 6
- Day-by-day chronology of the week's news flow

**This is dramatically better content than yfinance**, which would typically return press release titles + boilerplate descriptions. The Brave adapter is working as designed.

## Decision

**The Brave-news re-pilot at scale (Option 1's full 65-pair run, ~$32) is NOT recommended for NVDA.** Three independent conditions (WC-12, MR-3, Brave smoke) have now confirmed that NVDA's bullish ratings in 2026 Q1 underperform the bearish/moderate alternatives. Adding more Brave-news NVDA runs would just produce more confidently-wrong Buys at 6.5x the cost.

### Reframed architectural conclusion

After this experiment, the picture is:

1. **News quality matters for SOME outputs** — Brave enabled mode-collapse breaking (2/10 Buys vs pilot's 0/65).
2. **News quality DOES NOT improve calibration** — those Brave-enabled Buys are the most wrong of any condition (-4.27% alpha).
3. **The framework's bull-side bias on NVDA in this period is real and wrong** — confirmed across 4 conditions (WC-12 Buy α=-0.22%, Brave Buy α=-4.27%, both negative; pilot's accidentally-collapsed Overweights at +0.01% are barely calibrated; MR-3's cautious ratings outperformed).
4. **The synthesis was effectively a tax on bullishness** that, while methodologically wrong (per MR-2), was empirically right in this regime.

### What this changes about the architectural recommendation

**Don't pursue any of these as bullish-mode-collapse fixes for NVDA in this period:**
- Better news data (this experiment — produces wrong Buys)
- Synthesis-blind PM (WC-12 — produces wrong Buys)
- Synthesis prompt v2 (MR-3 — preserves correctness but doesn't break Buy collapse)

**The question shifts**: maybe NVDA's pilot mode collapse was the framework being honestly uncertain, and the moderate ratings (Overweight) actually represent the right confidence level for a mid-uptrend mega-cap. The "5-tier scale" might be the wrong target — perhaps a 3-tier scale (Buy/Hold/Sell) used sparingly is more honest given what the framework can actually predict.

### Should we run Brave on a different ticker?

**Yes, recommended next step**: re-run Brave on AAPL × 10 same dates. The cross-ticker WC-12 result on AAPL showed:
- Pilot: 7 Underweight + 3 Hold (bearish-skewed)
- WC-12 (PM-blind): 7 Hold + 2 Underweight + 1 Sell — and the bear-side commitments had POSITIVE alpha (Underweight +3.86%, Sell +0.95%)

If Brave news on AAPL produces more Sell ratings AND those Sells continue to have positive alpha, that's the calibration win we've been looking for. AAPL is a more discriminating test than NVDA because the bear case is correct in this period.

Cost: ~$5 (10 AAPL propagations). Same throttle, same setup — just `--news-vendor brave --tickers AAPL`.

## Detailed findings

### Why Brave + synthesis produced 2 Buys (vs pilot's 0)

The richer news content gave the analysts more specific bullish material to cite — Jensen Huang's $660B quote, the OpenAI revival from $20B commitment, the 8.2% intraday surge. Bull analyst arguments became more concrete; bear analyst arguments stayed at the higher-level "valuation, sustainability" complaints. The synthesis read the bull's better-grounded specifics as more dispositive.

But "better-grounded specifics" ≠ "predictive of forward returns". The bull's evidence was MORE COMPELLING than yfinance-news bull's evidence, but NVDA's actual price action over the next 5 days didn't reward that conviction. The market priced in the bullish news already; the upside was exhausted.

### Why pilot's mode collapse to Overweight was accidentally correct

The pilot's synthesis prompt (per MR-2) maps "two-sided evidence" → Hold-leaning ratings. With less compelling bull evidence (yfinance news), the bull's case was less specific, the synthesis perceived MORE balance, and ratings stuck at Overweight. Overweight has +0.01% α — barely positive, but at least not negative.

So the moderating effect of the synthesis prompt was COVERING for the framework's overall bull bias. Removing the moderation (WC-12) or improving the bull's input quality (Brave) both expose the underlying bias as wrong.

### The throttle worked

Brave free tier is 1 req/sec. The throttle (1.2s between calls) added ~10 seconds per propagation but eliminated 429s. Net wall-clock 77.6 min vs the WC-12 baseline of 68.7 min (NVDA same dates) — only +13% slower for the throttling.

## Limitations

- **n=10**, single ticker, single window
- Brave's freshness parameter filters by article publication date but ranking still favors currently-popular articles. The news content WAS dated correctly; the ranking bias is a residual concern.
- The 2 Buys are a small sample (n=2) and the -4.27% mean is dominated by both being wrong; can't reject "Brave Buys are random" with this n.
- 5-day forward window only.
- The previous failed-attempt artifacts (6 blank-rating rows in the CSV) were ignored by the analyzer (filters on empty error column AND non-empty rating). Verified clean.

## Next experiment

**brave-news-smoke-aapl** (cost ~$5, ~80 min wall-clock with throttle): re-run with `--tickers AAPL --news-vendor brave` on the same 10 dates. Tests whether better news on a bearish-context ticker produces:
- More Sells than the pilot's 0 OR the synthesis-blind WC-12's 1
- Calibration improvement (bear ratings outperforming moderate ones, as WC-12 AAPL showed)

If positive, that justifies the larger cross-ticker investment. If negative (Brave on AAPL produces mostly Holds like the rest), the architectural conclusion firms up: news quality is not the limiting factor for THIS framework's calibration.

Also worth: a longer holding window (10-day, 21-day) on the existing data — maybe the bullish thesis was correct on a longer timeframe than 5 days.

## Cost & timing

- Wall-clock: 77.6 min (vs 68.7 for WC-12 baseline; +13% from Brave throttle)
- Cost: ~$5
- Errors: 0/10 final (after fix; 4 prior failed attempts at $0 each because they died before any LLM calls)
- PARAMS.json: not auto-synced because `--news-vendor` doesn't go through the `--config-override` path. Manual record of the run is in this ANALYSIS.md.

## One-paragraph summary for findings.md

> Better news data via Brave Search enabled the synthesis pipeline to break NVDA's Buy-side mode collapse (2/10 Buys vs pilot's 0/65), but the resulting Buy calls had -4.27% mean alpha — confidently wrong, same direction as WC-12's NVDA-side finding — meaning yfinance's poor news quality was not the root cause; the framework's bullish bias on NVDA in 2026 Q1 is structurally wrong regardless of news source, and the planned 65-pair scale-up is NOT recommended for NVDA but should pivot to bear-skewed tickers (AAPL) where bear commitments showed positive forward-alpha.
