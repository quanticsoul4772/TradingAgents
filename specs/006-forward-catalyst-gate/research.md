# Phase 0: Research — Forward-Catalyst-Aware Contrarian Gate (Spec 007)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

Resolves the technical-context decisions surfaced during planning. All NEEDS CLARIFICATION items resolved here. Each entry: Decision / Rationale / Alternatives Considered.

---

## R-1: LLM client integration

**Decision**: Use `tradingagents.llm_clients.factory.create_llm_client(provider, model)` with `provider="anthropic"` + `model=config["forward_catalyst_model"]` (default `"claude-opus-4-7"`). Same factory the rest of the framework uses; lazy provider imports per the existing pattern.

**Rationale**:
- Single source of truth for LLM client construction across the framework
- Factory already supports Anthropic (`AnthropicClient`); no new provider plumbing needed
- Operator overrides via `config["forward_catalyst_model"]` flow through the factory transparently — Haiku, Sonnet, Opus, OpenAI variants, etc. all routable
- The Phase C `second_opinion.py` module already uses this pattern; precedent established

**Alternatives considered**:
- **Direct `anthropic.Anthropic()` client construction** — bypasses the factory; loses cost-tracking + provider-config mapping. Rejected.
- **Add a new `forward_catalyst_client` factory method** — overkill for what is one LLM call site. Rejected.

---

## R-2: Pydantic structured output via `with_structured_output`

**Decision**: Use `llm.with_structured_output(CasePricedInScore)` per the `second_opinion.py` pattern. The schema is defined as a Pydantic `BaseModel` with `bull_case_priced_in: float (ge=0, le=1)` + `bear_case_priced_in: float (ge=0, le=1)` + `rationale: str (max_length=2000)`. On structured-output failure (provider doesn't support it OR response doesn't validate), the filter degrades to `skipped="llm_failed"` per FR-010.

**Rationale**:
- Pydantic validates the response shape automatically; no manual JSON parsing
- Provider-native structured-output modes (json_schema for Anthropic, response_format for OpenAI) handled by the langchain wrapper
- The `second_opinion.py` precedent (Phase C, 218 LOC) is the closest existing parallel; reuse the same patterns (try/except around `with_structured_output` + try/except around `invoke(prompt)`)
- Max length 2000 chars matches the retrofit script's `CasePricedInScore.rationale` (post-bumping from 600 — Haiku rejected too many; Opus also wants room)

**Alternatives considered**:
- **Free-text response + regex parsing** — fragile; rejected
- **Two separate LLM calls** (one per side) — doubles cost; rejected
- **Embed the rationale in the suppression markdown only** (don't structure it) — loses queryability; rejected

---

## R-3: Threshold semantics

**Decision**: Strictly greater than (`bull_case_priced_in > bull_threshold` ⇒ fire; same for bear). Equality does NOT fire. Both thresholds MUST be in [0, 1]; values outside cause `skipped="invalid_threshold"` with logged warning.

**Rationale**:
- Strict greater-than mirrors A3 + spec 004 + spec 006 boundary semantics
- Boundary equality is rare in practice (LLM-extracted floats rarely hit a threshold to 6+ decimal places); strict-greater-than removes ambiguity in tests
- [0, 1] range constraint matches the Pydantic schema constraint on the LLM scores; values outside indicate misconfiguration

**Alternatives considered**:
- **`>=` (inclusive)** — surfaces boundary edge cases in tests; rejected for consistency with prior filters
- **No range validation** — operators can shoot themselves in the foot with thresholds like 1.5 (filter would never fire); rejected
- **Auto-clamp out-of-range thresholds** — silent behavior change; rejected. Better to skip the side + log a warning.

---

## R-4: Filter ordering in PM hook chain

**Decision**: Spec 007 runs LAST in the chain:
1. **A3** (per-ticker absolute bear suppression on UW/Sell)
2. **Spec 006** bear-sector-symmetry (sector-relative bear suppression on UW/Sell)
3. **Spec 003 + 003.5** contrarian gate (within-ticker / sector-baseline bull suppression on Buy/OW)
4. **Spec 004** sector-momentum filter (sector-ETF bull suppression on Buy/OW)
5. **Spec 007** forward-catalyst filter (LAST in chain — LLM-extracted case-priced-in)

**Rationale**:
- Spec 007 consumes the SAME analyst reports + debate as input that the prior 4 filters already saw; running last ensures spec 007 sees the rating that survived the prior chain
- If a prior filter has already overridden to Hold, spec 007 still calls the LLM (annotation captured for audit) but both bull-side and bear-side branches no-op (Hold is neither bullish nor bearish per FR-002)
- Cost optimization: if BOTH `bull_mode` and `bear_mode` are `"off"`, skip the LLM call entirely (FR-009 / SC-006). Operator can disable for cost-sensitive workflows.
- The order is documented in plan.md "Filter ordering" section + FR-012 + this R-item.

**Alternatives considered**:
- **Spec 007 BEFORE spec 003** — would let spec 007 catch consensus-priced-in commits before prose-density gate. Rejected because spec 003 is empirically validated at smaller sample sizes; spec 007 is a complementary signal class that should not pre-empt the prior filters.
- **Spec 007 in the middle** — no clear ordering rationale; rejected for FR-012 ordering clarity.
- **Spec 007 as a separate analyst stage** (not PM hook) — would require graph topology change (new node + edge in `setup.py`); rejected for KISS — keep the filter in the PM hook stage where the analyst reports are already in scope.

---

## R-5: Annotation persistence path

**Decision**: Add `"forward_catalyst"` to the `_log_state` whitelist in `tradingagents/graph/trading_graph.py`. One-line extension matching the precedent set by:
- Commit `4c14d0f` (added `contrarian_gate`)
- Spec 004 (added `sector_momentum`)
- Spec 006 (added `bear_sector_symmetry`)

Additionally, add `forward_catalyst: NotRequired[dict | None]` to the `AgentState` TypedDict in `tradingagents/agents/utils/agent_states.py`. Per R-5 in spec 006: undeclared keys are silently dropped from LangGraph state merges — declaring this key in the TypedDict ensures `final_state["forward_catalyst"]` is preserved end-to-end.

**Rationale**:
- The state-log writer is a strict whitelist (deliberate per the original architecture); silently dropping the new field would replicate the spec 003 bug
- The AgentState TypedDict declaration prevents the LangGraph silent-drop on graph state merges
- Adding both entries is mechanical + minimal-risk
- Test pattern (regression-guard tests added in commit `4c14d0f`, reproduced in spec 004 + spec 006) extends naturally — add a parallel `test_state_log_persists_forward_catalyst_field` test

**Alternatives considered**:
- **Refactor `_log_state` to dump everything** — broader change with unintended persistence-of-internal-state risks; rejected
- **Skip persistence; rely on event-log alone** — there's no event log for filters today; persistence via state log is the only audit path
- **Use a generic `filters` dict instead of one key per filter** — would conflate audit trails across 4 filters; harder to query downstream. Per-filter key (now 4 deep: `contrarian_gate` + `sector_momentum` + `bear_sector_symmetry` + `forward_catalyst`) is clearer

---

## R-6: Retrospective script methodology (SC-008)

**Decision**: Build `scripts/forward_catalyst_retrospective.py` that EXTENDS `scripts/forward_catalyst_class3_retrospective.py` (the existing retrofit script that produced the Opus PASS verdict) by:
1. Loading config from `tradingagents.default_config.DEFAULT_CONFIG` (production thresholds + modes + model)
2. Walking the same 45-commit cohort + ~50 controls from `claudedocs/sector-alpha-attribution-2026-05-06.csv`
3. For each commit, applying the PRODUCTION filter logic (not the retrofit's hardcoded thresholds)
4. Reporting per-side fire rates + cohort hit rates + net Δα per the SC-008 acceptance criteria

The SC-008 gate verifies: (a) bull-side fires on ≥24 of 27 ticker_weak commits at default `bull_threshold=0.60` (88.9% per Opus retrospective); (b) bear-side fires (in shadow mode) on ≥10 of 18 ticker_strong commits at default `bear_threshold=0.50` (per design doc §5; empirically validated at 13/18 in Opus retrospective).

**Rationale**:
- Retrofit script (forward_catalyst_class3_retrospective.py) used hardcoded thresholds (0.50/0.60/0.70/0.80 bull, 0.50/0.60/0.70/0.80 bear) for the threshold sweep
- Production retrospective uses the actual `DEFAULT_CONFIG` values; tests the operational filter as it ships
- Reuses the existing CSV scoring data (no need to re-call LLM 94 times); just re-applies the new thresholds + decision logic

**Alternatives considered**:
- **Re-call the LLM for the production retrospective** — wastes ~$2 of Opus calls; rejected
- **Inline the SC-008 check in test_forward_catalyst_filter.py** — pollutes the unit test suite with integration concerns; rejected. Keep the SC-008 retrospective as a standalone script with `@pytest.mark.integration` runnable.
- **Skip SC-008 entirely** — leaves the spec's empirical claim unverified at production-config; rejected

---

## R-7: Default model + thresholds (justification from Opus retrospective)

**Decision**:
- `forward_catalyst_model` = `"claude-opus-4-7"` (default)
- `forward_catalyst_bull_mode` = `"active"` (default; bull-side empirically passes Constitution VIII gate)
- `forward_catalyst_bear_mode` = `"shadow"` (default; bear-side passes 1+2 only — VIII shadow-mode-first)
- `forward_catalyst_bull_threshold` = `0.60` (default; sweet-spot from Opus retrospective threshold sweep — all 3 criteria pass)
- `forward_catalyst_bear_threshold` = `0.50` (default; bear-side highest discrimination from Opus retrospective)

**Rationale** (from `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md`):
- **Opus over Haiku**: bull cohort separation +0.097 (Opus) vs +0.048 (Haiku), 2× wider; score distribution std 0.090 (Opus) vs 0.071 (Haiku), +27% wider; bull T=0.60 net Δα +2.24pp (Opus, n=33 fires; meaningful) vs +9.12pp (Haiku, n=44 fires; suspect 94% fire rate). Opus is required for the bull-side default-on flip per the empirical evidence.
- **Bull T=0.60**: all 3 criteria pass decisively (discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp). T=0.70 cohort hit rate drops to 55.6% (just under 60% gate); T=0.50 fires too many at 94% rate. T=0.60 is the sweet spot.
- **Bear T=0.50**: criteria 1+2 pass (+23.10pp discrim / 72.2% hit rate); criterion 3 just fails (+0.30pp < +0.5pp gate). T=0.60 fires only 4 of 24 commits (5.6% hit rate; fails criterion 2). T=0.50 is the only operationally-meaningful threshold; shadow-mode-first compensates for criterion-3 failure.
- **Bear-side default = shadow**: per the Opus retrospective bear-side criterion-3 fail + design doc §5 shadow-mode-first condition. Operators flip to active only after observing n≥20 fresh propagates per the design doc.

**Alternatives considered**:
- **Bull T=0.50 (more aggressive)**: 94% fire rate → suppresses too many. Rejected.
- **Bull T=0.70 (more conservative)**: cohort hit rate drops to 55.6% — below 60% gate. Rejected.
- **Bear default-on at T=0.50** with no shadow-mode period: violates design doc §5 + Constitution VIII shadow-mode-first condition. Rejected.
- **Single threshold for both sides**: bull and bear distributions are different (bull mean 0.690 / std 0.090; bear mean 0.524 / std 0.089); separate thresholds give more flexibility. Confirmed.

---

## R-8: Module placement (extension vs new module)

**Decision**: New module `tradingagents/agents/utils/forward_catalyst_filter.py`. Mirrors A3's `momentum_filter.py` + spec 004's `sector_momentum_filter.py` + spec 006's `bear_sector_symmetry_filter.py` placement.

**Rationale**:
- A3 + spec 004 + spec 006 + spec 007 share the broad shape ("PM hook stage filter that may suppress to Hold") but operate on different inputs (per-ticker price / sector-ETF price / ticker-vs-sector relative / LLM-extracted prose synthesis) + emit different annotations. Co-located but separate keeps each module readable.
- Tests already follow the per-module pattern (`tests/test_momentum_filter.py` for A3; `tests/test_sector_momentum_filter.py` for spec 004; `tests/test_bear_sector_symmetry_filter.py` for spec 006; `tests/test_forward_catalyst_filter.py` for this).
- Placing in `tradingagents/signals/` (the `contrarian_gate.py` location) would be slightly less consistent — spec 003 is the only filter currently in `signals/` and it has its own module structure. Keeping spec 007 in `agents/utils/` matches the more recent precedent (specs 004 + 006).

**Alternatives considered**:
- **Inline in `portfolio_manager.py`** — too much logic in the PM module; rejected for testability
- **Extend `bear_sector_symmetry_filter.py`** — different mechanism class (LLM call vs price math); rejected
- **Put in `tradingagents/signals/`** — `signals/` is for featurizers + the contrarian gate; agent-stage filters belong in `agents/utils/` per the spec 004 + spec 006 precedents

---

## R-9: LLM cost discipline + Constitution III

**Decision**: Per-propagate Opus cost is ~$0.025 (measured at $2.35 / 94 calls in the retrofit). For typical operator workflow (`daily_signals.py` on 5-10 ticker watchlist, daily cadence): ~10 calls/day × $0.025 = $0.25/day. T1 (≤$5/experiment) classification holds.

For backtest workflows running 100+ propagates: ~$2.50 cost addition per backtest. Operators see this in the `--yes` cost confirmation prompt that `scripts/backtest.py` already implements.

For ablation experiments: the spec 007 cost is additive to the existing per-propagate framework cost (~$0.50-$1 typical Opus); operators should document the per-experiment cost in HYPOTHESIS.md per Constitution III T2 deliberation when running n≥30 commits.

**Rationale**:
- Empirically measured at the retrofit; Opus pricing is stable enough for the cost ceiling estimate
- Haiku alternative (~$0.0025/call, 10× cheaper) available via `forward_catalyst_model` config override; documented degradation noted in quickstart
- Both-modes-off escape hatch (FR-009 / SC-006) zeroes cost for operators who want to disable

**Alternatives considered**:
- **Haiku as default model** — empirically degraded discrimination + cohort separation. Bull-side cohort separation drops 10pp → 5pp; net Δα at T=0.60 becomes the suspect 94%-fire-rate measurement vs Opus's clean 70% fire rate. Rejected; Opus is the empirically-justified default.
- **Per-call cost gate that aborts the filter on cost-budget exceeded** — overengineering; Constitution III T1/T2 deliberation is the human-loop gate. Rejected.
- **Opus only on bull-side; Haiku on bear-side** — would require separate model configs; bear-side is shadow-mode anyway so the cost difference is small; rejected for simplicity.

---

## R-10: Constitution v1.4.0 amendment scope

**Decision**: As part of FR-015 + SC-009, the spec landing includes amending Constitution Principle VIII:
- Add a new sub-section titled "Forward-catalyst-class validation gate" with the three criteria (discrim ≥ +5pp / cohort hit rate ≥ 60% / net Δα ≥ +0.5pp OR shadow-mode-first)
- Bump version 1.3.0 → 1.4.0 (MINOR per added/amended principle rule)
- Update header + footer with the amendment description
- Update CLAUDE.md "eight principles" wording (remains at 8; just an extension to VIII)
- CHANGELOG.md entry references the amendment + spec 007 as the trigger

**Rationale**:
- The methodology lesson AT THE TIME the first forward-catalyst filter ships, rather than retroactively
- Future forward-catalyst filters have an explicit precedent without re-deriving the gate criteria
- Mirrors the original Constitution VIII landing pattern (commit `1008bac`, 2026-05-06): amendment lands AS PART OF the work that triggers it

**Alternatives considered**:
- **Land Constitution v1.4.0 amendment as a separate commit** before the spec — out-of-order; the spec is the empirical justification for the amendment. Rejected.
- **Wait until after spec 007 implementation lands; amend constitution later** — risks the amendment never landing; rejected.
- **Skip the amendment; rely on this spec as the de facto precedent** — loses the codification benefit; rejected.

---

## R-11: Naming convention (Spec 007 user-facing vs branch dir 006)

**Decision**: The spec-kit branch directory is `006-forward-catalyst-gate` (auto-numbered by `create-new-feature.ps1` based on the count of existing `specs/` directories). The user-facing name in CLAUDE.md, RESEARCH_FINDINGS.md, ROADMAP.md, commit messages, and this document is "Spec 007" to match the established filter-portfolio numbering (A3 / Spec 003 / Spec 003.5 / Spec 004 / Spec 006 / Spec 007 — skipping 005 to maintain consistent gap with the prior spec naming).

**Rationale**:
- The spec-kit script doesn't know about the user-facing offset (which exists because the project's filter portfolio names skip 005)
- The naming offset is a documentation artifact; future specs can either continue the offset (Spec 008 = branch dir 007-...) or align both numberings, at the operator's discretion when invoking `/speckit.specify`
- Both names are documented in the spec preamble + CLAUDE.md so readers know they refer to the same thing
- Same precedent established by spec 006 (branch dir `005-bear-sector-symmetry`)

**Alternatives considered**:
- **Rename the directory to `007-forward-catalyst-gate`** — would require manually fighting the spec-kit script + risks confusing future spec-kit invocations. Rejected.
- **Use only "Spec 006" in user-facing docs** — would conflict with the spec 006 (bear-sector-symmetry) reference. Rejected.
- **Drop the user-facing offset; rename all docs to use spec-kit branch numbers** — loses the established filter-portfolio numbering convention; large doc churn. Rejected.

---

## Summary of resolved unknowns

All technical-context items resolved:
- LLM client integration → R-1
- Pydantic structured output → R-2
- Threshold semantics → R-3
- Filter ordering → R-4
- Annotation persistence (state-log + AgentState TypedDict) → R-5
- Retrospective script methodology → R-6
- Default model + thresholds → R-7
- Module placement → R-8
- LLM cost discipline → R-9
- Constitution v1.4.0 amendment scope → R-10
- Naming convention (Spec 007 vs branch dir 006) → R-11

No outstanding NEEDS CLARIFICATION. Proceed to Phase 1 (data-model + contracts + quickstart).
