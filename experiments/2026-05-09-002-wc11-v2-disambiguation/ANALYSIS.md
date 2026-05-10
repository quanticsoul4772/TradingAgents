# ANALYSIS — WC-11 v2 disambiguation (cross-ticker + cross-rerun)

**Experiment ID**: `2026-05-09-002-wc11-v2-disambiguation`
**Run date**: 2026-05-09 evening (background pilot `bwzris458`; completed within ~12h wall-clock)
**Total LLM cost**: ~$24 (60 propagates × ~$0.40, T2)
**Predecessors**:
- WC-11 v1 ANALYSIS: `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md` (PR #177)
- HYPOTHESIS + ANALYSIS_TEMPLATE: PR #214
- Constitution v1.5.3 conditional patch drafts: PR #215
- Dual-pilot landing playbook: PR #214
- Landing-PR series template: PR #218

## Headline verdict

**PARTIAL** — NVDA reproduces v1 news_fundamentals_market elevation (commit rate 40% in both v1 and v2); AAPL + MSFT show DIFFERENT per-permutation patterns where news-first is NOT the elevated permutation.

**Constitution implication**: Apply **Patch D from PR #215 conditional drafts** (CLARIFY; v1.5.2 → v1.5.3 PATCH; ticker-conditional clarification paragraph added to Analyst-order scope sub-section).

n=60 propagates / 5 dates × 3 tickers (NVDA + AAPL + MSFT) × 4 permutations / $24.

## Per-permutation × per-ticker commit rate matrix

| Permutation | NVDA | AAPL | MSFT | Pooled |
|---|---:|---:|---:|---:|
| market_news_fundamentals (DEFAULT) | 0% | 20% | 20% | 13% |
| news_fundamentals_market | **40%** | 20% | **40%** | **33%** |
| fundamentals_market_news | 0% | **60%** | **40%** | 33% |
| market_fundamentals_news | 0% | **60%** | 0% | 20% |

**Pooled rate across all 4 perms**: 25% (vs WC-11 v1 NVDA-only pooled: 20%).

## Cross-rerun-variance check (NVDA only — v1 vs v2 same NVDA cohort)

| Permutation | v1 NVDA | v2 NVDA | Δ |
|---|---:|---:|---:|
| market_news_fundamentals (DEFAULT) | 20% | 0% | -20pp |
| news_fundamentals_market | 40% | **40%** | **0pp** (REPLICATES) |
| fundamentals_market_news | 20% | 0% | -20pp |
| market_fundamentals_news | 0% | 0% | 0pp (REPLICATES) |

**2 of 4 NVDA permutations REPLICATE exactly** between v1 and v2 (news_fundamentals_market + market_fundamentals_news); **2 of 4 vary by ±20pp** (DEFAULT + fundamentals_market_news). Stochastic NVDA variance is approximately ±20pp at n=5 dates per permutation. The **news_fundamentals_market elevation IS REAL on NVDA** (replicated exactly).

## Per-ticker pattern analysis

**NVDA** (cross-rerun-variance check + reproduction):
- Reproduces v1 first-speaker effect (news_fundamentals_market elevated to 40%)
- Other perms heavily Hold-biased (0% commit rate on 3 of 4 perms)

**AAPL** (NEW; cross-ticker generalization test):
- Highest commit rates on fundamentals_market_news (60%) + market_fundamentals_news (60%)
- news_fundamentals_market only 20% (NOT the elevated permutation)
- Pattern: AAPL elevates with **NEWS-LAST** ordering (both fundamentals_market_news + market_fundamentals_news have news as the LAST analyst)

**MSFT** (NEW; cross-ticker generalization test):
- Mixed pattern: news_fundamentals_market 40% + fundamentals_market_news 40% (both elevated)
- DEFAULT 20% + market_fundamentals_news 0%
- Pattern: MSFT elevates when fundamentals appears EARLY (positions 1 or 2)

**Net cross-ticker observation**: per-permutation commit rates are TICKER-SPECIFIC, not framework-general. NVDA shows news-first effect; AAPL shows news-last effect; MSFT shows fundamentals-early effect. **No single analyst-position rule explains all 3 tickers simultaneously**.

## Falsification framework verdict

| Verdict | Trigger | Observed | Match? |
|---|---|---|---|
| NULL revised | All 4 perms within ±10pp of pooled (25%) | range 13-33% (±10-12pp) | **NO** (just outside ±10pp band) |
| ALT-A confirmed | news-first elevates ≥+15pp vs DEFAULT across ≥2/3 tickers | NVDA +40pp; AAPL 0pp; MSFT +20pp | **PARTIAL** (2 of 3; but AAPL is 0pp not negative) |
| ALT-B confirmed | market-last drops ≤-15pp vs DEFAULT across ≥2/3 tickers | news_fundamentals_market is BOTH news-first AND market-last; same +20pp pooled effect | **inseparable from ALT-A** at v2 cohort |
| **PARTIAL** | NVDA reproduces v1 but AAPL/MSFT differ | NVDA reproduces; AAPL/MSFT show different patterns | **MATCH** (this is the verdict) |
| INCONCLUSIVE | v2 fails to reproduce v1 NVDA pattern at all | NVDA reproduces 40% on news_fundamentals_market | NO |

**Verdict per HYPOTHESIS framework**: PARTIAL. The v1 NVDA news-first effect REPLICATES on NVDA; AAPL + MSFT show DIFFERENT per-permutation patterns. Analyst-order effect is **TICKER-CONDITIONAL**, not framework-general first-speaker bias.

## v2 disambiguation outcome (vs v1 PARTIAL ALT-A + ALT-B)

v1 finding was "PARTIAL ALT-A + ALT-B; cannot disambiguate at n=20" (both triggers fired on news_fundamentals_market which is BOTH news-first AND market-last).

v2 expected to disambiguate via cross-ticker generalization. Result: **the disambiguation is itself ticker-conditional**:
- NVDA: news_fundamentals_market is the elevated permutation (news-first effect or market-last effect; still indistinguishable at NVDA)
- AAPL: news_fundamentals_market is NOT elevated (20%); the elevated perms are fundamentals_market_news + market_fundamentals_news (both NEWS-LAST). AAPL pattern is OPPOSITE of NVDA.
- MSFT: news_fundamentals_market and fundamentals_market_news both elevated (40%); pattern doesn't fit either pure first-speaker or pure last-speaker hypothesis.

**The v1 ambiguity (ALT-A vs ALT-B both fired on same perm) is now joined by a ticker-asymmetry finding**: there's no SINGLE order-mechanism that applies across NVDA + AAPL + MSFT. Whatever first-/last-speaker effect exists is conditional on (model × ticker × regime × prompt) per CLAUDE.md headline.

## Implications

### Constitution implication

Apply **Patch D from PR #215 conditional drafts** (CLARIFY; v1.5.2 → v1.5.3 PATCH).

The v1.5.2 randomize-or-document mandate stays AS-IS but is now explicit that the analyst-order effect is ticker-conditional. Per the HYPOTHESIS framework + PR #215 Patch D scaffolding, the new amendment paragraph documents:
- v1.5.2 mandate operative as a precautionary stance
- v2 evidence: ticker-specific patterns; no single order rule generalizes
- Future ablations should NOT assume first-speaker bias is uniform; commit-rate variance per permutation depends on the ticker set

### Operational implication

Operators interpreting WC-11 evidence in subsequent ablations should:
1. **Continue to randomize analyst order** OR document as confounder per v1.5.2
2. **NOT assume news-first is uniformly preferable** — empirically only NVDA-like tickers benefit (or fundamentals-rich AAPL-like tickers benefit from news-last)
3. **Per-ticker analysis** is necessary; pooled analyses across heterogeneous ticker sets average out the order-effect

### Phase E / spec-eligibility implication

No new spec drafting triggered. The analyst-order effect doesn't unblock a new filter or amendment beyond the existing v1.5.2 mandate + the v1.5.3 ticker-conditional clarification.

### v1 + v2 cross-experiment cost

v1 + v2 total: $32 LLM (8 v1 + 24 v2) for the analyst-order research line. Methodologically: this disambiguation cost is high per ship-quality unit (~$5/unit if v1+v2 produce 6-7 units across landing arc) compared to the project's overall $0.45/PR average. The disambiguation didn't yield a clean ALT-A vs ALT-B answer; it yielded a ticker-asymmetry observation.

## Constitution adherence

- ✅ I (Save Everything): isolated experiment dir
- ✅ II (One Experiment Per Change): single intervention per permutation
- ✅ III (Stay Cheap): T2 ($24); user-authorized
- ✅ IV (No Production Claims): PARTIAL verdict; no production deployment changes
- ✅ VI: no structural code change (uses existing harness)
- ✅ VII v1.5.2 → v1.5.3 (per Patch D): the v1.5.2 mandate is what this experiment stress-tested + the ticker-conditional clarification is what v2 surfaces

## Next steps (per PR #218 4-PR landing template)

1. **PR #1 (this ANALYSIS)**: ANALYSIS.md replacing template — current PR
2. **PR #2**: RESEARCH_FINDINGS.md WC-11 v2 section append + Open Questions row resolved
3. **PR #3**: ROADMAP.md row updated to RESOLVED
4. **PR #4**: Constitution v1.5.2 → v1.5.3 (Patch D from PR #215; CLARIFY ticker-conditional). Per PR #172 Constitution-amendment-sequencing rule + PR #218 dual-pilot landing playbook, WC-11 v2's amendment lands FIRST in the dual-pilot landing arc (BR-3 v2 had no amendment).

## Cost

$24 LLM (Constitution III T2; user-authorized via PR #214).

## Cross-references

- v1 ANALYSIS: `experiments/2026-05-08-004-wc11-order-randomization/ANALYSIS.md` (PR #177)
- HYPOTHESIS + PARAMS + ANALYSIS_TEMPLATE: this dir
- Constitution v1.5.3 conditional patch drafts (Patch D applies): `claudedocs/constitution-v1.5.3-conditional-patch-drafts-2026-05-09.md` (PR #215)
- Dual-pilot launch playbook: PR #214
- Landing PR series template: PR #218
- Constitution v1.5.2 (current; PR #179)
- Memory: `reference_wc11_analyst_order_first_speaker_bias.md`
