# WC-10 dry-run digest — 2026-04-22

_Synthesized from `experiments/2026-05-08-001-wc-10-pilot/results.csv` (WC-10 v1 pilot data, no LLM spend). Demonstrates the operator-facing markdown surface for Spec 009 Branch A (WC-10 production deployment via `daily_signals.py --wc-10-enabled`) vs the existing 5-tier baseline._

**Source**: experiments/2026-05-08-001-wc-10-pilot/results.csv (2 tickers on `2026-04-22`)


---

## Side-by-side comparison

| Ticker | WC-10 (scalar → bin) | 5-tier baseline | Decision differs? | Realized 21d α |
|---|---|---|---|---|
| AAPL | `+0.0500` → Hold | Hold | no | +3.66% (days=12) |
| NVDA | `+0.5800` → Overweight | Hold | **yes** | +2.56% (days=12) |

---

## Branch A — WC-10 mode (`--wc-10-enabled`)

**Actionable**: 1  | **Filtered (Hold / Underweight / Sell)**: 1


### Actionable signals (Buy / Overweight)

- **NVDA** — Overweight (scalar `+0.5800`) — realized 21d α = `+2.56%` (days=12)

### Filtered signals (Hold / Underweight / Sell)

- **AAPL** — Hold (scalar `+0.0500`) — realized 21d α = `+3.66%` (days=12)
  _Hold = calibrated abstention OR schema-induced collapse (per Constitution VII v1.5.0)._

---

## Existing baseline — 5-tier mode (default)

**Actionable**: 0  | **Filtered (Hold / Underweight / Sell)**: 2


### Filtered signals (Hold / Underweight / Sell)

- **AAPL** — Hold — realized 21d α = `+3.66%` (days=12)
  _Hold = calibrated abstention OR schema-induced collapse (per Constitution VII v1.5.0)._
- **NVDA** — Hold — realized 21d α = `+2.56%` (days=12)
  _Hold = calibrated abstention OR schema-induced collapse (per Constitution VII v1.5.0)._

---

## Operator interpretation

- WC-10 mode produced **1 actionable signal** of 2; baseline produced **0 actionable**.
- Tickers where WC-10 surfaces actionable signal that baseline suppresses are the schema-induced-collapse cases per Constitution VII v1.5.0.
- Realized 21d α values (above) are the empirical check on the additional commits.

**This is dry-run output**, not investment advice. Production deployment requires v2 + v3 verdicts per Spec 009 branch selection criteria.
