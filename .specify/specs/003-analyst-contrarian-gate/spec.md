# Feature Specification: Analyst-stage Contrarian Gate

**Feature Branch**: `003-analyst-contrarian-gate`
**Created**: 2026-05-05
**Status**: Draft
**Input**: User direction: "/speckit.specify spec 003 architectural variant for analyst-stage contrarian gating motivated by today's finding #4"

## Background

Derived from the within-ticker artifact-check finding documented in `claudedocs/within-ticker-artifact-check-2026-05-05.md` and elevated to publishable secondary finding #4 in `RESEARCH_FINDINGS.md`:

> `market_report bull_keyword_count` shows aggregate IC near zero (-0.011) but **within-ticker median IC = -0.4890 with 9 of 9 tickers negative**. Within-ticker permutation p<2e-4 (passes Bonferroni for 280 tests). Period-stable across Q4 2025 + Q1 2026 (4/4 and 9/9 negative). Six of nine tickers have CI excluding zero individually. **First validated within-ticker predictor in the corpus.** Mechanism candidates (not adjudicated): mean-reversion, recency bias, selection on recently-strong tickers.

The framework's market analyst is most bullish at locally-bullish moments that mean-revert over 90d. The current pipeline does not exploit this: the rating-stage decision agents (`research_manager`, `trader`, `portfolio_manager`) consume the market analyst's prose without a contrarian transform. A direct architectural intervention is to **gate or anti-weight the rating when the market analyst's prose hits a high bull-keyword density**.

This is structurally analogous to the **A3 mean-reversion suppression filter** (`tradingagents/agents/utils/momentum_filter.py`), which suppresses bearish UW commits when the underlying ticker is in mean-reversion zone. A3 operates on price; the contrarian gate operates on prose.

Per Constitution Principle VI (Spec Before Structural Change): introducing a contrarian gate that modifies the framework's commit behavior is a structural change requiring this spec before code.

Per Constitution Principle VII (Calibrated Abstention): the gate is permitted to either (a) downgrade bullish commits to Hold or (b) annotate the decision without modifying the rating. Justifying a Hold-rate change is satisfied by the empirical evidence in finding #4 itself — the within-ticker contrarian pattern is the calibration evidence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Shadow-mode contrarian flag (Priority: P1)

As a researcher, I want every Portfolio Manager decision to carry a **contrarian-gate annotation** computed from the market analyst's `bull_keyword_count` percentile within that ticker's recent history, so I can measure how often the gate would fire on production runs and whether the gated subset of commits has different realized α than the ungated subset, **without modifying the actual rating**.

**Why this priority**: foundational. Phase 1 mirrors the BOTS Phase 1 (Shadow Aggregator) and Spec 002 Phase 1 patterns — measure first, change behavior later. Removes the risk of shipping a gate that's miscalibrated by validating against real propagates first.

**Independent Test**: Run a fresh 10-date NVDA propagate with `contrarian_gate_enabled = True` (shadow only). Verify the state log carries `contrarian_gate: {percentile, threshold, would_fire, market_bull_count}` per propagate, and that the actual `final_trade_decision` rating is unchanged from the no-gate baseline.

**Acceptance Scenarios**:

1. **Given** a propagate completes with `contrarian_gate_enabled = True`, **When** the state log is read, **Then** it contains a `contrarian_gate` block with at minimum `percentile` (0-100, the market analyst's bull_keyword_count percentile within that ticker's last N=20 cached propagates), `would_fire` (bool, true when percentile >= configurable threshold), and `market_bull_count` (raw count for this propagate).
2. **Given** the gate is in shadow mode, **When** the same propagate is run with and without the gate flag, **Then** both runs produce byte-identical `final_trade_decision` content (gate is observation-only).
3. **Given** N >= 30 historical propagates have shadow-gate annotations, **When** I run a new analysis script `scripts/analyze_contrarian_gate.py`, **Then** it produces a markdown report with the realized 21d/90d α conditional on `would_fire = True` vs `would_fire = False` across the OW + Buy commit subset.

---

### User Story 2 — Active-gate mode (Priority: P2)

As a researcher, I want a config flag that **promotes the contrarian gate from shadow to active** — when the gate fires on a Buy or Overweight commit, the Portfolio Manager downgrades the rating to Hold (or to Underweight, configurable). Hold and Underweight commits are unchanged.

**Why this priority**: blocked on User Story 1 (need empirical evidence that the gate identifies the commit subset finding #4 implies). Active mode is the production-augmentation use case, parallel to A3's `uw_momentum_filter_threshold`.

**Independent Test**: Run a 10-date grid in shadow mode, then a matched 10-date grid in active mode. Compare rating distributions: active mode should have lower OW + Buy rate among the propagates where the gate fired, and the downgraded ratings should appear as Hold (or Underweight, per config).

**Acceptance Scenarios**:

1. **Given** `contrarian_gate_mode = "active"` and `contrarian_gate_target = "hold"`, **When** a propagate's gate fires AND the PM rating is Buy or Overweight, **Then** the final rating is overridden to Hold and the decision markdown carries an explicit annotation explaining the contrarian-gate override.
2. **Given** `contrarian_gate_mode = "active"`, **When** a propagate's gate fires AND the PM rating is already Hold/UW/Sell, **Then** the rating is unchanged (gate only suppresses bullish commits).
3. **Given** matched shadow vs active runs on the same 10 dates, **When** rating distributions are compared, **Then** active-mode OW + Buy rate is strictly less than shadow-mode rate, and the downgrades are concentrated on the propagates where `would_fire = True`.
4. **Given** `contrarian_gate_mode = "off"` (default), **When** any propagate runs, **Then** behavior is byte-identical to pre-spec-003 production.

---

### User Story 3 — Per-ticker percentile baseline (Priority: P2)

As a researcher, I want the gate's "bull_keyword_count percentile" to be computed **per ticker** (not pooled across tickers), so the gate's calibration matches the within-ticker mechanism documented in finding #4.

**Why this priority**: critical for correctness. Finding #4's signal is within-ticker, not between-ticker — pooling would re-introduce the between-ticker artifact pattern documented in `claudedocs/featurizer-artifact-check-2026-05-04.md`. Wrong baseline = gate fires on between-ticker variance instead of within-ticker variance.

**Independent Test**: Construct a synthetic case where ticker A has bull_keyword_counts in [10, 20, 30] across three propagates and ticker B has counts in [5, 10, 15]. Verify the percentile for ticker A's count=30 propagate is 100% (highest within ticker A) AND the percentile for ticker B's count=15 propagate is also 100% (highest within ticker B), even though A's 30 > B's 15 in absolute terms.

**Acceptance Scenarios**:

1. **Given** the contrarian gate is enabled, **When** percentile is computed for a ticker with N >= 20 cached propagates, **Then** it uses ONLY that ticker's history, not the corpus-wide distribution.
2. **Given** a ticker with N < 5 cached propagates, **When** the gate runs, **Then** it returns `would_fire = False` and emits a `gate_skipped: insufficient_history` annotation (no false-positives from low-n).
3. **Given** the per-ticker percentile baseline is implemented, **When** the gate fires across N=30 historical propagates, **Then** the within-ticker IC of the `would_fire` boolean against 90d α is significantly negative (matches finding #4's direction).

---

### User Story 4 — Generalize beyond market_report (Priority: P3)

As a researcher, I want the gate's source signal to be **configurable** — `market_report bull_keyword_count` is the validated default, but I want to be able to swap in any (signal, feature) pair so I can test gates motivated by future within-ticker findings without rewriting the gate machinery.

**Why this priority**: hedge against finding #4 being market-analyst-specific. If a follow-up artifact check on `news_report bull_keyword_count` (queued from commit `b8456cc`) shows the contrarian pattern generalizes, the gate should be reconfigurable to use that signal too. Or to use a composite of multiple analyst-stage features.

**Independent Test**: Reconfigure `contrarian_gate_signal = "news_report"` + `contrarian_gate_feature = "bull_keyword_count"`. Verify the percentile is computed from news_report values and the gate fires on a different subset of propagates than the market_report-default.

**Acceptance Scenarios**:

1. **Given** `contrarian_gate_signal` and `contrarian_gate_feature` are set in config, **When** the gate runs, **Then** it pulls the percentile from `(signal, feature)` cached values rather than hardcoded `market_report bull_keyword_count`.
2. **Given** the source feature is missing from the cache for a ticker (e.g., the analyst wasn't run), **When** the gate runs, **Then** it returns `gate_skipped: missing_source_signal` annotation and does not fire.
3. **Given** a composite source (multiple `(signal, feature)` pairs combined via `mean` or `max` percentile), **When** the gate runs, **Then** the composite percentile is logged in the annotation alongside the individual components.

## Functional Requirements *(mandatory)*

- **FR-001**: `tradingagents/signals/contrarian_gate.py` provides a `ContrarianGate` class with `compute_annotation(ticker, market_report_text, cache)` returning a dict `{percentile, threshold, would_fire, market_bull_count, gate_skipped?}`.
- **FR-002**: The gate is wired into `tradingagents/agents/managers/portfolio_manager.py` after the LLM PM decision but before the SignalProcessor extracts the rating. Annotation is always added to the decision markdown; rating override only happens when `mode == "active"`.
- **FR-003**: Three new config keys in `default_config.py`:
  - `contrarian_gate_mode`: `"off"` (default), `"shadow"`, `"active"`
  - `contrarian_gate_threshold`: integer percentile (default `80`)
  - `contrarian_gate_target`: `"hold"` (default) or `"underweight"` — what rating to downgrade to when gate fires in active mode
- **FR-004**: Per-ticker percentile baseline uses the most recent N=20 cached `(market_report, ticker, *, bull_keyword_count)` values from `~/.tradingagents/signals/cache.db`. **When N < 20, gate is skipped** (was N < 5 in the initial spec; bumped after the XLF investigation in `claudedocs/xlf-mechanism-2026-05-05.md` showed that N=10 with a degenerate prior-α distribution can fire false positives — the percentile is meaningless when the source feature has near-zero variance over the window). The gate emits `gate_skipped: insufficient_history` when N < 20.
- **FR-005**: Active-mode override only applies when PM rating is Buy or Overweight (per finding #4: the contrarian signal anti-predicts bullish commits, no evidence for the bearish direction).
- **FR-006**: State log emission: every propagate with `contrarian_gate_mode != "off"` writes a `contrarian_gate` block in the state log JSON for downstream analysis.
- **FR-007**: Backwards-compat: when `contrarian_gate_mode = "off"` (default), graph behavior is byte-identical to pre-spec-003.
- **FR-008**: New analysis script `scripts/analyze_contrarian_gate.py` reads cached + state-logged annotations, produces `claudedocs/contrarian-gate-analysis-<date>.md` with α stratified by `would_fire`.

## Success Criteria *(mandatory)*

- **SC-001** (Phase 1 / shadow correctness): On a fresh 10-date NVDA propagate in shadow mode, the gate annotation appears in 10/10 state logs, and `final_trade_decision` content is byte-identical to a no-gate baseline run.
- **SC-002** (Phase 1 / signal validation): Across N >= 30 shadow-mode propagates, the within-ticker IC of `would_fire` (boolean treated as +1/-1) against 90d α reproduces the finding #4 pattern — within-ticker median IC <= -0.30 with majority of tickers showing direction agreement. **Precondition**: tickers in the validation grid must have prior 30d α range >= 10pp (contain both meaningfully positive and meaningfully negative prior 30d α observations). Tickers in degenerate-window regimes (e.g., XLF in the current corpus, where all 10 cached dates fall in a sustained-underperformance window with prior 30d α range -6.48% to 0%) are excluded from this success criterion. The XLF case is documented in `claudedocs/xlf-mechanism-2026-05-05.md`.
- **SC-003** (Phase 2 / active mode behavior): Matched shadow-vs-active grids of N >= 10 each show active-mode OW + Buy rate strictly lower than shadow rate, with downgrades concentrated on `would_fire = True` propagates.
- **SC-004** (Phase 2 / α improvement, optional): Active-mode commits produce mean 21d α >= shadow-mode commits (point estimate, not strict significance — a $0 retrospective forecast is unblocked by SC-001+002).

## Out of Scope (this spec)

- LLM-emitted contrarian signals (the gate uses the existing market_analyst prose; no new LLM call).
- Cross-analyst composite signals beyond the pluggable single-source design (User Story 4 covers single-source generality; multi-source composite is left to a future spec if needed).
- Adjusting per-bot LLM model routing (Spec 001 Phase 4) based on gate state.
- Real-time threshold tuning. The threshold is a static config; auto-tuning from metrics is a future User Story.

## Open Questions

- **OQ-1**: Should the gate fire on `Buy` commits the same way it fires on `Overweight`, or treat Buy as more conviction-bearing and require a higher threshold? (Default in this spec: same threshold for both, matching finding #4's pooling of Buy + OW into "bullish commits".)
- **OQ-2**: When the gate fires in active mode, should the override be Hold (calibrated abstention) or Underweight (active contrarian)? Default: Hold. Underweight would be more aggressive but lacks empirical support — finding #4 is anti-prediction of bullish, not pro-prediction of bearish.
- **OQ-3**: Should the percentile baseline use a rolling window (e.g., last 20 propagates) or all available history? Default: last 20, matching the BOTS / drift-detector convention.
- **OQ-4**: How does this interact with the A3 momentum filter? A3 suppresses UW commits when ticker is in mean-reversion zone; spec 003 suppresses Buy/OW commits when market analyst is too bullish. Both could fire on the same propagate. Default: independent — let both run, log both annotations, do not arbitrate.
- **OQ-5** (added 2026-05-05 after XLF investigation): how should the gate handle tickers in sustained-underperformance regimes (XLF in this corpus had all 10 cached dates with non-positive prior 30d α + uniformly high bull_keyword_count)? Three candidate strategies: **(a) skip entirely** — if prior 30d α range over the percentile window is < some threshold (e.g., 5pp), emit `gate_skipped: degenerate_window` and don't fire; **(b) fire only on the percentile-and-trend conjunction** — require both high bull_count percentile AND meaningfully positive prior strength to fire; **(c) accept and treat as weak signal** — fire on percentile alone, accept that the gate operates on a different regime than the recency mechanism on degenerate-window tickers. Default in the spec is unresolved; needs validation data to decide.

## Related work

- **Finding #4**: `claudedocs/within-ticker-artifact-check-2026-05-05.md` — empirical foundation
- **A3 momentum filter**: `tradingagents/agents/utils/momentum_filter.py` — structurally analogous pattern (price-based suppression of bearish commits); spec 003 is the prose-based mirror image (suppression of bullish commits)
- **Spec 001 Phases 1-2**: Shadow → opt-in active pattern this spec follows
- **Constitution Principle VII**: Calibrated abstention is a valid output — gate downgrades to Hold are calibrated per the empirical evidence behind finding #4
