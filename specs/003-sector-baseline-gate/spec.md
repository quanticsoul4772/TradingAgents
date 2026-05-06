# Feature Specification: Sector-Baseline Fallback for Contrarian Gate

**Feature Branch**: `003-sector-baseline-gate`
**Created**: 2026-05-06
**Status**: Draft
**Input**: User description: "Cross-ticker (sector-level) baseline fallback for the spec 003 contrarian gate. Extends spec 003 with a sector-history fallback that fires when per-ticker history is below the FR-004 N>=20 floor. Empirical motivation (claudedocs/sc003-financials-gate-check-2026-05-06.md): SC-003 Financials investigation showed 4 of 5 losing OW commits had zero per-ticker prior history when the framework propagated on them, so the contrarian gate could not fire by construction even in shadow mode. Cross-ticker baseline closes that gap by aggregating bull_keyword_count history across all tickers in the same sector and using that as a percentile baseline when per-ticker history is thin."

## Why this exists

Spec 003 introduced the contrarian gate that downgrades Buy/Overweight to Hold when the analyst's `bull_keyword_count` exceeds the 80th percentile of the **per-ticker** prior history (≥20 historical observations per FR-004). The 2026-05-06 SC-003 Financials diagnostic (`claudedocs/sc003-financials-gate-check-2026-05-06.md`) revealed a structural gap:

- Of the 5 losing Financials Overweight commits in SC-003, **4 had zero per-ticker prior history** (BAC, WFC, GS, MA were all new-to-framework on 2026-04-03)
- The 5th (JPM) had 13 prior runs — below the FR-004 N≥20 floor
- The contrarian gate **could not fire by construction** on any of them, even in shadow mode
- The +6.46% retrospective Δα claim from `claudedocs/contrarian-gate-retrospective-2026-05-05.md` was concentrated entirely on tickers with thick per-ticker history (NVDA, AAPL — both had months of accumulated state logs)

For cold-start universes (operators starting a new watchlist; new tickers added to an existing watchlist; sector ETFs the framework hasn't yet seen), spec 003's gate provides **zero value**. This spec closes that gap with a sector-level fallback baseline.

The principled mechanism: if the operator has propagated on enough other tickers in the same sector, those observations carry SOME signal about typical bull-keyword density patterns for that sector, even if a specific ticker is new. A `bull_keyword_count` of 92 on a brand-new tech ticker is informative if the framework has seen Tech tickers cluster between 30-65 historically. The cross-ticker baseline preserves spec 003's "high prose density → mean-reverting bullishness" mechanism but extends it across same-sector observations rather than requiring per-ticker history.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cold-start ticker gets gate coverage via sector baseline (Priority: P1)

The operator runs `daily_signals.py` on a 10-ticker tech-sector watchlist where 2 tickers are new (zero per-ticker history). One of the new tickers receives a Buy rating with a high `bull_keyword_count` (e.g. 75). Per spec 003, the per-ticker history is empty so the gate skips. Per this spec, the gate falls back to the sector-level baseline: it aggregates `bull_keyword_count` history across all 8 prior-known tech tickers (combined 80+ observations), computes the 80th percentile of that pooled distribution, and fires the gate if 75 exceeds that percentile. The Buy is downgraded to Hold (active mode) or annotated as would-fire (shadow mode).

**Why this priority**: Without this story, the entire feature is moot — cold-start tickers were the empirical motivation. This is the MVP.

**Independent Test**: Hand-craft a sectors cache with 8 tech tickers having varied bull_keyword_count history. Run the gate against a new tech ticker with bull_kw=75 and per-ticker history N=0. Verify the gate fires when the sector-pooled 80th percentile is ≤75; verify it doesn't fire when sector-pooled 80th percentile is >75.

**Acceptance Scenarios**:

1. **Given** per-ticker history N=0 for ticker T, sector S has 80+ pooled observations of `bull_keyword_count`, and T's current `bull_keyword_count` exceeds the 80th percentile of the sector-pooled distribution, **When** the gate evaluates a Buy/Overweight for T, **Then** it fires (downgrade in active mode; would-fire annotation in shadow mode) with a `gate_baseline = "sector"` annotation.
2. **Given** per-ticker history N=0 AND sector pooled observations < 20, **When** the gate evaluates, **Then** it does NOT fire (insufficient_history); annotation reflects `gate_baseline = "none"`.
3. **Given** per-ticker history N=25 (above FR-004 floor), **When** the gate evaluates, **Then** it uses the per-ticker baseline as before (spec 003 semantics preserved); annotation reflects `gate_baseline = "per_ticker"`.
4. **Given** per-ticker history N=10 (below floor) AND sector pooled observations N=50, **When** the gate evaluates, **Then** it uses the sector-level baseline; per-ticker is NOT mixed in.

---

### User Story 2 - Operator distinguishes per-ticker vs sector firings in audit (Priority: P2)

The operator inspects the contrarian_gate annotation in a state log or events.jsonl entry. They want to know whether a gate firing was based on per-ticker history (high confidence — same-ticker mechanism validated by finding #4) or sector history (lower confidence — cross-ticker mechanism, no within-ticker IC validation). The annotation includes a `gate_baseline` field with values `"per_ticker"`, `"sector"`, or `"none"` (insufficient history) so the operator can filter accordingly.

**Why this priority**: Operational ergonomic — necessary so operators don't conflate the two firing types when computing realized α attribution, but not blocking the MVP firing logic.

**Independent Test**: Inspect contrarian_gate annotations across a mixed corpus (some thick-history tickers, some cold-start) and verify each annotation correctly identifies its baseline source.

**Acceptance Scenarios**:

1. **Given** a propagate that fires the gate via per-ticker baseline, **When** the operator reads `state["contrarian_gate"]["gate_baseline"]`, **Then** the value is `"per_ticker"`.
2. **Given** a propagate that fires via sector baseline, **When** the operator reads the same field, **Then** the value is `"sector"`.
3. **Given** a propagate where both per-ticker and sector floors are unmet, **When** the operator reads the field, **Then** the value is `"none"` and the gate did not fire.

---

### Edge Cases

- What happens when a ticker has no sector classification (yfinance returns `"Unknown"` per the `tradingagents/paper/sectors.py` cache)? Each `"Unknown"`-sector ticker is treated as its own sector for pooling purposes — i.e., effectively no sector-level pooling helps; gate falls back to "none". Same as if the ticker had its own one-element sector.
- What happens when the sector pool itself has many ticker contributions but they're all from one ticker (e.g., 50 NVDA observations and zero from anything else in Technology)? The pooled distribution is N=50, qualifies above floor; the gate fires based on it. This is acceptable: the operator is implicitly trusting that the dominant ticker's history represents sector dynamics. A future variant could require diversity (e.g., ≥3 distinct tickers in the pool) but v1 doesn't enforce.
- What happens when a sector has many tickers in the pool but the current ticker's `bull_keyword_count` is BELOW the sector median? The percentile is computed normally (e.g., 30th percentile) and is below the 80% threshold — the gate doesn't fire. Same semantics as per-ticker.
- What happens during the same-step processing of multiple new tickers in the same sector? The sector pool used for ticker A's evaluation does NOT include ticker B's current-day reading (strict no-look-ahead even within a step); only PRIOR observations contribute. This matches spec 003's strict-prior methodology.
- What happens when both per-ticker AND sector pools are above the floor? Per-ticker wins (spec 003 semantics preserved for thick-history tickers). Sector is the fallback only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The contrarian gate MUST evaluate baselines in fallback ladder order: (a) per-ticker history first; (b) sector-level pooled history when per-ticker count < FR-004 floor; (c) "none" / no fire when both are below floor.
- **FR-002**: The sector-level baseline MUST be computed from the pooled `bull_keyword_count` history across all tickers in the same GICS sector (per `tradingagents/paper/sectors.py` yfinance cache), strictly limited to PRIOR observations (no look-ahead within or across same-day evaluations).
- **FR-003**: The sector-level baseline floor MUST be configurable independently of the per-ticker floor (FR-004 of spec 003), defaulting to the same N=20 minimum to preserve spec 003's strictness rationale.
- **FR-004**: The gate MUST use the SAME 80th-percentile threshold and the SAME downgrade target (Buy/OW → Hold or Underweight per `contrarian_gate_target` config) regardless of which baseline (per-ticker vs sector) fired it. Spec 003's pluggable signal/feature configuration (`contrarian_gate_signal`, `contrarian_gate_feature`) is preserved.
- **FR-005**: The gate annotation emitted to state (`state["contrarian_gate"]`) MUST include a new field `gate_baseline` with values `"per_ticker"`, `"sector"`, or `"none"` indicating which baseline was used (or that none qualified).
- **FR-006**: The gate annotation MUST also include `n_history_per_ticker` and `n_history_sector` so operators can audit the size of each pool at evaluation time.
- **FR-007**: The fallback behavior MUST honor the existing `contrarian_gate_mode` config: `"off"` skips entirely (no annotation); `"shadow"` computes the annotation including `gate_baseline` but does not modify the rating; `"active"` computes and applies the downgrade.
- **FR-008**: When `"Unknown"` is the sector for a ticker (yfinance lookup failed or returned empty), the gate MUST NOT pool with other `"Unknown"`-sector tickers (each treated as its own one-ticker sector). Effectively the sector baseline is unavailable and the fallback collapses to "none".
- **FR-009**: The sector-history pool aggregation MUST be deterministic and reproducible across runs (same set of state logs → same pooled history → same percentile).
- **FR-010**: The feature MUST be feature-flagged via a new config key `contrarian_gate_sector_fallback_enabled` (default `True` once landed; settable to `False` to revert to spec 003 per-ticker-only semantics for ablation experiments per Constitution II).

### Key Entities *(include if data involved)*

- **SectorBaselineSource**: An enum-like string with values `"per_ticker"`, `"sector"`, `"none"` indicating which baseline was consulted at evaluation time.
- **GateAnnotation (extended)**: All existing fields from spec 003 plus `gate_baseline: SectorBaselineSource`, `n_history_per_ticker: int`, `n_history_sector: int`.
- **SectorPool**: A conceptual computed-on-demand collection of `bull_keyword_count` values aggregated from prior state logs of all same-sector tickers (excluding the current ticker's same-day reading per FR-002 strict-prior). Not persisted; recomputed per evaluation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Coverage extension)**: When evaluated against a synthetic test corpus with 5 cold-start tickers (per-ticker N=0) all in a sector with N≥20 pooled observations, the gate MUST emit a non-`"none"` annotation for at least 4 of the 5 (allowing one for sector-level percentile-below-threshold) versus the 0 of 5 spec 003 would emit.
- **SC-002 (Per-ticker preserved)**: When evaluated against a corpus with thick per-ticker history (≥20 observations per ticker), the firing decisions MUST be byte-identical to spec 003 (this feature is strictly additive on the cold-start path).
- **SC-003 (Audit clarity)**: For every state log produced after this feature lands, `state["contrarian_gate"]["gate_baseline"]` MUST be present and equal to one of the three enum values; an aggregator script MUST be able to filter the corpus by this field and produce per-baseline α statistics.
- **SC-004 (Reproducibility)**: Running the gate twice on the same set of state logs MUST produce byte-identical annotations including `gate_baseline`, `n_history_per_ticker`, and `n_history_sector`.
- **SC-005 (Ablation flag works)**: Setting `contrarian_gate_sector_fallback_enabled = False` MUST produce decisions byte-identical to spec 003 (cold-start gap restored). Verified by an ablation test that runs the same corpus under both flag values.
- **SC-006 (No new LLM cost)**: This feature adds zero LLM API calls. The sector baseline is computed entirely from existing persisted state logs.
- **SC-007 (Test coverage)**: New code targeting the sector-pool aggregator + the fallback-ladder logic reaches at least 90% line coverage. Tests cover all 4 acceptance scenarios in User Story 1.

## Assumptions

- **Sector source**: `tradingagents/paper/sectors.py` (yfinance cache, populated by Spec 002 paper-trading harness) is the canonical sector-membership source for both this gate and any future feature. If the harness sectors cache doesn't exist, the gate degrades to per-ticker-only (i.e., spec 003 semantics) without crashing.
- **State-log scan**: The sector-pool aggregator scans `~/.tradingagents/logs/<ticker>/TradingAgentsStrategy_logs/full_states_log_*.json` files for prior observations. This is the same I/O pattern used by `scripts/contrarian_gate_retrospective.py` and `scripts/sc003_financials_gate_check.py`. Cost: one filesystem scan per evaluation; cached if needed for performance.
- **Sector pooling does NOT remove the current ticker's own history**: if NVDA is in Tech and we're evaluating GOOGL with sector fallback, NVDA's prior observations DO contribute to the sector pool. This is intentional — the goal is "what does this sector typically look like."
- **No within-ticker correction**: when the sector baseline fires, we don't compute a within-ticker delta (current vs ticker mean) since by construction the ticker has thin per-ticker history. The percentile is purely against the sector-pooled distribution.
- **Default flag-on**: the feature ships with `contrarian_gate_sector_fallback_enabled = True` once landed. The flag exists primarily for ablation experiments per Constitution II.
- **Mode interaction**: in shadow mode the annotation IS emitted with the sector-baseline-derived `gate_baseline` field, so retrospective analysis can see what would have fired. In off mode no annotation is emitted at all (spec 003 semantics).
- **Sector-pool refresh cadence**: the pool is recomputed on each evaluation by scanning state logs at that moment. No persistent cache. If performance becomes a concern (e.g., large state-log directories), a future spec can add caching.
- **Within-step evaluations**: when multiple new tickers in the same sector are evaluated within the same step, each evaluation's sector pool excludes ALL same-day observations (not just the current ticker's). This preserves strict no-look-ahead.
