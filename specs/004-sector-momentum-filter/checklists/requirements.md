# Specification Quality Checklist: Sector-Momentum Filter

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-06
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — spec mentions `tradingagents/paper/sectors.py`, `tradingagents/agents/utils/momentum_filter.py`, and `tradingagents/dataflows/returns` only as integration-point hard contracts (existing modules the filter must reuse, per FR-003 / FR-005); no internal-implementation language ("which dataclass," "what algorithm")
- [x] Focused on user value and business needs — operator outcome (sector-rotation bullish miss prevented) drives US1; SC-003 Financials investigation provides empirical motivator; closes the loop on today's spec 003.5 validation findings
- [x] Written for non-technical stakeholders — uses filter / sector / ETF / threshold vocabulary; technical primitives only appear where they're hard contracts (yfinance sector cache, the existing `returns_from_frames` math primitive)
- [x] All mandatory sections completed — User Scenarios, Requirements, Success Criteria, Assumptions all present

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — design decisions resolved into Assumptions: lookback=30d (matches A3); threshold strict-less-than (matches A3); default mode=off (matches A3 introduction pattern); 11-ETF SPDR sector mapping hardcoded; filter order A3 → spec 003 → spec 004
- [x] Requirements are testable and unambiguous — every FR pairs to either a US scenario or a SC; threshold semantics named explicitly (FR-006 strict less-than); rating-effect named explicitly (FR-007 always Hold, never UW)
- [x] Success criteria are measurable — SC-001 names a specific synthetic corpus shape; SC-002 boundary equality test; SC-003 schema-conformance check; SC-006 byte-identity regression-guard with default-off; SC-007 90% line-coverage threshold; SC-008 names a specific empirical-validation gate (≥3 of 5 SC-003 Financials commits suppressed)
- [x] Success criteria are technology-agnostic — no Python / pandas / pytest names in SC-001..SC-008; reusing existing primitives is named only as a hard contract (`returns_from_frames`, paper sectors cache, paper_trade.py harness)
- [x] All acceptance scenarios are defined — US1 has 4 Given/When/Then scenarios covering all 4 ratings × the threshold-crossed condition; US2 has 3 covering active/shadow/off audit-annotation cases
- [x] Edge cases are identified — 8 explicit edge cases covering Unknown sector, no-ETF-mapping sectors, missing ETF data, boundary equality, filter ordering interactions, Buy-vs-Overweight handling, positive-threshold rejection, mode-independence between filters
- [x] Scope is clearly bounded — explicit "no UW downgrade" (FR-007); "no LLM cost" (SC-005); "default-off" (FR-008/SC-006); "11-ETF mapping table; new entries require code change" (FR-004); ablation flag = threshold = None (FR-013); corpus retrospective in SEPARATE commit before default-on flip (Assumption); no state-log replay invariant impact (Assumption)
- [x] Dependencies and assumptions identified — Assumptions section enumerates 8 explicit assumptions covering sector source, ETF universe, lookback, threshold semantics, default mode, filter ordering, paper-harness interaction, retrospective gating, state-log persistence path

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria — every FR maps to a US scenario or SC; FR-001 → US1 wiring; FR-002 → US1 scenarios 3+4; FR-003+FR-008 → US1 scenarios + edge case "Unknown sector"; FR-007 → US1 scenario 1 + SC-001; FR-009 → US2 scenarios 1-3 + SC-003; FR-013 → SC-006
- [x] User scenarios cover primary flows — sector-rotation miss prevention (US1, MVP); audit annotation (US2); each independently testable per template's MVP requirement
- [x] Feature meets measurable outcomes defined in Success Criteria — SC-001 directly tests US1; SC-003 directly tests US2; SC-002 + SC-006 are regression-protection; SC-008 is the empirical-validation gate that closes the loop on today's spec 003.5 validation
- [x] No implementation details leak into specification — see Content Quality items; integration points named only where they're hard contracts

## Validation Notes

- All checklist items pass on first iteration. Spec is informed by the just-completed spec 003.5 validation finding (`claudedocs/sc003-financials-gate-check-spec-003-5-validation-2026-05-06.md`) plus the well-established A3 + spec 003 + spec 003.5 precedent for filter shape, mode interaction, and Constitution VII interaction.
- One open meta-decision for `/speckit.plan`: whether to extend the existing `tradingagents/agents/utils/momentum_filter.py` module (adds the sector variant alongside A3's per-ticker variant) OR create a new `tradingagents/agents/utils/sector_momentum_filter.py` (separation of concerns; matches spec 003.5's sector_baseline.py-alongside-contrarian_gate.py pattern). Spec-level requirements (FR-001 / FR-005) accommodate either path; data-model.md will commit to one in plan phase.
- The new `state["sector_momentum"]` annotation is ADDITIVE to the existing state-log schema; existing consumers (e.g. `daily_signals.py`, `scripts/contrarian_gate_retrospective.py`) won't break. State-log writer (`trading_graph.py:_log_state`) needs the same one-line whitelist extension as commit `4c14d0f` did for `contrarian_gate`.
- SC-008 is the load-bearing empirical-validation gate. The implementation should verify XLF's 30d return before 2026-04-03 was indeed >5% negative; if the empirical fact doesn't hold, the spec's motivating narrative needs revisiting.

## Notes

- All items currently pass; spec is ready for `/speckit.plan`
