# Spec 012 Class 4 Macro-Environment Filter — deployment retrospective

**Date**: 2026-05-09
**Spec bundle**: `specs/012-class-4-macro-filter/`
**5-PR bundle**: #194 (spec.md + plan.md) + #197 (tasks.md) + #198 (MVP) + #199 (audit + state-log regression) + #200 (this PR — polish)
**Deployment status**: DEPLOYED end-to-end at default-SHADOW.

Per Constitution VIII v1.4.1 ships-its-retrospective discipline. This retrospective documents the chain: 2026-05-09 retrospective PASS (PR #193) → 5-PR spec-kit bundle → SHADOW mode launch.

## Why this spec exists

The 2026-05-06 sector-α attribution analysis (`claudedocs/sector-alpha-attribution-2026-05-06.md`) identified an 18-row bear-side ticker_strong cohort (mean realized α-vs-SPY = +28.02% — the largest bear-side anti-calibration finding in the corpus to date). The cohort is **uncatchable by A3 momentum filter by construction** (A3 fires on per-ticker DOWN absolute mean-reversion; ticker_strong tickers are UP).

Class 4 (cross-asset/macro) was the FIRST mechanism class identified that could catch this cohort. The 2026-05-09 retrospective (PR #193) tested whether VIX-based macro features identify these counter-trend bear commits BEFORE the framework commits Underweight/Sell.

## Verdict path

| Step | Result |
|---|---|
| **Retrospective (PR #193)** | PASS at v1.4.0 standalone (n=8 fires at VIX < 18; +24.07pp net Δα; 75% cohort hit) AND v1.4.3 additive (mechanism-disjoint vs A3; +24.07pp incremental) |
| **Spec drafting (PR #194)** | spec.md + plan.md scaffolded with 2 verdict-conditional branches (Branch A default-SHADOW; Branch B future default-ACTIVE) |
| **Tasks (PR #197)** | 17 tasks across 5 phases |
| **MVP (PR #198)** | helper module + PM hook + AgentState + state log + 17 tests; 1188 unit tests passing |
| **Audit + regression (PR #199)** | shadow audit script + 5 new tests (3 audit + 2 state-log persistence); 1193 unit tests passing |
| **Polish (this PR #200)** | docs/SIGNALS.md update + RESEARCH_FINDINGS row flip CONDITIONAL DRAFT → SHADOW + this retrospective |

**Total bundle effort**: ~4-5h wall-clock across 5 PRs. Plan.md estimate was ~5h; actual matched estimate.

**Cohort sizing**: original 18-row ticker_strong cohort (06) → 22-row cohort (today, post-WC-10 v2 + WC-11 + BR-3 corpus growth). Mean α-vs-SPY drifted up from +28.02% to +32.64% — anti-calibration finding strengthened, not weakened.

## What this catches that no other filter does

| Filter | Catches | Mechanism |
|---|---|---|
| A3 momentum | Per-ticker DOWN absolute mean-reversion (43 UW commits in-sample) | Backward-price |
| Spec 003 contrarian gate | Within-ticker bull-prose density spike | Prose-density (per-ticker IC) |
| Spec 004/006 | Sector-relative price patterns (default-OFF after retrospective fail) | Backward-price (sector) |
| Spec 007 bull/bear | Forward-catalyst absorption (LLM extracts from analyst reports) | LLM-extracted feature |
| Spec 008 Hybrid C | Calendar-boost on Spec 007 bull (default-OFF) | Hybrid (Class 3 LLM × Class 6 calendar) |
| Spec X-1 institutional rotation | 13F ownership delta below threshold | Quantitative-flow |
| **Spec 012 Class 4** | **Bear commits made when VIX low (risk-on environment)** | **Cross-asset macro** |

A3 catches 0 of 22 bear ticker_strong cohort by definition. Class 4 catches 6 of 22 at default threshold. Mechanism-disjoint pair.

## What this does NOT catch (deferred to v2 / future specs)

- **Bull-side macro** (`class_4_macro_bull_mode = "off"` default): "bullish commit when VIX rising fast" cohort would require separate retrospective. Reserved key in config; unimplemented.
- **Sector ETF correlation features**: retrospective showed VIX-30d-Δ% alone is sufficient discriminator; sector correlation can be added as v2 enhancement if needed.
- **10y yield + DXY USD threshold-gating**: retrospective showed these don't discriminate at the cohort level (Δ ≈ 0); deferred to v2 multi-feature variant.
- **Live-mode active suppression** (default-on flip): requires SC-010 evidence — n ≥ 30 live shadow-mode fires AND mean realized α-vs-SPY ≥ -1pp at 21d. Audit script `scripts/class4_macro_shadow_audit.py` outputs the readiness verdict.

## Operational characteristics

- **Cost**: $0 per propagate (yfinance + arithmetic; no LLM call).
- **Latency**: ~250ms p99 cache-cold (single yfinance VIX history fetch); ~5ms cache-warm.
- **Failure mode**: yfinance unreachable → graceful degradation (no fire; same as cache-empty).
- **Memory log impact**: none (filter operates pre-PM commit; doesn't write to memory).
- **Filter ordering**: PM hook chain runs A3 → Spec 003 / 003.5 → Spec 004 → Spec 006 → Spec 007 → Spec X-1 → **Class 4 (LAST)** per smallest-sample-last rule.

## Bundle delivery pattern observation

The 5-PR Spec 012 bundle followed the **same pattern as Spec X-1** (`reference_speckit_6pr_workflow_pattern.md` + PRs #88-#93). Key reuse points:
- Module structure mirrors `tradingagents/agents/utils/institutional_rotation_filter.py`
- State annotation pattern identical (None when off; full dict when on)
- PM hook integration pattern identical
- Test fixture structure mirrors Spec X-1 PM integration tests
- Retrospective pattern matches Spec X-1 retrospective at PR #93

The 5-PR-vs-6-PR difference: Spec X-1 had a separate research.md + data-model.md + contracts/ + checklists/ in the spec bundle (more design surface). Spec 012 collapsed plan + research into a single plan.md + only spec.md + plan.md scaffold (smaller design surface justified by retrospective-first methodology already establishing the empirical case).

## What's next for Class 4

1. **Live shadow-mode evidence accumulation**: as the framework runs in production with `class_4_macro_bear_mode = "shadow"`, would-fire instances accumulate in state logs.
2. **Periodic SC-010 audit**: operator runs `python scripts/class4_macro_shadow_audit.py` to check default-on flip readiness.
3. **Default-on flip when ready**: when n ≥ 30 fires AND mean α ≥ -1pp at 21d, ship a one-line PR amendment to spec.md + flip default to "active". No new code required (Branch B path per spec.md).
4. **v2 enhancements** (deferred): bull-side activation OR multi-feature variant (sector correlation + 10y yield + DXY) IF live evidence reveals cohorts the VIX-snapshot single-feature variant misses.

## Test count delta (across the 5-PR bundle)

| PR | Test count change | Cumulative |
|---|---:|---:|
| #194 (spec + plan) | +0 | 1171 |
| #197 (tasks.md) | +0 | 1171 |
| #198 (MVP) | +17 | 1188 |
| #199 (audit + regression) | +5 | 1193 |
| #200 (polish; this PR) | +0 | 1193 |
| **Bundle total** | **+22** | **1193** |

mypy clean on all new code; ruff clean.

## Cost summary

| PR | $ LLM | Wall-clock |
|---|---:|---:|
| #194 (spec + plan) | $0 | ~30 min |
| #197 (tasks.md) | $0 | ~20 min |
| #198 (MVP) | $0 | ~1.5h |
| #199 (audit + regression) | $0 | ~45 min |
| #200 (polish; this) | $0 | ~30 min |
| **Bundle total** | **$0** | **~4h** |

Plus the upstream retrospective (PR #193): $0 + ~30 min.

**Spec 012 total cost from retrospective inception to deployment: $0 LLM, ~4.5h wall-clock**.

## Constitution adherence

| Principle | Status |
|---|---|
| I (Save Everything) | ✅ this retrospective + PR #193 retrospective + per-PR retrospective notes |
| II (One Experiment Per Change) | ✅ single intervention (new filter) |
| III (Stay Cheap) | ✅ $0 LLM (yfinance + arithmetic per propagate) |
| IV (No Production Claims) | ✅ default-SHADOW per small-sample-caution; SC-010 enforces 30+ live fires before active flip |
| VI (Spec Before Structural Change) | ✅ 5-PR bundle (spec.md + plan.md + tasks.md + MVP + tests/audit + polish) |
| VII (Calibrated Abstention) | ✅ orthogonal — operates pre-PM commit |
| VIII v1.4.0 + v1.4.3 | ✅ both PASSED in PR #193 retrospective; SC-010 enforces shadow-mode-first launch |

## Cross-references

- `claudedocs/class4-macro-filter-retrospective-2026-05-09.md` (PR #193 — retrospective verdict)
- `claudedocs/sector-alpha-attribution-2026-05-06.md` (cohort identification)
- `specs/012-class-4-macro-filter/spec.md` (PR #194)
- `specs/012-class-4-macro-filter/plan.md` (PR #194)
- `specs/012-class-4-macro-filter/tasks.md` (PR #197)
- `tradingagents/agents/utils/macro_environment_filter.py` (PR #198)
- `tests/test_macro_environment_filter.py` (PR #198 — 13 unit tests)
- `tests/test_class_4_pm_integration.py` (PR #198 — 4 PM integration tests)
- `scripts/class4_macro_shadow_audit.py` (PR #199 — SC-010 readiness audit)
- `tests/test_class4_macro_shadow_audit.py` (PR #199 — 3 audit unit tests)
- `tests/test_trading_graph.py` (PR #199 — +2 state-log persistence regression tests)
- `docs/SIGNALS.md` (this PR — Class 4 sub-section)
- `RESEARCH_FINDINGS.md` Filter portfolio status (this PR — row flipped CONDITIONAL DRAFT → SHADOW)
- Memory: `reference_speckit_6pr_workflow_pattern.md` (the bundle pattern this PR series instantiated)
- Memory: `reference_conditional_branch_spec_pattern.md` (the verdict-conditional spec pattern PR #194 followed)
