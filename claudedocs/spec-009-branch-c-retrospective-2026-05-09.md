# Spec 009 Branch C activation retrospective

**Date**: 2026-05-09
**Spec**: `specs/009-wc-10-production-deployment/`
**Selected branch**: **C — bin-then-output ergonomic-only**
**Triggering verdict**: WC-10 v2 SC-005(b) NULL (combined v1+v2 n=100; Pearson r +0.0918 / Spearman ρ +0.0410, both BELOW ±0.197 critical at p=0.05).

## Why Branch C (not A / B / D)

Per `specs/009-wc-10-production-deployment/spec.md` 4-branch decision tree:

| Branch | Trigger | v2 actual | Match? |
|---|---|---|---|
| A | v2 STRONG (\|r\| ≥ 0.30) OR ALT-A on ≥6/8 tickers | r=+0.0918 / ALT-A on 5/8 | NO (correlation NULL; ALT-A 5/8 below FR-005 ≥6/8 threshold) |
| B | v2 MODERATE (0.197 < \|r\| < 0.30) OR ALT-A on 3-5/8 | r=+0.0918 below 0.197 | partial (ALT-A 5/8 = lower bound of B range) |
| **C** | v2 NULL (\|r\| < 0.197) | r=+0.0918 / Spearman +0.0410 | **YES** |
| D | v2 NULL + v3 ALT-A | v3 was PARTIAL ALT-A, not ALT-A | NO (D pre-ruled-out per plan.md gate) |

The SC-005(b) correlation gate is the PRIMARY decision criterion (per spec.md FR-005 ordering). NULL on the primary criterion → Branch C activates regardless of secondary FR-005 ALT-A generalization count.

## Implementation scope (per plan.md Branch C estimate: ~1.5h, ~10 LOC + ~3 unit tests)

Actual implementation match plan estimate:

- ✅ `tradingagents/default_config.py`: 4 LOC (TypedDict + DEFAULT_CONFIG entry + comment)
- ✅ `tradingagents/agents/managers/portfolio_manager.py`: 14 LOC (re import + 4-line bin-then-output branch in existing wc_10 bypass conditional)
- ✅ `tests/test_wc_10_pm_integration.py`: 3 new tests covering: positive scalar binning to Overweight, default-off scalar preservation, negative scalar binning to Underweight
- ✅ `docs/SIGNALS.md`: new "WC-10" section documenting v1+v2+v3 empirical chain + Branch C config + cohort-validation table

Total: ~30 LOC code + ~75 LOC tests + ~30 lines docs. All quality gates pass (pre-commit hooks + 5/5 PM integration tests + 10/10 bin function tests).

## What Branch C does NOT do

Per spec.md Out of Scope:

- **No `daily_signals.py` flag exposure** — WC-10 stays PARAMS.json-only research mode. Operators consuming signals via daily_signals.py see 5-tier output exclusively.
- **No `paper_trade.py` position-sizing changes** — Branch A/B feature; Branch C preserves 5-tier-only sizing.
- **No regime-aware gating** — Constitution v1.5.1 Patch D documented this as not required given v3 PARTIAL ALT-A magnitude bound. Runtime monitoring via `scripts/wc_10_underperformance_monitor.py` (PR #146) suffices.
- **No new mechanism class** — Branch C is plumbing only (overrides rendered Rating header with binned tier when both `wc_10_enabled` and `wc_10_internal_only` are True).

## Spec 009 status post-Branch C

Spec stays OPEN with Branch C as the active deployment. Future re-trigger conditions:
- v4+ corpus expansion to n≥200 might surface a weak-but-real correlation that n=100 missed (current critical r at n=200/p=0.05 = 0.139). If a follow-up confirms moderate correlation, Branch B would activate (research mode preserved + scalar exposed in PARAMS path). Branch A activation would require both correlation AND ≥6/8 ticker FR-005 generalization.
- Architecturally, Branch C does NOT preclude later Branch B/A activation — it ships as an interim ergonomic mode while the corpus grows.

## Cost

$0 LLM (pure plumbing + docs; no propagates).

Implementation wall-clock: ~30 min (code + tests + docs + retrospective). Plan estimate was 1.5h; came in faster because of pre-scaffolded design surface (5/7 spec-kit artifacts already shipped per PRs #137 + #144 + #145 + #149 + #150).

## Cross-references

- `specs/009-wc-10-production-deployment/spec.md` (PR #140 — 4 verdict-conditional branches)
- `specs/009-wc-10-production-deployment/plan.md` (PR #144 — Branch A/B/C plans)
- `specs/009-wc-10-production-deployment/contracts/daily_signals_wc_10_flag.md` (PR #145 — operator surface contract)
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1 verdict; PR #130)
- `experiments/2026-05-08-002-wc-10-v2-ticker-expansion/ANALYSIS.md` (v2 verdict; PR #181)
- `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS.md` (v3 verdict; PR #153)
- Constitution v1.5.0 (PR #131) + v1.5.1 (PR #154) + v1.5.2 (PR #179) — Principle VII evolution alongside WC-10 arc
- Triple-pilot landing playbook: PR #172
- v2 4-PR landing series: PR #181 (ANALYSIS) + PR #182 (RESEARCH_FINDINGS) + PR #183 (ROADMAP) + this PR (Branch C MVP)
- Memory `reference_conditional_branch_spec_pattern.md` — codifies the conditional-branch pre-scaffolding pattern that enabled this spec's rapid landing
