# ANALYSIS template — BR-3 v2 (news + fundamentals)

> **STATUS**: TEMPLATE awaiting data. When `results.csv` reaches 40 rows,
> replace `<TBD>` placeholders, pick matching verdict block per
> sub-experiment (KEEP one, DELETE other 4), rename to `ANALYSIS.md`.

**Experiment ID**: `2026-05-09-003-br3-v2-news-fundamentals`
**Created**: 2026-05-09
**Predecessor**: BR-3 v1 ANALYSIS at `experiments/2026-05-09-001-br3-squeak-market-analyst/ANALYSIS.md` (PR #178)

## Headline verdict (TBD post-data)

**Sub-experiment A (news_analyst)**: `<TBD>` from {NULL, ALT-A, ALT-B, PARTIAL ALT-B}
**Sub-experiment B (fundamentals_analyst)**: `<TBD>` from same set
**DIFFERENTIAL** if A and B differ.

## Per-sub-experiment metrics

### Sub-experiment A — news_analyst_format prose vs structured

| Mode | n | Buy/OW | Hold | UW/Sell | Mean rating-attrib α |
|---|---:|---:|---:|---:|---:|
| news_prose (control) | 10 | <TBD> | <TBD> | <TBD> | <TBD>% |
| news_structured (intervention) | 10 | <TBD> | <TBD> | <TBD> | <TBD>% |
| **Δ (structured − prose)** | — | <TBD> | <TBD> | <TBD> | <TBD>pp |

| Trigger | Threshold | Observed | Met? |
|---|---|---|---|
| Hold shift (ALT-A) | ≥ +20pp | <TBD>pp | <TBD> |
| Commit shift (ALT-B) | ≥ +20pp | <TBD>pp | <TBD> |
| α delta magnitude (ALT-B full) | ≥ +1.0pp | <TBD>pp | <TBD> |

### Sub-experiment B — fundamentals_analyst_format prose vs structured

(same structure)

## Computation snippet

```python
import csv
from collections import defaultdict
from tradingagents.graph.trading_graph import fetch_returns

ROWS = [r for r in csv.DictReader(open("experiments/2026-05-09-003-br3-v2-news-fundamentals/results.csv")) if not r["error"]]

per_mode = defaultdict(list)
for r in ROWS:
    raw, alpha, _ = fetch_returns(r["ticker"], r["date"], holding_days=21)
    if alpha is None: continue
    per_mode[r["mode"]].append({"ticker": r["ticker"], "date": r["date"],
                                 "rating": r["rating"], "alpha": alpha * 100})

def attr(rating, alpha):
    if rating in ("Buy", "Overweight"): return alpha
    if rating in ("Underweight", "Sell"): return -alpha
    return 0.0

print(f"{'Mode':<25} {'n':>3} {'mean attr α %':>14} {'Buy/OW':>7} {'Hold':>5} {'UW/Sell':>8}")
COMMITS = ("Buy", "Overweight", "Underweight", "Sell")
for mode in ("news_prose", "news_structured", "fund_prose", "fund_structured"):
    rs = per_mode[mode]; n = len(rs)
    mean_attr = sum(attr(r["rating"], r["alpha"]) for r in rs) / max(1, n)
    bull = sum(1 for r in rs if r["rating"] in ("Buy", "Overweight"))
    hold = sum(1 for r in rs if r["rating"] == "Hold")
    bear = sum(1 for r in rs if r["rating"] in ("Underweight", "Sell"))
    print(f"{mode:<25} {n:>3} {mean_attr:>+13.2f} {bull:>7} {hold:>5} {bear:>8}")

# Per sub-experiment Δ
for sub in ("A_news", "B_fund"):
    prose_key, struct_key = ("news_prose", "news_structured") if sub == "A_news" else ("fund_prose", "fund_structured")
    p_attr = sum(attr(r["rating"], r["alpha"]) for r in per_mode[prose_key]) / max(1, len(per_mode[prose_key]))
    s_attr = sum(attr(r["rating"], r["alpha"]) for r in per_mode[struct_key]) / max(1, len(per_mode[struct_key]))
    p_hold_pct = sum(1 for r in per_mode[prose_key] if r["rating"] == "Hold") / max(1, len(per_mode[prose_key])) * 100
    s_hold_pct = sum(1 for r in per_mode[struct_key] if r["rating"] == "Hold") / max(1, len(per_mode[struct_key])) * 100
    p_commit_pct = sum(1 for r in per_mode[prose_key] if r["rating"] in COMMITS) / max(1, len(per_mode[prose_key])) * 100
    s_commit_pct = sum(1 for r in per_mode[struct_key] if r["rating"] in COMMITS) / max(1, len(per_mode[struct_key])) * 100
    print(f"\nSub-experiment {sub}:")
    print(f"  α delta: {s_attr - p_attr:+.2f}pp")
    print(f"  Hold shift: {s_hold_pct - p_hold_pct:+.0f}pp (ALT-A trigger: ≥+20pp)")
    print(f"  Commit shift: {s_commit_pct - p_commit_pct:+.0f}pp (ALT-B trigger: ≥+20pp)")
```

## Verdict-conditional next-steps blocks (per sub-experiment)

### If sub-experiment X verdict NULL (analyst-stage robust to format)

1. **Memory entry**: `reference_brX_analyst_format_robustness.md` — analyst-stage prose is decorative for that analyst
2. **CHANGELOG**: "BR-3 v2 X — analyst stage X is format-robust"
3. **Spec implication**: NONE for that analyst

### If sub-experiment X verdict ALT-A confirmed (prose carries signal)

1. **Memory entry**: `reference_brX_analyst_prose_load_bearing.md`
2. **CHANGELOG**: "BR-3 v2 X ALT-A — do NOT structurize the X analyst in production"
3. **Architectural implication**: X analyst's prose is structurally important

### If sub-experiment X verdict ALT-B confirmed (structured surfaces signal)

1. **Memory entry**: `reference_structured_throughout_unblocked_X.md`
2. **CHANGELOG**: "BR-3 v2 X ALT-B — Phase E structured-output for X unblocked"
3. **Spec scaffold**: Phase E spec drafting candidate

### If sub-experiment X verdict PARTIAL ALT-B (commit shift but α delta below threshold)

1. **Memory entry**: same as v1 framing — analyst-stage effect REAL but n insufficient
2. **CHANGELOG**: "BR-3 v2 X PARTIAL — direction matches ALT-B but n=10 commit cohort insufficient"
3. **Sister experiments**: v3 extension to 20+ commits per mode

### If DIFFERENTIAL (A and B differ)

1. **Memory entry**: `reference_br3_v2_analyst_specific.md` — only one analyst stage carries the structured-output bottleneck; document which
2. **CHANGELOG**: "BR-3 v2 DIFFERENTIAL — analyst-stage structured-output effect is X-analyst-specific"
3. **Spec implication**: structured-output for X analyst could be considered Phase E candidate; other analyst stays prose

## Constitution adherence checklist

- [ ] I (Save Everything): isolated experiment dir
- [ ] II (One Experiment Per Change): 2 sub-experiments × single intervention each
- [ ] III (Stay Cheap): T2 ($16)
- [ ] IV (No Production Claims): NULL/PARTIAL valid
- [ ] VI: 2 new analyst modules + 2 config keys is structural change; this HYPOTHESIS + module testing serves spec-first
- [ ] VII: orthogonal — operates pre-PM

## Cross-references

- BR-3 v1 ANALYSIS: `experiments/2026-05-09-001-br3-squeak-market-analyst/ANALYSIS.md`
- Sister WC-11 v2 cohort: `experiments/2026-05-09-002-wc11-v2-disambiguation/`
- Dual-pilot landing playbook: `claudedocs/dual-pilot-launch-playbook-2026-05-09.md`
- Implementation: `tradingagents/agents/analysts/news_analyst_structured.py` + `fundamentals_analyst_structured.py`
- Pilot harness: `scripts/br3_v2_pilot.py` (NEW)
