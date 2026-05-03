# Hypothesis: single-call-baseline-nvda

**Experiment ID**: `2026-05-03-003-single-call-baseline-nvda`
**Created**: 2026-05-03
**Source idea**: Recommended next step from `experiments/2026-05-03-002-exa-news-smoke-aapl/ANALYSIS.md` "Decision" section — the cheap definitive test of the architectural premise after 9 experiments converged on "calibration is LLM-ceiling-bounded, not vendor-bounded".
**Cost estimate**: ~$1 (10 single Claude calls × ~$0.10 each, ~5 min wall-clock)

## What we're testing

The **architectural premise** of the multi-agent framework: that bull/bear debate + research synthesis + trader proposal + risk debate + portfolio manager produces better calibration than a single LLM call would on the same intermediate inputs.

The 9-experiment chain ruled out news quality, news time-faithfulness, synthesis presence/absence, and synthesis prompt design as the calibration bottleneck. The only remaining structural hypothesis is: **the multi-agent debate adds nothing beyond what one Claude call extracts from the same analyst reports**.

This experiment tests it directly. For each NVDA date, load the existing state log (already contains the 3 analyst reports the framework's analysts produced), feed all three to a single `claude-sonnet-4-6` call with the same 5-tier scale, and compare the resulting calibration to:
- Pilot NVDA (yfinance news, full framework)
- WC-12 NVDA (002, PM-blind variant)
- MR-3 NVDA (004, v2 synthesis prompt)
- Brave-news-smoke NVDA (007, Brave news, full framework)

All four prior NVDA experiments use the same 10 dates, so the comparison is direct.

## Predicted findings

**Scenario A (single-call ≈ framework calibration — most likely, ~70%)**
- Distribution and bucket-α within ±2pp of the framework's NVDA results
- Implication: the multi-agent structure adds cost (5+ LLM calls) without adding signal. The architecture's value proposition collapses.
- Decision: write FINDINGS.md aggregating all 10 experiments + the architectural conclusion

**Scenario B (single-call is materially worse — ~20%)**
- E.g. extreme mode collapse (10/10 Hold) or wildly different distribution
- Implication: the framework's structure DOES extract signal, even if calibration is still ceiling-bounded
- Decision: the structure earns its keep at least directionally; the calibration ceiling is genuinely LLM-bounded but the framework adds *something*. Pursue model-swap experiments next (different LLM might lift the ceiling).

**Scenario C (single-call is materially better — ~10%)**
- E.g. produces fewer Buys at higher hit rate, or breaks bull-side mode collapse correctly
- Implication: the multi-agent structure ADDS noise, confidence collapse, or hedging that hurts calibration. The framework should be SIMPLIFIED, not extended.
- Decision: rebuild around single-call-with-analyst-reports as the core, eliminate debate stages

## Why this is the right cheap definitive test

Per the brave-news-smoke-aapl ANALYSIS.md "Decision" section:
> If single-call calibration ≈ framework calibration, the multi-agent structure is adding cost without adding signal.

It's also:
- **Cheap**: $1, 5 min — vs $5/80 min for a full backtest
- **Apples-to-apples**: uses the EXACT same analyst reports the framework's downstream stages saw (loaded from state logs)
- **Hypothesis-discriminating**: the three scenarios above lead to genuinely different next experiments

## Success criterion

- [ ] 10 single-call ratings produced for NVDA × 10 dates
- [ ] Output CSV in same shape as scripts/backtest.py output
- [ ] Distribution comparison vs 4 prior NVDA experiments
- [ ] EH-2 gate output recorded
- [ ] Forward-α per bucket computed
- [ ] Decision: which scenario above the result supports

## Notes

- **Source state logs**: most-recent NVDA × 10 dates are from brave-news-smoke (007), per `~/.tradingagents/logs/NVDA/TradingAgentsStrategy_logs/full_states_log_*.json` mtime 2026-05-02. So the analyst reports already contain Brave-quality news. This is the fairest comparison input — best-available news content, no debate/synthesis/PM downstream.
- **Same model**: `claude-sonnet-4-6` matches the framework's `deep_think_llm`. No effort/extended-thinking flags (those are Opus-only on this provider).
- **Same scale**: BaselineDecision Pydantic schema mirrors PortfolioRating's 5-tier enum exactly. analyze_backtest.py + check_rating_distribution.py work unmodified.
- **Temperature 0.0**: minimizes single-call run-to-run variance for direct comparison. (The framework runs at provider defaults.)
- **What this DOESN'T test**: AAPL. AAPL would be a useful follow-up if NVDA shows a clear scenario; one ticker is enough to sanity-check the architectural premise first.

## Related experiments

- All 4 prior NVDA experiments use the same 10 dates: pilot, WC-12 (002), MR-3 (004), brave-news-smoke (007).
- **Pilot NVDA**: 0 Buy / 0 OW / 7 Hold / 3 UW / 0 Sell — baseline
- **WC-12 NVDA**: PM-blind broke mode collapse — 5 Buys but α=−0.22% (wrong direction)
- **MR-3 NVDA**: v2 synthesis — 6 OW + 3 Hold + 1 UW; 1 correct Underweight at +2.45% α
- **Brave NVDA**: Brave news + full pipeline — 2 Buys at α=−4.27% (very wrong)

## Decision tree on result

| Result | Action |
|---|---|
| ≈ pilot/Brave (Scenario A) | Write project-level FINDINGS.md. The framework as architected doesn't earn its keep. |
| Materially worse (Scenario B) | Framework adds *something*. Move to model-swap experiments (Opus 4.6 / GPT-5.4 / Gemini 3.x on same NVDA grid). |
| Materially better (Scenario C) | Framework adds noise. Pivot toward "single-call + analyst reports" as the core; deprecate debate stages. |
