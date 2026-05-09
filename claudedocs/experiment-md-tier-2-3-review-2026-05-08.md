# EXPERIMENT.md Tier 2/3 backlog review — 2026-05-08

**Trigger**: reasoning_decision rank #9 (0.36 score). Research backlog grooming.

**Context**: `docs/EXPERIMENT.md` was the original brainstorm dated 2026-05-01 with ~50 ideas tagged by source project (agent-harness-v2 / ladybird / battlecode2026 / bruno-swarm / mcp-reasoning + wild cards). CLAUDE.md notes "Most Tier 1 ideas now superseded by completed experiments; Tier 2/3 still untouched."

This review:
1. Marks each Tier 1/2/3 idea as DONE / IN-FLIGHT / SUPERSEDED / DEPRIORITIZED / STILL-OPEN
2. Re-ranks STILL-OPEN ideas by post-WC-10 empirical relevance
3. Recommends top 3 candidates for next ~$5-30 experiment slot

## Tier 1 status (4 ideas)

| ID | Idea | Status | Evidence |
|---|---|---|---|
| **MR-1** | `reasoning_contradiction` on bull/bear pairs | **DONE** | experiment 001 (`experiments/2026-05-02-001-mr1-contradiction/`) |
| **WC-12** | PM blind to debate | **DONE** | experiment 002 + variants |
| **EH-2** | Rating distribution gate | **DONE** | shipped as Spec 003 contrarian gate (per-ticker IC anti-prediction; default-on @ 80%) |
| **WC-11** | Order randomization | **STILL-OPEN** | not run; lower priority since 005-vs-007 finding showed run-to-run variance is real but bucket-level claims replicate (Constitution VII Replicability-scope sub-section captures this) |

**Tier 1 net**: 3 of 4 done; WC-11 (order randomization) remains as $10 quick win.

## Tier 2 status (4 ideas)

| ID | Idea | Status | Evidence |
|---|---|---|---|
| **BR-1** | Value-function alternative — single model emits `{Buy: 0.1, ...}` | **PARTIALLY SUPERSEDED** | Single-call baselines (experiments 003, 004) tested no-debate single-call architecture. BR-1's distinct contribution would be the SCORING vector across ALL 5 ratings (not just argmax). **Newly relevant post-WC-10**: WC-10 confirmed scalar can carry conviction; BR-1 extends to per-rating probability vector. |
| **WC-10** | Continuous scalar rating | **DONE** | v1 pilot ANALYSIS shipped 2026-05-08 (PR #130); SC-007 ALT-A confirmed. v2 + v3 in flight. |
| **WC-2** | Multi-temporal debate (5d/30d/90d/1yr lookbacks) | **STILL-OPEN** | not run. **Newly relevant post-WC-10**: WC-10 was single-horizon (21d analysis); multi-temporal could surface whether the 5d / 21d / 90d realized α structure is itself a horizon-specific schema artifact vs robust signal. |
| **MR-3** | `reasoning_decision` weighted-criteria scoring instead of free-text PM | **DONE** | experiment `2026-05-02-004-mr3-synthesis-v2/`; shipped as `research_manager_prompt_variant: "v2"` config option |

**Tier 2 net**: 2 done, 1 partially superseded, 1 still-open. WC-2 (multi-temporal) is the live Tier 2 candidate.

## Tier 3 status (4 ideas)

| ID | Idea | Status | Evidence |
|---|---|---|---|
| **EH-1** | Hash-chained SQLite event log replacing JSON-per-run | **PARTIALLY SHIPPED** | Spec 002 signal-lifecycle pipeline (`tradingagents/signals/cache.py`) provides per-signal-call cache + Phase D evaluation. Full unification of memory + checkpoint + paper-trade events into one event log is a Phase E architectural spec (deferred). |
| **BR-3** | Squeak — structured signaling instead of natural-language debate | **STILL-OPEN** | flagged as **L4 (top recommendation)** in `claudedocs/cross-pollination-review-2026-05-08.md`. Direct test of analyst-stage prose bottleneck (sister hypothesis to WC-10's PM-stage finding). $5-10 pilot. |
| **WC-4** | 5 debate topologies in parallel | **STILL-OPEN** | not run; expensive ($50). Architectural variant of WC-12. Lower leverage post-WC-10 since the WC-10 finding suggests OUTPUT SCHEMA is the bottleneck, not debate topology. **Deprioritized.** |
| **BS-2** | Local Ollama for high-volume agents | **STILL-OPEN** | not run; infra-heavy. Cost-savings story. Independent of WC-10 finding. Worth doing for the cost story but unrelated to research priorities. |

**Tier 3 net**: 1 partially shipped, 3 still-open. BR-3 (Squeak) is the highest-leverage; WC-4 deprioritized post-WC-10.

## Backlog re-ranking — new candidates surfaced post-WC-10

From the broader brainstorm, some BACKLOG ideas become more interesting given WC-10's finding that the categorical bottleneck is real:

| ID | Idea | Why newly interesting | Cost |
|---|---|---|---|
| **WC-3** | Stochastic ensemble (N runs at different temperatures, vote) | WC-10 v1 surfaced the run-to-run variance question (rerun-variance still listed as an open RESEARCH_FINDINGS question). Stochastic ensemble would directly measure the noise floor; if noise dominates, WC-10's signal claims weaken. | $20-30 |
| **BR-4** | Charge mode — short-circuit debate when analyst returns >X SD signal | Analogous to WC-10's "skip the schema bottleneck on high-conviction reads." Could test whether high-conviction analyst signals would benefit from bypassing the synthesis stage. | $15 |
| **WC-15** | Adversarial market regime — run during March 2020 / Aug 2022 volatility | WC-10 v3 tests Q4 2025 NVDA bear regime; broader market-stress regime testing would generalize the regime-conditional claim. | $20 |
| **EH-4** | Knowledge digestion pipeline (DEDUPE / CANDIDATE / REVIEW / COMMIT) | Sister to the cross-pollination L4 "Knowledge digestion + antibodies" pattern. Both are $0 (operate on saved data). | $0 |
| **MR-4** | `reasoning_tree` over rating decisions | WC-10 surfaces the question of how the PM commits to a number. Tree-search exploration could surface alternative ratings the PM considered but rejected. | $15 |

## Top 3 recommendations for next experiment slot

Ranked by (leverage × empirical foundation × cost-efficiency):

### 1. BR-3 Squeak — analyst-stage structured-output pilot ($5-10)

**Why now**: WC-10 confirmed PM-stage bottleneck. BR-3 directly tests whether analysts have an analogous prose-bottleneck. If yes, we have a second architectural lever beyond WC-10. If no, we know the bottleneck is PM-specific.

**Design** (rough):
- Pick 1 analyst (market analyst is simplest)
- Replace prose output with structured emitter: `{bullish: 0.7, key_risks: [...], confidence: 0.6, citations: [...]}`
- Run 10 propagates with structured market-analyst alongside existing 3 prose analysts
- Compare PM rating distribution + realized α vs baseline
- Cost: ~$0.40 × 10 = $4 (since structured analyst saves tokens on the changed analyst)

**Cross-references**: `claudedocs/cross-pollination-review-2026-05-08.md` L4-tier "Squeak" entry

### 2. WC-2 Multi-temporal debate ($30, T2-boundary)

**Why now**: WC-10 was single-horizon (21d). Multi-temporal would surface whether the framework's signal structure is itself horizon-conditional. If the same framework produces different ratings at 5d/30d/90d/1yr lookbacks, that's a different mode-collapse mechanism than the schema bottleneck WC-10 found.

**Design**:
- Pick 5 dates × 1 ticker (NVDA)
- Run 4× per propagate with `lookback ∈ {5d, 30d, 90d, 1yr}` debate-context configs
- 5 dates × 4 lookbacks = 20 propagates × $0.40 = $8 (overshoots if Opus or longer debates)
- Compare rating distributions + realized α at each lookback's natural horizon

**Sister to**: WC-3 stochastic ensemble (could be combined for $40-50 to test BOTH dimensions simultaneously)

### 3. EH-4 Knowledge digestion ($0)

**Why now**: WC-10 created the empirical basis for distinguishing genuine vs schema-induced Hold commits. EH-4's "DEDUPE / CANDIDATE / REVIEW / COMMIT" pipeline applied to historical state logs would auto-tag each Hold with attribution. Same idea as the cross-pollination L4 "Knowledge digestion via WC-10 replay" — overlap intentional; both can ship as one analysis script.

**Design**:
- Walk all 254 state logs accumulated 2026-05-04 to 2026-05-07
- For each Hold rating, replay through `bin_scalar_to_tier()` with the analyst-prose features used to generate it (no new LLM)
- Tag as "would-commit-under-WC-10" (schema-induced collapse) vs "Hold-stays-Hold" (genuine)
- Output: `claudedocs/historical-hold-attribution-2026-05-XX.md`

**Cost**: $0 LLM. ~3h work.

## Tier reorganization recommendation

Update `docs/EXPERIMENT.md` Tier 1/2/3 sections to reflect status:

- **Tier 1**: 3 of 4 items now superseded; mark them ✓ DONE inline
- **Tier 2**: WC-10 ✓ DONE; BR-1 PARTIALLY-SUPERSEDED; MR-3 ✓ DONE; WC-2 the only live Tier 2
- **Tier 3**: EH-1 PARTIALLY SHIPPED via Spec 002; BR-3 promoted to TOP RECOMMENDATION (L4 in cross-pollination); WC-4 deprioritized
- **New BACKLOG-promoted**: WC-3 + BR-4 + WC-15 + EH-4 + MR-4 (per re-ranking above)

Either:
- (a) inline edit `docs/EXPERIMENT.md` with status tags (~30 min)
- (b) leave EXPERIMENT.md as historical brainstorm + reference this review doc from ROADMAP

Recommend (b) — EXPERIMENT.md is preserved as the original brainstorm artifact (Constitution Principle I "Save Everything"); this review doc is the current operational ranking.

## Cost summary

This review: **$0**.

Top 3 recommendations total: **$5-10 (BR-3) + $0 (EH-4) + $30 (WC-2) = $35-40 if all three ship**. Realistic next slot: **BR-3 first** ($5-10, highest leverage post-WC-10).

## Cross-references

- `docs/EXPERIMENT.md` (original brainstorm, preserved as artifact)
- `claudedocs/cross-pollination-review-2026-05-08.md` (BR-3 L4 entry; EH-4 overlap)
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (anchors the post-WC-10 re-ranking)
- Constitution v1.5.0 Principle VII (frame for which experiments now have empirical support)
- `RESEARCH_FINDINGS.md` Open Questions table (overlapping but distinct surface — these candidates address NEW questions, not existing ones)
