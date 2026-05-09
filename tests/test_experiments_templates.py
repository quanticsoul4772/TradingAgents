"""Tests for tradingagents.experiments.templates."""

import json

import pytest

from tradingagents.experiments.templates import (
    render_analysis_template,
    render_hypothesis,
    render_params_json,
    render_run_ps1,
    render_run_sh,
)

pytestmark = pytest.mark.unit


# ---- render_hypothesis --------------------------------------------------


def test_hypothesis_includes_id_and_slug_and_date_from_id():
    out = render_hypothesis("2026-05-02-001-mr1-contradiction")
    assert "2026-05-02-001-mr1-contradiction" in out
    assert "mr1-contradiction" in out
    assert "2026-05-02" in out


def test_hypothesis_includes_source_idea_when_provided():
    out = render_hypothesis("2026-05-02-001-foo", source_idea="MR-1")
    assert "MR-1" in out


def test_hypothesis_omits_source_idea_when_not_provided():
    out = render_hypothesis("2026-05-02-001-foo")
    # The line is present but value is empty.
    assert "**Source idea**:" in out


def test_hypothesis_includes_cost_when_provided():
    out = render_hypothesis("2026-05-02-001-foo", cost=12.5)
    assert "~$12.50" in out


def test_hypothesis_omits_cost_when_not_provided():
    out = render_hypothesis("2026-05-02-001-foo")
    # The line label exists; value is empty (not shown as "~$0.00").
    assert "**Cost estimate**:" in out
    assert "~$0.00" not in out


def test_hypothesis_includes_required_section_headings():
    out = render_hypothesis("2026-05-02-001-foo")
    assert "## What we're testing" in out
    assert "## Why we expect" in out
    assert "## Success criterion" in out


def test_hypothesis_explicit_overrides_used():
    out = render_hypothesis(
        "2026-05-02-001-something",
        slug="custom-slug",
        date="1999-12-31",
    )
    assert "custom-slug" in out
    assert "1999-12-31" in out


# ---- Cost-tier infra (Constitution v1.2.0 Principle III) -----------------


def test_hypothesis_default_tier_is_T2():
    """No cost given + no tier given → T2 (default scaled-but-still-cheap)."""
    from tradingagents.experiments.templates import infer_tier

    out = render_hypothesis("2026-05-02-001-foo")
    assert "**Cost tier**: T2" in out
    assert infer_tier(None) == "T2"


def test_hypothesis_tier_inferred_from_cost():
    """Tier auto-derives from --cost when --tier not given."""
    from tradingagents.experiments.templates import infer_tier

    assert infer_tier(0) == "T1"
    assert infer_tier(3) == "T1"
    assert infer_tier(5) == "T1"  # boundary inclusive
    assert infer_tier(5.01) == "T2"
    assert infer_tier(20) == "T2"
    assert infer_tier(30) == "T2"
    assert infer_tier(30.01) == "T3"
    assert infer_tier(75) == "T3"
    assert infer_tier(100) == "T3"
    assert infer_tier(100.01) == "T4"
    assert infer_tier(250) == "T4"


def test_hypothesis_T1_no_cost_justification_section():
    """T1/T2 do NOT inject the Cost Justification section."""
    out = render_hypothesis("2026-05-02-001-foo", cost=2.0)
    assert "**Cost tier**: T1" in out
    assert "## Cost Justification" not in out


def test_hypothesis_T2_no_cost_justification_section():
    out = render_hypothesis("2026-05-02-001-foo", cost=15.0)
    assert "**Cost tier**: T2" in out
    assert "## Cost Justification" not in out


def test_hypothesis_T3_injects_cost_justification_section():
    """T3 injects the required-fields scaffold (why this scale, alternatives, outcome)."""
    out = render_hypothesis("2026-05-02-001-foo", cost=65.0)
    assert "**Cost tier**: T3" in out
    assert "## Cost Justification" in out
    assert "Why this scale" in out
    assert "Cheaper alternatives considered" in out
    assert "Outcome that would justify the spend" in out
    # T4-only fields should NOT appear in T3
    assert "Multi-day deliberation log" not in out
    assert "Kill criteria" not in out


def test_hypothesis_T4_injects_full_capital_section():
    """T4 includes T3 fields PLUS multi-day deliberation, fallback, kill criteria."""
    out = render_hypothesis("2026-05-02-001-foo", cost=250.0)
    assert "**Cost tier**: T4" in out
    assert "## Cost Justification" in out
    # T3 fields
    assert "Why this scale" in out
    assert "Cheaper alternatives considered" in out
    assert "Outcome that would justify the spend" in out
    # T4-additional fields
    assert "Multi-day deliberation log" in out
    assert "Fallback plan if experiment fails to deliver" in out
    assert "Alternative-experiment comparisons" in out
    assert "Kill criteria" in out


def test_hypothesis_explicit_tier_overrides_cost_inference():
    """If both --cost and --tier are given, --tier wins."""
    # cost=$5 would infer T1, but explicit T3 should win
    out = render_hypothesis("2026-05-02-001-foo", cost=5.0, tier="T3")
    assert "**Cost tier**: T3" in out
    assert "## Cost Justification" in out


def test_hypothesis_invalid_tier_raises():
    """Unknown tier → ValueError, not silent fallback."""
    import pytest

    with pytest.raises(ValueError, match="Invalid tier"):
        render_hypothesis("2026-05-02-001-foo", tier="T5")


def test_hypothesis_tier_label_includes_range_and_meaning():
    """Tier line includes human-readable range + label, not just 'T3'."""
    out = render_hypothesis("2026-05-02-001-foo", cost=50.0)
    # Should mention the dollar range and the tier label
    assert "T3" in out
    assert "scaled" in out
    assert "$30" in out
    assert "$100" in out


# ---- render_params_json -------------------------------------------------


def test_params_json_is_valid_json():
    out = render_params_json()
    parsed = json.loads(out)
    assert parsed == {
        "config_overrides": {},
        "explicit_flags": {},
        "baseline": "",
        "notes": "",
    }


def test_params_json_pretty_printed():
    out = render_params_json()
    assert "\n" in out  # multi-line, not minified


def test_params_json_ends_with_newline():
    out = render_params_json()
    assert out.endswith("\n")


# ---- render_run_sh / render_run_ps1 -------------------------------------


def test_run_sh_includes_id_and_path():
    out = render_run_sh("2026-05-02-001-foo")
    assert "2026-05-02-001-foo" in out
    assert "experiments/2026-05-02-001-foo/results.csv" in out


def test_run_sh_has_shebang():
    out = render_run_sh("2026-05-02-001-foo")
    assert out.startswith("#!/usr/bin/env bash")


def test_run_sh_uses_set_strict():
    out = render_run_sh("2026-05-02-001-foo")
    assert "set -euo pipefail" in out


def test_run_ps1_includes_id_and_path():
    out = render_run_ps1("2026-05-02-001-foo")
    assert "2026-05-02-001-foo" in out
    assert "experiments/2026-05-02-001-foo/results.csv" in out


def test_run_ps1_has_pwsh_shebang():
    out = render_run_ps1("2026-05-02-001-foo")
    assert out.startswith("#!/usr/bin/env pwsh")


def test_run_ps1_uses_strict_error_action():
    out = render_run_ps1("2026-05-02-001-foo")
    assert "$ErrorActionPreference = 'Stop'" in out


# ---- render_analysis_template -------------------------------------------


def test_analysis_template_includes_id_and_slug_and_date_from_id():
    out = render_analysis_template("2026-05-02-001-foo")
    assert "2026-05-02-001-foo" in out
    assert "foo" in out
    assert "2026-05-02" in out


def test_analysis_template_marked_as_template():
    out = render_analysis_template("2026-05-02-001-foo")
    assert "STATUS" in out
    assert "TEMPLATE" in out


def test_analysis_template_has_required_sections():
    out = render_analysis_template("2026-05-02-001-foo")
    required = (
        "## Headline verdict",
        "## Per-row results",
        "## Aggregate metrics",
        "## Falsification framework verdict",
        "## Constitution adherence checklist",
        "## Next steps",
        "## Cross-references",
    )
    for section in required:
        assert section in out, f"missing section: {section}"


def test_analysis_template_includes_TBD_placeholders():
    out = render_analysis_template("2026-05-02-001-foo")
    assert "<TBD>" in out


def test_analysis_template_constitution_checklist_covers_all_principles():
    out = render_analysis_template("2026-05-02-001-foo")
    # Roman numerals I, II, III, IV, VI, VII, VIII (V is "Steal Liberally" -
    # not a runtime adherence concern). Eight principles per Constitution v1.5.0.
    for principle in (
        "I (Save Everything)",
        "II (One Experiment",
        "III (Stay Cheap)",
        "IV (No Production Claims)",
        "VI (Spec Before Structural Change)",
        "VII (Calibrated Abstention)",
        "VIII (Retrospective",
    ):
        assert principle in out, f"missing principle: {principle}"
