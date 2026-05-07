# Feature Specification: Forward-Catalyst-Aware Contrarian Gate (Spec 007)

**Feature Branch**: `006-forward-catalyst-gate`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "Spec 007: Forward-Catalyst-Aware Contrarian Gate — FIRST forward-catalyst-aware filter in the framework. LLM-extracted bull/bear case-priced-in scores per propagate. Bull-side default-on at T=0.60 (Constitution VIII PASS); bear-side shadow-mode-first per design doc §5. Includes Constitution v1.4.0 amendment extending Principle VIII for forward-catalyst class."

> Naming note: this spec is referred to as **Spec 007** in CLAUDE.md, RESEARCH_FINDINGS.md, ROADMAP.md, and commit messages to match the user-facing filter-portfolio numbering. The spec-kit branch directory is auto-numbered `006-forward-catalyst-gate` because the spec-kit script ignores the user-facing offset (which exists because the project's filter portfolio names skip 005 to maintain consistent gap with the 4 prior specs). The two names refer to the same feature.

> **Constitution VIII alignment**: this spec follows Principle VIII discipline — pre-spec corpus retrospective ran BEFORE this spec was authored. Class 3 Opus retrospective (`claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md`) DECISIVELY PASSED the bull-side gate (discrim +14.43pp / cohort hit rate 88.9% / net Δα +2.24pp at T=0.60) and passed bear-side criteria 1+2 with shadow-mode-first condition. Spec invocation is empirically justified, not speculative.

## Why this exists

The framework now has 5 rating-suppression filters (A3 + spec 003 + spec 003.5 + spec 004 + spec 006) — all backward-looking and price-derived (or prose-density-derived for spec 003 family). Today's sector-α attribution analysis (`claudedocs/sector-alpha-attribution-2026-05-06.md`) revealed that **45 commits in the corpus** (27 bullish ticker_weak + 18 bearish ticker_strong) sit in cohorts that NONE of these 5 filters catches. The cohort losses + gains come from **forward catalysts** (earnings, guidance, news, sector rotations) the framework cannot see at signal-generation time.

Three same-day backward-price-only retrospectives all empirically failed to discriminate the cohorts (spec 004 -0.45pp, spec 006 -0.71pp, spec 005-candidate +0.31pp max). Constitution Principle VIII codified the lesson: backward-price filters require pre-spec retrospective showing net Δα ≥ +1pp before spec is written. The forward-catalyst-aware design exploration (`claudedocs/forward-catalyst-mechanism-exploration-2026-05-06.md`) identified Class 3 (LLM-extracted "case priced in" feature) as the most promising mechanism class, and the Class 3 Opus retrospective subsequently passed the gate.

This spec operationalizes the validated Class 3 mechanism as a production filter. It is the **fundamentally different mechanism class** the gap requires: not a backward-looking price comparison, but an LLM synthesis over the same analyst evidence the PM already saw, scoring how widely each side's thesis is already absorbed by the market.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bull-side suppression on consensus-priced-in commits (Priority: P1)

The framework propagates on AAPL on a date where the bull case (iPhone 17 supercycle, services growth, etc.) is widely accepted by the market — the LLM-extracted `bull_case_priced_in` score reads 0.78 (above the +0.60 default threshold). The Portfolio Manager would have committed Overweight, but the forward-catalyst filter recognizes the bull thesis is consensus-priced-in and downgrades to Hold. The persisted state log shows `final_trade_decision` as Hold (not Overweight) and `state["forward_catalyst"]["fired_bull"] == True`. Realized 21d α validates the filter empirically: the 27-commit `ticker_weak` cohort would have been suppressed at this threshold per the retrospective evidence.

**Why this priority**: This is the primary mechanism the spec exists for. The Class 3 Opus retrospective showed all three Constitution VIII gate criteria pass decisively for the bull side at T=0.60 (discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp on n=33 fires). Bull-side default-on is empirically justified; this scenario is the operational manifestation.

**Independent Test**: Run a propagate against AAPL for a date where the analyst reports + bull/bear debate produce a `bull_case_priced_in` score above 0.60 (verifiable by the retrospective CSV). With `forward_catalyst_bull_mode = "active"` + `bull_threshold = 0.60`, verify the rating is Hold (and the markdown contains a `[Forward-catalyst filter]` annotation explaining the score). With `bull_mode = "off"`, verify the rating is Overweight.

**Acceptance Scenarios**:

1. **Given** AAPL PM rating = Overweight AND `bull_case_priced_in` = 0.78 AND `bull_threshold` = 0.60 AND `bull_mode` = "active", **When** the filter evaluates the rating, **Then** the rating is downgraded to Hold and the decision markdown carries a `[Forward-catalyst filter]` note (model, scores, thresholds, rationale, original rating).
2. **Given** AAPL PM rating = Buy AND `bull_case_priced_in` = 0.78, **When** the filter evaluates, **Then** the rating is downgraded to Hold (filter acts on Buy as well as Overweight).
3. **Given** AAPL PM rating = Overweight AND `bull_case_priced_in` = 0.55 (below +0.60 threshold), **When** the filter evaluates, **Then** the rating remains Overweight (no override; `would_fire_bull` = False).
4. **Given** AAPL PM rating = Hold AND `bull_case_priced_in` = 0.78, **When** the filter evaluates, **Then** the rating remains Hold (no-op; nothing to suppress on the bull side).
5. **Given** AAPL PM rating = Underweight AND `bull_case_priced_in` = 0.78, **When** the filter evaluates, **Then** the bull-side branch no-ops (UW is not bullish); the bear-side branch may still fire independently.
6. **Given** AAPL PM rating = Overweight AND `bull_mode` = "shadow" AND `bull_case_priced_in` = 0.78, **When** the filter evaluates, **Then** `would_fire_bull` = True AND `fired_bull` = False AND rating remains Overweight.

---

### User Story 2 - Bear-side shadow-mode observation (Priority: P2)

The framework propagates on NVDA on a date where the bear case (valuation, China demand concerns, etc.) is widely accepted — the LLM-extracted `bear_case_priced_in` score reads 0.65 (above the +0.50 default threshold). The Portfolio Manager would have committed Underweight, but the bear-side filter is in **shadow mode by default** per Constitution VIII shadow-mode-first condition (the bear-side retrospective passed criteria 1+2 with +23pp discrimination + 72% cohort hit rate, but criterion 3 net Δα was +0.30pp, just under the +0.5pp gate). The annotation captures `would_fire_bear = True` but the rating is NOT modified. After 20+ propagates of shadow observation, the operator can review the annotations and decide whether to flip `bear_mode = "active"`.

**Why this priority**: Operational discipline — bear-side cannot ship default-on per the retrospective evidence, but the annotation infrastructure is necessary for the eventual default-on flip. Shadow-mode observation is the gate the design doc §5 specified.

**Independent Test**: Run a propagate against NVDA where `bear_case_priced_in` exceeds 0.50. With `bear_mode = "shadow"` (default), verify the rating remains Underweight + `state["forward_catalyst"]["would_fire_bear"] == True` + `fired_bear == False`. With `bear_mode = "active"`, verify the rating is Hold.

**Acceptance Scenarios**:

1. **Given** NVDA PM rating = Underweight AND `bear_case_priced_in` = 0.65 AND `bear_mode` = "shadow", **When** the filter evaluates, **Then** rating remains Underweight + `would_fire_bear = True` + `fired_bear = False`.
2. **Given** NVDA PM rating = Underweight AND `bear_case_priced_in` = 0.65 AND `bear_mode` = "active", **When** the filter evaluates, **Then** rating downgraded to Hold + `fired_bear = True`.
3. **Given** NVDA PM rating = Sell AND `bear_case_priced_in` = 0.65 AND `bear_mode` = "active", **When** the filter evaluates, **Then** rating downgraded to Hold (filter acts on Sell as well as Underweight).
4. **Given** NVDA PM rating = Hold AND `bear_case_priced_in` = 0.65, **When** the filter evaluates, **Then** rating remains Hold (no-op; nothing to suppress on the bear side).

---

### User Story 3 - Operator distinguishes forward-catalyst firings in audit (Priority: P2)

The operator inspects per-filter activity across a corpus and wants to know which Buy/OW → Hold or UW/Sell → Hold downgrades came from the forward-catalyst filter vs from A3 / spec 003 / spec 004 / spec 006. The filter emits a structured annotation (`forward_catalyst: dict | None`) into the LangGraph state alongside the existing `contrarian_gate` / `sector_momentum` / `bear_sector_symmetry` annotations, with fields identifying the LLM model used, the two scores, the rationale, the thresholds, the modes, the would-fire / fired booleans for each side, and pre/post ratings.

**Why this priority**: Operational ergonomic — necessary for per-filter α attribution. Mirrors the audit pattern established by spec 003 / spec 004 / spec 006.

**Independent Test**: Run a small corpus through the harness with bull-mode=shadow (so all annotations are captured without firing). Inspect each `state["forward_catalyst"]` annotation; verify the fields are populated correctly per the schema (model, bull_case_priced_in, bear_case_priced_in, rationale, bull_threshold, bear_threshold, bull_mode, bear_mode, would_fire_bull, would_fire_bear, fired_bull, fired_bear, pre_rating, post_rating, skipped, error).

**Acceptance Scenarios**:

1. **Given** a propagate where the bull-side filter fired (active mode, bull threshold crossed, bullish rating), **When** the operator reads `state["forward_catalyst"]`, **Then** the dict contains `{"model": "claude-opus-4-7", "bull_case_priced_in": 0.78, "bear_case_priced_in": 0.45, "rationale": "...", "bull_threshold": 0.60, "bear_threshold": 0.50, "bull_mode": "active", "bear_mode": "shadow", "would_fire_bull": True, "would_fire_bear": False, "fired_bull": True, "fired_bear": False, "pre_rating": "Overweight", "post_rating": "Hold", "skipped": None, "error": None}`.
2. **Given** a propagate where the LLM call failed (network error, parse error, etc.), **When** the operator reads the annotation, **Then** `skipped == "llm_failed"` AND `error` contains the exception summary AND rating is unchanged AND no fire occurs (filter degrades cleanly per the FR-010 resilience pattern).
3. **Given** a propagate where both modes are off, **When** the operator reads `state["forward_catalyst"]`, **Then** the field is `None` or absent.

---

### User Story 4 - Constitution v1.4.0 amendment (Priority: P3)

Per the design doc §6 candidate, this spec includes amending Constitution Principle VIII to explicitly add the forward-catalyst-class validation gate (discrim ≥ +5pp + cohort hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first). Constitution version bumps from v1.3.0 → v1.4.0 (MINOR per added/amended principle rule). The amendment formalizes the validation methodology that this spec is itself the first instance of.

**Why this priority**: Process documentation. The spec ships with the principle amendment so future forward-catalyst filters have an explicit precedent. Not blocking the MVP firing logic; lands as part of spec implementation rather than separately.

**Independent Test**: After implementation, verify `.specify/memory/constitution.md` Principle VIII has a new sub-section titled "Forward-catalyst-class validation gate" with the three criteria + shadow-mode-first condition. Verify version bumped to 1.4.0 in the header and footer. Verify CLAUDE.md "eight principles" wording remains correct (no count change, just an extension to VIII).

**Acceptance Scenarios**:

1. **Given** Constitution VIII pre-amendment (v1.3.0), **When** the operator reads the principle text, **Then** only the backward-price-filter gate is documented.
2. **Given** Constitution VIII post-amendment (v1.4.0), **When** the operator reads the principle text, **Then** both backward-price AND forward-catalyst gates are documented as separate sub-sections; CHANGELOG.md entry references the amendment + spec 007 as the trigger.

---

### Edge Cases

- What happens when the LLM call fails (network, rate limit, parse error)? Filter MUST degrade cleanly: emit `skipped="llm_failed"` + `error=str(exc)` annotation, leave the rating unchanged, log a warning, and never raise into the PM pipeline (FR-010). Same resilience pattern as the structured-output fallback in `tradingagents/agents/utils/structured.py`.
- What happens when the LLM returns a malformed structured response (Pydantic validation failure)? Same as above — `skipped="llm_failed"` with the validation error stringified.
- What happens when `bull_threshold` is set outside [0, 1]? Filter MUST log a warning at config-load and use the threshold value clamped to [0, 1] OR skip the bull-side branch with `skipped="invalid_threshold"`. Rejection at config-load (skip the bull side entirely) is the safer default.
- What happens when both `bull_mode` and `bear_mode` are "off"? Filter MUST skip the LLM call entirely (zero cost) and emit annotation with `skipped="off"`. Cost discipline per Constitution III.
- What happens when the analyst reports + debate are empty (e.g., test fixture)? Filter MUST still call the LLM with the empty content; the LLM may produce uncertain scores (~0.5/0.5). No special-casing — the filter trusts the LLM to handle empty input gracefully.
- What happens when prior filters in the chain have already overridden the rating to Hold? The forward-catalyst filter MUST still call the LLM (the LLM features are useful for audit even when no further override is possible). After the call, both bull-side and bear-side branches no-op (rating is Hold, neither bullish nor bearish).
- What happens when the same propagate hits both the bull-side AND bear-side fire conditions simultaneously? The pre-rating determines which branch acts: if pre-rating is bullish and bull-fire is true, downgrade to Hold via the bull branch. Bear-fire on a bullish rating is recorded in the annotation (`would_fire_bear` may be True) but does NOT alter the rating — bear-side only acts on bearish pre-ratings (FR-002).
- What happens when `forward_catalyst_model` is set to a non-Anthropic model (e.g., GPT-5.4)? Filter MUST attempt the call via `tradingagents.llm_clients.factory.create_llm_client`; if the provider doesn't support structured output, the filter falls back to the structured-output failure path (skipped="llm_failed") and degrades cleanly. Spec recommends Anthropic (Opus default) but doesn't lock provider choice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The filter MUST evaluate after the LLM's Portfolio Manager has emitted its rating but before the rating is persisted to state. Wired into `tradingagents/agents/managers/portfolio_manager.py` as the LAST hook in the chain (after A3, spec 006, spec 003/003.5, spec 004) per FR-012 ordering.
- **FR-002**: The filter's bull-side branch MUST only act on `Buy` and `Overweight` pre-ratings. The bear-side branch MUST only act on `Underweight` and `Sell` pre-ratings. `Hold` is passed through unchanged on both branches. The annotation is still emitted (with `would_fire_*` reflecting the LLM's score even though the filter doesn't act).
- **FR-003**: The filter MUST invoke an LLM (default `claude-opus-4-7`; configurable via `forward_catalyst_model`) with the 4 analyst reports + bull/bear debate history + investment plan as input. The LLM emits a structured response with two scores in [0, 1] + a rationale string (max length 2000 chars per the retrofit script's pattern).
- **FR-004**: The filter MUST use Pydantic structured output (`llm.with_structured_output(CasePricedInScore)`). When the provider doesn't support structured output OR the call/validation fails, the filter MUST emit `skipped="llm_failed"` + `error=str(exc)` annotation and leave the rating unchanged (FR-010 resilience).
- **FR-005**: The filter MUST use two configurable thresholds — `forward_catalyst_bull_threshold` (default `0.60`; bull-side fires when `bull_case_priced_in > threshold`) and `forward_catalyst_bear_threshold` (default `0.50`; bear-side fires when `bear_case_priced_in > threshold`). Both MUST be in [0, 1]; values outside the range cause `skipped="invalid_threshold"` with a logged warning.
- **FR-006**: The filter MUST support three modes per side via config: `forward_catalyst_bull_mode` and `forward_catalyst_bear_mode`, each `Literal["off", "shadow", "active"]`. Bull-side default is `"active"` (justified by Class 3 Opus retrospective DECISIVE PASS). Bear-side default is `"shadow"` (per Constitution VIII shadow-mode-first condition for criteria-1+2-only passes). Operators flip bear-side to `"active"` only after observing n≥20 fresh propagates per the design doc §5.
- **FR-007**: When the bull-side branch fires in active mode on a bullish rating, the rating MUST be downgraded to `"Hold"`. When the bear-side branch fires in active mode on a bearish rating, the rating MUST be downgraded to `"Hold"`. The filter MUST NEVER upgrade ratings (suppression target is always Hold; never flip-to-bullish or flip-to-bearish; aligns with the existing filter family's downgrade-only semantics). The decision markdown MUST be annotated with a `[Forward-catalyst filter]` note containing: model, both scores, rationale, both thresholds, both modes, which side fired, and the original rating.
- **FR-008**: The filter MUST emit a structured annotation to LangGraph state at `state["forward_catalyst"]` with the schema defined in Key Entities below. The annotation is `None` when both modes are `"off"`. The state-log writer (`tradingagents/graph/trading_graph.py:_log_state`) MUST be extended to persist this field (parallel to `contrarian_gate` / `sector_momentum` / `bear_sector_symmetry`). The LangGraph `AgentState` TypedDict (`tradingagents/agents/utils/agent_states.py`) MUST be extended with the `forward_catalyst` key (precedent set by spec 003 + spec 004 + spec 006 — undeclared keys are silently dropped from state merges).
- **FR-009**: The filter MUST call the LLM only when at least one of `bull_mode` or `bear_mode` is non-`"off"`. When both modes are `"off"`, the filter MUST skip the LLM call entirely (zero cost) and emit annotation with `skipped="off"`.
- **FR-010**: The filter MUST never break the PM pipeline. All exception paths (LLM failure, validation failure, missing reports, etc.) MUST log a warning + emit a skipped annotation + return the rating unchanged. Same resilience pattern as the existing A3 + spec 003 + spec 004 + spec 006 hooks.
- **FR-011**: The filter MUST be deterministic in its DECISION GIVEN the LLM scores. Same `(bull_case_priced_in, bear_case_priced_in, bull_threshold, bear_threshold, bull_mode, bear_mode, pre_rating)` tuple ⇒ same fire decision. The LLM call itself is non-deterministic (LLM stochasticity) but that's outside the filter's control; the structured output schema constrains the outputs to the required types.
- **FR-012**: When wired into the PM hook chain, the order MUST be: (1) A3 (per-ticker absolute bear suppression on UW/Sell), (2) Spec 006 bear-sector-symmetry filter (sector-relative bear suppression on UW/Sell), (3) Spec 003 + 003.5 contrarian gate (within-ticker / sector-baseline bull suppression on Buy/OW), (4) Spec 004 sector-momentum filter (sector-ETF bull suppression on Buy/OW), (5) **Spec 007 forward-catalyst filter (this spec — LAST in chain).** Spec 007 is last because it consumes ALL pre-filter outputs (the rating may have already been overridden to Hold by an earlier filter; the forward-catalyst filter still runs to capture the LLM annotation but the bull-side and bear-side branches both no-op when pre-rating is Hold).
- **FR-013**: The filter MUST be feature-flagged via the two mode keys (default-active for bull / default-shadow for bear). Setting both to `"off"` disables the filter entirely (no LLM call, no annotation). This is the operator's escape hatch for cost-sensitive workflows or for ablation experiments.
- **FR-014**: The filter MUST track per-call cost via the existing LLM client cost-tracking infrastructure (no new cost-tracking code; reuses `tradingagents/llm_clients/base_client.py` cost tracker if present). At Opus pricing (~$0.025/call) + ~5 ticker watchlist + daily cadence, total spec 007 LLM cost is ~$0.13/day for `daily_signals.py` workflow. Constitution III T1 (≤$5/experiment) classification applies; experiments using spec 007 should document the per-propagate cost addition.
- **FR-015**: As part of this spec landing, Constitution Principle VIII MUST be amended to v1.4.0 with a new sub-section "Forward-catalyst-class validation gate" containing: criterion 1 (discrimination ≥ +5pp in correct direction; PRIMARY), criterion 2 (cohort hit rate ≥ 60% when target cohort named), criterion 3 (net Δα ≥ +0.5pp OR shadow-mode-first if (3) is unmeasurable). The amendment is committed as part of this spec's implementation, not separately. CHANGELOG.md entry references the amendment + spec 007 as the trigger.

### Key Entities *(include if data involved)*

- **`CasePricedInScore`**: The Pydantic schema for the LLM structured output. Fields:
  - `bull_case_priced_in: float` (in [0, 1]) — how widely is the bull case ALREADY ACCEPTED by the market
  - `bear_case_priced_in: float` (in [0, 1]) — how widely is the bear case ALREADY ACCEPTED by the market
  - `rationale: str` (max length 2000) — short paragraph explaining both scores; references specific evidence from analyst reports

- **`ForwardCatalystAnnotation`**: The dict emitted to `state["forward_catalyst"]`. Fields:
  - `model: str` — the LLM model used (e.g., `"claude-opus-4-7"`)
  - `bull_case_priced_in: float | None` — the LLM's bull-side score (None if LLM failed)
  - `bear_case_priced_in: float | None` — the LLM's bear-side score (None if LLM failed)
  - `rationale: str | None` — the LLM's rationale (None if LLM failed)
  - `bull_threshold: float | None` — the configured bull threshold (None if `bull_mode="off"`)
  - `bear_threshold: float | None` — the configured bear threshold (None if `bear_mode="off"`)
  - `bull_mode: Literal["off", "shadow", "active"]` — the bull-side mode at evaluation
  - `bear_mode: Literal["off", "shadow", "active"]` — the bear-side mode at evaluation
  - `would_fire_bull: bool` — `True` iff `bull_case_priced_in > bull_threshold AND pre_rating in {Buy, Overweight} AND bull_mode != "off"`
  - `would_fire_bear: bool` — `True` iff `bear_case_priced_in > bear_threshold AND pre_rating in {Underweight, Sell} AND bear_mode != "off"`
  - `fired_bull: bool` — `True` iff `would_fire_bull AND bull_mode == "active"` (rating actually overridden via bull branch)
  - `fired_bear: bool` — `True` iff `would_fire_bear AND bear_mode == "active"` (rating actually overridden via bear branch)
  - `pre_rating: str` — the rating BEFORE this filter ran
  - `post_rating: str` — the rating AFTER this filter ran (may equal `pre_rating` if no fire)
  - `skipped: Literal["off", "llm_failed", "invalid_threshold", "rating_not_actionable"] | None` — reason filter didn't compute / fire (or `None` if it did)
  - `error: str | None` — exception summary if `skipped == "llm_failed"` (or None otherwise)

- **Configuration extensions to `TradingAgentsConfig` (TypedDict)**: Six new keys added to `tradingagents/default_config.py`:
  - `forward_catalyst_bull_mode: Literal["off", "shadow", "active"]` (default `"active"`)
  - `forward_catalyst_bear_mode: Literal["off", "shadow", "active"]` (default `"shadow"`)
  - `forward_catalyst_bull_threshold: float` (default `0.60`; range [0, 1])
  - `forward_catalyst_bear_threshold: float` (default `0.50`; range [0, 1])
  - `forward_catalyst_model: str` (default `"claude-opus-4-7"`; recommends `"claude-haiku-4-5"` for cost-sensitive workflows with degradation noted in quickstart)
  - `forward_catalyst_max_rationale_chars: int` (default `2000`; matches the retrofit script's max_length)

- **`AgentState` TypedDict extension**: New optional key `forward_catalyst: NotRequired[dict | None]` in `tradingagents/agents/utils/agent_states.py` (precedent set by spec 003 + spec 004 + spec 006).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Bull-side firing logic)**: When evaluated against a synthetic test corpus where `bull_case_priced_in = 0.78` and `bull_threshold = 0.60`, the filter MUST fire (bull-side) on `Buy`/`Overweight` ratings and NOT fire on `Hold`/`Underweight`/`Sell` ratings. Verified by 5 unit tests covering all 5 ratings × the threshold-crossed condition.
- **SC-002 (Threshold semantics — strict greater-than)**: When `bull_case_priced_in == bull_threshold` exactly (e.g., both 0.60), the filter MUST NOT fire (strict greater-than). Verified by a boundary unit test. Same for bear side.
- **SC-003 (Audit clarity)**: For every state log produced after this feature lands with mode != `"off"`, `state["forward_catalyst"]` MUST be present and equal a populated dict matching the schema in Key Entities. An aggregator script MUST be able to filter the corpus by `state["forward_catalyst"]["fired_bull"]` / `fired_bear` and produce per-side α statistics.
- **SC-004 (Reproducibility / determinism of decision)**: Running the filter twice with the same `(LLM scores, thresholds, modes, pre_rating)` tuple MUST produce identical fire decisions + post-ratings. The LLM call itself is non-deterministic but the filter's decision logic is.
- **SC-005 (Cost discipline)**: Per-propagate Opus cost MUST be ≤ $0.025 (per the retrofit measurement of $2.35 / 94 calls). At default Haiku (operator override), cost MUST be ≤ $0.0025/call. Verified by a unit test that mocks the LLM cost-tracker and asserts the per-call ceiling.
- **SC-006 (Both-modes-off honored)**: When BOTH `forward_catalyst_bull_mode` AND `forward_catalyst_bear_mode` are `"off"`, the filter MUST emit `state["forward_catalyst"] = None` or omit the key entirely AND NOT call the LLM (zero cost). PM ratings MUST be byte-identical to the no-filter baseline. Verified by a regression-guard unit test that mocks the LLM client and asserts zero invocations.
- **SC-007 (Test coverage)**: New code in `tradingagents/agents/utils/forward_catalyst_filter.py` AND the wiring in `portfolio_manager.py` MUST reach at least 90% line coverage. All 6 acceptance scenarios for User Story 1 + 4 for User Story 2 + 3 for User Story 3 are encoded as unit tests.
- **SC-008 (Empirical-validation gate against today's bear cohort)**: After landing, an offline retrospective script (`scripts/forward_catalyst_retrospective.py`) MUST be created that simulates the filter on the existing 45-commit cohort (27 ticker_weak-bull + 18 ticker_strong-bear) loaded from `claudedocs/sector-alpha-attribution-2026-05-06.csv`. At default thresholds (`bull_threshold=0.60`, `bear_threshold=0.50`), the script MUST verify: (a) bull-side fires on ≥24 of 27 ticker_weak commits (88.9% hit rate per Opus retrospective), (b) bear-side fires (in shadow mode) on ≥10 of 18 ticker_strong commits (per design doc §5 acceptance threshold; empirically validated at 13/18 in Opus retrospective). The script MUST extend the existing `scripts/forward_catalyst_class3_retrospective.py` to consume the production filter's CONFIG (vs the retrofit's hardcoded thresholds) and re-run against the same cohort.
- **SC-009 (Constitution v1.4.0 amendment)**: After landing, `.specify/memory/constitution.md` MUST contain Principle VIII v1.4.0 with the Forward-catalyst-class validation gate sub-section as specified in FR-015. Version bumped from 1.3.0 → 1.4.0 in the header + footer. CHANGELOG.md entry references the amendment.
- **SC-010 (LLM cost telemetry)**: Per-propagate cost addition from spec 007 MUST be measurable from the existing LLM client cost-tracker. Operators running `daily_signals.py` with default config (Opus + 5-ticker watchlist + daily cadence) see ≤$0.13/day total spec-007 cost addition. Verified by a manual smoke run with cost output captured.
- **SC-011 (Shadow-mode integrity for bear side)**: When `bear_mode == "shadow"` (the default), the bear-side branch MUST emit `would_fire_bear` annotations correctly but MUST NOT modify the rating under any circumstances. After 20+ propagates of shadow observation per the design doc §5 condition, the operator can review the annotations and decide on bear-side default-on flip. Verified by an integration test that runs 25 mocked-LLM propagates with shadow mode + asserts zero rating modifications + non-zero would-fire annotations.

## Assumptions

- **LLM provider source**: `tradingagents.llm_clients.factory.create_llm_client("anthropic", "claude-opus-4-7")` is the canonical entry point. Operators using non-Anthropic providers (OpenAI / Gemini) override `forward_catalyst_model` + the model gets routed via the same factory; structured-output failures degrade per FR-010.
- **Default model is Opus**: justified by the retrospective evidence — Haiku produces tighter score distribution + smaller cohort separation (5pp vs 10pp); Opus is required for the bull-side default-on flip to maintain the +14.43pp discrimination. Cost trade-off documented in quickstart; operators can opt-down to Haiku for cost-sensitive workflows with degradation accepted.
- **Default thresholds (0.60 bull / 0.50 bear)**: justified by the Class 3 Opus retrospective threshold sweep — 0.60 bull is the sweet spot where all 3 criteria pass; 0.50 bear is where criteria 1+2 pass with the highest discrimination. Operators can tune via config; tightening reduces fire rate + cohort hit rate; loosening risks more incorrect-suppression.
- **Bear-side default = shadow**: per Constitution VIII shadow-mode-first condition for criteria-1+2-only passes. NOT default-active. Operators must explicitly flip to active after observing n≥20 fresh propagates.
- **Filter ordering (last in chain)**: per FR-012, spec 007 runs LAST after all backward-price filters. Justification: spec 007 consumes the SAME analyst reports + debate as input that the prior filters already saw; running last ensures spec 007 sees the rating that survived the prior chain.
- **Cost discipline**: per Constitution III, spec 007 adds an Opus call per propagate (~$0.025). For the typical operator workflow (`daily_signals.py` on a 5-10 ticker watchlist), this is ~$0.125-0.25/day cost addition — well within T1 (≤$5/experiment). For backtest workflows running 100+ propagates, the Opus cost addition is ~$2.50; operators should account for this in `--yes` cost confirmation prompts.
- **State-log persistence**: additive to the JSON state log. Existing replay/analysis scripts continue to work. The `_log_state` whitelist + `AgentState` TypedDict extensions are one-line changes that mirror the spec 003 + spec 004 + spec 006 precedents.
- **No new propagate-stage hooks**: the filter is wired in the PM hook (existing infrastructure), not as a new analyst stage. The LLM call happens AT PM time, not as a separate analyst stage. This keeps the graph topology unchanged.
- **No interaction with paper-trading harness defaults**: the Spec 002 paper-trading harness consumes the framework's emitted ratings unchanged. If the bull-side filter is `"active"`, the harness sees Hold (and won't open a position). If `"off"` or `"shadow"`, the harness behaves identically to the no-filter baseline.
- **Constitution VIII amendment as part of spec landing**: not separate. The spec implementation includes the constitution edit + CHANGELOG entry. This codifies the methodology lesson AT THE TIME the first forward-catalyst filter ships, rather than retroactively.
- **Empirical retrospective evidence is load-bearing**: the spec is empirically justified by the Class 3 Opus retrospective (`claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md`). Future operators considering adjustments to thresholds / modes / model should re-run the retrospective with the new config to validate the change before flipping defaults. The retrospective script (`scripts/forward_catalyst_retrospective.py`) is the gate per FR-008's SC-008 + the new Constitution VIII v1.4.0 amendment.
