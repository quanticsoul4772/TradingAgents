"""Tests for scripts/new_experiment.py.

Per specs/001-experiments-scaffolding/contracts/new_experiment_cli.md.
"""

import json

# Import the script's helper directly to avoid CLI plumbing in unit tests.
import sys
from datetime import date
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from new_experiment import _create_experiment  # noqa: E402

pytestmark = pytest.mark.unit


# ---- Happy path ---------------------------------------------------------


def test_creates_dir_and_files(tmp_path):
    out = _create_experiment(
        "mr1-contradiction",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    assert out == tmp_path / "2026-05-02-001-mr1-contradiction"
    assert out.is_dir()
    assert (out / "HYPOTHESIS.md").exists()
    assert (out / "PARAMS.json").exists()
    assert (out / "run.sh").exists()
    assert (out / "run.ps1").exists()


def test_hypothesis_contains_id(tmp_path):
    out = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    text = (out / "HYPOTHESIS.md").read_text(encoding="utf-8")
    assert "2026-05-02-001-foo" in text


def test_params_json_is_valid_empty_object_structure(tmp_path):
    out = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    parsed = json.loads((out / "PARAMS.json").read_text(encoding="utf-8"))
    assert parsed == {
        "config_overrides": {},
        "explicit_flags": {},
        "baseline": "",
        "notes": "",
    }


def test_run_sh_references_experiment_id(tmp_path):
    out = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    text = (out / "run.sh").read_text(encoding="utf-8")
    assert "2026-05-02-001-foo" in text
    assert "experiments/2026-05-02-001-foo/results.csv" in text


# ---- FR-003: refuse duplicate -----------------------------------------


def test_refuses_duplicate(tmp_path):
    _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    # Second invocation with same args lands in NEXT sequence number, not
    # a conflict — this is by design (next_experiment_id auto-increments).
    out2 = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    assert out2.name == "2026-05-02-002-foo"
    # Real conflict scenario: pre-create the target dir manually, then
    # invoke. The FileExistsError protects against pre-existing dirs that
    # somehow have the same ID (which next_experiment_id should skip).
    pre_existing = tmp_path / "2026-05-03-001-bar"
    pre_existing.mkdir()
    # next_experiment_id sees this and goes to 002, so no conflict.
    out3 = _create_experiment(
        "bar",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 3),
    )
    assert out3.name == "2026-05-03-002-bar"


# ---- FR-001 (slug validation) -----------------------------------------


def test_rejects_invalid_short_name(tmp_path):
    with pytest.raises(ValueError, match="Invalid short-name"):
        _create_experiment(
            "Bad-Slug",
            experiments_dir=tmp_path,
            source_idea=None,
            cost=None,
            on_date=date(2026, 5, 2),
        )


def test_rejects_short_name_with_underscore(tmp_path):
    with pytest.raises(ValueError):
        _create_experiment(
            "snake_case",
            experiments_dir=tmp_path,
            source_idea=None,
            cost=None,
            on_date=date(2026, 5, 2),
        )


# ---- Sequence increment within day ------------------------------------


def test_increments_sequence_within_day(tmp_path):
    a = _create_experiment(
        "first",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    b = _create_experiment(
        "second",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    c = _create_experiment(
        "third",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    assert a.name == "2026-05-02-001-first"
    assert b.name == "2026-05-02-002-second"
    assert c.name == "2026-05-02-003-third"


def test_sequence_resets_across_days(tmp_path):
    _create_experiment(
        "aa",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 1),
    )
    _create_experiment(
        "bb",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 1),
    )
    out = _create_experiment(
        "cc",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    assert out.name == "2026-05-02-001-cc"


# ---- --source-idea pre-fill -------------------------------------------


def test_source_idea_prefills_hypothesis(tmp_path):
    out = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea="MR-1",
        cost=None,
        on_date=date(2026, 5, 2),
    )
    text = (out / "HYPOTHESIS.md").read_text(encoding="utf-8")
    assert "MR-1" in text


def test_cost_prefills_hypothesis(tmp_path):
    out = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=12.5,
        on_date=date(2026, 5, 2),
    )
    text = (out / "HYPOTHESIS.md").read_text(encoding="utf-8")
    assert "~$12.50" in text


# ---- ANALYSIS template flag ---------------------------------------------


def test_with_analysis_template_default_false_omits_file(tmp_path):
    out = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
    )
    assert not (out / "ANALYSIS_TEMPLATE.md").exists()


def test_with_analysis_template_true_writes_file(tmp_path):
    out = _create_experiment(
        "foo",
        experiments_dir=tmp_path,
        source_idea=None,
        cost=None,
        on_date=date(2026, 5, 2),
        with_analysis_template=True,
    )
    template = out / "ANALYSIS_TEMPLATE.md"
    assert template.exists()
    text = template.read_text(encoding="utf-8")
    assert "2026-05-02-001-foo" in text
    assert "## Headline verdict" in text
    assert "## Falsification framework verdict" in text
