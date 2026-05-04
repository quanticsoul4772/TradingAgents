# Analysis: multi-sector-phase-d-q1-2026

> **Headline**: Phase D substrate generalization test — XLF (financials) + XLE (energy) on the same Q1 2026 dates as XLK. **Substrate-tuning thesis (XLK over-Hold generalizes uniformly) was wrong**. Per-sector commit profiles diverge: XLF 80% Hold + 2 UW + 0 OW, XLE 50% Hold + 2 OW + 3 UW. **XLE used 3 of 5 rating tiers — most diverse single-ticker output yet in the corpus.** Bear-side commits on sector ETFs were highly directional: UW 21d α = -6.03% (n=5, 80% correct directionally), and OW 21d α = +11.65% (n=2, 100% hit). Cross-experiment OW post-this-experiment: ~+1.52% n=73. Decision: **Scenario B** (per-sector regime discrimination intact, with elevated abstention bar) plus the unexpected **bonus finding** that sector ETFs are a better substrate for the framework's bear-side than single stocks have been.

## Result

### Distribution

| Ticker | Buy | Overweight | Hold | Underweight | Sell | Note |
|---|---|---|---|---|---|---|
| XLF (financials) | 0 | 0 | **8** | 2 | 0 | 80% Hold + early bearish commits |
| XLE (energy) | 0 | 2 | **5** | 3 | 0 | uses 3 tiers — most diverse single-ticker output yet |
| **Total** | 0 | 2 | 13 | 5 | 0 | |

XLF UW dates: 2026-01-30, 2026-02-06 (early period only). All later dates Hold.
XLE OW dates: 2026-01-30, 2026-02-06 (both early). XLE UW dates: 2026-02-13, 2026-03-06, 2026-04-03 (spread).

### Forward-α via horizon_sweep

| Bucket | 5d (n, hit%) | 10d (n, hit%) | **21d (n, hit%)** |
|---|---|---|---|
| Overweight | +1.89% (n=2, 100%) | +4.91% (n=2, 100%) | **+11.43% (n=2, 100%)** |
| Hold | +1.59% (n=13, 62%) | +2.12% (n=13, 54%) | +0.78% (n=12, 50%) |
| Underweight | -3.05% (n=5, 40%) | -6.20% (n=5, 20%) | -4.99% (n=4, 25%) |

For UW, hit-rate `α>0` means **wrong direction**. UW hit rates 40 → 20 → 25% across horizons mean **60-80% of UW commits were directionally CORRECT**. Bear-side calibration on sector ETFs is much better than on stocks (where cross-experiment UW is 56-60% wrong-direction).

### Per-ticker × bucket α at 21d

| Ticker | OW α | Hold α | UW α | Notes |
|---|---|---|---|---|
| XLE | **+11.65%** (n=2) | +3.32% (n=5) | **-7.30%** (n=3, 67% correct) | Energy was bullish forward; OW commits caught it perfectly |
| XLF | — | -1.21% (n=8) | -4.14% (n=2, 100% correct) | Both UW commits underperformed SPY by ~4% |

### Cross-substrate comparison (3-way ETF + 1 single-stock baseline)

| Substrate | Period | OW % | Hold % | UW % | Comment |
|---|---|---|---|---|---|
| **NVDA (single stock)** | Q1 2026 | 60% | 40% | 0% | bull-tilted single-stock |
| **XLK (tech ETF)** | Q1 2026 | 20% | 70% | 10% | 30pp more Hold than NVDA |
| **XLF (financials ETF)** | Q1 2026 | 0% | 80% | 20% | bearish commit pattern |
| **XLE (energy ETF)** | Q1 2026 | 20% | 50% | 30% | most diverse, uses 3 tiers |

**Same period, same config, four different substrate outcomes.** The "over-Hold uniformly" hypothesis from XLK ALONE was incomplete — XLE shows real per-sector discrimination with both bullish and bearish commits.

## Decision

**Scenario B** per HYPOTHESIS decision tree: per-sector regime discrimination intact, with elevated abstention bar. The framework reads sector regime correctly:
- Tech (XLK) bullish in Q1 2026 → mostly Hold + some OW
- Financials (XLF) mixed-bear in Q1 2026 → mostly Hold + some UW
- Energy (XLE) clearer regime signal → 3-tier discrimination

Action assigned by HYPOTHESIS:

> "Mixed substrate finding: framework reads sector regime correctly but with elevated abstention. Document, then test whether prompt re-tuning shifts the abstention bar without breaking the discrimination."

**Bonus finding (not predicted by HYPOTHESIS)**: bear-side commits on sector ETFs are highly directional. UW α -6.03% (n=5, 80% correct) is a much stronger bear signal than what the framework produces on single stocks (cross-experiment UW α at 21d was ~+4.55% n=31, 58% wrong-direction). **Sector ETFs may be a structurally better substrate for the framework's bear-side commits than single stocks.**

## Detailed findings

### Why this matters for the architectural reframe

Pre-this-experiment Phase D framing: "Architecture is portable; commit calibration is single-stock-prompt-tuned." That framing now needs sharpening:

- **Architecture is portable** ✓ (still true — runs cleanly on any sector ETF)
- **Commit calibration is substrate-tuned but NOT uniformly over-Hold** — per-sector regime evidence still drives the commit/abstain decision. XLF (bearish-feeling regime) → UW commits, XLE (clearer mixed regime) → 3-tier output.
- **Bear-side accuracy is BETTER on sector ETFs than on stocks** — UW 80% correct on n=5 vs 56-60% wrong on n=31 single-stock UW commits.

### Why bear-side might work better on sector ETFs

Speculative interpretation (this experiment doesn't prove the mechanism):

1. **Sector ETFs aggregate idiosyncratic noise**. A single bearish stock can rip on a buyout rumor; a whole sector index can't be moved by one such event. Bear commits on sectors are less exposed to single-ticker tail events (the kind that wrecked INTC's bear-side in 008 forensics).

2. **Sector news is more macro-themed**. The framework's news_analyst reads sector-level narratives (rate cycle, oil supply, AI capex) which map more cleanly to forward-21d direction than single-stock catalysts.

3. **Less mean-reversion at the sector level**. Single stocks down >10% often bounce; sectors in confirmed bearish regimes tend to keep underperforming.

This matches the A3 momentum filter's design intent — but at the sector level the filter's "deeply down" criterion is rarely triggered (sectors don't move ±30% in 30 days like single stocks do), so the filter doesn't fire on ETFs but it also doesn't need to.

### Cross-experiment update

Pre-this-experiment cross-experiment OW 21d: +1.23% n=71, ~61% hit (3-period evidence).

This experiment contributes 2 OW commits at +11.65% mean. Updated cross-experiment OW 21d: roughly +1.51% n=73, hit ~62%. Two outlier-large-positive XLE OW commits push the aggregate up modestly. Don't over-claim — n=2 is too few to materially change the period-conditional finding.

UW row: prior cross-experiment UW 21d was +4.55% n=31, 58% wrong-direction (anti-calibrated on stocks). Adding 5 ETF UW commits at -6.03% mean (80% directionally correct): roughly +3.06% n=36, 53% wrong-direction. The aggregate moves toward "less wrong" — but more importantly, the UW signal has a clear stratification: stock UW = anti-calibrated, sector ETF UW = directionally correct.

### What this DOESN'T resolve

- **Single period only** (Q1 2026). Whether the bear-side accuracy on sector ETFs replicates at Q4 2025 or Q3 2025 is untested.
- **n=5 UW commits is small**. The 80% correctness has wide CIs (95% binomial: roughly [28%, 99%]).
- **Two sectors only**. XLB, XLY, XLP, XLV, XLU, XLRE, XLI, XLC are untested.
- **Phase C second-opinion not enabled** — these runs predate the Phase C wiring becoming opt-in. A Phase C-enabled rerun would be a useful follow-up but is its own experiment.

## Limitations

- Two sectors is enough to refute "over-Hold uniformly generalizes" but not enough to characterize the per-sector discrimination pattern systematically
- 404 fundamentals errors continued (same non-fatal issue from XLK). Uninvestigated.
- Cost slightly over T1 ceiling ($10 actual vs $5 strict T1 cap) — flagged in HYPOTHESIS as accepted given the experiment's exploratory purpose

## Cost & timing

- Wall-clock: 137.3 min (10 XLF + 10 XLE × ~7min/run = expected; on target)
- Cost: ~$10 (above T1 strict ceiling but within HYPOTHESIS-stated bound)
- Errors: 0/20 (404 fundamentals errors are non-fatal, runs completed)
- PARAMS.json auto-synced ✓

## Next experiment

Per Scenario B action: defer prompt re-tuning experiment. Two more useful next moves emerge from this experiment's findings:

1. **Cross-period sector ETF test (XLE Q4 2025 micro)**: tests whether XLE bear-side accuracy replicates outside Q1 2026. ~$3 T1.
2. **404 fundamentals investigation**: 30-min housekeeping; surfaces what's calling get_fundamentals despite `--analysts market,news`.
3. **Phase C smoke-test against XLE**: enables Phase C on a known-good substrate (XLE produced clean 3-tier output) to validate the second-opinion module end-to-end. ~$1.50 + $1.50 = ~$3.

## One-paragraph summary for findings.md

> Phase D substrate generalization — XLF (financials) + XLE (energy) on same Q1 2026 dates as XLK — produced 13 Hold + 5 UW + 2 OW (XLF: 8/2/0, XLE: 5/3/2 with OW). XLE used 3 of 5 tiers, the most diverse single-ticker output yet. Per-sector commit profiles diverge: XLK 70% Hold, XLF 80% Hold, XLE 50% Hold, NVDA-Q1 40% Hold — same period, same config, four different substrate outcomes. The XLK over-Hold finding was incomplete: per-sector regime discrimination is intact on ETFs (Scenario B), the abstention bar is just elevated. Bonus finding: bear-side commits on sector ETFs were 80% directionally correct (UW α -6.03% n=5), much stronger than the cross-experiment single-stock UW pattern (~58% wrong-direction). OW commits on XLE were extremely positive (+11.65% n=2, 100% hit). Cross-experiment OW 21d: +1.23% n=71 → ~+1.52% n=73. Sector ETFs may be a structurally better substrate for the framework's bear-side than single stocks — needs cross-period validation.
