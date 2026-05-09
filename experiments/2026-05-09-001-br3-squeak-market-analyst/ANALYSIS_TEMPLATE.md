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

<!-- Verdict-conditional bullets — what action follows from each possible
verdict. Pre-write all branches; delete non-matching after verdict lands. -->

1. If <verdict X> → ...
2. If <verdict Y> → ...

## Cross-references

- HYPOTHESIS.md (this dir)
- PARAMS.json (this dir)
- Constitution principles applicable: <TBD>
- Related experiments: <TBD>
