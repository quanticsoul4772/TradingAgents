# Hypothesis: brave-news-smoke

**Experiment ID**: `2026-05-02-007-brave-news-smoke`
**Created**: 2026-05-02
**Source idea**: Option 1 from the close-of-session menu — "Brave-news re-pilot to address the WC-12 forward-α root cause"
**Cost estimate**: ~$5 (10 NVDA propagations × ~$0.50, ~70 min)

## What we're testing

WC-12's forward-α follow-up showed that even when mode collapse breaks (PM-blind variant produces 5/10 Buys), the strong calls have **no better calibration** than the moderate baseline — bearish-side commitments outperformed bullish commitments. The most plausible root cause: the **upstream news data quality is poor** (yfinance news = press releases + headlines, not analyst commentary). MR-1 confirmed the bull/bear debates are real, MR-2 showed the synthesis prompt is hedging-by-design, MR-3 showed prompt fixes produce better calibration but no new Buys, WC-12 cross-ticker showed the synthesis-blind effect varies by underlying signal direction. **All evidence points at the analyst layer's input quality.**

This experiment tests one variable change: swap `data_vendors["news_data"]` from `yfinance` to `brave`. Everything else stays at pilot baseline (synthesis present + v1 prompt + PM sees synthesis).

If Brave news produces better-quality analyst inputs → the bull/bear debate has more accurate evidence → the synthesis arrives at better-calibrated ratings → forward-α improves vs both pilot baseline AND WC-12.

## Predicted finding

Two scenarios worth distinguishing:

**Scenario A (Brave news is the unlock)**: Forward-α calibration on NVDA × 10 dates improves materially over the pilot baseline (which had Overweight α ≈ +0.01% on these dates). Specifically: the rating distribution might still mode-collapse to Overweight (the synthesis hasn't changed), BUT the realized α per bucket should be more positive — better evidence → better-grounded ratings.

**Scenario B (news quality isn't the bottleneck)**: Forward-α numbers stay within the pilot's noise band. Means the synthesis-prompt-design problem (per MR-2) is the real bottleneck, not data quality.

## Why this is a smoke test, not the full re-pilot

The full Option 1 spec was 65 pairs (~$32, ~14 hours overnight) — over the Constitution Principle III ceiling and at risk of overnight kill (Windows update killed the original pilot at run 15/50 weeks ago). Starting with 10 NVDA matched to WC-12/MR-3 dates gives:

1. Matched comparison vs THREE existing baselines: pilot / WC-12 / MR-3
2. ~$5 spend, ~70 min wall-clock — within session, no overnight risk
3. Fast read on whether to commit to the full 65

If results warrant, scale to 65-pair (planned as a follow-up `brave-news-pilot-65` experiment).

## Success criterion

- [ ] 10 NVDA propagations complete with `news_vendor=brave`
- [ ] PARAMS.json records `news_vendor: brave` in explicit_flags
- [ ] Distribution comparison vs pilot, WC-12, MR-3 (4-way) on same 10 dates
- [ ] EH-2 gate output recorded
- [ ] Forward-α computed and compared
- [ ] Decision: scale to 65 / refine the experiment / re-route to a different intervention

## Notes

- The Brave news API was wired in commit `0bca21e` (`tradingagents/dataflows/brave_news.py`), tested with mocks (11 unit tests pass), and live-smoke-tested on a single NVDA query (returned 8.7KB of analyst commentary from CNBC, 24/7 Wall St., Yahoo Finance). This is its first multi-call run.
- **Important caveat about historical news**: Brave's `freshness=YYYY-MM-DDtoYYYY-MM-DD` parameter filters by article publication date but the search ranking still favors *currently popular* articles. Articles popular today may not have been the dominant narrative on the historical date. This is a real research limitation — Brave is a search index, not a snapshot archive. If results look promising, may need to consider a true historical news API (Polygon News, Benzinga) for rigorous backtest.
- `--news-vendor` is a new convenience flag added to `scripts/backtest.py` because `--config-override` can't reach nested dict keys (`data_vendors["news_data"]`).

## Related experiments

- **Pilot baseline** — used yfinance news; produced 0/65 Buys; Overweight α ≈ +0.01%
- **WC-12** (002) — synthesis-blind, yfinance news; 5 Buys but α=-0.22% (wrong)
- **MR-3** (004) — v2 synthesis prompt, yfinance news; better calibration but 0 Buys
- **Future brave-news-pilot-65** — full re-pilot at scale if this smoke shows differential signal
