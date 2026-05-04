"""Unit tests for dataflows/interface.py — vendor routing.

Tests the 3 public functions: get_category_for_method, get_vendor,
route_to_vendor. Previously 44% covered (54 stmts).

Routing semantics:
- Tool-level config (config["tool_vendors"][method]) overrides category-level
- Category-level config (config["data_vendors"][category]) is the default
- Multiple vendors can be specified comma-separated for primary preference
- AlphaVantageRateLimitError on the primary triggers fallback to other vendors
- All other exceptions propagate unchanged
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tradingagents.dataflows.alpha_vantage_common import AlphaVantageRateLimitError
from tradingagents.dataflows.interface import (
    VENDOR_METHODS,
    get_category_for_method,
    get_vendor,
    route_to_vendor,
)

# -- get_category_for_method ------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "method,expected_category",
    [
        ("get_stock_data", "core_stock_apis"),
        ("get_indicators", "technical_indicators"),
        ("get_fundamentals", "fundamental_data"),
        ("get_balance_sheet", "fundamental_data"),
        ("get_cashflow", "fundamental_data"),
        ("get_income_statement", "fundamental_data"),
        ("get_news", "news_data"),
        ("get_global_news", "news_data"),
        ("get_insider_transactions", "fundamental_data"),
    ],
)
def test_get_category_for_known_method(method, expected_category):
    assert get_category_for_method(method) == expected_category


@pytest.mark.unit
def test_get_category_for_unknown_method_raises():
    with pytest.raises(ValueError, match="not found in any category"):
        get_category_for_method("not_a_real_method")


# -- get_vendor -------------------------------------------------------------


@pytest.mark.unit
def test_get_vendor_returns_category_default():
    """When no tool-level override, return data_vendors[category]."""
    config = {
        "data_vendors": {"news_data": "exa"},
        "tool_vendors": {},
    }
    with patch("tradingagents.dataflows.interface.get_config", return_value=config):
        assert get_vendor("news_data") == "exa"


@pytest.mark.unit
def test_get_vendor_tool_override_beats_category():
    """tool_vendors[method] takes precedence over data_vendors[category]."""
    config = {
        "data_vendors": {"news_data": "exa"},
        "tool_vendors": {"get_news": "alpha_vantage"},
    }
    with patch("tradingagents.dataflows.interface.get_config", return_value=config):
        assert get_vendor("news_data", method="get_news") == "alpha_vantage"


@pytest.mark.unit
def test_get_vendor_no_override_no_default_returns_sentinel():
    """Missing entry in both → 'default' string (not raise, not None)."""
    config = {"data_vendors": {}, "tool_vendors": {}}
    with patch("tradingagents.dataflows.interface.get_config", return_value=config):
        assert get_vendor("news_data") == "default"


@pytest.mark.unit
def test_get_vendor_method_arg_with_no_tool_vendors_falls_back_to_category():
    """If method given but no tool-level entry exists, use category-level."""
    config = {
        "data_vendors": {"news_data": "exa"},
        "tool_vendors": {"get_other_thing": "alpha_vantage"},
    }
    with patch("tradingagents.dataflows.interface.get_config", return_value=config):
        assert get_vendor("news_data", method="get_news") == "exa"


# -- route_to_vendor --------------------------------------------------------


@pytest.mark.unit
def test_route_to_vendor_calls_configured_vendor():
    """Happy path: configured vendor's impl is invoked with passed args."""

    def fake_impl(*a, **kw):
        return f"called with {a}, {kw}"

    config = {"data_vendors": {"news_data": "exa"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(VENDOR_METHODS, {"get_news": {"exa": fake_impl}}, clear=False),
    ):
        result = route_to_vendor("get_news", "NVDA", "2026-01-30", "2026-02-06")
    assert "NVDA" in result
    assert "2026-01-30" in result


@pytest.mark.unit
def test_route_to_vendor_unknown_method_raises():
    with pytest.raises(ValueError, match="not found in any category"):
        route_to_vendor("totally_made_up_method")


@pytest.mark.unit
def test_route_to_vendor_falls_back_on_rate_limit():
    """When primary vendor raises AlphaVantageRateLimitError, fall back to another."""
    primary_calls = []
    fallback_calls = []

    def primary(*a, **kw):
        primary_calls.append((a, kw))
        raise AlphaVantageRateLimitError("rate limited")

    def fallback(*a, **kw):
        fallback_calls.append((a, kw))
        return "fallback result"

    config = {"data_vendors": {"news_data": "alpha_vantage"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(
            VENDOR_METHODS,
            {"get_news": {"alpha_vantage": primary, "exa": fallback}},
            clear=False,
        ),
    ):
        result = route_to_vendor("get_news", "NVDA")
    assert result == "fallback result"
    assert len(primary_calls) == 1
    assert len(fallback_calls) == 1


@pytest.mark.unit
def test_route_to_vendor_propagates_non_rate_limit_exceptions():
    """Non-rate-limit exceptions propagate (no fallback for general errors)."""

    def primary(*a, **kw):
        raise RuntimeError("network down")

    def fallback(*a, **kw):
        return "should not reach"

    config = {"data_vendors": {"news_data": "alpha_vantage"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(
            VENDOR_METHODS,
            {"get_news": {"alpha_vantage": primary, "exa": fallback}},
            clear=False,
        ),
    ):
        with pytest.raises(RuntimeError, match="network down"):
            route_to_vendor("get_news")


@pytest.mark.unit
def test_route_to_vendor_comma_separated_primary_vendors():
    """vendor_config 'a,b' tries a first, then b. Both honored as preference order."""
    calls = []

    def vendor_a(*a, **kw):
        calls.append("a")
        raise AlphaVantageRateLimitError("a rate-limited")

    def vendor_b(*a, **kw):
        calls.append("b")
        return "b result"

    config = {"data_vendors": {"news_data": "alpha_vantage,exa"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(
            VENDOR_METHODS,
            {"get_news": {"alpha_vantage": vendor_a, "exa": vendor_b}},
            clear=False,
        ),
    ):
        result = route_to_vendor("get_news")
    assert calls == ["a", "b"]
    assert result == "b result"


@pytest.mark.unit
def test_route_to_vendor_no_available_vendor_raises():
    """When all configured vendors rate-limit and there's no remaining fallback."""

    def vendor_a(*a, **kw):
        raise AlphaVantageRateLimitError("rate")

    config = {"data_vendors": {"news_data": "alpha_vantage"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(
            VENDOR_METHODS,
            {"get_news": {"alpha_vantage": vendor_a}},
            clear=False,
        ),
    ):
        with pytest.raises(RuntimeError, match="No available vendor"):
            route_to_vendor("get_news")


@pytest.mark.unit
def test_route_to_vendor_skips_unknown_vendor_in_config():
    """A vendor name in config that's not in VENDOR_METHODS gets skipped silently
    (treated like "vendor not available for this method")."""

    def real_vendor(*a, **kw):
        return "real result"

    # Config says "ghost" first then "exa"; ghost isn't in VENDOR_METHODS at all
    config = {"data_vendors": {"news_data": "ghost,exa"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(
            VENDOR_METHODS,
            {"get_news": {"exa": real_vendor}},
            clear=False,
        ),
    ):
        result = route_to_vendor("get_news")
    assert result == "real result"


@pytest.mark.unit
def test_route_to_vendor_handles_vendor_impl_as_list():
    """Some vendor impls might be wrapped as [callable] — route should unwrap."""

    def fake_impl(*a, **kw):
        return "list-wrapped result"

    config = {"data_vendors": {"news_data": "exa"}, "tool_vendors": {}}
    with (
        patch("tradingagents.dataflows.interface.get_config", return_value=config),
        patch.dict(VENDOR_METHODS, {"get_news": {"exa": [fake_impl]}}, clear=False),
    ):
        result = route_to_vendor("get_news")
    assert result == "list-wrapped result"


# -- Categorization regression guard ---------------------------------------
#
# Reason: experiment 008 errored on 22/22 runs because get_insider_transactions
# was in news_data category (default vendor "exa") but had no exa impl. The
# fallback chain skipped exa and tried alpha_vantage (next dict key), which
# raised ValueError on missing ALPHA_VANTAGE_API_KEY — never reached yfinance.
# This test asserts every (category, tool) pair has an impl for the category's
# DEFAULT_CONFIG vendor, catching the same class of bug at unit-test time.


@pytest.mark.unit
def test_every_categorized_tool_has_impl_for_default_vendor():
    """For every tool in TOOLS_CATEGORIES, the DEFAULT_CONFIG vendor for its
    category must appear in VENDOR_METHODS[tool] — otherwise route_to_vendor
    will fall through to whichever vendor happens to be next in dict order."""
    from tradingagents.dataflows.interface import TOOLS_CATEGORIES
    from tradingagents.default_config import DEFAULT_CONFIG

    default_vendors = DEFAULT_CONFIG["data_vendors"]
    failures = []
    for category, info in TOOLS_CATEGORIES.items():
        default_vendor = default_vendors.get(category)
        assert default_vendor is not None, (
            f"DEFAULT_CONFIG['data_vendors'] is missing a default for category {category!r}"
        )
        for tool in info["tools"]:
            available = list(VENDOR_METHODS.get(tool, {}).keys())
            if default_vendor not in available:
                failures.append(
                    f"{category}.{tool}: default vendor {default_vendor!r} not in "
                    f"VENDOR_METHODS[{tool!r}]={available!r}"
                )
    assert not failures, (
        "Some categorized tools have no impl for their category's default vendor:\n  "
        + "\n  ".join(failures)
    )
