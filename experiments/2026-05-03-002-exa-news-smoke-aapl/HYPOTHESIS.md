# Hypothesis: exa-news-smoke-aapl

**Experiment ID**: `2026-05-03-002-exa-news-smoke-aapl`
**Created**: 2026-05-03
**Source idea**: Recommended next step from `experiments/2026-05-03-001-brave-news-smoke-aapl/ANALYSIS.md` ("News quality decisively NOT the bottleneck") — but with the explicit caveat that Brave's `freshness` param has a time-leak (search ranking favors *currently popular* articles, not articles popular on the historical date). Exa closes that caveat.
**Cost estimate**: ~$5 (10 AAPL propagations × ~$0.50, ~50 min — Exa's 4-req/s ceiling is faster than Brave's 0.83/s, so wall-clock should beat Brave's 73 min)

## What we're testing

Third news vendor on the same 10-date AAPL grid. Single variable change vs `brave-news-smoke-aapl`: `--news-vendor exa` instead of `brave`. Everything else identical (same dates, same synthesis prompt, same models, same 4 analysts).

The 8-experiment chain converged on "calibration is LLM-ceiling-bounded, not news-quality-bounded" — but that conclusion rests on:
- yfinance (low-quality press releases + headlines)
- Brave (high-quality content, but `freshness=YYYY-MM-DDtoYYYY-MM-DD` filters by publication date while ranking still favors *currently popular* articles, leaking future information)

Exa's `startPublishedDate` / `endPublishedDate` constrain ranking itself (not just post-hoc filter), so this is the first **honest historical news** test. If calibration still flat → news quality is decisively, time-leak-fairly ruled out. If calibration improves → Brave's time-leak was the confound and the 8-experiment conclusion needs revision.

## Predicted findings

**Scenario A (calibration ceiling holds — most likely, ~80%)**
- Distribution similar to Brave-AAPL (mostly Hold + Underweight, 0 Buy/Sell)
- Forward-α per bucket within ±1% of Brave-AAPL's pattern
- Implication: news quality is not the bottleneck under any realistic vendor — confirms the LLM-single-call ceiling story honestly

**Scenario B (Exa enables better-calibrated bear commitments — ~15%)**
- More Underweight/Sell calls AND those bear ratings have positive α (matching the WC-12 cross-AAPL bear-side win)
- Implication: Brave's time-leak was confounding; the framework CAN extract signal from high-quality, time-honest news
- Justifies scaling: full 65-pair Exa re-pilot, or NVDA + cross-ticker Exa sweep

**Scenario C (Exa shifts calibration in unexpected direction — ~5%)**
- E.g. produces Buys (mode-collapse break like NVDA Brave) and they're wrong, or they're right
- Implication: news *content* shape (Exa's full-article-text vs Brave's excerpts) changes synthesis behavior in ways orthogonal to date-window faithfulness

## Why this is worth running despite the calibration-ceiling conclusion

The brave-news-smoke-aapl ANALYSIS.md "Decision" section ranked single-call baseline as the highest-information cheap test. This Exa experiment is the second-highest: it's the only honest way to close the news-quality question. Without it, the 8-experiment conclusion has a defensible footnote ("ruled out under Brave's known time-leak") that future readers — including future me — can poke at. With it, the news-quality intervention is closed regardless of what the result shows.

Cost is the same as Brave-AAPL (~$5, ~50 min), and the comparison value is high (3-way news-vendor ablation on identical dates is a clean ablation matrix).

## Success criterion

- [ ] 10 AAPL propagations complete with `--news-vendor exa`
- [ ] Distribution comparison vs 4 baselines: AAPL pilot (yfinance), AAPL WC-12 (yfinance, PM-blind), AAPL Brave smoke, NVDA Brave smoke
- [ ] EH-2 gate output recorded
- [ ] Forward-α per bucket computed
- [ ] Per-date breakdown showing which dates Exa diverges from Brave (the time-leak diagnostic)
- [ ] Decision: news-quality intervention closed / open new line of investigation

## Notes

- **Exa adapter** wired in commit (TBD) — `tradingagents/dataflows/exa_news.py`, registered in `interface.py` `VENDOR_LIST` + `VENDOR_METHODS`. Live smoke on AAPL × 2026-03-06→03-13 returned 32 KB of period-relevant content (vs Brave's 8.7 KB on same date), with Yahoo Finance + Investing.com sources within window.
- **Throttle**: 0.25s between Exa calls (free tier ~5 req/s). Should run faster than Brave's 1.2s throttle.
- **Exa per-month free quota**: 1000 search calls. 10 propagations × ~3 news calls ≈ 30 Exa calls. Plenty of headroom.
- **Time-leak diagnostic**: per-date comparison of Brave vs Exa article URLs would directly show which dates Brave was leaking future-popular articles. Out of scope for this analysis but interesting follow-up.
- **PARAMS.json caveat**: `--news-vendor` isn't a `--config-override`, so it doesn't auto-sync to PARAMS.json (same limitation as Brave-AAPL). Document in ANALYSIS.

## Related experiments

- **AAPL pilot** (yfinance news) — pilot baseline, 7 Underweight + 3 Hold
- **WC-12 AAPL cross-ticker** (002, yfinance + PM-blind) — moderated to 7 Hold + 2 Underweight + 1 Sell; bear bucket α=+3.86%
- **brave-news-smoke-aapl** (001, this batch) — 7 Hold + 3 Underweight + 0 Sell; bear bucket α=−1.46% (FLIPPED vs WC-12)
- **brave-news-smoke** (007, NVDA) — Brave produced 2 Buys but α=−4.27%
- **Future single-call baseline** — feed analyst reports straight to one Claude call; tests whether multi-agent structure adds signal

## Decision tree on result

| Result | Action |
|---|---|
| Calibration similar to Brave (Scenario A) | Close news-quality line. Move to single-call baseline as the next definitive test. |
| Calibration improves (Scenario B) | Run NVDA Exa smoke ($5) to confirm cross-ticker. If both improve, scale to 65-pair Exa pilot ($30 — at Constitution Principle III ceiling, requires deliberation). |
| Unexpected divergence (Scenario C) | Diagnose what changed (article content shape vs date-faithfulness). May require Exa-vs-Brave per-date URL diff. |
