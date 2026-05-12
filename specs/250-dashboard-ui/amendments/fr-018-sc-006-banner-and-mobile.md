# Amendment: FR-018 (no banner) + SC-006 (any operator-used browser)

**Spec**: 250-dashboard-ui
**Gaps**: G-4 (FR-018), G-7 (SC-006) per `plan.md`
**Tasks**: T015 + T016 per `tasks.md`
**Date**: 2026-05-11
**Status**: Operator-directed amendment. Authorization captured below.

## Operator authorization

The operator directed on 2026-05-11 that the FR-018 banner mandate and the SC-006 iOS-Safari validation requirement should both be removed from the spec, not papered over as "accepted deviations." This amendment executes that direction by changing the spec wording. It replaces the rejected PR #271, which had attempted to retcon both as accepted deviations without amendment.

## Amendment 1 — FR-018: drop banner mandate

### Original (line 137)

> **FR-018**: All pages MUST display the "Simulation only — not financial advice" banner per Constitution Principle IV.

### New

> **FR-018** *(amended 2026-05-11 per `amendments/fr-018-sc-006-banner-and-mobile.md`)*: No banner mandate. The dashboard is a single-operator surface gated by Caddy basic-auth; the "Simulation only — not financial advice" banner serves no protective function for the actual user. Constitution Principle IV remains satisfied by the paper-only architecture (no real-money trading integration; FR-007 paper_trade.py is the only signal consumer).

### Constitution Adherence section update (line 240)

Original:

> - **Principle IV (No Production Claims)**: dashboard banner "Simulation only — not financial advice." Paper-only. (FR-018)

New:

> - **Principle IV (No Production Claims)**: paper-only — no real-money trading integration anywhere in the system. The previous banner mandate (original FR-018) was dropped 2026-05-11 because a single-operator basic-auth-gated dashboard does not need an audience-facing disclaimer. The protective invariant (paper-only, no real broker integration) is preserved by the architecture itself.

## Amendment 2 — SC-006: drop iOS-Safari requirement

### Original (line 206)

> **SC-006**: Mobile responsive — real iOS Safari (not Chrome devtools emulator) renders all pages correctly; polling works over cellular; layout is usable in phone-portrait orientation.

### New

> **SC-006** *(amended 2026-05-11 per `amendments/fr-018-sc-006-banner-and-mobile.md`)*: Mobile responsive — the dashboard renders correctly on the operator's actual mobile browser (any modern phone browser; the operator does not use iOS). Polling works over cellular; layout is usable in phone-portrait orientation. Validation is performed by the operator on their own device once per spec change that touches the mobile layout.

## Why amend, not refactor

For both:
- The operator is the only user. iOS-specific constraints + a financial-disclaimer banner both target user populations that don't exist for this system.
- Original spec wording reflected a default assumption (multi-user dashboard, iPhone operator); the actual deployment is single-operator, non-iPhone.
- Keeping the original spec wording while shipping non-compliant code is the failure mode the operator just called out (sweeping deviations under the rug). Amending the spec to match the actual deployment is the correct closure pattern.

## Plan.md updates that follow

- G-4 row: marked CLOSED via amendment (was: ACCEPTED DEVIATION in the rejected PR #271)
- G-7 row: marked CLOSED via amendment (was: ACCEPTED DEVIATION in the rejected PR #271)
- Constitution Check row IV: flipped from ❌ VIOLATION to ✅ COMPLIANT (the amendment removes the banner mandate; paper-only architecture satisfies Principle IV directly)

## Out of scope for this amendment

- **G-8 (FR-005 graph.astream)**: operator directed a code refactor (not an amendment). Shipped as a separate PR (PR-E in the new sequence).
- **G-12 (FR-033 systemd version-check)**: trivial deploy doc fix, shipped as part of the next PR.
- **G-6 (SC-007 live-run validation)**: operator-gated, auto-completes when tonight's VPS run finishes.
