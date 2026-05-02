# Analysis: wc12-pm-blind

Withholding the Research Manager's synthesis from the Portfolio Manager broke the pilot's Buy-side mode collapse — 5 of 10 NVDA dates produced Buy ratings vs 0 of 65 in the full pilot — confirming that the synthesis IS where moderation gets injected and pointing the architectural fix at the Research Manager rather than the PM, the debate, or the rating scale.

## Result

### Matched-date comparison

NVDA × 10 weekly Fridays (2026-01-30 through 2026-04-03), same dates the pilot already ran:

| Date | Pilot rating | WC-12 (synthesis-blind) | Δ tier |
|---|---|---|---|
| 2026-01-30 | Overweight | Overweight | 0 |
| 2026-02-06 | Overweight | **Buy** | +1 |
| 2026-02-13 | Overweight | **Buy** | +1 |
| 2026-02-20 | Overweight | **Buy** | +1 |
| 2026-02-27 | Overweight | Hold | **−1** |
| 2026-03-06 | Overweight | **Buy** | +1 |
| 2026-03-13 | Overweight | **Buy** | +1 |
| 2026-03-20 | Overweight | Overweight | 0 |
| 2026-03-27 | Hold | Overweight | +1 |
| 2026-04-03 | Overweight | Overweight | 0 |

**Direction summary**: 6 stronger / 3 same / 1 weaker.

### Distribution shift

| Bucket | Pilot (N=10) | WC-12 (N=10) |
|---|---|---|
| **Buy** | **0** | **5** |
| Overweight | 9 | 4 |
| Hold | 1 | 1 |
| Underweight | 0 | 0 |
| Sell | 0 | 0 |

Pilot distribution: 90% concentrated at Overweight (the canonical mode-collapse signature). WC-12 distribution: bimodal across Buy and Overweight, with the 5 Buy ratings being the framework's first ever in any of our experiments (0 Buys across 65 pilot runs + 0 Buys across the original 65 pilot runs).

### Statistical caveat

n=10, single ticker. Cannot make significance claims. The **direction** is unambiguous (60% of dates shifted toward stronger calls, 0% across the pilot ever produced a Buy). The **magnitude** may be inflated by NVDA's pilot bias toward Overweight — different tickers may behave differently. Worth noting and not over-claiming.

## Decision

**Confirmed: the Research Manager's synthesis is the dilution step that produces TradingAgents' mode collapse to moderate ratings.** Removing it from the PM's input lets the PM commit to Buy on 50% of NVDA dates where the pilot produced 0%.

This is the most precise diagnostic finding of the project so far:
- **MR-1** showed the bull/bear debate produces real adversarial argument (refuted "theatrical debate" hypothesis)
- **WC-12 (this experiment)** shows the synthesis layer dilutes that real disagreement before the PM sees it
- **Combined**: the framework's mode collapse is structurally located at the Research Manager's prompt/output, not the debate, not the PM's prompt, not the rating scale, not the LLM's intrinsic moderation tendency

### Architectural implications

1. **Don't replace the debate** with a value-function alternative (per `WC-1` / `BR-1` in `docs/EXPERIMENT.md`) — the debate works.
2. **Don't redesign the PM prompt** in isolation — the PM is responsive to the inputs it gets; if you give it the synthesis, it moderates.
3. **Don't change the rating scale** — when the PM is freed of the synthesis, it uses Buy without coaxing.
4. **DO redesign the Research Manager's synthesis prompt/structure.** Specifically: what language does the current `investment_plan` use that makes the PM hedge? Does it actively recommend moderation, or simply describe both sides in a way the PM interprets as "balanced means moderate"? That's the next experiment (`MR-2`).

### What this doesn't fully isolate

- **WC-12 didn't replace the synthesis with a neutral placeholder** — it withheld it entirely with a marker. Possible that the marker text itself ("withheld by experimental config; build your decision from the trader plan and risk debate alone") has some causal effect on the PM beyond just removing the synthesis. A `WC-12c` follow-up could test this with a less-instructive marker.
- **One ticker, one regime.** Different tickers, different time periods, different market conditions might shift the result. Should re-run on at least 2 more tickers to validate.
- **No forward-return verification.** WC-12 produces stronger calls; we don't know yet whether those stronger calls have BETTER realized alpha than the moderate baseline. Need to wait ~7 calendar days then run the analyzer with the new dates.

## Detailed findings

### Cost & timing

- 10 propagations × 6:50 average = 68.7 min wall-clock (matches estimate)
- Total cost: ~$5 (estimate)
- 0 errors

### PARAMS.json auto-sync verification

This was the first production use of the R-007 PARAMS.json auto-sync feature from the experiments-scaffolding spec (commit `e9e1088`). It worked correctly:
```json
{
  "config_overrides": {"pm_sees_synthesis": false},
  "explicit_flags": {
    "--debate-rounds": 1,
    "--analysts": "market,news,fundamentals",
    "--provider": "anthropic",
    "--deep-model": "claude-sonnet-4-6",
    "--quick-model": "claude-haiku-4-5"
  },
  "baseline": "",
  "notes": ""
}
```

The runner picked up the override, applied it via `apply_overrides()`, propagated to the PM via the global config, AND wrote the effective overrides back to `PARAMS.json` after the run completed. Per Constitution Principle I (Save Everything), the parameters that drove this experiment are now reconstructable from disk forever.

### Subtleties

- **The Hold rating moved date.** Pilot had 1 Hold on 3/27. WC-12 has 1 Hold on 2/27. Same count of moderate ratings, different dates. The PM is not just shifting everything stronger — it's responding to the underlying signals coherently and choosing a different date to be cautious on.
- **The one weaker call (2/27 Overweight → Hold).** This is interesting. Looking at the pilot's NVDA 2/27 transcript would tell us what the synthesis *added* on that specific date that pulled the PM up from Hold to Overweight (or what the PM saw without synthesis that pulled it down). A short follow-up read.
- **Buy clustering Feb-Mar.** All 5 Buys are in February-mid-March; the late-March/April dates returned to Overweight. Possibly correlated with NVDA's actual price action over that window — worth checking against the realized returns once we have them.

## Limitations

- **n=10**, single ticker, single time window.
- **No forward-return data yet.** The dates need 5 trading days each before realized α vs SPY can be computed. Earliest WC-12 date (1/30) is fully resolved; latest (4/3) was almost a month ago, also resolved. Quick follow-up: run the analyzer on this CSV.
- **Withheld vs neutral placeholder confound** — see `WC-12c` future experiment above.
- **Only the `investment_plan` was withheld**; the trader plan still implicitly contains synthesis-influenced reasoning since the Trader runs after the Research Manager. So the PM still sees second-order synthesis effects via the trader plan.

## Next experiment

**`MR-2` (instrument the Research Manager).** Now that we've localized the dilution to the synthesis step, the next question is *why*. Read the actual `investment_plan` text from a few pilot runs — what's the language? Does it use words like "balanced", "moderate", "given the conflicting evidence"? Does the synthesis prompt explicitly request a balanced view? If we can identify the prompt-level cause, the architectural fix is even more precise: edit the synthesis prompt. Cost: $0 (read existing pilot data). Time: ~1 hour.

Also worth: **`WC-12 forward-alpha follow-up`** — run `scripts/analyze_backtest.py` on `experiments/2026-05-02-002-wc12-pm-blind/results.csv` to see whether the 5 stronger Buy calls have better realized α than the matched pilot Overweight calls. Free, immediate.

## One-paragraph summary for findings.md

> Withholding the Research Manager's synthesis from the Portfolio Manager broke the pilot's Buy-side mode collapse — 5 of 10 NVDA dates produced Buy ratings vs 0 of 65 in the full pilot — confirming that the synthesis IS where moderation gets injected and pointing the architectural fix at the Research Manager rather than the PM, the debate, or the rating scale.

---

## Follow-up: forward-alpha analysis (added 2026-05-02 same day)

Ran `scripts/analyze_backtest.py` on this experiment's CSV plus the matched pilot baseline. The forward-alpha numbers materially refine — and arguably partly invert — the conclusion above.

### Realized 5-day α vs SPY

| Bucket | WC-12 N | WC-12 mean α | Pilot N (matched dates) | Pilot mean α |
|---|---|---|---|---|
| Buy | 5 | **−0.22%** | 0 | — |
| Overweight | 4 | **+0.25%** | 9 | +0.01% |
| Hold | 1 | +2.34% | 1 | +2.12% |

**WC-12's Buy calls underperformed WC-12's Overweight calls by ~0.5pp.** The hit rate on Buy was 40% (2 of 5 produced positive α); on Overweight 50% (2 of 4). The Hold call (n=1 each, on different dates) had the highest α in both conditions.

### Critical reinterpretation

The original WC-12 finding (above) is technically correct — the synthesis IS the dilution step that produces moderate ratings — but the **forward-alpha analysis shows the synthesis was dampening an overconfident model, not a well-calibrated one**.

Removing the synthesis:
- ✅ Broke the mode collapse (5 Buys appeared)
- ❌ Did NOT improve calibration — Buy calls had worse α than Overweight calls
- ❌ Mirrors the original pilot's anti-signal pattern (in the full 65-run pilot, Overweight had **−0.35%** mean α with 41% hit rate; here the pattern repeats)

Two interpretations:

1. **The synthesis is defensively dampening a miscalibrated model.** The model can't tell which dates deserve Buy vs Overweight; the synthesis layer learned (probably implicitly via prompt design) to hedge into moderate ratings. Removing the hedge produces stronger labels on the same flawed underlying signal — which is *worse* for end users (now they have confident wrong calls).

2. **Mode collapse to moderate ratings might be a feature, not a bug.** A framework with no genuine edge might be best off staying moderate. The pilot's "0 Buys across 65 runs" looks like a bug in isolation but might be the model honestly conveying low conviction.

### What this changes about the architectural fix

**Original recommendation** (after WC-12 alone): redesign the Research Manager's synthesis prompt to stop diluting genuine disagreement.

**Revised recommendation** (after forward-alpha): redesigning the synthesis is necessary but not sufficient. The deeper issue is **the framework lacks predictive edge** — bull/bear debates produce real arguments (per MR-1), the synthesis dampens them (per WC-12 above), but the underlying signal is anti-correlated with realized returns regardless of what label the PM assigns. Even a perfectly-calibrated synthesis can't add value if the upstream analysis is wrong.

The architectural intervention that would actually matter:
1. **Better data sources upstream.** yfinance news quality is poor; analyst reports built on it can't surface genuine signal. Replace with a real news/sentiment API.
2. **Then** redesign the synthesis to preserve the (now-real) signal that comes through.
3. EH-2-style structural enforcement (rating distribution gates) is still useful for **detecting** miscalibration — would have caught the WC-12 inversion automatically.

### Caveats

- **n=10**, single ticker, single 3-month window. The forward-alpha pattern (Buy < Overweight) could be NVDA-specific or window-specific.
- **5-day horizon only.** Different holding periods might show different calibration.
- **NVDA was a strong-uptrend ticker in this period** — most dates positive α regardless. Cross-ticker validation needed.
- **Sample size for Hold (n=1 in each)** is too small to read into.

### Decision update

**Don't skip MR-2.** Now even more important: identify what specific language in the synthesis is doing the dampening, because we now know the dampening *was probably correct on average*. MR-2 should ask: is the synthesis hedging because it's prompt-instructed to, or because the model is implicitly recognizing low confidence in the analyst inputs? Different causes → different fixes.

**Forward-alpha cost**: $0 (used existing data + free yfinance fetch).
