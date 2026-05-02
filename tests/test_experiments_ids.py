"""Tests for tradingagents.experiments.ids."""

from datetime import date

import pytest

from tradingagents.experiments.ids import (
    ID_REGEX,
    SLUG_REGEX,
    next_experiment_id,
    parse_id,
    validate_id,
    validate_slug,
)

pytestmark = pytest.mark.unit


# ---- validate_id / parse_id round-trip -----------------------------------


@pytest.mark.parametrize(
    "id_str",
    [
        "2026-05-02-001-mr1-contradiction",
        "2026-05-02-002-pm-blind",
        "2026-12-31-999-end-of-year-final-experiment",
        "2026-01-01-001-ab",
    ],
)
def test_valid_ids_pass_validation(id_str):
    assert validate_id(id_str) is True


@pytest.mark.parametrize(
    "id_str",
    [
        "2026-5-2-001-foo",  # date components not zero-padded
        "2026-05-02-1-foo",  # sequence not zero-padded to 3
        "2026-05-02-001-Foo",  # uppercase in slug
        "2026-05-02-001--foo",  # double hyphen / leading hyphen in slug
        "2026-05-02-001-foo-",  # trailing hyphen in slug
        "2026-05-02-001-",  # empty slug
        "2026-05-02-001-a",  # single-char slug (regex requires 2+)
        "20260502-001-foo",  # missing date hyphens
        "",  # empty
        "not-an-id",
    ],
)
def test_invalid_ids_rejected(id_str):
    assert validate_id(id_str) is False


def test_parse_id_round_trip():
    parsed = parse_id("2026-05-02-007-foo-bar")
    assert parsed == (date(2026, 5, 2), 7, "foo-bar")


def test_parse_id_raises_on_invalid():
    with pytest.raises(ValueError):
        parse_id("not-a-real-id")


# ---- validate_slug ------------------------------------------------------


@pytest.mark.parametrize(
    "slug",
    [
        "ab",
        "mr1-contradiction",
        "pm-blind",
        "x9",
        "a-b-c-d-e",
    ],
)
def test_valid_slugs(slug):
    assert validate_slug(slug) is True


@pytest.mark.parametrize(
    "slug",
    [
        "",
        "a",  # too short
        "-foo",  # leading hyphen
        "foo-",  # trailing hyphen
        "Foo",  # uppercase
        "foo_bar",  # underscore not allowed
        "x" * 41,  # too long (max 40)
    ],
)
def test_invalid_slugs(slug):
    assert validate_slug(slug) is False


# ---- next_experiment_id sequence ---------------------------------------


def test_next_id_starts_at_001(tmp_path):
    out = next_experiment_id(tmp_path, "first", date=date(2026, 5, 2))
    assert out == "2026-05-02-001-first"


def test_next_id_increments_within_day(tmp_path):
    (tmp_path / "2026-05-02-001-foo").mkdir()
    (tmp_path / "2026-05-02-002-bar").mkdir()
    out = next_experiment_id(tmp_path, "baz", date=date(2026, 5, 2))
    assert out == "2026-05-02-003-baz"


def test_next_id_resets_across_days(tmp_path):
    (tmp_path / "2026-05-01-005-foo").mkdir()
    out = next_experiment_id(tmp_path, "newday", date=date(2026, 5, 2))
    assert out == "2026-05-02-001-newday"


def test_next_id_ignores_non_matching_dirs(tmp_path):
    (tmp_path / "not-an-experiment").mkdir()
    (tmp_path / "tmp").mkdir()
    (tmp_path / "2026-05-02-001-foo").mkdir()
    out = next_experiment_id(tmp_path, "bar", date=date(2026, 5, 2))
    assert out == "2026-05-02-002-bar"


def test_next_id_ignores_files(tmp_path):
    (tmp_path / "2026-05-02-001-foo").write_text("not a dir")
    out = next_experiment_id(tmp_path, "bar", date=date(2026, 5, 2))
    assert out == "2026-05-02-001-bar"


def test_next_id_handles_missing_experiments_dir(tmp_path):
    nonexistent = tmp_path / "experiments-that-do-not-exist-yet"
    out = next_experiment_id(nonexistent, "foo", date=date(2026, 5, 2))
    assert out == "2026-05-02-001-foo"


def test_next_id_rejects_invalid_slug(tmp_path):
    with pytest.raises(ValueError):
        next_experiment_id(tmp_path, "Bad-Slug", date=date(2026, 5, 2))


def test_id_regex_anchored_at_start():
    # Cannot match if there's stuff before the date.
    assert ID_REGEX.match("prefix-2026-05-02-001-foo") is None


def test_slug_can_contain_internal_hyphens():
    # `foo-suffix` is a valid kebab-case slug and a valid full ID.
    assert validate_id("2026-05-02-001-foo-suffix") is True
    assert validate_slug("foo-suffix") is True


def test_slug_regex_rejects_edge_hyphens():
    assert SLUG_REGEX.match("-leading") is None
    assert SLUG_REGEX.match("trailing-") is None
