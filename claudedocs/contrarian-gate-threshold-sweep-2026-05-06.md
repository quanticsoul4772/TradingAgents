# Spec 003 contrarian gate threshold sweep — 2026-05-06

**Spec**: `.specify/specs/003-analyst-contrarian-gate/spec.md`
**History floor**: N >= 20 (FR-004)
**Holding window**: 21 trading days
**Corpus**: 228 propagates → 82 bullish commits → 11 eligible (above floor + α available)

## Empirical motivation

Today's INTC investigation (`claudedocs/sc003-intc-hold-investigation-2026-05-06.md`)
surfaced that the spec 003 default-on flip (commit `2c6ebd0`, 2026-05-06) rests on
n=2 evidence (NVDA + AAPL retrospective, +6.46% cumulative Δα). INTC at bull_kw=98
/ 96th percentile is a concrete counter-example: gate would have suppressed a +103%
winner if PM had committed bullish.

This sweep tests whether a threshold change (tighten to 90/95% or revert to off)
is empirically justified.

## Baseline (no gate): n=11, mean α = +1.97%

## Threshold sweep

| threshold | n_kept | n_fired | kept α | fired α | net Δα | suppressed-loser α | suppressed-winner α |
|---|---|---|---|---|---|---|---|
| 75% | 8 | 3 | +3.33% | -1.65% | +1.36pp | -3.56% (n=2) | +2.18% (n=1) |
| 80% | 9 | 2 | +2.62% | -0.97% | +0.65pp | -4.11% (n=1) | +2.18% (n=1) |
| 85% | 11 | 0 | +1.97% | +nan% | +0.00pp | +nan% (n=0) | +nan% (n=0) |
| 90% | 11 | 0 | +1.97% | +nan% | +0.00pp | +nan% (n=0) | +nan% (n=0) |
| 95% | 11 | 0 | +1.97% | +nan% | +0.00pp | +nan% (n=0) | +nan% (n=0) |

## Per-sector breakdown at threshold 80%

| Sector | n_total | n_fired | kept α | fired α | net Δα |
|---|---|---|---|---|---|
| Technology | 11 | 2 | +2.62% | -0.97% | +0.65pp |

Only Technology has eligible commits. Other sectors don't have tickers with N≥20 prior history (NVDA + AAPL dominate the eligible set; the broader corpus is too young).

## Suppressed-winner outliers at threshold 80%

| Ticker | Date | bull_kw | percentile | n_history | realized α |
|---|---|---|---|---|---|
| NVDA | 2026-04-10 | 71 | 80% | 30 | +2.18% |

One incorrect-suppression in the eligible set. The other fire (-4.11% α) was a correct suppression of a loser.

## Verdict — KEEP default-on at 80%, with caveats

**The data supports keeping the spec 003 default-on flip at the 80% threshold.** Net Δα is positive at +0.65pp across 11 eligible commits, driven by 1 correct suppression of a loser (-4.11%) outweighing 1 incorrect suppression of a moderate winner (NVDA +2.18%).

**Caveats**:

1. **Sample is tiny (n=11)**. Only NVDA + AAPL in the corpus have ≥20 prior bullish observations meeting the FR-004 floor. Statistical confidence is low.
2. **50% hit rate on fires** at 80% (1 correct, 1 incorrect). The net positive comes from magnitude asymmetry, not from the gate being reliably right.
3. **The INTC case that motivated this sweep is NOT in the eligible set** — INTC was rated Hold, not Buy/OW, so it doesn't appear in the bullish-commit count. The +103% counter-example remains a *hypothetical*: the gate would have fired IF the PM had committed bullish.
4. **Tightening doesn't help**: at 85%, 90%, 95% the gate never fires in this corpus (zero data points to support a tighter threshold).
5. **Loosening to 75% gives +1.36pp** (better, but more fires + more incorrect-suppression risk on tickers like INTC if the PM had committed).

**No threshold change recommended at this corpus size.** The empirical signal supports neither tightening nor reverting; the 80% default stands.

**What would change the verdict**:

- A 50+ commit eligible set (would require multi-window SC-003 replication, T2-T3 cost). Adding more dates to the corpus should expand the bullish-commit count past the floor for more tickers.
- An actual (not hypothetical) gate-fire on a large winner like INTC. INTC's actual rating was Hold; if it had been Buy/OW + the gate had fired + INTC went +103%, that single counter-example would dwarf the current +0.65pp Δα and force a default-off revert.

**Operational recommendation**: keep default-on at 80% but document the small-sample basis prominently. Re-run this sweep after the next 30+ propagate runs to see if the picture changes. The INTC class of risk is real but unrealized in current data.

## Implications for the broader filter taxonomy

Combined with today's spec 003.5 + spec 004 retrospectives:

| Filter | Default | Empirical support | Caveat |
|---|---|---|---|
| A3 momentum (bear suppression) | ON @ -5% | +0.70pp Δα at -5% over 43 UW commits | In-sample motivated; not separately ablated |
| Spec 003 contrarian (bull, per-ticker) | ON @ 80% | +0.65pp Δα at 80% over 11 eligible commits | Tiny sample; INTC hypothetical risk |
| Spec 003.5 sector-baseline fallback | ON | Cold-start tickers gated when same-sector pool ≥ 20 | Doesn't help SC-003 Financials cohort |
| Spec 004 sector-momentum (bull, sector-ETF) | OFF | -0.45pp Δα at -5% across 73 commits | Anti-predictive in our corpus regimes |

Three of the four are default-on but only one (A3) has > 30 supporting data points. The framework's filter portfolio is empirically shaky in absolute terms — a multi-window corpus expansion would significantly strengthen the basis for current defaults.

## Reproducibility

```
python scripts/contrarian_gate_threshold_sweep.py --thresholds 75,80,85,90,95 --history-floor 20
```

Reads from `~/.tradingagents/logs/<ticker>/TradingAgentsStrategy_logs/`
+ spec 002 sectors cache + yfinance for realized α. No LLM cost.
