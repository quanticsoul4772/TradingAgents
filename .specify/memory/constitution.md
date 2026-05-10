# tradingagents-lab Constitution

**Project**: Personal experimental fork of TradingAgents — a research playground for studying multi-agent LLM debate dynamics, using equity-decision-making as the substrate because it has cheap, objective ground truth.

**Version**: 1.5.3
**Adopted**: 2026-05-01
**Last amended**: 2026-05-09 evening — added "Ticker-conditional clarification" paragraph to Principle VII Analyst-order scope sub-section after WC-11 v2 PARTIAL verdict. Empirical basis: `experiments/2026-05-09-002-wc11-v2-disambiguation/ANALYSIS.md` showed NVDA reproduces v1 first-/last-speaker effect at scale (news_fundamentals_market 40% replicates EXACTLY) BUT AAPL + MSFT do NOT show the same pattern (AAPL elevates with news-LAST orderings; MSFT shows fundamentals-early pattern). Analyst-order effect is conditional on (model × ticker × regime × prompt) per CLAUDE.md headline framing, NOT framework-general. The v1.5.2 randomize-or-document mandate stays AS-IS but is now explicit that effect varies by ticker. v1.5.2 → v1.5.3 (PATCH per scope-narrowing rule). Patch D applied per `claudedocs/constitution-v1.5.3-conditional-patch-drafts-2026-05-09.md` (PR #215).
**Prior version**: 1.5.2 — added "Analyst-order scope" paragraph to Principle VII Replicability-scope sub-section after WC-11 ALT-A verdict (first-speaker bias detected; ALT-B also triggered on same permutation). Empirical basis: `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md` showed commit rates ranging 0%-40% across 4 analyst-order permutations (±20pp from pooled 20% mean) at n=20; 2 of 5 dates produced divergent ratings across permutations. Operational implication: future ablations targeting commit-rate metrics MUST randomize analyst order OR explicitly document DEFAULT order as a confounder. Cross-references existing variance accounting (005-vs-007 NVDA finding). v1.5.1 → v1.5.2 (PATCH per scope-narrowing rule).
**Prior version**: 1.5.1 — added "Bear-regime validation" paragraph to Principle VII sub-section "Schema-induced abstention is NOT calibrated abstention" after WC-10 v3 PARTIAL ALT-A verdict. Empirical basis: `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS.md` showed direction matches ALT-A but `|α delta| < 1.0pp` on Q4 2025 NVDA (WC-10 mean +0.21% vs 5-tier +0.44%; Δpp -0.22). Caveat language preserved at v1.5.0 scope; empirical magnitude bound documented. Operational implication: Spec 009 Branch A activation does NOT require regime-aware gating as a hard requirement; runtime monitoring via `scripts/wc_10_underperformance_monitor.py` suffices. v1.5.0 → v1.5.1 (PATCH per scope-narrowing rule).
**Prior version**: 1.5.0 — added "Schema-induced abstention is NOT calibrated abstention" sub-section to Principle VII. Empirical basis: WC-10 v1 pilot (`experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md`) showed 90% commit rate (`|rating| > 0.2`) under continuous-scalar output vs 25% non-Hold rate under 5-tier categorical output across the same 20 (ticker, date) keys. SC-007 falsification verdict: ALT-A (categorical-bottleneck-confirmed). On NVDA the framework had clear bullish reads on every date but the 5-tier scale forced 8 of 10 emissions to Hold. The collapse-to-Hold was a SCHEMA artifact on this cohort, not calibrated abstention. v1.4.3 → v1.5.0 (MINOR per scope-narrowing rule: VII still applies but with explicit schema-artifact exception).
**Prior version**: 1.4.3 — added "Additive-to-existing-filter gate" sub-section to Principle VIII. Codifies the methodology lesson discovered tonight via Class 5 retrospective: a standalone PASS verdict can hide redundancy with existing default-active filters. New filter retrospectives that PASS the standalone gate must ALSO show net Δα improvement ≥ +0.5pp OR cohort hit improvement ≥ +5pp OR FP rate improvement ≥ -10pp over the union/intersection with the best-performing existing filter in the same direction. Prevents wasting ~6-8h spec+impl on filters that add nothing to the portfolio. v1.4.2 → v1.4.3 (PATCH per clarification rule).
**Prior version**: 1.4.2 — added a "Magnitude fungibility for hybrid filters" sub-section to Principle VIII forward-catalyst-class gate. Empirical basis: Spec 008 Hybrid C bull + Spec 009-candidate bear-inverted retrofits BOTH showed identical fire patterns across magnitude sweep within fixed window. v1.4.1 → v1.4.2 (PATCH per clarification rule).
**Prior version**: 1.4.1 — appended a "Spec ships its retrospective + verdict" sub-section to Principle VI. Codifies the pattern that today's 22-work-unit research-burst day demonstrated 5 times: spec invocation requires accompanying retrospective markdown in `claudedocs/` documenting the empirical justification + verdict + decision tree. Cost asymmetry (retrospective $0-2 / 1h vs spec+impl ~6-8h) makes "retrospective FIRST, spec SECOND" the dominant strategy. v1.4.0 → v1.4.1 (PATCH per clarification rule).
**Prior version**: 1.4.0 — extended **Principle VIII** with a "Forward-catalyst-class validation gate" sub-section. Empirical basis: Class 3 Opus retrospective DECISIVELY PASSED bull-side gate (discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp at T=0.60); bear-side passed criteria 1+2 with shadow-mode-first condition. Spec 007 ships as the first instance of this filter class.

This constitution governs how this project evolves. The commitments below are intentionally short and few. They are constraints, not aspirations — when in conflict with convenience, they win.

---

## Core Principles

### I. Save Everything (NON-NEGOTIABLE)

Every experiment writes its full output to `experiments/<YYYY-MM-DD>-<id>-<short-name>/`. The corpus is the research output, not the code. A run that doesn't save its full state log, params, and analysis is a wasted run.

**Required per experiment dir**:
- `HYPOTHESIS.md` — what we're testing, predicted outcome, success criterion
- `PARAMS.json` — exact knobs varied vs baseline
- `results.csv` (or equivalent) — raw output (gitignored, retained on disk)
- `ANALYSIS.md` — what we found, decision, one-line summary at top
- `run.sh` (or `run.ps1`) — one-line repro command

**Why**: Mode collapse, debate failures, and other phenomena we care about only become visible across many runs. The strategic doc this project produces is `findings.md` aggregated from `experiments/*/ANALYSIS.md` first lines, not commit messages.

### II. One Experiment Per Change

Each experiment varies **one** parameter against a documented baseline. If you can't write the experiment as "we varied X, holding everything else equal," it's not an experiment — it's a fork.

**Why**: The corpus must be interpretable as ablation data, not as a pile of one-off configurations. Two-variable experiments compound noise into uninterpretability.

**Acceptable exception**: a "shakeout run" of a new architecture against the existing baseline grid. Document explicitly as `shakeout_run: true` in `PARAMS.json`.

### III. Stay Cheap (tiered ceiling — amended 2026-05-03)

Per-experiment LLM spend is governed by a 4-tier ladder. Higher tiers require progressively more deliberation in `HYPOTHESIS.md` before launching.

| Tier | Range | Required deliberation |
|---|---|---|
| **T1: free exploration** | ≤ $5 | None. HYPOTHESIS may simply note "exploratory smoke." |
| **T2: standard** | $5 – $30 | HYPOTHESIS lists predicted cost + brief rationale (current default). |
| **T3: scaled** | $30 – $100 | HYPOTHESIS contains explicit cost-justification section: why this scale, what cheaper alternatives were considered, what specific outcome would justify the spend. |
| **T4: capital** | > $100 | HYPOTHESIS contains all of T3 plus: written multi-day deliberation, explicit fallback plan if the experiment doesn't deliver, alternative-experiment comparisons, and a "kill criteria" line stating what result would invalidate further T4 spending. |

The original $30 single-ceiling was set when Sonnet was the deep model (~$0.50/run) and the project had 0 prior experiments. As of 2026-05-03 we use Opus for the highest-impact runs (~$1/run) and have 13 experiments + $0-cost re-analysis pipelines (`scripts/horizon_sweep.py`, `identify_hold_extremes.py`, `bear_side_per_ticker.py`, `uw_suppression_filter.py`, etc.) that often substitute for new propagations entirely. The tiered structure reflects this maturity.

**Why tiered**: T1 + T2 stay friction-free for normal exploration; T3 forces explicit thought when scaling past 30 runs or swapping to Opus for a meaningful grid; T4 reserves the highest-spend decisions for genuine architectural commitments (e.g., the signal-lifecycle Phase 5 LLM-discovery effort budgeted at ~$250 lifetime).

**Implementation**: `scripts/backtest.py` already prints a cost estimate and gates on `--yes`. Future experiment runners follow the same pattern. The HYPOTHESIS template should grow a "Cost tier" frontmatter field; `scripts/new_experiment.py` should default it to T2 and require explicit elevation.

**Why this still preserves "Stay Cheap" intent**: every tier escalation is friction. A T4 experiment requires multi-day deliberation; a T3 requires written cost-justification. The ladder doesn't enable casual large spend, it just acknowledges that the *right* experiment occasionally costs $50-250 at the framework's current maturity, and forces deliberateness rather than blocking.

### IV. No Production Claims

The upstream disclaimer ("for research purposes... not investment advice") is load-bearing and we restate it. Nothing produced by this project may be presented as a trading recommendation, signal, or advice.

**Empirical backing** (added 2026-05-03 after 11 experiments + horizon sweep): the framework's 5-day rating bucket alphas are at the LLM single-call calibration ceiling — Buy α=-1.27% (n=8, 25% hit), Overweight α=-0.59% (n=33, 42% hit), Underweight α=+0.62% (n=26, 62% positive — wrong direction). At 21-day windows bullish commits do show ~+1.6% mean alpha across n=37 with 60-71% hit rate, AND single-call baseline does NOT show this lift, BUT n=37 across 9 tickers/dates is not portfolio-grade evidence and bear commits remain anti-calibrated at every horizon. This is research substrate, not signal.

**Why**: Beyond the obvious legal reasons: presenting research output as advice would corrupt the experimental discipline. We are studying *how the agents fail and where they marginally succeed*, not *whether they should be acted on*.

### V. Steal Liberally

Patterns from sibling projects in the portfolio are fair game without abstraction-purity tax:
- `agent-harness-v2` — event sourcing, structural enforcement, gates, knowledge digestion, antibodies
- `ladybird` — separate-process enforcement plane (Sentinel pattern)
- `battlecode2026` ratbot6 — value function over assigned roles, structured signaling
- `bruno-swarm` — multi-agent coordination patterns, abliteration for specialization
- `mcp-reasoning`, `branch-thinking`, `logic-thinking` — structured reasoning tools

Copy ideas, copy code, restate provenance in commit messages. The point is to test cross-project synthesis, not to maintain ten clean abstractions.

**Why**: This project's value is the cross-pollination, not the codebase. A "pure" abstraction we never reuse is worse than a messy direct copy that produces a finding.

### VI. Spec Before Structural Change

Any change to one of the following requires a spec under `.specify/specs/<id>-<name>/spec.md` before code:
- The event log schema (when introduced)
- Gate definitions and gate-firing logic (when introduced)
- Worker structures (the trading worker variant pattern)
- The `experiments/` directory convention itself
- The constitution

Use the spec-kit slash commands: `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

**Why**: The pilot showed the upstream framework had no spec for "the PM should produce all 5 ratings" — it was an implicit assumption that was violated emergently. Specs protect against the same class of failure here.

**Acceptable exception**: ad-hoc scripts under `scripts/` that don't touch structural state can skip the spec workflow. Bias toward writing the spec when in doubt.

### Spec ships its retrospective + verdict (added 2026-05-06 evening; v1.4.1)

Every spec MUST ship with an accompanying retrospective markdown in `claudedocs/` that documents:
1. **The empirical retrospective** that motivated the spec (or, for filters subject to Principle VIII, that PASSED the validation gate)
2. **The verdict block** — explicit pass/fail per the relevant gate criteria, with magnitudes
3. **The decision tree** — what happens if defaults are flipped, ablated, or the spec is later revisited

**Empirical basis** (today's 22-work-unit research-burst day demonstrated this pattern 5 times):

| Spec | Retrospective doc | Verdict |
|---|---|---|
| Spec 004 sector-momentum | `claudedocs/sector-momentum-retrospective-2026-05-06.md` | -0.45pp net Δα → default-off; KEEP off (Constitution VIII grandfathered) |
| Spec 006 bear-sector-symmetry | `claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md` | -0.71pp net Δα + SC-008 FAIL → default-off; KEEP off |
| Spec 005 candidate (per-ticker-vs-sector bull) | `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md` | max +0.31pp → SKIP spec entirely |
| Class 3 (Haiku) — Spec 007 candidate | `claudedocs/forward-catalyst-class3-retrospective-2026-05-06.md` | BORDERLINE → recommend Opus rerun |
| Class 3 (Opus) — Spec 007 actual | `claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md` | DECISIVE PASS → spec invocation justified at v0.7.0 |

The pattern: retrospective is the empirical justification for spec invocation (per Principle VIII v1.3.0 / v1.4.0 gates). The retrospective markdown ships alongside the spec dir so future readers can:
- Find the empirical case for the spec without reading commit history
- Re-run the retrospective with new corpus/data to revisit the verdict
- Understand WHY a default-on / default-off / shadow-mode-first decision was made

**Operational test**: `/speckit.specify` invocation for any new filter spec MUST be preceded by a retrospective commit in `claudedocs/<spec-name>-retrospective-<DATE>.md`. The spec.md preamble cross-references the retrospective. Constitution VIII gates apply to the retrospective; if the gate fails, the spec is NOT invoked.

**Why**: Without this codification, future iterations of the spec-kit workflow may write specs without the empirical-validation step, regressing back to the pre-v1.3.0 pattern of "build the filter, then maybe retrospect later." Today's $0-2 retrospective methodology is a Pareto improvement over the ~6-8h spec+impl+tests cost; the pattern is load-bearing for the project's research economy.

**Cost rationale** (cross-references Principle III): retrospectives cost $0-2 ($0 for offline-replay-against-existing-data; $0.10-2 for LLM-extracted features). Spec writing + implementation costs ~6-8h (~$0 LLM but significant time). The cost asymmetry makes "retrospective FIRST, spec SECOND" the dominant strategy for any filter mechanism class.

**Acceptable exception**: experimental "shakeout" filters scoped explicitly to operator-opt-in (default-off, no SC-008-style gate, marked `shakeout_filter: true` in PARAMS.json) — same exception as Principle VIII allows. Use sparingly.

### VII. Calibrated Abstention is a Valid Output (added 2026-05-03)

The framework's mode collapse to Hold ratings is empirically calibrated abstention, not a defect. Across 11 experiments and 4 reasoning architectures (full multi-agent framework, PM-blind variant, single-call baseline, MCP-reasoning Bayesian evidence tool), 5-day public-info evidence does not disambiguate forward direction at better than coin-flip rates. Hold is the architecturally correct response to that ambiguity. Single-call baselines that suppress Hold manufacture wrong-direction conviction.

**This principle replaces the prior implicit bias** that mode collapse needed fixing. MR-2 (synthesis prompt instrumentation) and MR-3 (v2 prompt) experiments were attacking honest output. Future experiments must justify why a proposed mode-collapse-breaking intervention would produce *better-calibrated* commits, not just *more* commits. The default null hypothesis is that more commits = more wrong commits.

**Why**: Without this principle, the project keeps re-discovering that prompt tweaks don't lift the calibration ceiling. With it, we ask the right question instead: when committing IS warranted (e.g., bullish 21-day), what makes the framework's commits work where single-call's don't?

**Operational test**: any new structural change that reduces Hold rate must include in its `HYPOTHESIS.md` (a) why the additional commits are expected to be calibrated rather than noise, (b) the horizon at which the calibration claim will be measured (5d? 21d? 90d?), (c) the directional asymmetry expectation (bull vs bear hit rate predictions).

**Replicability scope (added 2026-05-03 post-experiment-007)**: Claims derived from any single experiment must distinguish bucket-level from date-level evidence. Bucket-level claims ("Opus on NVDA-bull regime → ≥60% OW commits") are replicable across reruns; date-level claims ("Opus on NVDA 2026-02-06 → OW") are single observations. Empirical basis: experiment 005 produced 10/10 OW on Opus NVDA × 10 dates; experiment 007 produced 6/10 OW + 4 Hold on the SAME 10 NVDA dates with the same Opus model. Run-to-run variance is real because (a) exa news API returns different snippet sets per call, (b) per-experiment fresh memory logs evolve through the run. ANALYSIS.md write-ups must report bucket ratios as claims and per-date commits as observations.

**Analyst-order scope (added 2026-05-09, post-WC-11 ALT-A)**: The framework's analyst order is a confounding methodological variable for prior corpus claims. WC-11 (`experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md`, n=20 paired propagates / 5 dates × NVDA × 4 permutations / $8) found commit rates ranging from 0% (`market_fundamentals_news`) to 40% (`news_fundamentals_market`), a ±20pp shift from the pooled 20% mean — meets the ALT-A threshold for first-speaker bias AND ALT-B threshold for last-speaker bias (both triggered on the same `news_fundamentals_market` permutation; cannot disambiguate at n=20). 2 of 5 dates produced divergent ratings (UW/OW/Hold/Hold + Hold/OW/Buy/Hold) across permutations.

**Operational implication**: the project's DEFAULT analyst order `[market, news, fundamentals]` is empirically biased TOWARD Hold relative to alternative orderings — prior corpus bucket-level claims under DEFAULT order systematically UNDER-COUNT commits the framework would have emitted under news-first orderings. Future ablations targeting commit-rate metrics MUST either:

1. Randomize analyst order within the cohort (e.g., 4-permutation grid per ticker × date), OR
2. Explicitly fix the order AND document analyst-order as a confounder in HYPOTHESIS.md, AND restrict claims to within-order-cohort comparisons.

**Cross-reference to existing variance accounting**: the 005-vs-007 NVDA finding (10/10 OW → 6/10 OW + 4 Hold same dates same model) was previously attributed to stochastic LLM variance + exa news snippet variance + memory-log evolution. Post-WC-11, analyst-order is an additional documented contributor — both 005 and 007 used the DEFAULT order, so the within-order variance there is NOT order-related, but it sets the baseline for how much variance is order-specific vs cross-rerun stochastic.

**Ticker-conditional clarification (added 2026-05-09 evening, post-WC-11 v2)**: WC-11 v2 (`experiments/2026-05-09-002-wc11-v2-disambiguation/ANALYSIS.md`, n=60 paired propagates / 5 dates × 3 tickers × 4 perms / $24) found that the analyst-order effect is NOT framework-general but TICKER-CONDITIONAL. NVDA reproduced v1 first-/last-speaker effect EXACTLY (news_fundamentals_market 40% commit rate replicates between v1 and v2); AAPL elevated with the OPPOSITE pattern (news-LAST orderings: fundamentals_market_news 60% + market_fundamentals_news 60%; news_fundamentals_market only 20%); MSFT showed a fundamentals-early pattern. **No single analyst-position rule explains all 3 tickers**. Whatever first-/last-speaker effect exists is conditional on (model × ticker × regime × prompt) per CLAUDE.md headline framing. The randomize-or-document mandate above stays AS-IS but is now explicit that the underlying effect varies by ticker — pooled commit-rate analyses across heterogeneous ticker sets average out the order-effect, so per-ticker analysis is necessary for any commit-rate methodology claim. Constitution Patch D applied per `claudedocs/constitution-v1.5.3-conditional-patch-drafts-2026-05-09.md` (PR #215). v1.5.2 → v1.5.3 (PATCH per scope-narrowing rule).

**Cross-period scope (added 2026-05-03 evening post-experiment-008)**: Claims about realized α (not just commit-rate distribution) must be treated as period-conditional unless validated across multiple calendar periods. Empirical basis: experiment 007 (Opus 30-pair, Q1 2026 dates) produced 21d OW α = +3.05% n=8 with hit-rate climb 56→67→75%; experiment 008 (same config, Q4 2025 dates) produced -1.81% n=11 with hit-rate pattern 55→27→45%. Same model, prompt, A3 filter, news vendor, and tickers — only calendar period changed. The discrimination behavior (per-ticker bucket distribution) replicated cleanly cross-period; the realized-α direction did not. Reasoning_evidence Bayesian update: prior 0.64 (single-period n=50 milestone) → posterior 0.52 (roughly even odds the signal is stable cross-period vs period-favored). **Operationally**: any HYPOTHESIS asserting a realized-α property at the cross-experiment level must explicitly state (a) the calendar periods covered, (b) whether the property is claimed as period-stable or period-conditional, (c) the additional cross-period evidence required to upgrade the claim. ANALYSIS.md write-ups citing "the +X% OW α at n=N" as load-bearing must state the period composition of the n=N cohort and the cross-period replication status of the claim.

**Schema-induced abstention is NOT calibrated abstention (added 2026-05-08 post-WC-10)**: Where the underlying bull/bear evidence is one-directional but moderate-magnitude, the 5-tier categorical scale's collapse to Hold is a SCHEMA artifact, not calibrated abstention. Empirical basis: WC-10 v1 pilot (`experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md`) ran 10 dates × 2 tickers × 2 modes (continuous scalar vs 5-tier). On the SAME 20 (ticker, date) keys, continuous-scalar mode emitted `|rating| > 0.2` on 18/20 (90%) while 5-tier mode emitted non-Hold on 5/20 (25%) — a 3.6× ratio. NVDA was the clearest case: continuous-scalar emitted bullish reads (+0.38 to +0.72) on every date, while 5-tier emitted Hold on 8 of 10 dates. SC-007 falsification: ALT-A (categorical-bottleneck-confirmed) at distribution level.

**Operational implication**: VII still applies to commits whose underlying evidence is GENUINELY BALANCED (the original framing — "5-day public-info evidence does not disambiguate forward direction"). VII does NOT apply where:

- The underlying evidence is one-directional (bull-only or bear-only) but moderate-magnitude, AND
- The output schema lacks a partial-confidence tier between commit and abstain, AND
- Empirical evidence (e.g., a continuous-scalar replay against the same dates) shows the framework would commit if the schema permitted partial confidence.

Where these three conditions hold, the collapse-to-Hold is a SCHEMA fix problem, not an abstention discipline. The fix is the scale, not the inference. Future structural changes that "reduce Hold rate" must justify in HYPOTHESIS.md whether the change targets (a) genuine ambiguity (not eligible per VII), (b) schema-induced collapse (eligible — and the WC-10 pilot is the precedent), or (c) some mix.

**WC-10 caveat (signal calibration is asymmetric)**: WC-10 also showed that the bullish-side amplification was well-calibrated (NVDA Buy n=6 mean +4.67% α 21d) while the bearish-side amplification was anti-calibrated on this cohort (AAPL UW n=6 mean +3.56% α — UW called bearish but ticker rose +3-6%). Schema-fix recommendations should be cohort-aware: the case for breaking schema-induced collapse is strongest where the regime + ticker mix supports the proposed direction. Bear-regime validation of WC-10 (e.g., Q4 2025 NVDA replay) is required before treating the schema fix as universally beneficial.

**Bear-regime validation (added 2026-05-08, post-WC-10 v3)**: WC-10 v3 (Q4 2025 NVDA cohort, n=8 paired) confirms the asymmetric-calibration caveat at the predicted scope. On Q4 2025 NVDA — a regime where the framework's bullish commits historically failed (corpus headline: -0.47% mean 21d α, 22% hit) — WC-10 mode emitted 8/8 dates as Buy/OW (binned) vs 5-tier baseline's 0 OW + 1 UW + 7 Hold. The realized 21d α delta was -0.22pp (within ±100bps of baseline; statistically indistinguishable at n=8). The direction matches ALT-A (WC-10 amplifies the framework's bullish reads on a falling cohort), but the magnitude is small enough that the v1.5.0 caveat language ("WC-10 amplifies whatever signal the framework was already generating") is correct as-written without strengthening to "amplifies in a way that produces statistically worse outcomes." Empirical magnitude bound: `|delta| < 1.0pp` on this cohort.

**Operational implication for production deployment**: Spec 009 Branch A activation should ship with the v1.5.0 caveat documented in `docs/SIGNALS.md` per Spec 009 FR-006 but does NOT require regime-aware gating as a hard requirement. The direction of caution is correct; the magnitude is small enough that operator discretion (per docs/SIGNALS.md warning section) is sufficient. Runtime monitoring via `scripts/wc_10_underperformance_monitor.py` (PR #146) provides operational enforcement of the v1.5.0 caveat without requiring a regime-detection signal to gate WC-10 mode entirely.

### VIII. Retrospective Before Spec for Backward-Looking Price Filters (added 2026-05-06)

Any new rating-suppression filter whose mechanism is **backward-looking and price-derived** (i.e., consults only ticker / sector / index price history for the trade_date and prior N trading days, with no LLM call and no forward-looking signal) MUST pass a corpus retrospective showing **net Δα ≥ +1pp at the proposed default threshold** BEFORE the spec is written.

The retrospective is `$0` LLM cost (offline replay against the existing `experiments/*/results.csv` corpus + yfinance price history) and runs in ~1 hour. The full spec→plan→tasks→implement cycle for a filter of this class costs ~6–8 hours of work. Today's three retrospective failures (`claudedocs/sector-momentum-retrospective-2026-05-06.md`, `claudedocs/bear-sector-symmetry-retrospective-2026-05-06.md`, `claudedocs/ticker-sector-alpha-retrospective-2026-05-06.md`) validate that the cost asymmetry is severe enough that the retrospective gate must come FIRST for this filter class.

**Empirical basis** (2026-05-06):

| Filter (spec) | Default threshold | Net Δα at default | Cohort hit rate | Outcome |
|---|---|---|---|---|
| Spec 004 sector-momentum (bull/sector ETF) | -5% | -0.45pp / n=73 | suppressed 0/5 of SC-003 Financials | Default-OFF ship |
| Spec 006 bear-sector-symmetry (bear/ticker-vs-sector) | +5% | -0.71pp / n=36 | 5/18 of `ticker_strong`-bear cohort | Default-OFF ship; SC-008 FAILED |
| Spec 005 candidate (bull/ticker-vs-sector) | +3% / +5% | +0.23pp / +0.18pp / n=79 | 13/27 (48%) of `ticker_weak` cohort | SKIP spec (signal-to-noise too low) |

All three exhibit the same failure signature: backward-looking price patterns cannot DISCRIMINATE cohort losers from similar-pattern winners. Cohort-loser suppression (good) is roughly cancelled by winner suppression (bad). The mechanism class systematically misses cohorts whose realized α comes from forward-only catalysts (earnings, guidance, news, macro events) the filter cannot see at signal-generation time.

**Operational test** (required for any filter matching the trigger criteria):

1. Build the retrospective script in the same shape as `scripts/sector_momentum_retrospective.py` / `scripts/bear_sector_symmetry_retrospective.py` / `scripts/ticker_sector_alpha_retrospective.py`. Walks the corpus, computes per-commit feature, sweeps thresholds.
2. Report: (a) per-threshold n_kept / n_fired / kept_α / fired_α / **net Δα**; (b) per-sector breakdown at the proposed default; (c) cross-tab against any motivating cohort (e.g., the `ticker_weak` / `ticker_strong` cells from `scripts/sector_alpha_attribution.py`).
3. Write the verdict block at the bottom of the markdown output, applying the gate criteria below.
4. Commit the retrospective script + markdown BEFORE invoking `/speckit.specify`.

**Gate criteria** (both must pass for spec to be written):

- **Net Δα ≥ +1pp at the proposed default threshold** (the filter actually improves the bucket on the corpus).
- **Cohort hit rate ≥ 40% if a target cohort is named** (the filter actually catches a meaningful fraction of the failure-mode cohort it was built to address; e.g. ≥11 of 27 for spec 005 candidate).

If either criterion fails, **skip the spec entirely**. Document the verdict in the retrospective markdown for future reference. The decision to ship a filter as default-off operator-opt-in (spec 004 + spec 006 outcome) is reserved for filters whose IMPLEMENTATION already exists when the retrospective runs (i.e., the spec was written BEFORE this principle landed). New filters of this class do not get default-off ship as a fallback — they get skipped.

**Trigger criteria** (which filters this principle applies to):

- Yes: filter inputs are exclusively price/return/volume time series for the trade_date and prior N trading days (any combination of ticker / sector ETF / index / VIX / etc.).
- Yes: filter is deterministic given those inputs + a threshold (no LLM call, no learned model).
- Yes: filter targets rating suppression (Buy/OW → Hold; UW/Sell → Hold) at the PM hook stage.
- No: prose-density filters (spec 003 + spec 003.5 — operate on debate text, not price). Their mechanism class is fundamentally different and has its own validation track (within-ticker IC -0.489 finding).
- No: forward-catalyst-aware filters (news-density signals, options-IV, LLM-extracted features). Different mechanism class; validation criteria TBD if/when proposed.
- No: A3 (already shipped before this principle; precedent grandfathered). Future variants of A3 (e.g. different lookback / threshold) DO require pre-spec retrospective.

**Why**: Without this principle, the project will keep building filters that intuitively SHOULD work (fits the failure-mode taxonomy + has clean implementation path) but empirically DON'T (because forward catalysts dominate the cohort the filter targets, and similar-pattern winners cancel the cohort-loser gain). The cost asymmetry between retrospective ($0/1h) and spec+impl+tests ($0/6-8h) makes the retrospective-first ordering a Pareto improvement: it costs nothing to run, and it prevents 6-8 hours of work on filters whose empirical case won't hold. Three failures in one day is enough evidence to codify.

**Acceptable exception**: an experimental "shakeout" filter that is explicitly scoped to operator-opt-in (default-off, no SC-008-style empirical-validation gate, framed in the spec as "exploration, not commitment"). The filter still goes through `/speckit.specify` for documentation but skips the retrospective gate. Marked in `PARAMS.json` as `shakeout_filter: true`. Use sparingly — most filter ideas should pass the retrospective first.

### Forward-catalyst-class validation gate (added 2026-05-06; v1.4.0)

The original VIII gate (above) covers backward-looking + price-derived filters. **Forward-catalyst-aware filters** (mechanism class includes LLM-extracted features synthesizing analyst evidence, options-implied-volatility signals, news-density signals, fundamentals-delta features, cross-asset / regime features) follow a separate gate calibrated to their different signal characteristics:

1. **Discrimination ≥ +5pp in correct direction (PRIMARY)**. Among the suppressed cohort, the suppressed-cohort α magnitude must exceed the suppressed-non-cohort α magnitude by ≥ 5pp. This is the criterion spec 005 candidate FAILED catastrophically (-15pp wrong-sign discrimination) and that Class 3 Opus PASSED at +14.43pp (bull-side) / +23.10pp (bear-side).
2. **Cohort hit rate ≥ 60%** (tightened from VIII's 40%; forward-catalyst signals should be MORE specific because they have more information).
3. **Net Δα ≥ +0.5pp at the proposed default** (loosened from VIII's +1pp; smaller corpus + smaller discrimination is acceptable when criterion 1 is strong) **OR shadow-mode-first** for n ≥ 20 fresh propagates before active-mode flip if criterion 3 is unmeasurable on the small retrospective corpus.

**Empirical basis** (2026-05-06): Class 3 Opus retrospective on 94 cohort + control commits (`claudedocs/forward-catalyst-class3-opus-retrospective-2026-05-06.md`):

| Side | Cohort | Discrim | Hit rate | Net Δα | Outcome |
|---|---|---|---|---|---|
| Bull (T=0.60) | 27 ticker_weak | **+14.43pp** | **88.9%** | **+2.24pp** (n=33 fires) | DECISIVE PASS — bull default-on |
| Bear (T=0.50) | 18 ticker_strong | **+23.10pp** | **72.2%** | +0.30pp (n=24 fires) | Criteria 1+2 pass; shadow-mode-first per criterion 3 fail |

**Spec 007** (`specs/006-forward-catalyst-gate/`) ships as the first instance of this filter class, embodying the criteria above as `forward_catalyst_bull_mode = "active"` (default) + `forward_catalyst_bear_mode = "shadow"` (default).

**Operational test** (mirrors the original VIII gate, with criteria adapted):
1. Build the retrospective script in the same shape as `scripts/forward_catalyst_class3_retrospective.py`. Walks the corpus, computes per-commit feature, evaluates fire decisions at one or more thresholds.
2. Report: per-threshold n_kept / n_fired / kept α / fired α / **net Δα** + per-class mean scores + **discrimination magnitude** (suppressed-cohort α vs suppressed-non-cohort α) + cohort hit rate.
3. Write the verdict block at the bottom of the markdown applying the gate criteria.
4. Commit the retrospective + markdown BEFORE invoking `/speckit.specify`.

**Gate criteria** (all three must pass for spec to be permitted at default-on; OR criteria 1+2 must pass with shadow-mode-first condition for the failing side):
- Discrimination ≥ +5pp in correct direction
- Cohort hit rate ≥ 60% (when target cohort named)
- Net Δα ≥ +0.5pp OR shadow-mode-first if (3) is unmeasurable

If criterion 1 fails → SKIP spec entirely (mirrors backward-price-only gate failure pattern). If criteria 1+2 pass but criterion 3 fails → spec permitted with shadow-mode-first condition documented in the spec.

**Trigger criteria** (which filters this gate applies to):
- Yes: filter inputs include LLM-extracted features (synthesized from analyst evidence, prose, etc.)
- Yes: filter inputs include forward-looking signals (options-IV, news-density, fundamentals-delta, calendar features)
- Yes: filter inputs include cross-asset / regime features that aren't pure backward-price-only
- No: pure backward-price-only filters (use the original VIII gate above)
- No: prose-density filters operating on the framework's own debate text (use spec 003's IC-based validation; different mechanism class entirely)
- No: A3 (grandfathered; pre-dates Principle VIII)

**Why the separate gate**: forward-catalyst signals have different statistical properties than backward-price-only signals. The discrimination criterion is more load-bearing because forward-catalyst signals have (in principle) higher ceiling on per-commit information content; the net Δα threshold can be looser because corpus sizes for retrospective validation are often smaller (LLM scoring is more expensive than price-math). The shadow-mode-first condition lets operators observe production behavior on fresh data before committing to default-on, which is critical for LLM-feature filters where the retrospective sample may be small.

**Acceptable exception** (same as backward-price gate): explicit "shakeout" filters scoped to operator-opt-in (default-off, no validation gate, marked `shakeout_filter: true` in PARAMS.json).

### Magnitude fungibility for hybrid filters (added 2026-05-06 evening; v1.4.2)

For HYBRID filters (filters whose mechanism is a multiplicative or additive modulation of an underlying continuous-score filter), the **magnitude parameter is empirically fungible within a fixed window** when the modulation is large enough to cross the underlying threshold at the smallest tested magnitude. In that regime, sweeping magnitude is wasted compute — pick the most-conservative magnitude that produces the optimal fire pattern.

**Empirical basis** (2026-05-06):

| Retrospective | Sweep | Bull-side fire pattern at window=14d |
|---|---|---|
| Spec 008 Hybrid C bull (positive direction) | window={7,14,21}d × magnitude={0.5,1.0,2.0} | IDENTICAL across all magnitudes within window |
| Spec 009-candidate Hybrid C bear (inverted direction) | window={7,14,21}d × magnitude={0.5,1.0,2.0} | IDENTICAL across all magnitudes (no fires flipped at any config) |

The mechanism: at boost = 1.0 (earnings day, days_to_earnings=0), `effective = base × (1 + magnitude × 1.0)`. For a borderline-below-threshold base (e.g., 0.50, T=0.60), the smallest magnitude that pushes effective above T satisfies `0.50 × (1 + m) > 0.60` → `m > 0.20`. ANY magnitude > 0.2 produces an identical fire pattern at boost = 1.0. Sweeping magnitudes 0.5, 1.0, 2.0 all hit the same set of bordering scores.

**Operational test** (when applicable to a hybrid filter retrospective):
1. Sweep window first (the structural parameter that determines WHICH commits get any boost at all)
2. Sweep magnitude ONLY if the smallest tested magnitude doesn't satisfy `m × max_boost > (T - base) / base` for the borderline-cohort base scores
3. If magnitude sweep produces identical fire counts at every value: pick the SMALLEST tested magnitude as the production default (most conservative; minimizes saturation-clamp behavior at the [0, 1] boundary)
4. Document in the retrospective markdown: "magnitude is fungible within window=Nd at production thresholds; choosing M=X conservatively"

**Why**: Saves 60-66% of retrospective sweep time + reasoning. Spec 008's window=14d magnitude={0.5, 1.0, 2.0} sweep had three identical rows; only ONE row was needed once the fungibility was established. Future hybrid-filter retrospectives can default to a single magnitude (the smallest plausible) and only widen the sweep if results show variation.

**Non-applicability**: This principle applies ONLY to HYBRID filters whose modulation crosses the threshold at the smallest tested magnitude. For filters where:
- Magnitude affects fire patterns differently across cohort subgroups (some flip at m=0.5, some at m=1.0): KEEP the magnitude sweep
- Magnitude affects post-fire behavior beyond the binary fire decision (e.g., affects the suppressed rating's downstream cost): KEEP the magnitude sweep
- The retrospective is the FIRST instance of a hybrid filter class: KEEP the magnitude sweep to establish the fungibility regime

**Acceptable exception**: explicit "shakeout" sweeps that test magnitude as a hypothesis (e.g., does m=0.1 produce a DIFFERENT result than m=0.5?) — keep the sweep, document the hypothesis in the retrospective preamble.

**Why this matters operationally**: today's session demonstrated this twice (Spec 008 bull retrofit + bear-inverted retrofit). Each had 3 redundant rows. Codifying the principle now means future retrospectives skip the redundant work, freeing time for window-sweep + threshold-sweep variations that DO carry signal.

### Additive-to-existing-filter gate (added 2026-05-06 late-evening; v1.4.3)

For ANY new filter retrospective that PASSES the standalone Constitution VIII gate (whether backward-price OR forward-catalyst-class), an **OVERLAP analysis** against all existing default-active filters in the SAME DIRECTION (bull or bear) is REQUIRED before invoking `/speckit.specify`. The new filter must show one of:

1. **Net Δα improvement ≥ +0.5pp** for the union (new filter ∪ existing) over the BEST-performing existing filter alone, **OR**
2. **Cohort hit-rate improvement ≥ +5pp** for the union over the best-performing existing filter alone, **OR**
3. **False-positive-rate improvement ≥ -10pp** for the intersection over the best-performing existing filter alone (intersection variant — fire only when BOTH agree)

If NONE of the three improvement conditions hold, the new filter is REDUNDANT with the existing portfolio. **SKIP the spec entirely** even though the standalone gate PASSED. Document the redundancy in the overlap-analysis markdown for future reference.

**Empirical basis** (2026-05-06 late-evening — discovered via Class 5 retrospective):

The Class 5 (recent earnings surprise) retrospective PASSED the standalone Constitution VIII v1.4.0 forward-catalyst-class gate at threshold=0.02 with all three criteria clearing comfortably (discrim +11.92pp / hit 96.3% / net Δα +4.37pp). However, the post-hoc overlap analysis (`claudedocs/forward-catalyst-class5-vs-class3-overlap-2026-05-06.md`) revealed:

| Filter | n_fired | net Δα | cohort hit% | False-positive rate |
|---|---|---|---|---|
| Spec 007 alone (Class 3 LLM) | 33 | +2.24pp | 88.9% | 27% |
| Class 5 alone (surprise) | 41 | +4.37pp | 96.3% | 36% |
| Hybrid B union (OR) | 43 | **-1.85pp** | 96.3% | **39%** |
| Hybrid B intersection (AND) | 31 | +4.06pp | 88.9% | 22% |

**89% of cohort_a (bull losers) caught by BOTH** filters; only 2 incremental losers caught by Class 5 alone — at a cost of 8 additional false-positive winners. The union HURTS net Δα by -4.09pp vs Spec 007 alone. The two filters are correlated, not complementary.

**Without this gate, Spec 010 (Class 5 standalone) would have been invoked based on the standalone PASS verdict — wasting ~6-8h of spec+impl on a filter that adds nothing to Spec 007.** Cost asymmetry favors the additive test (~30min overlap analysis vs ~6-8h spec+impl).

**Operational test** (mirrors the original VIII gates, with overlap-comparison criteria adapted):

1. After the standalone retrospective PASSES the VIII gate, build an overlap script in the shape of `scripts/forward_catalyst_class5_vs_class3_overlap.py`. Compute the 2x2 fire-decision matrix (intersection / new-only / existing-only / neither) over the same cohort.
2. Report: per-set n / mean α / cohort hit / FP rate; underlying-filter comparison table; union AND intersection variants; explicit improvement vs each underlying filter.
3. Apply the 3-OR additive gate (net Δα ≥ +0.5pp OR cohort hit ≥ +5pp OR FP rate ≤ -10pp).
4. Write the verdict block at the bottom of the markdown.
5. Commit the overlap analysis BEFORE invoking `/speckit.specify`.

**Trigger criteria** (which retrospectives this gate applies to):

- Yes: ANY new bull-side filter retrospective that PASSES the standalone Constitution VIII gate AND there is at least one existing default-active bull-side filter
- Yes: ANY new bear-side filter retrospective that PASSES the standalone Constitution VIII gate AND there is at least one existing default-active bear-side filter
- No: A filter targeting a direction with NO existing default-active filter in the portfolio (the additive comparison is vacuous)
- No: A filter framed as a STRICT REPLACEMENT for an existing filter (different decision tree; out of scope for additive gate)
- No: HYBRID filters whose retrospective ALREADY uses the "improves over underlying filter" criterion (e.g., Spec 008 Hybrid C — already covered by the v1.4.2 magnitude-fungibility section's adjacent principle of "must improve at least one criterion vs underlying filter")

**Why this matters now**: today's filter portfolio has 4 default-active bull-side-relevant filters (spec 003, spec 003.5, spec 007 bull). The next bull-side filter retrospective will face a non-trivial overlap-analysis burden. Without this gate codified, future operators may invoke specs based on standalone PASS verdicts that hide redundancy. The 30-min overlap script is a cheap insurance policy.

**Acceptable exception**: same as VIII broader gates — explicit "shakeout" filters scoped to operator-opt-in (default-off, marked `shakeout_filter: true` in PARAMS.json) skip both the standalone gate AND the additive gate.

**Why the post-hoc retroactive verdict on Class 5**: the Class 5 standalone retrospective shipped today (`claudedocs/forward-catalyst-class5-retrospective-2026-05-06.md`) is left intact as historical record. The overlap analysis (`claudedocs/forward-catalyst-class5-vs-class3-overlap-2026-05-06.md`) supersedes its verdict — Class 5 is REDUNDANT with Spec 007 on this corpus, so Spec 010 invocation is NOT permitted under v1.4.3. If a future cohort expansion (e.g., 50-ticker SC-003 cross-window replication) shifts the overlap statistics, re-run the analysis and re-evaluate.

### Behavioral-additive sub-case (4th interpretation; added 2026-05-07; v1.4.6)

The Additive-to-existing-filter gate (v1.4.3) defaults to evaluating overlap
ON ACTUAL FIRE DECISIONS — what the new filter F actually fires vs what the
existing portfolio actually fires. Three sub-cases of "additive" cover
most workflows:

1. **Cohort-additive**: F catches different cohort losers than existing.
   Empirical overlap matrix shows < 60% intersection on the cohort.
2. **Mechanism-additive**: F operates on a different mechanism class than
   existing (e.g., LLM-extracted vs prose-density vs backward-price). The
   v1.4.0 forward-catalyst-class gate distinguishes mechanism classes
   formally.
3. **Underlying-additive** (hybrid filters): F MODULATES an underlying
   validated filter and improves at least one of its criteria (covered by
   the v1.4.2 magnitude-fungibility section's adjacent principle).

A **4th interpretation** — **behavioral-additive** — applies when F's
operational fire-decisions appear redundant with existing filters'
fire-decisions, BUT both correlate with the same PM commit decisions.
The PM has internalized F's contrarian logic via Constitution VII's
Calibrated Abstention training, so F is REDUNDANT-ON-EXECUTION but
COMPLEMENTARY-ON-DESIGN.

**The framing applies broadly to PM decisions, not just to one mechanism
class**: empirical evidence shows the PM has internalized contrarian
logic across multiple mechanism classes simultaneously (across this
project's filter portfolio: prose-density, LLM-extracted bull,
LLM-extracted bear, calendar-boosted). The right operating framing is
**PM-as-multi-mechanism-validator**: PM's Calibrated Abstention
operationally validates consensus across the analyst+debate ensemble —
when multiple mechanism classes flag the same contrarian condition,
PM commits Hold or stricter even though no filter operationally fires.

**Operational test** (when applying the v1.4.3 additive gate):

1. Run the standard intersection / new-only / existing-only / neither
   matrix on **actual** fire decisions (existing v1.4.3 procedure).
2. **ALSO** run a counterfactual matrix on **would-fire-if-PM-committed**
   decisions — parse state-log score fields without gating on actual
   pre_rating. (Reusable harness: `scripts/behavioral_additive_sweep.py`.)
3. Decision tree:
   - **Operational PASS** (cohort-additive on actual matrix per v1.4.3):
     SHIP THE SPEC unconditionally per existing v1.4.3.
   - **Operational FAIL but Mechanistic PASS** (counterfactual matrix
     shows F's would-fire matches PM's commits, different mechanism
     class than existing filters): **behavioral-additive case** — SHIP
     THE SPEC with documented expectation that production fires will be
     sparse until PM regime shifts. Document the behavioral-additive
     status in the spec's retrospective.
   - **Operational FAIL and Mechanistic FAIL**: SKIP per v1.4.3.

**Empirical basis** (2026-05-07 cross-cohort sweep):

The cross-cohort behavioral-additive sweep
(`scripts/behavioral_additive_sweep.py`,
`claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md`) walked
all 236 state logs accumulated 2026-05-04 to 2026-05-07 and found:

| Mechanism class | Behavioral-additive cases | Per-instrumented-log rate |
|---|---|---|
| Spec 003 (prose-density) | 7 | 70% |
| Spec 007 bull (LLM-extracted) | 7 → 8 (post-AMD) | 47-50% |
| Spec 007 bear (LLM-extracted) | 3 | 20% |
| Spec 008 (calendar-boosted) | 6 | 40% |

**ALL 4 mechanism classes show evidence**, distributed across 7 tickers
(AAPL, AMD, COP, INTC, MSFT, NVDA, WFC). MSFT shows the pattern in all 4
classes; AAPL+INTC in 3 each. AMD-04-17 (`claudedocs/amd-2026-04-17-deep-dive-2026-05-07.md`)
is the textbook case where PM verbalizes the bull-priced-in mechanism
in plain English — confirms the pattern is mechanistically interpretable,
not just numerically correlated.

**Three sub-patterns identified by the sweep**:

1. PM Hold + bull-priced-in scores high (original framing — "PM abstains
   when filter would suppress").
2. PM **stricter-than-Hold** (Underweight) + bull-priced-in scores high
   (extends original — "PM commits CONSISTENT-OR-STRICTER than the
   filter's would-be suppression"). AMD-04-17 + INTC×2 + AAPL-04-24
   are the canonical examples.
3. PM Hold + bear-priced-in scores high (BEAR-SIDE behavioral-additive;
   empirical kernel for Hybrid D candidate).

**Why this matters**: without the 4th interpretation, future filter
specs in mechanism classes the PM has internalized would all SKIP per
v1.4.3 — even though they provide robustness against PM regime drift
(if PM ever stops being Hold-prone, the filter starts firing on
previously-redundant cases). Codifying behavioral-additive prevents
SKIPPING mechanistically-valuable filter specs based on operational-
redundancy artifacts of the current PM regime.

**Risk acknowledged**: behavioral-additive is a permissive case. It
unlocks specs whose immediate operational impact is small. The risk is
shipping multiple specs whose fires never materialize in production.
Mitigation: behavioral-additive specs MUST also document a regime-shift
trigger (what PM behavior would cause F's fires to start materializing)
in the retrospective. If no plausible regime-shift exists, SKIP.

**Trigger criteria** (when this sub-case applies):

- Yes: new filter F PASSES the v1.4.3 standalone gate but FAILS the
  v1.4.3 additive overlap on actual fires.
- Yes: F's mechanism class is different from at least one existing
  default-active filter.
- Yes: counterfactual sweep shows F's would-fire correlates with PM's
  commits at ≥ 60% rate on the same cohort.
- No: F is in the SAME mechanism class as an existing default-active
  filter (then v1.4.3 standard applies — no behavioral-additive escape).

**Acceptable exception**: same as v1.4.3 broader gates — explicit
"shakeout" filters scoped to operator-opt-in (default-off, marked
`shakeout_filter: true` in PARAMS.json) skip both the standalone gate
AND the additive gate AND the behavioral-additive sub-case.

---

## Quality Gates

These are derived from the principles above. They must pass before any commit lands.

1. **All tests pass** — `pytest tests/ -q`. Currently 92/92.
2. **Ruff clean for new files** — pre-commit runs ruff on staged files. Existing baseline (305 errors) is grandfathered; new code adds zero new violations.
3. **No new tracked artifacts** — pilot CSVs, event logs, and experiment outputs go to gitignored paths. `git status` after a successful experiment should show only intentional doc/code changes.
4. **Spec exists for structural changes** — see Principle VI.
5. **`HYPOTHESIS.md` exists for experiment runs** — Principle I enforced; CI/pre-commit cannot enforce this directly, so the discipline is operator-enforced and visible in `findings.md` aggregation.

### Quality Gate #6 — Memory-log data-vs-prose discipline (added 2026-05-07; v1.4.5)

When operators read entries from any memory log file (`backtest_memory.md`,
`~/.tradingagents/memory/trading_memory.md`, or future variants),
operators MUST cross-check the entry's reflection prose against the
entry's header data (raw_return, alpha, holding_days). Reflection prose
can be hallucinated when the data contradicts the prior call's expected
direction; operators trusting prose over data risk propagating false
"lessons learned" into downstream decisions.

**Operational rule**:

1. **Read entry header FIRST**: extract date, ticker, rating, raw_return,
   alpha, holding_days.
2. **Check sign consistency**: bullish ratings (Buy, Overweight) expect
   raw_return ≥ 0; bearish ratings (Underweight, Sell) expect
   raw_return ≤ 0; Hold has no expected direction.
3. **If sign-mismatched, the reflection is SUSPECT**: do NOT cite
   reflection prose as evidence without verifying it acknowledges the
   data. Common hallucination phrases include "captured the inflection
   correctly," "validated the trim discipline," "directional call was
   correct" appearing on entries where the call DEMONSTRABLY failed at
   the holding-window horizon.
4. **In claudedocs / analysis**: distinguish "entry header says X" from
   "reflection narrates Y." Don't conflate.

**Empirical basis** (PR #54 + PR #55):

`scripts/memory_log_integrity_check.py` walks any memory log and flags
sign-mismatched entries with reflection-phrase scoring. On
`experiments/2026-05-07-001-spec-008-hybrid-c-ab-ablation/backtest_memory.md`
(15 resolved entries) it found:

| Ticker / Date | Rating | Raw return | Validation phrases in reflection |
|---|---|---|---|
| COP @ 2026-04-17 | Underweight | +4.90% | 1 |
| INTC @ 2026-04-17 | Underweight | +20.50% | 1 |
| AMD @ 2026-04-17 | Underweight | +24.90% | 5 (canonical) |

3 of 15 (20%) hallucinated reflections; ALL Underweight calls that went
UP; ALL with explicit self-validating phrases despite data refuting them.
PM-04-24 demonstrably trusted AMD-04-17's hallucinated reflection ("the
prior AMD lesson itself validates the trim discipline") rather than the
+24.9% raw return data — cascade-failure-mode documented.

**Mechanism explanation**: when `_resolve_pending_entries` writes a
reflection, the LLM generating the prose sees both the entry header data
AND the original DECISION prose. It faces "self-justification pressure"
when the realized data refutes the prior thesis: easier to write
narrative coherent with the prior thesis than to admit the call was
wrong. The framework has NO data-vs-prose consistency check on the
write; the prose can drift arbitrarily far from the data.

**Why this matters**:

- **Reflection-driven cascade failure**: PM trusts prior reflection
  prose over re-deriving from raw data. One bad reflection contaminates
  ALL downstream same-ticker runs until either (a) memory entry is
  manually corrected, or (b) realized data so strongly contradicts the
  cascading narrative that a future LLM generates a corrective
  reflection.
- **Operator-side defense is required**: framework provides no
  consistency check. Operators must parse data, not prose.
- **Symmetry with Constitution VII**: Principle VII says "filters parse
  rating, not prose" (in spirit, codified in operator memory). This
  Quality Gate extends the discipline to memory log: operators parse
  data, not prose.

**Tooling**:

`scripts/memory_log_integrity_check.py` (PR #55) is the canonical
reusable harness. Run periodically (or before any analysis that cites
memory log evidence) to surface suspect entries. Exit code 0 = clean,
1 = suspects found. CI-friendly.

**Acceptable exception**:

Hold-rating entries are exempt (no directional expectation). Reflection
prose on Hold entries can be checked using human judgment but isn't
flagged automatically.

**Trigger criteria** (when this gate applies):

- Yes: any operator analysis that cites prior memory log entries as
  evidence for current decisions.
- Yes: any spec retrospective that walks memory log to extract historical
  lessons.
- No: PM propagates themselves (framework-internal; framework lacks the
  consistency check to enforce). PM behavior is what THIS gate exists
  to protect operators against.

---

## Workflow

### Standard experimental loop

1. Pick an idea from `docs/EXPERIMENT.md` Tier 1 / 2 / 3.
2. Create `experiments/<date>-<id>-<name>/` with `HYPOTHESIS.md` and `PARAMS.json`.
3. If structural change required → `/speckit.specify` first.
4. Run: `bash run.sh` (or `pwsh run.ps1`) — produces `results.csv`.
5. Analyze: `scripts/analyze_backtest.py` (or experiment-specific analyzer) → `ANALYSIS.md`.
6. One-line summary at top of `ANALYSIS.md`.
7. Aggregate: `scripts/findings_aggregate.py` (when built) regenerates `findings.md`.
8. Commit: docs + scripts only; experiment outputs stay gitignored.

### Spec lifecycle (for structural changes)

1. `/speckit.constitution` — verify or amend constitution if needed.
2. `/speckit.specify <feature>` — generates `.specify/specs/<id>-<name>/spec.md`.
3. `/speckit.clarify` — if open questions exist, resolve interactively.
4. `/speckit.plan` — generates implementation plan.
5. `/speckit.tasks` — generates task list.
6. `/speckit.implement` — execute (or do by hand following the task list).
7. `/speckit.analyze` — post-mortem.

---

## Governance

This constitution is amendable. Amendments follow the spec-kit constitution flow (`/speckit.constitution`). Amendments must:

1. Be discussed in commit message body (not just title).
2. Bump the version (PATCH for clarification, MINOR for added principle, MAJOR for removed/redefined principle).
3. Update the "Adopted" date at the top.
4. Note the change in `CHANGELOG.md` under the relevant version entry.

The principles above are themselves up for amendment if they prove ceremonial rather than load-bearing. The test: after one month of use, are we honoring this principle because it's helping or because it's written down? If the latter, amend or remove.

**Version**: 1.4.6
**Last amended**: 2026-05-07 — appended a "Behavioral-additive sub-case (4th interpretation)" sub-section to Principle VIII v1.4.3 Additive-to-existing-filter gate. Codifies the case where a new filter F's operational fires appear redundant with existing portfolio fires BUT both correlate with PM commit decisions (PM has internalized F's contrarian logic via Constitution VII Calibrated Abstention training). Reframes PM operational role from analyst+debate aggregator to **multi-mechanism-validator**. Empirical basis: cross-cohort behavioral-additive sweep (`claudedocs/behavioral-additive-cross-cohort-sweep-2026-05-07.md`, PR #41 + AMD-04-17 deep-dive PR #43) — 23+ cases across 7 tickers in ALL 4 mechanism classes (Spec 003 prose-density, Spec 007 bull/bear LLM-extracted, Spec 008 calendar-boosted). MSFT shows pattern in all 4 classes; AMD-04-17 is textbook case (PM verbalizes bull-priced-in mechanism in plain English). Without this sub-case, future filter specs in mechanism classes the PM has internalized would all SKIP per v1.4.3 — even though they provide regime-drift robustness. Re-runnable harness: `scripts/behavioral_additive_sweep.py`. v1.4.5 → v1.4.6 (PATCH per clarification rule). Note: this content was originally drafted as v1.4.4 (`claudedocs/constitution-v1.4.4-draft-2026-05-07.md`) but ratified as v1.4.6 to preserve monotone numbering after v1.4.5 was ratified first per reasoning_decision rank ordering.
**Prior version**: 1.4.5 — added Quality Gate #6 "Memory-log data-vs-prose discipline" requiring operators to cross-check memory log entry reflection prose against entry header data. Empirical basis: PR #54 single-case (AMD-04-17 reflection claims "captured the inflection correctly" while header records +24.9% raw return showing trim FAILED) + PR #55 sweep finding the pattern is SYSTEMATIC at 20% incidence rate (3 of 15 entries; COP+INTC+AMD all Underweight calls that went UP). Symmetry with Constitution VII ("filters parse rating, not prose") extended to memory-log reading discipline ("operators parse data, not prose"). Tooling: `scripts/memory_log_integrity_check.py` (PR #55, 12 unit tests, CI-friendly exit code). v1.4.4 (drafted, not ratified) → v1.4.5 (PATCH per clarification rule, gap-skip).
**Prior version**: 1.4.3 — added "Additive-to-existing-filter gate" sub-section to Principle VIII. Discovered when Class 5 standalone retrospective PASSED but post-hoc overlap analysis showed 89% cohort overlap with Spec 007. v1.4.2 → v1.4.3 (PATCH).
**Prior version**: 1.4.2 — added a "Magnitude fungibility for hybrid filters" sub-section to Principle VIII (forward-catalyst-class gate). Empirical basis: Spec 008 Hybrid C bull retrofit + Spec 009-candidate bear-inverted retrofit BOTH produced identical fire patterns across magnitude={0.5, 1.0, 2.0} within fixed window. Codifies the methodology improvement: magnitude is fungible within a hybrid-filter window when the smallest tested magnitude already crosses the underlying threshold. Future retrospectives skip redundant magnitude sweeps in this regime. v1.4.1 → v1.4.2 (PATCH per clarification rule).
**Prior version**: 1.4.1 — appended a "Spec ships its retrospective + verdict" sub-section to Principle VI. Codifies the pattern that today's 22-work-unit research-burst day demonstrated 5 times: spec invocation requires accompanying retrospective markdown in `claudedocs/` documenting the empirical justification + verdict + decision tree. Cost asymmetry (retrospective $0-2 / 1h vs spec+impl ~6-8h) makes "retrospective FIRST, spec SECOND" the dominant strategy. v1.4.0 → v1.4.1 (PATCH per clarification rule).
**Prior version**: 1.4.0 — extended **Principle VIII** with a "Forward-catalyst-class validation gate" sub-section. Empirical basis: Class 3 Opus retrospective DECISIVELY PASSED bull-side (discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp at T=0.60 on n=33 fires); bear-side passed criteria 1+2 with shadow-mode-first condition (discrim +23.10pp / hit rate 72.2% / net Δα +0.30pp). Forward-catalyst signals follow a separate gate (discrim ≥ +5pp PRIMARY + cohort hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first) calibrated to their different statistical properties. Spec 007 ships as the first instance of this filter class.
**Prior version**: 1.3.0 — added **Principle VIII (Retrospective Before Spec for Backward-Looking Price Filters)** after three same-day retrospective failures (spec 004 sector momentum -0.45pp/n=73; spec 006 bear sector-symmetry -0.71pp/n=36; spec 005-candidate bull sector-relative +0.31pp max/n=79). Cost asymmetry: $0/1h retrospective vs ~6-8h spec+impl+tests. Backward-looking price filters cannot DISCRIMINATE cohort losers from similar-pattern winners; the retrospective gate must come FIRST for this filter class. Both criteria (net Δα ≥ +1pp at default + cohort hit rate ≥ 40%) must pass for spec to be written. Three failures in one day codified the lesson.
**Prior version**: 1.2.2 — Principle VII appended Cross-period scope clarification: realized-α claims (not commit-rate claims) must be treated as period-conditional unless validated across multiple periods. Empirical trigger: experiment 008 (same config as 007, Q4 2025 dates instead of Q1 2026) produced OW 21d α = -1.81% vs 007's +3.05%. Bayesian posterior on stable-cross-period-signal hypothesis dropped 0.64 → 0.52. ANALYSIS.md write-ups must state the period composition of any n=N cohort and the cross-period replication status of the claim.
**Prior version**: 1.2.1 — Principle VII appended Replicability-scope clarification: bucket-level (replicable) vs date-level (single observation) evidence. Trigger: 005-vs-007 NVDA non-replication on the same dates.
**Prior version**: 1.2.0 — Principle III restructured from single $30 ceiling to 4-tier ladder (T1 ≤$5 / T2 $5-30 / T3 $30-100 / T4 $100+) reflecting Opus pricing + accumulated re-analysis tooling; added Principle VII (Calibrated Abstention is a Valid Output); sharpened Principle IV with empirical backing.
**Prior version**: 1.1.0 — added Principle VII + sharpened IV (2026-05-03 earlier in the day)
**Prior version**: 1.0.0 — initial adoption 2026-05-01
