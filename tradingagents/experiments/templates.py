"""Template renderers for new-experiment scaffolding.

HYPOTHESIS.md, PARAMS.json, run.sh, run.ps1 — produced by
scripts/new_experiment.py per contracts/new_experiment_cli.md.
"""

from __future__ import annotations

import json

_HYPOTHESIS_TEMPLATE = """\
# Hypothesis: {slug}

**Experiment ID**: `{id}`
**Created**: {date}
**Source idea**: {source_idea}
**Cost estimate**: {cost}
**Cost tier**: {tier_label}

## What we're testing

<!-- One paragraph: what knob varies, against what baseline. -->

## Why we expect <prediction>

<!-- One paragraph: the predicted outcome and why. Replace <prediction> in the heading too. -->

## Success criterion

<!-- One bullet list: what observation would confirm the prediction. -->

- [ ] [criterion 1]
{tier_section}
## Notes

<!-- Optional: any pre-run thinking. -->

## Related experiments

<!-- Optional: link IDs of prior related experiments. -->
"""

# Cost tier ladder per Constitution Principle III (v1.2.0).
# T2 is the default — exploratory-but-cheap. T3 / T4 require justification.
_TIER_INFO = {
    "T1": {
        "range": "$0 – $5",
        "label": "free exploration",
    },
    "T2": {
        "range": "$5 – $30",
        "label": "standard",
    },
    "T3": {
        "range": "$30 – $100",
        "label": "scaled",
    },
    "T4": {
        "range": "> $100",
        "label": "capital",
    },
}


def infer_tier(cost: float | None) -> str:
    """Derive cost tier from a USD cost estimate.

    Boundaries are inclusive on the upper end: cost==5 is T1, cost==5.01 is T2.
    `None` → T2 (default for the standard exploratory case).
    """
    if cost is None:
        return "T2"
    if cost <= 5:
        return "T1"
    if cost <= 30:
        return "T2"
    if cost <= 100:
        return "T3"
    return "T4"


def _tier_section(tier: str) -> str:
    """Inject the Cost-Justification scaffold for T3 / T4. Empty for T1 / T2."""
    if tier in {"T1", "T2"}:
        return ""
    base = (
        "\n## Cost Justification (required for T3 / T4 — Constitution III)\n"
        "\n"
        "**Why this scale** (vs. a smaller pilot):\n"
        "<!-- One paragraph -->\n"
        "\n"
        "**Cheaper alternatives considered** (and why rejected):\n"
        "<!-- Bullet list -->\n"
        "\n"
        "**Outcome that would justify the spend**:\n"
        "<!-- One bullet — the result that, if observed, makes this run worth its cost -->\n"
    )
    if tier == "T4":
        base += (
            "\n**Multi-day deliberation log** (T4 only — when the idea was first floated, "
            "what objections were raised, why we proceeded anyway):\n"
            "<!-- Dated bullet list across at least 2 days -->\n"
            "\n"
            "**Fallback plan if experiment fails to deliver**:\n"
            "<!-- One paragraph -->\n"
            "\n"
            "**Alternative-experiment comparisons** (other ways to spend this $):\n"
            "<!-- Bullet list of alternatives we explicitly chose against -->\n"
            "\n"
            "**Kill criteria** (specific result that invalidates further T4 spending here):\n"
            "<!-- One bullet -->\n"
        )
    return base

_PARAMS_TEMPLATE = {
    "config_overrides": {},
    "explicit_flags": {},
    "baseline": "",
    "notes": "",
}

_ANALYSIS_TEMPLATE = """\
# ANALYSIS template — {slug}

> **STATUS**: TEMPLATE awaiting data. When the experiment completes,
> replace `<TBD>` placeholders with computed values, fill the verdict
> sections, and rename this file to `ANALYSIS.md`.

**Experiment ID**: `{id}`
**Created**: {date}

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
"""

_RUN_SH_TEMPLATE = """\
#!/usr/bin/env bash
# Repro command for experiment {id}
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
# `uv run` resolves to the project's .venv; bare `python` may resolve to
# the system interpreter, which doesn't have typer/anthropic/etc. installed.
set -euo pipefail
uv run --no-sync python scripts/backtest.py \\
    --experiment-id "{id}" \\
    --out "experiments/{id}/results.csv" \\
    --yes
"""

_RUN_PS1_TEMPLATE = """\
#!/usr/bin/env pwsh
# Repro command for experiment {id}
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
# `uv run` resolves to the project's .venv; bare `python` may resolve to
# the system interpreter, which doesn't have typer/anthropic/etc. installed.
$ErrorActionPreference = 'Stop'
uv run --no-sync python scripts/backtest.py `
    --experiment-id "{id}" `
    --out "experiments/{id}/results.csv" `
    --yes
"""


def render_hypothesis(
    id_str: str,
    *,
    slug: str | None = None,
    date: str | None = None,
    source_idea: str | None = None,
    cost: float | None = None,
    tier: str | None = None,
) -> str:
    """Render HYPOTHESIS.md content for a new experiment.

    `slug` and `date` are derived from `id_str` if not provided. `source_idea`
    and `cost` are optional pre-fills; absent values render as empty strings
    so the researcher can fill them in by hand. `tier` is the cost tier per
    Constitution Principle III; if not provided it is inferred from `cost`
    (None → T2). T3 / T4 inject a required Cost-Justification scaffold.
    """
    if slug is None or date is None:
        # Lazy import to avoid circular reference if templates ever
        # imports ids; today they don't.
        from tradingagents.experiments.ids import parse_id
        d, _seq, parsed_slug = parse_id(id_str)
        if slug is None:
            slug = parsed_slug
        if date is None:
            date = d.isoformat()

    if tier is None:
        tier = infer_tier(cost)
    if tier not in _TIER_INFO:
        raise ValueError(
            f"Invalid tier {tier!r}: must be one of {sorted(_TIER_INFO)}. "
            "T1 ≤$5 / T2 $5-30 (default) / T3 $30-100 / T4 >$100."
        )
    info = _TIER_INFO[tier]
    tier_label = f"{tier} ({info['label']}, {info['range']})"

    return _HYPOTHESIS_TEMPLATE.format(
        id=id_str,
        slug=slug,
        date=date,
        source_idea=source_idea if source_idea else "",
        cost=f"~${cost:.2f}" if cost is not None else "",
        tier_label=tier_label,
        tier_section=_tier_section(tier),
    )


def render_params_json() -> str:
    """Render the initial PARAMS.json content (pretty-printed JSON)."""
    return json.dumps(_PARAMS_TEMPLATE, indent=2) + "\n"


def render_run_sh(id_str: str) -> str:
    """Render the run.sh stub for `id_str`."""
    return _RUN_SH_TEMPLATE.format(id=id_str)


def render_run_ps1(id_str: str) -> str:
    """Render the run.ps1 stub for `id_str`."""
    return _RUN_PS1_TEMPLATE.format(id=id_str)


def render_analysis_template(
    id_str: str,
    *,
    slug: str | None = None,
    date: str | None = None,
) -> str:
    """Render ANALYSIS_TEMPLATE.md content for a new experiment.

    Pre-scaffolding pattern from PR #135 (WC-10 v2/v3 templates) extracted as
    reusable tooling per cross-pollination review (PR #143). Operators opt in
    via `--with-analysis-template` flag on `scripts/new_experiment.py`.

    The template provides:
    - Headline verdict scaffold
    - Per-row results table (operator extends columns to experiment grid)
    - Aggregate metrics table (n / mean / hit rate / dispersion)
    - Falsification framework verdict table (NULL / ALT-A / ALT-B rows)
    - Constitution adherence checklist (8 principles)
    - Verdict-conditional next-steps section
    """
    if slug is None or date is None:
        from tradingagents.experiments.ids import parse_id

        d, _seq, parsed_slug = parse_id(id_str)
        if slug is None:
            slug = parsed_slug
        if date is None:
            date = d.isoformat()

    return _ANALYSIS_TEMPLATE.format(id=id_str, slug=slug, date=date)
