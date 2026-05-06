# SC-003 Financials bullish-miss diagnostic — 2026-05-06

**Question (per CLAUDE.md SC-003 follow-up):** did the spec 003 contrarian gate flag any of the 5 losing Financials Overweight commits in shadow mode? If yes, the gate's active-mode value would be materially higher than the +6.46% retrospective number.

**Method:** the configured shadow-mode annotations were silently dropped by the state-log writer (see "Bug surfaced" below). Re-derived them offline from the persisted `market_report` text using the live gate's logic — `bull_keyword_count` percentile against per-ticker prior history with strict no-look-ahead.

## Result

| Ticker | OW α (21d) | bull_kw | history N | percentile | fire @ N≥20 (live) | fire @ N≥5 (permissive) |
|---|---|---|---|---|---|---|
| JPM | -5.12% | 55 | 13 | 92% | no (below floor) | **YES** |
| BAC | -3.73% | 65 | **0** | n/a | no | no |
| WFC | -12.23% | 48 | **0** | n/a | no | no |
| GS | -3.74% | 46 | **0** | n/a | no | no |
| MA | -10.55% | 50 | **0** | n/a | no | no |

## Verdict

**The gate is structurally impotent against this specific failure mode.**

- 4 of the 5 Financials Overweight commits had **zero per-ticker prior history** when SC-003 ran — the framework had never propagated on those tickers before. The percentile baseline doesn't exist; the gate cannot fire by construction.
- JPM had 13 prior runs (below the live N≥20 floor; just above the permissive N≥5). Its current `bull_keyword_count` (55) lands at the 92nd percentile of the 13 prior values — but 13 < 20 so the live gate skips. At permissive N≥5 it WOULD fire.
- **Even the permissive-floor counterfactual would have HURT** the Financials bucket: suppressing JPM (the *least*-wrong of the 5 at -5.12%) and keeping WFC (-12.23%) and MA (-10.55%) means survivor mean = -7.56% vs original -7.07%. Δα = −0.49pp.

## Why the +6.46% retrospective is real but narrow

The earlier `claudedocs/contrarian-gate-retrospective-2026-05-05.md` measured +6.46% cumulative Δα at 21d at the production N≥20 floor — but **only 2 commits in the entire corpus crossed the floor at the time of that retrospective**, and both were on tickers (NVDA, AAPL) with months of accumulated prior history.

**The gate's value is concentrated on tickers with thick per-ticker history.** For cold-start universes (most of the 50 SC-003 tickers, which were new-to-framework), the gate is silent.

## Implication for product-build framing

The default-on flip (commit `2c6ebd0`) is still defensible — the gate doesn't HURT on cold-start tickers, it just can't help. But the value claim should be qualified:

- **What the gate prevents:** within-ticker bullish-prose-density spikes on tickers the framework has seen before
- **What the gate does NOT prevent:** sector-wide directional misses on cold-start tickers (the SC-003 Financials case)

For the SC-003 Financials miss specifically, **no available filter would have caught it from offline-derivable signals.** The 5 losing OW commits all had bull_keyword_count in the 46–65 range (within typical bullish-write distribution, no per-ticker comparator possible). Any future filter that addresses this class of failure would need either:
- A cross-ticker baseline (e.g., compare to sector-level history), or
- Live macro/sector overlays (SPY-relative momentum, sector ETF performance)

## Bug surfaced

`tradingagents/graph/trading_graph.py:425-453` (the `_log_state` writer) explicitly whitelists fields from `final_state` to persist to the JSON log. The whitelist omitted `contrarian_gate`, so shadow-mode annotations from any historical run are silently lost.

**Fix landed in this commit:** added `"contrarian_gate": final_state.get("contrarian_gate")` to the whitelist; added two regression-guard tests (`test_state_log_persists_contrarian_gate_field`, `test_state_log_contrarian_gate_is_none_when_field_absent`).

Future shadow-mode runs will persist the live gate annotations directly; offline re-derivation (this script) is no longer needed for new data, but remains useful for re-analyzing pre-fix historical state logs.

## Reproducibility

```
python scripts/sc003_financials_gate_check.py
```

Reads from `~/.tradingagents/logs/<ticker>/TradingAgentsStrategy_logs/full_states_log_<date>.json`. No LLM cost.
