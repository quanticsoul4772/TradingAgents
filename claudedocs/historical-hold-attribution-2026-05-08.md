# Historical Hold attribution analysis — 2026-05-08

**Trigger**: reasoning_decision rank #6 (0.63 score). Direct empirical extension of WC-10 v1 ALT-A finding via state-log replay.

**Constitution context**: Per VII v1.5.0/v1.5.1, mode collapse to Hold is TWO-MECHANISM:

- **Mechanism A** (genuine ambiguity): Hold is calibrated abstention
- **Mechanism B** (schema-induced collapse): one-directional moderate-magnitude evidence; the framework would commit under WC-10 mode

---

## Corpus summary

- **Total experiments scanned**: 17
- **Total rows across all experiments**: 427
- **Total Hold commits**: 183 (43% of corpus)

## Hold commits by experiment

| Experiment | Hold count |
|---|---:|
| `2026-05-08-003-wc-10-bear-regime-q4-2025-nvda` | 7 |
| `2026-05-08-001-wc-10-pilot` | 15 |
| `2026-05-07-001-spec-008-hybrid-c-ab-ablation` | 27 |
| `2026-05-05-003-signal-at-scale` | 33 |
| `2026-05-05-002-spec003-sc002` | 4 |
| `2026-05-04-004-xle-q4-2025-micro` | 7 |
| `2026-05-04-003-multi-sector-phase-d-q1-2026` | 13 |
| `2026-05-04-002-xlk-q1-2026-substrate` | 7 |
| `2026-05-03-008-opus47-cross-period` | 15 |
| `2026-05-03-007-opus47-30pair-mixed` | 15 |
| `2026-05-03-006-opus47-swap-aapl` | 8 |
| `2026-05-03-002-exa-news-smoke-aapl` | 6 |
| `2026-05-03-001-brave-news-smoke-aapl` | 7 |
| `2026-05-02-006-wc12-cross-msft` | 8 |
| `2026-05-02-005-wc12-cross-aapl` | 7 |
| `2026-05-02-004-mr3-synthesis-v2` | 3 |
| `2026-05-02-002-wc12-pm-blind` | 1 |

## Hold commits by ticker

| Ticker | Hold count |
|---|---:|
| AAPL | 54 |
| NVDA | 26 |
| INTC | 12 |
| XLE | 12 |
| MSFT | 10 |
| XLF | 8 |
| XLK | 7 |
| JPM | 3 |
| MA | 2 |
| GOOGL | 2 |
| AMZN | 2 |
| AVGO | 2 |
| BAC | 2 |
| CSCO | 2 |
| GS | 2 |
| LLY | 2 |
| HON | 2 |
| META | 1 |
| TSLA | 1 |
| ORCL | 1 |
| ... (30 more tickers) | ... |

## Phase 2 extension (pending)

Heuristic classification (asymmetry threshold = 0.4) is scaffolded but PENDING state-log feature extraction. v2 pilot lands ~8h after this script ships and provides n=100 calibration data — at that point a follow-up PR can:

1. Fit a regression from existing prose features (bull_keyword_count, bear_keyword_count, hedge_density, etc.) to WC-10 scalar
2. Apply that regression to historical Hold commits to predict scalar
3. Bin predicted scalar via `bin_scalar_to_tier()` to classify each historical Hold as Mechanism A (predicted Hold-stays-Hold) or Mechanism B (predicted commit under WC-10)

Until then, this report quantifies the SCOPE of the question (how many historical Holds need attribution) and identifies which experiments + tickers have the highest concentration.

## Key insights from corpus scope

- **Highest Hold-density experiment**: `2026-05-05-003-signal-at-scale` with 33 Hold commits — natural starting cohort for Phase 2 attribution
- **Highest Hold-density ticker**: AAPL with 54 Hold commits across all experiments — likely a high-volatility / earnings-active ticker where the framework abstains often
- **Interpretation note**: per Constitution VII v1.5.0/v1.5.1, the TWO-MECHANISM reframe means we should NOT assume all historical Holds represent calibrated abstention. v1 pilot showed 8 of 10 NVDA Holds were schema-suppressed bullish reads (Mechanism B). Phase 2 attribution will tell us what fraction of the corpus's Holds were Mechanism B.

## Cross-references

- Constitution VII v1.5.0 sub-section + v1.5.1 Bear-regime paragraph (PR #131 + #154)
- WC-10 v1 ANALYSIS (PR #130) — empirical basis for Mechanism A vs B distinction
- `scripts/wc_10_underperformance_monitor.py` (PR #146) — runtime monitor for v1.5.1 caveat enforcement
- `claudedocs/cross-pollination-review-2026-05-08.md` (PR #143) — original L4 'Knowledge digestion' candidate identified
- `claudedocs/experiment-md-tier-2-3-review-2026-05-08.md` (PR #145) — EH-4 ranked as top-3 next-experiment candidate

## Cost

$0 LLM. Pure data walk; no propagate calls.
