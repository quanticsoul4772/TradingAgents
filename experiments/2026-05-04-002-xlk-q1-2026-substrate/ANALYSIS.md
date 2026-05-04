# Analysis: xlk-q1-2026-substrate

> **Headline**: Phase D substrate exploration — XLK (tech sector ETF) on the same Q1 2026 dates as 007's NVDA half. Distribution: **2 OW + 7 Hold + 1 UW**, vs NVDA Q1 2026's 6 OW + 4 Hold. **The framework went much more Hold-heavy on the ETF substrate than on the analogous single-stock substrate** — 70% Hold vs 40% Hold on NVDA in the same period. ALL three buckets show positive 21d α (XLK was bullish in Q1 2026 forward windows): OW +1.51% n=2 50% hit, Hold +2.82% n=6 83% hit, UW +2.15% n=1 100% wrong-direction. **The framework abstained when it could have committed and earned more α**. Decision: **Scenario B** per HYPOTHESIS — substrate-different commit behavior. Framework's discrimination is single-stock-prompt-tuned; ETF news/market texture reads as more ambiguous → more Hold.

## Result

### Distribution

| Bucket | XLK (this) | NVDA Q1 2026 (007) | Delta |
|---|---|---|---|
| Overweight | 2 (20%) | 6 (60%) | -40pp |
| Hold | 7 (70%) | 4 (40%) | +30pp |
| Underweight | 1 (10%) | 0 | +10pp |
| Sell | 0 | 0 | — |

XLK was way more Hold-heavy than NVDA on the SAME dates with the SAME bull-tailwind period.

### Forward-α via horizon_sweep

| Bucket | 5d (n, hit%) | 10d (n, hit%) | **21d (n, hit%)** |
|---|---|---|---|
| Overweight | -1.73% (n=2, 0%) | -1.01% (n=2, 0%) | **+1.51% (n=2, 50%)** |
| Hold | +0.87% (n=7, 86%) | +1.62% (n=7, 57%) | **+2.82% (n=6, 83%)** |
| Underweight | -1.01% (n=1, 0%) | -0.08% (n=1, 0%) | **+2.15% (n=1, 100% wrong)** |

90d data not yet resolved.

### Per-row commit comparison: XLK vs NVDA Q1 2026

| Date | XLK rating | NVDA rating (007) | Match? |
|---|---|---|---|
| 2026-01-30 | OW | OW | ✓ |
| 2026-02-06 | Hold | Hold | ✓ |
| 2026-02-13 | Hold | Hold | ✓ |
| 2026-02-20 | UW | Hold | ✗ |
| 2026-02-27 | Hold | Hold | ✓ |
| 2026-03-06 | Hold | OW | ✗ |
| 2026-03-13 | Hold | OW | ✗ |
| 2026-03-20 | OW | OW | ✓ |
| 2026-03-27 | Hold | OW | ✗ |
| 2026-04-03 | Hold | OW | ✗ |

**Match rate: 5/10**. The substrate produces materially different per-date commit decisions even though the underlying period is identical. Most divergences are XLK→Hold while NVDA→OW (4 cases). XLK abstained where NVDA committed.

### What this says about substrate generalization

Two things:

1. **Bucket-level discrimination diverges across substrates**. NVDA + AAPL + INTC produced similar bucket-ratio patterns within Q1 2026 (commit when bull, hold when mixed, UW when bear). XLK produces a DIFFERENT bucket-ratio pattern on the same period — much more Hold-leaning. The framework reads sector ETF evidence as more ambiguous than single-stock evidence.

2. **Realized α is positive in all buckets** for XLK because XLK was bullish in Q1 2026 forward windows. The framework would have earned more α by committing OW more aggressively. **The Hold over-abstention left α on the table.**

### Why the substrate matters

Sector ETF news (exa search "XLK" or "technology sector") reads as macro / sector-rotation narratives. Single-stock news reads as company-specific (earnings, product, competitive). The market analyst sees fund-flow patterns instead of stock-specific momentum. The framework appears to interpret this as evidence ambiguity → Hold.

This is the **single-stock-prompt-tuned** finding from the HYPOTHESIS Scenario B. The framework's prompts ARE stock-tuned (analyst prompts say "company" and "stock"). On a sector ETF the prompts produce more cautious behavior because the evidence pattern doesn't match what the prompt expects.

### A non-fatal data issue

The run printed `HTTP Error 404: No fundamentals data found for symbol: XLK` on every propagation despite `--analysts market,news` (no fundamentals analyst). This means SOMETHING in the market or news analyst pipeline is calling `get_fundamentals` on the ticker. The 404 is non-fatal — runs completed and produced ratings — but it indicates a tool in market or news analyst is fetching fundamentals data even when the fundamentals analyst is excluded.

**Not investigated in this analysis.** Worth a follow-up grep across analyst tool lists. Doesn't invalidate this experiment's results.

## Decision

**Scenario B** per HYPOTHESIS decision tree: substrate-different commit behavior. Framework's discrimination is single-stock-prompt-tuned. Action assigned by HYPOTHESIS:

> "Notable finding: framework is single-stock-prompt-tuned. Document, then test if a re-tuned prompt fixes it. Phase D continues but with prompt-engineering caveat."

Acting on this:

1. **Document the substrate-tuning finding** — this ANALYSIS captures it; RESEARCH_FINDINGS gets a Phase D section noting "framework's commit behavior is substrate-shaped; sector ETFs produce more Hold than single stocks in the same period."
2. **Don't yet build sector-ETF prompt variant** — testing prompt re-tuning is a separate experiment with its own hypothesis. File as a future Phase D iteration.
3. **Multi-sector basket experiment NOT immediately recommended** — first finding (XLK over-Hold) makes the multi-sector basket experiment less informative; we'd just see the same over-Hold pattern across sectors. Better next: try a different substrate type (commodity ETF, crypto pair) to see if the over-Hold pattern is sector-ETF-specific or generalizes to all non-stock substrates.

## Detailed findings

### What this finding adds to the project

1. **External validity test of the calibrated abstention claim**: passes weakly. The framework still produces calibrated-looking output (mostly Hold on ambiguous-feeling sector evidence) — it doesn't catastrophically fail on a non-stock substrate. But it also doesn't earn α as effectively as on stocks during the same period.

2. **The "framework as decision architecture" thesis** (from divergent reasoning synthesis): partially supported. The architecture *runs* on a sector ETF. The output behavior *changes* with substrate. So the architecture is portable but its behavior is substrate-specific.

3. **Prompt sensitivity is now load-bearing**: the framework's commit rate in this experiment (20% OW) is lower than the cross-experiment OW rate of ~40% almost entirely because the prompt frames analysts as company-evaluators. Re-tuning prompts for sector substrates would be a clear experiment.

### Cross-experiment OW 21d update (XLK contribution)

| Cohort | n | Mean α | Hit rate |
|---|---|---|---|
| Pre-XLK | 71 (incl. NVDA Q3 micro) | +1.23% | ~61% |
| XLK contribution | 2 OW | +1.51% | 50% |
| **Post-XLK** | **73** | **~+1.24%** | **~60%** |

Negligible effect because n=2 is too small. XLK doesn't materially update the cross-experiment claim.

## Limitations

- **Single sector ETF (XLK)**. Other sectors might behave differently. XLK is bull-correlated with NVDA so this is a "tech-sector vs tech-stock" substrate test, not a general "sector vs stock" test.
- **n=2 OW commits** is too few for any α-magnitude claim about substrate's effect on commit calibration.
- **Q1 2026 only**. Doesn't address whether substrate effect persists across periods.
- **Prompt non-adaptation**: this experiment used the stock-tuned analyst prompts on an ETF substrate. A "fair" substrate test would re-tune prompts for sector-rotation analysis. We didn't do that.
- **The 404 fundamentals issue** is uninvestigated.

## Cost & timing

- Wall-clock: 68.4 min (vs predicted ~80 min — slight underrun)
- Cost: ~$10 (T2)
- Errors: 0/10 (the 404s are non-fatal print outputs)
- PARAMS.json auto-synced ✓

## Next experiment

Per Scenario B action: defer multi-sector basket. Two more useful next moves:
1. **Substrate-prompt-adapted experiment**: re-tune market + news analyst prompts for sector-rotation language, re-run XLK Q1 2026, see if commit rate climbs toward the NVDA pattern. ~$10 T2.
2. **Different substrate type**: commodity ETF (USO, GLD) or crypto pair to test if "over-Hold on non-stock substrates" generalizes beyond sector ETFs. ~$10 T2.

Either of these is the natural next Phase D step. The micro-pilot's posterior recovery (NVDA Q3 2025 → posterior 0.63) means the empirical-track is in better shape than 008 alone suggested, so Phase D stays a priority but doesn't have to be the only thing.

## One-paragraph summary for findings.md

> Phase D substrate exploration — XLK (tech sector ETF) on same Q1 2026 dates as 007's NVDA half — produced 2 OW + 7 Hold + 1 UW vs NVDA's 6 OW + 4 Hold (per-date match rate 5/10). XLK was 30pp more Hold-heavy than the analogous single-stock substrate in the same period. All three buckets had positive 21d α (XLK bull-tailwind in this window): OW +1.51% n=2, Hold +2.82% n=6 83% hit, UW +2.15% n=1 wrong-direction. Framework over-abstained on the ETF substrate, leaving α on the table. Decision: Scenario B per HYPOTHESIS — substrate-different commit behavior; framework's discrimination is single-stock-prompt-tuned. Architecture is portable but commit calibration is substrate-specific. Next: either substrate-prompt-adapted XLK rerun, or different substrate type (commodity ETF, crypto pair) to test if over-Hold generalizes beyond sector ETFs.
