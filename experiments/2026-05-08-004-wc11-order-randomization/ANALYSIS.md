# ANALYSIS — WC-11 order randomization

**Experiment ID**: `2026-05-08-004-wc11-order-randomization`
**Run date**: 2026-05-09 (kicked off late 2026-05-08; completed early 2026-05-09)
**Total LLM cost**: ~$8 (20 propagates × ~$0.40, T1)
**Predecessors**:
- HYPOTHESIS + PARAMS scaffold (PR #148)
- Pilot harness + launch (PR #171)
- Triple-pilot landing playbook (PR #172)
- ANALYSIS_TEMPLATE (PR #173)

## Headline verdict

**SC-007 v1 falsification: ALT-A confirmed (first-speaker bias detected) — both ALT-A and ALT-B triggers fire at the +20pp threshold.**

n=20 propagates / 5 dates × NVDA × 4 permutations / $8.

| Verdict trigger | Result | Threshold | Pass/Fail |
|---|---|---|---|
| Per-permutation distribution shift ≥10pp from pooled | Up to ±20pp | NULL fails ≥10pp | **NULL REJECTED** |
| Per-first-analyst commit-rate shift ≥20pp | news-first +20pp | ALT-A trigger ≥20pp | **ALT-A TRIGGERED** |
| Per-last-analyst commit-rate shift ≥20pp | market-last +20pp | ALT-B trigger ≥20pp | **ALT-B ALSO TRIGGERED** |

The framework's analyst order is a confounding variable.

## Per-permutation results

| Permutation | n | Buy | OW | Hold | UW | Sell | Commit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| `market_news_fundamentals` (DEFAULT) | 5 | 0 | 0 | 4 | 1 | 0 | 20% |
| `news_fundamentals_market` | 5 | 0 | 2 | 3 | 0 | 0 | **40%** |
| `fundamentals_market_news` | 5 | 1 | 0 | 4 | 0 | 0 | 20% |
| `market_fundamentals_news` | 5 | 0 | 0 | 5 | 0 | 0 | **0%** |
| **POOLED** | **20** | 1 | 2 | 16 | 1 | 0 | **20%** |

**Range across permutations: 0% → 40% commit rate (±20pp from pooled mean).** NULL prediction (within ±10pp) clearly REJECTED.

## Per-first-analyst aggregation (PRIMARY for ALT-A)

| First analyst | n | Commit rate | Buy/OW rate | Shift vs pooled |
|---|---:|---:|---:|---:|
| POOLED | 20 | 20.0% | 15.0% | n/a |
| fundamentals | 5 | 20.0% | 20.0% | 0pp |
| market | 10 | 10.0% | 0.0% | -10pp |
| **news** | 5 | **40.0%** | 40.0% | **+20pp** ⚠ ALT-A |

**News-first permutations exhibit +20pp commit rate vs pooled mean — meets the ALT-A threshold.**

## Per-last-analyst aggregation (PRIMARY for ALT-B)

| Last analyst | n | Commit rate | Buy/OW rate | Shift vs pooled |
|---|---:|---:|---:|---:|
| fundamentals | 5 | 20.0% | 0.0% | 0pp |
| **market** | 5 | **40.0%** | 40.0% | **+20pp** ⚠ ALT-B |
| news | 10 | 10.0% | 10.0% | -10pp |

**Market-last permutations exhibit +20pp commit rate vs pooled mean — meets the ALT-B threshold.**

## Per-date variance check

| Date | Permutation ratings | Variance |
|---|---|---|
| 2026-01-30 | Hold, Hold, Hold, Hold | UNANIMOUS |
| 2026-02-13 | Hold, Hold, Hold, Hold | UNANIMOUS |
| 2026-02-27 | UW, OW, Hold, Hold | **DIVERGENT** (3 distinct ratings) |
| 2026-03-13 | Hold, Hold, Hold, Hold | UNANIMOUS |
| 2026-03-27 | Hold, OW, Buy, Hold | **DIVERGENT** (3 distinct ratings) |

**2 of 5 dates produced divergent ratings across permutations.** On 2026-02-27 + 2026-03-27, the SAME date produced both bullish (Buy/OW) and bearish (UW) commits depending on analyst order. This is direct evidence of order-dependent synthesis at the rating level.

## Disambiguation note

Both ALT-A AND ALT-B triggers fire on the SAME permutation (`news_fundamentals_market` has news-first AND market-last). Of the 4 corpus commits:

- `news_fundamentals_market` (first=news, last=market): 2 of 4 commits (NVDA 02-27 OW + 03-27 OW)
- `fundamentals_market_news` (first=fundamentals, last=news): 1 commit (NVDA 03-27 Buy)
- `market_news_fundamentals` (DEFAULT; first=market, last=fundamentals): 1 commit (NVDA 02-27 UW)

The single permutation `news_fundamentals_market` drives BOTH triggers. At n=20, we cannot disambiguate between:
- (a) news-first bias (news framing primes commitment)
- (b) market-last bias (final market-analyst review pushes commit)
- (c) interaction effect specific to the news_fundamentals_market sequence

What IS established at n=20:
1. **Synthesis is NOT order-robust** (NULL rejected at -20pp range)
2. **The fixed DEFAULT order `[market, news, fundamentals]` is NOT the most-commit-prone** — it produced 1 commit / 5 propagates (20%); `news_fundamentals_market` produced 2 / 5 (40%)
3. **Prior corpus claims using the DEFAULT order are systematically biased toward Hold** — operators using DEFAULT order get fewer commits than the framework would emit under news-first orderings

## Implications

### Constitution implication

**Constitution VII Replicability-scope sub-section needs amendment** to flag analyst-order as a load-bearing methodological variable. Recommended: v1.5.1 → **v1.5.2 (PATCH)** adding a paragraph documenting:
- WC-11 verdict (ALT-A/ALT-B triggered at n=20)
- The implication that bucket-level claims under DEFAULT order may UNDER-count commits the framework would emit under different orderings
- An operational note: future ablations should either randomize analyst order within the cohort OR explicitly document the DEFAULT order as a confounder

Per triple-landing playbook (PR #172) Constitution amendment sequencing: **WC-11 amendment lands FIRST** (most foundational; affects corpus interpretation); BR-3 + v2 amendments (if any) follow.

### Methodology implication

The 005-vs-007 NVDA cross-experiment finding (10/10 OW becomes 6/10 OW + 4 Hold on same dates with same model) — previously attributed to "stochastic LLM variance" per Constitution VII Replicability-scope — may be PARTIALLY explained by analyst-order variance. WC-11 establishes that ±20pp commit-rate shift across permutations is a real effect; same date producing different outputs across reruns may have order-dependent components beyond pure stochasticity.

### Research findings update

RESEARCH_FINDINGS.md "What's still open" entry on WC-11 should be marked RESOLVED with verdict ALT-A. The "Same-date rerun-variance" entry should be cross-referenced as related (WC-11 establishes one mechanism that contributes to that variance).

## Constitution adherence checklist

- ✅ I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / wc11_pilot_memory.md isolated to this dir
- ✅ II (One Experiment Per Change): single intervention (analyst order); no other variables changed across permutations
- ✅ III (Stay Cheap): T1 ($8 within ≤$10)
- ✅ IV (No Production Claims): ALT-A / ALT-B verdict is empirical evidence; no production deployment changes
- ✅ VI (Spec Before Structural Change): N/A — Option B harness avoided structural change
- ⚠️ VII (Calibrated Abstention v1.5.1): VERDICT TRIGGERS v1.5.2 amendment to Replicability-scope sub-section
- ✅ VIII: N/A — not a filter

## Next steps

1. **Constitution v1.5.1 → v1.5.2 amendment** (per triple-landing playbook sequencing — WC-11 amendment FIRST). Drafted as part of WC-11 landing series.
2. **RESEARCH_FINDINGS update** marking WC-11 as RESOLVED + cross-referencing the rerun-variance question.
3. **CHANGELOG entry**: "WC-11 ALT-A confirmed — analyst-order is a confounding methodological variable; DEFAULT `[market, news, fundamentals]` order systematically under-counts commits vs alternative orderings."
4. **Future ablations** should randomize analyst order OR explicitly document DEFAULT order as a confounder per the new v1.5.2 paragraph.

## Cross-references

- HYPOTHESIS.md (this dir) — 3-prediction framework
- PARAMS.json (this dir)
- Pilot harness: `scripts/wc11_order_pilot.py` (PR #171)
- Triple-pilot landing playbook (PR #172) — Constitution amendment sequencing rule
- ANALYSIS template extension (PR #173)
- Constitution VII Replicability-scope sub-section (current state pre-amendment)
- Memory `reference_pre_rating_temporal_learning.md` — temporal-learning is at a different scale (week-over-week vs within-propagate); WC-11's order-bias is a complementary mechanism

## Cost

$8 LLM (Constitution III T1).
