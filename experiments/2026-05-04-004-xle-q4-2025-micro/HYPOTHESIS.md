# Hypothesis: xle-q4-2025-micro

**Experiment ID**: `2026-05-04-004-xle-q4-2025-micro`
**Created**: 2026-05-04
**Source idea**: Cross-period validation of sector-ETF bear-side accuracy finding from 003 — XLE-only at Q4 2025 dates
**Cost estimate**: ~$3.00
**Cost tier**: T1 (free exploration, $0 – $5)

## What we're testing

Cross-period validation of the **sector-ETF bear-side accuracy finding** from `2026-05-04-003-multi-sector-phase-d-q1-2026`. That experiment found UW commits on sector ETFs were 80% directionally correct (n=5, mean α -6.03%) — much stronger than the cross-experiment single-stock UW pattern (~58% wrong-direction). The finding was based on Q1 2026 data only. **Knob varied**: calendar period (Q1 2026 → Q4 2025). All other config matched: same XLE ticker, same Opus + Haiku + A3 filter + exa + `--analysts market,news` + 1 round. **Grid**: 10 weekly Fridays 2025-11-07 → 2026-01-09 (matching 008 cross-period dates).

## Why we expect bear-side stability evidence either way

The Q1 2026 XLE finding (3 UW commits, all directionally correct, mean α -7.30%) was either:
- A real cross-period pattern of bear-side accuracy on sector ETFs → Q4 2025 XLE should show similar UW directionality
- A Q1-2026-specific outcome → Q4 2025 might show very different bear-side commit accuracy

The Bayesian-like update from this experiment:
- Prior: bear-side ETF accuracy is real (P ≈ 0.55, weak prior given n=5 only)
- If Q4 2025 UW commits are also directionally correct (≥60%) → posterior climbs toward 0.7+
- If Q4 2025 UW commits are mixed (~50% correct) → posterior stays near 0.5, claim weakens
- If Q4 2025 has zero UW commits → no update on UW side; experiment then tests just the regime-discrimination claim

## Predicted findings

**Scenario A (bear-side accuracy replicates)** — ~40%
- ≥2 UW commits with mean α ≤-2% (directionally correct)
- Posterior on "ETF bear-side accuracy is real" climbs to ~0.7
- Sector-ETF bear-side claim becomes load-bearing for Phase D direction

**Scenario B (commit pattern reflects regime, not bear-side accuracy)** — ~30%
- 1-3 UW + maybe some Hold + maybe some OW (varied by Q4 2025 energy regime)
- UW α direction less consistent than Q1 2026
- Bear-side accuracy claim may be Q1-2026-specific

**Scenario C (mostly Hold or mostly OW)** — ~20%
- 0-1 UW commits (Q4 2025 energy may have been bullish)
- Bear-side accuracy claim untestable from this run; need a different bearish-period sector instead

**Scenario D (basic operational issue)** — ~10%
- 404 fundamentals errors (known) cause meaningful issue, OR
- Q4 2025 XLE data has gaps, OR
- Run fails on some date

## Success criterion

- [ ] 10 propagations complete with ≤1 error
- [ ] XLE Q4 2025 distribution tabulated against XLE Q1 2026 (003)
- [ ] horizon_sweep on the new CSV
- [ ] If ≥2 UW commits: bear-side α direction reported
- [ ] Decision per scenario A/B/C/D
- [ ] Total cost ≤ $5

## Notes

- **T1 tier** ($3 estimated, well within ≤$5 ceiling)
- **Same Q4 2025 date grid as 008** (2025-11-07 → 2026-01-09 weekly Fridays) — comparable to the period that produced the cross-experiment posterior dip
- **`--analysts market,news`** (no fundamentals — XLE is an ETF; same config as 002 + 003)
- **A3 filter ON** at -5%/30d (matches all prior Phase D ETF experiments)
- **Forward-21d data**: full coverage through ~2026-02-09; well within current data window
- **Memory log fresh**

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (bear-side replicates) | Sector-ETF bear-side claim load-bearing. Update RESEARCH_FINDINGS Phase D. Plan multi-period multi-sector ETF experiment to formalize ($30 T3 candidate). |
| Scenario B (regime-driven, not bear-accuracy) | Document as "ETF commit calibration regime-driven; bear-side accuracy on Q1 2026 was period-favored." Phase D still useful but bear-side claim narrower. |
| Scenario C (mostly Hold/OW) | XLE wasn't bearish in Q4 2025; need a different bear-correct ETF (XLF Q4 2025? XLU Q4 2025?). Re-test against another sector. |
| Scenario D (operational) | Document failure mode; fix and re-run. |

## Related experiments

- **2026-05-04-003-multi-sector-phase-d-q1-2026**: XLE Q1 2026 produced 5 Hold + 2 OW + 3 UW; bear-side UW α = -7.30% n=3 (67% correct). Source of the bear-side ETF finding being tested.
- **008 opus47-cross-period (NVDA Q4 2025)**: same Q4 2025 date grid, single-stock substrate. 9 OW + 1 Hold, no UW.
- **2026-05-04-001-nvda-q3-2025-micro**: same micro-pilot pattern (T1, 10 dates, single ticker)
- **Cross-experiment OW 21d**: +1.52% n=73, posterior 0.63 (separate from this experiment's bear-side question)
