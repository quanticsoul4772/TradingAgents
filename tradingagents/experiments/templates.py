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

## What we're testing

<!-- One paragraph: what knob varies, against what baseline. -->

## Why we expect <prediction>

<!-- One paragraph: the predicted outcome and why. Replace <prediction> in the heading too. -->

## Success criterion

<!-- One bullet list: what observation would confirm the prediction. -->

- [ ] [criterion 1]

## Notes

<!-- Optional: any pre-run thinking. -->

## Related experiments

<!-- Optional: link IDs of prior related experiments. -->
"""

_PARAMS_TEMPLATE = {
    "config_overrides": {},
    "explicit_flags": {},
    "baseline": "",
    "notes": "",
}

_RUN_SH_TEMPLATE = """\
#!/usr/bin/env bash
# Repro command for experiment {id}
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
set -euo pipefail
python scripts/backtest.py \\
    --experiment-id "{id}" \\
    --out "experiments/{id}/results.csv" \\
    --yes
"""

_RUN_PS1_TEMPLATE = """\
#!/usr/bin/env pwsh
# Repro command for experiment {id}
# EDIT THIS FILE to point at the actual runner for your experiment.
# Default stub uses the standard backtest harness.
$ErrorActionPreference = 'Stop'
python scripts/backtest.py `
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
) -> str:
    """Render HYPOTHESIS.md content for a new experiment.

    `slug` and `date` are derived from `id_str` if not provided. `source_idea`
    and `cost` are optional pre-fills; absent values render as empty strings
    so the researcher can fill them in by hand.
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
    return _HYPOTHESIS_TEMPLATE.format(
        id=id_str,
        slug=slug,
        date=date,
        source_idea=source_idea if source_idea else "",
        cost=f"~${cost:.2f}" if cost is not None else "",
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
