"""Unit tests for dataflows/utils.py — small filesystem + date helpers.

Previously 0% coverage despite being used in vendor modules for CSV save
and weekday alignment.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from tradingagents.dataflows.utils import (
    decorate_all_methods,
    get_current_date,
    get_next_weekday,
    save_output,
)


# -- save_output ---------------------------------------------------------


@pytest.mark.unit
def test_save_output_writes_csv_when_path_given(tmp_path, capsys):
    """Writes a CSV at the given path and prints a save-confirmation line."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    out_path = tmp_path / "frame.csv"
    save_output(df, "test-tag", str(out_path))
    assert out_path.exists()
    # File contains the data
    loaded = pd.read_csv(out_path, index_col=0)
    assert list(loaded["a"]) == [1, 2]
    # Print includes tag + path
    captured = capsys.readouterr()
    assert "test-tag" in captured.out
    assert str(out_path) in captured.out


@pytest.mark.unit
def test_save_output_noop_when_path_none(tmp_path, capsys):
    """save_path=None → no file written, no print."""
    df = pd.DataFrame({"a": [1]})
    save_output(df, "tag", None)
    captured = capsys.readouterr()
    assert captured.out == ""


# -- get_current_date ---------------------------------------------------


@pytest.mark.unit
def test_get_current_date_returns_iso_format():
    """ISO YYYY-MM-DD format from today's date."""
    out = get_current_date()
    # Parse-able as ISO
    parsed = datetime.strptime(out, "%Y-%m-%d")
    assert parsed.strftime("%Y-%m-%d") == out


# -- decorate_all_methods --------------------------------------------------


@pytest.mark.unit
def test_decorate_all_methods_wraps_every_callable():
    """The class-decorator wraps each callable attribute in `decorator`."""
    calls = []

    def tracking_decorator(fn):
        def wrapped(*args, **kwargs):
            calls.append(fn.__name__)
            return fn(*args, **kwargs)
        return wrapped

    @decorate_all_methods(tracking_decorator)
    class Sample:
        def method_a(self):
            return "a"

        def method_b(self):
            return "b"

    s = Sample()
    s.method_a()
    s.method_b()
    s.method_a()
    assert calls == ["method_a", "method_b", "method_a"]


@pytest.mark.unit
def test_decorate_all_methods_skips_non_callable_attributes():
    """Class-level data attributes (str, int, etc.) are not wrapped."""

    def trivial_decorator(fn):
        return fn

    @decorate_all_methods(trivial_decorator)
    class Sample:
        CLASS_CONSTANT = "constant"

        def real_method(self):
            return self.CLASS_CONSTANT

    assert Sample.CLASS_CONSTANT == "constant"  # unchanged
    assert Sample().real_method() == "constant"


# -- get_next_weekday --------------------------------------------------


@pytest.mark.unit
def test_get_next_weekday_passes_through_weekdays():
    """Mon-Fri inputs return unchanged."""
    # 2026-02-02 is a Monday
    monday = datetime(2026, 2, 2)
    out = get_next_weekday(monday)
    assert out == monday

    # 2026-02-06 is a Friday
    friday = datetime(2026, 2, 6)
    out = get_next_weekday(friday)
    assert out == friday


@pytest.mark.unit
def test_get_next_weekday_advances_saturday_to_monday():
    """Saturday (weekday=5) → following Monday."""
    saturday = datetime(2026, 2, 7)  # Sat
    out = get_next_weekday(saturday)
    assert out.weekday() == 0  # Monday
    assert out == datetime(2026, 2, 9)


@pytest.mark.unit
def test_get_next_weekday_advances_sunday_to_monday():
    """Sunday (weekday=6) → following Monday."""
    sunday = datetime(2026, 2, 8)  # Sun
    out = get_next_weekday(sunday)
    assert out.weekday() == 0
    assert out == datetime(2026, 2, 9)


@pytest.mark.unit
def test_get_next_weekday_accepts_string_input():
    """ISO date string is parsed and processed identically."""
    out = get_next_weekday("2026-02-08")  # Sunday
    assert out == datetime(2026, 2, 9)
