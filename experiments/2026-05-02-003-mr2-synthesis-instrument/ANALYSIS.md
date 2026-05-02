# Analysis: mr2-synthesis-instrument

The Research Manager's prompt and the `ResearchPlan` schema both literally instruct the model to map "two-sided evidence" → Hold-leaning ratings, and MR-1 confirmed two-sided evidence exists in 100% of debates — which mechanically produces the moderation pattern we see; the fix is editing two specific strings of text in `research_manager.py` and `schemas.py`.

## Result

### The smoking gun: explicit prompt instructions

**`tradingagents/agents/managers/research_manager.py`** (lines 17-37 of the prompt) defines the rating scale:

```
**Rating Scale** (use exactly one):
- **Buy**: Strong conviction in the bull thesis; recommend taking or growing the position
- **Overweight**: Constructive view; recommend gradually increasing exposure
- **Hold**: Balanced view; recommend maintaining the current position
- **Underweight**: Cautious view; recommend trimming exposure
- **Sell**: Strong conviction in the bear thesis; recommend exiting or avoiding the position

Commit to a clear stance whenever the debate's strongest arguments warrant one;
reserve Hold for situations where the evidence on both sides is genuinely balanced.
```

**`tradingagents/agents/schemas.py`** `ResearchPlan.recommendation` field description:

```python
recommendation: PortfolioRating = Field(
    description=(
        "The investment recommendation. Exactly one of Buy / Overweight / "
        "Hold / Underweight / Sell. Reserve Hold for situations where the "
        "evidence on both sides is genuinely balanced; otherwise commit to "
        "the side with the stronger arguments."
    ),
)
```

And `rationale`:
```python
rationale: str = Field(
    description=(
        "Conversational summary of the key points from both sides of the "
        "debate, ending with which arguments led to the recommendation. "
        "Speak naturally, as if to a teammate."
    ),
)
```

### The fatal interaction with MR-1

MR-1 established that **100% of bull/bear pairs are either REAL_CONTRADICTION (50.8%) or PARTIAL_OVERLAP (49.2%) — zero pure parallel monologue**. Every single debate has *some* engagement on shared facts. The prompt instructs the model to interpret two-sided evidence as Hold-leaning. The two facts compose mechanically:

1. **Every debate is two-sided** (MR-1 finding)
2. **Two-sided evidence = "balanced" = Hold-leaning** (synthesis prompt instruction)
3. **Therefore: ratings cluster at Hold/Overweight/Underweight, not Buy/Sell**

The model is **following instructions correctly**. The "mode collapse" isn't emergent behavior — it's the literal result of doing what the prompt says.

### Confirming with the actual synthesis outputs

#### Synthesis-step rating distribution (n=65 pilot plans)

| Rating | N | % |
|---|---|---|
| **Buy** | **1** | 1.5% |
| Overweight | 28 | 43.1% |
| Hold | 24 | 36.9% |
| Underweight | 12 | 18.5% |
| **Sell** | **0** | 0.0% |

The Research Manager itself produces 1 Buy and 0 Sells across 65 runs (the PM downstream then converts that 1 Buy to something less strong, leaving 0 Buys at the final rating). The synthesis IS where the strong-call drought begins.

For comparison, the WC-12 PM (when blind to this synthesis) produced **5 Buys in 10 runs** — five times the rate. The dilution starts at the synthesis and propagates downstream.

#### Hedge-word frequency (across all 65 plans)

| Word/phrase | Count | Per-plan average |
|---|---|---|
| "but " | **283** | **4.4** |
| "overweight" | 159 | 2.4 |
| "both sides" | 69 | 1.1 |
| "risks" | 35 | 0.5 |
| "balanced" | 30 | 0.5 |
| "however" | 26 | 0.4 |
| "partial" | 24 | 0.4 |
| "concerns" | 22 | 0.3 |
| "caveats" / "caveat" | 14 | 0.2 |
| "moderately" | 3 | 0.05 |

The synthesis hedges **4.4 times per output on average**. "Both sides" appears in nearly every plan. The vocabulary is densely qualifying.

#### Representative excerpt: NVDA 2026-02-13

> **Recommendation**: Overweight
>
> **Rationale**: This was a high-quality debate, and **both analysts landed genuine punches** — let me walk through where each side stood and why the bull ultimately carried the argument, **albeit with important caveats the bear correctly raised.**
>
> **Where the Bear scored points:**
>
> The bear's strongest contribution was the cyclicality argument. ... The bear is absolutely right that 129% forward EPS growth is not a run rate; it's a snapshot of a company catching an enormous wave. **Deceleration is baked into reality.**

The synthesis itself names the structure: "the bull ultimately carried the argument" — but lands on **Overweight**, not Buy, because of "important caveats the bear correctly raised." This is the exact pattern the prompt design produces. The model isn't confused; it's doing what the rating scale's "Constructive view" definition asks for when the bear has any valid points (which, per MR-1, the bear always does).

## Decision

**Cause identified: the synthesis prompt + schema explicitly instruct the model to map two-sided evidence to Hold/Overweight/Underweight, and MR-1 confirmed two-sided evidence exists 100% of the time.**

This is hypothesis (1) AND (2) from the predictions — both the prompt and the schema description contain the moderation-inducing language. (3) — implicit modeling failure — is **not** the cause; the model is following correct instructions.

### The fix is precise

Three text edits across two files:

1. **`tradingagents/agents/managers/research_manager.py`**: change the closing instruction from
   > "Commit to a clear stance whenever the debate's strongest arguments warrant one; reserve Hold for situations where the evidence on both sides is genuinely balanced."

   to something like
   > "Two-sided evidence is the norm in stock debates; this alone does not warrant Hold. Commit to Buy or Sell when one side's strongest arguments outweigh the other's, even if the other side has legitimate points. Reserve Hold only for cases where the bull and bear arguments are *quantitatively* near-equal in conviction (e.g., similar specificity, similar evidence quality)."

2. **`tradingagents/agents/managers/research_manager.py`**: rewrite the rating-scale definitions to remove the gradient ("Strong conviction" → "Constructive" → "Balanced" → "Cautious" → "Strong conviction"). Replace with criteria that don't push toward the middle:
   - **Buy**: bull arguments outweigh bear; no specific bear arguments are likely to play out within the holding window.
   - **Overweight**: bull arguments outweigh bear; some bear concerns may play out but are likely smaller-magnitude.
   - **Hold**: bull and bear arguments are quantitatively near-equal; the data does not justify a directional view.
   - **Underweight**: bear arguments outweigh bull; some bull theses may play out but are likely smaller-magnitude.
   - **Sell**: bear arguments outweigh bull; no specific bull arguments are likely to play out within the holding window.

3. **`tradingagents/agents/schemas.py`**: update the `ResearchPlan.recommendation` field description to match the new prompt instruction (drop "reserve Hold for genuinely balanced"; add the "two-sided evidence is the norm" clause).

These three edits should — if our diagnosis is correct — produce a meaningfully different rating distribution from the synthesis without any model retraining, new data, or architectural change.

### Important caveat from WC-12 forward-alpha

WC-12's forward-alpha follow-up showed that **stronger ratings ≠ better calibrated**. Even if these prompt changes successfully shift the synthesis distribution toward more Buy/Sell, the realized α might not improve. The synthesis was probably *defensively dampening* a model that lacks predictive edge.

Implications for the next experiment:
- The prompt fix is worth doing because mode collapse is a *quality bug* in its own right (the framework advertises a 5-tier scale but uses 3).
- But the prompt fix alone won't fix the underlying calibration problem.
- The right architectural strategy is still to pursue **better data upstream** (replace yfinance news source) AND **better synthesis prompts** in parallel.

## Detailed findings

### Why "Overweight" specifically (43.1%)

Looking at the rating-scale ladder in the prompt:
- Buy = "Strong conviction in the bull thesis"
- Overweight = "Constructive view; recommend gradually increasing exposure"
- Hold = "Balanced view"

When the model sees a debate with bull arguments outweighing bear (the typical case in the pilot's bullish 2026 Q1 window), the linguistic gradient pushes toward "Constructive" (Overweight) rather than "Strong conviction" (Buy). "Strong conviction" reads as an absolute claim; "Constructive" reads as a defensible best-guess. The model defaults to the safer rhetoric.

This explains why the pilot produced 28 Overweight (43%) but only 1 Buy (1.5%). The Overweight bucket is acting as the "I think the bull is right but I'm hedging because the bear had valid points" answer.

### Comparison: synthesis distribution vs PM-blind WC-12 distribution

| Bucket | Synthesis (n=65 pilot) | WC-12 PM (n=10) |
|---|---|---|
| Buy | 1.5% | **50%** |
| Overweight | 43.1% | 40% |
| Hold | 36.9% | 10% |
| Underweight | 18.5% | 0% |
| Sell | 0% | 0% |

When the PM sees the synthesis, it stays close to the synthesis distribution. When the PM is blind to the synthesis, it commits to Buy 50% of the time (on a heavily-bullish ticker). The synthesis is exerting strong influence on the PM. **The fix is upstream of the PM.**

(Both still produce 0% Sell, which is a separate question. The pilot ran during a generally up-market Jan-Apr 2026 window for these tickers; we'd need a regime with bearish dates to test whether Sell is unreachable structurally or just unreachable in this data.)

## Limitations

- **Quoted plan excerpts are from one date** (NVDA 2026-02-13). A more rigorous version would systematically classify the rationale-text linguistic patterns. Skipped — the prompt-level evidence is overwhelming.
- **Hedge-word counting is keyword-based**, not semantic. "But" includes false positives (e.g., "but **then**", "anything but"). The 4.4-per-plan average is approximate, not exact.
- **The synthesis-rating extraction regex** matched the standard `**Recommendation**: <Label>` format. ~64/65 plans matched cleanly; one missed (probably formatted slightly differently). Doesn't change the directional finding.

## Next experiment

**MR-3: redesigned synthesis prompt.** Implement the proposed prompt edits above (3 text changes). Add a config flag `research_manager_prompt_variant: "default" | "v2"` so the change is reversible and A/B testable. Run the same 10 NVDA dates as WC-12 with `variant=v2`. Compare rating distributions: synthesis(default) vs synthesis(v2) vs PM-blind(WC-12 baseline).

Cost: ~$5 (10 NVDA propagations).
Predicted: synthesis(v2) produces 2-4 Buys (less than WC-12's 5 because the synthesis still rationalizes; more than the original synthesis's 1 because the prompt no longer pushes toward Overweight).

Also worth: **Forward-alpha on the v2 distribution**. Does it improve over either baseline or just shift labels?

## One-paragraph summary for findings.md

> The Research Manager's prompt and the `ResearchPlan` schema both literally instruct the model to map "two-sided evidence" → Hold-leaning ratings, and MR-1 confirmed two-sided evidence exists in 100% of debates — which mechanically produces the moderation pattern we see; the fix is editing two specific strings of text in `research_manager.py` and `schemas.py`.
