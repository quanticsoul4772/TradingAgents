# Spec 007 forward-catalyst retrospective — 2026-05-06

**Production-config validation** (extends `scripts/forward_catalyst_class3_retrospective.py`):
- Bull threshold: 0.6
- Bear threshold: 0.5
- Bull mode: active
- Bear mode: shadow
- Model: claude-opus-4-7

Loaded 94 cached scores from `claudedocs\forward-catalyst-class3-opus-retrospective-2026-05-06.csv` (zero new LLM cost; re-applies production filter logic).

## SC-008 cohort cross-tab

- Bull-side cohort hit: **24 / 27** (88.9%) — gate ≥24/27 → **PASS**
- Bear-side cohort hit: **13 / 18** (72.2%) — gate ≥10/18 → **PASS**

## Aggregate per-side metrics

| Side | n_total | n_fired | baseline α | kept α | net Δα |
|---|---|---|---|---|---|
| Bull | 47 | 33 | -0.08% | +2.16% | +2.24pp |
| Bear | 37 | 24 | +12.30% | +12.00% | +0.30pp |

## Verdict

**SC-008 gate: PASS** at production-config defaults.

Spec 007 ships with bull-side default-on @T=0.60 + bear-side default-shadow @T=0.50; production retrospective confirms the empirical evidence from the Opus retrofit.

## Reproducibility

```
python scripts/forward_catalyst_retrospective.py
```

Reads cached scores from `claudedocs\forward-catalyst-class3-opus-retrospective-2026-05-06.csv` + production config from `tradingagents.default_config.DEFAULT_CONFIG`. Zero LLM cost.
