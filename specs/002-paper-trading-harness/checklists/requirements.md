# Specification Quality Checklist: Paper-Trading Harness

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-06
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — spec mentions `tradingagents.dataflows.returns.returns_from_frames` and `daily_signals.py --emit-csv` but only as integration points (existing code the harness must reuse, per FR-012); no internal-implementation language ("which dataclass," "what Pydantic model") in functional requirements
- [x] Focused on user value and business needs — operator outcomes drive the user stories; SC-003 product-validation rationale stated in "Why this exists"
- [x] Written for non-technical stakeholders — spec uses operator/portfolio/digest vocabulary; technical primitives only appear where they're hard contracts (the SPY benchmark, the CSV schema), not as design choices
- [x] All mandatory sections completed — User Scenarios & Testing, Requirements, Success Criteria, Assumptions all present

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — defaults from the planning step were resolved into the Assumptions section; the load-bearing decisions (holding window fixed-21d, mid-window UW/Sell behavior, no-broker-integration) are committed in FRs and Assumptions
- [x] Requirements are testable and unambiguous — each FR has either a specific behavior with expected output or a measurable property; SC-001 through SC-008 each pin a single observable outcome
- [x] Success criteria are measurable — every SC includes a numeric tolerance (basis points, percentages, line-coverage thresholds) or a binary observable
- [x] Success criteria are technology-agnostic — none of SC-001..SC-008 reference Python, dataclasses, JSON-schema validators, or specific frameworks; SPY and `returns_from_frames` are referenced only as the existing project conventions the harness must conform to (not as implementation choices)
- [x] All acceptance scenarios are defined — every user story has Given/When/Then scenarios; US1 has 3, US2 has 4, US3 has 2
- [x] Edge cases are identified — 8 explicit edge cases covering data anomalies, cap breaches, missed days, conflicting ratings, calendar gaps, benchmark outages
- [x] Scope is clearly bounded — explicit "no shorts" (FR-007), "no signal generation" (FR-011), "no fractional shares" (Assumption), "no tax treatment" (Assumption), "no back-fill" (Assumption), "no broker integration" (mentioned in Input + FR-014 disclaimer); the default watchlist & default policy fix the demo path
- [x] Dependencies and assumptions identified — Assumptions section enumerates 14 explicit assumptions covering operator profile, defaults, persistence, calendar, cost responsibility, scope-out items

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria — every FR maps to a user-story scenario or success criterion; FR-001/006/010 → US2 scenarios; FR-005/006/008 → US1 scenarios; FR-015 → US3
- [x] User scenarios cover primary flows — replay (US1), live-forward step (US2), inspection (US3); each is independently testable per the template's MVP requirement
- [x] Feature meets measurable outcomes defined in Success Criteria — SC-001 (validation gate ±100bps), SC-002 (idempotency byte-identical), SC-004 (P&L reconciliation ±5bps), SC-007 (90% coverage), SC-008 (zero LLM calls) are all binary-checkable; SC-003 / SC-005 / SC-006 are observable from outputs
- [x] No implementation details leak into specification — see Content Quality items; integration points are named where they're hard contracts, not where they're choices

## Validation Notes

- All checklist items pass on first iteration. The spec is informed by the prior `Plan` agent output (in conversation, not committed to disk under this spec yet — to be re-derived under `/speckit.plan`) and by the empirical SC-003 result, which gives concrete targets for the validation gate.
- The spec deliberately resolves the 13 design questions from the plan into Assumptions rather than deferring them as NEEDS CLARIFICATION markers. Rationale: the operator (= primary stakeholder) participated in producing those defaults via the plan-review step; re-litigating in `/speckit.clarify` would be redundant. If the operator wishes to override any default, they can do so via PARAMS.json equivalents at implementation time without spec amendment.
- One open meta-decision remains for `/speckit.plan`: whether to bundle the `daily_signals.py --emit-csv` addition into the same implementation pass or extract it as a separate trivial PR. Spec-level requirements (FR-002, FR-011) accommodate either path.

## Notes

- Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`
- All items currently pass; spec is ready for `/speckit.plan`
