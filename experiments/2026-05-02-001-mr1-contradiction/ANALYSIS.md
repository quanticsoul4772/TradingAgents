# Analysis: mr1-contradiction

Bull/bear debates in TradingAgents are real adversarial debates, not parallel monologues — 50.8% REAL_CONTRADICTION + 49.2% PARTIAL_OVERLAP across 65 pairs, with **zero** PARALLEL_MONOLOGUE — refuting the hypothesis and shifting the locus of mode collapse from the debate to the synthesis step.

## Result

### Distribution

| Label | N | % | Mean score | Median |
|---|---|---|---|---|
| **REAL_CONTRADICTION** | 33 | **50.8%** | 0.75 | 0.75 |
| **PARTIAL_OVERLAP** | 32 | **49.2%** | 0.49 | 0.45 |
| STRAWMAN | 0 | 0.0% | — | — |
| **PARALLEL_MONOLOGUE** | **0** | **0.0%** | — | — |

Overall contradiction score: mean 0.62, median 0.72, range [0.35, 0.82], n=65, 0 errors.

### Per-ticker breakdown

| Ticker | N | Mean score | REAL | PART | STRA | PARA |
|---|---|---|---|---|---|---|
| AAPL | 13 | 0.59 | 4 | 9 | 0 | 0 |
| BRK.B | 3 | 0.55 | 1 | 2 | 0 | 0 |
| GOOGL | 12 | **0.66** | **8** | 4 | 0 | 0 |
| JPM | 12 | 0.64 | 7 | 5 | 0 | 0 |
| MSFT | 12 | 0.58 | 5 | 7 | 0 | 0 |
| NVDA | 13 | **0.67** | **8** | 5 | 0 | 0 |

GOOGL and NVDA produce the most directly-contradicting debates; AAPL and MSFT lean toward partial overlap. No ticker shows any parallel monologue.

### Hypothesis vs reality

| | Predicted | Actual |
|---|---|---|
| PARALLEL_MONOLOGUE | ≥50% | **0%** |
| REAL_CONTRADICTION | <25% | **50.8%** |
| PARTIAL_OVERLAP | (no prediction) | 49.2% |
| STRAWMAN | (no prediction) | 0% |

The prediction was **wrong by the maximum possible margin** on PARALLEL_MONOLOGUE.

### Illustrative excerpts

**Highest contradiction (REAL_CONTRADICTION 0.82): MSFT 2026-04-10**
> Bull and Bear identify the same specific factual claims — CapEx escalation to 66-85% of OCF, gross margin compression across three quarters, sequential revenue deceleration to 2%, MSFT underperformance — and reach opposite conclusions on each.
> Shared claims include: *"CapEx spending has increased significantly (66-85% of OCF)"* and *"Gross margins have compressed from 69.0% to 67.6% year-over-year"*.

**Highest contradiction (REAL_CONTRADICTION 0.82): NVDA 2026-02-06**
> Both sides identify identical claims: (1) Whether a 17.76x P/E justifies the stock at current growth rates, (2) Sustainability of NVDA's 73% YoY revenue growth rate, (3) Margin trajectory under capex pressure.

**Highest contradiction (REAL_CONTRADICTION 0.78): AAPL 2026-02-06**
> The Bull and Bear analysts directly engage on several core factual claims about Apple's valuation and business fundamentals. Both discuss whether the 34.35x P/E is justified — Bull argues Services rerating supports it; Bear argues hardware deceleration makes it untenable.

**Lowest contradiction (PARTIAL_OVERLAP 0.35): AAPL 2026-03-06**
> Bull and bear agree on several key factual premises — Apple's strong Q4 fundamentals, elevated valuation, technical weakness, and substantial FCF generation — but radically diverge on *what those premises imply*. Bull-only: cash conversion excellence (86%), Services ecosystem lock-in. Bear-only: Services growth deceleration (13-15% vs historical 20%+), iPhone market saturation.
>
> Pattern: when the debate falls into PARTIAL_OVERLAP, it's usually because the two sides agree on the *facts* but argue from different *frameworks* (technical vs fundamental, short-term vs structural). They engage with shared data but not with shared interpretations.

## Decision

**The mode-collapse-via-theatrical-debate hypothesis is refuted.** The bull/bear debate apparatus is doing its job — it produces real adversarial argument over the same facts. The framework's mode collapse to moderate ratings (0 Buys, 0 Sells across all 65 pilot runs) **must be located downstream**, in one or more of:

1. **The Research Manager synthesis step** — receives a real disagreement and dilutes it into a "balanced" investment plan that the PM then reads as moderate.
2. **The Portfolio Manager prompt** — given a real synthesis but trained / prompted to converge to Hold / Overweight / Underweight rather than commit to Buy / Sell.
3. **The 5-tier scale itself** — perhaps the prompt's framing of "Buy" and "Sell" makes them feel like extreme commitments the PM defaults away from on principle, regardless of evidence.

This rules out the most architecturally invasive remedy (replacing role-based debate with a battlecode2026-style unified value function — `WC-1`/`BR-1` in `docs/EXPERIMENT.md`) since the architecture works at the debate layer. **The fix is somewhere in the last 2-3 graph nodes.**

### Implications for the next experiments

- **WC-12 (PM-blind test)** is now the highest-leverage Tier 1 idea: if removing the debate from the PM's input doesn't change the rating distribution, then the PM's mode collapse is independent of the (real, working) debate. That confirms the locus is at the PM. If removing the debate DOES change the distribution toward more strong calls, then the PM is being moderated specifically BY the synthesis output.
- **EH-2 (rating distribution gate)** is still useful as a structural enforcement of "use all 5 tiers" but no longer addresses a root cause — the root cause is upstream of the rating choice.
- **A new direction worth adding to the brainstorm**: instrument the Research Manager step. What does its synthesis prompt do with two genuinely contradicting analysts? Does it mention the contradiction or smooth it over? That's a `MR-2`-style follow-up.

### One-paragraph summary for findings.md

(This is the line the aggregator extracts.)

> Bull/bear debates in TradingAgents are real adversarial debates, not parallel monologues — 50.8% REAL_CONTRADICTION + 49.2% PARTIAL_OVERLAP across 65 pairs, with **zero** PARALLEL_MONOLOGUE — refuting the hypothesis and shifting the locus of mode collapse from the debate to the synthesis step.

## Detailed findings

### Score distribution

REAL_CONTRADICTION scores cluster tightly around 0.72-0.78 (mean 0.75, σ ≈ 0.03), suggesting Haiku is using a calibrated band for this label rather than the full 0-1 range. PARTIAL_OVERLAP scores are bimodal at 0.45 and 0.55 (mean 0.49, σ ≈ 0.07). The tight bands are characteristic of structured-output classification rather than continuous reasoning — consistent with the rubric design.

### Why GOOGL and NVDA contradict more

Hypothesis (untested): both have richer valuation debate surface area — high P/E, growth-rate sustainability arguments, capex cycles — that produces more identifiable shared claims to argue over. AAPL has a more "what's it worth?" abstract debate where bull and bear can talk past each other on framework. Worth a follow-up if/when sector breadth expands.

### Why no STRAWMAN

The framework's prompts apparently don't reward (or even allow) misrepresenting the opposing side. The bull and bear are each shown the analyst reports independently (per the LangGraph topology in `tradingagents/graph/setup.py`), so they don't construct positions against the other's text — they argue against the data. STRAWMAN would require seeing and distorting the opponent's claim; the architecture prevents it. **This is an unintended structural protection** worth preserving in any redesign.

## Limitations

- **n=65 pilot data only**, single 3-month window (Jan-Apr 2026). Extending to other regimes would tell us whether the contradiction rate is stable or regime-dependent.
- **Haiku 4.5 used for classification** — Sonnet might be more discriminating (could surface the missing PARALLEL_MONOLOGUE cases that exist in lower-quality bands Haiku categorized as PARTIAL_OVERLAP). A subset re-classification with Sonnet would test rater stability.
- **Single rater, no inter-rater agreement** — would benefit from a second pass with a different prompt/model to validate the labels.
- **The rubric defines REAL_CONTRADICTION strictly** ("same specific factual claim, opposite conclusion"). A looser definition would shift labels but not change the directional finding (no parallel monologue exists).

## Next experiment

**WC-12: PM-blind test.** Strip the bull/bear debate from the Portfolio Manager's input on 10 dates, compare ratings to a 10-date debate-included baseline. If the rating distribution doesn't shift, the debate's contribution to the PM is already lost in synthesis. ~$10. The MR-1 finding makes this experiment higher-priority than I had it ranked in `docs/EXPERIMENT.md`.

## Cost accounting

- Wall-clock: ~11 minutes (65 pairs × ~10s each + 0.5s sleep)
- API cost: ~$3-5 estimated (Haiku 4.5, ~10k tokens per call)
- Errors: 0/65
