"""Tests for tradingagents.experiments.overrides."""

import logging

import pytest

from tradingagents.experiments.overrides import (
    apply_overrides,
    overrides_as_dict,
    parse_override,
)

pytestmark = pytest.mark.unit


# ---- parse_override coercion ladder ------------------------------------


def test_int_coercion():
    assert parse_override("max_debate_rounds=2") == ("max_debate_rounds", 2)


def test_negative_int_coercion():
    assert parse_override("offset=-5") == ("offset", -5)


def test_float_coercion():
    assert parse_override("temperature=1.5") == ("temperature", 1.5)


def test_negative_float_coercion():
    assert parse_override("alpha=-0.25") == ("alpha", -0.25)


def test_bool_true_coercion():
    assert parse_override("pm_sees_debate=true") == ("pm_sees_debate", True)


def test_bool_false_coercion():
    assert parse_override("pm_sees_debate=false") == ("pm_sees_debate", False)


def test_bool_case_insensitive():
    assert parse_override("flag=TRUE") == ("flag", True)
    assert parse_override("flag=False") == ("flag", False)


def test_null_coercion():
    assert parse_override("backend_url=none") == ("backend_url", None)
    assert parse_override("backend_url=null") == ("backend_url", None)


def test_string_fallback():
    assert parse_override("provider=anthropic") == ("provider", "anthropic")


def test_quoted_string_skips_coercion():
    # Without quotes "42" would become int 42; quotes keep it as str.
    assert parse_override('label="42"') == ("label", "42")
    assert parse_override('label="true"') == ("label", "true")


def test_value_with_equals_in_it():
    # Only the FIRST '=' splits; remainder is the value.
    assert parse_override("expr=a=b=c") == ("expr", "a=b=c")


def test_empty_value():
    # KEY= produces empty string after coercion fallback.
    assert parse_override("KEY=") == ("KEY", "")


# ---- parse_override error handling --------------------------------------


def test_missing_equals_raises():
    with pytest.raises(ValueError, match="must contain '='"):
        parse_override("no-equals-here")


def test_empty_key_raises():
    with pytest.raises(ValueError, match="empty key"):
        parse_override("=value")


# ---- apply_overrides --------------------------------------------------


def test_apply_overrides_does_not_mutate_input():
    config = {"a": 1, "b": 2}
    out = apply_overrides(config, ["a=42"])
    assert config == {"a": 1, "b": 2}  # unchanged
    assert out == {"a": 42, "b": 2}


def test_apply_overrides_multiple():
    config = {"a": 1, "b": 2, "c": "x"}
    out = apply_overrides(config, ["a=10", "b=20", "c=hello"])
    assert out == {"a": 10, "b": 20, "c": "hello"}


def test_apply_overrides_unknown_key_warns_by_default(caplog):
    config = {"known": 1}
    with caplog.at_level(logging.WARNING):
        out = apply_overrides(config, ["unknown=42"])
    assert out == {"known": 1, "unknown": 42}
    assert any("unknown config key" in r.message for r in caplog.records)


def test_apply_overrides_unknown_key_raises_when_disallowed():
    config = {"known": 1}
    with pytest.raises(ValueError, match="Unknown config key"):
        apply_overrides(config, ["unknown=42"], allow_unknown=False)


def test_apply_overrides_empty_list():
    config = {"a": 1}
    out = apply_overrides(config, [])
    assert out == {"a": 1}


# ---- overrides_as_dict --------------------------------------------------


def test_overrides_as_dict_collects_all():
    out = overrides_as_dict(["a=1", "b=2.5", "c=true"])
    assert out == {"a": 1, "b": 2.5, "c": True}


def test_overrides_as_dict_empty():
    assert overrides_as_dict([]) == {}
