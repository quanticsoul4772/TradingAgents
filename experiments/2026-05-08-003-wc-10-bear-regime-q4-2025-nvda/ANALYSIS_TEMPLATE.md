# WC-10 v3 bear-regime test — ANALYSIS template

> **STATUS**: TEMPLATE awaiting data. Background pilot in flight (~2.5h ETA from 2026-05-08 evening kickoff). Replace `<TODO>` placeholders + numerical TBDs with computed values once `results.csv` reaches 16 rows. Then move/rename this file to `ANALYSIS.md`.

**Experiment ID**: `2026-05-08-003-wc-10-bear-regime-q4-2025-nvda`
**Spec bundle**: `specs/108-wc-10-continuous-scalar-rating/`
**Run date**: 2026-05-08 → <TODO completion timestamp>
**Total LLM cost**: ~$6.40 (16 propagates × ~$0.40)
**Predecessors**:
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` (v1, n=20 paired)
- `experiments/2026-05-03-008-opus47-cross-period/` (5-tier Q4 2025 NVDA reference, Opus 4.7)

## Headline verdict (TBD post-data)

**SC-007 v3 falsification verdict: <NULL | ALT-A | ALT-B | PARTIAL ALT-A>** on the bear-regime cohort.

- **NULL** (regime-neutral): mean_α(WC-10) ≈ mean_α(5-tier) within ±100 bps
- **ALT-A** (bear-regime AMPLIFIES failure): WC-10 commits more bullishly → MORE wrong → mean_α(WC-10) − mean_α(5-tier) ≤ -100 bps
- **ALT-B** (bear-regime CORRECTS direction): WC-10 surfaces bearish reads → mean_α(WC-10) − mean_α(5-tier) ≥ +100 bps
- **PARTIAL ALT-A**: direction matches ALT-A (more bullish commits) but α delta < 100 bps in magnitude

## Per-date paired results

| Date | NVDA WC-10 rating | NVDA WC-10 binned | NVDA 5-tier rating | NVDA 21d raw | 21d α vs SPY |
|---|---|---|---|---:|---:|
| 2025-11-07 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-11-14 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-11-21 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-11-28 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-05 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-12 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-19 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |
| 2025-12-26 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD> |

(NVDA 21d raw is the same value across both modes per propagate; only the rating differs.)

## Aggregate metrics (PRIMARY)

| Mode | n | Mean rating | Buy/OW count | UW/Sell count | Hold-bin count | Mean 21d α |
|---|---:|---:|---:|---:|---:|---:|
| WC-10 | 8 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>% |
| 5-tier baseline | 8 | <TBD> | <TBD> | <TBD> | <TBD> | <TBD>% |

**α delta (WC-10 − 5-tier)**: <TBD>pp

**Verdict**: <NULL / ALT-A / ALT-B / PARTIAL ALT-A>

## Direction distribution comparison (SECONDARY)

| Bin | WC-10 count | 5-tier count | Pattern |
|---|---:|---:|---|
| Buy | <TBD> | <TBD> | <TBD> |
| Overweight | <TBD> | <TBD> | <TBD> |
| Hold | <TBD> | <TBD> | <TBD> |
| Underweight | <TBD> | <TBD> | <TBD> |
| Sell | <TBD> | <TBD> | <TBD> |

**Pattern interpretation**:

- If WC-10 emits MORE Buy/OW than 5-tier on this falling cohort → ALT-A confirmed
- If WC-10 emits MORE UW/Sell than 5-tier → ALT-B confirmed
- If both modes emit similar distributions → NULL
- If WC-10 amplifies BOTH directions while 5-tier collapses to Hold → PARTIAL ALT-A (the schema fix is direction-aware but not regime-aware)

## Cross-experiment comparison to 008 (TERTIARY)

Experiment 008 (Opus 4.7) ran the same 8 dates and produced **7/8 OW + 1 Hold (5-tier)** with realized 21d α ≈ -0.47% n=9, 22% hit per `RESEARCH_FINDINGS.md`. This experiment uses Sonnet 4.6 (lighter model); cross-experiment comparison is approximate. Within-experiment pairing is the load-bearing measurement.

| Source | Model | Mode | OW count | UW count | Hold count | Mean 21d α |
|---|---|---|---:|---:|---:|---:|
| Exp 008 | Opus 4.7 | 5-tier | 7 | 0 | 1 | -0.47% |
| v3 5-tier | Sonnet 4.6 | 5-tier | <TBD> | <TBD> | <TBD> | <TBD>% |
| v3 WC-10 | Sonnet 4.6 | continuous | <TBD> | <TBD> | <TBD> | <TBD>% |

If v3 5-tier ≈ 008 5-tier in direction (but with Sonnet's likely higher Hold rate per Constitution VII v1.5.0 mechanism A), then v3's WC-10 vs 5-tier delta isolates the schema effect from the model effect.

## Constitution VII v1.5.0 feedback (load-bearing)

| Verdict | What it implies for v1.5.0 caveat |
|---|---|
| ALT-A confirmed | v1.5.0 caveat STRENGTHENED — bear-regime validation IS load-bearing for universalizing schema fix; WC-10 is regime-conditional |
| ALT-B confirmed | v1.5.0 caveat WEAKENED — WC-10 may surface direction-correct signal independent of regime; consider revising caveat language |
| NULL | v1.5.0 caveat MAY BE OVER-CAUTIOUS — schema fix is regime-neutral; consider relaxing caveat to "asymmetric bullish-amplification but neutral overall" |
| PARTIAL ALT-A | v1.5.0 caveat CONFIRMED at predicted scope — regime-asymmetric calibration is real but bounded; caveat language is correct as-written |

## Constitution adherence checklist

- ✅ I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS / wc10_pilot_memory.md isolated to v3 dir
- ✅ II (One Experiment Per Change): same intervention as v1 + v2 (continuous-scalar schema). v3 differs only in cohort.
- ✅ III (Stay Cheap): T1 (≤$10) at $6.40
- ✅ IV (No Production Claims): bear-regime result informs the universalize-or-not decision; does not commit
- ✅ VI (Spec Before Structural Change): per spec bundle 108
- <TBD VII>: result feeds back into v1.5.0 caveat per the table above

## Next steps (for operator decision; populate after data lands)

<TBD per verdict — possibilities include:>

1. If ALT-A → memorialize regime-conditionality as a constitutional clarification (v1.5.0 → v1.5.1 PATCH); WC-10 production deployment requires regime-aware gating
2. If ALT-B → schema fix may be universally beneficial; v1.5.0 caveat language could be loosened
3. If NULL → schema fix is regime-neutral; bullish-amplification finding from v1 + v2 is the dominant claim and bear-regime concern was over-cautious
4. If PARTIAL ALT-A → caveat is correctly bounded; document the regime-asymmetry pattern in `RESEARCH_FINDINGS.md` headline

---

## Pre-scaffolding extensions (added 2026-05-08, PR #147)

### A. Ready-to-run computation snippet

When `results.csv` reaches 16 rows, run this against it to populate every `<TBD>` placeholder above:

```python
# Run from project root after results.csv has 16 rows.
# Outputs: per-date table + aggregate stats + verdict.

import csv
from collections import defaultdict
from tradingagents.graph.trading_graph import fetch_returns

CSV = "experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv"
ROWS = []
with open(CSV) as f:
    for row in csv.DictReader(f):
        if row["error"]: continue
        ROWS.append(row)

# Fetch realized α once per (ticker, date)
ret_cache = {}
for r in ROWS:
    key = (r["ticker"], r["date"])
    if key not in ret_cache:
        raw, alpha, days = fetch_returns(r["ticker"], r["date"], holding_days=21)
        ret_cache[key] = (raw, alpha, days)

# Aggregate per mode
def attr(rating, alpha):
    if rating in ("Buy", "Overweight"): return alpha
    if rating in ("Underweight", "Sell"): return -alpha
    return 0.0

per_mode = defaultdict(list)
for r in ROWS:
    raw, alpha, days = ret_cache[(r["ticker"], r["date"])]
    if alpha is None: continue
    rating = r["binned_tier"] if r["mode"] == "wc_10" else r["rating"]
    per_mode[r["mode"]].append({"date": r["date"], "rating": rating, "alpha": alpha * 100, "attr": attr(rating, alpha * 100)})

print("Mode,n,Mean rating-attributed α %,Buy/OW count,UW/Sell count,Hold count")
for mode in ("wc_10", "5tier_baseline"):
    rs = per_mode[mode]
    n = len(rs)
    mean_attr = sum(r["attr"] for r in rs) / n if n else 0
    bull = sum(1 for r in rs if r["rating"] in ("Buy", "Overweight"))
    bear = sum(1 for r in rs if r["rating"] in ("Underweight", "Sell"))
    hold = sum(1 for r in rs if r["rating"] == "Hold")
    print(f"{mode},{n},{mean_attr:+.2f},{bull},{bear},{hold}")

# Verdict
wc_mean = sum(r["attr"] for r in per_mode["wc_10"]) / max(1, len(per_mode["wc_10"]))
bs_mean = sum(r["attr"] for r in per_mode["5tier_baseline"]) / max(1, len(per_mode["5tier_baseline"]))
delta = wc_mean - bs_mean
wc_bull = sum(1 for r in per_mode["wc_10"] if r["rating"] in ("Buy", "Overweight"))
wc_bear = sum(1 for r in per_mode["wc_10"] if r["rating"] in ("Underweight", "Sell"))

print(f"\nα delta (WC-10 - 5-tier): {delta:+.2f}pp")
print(f"WC-10 commit direction: {wc_bull} bull / {wc_bear} bear")
if delta <= -1.0:
    print("→ VERDICT: ALT-A (bear-regime amplifies failure) — apply Patch A from constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md")
elif delta >= +1.0:
    if wc_bear / max(1, len(per_mode["wc_10"])) >= 0.30:
        print("→ VERDICT: ALT-B (bear-regime corrects direction) — apply Patch C")
    else:
        print("→ VERDICT: ALT-B candidate but bear count <30% — investigate before applying Patch C")
elif abs(delta) < 1.0:
    if wc_bull > 4:  # WC-10 went mostly bullish on a falling cohort
        print("→ VERDICT: PARTIAL ALT-A (direction matches ALT-A but magnitude <100bps) — apply Patch D")
    else:
        print("→ VERDICT: NULL (regime-neutral) — apply Patch B")
```

Output:
- One CSV row per mode (n / mean attributed α / bin counts)
- Headline α delta + verdict line
- Verdict line directly cites the matching Constitution v1.5.1 patch (per PR #144)

### B. Verdict-conditional ANALYSIS prose blocks

After running the script above, KEEP one of the four blocks below + DELETE the other three. Each block is pre-written for its verdict; just plug in computed numbers.

#### Block ALT-A (apply if `delta_pp ≤ -1.0`)

> **SC-007 v3 falsification: ALT-A confirmed (bear-regime amplifies failure).**
>
> WC-10 v3 on Q4 2025 NVDA produced mean rating-attributed 21d α of <FILL: WC-10 mean>%, vs 5-tier baseline's <FILL: 5-tier mean>%. The α delta of <FILL: delta>pp is in the ALT-A region (`delta ≤ -1.0pp`).
>
> Direction matches the v1 caveat: WC-10 emitted <FILL: WC-10 bull count>/8 dates as Buy/OW (binned), reading bullish on a falling cohort. The schema fix amplifies the framework's existing bullish reads regardless of whether those reads are direction-correct; on Q4 2025 NVDA where the framework reads wrong, the amplification produces worse outcomes.
>
> **Constitution VII v1.5.0 caveat STRENGTHENED.** Apply Constitution v1.5.1 Patch A from `claudedocs/constitution-v1.5.1-conditional-patch-drafts-2026-05-08.md` — adds "Bear-regime validation" paragraph requiring regime-aware gating for WC-10 production deployment.
>
> **Spec 009 branch selection**: Branch A activation requires regime-detection signal (e.g., VIX > 25 heuristic or per-ticker trailing-α). Branch B (research-only) is the safer default until regime-aware gating ships. v3 verdict pushes Spec 009 v2 plan toward Branch A + B hybrid: B by default, A opt-in with regime gate.

#### Block NULL (apply if `|delta_pp| < 1.0` AND `WC-10 bull count ≤ 4`)

> **SC-007 v3 falsification: NULL (regime-neutral).**
>
> WC-10 v3 on Q4 2025 NVDA produced mean rating-attributed 21d α of <FILL: WC-10 mean>%, vs 5-tier baseline's <FILL: 5-tier mean>%. The α delta of <FILL: delta>pp is statistically indistinguishable from baseline at n=8 (the NULL region: `|delta| < 1.0pp`).
>
> The schema fix is regime-NEUTRAL on this cohort. The v1 AAPL UW anti-calibration finding may have been a single-cohort artifact rather than a universal bear-side mechanism.
>
> **Constitution VII v1.5.0 caveat WEAKENED to "monitor and adjust if observed in production."** Apply Constitution v1.5.1 Patch B — preserves the caveat for documentation but downgrades it from a hard requirement to a runtime-monitoring trigger via `scripts/wc_10_underperformance_monitor.py` (PR #146).
>
> **Spec 009 branch selection**: Branch A activation does NOT require regime-aware gating per this evidence. Operator-opt-in WC-10 mode in `daily_signals.py` is unblocked.

#### Block ALT-B (apply if `delta_pp ≥ +1.0` AND `WC-10 bear count / n ≥ 0.30`)

> **SC-007 v3 falsification: ALT-B confirmed (bear-regime corrects direction).**
>
> WC-10 v3 on Q4 2025 NVDA produced mean rating-attributed 21d α of <FILL: WC-10 mean>%, vs 5-tier baseline's <FILL: 5-tier mean>%. The α delta of <FILL: delta>pp is in the ALT-B region (`delta ≥ +1.0pp`).
>
> Direction REVERSES the v1 caveat: WC-10 emitted <FILL: WC-10 bear count>/8 dates as Underweight (binned), surfacing bearish reads that 5-tier suppressed on a falling cohort. The schema fix surfaces direction-correct signal independent of regime — including bearish signal on falling tickers that the 5-tier scale's Hold-default was hiding.
>
> **Constitution VII v1.5.0 caveat REVERSED in direction.** Apply Constitution v1.5.1 Patch C — reframes the v1 AAPL UW finding as a regime-specific counter-case rather than a universal bear-side mechanism.
>
> **Spec 009 branch selection**: Branch A activation is universally beneficial across the bull/bear spectrum on this evidence. WC-10 mode in `daily_signals.py` ships without regime-aware gating.

#### Block PARTIAL ALT-A (apply if `|delta_pp| < 1.0` AND `WC-10 bull count > 4`)

> **SC-007 v3 falsification: PARTIAL ALT-A (direction matches but magnitude < 1.0pp).**
>
> WC-10 v3 on Q4 2025 NVDA produced mean rating-attributed 21d α of <FILL: WC-10 mean>%, vs 5-tier baseline's <FILL: 5-tier mean>%. The α delta of <FILL: delta>pp falls below the ALT-A magnitude threshold (`|delta| < 1.0pp`) but the direction matches: WC-10 emitted <FILL: WC-10 bull count>/8 dates as Buy/OW (binned), reading bullish on a falling cohort.
>
> The v1.5.0 caveat language ("WC-10 amplifies whatever signal the framework was already generating") is correct as-written. The magnitude is small enough that strengthening to "amplifies in a way that produces statistically worse outcomes" would over-claim from this sample.
>
> **Constitution VII v1.5.0 caveat CONFIRMED at predicted scope.** Apply Constitution v1.5.1 Patch D — preserves caveat language; documents empirical magnitude bound at < 1.0pp on this cohort.
>
> **Spec 009 branch selection**: Branch A activation ships with the v1.5.0 caveat documented in `docs/SIGNALS.md` per Spec 009 FR-006 but does NOT require regime-aware gating as a hard requirement. Operator discretion suffices.

### C. Monitoring loop integration

After v3 ANALYSIS lands, the WC-10 underperformance monitor (PR #146) provides the runtime monitoring tier:

```bash
python scripts/wc_10_underperformance_monitor.py --csv experiments/2026-05-08-003-wc-10-bear-regime-q4-2025-nvda/results.csv
```

Smoke test on v3 data — operators can verify:
1. The script flags the v3 cohort consistently with the verdict above
2. If verdict is ALT-A: monitor's per-pair alerts should fire on dates where WC-10 amplified bullish reads on falling NVDA
3. If verdict is NULL: monitor should NOT fire any alerts
4. If verdict is ALT-B: monitor's alerts should be inverted (5-tier mode dates would alert if cron-checked instead)

This converts the v3 verdict from a one-time research finding into ongoing operational tooling.

### D. Cross-references

- **PR #144** (Constitution v1.5.1 conditional patch drafts) — apply patch matching v3 verdict
- **PR #140** (Spec 009 conditional draft) — branch selection per v3 verdict
- **PR #146** (`scripts/wc_10_underperformance_monitor.py`) — runtime monitoring; smoke test on v3 data
- **PR #135** (this template's predecessor) — original template that this PR extends
- `experiments/2026-05-08-001-wc-10-pilot/ANALYSIS.md` — v1 verdict (ALT-A at distribution level)
- v2 ANALYSIS_TEMPLATE.md — sister template; v2 verdict feeds Spec 009 Branch A vs B vs C selection

### E. Estimated time-to-PR after data lands

With this extended pre-scaffolding:

1. Run computation snippet (1 min)
2. Pick matching verdict block (1 min)
3. Plug in `<FILL: X>` numbers (3 min)
4. Delete 3 non-matching verdict blocks (1 min)
5. Update Constitution adherence checklist + Next-steps section (3 min)
6. Open PR (5 min)

**Total: ~15 minutes** (vs ~45-60 min if drafting from scratch). Sister to PR #144's "~15 min vs ~45 min" Constitution v1.5.1 estimate; both compose into a single ~30-minute v3 landing PR series.
