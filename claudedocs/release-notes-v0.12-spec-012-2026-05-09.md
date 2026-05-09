# Release notes — v0.12.0-spec-012 (2026-05-09)

**Date**: 2026-05-09 evening
**Predecessor**: v0.8.1-spec-008.5 (2026-05-07)
**Tag command** (after this PR merges):

```bash
git tag -a v0.12.0-spec-012 -m "v0.12.0 — Spec 012 Class 4 macro-environment filter (FIRST cross-asset/macro filter; default-shadow bear) + WC-10 research arc CLOSED + Constitution v1.5.0/v1.5.1/v1.5.2 amendments"
git push origin v0.12.0-spec-012
```

## Why v0.12 (not v0.9 / v0.10 / v0.11)

The 2 minor versions skipped reflect the Spec X-1 deployment (2026-05-07) + the WC-10 v1+v2+v3 research arc + Constitution v1.5.0/v1.5.1 amendments that didn't get their own tags at the time. Per the project's tagging convention `v<MINOR>.<PATCH>-spec-<N>`:

- v0.9.x reserved for Spec X-1 institutional rotation deployment (PRs #88-#93 on 2026-05-07; never tagged)
- v0.10.x reserved for WC-10 v1 ALT-A confirmation + Constitution v1.5.0 (PRs #117-#136 on 2026-05-08; never tagged)
- v0.11.x reserved for WC-10 v3 PARTIAL ALT-A + Constitution v1.5.1 + Spec 011 (continuation of 2026-05-08; never tagged)
- **v0.12.0-spec-012 (this tag)** — Spec 012 Class 4 macro filter deployed end-to-end via 5-PR bundle on 2026-05-09; FIRST cross-asset/macro filter; first PASS at v1.4.0+v1.4.3 gates from a $0 retrospective. Captures the entire 2-day arc since v0.8.1-spec-008.5.

## What's new since v0.8.1-spec-008.5

### Specs deployed (2)

- **Spec X-1 institutional rotation filter** (2026-05-07; PRs #88-#93): FIRST quantitative-flow bear-side filter. Default-shadow bear @ T_outflow=0.05; standalone PASS n=12 + additive PASS vs Spec 007 bear union (+8.06pp Δα improvement).

- **Spec 012 Class 4 macro-environment filter** (2026-05-09; PRs #194-#200): FIRST cross-asset/macro filter. Default-shadow bear @ VIX < 18; standalone PASS n=8 + additive PASS vs A3 (+24.07pp incremental; mechanism-disjoint).

### Production deployment activated (1)

- **Spec 009 Branch C** (2026-05-09; PR #184): WC-10 continuous-scalar mode in **bin-then-output ergonomic-only** mode. New PARAMS key `wc_10_internal_only=True` keeps 5-tier external interface while preserving continuous internal representation for audit. Ships at the operator level via PARAMS only (NOT exposed in `daily_signals.py`). Activated per WC-10 v2 SC-005(b) NULL verdict (Pearson r +0.0918; n=100).

### Constitution amendments (3)

- **v1.5.0 (2026-05-08; PR #131)**: "Schema-induced abstention is NOT calibrated abstention" sub-section added to Principle VII per WC-10 v1 ALT-A confirmation (3.6× commit ratio at the 5-tier-vs-continuous-scalar PM stage).
- **v1.5.1 (2026-05-08 evening; PR #154)**: "Bear-regime validation" paragraph per WC-10 v3 PARTIAL ALT-A on Q4 2025 NVDA (α delta -0.22pp within ±100bps NULL region).
- **v1.5.2 (2026-05-09; PR #179)**: "Analyst-order scope" paragraph per WC-11 v1 PARTIAL ALT-A + ALT-B verdict; mandates randomize-or-document for future commit-rate ablations.

### Research arcs CLOSED (1)

- **WC-10 research arc** (v1 + v2 + v3 + Spec 009 Branch C): closed at $54.40 LLM total. Schema-induced collapse confirmed at PM stage; ALT-A generalizes 5/8 tickers; SC-005(b) NULL on combined v1+v2 (n=100) → bin-then-output Branch C selected. 4 ratified Constitution sub-sections + 1 production-deployment branch.

### Retrospectives closed (5 SKIP/DEFER + 2 PASS) — Constitution VIII v1.4.1 methodology validations

- **Class 4 BEAR macro retrospective** (PR #193): PASS → became Spec 012
- **Class 5 BULL fundamentals-delta** (PR #191 + #202 re-run): SKIP per v1.4.3 additive gate (89% Spec 007 overlap; union HURTS net Δα -4.09pp)
- **Class 4 BULL macro retrospective** (PR #203): SKIP — asymmetric to bear-side; mechanism is stock-specific not macro
- **Local-high BULL retrospective** (PR #205): DEFER — POTENTIAL PASS at n=2 floor only; needs corpus growth to 150+
- **bear-side mechanism class survey complete** (PR #93 from 2026-05-07): 6/6 evaluated; only C-4 institutional rotation spec-eligible

### Cleanup + audits (multiple)

- mypy floor 126 → 0 across 12 cleanup PRs (PR #128 4-line fix cleared 85 errors)
- 1 mypy regression introduced + fixed (PR #184 Branch C MVP introduced; PR #195 fixed)
- 1 script bug fixed (sector_alpha_attribution dual CSV schema; PR #204)
- 4 audit-pass cleans (Constitution v1.5.2 xref CLEAN PASS PR #210; Spec 011 candidate audit NO CANDIDATE PR #213)

### Filter portfolio: 8 → 10 production sides

| Filter | Default | Empirical support |
|---|---|---|
| A3 momentum | ON @ -5%/30d | +0.70pp/n=43 |
| Spec 003 contrarian gate | ON @ 80th pct | +0.65pp/n=11 |
| Spec 003.5 sector-baseline fallback | ON | Cold-start coverage |
| Spec 004 sector-momentum | OFF | -0.45pp/n=73 anti-pred |
| Spec 006 bear-sector-symmetry | OFF | -0.71pp/n=36; SC-008 FAILED |
| Spec 007 forward-catalyst BULL | ACTIVE @ T=0.60 | +14.43pp discrim / +2.24pp Δα |
| Spec 007 forward-catalyst BEAR | SHADOW @ T=0.50 | +23.10pp discrim / +0.30pp Δα |
| Spec 008 Hybrid C calendar boost | OFF (operator opt-in) | +3.35pp Δα improvement vs Class 3 alone |
| **Spec X-1 institutional rotation BEAR** (NEW since v0.8.1) | SHADOW @ T_outflow=0.05 | +5.41pp net Δα / 75% hit on n=12 |
| **Spec 012 Class 4 macro BEAR** (NEW since v0.8.1) | SHADOW @ VIX<18 | +24.07pp net Δα / 75% hit on n=8 |

## Stats

| Metric | v0.8.1 → v0.12.0 |
|---|---:|
| PRs merged (cumulative across the arc) | ~150+ |
| Tests | ~1022 → **1193** (+171) |
| Filter portfolio | 8 → **10 production sides** |
| Constitution version | 1.4.3 → **1.5.2** (+5 amendments) |
| Specs deployed | 2 (Spec X-1 + Spec 012) |
| LLM cost across arc | ~$53 (~$5 per ship-quality unit; cumulative ~$0.55) |
| mypy code regressions | 0 (1 introduced + fixed) |
| ruff floor | 0 errors maintained |

## In-flight (NOT included in v0.12.0 tag)

- **WC-11 v2 disambiguation** (`bwzris458`; ETA 2026-05-10): 60 propagates / $24
- **BR-3 v2 sister extensions** (`bkpnb5www`; ETA 2026-05-10): 40 propagates / $16

These pilots will land tomorrow + their landing arc (~8 PRs per dual-pilot landing template PR #218) targets the next minor version (v0.13.x).

## Tagging instructions

After this PR merges, apply the tag from the merge commit:

```bash
# On main, after merging this PR
git checkout main
git pull origin main
git tag -a v0.12.0-spec-012 -m "v0.12.0 — Spec 012 Class 4 macro-environment filter (FIRST cross-asset/macro filter; default-shadow bear) + WC-10 research arc CLOSED + Constitution v1.5.0/v1.5.1/v1.5.2 amendments + Spec X-1 institutional rotation filter shipped 2026-05-07"
git push origin v0.12.0-spec-012
```

The tag is rollback-safe via `git tag -d v0.12.0-spec-012 && git push origin :refs/tags/v0.12.0-spec-012` if needed.

## Cross-references

- Prior tag: `v0.8.1-spec-008.5` (2026-05-07)
- This release ships: PRs #88-#93 (Spec X-1) + PRs #117-#173 (2026-05-08 mypy + WC-10 arc) + PRs #179-#220 (2026-05-09 triple-pilot landing + Spec 012 + retrospectives + audits)
- Day-arc records: `claudedocs/research-burst-2026-05-07.md` + `research-burst-2026-05-08.md` + `research-burst-2026-05-09.md`
- WC-10 arc retrospective: `claudedocs/spec-009-branch-c-retrospective-2026-05-09.md` (PR #200)
- Spec 012 retrospective: `claudedocs/spec-012-class-4-deployment-retrospective-2026-05-09.md` (PR #200)
- Constitution v1.5.2 xref audit: `claudedocs/constitution-v1.5.2-xref-audit-2026-05-09.md` (PR #210)
