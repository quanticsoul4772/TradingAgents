# Spec 003.5 validation against SC-003 Financials cohort — 2026-05-06

**Question**: does the spec 003.5 sector-baseline fallback close the cold-start gap surfaced by today's Financials investigation (`claudedocs/sc003-financials-gate-check-2026-05-06.md`)?

**Method**: re-run `scripts/sc003_financials_gate_check.py` with `--sector-fallback` (spec 003.5 enabled, default) and `--no-sector-fallback` (spec 003 baseline). Same 5 Financials Overweight commits from SC-003 (2026-04-03). Sector lookup via `tradingagents/paper/sectors.py` yfinance cache; pool aggregated from state logs across all same-sector tickers strictly before SC-003 date.

## Result

### Spec 003 baseline (`--no-sector-fallback`)

```
Sector pool: N/A (fallback disabled)

| Ticker | OW α   | bull_kw | per-ticker N | per-ticker pct | gate_baseline | would_fire |
| JPM    | -5.12% |  55     |  13          | 92%            | none          | no         |
| BAC    | -3.73% |  65     |  0           | n/a            | none          | no         |
| WFC    | -12.23%|  48     |  0           | n/a            | none          | no         |
| GS     | -3.74% |  46     |  0           | n/a            | none          | no         |
| MA     | -10.55%|  50     |  0           | n/a            | none          | no         |

Gate fires: 0/5
```

### Spec 003.5 with sector fallback (`--sector-fallback`)

```
Sector pool (Financial Services): N=13, contributors={'JPM': 13}

| Ticker | OW α   | bull_kw | per-ticker N | sector N | sector pct | gate_baseline | would_fire |
| JPM    | -5.12% |  55     |  13          |  13      |  92%       | none          | no         |
| BAC    | -3.73% |  65     |  0           |  13      | 100%       | none          | no         |
| WFC    | -12.23%|  48     |  0           |  13      |  62%       | none          | no         |
| GS     | -3.74% |  46     |  0           |  13      |  54%       | none          | no         |
| MA     | -10.55%|  50     |  0           |  13      |  77%       | none          | no         |

Gate fires: 0/5
```

## Verdict

**Spec 003.5 does NOT help on this cohort either, for two compounding reasons.**

### Reason 1: sector pool itself below floor

Of the 5 Financials Overweight commits, only JPM had any prior framework history (N=13). The remaining 4 (BAC/WFC/GS/MA) had zero per-ticker history (which spec 003.5 was designed to address) but the resulting Financials sector pool aggregates to N=13 — all from JPM, the only contributor — which is **below the FR-003 sector floor of N≥20**.

The fallback is structurally well-defined; it just doesn't have enough fuel.

### Reason 2: even hypothetically lowering the sector floor wouldn't help

If we relaxed the sector floor to N≥10 (just below the actual N=13), only JPM (92nd percentile) and BAC (100th) would cross the 80% firing threshold. The other 3 — the actual big losers (WFC -12.23%, MA -10.55%, GS -3.74%) — sit at 62%/77%/54% of the JPM-derived pool, BELOW the firing threshold.

Suppressing JPM + BAC (the LEAST-wrong of the 5 at -5.12% and -3.73%) would WORSEN the bucket: survivor mean = (-12.23 + -3.74 + -10.55) / 3 = **-8.84%** vs baseline -7.07% → **Δα = -1.77pp** (gate makes things worse).

## What this means

**The Financials losers in SC-003 had MODERATE bull_keyword_counts (46–50, near the JPM median of 55), not high-percentile ones.** Their losses came from a different mechanism than the within-ticker bull-prose mean-reversion that finding #4 + spec 003 are built to catch.

> **CORRECTION (added 2026-05-06 evening, after spec 004 SC-008 validation in `claudedocs/spec-004-sc008-validation-2026-05-06.md`)**: this section originally said "likely a sector-wide regime move (Financials underperformed the SPY benchmark by ~7% in this 21d window)." That was a **misread**. The "-7%" figure was the per-ticker α-vs-SPY mean (which is what we measure for individual ratings), not sector-vs-SPY. Direct yfinance check at the SC-003 trade date: **XLF was UP +4.14% in the 21d window after 2026-04-03**, and was only -4.54% in the prior 30 trading days. The actual mechanism for the Financials losses was **per-ticker underperformance vs a rising sector** — neither sector-rotation nor within-ticker prose-density. Spec 004 (sector-momentum filter) was built against this misread premise; SC-008 falsified it for this cohort. The general spec 004 mechanism is still empirically reasonable for genuine sector-rotation cohorts, but the SC-003 Financials cohort isn't one of them. See the spec 004 validation doc for the full unwinding.

The contrarian gate's `bull_keyword_count` mechanism is calibrated against **prose-density-driven** mean-reversion. It does not catch per-ticker-α-vs-rising-sector losses (the actual SC-003 Financials mechanism). Spec 003.5 widens the data pool but doesn't change the mechanism.

### Implications for spec 003.5's value calculation

The +6.46% retrospective Δα number (`claudedocs/contrarian-gate-retrospective-2026-05-05.md`) was earned almost entirely on tickers (NVDA, AAPL) where:
1. Per-ticker history was thick enough (≥20)
2. The losing-OW failure mechanism WAS within-ticker bull-prose mean-reversion (consistent with finding #4)

Spec 003.5 extends spec 003's reach to **cold-start tickers in sectors with thick history** — but the SC-003 Financials cohort has neither. So the empirical motivator for spec 003.5 (this Financials cohort) is not actually addressed by spec 003.5.

This isn't a spec 003.5 design failure. The spec was correctly motivated by "gate has zero coverage on cold-start tickers" and the implementation correctly extends coverage when there's same-sector data to extend it onto. The Financials cohort just falls into the harder-still failure mode: **cold-start universe** (almost no same-sector accumulation) with **mechanism mismatch** (per-ticker-α-vs-rising-sector, not within-ticker bull-prose). [Per-ticker-α-vs-rising-sector was misidentified as "sector regime" in the original version of this doc; corrected after spec 004 SC-008 validation.]

### Implications for product framing

- For mature universes (NVDA/AAPL/etc with months of history), spec 003 fires + helps directly.
- For cold-start universes WITH dense same-sector history (e.g., adding a new tech ticker to a portfolio that's been running on 10+ tech tickers for months), spec 003.5 fires + helps.
- For cold-start universes WITHOUT same-sector accumulation (the SC-003 Financials case), neither spec 003 nor spec 003.5 fires. Spec 004 (sector-momentum filter) was built thinking it would address this — but its SC-008 validation showed XLF wasn't actually in the mean-reversion zone the filter is calibrated for. The actual SC-003 Financials mechanism (per-ticker-α-vs-rising-sector) is a fourth distinct failure mode no current filter catches. See `claudedocs/spec-004-sc008-validation-2026-05-06.md` for the unwinding.

## What we'd do next (research-track ideas)

If sector-rotation-loss prevention becomes a priority:
1. **Sector-momentum filter**: when a sector ETF (XLF for Financials) is in mean-reversion zone analogous to A3 for individual tickers, suppress same-sector bullish commits.
2. **SPY-relative regime detector**: when target ticker's sector is underperforming SPY in the prior 30d window, treat bullish commits as higher-risk.
3. **Cross-sector pool when same-sector unavailable**: relax the spec 003.5 ladder further — when same-sector pool is below floor, fall back to ALL-tickers pool. Probably has worse calibration but extends coverage to the absolute-cold-start case.

None of these are urgent. The product surface already (via Constitution VII calibrated abstention) defaults to Hold on weak evidence — the SC-003 Financials losses came from the framework being CONFIDENT about Buy/OW it shouldn't have been confident about, not from mode collapse.

## Reproducibility

```
python scripts/sc003_financials_gate_check.py --no-sector-fallback
python scripts/sc003_financials_gate_check.py --sector-fallback
```

Reads from `~/.tradingagents/logs/<ticker>/TradingAgentsStrategy_logs/full_states_log_<date>.json`. Uses spec 002 paper-harness sectors cache at `~/.tradingagents/paper/sectors.json` for sector lookup. No LLM cost.
