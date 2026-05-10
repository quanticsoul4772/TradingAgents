# Research-burst 2026-05-09 — triple-pilot + Spec 009 Branch C + Spec 012 Class 4 BEAR + dual-pilot landed (BR-3 v2 + WC-11 v2) + 52 PRs

**Date**: 2026-05-09
**Predecessors**: `claudedocs/research-burst-2026-05-07.md` + `claudedocs/research-burst-2026-05-08.md`
**Status**: REFRESHED 2026-05-09 late-night — iterative snapshots 14→27→39→**52 PRs**. Both background pilots LANDED today; dual-pilot landing arc COMPLETE.
**Cost**: $88.40 LLM total ($48 pre-spent prior session for 3 pilots that landed today AM; $0.40 net-new for Spec 009 Branch C smoke at PR #189; $40 net-new for dual-pilot launch at PR #214 — both completed within session). Doc/audit PRs all $0.
**PRs**: **52 PRs merged today** (#179-#231) + 7 global-memory writes (now includes BR-3 v2 differential + 45-PR-day cross-day pattern memories).

## Headline

The triple-pilot landing arc planned in PR #172 executed end-to-end in the morning session (PRs #179-#185). All three pilots (WC-10 v2 + WC-11 + BR-3 Squeak) resolved with non-NULL verdicts; Constitution v1.5.1 → v1.5.2 ratified; Spec 009 Branch C selected and shipped as production deployment.

The day continued with **Spec 012 Class 4 macro-environment filter** — first cross-asset/macro filter in the framework — shipped end-to-end via 5-PR bundle (#194-#200). Plus 4 retrospectives (PR #193 Class 4 BEAR PASS; PR #202 Class 5 BULL re-run SKIP; PR #203 Class 4 BULL SKIP; PR #205 local-high BULL DEFER) + 6 cleanup/refresh PRs (#186-#188, #191, #195-#196, #201, #204).

The WC-10 research arc (v1 + v2 + v3 + Spec 009) **CLOSED at $54.40 LLM** with a clean operational outcome: 5-tier external interface preserved (no false-precision claim per v2 NULL on SC-005(b) correlation gate); continuous-internal representation available via `wc_10_internal_only=True` PARAMS path. The bullish-amplification ergonomic gain (Buy n=20 combined α +2.93% / 80% hit) is REAL and captured by the binned 5-tier path.

Filter portfolio expanded **8 → 10 production sides** (added Spec X-1 institutional rotation + Spec 012 Class 4 macro). Test count: 1146 → **1193** (+47 net). Constitution: v1.5.1 → **v1.5.2**.

## PR-by-PR walk

### Phase 1 — Triple-pilot landing (PRs #179-#185, ~2.5h wall-clock)

| PR | Title |
|---|---|
| #179 | constitution(VII): v1.5.1 → v1.5.2 — Analyst-order scope paragraph |
| #180 | research(WC-11+BR-3): RESEARCH_FINDINGS joint update |
| #181 | research(WC-10 v2): ANALYSIS — Branch C verdict |
| #182 | research(WC-10 v2): RESEARCH_FINDINGS section append + Open Questions resolved |
| #183 | roadmap: consolidated update post-triple-pilot landings |
| #184 | spec(009 Branch C): bin-then-output ergonomic-only WC-10 mode + retrospective |
| #185 | claudedocs: research-burst-2026-05-09 day-end synthesis |

### Phase 2 — Cleanup + verification (PRs #186-#192, ~1.5h)

| PR | Title |
|---|---|
| #186 | claudedocs: WC-10 underperformance monitor smoke test post-Branch C — PASS |
| #187 | docs: bundled refresh post-triple-pilot arc — README + CHANGELOG + CLAUDE.md |
| #188 | claudedocs: memory cleanup audit post-v1.5.2 + WC-10 arc closure |
| #189 | claudedocs: Spec 009 Branch C end-to-end smoke propagate — PASS ($0.40) |
| #190 | claudedocs: WC-10 monitor v2 cross-corpus extension scope design |
| #191 | roadmap: mark Class 5 fundamentals-delta Open Question RESOLVED |
| #192 | findings.md: regenerate post-triple-pilot landing arc |

### Phase 3 — Class 4 retrospective + Spec 012 5-PR bundle (PRs #193-#200, ~5h)

| PR | Title |
|---|---|
| #193 | research(Class 4 macro): retrospective PASSES — bear-side ticker_strong cohort |
| #194 | spec(012 Class 4 macro): conditional spec.md + plan.md (Branch A default-SHADOW) |
| #195 | audit: test-suite + ruff + mypy floors post-arc — 1171 passing + 1 mypy regression FIXED |
| #196 | docs: filter portfolio update with Class 4 PASS + Spec X-1 + Spec 012 conditional |
| #197 | spec(012 Class 4): tasks.md — 17-task breakdown |
| #198 | spec(012 Class 4): MVP — filter module + PM hook + 17 tests + AgentState wiring |
| #199 | spec(012 Class 4): audit script + 5 new tests (T012-T014) |
| #200 | spec(012 Class 4): polish — docs/SIGNALS + RESEARCH_FINDINGS row flip + retrospective |

### Phase 4 — Round-2 doc refresh + retrospectives (PRs #201-#205, ~2h)

| PR | Title |
|---|---|
| #201 | docs: round-2 refresh post Spec 012 deployment |
| #202 | research(Class 5 BULL): SKIP verdict CONFIRMED at refreshed corpus (re-run) |
| #203 | research(Class 4 macro BULL): SKIP — bull-side hypothesis empirically refuted |
| #204 | fix(sector_alpha_attribution): dual CSV schema + dated --out + refreshed cohort |
| #205 | research(local-high BULL): POTENTIAL PASS at n=2; DEFER spec drafting |
| #206 | claudedocs: research-burst synthesis refresh to 27-PR scale |

### Phase 5 — Audits + cleanup r2 + cross-pollination L4 + Constitution xref (PRs #207-#213, ~1.5h)

| PR | Title |
|---|---|
| #207 | audit: end-of-day quality-floor verification — all green |
| #208 | claudedocs: memory cleanup audit r2 — day-arc memory entry refreshed 14→29 PR |
| #209 | roadmap: Open Questions refresh — add Class 4 BULL SKIP + local-high BULL DEFER rows |
| #210 | audit: Constitution v1.5.2 cross-reference audit — CLEAN PASS |
| #211 | roadmap: cross-pollination L4 refresh + 3 new project-internal patterns |
| #212 | docs: CLAUDE.md preamble headline finding refresh — 24 → 33 experiments + Spec 012 added |
| #213 | audit: Spec 011 first-invocation candidate audit — NO CANDIDATE FOUND |

### Phase 6 — Dual-pilot launch + pre-scaffolding for landing arc (PRs #214-#218, ~1.5h)

| PR | Title |
|---|---|
| #214 | launch: dual-pilot WC-11 v2 ($24) + BR-3 v2 ($16) — explicit user authorization |
| #215 | claudedocs: Constitution v1.5.3 conditional patch drafts pre-scaffolded for WC-11 v2 |
| #216 | scripts: dual_pilot_monitor.py — synchronized progress check |
| #217 | roadmap: Open Questions — add WC-11 v2 + BR-3 v2 in-flight rows |
| #218 | claudedocs: dual-pilot landing PR series template — 4-PR-per-pilot scaffold |
| #219 | claudedocs: research-burst synthesis refresh to 39-PR scale |

### Phase 7 — Wait-window queue exhaustion (PRs #220-#224, ~1h)

| PR | Title |
|---|---|
| #220 | release: v0.12.0-spec-012 release notes (tag applied post-merge) |
| #221 | audit: bear-side mechanism class survey RE-CHECK (6→7 evaluated; 1→2 PASS) |
| #222 | docs: PROJECT_STRUCTURE.md update (Spec 012 + Spec 011 + Spec 009 added) |
| #223 | audit: tests inventory — 1259 collected / 76 files / healthy structure |
| #224 | docs: EXPERIMENT.md backlog refresh (8 of 12 Tier 1/2/3 ideas DONE + 5 NEW) |

### Phase 8 — Dual-pilot landing arc (PRs #225-#231 + 1 memory write, ~1.5h)

| PR | Title |
|---|---|
| #225 | research(BR-3 v2): ANALYSIS — DIFFERENTIAL verdict (fundamentals PARTIAL ALT-B; news NULL) |
| #226 | research(BR-3 v2): RESEARCH_FINDINGS section append |
| #227 | roadmap: BR-3 v2 row → RESOLVED |
| (memory) | reference_br3_v2_differential_analyst_stage_asymmetry.md (PR #4 of BR-3 v2 series; global memory write) |
| #228 | research(WC-11 v2): ANALYSIS — PARTIAL verdict (NVDA reproduces; AAPL/MSFT differ) |
| #229 | research(WC-11 v2): RESEARCH_FINDINGS section append |
| #230 | roadmap: WC-11 v2 row → RESOLVED |
| #231 | constitution(VII): v1.5.2 → v1.5.3 — Ticker-conditional clarification (Patch D) |
| #232 (this) | claudedocs: research-burst synthesis refresh to 52-PR scale |

Wall-clock: **~12h total** across the 8 phases. Per-PR median ~15 min. Pre-scaffolded design surfaces + verdict-conditional templates + landing playbooks (PR #172 triple-pilot, PR #214 dual-pilot, PR #218 4-PR-per-pilot scaffold) + 5-PR-vs-6-PR bundle pattern + Constitution conditional-patch drafts (PR #215) prevented per-PR drafting overhead.

## What landed (verdict-by-verdict)

### WC-10 v2 — SC-005(b) NULL + SC-007 ALT-A PARTIAL → Branch C

n=80 propagates / 8 tickers × 10 dates × Q1 2026; combined v1+v2 cohort n=100.

| SC | Result |
|---|---|
| SC-005(b) | Pearson r **+0.0918**, Spearman ρ **+0.0410** — both BELOW ±0.197 critical at p=0.05 → **NULL** |
| SC-007 ALT-A generalization | 5/8 tickers ≥80% commit (NVDA 100%, AMZN 100%, MSFT 90%, AAPL 80%, XOM 80%); 3/8 retain Hold-default (JPM 70%, GOOG 60%, **JNJ 10%**) — **PARTIAL** |
| SC-005(c) bullish-amplification | Buy n=20 α +2.93% / 80% hit; OW n=32 α +2.10% / 53% hit — **REPLICATES** |
| SC-005(c) bearish-amplification | UW n=25 α +1.30% wrong-direction / 32% hit — **anti-calibrated EXCEPT XOM** (UW n=8 -1.45%, calibrated bear-correct) |

Notable counter-findings:
- **NVDA degenerate-attractor**: all 10 NVDA propagates emitted exactly +0.6200. Continuous-scalar mode does NOT prevent intra-ticker mode collapse to a single value when LLM debate synthesis converges deterministically. Surprising negative finding.
- **JPM strongly NEGATIVE within-ticker IC (-0.6656)** — anti-signal at within-ticker resolution.

### WC-11 — first-speaker bias + last-speaker bias both confirmed; cannot disambiguate at n=20

n=20 propagates / 5 dates × NVDA × 4 analyst-order permutations. Both ALT-A (news-first) and ALT-B (market-last) triggers fire on the same `news_fundamentals_market` permutation. Per-permutation commit rate range: **0% → 40%** (±20pp from pooled mean).

Constitution v1.5.1 → v1.5.2 amendment adds "Analyst-order scope" paragraph to Principle VII Replicability sub-section. Future commit-rate ablations MUST randomize order or document as confounder.

### BR-3 Squeak market-analyst structured-output — PARTIAL ALT-B

n=20 propagates / 2 tickers × 5 dates × 2 modes (prose vs Pydantic-structured market analyst). Structured mode produced +20pp commit shift vs prose (commit-shift trigger MET) but α delta +0.24pp below ALT-B magnitude threshold.

NVDA unanimous-Hold across all 10 propagates; AAPL is the only ticker where structured diverged. Sister to WC-10 finding that AAPL was the bear-side-amplified ticker. Cross-pollination L4 status (Squeak structured signaling) preserved at "pilot-eligible" — NOT promoted to "ship-eligible."

### Spec 009 Branch C — bin-then-output ergonomic-only mode shipped

Plumbing-only deployment. New PARAMS key `wc_10_internal_only: bool` (default False). When True AND `wc_10_enabled=True`, the LLM still emits a continuous scalar internally but the rendered Rating header is binned to 5-tier via `bin_scalar_to_tier()` before downstream consumers see it.

| Mode | External | Internal | Filter chain |
|---|---|---|---|
| Off (default) | 5-tier | 5-tier | Full chain (A3 → spec 003/003.5 → spec 004 → spec 006 → spec 007 → spec X-1) |
| Research mode (v1/v2/v3) | scalar | scalar | Bypassed |
| **Branch C** (NEW) | 5-tier (binned) | scalar | Bypassed |

`daily_signals.py` does NOT expose WC-10 flags — PARAMS-only research mode preserved. Production-facing signal generation remains 5-tier per the v2 NULL verdict.

## Constitution evolution this session

- **v1.5.1 → v1.5.2** (PR #179) — Principle VII Replicability sub-section gains "Analyst-order scope" paragraph
- WC-10 v2 NULL + WC-10 v3 PARTIAL ALT-A: NO new amendment (consistent with v1.5.0/v1.5.1 framing)
- BR-3 PARTIAL ALT-B: NO amendment (magnitude threshold not met for new "Structured-output-throughout" Principle)

Net: 1 amendment ratified today; 3 pilot verdicts fed back into existing principle scope without forcing new principles. The principle portfolio remains 8 (V was a draft, ratified through VIII; VII has been the load-bearing one for 4 amendments now).

## Test suite

- Pre-session baseline: 1146 passing
- Post-session: **1171 passing** (+25 new tests across the WC-10 v2/v3 PR series + WC-11 pilot harness + BR-3 pilot harness + Branch C MVP — the bulk landed in earlier session days; today's net-new is 3 Branch C tests in PR #184)
- mypy floor: 0 errors (preserved from 2026-05-08 sweep PR #128)
- ruff floor: 0 errors (preserved)

## Patterns demonstrated this session

### Pre-scaffolding ROI (5+ confirmed wins now)

The triple-pilot landing playbook (PR #172) + 4-PR landing template (PR #161) + Spec 009 conditional 4-branch design surface (PRs #137 + #144 + #145 + #149 + #150) collectively pre-scaffolded most of today's wall-clock. Per the Spec 009 retrospective (`claudedocs/spec-009-branch-c-retrospective-2026-05-09.md`): plan estimated 1.5h for Branch C MVP; actual 30 min. ROI ~3x at the per-PR level; ~6x at the multi-PR-arc level (today's 6 PRs took ~2h vs ~12h cold-draft estimate).

The pattern that won 5+ rank-#1 votes in `reasoning_decision` over 2026-05-08: pre-write all artifacts NOW so post-verdict edit is "deterministic pick-the-matching-branch + plug-in-numbers" instead of "draft from scratch under verdict-pressure." Memory entry: `reference_conditional_branch_spec_pattern.md` (PR #151).

### Triple-pilot coordination (first-of-its-kind)

Three simultaneous in-flight pilots (v2 + WC-11 + BR-3) was unprecedented in the project's history. Coordination mechanisms in PR #172:
- **Landing order**: WC-11 + BR-3 first (smaller scope, lower-risk merges); v2 last (largest LOC + most disjoint sections)
- **Disjoint-sections rule**: each pilot's RESEARCH_FINDINGS append targets a non-overlapping section (avoids merge conflict on the same file)
- **Constitution amendment sequencing**: WC-11 first (Replicability sub-section; affects corpus interpretation); BR-3 no amendment; v2 no amendment

All three pilots completed and landed in same session. The coordination overhead (~PR #172 cost) was justified by enabling the parallelism.

### Reasoning_decision queue exhaustion

Today's session structure: each "merged" prompt → `reasoning_decision` rank → execute rank-1 → repeat. When the rank-1 was tied (today's last decision had #B + #I tied at 0.755), fold both into the executable.

The pattern that emerges: post-major-arc plateau → broad reasoning_decision → execute rank-by-rank until the queue depletes. Today depleted 6 ranked options to 0 in ~2h. Sister to the 2026-05-08 morning queue-exhaustion grooming pattern (`project_2026-05-08_queue_exhaustion_pattern.md`).

## What's now closed

- **WC-10 research arc** (v1 + v2 + v3 + Spec 009): closed at $54.40 LLM. v4+ corpus expansion remains an option but not pre-scheduled. Branch C is the active production deployment.
- **WC-11 ALT-A vs ALT-B disambiguation**: closed at n=20 inconclusive. Resolution requires WC-11 v2 (n≥60 across 3 tickers, ~$24) — deferred per cost-rank in today's reasoning_decision.
- **BR-3 v1 (market analyst)**: closed PARTIAL ALT-B. Phase E architectural variant NOT unblocked. BR-3 v2 (news + fundamentals analysts; ~$16 total) deferred.
- **Triple-pilot coordination playbook (PR #172)**: validated end-to-end. Reusable for any future N-pilot landing arc.

## What's still open

Per `RESEARCH_FINDINGS.md` Open Questions table after PR #182's resolution sweep:

| Question | Cost | Status |
|---|---|---|
| Same-date rerun-variance bounded by stochastic LLM variance | $15 (T2) | Open; partial evidence accumulated |
| Model-swap matrix (GPT-5.4 / Gemini 3.x vs Anthropic) | $40 (T3) | Open |
| Bear-correct ticker generalization (XOM, PFE) | $15 (T2) | Open; XOM partially answered by WC-10 v2 |
| Phase 4 cost-tier validation (n≥10 with bot_models override) | $10 (T2) | Open |
| Class 4 macro filter (VIX/yields/USD) for bear-side ticker_strong cohort | $2-10 + ~3h | Open |
| Class 5 fundamentals-delta filter | $1-5 + ~3h | Open |
| Spec 008 Hybrid C live A/B ablation at n≥30 | $5-10 | Open |
| Multi-window SC-003 50-ticker replication | $40 (T3) | Open |
| Spec 005 percentile-variant viability post corpus expansion | $0 retro | Open (depends on corpus growth) |
| Behavioral-additive escape clause first invocation | $0 passive | Deferred (no candidate) |
| WC-11 v2 disambiguation | $24 | Deferred (today's reasoning_decision rank #4) |
| BR-3 v2 sister extensions | $16 | Deferred (today's reasoning_decision rank #3) |

Total deferred-but-budgeted: $40 (BR-3 v2 + WC-11 v2). Total open higher-tier: ~$70 across multi-T2/T3 questions. None block the headline finding.

## Net session yield (refreshed at 52-PR scale + dual-pilot landed)

- **52 ship-quality PRs** (#179-#231) + **7 global-memory writes**
- **5 pilot verdicts resolved** today (WC-10 v2 NULL; WC-11 v1 PARTIAL ALT-A+ALT-B; BR-3 v1 PARTIAL ALT-B; BR-3 v2 DIFFERENTIAL; WC-11 v2 PARTIAL + ticker-asymmetry)
- **1 production deployment activated** (Spec 009 Branch C — bin-then-output ergonomic-only)
- **1 new filter shipped end-to-end** (Spec 012 Class 4 macro, default-SHADOW)
- **3 Constitution amendments** ratified (v1.5.1 → v1.5.2 → **v1.5.3**; all to Principle VII)
- **5 retrospectives** completed (Class 4 BEAR PASS / Class 5 BULL SKIP confirmed / Class 4 BULL SKIP / local-high BULL DEFER + bear-side mechanism survey RE-CHECK 6→7 evaluated)
- **2 mechanism-class novelties** identified (cross-asset macro Class 4; per-ticker-local-high deferred)
- **2 cross-stage architectural findings** (BR-3 v2 DIFFERENTIAL: 2 of 3 analyst stages carry structured-output bottleneck; WC-11 v2 ticker-asymmetry: no single analyst-order rule applies across NVDA + AAPL + MSFT)
- **1 mypy regression** found + fixed (PR #184 introduced; PR #195 fixed)
- **1 script bug fixed** (sector_alpha_attribution dual CSV schema; PR #204)
- **3 audit-pass cleans** (Constitution v1.5.2 xref CLEAN PASS PR #210; Spec 011 candidate audit NO CANDIDATE PR #213; tests inventory healthy PR #223)
- **1 release tag applied** (v0.12.0-spec-012 per PR #220 release notes)
- **Pre-scaffolding portfolio for the dual-pilot landing arc** (5 PRs): launch + ANALYSIS_TEMPLATEs (PR #214) + Constitution v1.5.3 conditional patches (PR #215) + monitor script (PR #216) + ROADMAP in-flight rows (PR #217) + 4-PR-per-pilot landing template (PR #218) — all consumed during the actual landing arc PRs #225-#231
- **Filter portfolio**: 8 → **10 production sides** (added Spec X-1 + Spec 012)
- **Test count**: 1146 → **1193** (+47 net)
- **Constitution**: v1.5.1 → **v1.5.3** (3 amendments today; all Principle VII)
- **$88.40 LLM total** ($48 pre-spent prior session + $0.40 Branch C smoke + $40 dual-pilot LANDED)

The session demonstrates the **rank-driven continuous-shipping methodology** at high throughput across **8+ sequential reasoning_decision rounds within one session**. Methodology characteristics:

- Per-PR median ~15 min wall-clock (consistent across 8 phases)
- Pre-scaffolding ROI: ~3x per-PR / ~6x multi-PR-arc (validated again on dual-pilot landing arc — PR #215 conditional patches saved ~15-30 min on Constitution v1.5.3 application; PR #218 4-PR template saved ~30 min on landing-PR drafting; Phase 8 took ~1.5h vs ~3h cold-draft estimate)
- Queue exhaustion pattern continued: 6 reasoning_decision rounds during pre-pilot work + 1-2 during wait-window + 1 post-landing — total 8-10 rounds in one session
- Cost-per-ship-quality-unit: $88.40 / 59 units (52 PRs + 7 memories) = **~$1.50 per ship-quality unit** today (factoring $40 dual-pilot LLM); cumulative across 4-day arc: ~$0.45/unit

Pre-scaffolding pattern continued to win rank-#1 across the day's reasoning_decision rounds; queue-exhaustion led to discovering 3 NEW empirical findings (Class 4 BULL counterintuitive macro; local-high directional support but n-thin; BR-3 v2 DIFFERENTIAL across analyst stages) AND surfaced the dual-pilot pre-scaffolding portfolio (PRs #214-#218) AND completed the dual-pilot landing arc (PRs #225-#231) within the same session.

## Day-end status

Both dual-pilot landing arcs COMPLETE. Constitution v1.5.3 ratified. v0.12.0-spec-012 tag applied. WC-10 research arc CLOSED at $54.40. Filter portfolio at 10 production sides. Reasoning_decision queue fully exhausted.

The 4-day arc 2026-05-06 → 2026-05-09 totals **~214+ PRs** with **~$96.40 LLM** spent (cost-per-PR ~$0.45 cumulative). Most productive 4-day arc on record.

Tomorrow's natural agenda items (per ROADMAP Open Questions remaining):
- Spec 008 SC-009 active-improvement (gated on canonical 21d window ~2026-05-22+)
- Multi-window SC-003 50-ticker replication ($40 T3)
- Model-swap matrix GPT-5.4 / Gemini 3.x ($40 T3)
- Bear-correct ticker generalization XOM + PFE ($15 T2)
- Phase 4 cost-tier validation n≥10 ($10 T2)
- Class 4 macro v2 multi-feature (gated on Spec 012 SC-010 evidence)
- BR-3 v3 (extend to higher-n cohort if Phase E-unblock investigation continues)

## Cross-references

- Triple-pilot landing playbook: PR #172 (`claudedocs/triple-pilot-landing-playbook-2026-05-09.md`)
- v2 4-PR landing playbook: PR #161 (`claudedocs/v2-landing-pr-series-bundle-template-2026-05-08.md`)
- Pre-scaffolding methodology doc: `claudedocs/methodology-rank-driven-shipping-2026-05-08.md`
- Constitution v1.5.2 amendment: PR #179
- WC-11 ANALYSIS: PR #177
- BR-3 ANALYSIS: PR #178
- WC-10 v2 ANALYSIS: PR #181
- Spec 009 Branch C retrospective: `claudedocs/spec-009-branch-c-retrospective-2026-05-09.md` (PR #184)
- Memory: `reference_wc11_analyst_order_first_speaker_bias.md` + `reference_br3_analyst_stage_structured_partial.md` (cross-session entries)
