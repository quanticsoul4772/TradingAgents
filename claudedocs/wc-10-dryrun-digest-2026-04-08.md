# WC-10 dry-run digest — 2026-04-08

_Synthesized from `experiments/2026-05-08-001-wc-10-pilot/results.csv` (WC-10 v1 pilot data, no LLM spend). Demonstrates the operator-facing markdown surface for Spec 009 Branch A (WC-10 production deployment via `daily_signals.py --wc-10-enabled`) vs the existing 5-tier baseline._

**Source**: experiments/2026-05-08-001-wc-10-pilot/results.csv (2 tickers on `2026-04-08`)


---

## Side-by-side comparison

| Ticker | WC-10 (scalar → bin) | 5-tier baseline | Decision differs? | Realized 21d α |
|---|---|---|---|---|
| AAPL | `-0.3500` → Underweight | Underweight | no | +2.80% (days=21) |
| NVDA | `+0.6800` → Buy | Hold | **yes** | +7.94% (days=21) |

---

## Branch A — WC-10 mode (`--wc-10-enabled`)

**Actionable**: 1  | **Filtered (Hold / Underweight / Sell)**: 1


### Actionable signals (Buy / Overweight)

- **NVDA** — Buy (scalar `+0.6800`) — realized 21d α = `+7.94%` (days=21)

### Filtered signals (Hold / Underweight / Sell)

- **AAPL** — Underweight (scalar `-0.3500`) — realized 21d α = `+2.80%` (days=21)

---

## Existing baseline — 5-tier mode (default)

**Actionable**: 0  | **Filtered (Hold / Underweight / Sell)**: 2


### Filtered signals (Hold / Underweight / Sell)

- **AAPL** — Underweight — realized 21d α = `+2.80%` (days=21)
- **NVDA** — Hold — realized 21d α = `+7.94%` (days=21)
  _Hold = calibrated abstention OR schema-induced collapse (per Constitution VII v1.5.0)._

---

## Operator interpretation

- WC-10 mode produced **1 actionable signal** of 2; baseline produced **0 actionable**.
- Tickers where WC-10 surfaces actionable signal that baseline suppresses are the schema-induced-collapse cases per Constitution VII v1.5.0.
- Realized 21d α values (above) are the empirical check on the additional commits.

**This is dry-run output**, not investment advice. Production deployment requires v2 + v3 verdicts per Spec 009 branch selection criteria.
