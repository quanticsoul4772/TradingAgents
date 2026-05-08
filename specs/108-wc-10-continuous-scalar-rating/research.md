# Phase 0 Research: WC-10 Continuous Scalar Rating

**Branch**: `108-wc-10-continuous-scalar-rating` | **Date**: 2026-05-08

## Purpose

Resolve any NEEDS CLARIFICATION items from Technical Context, document decisions for non-trivial technical choices.

No NEEDS CLARIFICATION markers in spec.md or plan.md (all values concrete). Research below documents key decisions for traceability.

## Decision 1: Schema mutation strategy — Union type, not enum replacement

**Decision**: `PortfolioDecision.rating: Union[PortfolioRating, float]` rather than full replacement of the enum with float.

**Rationale**:
- Backward compatibility: existing 5-tier behavior must be PRESERVED when `wc_10_enabled=False` per FR-006. Union type allows the same model class to handle both cases.
- Pydantic validation: when `wc_10_enabled=True`, Pydantic accepts a float in [-1, +1]; when False, it accepts the enum string. Discriminator can be left implicit (Pydantic's default Union resolution).
- Memory log compatibility: existing 26-entry corpus uses enum strings. Union allows reading old entries unchanged.

**Alternatives considered**:
- **Full enum replacement**: would break backward compat with the existing 65-run corpus. Rejected.
- **Two separate Pydantic models** (`PortfolioDecision` + `PortfolioDecisionScalar`): would proliferate types throughout the codebase + force every consumer to handle both. Rejected.
- **Discriminated Union with explicit field tag**: cleaner schema but forces LLM to emit a tag field. Implicit Union resolution is simpler at the LLM-output boundary.

## Decision 2: SignalProcessor scalar extractor — Pydantic-first, regex fallback

**Decision**: When `wc_10_enabled=True`, SignalProcessor reads the parsed Pydantic model directly (rating is already a float). When `wc_10_enabled=False`, the existing regex extractor remains.

**Rationale**:
- Pydantic structured-output binding (per `agents/utils/structured.py`) already returns the parsed model. The regex extractor is a fallback for when structured-output fails. WC-10 leverages the same pattern.
- Avoids regex complications (matching float strings is fragile).
- If Pydantic parsing fails (e.g., LLM emits non-numeric rating), fall back to a clear error rather than try to regex-extract a scalar.

**Alternatives considered**:
- **Regex-extract float string from rendered markdown**: fragile (locale differences, scientific notation, NaN). Rejected.
- **JSON-only structured output, no markdown rendering**: changes the rendering pipeline; out of scope for v1.

## Decision 3: Bin function semantics — `<=` boundary, lower bin claims

**Decision**: `bin_scalar_to_tier(rating)` uses `<=` semantics; rating exactly at threshold lands in the LOWER bin (more bearish). Default thresholds `(-0.6, -0.2, +0.2, +0.6)` produce equal-width bins.

**Rationale**:
- Deterministic: single convention removes ambiguity at boundaries.
- Conservative: when rating is exactly -0.6 (a borderline Sell), interpreting as Sell rather than Underweight is the more cautious read for a bear-side rating.
- Symmetric: rating exactly +0.6 lands in Overweight (lower of {Overweight, Buy} bins), preserving conservatism for bull-side too.

**Alternatives considered**:
- **`<` strict less-than (boundary lands in upper bin)**: equally valid; rejected for arbitrary preference. Either convention is documented and tested deterministically.
- **Half-open interval per bin (right-inclusive)**: standard pandas-style binning. Adopted (≤ is right-inclusive at the bin's upper boundary).

## Decision 4: Filter-bypass mode — top-of-PM-node short-circuit

**Decision**: When `wc_10_enabled=True` AND `wc_10_filter_mode="bypass"`, `portfolio_manager_node` returns the LLM-emitted scalar rating WITHOUT invoking ANY filter from the chain. Implementation: a single `if config.get("wc_10_enabled") and config.get("wc_10_filter_mode") == "bypass":` branch at the top of the post-LLM-call portion of the node, returning state immediately.

**Rationale**:
- Cleanest single-intervention test per Constitution II — the experiment isolates the schema effect.
- Filters all operate on 5-tier strings; passing a float through them would require either binning (introduces 2nd intervention) or filter-side scalar handling (significant refactor of 9 filters).
- Bypass is reversible — operator flips back to default-off OR future `wc_10_filter_mode="passthrough"` to test bin-then-filter behavior in v2.

**Alternatives considered**:
- **Per-filter wc_10 awareness**: each of the 9 filters checks `wc_10_enabled` + handles scalar. Significant refactor; rejected for v1.
- **Bin-then-filter (passthrough mode)**: introduces second intervention; deferred per spec.md OUT OF SCOPE for v1.
- **Filter chain runs but only annotates (no rating mutation)**: would require state-shape change; rejected for v1.

## Decision 5: Pilot grid — 10 dates × 2 tickers (NVDA + AAPL)

**Decision**: Empirical v1 pilot is 20 propagates: 10 dates spanning 2026-04-01 through 2026-05-01 (Friday cadence) × NVDA + AAPL.

**Rationale**:
- NVDA + AAPL are tech mega-caps with the richest existing baseline corpora — direct comparison to existing 65-run corpus is meaningful.
- 10 dates × 2 tickers = 20 propagates; matches the n=20 range from prior Tier 2-style experiments (single_call_baseline at n=10-30; MR-3 v2 at n=20).
- Cost: 20 × ~$0.40 = ~$8. Plus 5-tier baseline same grid = ~$16 total. Constitution III T2 budget ≤$30; well under.
- Date range avoids the 2026-04-17 + 2026-04-24 dates that have rich existing analysis (sub-pattern 4, Hybrid E feasibility cohort) so the pilot adds NEW data rather than overlapping existing.

**Alternatives considered**:
- **5 dates × 4 tickers**: same n=20, more ticker diversity. Rejected because diversity-vs-corpus-comparability tradeoff favors the latter at v1.
- **20 dates × 1 ticker (NVDA only)**: most direct comparison to single_call_baseline. Rejected because 2-ticker variance check is more informative.
- **Larger grid (50+ propagates)**: ~$40+ cost; exceeds T2. Defer to v2 if v1 surfaces interesting results.

## Decision 6: TradingAgentsConfig key naming — `wc_10_*` prefix

**Decision**: 3 new keys use `wc_10_` prefix:
- `wc_10_enabled` (bool, default False)
- `wc_10_filter_mode` (Literal["bypass", "passthrough"], default "bypass")
- `wc_10_bin_thresholds` (tuple[float, float, float, float], default (-0.6, -0.2, +0.2, +0.6))

**Rationale**:
- Consistent with existing config-key prefix conventions: `forward_catalyst_*`, `contrarian_gate_*`, `sector_momentum_filter_*`, `institutional_rotation_*`.
- WC-10 is the canonical experiment name (per `docs/EXPERIMENT.md`) — preserve the original tagging.
- 3 keys (vs 4-6 for similar specs) reflects the experiment's narrower scope (output schema only, not a multi-mode filter).

**Alternatives considered**:
- **`continuous_rating_*` prefix**: more descriptive but loses the WC-10 experiment identity. Rejected.
- **Single nested dict `wc_10` config key**: cleaner namespacing but breaks the existing flat-config pattern. Rejected.

## Decision 7: AgentState extension — top-level `wc_10` field

**Decision**: New top-level `wc_10` field in AgentState TypedDict + added to `_log_state` whitelist.

**Rationale**:
- Per the spec 003 silent-drop bug history (`reference_speckit_6pr_workflow_pattern.md` memory): new state-level keys MUST be declared in AgentState OR LangGraph silently drops them from state merges.
- Spec X-1 used a SUB-DICT of `state["forward_catalyst"]` because Spec X-1 extends Spec 007's annotation. WC-10 is independent of the forward_catalyst lineage; top-level field is cleaner.
- Alternative: stuff WC-10 annotation into an existing field (`final_trade_decision` markdown). Rejected — non-discoverable for analyzer scripts.

**Alternatives considered**:
- **Sub-dict of an existing top-level field**: would force conceptual coupling to that field's lineage. Rejected as misleading.
- **No state annotation; reconstruct from logs**: would require parsing markdown rather than reading a structured field. Rejected as fragile.

## Decision 8: Test count — 6 unit + 2 integration

**Decision**: ~6 unit tests in `tests/test_wc_10_bin.py` + 2 integration tests in `tests/test_wc_10_pm_integration.py`. Matches the spec.md TEST COUNTS line.

Unit tests:
1. `bin_scalar_to_tier(0.7)` → "Buy" (interior bull)
2. `bin_scalar_to_tier(0.6)` → "Overweight" (boundary semantics; ≤ lands in lower bin)
3. `bin_scalar_to_tier(0.0)` → "Hold" (interior neutral)
4. `bin_scalar_to_tier(-0.6)` → "Sell" (boundary semantics)
5. `bin_scalar_to_tier(-0.7)` → "Sell" (interior bear)
6. `bin_scalar_to_tier()` rejects out-of-order thresholds (raises ValueError)

Integration tests:
1. `wc_10_enabled=False` (default) preserves 5-tier output + 9-filter chain execution + state log shape (SC-003)
2. `wc_10_enabled=True` + `wc_10_filter_mode="bypass"` produces scalar output + asserts NO filter from chain executes (SC-001 + SC-004)

**Alternatives considered**:
- **More unit tests (e.g., 12)**: would test custom thresholds + edge cases like -1.0/+1.0/0.5 boundaries. Defer to follow-up if v1 surfaces threshold-tuning interest.
- **PM hook integration test**: not strictly needed because filter-bypass mode skips the chain entirely. v1 keeps it minimal.

## Empirical evidence references

- `docs/EXPERIMENT.md` Tier 2 — original WC-10 brainstorm
- `claudedocs/experiment-md-tier-2-3-status-2026-05-08.md` — PR #97 Tier 2/3 survey identifying WC-10 as recommended next arc
- `claudedocs/wc-10-continuous-scalar-rating-feature-description-2026-05-08.md` — PR #104 feature description draft
- `RESEARCH_FINDINGS.md` — Constitution VII Calibrated Abstention thread + 5-tier mode collapse evidence (~70% Hold rate at single-call ceiling)
- `experiments/2026-05-03-003-single-call-baseline-nvda/` — closest existing experiment

## Pattern-reuse references

- `tradingagents/agents/utils/forward_catalyst_filter.py` (Spec 007) — precedent for: opt-in mode field, `Literal[...]` config types, state log persistence
- `tradingagents/agents/utils/institutional_rotation_filter.py` (Spec X-1) — precedent for: small helper module, default-off integrity, FR-011 backward-compat pattern
- `specs/091-c4-institutional-rotation/` (Spec X-1) — spec-kit 6-PR-bundle workflow precedent
- `tests/test_paper_sc003_reproduction.py` — SC-005 empirical-pilot pattern (replay-based reproduction gate)

No NEEDS CLARIFICATION items remain. Ready for Phase 1.
