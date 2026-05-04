# Hypothesis: nvda-q3-2025-micro

**Experiment ID**: `2026-05-04-001-nvda-q3-2025-micro`
**Created**: 2026-05-04
**Source idea**: B-priority 2b micro-pilot per post-008 mcp-reasoning ranking — NVDA-only Q3 2025 to disambiguate Q1'26 vs Q4'25 vs Q3'25
**Cost estimate**: ~$3.00
**Cost tier**: T1 (free exploration, $0 – $5)

## What we're testing

Cross-period micro-pilot: same Opus 4.7 + Haiku 4.5 + A3 filter + exa + 3 analysts + 1 round config as 007 + 008, on NVDA only at Q3 2025 dates (2025-08-01 → 2025-10-10, 10 weekly Fridays). 10 propagations total. Tests whether NVDA's Q4 2025 OW α flat result (-0.47% n=9) was period-specific or persistent across multiple non-Q1-2026 windows.

## Why we expect signal-stability evidence either way

NVDA is the highest-signal ticker in the corpus and drives the bull-α claim. Q1 2026 NVDA produced +4.36% OW α (007); Q4 2025 NVDA produced -0.47% (008). A third NVDA observation at Q3 2025 produces a 3-way comparison that sharpens the period-conditional Bayesian posterior (currently 0.52).

## Predicted findings

**Scenario A (Q3 2025 NVDA OW α positive, ≥+1%)** — ~35%
- Posterior climbs back toward 0.6
- Q1 2026 looks less like an outlier; signal claim recovers some strength

**Scenario B (Q3 2025 NVDA OW α near zero, ±0.5%)** — ~40%
- Posterior stays around 0.45-0.5
- Signal genuinely period-randomly-distributed; weak case for retirement

**Scenario C (Q3 2025 NVDA OW α negative, ≤-1%)** — ~25%
- Posterior drops toward 0.4
- Q1 2026 was the bull-favored outlier; load-bearing claim further weakened

## Success criterion

- [ ] 10 propagations complete with 0 errors
- [ ] NVDA OW commit count + 21d α reported
- [ ] horizon_sweep on the new CSV
- [ ] Bayesian posterior update via `mcp-reasoning reasoning_evidence` with 008's 0.52 as prior
- [ ] Three-way comparison table: Q3'25 (this) vs Q4'25 (008) vs Q1'26 (007)
- [ ] Decision per scenario A/B/C
- [ ] Total cost ≤ $5

## Notes

- T1 tier: no Cost-Justification scaffold required (cost ≤ $5).
- Single-ticker micro-pilot is the cheapest way to add cross-period evidence on the highest-signal ticker.
- Q3 2025 dates have full forward-21d data available (we are at 2026-05-04).
- A3 filter ON to match 007/008 config exactly.
- Memory log fresh per experiment.

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (Q3 positive) | Cross-experiment update + RESEARCH_FINDINGS edit. Plan full 30-pair Q3 validation as B-priority 2c at T2. Posterior climbs. |
| Scenario B (Q3 near zero) | Strong signal-retirement evidence. Update Constitution VII; reframe project around calibrated abstention only. |
| Scenario C (Q3 negative) | Q1 2026 was the outlier. Load-bearing claim further weakened. Pivot to Phase D substrate exploration. |

## Related experiments

- **007 opus47-30pair-mixed (Q1 2026)**: NVDA OW 21d α = +4.36% n=6
- **008 opus47-cross-period (Q4 2025)**: NVDA OW 21d α = -0.47% n=9
- **This experiment (Q3 2025)**: fills the third corner of the Q3'25-Q4'25-Q1'26 triangle
