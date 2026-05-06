# Daily Signals — 2026-05-06

**Universe**: 5 tickers  | **Actionable**: 2  | **Hold (calibrated abstention)**: 1  | **Spec 003 gate overrode**: 1  | **A3 filter overrode**: 0  | **Errored**: 2

**Filters**: A3 momentum filter ON · Spec 003 contrarian gate ON (active (rating override))

---

## Actionable signals (Buy / Overweight, gates not fired)

### AMZN — **Overweight**
> Executive Summary: Overweight AMZN with a scale-in approach: do not chase at $273+. Build toward a 5% target weight in tranches at $265-270 (40%), $258-262 (35%), and $245-250 (25%), with a weekly-close stop at $238. Holding period 6-12 mo…
- Spec 003 contrarian gate: **skipped** (insufficient_history; n_history=—)

### NVDA — **Overweight**
> # Portfolio Manager's Final Decision on NVDA
- Spec 003 contrarian gate: percentile 60 (threshold 80; n_history=20) — gate did not fire

---

## Filtered (Hold / Underweight / Sell, or gate-suppressed)

### AAPL — Hold
- **Spec 003 contrarian gate overrode** the original Buy/OW rating to Hold (analyst-prose bull-keyword percentile 100). See [`claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md`](../claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md).

---

## Errors

- **MSFT**: OverloadedError: Error code: 529 - {'type': 'error', 'error': {'type': 'overloaded_error', 'message': 'Overloaded'}, 'request_id': 'req_011CamYppe3a9nVzBWskhit5'}
- **GOOGL**: OverloadedError: Error code: 529 - {'type': 'error', 'error': {'type': 'overloaded_error', 'message': 'Overloaded'}, 'request_id': 'req_011Camai5iw7QCgunaznET9y'}

---

## Methodology

- **Horizon**: 21 trading days. 5d horizon is at the LLM single-call calibration ceiling (no signal); 21d shows +1.23% mean α on bullish commits across n=71 cross-experiment commits (~61% hit rate). See `RESEARCH_FINDINGS.md` headline.
- **Calibrated abstention** (Constitution VII): Hold ≈ 0% mean α at every horizon. Suppressed from the actionable list by default; the framework is correctly doing nothing 50-70% of the time.
- **A3 momentum filter** (`tradingagents/agents/utils/momentum_filter.py`): suppresses UW/Sell commits when the ticker is down ≥5% over 30 trading days; the framework's bearish commits on already-down tickers tend to mean-revert bullishly.
- **Spec 003 contrarian gate** (`tradingagents/signals/contrarian_gate.py`): suppresses Buy/OW commits when the market analyst's `bull_keyword_count` is in the top 20% of the prior 20-date history for that ticker; high analyst-prose density tracks recent strength which mean-reverts. Validated through 4 lines of evidence (`claudedocs/finding4-within-bullish-subset-ic-2026-05-05.md`).
- **Period-conditional**: realized α varies across calendar periods; the +1.23% is moderate-confidence (Bayesian posterior 0.63 across 3 NVDA periods).


---

_This is research substrate, not investment advice. Per Constitution Principle IV: the framework's outputs are not trading recommendations._
