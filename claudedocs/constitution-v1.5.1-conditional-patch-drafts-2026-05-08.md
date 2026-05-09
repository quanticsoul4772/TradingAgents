# Constitution v1.5.1 conditional patch drafts — 2026-05-08

> **STATUS**: PRE-VERDICT DRAFTS. WC-10 v3 (bear-regime Q4 2025 NVDA) in flight; ETA ~1h. When v3 lands, pick the matching patch below + apply via `/speckit.constitution` or hand-edit `.specify/memory/constitution.md`.

**Trigger**: reasoning_decision rank #5 (0.63 score). Pattern parallels Spec 009 conditional-branch drafting (PR #140) — pre-write the patch surface NOW so the post-verdict edit is a deterministic pick rather than a draft-from-scratch exercise.

**Scope**: each patch updates Constitution VII v1.5.0 sub-section "Schema-induced abstention is NOT calibrated abstention" with the v3 empirical evidence. The exact tier (PATCH v1.5.1 vs MINOR v1.6.0) depends on whether the patch tightens, loosens, or significantly reshapes the carve-out scope.

## v3 verdict matrix → patch selection

| v3 verdict | Implication for v1.5.0 caveat | Patch tier | Patch ID |
|---|---|---|---|
| **NULL** (regime-neutral; mean_α delta ≈ 0) | Caveat MAY BE OVER-CAUTIOUS — schema fix is regime-neutral | **PATCH v1.5.1** | Patch B |
| **ALT-A** (bear-regime AMPLIFIES failure; mean_α(WC-10) − mean_α(5-tier) ≤ −100bps) | Caveat STRENGTHENED — bear-regime validation IS load-bearing | **PATCH v1.5.1** | Patch A |
| **ALT-B** (bear-regime CORRECTS direction; mean_α delta ≥ +100bps) | Caveat WEAKENED — WC-10 may surface direction-correct signal independent of regime | **PATCH v1.5.1** | Patch C |
| **PARTIAL ALT-A** (direction matches ALT-A but α delta < 100bps) | Caveat CONFIRMED at predicted scope | **PATCH v1.5.1** | Patch D |

All four patches are PATCH-tier (v1.5.1) per the existing scope-narrowing rule — none introduce new principles, all refine the empirical scope of an existing carve-out.

---

## Patch A — v3 verdict ALT-A (bear-regime amplifies failure)

**Apply when**: v3 ANALYSIS.md headline reads "ALT-A confirmed" — `mean_α(WC-10) − mean_α(5-tier) ≤ −100bps` on Q4 2025 NVDA cohort.

**Edit target**: `.specify/memory/constitution.md` Principle VII sub-section "Schema-induced abstention is NOT calibrated abstention" → append the following paragraph after the existing **WC-10 caveat (signal calibration is asymmetric)** paragraph:

```markdown
**Bear-regime validation (added 2026-05-XX, post-WC-10 v3)**: WC-10 v3
(Q4 2025 NVDA cohort, n=8 paired) confirms that the asymmetric-calibration
caveat is REGIME-CONDITIONAL, not just cohort-conditional. On Q4 2025
NVDA — where the framework's commits historically failed (-0.47% mean
21d α, 22% hit per RESEARCH_FINDINGS headline) — WC-10 mode produced
mean 21d α of <FILL: WC-10 mean>% vs 5-tier baseline's <FILL: baseline
mean>%, a delta of <FILL: delta>pp WORSE under WC-10 mode. The schema
fix amplifies the framework's existing reads regardless of whether
those reads are direction-correct; in bear regimes where the framework
reads wrong, WC-10 makes outcomes worse.

**Operational implication for production deployment**: any operator
opt-in WC-10 mode (per Spec 009 Branch A or future) MUST include
regime-aware gating. The carve-out applies to bull regimes where the
schema bottleneck causes under-commitment; it does NOT apply to bear
regimes where the framework reads wrong. Spec 009 Branch A activation
requires a regime-detection signal (e.g., `vix > 25` heuristic or per-
ticker trailing-α signal) that disables WC-10 in bear regimes.
```

**Version bump**: v1.5.0 → **v1.5.1** (PATCH per scope-narrowing — empirical bound added, principle scope unchanged).

**Header update at top of constitution.md**:
```markdown
**Last amended**: 2026-05-XX — added "Bear-regime validation" paragraph
to Principle VII sub-section "Schema-induced abstention is NOT
calibrated abstention" after WC-10 v3 ALT-A confirmation. Empirical
basis: experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/
ANALYSIS.md showed mean 21d α delta of <X>pp WORSE under WC-10 mode
on Q4 2025 NVDA. Operational implication: WC-10 production deployment
requires regime-aware gating. v1.5.0 → v1.5.1 (PATCH per scope-
narrowing rule).
```

---

## Patch B — v3 verdict NULL (regime-neutral)

**Apply when**: v3 ANALYSIS.md headline reads "NULL" — `|mean_α(WC-10) − mean_α(5-tier)| < 100bps` on Q4 2025 NVDA cohort.

**Edit target**: same Principle VII sub-section → append the following paragraph after the existing **WC-10 caveat** paragraph:

```markdown
**Bear-regime validation (added 2026-05-XX, post-WC-10 v3)**: WC-10 v3
(Q4 2025 NVDA cohort, n=8 paired) shows the asymmetric-calibration
caveat from v1 may have been OVER-CAUTIOUS. On the historical Q4 2025
NVDA cohort, WC-10 mode produced mean 21d α of <FILL: WC-10 mean>%
vs 5-tier baseline's <FILL: baseline mean>%, a delta of <FILL: delta>pp
— statistically indistinguishable from baseline at this n. The schema
fix is regime-NEUTRAL on this cohort, not regime-amplifying-bad. The
v1 AAPL UW anti-calibration finding may have been a single-cohort
artifact rather than a universal bear-side mechanism.

**Operational implication**: production WC-10 deployment (Spec 009
Branch A) does NOT require regime-aware gating per this evidence. The
asymmetric-calibration caveat is preserved for documentation but
weakened from a hard requirement to a "monitor and adjust if observed
in production" caveat.
```

**Version bump**: v1.5.0 → **v1.5.1** (PATCH per scope-narrowing — caveat scope tightened, principle unchanged).

**Header update**:
```markdown
**Last amended**: 2026-05-XX — added "Bear-regime validation" paragraph
to Principle VII sub-section after WC-10 v3 NULL verdict. Empirical
basis: experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/
ANALYSIS.md showed mean 21d α delta of <±X>pp on Q4 2025 NVDA —
indistinguishable from baseline. Caveat weakened from hard requirement
to monitor-and-adjust. v1.5.0 → v1.5.1 (PATCH per scope-narrowing rule).
```

---

## Patch C — v3 verdict ALT-B (bear-regime corrects direction)

**Apply when**: v3 ANALYSIS.md headline reads "ALT-B" — `mean_α(WC-10) − mean_α(5-tier) ≥ +100bps` on Q4 2025 NVDA cohort, AND ≥30% of WC-10 commits bin to UW/Sell (i.e., the framework actually went bearish under continuous-scalar mode where 5-tier didn't).

**Edit target**: same Principle VII sub-section → append the following paragraph:

```markdown
**Bear-regime validation (added 2026-05-XX, post-WC-10 v3)**: WC-10 v3
(Q4 2025 NVDA cohort, n=8 paired) shows the asymmetric-calibration
caveat from v1 was WRONG in direction. On Q4 2025 NVDA, continuous-
scalar mode surfaced bearish reads that 5-tier suppressed: WC-10
emitted <FILL: N>/8 dates as Underweight (binned), while 5-tier
emitted <FILL: M>/8 as Overweight. Realized 21d α: WC-10 mean
<FILL: WC-10 mean>% vs 5-tier baseline's <FILL: baseline mean>%, a
delta of <FILL: delta>pp BETTER under WC-10 mode. The schema fix
surfaces direction-correct signal independent of regime — including
bearish signal that the 5-tier scale's Hold-default suppresses on
falling tickers.

**Operational implication for production deployment**: WC-10 mode is
universally beneficial across the bull/bear spectrum on this evidence
basis. Spec 009 Branch A may activate without regime-aware gating.
The v1 AAPL UW anti-calibration finding remains a NOTABLE counter-
case (the v1 cohort's bullish-rally regime may have been the actual
regime hostile to scalar UW commits), but Q4 2025 NVDA suggests the
bear-correct cohort BENEFITS from continuous-scalar bearish surfacing.
```

**Version bump**: v1.5.0 → **v1.5.1** (PATCH per scope-narrowing — empirical reversal of caveat direction, principle scope unchanged).

**Header update**:
```markdown
**Last amended**: 2026-05-XX — added "Bear-regime validation" paragraph
to Principle VII sub-section after WC-10 v3 ALT-B confirmation.
Empirical basis: experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-
nvda/ANALYSIS.md showed mean 21d α delta of +<X>pp BETTER under WC-10
mode on Q4 2025 NVDA. v1 AAPL UW caveat reframed as regime-specific
counter-case. v1.5.0 → v1.5.1 (PATCH per scope-narrowing rule).
```

---

## Patch D — v3 verdict PARTIAL ALT-A

**Apply when**: v3 ANALYSIS.md headline reads "PARTIAL ALT-A" — direction matches ALT-A (WC-10 commits more bullishly than 5-tier on the falling cohort) but `|α delta| < 100bps`.

**Edit target**: same Principle VII sub-section → append the following paragraph:

```markdown
**Bear-regime validation (added 2026-05-XX, post-WC-10 v3)**: WC-10 v3
(Q4 2025 NVDA cohort, n=8 paired) confirms the asymmetric-calibration
caveat at the predicted scope. On Q4 2025 NVDA — a regime where the
framework's bullish commits historically failed — WC-10 mode emitted
<FILL: N>/8 dates as Buy/OW (binned) vs 5-tier baseline's <FILL: M>/8
non-Hold. The realized 21d α delta was <FILL: delta>pp (within
±100bps of baseline; statistically indistinguishable at n=8). The
direction matches ALT-A (WC-10 amplifies the framework's bullish
reads on a falling cohort), but the magnitude is small enough that
the v1.5.0 caveat language ("WC-10 amplifies whatever signal the
framework was already generating") is correct as-written without
strengthening to "amplifies in a way that produces statistically
worse outcomes."

**Operational implication for production deployment**: Spec 009 Branch
A activation should ship with the v1.5.0 caveat documented but does
NOT require regime-aware gating as a hard requirement. The direction
of caution is correct; the magnitude is small enough that operator
discretion (per docs/SIGNALS.md warning section) is sufficient.
```

**Version bump**: v1.5.0 → **v1.5.1** (PATCH per scope-narrowing — empirical bound on caveat magnitude, principle scope unchanged).

**Header update**:
```markdown
**Last amended**: 2026-05-XX — added "Bear-regime validation" paragraph
to Principle VII sub-section after WC-10 v3 PARTIAL ALT-A verdict.
Empirical basis: experiments/2026-05-08-003-wc-10-bear-regime-q4-
2025-nvda/ANALYSIS.md showed direction matches ALT-A but |α delta|
< 100bps on Q4 2025 NVDA. Caveat language preserved at v1.5.0 scope;
empirical magnitude bound documented. v1.5.0 → v1.5.1 (PATCH per
scope-narrowing rule).
```

---

## Application workflow

When v3 lands:

1. Read v3 ANALYSIS.md headline verdict (NULL/ALT-A/ALT-B/PARTIAL ALT-A)
2. Pick matching patch (A/B/C/D) from this doc
3. Replace `<FILL: X>` placeholders with v3 ANALYSIS computed values
4. Apply edit to `.specify/memory/constitution.md` (Principle VII sub-section + header)
5. Open PR with title `constitution(VII): v3 bear-regime validation paragraph (v1.5.0 → v1.5.1; verdict <X>)`
6. Update `RESEARCH_FINDINGS.md` WC-10 section with v3 ANALYSIS cross-reference
7. Update `ROADMAP.md` Open Work / In-Flight section to mark v3 verdict landed

Estimated wall-clock from v3 ANALYSIS.md landing → PR open: **~15 minutes** (vs ~45 min if drafting from scratch).

## Cross-references

- Constitution v1.5.0 Principle VII sub-section "Schema-induced abstention is NOT calibrated abstention" (current state)
- `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/HYPOTHESIS.md` (3 predictions framework)
- `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS_TEMPLATE.md` (template that will populate the verdict)
- Spec 009 (`specs/009-wc-10-production-deployment/spec.md`) — its 4 verdict-conditional branches map to the 4 patches above (Branch A → Patch A, etc., one-to-one alignment with the verdict matrix)
- Memory `feedback_no_day_rollover_planning.md` — patches reference "2026-05-XX" placeholder for the application date; replaced with actual date when applied
