# SC-003 INTC +103% on Hold investigation — 2026-05-06

**Question**: was INTC's Hold rating on 2026-04-03 a calibrated abstention (framework didn't have evidence to commit, which is correct per Constitution VII even if the +103% outcome happened) or a calibration weakness (framework HAD evidence and should have called Buy/OW)?

This was the last unaddressed SC-003 follow-up. Closes the SC-003 follow-up arc.

## Verdict: calibrated abstention — but with a structural counter-example to spec 003

**Framework's Hold was correctly calibrated given the evidence visible at signal time.** The +103% outcome was driven by forward-looking events (April 23 earnings, etc.) the framework couldn't see on 2026-04-03.

**However**: this case is a counter-example to spec 003's mechanism. If the PM had committed Buy/OW based on the bull case, the spec 003 contrarian gate (default-on as of 2026-05-06) would have FIRED and downgraded back to Hold — costing the +103% either way.

## Evidence

### Framework state at 2026-04-03

| Metric | Value | Note |
|---|---|---|
| Final rating | Hold | "do not chase the 22% three-day rip and do not capitulate into strength" |
| INTC prior 30d return | +9.09% (46.18 → 50.38) | Already moving up coming in |
| `bull_keyword_count` | 98 | Highest of any single value across all INTC propagates |
| INTC prior bull_kw history | N=24, max 107, median 56, min 40 | Comfortably above FR-004 floor |
| Bull bull_kw percentile | 96th percentile of own history | Above the 80th-percentile gate threshold |
| Bull debate length | 14,123 chars | — |
| Bear debate length | 29,767 chars | **Bear dominated by 2x** |

### What the LLM saw + decided

The investment plan rationale said:

> "Both sides delivered substantive arguments and the truth on INTC sits between them, but neither side fully wins on the evidence presented."

> "The bull makes several genuinely strong points: normalized operating income did swing meaningfully (~$1B YoY), TTM OCF of $10.7B is real cash generation, $32.8B of liquidity gives multi-year runway, debt is actually down ~$5B YoY, and the technical tape (MACD crossover, price reclaiming the 50/200, Bollinger expansion on >100M share volume) is objectively constructive. The Fab 34 repurchase, the 18A ramp, and the in-progress government funding..."

> "Maintain INTC at 70-75% of benchmark weight at the current ~$50.38 level... do not chase the 22% three-day rip and do not capitulate into strength. Hard stop on a close below $41 (March capitulation low)... Re-underwrite at the April 23 earnings print, focusing on revenue inflection above $14B, normalized operating margin, and fab utilization guidance."

**Translation**: the framework saw real bull evidence + real bear evidence + chose to wait for the April 23 earnings print to commit. This is exactly Constitution VII's calibrated-abstention pattern.

### What actually happened

INTC went **+103.14% in 21 trading days** (2026-04-03 → 2026-05-04 close). Forward catalysts the framework couldn't see at signal time:

- April 23 earnings (the framework explicitly noted this was the "re-underwrite" trigger)
- Likely sector + company-specific news in the 21d window

## Implications for spec 003 + 003.5

This case is a **counter-example to spec 003's mechanism**. The spec is built on finding #4 (within-ticker bull_keyword_count anti-predicts within-ticker α at 90d, IC -0.489 across the corpus). INTC at 2026-04-03 went the opposite direction:

| Mechanism prediction | Reality |
|---|---|
| bull_kw=98 at 96th percentile → high probability of negative future α (per finding #4) | INTC realized +103% over 21 trading days |

If the PM had committed Buy or Overweight on 2026-04-03, the spec 003 contrarian gate (default-on as of today's earlier work) would have:
- Per-ticker baseline: 24 ≥ 20 → uses per-ticker baseline
- Percentile: 96th >= 80th threshold → **fires**
- Active mode: rating → Hold
- Realized cost: -103% α attribution from the suppression

This adds a third concrete data point about spec 003's calibration:

1. **NVDA/AAPL retrospective (2026-05-05)**: gate fires correctly on average, +6.46% cumulative Δα at 21d (per `claudedocs/contrarian-gate-retrospective-2026-05-05.md`)
2. **SC-003 Financials cohort (2026-05-06 validation)**: gate doesn't fire (cohort doesn't meet floor), -2.67pp net Δα would have hurt the bucket if the floor were lowered (per `claudedocs/sector-momentum-retrospective-2026-05-06.md` per-sector)
3. **INTC 2026-04-03 (this investigation)**: gate WOULD have fired if PM committed bullish, would have suppressed a +103% winner

The pattern: spec 003's mechanism is statistically real (corpus IC -0.489) but **fires high-confidence-wrong on individual outliers** where forward-looking catalysts dominate the within-ticker prose-density signal.

## Implications for product framing

Constitution VII (calibrated abstention) handled INTC correctly. The framework did NOT have evidence to commit, chose Hold, and in this specific case the +103% reward went to "diamond hands" who held / bought regardless. **There is no architectural change that would have caught this without changing the framework's truth-conditioning** — i.e., predicting the April 23 earnings print at signal-generation time on 2026-04-03.

The +103% outcome is **information the framework couldn't see**. Calibrated abstention is the correct response to that information state.

But the secondary finding (gate would have actively prevented commit in spec 003 active mode) raises a real concern:

- Spec 003 corpus retrospective showed +6.46% cumulative Δα at production floor — that was n=2.
- INTC adds a counter-example that by itself would dwarf the cumulative gain (if INTC had been a successful Buy, gate would suppress → -100+% α attribution).
- **The spec 003 retrospective sample is too small** to confidently support default-on. The default flip on 2026-05-06 was made on n=2 evidence; the framework now has at least one large counter-example.

## What this changes

**Recommendation**: revisit the spec 003 default-on flip. The retrospective sample (n=2) is insufficient to support it. The INTC case demonstrates that gate-fired-and-wrong outliers can dwarf gate-fired-and-right cumulative gains.

Two paths:
1. **Revert spec 003 default to off** (+ document this finding) until a 50+ commit retrospective shows positive net Δα robust to outliers.
2. **Keep default-on but tighten the threshold** (e.g., 90th percentile instead of 80th) to reduce false-fires on outliers like INTC. Would need a new threshold-sweep retrospective.

Either path is a separate work unit. Documented as a follow-up; not done in this investigation.

## What this DOESN'T change

- **Spec 002 paper-trading harness** — unaffected; would simply have honored whatever rating the framework emitted.
- **Constitution VII calibrated abstention** — INTC validates this principle. Framework correctly held when evidence was 2-sided.
- **A3 momentum filter** — unaffected; A3 only acts on bear ratings.
- **Spec 004 sector-momentum filter** — unaffected; default-off + already shown empirically not to help.

## SC-003 follow-up arc — closed

| Follow-up | Status |
|---|---|
| Financials bullish miss (per spec 003.5 + spec 004 validation) | Investigated; documented as fourth failure mode (per-ticker-α-vs-rising-sector); no current filter catches |
| INTC +103% on Hold (this investigation) | Investigated; calibrated abstention correct; surfaced counter-example to spec 003 default-on |
| Multi-window SC-003 replication | Not done; would expand corpus from 73 to 130+ commits; T2-T3 cost; deferred to later session |

## Reproducibility

```
.venv/Scripts/python.exe -c "
import json
from pathlib import Path
from tradingagents.signals.featurization import bull_keyword_count
log = Path.home() / '.tradingagents' / 'logs' / 'INTC' / 'TradingAgentsStrategy_logs' / 'full_states_log_2026-04-03.json'
state = json.loads(log.read_text(encoding='utf-8'))
print(f\"bull_kw: {bull_keyword_count(state['market_report']):.0f}\")
print(f\"rating: {state['final_trade_decision'].split(chr(10))[0]}\")
"
```

State logs at `~/.tradingagents/logs/INTC/TradingAgentsStrategy_logs/`. No LLM cost. Per-ticker history for percentile via the same `_per_ticker_bull_keyword_history` helper from `scripts/sc003_financials_gate_check.py`.
