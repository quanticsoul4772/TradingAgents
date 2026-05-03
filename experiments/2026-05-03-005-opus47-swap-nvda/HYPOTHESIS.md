# Hypothesis: opus47-swap-nvda

**Experiment ID**: `2026-05-03-005-opus47-swap-nvda`
**Created**: 2026-05-03
**Source idea**: Q3 from RESEARCH_FINDINGS — is the 21d bull-side lift Sonnet-specific or general? mcp-reasoning probabilistic verdict was posterior 0.64 (moderate model-specificity expected).
**Cost estimate**: ~$10 (10 NVDA propagations × ~$1 with Opus, ~80 min)

## What we're testing

Single variable: deep_think_llm Sonnet 4.6 → Opus 4.7. Same 10 NVDA dates as pilot, WC-12, MR-3, brave-news-smoke, single-call-baseline. Quick model stays Haiku 4.5.

Reframes Q3 in concrete form: does the +1.59% OW α at 21d (n=30 across-experiment) hold when we swap to a stronger model? mcp-reasoning's posterior on Q3 was 0.64 — moderate confidence the lift is general, not Sonnet-specific.

## Predicted findings

**Scenario A (Opus shows similar 21d bull lift)** — most likely per Q3 reasoning verdict (~65%)
- OW α at 21d positive, similar magnitude to Sonnet (+1-2%)
- Implication: 21d bull-side signal is general LLM property on this analyst-report substrate, not Sonnet-specific

**Scenario B (Opus differs materially)** — ~25%
- E.g. Opus more committed (more Buys) and 21d α stays positive but distribution shifts
- OR Opus more conservative (fewer commits, more Holds) and bucket alphas similar
- Implication: model-specific dynamics affect WHICH dates get committed but underlying signal extraction is shared

**Scenario C (Opus shows no 21d lift)** — ~10%
- OW α at 21d ~0 or negative
- Implication: the 21d lift was a Sonnet artifact. RESEARCH_FINDINGS architectural reframe needs revision.

## Success criterion

- [ ] 10 Opus 4.7 propagations complete on same NVDA grid
- [ ] Distribution comparison vs pilot/WC-12/MR-3/brave/single-call NVDA
- [ ] Forward α at 5d/10d/21d via horizon_sweep
- [ ] Decision: 21d lift is general (proceed with Q1 65-pair) / Sonnet-specific (drop the architectural-reframe claim) / new pattern emerged (re-investigate)

## Notes

- Opus 4.7 is the latest Opus model per env context (claude-opus-4-7). Sonnet experiments used claude-sonnet-4-6.
- Per-call cost: Opus ~3-5x Sonnet on input tokens. Total estimate $10 for 10 NVDA runs.
- No effort flag (--anthropic-effort default unset; Opus accepts effort but we're keeping defaults to match prior runs).
- Same news vendor (yfinance) as pilot for fair comparison vs original signal.

## Decision tree

| Result | Action |
|---|---|
| Scenario A (similar 21d lift) | Q3 answered positive; proceed to Q1 (65-pair re-pilot at 21d) with confidence |
| Scenario B (different distribution, similar bucket-α) | Document model-specificity in calibration; framework reframe survives |
| Scenario C (no lift) | Major revision to RESEARCH_FINDINGS; the 21d lift was Sonnet-substrate-specific |

## Related experiments

- All prior NVDA experiments use the same 10 dates: pilot, WC-12 (002), MR-3 (004), brave-news-smoke (007), single-call-baseline (003).
- Cross-experiment 21d OW α = +1.59% (n=30); Buy α = +1.16% (n=7).
