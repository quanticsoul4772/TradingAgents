# Spec 004 SC-008 empirical validation — 2026-05-06

**Question** (per spec 004 SC-008 + R-7): does the spec 004 sector-momentum filter, with default `-5%` threshold, suppress at least 3 of the 5 SC-003 Financials Overweight commits? The premise behind the spec was that "Financials losses came from sector-rotation; XLF was down >5% in 30d before 2026-04-03." This validation either confirms the premise or falsifies it.

**Method**: directly compute XLF prior-30-trading-day return at 2026-04-03 via the spec 004 helper `_compute_etf_30d_return_pct`, then check fire decisions for each of the 5 cohort tickers against the configured threshold.

## Result: PREMISE FALSIFIED

**XLF prior-30-trading-day return at 2026-04-03: -4.54%** — strictly above the -5% threshold. Filter would NOT fire.

```
XLF first close (2026-02-17): 51.93
XLF last close (2026-04-02): 49.53
XLF prior-30d return: -4.54%  (threshold: -5.0%; strict less-than → no fire)
```

**Threshold sensitivity** (which thresholds would have fired):
| threshold | fires? |
|---|---|
| -3.0% | yes (XLF was below this) |
| -4.0% | yes |
| -4.5% | yes |
| -4.6% | no |
| -5.0% | no (default) |
| -7.5% | no |
| -10.0% | no |

The filter would only have fired at thresholds shallower than -4.54%. At a -4% threshold, all 5 Financials commits would fire (since the trigger is sector-level, not per-ticker). Suppressing all 5 would change the bucket from -7.07% mean α → 0% (assuming Hold = 0% α). At -3%, same outcome. **But adopting a -3% to -4% default would be cargo-culting on this single cohort.**

## Bigger finding: sector wasn't even the mechanism

**XLF was UP +4.14% in the 21d window AFTER 2026-04-03** — the 5 Financials Overweight commits underperformed a RISING sector by ~11% on average.

```
XLF close at trade date 2026-04-02: 49.53
XLF close 21 trading days later (2026-05-04): 51.58
XLF 21d forward return: +4.14%

Financials cohort 21d mean α (vs SPY): -7.07%
```

So the losses came from **per-ticker underperformance vs a rising sector**, not from sector-rotation. The narrative in `claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md` ("Financials underperformed SPY by ~7%") was a misread — that was per-ticker α-vs-SPY (which is what we measure), not sector-vs-SPY (which I assumed without verifying).

**Spec 004 was built to catch a different failure mode than what SC-003 Financials actually was.** The filter mechanism (suppress bullish commits when sector ETF is in mean-reversion zone) is still empirically reasonable for genuine sector-rotation losses — it just doesn't address this specific cohort.

## What this means

### For spec 004 itself

The implementation is correct and the test suite is green (29 unit tests, ruff clean). The mechanism is well-defined and would fire on cohorts where the sector ETF actually IS in mean-reversion. But:

- **Default-on flip is NOT justified by the SC-003 Financials cohort.** SC-008 fails as written (would suppress 0 of 5, not ≥3 of 5).
- **The corpus retrospective (T025, deferred from spec 004 polish) becomes more important** — it would scan all bullish commits across the full experiments corpus and report at each threshold how often the filter fires + what the realized α effect is. If across 70+ historical bullish commits the filter shows positive net Δα, that's the empirical case for default-on. If not, default-off is the right call.

### For the empirical narrative

The SC-003 Financials cohort represents a **fourth distinct failure mode** that none of A3 / spec 003 / spec 003.5 / spec 004 catches:

| # | Failure mode | Caught by |
|---|---|---|
| 1 | Bear commits on mean-reversion-bound tickers | A3 (per-ticker momentum, threshold -5%) |
| 2 | Bullish commits with within-ticker bull-prose density spike (mature corpora) | Spec 003 (per-ticker `bull_keyword_count` percentile) |
| 3 | Bullish commits with within-sector bull-prose density spike (cold-start tickers) | Spec 003.5 (sector-pool `bull_keyword_count` percentile) |
| 4 | Bullish commits when sector ETF is in mean-reversion zone | Spec 004 (sector ETF prior-30d return) |
| **5** | **Bullish commits underperforming a rising sector — stock-specific α-vs-sector miss** | **None — needs a different signal** |

Possible signals for failure mode #5:
- Stock-specific bear catalysts (earnings, guidance, downgrades) — would need news/event analysis
- Ticker-α-vs-sector as a feature (current price relative to sector ETF over prior N days)
- Volatility/option-implied-skew signals
- LLM-extracted "ticker-specific risk vs sector" prose feature

None of these are urgent. Constitution VII calibrated abstention is the correct default for ambiguous cases — operators should accept that some commits will lose to per-ticker-vs-sector α drift.

### For default-on flip planning

**Do NOT flip spec 004 to default-on based on this cohort.** Instead:

1. Build T025 (`scripts/sector_momentum_retrospective.py`) to scan the full corpus
2. Report per-threshold (-3, -4, -5, -7.5, -10%) what would fire and the net Δα contribution
3. If positive net Δα at -5%: justify default-on
4. If negative or zero: keep default-off; document that the filter is operator-opt-in for sectors/regimes where they have specific reason to believe sector-rotation is at work

### For the spec 003.5 validation finding

Today's earlier doc (`claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md`) is still mostly correct but should be amended: the meta-finding that "Financials losses came from sector-rotation" was based on a misread. The actual mechanism was per-ticker-vs-sector. Update or note in a follow-up that spec 004 was built against a misread premise — and that the empirical case for spec 004 still has to come from the full-corpus retrospective.

## Reproducibility

```
.venv/Scripts/python.exe -c "
from tradingagents.agents.utils.sector_momentum_filter import _etf_history, _compute_etf_30d_return_pct
print(_compute_etf_30d_return_pct('XLF', '2026-04-03', lookback_days=30))
"
```

Or run the live integration test (T026, deferred during spec 004 implementation):

```
pytest tests/test_sector_momentum_filter.py -v -m integration
```

Output expected: assertion failure noting XLF prior-30d return = -4.54% > -5% threshold; filter would suppress 0/5 (not ≥3/5 as SC-008 required).

## What I'd do next

The reasoning_decision tool ranked spec 004 retrospective (T025) as #2 after this validation. The validation has now run; the next step is the corpus-wide retrospective. **If the retrospective shows the filter would have helped on OTHER bullish-commit cohorts in the historical corpus**, default-on becomes defensible. **If not, spec 004 stays default-off as an operator-opt-in tool for sector-rotation-suspected regimes.**
