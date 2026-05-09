# Cross-pollination opportunities review — 2026-05-08

**Trigger**: reasoning_decision rank #7 (0.46 score) executed during the WC-10 v2/v3 in-flight window.

**Why this review now**: WC-10 v1 ALT-A finding (categorical bottleneck confirmed at 3.6× commit ratio) + Constitution v1.5.0 amendment (schema-induced abstention carve-out) **change the relevance ordering** of the existing cross-pollination table in `ROADMAP.md`. Some patterns previously parked become more attractive (those that compress LLM reasoning into structured representations); some become less attractive (those that target Hold-rate reduction without addressing the schema issue).

This doc re-ranks the existing table entries by current empirical relevance + adds new candidate patterns surfaced today + flags 2 entries for partial supersession.

## Re-ranking of existing patterns

Five-tier empirical relevance:
- **L5 — Ship-eligible now**: empirical foundation supports a spec-kit invocation
- **L4 — Pilot-eligible**: design doc + small experiment justified
- **L3 — Worth testing in design**: ROADMAP retains; no immediate spec
- **L2 — Speculative**: keep in table for reference
- **L1 — Superseded or deprioritized**: flag for ROADMAP cleanup

| Pattern | From | Original ROADMAP framing | 2026-05-08 relevance | Tier |
|---|---|---|---|---|
| **Squeak (structured signaling)** | battlecode2026 ratbot6 | Analysts emit `{bullish: 0.7, key_risks: [...]}` instead of 10K-token prose | **NEW relevance from WC-10**: directly tests the same hypothesis (categorical-vs-continuous output) but ONE LEVEL UP — replace ANALYSTS' prose output with structured fields. WC-10 confirmed the PM's bottleneck; this would test whether the analysts' prose-bottleneck is similar. Per-analyst $0.05-0.10 cost savings × 4 analysts × 100 propagates = $20-40 saved per experiment. Plus easier featurizer extraction. | **L4** |
| **Unified value function architecture** | battlecode2026 ratbot6 | Replace prose analysts with numeric feature emitters | Sister pattern to Squeak above. Together they form a "structured-output-throughout" architectural variant. Worth a Phase E spec scaffold even pre-empirical-test. | **L3** |
| **Self-improvement (monitor → diagnose → execute → learn)** | mcp-reasoning | Auto-detect calibration drift, trigger re-analysis | **WC-10 caveat strengthens this**: WC-10 v3 specifically tests whether bear-regime causes WC-10 to mis-fire. A self-improvement system could AUTOMATICALLY detect such mis-fires post-hoc and trigger a re-spec. Already partially implemented as `scripts/memory_log_integrity_check.py` (PR #55). Could extend to "auto-detect when WC-10 commits underperform 5-tier baseline on a ticker × period cohort." | **L4** |
| **15+ reasoning modes** | mcp-reasoning | Phase C operationalization items | Already heavily used in this project's workflow (reasoning_decision drove 8+ of today's PRs). Cross-pollination is operationally COMPLETE — this is the canonical reference but no further porting needed. | **L5** (already-pollinated) |
| **Knowledge digestion + antibodies** | agent-harness-v2 | Periodic synthesis of UW failure modes from accumulated state logs | **WC-10 strengthens this**: WC-10 reframed mode collapse as two-mechanism. A knowledge-digestion pass could AUTOMATICALLY tag historical Hold commits as either "genuine ambiguity" or "schema-induced collapse" by replaying through WC-10 mode. Operates on saved data; $0 LLM cost. | **L4** |
| **Event sourcing** | agent-harness-v2 | Replace per-experiment CSV + state-log JSON with single event log | Spec 002 signal-lifecycle pipeline (Phases 0-2.5) partially shipped this idea via `tradingagents/signals/cache.py`. Unification of the three persistence systems (memory log + checkpoint + paper-trade events) would be a Phase E architectural spec. Significant scope; not blocked but not high-leverage. | **L3** |
| **Structural enforcement / gates** | agent-harness-v2 | Pre_pm gate that checks bull/bear evidence balance | **NEW interpretation post-WC-10**: instead of gating PM commits, structurally enforce SCHEMA-AWARENESS in the spec-writing process — every new filter spec MUST declare which sub-population (genuine balance vs schema collapse) its mechanism targets per Constitution v1.5.0 operational test. This is metadata-enforcement, not runtime-enforcement. Achievable as a one-script lint in `scripts/spec_audit.py`. | **L3** |
| **Sentinel pattern** | ladybird | Out-of-process enforcement plane | Operational complexity high; benefit unclear. The current in-process filter chain works fine empirically. Lower priority than other patterns. | **L2** |
| **Value function over assigned roles** | battlecode2026 ratbot6 | Each analyst has explicit value function for "good evidence" | Sister to Squeak; would naturally land alongside it in a Phase E spec. Standalone application is harder. | **L2** |
| **Self-removal after idle threshold** | battlecode2026 ratbot6 | Skip analyst if report below content threshold | **Aligns with Constitution VII Calibrated Abstention** — an analyst that emits empty evidence is the analyst-stage equivalent of PM Hold. Could ship as a defensive guard with empirical justification (skip downstream debate when analyst report < N chars). Low risk; small wall-clock + cost win. | **L3** |
| **Pre-computed decision-rule shortcuts** | battlecode2026 ratbot6 | Avoid LLM call when rule fires (e.g. "earnings beat + uptrend → default OW") | **Tension with WC-10 finding**: WC-10 showed the schema constrains expressivity; pre-computed rules would constrain it FURTHER. Risk of over-fitting to recent patterns. Lower relevance now. | **L1** (deprioritized post-WC-10) |
| **Bytecode budget tracking** | battlecode2026 ratbot6 | Per-analyst token-spend tracker | Operationally useful; not architecturally novel. Could be a small claudedocs analysis showing per-analyst cost per propagate. Useful tool, not a strategic move. | **L2** |
| **Explicit state machine** | battlecode2026 ratbot6 | Make `state.debate_phase` explicit instead of regex-detecting | Engineering hygiene. Worth doing eventually; not strategic. | **L2** |
| **abliteration for specialization** | bruno-swarm | Specialize each analyst via abliteration | Significant infrastructure investment for unclear benefit. Lower relevance vs Squeak structured-signaling which addresses similar question more cheaply. | **L1** (deprioritized) |
| **Branch-thinking / logic-thinking structured tools** | branch-thinking | Alternative synthesis substrates | Already exercised via mcp-reasoning. No additional porting needed. | **L5** (already-pollinated) |

## New candidate patterns surfaced 2026-05-08

| Pattern | From | Application | Tier |
|---|---|---|---|
| **Conditional-branch spec drafting** | (this project, today) | Pre-write spec.md with N verdict-conditional branches (Spec 009 pattern); when verdicts land, branch selection is deterministic. Pattern is now codified in Spec 009 + Spec 011 (which itself is a methodology spec). Could be extracted as a generic "conditional-branch spec" template in `.specify/templates/`. | **L4** |
| **Pre-scaffolding ANALYSIS templates** | (this project, today) | When experiments are in flight, write ANALYSIS_TEMPLATE.md in the experiment dir with `<TBD>` placeholders for all metric verdicts; data-landing PR is plug-in-the-numbers (PR #135 demonstrated). Could be extracted as a `scripts/new_experiment.py --with-analysis-template` flag. | **L4** |

## Recommendations

### Highest-leverage 3 patterns to act on next

1. **Squeak (L4)** — structured analyst output. WC-10's bottleneck-confirmed verdict makes this directly testable: replace one analyst's prose with a structured emitter, measure rating distribution shift + cost delta. Pilot at $5-10. Direct empirical test of whether the analyst-stage prose has its own bottleneck.

2. **Knowledge digestion via WC-10 replay (L4)** — auto-tag Hold commits in historical state logs as genuine vs schema-induced. $0 LLM (replays saved scalar data via `bin_scalar_to_tier()` thresholds). Output: a `claudedocs/historical-hold-attribution-2026-05-XX.md` showing what fraction of past Holds were schema-artifacts.

3. **Self-improvement: WC-10 underperformance auto-detect (L4)** — extend `scripts/memory_log_integrity_check.py` to flag any WC-10 commit that produces realized α < 5-tier baseline on the same date. Closes the loop between v3 verdict-conditional caveat (Constitution v1.5.0) and runtime monitoring.

### Specs to flag for ROADMAP cleanup

- **Pre-computed decision-rule shortcuts (L1)**: deprioritize via ROADMAP table comment. WC-10 finding shows schema constraints are already too tight, not too loose.
- **abliteration for specialization (L1)**: deprioritize. Squeak is cheaper and tests an adjacent hypothesis.

### Patterns ready to extract as project tooling

- **Conditional-branch spec template** (L4): Spec 009 + Spec 011 demonstrate the pattern works. Could ship a `.specify/templates/spec-template-conditional.md` for future verdict-conditional specs.
- **ANALYSIS template scaffolding flag** (L4): extend `scripts/new_experiment.py` with `--with-analysis-template` to auto-generate the template alongside HYPOTHESIS.md + PARAMS.json.

## Cost summary

This review: **$0** (analysis only).

If all 3 highest-leverage recommendations land:
- Squeak pilot: $5-10
- Knowledge digestion: $0
- Self-improvement extension: $0

Total: **$5-10** for 3 cross-pollination spec scaffolds + 1 production-ready analysis tool.

## Cross-references

- `ROADMAP.md` Cross-pollination opportunities table (existing, will likely be updated in a follow-up PR)
- Constitution v1.5.0 Principle VII sub-section (anchors the Knowledge Digestion + Self-Improvement reframings)
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (anchors the Squeak relevance)
- Memory `reference_pm_hold_with_bullish_prose.md` (anchors the historical-hold-attribution candidate)
