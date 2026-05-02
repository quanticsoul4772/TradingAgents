"""Tests for tradingagents.experiments.templates."""

import json

import pytest

from tradingagents.experiments.templates import (
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
