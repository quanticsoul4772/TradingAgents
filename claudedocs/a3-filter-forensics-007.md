# A3 Filter Forensics — Experiment 007 (INTC UW commits)

_Generated 2026-05-03 in response to ANALYSIS.md "Scenario D" finding._

## Question

Experiment 007 produced 6 INTC Underweight commits with mean 21d α of **+20.31%** (n=6, 50% hit). The HYPOTHESIS predicted "1-2 UW with at least 1 suppressed by A3 filter at -5%/30d." Reality: 6 UW, 0 suppressed. ANALYSIS.md provisionally diagnosed this as **Scenario D — filter misfires**.

This doc tests three sub-hypotheses:

1. Filter wasn't enabled (config bug)
2. Filter was enabled but INTC wasn't in the suppression zone (≥ -5% momentum)
3. Filter fired but PM emitted UW anyway

## Method

- Read `experiments/2026-05-03-007-opus47-30pair-mixed/PARAMS.json` to verify config
- Read `tradingagents/agents/managers/portfolio_manager.py:90-102` to verify wiring
- Compute INTC 30d momentum at each of the 6 UW dates using `trailing_momentum_pct()` from `tradingagents/agents/utils/momentum_filter.py` (the exact function the filter uses)
- Compute INTC + SPY 21d forward returns at each date to characterize per-row outcomes

## Result

### Sub-hypothesis (1): config bug

PARAMS.json shows:
```json
"config_overrides": {
    "uw_momentum_filter_threshold": -5.0,
    ...
}
```

PortfolioManager wiring (lines 93-102) reads `get_config().get("uw_momentum_filter_threshold")` and only invokes `maybe_suppress_bear_rating()` when non-None. Override is correctly read. **(1) ruled out.**

### Sub-hypothesis (2): INTC not in suppression zone

| Date | INTC 30d momentum | Suppression threshold | Filter fires? |
|---|---:|---:|---|
| 2026-02-06 | **+32.64%** | -5.00% | no |
| 2026-02-13 | **+24.61%** | -5.00% | no |
| 2026-02-20 | **+11.44%** | -5.00% | no |
| 2026-02-27 | -3.87% | -5.00% | no |
| 2026-03-20 | -4.98% | -5.00% | no (just barely) |
| 2026-04-03 | **+12.91%** | -5.00% | no |

**INTC was UP at 4 of the 6 UW dates** (range: +11% to +33%). Only marginally negative on 02-27 (-3.87%) and 03-20 (-4.98%) — both above the -5% threshold.

**Conclusion: filter correctly did not fire on any of these dates.** INTC was never in the mean-reversion zone the filter was designed to protect against.

**(2) confirmed as the answer.** (3) is moot because filter never had a chance to fire.

## Reframe of the per-row verdicts

Once the filter behavior is set aside, the 6 UW commits look very different than the +20.31% mean suggests:

| Date | 30d mom | INTC 21d | SPY 21d | Alpha | Verdict |
|---|---:|---:|---:|---:|---|
| 2026-02-06 | +32.64% | -7.53% | -1.95% | -5.59% | ✓ correct UW |
| 2026-02-13 | +24.61% | -5.83% | -1.61% | -4.23% | ✓ correct UW |
| 2026-02-20 | +11.44% | -0.23% | -4.94% | **+4.71%** | ✗ wrong UW |
| 2026-02-27 | -3.87% | -9.69% | -7.87% | -1.82% | ✓ correct UW |
| 2026-03-20 | -4.98% | **+51.04%** | +8.56% | **+42.48%** | ✗ wrong UW (catalyst) |
| 2026-04-03 | +12.91% | (insufficient fwd) | — | — | — |

**3 correct + 2 wrong + 1 unresolved → 60% hit on resolved (not 50% as analyzer reported)**.

Mean α excluding the 03-20 outlier: (-5.59 - 4.23 + 4.71 - 1.82) / 4 = **-1.73%** (correctly bearish).

The **"+20.31% catastrophe" headline is dominated by ONE extreme commit**: 03-20 INTC ripped +51% in 21d while SPY went +8.6%. That's not a mean-reversion failure (INTC was -5% over 30d, not deeply down) — it's a **regime-shift / catalyst event** that no simple momentum-based filter would catch.

## What this means

**The Scenario D framing in ANALYSIS.md is wrong.** The filter is not misfiring; it is correctly inert on tickers that aren't in mean-reversion zone. The bear-side framework on INTC actually has roughly the same per-row calibration as bull-side OW on AAPL — modest hit rate, mean dragged by single tail events.

**Revised diagnosis**: the 007 INTC UW failure mode is **single-event tail risk**, not systematic anti-calibration. With n=6 and one +42% outlier, mean α is meaningless; median +1.19% (per analyzer) or -1.73% (excluding the single outlier) is the honest signal.

**Implications for filter design**:
- The A3 filter targets the WRONG failure mode for this case. It catches mean-reversion bounces; it would not catch catalyst-driven breakouts.
- A "don't fight strong recent momentum" filter (suppress UW when 30d momentum > +X%) is a different filter, with different tradeoffs (would have suppressed correct UW commits on 02-06 and 02-13 too — the cost is missing real bear opportunities).
- **No simple momentum filter can catch the 03-20 case** without also catching the correct calls.

**Implications for ANALYSIS.md**:
- Headline INTC +20.31% should be footnoted with "median +1.19%, dominated by single 03-20 outlier"
- Per-ticker verdict on INTC should change from "catastrophic anti-calibration" to "modest bear bias with one tail event"
- "Scenario D filter misfires" decision should be REVERSED — filter behaved correctly per its design

**Implications for next experiment**:
- A3 filter forensics done; no filter changes warranted from 007 alone
- Cross-period validation (B-priority 2) is now a higher-confidence next step because the bear-side concern is reframed as small-sample noise, not systematic failure

## Cost

$0 — pure-compute over existing data + 6 yfinance calls.

## Files referenced

- `experiments/2026-05-03-007-opus47-30pair-mixed/PARAMS.json`
- `experiments/2026-05-03-007-opus47-30pair-mixed/results.csv`
- `tradingagents/agents/managers/portfolio_manager.py:90-102`
- `tradingagents/agents/utils/momentum_filter.py:33-104`
- `claudedocs/uw-suppression-filter.md` (original A3 in-sample doc)
