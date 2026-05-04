# Spec 001 Phase 3: Convergence-Shortcut Forecast

_Generated 2026-05-04T23:34:10+00:00._

**Corpus**: 156 state logs.
**Threshold**: 2+ bots with magnitude>0.2 sharing a direction.
**Debate cost assumption**: 30% of per-propagate tokens.

## Forecast

| Outcome | Count | % |
|---|---:|---:|
| Would skip debate | 27 | 17.3% |
| - bullish convergence | 16 | 10.3% |
| - bearish convergence | 11 | 7.1% |
| Would NOT skip | 129 | 82.7% |

**Projected per-fire token savings**: 30%
**Projected overall corpus token savings**: 5.2%

## SC-004 acceptance

- Overall ≥15%: FAIL
- Per-fire ≥30%: PASS

## Methodology

- Each historical propagate's analyst prose reports are featurized into Signals via `derive_signal_from_prose` (Phase 1.5+ unigram + bigram features).
- `should_skip_debate(signals)` checks if 3+ Signals share a strong direction (magnitude > 0.7).
- This is a **forecast**: the actual debate-cost fraction is an assumption (default 30%), not measured. Production wiring (Phase 3.5) would replace the assumption with measured per-stage token spend.
- The shortcut is intentionally conservative: it requires 2 bots agreeing on direction with high magnitude. Tuning these thresholds is part of Phase 3.5.
