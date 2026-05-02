# Hypothesis: mr2-synthesis-instrument

**Experiment ID**: `2026-05-02-003-mr2-synthesis-instrument`
**Created**: 2026-05-02
**Source idea**: MR-2 (from `docs/EXPERIMENT.md`)
**Cost estimate**: $0 (pure code read + analysis on existing pilot data)

## What we're testing

After **WC-12** confirmed the Research Manager's synthesis is the dilution step (and the **WC-12 forward-alpha follow-up** showed that dilution may be defensively *correct* on average), the natural next question is *why* the synthesis dilutes. Three possibilities:

1. **Prompt-induced**: the Research Manager's prompt explicitly instructs the model to hedge.
2. **Schema-induced**: the structured-output `ResearchPlan` schema's field descriptions instruct hedging.
3. **Implicit**: the model defaults to hedging because it can't tell which dates deserve commitment.

If (1) or (2) — the fix is editing strings in `research_manager.py` and/or `schemas.py`.
If (3) — the fix is upstream (better data, better analyst prompts).

## Method

Pure investigative analysis. No new LLM calls, no propagate runs.

1. Read `tradingagents/agents/managers/research_manager.py` and the `ResearchPlan` schema in `tradingagents/agents/schemas.py`. Quote the exact instructions given to the synthesis step.
2. Extract the `investment_plan` text from all 65 pilot JSON state logs.
3. Tally the synthesis-step rating distribution (independent of what the PM eventually output).
4. Count hedge-word frequency across all 65 plans (`but`, `however`, `although`, `caveats`, `balanced`, `both sides`, etc.).
5. Quote one or two representative plans that show the hedging pattern.
6. Identify which of (1)/(2)/(3) the evidence supports.

## Predicted finding

(1) and (2) are the cause. The current prompt and schema both contain language that explicitly equates "two-sided evidence" (which MR-1 confirmed is the norm) with Hold-leaning ratings. The model is following instructions correctly.

If the prediction holds, the fix is editing 2-3 strings of text. No model retraining, no architectural change — just better synthesis-step instructions.

## Success criterion

- [ ] Exact text of the moderation-inducing instructions extracted and quoted
- [ ] Synthesis-step rating distribution computed (compare to PM-step distribution from prior experiments)
- [ ] Hedge-word frequency table across all 65 plans
- [ ] At least one representative plan excerpt that demonstrates the pattern
- [ ] Recommendation: which exact strings need editing, with a proposed replacement

## Notes

- This is a **read-only investigation** — no code changes, no propagate runs, no new data. The next experiment after this would test a redesigned synthesis prompt.
- The pilot data (`~/.tradingagents/logs/`) plus the source code are everything we need.

## Related experiments

- **MR-1** (`experiments/2026-05-02-001-mr1-contradiction/`) — established the bull/bear debate is genuinely two-sided.
- **WC-12** (`experiments/2026-05-02-002-wc12-pm-blind/`) — showed the synthesis is the dilution step + forward-alpha refined: dilution may be defensively correct, fix isn't simple removal.
- **Future MR-3** (post-MR-2) — test a redesigned synthesis prompt that decouples "two-sided debate" from "Hold-leaning rating".
