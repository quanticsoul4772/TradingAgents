# tradingagents-lab Constitution

**Project**: Personal experimental fork of TradingAgents — a research playground for studying multi-agent LLM debate dynamics, using equity-decision-making as the substrate because it has cheap, objective ground truth.

**Version**: 1.4.2
**Adopted**: 2026-05-01
**Last amended**: 2026-05-06 (evening, fourth amendment of the day) — added a "Magnitude fungibility for hybrid filters" sub-section to Principle VIII forward-catalyst-class gate. Empirical basis: Spec 008 Hybrid C bull + Spec 009-candidate bear-inverted retrofits BOTH showed identical fire patterns across magnitude sweep within fixed window. v1.4.1 → v1.4.2 (PATCH per clarification rule).
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

**Cross-period scope (added 2026-05-03 evening post-experiment-008)**: Claims about realized α (not just commit-rate distribution) must be treated as period-conditional unless validated across multiple calendar periods. Empirical basis: experiment 007 (Opus 30-pair, Q1 2026 dates) produced 21d OW α = +3.05% n=8 with hit-rate climb 56→67→75%; experiment 008 (same config, Q4 2025 dates) produced -1.81% n=11 with hit-rate pattern 55→27→45%. Same model, prompt, A3 filter, news vendor, and tickers — only calendar period changed. The discrimination behavior (per-ticker bucket distribution) replicated cleanly cross-period; the realized-α direction did not. Reasoning_evidence Bayesian update: prior 0.64 (single-period n=50 milestone) → posterior 0.52 (roughly even odds the signal is stable cross-period vs period-favored). **Operationally**: any HYPOTHESIS asserting a realized-α property at the cross-experiment level must explicitly state (a) the calendar periods covered, (b) whether the property is claimed as period-stable or period-conditional, (c) the additional cross-period evidence required to upgrade the claim. ANALYSIS.md write-ups citing "the +X% OW α at n=N" as load-bearing must state the period composition of the n=N cohort and the cross-period replication status of the claim.

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

---

## Quality Gates

These are derived from the principles above. They must pass before any commit lands.

1. **All tests pass** — `pytest tests/ -q`. Currently 92/92.
2. **Ruff clean for new files** — pre-commit runs ruff on staged files. Existing baseline (305 errors) is grandfathered; new code adds zero new violations.
3. **No new tracked artifacts** — pilot CSVs, event logs, and experiment outputs go to gitignored paths. `git status` after a successful experiment should show only intentional doc/code changes.
4. **Spec exists for structural changes** — see Principle VI.
5. **`HYPOTHESIS.md` exists for experiment runs** — Principle I enforced; CI/pre-commit cannot enforce this directly, so the discipline is operator-enforced and visible in `findings.md` aggregation.

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

**Version**: 1.4.2
**Last amended**: 2026-05-06 (evening, fourth amendment of the day) — added a "Magnitude fungibility for hybrid filters" sub-section to Principle VIII (forward-catalyst-class gate). Empirical basis: Spec 008 Hybrid C bull retrofit + Spec 009-candidate bear-inverted retrofit BOTH produced identical fire patterns across magnitude={0.5, 1.0, 2.0} within fixed window. Codifies the methodology improvement: magnitude is fungible within a hybrid-filter window when the smallest tested magnitude already crosses the underlying threshold. Future retrospectives skip redundant magnitude sweeps in this regime. v1.4.1 → v1.4.2 (PATCH per clarification rule).
**Prior version**: 1.4.1 — appended a "Spec ships its retrospective + verdict" sub-section to Principle VI. Codifies the pattern that today's 22-work-unit research-burst day demonstrated 5 times: spec invocation requires accompanying retrospective markdown in `claudedocs/` documenting the empirical justification + verdict + decision tree. Cost asymmetry (retrospective $0-2 / 1h vs spec+impl ~6-8h) makes "retrospective FIRST, spec SECOND" the dominant strategy. v1.4.0 → v1.4.1 (PATCH per clarification rule).
**Prior version**: 1.4.0 — extended **Principle VIII** with a "Forward-catalyst-class validation gate" sub-section. Empirical basis: Class 3 Opus retrospective DECISIVELY PASSED bull-side (discrim +14.43pp / hit rate 88.9% / net Δα +2.24pp at T=0.60 on n=33 fires); bear-side passed criteria 1+2 with shadow-mode-first condition (discrim +23.10pp / hit rate 72.2% / net Δα +0.30pp). Forward-catalyst signals follow a separate gate (discrim ≥ +5pp PRIMARY + cohort hit rate ≥ 60% + net Δα ≥ +0.5pp OR shadow-mode-first) calibrated to their different statistical properties. Spec 007 ships as the first instance of this filter class.
**Prior version**: 1.3.0 — added **Principle VIII (Retrospective Before Spec for Backward-Looking Price Filters)** after three same-day retrospective failures (spec 004 sector momentum -0.45pp/n=73; spec 006 bear sector-symmetry -0.71pp/n=36; spec 005-candidate bull sector-relative +0.31pp max/n=79). Cost asymmetry: $0/1h retrospective vs ~6-8h spec+impl+tests. Backward-looking price filters cannot DISCRIMINATE cohort losers from similar-pattern winners; the retrospective gate must come FIRST for this filter class. Both criteria (net Δα ≥ +1pp at default + cohort hit rate ≥ 40%) must pass for spec to be written. Three failures in one day codified the lesson.
**Prior version**: 1.2.2 — Principle VII appended Cross-period scope clarification: realized-α claims (not commit-rate claims) must be treated as period-conditional unless validated across multiple periods. Empirical trigger: experiment 008 (same config as 007, Q4 2025 dates instead of Q1 2026) produced OW 21d α = -1.81% vs 007's +3.05%. Bayesian posterior on stable-cross-period-signal hypothesis dropped 0.64 → 0.52. ANALYSIS.md write-ups must state the period composition of any n=N cohort and the cross-period replication status of the claim.
**Prior version**: 1.2.1 — Principle VII appended Replicability-scope clarification: bucket-level (replicable) vs date-level (single observation) evidence. Trigger: 005-vs-007 NVDA non-replication on the same dates.
**Prior version**: 1.2.0 — Principle III restructured from single $30 ceiling to 4-tier ladder (T1 ≤$5 / T2 $5-30 / T3 $30-100 / T4 $100+) reflecting Opus pricing + accumulated re-analysis tooling; added Principle VII (Calibrated Abstention is a Valid Output); sharpened Principle IV with empirical backing.
**Prior version**: 1.1.0 — added Principle VII + sharpened IV (2026-05-03 earlier in the day)
**Prior version**: 1.0.0 — initial adoption 2026-05-01
