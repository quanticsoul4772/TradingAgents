# WC-10 v2 ticker expansion — ANALYSIS

**Experiment ID**: `2026-05-08-002-wc-10-v2-ticker-expansion`
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/`
**Run date**: 2026-05-08 (kickoff) → 2026-05-09 (completion)
**Total LLM cost**: ~$32 (80 propagates × ~$0.40)
**Predecessors**:
- v1 ANALYSIS: `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (n=20 paired)
- v3 ANALYSIS: `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS.md` (PARTIAL ALT-A)
- Pre-scaffolded landing playbook: `claudedocs/v2-landing-pr-series-bundle-template-2026-05-08.md`
- Triple-pilot landing coordination: PR #172

## Headline verdict

**SC-005(b) at n=100 (combined v1+v2): NULL.** Pearson r = **+0.0918**, Spearman ρ = **+0.0410** — both BELOW the ±0.197 critical value at n=100/p=0.05. The signed-scalar magnitude carries NO information beyond what the binned-tier captures.

**SC-007 ALT-A generalization: PARTIAL — 5 of 8 tickers** met the ≥80% commit-rate threshold (NVDA 100%, AMZN 100%, MSFT 90%, AAPL 80%, XOM 80%). Three tickers retained Hold-collapse under continuous-scalar mode (JPM 70%, GOOG 60%, **JNJ 10%**) — these fall back into Constitution VII's original "genuine ambiguity" sub-population.

**SC-005(c) per-bucket realized α generalization**: bullish-side amplification REPLICATES at expanded n. Buy n=20 (combined) mean α = +2.93%, 80% hit; OW n=32 mean α = +2.10%, 53% hit. Bearish-side anti-calibration also REPLICATES: UW n=25 mean α = +1.30% (wrong direction), 32% hit.

**Operational verdict**: per the pre-scaffolded "Branch C" playbook → **bin-then-output pattern** (continuous internal, 5-tier external) — captures the bullish-amplification ergonomic gain without the false-precision claim that scalar magnitude is interpretable beyond the bin.

## SC-005(b) — signed-rating × 21d-α correlation (PRIMARY)

Pooled across all 100 WC-10 propagates (20 from v1 + 80 from v2):

| Statistic | Value | Critical (p=0.05) | Verdict |
|---|---:|---|---|
| Pearson r | **+0.0918** | ±0.197 | **NS (NULL)** |
| Spearman ρ | **+0.0410** | ±0.197 | **NS (NULL)** |

**v2 alone (n=80)**: Pearson r = +0.0926, Spearman ρ = +0.0462 (effectively identical to combined; v1's n=20 contribution is negligible).

**Per-ticker correlation** (within-ticker IC over n=10 each):

| Ticker | n | Pearson r | Mean WC-10 rating | Mean 21d α |
|---|---:|---:|---:|---:|
| NVDA | 10 | 0.0000* | +0.620 | +2.54% |
| AAPL | 10 | -0.3041 | -0.092 | -0.53% |
| MSFT | 10 | -0.2460 | +0.243 | -0.14% |
| GOOG | 10 | +0.0857 | +0.339 | +3.04% |
| AMZN | 10 | -0.3157 | +0.343 | +7.72% |
| JPM | 10 | -0.6656 | +0.201 | -0.75% |
| JNJ | 10 | -0.1787 | +0.067 | -2.88% |
| XOM | 10 | +0.2659 | -0.310 | +0.02% |

*NVDA std=0.000: all 10 NVDA propagates emitted exactly +0.6200 — the LLM degenerate-collapsed to a single scalar value across all 10 dates. This is itself a noteworthy finding: continuous-scalar mode does NOT prevent intra-ticker mode collapse to a single value when the LLM's analyst+debate synthesis converges deterministically. NVDA was the Q1 2026 bull-rally ticker; the prompt+inputs apparently produced "Buy at +0.62" as a ROBUST attractor across 10 distinct dates.

**JPM has a strongly NEGATIVE within-ticker IC (-0.6656)** — higher rating predicts LOWER alpha. Anti-signal at within-ticker resolution. AAPL + MSFT + AMZN also show negative within-ticker correlation. Only XOM shows a positive within-ticker IC (+0.2659).

## SC-007 ALT-A generalization across tickers (SECONDARY)

Per-ticker fraction of `|rating| > 0.2` (committed):

| Ticker | n | Committed | % | Buy | OW | Hold | UW | Sell |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NVDA | 10 | 10 | 100% | 10 | 0 | 0 | 0 | 0 |
| AMZN | 10 | 10 | 100% | 1 | 8 | 0 | 1 | 0 |
| MSFT | 10 | 9 | 90% | 2 | 5 | 1 | 2 | 0 |
| AAPL | 10 | 8 | 80% | 0 | 2 | 2 | 6 | 0 |
| XOM | 10 | 8 | 80% | 0 | 0 | 2 | 8 | 0 |
| JPM | 10 | 7 | 70% | 0 | 6 | 3 | 1 | 0 |
| GOOG | 10 | 6 | 60% | 1 | 5 | 4 | 0 | 0 |
| **JNJ** | **10** | **1** | **10%** | 0 | 0 | 9 | 1 | 0 |
| **Total** | **80** | **59** | **74%** | 14 | 26 | 21 | 19 | 0 |

ALT-A predicted ≥80% commit rate per ticker matching v1's NVDA pattern. **5 of 8 tickers cross the threshold**; 3 tickers do not. The cleanest counter-finding is **JNJ at 10% commit rate** — defensive-sector low-volatility ticker that retains Hold-default even under continuous-scalar output. JNJ falls into Constitution VII's original "genuine ambiguity" sub-population.

GOOG and JPM (60% and 70%) sit in an intermediate band — partial ALT-A.

## SC-005(c) — per-bucket realized α generalization (TERTIARY)

Combined v1 + v2 per-binned-tier:

| Bucket | v1 n | v1 mean α | v2 n | v2 mean α | Combined n | Combined mean α | Combined hit |
|---|---:|---:|---:|---:|---:|---:|---:|
| Buy | 6 | +4.67% | 14 | +2.19% | **20** | **+2.93%** | **80%** |
| Overweight | 6 | +2.34% | 26 | +2.05% | **32** | **+2.10%** | **53%** |
| Hold | 2 | +4.29% | 21 | -0.23% | **23** | +0.16% | — |
| Underweight | 6 | +3.56% | 19 | +0.59% | **25** | +1.30% | **32%** |
| Sell | 0 | — | 0 | — | 0 | — | — |

**Bullish-side amplification GENERALIZES**: Buy bucket combined α +2.93% at 80% hit (n=20) is the strongest bullish signal in the WC-10 corpus. OW bucket combined α +2.10% at 53% hit (n=32) is consistent with the broader corpus's 21d OW signal (RESEARCH_FINDINGS reports OW α +1.23% at 61% hit across n=71 cross-experiment).

**Bearish-side anti-calibration GENERALIZES**: UW bucket combined α +1.30% (positive when bearish call would predict negative) at 32% hit (only 32% of UW commits had α<0). The v1 finding that UW commits were anti-calibrated on AAPL extends to most of the v2 universe — except XOM (UW n=8 mean -1.45%, calibrated).

**XOM is the bear-correct counter-case**: 8 of 10 XOM propagates emitted UW with mean α -1.45% — the bearish-side-amplification mechanism IS calibrated when the underlying ticker is in a bear regime. This matches the broader project finding that bear commits are regime-asymmetric, not uniformly anti-calibrated.

## Per-ticker × binned-tier breakdown (v2 only, for cohort attribution)

| Ticker | Buy | OW | Hold | UW | Pattern |
|---|---|---|---|---|---|
| NVDA | n=10 / +2.54% | — | — | — | Bullish-degenerate (single +0.62 attractor); all calls correct direction |
| AMZN | n=1 / -11.09% | n=8 / +9.81% | — | n=1 / +9.86% | Strong bullish (OW correct); UW commit was direction-wrong |
| GOOG | n=1 / +19.26% | n=5 / -0.93% | n=4 / +3.95% | — | Bullish-amplified but OW commits flat; Hold dates were bullish (counterfactual) |
| MSFT | n=2 / -1.44% | n=5 / -0.68% | n=1 / +1.10% | n=2 / +1.91% | Bullish-amplified but flat; UW direction-wrong |
| AAPL | — | n=2 / -1.75% | n=2 / -0.38% | n=6 / -0.17% | Mostly bearish; UW slightly correct |
| JPM | — | n=6 / -2.28% | n=3 / +0.43% | n=1 / +4.95% | Bullish-amplified but ANTI-calibrated; UW direction-wrong |
| XOM | — | — | n=2 / +5.88% | n=8 / -1.45% | Bearish-amplified, CORRECT direction (only bear-correct case) |
| JNJ | — | — | n=9 / -3.78% | n=1 / +5.23% | Genuine Hold-default; the 1 UW was direction-wrong |

## Combined v1+v2 full breakdown (n=100)

| Metric | v1 (n=20) | v2 (n=80) | Combined (n=100) |
|---|---:|---:|---:|
| Commit rate (`\|rating\|>0.2`) | 90% | 74% | **77%** |
| Mean rating | +0.249 | +0.176 | +0.190 |
| Std rating | 0.398 | 0.357 | 0.368 |
| Mean 21d α | +3.55% | +1.13% | +1.62% |
| Pearson r (rating × α) | +0.065 | +0.093 | **+0.0918** |
| Spearman ρ | +0.009 | +0.046 | **+0.0410** |

## Cohort + period notes

v2 dates span Q1 2026 (2026-01-30 → 2026-04-03) — same window as project's Q1 2026 cohort that produced the +1.99% n=50 OW α finding. The bullish bucket means (Buy +2.19%, OW +2.05%) are CONSISTENT with the broader Q1 2026 framework signal. v1 dates (April 2026, NVDA + AAPL only) sat at the boundary of the Q1/Q2 transition.

Combined cohort therefore primarily samples the Q1 2026 broad-Tech-rally regime. Per Constitution VII v1.5.0 cross-period scope clarification, the realized-α finding is **period-conditional**; generalization to Q4 2025 + Q3 2025 is partially addressed by v3 (which produced PARTIAL ALT-A on Q4 2025 NVDA with α delta within ±100bps NULL region).

## Constitution v1.5.0/v1.5.1 implication update

v1.5.0's "schema-induced abstention" carve-out generalizes to **5 of 8** tickers in v2's broader Tech + Financials + Defensive + Energy mix. Three tickers retain genuine Hold-default under continuous-scalar mode (JNJ + GOOG + JPM), validating that v1.5.0 is correctly carved out as a SUB-POPULATION rather than a wholesale replacement of VII original.

v1.5.1's empirical magnitude bound on |α delta| < 1pp is consistent with combined-cohort data: the schema swap generates LARGE distribution shift (commit rate 25% → 77% at the 5-tier vs WC-10 comparison) but α delta on that shift is within ±2pp — schema effect is bigger than realized-signal effect.

**No new amendment required** for v2. The verdict (SC-005(b) NULL) is consistent with v1.5.1's framing that schema-induced collapse is a real but bounded phenomenon. The "structural change reduces Hold rate" justification still applies; v2 confirms ALT-A on majority of ticker base.

## SC-001 / SC-002 / SC-003 / SC-004 (instrumentation gates)

All gates passed by construction (v2 reused v1's instrumentation):
- SC-001: 80/80 propagates produced numeric ratings in [-1, +1]; signal_processor extracted scalar correctly across all 80 rows
- SC-002: bin_scalar_to_tier() applied deterministically to all 80 rows (binned_tier column populated)
- SC-003: default-off integrity preserved (other experiments running concurrently with wc_10_enabled=False)
- SC-004: filter-bypass mode verified (no filter state-log entries on any v2 propagate)

## Constitution adherence checklist

- ✅ I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / wc10_pilot_memory.md isolated to v2 dir
- ✅ II (One Experiment Per Change): same intervention as v1 (continuous-scalar schema). v2 is SCALE expansion only (8 tickers vs 2; 10 dates per ticker)
- ✅ III (Stay Cheap): T2-boundary at $32 explicitly deliberated in HYPOTHESIS.md
- ✅ IV (No Production Claims): NULL on primary correlation gate explicitly noted; bullish-amplification is the data, not a production-readiness call
- ✅ VI (Spec Before Structural Change): per spec bundle 108
- ✅ VII (Calibrated Abstention v1.5.0/v1.5.1): result confirms 5-of-8 schema-collapse generalization; 3-of-8 genuine-ambiguity sub-population

## Next steps (per pre-scaffolded landing playbook PR #161)

**Branch C (SC-005(b) NULL) selected** — bin-then-output pattern. Per the v2 4-PR landing playbook:

1. **PR #1 (this PR)**: ANALYSIS.md replacing template — current PR
2. **PR #2**: RESEARCH_FINDINGS.md v2 section append (joint with WC-11 + BR-3 already landed in PR #180) — adds combined-cohort metrics + Branch C selection
3. **PR #3**: ROADMAP consolidated update — integrates WC-11 + BR-3 + v2 outcomes into Phase B/C/D/E posture
4. **PR #4**: Spec 009 MVP — Branch C activation (bin-then-output pattern; 5-tier external surface preserved; continuous internal for ergonomic use)

**Architectural implication**: WC-10 continuous-scalar mode SHOULD NOT ship as the operator-facing output schema. The bullish-amplification ergonomic gain (Buy bucket α +2.93% at 80% hit) is REAL but is captured equally well by binning-then-emitting 5-tier. The scalar magnitude beyond the bin assignment carries no detectable signal at n=100. Spec 009 Branch C activates the bin-then-output pattern — keeps the categorical schema as external interface, uses continuous internal representation for cases where the operator wants a richer audit trail.

**Memory entry**: `reference_wc10_v2_null_correlation.md` — documents the SC-005(b) NULL finding + JNJ counter-finding + NVDA degenerate-attractor pattern for future continuous-scalar work.

**Cross-pollination L4 update**: v2 doesn't change the BR-3 Squeak L4 status (analyst-stage hypothesis; orthogonal mechanism).

## Cost

$32 LLM (Constitution III T2-boundary; spent on 80 propagates).

## Cross-references

- HYPOTHESIS.md (this dir) — 3-prediction framework (NULL / ALT-A / ALT-B) per spec 108
- PARAMS.json (this dir) — 8 tickers × 10 dates grid; wc_10_enabled=True; filter-bypass mode
- v1 ANALYSIS: `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (PR #130) — categorical-bottleneck-confirmed at n=20
- v3 ANALYSIS: `experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/ANALYSIS.md` (PR #153) — PARTIAL ALT-A on Q4 2025 NVDA
- Constitution v1.5.0 amendment: PR #131
- Constitution v1.5.1 amendment: PR #154
- Constitution v1.5.2 amendment (WC-11): PR #179
- v2 4-PR landing playbook: `claudedocs/v2-landing-pr-series-bundle-template-2026-05-08.md` (PR #161)
- Spec 009 conditional design surface: `specs/009-wc-10-production-deployment/` (PRs #137 + #144 + #145 + #149 + #150)
- Triple-pilot landing playbook: PR #172
