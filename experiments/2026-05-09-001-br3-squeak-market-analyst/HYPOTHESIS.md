# BR-3 Squeak — Market Analyst Structured-Output Pilot HYPOTHESIS

**Experiment ID**: `2026-05-09-001-br3-squeak-market-analyst`
**Source idea**: BR-3 (per `docs/EXPERIMENT.md` Tier 3 — flagged L4 in `claudedocs/cross-pollination-review-2026-05-08.md` PR #143)
**Date**: 2026-05-09 (scaffold; launch deferred pending operator decision)
**Cost estimate**: ~$8.00
**Cost tier**: T2 (standard, $5 – $30 per Constitution III)

> **STATUS**: SCAFFOLD ONLY — HYPOTHESIS + PARAMS drafted; experiment NOT yet launched. Operator decides whether to invoke. Cost when launched: ~$8 (T2).

## Question

WC-10 v1 (PR #130) confirmed the **PM-stage** categorical schema is a bottleneck — continuous-scalar mode commits 3.6× more often than 5-tier on the same dates. Constitution VII v1.5.0 carved out the schema-induced-collapse case.

BR-3 tests whether the **analyst-stage** has an analogous prose-to-structured bottleneck. If the market analyst's free-form prose output is converted to structured fields (`{bullish: 0.7, key_risks: [...], confidence: 0.6, citations: [...]}`), does the framework's downstream synthesis quality CHANGE? If yes (in either direction), analyst-stage prose is itself a load-bearing or harmful intermediate representation. If no, the prose is just a decorative channel and structured output is a pure cost win.

This is the **sister hypothesis** to WC-10 — same mechanism (prose vs structured) but applied at a different stage of the pipeline.

## Three predictions

| Prediction | What it means | Empirical signature |
|---|---|---|
| **NULL** (analyst-stage robust to format) | Synthesis quality + rating distribution + realized α stable across prose-vs-structured market analyst formats. The prose is decorative; structured saves tokens with no signal change. | Per-format rating distribution within ±10pp; mean rating-attributed α within ±50bps |
| **ALT-A (prose carries signal)** | Structured output LOSES signal that prose was carrying — synthesis quality degrades, rating distribution shifts, realized α drops. The prose's free-form structure was load-bearing. | Per-format mean rating-attributed α drops by ≥1pp under structured; rating distribution shifts ≥20pp toward Hold (synthesis can't extract signal from structured fields) |
| **ALT-B (structured surfaces signal)** | Structured output reveals signal the prose was burying. Synthesis quality improves; rating distribution becomes more decisive; realized α improves. | Per-format mean rating-attributed α improves by ≥1pp under structured; rating distribution shifts ≥20pp toward commits (Buy/OW/UW/Sell) |

## Test grid

5 dates × 2 tickers × 2 formats = **20 propagates**.

- **Tickers**: NVDA + AAPL (matches v1 cohort + WC-10 baseline for direct cross-experiment comparison)
- **Dates** (5 weekly Q1 2026 Fridays): 2026-01-30, 2026-02-13, 2026-02-27, 2026-03-13, 2026-03-27 (matches WC-10 v2 dates for additional cross-experiment alignment)
- **Formats**:
  - `prose` (default; current production market analyst output)
  - `structured` (replace prose with structured emitter — see Implementation below)

## Cost estimate

20 propagates × ~$0.40 = **~$8 LLM**. Constitution III T2 ($5-$30; standard exploratory).

## Headline metrics

1. **(Primary) Mean rating-attributed 21d α delta**: `mean_α(structured) - mean_α(prose)`. Sign + magnitude → NULL/ALT-A/ALT-B verdict.
2. **(Secondary) Rating distribution shift**: per-format counts of {Buy/OW/Hold/UW/Sell}. Test for ≥20pp shift toward commits or Hold.
3. **(Tertiary) Token cost delta**: per-propagate average input + output tokens for the market analyst. Structured should be ≥30% cheaper; quantify the cost savings.
4. **(Quaternary) PM rationale length**: does the PM produce shorter rationale when fed structured market analyst output? Tests whether prose volume from analysts inflates PM verbosity.

## Falsification verdict

Determined post-run; documented in `ANALYSIS.md` (template scaffolded via `--with-analysis-template` from PR #150). Possible verdicts:

- **NULL** — structured output is pure cost win; consider extending to other analysts (news, fundamentals)
- **ALT-A** — prose is load-bearing; do NOT structurize; rest of project should treat prose as architecturally important
- **ALT-B** — structured surfaces signal; consider full structured-output-throughout architecture (Phase E variant per ROADMAP)
- **MIXED / INCONCLUSIVE at n=20** — re-run at n=40 if any directional pattern

## Implementation approach (operator notes when launching)

The market analyst currently emits free-form prose via `tradingagents/agents/analysts/market_analyst.py`. Two options:

### Option A: Forked analyst with structured output schema

Create `tradingagents/agents/analysts/market_analyst_structured.py` that:
1. Uses the same tools (technical indicators, OHLCV)
2. Binds `llm.with_structured_output(MarketAnalystSquared)` — new Pydantic schema
3. Writes structured output AND a derived markdown synthesis to `state["market_report"]` so downstream consumers see something

Pydantic schema sketch:
```python
class MarketAnalystSquared(BaseModel):
    bullish_score: float = Field(ge=-1.0, le=+1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    key_drivers: list[str] = Field(max_items=5)
    key_risks: list[str] = Field(max_items=5)
    citations: list[str] = Field(default_factory=list)  # ticker symbols / event dates
```

Pros: clean separation; doesn't disturb existing prose analyst.
Cons: requires new file + test coverage.

### Option B: Config flag `market_analyst_format: "prose" | "structured"`

Add a config key that switches the existing `market_analyst.py` between modes. Smaller code surface but mixes two paths in one file.

**Recommendation**: Option A. Cleaner separation matches the project's "don't mix two modes in one file" pattern (per Spec X-1 + Spec 007 architecture). Plus a forked module is easy to delete if BR-3 returns NULL/ALT-A.

## Constitution adherence

- ✅ I (Save Everything): per-propagate state log + this HYPOTHESIS + PARAMS + (when launched) results.csv + ANALYSIS.md (template scaffolded)
- ✅ II (One Experiment Per Change): single intervention (market analyst format). News + fundamentals analysts unchanged. Bull/bear debate unchanged. PM unchanged.
- ✅ III (Stay Cheap): T2 ($5-$30) at $8
- ✅ IV (No Production Claims): NULL is valid; ALT-A would be a cautionary finding; ALT-B would unblock Phase E architectural variant
- ✅ VI (Spec Before Structural Change): Implementation Option A is a NEW analyst module; per Constitution VI a small module addition isn't structural enough to require spec-kit (analogous to A3 momentum filter precedent — shipped as utility module without spec). If launched, document in ANALYSIS.md whether spec-kit invocation is warranted for follow-up extension to other analysts.
- ✅ VII (Calibrated Abstention v1.5.1): orthogonal — operates upstream of PM. The structured market_report changes the INPUT to PM, not PM's output schema.

## Cross-references

- `docs/EXPERIMENT.md` BR-3 (Tier 3 still-open as of 2026-05-08)
- `claudedocs/cross-pollination-review-2026-05-08.md` (PR #143) — flagged as L4 top recommendation
- `claudedocs/experiment-md-tier-2-3-review-2026-05-08.md` (PR #145) — top-3 candidate
- WC-10 v1 ANALYSIS.md (PR #130) — sister hypothesis at PM-stage
- Constitution v1.5.1 Principle VII sub-section — frames the prose-vs-structured bottleneck question
- ROADMAP.md Phase E architectural variants section — BR-3 + BR-1 + BR-2 are the structured-output candidates

## Operational note

This is a SCAFFOLD. Launching requires:

1. Operator authorization (~$8 cost is T2; in-scope per default tier)
2. Implementation Option A: ~120 LOC for the new analyst module + 8-10 unit tests
3. Background task launch + monitor armed (mirror v3/v2 pattern)
4. ANALYSIS.md write-up using the pre-scaffolded template

Estimated wall-clock: 20 propagates × ~9 min = ~3 hours.

## Sister scaffolds (BR family)

If BR-3 returns ALT-B (structured surfaces signal), follow-up experiments worth scaffolding:

- **BR-3 v2**: extend to news + fundamentals analysts (same structured schema shape, different domain)
- **BR-1**: value-function alternative — single model emits `{Buy: 0.1, OW: 0.3, ...}` instead of debate (revisits Tier 2 idea per EXPERIMENT.md review)
- **WC-10 v4 + BR-3 combined**: continuous-scalar PM + structured analysts — tests whether the bottlenecks COMPOUND
