# Analysis: phase-c-smoke-test

> **Headline**: Phase C end-to-end smoke test passes. Single NVDA 2026-01-30 propagation with `second_opinion_enabled=true` produced a clean Overweight commit + a substantive `[Phase C second-opinion]` annotation block in `final_trade_decision`. All 4 success criteria from HYPOTHESIS met. The asymmetric handling worked correctly: PM Overweight (bullish) + second-opinion bullish + posterior 0.55 → **NEUTRAL** annotation (direction matches but below the 0.6 agreement threshold). Phase C ships as a working opt-in feature.

## Result

### Run summary

- 1 propagation, 0 errors, 7.6 min wall-clock, ~$1-2 actual cost
- Rating: Overweight (extracted from annotated decision via `parse_rating`)
- Decision markdown length: 5875 chars (PM body + Phase C annotation block appended)

### Phase C annotation as actually rendered

```
**[Phase C second-opinion]** [NEUTRAL] Second opinion agrees with direction
                              but at low confidence

- **PM rating**: Overweight (direction: bullish)
- **Second-opinion direction**: bullish
- **Posterior P(framework commit directionally correct)**: 0.55
- **Tone**: neutral
- **Reasoning**: The framework's Overweight commit on NVDA over a 21-day
  horizon has modest positive edge. Technicals are clearly bullish: price
  above 10 EMA > 50 SMA > 200 SMA, MACD accelerating positive, RSI 57
  (room to run), and recent recovery from $178 to $192.50. Fundamentals
  remain best-in-class (66% data center growth, $57B Q3 revenue, expanding
  margins, 0.63 PEG). The Feb 25 earnings catalyst falls within the 21-day
  window... [continues]
- **Evidence supporting PM commit**: 6 bullets — technicals, fundamentals,
  AI capex, China H200, earnings skew, recovery from oversold
- **Evidence contradicting PM commit**: bullets — Bollinger upper band,
  MSFT post-earnings drop, Fed cut delay, software rotation, earnings
  binary risk, SPY tech-overlap

NOTE: This is an advisory annotation only. The PM's rating is NOT modified
by this check.
```

### Validation against HYPOTHESIS success criteria

| Criterion | Result |
|---|---|
| 1 propagation completes with 0 errors | ✓ |
| Final decision contains `[Phase C second-opinion]` annotation block | ✓ |
| PM rating is parseable (Overweight extracted) | ✓ |
| No warning about second-opinion failure in stderr | ✓ |
| Total cost ≤ $3 | ✓ (~$1-2 actual) |

All 4 met. **Scenario A** per HYPOTHESIS decision tree.

### Quality assessment of the second-opinion output

The LLM (Anthropic Opus 4.7) produced:
- A coherent paragraph of reasoning with 6 specific evidence points
- Calibrated posterior (0.55) — not over-confident, not under-confident; matches the "modest bullish lean but not high-conviction" tone
- Direction aligned with PM (bullish) but at low confidence — exactly the case the NEUTRAL annotation tier was designed for
- Evidence bullets that engage with both the bull case (catalyst, fundamentals, technicals) and the bear case (extended positioning, MSFT precedent, Fed)

This is the honest middle-tier output. Direction agreement (bullish/bullish) prevented a REVIEW FLAG; posterior 0.55 < 0.6 threshold prevented a CONFIRMED label. The asymmetric handling did the right thing.

### What this validates about the design

1. **Anthropic Opus + `with_structured_output(SecondOpinionResult)` works in practice** — no graceful degradation triggered. The Pydantic schema (posterior + direction Literal + reasoning + 2 evidence lists) round-trips cleanly through the structured-output path.
2. **The prompt produces useful output** — the LLM read the analyst reports + investment plan + risk debate and synthesized them into independent reasoning. It did NOT just regurgitate the PM's logic.
3. **Asymmetric annotation tiers are useful in practice** — the NEUTRAL tier captures real information ("we agree but cautiously") that would be lost if we only had AGREEMENT/DISAGREEMENT.
4. **PM remains decisive** — rating extracted cleanly; annotation appended without breaking parse_rating.

## Decision

**Scenario A** per HYPOTHESIS decision tree: clean smoke test. Action assigned by HYPOTHESIS:

> "Phase C confirmed end-to-end. RESEARCH_FINDINGS gets a 'Phase C validated' note. Ready to ship Phase C as opt-in feature."

Acting on this:
1. Phase C marked as validated end-to-end in RESEARCH_FINDINGS Q5
2. Phase C remains opt-in (default `second_opinion_enabled=false`) — no change to default behavior
3. Phase C is now suitable to enable for any future experiment that wants per-decision auditing

## Detailed findings

### Cost-effectiveness of the smoke test

The smoke test cost approximately $1-2 (one full Opus propagation including the +1 LLM call for second-opinion) and validated 4 separate concerns about shipped code:
- Schema compatibility with the LLM provider
- Annotation rendering pipeline
- PM rating-extraction robustness when the decision text grows
- Graceful-degradation paths NOT triggering in the happy path

That's $0.25-0.50 per validated concern. The mcp-reasoning recommendation in the post-Phase-C-ship decision call ranked the smoke-test 4th at 0.698 — close to the top — and it earned its rank.

### What this does NOT validate

- **Disagreement-direction case** (REVIEW FLAG): the smoke ran a happy-path agreement case. A REVIEW FLAG annotation has not been observed end-to-end. Would require running until the second-opinion produces a different direction from the PM (likely on a Hold-leaning ticker where the PM commits OW or vice versa).
- **Provider variants**: only Anthropic Opus tested. OpenAI / Google / others use different `with_structured_output` implementations.
- **Cost at scale**: this was one propagation. A full 30-pair experiment with Phase C enabled would add ~$3-5 to a typical $30 T3 budget (10-15% overhead).
- **Statistical claim about second-opinion utility**: this experiment tested that Phase C *runs*, not that it *adds value*. A "Phase C analysis experiment" (deferred, $30+ T3) would measure if second-opinion annotations correlate with realized α correctness.

## Limitations

- Single propagation; no statistical claims possible
- Single ticker (NVDA), single date, single provider (Anthropic)
- The 0.55 posterior is one observation; the second-opinion's posterior calibration across many decisions is unmeasured

## Cost & timing

- Wall-clock: 7.6 min for 1 propagation (vs 6-8 min typical for Opus single-ticker)
- Cost: ~$1-2 (within T1 ≤$5 ceiling)
- Errors: 0/1
- PARAMS.json auto-synced ✓

## Next experiment

Phase C is validated end-to-end and ready to use. No immediate follow-up experiment is required for Phase C itself.

If a Phase C analysis experiment becomes interesting later, the design would be: enable Phase C in a 30-pair experiment, measure (a) what fraction of CONFIRMED annotations land on directionally-correct PM commits vs REVIEW FLAGS landing on directionally-wrong commits. That tests whether the second-opinion's posterior actually predicts outcome accuracy. ~$30-40 T3.

## One-paragraph summary for findings.md

> Phase C end-to-end smoke test passed. Single NVDA 2026-01-30 propagation with `second_opinion_enabled=true` produced a clean Overweight commit plus a substantive `[Phase C second-opinion]` annotation: NEUTRAL tier (direction matches at posterior 0.55, below 0.6 agreement threshold), 6 evidence-for bullets + evidence-against bullets, paragraph of independent reasoning citing technicals + fundamentals + earnings catalyst risk. All 4 success criteria from HYPOTHESIS met (run completes 0 errors, annotation present, rating parseable, no degradation warnings). Validates: Anthropic Opus structured-output works for SecondOpinionResult schema; the prompt produces non-regurgitative reasoning; asymmetric annotation tiers (CONFIRMED / NEUTRAL / REVIEW FLAG) capture real information; PM rating extraction is robust to the appended annotation. Phase C ships as opt-in feature. Cost ~$1-2 / 7.6 min — one of the most cost-effective validations in the project.
