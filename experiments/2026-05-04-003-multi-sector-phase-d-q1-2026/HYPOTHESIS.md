# Hypothesis: multi-sector-phase-d-q1-2026

**Experiment ID**: `2026-05-04-003-multi-sector-phase-d-q1-2026`
**Created**: 2026-05-04
**Source idea**: Phase D substrate generalization — XLF + XLE on same Q1 2026 dates as XLK to test if over-Hold finding generalizes across sectors
**Cost estimate**: ~$6.00 (note: T1 ceiling is $5; this experiment is at the T1/T2 boundary — accepted because the underlying scope is still exploratory)
**Cost tier**: T1 (free exploration)

## What we're testing

Phase D substrate generalization: do other sector ETFs reproduce the XLK over-Hold finding from `2026-05-04-002-xlk-q1-2026-substrate`? Same config as the XLK experiment (Opus + Haiku + A3 filter + exa + `--analysts market,news` + 1 round) on **two new sector ETFs** at the **same Q1 2026 dates** (2026-01-30 → 2026-04-03, 10 weekly Fridays). 20 propagations total (10 per ticker).

**Substrate choice**: XLF (financials, neutral-to-mixed regime in Q1 2026) and XLE (energy, often counter-cyclical to tech). These cover regime variation that XLK didn't — XLK was tech-bull-correlated, mirroring NVDA. XLF + XLE test whether over-Hold is a sector-ETF property or specifically a tech-sector property.

## Why we expect substrate generalization evidence either way

The XLK experiment found that the framework went 30pp more Hold-heavy on a sector ETF than on the analogous single-stock substrate (NVDA) in the same period. The hypothesis was: framework's prompts are single-stock-tuned, ETF news/market texture reads as more ambiguous → more Hold.

If that hypothesis is right, XLF + XLE should ALSO be Hold-heavy (~60-80% Hold each). If wrong, XLF or XLE could produce different distributions (e.g., XLE could produce UW commits if energy news reads as bear, or XLF could produce OW commits if banking news is clearly bullish).

## Predicted findings

**Scenario A (over-Hold generalizes — both ETFs Hold-heavy)** — ~50%
- XLF: ≥60% Hold
- XLE: ≥60% Hold
- Confirms substrate-tuning thesis. Phase D follow-up: prompt re-tuning experiment.

**Scenario B (per-sector regime discrimination)** — ~30%
- XLF: Hold-leaning (banking was mixed in Q1 2026)
- XLE: UW-leaning OR OW-leaning depending on energy regime
- Different commit pattern per sector indicates the framework IS reading sector evidence directionally — just with a higher abstention bar than on single stocks
- Substrate-tuning thesis partially confirmed (over-Hold) but discrimination still works

**Scenario C (XLK was the outlier)** — ~15%
- XLF + XLE produce single-stock-similar distributions (commit rates ≥40%)
- XLK over-Hold was tech-sector-specific, not ETF-substrate-general
- Substrate-tuning thesis weakens

**Scenario D (data/prompt fails on non-tech ETFs)** — ~5%
- One or both sectors produce empty reports or LLM-error rates >10%
- Operational fix needed before Phase D continues

## Success criterion

- [ ] 20 propagations complete with ≤1 error
- [ ] XLF + XLE distributions tabulated against XLK (3-way ETF comparison) and against NVDA Q1 2026 (007 NVDA half)
- [ ] horizon_sweep on the new CSV
- [ ] Per-sector commit-vs-realized-α at 21d
- [ ] Decision per scenario A/B/C/D
- [ ] Total cost ≤ $10

## Notes

- **T1 ceiling caveat**: the experiment's cost estimate ($6) slightly exceeds the strict T1 ≤$5 ceiling. Accepted because (a) the cost is dominated by 2 tickers × 10 dates and the per-run cost is the same as XLK, (b) the underlying purpose is still exploratory smoke (testing generalization of a finding from a single experiment), and (c) the marginal cost of the second ticker is what produces the cross-sector comparison that's the entire point.
- **Same dates as XLK** (2026-01-30 → 2026-04-03) — direct comparability with `2026-05-04-002-xlk-q1-2026-substrate`.
- **`--analysts market,news`** (no fundamentals) — same config as XLK; ETFs lack fundamentals.
- **A3 filter ON** — matches all prior Q1 2026 experiments.
- **Memory log**: fresh per experiment.
- **Forward-21d data availability**: full coverage through 2026-04-24, well within today's data window.
- **Anticipated Phase C interaction**: Phase C second-opinion is default DISABLED, so this experiment runs without Phase C overhead. Phase C smoke testing is a separate (deferred) follow-up.

## Decision tree on result

| Result | Action |
|---|---|
| Scenario A (over-Hold generalizes) | Substrate-tuning thesis confirmed. Schedule prompt-adaptation experiment as next Phase D step. RESEARCH_FINDINGS Phase D section gets a "generalizes across sectors" claim. |
| Scenario B (per-sector discrimination intact) | Mixed substrate finding: framework reads sector regime correctly but with elevated abstention. Document, then test whether prompt re-tuning shifts the abstention bar without breaking the discrimination. |
| Scenario C (XLK was outlier) | Substrate-tuning thesis weakens. Phase D pivots to a different question: why XLK specifically, then. |
| Scenario D (operational fail) | Document failure mode; fix before continuing Phase D. |

## Related experiments

- **2026-05-04-002-xlk-q1-2026-substrate**: 2 OW + 7 Hold + 1 UW on tech-sector ETF — produced the over-Hold finding this experiment tests
- **007 opus47-30pair-mixed (NVDA Q1 2026 half)**: 6 OW + 4 Hold on single-stock equivalent — the comparison baseline
- **008 opus47-cross-period**: NVDA + AAPL + INTC Q4 2025 single-stock cross-period — cross-period dimension (out of scope here; this experiment fixes period to Q1 2026 to isolate substrate)
