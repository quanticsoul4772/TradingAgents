# Hypothesis: xlk-q1-2026-substrate

**Experiment ID**: `2026-05-04-002-xlk-q1-2026-substrate`
**Created**: 2026-05-04
**Source idea**: Phase D substrate exploration per post-008 mcp-reasoning Option E — sector ETF as substrate, single ticker XLK on same Q1 2026 dates as 007
**Cost estimate**: ~$10.00
**Cost tier**: T2 (standard, $5 – $30)

## What we're testing

External validity of the architectural reframe (calibrated abstention + per-ticker discrimination + period-conditional realized α) on a NON-EQUITY substrate. **Knob varied**: substrate (single-stock NVDA → sector ETF XLK). All other config matched to 007's NVDA half: same 10 weekly Friday dates 2026-01-30 → 2026-04-03, same Opus 4.7 + Haiku 4.5, same A3 filter at -5%/30d, same exa news vendor, same 1/1 debate rounds. **Adaptation**: `--analysts market,news` only — fundamentals analyst dropped because ETFs have no financial statements / ratings / insider transactions (yfinance returns 404 on `get_fundamentals` for XLK).

## Why we expect generalization signal either way

Under the architectural-reframe hypothesis (framework's value = decision architecture, not equity-specific prediction), XLK Q1 2026 should produce a similar bucket distribution to NVDA Q1 2026 (mostly OW commits, some Hold during local selloffs) — because XLK and NVDA share the tech-sector bull regime in this period. If the framework's behavior is sector-substrate-portable, calibrated abstention should emerge at roughly the same commit rate.

Under the alternative hypothesis (framework is single-stock-tuned), XLK might produce different commit behavior because the news the analysts read is sector-narrative rather than stock-specific, and the market analyst sees ETF flow patterns instead of single-stock momentum.

## Predicted findings

**Scenario A (substrate generalizes)** — ~45%
- XLK distribution ≥60% OW, similar to NVDA Q1 2026's 60% OW pattern (007)
- Realized 21d α positive (XLK is a tech ETF in a bull period)
- Per-row commit pattern similar shape to NVDA Q1 2026

**Scenario B (substrate-different commit behavior)** — ~30%
- XLK distribution skews more Hold than NVDA (sector-narrative more ambiguous than stock-narrative)
- Realized α may still be positive (sector was bullish) but commit rate diverges
- Suggests framework's discrimination is single-stock-prompt-tuned

**Scenario C (substrate-conditional collapse)** — ~20%
- XLK produces different bucket ratio AND different α direction from NVDA
- Substrate is a confound; framework needs prompt redesign for non-stock substrates

**Scenario D (data integration breaks)** — ~5%
- get_news_exa fails or returns nothing useful for "XLK" or "technology sector"
- market analyst tools work on ETF tickers but produce different output texture
- Run completes with errors or empty reports

## Success criterion

- [ ] 10 propagations complete with 0 errors (or ≤1 error)
- [ ] XLK rating distribution tabulated against NVDA Q1 2026 (007)
- [ ] horizon_sweep on the new CSV
- [ ] Per-row commit comparison: XLK 2026-01-30 vs NVDA 2026-01-30 (007), etc.
- [ ] Decision per scenario A/B/C/D
- [ ] Total cost ≤ $15

## Notes

- **Substrate adaptation**: `--analysts market,news` (no fundamentals). Verified `get_fundamentals('XLK')` returns 404 from yfinance.
- **Macro signal self-reference**: market_analyst's `get_sector_etf_strength` will be self-referential when applied to a sector ETF (returns "+1.0% relative strength" XLK vs XLK). Acceptable as a no-op; the analyst will read past it.
- **News for ETFs**: exa search on "XLK" returns ETF flow / sector trend stories. Different texture from single-stock news but populated.
- **Benchmark**: 21d alpha vs SPY. For XLK (tech sector), positive α = "tech outperformed broad market in this 21d window" — measures sector-rotation skill rather than stock-picking skill.
- **Memory log**: fresh `backtest_memory.md` per experiment.
- **Date range**: identical to 007's NVDA half for direct comparison. Q1 2026 (the bull-tailwind period from 007/008 cohort split).
- **Why XLK first** (vs XLF / XLE / etc.): tech is the most analogous sector to NVDA (the highest-signal equity in the corpus). Direct comparison is cleanest.

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (generalizes) | Update RESEARCH_FINDINGS to add "framework's value generalizes to sector-ETF substrate." Plan multi-sector basket (XLK + XLF + XLE) at T3 ~$30. Continues Phase D. |
| Scenario B (substrate-different commit) | Notable finding: framework is single-stock-prompt-tuned. Document, then test if a re-tuned prompt fixes it. Phase D continues but with prompt-engineering caveat. |
| Scenario C (substrate-conditional collapse) | Substrate generalization fails. Phase D pivot: try a different substrate (crypto, FX, prediction markets) instead of more sector ETFs. |
| Scenario D (data integration breaks) | Operational fix needed before continuing Phase D. Document failure mode, plan minimum adaptation. |

## Related experiments

- **007 opus47-30pair-mixed (NVDA Q1 2026 half)**: 6 OW + 4 Hold, 21d OW α = +4.36% n=6, 83% hit
- **008 opus47-cross-period (NVDA Q4 2025)**: 9 OW + 1 Hold, 21d OW α = -0.47% n=9 — period-conditional finding
- **This experiment (XLK Q1 2026)**: tests substrate-generalization hypothesis on the same period as 007's strongest result
- **2026-05-04-001 nvda-q3-2025-micro**: parallel cross-period micro-pilot, running concurrently
