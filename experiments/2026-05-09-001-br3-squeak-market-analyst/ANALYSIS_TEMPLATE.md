# ANALYSIS template — br3-squeak-market-analyst

> **STATUS**: TEMPLATE awaiting data. When the experiment completes,
> replace `<TBD>` placeholders with computed values, fill the verdict
> sections, and rename this file to `ANALYSIS.md`.

**Experiment ID**: `2026-05-09-001-br3-squeak-market-analyst`
**Created**: 2026-05-09

## Headline verdict (TBD post-data)

<!-- One-paragraph plain-English summary. Pick from the verdict choices in
the Falsification framework section below. -->

**Verdict**: <TBD>

## Per-row results

| Row | Variable A | Variable B | Outcome metric |
|---|---|---|---|
| 1 | <TBD> | <TBD> | <TBD> |
| 2 | <TBD> | <TBD> | <TBD> |
| ... | ... | ... | ... |

<!-- Add columns + rows matching this experiment's grid. For paired
experiments, render side-by-side; for sweep experiments, one row per
parameter setting. -->

## Aggregate metrics

| Metric | Value | Notes |
|---|---:|---|
| Sample size n | <TBD> | |
| Mean / median outcome | <TBD> | |
| Hit rate | <TBD>% | If applicable to the prediction |
| Cohort std / dispersion | <TBD> | |

## Falsification framework verdict

<!-- For each prediction in HYPOTHESIS.md (NULL / ALT-A / ALT-B / ...),
state: which empirical signature was observed; which prediction it
matches; whether the verdict is decisive or borderline. -->

| Prediction | Empirical signature | Observed? | Verdict |
|---|---|---|---|
| NULL | | | <TBD> |
| ALT-A | | | <TBD> |
| ALT-B | | | <TBD> |

## Constitution adherence checklist

- [ ] I (Save Everything): HYPOTHESIS / PARAMS / results.csv / ANALYSIS isolated to this experiment dir
- [ ] II (One Experiment Per Change): single intervention per HYPOTHESIS.md
- [ ] III (Stay Cheap): cost ≤ T1/T2/T3/T4 budget per HYPOTHESIS.md
- [ ] IV (No Production Claims): negative results explicitly noted; no over-claiming
- [ ] VI (Spec Before Structural Change): N/A (or per spec bundle reference)
- [ ] VII (Calibrated Abstention): orthogonal OR specifies which sub-population per v1.5.0
- [ ] VIII (Retrospective gate): N/A OR retrospective markdown shipped alongside

## Next steps (for operator decision; populate after data lands)

<!-- Pre-written verdict-conditional bullets per HYPOTHESIS framework
(NULL / ALT-A / ALT-B). Delete the 2 non-matching after verdict lands. -->

### If verdict NULL (analyst-stage robust to format)

1. **Memory entry**: capture as `reference_analyst_stage_format_robustness.md` — operationally, the prose vs structured choice is a pure cost-vs-readability tradeoff with no signal implications
2. **CHANGELOG entry**: "BR-3 ruled out — analyst-stage prose is decorative; structured output is pure cost win"
3. **Sister experiments unblocked**: extend structured-output to news + fundamentals analysts (BR-3 v2 sister scaffolds — adds ~$8 each)
4. **Constitution implication**: NONE
5. **Spec implication**: NONE — BR-3 line closes; no Phase E spec needed

### If verdict ALT-A (prose carries signal)

1. **Memory entry**: capture as `reference_analyst_stage_prose_load_bearing.md` — flag prose-as-load-bearing for any future analyst-stage refactoring
2. **CHANGELOG entry**: "BR-3 ALT-A confirmed — analyst-stage prose carries signal that structured output loses; do NOT structurize analysts in production"
3. **Architectural implication**: rest of project should treat prose-emitting analysts as architecturally important (not refactor candidates)
4. **Constitution implication**: possible new sub-section on Principle VII or new Principle on prose-as-information-channel; defer to operator decision
5. **Spec implication**: NONE — BR-3 line closes with "prose preserved" verdict

### If verdict ALT-B (structured surfaces signal)

1. **Memory entry**: capture as `reference_structured_output_throughout_unblocked.md` — major architectural implication
2. **CHANGELOG entry**: "BR-3 ALT-B confirmed — structured output surfaces signal that prose was burying; Phase E architectural variant unblocked"
3. **Spec scaffold**: `specs/012-structured-output-throughout/spec.md` — conditional draft (analogous to Spec 009 conditional pattern); 4 verdict-conditional branches per how broadly structured output applies (just market analyst / all 3 analysts / all analysts + bull/bear / full pipeline)
4. **Sister experiments**: BR-3 v2 (extend to news + fundamentals; ~$8) + BR-3 v3 (extend to bull/bear debate stage; ~$10)
5. **Constitution implication**: possible v1.5.1 → v1.6.0 MAJOR — new Principle "Structured-output-throughout architecture" if Phase E proceeds
6. **Cross-pollination L4 update**: NEW-1 (Squeak structured signaling) is no longer a candidate — it's a confirmed architectural direction

## Computation snippet (run when results.csv reaches 20 rows)

```python
import csv
from collections import defaultdict
from tradingagents.graph.trading_graph import fetch_returns

CSV = "experiments/2026-05-09-001-br3-squeak-market-analyst/results.csv"
ROWS = []
with open(CSV) as f:
    for row in csv.DictReader(f):
        if row["error"]: continue
        ROWS.append(row)

# Group by mode + ticker for paired comparison
ret_cache = {}
for r in ROWS:
    key = (r["ticker"], r["date"])
    if key not in ret_cache:
        raw, alpha, days = fetch_returns(r["ticker"], r["date"], holding_days=21)
        ret_cache[key] = (raw, alpha, days)

def attr(rating, alpha):
    if rating in ("Buy", "Overweight"): return alpha
    if rating in ("Underweight", "Sell"): return -alpha
    return 0.0

per_mode = defaultdict(list)
for r in ROWS:
    raw, alpha, days = ret_cache[(r["ticker"], r["date"])]
    if alpha is None: continue
    per_mode[r["mode"]].append({"date": r["date"], "ticker": r["ticker"], "rating": r["rating"], "alpha": alpha * 100, "attr": attr(r["rating"], alpha * 100)})

print("Mode,n,Mean rating-attributed α %,Buy/OW count,UW/Sell count,Hold count")
for mode in ("prose", "structured"):
    rs = per_mode[mode]
    n = len(rs)
    mean_attr = sum(r["attr"] for r in rs) / n if n else 0
    bull = sum(1 for r in rs if r["rating"] in ("Buy", "Overweight"))
    bear = sum(1 for r in rs if r["rating"] in ("Underweight", "Sell"))
    hold = sum(1 for r in rs if r["rating"] == "Hold")
    print(f"{mode},{n},{mean_attr:+.2f},{bull},{bear},{hold}")

# Verdict
prose_mean = sum(r["attr"] for r in per_mode["prose"]) / max(1, len(per_mode["prose"]))
struct_mean = sum(r["attr"] for r in per_mode["structured"]) / max(1, len(per_mode["structured"]))
delta = struct_mean - prose_mean

# Distribution shift toward Hold (ALT-A signature)
prose_hold = sum(1 for r in per_mode["prose"] if r["rating"] == "Hold") / max(1, len(per_mode["prose"]))
struct_hold = sum(1 for r in per_mode["structured"] if r["rating"] == "Hold") / max(1, len(per_mode["structured"]))
hold_shift_pp = (struct_hold - prose_hold) * 100

# Distribution shift toward commits (ALT-B signature)
prose_commit = sum(1 for r in per_mode["prose"] if r["rating"] in ("Buy", "Overweight", "Underweight", "Sell")) / max(1, len(per_mode["prose"]))
struct_commit = sum(1 for r in per_mode["structured"] if r["rating"] in ("Buy", "Overweight", "Underweight", "Sell")) / max(1, len(per_mode["structured"]))
commit_shift_pp = (struct_commit - prose_commit) * 100

print(f"\nα delta (structured - prose): {delta:+.2f}pp")
print(f"Hold shift (structured - prose): {hold_shift_pp:+.0f}pp (ALT-A trigger ≥+20pp)")
print(f"Commit shift: {commit_shift_pp:+.0f}pp (ALT-B trigger ≥+20pp)")

# Verdict logic
if delta <= -1.0 and hold_shift_pp >= 20:
    print("→ VERDICT: ALT-A (prose carries signal)")
elif delta >= +1.0 and commit_shift_pp >= 20:
    print("→ VERDICT: ALT-B (structured surfaces signal)")
elif abs(delta) < 1.0 and abs(hold_shift_pp) < 10 and abs(commit_shift_pp) < 10:
    print("→ VERDICT: NULL (format-robust)")
else:
    print("→ VERDICT: PARTIAL / INCONCLUSIVE — investigate per-direction asymmetry")
```

Output:
- Per-mode CSV row (n / mean attributed α / bin counts)
- Headline α delta + Hold shift + Commit shift
- Verdict line (NULL / ALT-A / ALT-B / PARTIAL)

## Cross-references

- HYPOTHESIS.md (this dir) — 3-prediction framework
- PARAMS.json (this dir) — 5 dates × 2 tickers × 2 formats grid
- Implementation: `tradingagents/agents/analysts/market_analyst_structured.py` (PR #169)
- Pilot harness: `scripts/br3_squeak_pilot.py` (PR #169)
- Sister hypothesis: WC-10 v1 ANALYSIS.md (PM-stage; PR #130)
- Constitution v1.5.1 Principle VII — orthogonal (BR-3 operates upstream of PM)
- Triple-pilot landing playbook: `claudedocs/triple-pilot-landing-playbook-2026-05-09.md` (PR #172)

## Estimated time-to-PR

With this extended pre-scaffolding:

| Step | Time |
|---|---|
| Run computation snippet (1 min) + verify verdict | 3 min |
| Pick matching verdict block (KEEP one, DELETE two) | 2 min |
| Plug in computed numbers + per-mode tables | 8 min |
| Update Constitution adherence checklist + Next-steps section | 3 min |
| Open PR | 5 min |
| **Total** | **~21 min** |

vs ~45 min if drafting ANALYSIS from scratch.
